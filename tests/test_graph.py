"""Stage 2: features built on several features (stage 2 design, sections 2-6).  g1 and g2 are built
on Isabelle itself and change a.ML far apart; g3 is built on both; the levels are sets."""
import fcntl
import shutil

import pytest

from conftest import same_tree, snapshot, tool
from isabelle_patch_control import api, engine, features, texts
from test_hooks import Prefix, said


def edit(toy, rel, old, new):
    return lambda: toy.edit(rel, lambda s: s.replace(old, new))


@pytest.fixture
def graph(toy):
    toy.feature("g1", lambda: (edit(toy, "src/Pure/a.ML", "a2\n", "a2\nG1\n")(),
                               edit(toy, "etc/options", "true\n", "true\noption g1 : bool = true\n")()), bases=())
    toy.feature("g2", edit(toy, "src/Pure/a.ML", "a11\n", "A11\n"), bases=())
    toy.feature("g3", edit(toy, "src/Pure/a.ML", "a6\n", "a6\nG3\n"), bases=("g1", "g2"))
    return toy


def states(toy, t, features_d=None) -> dict[str, str]:
    st = api.status(t, features_d or toy.features_d)
    return {fd.name: s.state for fd, s in zip(st.installed, st.features)}


def without(toy, *names):
    """features.d without the named features (moved next to it)."""
    for n in names:
        (toy.features_d / n).rename(toy.root / f"aside-{n}")


def back(toy, *names):
    for n in names:
        (toy.root / f"aside-{n}").rename(toy.features_d / n)


def test_the_environments_order_is_by_depth_then_package_name(graph):
    graph.feature("a0", edit(graph, "src/Pure/b.ML", "b2\n", "B2\n"), bases=("g1",))   # depth 2: after g2 despite its name
    installed = features.link(features.Tree.read(graph.tree()), features.read_feature_dirs(graph.features_d))
    assert [fd.name for fd in installed] == ["g1", "g2", "a0", "g3"]
    assert features.below(installed) == {1: set(), 2: set(), 3: {1}, 4: {1, 2}}


def test_two_features_on_one_base_work_together_in_either_order(graph):
    without(graph, "g3")
    trees = []
    for first, second in (("g1", "g2"), ("g2", "g1")):
        t = graph.tree()
        without(graph, second)
        assert tool(t, graph.features_d, "apply").code == 0
        back(graph, second)
        assert tool(t, graph.features_d, "apply").code == 0
        assert states(graph, t) == {"g1": "applied", "g2": "applied"}
        trees.append(snapshot(t))
    assert trees[0] == trees[1]
    a = trees[0]["src/Pure/a.ML"][0].decode()
    assert "a2\nG1\na3\n" in a and "A11\n" in a
    r = tool(t, graph.features_d, "status", "-v")
    assert "      src/Pure/a.ML  level 1+2 (g1, g2)\n" in r.out


def test_a_feature_on_two_bases(graph):
    t = graph.tree()
    r = tool(t, graph.features_d, "apply")
    assert r.code == 0 and "(applied: g1, g2, g3)" in r.out
    same_tree(t, graph.expected("g3"))                      # g3's release commit: git's merge of g1 and g2, then g3
    assert tool(t, graph.features_d, "unapply").code == 0
    same_tree(t, graph.expected(None))


def test_unapply_feature_leaves_an_unrelated_feature_applied(graph):
    t = graph.tree()
    assert tool(t, graph.features_d, "apply").code == 0
    r = tool(t, graph.features_d, "unapply", "--feature", "g1")
    assert r.code == 0 and "(undone: g1, g3)" in r.out
    assert states(graph, t) == {"g1": "not-applied", "g2": "applied", "g3": "not-applied"}
    assert (t / "src/Pure/a.ML").read_bytes() == graph.expected("g2")["src/Pure/a.ML"][0]


def test_apply_with_a_conflict_still_applies_the_unrelated_feature(graph):
    t = graph.tree()
    (t / "etc/options").write_text("edited by hand\n")       # a file only g1 changes
    r = tool(t, graph.features_d, "apply")
    assert r.code == 1
    assert states(graph, t) == {"g1": "CONFLICT", "g2": "applied", "g3": "not-applied"}


def test_a_hand_edit_next_to_an_unrelated_feature_is_conflict_not_a_refusal(graph):
    without(graph, "g3")
    t = graph.tree()
    assert tool(t, graph.features_d, "apply").code == 0
    p = t / "src/Pure/a.ML"
    p.write_text(p.read_text().replace("a1\n", "edited\n"))
    r = tool(t, graph.features_d, "status")
    assert r.code == 1 and states(graph, t)["g1"] == "CONFLICT"


