"""make-patches [-C <tree>] --package <dir> [<R>/]<feature> <version>
make-patches [-C <dir>] --hg <repo> --tarball <file> [<R>/]pristine <hg id>

Release of a feature, run on the owner's order in the feature's private tree <tree> (default:
the current directory).  No network, nothing pushed.
<R> defaults to the release line of the branch checked out there.  The package directory <dir>
lies in the feature repository H that registers the tree (new-tree --home) and holds
tools/patched_files.txt, tools/signature_additions.txt and tools/required_sessions.txt (see
RELEASE.md, "First-time setup of a feature repository"); it receives patches/<R>/*.patch and
patches/<R>/provenance.txt.  The base is the one H's .gitmodules records; branches and tags are
the private tree's own (fetch first when the base was released elsewhere).

Gates, in order, all before anything is written or tagged:
  7. tools/patched_files.txt, signature_additions.txt, required_sessions.txt and, if present,
     tools/component_files.txt with the files it lists are committed and unchanged in H; H's
     .gitmodules registers the feature's two trees and <tree> is the private one, clean and on
     <R>/<feature>, whose tip carries no release tag of this feature yet (commit first).
  0. base tag: `git merge-base --all origin/<base> <tip>` is one commit, exactly one release tag
     <base>/* points at it, and the stock tree stands there (else rerun <H>/init.sh).  Every gate
     below is relative to that tag.
  (f) `git diff-tree -r --no-renames --name-only` between the two equals tools/patched_files.txt.
  (d) check-signatures with tools/signature_additions.txt.
  (c) the patch files (one `git diff-tree -p` block per file, under its flat name: the path with
     `/` as `-`, plus `.patch`), generated into a temporary directory, replayed through the patch
     tool's directory interface on `git archive <base tag>` forward and backward, compared by tree
     hash.
Then, each step repeatable after a failure: the package's
patches/<R>/ receives the files and the provenance file; H's release commit is made by path, of
those files, .gitmodules and the two trees, whose gitlinks record the tip and the base tag's
commit; the commit to tag (the new one, or the one an existing tag of this version points at) is
checked to hold exactly the generated files, the gates' component files and those gitlinks; the
annotated tag <R>/<feature>/<version> is created in H; and last in the private tree, whose tag
marks the release as done.

`pristine <hg id>` runs check (a) only, in the repository of <dir>: the tip of
<R>/pristine equals the hg tag <R> minus Admin/, README_REPOSITORY and .hg*, plus the five release
text files of the official tarball and the commit's own .gitignore; then tags <R>/pristine/<hg id>.
"""
# This docstring is what `make-patches --help` prints.  Gate numbers 7, 0 and the letters (f), (d),
# (c) are MLML's ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md §5.1's, check (a) its §5.2 (gates 1 and
# (e) are gone since §12's fourth draft, item 6); the write steps are the patch tool plan's decision
# 16 point 8.
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from . import check_signatures
from .api import apply_to, unapply_from
from .dev import (build_string_prefix, exists, feature_pin, git, head_branch, listed, patch_blocks, rev, run,
                  shipped_files, split_branch, status, tags_at, toplevel)
from .errors import Refused
from .new_tree import registrations

# paths git tracks that an hg checkout of the release does not have, or has differently; the CI
# build assertion hashes its hg checkout minus Admin/, README_REPOSITORY and .hg* and compares
TREE_HASH_EXCLUDES = [".gitignore", "Isabelle.options", "etc/ISABELLE_ID", "etc/ISABELLE_TAGS",
                      "etc/components", "lib/scripts/Isabelle_app"]
RELEASE_FILES = ["etc/ISABELLE_ID", "etc/ISABELLE_TAGS", "etc/components", "lib/scripts/Isabelle_app", "Isabelle.options"]
HG_ONLY = ["Admin", "README_REPOSITORY", ".hg_archival.txt", ".hgignore", ".hgtags"]


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


def tree_hash_excluding(tree: Path, commit: str, excludes: list[str]) -> str:
    """The tree hash of commit's tracked files minus the excluded paths."""
    with tempfile.TemporaryDirectory(prefix="index-") as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index"}
        run(["git", "read-tree", commit], cwd=tree, env=env)
        if excludes:
            run(["git", "update-index", "--force-remove", "--", *excludes], cwd=tree, env=env)
        return run(["git", "write-tree"], cwd=tree, env=env).stdout.strip()


