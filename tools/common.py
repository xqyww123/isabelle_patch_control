"""Shared code of new-tree, run-tree, make-patches, check-signatures and advance-daily: the layout
of the Isabelle source repository (migration plan §2-§3) and the git calls they all make.

Layout.  The repository's common git directory is either `<trees root>/<R>/.git` (the shared tree
of release line <R> is the main worktree) or a bare `<trees root>/isabelle-patched.git`.  Branch
`<R>/<name>` has its worktree at `<trees root>/<R>-<name>`, except `<R>/daily`, whose tree is the
shared tree `<trees root>/<R>`; the stock tree of feature `<R>/<f>` is `<trees root>/<R>-<f>-stock`.
A tree's `etc/ISABELLE_IDENTIFIER` equals its directory name (new-tree is the only writer).
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR.parent))            # the checkout's isabelle_patch_control, not an installed one
from isabelle_patch_control.errors import Error as ToolError  # noqa: E402
from isabelle_patch_control.names import package_name  # noqa: E402,F401  (re-exported for the scripts)

HOOK_SOURCE = TOOLS_DIR / "hooks" / "reference-transaction"
# build products a private or stock tree takes from its line's shared tree (decision 5 step 3):
# copied because `scala_build` rewrites them in place, linked because they are read-only data
PRODUCT_COPIES = ("lib/classes", "src/Tools/Demo/lib")
PRODUCT_LINKS = ("lib/browser_info.db", "src/Tools/Find_Facts/lib/isabelle.db")


class Refused(Exception):
    """A precondition of the plan does not hold; the message says which one."""


def run(args, cwd=None, env=None, check=True, input=None, text=True) -> subprocess.CompletedProcess:
    """`text=False` keeps the output's bytes (a diff may hold CRs and non-UTF-8 bytes)."""
    args = [str(a) for a in args]
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


def main(fn):
    """Run a script's main function; a Refused exception, or a refusal of the patch tool's API, is
    the script's refusal (exit 1)."""
    try:
        sys.exit(fn() or 0)
    except (Refused, ToolError) as e:
        print(f"{Path(sys.argv[0]).name}: refused: {e}", file=sys.stderr)
        sys.exit(1)


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


def components_sh(package: str, verb: str) -> str:
    """The hook lines that register (-u) or unregister (-x) a package's component, share/<package>."""
    return (f'"$PREFIX/isa/bin/isabelle" components {verb} "$PREFIX/share/{package}" 2>/dev/null \\\n'
            f'  || echo "warning: \'isabelle components {verb} {package}\' failed; the session may be unavailable"'
            f' >> "$PREFIX/.messages.txt"\n')


def components_bat(package: str, verb: str) -> list[str]:
    # Isabelle_RPC/conda/recipe.yaml's lines without their `@echo off`: a Cygwin path for
    # components, and the getenv warm-up without which the first call cannot run a Scala tool.
    return [f'set "COMP=%PREFIX%\\share\\{package}"',
            'set "DL=%COMP:~0,1%"',
            'set "REST=%COMP:~2%"',
            'set "REST=%REST:\\=/%"',
            'set "CYG=/cygdrive/%DL%%REST%"',
            'call "%PREFIX%\\isa\\bin\\isabelle.bat" getenv -b ISABELLE_HOME >nul 2>&1',
            f'call "%PREFIX%\\isa\\bin\\isabelle.bat" components {verb} "%CYG%" >nul 2>&1']


def block_path(block: bytes) -> str:
    """The path of one `git diff` block, from its `diff --git a/P b/P` line.  Not from `---`/`+++`:
    git writes none for an empty file and appends a TAB to a path with a space."""
    head = block.split(b"\n", 1)[0].decode(errors="replace")          # git quotes unusual paths, so ASCII
    m = re.fullmatch(r"diff --git a/(.*) b/\1", head)
    if not m:
        raise Refused(f"unexpected diff header: {head}")
    return m[1]


def block_header(block: bytes) -> tuple[str, str, str]:
    """(path, pre-image, post-image) of one `git diff` block; the images come from its `index
    <pre>..<post>` line, an all-zero image being a file absent on that side."""
    path = block_path(block)
    index = re.search(rb"(?m)^index ([0-9a-f]+)\.\.([0-9a-f]+)", block.split(b"\n@@", 1)[0])
    if not index:
        raise Refused(f"{path}: no index line in the diff header")
    return path, index[1].decode(), index[2].decode()


def split_branch(branch: str) -> tuple[str, str]:
    parts = branch.split("/")
    if len(parts) != 2 or not all(parts):
        raise Refused(f"a branch name is <release>/<name>, not {branch!r}")
    return parts[0], parts[1]


