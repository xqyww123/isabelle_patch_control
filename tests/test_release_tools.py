"""tools/release-plan and tools/check-packages (plan decision 11): the build job's plan against a
file:// channel, its look inside the packages, and the environments of a batch; the archives are made
here."""
import functools
import http.server
import itertools
import importlib.machinery
import importlib.util
import io
import json
import threading
import tarfile
import zipfile

import pytest
import zstandard

from conftest import ROOT


def load(name: str):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(ROOT / "tools" / name))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


rp, cp = load("release-plan"), load("check-packages")
from common import entries  # noqa: E402  (tools/ is on sys.path once a tool is loaded)


def words(*tags: str) -> list[str]:
    """release-plan's words for these release tags: each feature in its own repository owner/<feature>."""
    return [f"owner/{tag.split('/')[1]}@{tag}" for tag in tags]


def tar_zst(files: dict[str, tuple[bytes, int]]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as t:
        for name, (data, mode) in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), mode
            t.addfile(info, io.BytesIO(data))
    return zstandard.ZstdCompressor().compress(raw.getvalue())


def conda(path, index: dict, files: dict[str, tuple[bytes, int]]):
    stem = path.name.removesuffix(".conda")
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("metadata.json", '{"conda_pkg_format_version": 2}')
        z.writestr(f"info-{stem}.tar.zst", tar_zst({"info/index.json": (json.dumps(index).encode(), 0o644)}))
        z.writestr(f"pkg-{stem}.tar.zst", tar_zst(files))


def record(name, version, n, isabelle_build=None):
    build = f"Isabelle2025_2_{n}" if isabelle_build else f"pyh4616a5c_{n}"
    depends = [f"isabelle ==2025.2 {isabelle_build}"] if isabelle_build else ["python >=3.12"]
    return f"{name}-{version}-{build}.conda", {"name": name, "version": version, "build": build, "build_number": n,
                                               "depends": depends, "subdir": "noarch"}


def channel(tmp_path, indexed, served=()):
    ch = tmp_path / "channel"
    (ch / "noarch").mkdir(parents=True)
    (ch / "noarch" / "repodata.json").write_text(json.dumps({"packages": {}, "packages.conda": dict(indexed)}))
    for fn, rec in served:
        conda(ch / "noarch" / fn, rec, {"x": (b"x", 0o644)})
    return f"file://{ch}"


