"""Toy Isabelle trees and toy feature chains for the pytest suite (plan decision 15).

A `Toy` holds a git repository that plays the Isabelle source repository: the pristine commit is
tagged `<R>/pristine/<id>`, every feature is one commit tagged `<R>/<name>/1`, and its feature
directory is written the way make-patches writes it (one `git diff-tree -p` block per changed
path, flat file names, a provenance file).  Trees are `git archive` extractions of a tag.
No Isabelle is needed and nothing runs `isabelle`.
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from common import patch_blocks  # noqa: E402  (the fixture cuts patch files the way make-patches does)
from isabelle_patch_control import api, cli  # noqa: E402

RELEASE = "Isabelle2025-2"
PRISTINE_ID = "89701cf1768e"
OLD_BUILD_ID = "5533cd83156e"
GIT_ENV = dict(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_ATTR_NOSYSTEM="1", GIT_AUTHOR_NAME="t",
               GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
GIT_FLAGS = ["-c", "core.autocrlf=false", "-c", f"core.attributesFile={os.devnull}", "-c", "tar.umask=022"]


def git_env() -> dict:
    """The fixtures' own git must not see the hostile settings some tests put into the environment."""
    return {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **GIT_ENV}

PRISTINE_FILES = {
    "etc/ISABELLE_IDENTIFIER": RELEASE,                    # the release writes it without a newline
    "etc/ISABELLE_ID": PRISTINE_ID + "\n",
    "etc/options": "option ML_system_64 : bool = true\n",
    "src/Pure/a.ML": "".join(f"a{i}\n" for i in range(1, 13)),
    "src/Pure/b.ML": "".join(f"b{i}\n" for i in range(1, 13)),
    "src/Pure/c.ML": "c1\nc2\n",
    "bin/tool": "#!/bin/sh\necho tool\n",
    "README": "readme without trailing newline",
}
EXECUTABLE = {"bin/tool", "src/Pure/c.ML"}       # c.ML: f1 deletes a 0755 file, unapply restores it


class Toy:
    def __init__(self, root: Path):
        self.root = root
        self.repo = root / "repo"
        self.features_d = root / "features.d"
        self.features_d.mkdir()
        self.repo.mkdir()
        self.trees = 0
        self.tags = [f"{RELEASE}/pristine/{PRISTINE_ID}"]      # bottom first
        self.names: list[str] = []
        self.git("init", "-q")
        for rel, text in PRISTINE_FILES.items():
            self.write(rel, text, mode=0o755 if rel in EXECUTABLE else None)
        self.git("add", "-A")
        self.git("commit", "-qm", "pristine")
        self.git("tag", self.tags[0])

    # --- the repository
    def git(self, *args, text: bool = True) -> str | bytes:
        r = subprocess.run(["git", *GIT_FLAGS, *args], cwd=self.repo, env=git_env(), text=text,
                           capture_output=True, check=True)
        return r.stdout

    def write(self, rel: str, text: str | bytes, mode: int | None = None):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode() if isinstance(text, str) else text)
        if mode is not None:
            p.chmod(mode)

    def edit(self, rel: str, fn):
        p = self.repo / rel
        p.write_text(fn(p.read_text()))

    def delete(self, rel: str):
        (self.repo / rel).unlink()

    def feature(self, name: str, changes, version: str = "1") -> Path:
        """Commit `changes()` as feature `name` on top of the chain and write its feature directory."""
        changes()
        self.git("add", "-A")
        self.git("commit", "-qm", name)
        tag = f"{RELEASE}/{name}/{version}"
        self.git("tag", tag)
        base = self.tags[-1]
        d = self.features_d / name
        d.mkdir()
        diff = self.git("diff-tree", "-r", "-p", "--no-renames", base, tag, text=False)
        for file, block in patch_blocks(diff).items():
            (d / file).write_bytes(block)
        (d / "provenance.txt").write_text(
            f"feature: {RELEASE}/{name}\nrelease_tag: {tag}\ncommit: {self.git('rev-parse', tag).strip()}\n"
            f"base_tag: {base}\nbase_commit: {self.git('rev-parse', base).strip()}\n"
            f"base_package_version: none\nbase_pin: none\nbuild_string_prefix: Isabelle2025_2\n"
            f"tree_hash: x\ntree_hash_excludes: x\n")
        self.tags.append(tag)
        self.names.append(name)
        return d

    def standard_chain(self):
        """f1, f2, f3: a modified, a created, a deleted and a non-source file; an executable; a
        file without a trailing newline; f3's hunk on a.ML has f1's added line as context, and
        a.ML is touched by features 1 and 3 (feature numbers differ from touch order)."""
        def f1():
            self.edit("src/Pure/a.ML", lambda s: s.replace("a3\n", "a3\nF1\n"))
            self.write("src/Pure/new1.ML", "new1 line\n")
            self.delete("src/Pure/c.ML")
            self.edit("etc/options", lambda s: s + "option f1 : bool = true\n")

        def f2():
            self.edit("src/Pure/b.ML", lambda s: s.replace("b5\n", "B5\n"))
            self.write("bin/new2", "#!/bin/sh\necho new2\n", mode=0o755)
            self.edit("README", lambda s: s + " (f2)")

        def f3():
            self.edit("src/Pure/a.ML", lambda s: s.replace("F1\na4\n", "F1\nF3\na4\n"))
            self.edit("src/Pure/new1.ML", lambda s: s + "f3 addition\n")

        self.feature("f1", f1)
        self.feature("f2", f2)
        self.feature("f3", f3)
        return self

    # --- trees
    def tag_of(self, name: str | None) -> str:
        return self.tags[0] if name is None else self.tags[self.names.index(name) + 1]

    def tree(self, at: str | None = None, name: str | None = None) -> Path:
        """A tree at the level of feature `at` (None: pristine), extracted from the archive."""
        self.trees += 1
        d = self.root / (name or f"tree{self.trees}")
        d.mkdir()
        # tar.umask=022 (GIT_FLAGS): files 0644/0755 like the conda package's, not git archive's 0664/0775
        tar = subprocess.run(["git", *GIT_FLAGS, "archive", "--format=tar", self.tag_of(at)], cwd=self.repo,
                             capture_output=True, check=True, env=git_env()).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            tf.extractall(d, filter="fully_trusted")
        return d

    def expected(self, at: str | None) -> dict[str, tuple[bytes, int]]:
        d = self.tree(at, name=f"expected-{at or 'pristine'}-{self.trees + 1}")
        return snapshot(d)

    def old_build_tree(self) -> Path:
        d = self.tree()
        (d / "etc" / "ISABELLE_ID").write_text(OLD_BUILD_ID + "\n")
        return d


