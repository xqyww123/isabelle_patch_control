"""Check and repair the changes that Isabelle feature packages make to Isabelle's sources.

isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

`status` is the command to check things with: it lists every installed Isabelle feature package
and whether its changes are in place, and changes nothing.

  status   [--feature F]               one line per feature; exit 0 when F (or everything) is applied
  apply    [--feature F] [--dry-run]   put the installed features' changes in place, up to F (or all)
  unapply  [--feature F] [--dry-run]   take them out again, from F upwards (or all of them)
  help                                 what to do in common situations (CONFLICT, a broken chain, Ctrl-C)

Not for hand use:
  apply-to      <dir> <feature dir>    one feature directory onto any directory, no lock, no provenance
  unapply-from  <dir> <feature dir>    the reverse
  conda-hook    post-link | pre-unlink <feature>     what the feature packages' hooks run

Exit codes: 0 everything asked for is applied (also: no feature packages installed); 1 something
is not applied, a file could not be moved, or the lock is busy; 2 no Isabelle tree where expected,
or git missing or older than 2.43; 3 refused: the installed packages do not link into one chain,
the tree is another build than they were made for, it has a .git, a patch target is a symbolic
link, a patch file cannot be read, or a name is unknown.  conda-hook exits 0 whenever it wrote its
own message.
"""
# This docstring is what --help prints; the command line is plan §4.
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import api, conda_hook, model, texts
from .errors import Error, Refused, WriteFailed
from .features import locate


def main():
    sys.exit(run(sys.argv[1:], os.environ))


