#!/usr/bin/env bash
# toy-channel.sh <dir> [<release line>]: the toy channels of the hook-layer test and of the GitHub
# test workflow (patch tool plan decision 15), built under <dir>.  For Isabelle2025-2 (the default):
#   channel/            the tool; isabelle builds 0 (another ISABELLE_ID), 1 and 2; the features t_one,
#                       t_two, t_three for builds 1 and 2, through the real renderer; toy-component;
#                       toy-indirect and toy-slow (the hook-layer test's)
#   channel-broken/     a tool that raises on import
#   channel-norelease/  isabelle build 2 with the features of build 1 only
#   summary.json        tools/check-packages --summary of the build-2 batch, as the release's build job writes it
# For Isabelle2026, a new release line whose first pristine build is build 0: channel/ holds the
# tool, isabelle 2026 build 0 (pristine), the three features for it and toy-component; summary.json
# is of the build-0 batch.  The GitHub test workflow serves both lines' channel/ as one channel, as
# the online channel will: every file but the tool's has a name of its own per line.
# Every package is noarch, so one channel serves all five platforms.  RATTLER_BUILD names the
# rattler-build binary (default: rattler-build on PATH).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../.." && pwd); tools="$root/tools"
W=$1; mkdir -p "$W"; W=$(cd "$W" && pwd)
RB=${RATTLER_BUILD:-rattler-build}
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
CH="$W/channel"; BAD="$W/channel-broken"; NORE="$W/channel-norelease"; R=${2:-Isabelle2025-2}
case $R in       # the isabelle version, its pristine builds (each with the features), toy-component's isabelle range and build number
  Isabelle2025-2) V=2025.2 BUILDS="1 2" RANGE=">=2025.2,<2025.3" COMPONENT_BUILD=0 ;;
  Isabelle2026)   V=2026   BUILDS=0     RANGE=">=2026,<2026.1"   COMPONENT_BUILD=1 ;;
  *) echo "toy-channel.sh: no toy release line $R (Isabelle2025-2, Isabelle2026)" >&2; exit 2 ;;
esac
crlf() { printf '%s\r\n' "$@"; }

# ---------------------------------------------------------------- the toy sources and feature repositories
# One description of the toy Isabelle tree feeds both the isabelle package's isa/ and the toy
# Isabelle source repository the patch files are cut from, so the patches fit the packaged tree.
python3 -I - "$W" "$tools" "$R" <<'PY'
import os, subprocess, sys
from pathlib import Path
W, tools, R = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path.insert(0, tools); sys.path.insert(0, str(Path(tools).parent))
from common import build_string_prefix, feature_pin, patch_blocks

PRISTINE, PREFIX = "89701cf1768e", build_string_prefix(R)
TREE = {
    "etc/ISABELLE_IDENTIFIER": R,
    "etc/options": "option ML_system_64 : bool = true\n",
    "src/Pure/a.ML": "".join(f"a{i}\n" for i in range(1, 9)),
    "src/Pure/b.ML": "".join(f"b{i}\n" for i in range(1, 9)),
    "src/Pure/c.ML": "".join(f"c{i}\n" for i in range(1, 9)),
}

def write(base, rel, text):
    p = base / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

for rel, text in TREE.items():
    write(W / "isa-src", rel, text)
src = W / "src"; src.mkdir()
git(src, "init", "-q", "-b", "main")
for rel, text in TREE.items():
    write(src, rel, text)
write(src, "etc/ISABELLE_ID", PRISTINE + "\n")
git(src, "add", "-A"); git(src, "commit", "-qm", "pristine"); git(src, "tag", f"{R}/pristine/{PRISTINE}")

def edit(rel, old, new):
    p = src / rel; s = p.read_text(); assert old in s, (rel, old); p.write_text(s.replace(old, new, 1))

