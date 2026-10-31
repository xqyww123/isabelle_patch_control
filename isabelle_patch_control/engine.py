"""The engine (plan decisions 4-6): the one function that starts git outside the developer
subcommands, the lock on the tree, the work directory, the per-file replay that gives a file its
level, and the writes into the tree.

git runs only inside a directory this module created (the staging directory or a temporary one),
never in the tree and never in the caller's current directory.  The tree is changed only by
os.replace and os.unlink, one file at a time.
"""
from __future__ import annotations

import errno
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from . import texts
from .errors import Busy, NotFound, Refused, WriteFailed

LOCK_FILE = "etc/ISABELLE_ID"          # an existing file of every tree; locked, never created
LOCK_TIMEOUT = 60.0
LOCK_OFFSET = 0x40000000               # Windows: one byte no reader of the file ever reaches
MIN_GIT = (2, 43)
WINDOWS = os.name == "nt"


# --- git

class Git:
    """Locates git and runs it; outside the developer subcommands, `run` is the only place in the
    tool that starts git."""

    def __init__(self):
        own = Path(sys.prefix) / ("Library/bin/git.exe" if WINDOWS else "bin/git")
        self.exe = str(own) if own.is_file() else shutil.which("git")
        if not self.exe:
            raise NotFound("git not found: isabelle-patch-control needs git >= %d.%d" % MIN_GIT)
        with tempfile.TemporaryDirectory(prefix="isabelle-patch-control-") as tmp:
            out = self.run(Path(tmp), "--version").stdout.decode(errors="replace")
        m = re.search(r"(\d+)\.(\d+)", out)
        if not m or (int(m[1]), int(m[2])) < MIN_GIT:
            raise NotFound(f"{self.exe} is {out.strip() or 'of unknown version'}; "
                           "isabelle-patch-control needs git >= %d.%d" % MIN_GIT)

    def run(self, workdir: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        """git with a whitelisted environment and fixed configuration, in `workdir` (decision 4):
        no system/global/XDG config, no attributes, no repository above the work directory."""
        env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "TEMP", "TMP") if k in os.environ}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM="1", LC_ALL="C",
                   GIT_CEILING_DIRECTORIES=str(Path(os.path.realpath(workdir)).parent))
        cmd = [self.exe, "-c", "core.autocrlf=false", "-c", f"core.attributesFile={os.devnull}"]
        if WINDOWS:
            cmd += ["-c", "core.longpaths=true"]
        return subprocess.run([*cmd, *args], cwd=workdir, env=env, capture_output=True,
                              stdin=subprocess.DEVNULL, umask=-1 if WINDOWS else 0o022)


# --- the lock on the tree

@contextmanager
def locked(tree: Path, exclusive: bool):
    """Hold the lock on tree/etc/ISABELLE_ID: shared for reading, exclusive for writing; Busy
    after LOCK_TIMEOUT seconds (read when called, so tests can shorten it)."""
    path = tree / LOCK_FILE
    with open(path, "r+b" if exclusive else "rb") as f:
        deadline = time.monotonic() + LOCK_TIMEOUT
        while not _try_lock(f, exclusive):
            if time.monotonic() >= deadline:
                raise Busy(texts.lock_busy(path, LOCK_TIMEOUT))
            time.sleep(0.05)
        try:
            yield
        finally:
            _unlock(f)


def _try_lock(f, exclusive: bool) -> bool:
    if WINDOWS:
        import msvcrt
        f.seek(LOCK_OFFSET)
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EDEADLK):
                return False
            raise
    import fcntl
    try:
        fcntl.flock(f, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _unlock(f):
    if WINDOWS:
        import msvcrt
        f.seek(LOCK_OFFSET)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)


# --- work directories

