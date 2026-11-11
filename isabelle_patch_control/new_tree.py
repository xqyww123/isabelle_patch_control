"""new-tree <feature repository>
new-tree --home <feature repository> --base <R>/<base> [--base <R>/<base> ...] <R>/<feature>
new-tree --home <feature repository> --merge <R>/<base> [--merge <R>/<base> ...] <R>/<feature>

The two trees of each feature that a feature repository H registers.  Both are plain clones of
the Isabelle source repository (the origin of the line's shared tree <H>/../<R>) and submodules of
H: the private tree worktrees/<R>-<feature> on branch <R>/<feature>, and the stock tree
worktrees/<R>-<feature>-stock, detached at the base commit: with one base,
merge-base(origin/<R>/<base>, <R>/<feature>); with several, the most recent commit of the branch
whose parents are exactly the merge bases of the branch with each base, which --merge makes, or that
commit itself when they are all one commit.  H's
.gitmodules gives both `ignore = all` and gives the private tree `branch` and `base` (the bases,
separated by spaces).

  <feature repository>   for each feature it registers, on its own: a tree whose directory is
                         empty is cloned (`git submodule update --init --remote`); the private
                         tree is switched to its branch; both receive the build products of the
                         shared tree; the stock tree moves to the base commit, computed in the
                         private tree after a fetch.  The feature repository's init.sh runs this;
                         rerun it after merging a release of a base.
  --home ... --base ...  registers the feature in H: the private tree on the branch from GitHub,
                         or on a new branch without upstream at origin/<R>/<base> (several bases:
                         at their branch tips put together as --merge does it, a commit that merges
                         them or that commit itself when they are all one commit; push
                         it with `git push -u origin <R>/<feature>` before H's registration
                         commit), the stock tree, then the above; .gitmodules and both trees are
                         staged in H.
  --home ... --merge ... after a fetch, takes each named base at its branch tip and every other
                         base at the last commit of it that the branch and those tips contain;
                         with several bases, makes a commit (your git identity) whose parents are
                         exactly these commits and whose tree is their changes put together, which
                         must apply in every order with the same result, or names the branch's
                         commit that already merges exactly them, or that commit itself when they
                         are all one commit; prints it and the
                         `git merge --no-commit` that takes it into the branch.  Writes only that
                         commit into the private tree's repository.

Every step already done is skipped; a tree in another shape is refused, not repaired.
"""
# This docstring is what `new-tree --help` prints.
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from . import texts
from .dev import exists, git, head_branch, merge_base, merge_commit, rev, run, split_branch, status, tags_at, toplevel
from .errors import Refused

# copied from the shared tree, not linked: `scala_build` rewrites them in place
PRODUCT_COPIES = ("lib/classes", "src/Tools/Demo/lib")


@dataclass(frozen=True)
class Feature:
    """Feature <R>/<name> of the feature repository `home`, on bases <R>/<base> ..."""
    home: Path
    branch: str
    bases: tuple[str, ...]

    @property
    def path(self) -> str:
        return "worktrees/" + "-".join(split_branch(self.branch))

    @property
    def stock_path(self) -> str:
        return self.path + "-stock"

    @property
    def shared(self) -> Path:
        """The line's shared tree, next to the feature repository."""
        return self.home.parent / split_branch(self.branch)[0]

    @property
    def url(self) -> str:
        """The Isabelle repository: the shared tree's origin."""
        return git("config", "--get", "remote.origin.url", cwd=self.shared)

    def merge_bases(self, *also: str) -> dict[str, str]:
        """Each base's last commit that the branch (and `also`) contain, computed in the private tree,
        which may hold an unpushed merge (fetch first to see the bases' releases)."""
        return {b: merge_base(self.home / self.path, f"origin/{b}", self.branch, *also) for b in self.bases}

    def base_commit(self, commits: dict[str, str]) -> str | None:
        """The base commit for the bases' last merged commits `commits`: one commit is itself; several,
        the most recent commit of the branch whose parents are exactly them; None when there is none."""
        distinct = set(commits.values())
        if len(distinct) == 1:
            return distinct.pop()
        for line in git("rev-list", "--merges", "--parents", self.branch, cwd=self.home / self.path).splitlines():
            c, *parents = line.split()
            if set(parents) == distinct:
                return c
        return None

    def stock_commit(self) -> str:
        """The base commit, where the stock tree stands and the release's patches are cut from."""
        commits = self.merge_bases()
        if (c := self.base_commit(commits)) is None:
            raise Refused(f"no commit of {self.branch} merges exactly the last merged commits of its bases "
                          f"({', '.join(f'{b} {c[:12]}' for b, c in commits.items())}): merge the bases with "
                          f"new-tree --merge (SKILL 3.3)")
        return c

    def merge_message(self, commits: dict[str, str]) -> str:
        return f"Merge the bases of {self.branch}: " + ", ".join(f"{b} {c[:12]}" for b, c in commits.items())


