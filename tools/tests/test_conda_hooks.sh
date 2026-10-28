#!/usr/bin/env bash
# Hook-layer tests (patch tool plan decision 15): real conda, a private HOME, CONDARC and
# CONDA_PKGS_DIRS, channels `--override-channels -c file://<toy> -c conda-forge`.  The feature
# packages are built by the real renderer and rattler-build; only the toy isabelle package, a
# package that depends on isabelle only indirectly, and the broken tool are built from small recipes
# written here.  Assertions read conda's stdout (conda deletes .messages.txt after printing it) and
# the tree's bytes (tools/check-bytes against the unpacked packages in the package cache).
#
# Usage: test_conda_hooks.sh [<scratch dir>] [<scenario>...]
#   RATTLER_BUILD  the rattler-build binary (default: rattler-build on PATH)
#   CONDA_EXE      the conda binary (default: conda on PATH)
#   HOOKS_TEST_CACHE  a directory kept between runs for conda's and rattler-build's downloads
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../.." && pwd); tools="$root/tools"
W=${1:-$(mktemp -d)}; shift || true
rm -rf "$W"; mkdir -p "$W"; W=$(cd "$W" && pwd)
RB=${RATTLER_BUILD:-rattler-build}
CONDA=${CONDA_EXE:-conda}
cache=${HOOKS_TEST_CACHE:-$W/cache}; mkdir -p "$cache"
export HOME="$W/home" CONDARC="$W/condarc" CONDA_PKGS_DIRS="$cache/pkgs" RATTLER_CACHE_DIR="$cache/rattler" \
  CONDA_CHANNEL_PRIORITY=strict CONDA_ALWAYS_YES=true CONDA_NOTIFY_OUTDATED_CONDA=false \
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME"; : > "$CONDARC"
CH="$W/channel"; BAD="$W/channel-broken"; NORE="$W/channel-norelease"; R=Isabelle2025-2
CHANNELS=(--override-channels -c "file://$CH" -c conda-forge)
BROKEN=(--override-channels -c "file://$BAD" -c "file://$CH" -c conda-forge)   # strict priority: its tool wins
NORELEASE=(--override-channels -c "file://$NORE" -c conda-forge)              # isabelle build 2, features for build 1 only
log() { echo "    $*"; }

# ---------------------------------------------------------------- the toy sources and feature repositories
# One description of the toy Isabelle tree feeds both the isabelle package's isa/ and the toy
# Isabelle source repository the patch files are cut from, so the patches fit the packaged tree.
python3 -I - "$W" "$tools" <<'PY'
import os, subprocess, sys
from pathlib import Path
W, tools = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, tools); sys.path.insert(0, str(Path(tools).parent))
from common import feature_pin, patch_blocks

R, PRISTINE = "Isabelle2025-2", "89701cf1768e"
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

FEATURES = [  # name, changes; t_two's a.ML hunk has t_one's line as context (stacked), t_two ships a component
    ("t_one", lambda: (edit("src/Pure/a.ML", "a3\n", "a3\nT1\n"), write(src, "src/Pure/t_one.ML", "t_one\n"))),
    ("t_two", lambda: (edit("src/Pure/a.ML", "T1\na4\n", "T1\nT2\na4\n"), edit("src/Pure/b.ML", "b5\n", "B5\n"))),
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
        f"base_pin: {'none' if pristine else feature_pin(base_version, 'Isabelle2025_2')}",
        "build_string_prefix: Isabelle2025_2", "tree_hash: x", "tree_hash_excludes: etc/ISABELLE_ID"]) + "\n")
    write(pkg, "README.md", f"# {name}\n\nA toy feature of the hook-layer tests.\n")
    if name == "t_two":
        write(pkg, "tools/component_files.txt", "ROOT\nT_Two.thy\n")
        write(pkg, "ROOT", "session T_Two = Pure + theories T_Two\n")
        write(pkg, "T_Two.thy", "theory T_Two imports Pure begin end\n")
    git(pkg, "init", "-q", "-b", "main"); git(pkg, "add", "-A"); git(pkg, "commit", "-qm", f"{name} release 1")
    git(pkg, "tag", "-a", "-m", "release", tag)
    base = tag
PY

