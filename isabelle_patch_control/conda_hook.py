"""`conda-hook post-link` and `conda-hook pre-unlink <feature>` (plan decision 9): what the hooks
of every feature package run.  Both report only through $PREFIX/.messages.txt, every paragraph
with the isabelle-patch-control prefix on its first line, and exit 0 whenever they wrote their own
message.  When they cannot finish (a crash, or pre-unlink cannot tell which files still carry the
feature's changes) they write nothing and exit non-zero, and the hook text's `||` line speaks.

post-link applies the whole chain and reports what it changed; the complete diagnostic of a
CONFLICT is written only by the chain top's hook (PKG_NAME), the others write one line.
pre-unlink reverses the feature and everything above it, never applies, and when files of the
feature still carry its changes writes the residue block with the reason and the recovery steps.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable

from . import api, model, names, texts
from .engine import tree_path
from .features import locate


def run(hook: str, feature: str | None, env) -> int:
    prefix = Path(env["PREFIX"])
    if hook == "post-link":
        paragraphs = post_link(prefix, env.get("PKG_NAME"))
    else:
        assert feature, "conda-hook pre-unlink <feature>"
        paragraphs = [pre_unlink(prefix, feature)]
    if paragraphs := [p for p in paragraphs if p]:
        # ASCII: conda reads the file with a bare open(), the ANSI code page on Windows
        with open(prefix / ".messages.txt", "a", encoding="ascii", errors="backslashreplace") as f:
            f.writelines(f"{texts.PREFIX}{p}\n" for p in paragraphs)
    return 0


def post_link(prefix: Path, pkg_name: str | None) -> list[str]:
    tree, root = locate(prefix)
    try:
        res = api.apply(tree, root)
    except api.Busy as e:
        return [f"{e}{texts.LOCK_BUSY_HOOK_TAIL}"]
    except api.WriteFailed as e:
        try:
            st = api.status(tree, root, lock=False)
        except api.Error:                                     # the same failure again: say what failed, not what is applied
            return [texts.post_link_write_failed(str(e))]
        applied = [fd.name for fd, s in zip(st.chain, st.features) if s.state == model.APPLIED and not s.hole]
        return [texts.post_link_write_failed(str(e), applied)]
    except api.Error as e:
        return [texts.post_link_failed(str(e))]
    out = []
    if res.moves:
        out.append(texts.changed(tree, applied=res.applied) + (f"\n{texts.HEAP_PARAGRAPH}" if res.src_changed else ""))
    if res.conflicts:
        s = next(s for s in res.before.features if s.state == model.CONFLICT)   # the lowest feature stopped by a CONFLICT
        feature = res.before.chain[s.number - 1].name
        if _is_top(pkg_name, res.before.chain):
            files = [(t, res.before.levels[t].created_by(s.number)) for t in s.conflicts]
            cache = _edited_in_cache(prefix, tree, s.conflicts, linking=True)
            out.append(texts.conflict_full(feature, files, tree, cache=cache))
        else:
            out.append(texts.conflict_line(feature, s.conflicts))
    return out


def _is_top(pkg_name: str | None, chain) -> bool:
    """The hook of the chain top writes the complete diagnostic; an unset or unknown PKG_NAME counts
    as the top."""
    feature = names.feature_name(pkg_name) if pkg_name else None
    return feature not in {fd.name for fd in chain} or feature == chain[-1].name


def pre_unlink(prefix: Path, feature: str) -> str:
    tree, root = locate(prefix)
    package = names.package_name(feature)
    try:
        res = api.unapply(tree, root, feature=feature)
    except api.Busy:
        st = api.status(tree, root, feature=feature, lock=False)
        return _residue(prefix, tree, st, texts.REASON_LOCK, lock_package=(st.chain[-1].package, st.chain[-1].version))
    except api.WriteFailed:
        st = api.status(tree, root, feature=feature, lock=False)
        return _residue(prefix, tree, st, texts.REASON_WRITE)
    except api.ChainBroken as e:
        return texts.chain_broken_removal(feature, package, str(e))
    except api.Error as e:
        return texts.pre_unlink_failed(feature, package, str(e))
    left = _residue(prefix, tree, res.before, texts.REASON_CONFLICT, level=res.level_after)
    if left:
        return left
    if res.moves:
        return texts.undone_at_bottom(feature, tree) if res.at_bottom else texts.undone(feature, tree, res.reversed)
    return ""


def _residue(prefix: Path, tree: Path, st: api.Status, reason: str, *, level: Callable[[str], int | None] | None = None,
             lock_package: tuple[str, str] | None = None) -> str:
    """The residue block for the selected feature, or "" when none of its files still carries its
    changes.  `level` reads a file's level (the one after the run, or the status's own)."""
    k = st.selected
    level = level or (lambda t: st.levels[t].level)
    left = [(t, st.levels[t].created_by(k)) for t in st.features[k - 1].files if (lv := level(t)) is None or lv >= k]
    if not left:
        return ""
    cache = None if lock_package else _edited_in_cache(prefix, tree, [t for t, _ in left])
    return texts.residue(st.chain[k - 1].name, reason, left, tree, lock_package=lock_package, cache=cache)


def _edited_in_cache(prefix: Path, tree: Path, targets, *, linking: bool = False) -> texts.CacheCopy | None:
    """Decision 9's one reading of conda-meta: the `isabelle` record's extracted_package_dir and
    paths_data.  A file that is the same inode as the package cache's copy but no longer has the
    recorded sha256 was edited in place through the hard link; a plain reinstall keeps the edit.
    Returns the extracted_package_dir when any of `targets` is such a file.  In a post-link
    (`linking`) without an `isabelle` record, this very command is linking isabelle (conda writes
    the records after the post-links): its files came from the package cache just now, so a
    changed target of the package means the cache's copy is changed; its directory is not known
    yet (a created path in the way has no step 2 to word)."""
    meta = prefix / "conda-meta"
    if not meta.is_dir():
        return None
    for record in meta.glob("*.json"):
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("name") != "isabelle":
            continue
        extracted = Path(data.get("extracted_package_dir", ""))
        recorded = {p["_path"]: p.get("sha256") for p in data.get("paths_data", {}).get("paths", [])}
        for t in targets:
            mine, cached = tree_path(tree, t), extracted.joinpath("isa", *t.split("/"))
            sha = recorded.get("isa/" + t)
            try:
                same = sha and os.path.samefile(mine, cached)
            except OSError:
                same = False
            if same and hashlib.sha256(mine.read_bytes()).hexdigest() != sha:
                return texts.CacheCopy(extracted)
        return None
    return texts.CacheCopy(None) if linking and targets else None
