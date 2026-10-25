"""Decision 5: writes into the tree are one os.replace/os.unlink per file; interruption leaves every
file old or new and the next run converges; write failures leave the tree alone; permission bits;
shared inodes; the directory interface (decision 8)."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT, same_tree, snapshot, tool
from isabelle_patch_control import api, engine

KILL = Path(__file__).parent / "kill_after.py"


def killed(k: int, command: str, tree: Path, features_d: Path) -> int:
    r = subprocess.run([sys.executable, str(KILL), str(k), command, str(tree), str(features_d)],
                       env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True)
    return r.returncode


@pytest.mark.parametrize("k", range(1, 8))
def test_interrupted_apply_leaves_each_file_old_or_new_and_converges(chain3, k):
    t = chain3.tree()
    old, new = chain3.expected(None), chain3.expected("f3")
    assert killed(k, "apply", t, chain3.features_d) == 9
    for rel in set(old) | set(new):
        got = snapshot(t).get(rel)
        assert got in (old.get(rel), new.get(rel)), rel
    assert not Path(str(t) + ".staging").exists() or True       # the killed run could not clean up; the next does
    assert tool(t, chain3.features_d, "apply").code == 0
    same_tree(t, new)
    assert not Path(str(t) + ".staging").exists()


@pytest.mark.parametrize("k", range(1, 8))
def test_interrupted_unapply_converges(applied, k):
    toy, t = applied
    old, new = toy.expected("f3"), toy.expected(None)
    assert killed(k, "unapply", t, toy.features_d) == 9
    for rel in set(old) | set(new):
        assert snapshot(t).get(rel) in (old.get(rel), new.get(rel)), rel
    assert tool(t, toy.features_d, "unapply").code == 0
    same_tree(t, new)


def test_git_write_failure_changes_nothing(fresh, monkeypatch):
    toy, t = fresh
    before = snapshot(t)
    real_run = engine.Git.run

    def failing_run(self, workdir, *args):
        if args[0] == "apply" and "--numstat" not in args:
            return subprocess.CompletedProcess(args, 128, b"", b"fatal: unable to write new index file\n")
        return real_run(self, workdir, *args)

    monkeypatch.setattr(engine.Git, "run", failing_run)
    with pytest.raises(api.WriteFailed) as e:
        api.apply(t, toy.features_d)
    msg = str(e.value)
    assert "fatal: unable to write new index file" in msg and ".patch" in msg and "exit code 128" in msg
    assert "cannot read" not in msg and "corrupt" not in msg          # it does not blame the patch file
    assert snapshot(t) == before
    r = tool(t, toy.features_d, "apply")
    assert r.code == 1 and "git could not finish writing" in r.err


def test_os_replace_failure_is_reported_with_status(fresh, monkeypatch):
    toy, t = fresh

    def failing_replace(src, dst):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", failing_replace)
    r = tool(t, toy.features_d, "apply")
    assert r.code == 1 and "No space left on device" in r.err
    assert r.out.startswith(f"tree {t}")                                   # status printed after the failure


def test_shared_inode_keeps_content_and_mode(fresh, tmp_path):
    """Files hard-linked from the package cache (or another environment) are not changed."""
    toy, t = fresh
    other = tmp_path / "other"
    other.mkdir()
    a, b = t / "src" / "Pure" / "a.ML", t / "bin" / "tool"
    b.chmod(0o755)
    os.link(a, other / "a.ML")
    os.link(b, other / "tool")
    assert tool(t, toy.features_d, "apply").code == 0
    assert (other / "a.ML").read_bytes() == toy.expected(None)["src/Pure/a.ML"][0]
    assert os.stat(other / "tool").st_mode & 0o777 == 0o755
    assert (a.stat().st_ino != (other / "a.ML").stat().st_ino)


@pytest.mark.parametrize("umask", [0o002, 0o077])
def test_permission_bits(chain3, umask):
    """Changed files keep their bits, created files get the patch header's, under any umask;
    apply and apply-to agree."""
    t = chain3.tree()
    (t / "src" / "Pure" / "a.ML").chmod(0o600)
    (t / "src" / "Pure" / "b.ML").chmod(0o664)
    old = os.umask(umask)
    try:
        assert api.apply(t, chain3.features_d).exit_code == 0
        d = chain3.tree()
        api.apply_to(d, chain3.features_d / "f1")
    finally:
        os.umask(old)
    got = snapshot(t)
    assert got["src/Pure/a.ML"][1] == 0o600 and got["src/Pure/b.ML"][1] == 0o664
    assert got["src/Pure/new1.ML"][1] == 0o644 and got["bin/new2"][1] == 0o755
    assert snapshot(d)["src/Pure/new1.ML"][1] == 0o644


def test_directory_interface(chain3, tmp_path):
    d = chain3.tree()
    r = tool(d, chain3.features_d, "status")                               # a tree, so the full interface works too
    assert r.code == 1
    assert api.apply_to(d, chain3.features_d / "f1").exit_code == 0
    same_tree(d, chain3.expected("f1"))
    assert api.apply_to(d, chain3.features_d / "f1").moves == []           # idempotent
    assert api.unapply_from(d, chain3.features_d / "f1").exit_code == 0
    same_tree(d, chain3.expected(None))
    assert [p for p in d.parent.iterdir() if p.name.startswith("isabelle-patch-control-")] == []
    # a plain directory without etc/ISABELLE_ID or etc/ISABELLE_IDENTIFIER: no lock, no provenance
    plain = tmp_path / "plain"
    shutil.copytree(d, plain)
    (plain / "etc" / "ISABELLE_ID").unlink()
    (plain / "etc" / "ISABELLE_IDENTIFIER").unlink()
    assert api.apply_to(plain, chain3.features_d / "f2").exit_code == 0
    assert (plain / "bin" / "new2").exists()
    # a conflict is exit 1 with git's output
    (plain / "src" / "Pure" / "a.ML").write_text("x\n")
    res = api.apply_to(plain, chain3.features_d / "f1")
    assert res.exit_code == 1 and [lv.target for lv in res.conflicts] == ["src/Pure/a.ML"]
    r = subprocess.run([sys.executable, "-m", "isabelle_patch_control", "apply-to", str(plain), str(chain3.features_d / "f1")],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 1 and "CONFLICT  src/Pure/a.ML" in r.stdout


def test_apply_unapply_leaves_the_pristine_file_set(applied):
    toy, t = applied
    assert tool(t, toy.features_d, "unapply").code == 0
    assert snapshot(t).keys() == toy.expected(None).keys()
