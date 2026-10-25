"""Every text of plan §4 and decision 9, and every frame a conda hook writes (a frame quotes the
refusal's own sentence, written next to its check in features.py, engine.py or api.py).  The five
texts named in plan §8 were proofread by three readers; the rest were written by the author and
read once by three readers after code review 1 (see develop.md).  `tree` is the real path of the
Isabelle tree, `$PREFIX/isa` in the plan.  A hook message gets the isabelle-patch-control prefix on
its first line from the writer in conda_hook.run (decision 9); the texts here carry none, except
`interrupted`, which the command line prints."""
from __future__ import annotations

from pathlib import Path

CHANNELS = "-c https://conda.qiyuan.me -c conda-forge"
PREFIX = "isabelle-patch-control: "
NO_FEATURES = "no feature packages installed"
CREATED = "(created by the feature)"
UPDATE_LINE = ("If you are updating or reinstalling, for example conda update --all: "
               "when it finishes, run isabelle-patch-control status.")
SAVE_LINE = ("Copy anything of your own out of {tree} and out of this environment's Isabelle user directory (isabelle getenv -b\n"
             "     ISABELLE_HOME_USER prints it; it is a directory under ~/.isabelle that belongs to this environment alone). The next step\n"
             "     replaces every file of the isabelle package and deletes this environment's Isabelle user directory: the heaps built there,\n"
             "     its etc/settings and preferences, and every component you registered by hand. Installed packages register their\n"
             "     components again; your own settings do not come back.")


def _names(names) -> str:
    return ", ".join(names)


# --- heap hints (§4)

def changed(tree: Path, applied=(), reversed=()) -> str:
    what = [] if not applied else [f"applied: {_names(applied)}"]
    what += [] if not reversed else [f"reversed: {_names(reversed)}"]
    return f"Isabelle sources under {tree} changed ({'; '.join(what)})."


HEAP_PARAGRAPH = (
    "The heaps shipped with the isabelle package were built from other sources; Isabelle rebuilds, on first use, every heap not\n"
    "built from exactly these sources, into the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER),\n"
    "under heaps/ (HOL takes several minutes). To do it now: isabelle build -b HOL")

BACK_AT_BOTTOM = (
    "The tree is back at the shipped sources. If you delete heaps/ in the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER),\n"
    "Isabelle uses the shipped heaps again instead of the rebuilt ones.")


# --- pre-unlink: success (§4, decision 9's removal/replacement rule)

def undone_at_bottom(feature: str, tree: Path) -> str:
    return (f"{feature} was undone; Isabelle sources under {tree} are back to the original.\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: you may delete heaps/ in your Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER);\n"
            "Isabelle then uses the original heaps again instead of rebuilding them on first use (several minutes).")


def undone(feature: str, tree: Path, reversed) -> str:
    return (f"{feature} was undone; Isabelle sources under {tree} changed (reversed: {_names(reversed)}).\n"
            f"{UPDATE_LINE}")


# --- chain problems (§4)

def chain_broken(package: str, version: str, directory: str, needs_package: str, needs_version: str,
                 needs_tag: str, installed: str) -> str:
    return (f"install matching versions of these packages: {package} {version} needs {needs_package} {needs_version}; "
            f"installed: {installed} (features.d/{directory} needs {needs_tag}).")


def not_pristine(tree: Path, tree_id: str, directory: str, release: str, pristine_id: str) -> str:
    return (f"run: conda update --all {CHANNELS}. {tree} is not the Isabelle build the feature packages were made for: they need "
            f"the unmodified {release} build of the isabelle package (etc/ISABELLE_ID {tree_id}; features.d/{directory} was made for "
            f"{release} pristine {pristine_id}).")


def chain_broken_removal(feature: str, package: str, error: str) -> str:
    """pre-unlink when the installed packages do not link (decision 9): the chain text, then the
    two branches; nothing was reversed."""
    return (f"{feature} was not undone: {error}\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: first install the matching versions named above, then conda remove {package}.")


# --- the hook frames for every other refusal (decision 9): what happened, then the command to run

def post_link_failed(detail: str) -> str:
    return (f"the installed Isabelle feature packages were not applied: {detail}\n"
            "When this is fixed, run: isabelle-patch-control apply")


def post_link_write_failed(detail: str, applied=None) -> str:
    """`applied` is None when the state could not be read again after the failure."""
    so_far = "" if applied is None else f"Applied so far: {_names(applied) or 'none'}. "
    return (f"the installed Isabelle feature packages were not fully applied: {detail}\n"
            f"{so_far}When this is fixed, run: isabelle-patch-control apply")


def pre_unlink_failed(feature: str, package: str, detail: str) -> str:
    return (f"{feature} could not be undone: {detail}\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: when this is fixed, run conda install {CHANNELS} {package} (this puts the package back so that\n"
            f"its changes can be undone cleanly); then conda remove {package}.")


def symlink(path: Path, tree: Path) -> str:
    return (f"{path} is or lies under a symbolic link; isabelle-patch-control replaces files in place and does not follow links\n"
            "(conda's always_softlink / allow_softlinks settings create such trees). To fix:\n"
            f"  1. {SAVE_LINE.format(tree=tree)}\n"
            "  2. conda config --set always_softlink false; conda config --set allow_softlinks false\n"
            f"  3. conda install {CHANNELS} --force-reinstall isabelle")


# --- CONFLICT (§4)

