#!/usr/bin/env bash
# Toy run of `isabelle-patch-control check-signatures`: ML files with signature sections, entries
# kept, added, removed, retyped, commented, continued over lines, with type parameters, in a new
# file; -C naming another clone.  Usage: test_signatures.sh [<scratch dir>]
set -euo pipefail
. "$(dirname "$0")/harness.sh" "$@"
cd "$work"
cs() { isabelle-patch-control check-signatures "$@"; }

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
expect ok      "additions exactly as listed"                     -- cs "$base" "$feat" additions.txt
saw "5 additions counted" "5 additions as listed"
expect ok      "the list through a pipe (read once)"            -- cs "$base" "$feat" <(cat additions.txt)
saw "counted from that one reading" "5 additions as listed"
sed '/is_light/d' additions.txt > short.txt
expect refused "an addition that is not listed"                  -- cs "$base" "$feat" short.txt
saw "names the unlisted head" "not listed: src/Pure/locale.ML LOCALE val is_light"
sed "s/datatype structure_state/datatype 'a structure_state/" additions.txt > params.txt
expect refused "a head written with its type parameters"         -- cs "$base" "$feat" params.txt
saw "names the head without them" "not listed: src/Pure/locale.ML LOCALE datatype structure_state"
echo "src/Pure/other.ML OTHER val y" >> additions.txt
expect refused "a listed head that was not added"                -- cs "$base" "$feat" additions.txt
saw "names the missing head" "listed but not added: src/Pure/other.ML OTHER val y"

# a removed entry and a retyped entry
sed -i '/exception Bad/d; s/val x: int/val x: string/' src/Pure/locale.ML src/Pure/other.ML
git commit -q -am broken; broken=$(git rev-parse HEAD)
sed -i '/other.ML/d' additions.txt
expect refused "removed and retyped entries"                     -- cs "$base" "$broken" additions.txt
saw "reports the removed exception" "LOCALE: exception Bad of string"
saw "reports the retyped val as changed" "OTHER: val x: int"

echo "--- -C: both revisions resolved, and the files read, in that repository"
git clone -q . ../clone; cd ../clone; git reset -q --hard "$feat"     # toy clone only
printf 'signature CLONE_ONLY =\nsig\n  val g: int\nend\n' > src/Pure/clone_only.ML; git add -A; git commit -q -m "only in the clone"
cd ../repo; git reset -q --hard "$feat"
cp additions.txt more.txt; echo "src/Pure/clone_only.ML CLONE_ONLY val g" >> more.txt
expect ok      "-C the clone: HEAD is the clone's"                -- cs -C ../clone "$base" HEAD more.txt
expect refused "the same in this repository: its HEAD lacks val g" -- cs "$base" HEAD more.txt
saw "names the head" "listed but not added: src/Pure/clone_only.ML CLONE_ONLY val g"

echo "--- $pass passed, $fail wrong (toy repository: $work/repo)"
[[ $fail == 0 ]]
