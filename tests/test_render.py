"""tools/render-feature-recipe (plan decision 10): the recipe of a feature package, its files and its
hooks, computed from the package directory at its release tag."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import GIT_FLAGS, ROOT, git_env

sys.path.insert(0, str(ROOT / "tools"))
from common import Wanted, isabelle_pin  # noqa: E402

RENDER = ROOT / "tools" / "render-feature-recipe"
HOOKS = ROOT / "isabelle_patch_control" / "hooks"
COMMON = (ROOT / "common-readme.md").read_bytes()
R = "Isabelle2025-2"
PATCH = b"diff --git a/src/Pure/a.ML b/src/Pure/a.ML\n--- a/src/Pure/a.ML\n+++ b/src/Pure/a.ML\n@@ -1 +1 @@\n-a\n+b\n"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *GIT_FLAGS, *args], cwd=cwd, env=git_env(), check=True,
                          capture_output=True, text=True).stdout


def provenance(feature: str, version: str, base_tag: str) -> str:
    return (f"feature: {R}/{feature}\nrelease_tag: {R}/{feature}/{version}\ncommit: 0\nbase_tag: {base_tag}\n"
            f"base_commit: 0\nbase_package_version: x\nbase_pin: x\nbuild_string_prefix: Isabelle2025_2\n"
            f"tree_hash: 0\ntree_hash_excludes: etc/ISABELLE_ID\n")


def package(repo: Path, subdir: str = ".", feature: str = "light_locale", version: str = "2",
            base_tag: str = f"{R}/future_assign_interrupt/1", components: dict | None = None, tag: bool = True) -> Path:
    """A feature repository with one package directory, committed and tagged like make-patches leaves it."""
    pkg = repo / subdir
    (pkg / "patches" / R).mkdir(parents=True)
    (pkg / "README.md").write_text(f"# {feature}\n\nThe feature's own README.\n")
    (pkg / "patches" / R / "provenance.txt").write_text(provenance(feature, version, base_tag))
    (pkg / "patches" / R / "src-Pure-a.ML.patch").write_bytes(PATCH)
    if components is not None:
        (pkg / "tools").mkdir()
        (pkg / "tools" / "component_files.txt").write_text("# shipped under share/<package>/\n" + "".join(f"{c}\n" for c in components))
        for rel, data in components.items():
            (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
            (pkg / rel).write_text(data)
    if not (repo / ".git").exists():
        git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"{feature} release {version}")
    if tag:
        git(repo, "tag", "-a", "-m", "release", f"{R}/{feature}/{version}")
    return pkg


def render(pkg: Path, out: Path, isabelle_build: str = "1", n: int = 3, tools: Path = ROOT / "tools"):
    old = os.umask(0o002)                          # the package's modes must not follow the builder's umask
    try:
        return subprocess.run([sys.executable, tools / "render-feature-recipe", pkg, "--isabelle-build", isabelle_build,
                               "--build-number", str(n), "-o", out], capture_output=True, text=True)
    finally:
        os.umask(old)


def run_deps(recipe: str) -> list[str]:
    block = recipe.split("  run:\n", 1)[1].split("about:", 1)[0]
    return [json.loads(line.strip()[2:]) for line in block.splitlines() if line.strip().startswith("- ")]


def files_of(out: Path) -> dict[str, tuple[bytes, int]]:
    return {p.relative_to(out / "files").as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in sorted((out / "files").rglob("*")) if p.is_file()}


def test_recipe_pins_files_and_readme(tmp_path):
    pkg = package(tmp_path / "repo")
    out = tmp_path / "out"
    r = render(pkg, out)
    assert r.returncode == 0, r.stderr
    assert "noarch/isabelle-light-locale-2-Isabelle2025_2_3.conda" in r.stdout
    recipe = (out / "recipe.yaml").read_text()
    for line in ('name: "isabelle-light-locale"', 'version: "2"', "number: 3", 'string: "Isabelle2025_2_3"', "noarch: generic"):
        assert line in recipe
    deps = run_deps(recipe)
    assert deps == ["isabelle-patch-control >=1.0,<2", "isabelle ==2025.2 1",
                    "isabelle-future-assign-interrupt ==1 Isabelle2025_2_*"]
    # the recipe's pin is the one plan_builds looks for: a package built from it is what this batch wants
    wanted = Wanted("isabelle-light-locale", "2", "Isabelle2025_2", isabelle_pin("Isabelle2025_2", "1"))
    assert wanted.accepts({"depends": deps})
    assert not Wanted("isabelle-light-locale", "2", "Isabelle2025_2", isabelle_pin("Isabelle2025_2", "2")).accepts({"depends": deps})

    files = files_of(out)
    fd = "share/isabelle_patch_control/features.d/light_locale"
    p = "isabelle-light-locale"
    assert set(files) == {f"{fd}/provenance.txt", f"{fd}/src-Pure-a.ML.patch", f"share/doc/{p}/README.md",
                          f"bin/.{p}-post-link.sh", f"bin/.{p}-pre-unlink.sh",
                          f"Scripts/.{p}-post-link.bat", f"Scripts/.{p}-pre-unlink.bat"}
    assert files[f"{fd}/src-Pure-a.ML.patch"][0] == PATCH
    assert files[f"{fd}/provenance.txt"][0] == (pkg / "patches" / R / "provenance.txt").read_bytes()
    assert files[f"share/doc/{p}/README.md"][0] == COMMON + b"\n" + (pkg / "README.md").read_bytes()
    assert {rel: mode for rel, (_, mode) in files.items()} == {
        rel: 0o755 if rel.endswith(".sh") else 0o644 for rel in files}


def test_hooks_are_the_fragments_verbatim(tmp_path):
    pkg = package(tmp_path / "repo")
    out = tmp_path / "out"
    assert render(pkg, out).returncode == 0
    files = files_of(out)
    p = "isabelle-light-locale"
    fill = lambda b: b.replace(b"<feature>", b"light_locale").replace(b"<package>", p.encode()).replace(b"<version>", b"2")
    assert files[f"bin/.{p}-post-link.sh"][0] == b"#!/bin/bash\n" + (HOOKS / "post-link.sh").read_bytes() + b"exit 0\n"
    assert files[f"bin/.{p}-pre-unlink.sh"][0] == b"#!/bin/bash\n" + fill((HOOKS / "pre-unlink.sh").read_bytes()) + b"exit 0\n"
    assert files[f"Scripts/.{p}-post-link.bat"][0] == (HOOKS / "post-link.bat").read_bytes() + b"exit /b 0\r\n"
    assert files[f"Scripts/.{p}-pre-unlink.bat"][0] == fill((HOOKS / "pre-unlink.bat").read_bytes()) + b"exit /b 0\r\n"
    for rel, (data, _) in files.items():
        if rel.endswith(".bat"):
            assert b"\n" not in data.replace(b"\r\n", b"")
        if rel.endswith((".sh", ".bat")):
            assert not re.search(rb"<(feature|package|version)>", data)
            assert b"pre-unlink light_locale" in data or b"post-link" in data


def test_pristine_base_has_no_base_dependency(tmp_path):
    pkg = package(tmp_path / "repo", feature="expose_foreign", version="1", base_tag=f"{R}/pristine/89701cf1768e")
    out = tmp_path / "out"
    assert render(pkg, out, isabelle_build="h1a2b_4", n=0).returncode == 0
    assert run_deps((out / "recipe.yaml").read_text()) == ["isabelle-patch-control >=1.0,<2", "isabelle ==2025.2 h1a2b_4"]


def test_component_payload_and_registration(tmp_path):
    pkg = package(tmp_path / "repo", components={"ROOT": "session Light_Locale = Pure +\n", "Light_Locale.thy": "theory X\n"})
    out = tmp_path / "out"
    r = render(pkg, out)
    assert r.returncode == 0, r.stderr
    files = files_of(out)
    p = "isabelle-light-locale"
    assert files[f"share/{p}/ROOT"][0] == b"session Light_Locale = Pure +\n"
    assert files[f"share/{p}/Light_Locale.thy"][0] == b"theory X\n"
    assert f"share/{p}/tools/component_files.txt" not in files
    post = files[f"bin/.{p}-post-link.sh"][0].decode()
    pre = files[f"bin/.{p}-pre-unlink.sh"][0].decode()
    # after the fragment's fi, before exit 0 (decision 9); after the tool's line in pre-unlink
    assert re.search(rf'\nfi\n"\$PREFIX/isa/bin/isabelle" components -u "\$PREFIX/share/{p}" .*\nexit 0\n$', post, re.S)
    assert re.search(rf'messages\.txt"\n"\$PREFIX/isa/bin/isabelle" components -x "\$PREFIX/share/{p}" .*\nexit 0\n$', pre, re.S)
    post_bat = files[f"Scripts/.{p}-post-link.bat"][0].decode().split("\r\n")
    pre_bat = files[f"Scripts/.{p}-pre-unlink.bat"][0].decode().split("\r\n")
    for lines, verb in ((post_bat, "-u"), (pre_bat, "-x")):
        end = lines.index(":end")
        assert lines[end + 1] == f'set "COMP=%PREFIX%\\share\\{p}"'
        assert lines[-3:] == [f'call "%PREFIX%\\isa\\bin\\isabelle.bat" components {verb} "%CYG%" >nul 2>&1', "exit /b 0", ""]
        assert 'getenv -b ISABELLE_HOME >nul 2>&1' in lines[-4]


def test_a_repository_with_two_packages(tmp_path):
    repo = tmp_path / "repo"
    ef = package(repo, "expose_foreign", feature="expose_foreign", version="1", base_tag=f"{R}/pristine/89701cf1768e")
    fai = package(repo, "future_assign_interrupt", feature="future_assign_interrupt", version="1",
                  base_tag=f"{R}/expose_foreign/1")
    assert render(fai, tmp_path / "fai").returncode == 0
    r = render(ef, tmp_path / "ef")                # HEAD carries only future_assign_interrupt/1
    assert r.returncode == 1 and "check out the release tag" in r.stderr
    git(repo, "-c", "advice.detachedHead=false", "checkout", "-q", f"{R}/expose_foreign/1")
    assert render(ef, tmp_path / "ef").returncode == 0


@pytest.mark.parametrize("case, says", [
    ("untagged", "check out the release tag"),
    ("untracked_patch", "differs from the checked-out release tag"),
    ("edited_readme", "differs from the checked-out release tag"),
    ("missing_component", "is not a committed file"),
    ("no_readme", "README.md is missing"),
    ("output_not_empty", "is not empty"),
    ("bad_build_string", "is not a build string"),
])
def test_refusals(tmp_path, case, says):
    out = tmp_path / "out"
    pkg = package(tmp_path / "repo", tag=case != "untagged",
                  components={"ROOT": "x\n"} if case == "missing_component" else None)
    build = "1"
    if case == "untracked_patch":
        (pkg / "patches" / R / "src-Pure-b.ML.patch").write_bytes(PATCH)
    elif case == "edited_readme":
        (pkg / "README.md").write_text("changed\n")
    elif case == "missing_component":
        (pkg / "tools" / "component_files.txt").write_text("ROOT\nLICENSE\n")
        git(tmp_path / "repo", "commit", "-q", "-am", "list LICENSE")
        git(tmp_path / "repo", "tag", "-f", "-a", "-m", "release", f"{R}/light_locale/2")
    elif case == "no_readme":
        (pkg / "README.md").unlink()
    elif case == "output_not_empty":
        out.mkdir()
        (out / "x").write_text("x")
    elif case == "bad_build_string":
        build = "1 x"
    r = render(pkg, out, isabelle_build=build)
    assert r.returncode == 1, r.stdout
    assert says in r.stderr


def test_a_cmd_metacharacter_in_an_echo_line_is_refused(tmp_path):
    """The .bat echo lines may hold only the quoted %PREFIX% and the closing >> (decision 9)."""
    copy = tmp_path / "tool"
    shutil.copytree(ROOT / "tools", copy / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__"))
    shutil.copytree(ROOT / "isabelle_patch_control", copy / "isabelle_patch_control", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "common-readme.md", copy)
    bat = copy / "isabelle_patch_control" / "hooks" / "pre-unlink.bat"
    bat.write_bytes(bat.read_bytes().replace(b"run isabelle-patch-control status.", b"run status & retry."))
    pkg = package(tmp_path / "repo")
    r = render(pkg, tmp_path / "out", tools=copy / "tools")
    assert r.returncode == 1 and "cmd metacharacter" in r.stderr
