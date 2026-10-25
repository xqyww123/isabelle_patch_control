"""`conda-hook post-link` and `conda-hook pre-unlink <feature>` (plan decision 9): what the hooks
of every feature package run.  Both report only through $PREFIX/.messages.txt and return 0; an
unexpected exception propagates (exit 1), and the hook text's `||` branch then speaks instead.

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

from . import api, names, texts
from .engine import tree_path
from .features import read_feature_dirs

FEATURES_D = Path("share/isabelle_patch_control/features.d")


def run(hook: str, feature: str | None, env) -> int:
    prefix = Path(env["PREFIX"])
    if hook == "post-link":
        text = post_link(prefix, env.get("PKG_NAME"))
    else:
        assert feature, "conda-hook pre-unlink <feature>"
        text = pre_unlink(prefix, feature)
    if text:
        with open(prefix / ".messages.txt", "a", encoding="utf-8") as f:
            f.write(text + "\n")
    return 0


def _features_root(prefix: Path) -> Path | None:
    root = prefix / FEATURES_D
    return root if root.is_dir() else None


def post_link(prefix: Path, pkg_name: str | None) -> str:
    tree, root = prefix / "isa", _features_root(prefix)
    try:
        res = api.apply(tree, root)
    except api.Busy as e:
        return f"{e}{texts.LOCK_BUSY_HOOK_TAIL}"
    except api.Error as e:
        return f"{texts.PREFIX}{e}"
    out = []
    if res.moves:
        out.append(texts.changed(tree, applied=res.applied) + (f"\n{texts.HEAP_PARAGRAPH}" if res.src_changed else ""))
    if res.conflicts:
        k = min(lv.patches[0].feature for lv in res.conflicts)      # the lowest feature stopped by a CONFLICT
        feature = res.before.chain[k - 1].name
        files = [lv.target for lv in res.conflicts if any(p.feature == k for p in lv.patches)]
        if _is_top(pkg_name, res.before.chain):
            out.append(texts.conflict_full(feature, files, tree, cache_dir=_edited_through_hardlink(prefix, tree, files)))
        else:
            out.append(texts.conflict_line(feature, files))
    return "\n".join(out)


def _is_top(pkg_name: str | None, chain) -> bool:
    """The hook of the chain top writes the complete diagnostic; an unset or unknown PKG_NAME counts
    as the top."""
    feature = names.feature_name(pkg_name) if pkg_name else None
    return feature not in {fd.name for fd in chain} or feature == chain[-1].name


def pre_unlink(prefix: Path, feature: str) -> str:
    tree, root = prefix / "isa", _features_root(prefix)
    try:
        res = api.unapply(tree, root, feature=feature)
    except api.Busy:
        return _residue_without_lock(prefix, tree, root, feature)
    except api.ChainBroken as e:
        return _residue_chain_broken(prefix, tree, root, feature, e)
    except api.WriteFailed:
        return _residue_from_status(prefix, tree, api.status(tree, root), feature, texts.REASON_WRITE)
    except api.Error as e:
        return f"{texts.PREFIX}{e}"
    k = res.before.number(feature)
    left = [(t, res.before.levels[t].created_by(k)) for t in res.before.features[k - 1].files
            if (after := res.level_after(t)) is None or after >= k]
    if left:
        return texts.residue(feature, texts.REASON_CONFLICT, left, tree,
                             cache_dir=_edited_through_hardlink(prefix, tree, [t for t, _ in left]))
    if res.moves:
        return texts.undone_at_bottom(feature, tree) if res.at_bottom else texts.undone(feature, tree, res.reversed)
    return ""


def _residue_without_lock(prefix, tree, root, feature) -> str:
    """After a lock timeout: levels computed without the lock, in a temporary directory; the
    recovery is one line naming the highest feature package."""
    try:
        st = api.status(tree, root, lock=False)
    except api.ChainBroken as e:
        return _residue_chain_broken(prefix, tree, root, feature, e)
    except api.Error as e:
        return f"{texts.PREFIX}{e}"
    top = st.chain[-1]
    return _residue_from_status(prefix, tree, st, feature, texts.REASON_LOCK, lock_package=(top.package, top.version))


def _residue_from_status(prefix, tree, st: api.Status, feature, reason, **kw) -> str:
    k = st.number(feature)
    left = [(t, st.levels[t].created_by(k)) for t in st.features[k - 1].files
            if (lv := st.levels[t].level) is None or lv >= k]
    if not left:
        return ""
    cache = None if kw.get("lock_package") else _edited_through_hardlink(prefix, tree, [t for t, _ in left])
    return texts.residue(feature, reason, left, tree, cache_dir=cache, **kw)


def _residue_chain_broken(prefix, tree, root, feature, error) -> str:
    """The chain does not link, so levels are relative to this feature alone: a file whose copy
    does not take the feature's patch forward still carries its change (or is unrecognised)."""
    own = [fd for fd in (read_feature_dirs(root) if root else []) if fd.name == feature]
    if not own:
        return f"{texts.PREFIX}{error}"
    levels = api.single_feature_levels(tree, own[0].dir)
    left = [(t, lv.created_by(1)) for t, lv in sorted(levels.items()) if lv.level != 0]
    if not left:
        return ""
    return texts.residue(feature, texts.REASON_CHAIN, left, tree,
                         cache_dir=_edited_through_hardlink(prefix, tree, [t for t, _ in left]))


def _edited_through_hardlink(prefix: Path, tree: Path, targets) -> Path | None:
    """Decision 9's one reading of conda-meta: the `isabelle` record's extracted_package_dir and
    paths_data.  A file that is the same inode as the package cache's copy but no longer has the
    recorded sha256 was edited in place through the hard link; a plain reinstall keeps the edit.
    Returns the extracted_package_dir when any of `targets` is such a file."""
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
                return extracted
        return None
    return None
