"""tools/check-roundtrip (plan decision 17) on the toy chain: the tool against GNU patch."""
import os
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT, snapshot

SCRIPT = ROOT / "tools" / "check-roundtrip"


def gnu(command: str) -> bool:
    return bool(shutil.which(command)) and "GNU" in subprocess.run([command, "--version"], capture_output=True, text=True).stdout


pytestmark = pytest.mark.skipif(not all(map(gnu, ("find", "diff", "patch"))),
                                reason="check-roundtrip needs GNU find, diff and patch; it runs only in the release's ubuntu job")


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


def test_fetch_takes_exactly_the_two_tags_from_a_remote(chain3, tmp_path):
    """The release workflow's form: an empty repository whose remote holds the tags (--fetch)."""
    empty = tmp_path / "fetched"
    subprocess.run(["git", "init", "-q", str(empty)], check=True)
    subprocess.run(["git", "-C", str(empty), "remote", "add", "origin", str(chain3.repo)], check=True)
    r = subprocess.run([sys.executable, str(SCRIPT), str(chain3.tree()), "f3", "-C", str(empty), "--fetch", "origin",
                        "--features-dir", str(chain3.features_d)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    tags = subprocess.run(["git", "-C", str(empty), "tag"], capture_output=True, text=True).stdout.split()
    assert sorted(tags) == sorted([chain3.tags[0], chain3.tag_of("f3")])
    r = subprocess.run([sys.executable, str(SCRIPT), str(chain3.tree()), "f3", "-C", str(tmp_path / "fetched"),
                        "--features-dir", str(chain3.features_d)], capture_output=True, text=True)
    assert r.returncode == 0                              # fetched once, the tags stay


def test_roundtrip_fails_when_the_tool_and_the_repository_disagree(chain3):
    """FD holds f3 while the repository's diff is taken only to f2: A has more than B."""
    r = roundtrip(chain3, chain3.tree(), "f2")
    assert r.returncode == 1 and "A (the tool) against B (GNU patch): the trees differ" in r.stderr


def test_roundtrip_fails_when_a_patch_does_not_apply(chain3):
    p = chain3.features_d / "f2" / "src-Pure-b.ML.patch"
    p.write_text(p.read_text().replace(" b4\n", " b4 edited\n"))
    r = roundtrip(chain3, chain3.tree(), "f3")
    assert r.returncode == 1 and "apply on A exited 1" in r.stderr


FAULTS = {
    "a created file's mode is changed after apply": ("chmod", "the listings (modes and paths) differ"),
    "unapply does nothing": ("noop-unapply", "A after unapply against the pristine tree: the trees differ"),
    "status -v does not list a created file": ("drop-created", "status -v does not show these created files"),
}
WRAPPER = """\
import os, subprocess, sys
fault, args = sys.argv[1], sys.argv[2:]
if fault == "noop-unapply" and "unapply" in args:
    sys.exit(0)
r = subprocess.run([sys.executable, "-m", "isabelle_patch_control", *args], capture_output=True, text=True,
                   env={**os.environ, "PYTHONPATH": %r})
out = r.stdout
if fault == "drop-created" and "status" in args:
    out = "".join(l for l in out.splitlines(True) if "new1.ML" not in l)
if fault == "chmod" and "apply" in args and r.returncode == 0:
    os.chmod(os.path.join(args[args.index("--isabelle-home") + 1], "src", "Pure", "new1.ML"), 0o755)
sys.stdout.write(out); sys.stderr.write(r.stderr); sys.exit(r.returncode)
"""


@pytest.mark.parametrize("fault", FAULTS, ids=lambda f: FAULTS[f][0])
def test_roundtrip_catches_a_tool_that_misbehaves(chain3, tmp_path, fault):
    """Each check of decision 17 against a wrapped tool with one fault."""
    kind, message = FAULTS[fault]
    wrapper = tmp_path / "tool.py"
    wrapper.write_text(WRAPPER % str(ROOT))
    r = roundtrip(chain3, chain3.tree(), "f3", "--tool", f"{sys.executable} {wrapper} {kind}")
    assert r.returncode == 1 and message in r.stderr, r.stdout + r.stderr


def test_roundtrip_refuses_a_bad_pristine_tree_before_copying(chain3):
    """The tags come from the tool's own readers: a `git archive` of the pristine tag has no
    etc/ISABELLE_IDENTIFIER, and a tree with a .git is refused before the two copies are made."""
    tree = chain3.tree()
    (tree / "etc" / "ISABELLE_IDENTIFIER").unlink()
    r = roundtrip(chain3, tree, "f3")
    assert r.returncode == 1 and "no Isabelle tree" in r.stderr and "copies under" not in r.stdout
    tree = chain3.tree()
    (tree / ".git").mkdir()
    r = roundtrip(chain3, tree, "f3")
    assert r.returncode == 1 and "has a .git" in r.stderr and "copies under" not in r.stdout
    r = roundtrip(chain3, chain3.tree(), "nope")
    assert r.returncode == 1 and "provenance.txt is missing" in r.stderr and "copies under" not in r.stdout


def test_roundtrip_keeps_crlf_bytes(toy):
    """The diff goes to GNU patch as bytes: a CRLF file and a non-UTF-8 byte survive both sides."""
    toy.write("etc/crlf.txt", b"crlf 1\r\ncrlf 2\r\n")
    toy.write("etc/latin1.txt", b"caf\xe9\n")
    toy.git("add", "-A")
    toy.git("commit", "-qm", "pristine with a CRLF and a Latin-1 file")
    toy.git("tag", "-f", toy.tags[0])

    def f1():
        toy.write("etc/crlf.txt", b"crlf 1\r\ncrlf 2\r\ncrlf 3\r\n")
        toy.write("etc/latin1.txt", b"caf\xe9 au lait\n")
        toy.write("etc/new_crlf.txt", b"new\r\n")

    toy.feature("f1", f1)
    r = roundtrip(toy, toy.tree(), "f1")
    assert r.returncode == 0, r.stdout + r.stderr


def test_roundtrip_keep(chain3):
    tree = chain3.tree()
    r = roundtrip(chain3, tree, "f3", "--keep")
    assert r.returncode == 0
    kept = [p for p in tree.parent.iterdir() if p.name.startswith("check-roundtrip-")]
    assert len(kept) == 1 and (kept[0] / "A").is_dir() and (kept[0] / "B").is_dir()
