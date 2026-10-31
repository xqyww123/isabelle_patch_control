"""Decision 9 without conda: `conda-hook post-link` and `pre-unlink` against a fake prefix
($PREFIX/isa, conda-meta/, share/isabelle_patch_control/features.d), reading .messages.txt."""
import errno
import fcntl
import os
import shutil
from pathlib import Path

import pytest

from conftest import run_cli, same_tree, snapshot
from isabelle_patch_control import api, engine, features, texts


class Prefix:
    def __init__(self, toy, root: Path, at=None, *, features_d=True):
        self.toy = toy
        self.path = root
        root.mkdir()
        self.tree, self.features_d = features.locate(root)
        toy.tree(at).rename(self.tree)
        (root / "conda-meta").mkdir()
        if features_d:
            shutil.copytree(toy.features_d, self.features_d)
        self.messages = root / ".messages.txt"

    def hook(self, *args, pkg: str | None = None) -> str:
        """Run the hook as conda would; return what it appended to .messages.txt (conda prints and
        deletes the file after every hook, so each call starts empty)."""
        r = self.run(*args, pkg=pkg)
        assert r.code == 0 and r.out == "" and r.err == ""
        text = self.messages.read_text() if self.messages.exists() else ""
        if self.messages.exists():
            self.messages.unlink()
        return text

    def run(self, *args, pkg: str | None = None):
        env = {"PREFIX": str(self.path)}
        if pkg:
            env["PKG_NAME"] = pkg
        return run_cli("conda-hook", *args, env=env)

    def edit(self, rel: str, old: str, new: str):
        p = self.tree.joinpath(*rel.split("/"))
        p.write_text(p.read_text().replace(old, new))


def said(*paragraphs: str) -> str:
    """What .messages.txt holds after a hook wrote these paragraphs: each with the prefix on its
    first line (decision 9), added by the writer and by nothing else."""
    assert not any(p.startswith(texts.PREFIX) for p in paragraphs)
    return "".join(f"{texts.PREFIX}{p}\n" for p in paragraphs)


@pytest.fixture
def prefix(chain3, tmp_path):
    return Prefix(chain3, tmp_path / "env")


# --- post-link

def test_post_link_applies_the_whole_chain_once(prefix):
    text = prefix.hook("post-link", pkg="isabelle-f1")
    assert text == said(texts.changed(prefix.tree, applied=["f1", "f2", "f3"]) + "\n" + texts.HEAP_PARAGRAPH)
    assert api.status(prefix.tree, prefix.features_d).exit_code == 0
    assert prefix.hook("post-link", pkg="isabelle-f2") == ""              # nothing changed: not a word
    assert prefix.hook("post-link", pkg="isabelle-f3") == ""


