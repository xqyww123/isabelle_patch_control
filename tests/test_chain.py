"""Decisions 2 and 3: locating the tree and features.d, reading feature directories, linking the
chain by exact tags, and every refusal of the start of a command."""
import shutil
import stat
import sys
from pathlib import Path

import pytest

from conftest import OLD_BUILD_ID, PRISTINE_ID, RELEASE, run_cli, tool
from isabelle_patch_control import api, features, texts


def test_fresh_tree_links_three_features(fresh):
    toy, t = fresh
    r = tool(t, toy.features_d, "status")
    assert r.code == 1
    lines = r.out.splitlines()
    assert lines[0] == f"tree {t}   features.d {toy.features_d}"
    assert [l.split()[1] for l in lines[1:]] == ["f1", "f2", "f3"]
    assert all(l.startswith("not-applied") for l in lines[1:])
    assert lines[1].endswith(" 4 files") and lines[2].endswith(" 3 files") and lines[3].endswith(" 2 files")


def test_hole_in_the_chain_is_refused(fresh):
    toy, t = fresh
    shutil.rmtree(toy.features_d / "f2")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert r.err.strip() == texts.PREFIX + texts.chain_broken("isabelle-f3", "1", "f3", "isabelle-f2", "1", f"{RELEASE}/f2/1", "none")
    assert "needs isabelle-f2 1; installed: none" in r.err


