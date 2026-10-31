"""Check and repair the changes that Isabelle feature packages make to Isabelle's sources.

Run `status` to check: it lists every installed Isabelle feature package and whether its changes
are in place, and changes nothing.

  status   [--feature F]               one line per feature; exit 0 when F and every feature below it (or everything) is applied
  apply    [--feature F] [--dry-run]   put the installed features' changes in place, up to F (or all)
  unapply  [--feature F] [--dry-run]   take them out again, from F upwards (or all of them)
  help                                 what to do when a feature cannot be applied, and in other situations

Not for hand use:
  apply-to      <dir> <feature dir>    one feature directory onto any directory, no lock, no provenance
  unapply-from  <dir> <feature dir>    the reverse
  conda-hook    post-link | pre-unlink <feature>     what the feature packages' hooks run

For the developers of feature packages (`<command> --help` says more):
  new-tree      <feature repo>         put the trees that the feature repository registers in place
  new-tree      --home <feature repo> --base <R>/<base> <R>/<feature>     register a feature's two trees
  make-patches  --package <dir> [<R>/]<feature> <version>                 release a feature, in its private tree
  check-signatures  <base rev> <rev> <additions file>                     release gate (d) on its own

Exit codes: 0 `status` found everything asked for applied, or `apply`/`unapply` found nothing in its
way (also: no feature packages installed); 1 something is not applied, a file could not be moved,
or the lock is busy; 2 no Isabelle tree where expected, git missing or older than 2.43, or a wrong
command line; 3 refused: the installed packages do not link into one chain,
the tree is another build than they were made for, it has a .git, a patch target is a symbolic
link, a patch file cannot be read, a name is unknown, the prefix is not a conda environment and no
--features-dir is given, or --features-dir is not a directory.  conda-hook exits 0 whenever it wrote
its own message.  new-tree, make-patches and check-signatures exit 0 when done and 3 when refused;
check-signatures exits 1 when the signatures differ from the additions file.
"""
# This docstring is what --help prints; the command line is plan §4.
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import api, check_signatures, conda_hook, make_patches, model, names, new_tree, texts
from .dev import listed
from .errors import Error, Refused, WriteFailed
from .features import locate


def main():
    sys.stdout.reconfigure(line_buffering=True)      # progress lines stay in order with refusals when output is captured
    sys.exit(run(sys.argv[1:], os.environ))