@contextmanager
def staging_dir(tree: Path):
    """`<realpath(tree)>.staging`, used only by the run that holds the exclusive lock (decision 5):
    same file system as the tree, emptied first, removed at the end."""
    d = Path(os.path.realpath(tree) + ".staging")
    if d.is_dir() and not d.is_symlink():
        _remove_tree(d)
    elif d.exists() or d.is_symlink():
        d.unlink()
    d.mkdir()
    try:
        yield d
    finally:
        _remove_tree(d, best_effort=True)


@contextmanager
def temp_dir(near: Path | None = None):
    """A fresh temporary directory for every other git call; `near` puts it next to a directory the
    tool writes into without a lock (the directory interface, decision 8)."""
    d = Path(tempfile.mkdtemp(prefix="isabelle-patch-control-", dir=near))
    try:
        yield d
    finally:
        _remove_tree(d, best_effort=True)


def _remove_tree(d: Path, *, best_effort: bool = False):
    """shutil.rmtree that also removes read-only files, which Windows refuses to delete: the copy of
    a read-only target in the staging directory is one (install keeps the target's mode)."""
    def writable(remove, path, _):
        os.chmod(path, stat.S_IWRITE)
        remove(path)
    try:
        shutil.rmtree(d, onexc=writable)
    except OSError:
        if not best_effort:
            raise


# --- patches and levels

@dataclass(frozen=True)
class PatchFile:
    """One patch file of one feature: it changes exactly one path of the tree."""
    feature: int                    # the feature's number in the chain, 1-based
    path: Path                      # the .patch file
    target: str                     # tree-relative, '/'-separated
    creates: bool
    deletes: bool
    mode: int | None                # permission bits in the create/delete line


def tree_path(tree: Path, target: str) -> Path:
    return tree.joinpath(*target.split("/"))


@dataclass
class Levels:
    """What replaying a file's patches says about it (decision 6).

    `tables[L]` exists for every level L the file matches; it maps every candidate level to the
    file's content at that level (None = the file does not exist), computed while checking L.
    Exactly one match is the file's level; none or several is CONFLICT."""
    target: str
    patches: tuple[PatchFile, ...]            # ascending by feature
    tables: dict[int, dict[int, bytes | None]] = field(default_factory=dict)
    failures: dict[int, str] = field(default_factory=dict)   # rejected level -> git's complaint

    @property
    def candidates(self) -> tuple[int, ...]:
        return (0, *(p.feature for p in self.patches))

    @property
    def level(self) -> int | None:
        return next(iter(self.tables)) if len(self.tables) == 1 else None

    def content_at(self, level: int) -> bytes | None:
        assert self.level is not None, "a CONFLICT file has no content table"
        return self.tables[self.level][level]

    @property
    def created(self) -> bool:
        """The file is not in the isabelle package: a feature creates it, so a reinstall of isabelle
        does not touch it."""
        return self.patches[0].creates

    def mode_at(self, level: int) -> int | None:
        """The permission bits a file that does not exist in the tree gets at `level`: from the
        patch that creates it, else from the patch that deletes it (mode changes are never
        released, so every patch that mentions the mode agrees)."""
        for p in reversed(self.patches):
            if p.feature <= level and p.creates:
                return p.mode
        for p in self.patches:
            if p.feature > level and p.deletes:
                return p.mode
        return None


