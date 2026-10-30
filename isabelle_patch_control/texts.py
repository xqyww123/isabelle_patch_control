"""Every text of plan §4 and decision 9, and every frame a conda hook writes (a frame quotes the
refusal's own sentence, written next to its check in features.py, engine.py or api.py); how they
are written: develop.md.  `tree` is the real path of the Isabelle tree, `$PREFIX/isa` in the plan.
A hook message gets the isabelle-patch-control prefix on its first line from the writer in
conda_hook.run (decision 9); the texts here carry none."""
from __future__ import annotations

import os
import shlex
from pathlib import Path

CHANNELS = "-c https://conda.qiyuan.me -c conda-forge"
PREFIX = "isabelle-patch-control: "
TOOL = "isabelle-patch-control"
APPLY = f"{TOOL} apply"
NO_FEATURES = "No feature packages are installed, so there is nothing to apply."
CREATED = "(created by a feature)"
UPDATE_LINE = ("If you are updating or reinstalling, for example conda update --all: "
               "when it finishes, run isabelle-patch-control status.")


def quoted(path: Path) -> str:
    """A path as the user's shell takes it: cmd.exe and PowerShell on Windows, a POSIX shell elsewhere."""
    return (f'"{path}"' if " " in str(path) else str(path)) if os.name == "nt" else shlex.quote(str(path))


def reinstall(tree: Path) -> str:
    """The reinstall of every repair (the tree of an environment is <prefix>/isa, decision 2).  Every
    conda command a message gives names the environment with -p: run while another environment is
    active, it would act on that one (this one would delete its Isabelle user directory)."""
    return f"conda install -p {quoted(tree.parent)} {CHANNELS} --force-reinstall isabelle"


def reinstall_steps(tree: Path, lead: str) -> str:
    """The one repair of the sources (plan §0 item 41): `lead`, which ends in "reinstall the isabelle
    package.", on its own line, then what the reinstall deletes, then the command.  Messages break
    lines only between sentences and before a command."""
    return (f"{lead}\n"
            "This deletes this environment's Isabelle user directory (the heaps built there, your settings and preferences, "
            "and components you registered by hand); copy out anything you want to keep first "
            "(isabelle getenv -b ISABELLE_HOME_USER shows where it is).\n"
            f"Then run:\n  {reinstall(tree)}\n"
            "The installed feature packages are applied again, and Isabelle rebuilds the heaps on first use.")


def _names(names) -> str:
    return ", ".join(names)


def _and(names) -> str:
    """`a`, `a and b`, `a, b and c`: the names inside a sentence."""
    names = list(names)
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


# --- status (§4, decision 6): one sentence per feature (plan §0 item 41)

ALL_APPLIED = "Everything is in order."
IS_APPLIED, IS_NOT_APPLIED, IS_HALF, IS_CONFLICT = "is applied", "is not applied yet", "is only partly applied", "cannot be applied"
CANNOT_UNDO = "cannot be undone"
WOULD_CHANGE, NOTHING_WOULD_CHANGE, CHANGED_FILES = "These files would change:", "Nothing would change.", "These files changed:"


def checked(tree: Path, n: int) -> str:
    return f"Checked the Isabelle sources in {tree} against {n} feature package{'s' if n != 1 else ''}."


def read_from(root: Path) -> str:
    return f"The feature packages' patches are read from {root}."


def sentence(name: str, phrase: str, detail: str = "") -> str:
    """The frame of every feature sentence; read_sentence reads it back."""
    return f"Feature `{name}` {phrase}{detail}."


def read_sentence(line: str) -> tuple[str, str] | None:
    """(name, the rest after the name and a space) of a line `sentence` wrote, else None."""
    if line.startswith("Feature `") and "` " in line:
        name, rest = line[len("Feature `"):].split("` ", 1)
        return name, rest
    return None


def applied(name: str, not_below=()) -> str:
    """`not_below`: the features below it that are not applied."""
    if not not_below:
        return sentence(name, IS_APPLIED)
    return sentence(name, IS_APPLIED, f", but {_and(f'`{f}`' for f in not_below)} below it {'is' if len(not_below) == 1 else 'are'} not")


def not_applied(name: str) -> str:
    return sentence(name, IS_NOT_APPLIED)


def half_applied(name: str, below: int, files: int) -> str:
    return sentence(name, IS_HALF, f": {below} of its {files} files {'does' if below == 1 else 'do'} not have the feature's changes yet")


def conflict(name: str, files, phrase: str = IS_CONFLICT) -> str:
    """`phrase` is CANNOT_UNDO after `unapply`."""
    files = list(files)
    return sentence(name, phrase, f": {_and(files)} {'was' if len(files) == 1 else 'were'} changed by something other than "
                                 "the installed feature packages")


