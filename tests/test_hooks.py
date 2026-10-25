"""Decision 9 without conda: `conda-hook post-link` and `pre-unlink` against a fake prefix
($PREFIX/isa, conda-meta/, share/isabelle_patch_control/features.d), reading .messages.txt."""
import fcntl
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from conftest import run_cli, snapshot
from isabelle_patch_control import api, cli, engine, texts


class Prefix:
    def __init__(self, toy, root: Path, at=None, *, features=True):
        self.toy = toy
        self.path = root
        root.mkdir()
        self.tree = root / "isa"
        toy.tree(at).rename(self.tree)
        (root / "conda-meta").mkdir()
        self.features_d = root / cli.FEATURES_D
        if features:
            shutil.copytree(toy.features_d, self.features_d)
        self.messages = root / ".messages.txt"

    def hook(self, *args, pkg: str | None = None) -> str:
        """Run the hook as conda would; return what it appended to .messages.txt (conda prints and
        deletes the file after every hook, so each call starts empty)."""
        env = {"PREFIX": str(self.path)}
        if pkg:
            env["PKG_NAME"] = pkg
        r = run_cli("conda-hook", *args, env=env)
        assert r.code == 0 and r.out == "" and r.err == ""
        text = self.messages.read_text() if self.messages.exists() else ""
        if self.messages.exists():
            self.messages.unlink()
        return text

    def edit(self, rel: str, old: str, new: str):
        p = self.tree.joinpath(*rel.split("/"))
        p.write_text(p.read_text().replace(old, new))


@pytest.fixture
def prefix(chain3, tmp_path):
    return Prefix(chain3, tmp_path / "env")


# --- post-link

def test_post_link_applies_the_whole_chain_once(prefix):
    text = prefix.hook("post-link", pkg="isabelle-f1")
    assert text == texts.changed(prefix.tree, applied=["f1", "f2", "f3"]) + "\n" + texts.HEAP_PARAGRAPH + "\n"
    assert api.status(prefix.tree, prefix.features_d).exit_code() == 0
    assert prefix.hook("post-link", pkg="isabelle-f2") == ""              # nothing changed: not a word
    assert prefix.hook("post-link", pkg="isabelle-f3") == ""