# name, changes; t_two's a.ML hunk has t_one's line as context (stacked), t_two ships a component.
# Every feature creates a file: the hook-layer test's interrupted install abandons t_two.
FEATURES = [
    ("t_one", lambda: (edit("src/Pure/a.ML", "a3\n", "a3\nT1\n"), write(src, "src/Pure/t_one.ML", "t_one\n"))),
    ("t_two", lambda: (edit("src/Pure/a.ML", "T1\na4\n", "T1\nT2\na4\n"), edit("src/Pure/b.ML", "b5\n", "B5\n"),
                       write(src, "src/Pure/t_two.ML", "t_two\n"))),
    ("t_three", lambda: (edit("src/Pure/c.ML", "c2\n", "C2\n"), write(src, "src/Tools/t_three.ML", "t_three\n"))),
]
base = f"{R}/pristine/{PRISTINE}"
for name, change in FEATURES:
    change()
    git(src, "add", "-A"); git(src, "commit", "-qm", name)
    tag = f"{R}/{name}/1"; git(src, "tag", tag)
    pkg = W / "features" / name; d = pkg / "patches" / R; d.mkdir(parents=True)
    diff = subprocess.run(["git", "diff-tree", "-r", "-p", "--no-renames", base, tag], cwd=src, check=True,
                          capture_output=True).stdout
    for file, block in patch_blocks(diff).items():
        (d / file).write_bytes(block)
    _, base_name, base_version = base.split("/")
    pristine = base_name == "pristine"
    (d / "provenance.txt").write_text("\n".join([
        f"feature: {R}/{name}", f"release_tag: {tag}", f"commit: {git(src, 'rev-parse', tag)}", f"base_tag: {base}",
        f"base_commit: {git(src, 'rev-parse', base)}",
        f"base_package_version: {'none (the base is pristine)' if pristine else base_version}",
        f"base_pin: {'none' if pristine else feature_pin(base_version, PREFIX)}",
        f"build_string_prefix: {PREFIX}", "tree_hash: x", "tree_hash_excludes: etc/ISABELLE_ID"]) + "\n")
    write(pkg, "README.md", f"# {name}\n\nA toy feature of the hook-layer tests.\n")
    if name == "t_two":
        write(pkg, "tools/component_files.txt", "ROOT\nT_Two.thy\n")
        write(pkg, "ROOT", "session T_Two = Pure + theories T_Two\n")
        write(pkg, "T_Two.thy", "theory T_Two imports Pure begin end\n")
    git(pkg, "init", "-q", "-b", "main"); git(pkg, "add", "-A"); git(pkg, "commit", "-qm", f"{name} release 1")
    git(pkg, "tag", "-a", "-m", "release", tag)
    base = tag
PY

# ---------------------------------------------------------------- the toy isabelle package (2025.2: builds 0, 1, 2; 2026: 0)
# 2025.2's build 0 plays the patched 2025.2-0 (another ISABELLE_ID); the others are pristine builds.  isa/bin's
# isabelle and isabelle.bat run toy_isabelle.py with the environment's python, which the package
# depends on (as the CI plan's isabelle package does, plan decision 12 point 2); its post-link only
# re-runs the post-link of the packages that depend on isabelle directly (plan §0 items 26, 33, 34).
isabelle_recipe() {  # <build number> <ISABELLE_ID> <output channel>
  local n=$1 id=$2 out=$3 d="$W/recipes/isabelle-$1-$(basename "$3")"
  mkdir -p "$d/files/isa/bin" "$d/files/bin" "$d/files/Scripts"
  cp -a "$W/isa-src/." "$d/files/isa/"
  printf '%s\n' "$id" > "$d/files/isa/etc/ISABELLE_ID"
  cp "$here/toy_isabelle.py" "$d/files/isa/bin/isabelle.py"
  printf '#!/bin/bash\nexec "$(dirname "$0")/../../bin/python" -I "$(dirname "$0")/isabelle.py" "$@"\n' > "$d/files/isa/bin/isabelle"
  crlf '@echo off' '"%~dp0..\..\python.exe" -I "%~dp0isabelle.py" %*' 'exit /b %errorlevel%' > "$d/files/isa/bin/isabelle.bat"
  printf '#!/bin/bash\n"$PREFIX/bin/python" -I "$PREFIX/isa/bin/isabelle.py" --rerun-post-links || true\nexit 0\n' \
    > "$d/files/bin/.isabelle-post-link.sh"
  crlf '@echo off' '"%PREFIX%\python.exe" -I "%PREFIX%\isa\bin\isabelle.py" --rerun-post-links' 'exit /b 0' \
    > "$d/files/Scripts/.isabelle-post-link.bat"
  # the real pre-unlinks: isabelle-packaging-ci conda/recipe.yaml:223-231 (.sh) and :153-169 (.bat)
  printf '%s\n' \
    '#!/bin/bash' \
    'd="$("$PREFIX/isa/bin/isabelle" getenv -b ISABELLE_HOME_USER 2>/dev/null)" || exit 0' \
    'case "$d" in' \
    '  */.isabelle/*-conda-*) rm -rf "$d" ;;' \
    'esac' \
    'exit 0' \
    > "$d/files/bin/.isabelle-pre-unlink.sh"
  crlf \
    '@echo off' \
    'set "ISA=%PREFIX%\isa"' \
    'call "%ISA%\bin\isabelle.bat" version >nul 2>&1' \
    'set "ISAU="' \
    'for /f "delims=" %%d in ('"'"'call "%ISA%\bin\isabelle.bat" getenv -b ISABELLE_HOME_USER 2^>nul'"'"') do set "ISAU=%%d"' \
    'if not defined ISAU exit /b 0' \
    'echo %ISAU%| findstr /C:"-conda-" >nul || exit /b 0' \
    'echo %ISAU%| findstr /B /C:"/cygdrive/" >nul || exit /b 0' \
    'set "P=%ISAU:/cygdrive/=%"' \
    'set "DL=%P:~0,1%"' \
    'set "REST=%P:~1%"' \
    'set "ISAUW=%DL%:%REST%"' \
    'set "ISAUW=%ISAUW:/=\%"' \
    'if exist "%ISAUW%" rmdir /s /q "%ISAUW%"' \
    'exit /b 0' \
    > "$d/files/Scripts/.isabelle-pre-unlink.bat"
  chmod 755 "$d/files/isa/bin/isabelle" "$d/files/bin/".isabelle-*.sh
  cat > "$d/recipe.yaml" <<EOF
schema_version: 1
package: {name: isabelle, version: "$V"}
source: [{path: files}]
build:
  number: $n
  string: "$n"
  noarch: generic
  script:
    interpreter: bash
    content: |
      set -euo pipefail
      cp -a "\$SRC_DIR/isa" "\$SRC_DIR/bin" "\$SRC_DIR/Scripts" "\$PREFIX/"
requirements: {run: [python]}
EOF
  "$RB" build --recipe "$d/recipe.yaml" --output-dir "$out" --no-test > "$d.log" 2>&1 || { tail -20 "$d.log"; exit 1; }
}