def run(argv, env) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "help":
            print((Path(__file__).parent / "AGENTS.md").read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "conda-hook":
            return conda_hook.run(args.hook, getattr(args, "feature", None), env)
        if args.command in DEVELOPER:
            return developer_run(args)
        if args.command in ("apply-to", "unapply-from"):
            fn = api.apply_to if args.command == "apply-to" else api.unapply_from
            res = fn(Path(os.path.abspath(args.dir)), Path(os.path.abspath(args.feature_dir)))
            report_moves(res, root=None, verbose=args.verbose, quiet=args.quiet)
            return res.exit_code
        tree, root, conda = resolve(args)
        tool = invocation(args, tree, root)
        if args.command == "status":
            st = api.status(tree, root, feature=args.feature)
            if not args.quiet:
                report_status(st, root, args.verbose, conda=conda, tool=tool)
            return st.exit_code
        fn = api.apply if args.command == "apply" else api.unapply
        try:
            res = fn(tree, root, feature=args.feature, dry_run=args.dry_run)
        except WriteFailed as e:
            print(f"{texts.PREFIX}{e}", file=sys.stderr)
            if args.command == "apply" and not args.quiet:   # where did it stop? (its last line would say apply after unapply)
                report_status(api.status(tree, root), root, args.verbose, conda=conda, tool=tool)
            return e.exit_code
        report_moves(res, root, verbose=args.verbose, quiet=args.quiet, tool=tool)
        return res.exit_code
    except Error as e:
        print(f"{texts.PREFIX}{e}", file=sys.stderr)
        return e.exit_code


def resolve(args) -> tuple[Path, Path, bool]:
    """Decision 2: the prefix P is --isabelle-home's parent, else sys.prefix; the tree is
    --isabelle-home or P/isa; the features.d root is --features-dir or P's, which exists only in a
    conda environment (P/conda-meta is a directory).  Returns (tree, root, whether P is a conda
    environment)."""
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
    return tree, root, (prefix / "conda-meta").is_dir()


def invocation(args, tree: Path, root: Path) -> str:
    """The tool as the user ran it: a command the output gives must reach the same tree."""
    return " ".join([texts.TOOL, *([f"--isabelle-home {texts.quoted(tree)}"] if args.isabelle_home else []),
                     *([f"--features-dir {texts.quoted(root)}"] if args.features_dir else [])])


def report_status(st: api.Status, root: Path, verbose: bool, *, conda: bool, tool: str):
    """One sentence per feature (§4).  `conda`: the tree is a conda environment's, so a reinstall of
    isabelle restores its files.  `tool`: what the commands in the last lines start with."""
    if not st.chain:
        print(texts.NO_FEATURES)
        return
    print(texts.checked(st.tree, len(st.chain)))
    if verbose:
        print(texts.read_from(root))
    print()
    for fd, s in zip(st.chain, st.features):
        print(feature_sentence(st, s))
        if verbose:
            print(f"    package {names.package_name(fd.name)}, release {fd.release_tag}; its files:")
            for t in s.files:
                print(f"      {t}  {describe_level(st, st.levels[t])}" + (f"  {texts.CREATED}" if st.levels[t].created else ""))
                complaints(st.levels[t], "        ", first_only=True)
    print()
    asked = st.features[:st.selected]                        # --feature F: F and the features below it
    unrecognised = {t for s in asked if s.state == model.CONFLICT for t in s.conflicts}
    if unrecognised:
        print(texts.conflict_fix(st.tree, [(t, st.levels[t].created) for t in sorted(unrecognised)], conda=conda, tool=tool))
    elif st.exit_code == 0:
        print(texts.in_order(st.chain[st.selected - 1].name if st.selected else None))
    else:
        print(texts.missing(st.chain[st.selected - 1].name if st.selected else None, tool))


def feature_sentence(st: api.Status, s: model.FeatureState) -> str:
    name = st.chain[s.number - 1].name
    if s.state == model.APPLIED:
        return texts.applied(name, [st.chain[k - 1].name for k in s.not_below])
    if s.state == model.NOT_APPLIED:
        return texts.not_applied(name)
    if s.state == model.HALF:
        return texts.half_applied(name, s.below, len(s.files))
    return texts.conflict(name, s.conflicts)


PHRASES = {model.APPLIED: texts.IS_APPLIED, model.NOT_APPLIED: texts.IS_NOT_APPLIED, model.HALF: texts.IS_HALF,
           model.CONFLICT: texts.IS_CONFLICT}


def read_status(out: str) -> list[tuple[str, str]]:
    """(state, feature) of every feature sentence in what `status` printed: for scripts and tests,
    which should read the exit code where they can."""
    return [(state, name) for name, rest in filter(None, map(texts.read_sentence, out.splitlines()))
            for state, phrase in PHRASES.items() if rest.startswith(phrase)]


def level_name(st: api.Status, level: int) -> str:
    """`level 3 (f3)`: the number with the feature it stands for."""
    return f"level {level} ({st.chain[level - 1].name if level else 'original'})"


def describe_level(st: api.Status, lv) -> str:
    if lv.level is not None:
        return level_name(st, lv.level)
    return f"levels {', '.join(map(str, lv.tables))}" if lv.tables else "no level"


def complaints(lv, indent: str, *, first_only: bool):
    """git's complaint per rejected level of a CONFLICT file, without its warnings (the copy git
    works on has no permission bits, so a mode warning would come first)."""
    if lv.level is None:
        for level, complaint in sorted(lv.failures.items()):
            lines = [line for line in complaint.splitlines() if not line.startswith("warning: ")] or ["does not apply"]
            for line in (lines[:1] if first_only else lines):
                print(f"{indent}level {level}: {line}")


def report_moves(res: api.Moves, root: Path | None, *, verbose: bool, quiet: bool, tool: str = texts.TOOL):
    """`root` is None for the directory interface, which prints only the moves (under -v) and the
    CONFLICT sentences: its texts about the conda environment do not apply to an arbitrary directory."""
    st = res.before
    tree = st.tree
    if verbose and root is not None:
        print(texts.checked(tree, len(st.chain)))
        print(texts.read_from(root))
    if quiet:
        return
    if res.dry_run or verbose:
        if res.moves:
            print(texts.WOULD_CHANGE if res.dry_run else texts.CHANGED_FILES)
        elif res.dry_run:
            print(texts.NOTHING_WOULD_CHANGE)
        for m in res.moves:
            print(f"  {m.levels.target}  {level_name(st, m.source)} -> {level_name(st, m.target)}")
    # the features the command was asked about; their CONFLICT files are exactly res.conflicts
    asked = st.features[:st.selected] if res.up else st.features[(st.selected or 1) - 1:]
    stuck = [s for s in asked if s.state == model.CONFLICT]
    if res.moves and not res.dry_run and root is not None:
        if res.applied:                                      # never a CONFLICT feature: apply stops below it
            print(texts.changed(tree, applied=res.applied))
            if res.src_changed:
                print(texts.HEAP_PARAGRAPH)
        if undone := [n for n in res.reversed if n not in {st.chain[s.number - 1].name for s in stuck}]:
            print(texts.changed(tree, undone=undone))
            if res.at_bottom:
                print(texts.BACK_AT_BOTTOM)
    phrase = texts.IS_CONFLICT if res.up else texts.CANNOT_UNDO
    for s in stuck:                                          # last: what the user acts on
        name = st.chain[s.number - 1].name
        print(texts.conflict(name, s.conflicts, phrase) if root is None else texts.conflict_line(name, s.conflicts, phrase, tool))
        if verbose:
            for t in s.conflicts:
                print(f"    {t}  {describe_level(st, st.levels[t])}")
                complaints(st.levels[t], "      ", first_only=False)


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
    developer(subs)
    return p


DEVELOPER = {"new-tree": new_tree, "make-patches": make_patches, "check-signatures": check_signatures}


def developer(subs):
    """The developers' subcommands: each module's docstring is its `--help`."""
    def add(name):
        s = subs.add_parser(name, description=DEVELOPER[name].__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        s.set_defaults(usage=s)
        return s
    s = add("new-tree")
    s.add_argument("--home", metavar="<feature repo>", help="register <R>/<feature> in this feature repository")
    s.add_argument("--base", metavar="<R>/<base>", help="the base of the feature --home registers")
    s.add_argument("target", metavar="<feature repo> | <R>/<feature>")
    s = add("make-patches")
    s.add_argument("-C", metavar="dir", default=".", help="the private tree (pristine: a directory in the repository)")
    s.add_argument("--package", metavar="dir", type=Path, help="the feature's package directory")
    s.add_argument("--hg", metavar="repo", type=Path, help="pristine: the Isabelle hg repository")
    s.add_argument("--tarball", metavar="file", type=Path, help="pristine: the official release tarball")
    s.add_argument("feature", metavar="[<R>/]<feature>")
    s.add_argument("version", metavar="<version>|<hg id>")
    s = add("check-signatures")
    s.add_argument("-C", metavar="dir", default=".", help="a directory inside the repository")
    s.add_argument("base", metavar="<base rev>")
    s.add_argument("rev", metavar="<rev>")
    s.add_argument("additions", metavar="<additions file>", type=Path)


def developer_run(args) -> int:
    if args.command == "new-tree":
        if (args.home is None) != (args.base is None):
            args.usage.error("--home and --base go together")
        if args.home:
            new_tree.register(new_tree.feature_home(Path(args.home)), args.target, args.base)
        else:
            new_tree.set_up_all(new_tree.feature_home(Path(args.target)))
        return 0
    if args.command == "make-patches":
        if args.feature.rsplit("/", 1)[-1] == "pristine":
            if not (args.hg and args.tarball):
                args.usage.error("pristine needs --hg <repo> and --tarball <file>")
            make_patches.pristine_release(Path(args.C), args.feature, args.version, args.hg, args.tarball)
        else:
            if not args.package:
                args.usage.error("a feature release needs --package <dir>")
            make_patches.feature_release(Path(args.C), args.feature, args.version, args.package.resolve())
        return 0
    heads = listed(args.additions)
    problems = check_signatures.check(Path(args.C), args.base, args.rev, heads, str(args.additions))
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print(f"signature sections: every entry of {args.base} unchanged in {args.rev}, {len(heads)} additions as listed")
    return 0


def verbosity(p: argparse.ArgumentParser, default):
    g = p.add_mutually_exclusive_group()
    g.add_argument("-v", "--verbose", action="store_true", default=default,
                   help="also list every file a feature changes, its level, and git's complaints")
    g.add_argument("-q", "--quiet", action="store_true", default=default, help="print only errors; read the exit code")
