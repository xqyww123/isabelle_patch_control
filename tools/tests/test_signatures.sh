#!/usr/bin/env bash
# Toy run of check-signatures: ML files with signature sections, entries kept, added, removed,
# retyped, commented, continued over lines, with type parameters, in a new file.
# Usage: test_signatures.sh [<scratch dir>]
set -euo pipefail
tools=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work"; cd "$work"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
pass=0; fail=0
expect() {  # expect ok|refused <description> -- <command...>
  local want=$1 what=$2; shift 3
  if "$@" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
saw() { if /usr/bin/grep -q -- "$2" "$work/out"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1 (output lacks: $2)"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi; }

git init -q -b main repo; cd repo; mkdir -p src/Pure
cat > src/Pure/locale.ML <<'EOF'
signature LOCALE =
sig
  type level
  val register: string -> theory -> theory
  val activate_facts: (* a comment *) morphism option ->
    string * morphism -> Context.generic -> Context.generic
  exception Bad of string
end;

structure Locale: LOCALE = struct end;
EOF
cat > src/Pure/other.ML <<'EOF'
signature OTHER =
sig
  val x: int
end
EOF
git add -A; git commit -q -m base; base=$(git rev-parse HEAD)

# feature: one entry added to LOCALE (continued over two lines), datatypes and a type with type
# parameters, a new file
cat > src/Pure/locale.ML <<'EOF'
signature LOCALE =
sig
  type level
  datatype position_kind = Head | Body
  datatype 'a structure_state = Inherited | Structure_Of of 'a
  type ('a, 'b) table
  val register: string -> theory -> theory
  val activate_facts: morphism option -> (* comment moved *)
    string * morphism -> Context.generic -> Context.generic
  val is_light: theory ->
    string -> bool
  exception Bad of string
end;

structure Locale: LOCALE = struct end;
EOF
cat > src/Pure/new_file.ML <<'EOF'
signature NEW_FILE =
sig
  val f: int -> int
end
EOF
echo "(* body only *)" >> src/Pure/other.ML
git add -A; git commit -q -m feature; feat=$(git rev-parse HEAD)

cat > additions.txt <<'EOF'
# heads of the entries the feature adds
src/Pure/locale.ML LOCALE datatype position_kind
src/Pure/locale.ML LOCALE datatype structure_state
src/Pure/locale.ML LOCALE type table
src/Pure/locale.ML LOCALE val is_light
src/Pure/new_file.ML NEW_FILE val f
EOF
expect ok      "additions exactly as listed"                     -- "$tools/check-signatures" "$base" "$feat" additions.txt
saw "5 additions counted" "5 additions as listed"
expect ok      "the list through a pipe (read once)"            -- "$tools/check-signatures" "$base" "$feat" <(cat additions.txt)
saw "counted from that one reading" "5 additions as listed"
sed '/is_light/d' additions.txt > short.txt
expect refused "an addition that is not listed"                  -- "$tools/check-signatures" "$base" "$feat" short.txt
saw "names the unlisted head" "not listed: src/Pure/locale.ML LOCALE val is_light"
sed "s/datatype structure_state/datatype 'a structure_state/" additions.txt > params.txt
expect refused "a head written with its type parameters"         -- "$tools/check-signatures" "$base" "$feat" params.txt
saw "names the head without them" "not listed: src/Pure/locale.ML LOCALE datatype structure_state"
echo "src/Pure/other.ML OTHER val y" >> additions.txt
expect refused "a listed head that was not added"                -- "$tools/check-signatures" "$base" "$feat" additions.txt
saw "names the missing head" "listed but not added: src/Pure/other.ML OTHER val y"

# a removed entry and a retyped entry
sed -i '/exception Bad/d; s/val x: int/val x: string/' src/Pure/locale.ML src/Pure/other.ML
git commit -q -am broken; broken=$(git rev-parse HEAD)
sed -i '/other.ML/d' additions.txt
expect refused "removed and retyped entries"                     -- "$tools/check-signatures" "$base" "$broken" additions.txt
saw "reports the removed exception" "LOCALE: exception Bad of string"
saw "reports the retyped val as changed" "OTHER: val x: int"

echo "--- $pass passed, $fail wrong (toy repository: $work/repo)"
[[ $fail == 0 ]]