def in_order(feature: str | None) -> str:
    """The last line when everything asked about is applied; with --feature F only F and the
    features below it were asked about."""
    return f"Everything up to `{feature}` is in order." if feature else ALL_APPLIED


def missing(feature: str | None, tool: str = TOOL) -> str:
    """`tool`: the command as the user ran it (with --isabelle-home / --features-dir), so that the
    command given reaches the same tree."""
    return f"To apply what is missing, run: {tool} apply" + (f" --feature {feature}" if feature else "")


def conflict_fix(tree: Path, files, *, conda: bool, tool: str = TOOL) -> str:
    """After the feature sentences, when one cannot be applied.  `files` are (path, created) pairs of
    the files no level fits; a created one is not in the isabelle package, so a reinstall of isabelle
    does not touch it and it is deleted first.  `conda`: the tree is a conda environment's."""
    files = list(files)
    edited = [str(tree / p) for p, c in files if not c]
    created = [p for p, c in files if c]
    delete = f"delete {_and(str(tree / p) for p in created)} {CREATED}" if created else ""
    if edited and conda:
        first = f"first {delete}; then " if created else ""
        return reinstall_steps(tree, "This usually means a conda command was interrupted halfway. "
                                     f"To fix it, {first}reinstall the isabelle package.")
    if edited:
        return f"Restore {_and(edited)} to the original Isabelle sources{f' and {delete}' if created else ''}, then run: {tool} apply"
    return f"To fix it, {delete}, then run: {tool} apply"


# --- heap hints (§4)

def changed(tree: Path, applied=(), undone=()) -> str:
    what = [] if not applied else [f"applied: {_names(applied)}"]
    what += [] if not undone else [f"undone: {_names(undone)}"]
    return f"Isabelle sources under {tree} changed ({'; '.join(what)})."


HEAP_PARAGRAPH = (
    "Isabelle rebuilds its heaps from the changed sources on first use (HOL takes several minutes).\n"
    "To do it now, run: isabelle build -b HOL")

ORIGINAL_HEAPS = ("you may delete heaps/ in this environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER); "
                  "Isabelle then uses the original heaps again instead of rebuilding them on first use (several minutes).")

BACK_AT_BOTTOM = f"The sources are back to the original: {ORIGINAL_HEAPS}"


# --- pre-unlink: success (§4, decision 9's removal/replacement rule)

def undone_at_bottom(feature: str, tree: Path) -> str:
    return (f"{feature} was undone; Isabelle sources under {tree} are back to the original.\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: {ORIGINAL_HEAPS}")


def undone(feature: str, tree: Path, features) -> str:
    """`features`: every feature this run undid, the removed one and those above it."""
    with_it = [f for f in features if f != feature]
    return (f"{feature} was undone in the Isabelle sources under {tree}"
            f"{f', and with it {_and(with_it)}' if with_it else ''}.\n"
            f"{UPDATE_LINE}")


# --- chain problems (§4)

def chain_broken(package: str, version: str, needs_package: str, needs_version: str, installed: str | None) -> str:
    """`installed`: the versions of `needs_package` that are installed, or None."""
    have = f"but {installed} is installed" if installed else "which is not installed"
    return f"{package} {version} needs {needs_package} {needs_version}, {have}. Install matching versions of these packages."


def not_pristine(tree: Path, tree_id: str, directory: str, release: str, pristine_id: str) -> str:
    return (f"{tree} is not the Isabelle build the feature packages were made for: they need the unmodified {release} build of "
            f"the isabelle package (this tree has etc/ISABELLE_ID {tree_id}; features.d/{directory} was made for {release} pristine "
            f"{pristine_id}). To fix it, run: conda update -p {quoted(tree.parent)} --all {CHANNELS}")


def chain_broken_removal(feature: str, package: str, error: str, tree: Path) -> str:
    """pre-unlink when the installed packages do not link or the tree is another build (decision 9):
    the refusal, then the two branches; nothing was reversed."""
    return (f"{feature} was not undone: {error}\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: first do what the first line says, then run:\n"
            f"  conda remove -p {quoted(tree.parent)} {package}")


# --- the hook frames for every other refusal (decision 9): what happened, then the command to run

def post_link_failed(detail: str) -> str:
    """Most of these refusals are fixed by a conda command that applies the features by itself
    (another build, a broken chain, a symbolic link), so the frame sends the user to `status`."""
    return (f"the installed Isabelle feature packages were not applied: {detail}\n"
            f"When this is fixed, run: {TOOL} status")


def post_link_write_failed(detail: str, applied=None) -> str:
    """`applied` is None when the state could not be read again after the failure."""
    already = "" if applied is None else f"Already applied: {_names(applied) or 'none'}. "
    return (f"the installed Isabelle feature packages were not fully applied: {detail}\n"
            f"{already}When this is fixed, run: {APPLY}")