def archive(tree: Path, commit: str, into: Path):
    """`git archive commit` extracted into the directory (modes preserved)."""
    with subprocess.Popen(["git", "archive", "--format=tar", commit], cwd=tree, stdout=subprocess.PIPE) as g:
        subprocess.run(["tar", "-x", "-C", str(into)], stdin=g.stdout, check=True)
        if g.wait():
            raise Refused(f"git archive {commit} failed")


def replay(directory: Path, patches: Path, reverse: bool = False):
    """Gate (c) through the patch tool's directory interface: every patch file of `patches` applied
    to (or reversed from) `directory`, CONFLICT files refused."""
    res = (unapply_from if reverse else apply_to)(directory, patches)
    if res.conflicts:
        files = "".join(f"\n  {lv.target}: " + (next(iter(lv.failures.values()), "").splitlines() or ["?"])[0]
                        for lv in res.conflicts)
        raise Refused(f"gate (c): the patches do not {'reverse' if reverse else 'apply'} cleanly:{files}")


# --- the feature repository (decision 16 point 7)

def require_committed(top: Path, paths: list[Path]):
    rel = [os.path.relpath(p, top) for p in paths]
    for p, r in zip(paths, rel):
        if not p.is_file():
            raise Refused(f"{p} is missing")
        if run(["git", "ls-files", "--error-unmatch", "--", r], cwd=top, check=False).returncode:
            raise Refused(f"{p} is not committed in the feature repository {top}: commit it first")
    dirty = run(["git", "status", "--porcelain", "--", *rel], cwd=top).stdout
    if dirty:
        raise Refused(f"uncommitted changes in the feature repository {top}: commit them first\n{dirty.rstrip()}")


def committed_files(top: Path, commit: str, directory: Path) -> dict[str, str]:
    """path -> blob hash of the files `commit` holds under `directory` of the feature repository."""
    out = {}
    for line in run(["git", "ls-tree", "-r", commit, "--", os.path.relpath(directory, top)], cwd=top).stdout.splitlines():
        meta, path = line.split("\t", 1)
        out[path] = meta.split()[2]
    return out


