"""tools/check-bytes (plan decision 15): the byte oracle the hook-layer tests and the acceptance
legs use, checked here against trees the tool itself put in each state."""
import hashlib
import importlib.machinery
import importlib.util
import json
import shutil

import pytest

from conftest import ROOT, api

_loader = importlib.machinery.SourceFileLoader("check_bytes", str(ROOT / "tools" / "check-bytes"))
cb = importlib.util.module_from_spec(importlib.util.spec_from_loader("check_bytes", _loader))
_loader.exec_module(cb)


def unpacked(toy, root):
    """The isabelle package and the three feature packages as conda unpacks them into pkgs/."""
    isabelle = root / "isabelle-2025.2-1"
    shutil.copytree(toy.tree(), isabelle / "isa")
    paths = [{"_path": p.relative_to(isabelle).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted((isabelle / "isa").rglob("*")) if p.is_file()]
    (isabelle / "info").mkdir()
    (isabelle / "info" / "paths.json").write_text(json.dumps({"paths": paths, "paths_version": 1}))
    features = []
    for name in reversed(toy.names):                 # any order: the chain is read from provenance.txt
        pkg = root / f"isabelle-{name}-1-Isabelle2025_2_0"
        shutil.copytree(toy.features_d / name, pkg / cb.FEATURES_D / name)
        features.append(pkg)
    return isabelle, features


@pytest.fixture
def pkgs(chain3, tmp_path):
    return unpacked(chain3, tmp_path / "pkgs")


def check(tree, pkgs, applied=None):
    return cb.check(tree, pkgs[0], pkgs[1], applied)


def test_every_state_the_tool_leaves(chain3, pkgs):
    t = chain3.tree()
    assert check(t, pkgs, []) == ([], [], 7)       # a.ML, new1.ML, c.ML, etc/options, b.ML, bin/new2, README
    problems, _, _ = check(t, pkgs)
    assert len(problems) == 7
    api.apply(t, chain3.features_d, feature="f1")
    assert check(t, pkgs, ["f1"])[0] == []
    assert check(t, pkgs, [])[0]
    api.apply(t, chain3.features_d)
    assert check(t, pkgs)[0] == []
    assert any("src/Pure/a.ML" in p for p in check(t, pkgs, ["f1", "f2"])[0])
    api.unapply(t, chain3.features_d)
    assert check(t, pkgs, [])[0] == []


def test_what_it_catches(chain3, pkgs):
    t = chain3.tree()
    api.apply(t, chain3.features_d)
    b = t / "src/Pure/b.ML"
    applied_b = b.read_bytes()
    b.write_text("edited\n")
    assert check(t, pkgs)[0] == ["src/Pure/b.ML: blob " + cb.blob_id(b"edited\n")[:12]
                                 + ", but f2 (applied) leaves it at " + cb.header(next((chain3.features_d / "f2").glob("src-Pure-b*")))[2]]
    b.write_bytes(applied_b)
    api.unapply(t, chain3.features_d)
    b.write_text("edited\n")
    assert check(t, pkgs, [])[0] == ["src/Pure/b.ML: not the isabelle package's content, but no feature that changes it is applied"]
    (t / "src/Pure/b.ML").write_bytes((pkgs[0] / "isa/src/Pure/b.ML").read_bytes())
    (t / "src/Pure/new1.ML").write_text("left behind\n")       # a created file that stayed
    (t / "src/Pure/c.ML").unlink()                               # a deleted file that was not restored
    assert check(t, pkgs, [])[0] == ["src/Pure/c.ML: missing, but no feature that changes it is applied",
                                     "src/Pure/new1.ML: exists, but no feature that creates it is applied"]


def test_the_package_cache_is_checked_too(chain3, pkgs):
    """An in-place edit through the hard link changes the cache's copy: reported, never trusted."""
    t = chain3.tree()
    (pkgs[0] / "isa/src/Pure/a.ML").write_text("edited through the hard link\n")
    problems, _, _ = check(t, pkgs, [])
    assert problems == ["src/Pure/a.ML: the package cache's copy of isa/src/Pure/a.ML is not what paths.json records (edited in place)"]


def test_a_file_the_packaging_changed(chain3, pkgs):
    """Not checked while a feature touching it is applied (listed instead); once none is, it must be
    the package's content again (plan decision 15)."""
    isabelle, packaged = pkgs[0], b"option packaged : bool = true\n"
    (isabelle / "isa/etc/options").write_bytes(packaged)
    paths = json.loads((isabelle / "info/paths.json").read_text())
    for p in paths["paths"]:
        if p["_path"] == "isa/etc/options":
            p["sha256"] = hashlib.sha256(packaged).hexdigest()
    (isabelle / "info/paths.json").write_text(json.dumps(paths))
    t = chain3.tree()
    api.apply(t, chain3.features_d)
    assert check(t, pkgs) == ([], ["etc/options"], 6)
    api.unapply(t, chain3.features_d)                    # the toy tree's etc/options is not the packaged one
    assert check(t, pkgs, []) == (
        ["etc/options: not the isabelle package's content, but no feature that changes it is applied"], [], 7)
    (t / "etc/options").write_bytes(packaged)
    assert check(t, pkgs, []) == ([], [], 7)


def test_empty_files_and_a_path_with_a_space(toy, tmp_path):
    """git writes no ---/+++ lines for an empty file and a TAB after a path with a space; the block
    header is read from the diff --git and index lines (common.block_header)."""
    toy.feature("f1", lambda: (toy.write("src/Pure/empty.ML", ""), toy.write("src/Pure/with space.ML", "one\ntwo\n")))
    toy.feature("f2", lambda: (toy.write("src/Pure/new.ML", ""),
                               toy.edit("src/Pure/with space.ML", lambda s: s.replace("two", "TWO"))))
    assert cb.header(toy.features_d / "f1" / "src-Pure-empty.ML.patch")[1:] == ("0000000", "e69de29")
    assert cb.header(toy.features_d / "f1" / "src-Pure-with space.ML.patch")[0] == "src/Pure/with space.ML"
    deletion = b"diff --git a/src/Pure/e.ML b/src/Pure/e.ML\ndeleted file mode 100644\nindex e69de29..0000000\n"
    assert cb.block_header(deletion) == ("src/Pure/e.ML", "e69de29", "0000000")
    pk = unpacked(toy, tmp_path / "pkgs")
    t = toy.tree()
    assert check(t, pk, []) == ([], [], 3)
    api.apply(t, toy.features_d, feature="f1")
    assert check(t, pk, ["f1"])[0] == []
    api.apply(t, toy.features_d)
    assert check(t, pk)[0] == []
    (t / "src/Pure/new.ML").write_text("not empty\n")
    assert check(t, pk)[0] == [f"src/Pure/new.ML: blob {cb.blob_id(b'not empty' + bytes([10]))[:12]}, but f2 (applied) leaves it at e69de29"]
    (t / "src/Pure/new.ML").write_text("")
    api.unapply(t, toy.features_d)
    assert check(t, pk, [])[0] == []


def test_refusals(chain3, pkgs):
    t = chain3.tree()
    with pytest.raises(cb.Refused, match="no --feature package holds"):
        check(t, pkgs, ["f9"])
    with pytest.raises(cb.Refused, match="do not form one chain"):
        check(t, (pkgs[0], [p for p in pkgs[1] if "f2" not in p.name]))
