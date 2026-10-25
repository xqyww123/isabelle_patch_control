"""Decision 4: git runs with a whitelisted environment and fixed configuration, ceiling at the work
directory's parent.  Every hostile setup must give the bytes and the conclusions of a clean run."""
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from conftest import git_env, same_tree, tool
from isabelle_patch_control import api


def git_repo(path, *files):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, env=git_env())
    for name, text in files:
        (path / name).write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, env=git_env())
    subprocess.run(["git", "commit", "-qm", "x", "--allow-empty"], cwd=path, check=True, env=git_env())
    return path


SETUPS = ["tree-in-ignored-subdir", "cwd-in-worktree", "cwd-bad-git-file", "home-config", "git-env-vars"]


@dataclass
class Hostile:
    tree: Path
    clean_status: list[str]        # computed before the environment turned hostile
    expected_top: dict
    expected_pristine: dict


@pytest.fixture(params=SETUPS)
def hostile(request, chain3, tmp_path, monkeypatch):
    """The tree to use, with the clean run's results taken before the environment is made hostile
    in the parametrized way (the fixtures' own git must not be fooled either)."""
    setup = request.param
    clean = tool(chain3.tree(), chain3.features_d, "status").out.splitlines()[1:]
    expected_top, expected_pristine = chain3.expected("f3"), chain3.expected(None)
    tree = chain3.tree()
    if setup == "tree-in-ignored-subdir":
        repo = git_repo(tmp_path / "outer", (".gitignore", "/env/\n"))
        (repo / "env").mkdir()
        tree.rename(repo / "env" / "isa")
        tree = repo / "env" / "isa"
    elif setup == "cwd-in-worktree":
        repo = git_repo(tmp_path / "work", ("f", "x\n"))
        (repo / "sub").mkdir()
        monkeypatch.chdir(repo / "sub")
    elif setup == "cwd-bad-git-file":
        d = tmp_path / "cwd"
        d.mkdir()
        (d / ".git").write_text("gitdir: /nonexistent/nothing\n")
        monkeypatch.chdir(d)
    elif setup == "home-config":
        home = tmp_path / "home"
        (home / ".config" / "git").mkdir(parents=True)
        (home / ".gitconfig").write_text("[core]\n\tautocrlf = true\n[apply]\n\tignoreWhitespace = change\n[diff]\n\tnoprefix = true\n")
        (home / ".config" / "git" / "attributes").write_text("* text eol=crlf\n")
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
        monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
        monkeypatch.delenv("GIT_CONFIG_NOSYSTEM", raising=False)
    elif setup == "git-env-vars":
        repo = git_repo(tmp_path / "elsewhere", ("f", "x\n"))
        monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
        monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))         # like a dotfile manager's GIT_WORK_TREE=$HOME: it contains the tree
        monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
        monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.autocrlf")
        monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    return Hostile(tree, clean, expected_top, expected_pristine)


def test_hostile_environment_gives_the_clean_result(chain3, hostile):
    t = hostile.tree
    assert tool(t, chain3.features_d, "status").out.splitlines()[1:] == hostile.clean_status
    r = tool(t, chain3.features_d, "apply")
    assert r.code == 0
    same_tree(t, hostile.expected_top)
    assert tool(t, chain3.features_d, "status").code == 0
    assert tool(t, chain3.features_d, "unapply").code == 0
    same_tree(t, hostile.expected_pristine)


def test_git_sees_no_repository_above_the_work_directory(chain3, tmp_path, monkeypatch):
    """The failure mode of plan §2.4: inside a worktree, git apply skips every patch with rc 0 and
    `--numstat` prints nothing.  With the ceiling it must not."""
    repo = git_repo(tmp_path / "work", ("f", "x\n"))
    monkeypatch.setattr(tempfile, "tempdir", str(repo))     # temporary directories land inside the worktree (TMPDIR is already cached)
    t = chain3.tree()
    st = api.status(t, chain3.features_d)
    assert {s.state for s in st.features} == {"not-applied"}


def test_tree_inside_git_is_refused(chain3, tmp_path):
    repo = git_repo(tmp_path / "work", ("f", "x\n"))
    tree = repo / "isa"
    chain3.tree().rename(tree)
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True, env=git_env())
    assert tool(tree, chain3.features_d, "status").code == 3