def feature_home(path: Path) -> Path:
    home = path.resolve()
    if toplevel(home) != home:
        raise Refused(f"{home} is not the top directory of a git repository (a feature repository)")
    return home


def submodules(home: Path) -> dict[str, dict[str, str]]:
    """The entries of H's .gitmodules as it is on disk: path -> {key: value}."""
    entries = {}
    if (home / ".gitmodules").is_file():
        for item in git("config", "-f", ".gitmodules", "-z", "--list", cwd=home).split("\0"):
            key, _, value = item.partition("\n")
            if key.startswith("submodule."):
                name, _, k = key.removeprefix("submodule.").rpartition(".")
                entries.setdefault(name, {})[k] = value
    return {e["path"]: e for e in entries.values() if "path" in e}


def registrations(home: Path) -> list[Feature]:
    """The features H registers, each with both trees; another entry under worktrees/ is refused."""
    trees = {p: e for p, e in submodules(home).items() if p.startswith("worktrees/")}
    features = []
    for path, e in sorted(trees.items()):
        if "branch" in e:
            f = Feature(home, e["branch"], tuple(e.get("base", "").split()))
            if f.path != path or not f.bases or any("/" not in b or split_branch(b)[0] != split_branch(f.branch)[0] for b in f.bases):
                raise Refused(f"{home}/.gitmodules: {path} needs `branch = <R>/<F>` with path worktrees/<R>-<F> "
                              "and `base =` one or more <R>/<base> of the same line, separated by spaces")
            features.append(f)
    privates = {f.path for f in features}
    for path in trees:
        if path not in privates and not (path.endswith("-stock") and path.removesuffix("-stock") in privates):
            raise Refused(f"{home}/.gitmodules: {path} is neither a private tree (with branch and base) nor its stock tree")
    if missing := [f.path for f in features if f.stock_path not in trees]:
        raise Refused(f"{home}/.gitmodules registers no stock tree for {' '.join(missing)}")
    if not features:
        raise Refused(f"{home} registers no trees: new-tree --home registers a feature's")
    return features


def set_up_all(home: Path):
    refused = []
    for f in registrations(home):
        try:
            set_up(f)
        except Refused as e:
            print(f"{texts.PREFIX}{f.branch}: {e}", file=sys.stderr)
            refused.append(f.branch)
    if refused:
        raise Refused(f"not set up: {' '.join(refused)}")


def set_up(f: Feature):
    tree = clone(f.home, f.path)
    if head_branch(tree) != f.branch:
        git("switch", "-q", f.branch, cwd=tree)
        print(f"{tree}: switched to {f.branch}")
    git("fetch", "-q", "origin", cwd=tree)
    stock = clone(f.home, f.stock_path)
    for t in (tree, stock):
        install_products(t, f.shared)
    target = f.stock_commit()
    if git("rev-parse", "HEAD", cwd=stock) != target or head_branch(stock):
        if status(stock):
            raise Refused(f"{stock} has uncommitted changes, and it must move to {target[:12]}: a stock tree is not edited")
        if not exists(stock, target):
            git("fetch", "-q", str(tree), target, cwd=stock)
        git("switch", "-q", "--detach", target, cwd=stock)
        print(f"{stock}: moved to {target[:12]}")
    print(f"ready: {f.path} on {f.branch}, {f.stock_path} at {target}: {describe(tree, f.merge_bases())}")


def release(tree: Path, base: str, commit: str) -> str:
    tags = tags_at(tree, commit, f"{base}/*")
    return f"release tag {' '.join(tags)}" if tags else "not a release of the base"


def describe(tree: Path, commits: dict[str, str]) -> str:
    """Each base's commit with its release tag, or that it is not a release of the base."""
    return "; ".join(f"{b} at {c[:12]}, {release(tree, b, c)}" for b, c in commits.items())


def clone(home: Path, path: str) -> Path:
    """H's clone at `path`, cloned while its directory is empty: `--remote`, because the gitlink may
    name a commit that is not on GitHub yet."""
    tree = home / path
    if not tree.is_dir() or not any(tree.iterdir()):
        git("submodule", "update", "--init", "--remote", "--", path, cwd=home)
        print(f"{tree}: cloned")
    elif toplevel(tree) != tree:
        raise Refused(f"{tree} is not empty and not a clone")
    return tree