def snapshot(d: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under d: content and permission bits."""
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and not p.is_symlink():
            out[p.relative_to(d).as_posix()] = (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
    return out


def same_tree(d: Path, expected: dict, *, modes: bool = True, ignore=("etc/ISABELLE_ID",)):
    got = snapshot(d)
    assert set(got) == set(expected), (set(got) ^ set(expected))
    for rel in expected:
        if rel in ignore:
            continue
        assert got[rel][0] == expected[rel][0], rel
        if modes:
            assert got[rel][1] == expected[rel][1], (rel, oct(got[rel][1]), oct(expected[rel][1]))


class Result:
    def __init__(self, code: int, out: str, err: str):
        self.code, self.out, self.err = code, out, err

    def __repr__(self):
        return f"Result({self.code}, out={self.out!r}, err={self.err!r})"


def run_cli(*args, env=None) -> Result:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run([str(a) for a in args], env if env is not None else {})
    return Result(code, out.getvalue(), err.getvalue())


def tool(tree: Path, features_d: Path, *args) -> Result:
    return run_cli("--isabelle-home", tree, "--features-dir", features_d, *args)


def ran(tree: Path, features_d: Path) -> str:
    """The tool as `tool` runs it: the commands in its output repeat the two options."""
    return f"isabelle-patch-control --isabelle-home {tree} --features-dir {features_d}"


@pytest.fixture
def toy(tmp_path) -> Toy:
    return Toy(tmp_path)


@pytest.fixture
def chain3(toy) -> Toy:
    return toy.standard_chain()


@pytest.fixture
def fresh(chain3) -> tuple[Toy, Path]:
    return chain3, chain3.tree()


@pytest.fixture
def applied(chain3) -> tuple[Toy, Path]:
    """The standard chain fully applied by the tool itself."""
    t = chain3.tree()
    res = api.apply(t, chain3.features_d)
    assert res.exit_code == 0 and len(res.moves) == 7
    return chain3, t


def make_writable(d: Path):
    for p in d.rglob("*"):
        p.chmod(p.stat().st_mode | stat.S_IWUSR)
    d.chmod(d.stat().st_mode | stat.S_IWUSR)


def copy_tree(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst, symlinks=True)
    return dst