def feature_release(where: Path, feature: str, version: str, package: Path):
    tree = toplevel(where)
    branch = resolve_branch(tree, feature)
    release, name = split_branch(branch)
    if not re.fullmatch(r"[1-9][0-9]*", version):
        raise Refused(f"the version is a positive integer, not {version!r}")
    tag = f"{branch}/{version}"

    # 7. the feature repository and the two trees
    top = toplevel(package)
    f = next((f for f in registrations(top) if f.branch == branch), None)
    if f is None:
        raise Refused(f"{top}/.gitmodules does not register {branch} (new-tree --home registers it)")
    if top / f.path != tree:
        raise Refused(f"{tree} is not the private tree of {branch}, {top / f.path}: run make-patches there")
    shipped = [package / rel for rel in shipped_files(package)]
    lists = [package / "tools" / n for n in ("patched_files.txt", "signature_additions.txt", "required_sessions.txt")]
    require_committed(top, [*lists, *shipped])
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
                      "will do) to release this commit's content again under a new version")
    H = git("rev-parse", "HEAD", cwd=top)
    shipped_rel = [os.path.relpath(p, top) for p in shipped]

    # 0. the base tag, where the stock tree stands
    base = f.base
    base_commit = f.stock_commit()
    base_tags = tags_at(tree, base_commit, f"{base}/*")
    if len(base_tags) != 1:
        raise Refused(f"gate 0: merge-base(origin/{base}, {branch}) = {base_commit[:12]} carries {len(base_tags)} release "
                      f"tags of {base} ({' '.join(base_tags) or 'none'}), not exactly one: merge a release of {base} "
                      "(fetch first if it was released elsewhere)")
    base_tag = base_tags[0]
    stock = top / f.stock_path
    if git("rev-parse", "HEAD", cwd=stock) != base_commit:
        raise Refused(f"gate 0: the stock tree {stock} is not at {base_tag} ({base_commit[:12]}): rerun {top}/init.sh")
    print(f"base tag {base_tag} at {base_commit[:12]}, the stock tree's commit")

    # (f) the changed files
    changed = sorted(git("diff-tree", "-r", "--name-only", "--no-renames", base_tag, tip, cwd=tree).split("\n"))
    changed = [c for c in changed if c]
    expected = sorted(listed(package / "tools" / "patched_files.txt"))
    if changed != expected:
        extra = sorted(set(changed) - set(expected))
        missing = sorted(set(expected) - set(changed))
        raise Refused("gate (f): the files changed since the base tag are not tools/patched_files.txt:"
                      + "".join(f"\n  changed but not listed: {p}" for p in extra)
                      + "".join(f"\n  listed but unchanged: {p}" for p in missing))
    print(f"gate (f): {len(changed)} changed files, exactly tools/patched_files.txt")

    # (d) signatures
    additions = package / "tools" / "signature_additions.txt"
    heads = listed(additions)
    if problems := check_signatures.check(tree, base_tag, tip, heads, str(additions)):
        raise Refused("gate (d):\n" + "\n".join(f"ERROR: {p}" for p in problems))
    print(f"gate (d): signature sections: every entry of {base_tag} unchanged, {len(heads)} additions as listed")

    # provenance
    tree_hash = tree_hash_excluding(tree, tip, TREE_HASH_EXCLUDES)
    build_prefix = build_string_prefix(release)
    base_version = base_tag.rsplit("/", 1)[1]
    base_is_pristine = split_branch(base)[1] == "pristine"
    provenance = [
        f"feature: {branch}",
        f"release_tag: {tag}",
        f"commit: {tip}",
        f"base_tag: {base_tag}",
        f"base_commit: {base_commit}",
        f"base_package_version: {'none (the base is pristine)' if base_is_pristine else base_version}",
        f"base_pin: {'none' if base_is_pristine else feature_pin(base_version, build_prefix)}",
        f"build_string_prefix: {build_prefix}",
        f"tree_hash: {tree_hash}",
        f"tree_hash_excludes: {' '.join(TREE_HASH_EXCLUDES)}",
    ]

    with tempfile.TemporaryDirectory(prefix="make-patches-") as tmp:
        # generation, into the temporary directory: the package is not touched before every gate passed
        gen = Path(tmp) / "patches"
        gen.mkdir()
        diff = run(["git", "diff-tree", "-r", "-p", "--no-renames", base_tag, tip], cwd=tree, text=False).stdout
        for file, block in patch_blocks(diff).items():                 # bytes throughout: CRs and non-UTF-8 survive
            (gen / file).write_bytes(block)
        patch_names = sorted(p.name for p in gen.glob("*.patch"))
        print(f"{len(patch_names)} patch files generated")

        # (c) round trip on the base tag's archive through the tool's directory interface, compared by tree hash
        work = Path(tmp) / "tree"
        work.mkdir()
        archive(tree, base_tag, work)
        replay(work, gen)
        got, want = tree_hash_of_dir(tree, work), git("rev-parse", f"{tip}^{{tree}}", cwd=tree)
        if got != want:
            raise Refused(f"gate (c): forward application gives tree {got}, the commit's tree is {want}")
        replay(work, gen, reverse=True)
        got, want = tree_hash_of_dir(tree, work), git("rev-parse", f"{base_tag}^{{tree}}", cwd=tree)
        if got != want:
            raise Refused(f"gate (c): backward application gives tree {got}, the base tag's tree is {want}")
        print("gate (c): round trip on the base tag's archive reproduces both trees")
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
            run(["git", "commit", "-q", "-m", f"{name} release {version}: patches/{release}", "--", *L], cwd=top)
            print(f"committed patches/{release} and the two trees' gitlinks in {top}")
        else:
            print(f"patches/{release} and the gitlinks already committed in {top}")

        # write step (d): the commit to tag holds exactly the generated files, the gates' component files and the gitlinks
        tag_exists = exists(top, f"refs/tags/{tag}")
        commit = rev(top, f"refs/tags/{tag}" if tag_exists else "HEAD")
        in_commit = committed_files(top, commit, out)
        want = {p: git("hash-object", "--", gen / file, cwd=top) for p, file in zip(paths, generated)}
        differing = sorted(set(in_commit) ^ set(want) | {p for p in want if in_commit.get(p) != want[p]})
        links = {line.split("\t", 1)[1]: line.split()[2] for line in git("ls-tree", commit, "--", *trees, cwd=top).splitlines()}
        differing += [f"{p} (gitlink)" for p, c in zip(trees, (tip, base_commit)) if links.get(p) != c]
        if not differing and shipped_rel and run(["git", "diff", "--quiet", H, commit, "--", *shipped_rel], cwd=top, check=False).returncode:
            differing = ["(component files)", *shipped_rel]
        if differing:
            where = f"release tag {tag} already exists at {commit[:12]} and" if tag_exists else f"commit {commit[:12]}"
            raise Refused(f"{where} does not hold the generated files: {' '.join(differing)}"
                          + (f"\nthis version number is spent: release {int(version) + 1}" if tag_exists else ""))

        # write step (e): the feature repository's tag
        if not tag_exists:
            git("tag", "-a", "-m", f"{branch} release {version}\n\n" + "\n".join(provenance), tag, commit, cwd=top)
            print(f"release tag {tag} created in {top} at {commit[:12]}")
        else:
            print(f"release tag {tag} already in {top} at {commit[:12]}")

    # write step (f): the private tree's tag, last: its existence marks the release as done
    git("tag", "-a", "-m", f"{branch} release {version}\n\n" + "\n".join(provenance), tag, tip, cwd=tree)
    print(f"release tag {tag} created in {tree} at {tip[:12]}")


