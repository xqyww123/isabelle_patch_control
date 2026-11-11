"""The tree, the feature directories and how they link (plan decisions 2 and 3)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import names, texts
from .dev import package_version
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


def provenance_fields(text: str) -> dict[str, str]:
    """The `key: value` lines of a provenance file's text (make-patches writes them)."""
    fields = {}
    for line in text.splitlines():
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
    release_tag: str    # <R>/<name>/<m>
    base_tags: tuple[str, ...]    # the tags of the features it is built on, or (<R>/pristine/<id>,)

    @classmethod
    def read(cls, d: Path) -> FeatureDir | None:
        provenance = d / "provenance.txt"
        if not provenance.is_file():
            return None
        fields = provenance_fields(provenance.read_text())
        try:
            release_tag, base_tag = fields["release_tag"], fields["base_tag"]
        except KeyError as e:
            raise Refused(f"{provenance} lacks the field {e.args[0]}")
        return cls(d, release_tag.split("/")[1], release_tag, tuple(base_tag.split()))

    @property
    def version(self) -> str:
        return package_version(self.release_tag)

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


def link(tree: Tree, dirs: list[FeatureDir]) -> list[FeatureDir]:
    """Decision 3: every base tag of every directory is the tree's pristine tag or the release_tag of
    a directory; the directories in the environment's order (`ordered`).  A directory made for
    another pristine build is refused first; otherwise the refusal names, by directory, the first
    base no directory releases."""
    for fd in dirs:
        for base in fd.base_tags:
            m = re.fullmatch(r"([^/]+)/pristine/(.+)", base)
            if m and (m[1], m[2]) != (tree.release, tree.id):
                raise ChainBroken(texts.not_pristine(tree.path, tree.id, fd.dir.name, m[1], m[2]))
    released = {fd.release_tag for fd in dirs}
    for fd in sorted(dirs, key=lambda d: d.dir.name):
        for base in fd.base_tags:
            if base != tree.pristine_tag and base not in released:
                needs_name = base.split("/")[1]
                installed = [d for d in dirs if d.name == needs_name]
                raise ChainBroken(texts.chain_broken(
                    fd.package, fd.version, names.package_name(needs_name), package_version(base),
                    " and ".join(d.package + " " + d.version for d in installed) or None))
    return ordered(dirs)


def ordered(dirs: list[FeatureDir]) -> list[FeatureDir]:
    """The environment's order: by depth (1 on Isabelle itself, else one more than the deepest base),
    then by package name; the order in which conda links feature packages."""
    by_tag = {fd.release_tag: fd for fd in dirs}
    depth: dict[str, int] = {}

    def depth_of(fd: FeatureDir) -> int:
        if fd.release_tag not in depth:
            depth[fd.release_tag] = 1 + max((depth_of(by_tag[b]) for b in fd.base_tags if b in by_tag), default=0)
        return depth[fd.release_tag]

    return sorted(dirs, key=lambda fd: (depth_of(fd), fd.package))


def below(features: list[FeatureDir]) -> dict[int, frozenset[int]]:
    """For each feature number (1-based, in the environment's order), the numbers of the features
    below it: its bases, their bases, and so on."""
    number = {fd.release_tag: k for k, fd in enumerate(features, 1)}
    out: dict[int, frozenset[int]] = {}
    for k, fd in enumerate(features, 1):
        out[k] = frozenset().union(*({number[b]} | out[number[b]] for b in fd.base_tags if b in number))
    return out


def feature_number(installed: list[FeatureDir], feature: str) -> int:
    """The 1-based position of a feature, named by its feature name or its package name."""
    wanted = {feature, names.feature_name(feature)}
    for k, fd in enumerate(installed, 1):
        if fd.name in wanted:
            return k
    raise Refused(f"no feature package named {feature!r} is installed "
                  f"(installed: {', '.join(fd.name for fd in installed) or 'none'})")
