"""Shared code of the developer subcommands (new-tree, make-patches, check-signatures) and of the
release scripts in tools/, which import it through tools/common.py: the developer's own git, and
the formats of a release (patch files cut from a diff, a package's list files, build strings and
package versions); texts takes a release line's isabelle version from it for the update it advises,
and features a package's version.  Unlike engine.Git, git runs here with the user's configuration:
it commits, tags and fetches."""
from __future__ import annotations

import itertools
import os
import re
import subprocess
import tempfile
from pathlib import Path

from .errors import Refused


def run(args, cwd=None, env=None, check=True, input=None, text=True) -> subprocess.CompletedProcess:
    """`text=False` keeps the output's bytes (a diff may hold CRs and non-UTF-8 bytes)."""
    args = [str(a) for a in args]
    if cwd is not None and not Path(cwd).is_dir():
        raise Refused(f"{cwd} is not a directory")
    r = subprocess.run(args, cwd=cwd, env=env, text=text, capture_output=True, input=input)
    if check and r.returncode:
        where = f" in {cwd}" if cwd else ""
        out = r.stderr or r.stdout
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        raise Refused(f"`{' '.join(args)}` failed{where}:\n{out.strip()}")
    return r


def git(*args, cwd=None, check=True, input=None) -> str:
    return run(["git", *args], cwd=cwd, check=check, input=input).stdout.rstrip("\n")


def split_branch(branch: str) -> tuple[str, str]:
    parts = branch.split("/")
    if len(parts) != 2 or not all(parts):
        raise Refused(f"a branch name is <release>/<name>, not {branch!r}")
    return parts[0], parts[1]


def merge_base(tree: Path, base: str, branch: str, *also: str) -> str:
    """The one merge base of `base` and `branch` in the repository of `tree`; with `also`, of `base`
    and what the branch and `also` together contain."""
    r = run(["git", "merge-base", "--all", base, branch, *also], cwd=tree, check=False)
    bases = r.stdout.split()
    if r.returncode > 1 or len(bases) != 1:
        with_also = f" with {' '.join(also)}" if also else ""
        raise Refused(f"{base} and {branch}{with_also} have {len(bases)} merge bases ({' '.join(bases) or r.stderr.strip()}), "
                      "not exactly one")
    return bases[0]


def combine(repo: Path, commits: dict[str, str]) -> str:
    """The tree of the changes of `commits` (name -> commit) put together (stage 2 design, section 7):
    of the commits that no other of them contains, each one's changes since what it shares with the
    others, applied one after another as the patch tool applies a patch, in every order, with the same
    result; else refused, naming those whose changes meet.  Several merge bases count as the tree git's
    own merge would use, their combination."""
    independent = set(git("merge-base", "--independent", *commits.values(), cwd=repo).split())
    named: dict[str, str] = {}
    for n, c in commits.items():
        if c in independent and c not in named.values():
            named[n] = c
    if len(named) == 1:
        return git("rev-parse", f"{next(iter(named.values()))}^{{tree}}", cwd=repo)
    shared = {n: git("merge-base", "--all", c, *(o for m, o in named.items() if m != n), cwd=repo).split()
              for n, c in named.items()}
    x = combine(repo, {b: b for bs in shared.values() for b in bs})
    diffs = {n: run(["git", "diff-tree", "-r", "-p", "--binary", "--no-renames", combine(repo, {b: b for b in shared[n]}), c],
                    cwd=repo, text=False).stdout for n, c in named.items()}

    def changed(since: str, commit: str) -> set[str]:
        return set(filter(None, git("diff-tree", "-r", "--name-only", "--no-renames", since, commit, cwd=repo).split("\n")))

    def meets(m: str, n: str) -> bool:
        """Whether m and n, since their own merge base, change a file in common."""
        since = combine(repo, {b: b for b in git("merge-base", "--all", named[m], named[n], cwd=repo).split()})
        return bool(changed(since, named[m]) & changed(since, named[n]))

    trees = set()
    for order in itertools.permutations(named):
        with tempfile.TemporaryDirectory(prefix="combine-") as tmp:
            env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index"}
            run(["git", "read-tree", x], cwd=repo, env=env)
            for n in order:
                r = run(["git", "apply", "--cached", "--allow-empty", "--whitespace=nowarn", "--no-ignore-whitespace"], cwd=repo,
                        env=env, input=diffs[n], check=False, text=False)
                if r.returncode:
                    meet = [m for m in named if m != n and meets(m, n)]
                    line = (r.stderr.decode(errors="replace").strip().splitlines() or ["?"])[-1]
                    raise Refused(f"the changes of {' and '.join([*meet, n])} cannot be applied one after the other in every "
                                  f"order ({line}): they cannot be installed together")
            trees.add(run(["git", "write-tree"], cwd=repo, env=env).stdout.strip())
    if len(trees) > 1:
        raise Refused(f"the changes of {' and '.join(named)} give different files in different orders: they cannot be "
                      "installed together")
    return trees.pop()