@pytest.fixture
def over_http():
    """over_http(file URL) -> the same directory served on 127.0.0.1 by a server that, like the
    channel's Cloudflare front, refuses urllib's default User-Agent with 403."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("User-Agent", "").startswith("Python-urllib/"):
                self.send_error(403, "error code: 1010")
            else:
                super().do_GET()

        def log_message(self, *args):
            pass

    servers = []

    def serve(file_url):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=file_url.removeprefix("file://")))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield serve
    for server in servers:
        server.shutdown()
        server.server_close()


def files_of(result):
    return {p["name"]: (p["action"], p["file"]) for p in result["packages"]}


@pytest.mark.parametrize("transport", ["file", "http"])
def test_plan_against_a_channel_with_a_served_file_not_yet_indexed(tmp_path, over_http, transport):
    url = channel(tmp_path,
                  [record("isabelle-patch-control", "1.0.0", 0), record("isabelle-expose-foreign", "2025.2.1", 0, "1"),
                   record("isabelle-light-locale", "2025.2.1", 0, "1")],
                  served=[record("isabelle-light-locale", "2025.2.1", 1, "2"),        # uploaded, not indexed, pins build 2
                          record("isabelle-expose-foreign", "2025.2.1", 1, "3")])     # pins another build: skipped
    if transport == "http":                                                    # also the HTTP 404 of a file not served
        url = over_http(url)
    result = rp.plan(url, "2", "1.0.0", "pyh4616a5c", words("Isabelle2025-2/expose_foreign/1", "Isabelle2025-2/light_locale/1"))
    assert files_of(result) == {
        "isabelle-patch-control": ("reuse", "isabelle-patch-control-1.0.0-pyh4616a5c_0.conda"),
        "isabelle-expose-foreign": ("build", "isabelle-expose-foreign-2025.2.1-Isabelle2025_2_2.conda"),
        "isabelle-light-locale": ("reuse", "isabelle-light-locale-2025.2.1-Isabelle2025_2_1.conda")}
    assert [(p.get("tag"), p.get("repository"), p.get("build_number")) for p in result["packages"]] == [
        (None, None, None), ("Isabelle2025-2/expose_foreign/1", "owner/expose_foreign", 2),
        ("Isabelle2025-2/light_locale/1", "owner/light_locale", None)]
    # each package's indexed records only: the served 2 and 3 are not counted
    assert [p.get("isabelle_old_build") for p in result["packages"]] == [None, "1", "1"]


def test_an_empty_channel_and_no_other_build(tmp_path):
    empty = tmp_path / "empty"
    (empty / "noarch").mkdir(parents=True)
    result = rp.plan(f"file://{empty}", "1", "1.0.0", "pyh4616a5c", words("Isabelle2025-2/expose_foreign/1"))
    assert files_of(result) == {"isabelle-patch-control": ("build", "isabelle-patch-control-1.0.0-pyh4616a5c_0.conda"),
                                "isabelle-expose-foreign": ("build", "isabelle-expose-foreign-2025.2.1-Isabelle2025_2_0.conda")}
    assert result["packages"][1]["isabelle_old_build"] == ""


def old_builds(result):
    return {p["name"]: p["isabelle_old_build"] for p in result["packages"] if "tag" in p}


def test_each_package_has_its_own_old_build(tmp_path):
    """tools/accept's scenario (h) installs one package of the batch at that build, so that package's
    own records count, of any version; not the others' or this batch's build."""
    other_line = ("isabelle-light-locale-2026.1.1-Isabelle2026_1_0.conda",
                  {"name": "isabelle-light-locale", "version": "2026.1.1", "build": "Isabelle2026_1_0", "build_number": 0,
                   "depends": ["isabelle ==2026.1 13"], "subdir": "noarch"})
    url = channel(tmp_path, [record("isabelle-light-locale", "2025.2.1", 0, "9"), record("isabelle-light-locale", "2025.2.1", 1, "10"),
                             record("isabelle-light-locale", "2025.2.2", 2, "11"),      # another version of the top: counts
                             record("isabelle-light-locale", "2025.2.1", 3, "12"),      # this batch's own build: not an old one
                             record("isabelle-expose-foreign", "2025.2.1", 4, "14"),    # a lower feature: no state of (h)
                             other_line])                                        # another release line's pin
    result = rp.plan(url, "12", "1.0.0", "p", words("Isabelle2025-2/expose_foreign/1", "Isabelle2025-2/light_locale/1"))
    assert old_builds(result) == {"isabelle-expose-foreign": "14", "isabelle-light-locale": "11"}
    assert old_builds(rp.plan(url, "14", "1.0.0", "p", words("Isabelle2025-2/expose_foreign/1"))) == {"isabelle-expose-foreign": ""}


def test_the_isabelle_version_is_the_release_line_of_the_batch(tmp_path):
    """2025.2's build 0 is not pristine (it carries expose_foreign); 2026 has no such build."""
    url = channel(tmp_path, [])
    old = rp.plan(url, "1", "1.0.0", "p", words("Isabelle2025-2/expose_foreign/1"))
    assert (old["isabelle_version"], old["isabelle_non_pristine_build"]) == ("2025.2", "0")
    new = rp.plan(url, "0", "1.0.0", "p", words("Isabelle2026/expose_foreign/1", "Isabelle2026/light_locale/1"))
    assert (new["isabelle_version"], new["isabelle_non_pristine_build"]) == ("2026", "")
    assert files_of(new)["isabelle-light-locale"] == ("build", "isabelle-light-locale-2026.0.1-Isabelle2026_0.conda")


def isabelle(version, build, subdir):
    return f"isabelle-{version}-{build}.conda", {"name": "isabelle", "version": version, "build": build,
                                                 "build_number": int(build), "depends": ["python"], "subdir": subdir}


@pytest.mark.parametrize("transport", ["file", "http"])
def test_a_rehearsal_is_refused_only_for_an_isabelle_build_the_channel_serves(tmp_path, over_http, transport, monkeypatch):
    """One platform's repodata.json serves 2025.2-0; the other four platforms have none, which is no error."""
    url = channel(tmp_path, [])
    arm = tmp_path / "channel" / "linux-aarch64"
    arm.mkdir()
    (arm / "repodata.json").write_text(json.dumps({"packages": {}, "packages.conda": dict([isabelle("2025.2", "0", "linux-aarch64")])}))
    if transport == "http":
        url = over_http(url)
    monkeypatch.setattr("sys.argv", ["release-plan", "--channel", url, "--isabelle-build", "0", "--tool-version", "1.0.0",
                                     "--tool-prefix", "p", "--rehearsal", *words("Isabelle2025-2/light_locale/1")])
    with pytest.raises(rp.Refused, match=r"serves isabelle 2025\.2 0 \(linux-aarch64\).*conda cannot tell the two apart"):
        rp.cli()                                                                                # the workflow's path
    assert rp.plan(url, "1", "1.0.0", "p", words("Isabelle2025-2/light_locale/1"), rehearsal=True)
    assert rp.plan(url, "0", "1.0.0", "p", words("Isabelle2026/light_locale/1"), rehearsal=True)     # a new line's first build
    assert rp.plan(url, "0", "1.0.0", "p", words("Isabelle2025-2/light_locale/1"))                   # not a rehearsal


