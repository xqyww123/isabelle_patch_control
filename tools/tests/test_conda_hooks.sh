#!/usr/bin/env bash
# Hook-layer tests (patch tool plan decision 15): real conda, a private HOME, CONDARC and
# CONDA_PKGS_DIRS, channels `--override-channels -c file://<toy> -c conda-forge`, the toy channels
# of toy-channel.sh.  Assertions read conda's stdout (conda deletes .messages.txt after printing it)
# and the tree's bytes (tools/check-bytes against the unpacked packages in the package cache).
#
# Usage: test_conda_hooks.sh [<scratch dir>] [<scenario>...]
#   RATTLER_BUILD  the rattler-build binary (default: rattler-build on PATH)
#   CONDA_EXE      the conda binary (default: conda on PATH)
#   HOOKS_TEST_CACHE  a directory kept between runs for conda's and rattler-build's downloads
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../.." && pwd); tools="$root/tools"
W=${1:-$(mktemp -d)}; shift || true
rm -rf "$W"; mkdir -p "$W"; W=$(cd "$W" && pwd)
CONDA=${CONDA_EXE:-conda}
cache=${HOOKS_TEST_CACHE:-$W/cache}; mkdir -p "$cache"
export HOME="$W/home" CONDARC="$W/condarc" CONDA_PKGS_DIRS="$cache/pkgs" RATTLER_CACHE_DIR="$cache/rattler" \
  CONDA_CHANNEL_PRIORITY=strict CONDA_ALWAYS_YES=true CONDA_NOTIFY_OUTDATED_CONDA=false
mkdir -p "$HOME"; : > "$CONDARC"
CH="$W/channel"; BAD="$W/channel-broken"; NORE="$W/channel-norelease"; R=Isabelle2025-2
CHANNELS=(--override-channels -c "file://$CH" -c conda-forge)
BROKEN=(--override-channels -c "file://$BAD" -c "file://$CH" -c conda-forge)   # strict priority: its tool wins
NORELEASE=(--override-channels -c "file://$NORE" -c conda-forge)              # isabelle build 2, features for build 1 only
log() { echo "    $*"; }

bash "$here/toy-channel.sh" "$W"

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
userdir() { "$1/isa/bin/isabelle" getenv -b ISABELLE_HOME_USER; }     # the stub owns the naming rule
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
paragraph_rule() {  # paragraph_rule [<file>]: decision 9's removal/replacement rule in conda's output
  # (default $OUT): a `conda remove` step only under "If you are removing", in every hook text,
  # the tool's and the `||` fallbacks' alike
  python3 -I - "${1:-$OUT}" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
before, *messages = re.split(r"isabelle-patch-control(?:: | could not run| is not installed)", text)
if "If you are removing" in before or "conda remove" in before:
    sys.exit(f"removal text before the first message: {before[-300:]!r}")
for m in messages:
    if m.count("If you are removing") > 1:
        sys.exit(f"two removal labels in one message: {m[:300]!r}")
    if "conda remove" in m.split("If you are removing", 1)[0]:
        sys.exit(f"a conda remove step outside the removal branch: {m[:300]!r}")
PY
}
refuses() { ! "$@" 2> /dev/null; }
heap_paragraph_once() {  # the whole heap paragraph exactly once in conda's output
  python3 -I -c "import sys; sys.path.insert(0, sys.argv[2]); from isabelle_patch_control import texts; sys.exit(open(sys.argv[1]).read().count(texts.HEAP_PARAGRAPH) != 1)" "$OUT" "$root"
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
  check "and one heap paragraph" heap_paragraph_once
  check "the user's heaps are still there" test -d "$(userdir "$E")/heaps/HOL"
  check "status and bytes after the relink" all_applied "$E"
  check "bytes after the relink" chain_bytes "$E" 1 t_one t_two t_three
}

