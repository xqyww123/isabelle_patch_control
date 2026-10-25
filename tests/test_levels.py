"""Decisions 6 and 7: file levels, the four displayed states, apply/unapply/--dry-run, the
scenarios of review 1 C3, multi-level files, a simulated relink."""
import pytest

from conftest import same_tree, snapshot, tool
from isabelle_patch_control import api, texts


def states(toy, t) -> dict[str, str]:
    st = api.status(t, toy.features_d)
    return {fd.name: s.state for fd, s in zip(st.chain, st.features)}


def levels(toy, t) -> dict[str, int | None]:
    return {k: lv.level for k, lv in api.status(t, toy.features_d).levels.items()}


# --- the fresh stacked tree (scenario 1) and the fully applied tree

def test_fresh_tree(fresh):
    toy, t = fresh
    assert states(toy, t) == {"f1": "not-applied", "f2": "not-applied", "f3": "not-applied"}
    assert set(levels(toy, t).values()) == {0}
    dry = tool(t, toy.features_d, "apply", "--dry-run")
    assert dry.code == 0 and sorted(dry.out.splitlines()) == sorted([
        "  src/Pure/a.ML  level 0 -> 3", "  src/Pure/new1.ML  level 0 -> 3", "  src/Pure/c.ML  level 0 -> 1",
        "  etc/options  level 0 -> 1", "  src/Pure/b.ML  level 0 -> 2", "  bin/new2  level 0 -> 2", "  README  level 0 -> 2"])
    assert tool(t, toy.features_d, "apply", "--dry-run", "-q").out == ""
    assert tool(t, toy.features_d, "apply", "-v", "--dry-run").out.splitlines()[0] == f"tree {t}   features.d {toy.features_d}"
    same_tree(t, toy.expected(None))                       # a dry run changes nothing
    down = tool(t, toy.features_d, "unapply", "--dry-run")
    assert (down.code, down.out) == (0, "")


def test_apply_everything(fresh):
    toy, t = fresh
    r = tool(t, toy.features_d, "apply")
    assert r.code == 0
    assert r.out == texts.changed(t, applied=["f1", "f2", "f3"]) + "\n" + texts.HEAP_PARAGRAPH + "\n"
    same_tree(t, toy.expected("f3"))
    assert states(toy, t) == {"f1": "applied", "f2": "applied", "f3": "applied"}
    assert tool(t, toy.features_d, "status").code == 0
    dry = tool(t, toy.features_d, "apply", "--dry-run")
    assert (dry.code, dry.out) == (0, "")                  # a fully applied tree lists no file
    again = tool(t, toy.features_d, "apply")
    assert (again.code, again.out) == (0, "")


def test_unapply_everything(applied):
    toy, t = applied
    r = tool(t, toy.features_d, "unapply")
    assert r.code == 0
    assert r.out == texts.changed(t, reversed=["f1", "f2", "f3"]) + "\n" + texts.BACK_AT_BOTTOM + "\n"
    same_tree(t, toy.expected(None))
    assert not (t / "src" / "Pure" / "new1.ML").exists() and not (t / "bin" / "new2").exists()


def test_feature_numbers_differ_from_touch_order(chain3):
    """a.ML is touched by features 1 and 3.  On a tree at f1, `apply --feature f2` must leave a.ML
    at level 1 (its target below 2 is 1) and move only f2's files."""
    t = chain3.tree("f1")
    assert levels(chain3, t)["src/Pure/a.ML"] == 1
    r = tool(t, chain3.features_d, "apply", "--feature", "f2", "--dry-run")
    assert sorted(r.out.splitlines()) == ["  README  level 0 -> 2", "  bin/new2  level 0 -> 2", "  src/Pure/b.ML  level 0 -> 2"]
    assert tool(t, chain3.features_d, "apply", "--feature", "f2").code == 0
    same_tree(t, chain3.expected("f2"))
    assert states(chain3, t) == {"f1": "applied", "f2": "applied", "f3": "not-applied"}
    assert tool(t, chain3.features_d, "status", "--feature", "f2").code == 0
    assert tool(t, chain3.features_d, "status").code == 1