def run(argv, env) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "help":
            print((Path(__file__).parent / "AGENTS.md").read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "conda-hook":
            return conda_hook.run(args.hook, getattr(args, "feature", None), env)
        if args.command in ("apply-to", "unapply-from"):
            fn = api.apply_to if args.command == "apply-to" else api.unapply_from
            res = fn(Path(os.path.abspath(args.dir)), Path(os.path.abspath(args.feature_dir)))
            report_moves(res, root=None, verbose=args.verbose, quiet=args.quiet)
            return res.exit_code
        prefix, tree, root = resolve(args)
        if args.command == "status":
            st = api.status(tree, root, feature=args.feature)
            if not args.quiet:
                report_status(st, root, args.verbose)
                if (prefix / "conda-meta").is_dir() and not (prefix / "conda-meta" / "history").exists():
                    print(texts.interrupted(prefix))
            return st.exit_code
        fn = api.apply if args.command == "apply" else api.unapply
        try:
            res = fn(tree, root, feature=args.feature, dry_run=args.dry_run)
        except WriteFailed as e:
            print(f"{texts.PREFIX}{e}", file=sys.stderr)
            report_status(api.status(tree, root), root, args.verbose)   # where did it stop?
            return e.exit_code
        report_moves(res, root, verbose=args.verbose, quiet=args.quiet)
        return res.exit_code
    except Error as e:
        print(f"{texts.PREFIX}{e}", file=sys.stderr)
        return e.exit_code


def resolve(args) -> tuple[Path, Path, Path]:
    """Decision 2: the prefix P is --isabelle-home's parent, else sys.prefix; the tree is
    --isabelle-home or P/isa; the features.d root is --features-dir or P's, which exists only in a
    conda environment (P/conda-meta is a directory).  Returns (P, tree, root)."""
    if args.isabelle_home:
        tree = Path(os.path.abspath(args.isabelle_home))
        prefix = tree.parent
    else:
        prefix = Path(sys.prefix)
        tree = locate(prefix)[0]
    if args.features_dir:
        root = Path(os.path.abspath(args.features_dir))
        if not root.is_dir():
            raise Refused(f"--features-dir {root} is not a directory")
    elif (prefix / "conda-meta").is_dir():
        root = locate(prefix)[1]
    else:
        raise Refused(f"{prefix} is not a conda environment (no conda-meta directory): isabelle-patch-control supports "
                      "only the conda isabelle package; for another tree pass --features-dir DIR")
    return prefix, tree, root


def report_status(st: api.Status, root: Path, verbose: bool):
    print(f"tree {st.tree}   features.d {root}")
    if not st.chain:
        print(texts.NO_FEATURES)
        return
    rows = []
    for fd, s in zip(st.chain, st.features):
        if s.state == model.CONFLICT:
            detail = ", ".join(s.conflicts)
        else:
            detail = f"{len(s.files)} file{'s' if len(s.files) != 1 else ''}"
            if s.state == model.HALF:
                detail += f", {s.below} below"
        rows.append((s.state, fd.name, fd.release_tag, detail + (" (hole below)" if s.hole else "")))
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for (state, name, tag, detail), s in zip(rows, st.features):
        print(f"{state:<{widths[0]}} {name:<{widths[1]}} {tag:<{widths[2]}} {detail}")
        if verbose:
            for t in s.files:
                print(f"    {t}  {describe_level(st.levels[t])}" + (f"  {texts.CREATED}" if st.levels[t].created_by(s.number) else ""))
                if st.levels[t].level is None:
                    for level, complaint in sorted(st.levels[t].failures.items()):
                        print(f"      level {level}: {complaint.splitlines()[0] if complaint else 'does not apply'}")


def describe_level(lv) -> str:
    if lv.level is not None:
        return f"level {lv.level}"
    return f"levels {', '.join(map(str, lv.tables))}" if lv.tables else "no level"


def report_moves(res: api.Moves, root: Path | None, *, verbose: bool, quiet: bool):
    """`root` is None for the directory interface, which prints only the moves (under -v) and the
    CONFLICT files: its texts about the conda environment do not apply to an arbitrary directory."""
    tree = res.before.tree
    if verbose and root is not None:
        print(f"tree {tree}   features.d {root}")
    if quiet:
        return
    if res.dry_run or verbose:
        for m in res.moves:
            print(f"  {m.levels.target}  level {m.source} -> {m.target}")
    for lv in res.conflicts:
        print(f"CONFLICT  {lv.target}  {describe_level(lv)}")
        for level, complaint in sorted(lv.failures.items()):
            lines = complaint.splitlines() or ["does not apply"]
            for line in (lines if verbose else lines[:1]):
                print(f"    level {level}: {line}")
    if res.moves and not res.dry_run and root is not None:
        if res.applied:
            print(texts.changed(tree, applied=res.applied))
            if res.src_changed:
                print(texts.HEAP_PARAGRAPH)
        if res.reversed:
            print(texts.changed(tree, reversed=res.reversed))
            if res.at_bottom:
                print(texts.BACK_AT_BOTTOM)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="isabelle-patch-control", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--isabelle-home", metavar="DIR", help="the Isabelle tree (default: <prefix>/isa)")
    p.add_argument("--features-dir", metavar="DIR", help="read the installed features from DIR instead of the conda environment (for scripts)")
    verbosity(p, default=False)
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("status", "apply", "unapply"):
        s = subs.add_parser(name)
        s.add_argument("--feature", metavar="F", help="a feature name or its package name")
        if name != "status":
            s.add_argument("--dry-run", action="store_true")
        verbosity(s, default=argparse.SUPPRESS)        # `status -v` as the messages say
    for name in ("apply-to", "unapply-from"):
        s = subs.add_parser(name)
        s.add_argument("dir")
        s.add_argument("feature_dir", metavar="feature-dir")
        verbosity(s, default=argparse.SUPPRESS)
    h = subs.add_parser("conda-hook")
    hs = h.add_subparsers(dest="hook", required=True)
    hs.add_parser("post-link")
    hs.add_parser("pre-unlink").add_argument("feature")
    subs.add_parser("help")
    return p


def verbosity(p: argparse.ArgumentParser, default):
    g = p.add_mutually_exclusive_group()
    g.add_argument("-v", "--verbose", action="store_true", default=default)
    g.add_argument("-q", "--quiet", action="store_true", default=default)
