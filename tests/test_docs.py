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


def test_agents_md_lists_the_commands_as_help_does():
    from isabelle_patch_control import cli
    block = (ROOT / "AGENTS.md").read_text().split("## Commands\n\n```\n", 1)[1].split("```", 1)[0]
    commands = [line for line in block.splitlines() if line.startswith("  ")]
    assert len(commands) == 7 and all(line in cli.__doc__.splitlines() for line in commands)


def test_readme_sends_what_to_do_to_help():
    """The common text answers what it is, how to install, how to check; what to do is in AGENTS.md,
    which `isabelle-patch-control help` prints."""
    common = " ".join((ROOT / "common-readme.md").read_text().split())
    assert "`isabelle-patch-control help`" in common and "--force-reinstall" not in common
    agents = (ROOT / "AGENTS.md").read_text()
    assert "## What to do in each situation" in agents and "## Removing, re-installing, and what conda does on its own" in agents
    assert (ROOT / "isabelle_patch_control" / "AGENTS.md").resolve() == (ROOT / "AGENTS.md").resolve()
