"""Shared code of the developer subcommands (new-tree, make-patches, check-signatures) and of the
release scripts in tools/, which import it through tools/common.py: the developer's own git, and
the formats of a release (patch files cut from a diff, a package's list files, build strings and
pins); texts takes a release line's isabelle version from it for the update it advises.  Unlike
engine.Git, git runs here with the user's configuration: it commits, tags and fetches."""
from __future__ import annotations

import re
import subprocess
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


def merge_base(tree: Path, base: str, branch: str) -> str:
    """The one merge base of `base` and `branch` in the repository of `tree`."""
    r = run(["git", "merge-base", "--all", base, branch], cwd=tree, check=False)
    bases = r.stdout.split()
    if r.returncode > 1 or len(bases) != 1:
        raise Refused(f"{base} and {branch} have {len(bases)} merge bases ({' '.join(bases) or r.stderr.strip()}), not exactly one")
    return bases[0]


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


# --- build strings and pins

def build_string_prefix(release: str) -> str:
    """A release line's build string prefix: Isabelle2025-2 -> Isabelle2025_2 (conda refuses '-' there)."""
    return release.replace("-", "_")


def isabelle_version(build_string_prefix: str) -> str:
    """The `isabelle` package version of a release line: Isabelle2025_2 -> 2025.2, Isabelle2026 -> 2026."""
    return build_string_prefix.removeprefix("Isabelle").replace("_", ".")


def feature_pin(version: str, build_string_prefix: str) -> str:
    """A feature package's pin on the package of its base, e.g. `==1 Isabelle2025_2_*`: that version,
    any build of the release line.  make-patches writes it as base_pin; the renderer computes it from
    base_tag (base_pin of releases cut before 2026-10-28 reads `==1=Isabelle2025_2_*`, which conda
    reads the same way and rattler-build refuses)."""
    return f"=={version} {build_string_prefix}_*"