def test_stacked_context_on_every_tree(chain3):
    """f3's hunk on a.ML has f1's line as context (the syntax_phases.ML shape): correct on the
    fresh, the half-applied and the fully applied tree, for status and both directions."""
    for at, want in ((None, 0), ("f1", 1), ("f3", 3)):
        t = chain3.tree(at)
        assert levels(chain3, t)["src/Pure/a.ML"] == want
        st = tool(t, chain3.features_d, "status")
        assert "CONFLICT" not in st.out and ("below" in st.out) == False
        up, down = tool(t, chain3.features_d, "apply", "--dry-run"), tool(t, chain3.features_d, "unapply", "--dry-run")
        assert up.code == 0 and down.code == 0
        assert (f"  src/Pure/a.ML  level {want} -> 3" in up.out) == (want < 3)
        assert (f"  src/Pure/a.ML  level {want} -> 0" in down.out) == (want > 0)
        same_tree(t, chain3.expected(at))                                 # dry runs change nothing
        assert tool(t, chain3.features_d, "apply").code == 0
        same_tree(t, chain3.expected("f3"))
        assert tool(t, chain3.features_d, "unapply").code == 0
        same_tree(t, chain3.expected(None))


def test_half_applied(applied):
    toy, t = applied
    (t / "src" / "Pure" / "a.ML").write_bytes(toy.expected("f1")["src/Pure/a.ML"][0])      # a.ML back to level 1
    st = api.status(t, toy.features_d)
    assert states(toy, t) == {"f1": "applied", "f2": "applied", "f3": "half-applied"}
    assert st.features[2].below == 1
    r = tool(t, toy.features_d, "status")
    assert r.code == 1 and "half-applied f3" in r.out and "2 files, 1 below" in r.out
    assert tool(t, toy.features_d, "apply", "--dry-run").out == "  src/Pure/a.ML  level 1 -> 3\n"
    assert tool(t, toy.features_d, "apply").code == 0
    same_tree(t, toy.expected("f3"))


def test_lost_change_reads_half_applied(applied):
    """Scenario 4: a file only f2 touches is back at its base content."""
    toy, t = applied
    (t / "README").write_bytes(toy.expected(None)["README"][0])
    assert states(toy, t) == {"f1": "applied", "f2": "half-applied", "f3": "applied"}


def test_hand_edit_is_conflict_and_caps_apply(fresh):
    """Scenario 3: an edit inside f2's hunk of b.ML.  f2 reads CONFLICT; apply stops below f2."""
    toy, t = fresh
    b = t / "src" / "Pure" / "b.ML"
    b.write_text(b.read_text().replace("b5\n", "edited\n"))
    r = tool(t, toy.features_d, "apply")
    assert r.code == 1
    assert "CONFLICT  src/Pure/b.ML  no level" in r.out and "level 0:" in r.out and "level 2:" in r.out
    assert texts.changed(t, applied=["f1"]) in r.out
    assert states(toy, t) == {"f1": "applied", "f2": "CONFLICT", "f3": "not-applied"}
    st = tool(t, toy.features_d, "status")
    assert st.code == 1 and "CONFLICT    f2" in st.out.replace("CONFLICT     f2", "CONFLICT    f2")
    assert "src/Pure/b.ML" in st.out
    assert tool(t, toy.features_d, "apply", "--feature", "f1").code == 0          # below the CONFLICT: fine
    # unapply moves what it can and lists what it cannot
    r = tool(t, toy.features_d, "unapply")
    assert r.code == 1 and "CONFLICT  src/Pure/b.ML" in r.out
    assert levels(toy, t)["src/Pure/a.ML"] == 0


def test_covered_case_is_just_applied(applied):
    """Scenario 2: a file changed by a lower and an upper feature, both applied."""
    toy, t = applied
    assert levels(toy, t)["src/Pure/a.ML"] == 3 and levels(toy, t)["src/Pure/new1.ML"] == 3
    assert states(toy, t)["f1"] == "applied"


def test_upper_feature_moves_a_line_the_lower_added(toy):
    """Scenario 5: g2 moves g1's line elsewhere; the file is at level 2, nothing is re-applied."""
    toy.feature("g1", lambda: toy.edit("src/Pure/a.ML", lambda s: s.replace("a3\n", "a3\nX\n")))
    toy.feature("g2", lambda: toy.edit("src/Pure/a.ML", lambda s: s.replace("a3\nX\n", "a3\n").replace("a9\n", "a9\nX\n")))
    t = toy.tree("g2")
    assert levels(toy, t) == {"src/Pure/a.ML": 2}
    assert states(toy, t) == {"g1": "applied", "g2": "applied"}
    assert tool(t, toy.features_d, "apply", "--dry-run").out == ""
    assert tool(t, toy.features_d, "unapply").code == 0
    same_tree(t, toy.expected(None))