s_components() {
  echo "--- component registration; re-running the direct dependents' post-link"
  fresh comp "isabelle=2025.2=1" isabelle-t-one isabelle-t-two isabelle-t-three toy-indirect || return 0
  check "registered" registered "$E" isabelle-t-two
  check "the indirect package's post-link ran once" test "$(wc -l < "$E/toy-indirect.count")" = 1
  mkdir -p "$(userdir "$E")/heaps/HOL"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "--force-reinstall isabelle: the user directory was deleted" test ! -e "$(userdir "$E")/heaps/HOL"
  check "and t_two registered again" registered "$E" isabelle-t-two
  check "the chain re-applied by the re-run post-links" all_applied "$E"
  check "bytes" chain_bytes "$E" 1 t_one t_two t_three
  check "one applied line" once "changed (applied: t_one, t_two, t_three)"
  check "the indirect package's post-link was not re-run" test "$(wc -l < "$E/toy-indirect.count")" = 1
  mkdir -p "$(userdir "$E")/heaps/HOL"
  c update -p "$E" "${CHANNELS[@]}" --all
  check "update --all moved isabelle to build 2" installed "$E" isabelle-2025.2-2
  check "update --all: the user directory was deleted" test ! -e "$(userdir "$E")/heaps/HOL"
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
  check "t_three's changed file untouched" cmp -s "$E/isa/src/Pure/c.ML" "$P/isabelle-2025.2-1/isa/src/Pure/c.ML"
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
  sed -i 's/^B5$/mine/' "$E/isa/src/Pure/b.ML"                     # a CONFLICT in the middle of the chain
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-one
  check "a CONFLICT at t_two, relinking t_one below it: t_one applied, t_three capped" \
    states "$E" "applied t_one" "CONFLICT t_two" "not-applied t_three"
  check "one line for t_two" once "t_two was not applied (src/Pure/b.ML has unexpected content); see isabelle-patch-control status -v"
}

s_rebuild() {
  echo "--- a new isabelle build, with and without the matching re-release"
  fresh rebuild "isabelle=2025.2=1" isabelle-t-three || return 0
  c update -p "$E" "${CHANNELS[@]}" --all
  check "update --all: isabelle build 2 and the re-released features" bash -c "compgen -G '$E/conda-meta/isabelle-2025.2-2.json' >/dev/null && compgen -G '$E/conda-meta/isabelle-t-three-1-Isabelle2025_2_1.json' >/dev/null"
  check "the chain applied, bytes against build 2" chain_bytes "$E" 2 t_one t_two t_three
  check "status" all_applied "$E"
  check "one applied line" once "changed (applied: t_one, t_two, t_three)"
  check "the heap paragraph in full" heap_paragraph_once
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
  check "and installing build 2 explicitly is refused by the solver" bash -c "[ $RC != 0 ] && /usr/bin/grep -q LibMambaUnsatisfiableError '$OUT' && compgen -G '$E/conda-meta/isabelle-2025.2-1.json' >/dev/null"
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
  check "the removal rule holds" paragraph_rule
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
    check "($route) the dry run lists the top for removal" bash -c "sed -n '/will be REMOVED/,\$p' '$OUT' | /usr/bin/grep -q '  isabelle-t-one-'"
    check "($route) removing the top later keeps isabelle (it is asked for again)" bash -c "! sed -n '/will be REMOVED/,\$p' '$OUT' | /usr/bin/grep -q '  isabelle-2025'"
  done
}

