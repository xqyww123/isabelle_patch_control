"""The documents carry texts other things depend on: README embeds common-readme.md verbatim (the
release workflow copies that file into every feature package and runs its install command)."""
import re
import tomllib

from conftest import ROOT


def test_readme_embeds_the_common_text_verbatim():
    """The common text is everything between README's two rules, and every "*X* below" pointer in
    it names a heading that follows inside the common text (the feature packages' README has
    nothing else after it)."""
    common = (ROOT / "common-readme.md").read_text()
    assert (ROOT / "README.md").read_text().split("\n---\n")[1].strip() == common.strip()
    flat = " ".join(common.split())                                   # pointers and headings may wrap
    for m in re.finditer(r"\*([^*]+)\* below", flat):
        name = m.group(1)
        assert f"## {name}" in flat[m.end():] or f"**{name}.**" in flat[m.end():], name


def test_common_text_has_the_install_command_on_its_own_line():
    lines = (ROOT / "common-readme.md").read_text().splitlines()
    installs = [l for l in lines if l.startswith("conda create -n ")]     # the recovery's `conda create -p` is not it
    assert installs == ["conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale"]
    assert "conda update --all -c https://conda.qiyuan.me -c conda-forge" in lines


def test_pyproject_names_the_new_tool_only():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["name"] == "isabelle-patch-control"
    assert data["project"]["scripts"] == {"isabelle-patch-control": "isabelle_patch_control.cli:main"}
    assert data["tool"]["setuptools"]["packages"]["find"]["include"] == ["isabelle_patch_control", "isabelle_patch_control.*"]
    assert not re.search(r"my_better_isabelle_prover", (ROOT / "pyproject.toml").read_text())


def test_agents_md_has_the_section_the_conflict_message_points_to():
    assert "## Coming from my-better-isabelle 0.x" in (ROOT / "AGENTS.md").read_text()
    assert (ROOT / "isabelle_patch_control" / "AGENTS.md").resolve() == (ROOT / "AGENTS.md").resolve()
