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


def test_a_file_the_packaging_changed_is_listed_not_checked(chain3, pkgs):
    isabelle = pkgs[0]
    (isabelle / "isa/etc/options").write_text("option packaged : bool = true\n")
    paths = json.loads((isabelle / "info/paths.json").read_text())
    for p in paths["paths"]:
        if p["_path"] == "isa/etc/options":
            p["sha256"] = hashlib.sha256(b"option packaged : bool = true\n").hexdigest()
    (isabelle / "info/paths.json").write_text(json.dumps(paths))
    assert check(chain3.tree(), pkgs, []) == ([], ["etc/options"], 6)


def test_refusals(chain3, pkgs):
    t = chain3.tree()
    with pytest.raises(cb.Refused, match="no --feature package holds"):
        check(t, pkgs, ["f9"])
    with pytest.raises(cb.Refused, match="do not form one chain"):
        check(t, (pkgs[0], [p for p in pkgs[1] if "f2" not in p.name]))