def test_post_link_without_features_d_or_with_empty_chain(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env", features_d=False)
    assert p.hook("post-link") == ""
    p.features_d.mkdir(parents=True)
    assert p.hook("post-link") == ""


def test_post_link_conflict_full_diagnostic_only_from_the_chain_top(prefix):
    prefix.edit("src/Pure/b.ML", "b5\n", "edited\n")                        # f2's file
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text == said(texts.changed(prefix.tree, applied=["f1"]) + "\n" + texts.HEAP_PARAGRAPH,
                        texts.conflict_full("f2", [("src/Pure/b.ML", False)], prefix.tree))
    assert text.endswith(
        "\nisabelle-patch-control: Feature `f2` cannot be applied: src/Pure/b.ML was changed by something other than the "
        "installed feature packages.\n"
        "Until this is fixed, the tool does not apply f2 or the feature packages that depend on it.\n"
        "This usually means a conda command was interrupted halfway. To fix it, reinstall the isabelle package.\n"
        "This deletes this environment's Isabelle user directory (the heaps built there, your settings and preferences, "
        "and components you registered by hand); copy out anything you want to keep first "
        "(isabelle getenv -b ISABELLE_HOME_USER shows where it is).\n"
        f"Then run:\n  conda install -p {prefix.path} -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle\n"
        "The installed feature packages are applied again, and Isabelle rebuilds the heaps on first use.\n"
        "Upgrading from my-better-isabelle 0.x? See: isabelle-patch-control help\n")
    # a lower package's hook (or the one being installed below the top): one line
    line = ("isabelle-patch-control: Feature `f2` cannot be applied: src/Pure/b.ML was changed by something other than the "
            "installed feature packages. Run isabelle-patch-control status for what to do.\n")
    assert prefix.hook("post-link", pkg="isabelle-f1") == line
    assert prefix.hook("post-link", pkg="isabelle-f2") == line
    # unset or unknown PKG_NAME counts as the top
    assert prefix.hook("post-link").startswith(texts.PREFIX + texts.conflict("f2", ["src/Pure/b.ML"]) + "\nUntil")
    assert prefix.hook("post-link", pkg="isabelle").startswith(texts.PREFIX + texts.conflict("f2", ["src/Pure/b.ML"]) + "\nUntil")


def test_post_link_names_the_lowest_feature_stopped_by_a_conflict(prefix):
    prefix.edit("src/Pure/b.ML", "b5\n", "edited\n")                        # f2's file
    prefix.edit("etc/options", "ML_system_64", "edited")                    # f1's file
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text == said(texts.conflict_full("f1", [("etc/options", False)], prefix.tree))


def test_post_link_conflict_on_a_file_the_feature_creates(prefix):
    prefix.hook("post-link")
    prefix.edit("bin/new2", "echo new2", "echo mine")                        # f2 creates it
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text == said(texts.conflict_full("f2", [("bin/new2", True)], prefix.tree))
    assert f"To fix it, delete {prefix.tree / 'bin' / 'new2'} {texts.CREATED}, then run: isabelle-patch-control apply" in text
    assert "--force-reinstall" not in text


def test_post_link_conflict_on_two_files_deletes_the_created_one_before_the_reinstall(prefix):
    prefix.hook("post-link")
    prefix.edit("bin/new2", "echo new2", "echo mine")                        # f2 creates it
    prefix.edit("src/Pure/b.ML", "B5\n", "edited\n")                        # f2 changes it
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text == said(texts.conflict_full("f2", [("bin/new2", True), ("src/Pure/b.ML", False)], prefix.tree))
    assert ("Feature `f2` cannot be applied: bin/new2 and src/Pure/b.ML were changed by something other than the installed "
            "feature packages.\n") in text
    assert (f"To fix it, first delete {prefix.tree / 'bin' / 'new2'} (created by a feature); then reinstall the isabelle "
            "package.\n") in text and "--force-reinstall isabelle" in text


def test_post_link_lock_busy(prefix, monkeypatch):
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.2)
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            text = prefix.hook("post-link", pkg="isabelle-f3")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    assert text == said(texts.lock_busy(prefix.tree / engine.LOCK_FILE, 0.2, then="run: isabelle-patch-control apply"))
    assert "gave up after 0.2 s. Wait for that run to finish, then run: isabelle-patch-control apply.\n" in text
    assert "retry" not in text                                              # a hook cannot be retried


def test_post_link_on_the_old_build(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env")
    (p.tree / "etc" / "ISABELLE_ID").write_text("5533cd83156e\n")
    text = p.hook("post-link", pkg="isabelle-f3")
    assert text.startswith(texts.PREFIX + "the installed Isabelle feature packages were not applied: ")
    assert f'To fix it, run: conda install -p {p.path} --update-all "isabelle==2025.2"' in text \
        and text.endswith("\nWhen this is fixed, run: isabelle-patch-control status\n")


def test_post_link_refusals_end_with_the_command_to_run(prefix):
    (prefix.tree / ".git").write_text("gitdir: /nowhere\n")
    text = prefix.hook("post-link")
    assert text == said(texts.post_link_failed(f"{prefix.tree} has a .git: isabelle-patch-control does not touch a tree that git manages"))
    (prefix.tree / ".git").unlink()
    real, aside = prefix.tree / "src" / "Pure" / "b.ML", prefix.tree / "b.real"
    real.rename(aside)
    real.symlink_to(aside)
    text = prefix.hook("post-link")
    assert text == said(texts.post_link_failed(texts.symlink(real, prefix.tree)))
    assert "\n  conda config --set always_softlink false\n  conda config --set allow_softlinks false\n" in text   # one per line: cmd.exe has no `;`
    assert "--force-reinstall isabelle" in text
    assert text.index("copy out anything you want to keep first") < text.index("--force-reinstall")   # before the command


def test_post_link_write_failure_says_what_was_applied(prefix, monkeypatch):
    calls = []

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 2:
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text.startswith(texts.PREFIX + "the installed Isabelle feature packages were not fully applied: could not write ")
    assert "No space left on device" in text
    assert "Already applied: none. When this is fixed, run: isabelle-patch-control apply" in text


def test_post_link_write_failure_lists_only_features_applied_without_a_hole(chain3, tmp_path, monkeypatch):
    """A tree at f1; the third os.replace (a.ML, f3's) fails: f1 is applied, f2 half, f3 not."""
    prefix = Prefix(chain3, tmp_path / "env", at="f1")
    calls = []

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 3:
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)
    text = prefix.hook("post-link")
    assert "Already applied: f1. When this is fixed" in text
    st = api.status(prefix.tree, prefix.features_d)
    assert [s.state for s in st.features] == ["applied", "half-applied", "not-applied"]


def test_post_link_write_failure_leaves_out_a_feature_applied_above_a_hole(prefix, monkeypatch):
    """The sixth os.replace (new1.ML, f1's and f3's) fails: f2's three files are in, new1.ML is not."""
    calls = []

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 6:
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)
    text = prefix.hook("post-link")
    assert Path(calls[-1]).name == "new1.ML"
    st = api.status(prefix.tree, prefix.features_d)
    assert [(s.state, s.hole) for s in st.features] == [("half-applied", False), ("applied", True), ("half-applied", False)]
    assert "Already applied: none. When this is fixed" in text


def test_post_link_write_failure_that_recurs_still_speaks(prefix):
    """When reading the state again fails the same way, the frame names the failure and the hook
    still exits 0 (the `||` line must not blame the tool's installation)."""
    (prefix.tree / "src" / "Pure" / "b.ML").chmod(0)
    try:
        text = prefix.hook("post-link", pkg="isabelle-f3")
    finally:
        (prefix.tree / "src" / "Pure" / "b.ML").chmod(0o644)
    assert text.startswith(texts.PREFIX + "the installed Isabelle feature packages were not fully applied: Permission denied")
    assert "Already applied" not in text and text.endswith("When this is fixed, run: isabelle-patch-control apply\n")


def test_messages_file_is_ascii_whatever_the_prefix(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env-李明")
    p.run("post-link", pkg="isabelle-f3")
    raw = p.messages.read_bytes()
    assert raw.isascii()
    expected = said(texts.changed(p.tree, applied=["f1", "f2", "f3"]) + "\n" + texts.HEAP_PARAGRAPH)
    assert raw.decode() == expected.encode("ascii", errors="backslashreplace").decode()
    assert "\\u674e\\u660e" in raw.decode()


# --- pre-unlink

def test_pre_unlink_reverses_and_reports(prefix):
    prefix.hook("post-link")
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.undone("f3", prefix.tree, ["f3"]))
    assert text.splitlines()[1] == texts.UPDATE_LINE
    text = prefix.hook("pre-unlink", "f1")                                  # f1 and f2 go: back at the bottom
    assert text == said(texts.undone_at_bottom("f1", prefix.tree))
    assert "you may delete heaps/" in text
    assert prefix.hook("pre-unlink", "f1") == ""                             # nothing left to reverse
    assert snapshot(prefix.tree).keys() == prefix.toy.expected(None).keys()


def test_pre_unlink_names_the_features_undone_with_it(prefix):
    prefix.hook("post-link")
    assert prefix.hook("pre-unlink", "f2") == (
        f"isabelle-patch-control: f2 was undone in the Isabelle sources under {prefix.tree}, and with it f3.\n"
        "If you are updating or reinstalling, for example conda update --all: when it finishes, run isabelle-patch-control status.\n")


def test_pre_unlink_never_applies(prefix):
    assert prefix.hook("pre-unlink", "f2") == ""
    assert api.status(prefix.tree, prefix.features_d).exit_code == 1


def test_pre_unlink_residue_after_a_conflict(prefix):
    prefix.hook("post-link")
    prefix.edit("src/Pure/new1.ML", "new1 line\n", "edited\n")              # created by f1, changed by f3
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.residue("f3", texts.REASON_CONFLICT, [("src/Pure/new1.ML", True)], prefix.tree))
    assert text == (                                                         # not in the isabelle package: a reinstall would not help
        "isabelle-patch-control: f3 could not be fully undone (reason: a file was changed by something other than the "
        "installed feature packages).\n"
        f"These files under {prefix.tree} still carry its changes:\n"
        "  src/Pure/new1.ML   (created by a feature)\n"
        "If you are updating or reinstalling, for example conda update --all: when it finishes, run isabelle-patch-control status.\n"
        "If you are removing f3, clean up now (nothing will remind you later): first delete every file marked "
        "\"(created by a feature)\" in these messages; then run: isabelle-patch-control apply (if that command is no longer "
        "found, no feature package is left and you are done)\n")
    assert api.status(prefix.tree, prefix.features_d).levels["src/Pure/a.ML"].level == 1   # what could move, moved
    text = prefix.hook("pre-unlink", "f1")
    assert f"  src/Pure/new1.ML   {texts.CREATED}" in text and "reinstall the isabelle package" not in text


def test_pre_unlink_residue_after_a_lock_timeout(prefix, monkeypatch):
    prefix.hook("post-link")
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.2)
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            text = prefix.hook("pre-unlink", "f2")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    assert text == said(texts.residue("f2", texts.REASON_LOCK, [("README", False), ("bin/new2", True), ("src/Pure/b.ML", False)],
                                      prefix.tree, lock_package=("isabelle-f3", "1")))
    assert (f"run:\n  conda install -p {prefix.path} {texts.CHANNELS} isabelle-f3=1\n  conda remove -p {prefix.path} isabelle-f3\n") in text
    assert texts.UPDATE_LINE in text and "reinstall the isabelle package" not in text and "delete every file" not in text


def test_pre_unlink_residue_after_a_write_failure(prefix, monkeypatch):
    prefix.hook("post-link")
    calls = []

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 2:
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.residue("f3", texts.REASON_WRITE, [("src/Pure/new1.ML", True)], prefix.tree))
    assert "(reason: a file could not be written)" in text


def test_pre_unlink_residue_deletes_created_files_before_the_reinstall(prefix, monkeypatch):
    """The first os.replace (README) fails: all three of f2's files still carry its changes."""
    prefix.hook("post-link")

    def failing_replace(src, dst):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "replace", failing_replace)
    text = prefix.hook("pre-unlink", "f2")
    assert text == (
        "isabelle-patch-control: f2 could not be fully undone (reason: a file could not be written).\n"
        f"These files under {prefix.tree} still carry its changes:\n"
        "  README\n"
        "  bin/new2   (created by a feature)\n"
        "  src/Pure/b.ML\n"
        "If you are updating or reinstalling, for example conda update --all: when it finishes, run isabelle-patch-control status.\n"
        "If you are removing f2, clean up now (nothing will remind you later): first fix what stopped the write (for "
        "example, free disk space); then delete every file marked \"(created by a feature)\" in these messages; then "
        "reinstall the isabelle package.\n"
        "This deletes this environment's Isabelle user directory (the heaps built there, your settings and preferences, "
        "and components you registered by hand); copy out anything you want to keep first "
        "(isabelle getenv -b ISABELLE_HOME_USER shows where it is).\n"
        f"Then run:\n  conda install -p {prefix.path} -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle\n"
        "The installed feature packages are applied again, and Isabelle rebuilds the heaps on first use.\n")


def test_pre_unlink_residue_after_a_write_failure_is_computed_without_the_lock(prefix, monkeypatch):
    """Another run takes the lock right after the failure: the residue is still computed and written."""
    prefix.hook("post-link")
    calls = []

    def busy(tree, exclusive):
        raise api.Busy("another run took the lock")

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 2:
            monkeypatch.setattr(api, "locked", busy)
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    monkeypatch.setattr(os, "replace", failing_replace)
    assert prefix.hook("pre-unlink", "f3") == said(texts.residue("f3", texts.REASON_WRITE, [("src/Pure/new1.ML", True)], prefix.tree))


def test_pre_unlink_write_failure_then_no_residue_exits_non_zero(prefix, monkeypatch):
    prefix.hook("post-link")
    calls = []

    def failing_replace(src, dst):
        calls.append(dst)
        if len(calls) == 2:
            raise OSError(errno.ENOSPC, "No space left on device")
        return os.rename(src, dst)

    def no_temp_dir(near=None):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "replace", failing_replace)
    monkeypatch.setattr(api, "temp_dir", no_temp_dir)
    r = prefix.run("pre-unlink", "f3")
    assert r.code == 1 and not prefix.messages.exists()


def test_pre_unlink_that_cannot_tell_the_residue_exits_non_zero_and_writes_nothing(prefix, monkeypatch):
    """The `||` line of the hook text speaks then: the tool must not write a wrong message."""
    prefix.hook("post-link")
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.2)

    def no_temp_dir(near=None):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(api, "temp_dir", no_temp_dir)
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            r = prefix.run("pre-unlink", "f2")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    assert r.code == 1 and "No space left on device" in r.err and not prefix.messages.exists()


def test_pre_unlink_when_the_chain_does_not_link(prefix):
    prefix.hook("post-link")
    shutil.rmtree(prefix.features_d / "f2")
    error = texts.chain_broken("isabelle-f3", "1", "isabelle-f2", "1", None)
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.chain_broken_removal("f3", "isabelle-f3", error, prefix.tree)) and texts.UPDATE_LINE in text
    assert prefix.hook("pre-unlink", "f2") == said(texts.chain_broken_removal("f2", "isabelle-f2", error, prefix.tree))
    assert text.endswith(f"first do what the first line says, then run:\n  conda remove -p {prefix.path} isabelle-f3\n")
    same_tree(prefix.tree, prefix.toy.expected("f3"))                        # nothing was reversed


def test_pre_unlink_of_an_unknown_feature(prefix):
    text = prefix.hook("pre-unlink", "f9")
    assert text == said(texts.pre_unlink_failed("f9", "isabelle-f9", "no feature package named 'f9' is installed (installed: f1, f2, f3)",
                                             prefix.tree))
    assert texts.UPDATE_LINE in text and text.endswith(
        f"so that its changes are undone cleanly:\n  conda install -p {prefix.path} {texts.CHANNELS} isabelle-f9\n"
        f"  conda remove -p {prefix.path} isabelle-f9\n")