# ---------------------------------------------------------------- the toy isabelle package (builds 0, 1, 2)
# Build 0 plays the patched 2025.2-0 (another ISABELLE_ID); 1 and 2 are pristine builds.  The stub
# isabelle answers what the hooks ask; pre-unlink is the real one (isabelle-packaging-ci
# conda/recipe.yaml); post-link only re-runs the post-link of the installed packages that depend
# on isabelle directly (plan §0 items 26, 33, 34; the CI plan implements the real one).
isabelle_recipe() {  # <build number> <ISABELLE_ID> <output channel>
  local n=$1 id=$2 out=$3 d="$W/recipes/isabelle-$1-$(basename "$3")"
  mkdir -p "$d/files/isa/bin" "$d/files/bin"
  cp -a "$W/isa-src/." "$d/files/isa/"
  printf '%s\n' "$id" > "$d/files/isa/etc/ISABELLE_ID"
  cat > "$d/files/isa/bin/isabelle" <<'EOF'
#!/bin/bash
# toy isabelle: getenv -b ISABELLE_HOME_USER|ISABELLE_HOME, components -u|-x <dir>
home=$(cd "$(dirname "$0")/.." && pwd)
user="$HOME/.isabelle/Isabelle2025-2-conda-$(basename "$(dirname "$home")")"
case "$1 ${2-}" in
  "getenv -b") case "$3" in ISABELLE_HOME_USER) echo "$user" ;; ISABELLE_HOME) echo "$home" ;; *) exit 2 ;; esac ;;
  "components -u") mkdir -p "$user/etc"; touch "$user/etc/components"
                   grep -qxF "$3" "$user/etc/components" || echo "$3" >> "$user/etc/components" ;;
  "components -x") [ -f "$user/etc/components" ] || exit 0
                   grep -vxF "$3" "$user/etc/components" > "$user/etc/components.new" || true
                   mv "$user/etc/components.new" "$user/etc/components" ;;
  *) echo "toy isabelle: $*" >&2; exit 2 ;;
esac
EOF
  chmod 755 "$d/files/isa/bin/isabelle"
  cat > "$d/files/bin/.isabelle-pre-unlink.sh" <<'EOF'