def test_hole_below_marker(fresh):
    """f2 applied while f1 is not (their files are disjoint): f2 shows (hole below), exit 1."""
    toy, t = fresh
    final = toy.expected("f3")
    for rel in ("src/Pure/b.ML", "bin/new2", "README"):
        p = t.joinpath(*rel.split("/"))
        p.parent.mkdir(exist_ok=True)
        p.write_bytes(final[rel][0])
    assert states(toy, t) == {"f1": "not-applied", "f2": "applied", "f3": "not-applied"}
    r = tool(t, toy.features_d, "status")
    assert r.code == 1 and "(hole below)" in [l for l in r.out.splitlines() if " f2 " in l][0]
    assert tool(t, toy.features_d, "status", "--feature", "f2").code == 1


@pytest.mark.parametrize("below", ["half-applied", "CONFLICT"])
def test_hole_below_counts_any_feature_that_is_not_applied(applied, below):
    """Decision 6: `status --feature F` is 0 only when F and everything below it are applied; an
    interrupted run leaves exactly this shape (files move in path order, not chain order)."""
    toy, t = applied
    options = t / "etc" / "options"
    options.write_bytes(toy.expected(None)["etc/options"][0] if below == "half-applied" else b"other\n")
    assert states(toy, t) == {"f1": below, "f2": "applied", "f3": "applied"}
    r = tool(t, toy.features_d, "status")
    assert r.code == 1
    assert all(l.endswith("(hole below)") for l in r.out.splitlines() if " f2 " in l or " f3 " in l)
    assert tool(t, toy.features_d, "status", "--feature", "f3").code == 1
    assert tool(t, toy.features_d, "status", "--feature", "f1").code == 1


# --- a CONFLICT file that two features touch (a.ML: f1 and f3)

def test_conflict_in_a_shared_file_caps_apply_below_its_lowest_feature(fresh):
    toy, t = fresh
    a = t / "src" / "Pure" / "a.ML"
    a.write_text(a.read_text().replace("a3\n", "edited\n"))
    r = tool(t, toy.features_d, "apply")
    assert r.code == 1
    assert states(toy, t) == {"f1": "CONFLICT", "f2": "not-applied", "f3": "CONFLICT"}
    assert tool(t, toy.features_d, "apply", "--feature", "f1").code == 1
    assert tool(t, toy.features_d, "apply", "--feature", "f2").code == 1


def test_unapply_of_a_shared_conflict_file_is_in_the_way_by_its_highest_feature(applied):
    toy, t = applied
    a = t / "src" / "Pure" / "a.ML"
    a.write_text(a.read_text().replace("a5\n", "edited\n"))
    r = tool(t, toy.features_d, "unapply", "--feature", "f3")
    assert r.code == 1 and "CONFLICT  src/Pure/a.ML" in r.out


def test_unapply_passes_a_conflict_file_below_its_target(applied):
    """b.ML (f2 only) is CONFLICT; reversing f3 does not need it, so exit 0, and a.ML (f1 and f3)
    comes down to level 1."""
    toy, t = applied
    b = t / "src" / "Pure" / "b.ML"
    b.write_text(b.read_text().replace("B5\n", "edited\n"))
    r = tool(t, toy.features_d, "unapply", "--feature", "f3")
    assert r.code == 0 and levels(toy, t)["src/Pure/a.ML"] == 1


def test_features_above_a_conflict_stay_applied(applied):
    """apply only moves files up: after a hand edit in f2's file, a new top package g4 is not
    applied, and f3 stays applied."""
    toy, t = applied
    toy.feature("g4", lambda: toy.write("src/Pure/g4.ML", "g4\n"))
    b = t / "src" / "Pure" / "b.ML"
    b.write_text(b.read_text().replace("B5\n", "edited\n"))
    assert tool(t, toy.features_d, "apply").code == 1
    assert states(toy, t) == {"f1": "applied", "f2": "CONFLICT", "f3": "applied", "g4": "not-applied"}


def test_unapply_feature(applied):
    toy, t = applied
    r = tool(t, toy.features_d, "unapply", "--feature", "f2")
    assert r.code == 0 and r.out == texts.changed(t, reversed=["f2", "f3"]) + "\n"
    same_tree(t, toy.expected("f1"))
    assert states(toy, t) == {"f1": "applied", "f2": "not-applied", "f3": "not-applied"}