def test_wrong_version_installed_is_named(fresh):
    toy, t = fresh
    prov = toy.features_d / "f2" / "provenance.txt"
    prov.write_text(prov.read_text().replace(f"release_tag: {RELEASE}/f2/1", f"release_tag: {RELEASE}/f2/2"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert f"needs isabelle-f2 1; installed: isabelle-f2 2 (features.d/f3 needs {RELEASE}/f2/1)." in r.err


def test_fork_is_refused(fresh):
    toy, t = fresh
    shutil.copytree(toy.features_d / "f2", toy.features_d / "f2b")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert "features.d/f2 and features.d/f2b" in r.err and f"{RELEASE}/f1/1" in r.err


def test_tree_of_another_release_is_refused(fresh):
    """The release line is compared too, not only the build: both come from the bottom directory's
    base_tag."""
    toy, t = fresh
    (t / "etc" / "ISABELLE_IDENTIFIER").write_text("Isabelle2024")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert r.err.strip() == texts.PREFIX + texts.not_pristine(t, PRISTINE_ID, "f1", RELEASE, PRISTINE_ID)


def test_tree_that_is_not_the_pristine_build(chain3):
    t = chain3.old_build_tree()
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3
    assert r.err.strip() == texts.PREFIX + texts.not_pristine(t, OLD_BUILD_ID, "f1", RELEASE, PRISTINE_ID)
    assert r.err.startswith(texts.PREFIX + f"run: conda update --all {texts.CHANNELS}.") and OLD_BUILD_ID in r.err
    for cmd in ("apply", "unapply"):
        assert tool(t, chain3.features_d, cmd).code == 3


def test_refusals_do_not_depend_on_directory_order(chain3):
    """The real feature names do not sort in chain order (dev_patches first); the directory that
    the refusal names is the one with the bad base, whatever sorts first."""
    (chain3.features_d / "f3").rename(chain3.features_d / "a3")             # the top now sorts first
    t = chain3.old_build_tree()
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3 and "features.d/f1 was made for" in r.err and "conda update --all" in r.err
    shutil.rmtree(chain3.features_d / "f2")                                 # a3's base is unreleased too: the build still comes first
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3 and "features.d/f1 was made for" in r.err
    shutil.rmtree(chain3.features_d / "f1")
    r = tool(chain3.tree(), chain3.features_d, "status")
    assert r.code == 3
    assert "isabelle-f3 1 needs isabelle-f2 1; installed: none (features.d/a3 needs" in r.err   # the name comes from release_tag


def test_no_feature_packages(toy, tmp_path):
    empty = tmp_path / "empty.d"
    empty.mkdir()
    for t in (toy.tree(), toy.old_build_tree()):           # whatever build the tree is (ruling 29)
        r = tool(t, empty, "status")
        assert r.code == 0 and r.out.splitlines() == [f"tree {t}   features.d {empty}", texts.NO_FEATURES]
        for cmd in ("apply", "unapply"):
            r = tool(t, empty, cmd)
            assert (r.code, r.out) == (0, "")
    assert tool(toy.tree(), empty, "apply", "--feature", "f1").code == 3


def test_unknown_feature_name(fresh):
    toy, t = fresh
    for cmd in ("status", "apply", "unapply"):
        r = tool(t, toy.features_d, cmd, "--feature", "f9")
        assert r.code == 3 and "f9" in r.err and "f1, f2, f3" in r.err
        assert r.out == ""                                   # refused before the lock and the table


def test_feature_option_takes_the_package_name_too(fresh):
    toy, t = fresh
    assert tool(t, toy.features_d, "apply", "--feature", "isabelle-f2").code == 0
    assert tool(t, toy.features_d, "status", "--feature", "isabelle-f2").code == 0
    assert tool(t, toy.features_d, "status", "--feature", "f3").code == 1
    assert tool(t, toy.features_d, "unapply", "--feature", "isabelle-f1").code == 0


def test_other_entries_in_features_d_are_ignored(fresh):
    toy, t = fresh
    before = tool(t, toy.features_d, "status", "-v").out
    (toy.features_d / "noprov").mkdir()
    (toy.features_d / "noprov" / "x.patch").write_text("garbage")
    (toy.features_d / "stray.txt").write_text("x")
    (toy.features_d / "f2" / "src-Pure-b.ML.patch.c~").write_text("garbage")
    (toy.features_d / "f2" / "provenance.txt.c~").write_text("garbage")
    (toy.features_d / "f2" / "notes.md").write_text("garbage")
    assert tool(t, toy.features_d, "status", "-v").out == before


def test_unreadable_patch_file(fresh):
    toy, t = fresh
    bad = toy.features_d / "f2" / "src-Pure-b.ML.patch"
    bad.write_text("this is not a patch\n")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and str(bad) in r.err and "cannot read" in r.err


def test_patch_file_with_two_targets(fresh):
    toy, t = fresh
    f1 = toy.features_d / "f1"
    two = f1 / "src-Pure-a.ML.patch"
    two.write_text(two.read_text() + (f1 / "src-Pure-new1.ML.patch").read_text())
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and str(two) in r.err and "changes 2" in r.err


def test_feature_directory_without_patch_files(fresh):
    toy, t = fresh
    for p in (toy.features_d / "f3").glob("*.patch"):
        p.unlink()
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and "features.d/f3".replace("features.d/", "") in r.err and "no patch file" in r.err


def test_tree_with_git_is_refused(fresh):
    toy, t = fresh
    (t / ".git").write_text("gitdir: /nowhere\n")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and ".git" in r.err


def test_missing_tree(chain3, tmp_path):
    r = tool(tmp_path / "nothing", chain3.features_d, "status")
    assert r.code == 2 and "no Isabelle tree" in r.err


def test_symlinked_target_is_refused(fresh):
    toy, t = fresh
    real = t / "src" / "Pure" / "b.ML"
    aside = t / "b.real"
    real.rename(aside)
    real.symlink_to(aside)
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and "symbolic link" in r.err and "always_softlink" in r.err


def test_resolve_prefix_and_features_root(chain3, tmp_path, monkeypatch):
    """Decision 2: P from --isabelle-home's parent, else sys.prefix; features.d only in a conda
    environment; another environment's tool reads this one's features.d via --isabelle-home."""
    env = tmp_path / "env"
    tree = env / "isa"
    shutil.copytree(chain3.tree(), tree)
    (env / "conda-meta").mkdir()
    root = env / features.FEATURES_D
    shutil.copytree(chain3.features_d, root)
    r = run_cli("--isabelle-home", tree, "status")
    assert r.code == 1 and r.out.startswith(f"tree {tree}   features.d {root}\n")
    # the default invocation: sys.prefix is the environment; CONDA_PREFIX and ISABELLE_HOME are not read
    monkeypatch.setattr(sys, "prefix", str(env))
    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path / "decoy"))
    monkeypatch.setenv("ISABELLE_HOME", str(tmp_path / "decoy" / "isa"))
    r = run_cli("status")
    assert r.code == 1 and r.out.startswith(f"tree {tree}   features.d {root}\n")
    # `..` in --isabelle-home: the prefix is the tree's real parent
    monkeypatch.chdir(tree / "src")
    r = run_cli("--isabelle-home", "..", "status")
    assert r.code == 1 and r.out.startswith(f"tree {tree}   features.d {root}\n")
    # the tool of another prefix, no conda-meta there: sys.prefix is not an environment
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "plain"))
    r = run_cli("status")
    assert r.code == 3 and "not a conda environment" in r.err and "--features-dir" in r.err
    r = run_cli("--isabelle-home", chain3.tree(), "status")       # a tree outside any environment
    assert r.code == 3 and "--features-dir" in r.err
    r = run_cli("--isabelle-home", tree, "--features-dir", tmp_path / "missing", "status")
    assert r.code == 3 and "is not a directory" in r.err
    # a conda environment without any feature package: its features.d does not exist
    shutil.rmtree(root)
    r = run_cli("--isabelle-home", tree, "status")
    assert r.code == 0 and r.out.splitlines()[1] == texts.NO_FEATURES
    assert "conda-meta/history" in r.out                            # no history file: an interrupted conda command
    (env / "conda-meta" / "history").write_text("")
    r = run_cli("--isabelle-home", tree, "status")
    assert r.code == 0 and r.out.splitlines() == [f"tree {tree}   features.d {root}", texts.NO_FEATURES]


