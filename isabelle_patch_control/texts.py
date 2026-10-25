"""Every user-visible text, word for word from plan §4 and decision 9 (proofread by three readers;
do not reword here).  `tree` is the real path of the Isabelle tree, `$PREFIX/isa` in the plan."""
from __future__ import annotations

from pathlib import Path

CHANNELS = "-c https://conda.qiyuan.me -c conda-forge"
PREFIX = "isabelle-patch-control: "
NO_FEATURES = "no feature packages installed"
CREATED = "(created by the feature)"
UPDATE_LINE = ("If you are updating or reinstalling, for example conda update --all: "
               "when it finishes, run isabelle-patch-control status.")


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
    "The tree is back at the shipped sources. Delete heaps/ in the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER)\n"
    "and the shipped heaps are used again.")


# --- pre-unlink: success (§4, decision 9's removal/replacement rule)

def undone_at_bottom(feature: str, tree: Path) -> str:
    return (f"{PREFIX}{feature} was undone; Isabelle sources under {tree} are back to the original.\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: you may delete heaps/ in your Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER);\n"
            "Isabelle then uses the original heaps again instead of rebuilding them on first use (several minutes).")


def undone(feature: str, tree: Path, reversed) -> str:
    return (f"{PREFIX}{feature} was undone; Isabelle sources under {tree} changed (reversed: {_names(reversed)}).\n"
            f"{UPDATE_LINE}")


# --- chain problems (§4)

def chain_broken(package: str, version: str, directory: str, needs_package: str, needs_version: str,
                 needs_tag: str, installed: str) -> str:
    return (f"feature chain broken: {package} {version} (features.d/{directory}) needs {needs_package} {needs_version} "
            f"({needs_tag}); installed: {installed}. Install matching versions of these packages.")


def not_pristine(tree: Path, tree_id: str, directory: str, release: str, pristine_id: str) -> str:
    return (f"{tree} has etc/ISABELLE_ID {tree_id}, but features.d/{directory} was made for {release} pristine {pristine_id}. "
            f"Feature packages exist only for the pristine isabelle build. Run: conda update --all {CHANNELS}")


# --- CONFLICT (§4)

def conflict_full(feature: str, files, tree: Path, cache_dir: Path | None = None) -> str:
    """The complete diagnostic, written by the chain top's post-link.  `cache_dir` is the
    extracted_package_dir when the file was edited in place through its hard link."""
    files = list(files)
    head = (f"{PREFIX}{feature} was NOT applied: {_names(files)} under {tree} "
            f"{'has' if len(files) == 1 else 'have'} content the tool does not recognise\n"
            f"(did you edit it?). The feature packages {feature} depends on are applied; {feature} and the packages that depend on it are not.\n"
            "To fix:\n"
            f"  1. Save any edits of your own under {tree} and in your Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER):\n"
            "     the next step replaces every file of the isabelle package and deletes that directory. Installed packages re-register\n"
            "     themselves; your own settings and manual \"isabelle components -u\" entries do not come back.\n")
    tail = (f"If the unrecognised file is one the feature itself creates (marked \"{CREATED}\" in isabelle-patch-control status -v):\n"
            "move it aside, then run isabelle-patch-control apply.\n"
            "Details: isabelle-patch-control status -v.  Upgrading from my-better-isabelle 0.x? See: isabelle-patch-control help")
    return head + step2(cache_dir) + "\n" + tail


def step2(cache_dir: Path | None) -> str:
    if cache_dir is None:
        return f"  2. conda install {CHANNELS} --force-reinstall isabelle"
    return (f"  2. Your edit went into conda's shared package cache, so a plain reinstall would keep it. Delete {cache_dir} (conda re-creates\n"
            f"     it from the .conda archive), then run conda install {CHANNELS} --force-reinstall isabelle in this environment and in every other environment\n"
            "     that uses the same package cache (they may share the edited file without reporting anything).")


def conflict_line(feature: str, files) -> str:
    files = list(files)
    return (f"{PREFIX}{feature} was not applied ({_names(files)} "
            f"{'has' if len(files) == 1 else 'have'} unexpected content); see isabelle-patch-control status -v")


# --- pre-unlink: the residue block (§4)

REASON_CONFLICT = "a file has unexpected content"
REASON_LOCK = "another isabelle-patch-control was running"
REASON_CHAIN = "a feature package it needs is missing or has the wrong version"
REASON_WRITE = "a file could not be written"


def residue(feature: str, reason: str, files, tree: Path, *, lock_package: tuple[str, str] | None = None,
            cache_dir: Path | None = None) -> str:
    """`files` are (path, created) pairs of this feature's files that still carry its changes.
    `lock_package` = (package, version) of the highest feature package replaces steps 1-3 after a
    lock timeout; `cache_dir` selects the package-cache wording of step 2."""
    lines = [f"{PREFIX}{feature} could not be fully undone (reason: {reason}). These files under {tree}",
             "still carry its changes:"]
    lines += [f"  {path}" + (f"   {CREATED}" if created else "") for path, created in files]
    lines += [UPDATE_LINE, f"If you are removing {feature}, clean up now (nothing will remind you later):"]
    if lock_package:
        package, version = lock_package
        lines.append(f"  conda install {CHANNELS} {package}={version}; then conda remove {package}")
    else:
        lines += [f"  1. Save any edits of your own under {tree} and in your Isabelle user directory: the next step deletes both.",
                  step2(cache_dir) + ("   (your other feature packages are re-applied automatically)" if cache_dir is None else ""),
                  f"  3. Delete every file marked \"{CREATED}\" in these messages."]
    return "\n".join(lines)


# --- an interrupted conda command (§4; `status` prints it while conda-meta/history is missing)

def interrupted(prefix: Path) -> str:
    return (f"{PREFIX}{prefix} has no conda-meta/history: a conda command was interrupted (Ctrl-C) and conda rolled it back, but\n"
            f"the changes it had already made under {prefix / 'isa'} stay, and until this is repaired every isabelle command may\n"
            "print \"### Missing Isabelle component\". To repair, either:\n"
            f"  conda create -p {prefix} {CHANNELS} <every package you want to keep, and the one that was being installed>\n"
            f"or: touch {prefix / 'conda-meta' / 'history'}   (Windows: type nul > \"%PREFIX%\\conda-meta\\history\"), then\n"
            f"  conda install {CHANNELS} <those same packages>\n"
            "If you do not want that feature after all: repair first, then conda remove <its package>.")


# --- the lock, write failures

def lock_busy(path: Path, seconds: float) -> str:
    s = int(seconds) if float(seconds).is_integer() else seconds
    return (f"another isabelle-patch-control run holds the lock on {path} (its inode may be shared with another conda\n"
            f"environment on this machine); gave up after {s} s. Retry later.")


LOCK_BUSY_HOOK_TAIL = " Then run: isabelle-patch-control apply"


def write_failed(copy: Path, patch: Path, rc: int, out: str) -> str:
    return (f"git could not finish writing the copy {copy} while replaying {patch} (exit code {rc}); "
            f"nothing in the tree was changed. git said:\n{out}")