@pytest.mark.parametrize("given, says", [(["Isabelle2025-2/light_locale/1"], "is not <GitHub repository>@<release tag>"),
                                        (["owner/light_locale@light_locale/1"], "is not a release tag"),
                                        (words("Isabelle2025-2/light_locale/0"), "is not a release tag"),
                                        (words("Isabelle2025-2/a/1", "Isabelle2025-2/a/2"), "names a feature twice"),
                                        (words("Isabelle2025-2/a/1", "Isabelle2026/b/1"),
                                         "span the release lines Isabelle2025-2 and Isabelle2026: one batch is one isabelle version")])
def test_plan_refusals(tmp_path, given, says):
    with pytest.raises(rp.Refused, match=says):
        rp.plan(channel(tmp_path, []), "1", "1.0.0", "p", given)


NAME = "isabelle-light-locale"
LF = b"#!/bin/bash\nexit 0\n"
CRLF = b"@echo off\r\nexit /b 0\r\n"


def feature_files(**changes) -> dict[str, tuple[bytes, int]]:
    files = {f"bin/.{NAME}-post-link.sh": (b'#!/bin/bash\n"$PREFIX/isa/bin/isabelle" components -u "$PREFIX/share/' + NAME.encode() + b'"\nexit 0\n', 0o755),
             f"bin/.{NAME}-pre-unlink.sh": (LF, 0o755),
             f"Scripts/.{NAME}-post-link.bat": (CRLF, 0o644), f"Scripts/.{NAME}-pre-unlink.bat": (CRLF, 0o644),
             "share/isabelle_patch_control/features.d/light_locale/provenance.txt": (b"release_tag: x\n", 0o644),
             "share/isabelle_patch_control/features.d/light_locale/src-Pure-a.ML.patch": (b"diff\n", 0o644),
             f"share/doc/{NAME}/README.md": (b"# readme\n", 0o644),
             f"share/{NAME}/ROOT": (b"session X\n", 0o644)}
    for rel, value in changes.items():
        rel = rel.replace("__", "/").replace("NAME", NAME)
        if value is None:
            files.pop(rel)
        else:
            files[rel] = value
    return files


def package(tmp_path, files, subdir="noarch", name=NAME):
    p = tmp_path / subdir / f"{name}-1-Isabelle2025_2_0.conda"
    conda(p, {"name": name, "version": "1", "subdir": subdir}, files)
    return p


def problems_in(path):
    return cp.problems_of(path, *cp.conda_archive(path.read_bytes()))


def test_a_good_feature_package(tmp_path):
    assert problems_in(package(tmp_path, feature_files())) == []


@pytest.mark.parametrize("change, says", [
    ({"Scripts__.NAME-pre-unlink.bat": None}, "missing Scripts/.isabelle-light-locale-pre-unlink.bat"),
    ({"Scripts__.NAME-post-link.bat": (b"@echo off\nexit /b 0\r\n", 0o644)}, "is not CRLF throughout"),
    ({"bin__.NAME-pre-unlink.sh": (b"#!/bin/bash\r\nexit 0\n", 0o755)}, "has a carriage return"),
    ({"bin__.NAME-pre-unlink.sh": (LF, 0o644)}, "is not executable"),
    ({"bin__.NAME-post-link.sh": (LF, 0o755)}, "does not register share/isabelle-light-locale"),
    ({"share__isabelle_patch_control__features.d__light_locale__src-Pure-a.ML.patch": None}, "lacks provenance.txt or a patch file"),
    ({"share__doc__NAME__README.md": None}, "missing share/doc/isabelle-light-locale/README.md"),
])
def test_what_check_packages_refuses(tmp_path, change, says):
    problems = problems_in(package(tmp_path, feature_files(**change)))
    assert len(problems) == 1 and says in problems[0], problems