@pytest.fixture
def too_close(toy):
    """h1 and h2, both on Isabelle, insert a line after the same line of a.ML."""
    toy.feature("h1", edit(toy, "src/Pure/a.ML", "a5\n", "a5\nH1\n"), bases=())
    toy.feature("h2", edit(toy, "src/Pure/a.ML", "a5\n", "a5\nH2\n"), bases=())
    return toy


def test_changes_too_close_are_refused(too_close):
    t = too_close.tree()
    before = snapshot(t)
    refusal = texts.PREFIX + texts.cannot_combine("isabelle-h1 2025.2.1", "isabelle-h2 2025.2.1", "src/Pure/a.ML") + "\n"
    for cmd in ("status", "apply", "unapply"):
        r = tool(t, too_close.features_d, cmd)
        assert (r.code, r.out, r.err) == (3, "", refusal)
    assert snapshot(t) == before


def test_the_same_change_twice_is_refused_also_when_one_is_applied(toy):
    for name in ("k1", "k2"):
        toy.feature(name, edit(toy, "src/Pure/a.ML", "a5\n", "a5\nK\n"), bases=())
    t = toy.tree()
    without(toy, "k2")
    assert tool(t, toy.features_d, "apply").code == 0
    back(toy, "k2")                                         # two levels pass now: {k1} and {k2}
    r = tool(t, toy.features_d, "status")
    assert r.code == 3 and texts.cannot_combine("isabelle-k1 2025.2.1", "isabelle-k2 2025.2.1", "src/Pure/a.ML") in r.err


def test_pre_unlink_leaves_an_unrelated_feature_applied(graph, tmp_path):
    prefix = Prefix(graph, tmp_path / "env")
    prefix.hook("post-link")
    text = prefix.hook("pre-unlink", "g1")
    assert text == said(texts.undone("g1", prefix.tree, ["g1", "g3"]))
    assert states(graph, prefix.tree, prefix.features_d) == {"g1": "not-applied", "g2": "applied", "g3": "not-applied"}


def test_pre_unlink_after_a_lock_timeout_names_every_top_above_the_feature(graph, tmp_path, monkeypatch):
    graph.feature("g4", edit(graph, "src/Pure/b.ML", "b2\n", "B2\n"), bases=("g1",))
    graph.feature("g5", edit(graph, "src/Pure/b.ML", "b10\n", "B10\n"), bases=("g4",))   # g4 is above g1 but not a top
    prefix = Prefix(graph, tmp_path / "env")
    prefix.hook("post-link")
    monkeypatch.setattr(engine, "LOCK_TIMEOUT", 0.2)
    with open(prefix.tree / engine.LOCK_FILE, "rb") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            text = prefix.hook("pre-unlink", "g1")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    assert (f"  conda install -p {prefix.path} {texts.CHANNELS} isabelle-g3=2025.2.1 isabelle-g5=2025.2.1\n"
            f"  conda remove -p {prefix.path} isabelle-g3 isabelle-g5\n") in text


def test_post_link_conflict_diagnostic_from_the_last_feature_above_the_stopped_one(graph, tmp_path):
    graph.feature("g4", edit(graph, "src/Pure/b.ML", "b2\n", "B2\n"), bases=("g2",))   # last in the order, not above g1
    prefix = Prefix(graph, tmp_path / "env")
    (prefix.tree / "etc/options").write_text("edited by hand\n")
    assert "This usually means" not in prefix.hook("post-link", pkg="isabelle-g4")
    assert "This usually means" in prefix.hook("post-link", pkg="isabelle-g3")


def test_a_feature_with_two_bases_needs_both(graph):
    shutil.rmtree(graph.features_d / "g2")
    r = tool(graph.tree(), graph.features_d, "status")
    assert r.code == 3 and "isabelle-g3 2025.2.1 needs isabelle-g2 2025.2.1, which is not installed." in r.err


def test_the_byte_check_reads_a_level_with_two_tops_from_the_patch_above_both(graph, tmp_path):
    from test_check_bytes import cb, unpacked
    isabelle, packages = unpacked(graph, tmp_path / "pkgs")
    t = graph.tree()
    api.apply(t, graph.features_d)
    assert cb.check(t, isabelle, packages, None)[:2] == ([], [])
    api.unapply(t, graph.features_d, feature="g3")
    assert cb.check(t, isabelle, packages, ["g1", "g2"])[:2] == ([], [])        # g3's pre-image
    alone = [p for p in packages if "-g3-" not in p.name]
    assert cb.check(t, isabelle, alone, ["g1", "g2"])[:2] == ([], ["src/Pure/a.ML"])
    (t / "src/Pure/a.ML").write_text("x\n")
    assert cb.check(t, isabelle, packages, ["g1", "g2"])[0][0].startswith("src/Pure/a.ML: blob ")
