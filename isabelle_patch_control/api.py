"""The public Python API (plan decision 8): the functions the command line runs.  They return
result objects or raise `errors.Error`; nothing here exits.

status(), apply() and unapply() work on a tree and a `features.d` root; apply_to() and
unapply_from() are the directory interface: one directory, one feature directory, no lock, no
provenance.  All of them share one path: link the chain, lock, read every patch's target, replay
every touched file to find its level, and (for the writing commands) move files to their target
levels one os.replace at a time.
"""
from __future__ import annotations

import os
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path

from . import model
from .engine import LOCK_TIMEOUT, Git, Levels, Replayer, locked, staging_dir, temp_dir, tree_path
from .errors import Busy, ChainBroken, Error, NotFound, Refused, WriteFailed  # noqa: F401  (re-exported)
from .features import FeatureDir, Tree, link_chain, read_feature_dirs

__all__ = ["status", "apply", "unapply", "apply_to", "unapply_from", "Status", "Moves",
           "Error", "NotFound", "Refused", "ChainBroken", "Busy", "WriteFailed"]


@dataclass
class Status:
    tree: Path
    chain: list[FeatureDir]
    levels: dict[str, Levels] = field(default_factory=dict)        # target -> levels
    features: list[model.FeatureState] = field(default_factory=list)

    def number(self, feature: str) -> int:
        for k, fd in enumerate(self.chain, 1):
            if fd.name == feature:
                return k
        raise Refused(f"no feature package named {feature!r} is installed "
                      f"(installed: {', '.join(fd.name for fd in self.chain) or 'none'})")

    def exit_code(self, feature: str | None = None) -> int:
        """0 when the selected features (all by default) are applied without a hole below."""
        selected = self.features if feature is None else [self.features[self.number(feature) - 1]]
        return 0 if all(s.state == model.APPLIED and not s.hole for s in selected) else 1


@dataclass
class Moves:
    """What apply/unapply did (or, with dry_run, would do)."""
    before: Status
    moves: list[model.Move]
    conflicts: list[Levels]            # CONFLICT files in the command's way
    dry_run: bool

    def level_after(self, target: str) -> int | None:
        for m in self.moves:
            if m.levels.target == target:
                return m.target
        return self.before.levels[target].level

    def _crossed(self, up: bool) -> list[str]:
        """Features whose own files moved across them: applied (up) or reversed (down) by this run."""
        names = []
        for k, fd in enumerate(self.before.chain, 1):
            own = [m for m in self.moves if any(p.feature == k for p in m.levels.patches)]
            if any((m.source < k <= m.target) if up else (m.target < k <= m.source) for m in own):
                names.append(fd.name)
        return names

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
        return all(self.level_after(t) == 0 for t in self.before.levels)

    @property
    def exit_code(self) -> int:
        return 1 if self.conflicts else 0


# --- the shared path

def _chain(tree: Path, features_dir: Path | None) -> tuple[Tree, list[FeatureDir]]:
    t = Tree.read(tree)
    return t, link_chain(t, read_feature_dirs(features_dir) if features_dir else [])


@contextmanager
def _session(tree: Path, chain: list[FeatureDir], *, exclusive: bool, lock: bool, timeout: float = LOCK_TIMEOUT,
             near: Path | None = None):
    """Lock, work directory, patch targets, levels.  Only the run that holds the exclusive lock
    replays in the staging directory next to the tree (decision 5)."""
    with locked(tree, exclusive, timeout) if lock else nullcontext():
        with staging_dir(tree) if lock and exclusive else temp_dir(near) as workdir:
            replayer = Replayer(Git(), workdir)
            patches = [replayer.read_target(p, k) for k, fd in enumerate(chain, 1) for p in fd.patch_files]
            real_tree = os.path.realpath(tree)
            for p in patches:
                if os.path.realpath(tree_path(tree, p.target)) != os.path.join(real_tree, *p.target.split("/")):
                    raise Refused(f"{tree_path(tree, p.target)} is or lies under a symbolic link; isabelle-patch-control "
                                  "replaces files in place and does not follow links (conda's always_softlink / "
                                  "allow_softlinks settings create such trees)")
            by_target: dict[str, list] = {}
            for p in patches:
                by_target.setdefault(p.target, []).append(p)
            levels = {}
            for target, ps in sorted(by_target.items()):
                path = tree_path(tree, target)
                levels[target] = replayer.levels(target, path.read_bytes() if path.exists() else None, ps)
            st = Status(tree, chain, levels, model.feature_states(levels, len(chain)))
            yield st, replayer


