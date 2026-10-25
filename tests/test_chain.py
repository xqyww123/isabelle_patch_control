"""Decisions 2 and 3: locating the tree and features.d, reading feature directories, linking the
chain by exact tags, and every refusal of the start of a command."""
import shutil
import sys

import pytest

from conftest import OLD_BUILD_ID, PRISTINE_ID, RELEASE, run_cli, tool
from isabelle_patch_control import api, cli, texts


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
    assert r.err.strip() == texts.PREFIX + (
        f"feature chain broken: isabelle-f3 1 (features.d/f3) needs isabelle-f2 1 ({RELEASE}/f2/1); installed: none. "
        "Install matching versions of these packages.")


def test_wrong_version_installed_is_named(fresh):
    toy, t = fresh
    prov = toy.features_d / "f2" / "provenance.txt"
    prov.write_text(prov.read_text().replace(f"release_tag: {RELEASE}/f2/1", f"release_tag: {RELEASE}/f2/2"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert f"needs isabelle-f2 1 ({RELEASE}/f2/1); installed: isabelle-f2 2." in r.err


def test_fork_is_refused(fresh):
    toy, t = fresh
    shutil.copytree(toy.features_d / "f2", toy.features_d / "f2b")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert "features.d/f2 and features.d/f2b" in r.err and f"{RELEASE}/f1/1" in r.err


def test_release_line_mismatch_is_refused(fresh):
    toy, t = fresh
    prov = toy.features_d / "f1" / "provenance.txt"
    prov.write_text(prov.read_text().replace(f"feature: {RELEASE}/f1", "feature: Isabelle2024/f1"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and "features.d/f1 is for Isabelle2024" in r.err


def test_tree_that_is_not_the_pristine_build(chain3):
    t = chain3.old_build_tree()
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3
    assert r.err.strip() == texts.PREFIX + (
        f"{t} has etc/ISABELLE_ID {OLD_BUILD_ID}, but features.d/f1 was made for {RELEASE} pristine {PRISTINE_ID}. "
        f"Feature packages exist only for the pristine isabelle build. Run: conda update --all {texts.CHANNELS}")
    for cmd in ("apply", "unapply"):
        assert tool(t, chain3.features_d, cmd).code == 3


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
    root = env / cli.FEATURES_D
    shutil.copytree(chain3.features_d, root)
    r = run_cli("--isabelle-home", tree, "status")
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
        api.status(t, toy.features_d).number("nope")
    with pytest.raises(api.NotFound):
        api.status(t / "nowhere", toy.features_d)