def test_status_verbose_lists_files_with_levels(fresh):
    toy, t = fresh
    r = tool(t, toy.features_d, "status", "-v")
    assert "    src/Pure/new1.ML  level 0  " + texts.CREATED in r.out      # f1 creates it
    assert "    src/Pure/c.ML  level 0\n" in r.out
    assert r.out.count(texts.CREATED) == 2                                 # new1.ML (f1) and bin/new2 (f2)


def test_help_prints_agents_md():
    r = run_cli("help")
    assert r.code == 0 and r.out.startswith("#")


def test_python_api_never_exits(fresh):
    toy, t = fresh
    with pytest.raises(api.Refused):
        api.status(t, toy.features_d, feature="nope")
    with pytest.raises(api.NotFound):
        api.status(t / "nowhere", toy.features_d)


def test_python_api_takes_relative_paths_and_a_missing_root(fresh, monkeypatch, tmp_path):
    """The API applies decision 2's rules itself: a features.d that does not exist means no
    feature package, and a relative directory is read from where the caller is, not from the work
    directory git runs in."""
    toy, t = fresh
    assert api.status(t, tmp_path / "no-such-features.d").chain == []
    (toy.features_d / "f2" / "provenance.txt").chmod(0)                  # an unreadable file is exit 1, never a traceback
    try:
        with pytest.raises(api.WriteFailed):
            api.status(t, toy.features_d)
        r = tool(t, toy.features_d, "status")
        assert r.code == 1 and r.err.startswith(texts.PREFIX + "Permission denied") and r.out == ""
    finally:
        (toy.features_d / "f2" / "provenance.txt").chmod(0o644)
    monkeypatch.chdir(toy.root)
    assert api.status(Path(t.name), Path("features.d")).exit_code == 1
    assert api.apply_to(Path(t.name), Path("features.d") / "f1").exit_code == 0


def fake_git(bin_dir: Path, version: str):
    bin_dir.mkdir(parents=True)
    git = bin_dir / "git"
    git.write_text(f"#!/bin/sh\necho 'git version {version}'\n")
    git.chmod(git.stat().st_mode | stat.S_IXUSR)


def test_git_is_looked_up_at_the_prefix_first_and_must_be_recent(fresh, tmp_path, monkeypatch):
    """Decision 4: <prefix>/bin/git, then PATH; older than 2.43 is exit 2, as is no git at all."""
    toy, t = fresh
    fake_git(tmp_path / "old" / "bin", "2.30.0")
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "old"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 2 and str(tmp_path / "old" / "bin" / "git") in r.err and ">= 2.43" in r.err
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "without-git"))
    (tmp_path / "empty").mkdir()
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 2 and "git not found" in r.err
