"""Decision 5: the lock on etc/ISABELLE_ID; shared for status and --dry-run, exclusive for writes;
busy within the limit; the staging directory belongs to the lock holder alone."""
import fcntl
import os
import stat
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from conftest import make_writable, same_tree, tool
from isabelle_patch_control import api, engine, texts


@contextmanager
def held(tree: Path, exclusive: bool):
    with open(tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def test_status_and_dry_run_on_a_read_only_tree(fresh):
    toy, t = fresh
    for p in t.rglob("*"):
        p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)
    try:
        assert tool(t, toy.features_d, "status").code == 1
        r = tool(t, toy.features_d, "apply", "--dry-run")
        assert r.code == 0 and "src/Pure/a.ML  level 0 -> 3" in r.out
        r = tool(t, toy.features_d, "apply")
        assert r.code == 1 and "Permission denied" in r.err
    finally:
        make_writable(t)


def test_busy_is_reported_within_the_limit(fresh):
    toy, t = fresh
    with held(t, exclusive=True):
        start = time.monotonic()
        with pytest.raises(api.Busy) as e:
            api.status(t, toy.features_d, timeout=0.3)
        assert 0.3 <= time.monotonic() - start < 3
        assert str(e.value) == texts.lock_busy(t / engine.LOCK_FILE, 0.3)
        assert "Retry later" in str(e.value) and str(t / "etc" / "ISABELLE_ID") in str(e.value)
    assert api.status(t, toy.features_d, timeout=0.3).exit_code() == 1


def test_shared_lock_lets_status_through_but_not_apply(fresh):
    toy, t = fresh
    with held(t, exclusive=False):
        assert api.status(t, toy.features_d, timeout=0.3).exit_code() == 1
        assert api.apply(t, toy.features_d, dry_run=True, timeout=0.3).exit_code == 0
        with pytest.raises(api.Busy):
            api.apply(t, toy.features_d, timeout=0.3)


def test_two_exclusive_runs_serialize(fresh):
    toy, t = fresh
    results, errors = [], []

    def run():
        try:
            results.append(api.apply(t, toy.features_d, timeout=30))
        except Exception as e:                                           # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert not errors and len(results) == 2
    assert sorted(len(r.moves) for r in results) == [0, 7]              # one did the work, the other found it done
    same_tree(t, toy.expected("f3"))


def test_unlocked_status_uses_a_temporary_directory_not_the_staging_one(fresh):
    """A pre-unlink that gave up on the lock computes levels without it and must not touch the
    staging directory the lock holder is using."""
    toy, t = fresh
    staging = Path(str(t) + ".staging")
    with held(t, exclusive=True):
        staging.mkdir()
        (staging / "sentinel").write_text("holder's file")
        st = api.status(t, toy.features_d, lock=False)
        assert {s.state for s in st.features} == {"not-applied"}
        assert (staging / "sentinel").read_text() == "holder's file"
        with pytest.raises(api.Busy):
            api.status(t, toy.features_d, timeout=0.2)
    staging.joinpath("sentinel").unlink()
    staging.rmdir()


def test_exclusive_run_empties_a_stale_staging_directory(fresh):
    toy, t = fresh
    staging = Path(str(t) + ".staging")
    staging.mkdir()
    (staging / "leftover").write_text("x")
    assert api.apply(t, toy.features_d).exit_code == 0
    assert not staging.exists()


def test_lock_is_on_the_existing_id_file_and_creates_nothing(fresh):
    toy, t = fresh
    before = sorted(p.relative_to(t) for p in t.rglob("*"))
    api.status(t, toy.features_d)
    assert sorted(p.relative_to(t) for p in t.rglob("*")) == before
    assert (t / "etc" / "ISABELLE_ID").read_text() == "89701cf1768e\n"
    assert os.listdir(t.parent).count(t.name + ".staging") == 0
