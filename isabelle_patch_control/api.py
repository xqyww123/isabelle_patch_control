"""The public Python API (plan decision 8): the functions the command line runs.  They return
result objects or raise `errors.Error`; nothing here exits.

status(), apply() and unapply() work on a tree and a `features.d` root; apply_to() and
unapply_from() are the directory interface: one directory, one feature directory, no lock, no
provenance.  All of them share one path: link the installed features, lock, read every patch's
target, replay every touched file to find its level, and (for the writing commands) move files to
their target levels one os.replace at a time.
"""
from __future__ import annotations

import functools
import os
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path

from . import model, texts
from .engine import Git, Level, Levels, Replayer, locked, staging_dir, temp_dir, tree_path
from .errors import Busy, ChainBroken, Error, NotFound, Refused, WriteFailed  # noqa: F401  (re-exported)
from .features import FeatureDir, Tree, below, feature_number, link, read_feature_dirs

__all__ = ["status", "apply", "unapply", "apply_to", "unapply_from", "Status", "Moves",
           "Error", "NotFound", "Refused", "ChainBroken", "Busy", "WriteFailed"]


@dataclass
class Status:
    tree: Path
    installed: list[FeatureDir]                                      # in the environment's order
    below: dict[int, frozenset[int]] = field(default_factory=dict)  # feature number -> the numbers below it
    levels: dict[str, Levels] = field(default_factory=dict)        # target -> levels
    features: list[model.FeatureState] = field(default_factory=list)
    selected: int | None = None                                      # --feature F's number

    def above(self, k: int) -> frozenset[int]:
        return model.above(self.below, [k])

    def asked(self, up: bool = True) -> list[model.FeatureState]:
        """The features a command was asked about: all, or with --feature F, F and the features below
        it (status, apply) or above it (unapply)."""
        if self.selected is None:
            return self.features
        k = self.selected
        near = self.below[k] if up else self.above(k)
        return [s for s in self.features if s.number == k or s.number in near]

    @property
    def exit_code(self) -> int:
        """0 when the features asked about are applied."""
        return 0 if all(s.state == model.APPLIED for s in self.asked()) else 1


@dataclass
class Moves:
    """What apply/unapply did (or, with dry_run, would do)."""
    before: Status
    moves: list[model.Move]
    conflicts: list[Levels]            # CONFLICT files in the command's way
    dry_run: bool
    up: bool                           # apply, not unapply

    def level_after(self, target: str) -> Level | None:
        for m in self.moves:
            if m.levels.target == target:
                return m.target
        return self.before.levels[target].level

    def _crossed(self, up: bool) -> list[str]:
        """Features that a move added to (up) or took away from (down) some file."""
        return [fd.name for k, fd in enumerate(self.before.installed, 1)
                if any(k in ((m.target - m.source) if up else (m.source - m.target)) for m in self.moves)]

    @property
    def applied(self) -> list[str]:
        return self._crossed(up=True)

    @property
    def reversed(self) -> list[str]:
        return self._crossed(up=False)

    @property
    def src_changed(self) -> bool:
        return not self.dry_run and any(m.levels.target.startswith("src/") for m in self.moves)

    @property
    def at_bottom(self) -> bool:
        return all(self.level_after(t) == frozenset() for t in self.before.levels)

    @property
    def exit_code(self) -> int:
        return 1 if self.conflicts else 0


# --- the shared path

def _public(fn):
    """Every public function raises only errors.Error: any OSError on the way (a read-only file
    system, a full disk, an unreadable provenance file) becomes WriteFailed here."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except OSError as e:
            raise WriteFailed(texts.os_error(e)) from e
    return wrapper


def _link(tree: Path, features_dir: Path, feature: str | None) -> tuple[list[FeatureDir], int | None]:
    """Every refusal of the start of a command (decision 2), before the lock: the tree, how the
    installed features link, and the selected feature's number."""
    installed = link(Tree.read(tree), read_feature_dirs(features_dir))
    return installed, None if feature is None else feature_number(installed, feature)


