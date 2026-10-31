"""Decisions 2 and 3: locating the tree and features.d, reading feature directories, linking the
chain by exact tags, and every refusal of the start of a command."""
import shutil
import stat
import sys
from pathlib import Path

import pytest

from conftest import OLD_BUILD_ID, PRISTINE_ID, RELEASE, ran, run_cli, tool
from isabelle_patch_control import api, cli, features, texts


def test_fresh_tree_links_three_features(fresh):
    toy, t = fresh
    r = tool(t, toy.features_d, "status")
    assert r.code == 1
    assert r.out.splitlines()[0] == texts.checked(t, 3)
    assert cli.read_status(r.out) == [("not-applied", "f1"), ("not-applied", "f2"), ("not-applied", "f3")]
    assert r.out.endswith(f"\n\nTo apply what is missing, run: {ran(t, toy.features_d)} apply\n")   # the same tree again
    shutil.rmtree(toy.features_d / "f3")
    shutil.rmtree(toy.features_d / "f2")
    r = tool(t, toy.features_d, "status")
    assert r.out == (f"Checked the Isabelle sources in {t} against 1 feature package.\n\n"
                     f"Feature `f1` is not applied yet.\n\nTo apply what is missing, run: {ran(t, toy.features_d)} apply\n")


def test_hole_in_the_chain_is_refused(fresh):
    toy, t = fresh
    shutil.rmtree(toy.features_d / "f2")
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert r.err.strip() == texts.PREFIX + texts.chain_broken("isabelle-f3", "1", "isabelle-f2", "1", None)
    assert r.err == ("isabelle-patch-control: isabelle-f3 1 needs isabelle-f2 1, which is not installed. "
                     "Install matching versions of these packages.\n")


def test_wrong_version_installed_is_named(fresh):
    toy, t = fresh
    prov = toy.features_d / "f2" / "provenance.txt"
    prov.write_text(prov.read_text().replace(f"release_tag: {RELEASE}/f2/1", f"release_tag: {RELEASE}/f2/2"))
    r = tool(t, toy.features_d, "status")
    assert r.code == 3
    assert "isabelle-f3 1 needs isabelle-f2 1, but isabelle-f2 2 is installed. Install matching versions" in r.err


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
    assert r.err.startswith(f"{texts.PREFIX}{t} is not the Isabelle build the feature packages were made for: ") and OLD_BUILD_ID in r.err
    assert r.err.endswith(f'. To fix it, run: conda install -p {t.parent} --update-all "isabelle==2025.2" '
                          '-c https://conda.qiyuan.me -c conda-forge\n')            # the update that keeps the release line
    for cmd in ("apply", "unapply"):
        assert tool(t, chain3.features_d, cmd).code == 3


def test_refusals_do_not_depend_on_directory_order(chain3):
    """The real feature names do not sort in chain order (dev_patches first); the directory that
    the refusal names is the one with the bad base, whatever sorts first."""
    (chain3.features_d / "f3").rename(chain3.features_d / "a3")             # the top now sorts first
    t = chain3.old_build_tree()
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3 and "features.d/f1 was made for" in r.err and ' --update-all "isabelle==2025.2" -c https://conda.qiyuan.me' in r.err
    shutil.rmtree(chain3.features_d / "f2")                                 # a3's base is unreleased too: the build still comes first
    r = tool(t, chain3.features_d, "status")
    assert r.code == 3 and "features.d/f1 was made for" in r.err
    shutil.rmtree(chain3.features_d / "f1")
    r = tool(chain3.tree(), chain3.features_d, "status")
    assert r.code == 3
    assert "isabelle-f3 1 needs isabelle-f2 1, which is not installed." in r.err   # the name comes from release_tag


def test_no_feature_packages(toy, tmp_path):
    empty = tmp_path / "empty.d"
    empty.mkdir()
    for t in (toy.tree(), toy.old_build_tree()):           # whatever build the tree is (ruling 29)
        r = tool(t, empty, "status")
        assert r.code == 0 and r.out.splitlines() == [texts.NO_FEATURES]
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
    head = f"Checked the Isabelle sources in {tree} against 3 feature packages.\nThe feature packages' patches are read from {root}.\n"
    r = run_cli("--isabelle-home", tree, "status", "-v")
    assert r.code == 1 and r.out.startswith(head)
    # the default invocation: sys.prefix is the environment; CONDA_PREFIX and ISABELLE_HOME are not read
    monkeypatch.setattr(sys, "prefix", str(env))
    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path / "decoy"))
    monkeypatch.setenv("ISABELLE_HOME", str(tmp_path / "decoy" / "isa"))
    r = run_cli("status", "-v")
    assert r.code == 1 and r.out.startswith(head)
    # `..` in --isabelle-home: the prefix is the tree's real parent
    monkeypatch.chdir(tree / "src")
    r = run_cli("--isabelle-home", "..", "status", "-v")
    assert r.code == 1 and r.out.startswith(head)
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
    assert r.code == 0 and r.out.splitlines() == [texts.NO_FEATURES]


