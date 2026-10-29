"""tools/release-plan and tools/check-packages (plan decision 11): the build job's plan against a
file:// channel, and its look inside the packages; the archives are made here."""
import functools
import http.server
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
                  [record("isabelle-patch-control", "1.0.0", 0), record("isabelle-expose-foreign", "1", 0, "1"),
                   record("isabelle-light-locale", "1", 0, "1")],
                  served=[record("isabelle-light-locale", "1", 1, "2"),        # uploaded, not indexed, pins build 2
                          record("isabelle-expose-foreign", "1", 1, "3")])     # pins another build: skipped
    if transport == "http":                                                    # also the HTTP 404 of a file not served
        url = over_http(url)
    result = rp.plan(url, "2", "1.0.0", "pyh4616a5c", ["Isabelle2025-2/expose_foreign/1", "Isabelle2025-2/light_locale/1"])
    assert files_of(result) == {
        "isabelle-patch-control": ("reuse", "isabelle-patch-control-1.0.0-pyh4616a5c_0.conda"),
        "isabelle-expose-foreign": ("build", "isabelle-expose-foreign-1-Isabelle2025_2_2.conda"),
        "isabelle-light-locale": ("reuse", "isabelle-light-locale-1-Isabelle2025_2_1.conda")}
    assert [(p.get("tag"), p.get("feature"), p.get("build_number")) for p in result["packages"]] == [
        (None, None, None), ("Isabelle2025-2/expose_foreign/1", "expose_foreign", 2), ("Isabelle2025-2/light_locale/1", "light_locale", None)]
    assert result["isabelle_old_build"] == "1"             # the top's indexed records only; the served 2 is not counted


def test_an_empty_channel_and_no_other_build(tmp_path):
    empty = tmp_path / "empty"
    (empty / "noarch").mkdir(parents=True)
    result = rp.plan(f"file://{empty}", "1", "1.0.0", "pyh4616a5c", ["Isabelle2025-2/expose_foreign/1"])
    assert files_of(result) == {"isabelle-patch-control": ("build", "isabelle-patch-control-1.0.0-pyh4616a5c_0.conda"),
                                "isabelle-expose-foreign": ("build", "isabelle-expose-foreign-1-Isabelle2025_2_0.conda")}
    assert result["isabelle_old_build"] == ""


def test_the_old_build_is_the_highest_other_one_the_chain_top_pins(tmp_path):
    """§6 (h) installs the chain top at that build, so only the top's records count, of any version."""
    other_line = ("isabelle-light-locale-1-Isabelle2026_1_0.conda",
                  {"name": "isabelle-light-locale", "version": "1", "build": "Isabelle2026_1_0", "build_number": 0,
                   "depends": ["isabelle ==2026.1 13"], "subdir": "noarch"})
    url = channel(tmp_path, [record("isabelle-light-locale", "1", 0, "9"), record("isabelle-light-locale", "1", 1, "10"),
                             record("isabelle-light-locale", "2", 2, "11"),      # another version of the top: counts
                             record("isabelle-light-locale", "1", 3, "12"),      # this batch's own build: not an old one
                             record("isabelle-expose-foreign", "1", 4, "14"),    # a lower feature: no state of (h)
                             other_line])                                        # another release line's pin
    result = rp.plan(url, "12", "1.0.0", "p", ["Isabelle2025-2/expose_foreign/1", "Isabelle2025-2/light_locale/1"])
    assert result["isabelle_old_build"] == "11"
    lower_only = rp.plan(url, "14", "1.0.0", "p", ["Isabelle2025-2/expose_foreign/1"])
    assert lower_only["isabelle_old_build"] == ""


@pytest.mark.parametrize("tags, says", [(["light_locale/1"], "is not a release tag"),
                                        (["Isabelle2025-2/light_locale/0"], "is not a release tag"),
                                        (["Isabelle2025-2/a/1", "Isabelle2025-2/a/2"], "names a feature twice")])
def test_plan_refusals(tmp_path, tags, says):
    with pytest.raises(rp.Refused, match=says):
        rp.plan(channel(tmp_path, []), "1", "1.0.0", "p", tags)


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


def chained(tmp_path, *links):
    """{path: archive} of feature packages whose provenance links (release tag, base tag)."""
    out = {}
    for tag, base in links:
        feature = tag.split("/")[1]
        name = f"isabelle-{feature.replace('_', '-')}"
        p = tmp_path / "noarch" / f"{name}-1-Isabelle2025_2_0.conda"
        conda(p, {"name": name, "version": "1", "subdir": "noarch"},
              {f"share/isabelle_patch_control/features.d/{feature}/provenance.txt": (f"release_tag: {tag}\nbase_tag: {base}\n".encode(), 0o644)})
        out[p] = cp.conda_archive(p.read_bytes())
    return out


R = "Isabelle2025-2"
CHAIN = [(f"{R}/a/1", f"{R}/pristine/89701cf1768e"), (f"{R}/b/2", f"{R}/a/1"), (f"{R}/c/1", f"{R}/b/2")]


def test_the_batch_is_the_whole_chain_bottom_first(tmp_path):
    archives = chained(tmp_path, *CHAIN)
    assert cp.chain_problems(archives, [t for t, _ in CHAIN]) == []
    assert cp.chain_problems(archives, [f"{R}/b/2", f"{R}/a/1", f"{R}/c/1"]) == [
        f"{R}/b/2 is the bottom of the batch but stands on {R}/a/1: the batch must be the whole chain",
        f"{R}/a/1 stands on {R}/pristine/89701cf1768e, not on {R}/b/2: list the whole chain, bottom first",
        f"{R}/c/1 stands on {R}/b/2, not on {R}/a/1: list the whole chain, bottom first"]
    top_only = chained(tmp_path / "top", CHAIN[2])
    assert cp.chain_problems(top_only, [f"{R}/c/1"]) == [
        f"{R}/c/1 is the bottom of the batch but stands on {R}/b/2: the batch must be the whole chain"]
    assert cp.chain_problems(archives, [f"{R}/a/1", f"{R}/b/2"]) == [
        f"the feature packages are {R}/a/1 {R}/b/2 {R}/c/1, the batch names {R}/a/1 {R}/b/2"]