def _move(st: Status, replayer: Replayer, *, target: int, up: bool, dry_run: bool) -> Moves:
    moves, conflicts = model.plan(st.levels, len(st.chain), target, up)
    if not dry_run:
        for m in moves:
            try:
                replayer.install(st.tree, m.levels, m.target)
            except OSError as e:
                raise WriteFailed(f"could not write {tree_path(st.tree, m.levels.target)}: {e}") from e
    return Moves(st, moves, conflicts, dry_run)


# --- the public functions

def status(tree: Path, features_dir: Path | None, *, lock: bool = True, timeout: float = LOCK_TIMEOUT) -> Status:
    """`lock=False` is for the pre-unlink hook after a lock timeout: levels are then computed in a
    temporary directory without the lock (every write into the tree is a single os.replace, so
    reading without the lock is safe)."""
    t, chain = _chain(tree, features_dir)
    if not chain:
        return Status(tree, [])
    with _session(tree, chain, exclusive=False, lock=lock, timeout=timeout) as (st, _):
        return st


def apply(tree: Path, features_dir: Path | None, *, feature: str | None = None, dry_run: bool = False,
          timeout: float = LOCK_TIMEOUT) -> Moves:
    return _apply_or_unapply(tree, features_dir, feature, dry_run, timeout, up=True)


def unapply(tree: Path, features_dir: Path | None, *, feature: str | None = None, dry_run: bool = False,
            timeout: float = LOCK_TIMEOUT) -> Moves:
    return _apply_or_unapply(tree, features_dir, feature, dry_run, timeout, up=False)


def _apply_or_unapply(tree, features_dir, feature, dry_run, timeout, *, up: bool) -> Moves:
    t, chain = _chain(tree, features_dir)
    empty = Status(tree, chain)
    if feature is not None:
        empty.number(feature)
    if not chain:
        return Moves(empty, [], [], dry_run)
    with _session(tree, chain, exclusive=not dry_run, lock=True, timeout=timeout) as (st, replayer):
        k = st.number(feature) if feature else None
        target = (k if k else len(chain)) if up else (k - 1 if k else 0)
        return _move(st, replayer, target=target, up=up, dry_run=dry_run)


def apply_to(directory: Path, feature_dir: Path) -> Moves:
    """Directory interface: `directory` is the tree, `feature_dir` the only feature (decision 8)."""
    return _directory(directory, feature_dir, up=True)


def unapply_from(directory: Path, feature_dir: Path) -> Moves:
    return _directory(directory, feature_dir, up=False)


def _directory(directory: Path, feature_dir: Path, *, up: bool) -> Moves:
    if not directory.is_dir():
        raise NotFound(f"{directory} is not a directory")
    fd = FeatureDir(feature_dir, feature_dir.name, "", "", "")
    near = Path(os.path.realpath(directory)).parent
    with _session(directory, [fd], exclusive=False, lock=False, near=near) as (st, replayer):
        return _move(st, replayer, target=1 if up else 0, up=up, dry_run=False)


def single_feature_levels(tree: Path, feature_dir: Path) -> dict[str, Levels]:
    """The levels of a tree's files relative to one feature alone (used by the pre-unlink hook when
    the chain does not link): 0 = the feature's change is absent, 1 = present."""
    fd = FeatureDir(feature_dir, feature_dir.name, "", "", "")
    with _session(tree, [fd], exclusive=False, lock=False) as (st, _):
        return st.levels