def register(home: Path, branch: str, bases: list[str]):
    for base in bases:
        if split_branch(base)[0] != split_branch(branch)[0]:
            raise Refused(f"the base {base} is not of {branch}'s release line")
    f = Feature(home, branch, tuple(bases))
    entries = submodules(home)
    if f.path in entries:
        e = entries[f.path]
        if (e.get("branch"), e.get("base", "").split()) != (branch, bases):
            raise Refused(f"{home}/.gitmodules registers {f.path} with branch {e.get('branch')} and base {e.get('base')}")
    else:
        url = f.url
        on_github = git("ls-remote", url, f"refs/heads/{branch}", *(f"refs/heads/{b}" for b in bases), cwd=home).split()
        for base in bases:
            if f"refs/heads/{base}" not in on_github:
                raise Refused(f"{base} is not on {url}")
        if f"refs/heads/{branch}" in on_github:
            git("submodule", "add", "-q", "-b", branch, url, f.path, cwd=home)
        else:
            git("fetch", "-q", "origin", cwd=f.shared)                # the start, before anything is registered
            tips = {b: rev(f.shared, f"origin/{b}") for b in bases}
            start = merge_commit(f.shared, tips, f.merge_message(tips))
            git("submodule", "add", "-q", url, f.path, cwd=home)
            tree = home / f.path
            if not exists(tree, start):
                git("fetch", "-q", str(f.shared), start, cwd=tree)
            git("switch", "-q", "--no-track", "-c", branch, start, cwd=tree)
            merged = " merged" if start not in tips.values() else ""
            print(f"new branch {branch} at {' and '.join(f'origin/{b}' for b in bases)}{merged}, "
                  f"without upstream: push it with `git -C {tree} push -u origin {branch}` before the registration commit in {home}")
        configure(home, f.path, branch=branch, base=" ".join(bases), ignore="all")
    if f.stock_path not in entries:
        git("submodule", "add", "-q", f.url, f.stock_path, cwd=home)
        configure(home, f.stock_path, ignore="all")
    set_up(f)
    git("add", "-f", "--", ".gitmodules", f.path, f.stock_path, cwd=home)     # -f: git 2.54+ skips ignore = all submodules
    print(f"registered {branch} in {home}: .gitmodules and both trees staged")


def merge(home: Path, branch: str, named: list[str]):
    """--merge: the commit that takes the named bases' branch tips into `branch` (see the module's
    docstring)."""
    f = next((f for f in registrations(home) if f.branch == branch), None)
    if f is None:
        raise Refused(f"{home}/.gitmodules does not register {branch}")
    if unknown := [n for n in named if n not in f.bases]:
        raise Refused(f"{' '.join(unknown)}: not a base of {branch} (its bases: {' '.join(f.bases)})")
    tree = home / f.path
    git("fetch", "-q", "origin", cwd=tree)
    commits = f.merge_bases(*(f"origin/{n}" for n in named))
    for b, c in commits.items():
        merged = run(["git", "merge-base", "--is-ancestor", c, f.branch], cwd=tree, check=False).returncode == 0
        note = "" if b in named else " (already merged)" if merged else " (comes with the bases named)"
        print(f"{b}: {c[:12]}{note}, {release(tree, b, c)}")
    commit = f.base_commit(commits) or merge_commit(tree, commits, f.merge_message(commits))
    print(f"the merge of {branch}'s bases: {commit}")
    print(f"now run: git -C {tree} merge --no-commit {commit}")


def configure(home: Path, path: str, **keys: str):
    for key, value in keys.items():
        git("config", "-f", ".gitmodules", f"submodule.{path}.{key}", value, cwd=home)


# --- what a tree takes from its line's shared tree

def install_products(tree: Path, shared: Path):
    """Idempotent: `contrib` linked into the shared tree, the jar directories copied, and
    etc/ISABELLE_IDENTIFIER = the directory name."""
    if not ((shared / "contrib").is_dir() and (shared / "lib" / "classes").is_dir()):
        raise Refused(f"{shared} has no build products (contrib/, lib/classes/): new-tree expects the line's shared tree there")
    link(tree / "contrib", os.path.relpath(shared / "contrib", tree))
    for p in PRODUCT_COPIES:
        copy_dir(tree / p, shared / p)
    identifier = tree / "etc" / "ISABELLE_IDENTIFIER"            # as the release writes it: no newline
    if not identifier.is_file() or identifier.read_text() != tree.name:
        identifier.write_text(tree.name)


def link(path: Path, target: str):
    if path.is_symlink():
        if os.readlink(path) == target:
            return
        raise Refused(f"{path} links to {os.readlink(path)}, expected {target}")
    if path.exists():
        raise Refused(f"{path} exists and is not the expected symlink to {target}")
    path.symlink_to(target)


def copy_dir(path: Path, source: Path):
    if path.is_symlink():
        raise Refused(f"{path} must be a real directory, not a symlink (scala_build rewrites it in place)")
    if path.exists():
        return
    if not source.is_dir():
        raise Refused(f"{source} is missing: the shared tree has no build products to copy")
    path.parent.mkdir(parents=True, exist_ok=True)
    run(["cp", "-a", source, path])
