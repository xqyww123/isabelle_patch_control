"""new-tree <feature repository>
new-tree --home <feature repository> --base <R>/<base> <R>/<feature>

The two trees of each feature that a feature repository H registers.  Both are plain clones of
the Isabelle source repository and submodules of H: the private tree worktrees/<R>-<feature> on
branch <R>/<feature>, and the stock tree worktrees/<R>-<feature>-stock, detached at
merge-base(origin/<R>/<base>, <R>/<feature>).  H's .gitmodules gives both `ignore = all` and gives
the private tree `branch` and `base`.

  <feature repository>   for each feature it registers, on its own: a tree whose directory is
                         empty is cloned (`git submodule update --init --remote`); the private
                         tree is switched to its branch; the stock tree moves to the merge base,
                         computed in the private tree after a fetch; both receive the build
                         products of the line's shared tree <H>/../<R>.  The feature repository's
                         init.sh runs this; rerun it after merging a release of the base.
  --home ... --base ...  registers the feature in H: the private tree on the branch from GitHub,
                         or on a new branch at origin/<R>/<base> without upstream (push it with
                         `git push -u origin <R>/<feature>` before H's registration commit), the
                         stock tree, then the above; .gitmodules and both trees are staged in H.

Every step already done is skipped; a tree in another shape is refused, not repaired.
"""
# This docstring is what `new-tree --help` prints; the design is MLML's
# ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md §12, fourth draft, item 6.
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from . import texts
from .dev import exists, git, head_branch, merge_base, run, split_branch, status, tags_at, toplevel
from .errors import Refused

URL = "https://github.com/xqyww123/isabelle-patched.git"
# copied from the shared tree, not linked: `scala_build` rewrites them in place
PRODUCT_COPIES = ("lib/classes", "src/Tools/Demo/lib")


@dataclass(frozen=True)
class Feature:
    """Feature <R>/<name> of the feature repository `home`, on base <R>/<base>."""
    home: Path
    branch: str
    base: str

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

    def stock_commit(self) -> str:
        """Where the stock tree stands and the release's base tag must point: computed in the private
        tree, which may hold an unpushed merge of the base (fetch first to see the base's releases)."""
        return merge_base(self.home / self.path, f"origin/{self.base}", self.branch)


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
            f = Feature(home, e["branch"], e.get("base", ""))
            if f.path != path or "/" not in f.base or split_branch(f.base)[0] != split_branch(f.branch)[0]:
                raise Refused(f"{home}/.gitmodules: {path} needs `branch = <R>/<F>` with path worktrees/<R>-<F> "
                              "and `base = <R>/<base>` of the same line")
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
    target = f.stock_commit()
    stock = clone(f.home, f.stock_path)
    if git("rev-parse", "HEAD", cwd=stock) != target or head_branch(stock):
        if status(stock):
            raise Refused(f"{stock} has uncommitted changes, and it must move to {target[:12]}: a stock tree is not edited")
        if not exists(stock, target):
            git("fetch", "-q", "origin", cwd=stock)
        git("switch", "-q", "--detach", target, cwd=stock)
        print(f"{stock}: moved to {target[:12]}")
    for t in (tree, stock):
        install_products(t, f.shared)
    tags = tags_at(tree, target, f"{f.base}/*")
    print(f"ready: {f.path} on {f.branch}, {f.stock_path} at {target[:12]} = merge-base(origin/{f.base}, {f.branch})"
          + (f", release tag {' '.join(tags)}" if tags else ", not a release of the base"))


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


def register(home: Path, branch: str, base: str):
    if split_branch(base)[0] != split_branch(branch)[0]:
        raise Refused(f"the base {base} is not of {branch}'s release line")
    f = Feature(home, branch, base)
    entries = submodules(home)
    if f.path in entries:
        e = entries[f.path]
        if (e.get("branch"), e.get("base")) != (branch, base):
            raise Refused(f"{home}/.gitmodules registers {f.path} with branch {e.get('branch')} and base {e.get('base')}")
    else:
        on_github = git("ls-remote", URL, f"refs/heads/{branch}", f"refs/heads/{base}", cwd=home).split()
        if f"refs/heads/{base}" not in on_github:
            raise Refused(f"{base} is not on {URL}")
        if f"refs/heads/{branch}" in on_github:
            git("submodule", "add", "-q", "-b", branch, URL, f.path, cwd=home)
        else:
            git("submodule", "add", "-q", URL, f.path, cwd=home)
            git("switch", "-q", "--no-track", "-c", branch, f"origin/{base}", cwd=home / f.path)
            print(f"new branch {branch} at origin/{base}, without upstream: push it with "
                  f"`git -C {home / f.path} push -u origin {branch}` before the registration commit in {home}")
        configure(home, f.path, branch=branch, base=base, ignore="all")
    if f.stock_path not in entries:
        git("submodule", "add", "-q", URL, f.stock_path, cwd=home)
        configure(home, f.stock_path, ignore="all")
    set_up(f)
    git("add", "-f", "--", ".gitmodules", f.path, f.stock_path, cwd=home)     # -f: git 2.54+ skips ignore = all submodules
    print(f"registered {branch} in {home}: .gitmodules and both trees staged")


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