def merge_commit(repo: Path, commits: dict[str, str], message: str) -> str:
    """A commit whose tree is `combine(commits)` and whose parents are exactly the commits; one commit
    is itself."""
    parents = list(dict.fromkeys(commits.values()))
    if len(parents) == 1:
        return parents[0]
    tree = combine(repo, commits)
    return git("commit-tree", "--no-gpg-sign", tree, *(x for c in parents for x in ("-p", c)), "-m", message, cwd=repo)


def status(tree: Path) -> str:
    """`git status --porcelain` with every untracked file: empty when the tree is clean."""
    return git("status", "--porcelain", "--untracked-files=all", cwd=tree)


def head_branch(tree: Path) -> str | None:
    r = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=tree, check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def toplevel(where: Path) -> Path:
    r = run(["git", "rev-parse", "--show-toplevel"], cwd=where, check=False)
    if r.returncode:
        raise Refused(f"{where} is not inside a git repository")
    return Path(r.stdout.strip()).resolve()


def exists(tree: Path, ref: str) -> bool:
    return run(["git", "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"], cwd=tree, check=False).returncode == 0


def rev(tree: Path, ref: str) -> str:
    return git("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=tree)


def tags_at(tree: Path, commit: str, pattern: str) -> list[str]:
    return git("tag", "--points-at", commit, "--list", pattern, cwd=tree).split()


# --- patch files

def patch_blocks(diff: bytes) -> dict[str, bytes]:
    """The patch files of one `git diff-tree -r -p --no-renames` output: flat file name (the path
    with '/' as '-', plus .patch) -> the file's block, byte for byte.  Mode changes, renames and
    binary diffs are not released (patch tool plan decision 16)."""
    out = {}
    for block in (b for b in re.split(rb"(?m)^(?=diff --git )", diff) if b):
        path = block_path(block)
        if re.search(rb"(?m)^(old mode|new mode|Binary files |GIT binary patch|similarity index)", block):
            raise Refused(f"{path}: mode changes, renames and binary diffs are not released")
        out[path.replace("/", "-") + ".patch"] = block
    return out


def block_path(block: bytes) -> str:
    """The path of one `git diff` block, from its `diff --git a/P b/P` line.  Not from `---`/`+++`:
    git writes none for an empty file and appends a TAB to a path with a space."""
    head = block.split(b"\n", 1)[0].decode(errors="replace")          # git quotes unusual paths, so ASCII
    m = re.fullmatch(r"diff --git a/(.*) b/\1", head)
    if not m:
        raise Refused(f"unexpected diff header: {head}")
    return m[1]


# --- a feature package's list files

COMPONENT_LIST = "tools/component_files.txt"
LICENSE_LIST = "tools/license.txt"
LISTS = ("tools/patched_files.txt", "tools/signature_additions.txt", "tools/required_sessions.txt")


def listed(path: Path) -> list[str]:
    """The entries of a list file (tools/*.txt, an additions file): its non-blank lines that do not
    start with #.  Read once, so a pipe (/dev/fd/N) works."""
    if not path.exists():
        raise Refused(f"{path} is missing")
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]