simple_recipe() {  # <dir> <name> <version> <run dependency> <post-link body>: a generic package with one post-link
  local d=$1
  mkdir -p "$d/files/bin"
  printf '#!/bin/bash\n%s\nexit 0\n' "$5" > "$d/files/bin/.$2-post-link.sh"; chmod 755 "$d/files/bin/.$2-post-link.sh"
  cat > "$d/recipe.yaml" <<EOF
schema_version: 1
package: {name: $2, version: "$3"}
source: [{path: files}]
build: {number: 0, noarch: generic, script: {interpreter: bash, content: 'cp -a "\$SRC_DIR/bin" "\$PREFIX/"'}}
requirements: {run: ["$4"]}
EOF
}

echo "--- building the toy channels under $W"
TOOL_VERSION=$(python3 -I -c "import tomllib,sys; print(tomllib.load(open(sys.argv[1],'rb'))['project']['version'])" "$root/pyproject.toml")
# build number 1: the broken tool's 0 is below it, so `conda update --all` moves from it to this one;
# with the recipe's tests, as the release builds it
TOOL_VERSION=$TOOL_VERSION TOOL_BUILD_NUMBER=1 "$RB" build --recipe "$root/conda/recipe.yaml" --output-dir "$CH" \
  -c conda-forge > "$W/tool.log" 2>&1 || { tail -30 "$W/tool.log"; exit 1; }
[ "$R" != Isabelle2025-2 ] || isabelle_recipe 0 5533cd83156e "$CH"
for b in $BUILDS; do isabelle_recipe "$b" 89701cf1768e "$CH"; done
n=0
for b in $BUILDS; do                               # every feature for each pristine build, build numbers 0, 1, ...
  for f in t_one t_two t_three; do
    r="$W/recipes/$f-$b"
    python3 "$tools/render-feature-recipe" "$W/features/$f" --isabelle-build "$b" --build-number $n -o "$r" > /dev/null
    "$RB" build --recipe "$r/recipe.yaml" --output-dir "$CH" --no-test > "$r.log" 2>&1 || { tail -20 "$r.log"; exit 1; }
  done
  n=$((n + 1))
done

# an Isabelle_RPC-style component package (plan §6 (c), (e)): it registers share/toy-component with
# the hook lines every component package uses
python3 -I - "$W/recipes/component" "$tools" "$RANGE" "$COMPONENT_BUILD" <<'PY'
import sys
from pathlib import Path
d, tools, isabelle_range, number = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, tools); sys.path.insert(0, str(Path(tools).parent))
from common import components_bat, components_sh
name, files = "toy-component", d / "files"
(files / "share" / name).mkdir(parents=True)
(files / "share" / name / "ROOT").write_text("session Toy_Component = Pure\n")
for hook, verb in (("post-link", "-u"), ("pre-unlink", "-x")):
    sh = files / "bin" / f".{name}-{hook}.sh"
    sh.parent.mkdir(exist_ok=True)
    sh.write_text("#!/bin/bash\n" + components_sh(name, verb) + "exit 0\n"); sh.chmod(0o755)
    bat = files / "Scripts" / f".{name}-{hook}.bat"
    bat.parent.mkdir(exist_ok=True)
    bat.write_bytes(("\r\n".join(["@echo off", *components_bat(name, verb), "exit /b 0"]) + "\r\n").encode())