class Repo:
    def __init__(self, somewhere: Path):
        self.common_dir = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=somewhere))
        self.trees_root = (self.common_dir.parent.parent if self.common_dir.name == ".git"
                           else self.common_dir.parent)

    def git(self, *args, check=True) -> str:
        return git(*args, cwd=self.common_dir, check=check)

    # --- layout
    def shared_tree(self, release: str) -> Path:
        return self.trees_root / release

    def tree_dir(self, branch: str) -> Path:
        release, name = split_branch(branch)
        return self.trees_root / (release if name == "daily" else f"{release}-{name}")

    def stock_dir(self, feature: str) -> Path:
        release, name = split_branch(feature)
        return self.trees_root / f"{release}-{name}-stock"

    def branches(self) -> list[str]:
        return self.git("for-each-ref", "--format=%(refname:short)", "refs/heads/*/*").split()

    # --- refs
    def exists(self, ref: str) -> bool:
        return run(["git", "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"],
                   cwd=self.common_dir, check=False).returncode == 0

    def rev(self, ref: str) -> str:
        return self.git("rev-parse", "--verify", f"{ref}^{{commit}}")

    def upstream(self, branch: str) -> str | None:
        r = run(["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"], cwd=self.common_dir, check=False)
        return r.stdout.strip() if r.returncode == 0 else None

    def base_of(self, branch: str) -> str:
        """The base branch (decision 3: recorded as the git upstream)."""
        base = self.upstream(branch)
        if base is None:
            raise Refused(f"{branch} has no upstream: its base branch is not recorded")
        return base

    def is_ancestor(self, a: str, b: str) -> bool:
        return run(["git", "merge-base", "--is-ancestor", a, b], cwd=self.common_dir, check=False).returncode == 0

    def merge_base(self, a: str, b: str) -> str:
        bases = self.git("merge-base", "--all", a, b).split()
        if len(bases) != 1:
            raise Refused(f"{a} and {b} have {len(bases)} merge bases ({' '.join(bases)}), not exactly one")
        return bases[0]

    def tags_at(self, commit: str, pattern: str) -> list[str]:
        return self.git("tag", "--points-at", commit, "--list", pattern).split()

    # --- worktrees
    def worktrees(self) -> list[dict]:
        trees = []
        for block in self.git("worktree", "list", "--porcelain").split("\n\n"):
            if not block.strip():
                continue
            t = {"path": None, "head": None, "branch": None, "locked": False, "detached": False, "bare": False}
            for line in block.splitlines():
                key, _, value = line.partition(" ")
                if key == "worktree":
                    t["path"] = Path(value).resolve()
                elif key == "HEAD":
                    t["head"] = value
                elif key == "branch":
                    t["branch"] = value.removeprefix("refs/heads/")
                elif key in ("locked", "detached", "bare"):
                    t[key] = True
            trees.append(t)
        return trees

    def worktree_of(self, branch: str) -> dict | None:
        return next((t for t in self.worktrees() if t["branch"] == branch), None)

    def worktree_at(self, path: Path) -> dict | None:
        return next((t for t in self.worktrees() if t["path"] == path.resolve()), None)

    def is_main_worktree(self, path: Path) -> bool:
        first = self.worktrees()[0]
        return not first["bare"] and first["path"] == path.resolve()

    # --- per-tree state
    @staticmethod
    def status(tree: Path, untracked: bool = True) -> str:
        return git("status", "--porcelain", f"--untracked-files={'all' if untracked else 'no'}", cwd=tree)

    @staticmethod
    def head_branch(tree: Path) -> str | None:
        r = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=tree, check=False)
        return r.stdout.strip() if r.returncode == 0 else None

    # --- tree hashes (release gate (c) and the provenance file, plan §5.1)
    def tree_hash_of_dir(self, directory: Path) -> str:
        """The git tree hash of a directory's content, every file included (ignore rules off),
        through a temporary index of this repository."""
        with tempfile.TemporaryDirectory(prefix="index-") as tmp:
            env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index", "GIT_DIR": str(self.common_dir),
                   "GIT_WORK_TREE": str(directory)}
            run(["git", "add", "-f", "-A", "."], cwd=directory, env=env)
            return run(["git", "write-tree"], cwd=directory, env=env).stdout.strip()

    def tree_hash_excluding(self, commit: str, excludes: list[str]) -> str:
        """The tree hash of commit's tracked files minus the excluded paths."""
        with tempfile.TemporaryDirectory(prefix="index-") as tmp:
            env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index", "GIT_DIR": str(self.common_dir)}
            run(["git", "read-tree", commit], cwd=self.common_dir, env=env)
            if excludes:
                run(["git", "update-index", "--force-remove", "--", *excludes], cwd=self.common_dir, env=env)
            return run(["git", "write-tree"], cwd=self.common_dir, env=env).stdout.strip()

    # --- tested records (written by run-tree only)
    def tested_records(self, commit: str) -> list[dict]:
        """The records of `git notes --ref=tested` on commit: {when, tree, command, sessions, dirs},
        `dirs` mapping each `-d` repository's top-level directory to (HEAD, tracked files with
        uncommitted changes) (migration plan §0 item 32)."""
        r = run(["git", "notes", "--ref=tested", "show", commit], cwd=self.common_dir, check=False)
        records = []
        for line in (r.stdout if r.returncode == 0 else "").splitlines():
            if line.startswith("tested "):
                _, when, _, tree = line.split(" ", 3)
                records.append({"when": when, "tree": tree, "command": "", "sessions": set(), "dirs": {}})
            elif records and line.startswith("command: "):
                records[-1]["command"] = line[len("command: "):]
            elif records and line.startswith("sessions: "):
                records[-1]["sessions"] = set(line[len("sessions: "):].split())
            elif records and line.startswith("dir: "):
                top, head, *files = line[len("dir: "):].split(" ")
                records[-1]["dirs"][top] = (head, files)
        return records

    # --- the hook
    def check_hook(self):
        installed = self.common_dir / "hooks" / "reference-transaction"
        if not installed.is_file() or installed.read_bytes() != HOOK_SOURCE.read_bytes():
            raise Refused(f"{installed} is missing or differs from the reviewed hook {HOOK_SOURCE}")


