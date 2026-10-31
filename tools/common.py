"""Shared code of the release scripts in tools/ (the workflows run them): patch file headers, the
hooks' component lines, conda archives, and which packages a release builds.  The helpers that
make-patches shares with them live in isabelle_patch_control.dev and are re-exported here.
"""
from __future__ import annotations

import io
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR.parent))            # the checkout's isabelle_patch_control, not an installed one
from isabelle_patch_control.dev import (block_path, build_string_prefix, feature_pin, patch_blocks,  # noqa: E402,F401
                                        run, shipped_files)                  # (re-exported for the scripts)
from isabelle_patch_control.errors import Error as ToolError, Refused  # noqa: E402
from isabelle_patch_control.names import package_name  # noqa: E402,F401  (re-exported for the scripts)


def main(fn):
    """Run a script's main function; a refusal (Refused, or any other error of the patch tool's
    API) is the script's refusal (exit 1)."""
    try:
        sys.exit(fn() or 0)
    except ToolError as e:
        print(f"{Path(sys.argv[0]).name}: refused: {e}", file=sys.stderr)
        sys.exit(1)


def components_sh(package: str, verb: str) -> str:
    """The hook lines that register (-u) or unregister (-x) a package's component, share/<package>."""
    return (f'"$PREFIX/isa/bin/isabelle" components {verb} "$PREFIX/share/{package}" 2>/dev/null \\\n'
            f'  || echo "warning: \'isabelle components {verb} {package}\' failed; the session may be unavailable"'
            f' >> "$PREFIX/.messages.txt"\n')


def components_bat(package: str, verb: str) -> list[str]:
    # Isabelle_RPC/conda/recipe.yaml's lines without their `@echo off`: a Cygwin path for
    # components, and the getenv warm-up without which the first call cannot run a Scala tool.
    return [f'set "COMP=%PREFIX%\\share\\{package}"',
            'set "DL=%COMP:~0,1%"',
            'set "REST=%COMP:~2%"',
            'set "REST=%REST:\\=/%"',
            'set "CYG=/cygdrive/%DL%%REST%"',
            'call "%PREFIX%\\isa\\bin\\isabelle.bat" getenv -b ISABELLE_HOME >nul 2>&1',
            f'call "%PREFIX%\\isa\\bin\\isabelle.bat" components {verb} "%CYG%" >nul 2>&1']


def block_header(block: bytes) -> tuple[str, str, str]:
    """(path, pre-image, post-image) of one `git diff` block; the images come from its `index
    <pre>..<post>` line, an all-zero image being a file absent on that side."""
    path = block_path(block)
    index = re.search(rb"(?m)^index ([0-9a-f]+)\.\.([0-9a-f]+)", block.split(b"\n@@", 1)[0])
    if not index:
        raise Refused(f"{path}: no index line in the diff header")
    return path, index[1].decode(), index[2].decode()


# --- which packages the release workflow builds and which it reuses (patch tool plan decision 10)

@dataclass(frozen=True)
class Wanted:
    """One package the batch wants: name and version; build n is the file
    `<name>-<version>-<build_string_prefix>_<n>.conda` (the prefix as provenance.txt spells it,
    `Isabelle2025_2`; the tool's is `pyh<hash>`); `pin` is the `isabelle` dependency a candidate on
    the channel must carry to be exactly what the batch wants (a feature package pins this batch's
    isabelle build; the tool, pin None, is any build of the version)."""
    name: str
    version: str
    build_string_prefix: str
    pin: str | None

    def filename(self, n: int) -> str:
        return f"{self.name}-{self.version}-{self.build_string_prefix}_{n}.conda"

    def accepts(self, record: dict) -> bool:
        return self.pin is None or self.pin in record["depends"]


def isabelle_pin(build_string_prefix: str, isabelle_build: str) -> str:
    """The `isabelle` dependency of a feature package, e.g. `isabelle ==2025.2 1`.  The renderer of the
    feature recipes imports this: the pin a recipe writes and the pin plan_builds looks for are then
    one and the same (rattler-build records it in `depends` as written).  `==`, not a bare version:
    rattler-build refuses `isabelle 2025.2 1` in a recipe; conda reads both the same."""
    return f"isabelle =={build_string_prefix.removeprefix('Isabelle').replace('_', '.')} {isabelle_build}"


def pinned_build(record: dict, build_string_prefix: str) -> str | None:
    """The inverse of isabelle_pin: the isabelle build a package record's depends pin, or None."""
    pin = isabelle_pin(build_string_prefix, "")
    return next((dep[len(pin):] for dep in record.get("depends", []) if dep.startswith(pin) and dep != pin), None)


def unzstd(data: bytes) -> bytes:
    """zstd decompression: the standard library's from Python 3.14, else the zstandard module."""
    try:
        from compression import zstd
    except ImportError:
        import zstandard
        return zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data)).read()
    return zstd.decompress(data)


def conda_archive(data: bytes) -> tuple[dict, dict[str, tuple[bytes, int]]]:
    """(info/index.json, {path: (bytes, mode)} of the payload) of a .conda archive: a zip of two
    zstd tarballs."""
    import tarfile
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(data))

    def members(prefix: str) -> dict[str, tuple[bytes, int]]:
        name = next(n for n in z.namelist() if n.startswith(prefix) and n.endswith(".tar.zst"))
        raw = unzstd(z.read(name))
        with tarfile.open(fileobj=io.BytesIO(raw)) as t:
            return {m.name: (t.extractfile(m).read(), m.mode) for m in t.getmembers() if m.isfile()}

    return json.loads(members("info-")["info/index.json"][0]), members("pkg-")


def plan_builds(repodata: dict, wanted: list[Wanted], fetch: Callable[[str], dict | None]) -> dict[str, tuple[str, str | int]]:
    """For every wanted package: ("reuse", <file name on the channel>) or ("build", <build number>).

    Candidates are the channel's indexed records of (name, version) plus the files the channel
    serves but has not indexed yet: `fetch(filename)` returns such a file's index record or None,
    probed from the highest indexed build number + 1 upwards.  A candidate the batch wants is
    reused; a served candidate it does not want is skipped; with no wanted candidate the package
    is built with the next number after everything indexed or served (0 when there is nothing).
    So a dispatch repeated with the same inputs resumes byte for byte."""
    records = {**repodata.get("packages", {}), **repodata.get("packages.conda", {})}
    plan = {}
    for w in wanted:
        candidates = [(fn, rec) for fn, rec in records.items()
                      if rec.get("name") == w.name and rec.get("version") == w.version]
        n = max((int(rec["build_number"]) for _, rec in candidates), default=-1) + 1
        while (rec := fetch(w.filename(n))) is not None:
            candidates.append((w.filename(n), rec))
            n += 1
        matching = [(int(rec["build_number"]), fn) for fn, rec in candidates if w.accepts(rec)]
        plan[w.name] = ("reuse", max(matching)[1]) if matching else ("build", n)
    return plan