(d / "recipe.yaml").write_text(f"""schema_version: 1
package: {{name: {name}, version: "1"}}
source: [{{path: files}}]
build: {{number: {number}, noarch: generic, script: {{interpreter: bash, content: 'cp -a "$SRC_DIR/bin" "$SRC_DIR/Scripts" "$SRC_DIR/share" "$PREFIX/"'}}}}
requirements: {{run: ["isabelle {isabelle_range}"]}}
""")
PY
"$RB" build --recipe "$W/recipes/component/recipe.yaml" --output-dir "$CH" --no-test > "$W/recipes/component.log" 2>&1 \
  || { tail -20 "$W/recipes/component.log"; exit 1; }

if [ "$R" = Isabelle2025-2 ]; then                 # the hook-layer test's packages and channels
  simple_recipe "$W/recipes/indirect" toy-indirect 1 isabelle-t-two 'echo x >> "$PREFIX/toy-indirect.count"'
  "$RB" build --recipe "$W/recipes/indirect/recipe.yaml" --output-dir "$CH" --no-test > "$W/recipes/indirect.log" 2>&1
  # the interrupted install's slow package: its post-link marks that every file is linked (t_two's
  # post-link ran before it, its dependency), then waits for the SIGINT
  simple_recipe "$W/recipes/slow" toy-slow 1 isabelle-t-two 'touch "$PREFIX/slow.started"; sleep 120'
  "$RB" build --recipe "$W/recipes/slow/recipe.yaml" --output-dir "$CH" --no-test > "$W/recipes/slow.log" 2>&1

  # the channel without a matching re-release: the same files (the package cache knows a package by its
  # file name), isabelle build 2 but the features of build 1 only; building one more package indexes it
  mkdir -p "$NORE/noarch"
  cp "$CH"/noarch/isabelle-patch-control-*_1.conda "$CH"/noarch/isabelle-2025.2-[12].conda \
     "$CH"/noarch/isabelle-t-*-Isabelle2025_2_0.conda "$NORE/noarch/"
  simple_recipe "$W/recipes/index" toy-index 1 isabelle ':'
  "$RB" build --recipe "$W/recipes/index/recipe.yaml" --output-dir "$NORE" --no-test > "$W/recipes/index.log" 2>&1

  # the broken tool: the same name and entry point, a module that raises on import; its own channel
  b="$W/recipes/broken"; mkdir -p "$b/files/isabelle_patch_control"
  echo 'raise RuntimeError("a broken isabelle-patch-control for the hook-layer tests")' > "$b/files/isabelle_patch_control/__init__.py"
  : > "$b/files/isabelle_patch_control/cli.py"
  printf '[build-system]\nrequires = ["setuptools>=77"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "isabelle-patch-control"\nversion = "%s"\n' "$TOOL_VERSION" > "$b/files/pyproject.toml"
  cat > "$b/recipe.yaml" <<EOF
schema_version: 1
package: {name: isabelle-patch-control, version: "$TOOL_VERSION"}
source: [{path: files}]
build:
  number: 0
  noarch: python
  python: {entry_points: ["isabelle-patch-control = isabelle_patch_control.cli:main"]}
  script: {interpreter: bash, content: '\$PYTHON -m pip install . --no-deps --no-build-isolation'}
requirements: {host: [python >=3.12, pip, setuptools >=77], run: [python >=3.12, git >=2.43]}
EOF
  "$RB" build --recipe "$b/recipe.yaml" --output-dir "$BAD" -c conda-forge --no-test > "$b.log" 2>&1 || { tail -20 "$b.log"; exit 1; }
  python3 -I - "$NORE" <<'PY'                       # the indexing step must have seen the copied files
import json, sys
names = set(json.load(open(f"{sys.argv[1]}/noarch/repodata.json"))["packages.conda"])
assert {"isabelle-2025.2-2.conda", "isabelle-t-three-1-Isabelle2025_2_0.conda"} <= names, sorted(names)
assert not any(n.endswith("Isabelle2025_2_1.conda") for n in names), sorted(names)
PY
fi
# the batch of the last pristine build (2025.2: build 2) as the release's build job looks at it
python3 "$tools/check-packages" --chain "$R/t_one/1" "$R/t_two/1" "$R/t_three/1" --summary "$W/summary.json" \
  "$CH"/noarch/isabelle-patch-control-*.conda "$CH"/noarch/isabelle-t-*-"${R//-/_}_$((n - 1))".conda
find "$W"/channel* -name '*.conda' -printf '  %h/%f\n' | sed "s|$W/||" | sort