# --- what new-tree installs in a tree

def write_identifier(tree: Path):
    """etc/ISABELLE_IDENTIFIER = the directory name, written as the release does (no newline)."""
    path = tree / "etc" / "ISABELLE_IDENTIFIER"
    if not path.is_file() or path.read_text() != tree.name:
        path.write_text(tree.name)


def _link(path: Path, target: str):
    if path.is_symlink():
        if os.readlink(path) == target:
            return
        raise Refused(f"{path} links to {os.readlink(path)}, expected {target}")
    if path.exists():
        raise Refused(f"{path} exists and is not the expected symlink to {target}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def _copy_dir(path: Path, source: Path):
    if path.is_symlink():
        raise Refused(f"{path} must be a real directory, not a symlink (scala_build rewrites it in place)")
    if path.exists():
        return
    if not source.is_dir():
        raise Refused(f"{source} is missing: the shared tree has no build products to copy")
    path.parent.mkdir(parents=True, exist_ok=True)
    run(["cp", "-a", source, path])


def install_products(tree: Path, shared: Path):
    """Decision 5 step 3, idempotent: `contrib` linked into the shared tree, the jar directories
    copied, the two databases linked; a tree in any other shape is refused rather than repaired.
    Skipped while the shared tree has no products itself (a new release line before its shared
    tree exists, decision 7 step 2; rerun new-tree afterwards)."""
    if not has_products(shared):
        print(f"build products not installed: {shared} has none yet; rerun new-tree once it has")
        return
    _link(tree / "contrib", os.path.relpath(shared / "contrib", tree))
    for p in PRODUCT_COPIES:
        _copy_dir(tree / p, shared / p)
    for p in PRODUCT_LINKS:
        if (shared / p).exists():
            _link(tree / p, os.path.relpath(shared / p, (tree / p).parent))


def has_products(tree: Path) -> bool:
    classes = tree / "lib" / "classes"
    return (tree / "contrib").is_dir() and classes.is_dir() and not classes.is_symlink()


# --- the state of a `-d` repository (migration plan §0 item 32; written into tested records by run-tree)

def repo_state(directory: Path) -> tuple[str, str, list[str]] | None:
    """(top-level directory, HEAD, tracked files with uncommitted changes, staged new files
    included) of the git worktree that covers `directory`, or None when none does: outside every
    worktree, or ignored by it with no tracked file inside (`git check-ignore .` also consults the
    index).  The `dir:` line of a tested record is exactly these three."""
    if not directory.is_dir():
        return None
    r = run(["git", "rev-parse", "--show-toplevel"], cwd=directory, check=False)
    if r.returncode or run(["git", "check-ignore", "-q", "."], cwd=directory, check=False).returncode == 0:
        return None
    top = str(Path(r.stdout.strip()).resolve())
    head = run(["git", "rev-parse", "HEAD"], cwd=top, check=False).stdout.strip() or "none"
    files = sorted(line[3:] for line in Repo.status(Path(top), untracked=False).splitlines())
    return top, head, files


def tracked_mtimes(top: str) -> dict[str, tuple[int, int]]:
    """(mtime, size) of every tracked file: a file changed during a build and changed back leaves
    the `dir:` line unchanged but not this."""
    out = {}
    for rel in run(["git", "ls-files", "-z"], cwd=top).stdout.split("\0"):
        if rel:
            try:
                st = os.lstat(os.path.join(top, rel))
                out[rel] = (st.st_mtime_ns, st.st_size)
            except FileNotFoundError:
                out[rel] = (0, -1)
    return out


# --- which packages the release workflow builds and which it reuses (patch tool plan decision 10)

@dataclass(frozen=True)
class Wanted:
    """One package the batch wants: name and version; build n is the file
    `<name>-<version>-<build_string_prefix>_<n>.conda` (the prefix as provenance.txt spells it,
    `Isabelle2025_2`; the tool's is `pyh<hash>`); `pin` is the `isabelle` dependency a candidate on
    the channel must carry to be exactly what the batch wants (a feature package pins this batch's
    isabelle build; the tool, pin None, is any build of the version)."""
    name: str
    version: str
    build_string_prefix: str
    pin: str | None

    def filename(self, n: int) -> str:
        return f"{self.name}-{self.version}-{self.build_string_prefix}_{n}.conda"

    def accepts(self, record: dict) -> bool:
        return self.pin is None or self.pin in record["depends"]


def isabelle_pin(build_string_prefix: str, isabelle_build: str) -> str:
    """The `isabelle` dependency of a feature package, e.g. `isabelle ==2025.2 1`.  The renderer of the
    feature recipes imports this: the pin a recipe writes and the pin plan_builds looks for are then
    one and the same (rattler-build records it in `depends` as written).  `==`, not a bare version:
    rattler-build refuses `isabelle 2025.2 1` in a recipe; conda reads both the same."""
    return f"isabelle =={build_string_prefix.removeprefix('Isabelle').replace('_', '.')} {isabelle_build}"


def pinned_build(record: dict, build_string_prefix: str) -> str | None:
    """The inverse of isabelle_pin: the isabelle build a package record's depends pin, or None."""
    pin = isabelle_pin(build_string_prefix, "")
    return next((dep[len(pin):] for dep in record.get("depends", []) if dep.startswith(pin) and dep != pin), None)


def build_string_prefix(release: str) -> str:
    """A release line's build string prefix: Isabelle2025-2 -> Isabelle2025_2 (conda refuses '-' there)."""
    return release.replace("-", "_")


def feature_pin(version: str, build_string_prefix: str) -> str:
    """A feature package's pin on the package of its base, e.g. `==1 Isabelle2025_2_*`: that version,
    any build of the release line.  make-patches writes it as base_pin; the renderer computes it from
    base_tag (base_pin of releases cut before 2026-10-28 reads `==1=Isabelle2025_2_*`, which conda
    reads the same way and rattler-build refuses)."""
    return f"=={version} {build_string_prefix}_*"


def unzstd(data: bytes) -> bytes:
    """zstd decompression: the standard library's from Python 3.14, else the zstandard module."""
    try:
        from compression import zstd
    except ImportError:
        import zstandard
        return zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data)).read()
    return zstd.decompress(data)


