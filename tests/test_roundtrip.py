"""tools/check-roundtrip (plan decision 17) on the toy chain: the tool against GNU patch."""
import os
import subprocess
import sys

from conftest import ROOT, snapshot

SCRIPT = ROOT / "tools" / "check-roundtrip"


def roundtrip(toy, tree, top, *extra):
    return subprocess.run([sys.executable, str(SCRIPT), str(tree), top, "-C", str(toy.repo), "--features-dir",
                           str(toy.features_d), *extra], capture_output=True, text=True, env={**os.environ})


def test_roundtrip_passes_on_the_toy_chain(chain3):
    tree = chain3.tree()
    before = snapshot(tree)
    r = roundtrip(chain3, tree, "f3")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "check-roundtrip: ok" in r.stdout and "shows the 2 created files" in r.stdout
    assert snapshot(tree) == before                                    # the pristine tree is not touched
    assert not [p for p in tree.parent.iterdir() if p.name.startswith("check-roundtrip-")]


def test_roundtrip_fails_when_the_tool_and_the_repository_disagree(chain3):
    """FD holds f3 while the repository's diff is taken only to f2: A has more than B."""
    r = roundtrip(chain3, chain3.tree(), "f2")
    assert r.returncode == 1 and "A (the tool) against B (GNU patch): the trees differ" in r.stderr


def test_roundtrip_fails_when_a_patch_does_not_apply(chain3):
    p = chain3.features_d / "f2" / "src-Pure-b.ML.patch"
    p.write_text(p.read_text().replace(" b4\n", " b4 edited\n"))
    r = roundtrip(chain3, chain3.tree(), "f3")
    assert r.returncode == 1 and "apply on A exited 1" in r.stderr


def test_roundtrip_keep(chain3):
    tree = chain3.tree()
    r = roundtrip(chain3, tree, "f3", "--keep")
    assert r.returncode == 0
    kept = [p for p in tree.parent.iterdir() if p.name.startswith("check-roundtrip-")]
    assert len(kept) == 1 and (kept[0] / "A").is_dir() and (kept[0] / "B").is_dir()