def shipped_files(package: Path) -> list[str]:
    """The component payload of a feature package, relative to its package directory:
    tools/component_files.txt and the files it lists; none without that list."""
    return [COMPONENT_LIST, *listed(package / COMPONENT_LIST)] if (package / COMPONENT_LIST).is_file() else []


def up_to_top(package: Path) -> list[Path]:
    """The package directory and every directory above it up to its repository's top."""
    dirs = [package, *package.parents]
    return dirs[:dirs.index(toplevel(package)) + 1]


def release_inputs(package: Path) -> tuple[list[str], list[str]]:
    """What a release reads from a package directory, relative to it: (required, checked when
    present).  Required: the three lists, README.md and the files tools/component_files.txt lists;
    checked when present: that list, tools/release_build.sh, tools/license.txt and every LICENSE
    from the package directory up to its repository's top."""
    package = package.resolve()
    licenses = [os.path.relpath(d / "LICENSE", package) for d in up_to_top(package)]
    return ([*LISTS, "README.md", *shipped_files(package)[1:]],
            [COMPONENT_LIST, "tools/release_build.sh", LICENSE_LIST, *licenses])


def license_of(package: Path) -> str | None:
    """The package's SPDX license expression: the one entry of tools/license.txt; None without the
    file or an entry."""
    path = package / LICENSE_LIST
    entries = listed(path) if path.is_file() else []
    if len(entries) > 1:
        raise Refused(f"{path} holds more than one entry: give one SPDX license expression, or none")
    return entries[0] if entries else None


def license_file(package: Path) -> Path | None:
    """The package's license file: the nearest file named exactly LICENSE from the package
    directory up to its repository's top (by name, also where the file system ignores case)."""
    return next((d / "LICENSE" for d in up_to_top(package.resolve())
                 if "LICENSE" in os.listdir(d) and (d / "LICENSE").is_file()), None)


def require_committed(package: Path):
    """A release reads its inputs (release_inputs) as they are committed: refused when a required one
    is missing, a present one is not committed, or any of them, present or not, has uncommitted
    changes (a deletion included), and when tools/license.txt holds more than one entry."""
    package = package.resolve()
    top = toplevel(package)
    required, present = release_inputs(package)
    for rel in required:
        if not (package / rel).is_file():
            raise Refused(f"{os.path.normpath(package / rel)} is missing")
    for rel in [*required, *present]:
        if (package / rel).exists() and run(["git", "ls-files", "--error-unmatch", "--", rel], cwd=package, check=False).returncode:
            raise Refused(f"{os.path.normpath(package / rel)} is not committed in the feature repository {top}: commit it first")
    dirty = run(["git", "status", "--porcelain", "--untracked-files=all", "--", *required, *present], cwd=package).stdout
    if dirty:
        raise Refused(f"uncommitted changes in the feature repository {top}: commit them first\n{dirty.rstrip()}")
    license_of(package)


# --- build strings and package versions

def build_string_prefix(release: str) -> str:
    """A release line's build string prefix: Isabelle2025-2 -> Isabelle2025_2 (conda refuses '-' there)."""
    return release.replace("-", "_")


def isabelle_version(build_string_prefix: str) -> str:
    """The `isabelle` package version of a release line: Isabelle2025_2 -> 2025.2, Isabelle2026 -> 2026."""
    return build_string_prefix.removeprefix("Isabelle").replace("_", ".")


def package_version(release_tag: str) -> str:
    """The version of the package built from a release tag <R>/<feature>/<m>: the release line's
    isabelle version with a second number (0 when it has none), then m.  Isabelle2026/bicompose_rename_fix/1
    -> 2026.0.1, Isabelle2025-2/expose_foreign/1 -> 2025.2.1: three numbers, so lines never share a version
    and a newer line's are higher."""
    release, _, m = release_tag.split("/")
    y, _, k = isabelle_version(build_string_prefix(release)).partition(".")
    return f"{y}.{k or 0}.{m}"
