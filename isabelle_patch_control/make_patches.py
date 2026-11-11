"""make-patches [-C <tree>] --package <dir> [<R>/]<feature> <m>

Release <m> (1, 2, 3, ...) of a feature, run in the feature's private tree <tree> (default: the current
directory).  No network, nothing pushed.  <R> defaults to the release line of the branch checked out
there.  The package directory <dir> lies in the feature repository H that registers the tree (new-tree
--home); it receives patches/<R>/*.patch and patches/<R>/provenance.txt.  The bases are the ones H's
.gitmodules records; branches and tags are the private tree's own (fetch first when a base was
released elsewhere).

Gates, in order, all before anything is written or tagged:
  1. committed files: in H, <dir>'s README.md, tools/patched_files.txt, tools/signature_additions.txt,
     tools/required_sessions.txt and the files tools/component_files.txt lists exist; these and, when
     present, tools/component_files.txt, tools/release_build.sh, tools/license.txt (at most one entry)
     and every LICENSE from <dir> up to H's top are committed and unchanged (see RELEASE.md, "First-time
     setup of a feature repository"); H's .gitmodules registers the feature's two trees and <tree> is the
     private one, clean and on <R>/<feature>, whose tip carries no release tag of this feature yet
     (commit first; an empty commit releases the same sources under the new number).
  2. base tags: for each base, `git merge-base --all origin/<base> <tip>` is one commit and exactly one
     release tag <base>/* points at it.  The base commit is that commit with one base; with several, the
     most recent commit of the tip's history whose parents are exactly those commits (new-tree --merge
     makes it), or that commit itself when they are all one commit, and its tree must be their changes
     put together (it adds nothing to them).  The stock
     tree stands at the base commit (else rerun <H>/init.sh).  Every gate below is relative to it.
  3. changed files: `git diff-tree -r --no-renames --name-only` between the two equals
     tools/patched_files.txt.
  4. signatures: check-signatures with tools/signature_additions.txt.
  5. round trip: the patch files (one `git diff-tree -p` block per file, under its flat name: the path
     with `/` as `-`, plus `.patch`), generated into a temporary directory, replayed through the patch
     tool's directory interface on `git archive <base commit>` forward and backward, compared by tree hash.
Then, each step repeatable after a failure: the package's patches/<R>/ receives the files and the
provenance file; H's release commit is made by path, of those files, .gitmodules and the two trees,
whose gitlinks record the tip and the base commit; the commit to tag (the new one, or the one an
existing tag of this number points at) is checked to hold exactly the generated files, gate 1's files
and those gitlinks; the annotated tag <R>/<feature>/<m> is created in H; and last in the private tree,
whose tag marks the release as done.
"""
# This docstring is what `make-patches --help` prints.  The gates and the write steps are the patch
# tool plan's decision 16 points 7 and 8; a release line's pristine is the official release committed
# as it is, so no gate checks it.
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import check_signatures
from .api import apply_to, unapply_from
from .dev import (build_string_prefix, combine, exists, git, head_branch, listed, patch_blocks, release_inputs, require_committed,
                  rev, run, split_branch, status, tags_at, toplevel)
from .errors import Refused
from .new_tree import registrations


# --- the repository of a tree

def resolve_branch(tree: Path, name: str) -> str:
    if "/" in name:
        split_branch(name)
        return name
    head = head_branch(tree)
    if not head or "/" not in head:
        raise Refused(f"{tree} is not on a <R>/... branch; give the release line as {name}'s prefix")
    return f"{split_branch(head)[0]}/{name}"


def tree_hash_of_dir(tree: Path, directory: Path) -> str:
    """The git tree hash of a directory's content, every file included (ignore rules off),
    through a temporary index of the tree's repository."""
    with tempfile.TemporaryDirectory(prefix="index-") as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index", "GIT_DIR": git("rev-parse", "--absolute-git-dir", cwd=tree),
               "GIT_WORK_TREE": str(directory)}
        run(["git", "add", "-f", "-A", "."], cwd=directory, env=env)
        return run(["git", "write-tree"], cwd=directory, env=env).stdout.strip()


def archive(tree: Path, commit: str, into: Path):
    """`git archive commit` extracted into the directory (modes preserved)."""
    with subprocess.Popen(["git", "archive", "--format=tar", commit], cwd=tree, stdout=subprocess.PIPE) as g:
        subprocess.run(["tar", "-x", "-C", str(into)], stdin=g.stdout, check=True)
        if g.wait():
            raise Refused(f"git archive {commit} failed")


def replay(directory: Path, patches: Path, reverse: bool = False):
    """Gate 5 through the patch tool's directory interface: every patch file of `patches` applied
    to (or reversed from) `directory`, CONFLICT files refused."""
    res = (unapply_from if reverse else apply_to)(directory, patches)
    if res.conflicts:
        files = "".join(f"\n  {lv.target}: " + (next(iter(lv.failures.values()), "").splitlines() or ["?"])[0]
                        for lv in res.conflicts)
        raise Refused(f"gate 5 (round trip): the patches do not {'reverse' if reverse else 'apply'} cleanly:{files}")


