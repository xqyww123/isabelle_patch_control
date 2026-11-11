"""Pure logic over file levels (plan decisions 6 and 7; stage 2 design, section 5): a feature's
displayed state, and which files a command moves to which level.  A level is the set of the
features whose changes a file carries."""
from __future__ import annotations

from dataclasses import dataclass

from .engine import Level, Levels

APPLIED, HALF, NOT_APPLIED, CONFLICT = "applied", "half-applied", "not-applied", "CONFLICT"


@dataclass(frozen=True)
class FeatureState:
    number: int
    files: tuple[str, ...]          # targets of this feature's patches, sorted
    state: str
    conflicts: tuple[str, ...]      # files without a single level
    lacking: int                    # files that do not carry it (half-applied)
    not_below: tuple[int, ...]      # applied, but these features below it are not

    @property
    def hole(self) -> bool:
        return bool(self.not_below)


def feature_states(levels: dict[str, Levels], below: dict[int, frozenset[int]]) -> list[FeatureState]:
    states = []
    for k in sorted(below):
        own = sorted(t for t, lv in levels.items() if any(p.feature == k for p in lv.patches))
        conflicts = tuple(t for t in own if levels[t].level is None)
        carried = [k in levels[t].level for t in own if t not in conflicts]
        if conflicts:
            state = CONFLICT
        elif all(carried):
            state = APPLIED
        elif not any(carried):
            state = NOT_APPLIED
        else:
            state = HALF
        not_below = tuple(s.number for s in states if s.number in below[k] and s.state != APPLIED) if state == APPLIED else ()
        states.append(FeatureState(k, tuple(own), state, conflicts, carried.count(False), not_below))
    return states


@dataclass(frozen=True)
class Move:
    levels: Levels
    source: Level
    target: Level


def above(below: dict[int, frozenset[int]], features) -> frozenset[int]:
    """The features above any of `features`."""
    return frozenset(j for j, b in below.items() if b & set(features))


def plan(levels: dict[str, Levels], asked: frozenset[int], up: bool,
         below: dict[int, frozenset[int]]) -> tuple[list[Move], list[Levels]]:
    """The moves of `apply` (up: each file gains the features asked for that change it, except every
    feature that owns a CONFLICT file and the features above it) or `unapply` (down: each file loses
    the features asked for), and the CONFLICT files in the command's way: changed by a feature asked
    for."""
    conflicts = [lv for lv in levels.values() if lv.level is None]
    moving = asked
    if up:
        owners = {p.feature for lv in conflicts for p in lv.patches}
        moving = asked - owners - above(below, owners)
    moves = []
    for t in sorted(levels):
        lv = levels[t]
        if lv.level is None:
            continue
        goal = lv.level | {p.feature for p in lv.patches if p.feature in moving} if up else lv.level - moving
        if goal != lv.level:
            moves.append(Move(lv, lv.level, goal))
    in_the_way = [lv for lv in conflicts if any(p.feature in asked for p in lv.patches)]
    return moves, in_the_way