s_hardlink() {
  echo "--- an edit in place through the hard link into the package cache (a package cache of its own)"
  local P="$W/pkgs-hardlink"; local -x CONDA_PKGS_DIRS="$W/pkgs-hardlink"   # a failure cannot leave the shared cache edited
  fresh hl2 "isabelle=2025.2=1" isabelle-t-one || return 0
  local other=$E
  fresh hl1 "isabelle=2025.2=1" isabelle-t-one || return 0
  local cached="$P/isabelle-2025.2-1" shared="Your edit went into conda's shared package cache"
  local plain="(your other feature packages are re-applied automatically)"
  check "b.ML (t_two's) is the package cache's file in both environments" python3 -I -c \
    'import os, sys; sys.exit(not all(os.path.samefile(p, sys.argv[1]) for p in sys.argv[2:]))' \
    "$cached/isa/src/Pure/b.ML" "$E/isa/src/Pure/b.ML" "$other/isa/src/Pure/b.ML"
  python3 -I -c 'import sys; f = open(sys.argv[1], "r+b"); f.seek(len("b1\nb2\nb3\nb4\n")); f.write(b"XX")' "$E/isa/src/Pure/b.ML"
  c install -p "$E" "${CHANNELS[@]}" isabelle-t-two
  check "installing t_two over the edit: rc 0, the wording names the package cache" \
    bash -c '[ "$1" = 0 ] && /usr/bin/grep -qF "$2" "$3" && /usr/bin/grep -qF "     $4 (conda re-creates it" "$3"' _ "$RC" "$shared" "$OUT" "$cached"
  check "status: CONFLICT at t_two" states "$E" "applied t_one" "CONFLICT t_two"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "a plain --force-reinstall isabelle keeps the edit, rc 0" bash -c '[ "$1" = 0 ] && /usr/bin/grep -qx XX "$2"' _ "$RC" "$E/isa/src/Pure/b.ML"
  # conda writes isabelle's record only after the post-links: the cache wording, the directory found through conda list
  check "and still names the package cache" bash -c '/usr/bin/grep -qF "$1" "$3" && /usr/bin/grep -qF "conda list -p $2 --full-name isabelle shows" "$3"' \
    _ "$shared" "$E" "$OUT"
  "$CONDA" clean -p -y > "$W/out/hardlink-clean.txt" 2>&1 || true
  check "conda clean -p keeps the extracted directory" test -f "$cached/isa/src/Pure/b.ML"
  check "the other environment carries the edit and says nothing" /usr/bin/grep -qx XX "$other/isa/src/Pure/b.ML"
  rm -rf "$cached"                                                          # decision 9's fix
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "the directory deleted, --force-reinstall isabelle: the chain applied" states "$E" "applied t_one" "applied t_two"
  check "bytes" bytes "$E" 1 t_one t_two -- t_one t_two
  local here_env=$E; E=$other
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "the other environment reinstalled too: b.ML is the original" /usr/bin/grep -qx b5 "$E/isa/src/Pure/b.ML"
  E=$here_env
  sed -i 's/^B5$/mine/' "$E/isa/src/Pure/b.ML"                              # a new inode, the cache unpacked again
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle-t-two
  check "an edit through a new inode: the plain wording" \
    bash -c '/usr/bin/grep -qF -- "$1" "$2" && ! /usr/bin/grep -qF "$3" "$2"' _ "$plain" "$OUT" "$shared"
  c install -p "$E" "${CHANNELS[@]}" --force-reinstall isabelle
  check "its step 2 works: the chain applied" states "$E" "applied t_one" "applied t_two"
  check "bytes after step 2" bytes "$E" 1 t_one t_two -- t_one t_two
}

ALL=(s_order s_components s_conflict s_rebuild s_prune s_residue s_rule s_tool s_oldbuild s_leftovers s_interrupt s_hardlink)
scenarios=("$@"); [ ${#scenarios[@]} -gt 0 ] || scenarios=("${ALL[@]}")
# the removal rule's own positive control: a `conda remove` step outside the removal branch
OUT="$W/out/rule-control.txt"
echo "isabelle-patch-control could not run, so t_x may still be applied. Run conda remove isabelle-t-x now. If you are removing t_x, run conda remove isabelle-t-x." > "$OUT"
check "the removal rule refuses a conda remove step outside its branch" refuses paragraph_rule
for s in "${scenarios[@]}"; do "$s"; done
echo "--- $pass passed, $fail wrong (work directory: $W)"
for f in "${failed[@]}"; do echo "  wrong: $f"; done
[ "$fail" = 0 ]