def test_post_link_without_features_d_or_with_empty_chain(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env", features=False)
    assert p.hook("post-link") == ""
    p.features_d.mkdir(parents=True)
    assert p.hook("post-link") == ""


def test_post_link_conflict_full_diagnostic_only_from_the_chain_top(prefix):
    prefix.edit("src/Pure/b.ML", "b5\n", "edited\n")                        # f2's file
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert text == (texts.changed(prefix.tree, applied=["f1"]) + "\n" + texts.HEAP_PARAGRAPH + "\n"
                    + texts.conflict_full("f2", ["src/Pure/b.ML"], prefix.tree) + "\n")
    assert "was NOT applied: src/Pure/b.ML under" in text and "--force-reinstall isabelle" in text
    assert "isabelle-patch-control help" in text.splitlines()[-1]
    # a lower package's hook (or the one being installed below the top): one line
    assert prefix.hook("post-link", pkg="isabelle-f1") == texts.conflict_line("f2", ["src/Pure/b.ML"]) + "\n"
    assert prefix.hook("post-link", pkg="isabelle-f2") == texts.conflict_line("f2", ["src/Pure/b.ML"]) + "\n"
    # unset or unknown PKG_NAME counts as the top
    assert prefix.hook("post-link").startswith(texts.PREFIX + "f2 was NOT applied")
    assert prefix.hook("post-link", pkg="isabelle").startswith(texts.PREFIX + "f2 was NOT applied")


def test_post_link_lock_busy(prefix):
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        engine.LOCK_TIMEOUT, saved = 0.2, engine.LOCK_TIMEOUT
        try:
            text = prefix.hook("post-link", pkg="isabelle-f3")
        finally:
            engine.LOCK_TIMEOUT = saved
            fcntl.flock(f, fcntl.LOCK_UN)
    assert text.startswith("another isabelle-patch-control run holds the lock on")
    assert text.rstrip().endswith("Retry later." + texts.LOCK_BUSY_HOOK_TAIL)


def test_post_link_on_the_old_build(chain3, tmp_path):
    p = Prefix(chain3, tmp_path / "env")
    (p.tree / "etc" / "ISABELLE_ID").write_text("5533cd83156e\n")
    text = p.hook("post-link", pkg="isabelle-f3")
    assert text.startswith(texts.PREFIX) and "conda update --all" in text


# --- pre-unlink

def test_pre_unlink_reverses_and_reports(prefix):
    prefix.hook("post-link")
    text = prefix.hook("pre-unlink", "f3")
    assert text == texts.undone("f3", prefix.tree, ["f3"]) + "\n"
    assert text.splitlines()[1] == texts.UPDATE_LINE
    text = prefix.hook("pre-unlink", "f1")                                  # f1 and f2 go: back at the bottom
    assert text == texts.undone_at_bottom("f1", prefix.tree) + "\n"
    assert "you may delete heaps/" in text
    assert prefix.hook("pre-unlink", "f1") == ""                             # nothing left to reverse
    assert snapshot(prefix.tree).keys() == prefix.toy.expected(None).keys()


def test_pre_unlink_never_applies(prefix):
    assert prefix.hook("pre-unlink", "f2") == ""
    assert api.status(prefix.tree, prefix.features_d).exit_code() == 1


def test_pre_unlink_residue_after_a_conflict(prefix):
    prefix.hook("post-link")
    prefix.edit("src/Pure/new1.ML", "new1 line\n", "edited\n")              # created by f1, changed by f3
    text = prefix.hook("pre-unlink", "f3")
    assert text == texts.residue("f3", texts.REASON_CONFLICT, [("src/Pure/new1.ML", False)], prefix.tree) + "\n"
    assert "(reason: a file has unexpected content)" in text
    assert texts.UPDATE_LINE in text and "  1. Save any edits" in text and "  3. Delete every file marked" in text
    assert "Retry later" not in text
    assert api.status(prefix.tree, prefix.features_d).levels["src/Pure/a.ML"].level == 1   # what could move, moved
    text = prefix.hook("pre-unlink", "f1")
    assert f"  src/Pure/new1.ML   {texts.CREATED}" in text                   # f1 created it


def test_pre_unlink_residue_after_a_lock_timeout(prefix):
    prefix.hook("post-link")
    with open(prefix.tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        engine.LOCK_TIMEOUT, saved = 0.2, engine.LOCK_TIMEOUT
        try:
            text = prefix.hook("pre-unlink", "f2")
        finally:
            engine.LOCK_TIMEOUT = saved
            fcntl.flock(f, fcntl.LOCK_UN)
    assert text == texts.residue("f2", texts.REASON_LOCK, [("README", False), ("bin/new2", True), ("src/Pure/b.ML", False)],
                                 prefix.tree, lock_package=("isabelle-f3", "1")) + "\n"
    assert f"  conda install {texts.CHANNELS} isabelle-f3=1; then conda remove isabelle-f3" in text
    assert "Retry later" not in text and "1. Save" not in text


def test_pre_unlink_residue_when_the_chain_does_not_link(prefix):
    prefix.hook("post-link")
    shutil.rmtree(prefix.features_d / "f2")
    text = prefix.hook("pre-unlink", "f3")
    assert text.startswith(f"{texts.PREFIX}f3 could not be fully undone (reason: {texts.REASON_CHAIN})")
    assert "  src/Pure/a.ML\n" in text and "  src/Pure/new1.ML\n" in text
    assert "--force-reinstall isabelle" in text


def test_pre_unlink_of_an_unknown_feature(prefix):
    text = prefix.hook("pre-unlink", "f9")
    assert text.startswith(texts.PREFIX) and "f9" in text


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


def test_in_place_edit_through_the_hard_link_selects_the_cache_wording(prefix, tmp_path):
    cache = tmp_path / "pkgs" / "isabelle-2025.2-1"
    fake_isabelle_record(prefix, cache)
    b = prefix.tree / "src" / "Pure" / "b.ML"
    with open(b, "r+b") as f:                       # same inode: the cache copy changes too
        f.seek(len("b1\nb2\nb3\nb4\n"))
        f.write(b"XX")
    assert (cache / "isa" / "src" / "Pure" / "b.ML").read_bytes() == b.read_bytes()
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert texts.conflict_full("f2", ["src/Pure/b.ML"], prefix.tree, cache_dir=cache) in text
    assert f"Delete {cache} (conda re-creates" in text
    # the same file edited through a new inode: the plain wording
    b.unlink()
    b.write_bytes(prefix.toy.expected(None)["src/Pure/b.ML"][0].replace(b"b5\n", b"YY\n"))
    text = prefix.hook("post-link", pkg="isabelle-f3")
    assert texts.conflict_full("f2", ["src/Pure/b.ML"], prefix.tree) in text
