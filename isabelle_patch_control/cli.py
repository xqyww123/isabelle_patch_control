"""The command line (plan §4).

isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]               tree and features.d root, then one line per feature
  apply    [--feature F] [--dry-run]   move every file up to its target level below the top (or F)
  unapply  [--feature F] [--dry-run]   move every file down to its target level below F (or to 0)
  apply-to      <dir> <feature dir>    directory interface: <dir> is the tree, one feature
  unapply-from  <dir> <feature dir>    directory interface: reverse
  conda-hook    post-link              for the hooks: whole-chain apply; exit 0; $PREFIX/.messages.txt
  conda-hook    pre-unlink <feature>   for the hooks: reverse <feature> and everything above; exit 0
  help                                 print AGENTS.md

Exit codes: 0 success (also: no feature packages installed); 1 something is not applied, a file
could not be moved, git could not write a copy, or the lock is busy; 2 no tree, or git missing or
too old; 3 refused (see errors.Refused).  conda-hook always exits 0.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import api, conda_hook, model, texts
from .errors import Error, Refused, WriteFailed

FEATURES_D = Path("share/isabelle_patch_control/features.d")


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
            res = fn(Path(args.dir).absolute(), Path(args.feature_dir).absolute())
            report_moves(res, root=None, verbose=args.verbose, quiet=args.quiet)
            return res.exit_code
        prefix, tree, root = resolve(args)
        features_dir = root if root.is_dir() else None
        if args.command == "status":
            st = api.status(tree, features_dir)
            if not args.quiet:
                report_status(st, root, args.verbose)
                if (prefix / "conda-meta").is_dir() and not (prefix / "conda-meta" / "history").exists():
                    print(texts.interrupted(prefix))
            return st.exit_code(args.feature)
        fn = api.apply if args.command == "apply" else api.unapply
        try:
            res = fn(tree, features_dir, feature=args.feature, dry_run=args.dry_run)
        except WriteFailed as e:
            print(f"{texts.PREFIX}{e}", file=sys.stderr)
            report_status(api.status(tree, features_dir), root, args.verbose)   # where did it stop?
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
        tree = Path(args.isabelle_home).absolute()
        prefix = tree.parent
    else:
        prefix = Path(sys.prefix)
        tree = prefix / "isa"
    if args.features_dir:
        root = Path(args.features_dir).absolute()
        if not root.is_dir():
            raise Refused(f"--features-dir {root} is not a directory")
    elif (prefix / "conda-meta").is_dir():
        root = prefix / FEATURES_D
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
    if res.moves and not res.dry_run:
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
    p.add_argument("--features-dir", metavar="DIR", help="the features.d root (default: the conda environment's)")
    verbosity(p, default=False)
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("status", "apply", "unapply"):
        s = subs.add_parser(name)
        s.add_argument("--feature", metavar="F")
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
