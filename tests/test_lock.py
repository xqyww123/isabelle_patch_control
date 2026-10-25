"""Decision 5: the lock on etc/ISABELLE_ID; shared for status and --dry-run, exclusive for writes;
busy within the limit; the staging directory belongs to the lock holder alone."""
import errno
import fcntl
import stat
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from conftest import make_writable, same_tree, tool
from isabelle_patch_control import api, engine, texts


@pytest.fixture
def quick_lock(monkeypatch):
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.3)


@contextmanager
def held(tree: Path, exclusive: bool):
    with open(tree / engine.LOCK_FILE, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def test_status_and_dry_run_on_a_read_only_tree(fresh):
    """A system-wide install: neither the tree nor its parent is writable; status and --dry-run
    write nothing there (decision 5), apply fails with the status printed."""
    toy, t = fresh
    for p in [t.parent, t, *t.rglob("*")]:
        p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)
    try:
        assert tool(t, toy.features_d, "status").code == 1
        r = tool(t, toy.features_d, "apply", "--dry-run")
        assert r.code == 0 and "src/Pure/a.ML  level 0 -> 3" in r.out
        r = tool(t, toy.features_d, "apply")
        assert r.code == 1 and "Permission denied" in r.err and r.out.startswith(f"tree {t}")
    finally:
        t.parent.chmod(t.parent.stat().st_mode | stat.S_IWUSR)
        make_writable(t)


def test_any_os_error_is_reported_with_status(fresh, monkeypatch):
    """EROFS on the lock file, ENOSPC while writing a copy (no file name in the error): exit 1,
    one message, the status printed, never a traceback."""
    toy, t = fresh
    real_open = open

    def read_only_open(path, mode="r", *args, **kw):
        if "+" in mode:
            raise OSError(errno.EROFS, "Read-only file system", str(path))
        return real_open(path, mode, *args, **kw)

    monkeypatch.setattr(engine, "open", read_only_open, raising=False)
    r = tool(t, toy.features_d, "apply")
    assert r.code == 1 and r.out.startswith(f"tree {t}")
    assert r.err == texts.PREFIX + texts.os_error(OSError(errno.EROFS, "Read-only file system", str(t / "etc" / "ISABELLE_ID"))) + "\n"
    assert r.err.startswith(texts.PREFIX + f"Read-only file system ({t / 'etc' / 'ISABELLE_ID'}); nothing in the tree was changed.")
    monkeypatch.undo()
    real_copy = engine.Replayer._copy

    def full_disk_copy(self, target, content):
        if self.workdir.name.endswith(".staging"):
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_copy(self, target, content)

    monkeypatch.setattr(engine.Replayer, "_copy", full_disk_copy)
    r = tool(t, toy.features_d, "unapply")
    assert r.code == 1 and r.out.startswith(f"tree {t}")
    assert r.err == texts.PREFIX + texts.os_error(OSError(errno.ENOSPC, "No space left on device")) + "\n"
    assert r.err.startswith(texts.PREFIX + "No space left on device; nothing in the tree was changed.")
    same_tree(t, toy.expected(None))


def test_busy_is_reported_within_the_limit(fresh, quick_lock):
    toy, t = fresh
    with held(t, exclusive=True):
        start = time.monotonic()
        with pytest.raises(api.Busy) as e:
            api.status(t, toy.features_d)
        assert 0.3 <= time.monotonic() - start < 3
        assert str(e.value) == texts.lock_busy(t / engine.LOCK_FILE, 0.3)
        assert "then retry" in str(e.value) and str(t / "etc" / "ISABELLE_ID") in str(e.value)
    assert api.status(t, toy.features_d).exit_code == 1


def test_shared_lock_lets_status_through_but_not_apply(fresh, quick_lock):
    toy, t = fresh
    with held(t, exclusive=False):
        assert api.status(t, toy.features_d).exit_code == 1
        assert api.apply(t, toy.features_d, dry_run=True).exit_code == 0
        with pytest.raises(api.Busy):
            api.apply(t, toy.features_d)


def test_two_exclusive_runs_serialize(fresh):
    toy, t = fresh
    results, errors = [], []

    def run():
        try:
            results.append(api.apply(t, toy.features_d))
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


def test_runs_without_the_exclusive_lock_leave_the_staging_directory_alone(fresh, quick_lock):
    """Decision 5: the staging directory belongs to the holder of the exclusive lock.  A pre-unlink
    that gave up on the lock computes levels without it; status and --dry-run hold the shared lock;
    none of them may touch what the holder is using."""
    toy, t = fresh
    staging = Path(str(t) + ".staging")
    staging.mkdir()
    (staging / "sentinel").write_text("holder's file")
    with held(t, exclusive=True):
        st = api.status(t, toy.features_d, lock=False)
        assert {s.state for s in st.features} == {"not-applied"}
        assert (staging / "sentinel").read_text() == "holder's file"
        with pytest.raises(api.Busy):
            api.status(t, toy.features_d)
    api.status(t, toy.features_d)
    api.apply(t, toy.features_d, dry_run=True)
    assert (staging / "sentinel").read_text() == "holder's file"
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
