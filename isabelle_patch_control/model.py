"""Pure logic over file levels (plan decisions 6 and 7): a feature's displayed state, and which
files a command moves to which level."""
from __future__ import annotations

from dataclasses import dataclass

from .engine import Levels

APPLIED, HALF, NOT_APPLIED, CONFLICT = "applied", "half-applied", "not-applied", "CONFLICT"


@dataclass(frozen=True)
class FeatureState:
    number: int
    files: tuple[str, ...]          # targets of this feature's patches, sorted
    state: str
    conflicts: tuple[str, ...]      # files without a single level
    below: int                      # files at a level below this feature (half-applied)
    hole: bool                      # applied with a not-applied feature below it


def feature_states(levels: dict[str, Levels], n: int) -> list[FeatureState]:
    states = []
    for k in range(1, n + 1):
        own = sorted(t for t, lv in levels.items() if any(p.feature == k for p in lv.patches))
        conflicts = tuple(t for t in own if levels[t].level is None)
        at_or_above = [levels[t].level >= k for t in own if t not in conflicts]
        if conflicts:
            state = CONFLICT
        elif all(at_or_above):
            state = APPLIED
        elif not any(at_or_above):
            state = NOT_APPLIED
        else:
            state = HALF
        hole = state == APPLIED and any(s.state == NOT_APPLIED for s in states)
        states.append(FeatureState(k, tuple(own), state, conflicts, at_or_above.count(False), hole))
    return states


@dataclass(frozen=True)
class Move:
    levels: Levels
    source: int
    target: int


def target_level(lv: Levels, reach: int) -> int:
    """The file's own target level T_p: the highest candidate <= reach (decision 7)."""
    return max(c for c in lv.candidates if c <= reach)


def plan(levels: dict[str, Levels], n: int, target: int, up: bool) -> tuple[list[Move], list[Levels]]:
    """The moves of `apply` (up) or `unapply` (down) towards `target`, and the CONFLICT files in
    the command's way.  `apply` is capped below the lowest feature that owns a CONFLICT file."""
    conflicts = [lv for lv in levels.values() if lv.level is None]
    reach = target
    if up:
        reach = min(target, min((lv.patches[0].feature for lv in conflicts), default=n + 1) - 1)
    moves = []
    for t in sorted(levels):
        lv = levels[t]
        if lv.level is None:
            continue
        tp = target_level(lv, reach)
        if (lv.level < tp) if up else (lv.level > tp):
            moves.append(Move(lv, lv.level, tp))
    in_the_way = [lv for lv in conflicts
                  if ((lv.patches[0].feature <= target) if up else (lv.patches[-1].feature > target))]
    return moves, in_the_way