# --- the feature repository (decision 16 point 7)

def committed_files(top: Path, commit: str, directory: Path) -> dict[str, str]:
    """path -> blob hash of the files `commit` holds under `directory` of the feature repository."""
    out = {}
    for line in run(["git", "ls-tree", "-r", commit, "--", os.path.relpath(directory, top)], cwd=top).stdout.splitlines():
        meta, path = line.split("\t", 1)
        out[path] = meta.split()[2]
    return out


def feature_release(where: Path, feature: str, m: str, package: Path):
    tree = toplevel(where)
    branch = resolve_branch(tree, feature)
    release, name = split_branch(branch)
    if not re.fullmatch(r"[1-9][0-9]*", m):
        raise Refused(f"the number at the end of the release tag is a positive integer (1, 2, 3, ...), not {m!r}")
    tag = f"{branch}/{m}"

    # 1. the committed files of the feature repository, and the two trees
    top = toplevel(package)
    f = next((f for f in registrations(top) if f.branch == branch), None)
    if f is None:
        raise Refused(f"{top}/.gitmodules does not register {branch} (new-tree --home registers it)")
    if top / f.path != tree:
        raise Refused(f"{tree} is not the private tree of {branch}, {top / f.path}: run make-patches there")
    require_committed(package)
    if head_branch(tree) != branch:
        raise Refused(f"{tree} is not on {branch}")
    if dirty := status(tree):
        raise Refused(f"{tree} has uncommitted changes:\n{dirty}")
    if exists(tree, f"refs/tags/{tag}"):
        raise Refused(f"release tag {tag} already exists")
    tip = rev(tree, branch)
    earlier = tags_at(tree, tip, f"{branch}/*")
    if earlier:
        raise Refused(f"{tip[:12]} already carries release tag {' '.join(earlier)}: commit first (an empty commit "
                      "will do) to release this commit's content again under a new number")
    H = git("rev-parse", "HEAD", cwd=top)
    inputs = [rel for rels in release_inputs(package) for rel in rels]

    # 2. the base tags, and the base commit, where the stock tree stands
    commits = f.merge_bases()
    base_tags = []
    for base, commit in commits.items():
        tags = tags_at(tree, commit, f"{base}/*")
        if len(tags) != 1:
            raise Refused(f"gate 2 (base tags): merge-base(origin/{base}, {branch}) = {commit[:12]} carries {len(tags)} release "
                          f"tags of {base} ({' '.join(tags) or 'none'}), not exactly one: merge a release of {base} "
                          "(fetch first if it was released elsewhere)")
        base_tags += tags
    base_commit = f.stock_commit()
    if len(commits) > 1 and (want := combine(tree, commits)) != git("rev-parse", f"{base_commit}^{{tree}}", cwd=tree):
        more = git("diff-tree", "-r", "--name-only", "--no-renames", want, f"{base_commit}^{{tree}}", cwd=tree).split()
        raise Refused(f"gate 2 (base tags): {base_commit[:12]}, the merge of the bases, holds changes beyond them: {' '.join(more)}")
    stock = top / f.stock_path
    if git("rev-parse", "HEAD", cwd=stock) != base_commit:
        raise Refused(f"gate 2 (base tags): the stock tree {stock} is not at the base commit {base_commit[:12]}: rerun {top}/init.sh")
    print(f"base tags {' '.join(base_tags)}; base commit {base_commit[:12]}, the stock tree's commit")

    # 3. the changed files
    changed = sorted(git("diff-tree", "-r", "--name-only", "--no-renames", base_commit, tip, cwd=tree).split("\n"))
    changed = [c for c in changed if c]
    expected = sorted(listed(package / "tools" / "patched_files.txt"))
    if changed != expected:
        extra = sorted(set(changed) - set(expected))
        missing = sorted(set(expected) - set(changed))
        raise Refused("gate 3 (changed files): the files changed since the base commit are not tools/patched_files.txt:"
                      + "".join(f"\n  changed but not listed: {p}" for p in extra)
                      + "".join(f"\n  listed but unchanged: {p}" for p in missing))
    print(f"gate 3 (changed files): {len(changed)} changed files, exactly tools/patched_files.txt")

    # 4. signatures
    additions = package / "tools" / "signature_additions.txt"
    heads = listed(additions)
    if problems := check_signatures.check(tree, base_commit, tip, heads, str(additions)):
        raise Refused("gate 4 (signatures):\n" + "\n".join(f"ERROR: {p}" for p in problems))
    print(f"gate 4 (signatures): every entry of the base commit unchanged, {len(heads)} additions as listed")

    # provenance
    provenance = [
        f"feature: {branch}",
        f"release_tag: {tag}",
        f"commit: {tip}",
        f"base_tag: {' '.join(base_tags)}",
        f"base_commit: {base_commit}",
        f"build_string_prefix: {build_string_prefix(release)}",
    ]

    with tempfile.TemporaryDirectory(prefix="make-patches-") as tmp:
        # generation, into the temporary directory: the package is not touched before every gate passed
        gen = Path(tmp) / "patches"
        gen.mkdir()
        diff = run(["git", "diff-tree", "-r", "-p", "--no-renames", base_commit, tip], cwd=tree, text=False).stdout
        for file, block in patch_blocks(diff).items():                 # bytes throughout: CRs and non-UTF-8 survive
            (gen / file).write_bytes(block)
        patch_names = sorted(p.name for p in gen.glob("*.patch"))
        print(f"{len(patch_names)} patch files generated")

        # 5. round trip on the base commit's archive through the tool's directory interface, compared by tree hash
        work = Path(tmp) / "tree"
        work.mkdir()
        archive(tree, base_commit, work)
        replay(work, gen)
        got, want = tree_hash_of_dir(tree, work), git("rev-parse", f"{tip}^{{tree}}", cwd=tree)
        if got != want:
            raise Refused(f"gate 5 (round trip): forward application gives tree {got}, the commit's tree is {want}")
        replay(work, gen, reverse=True)
        got, want = tree_hash_of_dir(tree, work), git("rev-parse", f"{base_commit}^{{tree}}", cwd=tree)
        if got != want:
            raise Refused(f"gate 5 (round trip): backward application gives tree {got}, the base commit's tree is {want}")
        print("gate 5 (round trip): the base commit's archive reproduces both trees")
        (gen / "provenance.txt").write_text("\n".join(provenance) + "\n")
        print("\n".join(provenance))

        # write step (b): old patch files go, the generated files and the provenance file come
        out = package / "patches" / release
        out.mkdir(parents=True, exist_ok=True)
        stale = sorted(p.name for p in out.glob("*.patch") if p.name not in patch_names)
        for file in stale:
            (out / file).unlink()
        generated = [*patch_names, "provenance.txt"]
        for file in generated:
            shutil.copy2(gen / file, out / file)
        print(f"{len(patch_names)} patch files written to {out}" + (f"; removed {' '.join(stale)}" if stale else ""))

        # write step (c): staged and committed by path, never by directory (that would sweep in unrelated edits):
        # the files, .gitmodules and the two trees, whose gitlinks record their HEADs (`ignore = all` hides them
        # from a plain `git diff`); the files to remove are the old *.patch of HEAD, not of the disk: a rerun after
        # a failure here sees them too
        paths = [os.path.relpath(out / file, top) for file in generated]
        removed = sorted(p for p in committed_files(top, "HEAD", out) if p.endswith(".patch") and p not in paths)
        trees = [f.path, f.stock_path]
        run(["git", "add", "-f", "--", *paths, ".gitmodules", *trees], cwd=top)     # -f: git 2.54+ skips ignore = all submodules
        if removed:
            run(["git", "rm", "--cached", "-q", "--ignore-unmatch", "--", *removed], cwd=top)
        L = [*paths, *removed, ".gitmodules", *trees]
        if run(["git", "diff", "--cached", "--quiet", "--ignore-submodules=none", "--", *L], cwd=top, check=False).returncode:
            run(["git", "commit", "-q", "-m", f"{name} release {m}: patches/{release}", "--", *L], cwd=top)
            print(f"committed patches/{release} and the two trees' gitlinks in {top}")
        else:
            print(f"patches/{release} and the gitlinks already committed in {top}")

        # write step (d): the commit to tag holds exactly the generated files, gate 1's files as H holds them and the gitlinks
        tag_exists = exists(top, f"refs/tags/{tag}")
        commit = rev(top, f"refs/tags/{tag}" if tag_exists else "HEAD")
        in_commit = committed_files(top, commit, out)
        want = {p: git("hash-object", "--", gen / file, cwd=top) for p, file in zip(paths, generated)}
        differing = sorted(set(in_commit) ^ set(want) | {p for p in want if in_commit.get(p) != want[p]})
        links = {line.split("\t", 1)[1]: line.split()[2] for line in git("ls-tree", commit, "--", *trees, cwd=top).splitlines()}
        differing += [f"{p} (gitlink)" for p, c in zip(trees, (tip, base_commit)) if links.get(p) != c]
        if not differing and (moved := git("diff", "--name-only", H, commit, "--", *inputs, cwd=package).split()):
            differing = ["(gate 1's files)", *moved]
        if differing:
            where = f"release tag {tag} already exists at {commit[:12]} and" if tag_exists else f"commit {commit[:12]}"
            raise Refused(f"{where} does not hold the generated files: {' '.join(differing)}"
                          + (f"\nthis number is spent: release {int(m) + 1}" if tag_exists else ""))

        # write step (e): the feature repository's tag
        if not tag_exists:
            git("tag", "-a", "-m", f"{branch} release {m}\n\n" + "\n".join(provenance), tag, commit, cwd=top)
            print(f"release tag {tag} created in {top} at {commit[:12]}")
        else:
            print(f"release tag {tag} already in {top} at {commit[:12]}")

    # write step (f): the private tree's tag, last: its existence marks the release as done
    git("tag", "-a", "-m", f"{branch} release {m}\n\n" + "\n".join(provenance), tag, tip, cwd=tree)
    print(f"release tag {tag} created in {tree} at {tip[:12]}")
