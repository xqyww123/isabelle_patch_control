"""check-signatures [-C <dir>] <base rev> <rev> <additions file>

Release gate (d) of make-patches: for every .ML file that differs between <base rev> and <rev>,
every entry of the signature sections of the base version is still present unchanged in <rev>,
and the entries added have exactly the heads listed in <additions file>.  Both revisions are
resolved, and the files read, in the repository of <dir> (default: the current directory).

A signature section is Isabelle style: `signature NAME =` ... `end` at column 0.  An entry starts
at a specification keyword (val, type, eqtype, datatype, exception, structure, include, sharing);
its continuation lines are joined, comments dropped, white space squeezed.  A head is
`<path> <NAME> <keyword> <name>` (neither the type nor its type parameters are part of it:
`datatype 'a state = ...` has the head `... datatype state`).  The additions file lists one
head per line; `#` lines and blank lines are ignored.
"""
# This docstring is what `check-signatures --help` prints; gate (d) is MLML's
# ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md §5.1, light locale's make_patches.sh check generalised.
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .dev import git, run

KEYWORDS = {"val", "type", "eqtype", "datatype", "exception", "structure", "include", "sharing"}
COMMENT = re.compile(r"\(\*([^*]|\*+[^*)])*\*+\)")
SECTION = re.compile(r"^signature ([A-Z_0-9]+) *=")
END = re.compile(r"^end;?\s*$")
TYPE_PARAMS = re.compile(r"^(type|eqtype|datatype) ('\S+ |\(\s*'[^)]*\) ?)")  # `'a ` or `('a, 'b)`


def entries(text: str) -> Counter:
    """`NAME: entry` for every entry of every signature section of an ML file."""
    found = Counter()
    name = None
    entry = None
    inside = False

    def flush():
        nonlocal entry
        if entry:
            e = re.sub(r"[ \t]+", " ", COMMENT.sub(" ", entry)).strip()
            found[f"{name}: {e}"] += 1
        entry = None

    for line in text.splitlines():
        m = SECTION.match(line)
        if m:
            name, inside = m.group(1), True
            continue
        if inside and END.match(line):
            flush()
            inside = False
            continue
        if not inside:
            continue
        words = COMMENT.sub(" ", line).split()
        if words and words[0] in KEYWORDS:
            flush()
            entry = line
        elif entry is not None:
            entry += " " + line
    return found


def head(path: str, entry: str) -> str:
    name, _, body = entry.partition(": ")
    body = TYPE_PARAMS.sub(r"\1 ", body)
    return f"{path} {name} " + re.sub(r" *(:|=| of ).*", "", body)


def show(repo: Path, rev: str, path: str) -> str:
    """The file's content at rev; empty when it does not exist there (a new or deleted file)."""
    if run(["git", "cat-file", "-e", f"{rev}:{path}"], cwd=repo, check=False).returncode:
        return ""
    return run(["git", "show", f"{rev}:{path}"], cwd=repo).stdout


def check(repo: Path, base: str, rev: str, heads: list[str], source: str) -> list[str]:
    """The problems found (empty = the gate passes); `heads` are the heads read from `source`."""
    problems = []
    added = []
    for path in git("diff-tree", "-r", "--name-only", "--no-renames", base, rev, cwd=repo).split("\n"):
        if not path.endswith(".ML"):
            continue
        before = entries(show(repo, base, path))
        after = entries(show(repo, rev, path))
        removed = before - after
        if removed:
            problems.append(f"signature entries of {path} changed or disappeared:\n  " + "\n  ".join(sorted(removed.elements())))
        added += [head(path, e) for e in (after - before).elements()]
    if sorted(added) != sorted(heads):
        extra = sorted(Counter(added) - Counter(heads))
        missing = sorted(Counter(heads) - Counter(added))
        problems.append(f"the signature additions differ from {source}:"
                        + "".join(f"\n  not listed: {h}" for h in extra)
                        + "".join(f"\n  listed but not added: {h}" for h in missing))
    return problems