def conda_archive(data: bytes) -> tuple[dict, dict[str, tuple[bytes, int]]]:
    """(info/index.json, {path: (bytes, mode)} of the payload) of a .conda archive: a zip of two
    zstd tarballs."""
    import tarfile
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(data))

    def members(prefix: str) -> dict[str, tuple[bytes, int]]:
        name = next(n for n in z.namelist() if n.startswith(prefix) and n.endswith(".tar.zst"))
        raw = unzstd(z.read(name))
        with tarfile.open(fileobj=io.BytesIO(raw)) as t:
            return {m.name: (t.extractfile(m).read(), m.mode) for m in t.getmembers() if m.isfile()}

    return json.loads(members("info-")["info/index.json"][0]), members("pkg-")


def plan_builds(repodata: dict, wanted: list[Wanted], fetch: Callable[[str], dict | None]) -> dict[str, tuple[str, str | int]]:
    """For every wanted package: ("reuse", <file name on the channel>) or ("build", <build number>).

    Candidates are the channel's indexed records of (name, version) plus the files the channel
    serves but has not indexed yet: `fetch(filename)` returns such a file's index record or None,
    probed from the highest indexed build number + 1 upwards.  A candidate the batch wants is
    reused; a served candidate it does not want is skipped; with no wanted candidate the package
    is built with the next number after everything indexed or served (0 when there is nothing).
    So a dispatch repeated with the same inputs resumes byte for byte."""
    records = {**repodata.get("packages", {}), **repodata.get("packages.conda", {})}
    plan = {}
    for w in wanted:
        candidates = [(fn, rec) for fn, rec in records.items()
                      if rec.get("name") == w.name and rec.get("version") == w.version]
        n = max((int(rec["build_number"]) for _, rec in candidates), default=-1) + 1
        while (rec := fetch(w.filename(n))) is not None:
            candidates.append((w.filename(n), rec))
            n += 1
        matching = [(int(rec["build_number"]), fn) for fn, rec in candidates if w.accepts(rec)]
        plan[w.name] = ("reuse", max(matching)[1]) if matching else ("build", n)
    return plan