def pristine_release(where: Path, feature: str, hg_id: str, hg_repo: Path, tarball: Path):
    tree = toplevel(where)
    branch = resolve_branch(tree, feature)
    release = split_branch(branch)[0]
    if not exists(tree, branch):
        raise Refused(f"{branch} does not exist")
    tip = rev(tree, branch)
    tag = f"{branch}/{hg_id}"
    node = run(["hg", "-R", hg_repo, "log", "-r", f"tag('{release}')", "--template", "{node|short}"]).stdout.strip()
    tags = run(["hg", "-R", hg_repo, "log", "-r", f"tag('{release}')", "--template", "{tags}"]).stdout.strip()
    if node != hg_id:
        raise Refused(f"hg tag {release} is changeset {node}, not {hg_id}")
    with tempfile.TemporaryDirectory(prefix="make-patches-") as tmp:
        expected = Path(tmp) / "expected"
        run(["hg", "-R", hg_repo, "archive", "-r", f"tag('{release}')", "-t", "files", expected])
        for p in HG_ONLY:
            path = expected / p
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        with tarfile.open(tarball) as tf:
            for f in RELEASE_FILES:
                try:
                    member = tf.getmember(f"{release}/{f}")
                except KeyError:
                    raise Refused(f"{tarball} has no {release}/{f}")
                (expected / f).parent.mkdir(parents=True, exist_ok=True)
                (expected / f).write_bytes(tf.extractfile(member).read())
                os.chmod(expected / f, member.mode & 0o777)   # the executable bit is part of the tree hash
        (expected / ".gitignore").write_text(run(["git", "show", f"{tip}:.gitignore"], cwd=tree).stdout)
        for f, want in (("etc/ISABELLE_ID", node), ("etc/ISABELLE_TAGS", tags)):
            got = (expected / f).read_text().strip()
            if got != want:
                raise Refused(f"check (a): the tarball's {f} is {got!r}, hg says {want!r}")
        got, want = tree_hash_of_dir(tree, expected), git("rev-parse", f"{tip}^{{tree}}", cwd=tree)
    if got != want:
        raise Refused(f"check (a): {branch} ({tip[:12]}) has tree {want}; hg tag {release} plus the release files "
                      f"of {tarball.name} has tree {got}")
    print(f"check (a): {branch} at {tip[:12]} equals hg {release} ({node}) plus the five release text files "
          f"of {tarball.name} and .gitignore")
    if exists(tree, tag):
        if rev(tree, tag) != tip:
            raise Refused(f"{tag} exists but points at {rev(tree, tag)[:12]}, not {tip[:12]}")
        print(f"release tag {tag} already exists at {tip[:12]}")
    else:
        git("tag", "-a", "-m", f"{release} pristine, hg changeset {hg_id}", tag, tip, cwd=tree)
        print(f"release tag {tag} created at {tip[:12]}")