def conflict_full(feature: str, files, tree: Path, cache_dir: Path | None = None) -> str:
    """The complete diagnostic, written by the chain top's post-link.  `files` are (path, created)
    pairs; `cache_dir` is the extracted_package_dir when a file was edited in place through its
    hard link."""
    files = list(files)
    paths = [p for p, _ in files]
    created = [p for p, c in files if c]
    edited = [p for p, c in files if not c]
    lines = [f"{feature} was NOT applied: {_names(paths)} under {tree} "
             f"{'has' if len(paths) == 1 else 'have'} content the tool does not recognise",
             f"(did you edit it?). The feature packages {feature} depends on are applied; until this is fixed, the tool applies",
             f"neither {feature} nor the packages that depend on it.",
             "If you remember exactly what you changed: undo it, then run isabelle-patch-control apply. Otherwise:"]
    if edited:
        lines += [f"  1. {SAVE_LINE.format(tree=tree)}", step2(cache_dir)]
    if created:
        lines.append((f"  {'3' if edited else '1'}. {_names(created)} {'is a file' if len(created) == 1 else 'are files'} the feature "
                      f"itself creates {CREATED}: move {'it' if len(created) == 1 else 'them'} aside, then run isabelle-patch-control apply."))
    lines += ["Then run isabelle-patch-control status; Isabelle rebuilds the heaps on first use.",
              "A personal edit of a file that a feature also changes reads CONFLICT again every time; make such experiments in a separate",
              f"Isabelle installation (for example the official release), not under {tree}.",
              "Details: isabelle-patch-control status -v.  Upgrading from my-better-isabelle 0.x? See: isabelle-patch-control help"]
    return "\n".join(lines)


def step2(cache_dir: Path | None) -> str:
    if cache_dir is None:
        return f"  2. conda install {CHANNELS} --force-reinstall isabelle   (your other feature packages are re-applied automatically)"
    return (f"  2. Your edit went into conda's shared package cache, so a plain reinstall would keep it. Delete {cache_dir} (conda re-creates\n"
            f"     it from the .conda archive), then run conda install {CHANNELS} --force-reinstall isabelle in this environment and in every other\n"
            "     environment built from the same package cache (conda env list names the environments; they may share the edited file\n"
            "     without reporting anything).")


def conflict_line(feature: str, files) -> str:
    files = list(files)
    return (f"{feature} was not applied ({_names(files)} "
            f"{'has' if len(files) == 1 else 'have'} unexpected content); see isabelle-patch-control status -v")


# --- pre-unlink: the residue block (§4)

REASON_CONFLICT = "a file has unexpected content"
REASON_LOCK = "another isabelle-patch-control was running"
REASON_WRITE = "a file could not be written"


def residue(feature: str, reason: str, files, tree: Path, *, lock_package: tuple[str, str] | None = None,
            cache_dir: Path | None = None) -> str:
    """`files` are (path, created) pairs of this feature's files that still carry its changes.
    `lock_package` = (package, version) of the highest feature package replaces steps 1-3 after a
    lock timeout; `cache_dir` selects the package-cache wording of step 2."""
    lines = [f"{feature} could not be fully undone (reason: {reason}). These files under {tree}",
             "still carry its changes:"]
    lines += [f"  {path}" + (f"   {CREATED}" if created else "") for path, created in files]
    lines += [UPDATE_LINE, f"If you are removing {feature}, clean up now (nothing will remind you later):"]
    if lock_package:
        package, version = lock_package
        lines.append(f"  conda install {CHANNELS} {package}={version}; then conda remove {package}")
    else:
        lines += [f"  1. {SAVE_LINE.format(tree=tree)}", step2(cache_dir),
                  f"  3. Delete every file marked \"{CREATED}\" in these messages."]
    return "\n".join(lines)


# --- an interrupted conda command (§4; `status` prints it while conda-meta/history is missing)

def interrupted(prefix: Path) -> str:
    history = prefix / "conda-meta" / "history"
    return (f"{PREFIX}{prefix} has no conda-meta/history: a conda command was interrupted (Ctrl-C) and conda rolled it back, but\n"
            f"the changes it had already made under {prefix / 'isa'} stay, and until this is repaired every isabelle command may\n"
            "print \"### Missing Isabelle component\". To repair, either:\n"
            f"  conda create -p {prefix} {CHANNELS} <every package you want to keep, and the one that was being installed>\n"
            f"  (ls {prefix / 'conda-meta'} lists one <package>-<version>-<build>.json per installed package; conda itself will not list them now)\n"
            f"or: touch {history}   (Windows: type nul > \"{history}\"), then\n"
            f"  conda install {CHANNELS} <those same packages>\n"
            "If you do not want that feature after all: repair first, then conda remove <its package>.")


# --- the lock, write failures

def lock_busy(path: Path, seconds: float) -> str:
    s = int(seconds) if float(seconds).is_integer() else seconds
    return (f"another isabelle-patch-control run holds the lock on {path} (it may be running in another conda environment\n"
            f"that shares this package cache); gave up after {s} s. Wait for that run to finish, then retry.")


LOCK_BUSY_HOOK_TAIL = " Then run: isabelle-patch-control apply"


def write_failed(copy: Path, patch: Path, rc: int, out: str) -> str:
    return (f"git could not apply {patch} to a working copy ({copy}, exit code {rc}); nothing in the tree was changed. "
            f"Fix what git reports below (often a full disk or missing permissions), then retry. git said:\n{out}")


def os_error(e: OSError) -> str:
    """Any OSError before the first file is installed (a read-only file system, a full disk, an
    unwritable parent); `e.filename` is None for some of them."""
    where = f" ({e.filename})" if e.filename else ""
    return f"{e.strerror}{where}; nothing in the tree was changed. Fix this (for example free disk space or make the directory writable), then retry."