@contextmanager
def _session(tree: Path, installed: list[FeatureDir], *, exclusive: bool, lock: bool, selected: int | None = None,
             near: Path | None = None):
    """Lock, work directory, patch targets, levels; refused when two features cannot be installed
    together (stage 2 design, section 4).  Only the run that holds the exclusive lock replays in the staging
    directory next to the tree (decision 5)."""
    under = below(installed)
    with locked(tree, exclusive) if lock else nullcontext():
        with staging_dir(tree) if lock and exclusive else temp_dir(near) as workdir:
            replayer = Replayer(Git(), workdir)
            patches = [replayer.read_target(p, k) for k, fd in enumerate(installed, 1) for p in fd.patch_files]
            real_tree = os.path.realpath(tree)
            for p in patches:
                if os.path.realpath(tree_path(tree, p.target)) != os.path.join(real_tree, *p.target.split("/")):
                    raise Refused(texts.symlink(tree_path(tree, p.target), tree))
            by_target: dict[str, list] = {}
            for p in patches:
                by_target.setdefault(p.target, []).append(p)
            levels = {}
            for target, ps in sorted(by_target.items()):
                try:
                    content = tree_path(tree, target).read_bytes()
                except FileNotFoundError:                   # deleted by the lock holder meanwhile (a read without the lock)
                    content = None
                levels[target] = lv = replayer.levels(target, content, ps, under)
                if lv.cannot_combine:
                    a, b = (installed[k - 1] for k in lv.cannot_combine)
                    raise ChainBroken(texts.cannot_combine(f"{a.package} {a.version}", f"{b.package} {b.version}", target))
            yield Status(tree, installed, under, levels, model.feature_states(levels, under), selected), replayer


def _move(st: Status, replayer: Replayer, *, asked: frozenset[int], up: bool, dry_run: bool) -> Moves:
    moves, conflicts = model.plan(st.levels, asked, up, st.below)
    if not dry_run:
        for m in moves:
            try:
                replayer.install(st.tree, m.levels, m.target)
            except OSError as e:
                raise WriteFailed(f"could not write {tree_path(st.tree, m.levels.target)}: {e}") from e
    return Moves(st, moves, conflicts, dry_run, up)


# --- the public functions

@_public
def status(tree: Path, features_dir: Path, *, feature: str | None = None, lock: bool = True) -> Status:
    """`lock=False` is for the pre-unlink hook after a lock timeout: levels are then computed in a
    temporary directory without the lock (every write into the tree is a single os.replace, so
    reading without the lock is safe)."""
    installed, k = _link(tree, features_dir, feature)
    if not installed:
        return Status(tree, [])
    with _session(tree, installed, exclusive=False, lock=lock, selected=k) as (st, _):
        return st


@_public
def apply(tree: Path, features_dir: Path, *, feature: str | None = None, dry_run: bool = False) -> Moves:
    return _apply_or_unapply(tree, features_dir, feature, dry_run, up=True)


@_public
def unapply(tree: Path, features_dir: Path, *, feature: str | None = None, dry_run: bool = False) -> Moves:
    return _apply_or_unapply(tree, features_dir, feature, dry_run, up=False)


def _apply_or_unapply(tree, features_dir, feature, dry_run, *, up: bool) -> Moves:
    installed, k = _link(tree, features_dir, feature)
    if not installed:
        return Moves(Status(tree, []), [], [], dry_run, up)
    with _session(tree, installed, exclusive=not dry_run, lock=True, selected=k) as (st, replayer):
        return _move(st, replayer, asked=frozenset(s.number for s in st.asked(up)), up=up, dry_run=dry_run)


@_public
def apply_to(directory: Path, feature_dir: Path) -> Moves:
    """Directory interface: `directory` is the tree, `feature_dir` the only feature (decision 8)."""
    return _directory(directory, feature_dir, up=True)


@_public
def unapply_from(directory: Path, feature_dir: Path) -> Moves:
    return _directory(directory, feature_dir, up=False)


def _directory(directory: Path, feature_dir: Path, *, up: bool) -> Moves:
    if not directory.is_dir():
        raise NotFound(f"{directory} is not a directory")
    fd = FeatureDir(feature_dir, feature_dir.name, "", ())     # decision 8: no provenance is read; only .dir and .patch_files mean anything
    near = Path(os.path.realpath(directory)).parent
    with _session(directory, [fd], exclusive=False, lock=False, near=near) as (st, replayer):
        return _move(st, replayer, asked=frozenset({1}), up=up, dry_run=False)
