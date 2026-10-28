"""The tree, the feature directories and the chain (plan decisions 2 and 3)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import names, texts
from .errors import ChainBroken, NotFound, Refused

FEATURES_D = Path("share/isabelle_patch_control/features.d")


def locate(prefix: Path) -> tuple[Path, Path]:
    """Decision 2: a conda environment's tree and features.d root."""
    return prefix / "isa", prefix / FEATURES_D


@dataclass(frozen=True)
class Tree:
    path: Path
    release: str        # etc/ISABELLE_IDENTIFIER, e.g. Isabelle2025-2
    id: str             # etc/ISABELLE_ID, the hg changeset of the build

    @classmethod
    def read(cls, path: Path) -> Tree:
        identifier, build_id = path / "etc" / "ISABELLE_IDENTIFIER", path / "etc" / "ISABELLE_ID"
        if not (identifier.is_file() and build_id.is_file()):
            raise NotFound(f"no Isabelle tree at {path} (etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID expected)")
        if (path / ".git").exists():
            raise Refused(f"{path} has a .git: isabelle-patch-control does not touch a tree that git manages")
        return cls(path, identifier.read_text().strip(), build_id.read_text().strip())

    @property
    def pristine_tag(self) -> str:
        return f"{self.release}/pristine/{self.id}"


def provenance_fields(provenance: Path) -> dict[str, str]:
    """The `key: value` lines of a provenance file (make-patches writes them)."""
    fields = {}
    for line in provenance.read_text().splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


@dataclass(frozen=True)
class FeatureDir:
    """A feature package's directory `features.d/<feature>/`: its provenance file and patch files
    are all the tool reads of it."""
    dir: Path
    name: str           # the <name> of release_tag
    release_tag: str    # <R>/<name>/<version>
    base_tag: str       # the tag of the feature below, or <R>/pristine/<id>

    @classmethod
    def read(cls, d: Path) -> FeatureDir | None:
        provenance = d / "provenance.txt"
        if not provenance.is_file():
            return None
        fields = provenance_fields(provenance)
        try:
            release_tag, base_tag = fields["release_tag"], fields["base_tag"]
        except KeyError as e:
            raise Refused(f"{provenance} lacks the field {e.args[0]}")
        return cls(d, release_tag.split("/")[1], release_tag, base_tag)

    @property
    def version(self) -> str:
        return self.release_tag.rsplit("/", 1)[1]

    @property
    def package(self) -> str:
        return names.package_name(self.name)

    @property
    def patch_files(self) -> list[Path]:
        files = sorted(self.dir.glob("*.patch"))
        if not files:
            raise Refused(f"{self.dir} has no patch file")
        return files


def read_feature_dirs(root: Path) -> list[FeatureDir]:
    """Every subdirectory with a provenance.txt; anything else (`*.c~` left by conda, editor
    droppings) is not looked at.  No root: no feature package is installed."""
    if not root.is_dir():
        return []
    return [fd for d in sorted(root.iterdir()) if d.is_dir() and (fd := FeatureDir.read(d))]


def link_chain(tree: Tree, dirs: list[FeatureDir]) -> list[FeatureDir]:
    """Decision 3: from the tree's pristine tag, exactly one directory's base_tag equals the
    current tag at each step and its release_tag becomes the next; every directory must be used.
    A directory made for another pristine build is refused first; otherwise the refusal names a
    leftover directory whose base_tag no directory releases."""
    for fd in dirs:
        m = re.fullmatch(r"([^/]+)/pristine/(.+)", fd.base_tag)
        if m and (m[1], m[2]) != (tree.release, tree.id):
            raise ChainBroken(texts.not_pristine(tree.path, tree.id, fd.dir.name, m[1], m[2]))
    by_base: dict[str, list[FeatureDir]] = {}
    for fd in dirs:
        by_base.setdefault(fd.base_tag, []).append(fd)
    chain, tag = [], tree.pristine_tag
    while tag in by_base:
        nexts = by_base.pop(tag)
        if len(nexts) > 1:
            raise ChainBroken(f"features.d/{nexts[0].dir.name} and features.d/{nexts[1].dir.name} are both made "
                              f"for {tag}: {' and '.join(fd.package + ' ' + fd.version for fd in nexts)} cannot be "
                              "installed together")
        chain.append(nexts[0])
        tag = nexts[0].release_tag
    if left := [fd for fds in by_base.values() for fd in fds]:
        released = {fd.release_tag for fd in dirs}
        fd = min(left, key=lambda d: d.base_tag in released)        # one whose base no directory releases
        needs_name, needs_version = fd.base_tag.split("/")[1:3]
        installed = [d for d in dirs if d.name == needs_name]
        raise ChainBroken(texts.chain_broken(
            fd.package, fd.version, fd.dir.name, names.package_name(needs_name), needs_version, fd.base_tag,
            " and ".join(d.package + " " + d.version for d in installed) or "none"))
    return chain


def feature_number(chain: list[FeatureDir], feature: str) -> int:
    """The 1-based position of a feature, named by its feature name or its package name."""
    wanted = {feature, names.feature_name(feature)}
    for k, fd in enumerate(chain, 1):
        if fd.name in wanted:
            return k
    raise Refused(f"no feature package named {feature!r} is installed "
                  f"(installed: {', '.join(fd.name for fd in chain) or 'none'})")