def test_noarch_only_and_the_tool(tmp_path):
    assert any("not a noarch package" in p for p in problems_in(package(tmp_path, feature_files(), subdir="linux-64")))
    tool = package(tmp_path, {f: (b"x", 0o644) for f in cp.FRAGMENTS[:3]}, name="isabelle-patch-control")
    assert problems_in(tool) == ["missing site-packages/isabelle_patch_control/hooks/pre-unlink.bat"]
    assert problems_in(package(tmp_path, {}, name="isabelle")) == ["isabelle is neither the tool nor a feature package"]


R = "Isabelle2025-2"
PRISTINE = f"{R}/pristine/89701cf1768e"
PUBLIC = "conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle"


def feature_package(d, tag, base):
    """A feature package of `tag` built on `base`, as check-packages reads it."""
    feature = tag.split("/")[1]
    name, version = rp.package_name(feature), rp.package_version(tag)
    fd = f"share/isabelle_patch_control/features.d/{feature}"
    files = {f"bin/.{name}-post-link.sh": (LF, 0o755), f"bin/.{name}-pre-unlink.sh": (LF, 0o755),
             f"Scripts/.{name}-post-link.bat": (CRLF, 0o644), f"Scripts/.{name}-pre-unlink.bat": (CRLF, 0o644),
             f"{fd}/provenance.txt": (f"release_tag: {tag}\nbase_tag: {base}\n".encode(), 0o644),
             f"{fd}/src-Pure-a.ML.patch": (b"diff\n", 0o644),
             f"share/doc/{name}/README.md": (f"# {feature}\n\n{PUBLIC} {name}\n".encode(), 0o644)}
    p = d / "noarch" / f"{name}-{version}-Isabelle2025_2_0.conda"
    conda(p, {"name": name, "version": version, "subdir": "noarch"}, files)
    return p


def tool_package(d):
    return package(d, {f: (b"x", 0o644) for f in cp.FRAGMENTS}, name="isabelle-patch-control")


def environments(tmp_path, links):
    """{entry: (its batch_release_tags, its isabelle_old_build)} of a batch: the tool and a feature package
    for each (release tag, base tag), each with its own old build in the plan."""
    paths = [tool_package(tmp_path)] + [feature_package(tmp_path, tag, base) for tag, base in links]
    plan = {"packages": [{"file": paths[0].name}] + [{"file": p.name, "tag": tag, "isabelle_old_build": str(i)}
                                                      for i, (p, (tag, _)) in enumerate(zip(paths[1:], links), 1)]}
    envs = cp.environments({p: cp.conda_archive(p.read_bytes()) for p in paths}, plan)
    assert all(e["install"] == f"{PUBLIC} {e['package']}" for e in envs)
    return {e["release_tag"]: (e["batch_release_tags"], e["isabelle_old_build"]) for e in envs}


def test_the_environments_of_a_chain_and_of_a_tree(tmp_path):
    """Each entry carries the release tags of its environment and its own package's old build."""
    a, b, c, d = (f"{R}/{f}/1" for f in "abcd")
    assert environments(tmp_path / "chain", [(a, PRISTINE), (b, a), (c, b)]) == {c: ([a, b, c], "3")}
    assert environments(tmp_path / "tree", [(a, PRISTINE), (b, a), (c, b), (d, a)]) == {c: ([a, b, c], "3"), d: ([a, d], "4")}


def test_the_environments_do_not_depend_on_the_order():
    """common.entries on a chain, a tree, a forest, one feature and a deeper tree, under every order."""
    shapes = [{"a": [], "b": ["a"], "c": ["b"]}, {"a": [], "b": ["a"], "c": ["a"]}, {"a": [], "b": [], "c": ["b"]},
              {"a": []}, {"a": [], "b": ["a"], "c": ["b"], "d": ["b"], "e": ["a"]},
              {"b": ["x"]}]                                                       # x: from a channel
    expected = [{"c": ["a", "b", "c"]}, {"b": ["a", "b"], "c": ["a", "c"]}, {"a": ["a"], "c": ["b", "c"]},
                {"a": ["a"]}, {"c": ["a", "b", "c"], "d": ["a", "b", "d"], "e": ["a", "e"]}, {"b": ["b"]}]
    for shape, want in zip(shapes, expected):
        for order in itertools.permutations(shape):
            got = entries({tag: shape[tag] for tag in order})
            assert json.dumps(got) == json.dumps(want), (order, got)
