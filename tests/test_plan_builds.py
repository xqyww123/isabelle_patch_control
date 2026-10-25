"""tools/common.py: plan_builds (plan decision 10): which packages of a batch are reused from the
channel and which are built with which build number."""
import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))
from common import Wanted, plan_builds  # noqa: E402

TOOL = "isabelle-patch-control"


def feature(name, version, isabelle_build) -> Wanted:
    return Wanted(name, version, lambda n: f"{name}-{version}-Isabelle2025_2_{n}.conda",
                  lambda rec: f"isabelle 2025.2 {isabelle_build}" in rec["depends"])


def tool(version) -> Wanted:
    return Wanted(TOOL, version, lambda n: f"{TOOL}-{version}-py_{n}.conda", lambda rec: True)


def record(name, version, n, isabelle_build=None):
    depends = [f"isabelle 2025.2 {isabelle_build}", f"{TOOL} >=1.0,<2"] if isabelle_build else ["python >=3.12", "git >=2.43"]
    build = f"Isabelle2025_2_{n}" if isabelle_build else f"py_{n}"
    return f"{name}-{version}-{build}.conda", {"name": name, "version": version, "build": build,
                                              "build_number": n, "depends": depends}


def repodata(*records):
    return {"packages": {}, "packages.conda": dict(records)}


def nothing_served(filename):
    return None


def test_hol_side_rerelease_of_one_feature():
    """light 2 is new; expose_foreign 1 and the tool are on the channel pinned to this build."""
    data = repodata(record("isabelle-expose-foreign", "1", 0, "1"), record("isabelle-light-locale", "1", 0, "1"),
                    record(TOOL, "1.0.0", 0))
    plan = plan_builds(data, [tool("1.0.0"), feature("isabelle-expose-foreign", "1", "1"), feature("isabelle-light-locale", "2", "1")],
                       nothing_served)
    assert plan == {TOOL: ("reuse", f"{TOOL}-1.0.0-py_0.conda"),
                    "isabelle-expose-foreign": ("reuse", "isabelle-expose-foreign-1-Isabelle2025_2_0.conda"),
                    "isabelle-light-locale": ("build", 0)}


def test_new_isabelle_build_rebuilds_every_feature_but_not_the_tool():
    data = repodata(record("isabelle-expose-foreign", "1", 0, "1"), record("isabelle-light-locale", "1", 0, "1"),
                    record("isabelle-light-locale", "1", 1, "1"), record(TOOL, "1.0.0", 0))
    plan = plan_builds(data, [tool("1.0.0"), feature("isabelle-expose-foreign", "1", "2"), feature("isabelle-light-locale", "1", "2")],
                       nothing_served)
    assert plan == {TOOL: ("reuse", f"{TOOL}-1.0.0-py_0.conda"),
                    "isabelle-expose-foreign": ("build", 1), "isabelle-light-locale": ("build", 2)}


def test_repeated_dispatch_reuses_everything():
    data = repodata(record("isabelle-expose-foreign", "1", 0, "1"), record("isabelle-expose-foreign", "1", 1, "2"),
                    record("isabelle-light-locale", "1", 2, "2"), record(TOOL, "1.0.0", 0))
    plan = plan_builds(data, [tool("1.0.0"), feature("isabelle-expose-foreign", "1", "2"), feature("isabelle-light-locale", "1", "2")],
                       nothing_served)
    assert plan == {TOOL: ("reuse", f"{TOOL}-1.0.0-py_0.conda"),
                    "isabelle-expose-foreign": ("reuse", "isabelle-expose-foreign-1-Isabelle2025_2_1.conda"),
                    "isabelle-light-locale": ("reuse", "isabelle-light-locale-1-Isabelle2025_2_2.conda")}


def test_files_uploaded_but_not_indexed():
    """Three shapes: a tool package of the same version (reuse), a feature file pinning this
    build (reuse), a feature file pinning another build (skipped: the next number is used)."""
    data = repodata(record("isabelle-expose-foreign", "1", 0, "1"), record("isabelle-light-locale", "1", 0, "1"))
    served = dict([record(TOOL, "1.0.0", 0), record("isabelle-expose-foreign", "1", 1, "2"),
                   record("isabelle-light-locale", "1", 1, "3")])
    probed = []

    def fetch(filename):
        probed.append(filename)
        return served.get(filename)

    plan = plan_builds(data, [tool("1.0.0"), feature("isabelle-expose-foreign", "1", "2"), feature("isabelle-light-locale", "1", "2")],
                       fetch)
    assert plan == {TOOL: ("reuse", f"{TOOL}-1.0.0-py_0.conda"),
                    "isabelle-expose-foreign": ("reuse", "isabelle-expose-foreign-1-Isabelle2025_2_1.conda"),
                    "isabelle-light-locale": ("build", 2)}
    # probing starts right above the highest indexed build and stops at the first file not served
    assert probed == [f"{TOOL}-1.0.0-py_0.conda", f"{TOOL}-1.0.0-py_1.conda",
                      "isabelle-expose-foreign-1-Isabelle2025_2_1.conda", "isabelle-expose-foreign-1-Isabelle2025_2_2.conda",
                      "isabelle-light-locale-1-Isabelle2025_2_1.conda", "isabelle-light-locale-1-Isabelle2025_2_2.conda"]


def test_empty_channel_builds_zero():
    plan = plan_builds({}, [tool("1.0.0"), feature("isabelle-expose-foreign", "1", "1")], nothing_served)
    assert plan == {TOOL: ("build", 0), "isabelle-expose-foreign": ("build", 0)}