def test_dry_run_exit_codes_equal_the_real_run(fresh):
    toy, t = fresh
    b = t / "src" / "Pure" / "b.ML"
    b.write_text(b.read_text().replace("b5\n", "edited\n"))
    assert tool(t, toy.features_d, "apply", "--dry-run").code == tool(t, toy.features_d, "apply").code == 1


def test_heap_hint_only_when_src_changed(applied):
    toy, t = applied
    (t / "etc" / "options").write_bytes(toy.expected(None)["etc/options"][0])
    r = tool(t, toy.features_d, "apply")
    assert r.code == 0 and r.out == texts.changed(t, applied=["f1"]) + "\n"


# --- multi-level files are CONFLICT (decision 6)

def test_created_then_deleted_file_matches_two_levels(toy):
    toy.feature("g1", lambda: toy.write("src/Pure/n.ML", "n\n"))
    toy.feature("g2", lambda: toy.delete("src/Pure/n.ML"))
    t = toy.tree()
    st = api.status(t, toy.features_d)
    assert sorted(st.levels["src/Pure/n.ML"].tables) == [0, 2]
    assert states(toy, t) == {"g1": "CONFLICT", "g2": "CONFLICT"}
    r = tool(t, toy.features_d, "status", "-v")
    assert "src/Pure/n.ML  levels 0, 2" in r.out
    assert tool(t, toy.features_d, "apply").code == 1


def test_repeated_context_matches_two_levels(toy):
    """The lvl/ example of plan §8: the hunk's context occurs twice in the file."""
    block = "x1\nx2\nx3\n{a}\ny1\ny2\ny3\n"
    toy.write("src/Pure/r.ML", "head\n" + block.format(a="A") + "z\nz\nz\n" + block.format(a="A"))
    toy.git("add", "-A")
    toy.git("commit", "-qm", "r")
    toy.git("tag", "-f", toy.tags[0])                                     # make it part of pristine
    toy.feature("g1", lambda: toy.edit("src/Pure/r.ML", lambda s: s.replace("x3\nA\n", "x3\nC\n", 1)))
    t = toy.tree("g1")
    assert sorted(api.status(t, toy.features_d).levels["src/Pure/r.ML"].tables) == [0, 1]
    assert states(toy, t) == {"g1": "CONFLICT"}


# --- created files and a simulated relink

def test_two_created_files_relink(toy):
    toy.feature("g1", lambda: toy.write("src/Pure/n1.ML", "n1\n"))
    toy.feature("g2", lambda: toy.write("src/Tools/n2.ML", "n2\n"))
    t = toy.tree()
    assert tool(t, toy.features_d, "apply").code == 0
    same_tree(t, toy.expected("g2"))
    # relink g1: its pre-unlink reverses g1 and above, its post-link applies the whole chain
    assert tool(t, toy.features_d, "unapply", "--feature", "g1").code == 0
    assert snapshot(t).keys() == toy.expected(None).keys()
    assert tool(t, toy.features_d, "apply").code == 0
    same_tree(t, toy.expected("g2"))
    assert tool(t, toy.features_d, "unapply").code == 0
    same_tree(t, toy.expected(None))
    assert not (t / "src" / "Tools").exists()                                # emptied directory removed


def test_created_file_with_other_content_is_conflict(toy):
    toy.feature("g1", lambda: toy.write("src/Pure/n1.ML", "n1\n"))
    t = toy.tree()
    (t / "src" / "Pure" / "n1.ML").write_text("something else\n")
    assert states(toy, t) == {"g1": "CONFLICT"}
    (t / "src" / "Pure" / "n1.ML").write_text("n1\n")                        # the feature's own content
    assert states(toy, t) == {"g1": "applied"}
    assert tool(t, toy.features_d, "unapply").code == 0 and not (t / "src" / "Pure" / "n1.ML").exists()


def test_level_tables_are_the_bytes_that_get_installed(fresh):
    """status predicts the bytes apply installs (one shared path, decision 5)."""
    toy, t = fresh
    st = api.status(t, toy.features_d)
    predicted = {k: lv.content_at(lv.candidates[-1]) for k, lv in st.levels.items()}
    tool(t, toy.features_d, "apply")
    got = snapshot(t)
    for k, content in predicted.items():
        assert got.get(k, (None,))[0] == content, k