#!/bin/bash
d="$("$PREFIX/isa/bin/isabelle" getenv -b ISABELLE_HOME_USER 2>/dev/null)" || exit 0
case "$d" in
  */.isabelle/*-conda-*) rm -rf "$d" ;;
esac
exit 0
EOF
  cat > "$d/files/bin/.isabelle-post-link.sh" <<'EOF'
#!/bin/bash
[ -x "$PREFIX/bin/python" ] || exit 0
"$PREFIX/bin/python" -I - <<'PY' || true
import json, os, subprocess
from pathlib import Path
prefix = Path(os.environ["PREFIX"])
records = {}
for p in (prefix / "conda-meta").glob("*.json"):
    d = json.loads(p.read_text())
    records[d["name"]] = d
direct = {n: d for n, d in records.items() if any(dep.split()[0] == "isabelle" for dep in d.get("depends", []))}
order, seen = [], set()
def visit(n):
    if n not in seen:
        seen.add(n)
        for dep in direct[n].get("depends", []):
            if dep.split()[0] in direct:
                visit(dep.split()[0])
        order.append(n)
for n in sorted(direct):
    visit(n)
for n in order:
    script = prefix / "bin" / f".{n}-post-link.sh"
    if script.is_file():
        d = direct[n]
        subprocess.run(["bash", str(script)], env={**os.environ, "PKG_NAME": n, "PKG_VERSION": d["version"],
                                                   "PKG_BUILDNUM": str(d["build_number"])})
PY
exit 0
EOF
  chmod 755 "$d/files/bin/".isabelle-*.sh
  cat > "$d/recipe.yaml" <<EOF
schema_version: 1
package: {name: isabelle, version: "2025.2"}
source: [{path: files}]
build:
  number: $n
  string: "$n"
  noarch: generic
  script:
    interpreter: bash
    content: |
      set -euo pipefail
      cp -a "\$SRC_DIR/isa" "\$SRC_DIR/bin" "\$PREFIX/"
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
# build number 1: the broken tool's 0 is below it, so `conda update --all` moves from it to this one
TOOL_VERSION=$TOOL_VERSION TOOL_BUILD_NUMBER=1 "$RB" build --recipe "$root/conda/recipe.yaml" --output-dir "$CH" \
  -c conda-forge --no-test > "$W/tool.log" 2>&1 || { tail -30 "$W/tool.log"; exit 1; }
isabelle_recipe 0 5533cd83156e "$CH"
isabelle_recipe 1 89701cf1768e "$CH"
isabelle_recipe 2 89701cf1768e "$CH"
for b in 1 2; do                                   # every feature for build 1 (build number 0) and build 2 (1)
  for f in t_one t_two t_three; do
    r="$W/recipes/$f-$b"
    python3 "$tools/render-feature-recipe" "$W/features/$f" --isabelle-build "$b" --build-number $((b - 1)) -o "$r" > /dev/null
    "$RB" build --recipe "$r/recipe.yaml" --output-dir "$CH" --no-test > "$r.log" 2>&1 || { tail -20 "$r.log"; exit 1; }
  done
done
simple_recipe "$W/recipes/indirect" toy-indirect 1 isabelle-t-two 'echo x >> "$PREFIX/toy-indirect.count"'
"$RB" build --recipe "$W/recipes/indirect/recipe.yaml" --output-dir "$CH" --no-test > "$W/recipes/indirect.log" 2>&1
# s_interrupt's slow package: its post-link marks that every file is linked (t_two's post-link ran
# before it, its dependency), then waits for the SIGINT
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
python3 -I - "$NORE" <<'PY'                         # the indexing step must have seen the copied files
import json, sys
names = set(json.load(open(f"{sys.argv[1]}/noarch/repodata.json"))["packages.conda"])
assert {"isabelle-2025.2-2.conda", "isabelle-t-three-1-Isabelle2025_2_0.conda"} <= names, sorted(names)
assert not any(n.endswith("Isabelle2025_2_1.conda") for n in names), sorted(names)
PY
find "$CH" "$BAD" "$NORE" -name '*.conda' -printf '  %h/%f\n' | sed "s|$W/||" | sort

# ---------------------------------------------------------------- the harness
P="$CONDA_PKGS_DIRS"; mkdir -p "$W/out" "$W/envs"
pass=0; fail=0; failed=(); n=0; OUT=/dev/null; RC=0; ST=; STRC=0
ok()  { echo "ok       $1"; pass=$((pass + 1)); }
bad() { echo "WRONG    $1"; [ -f "${2-}" ] && sed 's/^/           /' "$2" | tail -40; fail=$((fail + 1)); failed+=("$1"); }
check() { local what=$1; shift; if "$@"; then ok "$what"; else bad "$what" "$OUT"; fi; }
c() {  # c <verb> <args...>: conda, quiet; its output (CR removed) in $OUT, its exit code in $RC
  local verb=$1; shift; n=$((n + 1)); OUT="$W/out/$n-$verb.txt"
  RC=0; "$CONDA" "$verb" -q -y "$@" > "$OUT.raw" 2>&1 || RC=$?
  tr -d '\r' < "$OUT.raw" > "$OUT"; rm -f "$OUT.raw"
}
times() { /usr/bin/grep -o -F -- "$1" "$OUT" | wc -l | tr -d ' '; }      # occurrences in conda's output
once() { [ "$(times "$1")" = 1 ]; }
never() { [ "$(times "$1")" = 0 ]; }
rc0() { [ "$RC" = 0 ]; }
userdir() { echo "$HOME/.isabelle/Isabelle2025-2-conda-$(basename "$1")"; }
registered() { [ -f "$(userdir "$1")/etc/components" ] && /usr/bin/grep -qxF "$1/share/$2" "$(userdir "$1")/etc/components"; }
history() { [ -f "$1/conda-meta/history" ]; }
installed() { compgen -G "$1/conda-meta/$2*.json" > /dev/null; }        # installed <env> <name-version-build>
status_of() {  # the checkout's tool reads the environment: the state no matter which tool the environment has
  STRC=0; ST=$(PYTHONPATH="$root" python3 -m isabelle_patch_control --isabelle-home "$1/isa" status 2>&1) || STRC=$?
}
states() {  # states <env> "<state> <feature>"...: exactly these feature lines, in this order
  status_of "$1"; shift
  local got; got=$(printf '%s\n' "$ST" | awk 'NR > 1 && $1 != "" {print $1, $2}')
  [ "$got" = "$(printf '%s\n' "$@")" ] || { echo "           status: $ST" | head -8; return 1; }
}
all_applied() { states "$1" "applied t_one" "applied t_two" "applied t_three" && [ "$STRC" = 0 ]; }
bytes() {  # bytes <env> <isabelle build> <features of the chain, bottom first> -- <applied...>
  local e=$1 b=$2; shift 2
  local args=(--isabelle "$P/isabelle-2025.2-$b")
  while [ "$1" != -- ]; do args+=(--feature "$P/isabelle-${1//_/-}-1-Isabelle2025_2_$((b - 1))"); shift; done; shift
  python3 "$tools/check-bytes" "$e/isa" "${args[@]}" --applied "$@" > "$W/out/bytes.txt" 2>&1 \
    || { sed 's/^/           /' "$W/out/bytes.txt"; return 1; }
}
chain_bytes() { bytes "$1" "$2" t_one t_two t_three -- "${@:3}"; }
hold_lock() {  # hold_lock <env> <seconds>: another isabelle-patch-control holding the tree's lock; pid in $HOLDER
  python3 -I -c 'import fcntl, sys, time; f = open(sys.argv[1], "rb"); fcntl.flock(f, fcntl.LOCK_EX); open(sys.argv[3], "w").close(); time.sleep(float(sys.argv[2]))' \
    "$1/isa/etc/ISABELLE_ID" "$2" "$W/out/locked" &
  HOLDER=$!
  while [ ! -e "$W/out/locked" ]; do sleep 0.1; done; rm -f "$W/out/locked"
}
paragraph_rule() {  # decision 9's removal/replacement rule: a `conda remove` step only under "If you are removing"
  python3 -I - "$OUT" <<'PY'
import sys
text = open(sys.argv[1]).read()
for para in text.split("isabelle-patch-control: ")[1:]:
    head = para.split("If you are removing", 1)[0]
    if "conda remove" in head:
        sys.exit(f"a conda remove step outside the removal branch: {para[:300]!r}")
PY
}
fresh() {  # fresh <name> <specs...>: a new environment; its path in $E
  E="$W/envs/$1"; shift
  c create -p "$E" "${CHANNELS[@]}" "$@"
  rc0 || { bad "creating $(basename "$E")"; return 1; }
}

# ---------------------------------------------------------------- the scenarios (plan decision 15)
s_order() {
  echo "--- post-link order and idempotence; a relinked lower feature"
  fresh order "isabelle=2025.2=1" isabelle-t-three || return 0
  check "one applied line, in chain order" once "changed (applied: t_one, t_two, t_three)"
  check "only that one" once "changed (applied:"
  check "one heap paragraph" once "The heaps shipped with the isabelle package were built from other sources"
  check "status: the chain applied, exit 0" all_applied "$E"
  check "bytes: the chain applied" chain_bytes "$E" 1 t_one t_two t_three
  check "t_two's component registered" registered "$E" isabelle-t-two
  mkdir -p "$(userdir "$E")/heaps/HOL"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-one
  check "--force-reinstall t_one: its pre-unlink undid the chain" once "t_one was undone; Isabelle sources under $E/isa are back to the original."
  check "the heap line stands under the removal label" once "If you are removing t_one: you may delete heaps/"
  check "then one applied line" once "changed (applied: t_one, t_two, t_three)"
  check "the user's heaps are still there" test -d "$(userdir "$E")/heaps/HOL"
  check "status and bytes after the relink" all_applied "$E"
  check "bytes after the relink" chain_bytes "$E" 1 t_one t_two t_three
}

s_components() {
  echo "--- component registration; re-running the direct dependents' post-link"
  fresh comp "isabelle=2025.2=1" isabelle-t-one isabelle-t-two isabelle-t-three toy-indirect || return 0
  check "registered" registered "$E" isabelle-t-two
  check "the indirect package's post-link ran once" test "$(wc -l < "$E/toy-indirect.count")" = 1
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "--force-reinstall isabelle: the user directory was deleted and t_two registered again" registered "$E" isabelle-t-two
  check "the chain re-applied by the re-run post-links" all_applied "$E"
  check "bytes" chain_bytes "$E" 1 t_one t_two t_three
  check "one applied line" once "changed (applied: t_one, t_two, t_three)"
  check "the indirect package's post-link was not re-run" test "$(wc -l < "$E/toy-indirect.count")" = 1
  c update -p "$E" "${CHANNELS[@]}" --all
  check "update --all moved isabelle to build 2" installed "$E" isabelle-2025.2-2
  check "registered after update --all" registered "$E" isabelle-t-two
  check "applied after update --all" all_applied "$E"
  check "bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
  c remove -p "$E" "${CHANNELS[@]}" toy-indirect isabelle-t-three isabelle-t-two
  check "removing t_two: its registration is gone" bash -c "! /usr/bin/grep -qF share/isabelle-t-two '$(userdir "$E")/etc/components'"
  check "the user directory is still there (isabelle was asked for)" test -d "$(userdir "$E")"
  check "t_one still applied" states "$E" "applied t_one"
}

s_conflict() {
  echo "--- CONFLICT: exactly one complete diagnostic per command that links isabelle or the chain top"
  fresh conflict "isabelle=2025.2=1" isabelle-t-one isabelle-t-two || return 0
  mkdir -p "$E/isa/src/Tools"; echo "my own file" > "$E/isa/src/Tools/t_three.ML"   # §6 (f2): conda does not track it
  local full="t_three was NOT applied: src/Tools/t_three.ML under $E/isa has content the tool does not recognise"
  local line="t_three was not applied (src/Tools/t_three.ML has unexpected content); see isabelle-patch-control status -v"
  c install -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "installing the top alone: one complete diagnostic" once "$full"
  check "and no one-line hint" never "$line"
  check "the install succeeded, history is there" bash -c "[ $RC = 0 ] && [ -f '$E/conda-meta/history' ]"
  check "status: CONFLICT at t_three, the two below applied" states "$E" "applied t_one" "applied t_two" "CONFLICT t_three"
  check "bytes below the CONFLICT" bytes "$E" 1 t_one t_two -- t_one t_two
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "--force-reinstall isabelle, CONFLICT still there: one complete diagnostic" once "$full"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-three
  check "--force-reinstall of the top: one complete diagnostic" once "$full"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-one
  check "relinking only a lower package: no complete diagnostic" never "t_three was NOT applied"
  check "but one line" once "$line"
  c update -p "$E" "${CHANNELS[@]}" --all
  check "update --all to a new isabelle build: one complete diagnostic" once "$full"
  check "state after update --all" states "$E" "applied t_one" "applied t_two" "CONFLICT t_three"
  mv "$E/isa/src/Tools/t_three.ML" "$W/out/aside.ML"
  PYTHONPATH="$root" python3 -m isabelle_patch_control --isabelle-home "$E/isa" apply > "$W/out/apply.txt" 2>&1 || true
  check "moved aside and applied: the chain applied" all_applied "$E"
  check "bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
}

s_rebuild() {
  echo "--- a new isabelle build, with and without the matching re-release"
  fresh rebuild "isabelle=2025.2=1" isabelle-t-three || return 0
  c update -p "$E" "${CHANNELS[@]}" --all
  check "update --all: isabelle build 2 and the re-released features" bash -c "compgen -G '$E/conda-meta/isabelle-2025.2-2.json' >/dev/null && compgen -G '$E/conda-meta/isabelle-t-three-1-Isabelle2025_2_1.json' >/dev/null"
  check "the chain applied, bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
  check "status" all_applied "$E"
  check "one applied line" once "changed (applied: t_one, t_two, t_three)"
  check "the heap paragraph in full" python3 -I -c "import sys; sys.path.insert(0, sys.argv[2]); from isabelle_patch_control import texts; sys.exit(open(sys.argv[1]).read().count(texts.HEAP_PARAGRAPH) != 1)" "$OUT" "$root"
  local clone="$W/envs/rebuild-clone"
  c create -p "$clone" "${CHANNELS[@]}" --clone "$E"
  check "--clone: the same state" all_applied "$clone"
  check "--clone: the same bytes" chain_bytes "$clone" 2 t_one t_two t_three
  E="$W/envs/norelease"
  c create -p "$E" "${NORELEASE[@]}" "isabelle=2025.2=1" isabelle-t-three
  rc0 || { bad "creating norelease"; return 0; }
  c update -p "$E" "${NORELEASE[@]}" --all
  check "no re-release: update --all keeps isabelle build 1" installed "$E" isabelle-2025.2-1
  c install -p "$E" "${NORELEASE[@]}" "isabelle=2025.2=2"
  check "and installing build 2 explicitly is refused by the solver" bash -c "[ $RC != 0 ] && compgen -G '$E/conda-meta/isabelle-2025.2-1.json' >/dev/null"
  c install -p "$E" "${NORELEASE[@]}" --force-reinstall isabelle
  check "--force-reinstall isabelle re-applies" all_applied "$E"
  check "bytes" chain_bytes "$E" 1 t_one t_two t_three
}

s_prune() {
  echo "--- the three pruning shapes"
  fresh prune1 "isabelle=2025.2=1" isabelle-t-one isabelle-t-two isabelle-t-three || return 0
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "(i) lower packages asked for: only the top's pre-unlink ran" bash -c "[ \$(/usr/bin/grep -o 'was undone' '$OUT' | wc -l) = 1 ]"
  check "(i) t_three undone" once "t_three was undone"
  check "(i) the two below still applied" states "$E" "applied t_one" "applied t_two"
  check "(i) bytes" bytes "$E" 1 t_one t_two t_three -- t_one t_two
  fresh prune2 "isabelle=2025.2=1" isabelle-t-three || return 0
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "(ii) only isabelle and the top asked for: three pre-unlinks, top first" python3 -I -c "import sys; t = open(sys.argv[1]).read(); i = [t.find(f'{f} was undone') for f in ('t_three', 't_two', 't_one')]; sys.exit(not (-1 < i[0] < i[1] < i[2]))" "$OUT"
  check "(ii) the tool went too" bash -c "! compgen -G '$E/conda-meta/isabelle-patch-control-*.json' >/dev/null"
  check "(ii) the tree is back at the original" chain_bytes "$E" 1
  check "(ii) no staging directory" bash -c "! compgen -G '$E/isa.staging*' >/dev/null"
  fresh prune3 "isabelle=2025.2=1" isabelle-t-three || return 0
  c remove -p "$E" "${CHANNELS[@]}" --force isabelle-t-three
  check "(iii) --force: only the top removed" bash -c "compgen -G '$E/conda-meta/isabelle-t-two-*.json' >/dev/null && compgen -G '$E/conda-meta/isabelle-patch-control-*.json' >/dev/null"
  check "(iii) its pre-unlink ran" once "t_three was undone"
  check "(iii) the two below still applied" states "$E" "applied t_one" "applied t_two"
}

s_residue() {
  echo "--- pre-unlink residue blocks"
  fresh residue1 "isabelle=2025.2=1" isabelle-t-one isabelle-t-two isabelle-t-three || return 0
  # on the line t_three changed: an edit away from every hunk is no CONFLICT (the patch still
  # reverses, decision 6) and is kept; sed -i writes a new file, not through the hard link
  sed -i 's/^C2$/my edit/' "$E/isa/src/Pure/c.ML"
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "an edited file: the residue block names it and the reason" bash -c "/usr/bin/grep -qF 't_three could not be fully undone (reason: a file has unexpected content).' '$OUT' && /usr/bin/grep -qx '  src/Pure/c.ML' '$OUT'"
  check "no Retry later" never "Retry later"
  check "the removal succeeded" rc0

  fresh residue2 "isabelle=2025.2=1" isabelle-t-three || return 0
  echo "mine" >> "$E/isa/src/Pure/t_one.ML"; echo "mine" >> "$E/isa/src/Tools/t_three.ML"
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "(iv) two residue blocks, one created file each" bash -c "[ \$(/usr/bin/grep -c 'could not be fully undone' '$OUT') = 2 ] && /usr/bin/grep -qF '  src/Tools/t_three.ML   (created by the feature)' '$OUT' && /usr/bin/grep -qF '  src/Pure/t_one.ML   (created by the feature)' '$OUT'"
  check "(iv) the removal rule holds" paragraph_rule
  local removal=$OUT
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle              # the last block's step 2
  /usr/bin/grep -F "(created by the feature)" "$removal" | awk '{print $1}' | sort -u | while read -r f; do rm -f "$E/isa/$f"; done
  check "(iv) after the last block's steps no created file is left, the tree is the original" chain_bytes "$E" 1

  fresh residue3 "isabelle=2025.2=1" isabelle-t-three || return 0
  hold_lock "$E" 100000                      # until killed: every pre-unlink waits its 60 s and gives up
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  kill "$HOLDER" 2>/dev/null || true; wait "$HOLDER" 2>/dev/null || true
  check "lock busy while pruning: a residue block per feature, reason the lock" bash -c "[ \$(/usr/bin/grep -c 'reason: another isabelle-patch-control was running' '$OUT') = 3 ]"
  check "every block names the same, highest package" bash -c "[ \$(/usr/bin/grep -cF 'isabelle-t-three=1; then conda remove isabelle-t-three' '$OUT') = 3 ]"
  check "a.ML (changed by t_one and t_two) is listed" /usr/bin/grep -qx '  src/Pure/a.ML' "$OUT"
  check "no Retry later" never "Retry later"
  c install -p "$E" "${CHANNELS[@]}" "isabelle-t-three=1"
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "after the last block's steps the tree is the original" chain_bytes "$E" 1
  check "and features.d is empty" bash -c "[ -z \"\$(ls -A '$E/share/isabelle_patch_control/features.d' 2>/dev/null)\" ]"

  fresh residue4 "isabelle=2025.2=1" isabelle-t-one isabelle-t-two isabelle-t-three || return 0
  c install -p "$E" "${BROKEN[@]}" "isabelle-patch-control=*=*_0"
  c remove -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "a tool that cannot start: the hook text speaks" once "isabelle-patch-control could not run, so t_three may still be applied to Isabelle"
  check "the removal succeeded, history is there" bash -c "[ $RC = 0 ] && [ -f '$E/conda-meta/history' ]"
  check "no Retry later" never "Retry later"
}

s_rule() {
  echo "--- decision 9's removal/replacement rule"
  fresh rule1 "isabelle=2025.2=1" isabelle-t-three || return 0
  # until killed: the post-links lock the new build's etc/ISABELLE_ID, a new file, and are not stopped
  hold_lock "$E" 100000
  c update -p "$E" "${CHANNELS[@]}" --all
  kill "$HOLDER" 2>/dev/null || true; wait "$HOLDER" 2>/dev/null || true
  check "(i) lock busy during update --all: the residue blocks came" bash -c "[ \$(/usr/bin/grep -c 'reason: another isabelle-patch-control was running' '$OUT') = 3 ]"
  check "(i) no removal step outside the removal branch" paragraph_rule
  check "(i) at the end every feature is applied" all_applied "$E"
  check "(i) bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
  fresh rule2 "isabelle=2025.2=1" isabelle-t-three || return 0
  c install -p "$E" "${BROKEN[@]}" "isabelle-patch-control=*=*_0"
  c update -p "$E" "${CHANNELS[@]}" --all
  check "(ii) from a tool that cannot start to one that can: the hook texts spoke" once "isabelle-patch-control could not run, so t_three may still be applied"
  check "(ii) no removal step outside the removal branch" paragraph_rule
  check "(ii) the new post-link applied the chain" all_applied "$E"
  check "(ii) bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
}

s_tool() {
  echo "--- no tool, and a tool that cannot start"
  fresh notool "isabelle=2025.2=1" isabelle-t-three || return 0
  c remove -p "$E" "${CHANNELS[@]}" --force isabelle-patch-control
  c install -p "$E" "${CHANNELS[@]}" --no-deps --force-reinstall isabelle-t-one
  check "no tool: the post-link says so" once "isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied."
  check "the install succeeded, history is there" bash -c "[ $RC = 0 ] && [ -f '$E/conda-meta/history' ]"
  fresh broken "isabelle=2025.2=1" isabelle-t-three || return 0
  c install -p "$E" "${BROKEN[@]}" "isabelle-patch-control=*=*_0"
  c install -p "$E" "${BROKEN[@]}" --force-reinstall isabelle-t-one
  check "a tool that cannot start: the post-link says so" once "isabelle-patch-control: the hook could not run."
  check "the install succeeded, history is there" bash -c "[ $RC = 0 ] && [ -f '$E/conda-meta/history' ]"
}

s_oldbuild() {
  echo "--- installing a feature into an environment of the old build"
  fresh oldbuild "isabelle=2025.2=0" || return 0
  c install -p "$E" "${CHANNELS[@]}" isabelle-t-three
  check "the solver moved isabelle off build 0" bash -c "! compgen -G '$E/conda-meta/isabelle-2025.2-0.json' >/dev/null"
  check "the chain applied" all_applied "$E"
  check "t_two registered by the new post-link" registered "$E" isabelle-t-two
}

s_leftovers() {
  echo "--- conda remove isabelle after a relink; stray files in features.d"
  fresh rmisa "isabelle=2025.2=1" isabelle-t-three || return 0
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  c remove -p "$E" "${CHANNELS[@]}" isabelle
  check "no isa/ left" test ! -e "$E/isa"
  fresh stray "isabelle=2025.2=1" isabelle-t-three || return 0
  touch "$E/share/isabelle_patch_control/features.d/t_one.c~"; mkdir "$E/share/isabelle_patch_control/features.d/junk"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-one
  check "*.c~ and a directory without provenance.txt are ignored" all_applied "$E"
  check "the install succeeded" rc0
}

s_interrupt() {
  echo "--- conda install interrupted (SIGINT to its process group); the two repairs of §4, then the removal"
  local route
  for route in touch create; do
    fresh "int-$route" "isabelle=2025.2=1" isabelle-t-one || continue
    n=$((n + 1)); OUT="$W/out/$n-interrupted.txt"
    setsid "$CONDA" install -q -y -p "$E" "${CHANNELS[@]}" toy-slow > "$OUT" 2>&1 &
    local pid=$! i
    for i in $(seq 1 1200); do [ -e "$E/slow.started" ] && break; sleep 0.1; done
    kill -INT -- "-$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
    check "($route) the interrupted install deleted conda-meta/history" test ! -e "$E/conda-meta/history"
    status_of "$E"
    check "($route) status prints the repair" bash -c "printf '%s' \"\$1\" | /usr/bin/grep -qF 'has no conda-meta/history: a conda command was interrupted'" _ "$ST"
    if [ "$route" = touch ]; then
      touch "$E/conda-meta/history"
      c install -p "$E" "${CHANNELS[@]}" "isabelle=2025.2=1" isabelle-t-one isabelle-t-two
    else
      c create -p "$E" "${CHANNELS[@]}" "isabelle=2025.2=1" isabelle-t-one isabelle-t-two
    fi
    check "($route) the repair succeeded" rc0
    check "($route) kept: both features applied" states "$E" "applied t_one" "applied t_two"
    check "($route) kept: bytes" bytes "$E" 1 t_one t_two -- t_one t_two
    check "($route) kept: t_two registered" registered "$E" isabelle-t-two
    check "($route) no staging directory" bash -c "! compgen -G '$E/isa.staging*' >/dev/null"
    c remove -p "$E" "${CHANNELS[@]}" isabelle-t-two
    check "($route) abandoned: t_two is gone, t_one applied" states "$E" "applied t_one"
    check "($route) abandoned: bytes" bytes "$E" 1 t_one t_two -- t_one
    check "($route) abandoned: t_two no longer registered" bash -c "! /usr/bin/grep -qF share/isabelle-t-two '$(userdir "$E")/etc/components'"
    c remove -p "$E" "${CHANNELS[@]}" --dry-run isabelle-t-one
    check "($route) removing the top later keeps isabelle (it is asked for again)" bash -c "! sed -n '/will be REMOVED/,\$p' '$OUT' | /usr/bin/grep -q '  isabelle-2025'"
  done
}

ALL=(s_order s_components s_conflict s_rebuild s_prune s_residue s_rule s_tool s_oldbuild s_leftovers s_interrupt)
scenarios=("$@"); [ ${#scenarios[@]} -gt 0 ] || scenarios=("${ALL[@]}")
for s in "${scenarios[@]}"; do "$s"; done
echo "--- $pass passed, $fail wrong (work directory: $W)"
for f in "${failed[@]}"; do echo "  wrong: $f"; done
[ "$fail" = 0 ]