def test_status_verbose_lists_files_with_levels(fresh):
    toy, t = fresh
    r = tool(t, toy.features_d, "status", "-v")
    assert "    src/Pure/new1.ML  level 0 (original)  (created by a feature)" in r.out    # f1 creates it
    assert "    src/Pure/c.ML  level 0 (original)\n" in r.out
    assert r.out.count(texts.CREATED) == 3                                 # new1.ML under f1 and f3, bin/new2 under f2
    assert "\n    package isabelle-f1, release Isabelle2025-2/f1/1; its files:\n" in r.out


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


def test_the_reinstall_command_quotes_the_prefix(monkeypatch):
    """It is pasted into the user's shell: a POSIX shell, or cmd.exe / PowerShell on Windows."""
    tail = "-c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle"
    spaced = Path("/home/a b/env/isa")
    if sys.platform != "win32":
        assert texts.reinstall(spaced) == f"conda install -p '/home/a b/env' {tail}"
        assert texts.reinstall(Path("/home/ab/env/isa")) == f"conda install -p /home/ab/env {tail}"
    monkeypatch.setattr(texts.os, "name", "nt")
    assert texts.reinstall(spaced) == f'conda install -p "{spaced.parent}" {tail}'


def test_status_says_how_to_fix_files_it_does_not_recognise(chain3, tmp_path, monkeypatch):
    """The last line of status for a feature that cannot be applied: delete a file a feature creates
    (first), reinstall isabelle for a file of the isabelle package (in a conda environment only)."""
    env = tmp_path / "env"
    tree = env / "isa"
    shutil.copytree(chain3.tree("f3"), tree)
    (env / "conda-meta").mkdir()
    shutil.copytree(chain3.features_d, env / features.FEATURES_D)
    (tree / "bin" / "new2").write_text("other\n")                                  # f2 creates it
    r = run_cli("--isabelle-home", tree, "status")
    assert r.code == 1 and ("CONFLICT", "f2") in cli.read_status(r.out)
    assert r.out.endswith(f"\nTo fix it, delete {tree / 'bin' / 'new2'} (created by a feature), "
                          f"then run: isabelle-patch-control --isabelle-home {tree} apply\n")
    v = run_cli("--isabelle-home", tree, "status", "-v").out                  # bin/new2 is 0755: git's mode warning is left out
    assert "\n        level 2: error: " in v and "warning:" not in v
    (tree / "src" / "Pure" / "b.ML").write_text("edited\n")                        # f2 changes it
    r = run_cli("--isabelle-home", tree, "status")
    assert ("Feature `f2` cannot be applied: bin/new2 and src/Pure/b.ML were changed by something other than the installed "
            "feature packages.\n") in r.out
    assert r.out.endswith(
        "\nThis usually means a conda command was interrupted halfway. To fix it, first delete "
        f"{tree / 'bin' / 'new2'} (created by a feature); then reinstall the isabelle package.\n"
        "This deletes this environment's Isabelle user directory (the heaps built there, your settings and preferences, "
        "and components you registered by hand); copy out anything you want to keep first "
        "(isabelle getenv -b ISABELLE_HOME_USER shows where it is).\n"
        f"Then run:\n  conda install -p {env} -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle\n"
        "The installed feature packages are applied again, and Isabelle rebuilds the heaps on first use.\n")
    # a file f1 creates and f3 changes is deleted, not reinstalled, whichever feature's state shows it
    shutil.rmtree(tree)
    shutil.copytree(chain3.tree("f3"), tree)
    (tree / "src" / "Pure" / "new1.ML").write_text("other\n")
    r = run_cli("--isabelle-home", tree, "status")
    assert cli.read_status(r.out) == [("CONFLICT", "f1"), ("applied", "f2"), ("CONFLICT", "f3")]
    assert r.out.endswith(f"\nTo fix it, delete {tree / 'src' / 'Pure' / 'new1.ML'} (created by a feature), "
                          f"then run: isabelle-patch-control --isabelle-home {tree} apply\n") and "reinstall" not in r.out
    monkeypatch.setattr(sys, "prefix", str(env))                                      # run without options: the command is too
    r = run_cli("status")
    assert r.out.endswith(" (created by a feature), then run: isabelle-patch-control apply\n")
    t = chain3.tree("f3")                                                            # outside a conda environment
    (t / "src" / "Pure" / "b.ML").write_text("edited\n")
    r = tool(t, chain3.features_d, "status")
    assert r.out.endswith(f"\nRestore {t / 'src' / 'Pure' / 'b.ML'} to the original Isabelle sources, then run: "
                          f"{ran(t, chain3.features_d)} apply\n")
    assert "reinstall" not in r.out
    (t / "bin" / "new2").write_text("other\n")
    r = tool(t, chain3.features_d, "status")
    assert r.out.endswith(f"\nRestore {t / 'src' / 'Pure' / 'b.ML'} to the original Isabelle sources and delete {t / 'bin' / 'new2'} "
                          f"(created by a feature), then run: {ran(t, chain3.features_d)} apply\n")