class Replayer:
    """Replays patches on single-file copies inside `workdir` and installs the results."""

    def __init__(self, git: Git, workdir: Path):
        self.git = git
        self.workdir = workdir

    def read_target(self, patch: Path, feature: int) -> PatchFile:
        """`git apply --numstat --summary`: the one path the patch changes, and whether it creates
        or deletes the file (decision 3)."""
        patch = Path(os.path.abspath(patch))                 # git runs in the work directory
        r = self.git.run(self.workdir, "apply", "--numstat", "--summary", str(patch))
        out = (r.stdout + r.stderr).decode(errors="replace")
        if r.returncode:
            raise Refused(f"{patch}: git cannot read this patch file:\n{out.rstrip()}")
        targets, creates, deletes, mode = [], False, False, None
        for line in out.splitlines():
            if m := re.fullmatch(r"(?:\d+|-)\t(?:\d+|-)\t(.+)", line):
                targets.append(m[1])
            elif m := re.fullmatch(r" (create|delete) mode (\d+) .+", line):
                creates, deletes = m[1] == "create", m[1] == "delete"
                mode = 0o755 if m[2].endswith("755") else 0o644
        if len(targets) != 1:
            raise Refused(f"{patch}: a patch file changes exactly one path; this one changes "
                          f"{len(targets)} ({', '.join(targets) or 'none'})")
        return PatchFile(feature, patch, targets[0], creates, deletes, mode)

    def levels(self, target: str, content: bytes | None, patches: list[PatchFile]) -> Levels:
        """Decision 6: the file is at level L when reversing the patches <= L (descending) and
        forward-applying the patches > L (ascending) both succeed, each chain replayed step by
        step on its own copy starting from the file's current content."""
        lv = Levels(target, tuple(sorted(patches, key=lambda p: p.feature)))
        cands = lv.candidates
        for L in cands:
            table = {L: content}
            below = [p for p in lv.patches if p.feature <= L]
            above = [p for p in lv.patches if p.feature > L]
            ok, cur = True, content
            for p in reversed(below):
                rc, out, cur = self._step(target, cur, p, reverse=True)
                if rc:
                    ok, lv.failures[L] = False, out
                    break
                table[cands[cands.index(p.feature) - 1]] = cur
            cur = content
            for p in above if ok else []:
                rc, out, cur = self._step(target, cur, p, reverse=False)
                if rc:
                    ok, lv.failures[L] = False, out
                    break
                table[p.feature] = cur
            if ok:
                lv.tables[L] = table
        return lv

    def _step(self, target: str, content: bytes | None, patch: PatchFile, reverse: bool):
        """One `git apply [-R]` on the copy; rc 1 is "does not apply", anything else non-zero is
        a write failure (decision 4): the copy is the tool's own, so only a mismatch can be 1."""
        copy = self._copy(target, content)
        r = self.git.run(self.workdir, "apply", *(["-R"] if reverse else []), "--whitespace=nowarn", str(patch.path))
        if r.returncode == 0:
            return 0, "", copy.read_bytes() if copy.exists() else None
        out = (r.stderr or r.stdout).decode(errors="replace").rstrip()
        if r.returncode == 1:
            return 1, out, None
        raise WriteFailed(texts.write_failed(copy, patch.path, r.returncode, out))

    def _copy(self, target: str, content: bytes | None) -> Path:
        copy = tree_path(self.workdir, target)
        copy.parent.mkdir(parents=True, exist_ok=True)   # git removes directories it emptied
        if content is None:
            copy.unlink(missing_ok=True)
        else:
            copy.write_bytes(content)
        return copy

    def install(self, tree: Path, lv: Levels, level: int):
        """Move the file to `level` (decision 5): the content computed by the replay, written in
        the work directory with its permission bits set, then one os.replace; or one os.unlink."""
        dest = tree_path(tree, lv.target)
        content = lv.content_at(level)
        if content is None:
            _retry(os.unlink, dest)
            _remove_empty_parents(dest.parent, tree)
            return
        mode = dest.stat().st_mode & 0o7777 if dest.exists() else lv.mode_at(level) or 0o644
        src = self._copy(lv.target, content)
        os.chmod(src, mode)
        dest.parent.mkdir(parents=True, exist_ok=True)
        _retry(os.replace, src, dest)


def _retry(fn, *args):
    """Windows holds files open behind the tool's back; retry like conda does (about 6 s)."""
    delays = (0.1, 0.2, 0.4, 0.8, 1.6, 3.2) if WINDOWS else ()
    for delay in delays:
        try:
            return fn(*args)
        except PermissionError:
            time.sleep(delay)
    return fn(*args)


def _remove_empty_parents(d: Path, stop: Path):
    while d != stop and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent
