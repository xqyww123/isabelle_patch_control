"""Decision 9 without conda: `conda-hook post-link` and `pre-unlink` against a fake prefix
($PREFIX/isa, conda-meta/, share/isabelle_patch_control/features.d), reading .messages.txt."""
import errno
import fcntl
import hashlib
import json
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
        # isabelle is installed and this command does not link it: its record is there (decision 9)
        self.isabelle_record.write_text(json.dumps({"name": "isabelle", "paths_data": {"paths": []}}))
        if features_d:
            shutil.copytree(toy.features_d, self.features_d)
        self.messages = root / ".messages.txt"

    @property
    def isabelle_record(self) -> Path:
        return self.path / "conda-meta" / "isabelle-2025.2-1.json"

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
    assert "was NOT applied: src/Pure/b.ML under" in text and "--force-reinstall isabelle" in text
    assert "until this is fixed, the tool applies\nneither f2 nor the packages that depend on it" in text
    assert "isabelle-patch-control help" in text.splitlines()[-1]
    # a lower package's hook (or the one being installed below the top): one line
    assert prefix.hook("post-link", pkg="isabelle-f1") == said(texts.conflict_line("f2", ["src/Pure/b.ML"]))
    assert prefix.hook("post-link", pkg="isabelle-f2") == said(texts.conflict_line("f2", ["src/Pure/b.ML"]))
    # unset or unknown PKG_NAME counts as the top
    assert prefix.hook("post-link").startswith(texts.PREFIX + "f2 was NOT applied")
    assert prefix.hook("post-link", pkg="isabelle").startswith(texts.PREFIX + "f2 was NOT applied")


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
    assert "move it aside, then run isabelle-patch-control apply" in text and "--force-reinstall" not in text


def test_post_link_lock_busy(prefix, monkeypatch):
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.2)
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            text = prefix.hook("post-link", pkg="isabelle-f3")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    assert text == said(texts.lock_busy(prefix.tree / engine.LOCK_FILE, 0.2) + texts.LOCK_BUSY_HOOK_TAIL)
    assert "gave up after 0.2 s" in text


def test_post_link_on_the_old_build(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env")
    (p.tree / "etc" / "ISABELLE_ID").write_text("5533cd83156e\n")
    text = p.hook("post-link", pkg="isabelle-f3")
    assert text.startswith(texts.PREFIX + "the installed Isabelle feature packages were not applied: ")
    assert "conda update --all" in text and text.endswith("run: isabelle-patch-control apply\n")


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
    assert "conda config --set always_softlink false" in text and "--force-reinstall isabelle" in text
    assert "2. Copy anything of your own out of" in text                      # right before the step that deletes it


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
    assert "Applied so far: none. When this is fixed, run: isabelle-patch-control apply" in text


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
    assert "Applied so far: f1. When this is fixed" in text
    st = api.status(prefix.tree, prefix.features_d)
    assert [s.state for s in st.features] == ["applied", "half-applied", "not-applied"]


def test_post_link_write_failure_that_recurs_still_speaks(prefix):
    """When reading the state again fails the same way, the frame names the failure and the hook
    still exits 0 (the `||` line must not blame the tool's installation)."""
    (prefix.tree / "src" / "Pure" / "b.ML").chmod(0)
    try:
        text = prefix.hook("post-link", pkg="isabelle-f3")
    finally:
        (prefix.tree / "src" / "Pure" / "b.ML").chmod(0o644)
    assert text.startswith(texts.PREFIX + "the installed Isabelle feature packages were not fully applied: Permission denied")
    assert "Applied so far" not in text and text.endswith("When this is fixed, run: isabelle-patch-control apply\n")


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


def test_pre_unlink_never_applies(prefix):
    assert prefix.hook("pre-unlink", "f2") == ""
    assert api.status(prefix.tree, prefix.features_d).exit_code == 1


def test_pre_unlink_residue_after_a_conflict(prefix):
    prefix.hook("post-link")
    prefix.edit("src/Pure/new1.ML", "new1 line\n", "edited\n")              # created by f1, changed by f3
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.residue("f3", texts.REASON_CONFLICT, [("src/Pure/new1.ML", False)], prefix.tree))
    assert "(reason: a file has unexpected content)" in text
    assert texts.UPDATE_LINE in text and "  1. Copy anything of your own out of" in text and "  3. Delete every file marked" in text
    assert "Retry later" not in text
    assert api.status(prefix.tree, prefix.features_d).levels["src/Pure/a.ML"].level == 1   # what could move, moved
    text = prefix.hook("pre-unlink", "f1")
    assert f"  src/Pure/new1.ML   {texts.CREATED}" in text                   # f1 created it


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
    assert f"  conda install {texts.CHANNELS} isabelle-f3=1; then conda remove isabelle-f3" in text
    assert "Retry later" not in text and "1. Save" not in text


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
    assert text == said(texts.residue("f3", texts.REASON_WRITE, [("src/Pure/new1.ML", False)], prefix.tree))
    assert "(reason: a file could not be written)" in text


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
    assert prefix.hook("pre-unlink", "f3") == said(texts.residue("f3", texts.REASON_WRITE, [("src/Pure/new1.ML", False)], prefix.tree))


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
    error = texts.chain_broken("isabelle-f3", "1", "f3", "isabelle-f2", "1", "Isabelle2025-2/f2/1", "none")
    text = prefix.hook("pre-unlink", "f3")
    assert text == said(texts.chain_broken_removal("f3", "isabelle-f3", error)) and texts.UPDATE_LINE in text
    assert prefix.hook("pre-unlink", "f2") == said(texts.chain_broken_removal("f2", "isabelle-f2", error))
    same_tree(prefix.tree, prefix.toy.expected("f3"))                        # nothing was reversed


def test_pre_unlink_of_an_unknown_feature(prefix):
    text = prefix.hook("pre-unlink", "f9")
    assert text == said(texts.pre_unlink_failed("f9", "isabelle-f9", "no feature package named 'f9' is installed (installed: f1, f2, f3)"))
    assert texts.UPDATE_LINE in text and "conda install" in text and "then conda remove isabelle-f9" in text


# --- the in-place edit through a hard link (decision 9's one reading of conda-meta)

def fake_isabelle_record(prefix: Prefix, cache: Path):
    """conda-meta/isabelle-2025.2-1.json with paths_data for the tree's files, hard-linked from
    `cache` (the extracted package directory)."""
    paths = []
    for rel, (content, _) in snapshot(prefix.tree).items():
        cached = cache / "isa" / rel
        cached.parent.mkdir(parents=True, exist_ok=True)
        if cached.exists():
            cached.unlink()
        os.link(prefix.tree / rel, cached)
        paths.append({"_path": "isa/" + rel, "sha256": hashlib.sha256(content).hexdigest()})
    record = {"name": "isabelle", "version": "2025.2", "build": "1", "extracted_package_dir": str(cache),
              "paths_data": {"paths": paths}}
    (prefix.path / "conda-meta" / "isabelle-2025.2-1.json").write_text(json.dumps(record))
    (prefix.path / "conda-meta" / "isabelle-f1-1-Isabelle2025_2_0.json").write_text(json.dumps({"name": "isabelle-f1"}))


def test_while_isabelle_is_being_linked_a_changed_file_names_the_cache_without_its_directory(prefix):
    """No isabelle record in a post-link: this command links isabelle (conda writes the records
    after the post-links), so its files came from the package cache just now (decision 9, (b))."""
    prefix.hook("post-link")
    prefix.edit("src/Pure/b.ML", "B5\n", "edited\n")                        # f2's file
    prefix.edit("bin/new2", "echo new2", "echo mine")                        # f2 creates it
    prefix.isabelle_record.unlink()
    text = prefix.hook("post-link", pkg="isabelle-f3")
    files = [("bin/new2", True), ("src/Pure/b.ML", False)]
    assert texts.conflict_full("f2", files, prefix.tree, cache=texts.CacheCopy(None)) in text
    assert f"conda list -p {prefix.path} --full-name isabelle shows" in text
    # only a created path in the way: no step 2, so no word of the cache
    prefix.edit("src/Pure/b.ML", "edited\n", "B5\n")
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert texts.conflict_full("f2", [("bin/new2", True)], prefix.tree) in text and "package cache" not in text


def test_pre_unlink_does_not_infer_the_cache_from_a_missing_record(prefix):
    """pre-unlink runs before conda removes any record: a missing one says nothing about the cache."""
    prefix.hook("post-link")
    prefix.edit("src/Pure/b.ML", "B5\n", "edited\n")
    prefix.isabelle_record.unlink()
    text = prefix.hook("pre-unlink", "f2")
    assert "could not be fully undone" in text and "package cache" not in text


def test_in_place_edit_through_the_hard_link_selects_the_cache_wording(prefix, tmp_path):
    cache = tmp_path / "pkgs" / "isabelle-2025.2-1"
    fake_isabelle_record(prefix, cache)
    b = prefix.tree / "src" / "Pure" / "b.ML"
    with open(b, "r+b") as f:                       # same inode: the cache copy changes too
        f.seek(len("b1\nb2\nb3\nb4\n"))
        f.write(b"XX")
    assert (cache / "isa" / "src" / "Pure" / "b.ML").read_bytes() == b.read_bytes()
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert texts.conflict_full("f2", [("src/Pure/b.ML", False)], prefix.tree, cache=texts.CacheCopy(cache)) in text
    assert f"Delete\n     {cache} (conda re-creates it from the .conda archive)" in text
    # the same file edited through a new inode: the plain wording
    b.unlink()
    b.write_bytes(prefix.toy.expected(None)["src/Pure/b.ML"][0].replace(b"b5\n", b"YY\n"))
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert texts.conflict_full("f2", [("src/Pure/b.ML", False)], prefix.tree) in text