def pre_unlink_failed(feature: str, package: str, detail: str, tree: Path) -> str:
    prefix = quoted(tree.parent)
    return (f"{feature} could not be undone: {detail}\n"
            f"{UPDATE_LINE}\n"
            f"If you are removing {feature}: when this is fixed, put the package back and remove it again, so that its "
            "changes are undone cleanly:\n"
            f"  conda install -p {prefix} {CHANNELS} {package}\n"
            f"  conda remove -p {prefix} {package}")


def symlink(path: Path, tree: Path) -> str:
    return (f"{path} is a symbolic link or lies under one, which isabelle-patch-control cannot change (conda's always_softlink "
            "and allow_softlinks settings create them). To fix it, run:\n"
            "  conda config --set always_softlink false\n"
            "  conda config --set allow_softlinks false\n"
            + reinstall_steps(tree, "and reinstall the isabelle package."))


# --- CONFLICT in a hook (§4): the status sentence and the same repair

def stopped(feature: str) -> str:
    return f"Until this is fixed, the tool does not apply {feature} or the feature packages that depend on it."


def conflict_full(feature: str, files, tree: Path) -> str:
    """The complete diagnostic, written by the chain top's post-link.  `files` are (path, created) pairs."""
    files = list(files)
    return "\n".join([conflict(feature, [p for p, _ in files]), stopped(feature), conflict_fix(tree, files, conda=True),
                      "Upgrading from my-better-isabelle 0.x? See: isabelle-patch-control help"])


def conflict_line(feature: str, files, phrase: str = IS_CONFLICT, tool: str = TOOL) -> str:
    return f"{conflict(feature, files, phrase)} Run {tool} status for what to do."


# --- pre-unlink: the residue block (§4)

REASON_CONFLICT = "a file was changed by something other than the installed feature packages"
REASON_LOCK = "another isabelle-patch-control was running"
REASON_WRITE = "a file could not be written"


def residue(feature: str, reason: str, files, tree: Path, *, lock_package: tuple[str, str] | None = None) -> str:
    """`files` are (path, created) pairs of this feature's files that still carry its changes.
    `lock_package` = (package, version) of the highest feature package replaces the reinstall after a
    lock timeout."""
    files = list(files)
    lines = [f"{feature} could not be fully undone (reason: {reason}).",
             f"These files under {tree} still carry its changes:"]
    lines += [f"  {path}" + (f"   {CREATED}" if created else "") for path, created in files]
    removing = f"If you are removing {feature}, clean up now (nothing will remind you later)"
    if lock_package:
        package, version = lock_package
        prefix = quoted(tree.parent)
        lines += [UPDATE_LINE, f"{removing}, run:", f"  conda install -p {prefix} {CHANNELS} {package}={version}",
                  f"  conda remove -p {prefix} {package}"]
        return "\n".join(lines)
    steps = ["fix what stopped the write (for example, free disk space)"] if reason == REASON_WRITE else []
    steps += [f"delete every file marked \"{CREATED}\" in these messages"] if any(c for _, c in files) else []
    if all(c for _, c in files):                              # conda removes the tool with the last feature package
        last = f"run: {APPLY} (if that command is no longer found, no feature package is left and you are done)"
        lines += [UPDATE_LINE, f"{removing}: {_steps(steps + [last])}"]
    else:
        lines += [UPDATE_LINE, reinstall_steps(tree, f"{removing}: {_steps(steps + ['reinstall the isabelle package.'])}")]
    return "\n".join(lines)


def _steps(steps: list[str]) -> str:
    """`a`, `first a; then b`, `first a; then b; then c`."""
    return steps[0] if len(steps) == 1 else "first " + "; then ".join(steps)


# --- the lock, write failures

def lock_busy(path: Path, seconds: float, then: str = "retry") -> str:
    """`then` is what to do once the other run finished: a hook cannot be retried, so it says apply."""
    s = int(seconds) if float(seconds).is_integer() else seconds
    return (f"another isabelle-patch-control run holds the lock on {path} (perhaps a run in another conda environment that "
            f"shares this package cache); gave up after {s} s. Wait for that run to finish, then {then}.")


def write_failed(copy: Path, patch: Path, rc: int, out: str) -> str:
    """The next step is the caller's: the command line is retried, a hook's frame says apply."""
    return (f"git could not apply {patch} to a working copy ({copy}, exit code {rc}); nothing in the tree was changed. "
            f"Fix what git reports below (often a full disk or missing permissions). git said:\n{out}")


def os_error(e: OSError) -> str:
    """Any OSError before the first file is installed (a read-only file system, a full disk, an
    unwritable parent); `e.filename` is None for some of them."""
    where = f" ({e.filename})" if e.filename else ""
    return f"{e.strerror}{where}; nothing in the tree was changed. Fix this (for example free disk space or make the directory writable)."
