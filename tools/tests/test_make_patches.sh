#!/usr/bin/env bash
# Toy run of make-patches: a chain R/pristine -> R/base -> R/feat with release tags, a package
# directory in light locale's layout inside its own git repository (the feature repository), tested
# records as run-tree writes them; every gate from both sides; the write order with a failure
# injected after each write and the rerun completing; a package with component files (migration
# plan §0 item 32); then check (a) for pristine against a toy hg repository and tarball.
# Usage: test_make_patches.sh [<scratch dir>]
set -euo pipefail
tools=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work"; cd "$work"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t HGUSER=t ISABELLE_GIT_OWNER=1
unset MAKE_PATCHES_FAIL_AFTER
pass=0; fail=0
expect() {  # expect ok|refused <description> -- <command...>
  local want=$1 what=$2; shift 3
  if "$@" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
check() { if eval "$2"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1"; fail=$((fail + 1)); fi; }
saw() { if /usr/bin/grep -q -- "$2" "$work/out"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1 (output lacks: $2)"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi; }
tested() { git notes --ref=tested append -m "tested 2026-10-22T00:00:00+08:00 in R-feat
command: isabelle build -b $*
sessions: Pure $*" HEAD; }
tested_with_dir() {  # tested_with_dir <feature repository> <sessions...>: a record whose build used -d <repository>
  local top; top=$(cd "$1" && pwd -P); shift
  local files; files=$(git -C "$top" status --porcelain --untracked-files=all | cut -c4- | sort | tr '\n' ' ')
  git notes --ref=tested append -m "tested 2026-10-22T00:00:00+08:00 in R-feat
command: isabelle build -b -d $top $*
sessions: Pure $*
dir: $top $(git -C "$top" rev-parse HEAD)${files:+ ${files% }}" HEAD; }
new_tip() { git commit -q --allow-empty -m "$1"; }   # a new commit on the feature branch, same content
tags() { git -C "$1" tag -l "R/feat/$2" | wc -l; }
mp="$tools/make-patches"

# the toy line: hg "upstream" first, so that pristine can be checked against it
hg init hgrepo; cd hgrepo; mkdir -p Admin src/Pure etc lib/scripts
echo admin > Admin/x; echo repo > README_REPOSITORY; echo 'syntax: glob' > .hgignore
printf 'signature A =\nsig\n  val a: int\nend\n' > src/Pure/a.ML
printf 'signature B =\nsig\n  val b: int\nend\n' > src/Pure/b.ML
echo 'init_component built-in' > etc/components; echo x > etc/x; echo script > lib/scripts/getsettings
hg add -q; hg commit -q -m pristine; hg tag -q R; node=$(hg log -r "tag('R')" --template '{node|short}')
cd "$work"
mkdir -p rel/R/etc rel/R/lib/scripts
echo "$node" > rel/R/etc/ISABELLE_ID; echo R > rel/R/etc/ISABELLE_TAGS
printf 'init_component built-in\ninit_component bundled\n' > rel/R/etc/components
echo app > rel/R/lib/scripts/Isabelle_app; echo opts > rel/R/Isabelle.options
tar -czf R_linux.tar.gz -C rel R

git init -q -b R/pristine repo; cd repo
hg -R ../hgrepo archive -r "tag('R')" -t files . >/dev/null; rm -rf Admin README_REPOSITORY .hg_archival.txt .hgignore .hgtags
cp ../rel/R/etc/ISABELLE_ID ../rel/R/etc/ISABELLE_TAGS ../rel/R/etc/components etc/; cp ../rel/R/lib/scripts/Isabelle_app lib/scripts/; cp ../rel/R/Isabelle.options .
printf '/contrib\n/heaps\n' > .gitignore
git add -A; git commit -q -m pristine
cp "$tools/hooks/reference-transaction" .git/hooks/; chmod +x .git/hooks/reference-transaction

echo "--- check (a) for pristine"
expect ok      "pristine equals hg + release files"              -- "$mp" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
check "tag R/pristine/$node created" "git rev-parse -q --verify refs/tags/R/pristine/$node >/dev/null"
expect ok      "check (a) again with the tag in place"           -- "$mp" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
saw "says the tag exists" "already exists"
expect refused "wrong hg id"                                     -- "$mp" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine 0000000abcde
git switch -q -c R/wrong_pristine; echo changed >> src/Pure/b.ML; git commit -q -am oops
git branch -f R/pristine R/wrong_pristine 2>/dev/null; git switch -q R/pristine; git branch -D -q R/wrong_pristine
expect refused "a pristine that differs from hg"                 -- "$mp" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
git reset -q --hard "R/pristine/$node"   # toy repository only

echo "--- the feature chain"
git switch -q -c R/base; git branch -q -u R/pristine; echo "(* base fix *)" >> src/Pure/b.ML; git commit -q -am "base fix"
git tag -a -m v1 R/base/1
git switch -q -c R/feat; git branch -q -u R/base
printf 'signature A =\nsig\n  val a: int\n  val a2: string -> int\nend\n' > src/Pure/a.ML
printf 'signature NEW =\nsig\n  val n: int\nend\n' > src/Pure/new.ML; mkdir -p bin; printf '#!/bin/sh\necho tool\n' > bin/tool; chmod +x bin/tool
git rm -q etc/x; git add -A; git commit -q -m "feature"
git switch -q -c R/upper; git branch -q -u R/feat; git switch -q R/feat
# the feature repository: the package directory is its root
git init -q ../pkg; mkdir -p ../pkg/tools
printf 'src/Pure/a.ML\nsrc/Pure/new.ML\nbin/tool\netc/x\n' > ../pkg/tools/patched_files.txt
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > ../pkg/tools/signature_additions.txt
printf 'Pure\nHOL\n' > ../pkg/tools/required_sessions.txt
expect refused "lists not committed in the feature repository (point 7)" -- "$mp" -C . --package ../pkg feat 1
saw "says commit first" "not committed in the feature repository"
git -C ../pkg add -A; git -C ../pkg commit -q -m tools
echo '# later' >> ../pkg/tools/required_sessions.txt
expect refused "an uncommitted change to a list (point 7)"       -- "$mp" -C . --package ../pkg feat 1
saw "names the uncommitted change" "uncommitted changes in the feature repository"
printf 'Pure\nHOL\n' > ../pkg/tools/required_sessions.txt
check "refusals created no tag anywhere" '[[ $(tags . 1) == 0 && $(tags ../pkg 1) == 0 ]]'
expect refused "no tested record"                                -- "$mp" -C . --package ../pkg feat 1
saw "gate (e) names the missing record" "no tested record"
tested HOL
expect ok      "release 1 of R/feat"                             -- "$mp" -C . --package ../pkg feat 1
cat "$work/out"
check "four patch files, flat names" '[[ $(ls ../pkg/patches/R/*.patch | wc -l) == 4 && -f ../pkg/patches/R/src-Pure-new.ML.patch && -f ../pkg/patches/R/bin-tool.patch ]]'
check "provenance file" '/usr/bin/grep -q "^base_tag: R/base/1$" ../pkg/patches/R/provenance.txt && /usr/bin/grep -q "^base_pin: ==1=R_\*$" ../pkg/patches/R/provenance.txt'
check "committed in the feature repository, clean" '[[ -z $(git -C ../pkg status --porcelain) && $(git -C ../pkg ls-tree -r --name-only HEAD -- patches/R | wc -l) == 5 ]]'
check "feature repository tag R/feat/1 at its HEAD" '[[ $(git -C ../pkg rev-parse R/feat/1^{commit}) == $(git -C ../pkg rev-parse HEAD) ]]'
check "tag R/feat/1 at the tip" '[[ $(git rev-parse R/feat/1^{commit}) == $(git rev-parse R/feat) ]]'
check "tree hash excludes the release files" '[[ $(/usr/bin/grep "^tree_hash: " ../pkg/patches/R/provenance.txt | cut -d" " -f2) != $(git rev-parse R/feat^{tree}) ]]'
expect refused "release 1 again (tag exists)"                    -- "$mp" -C . --package ../pkg feat 1
expect refused "release 2 on the same tip (point 7)"             -- "$mp" -C . --package ../pkg feat 2
saw "asks for a commit first" "commit first"
expect refused "default line from a detached cwd"                -- "$mp" -C "$work" --package ../pkg feat 2

echo "--- gates"
new_tip "tip for 2"; tested HOL
echo ZF >> ../pkg/tools/required_sessions.txt; git -C ../pkg commit -q -am ZF
expect refused "required session not covered"                    -- "$mp" -C . --package ../pkg R/feat 2
saw "names ZF" "do not cover ZF"
printf 'Pure\nHOL\n' > ../pkg/tools/required_sessions.txt; git -C ../pkg commit -q -am "no ZF"
sed -i '/bin\/tool/d' ../pkg/tools/patched_files.txt; git -C ../pkg commit -q -am "drop tool"
expect refused "changed file not listed"                         -- "$mp" -C . --package ../pkg R/feat 2
saw "names bin/tool" "changed but not listed: bin/tool"
echo bin/tool >> ../pkg/tools/patched_files.txt; git -C ../pkg commit -q -am "tool back"
sed -i '/new.ML/d' ../pkg/tools/signature_additions.txt; git -C ../pkg commit -q -am "drop sig"
expect refused "signature addition not listed"                   -- "$mp" -C . --package ../pkg R/feat 2
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > ../pkg/tools/signature_additions.txt; git -C ../pkg commit -q -am "sig back"
git switch -q R/upper; echo "(* upper *)" >> src/Pure/new.ML; git commit -q -am upper; git switch -q R/feat
git merge -q --no-ff --no-edit R/upper; tested HOL
expect refused "merge of the upper branch leaks its commit"      -- "$mp" -C . --package ../pkg R/feat 2
saw "gate 1 names it" "gate 1"
git reset -q --hard R/feat/1   # toy repository only
new_tip "tip for 2 again"
git switch -q R/base; echo "(* base fix 2 *)" >> src/Pure/b.ML; git commit -q -am "base fix 2"; git switch -q R/feat
git merge -q --no-edit R/base; tested HOL
expect refused "merged an unreleased base commit"                -- "$mp" -C . --package ../pkg R/feat 2
saw "gate 0 asks for a release of the base" "merge a release of R/base"
git tag -a -m v2 R/base/2 R/base
echo unrelated > ../pkg/unrelated.txt; git -C ../pkg add unrelated.txt       # staged, not part of the release
expect ok      "release 2 after the base released"               -- "$mp" -C . --package ../pkg R/feat 2
saw "pinned to base 2" "base_pin: ==2=R_\*"
check "an unrelated staged file stays out of the release commit" '! git -C ../pkg ls-tree --name-only HEAD unrelated.txt | /usr/bin/grep -q . && git -C ../pkg status --porcelain | /usr/bin/grep -q "^A  unrelated.txt$"'
git -C ../pkg rm -q --cached unrelated.txt; rm ../pkg/unrelated.txt
chmod +x src/Pure/b.ML; git commit -q -am "mode change of a base file"; tested HOL; echo src/Pure/b.ML >> ../pkg/tools/patched_files.txt; git -C ../pkg commit -q -am "list b"
expect refused "a mode change is not released"                   -- "$mp" -C . --package ../pkg R/feat 3
saw "names the mode change" "mode changes, renames and binary diffs are not released"
check "nothing written to the package by a refused run" '[[ -z $(git -C ../pkg status --porcelain) && $(tags ../pkg 3) == 0 ]]'
git reset -q --hard R/feat/2   # toy repository only
sed -i '/src\/Pure\/b.ML/d' ../pkg/tools/patched_files.txt; git -C ../pkg commit -q -am "unlist b"

echo "--- the write order: a failure after each write, then the rerun completes (decision 16 point 8)"
new_tip "tip for 3"; tested HOL
expect refused "fail after (b): files written, not committed"    -- env MAKE_PATCHES_FAIL_AFTER=b "$mp" -C . --package ../pkg R/feat 3
check "package has the files uncommitted, no tags" '/usr/bin/grep -q "^release_tag: R/feat/3$" ../pkg/patches/R/provenance.txt && [[ -n $(git -C ../pkg status --porcelain) && $(tags ../pkg 3) == 0 && $(tags . 3) == 0 ]]'
expect ok      "rerun after (b) completes"                       -- "$mp" -C . --package ../pkg R/feat 3
check "release 3 done: both tags, feature repository clean" '[[ $(tags ../pkg 3) == 1 && $(tags . 3) == 1 && -z $(git -C ../pkg status --porcelain) ]]'
new_tip "tip for 4"; tested HOL
expect refused "fail after (c): committed, no tags"              -- env MAKE_PATCHES_FAIL_AFTER=c "$mp" -C . --package ../pkg R/feat 4
check "committed and clean, no tags" '[[ -z $(git -C ../pkg status --porcelain) && $(tags ../pkg 4) == 0 && $(tags . 4) == 0 ]]'
before=$(git -C ../pkg rev-parse HEAD)
expect ok      "rerun after (c) completes without a second commit" -- "$mp" -C . --package ../pkg R/feat 4
saw "says already committed" "already committed"
check "no new commit; tags on that commit" '[[ $(git -C ../pkg rev-parse HEAD) == $before && $(git -C ../pkg rev-parse R/feat/4^{commit}) == $before && $(tags . 4) == 1 ]]'
new_tip "tip for 5"; tested HOL
expect refused "fail after (e): feature repository tagged, Isabelle not" -- env MAKE_PATCHES_FAIL_AFTER=e "$mp" -C . --package ../pkg R/feat 5
check "feature tag exists, Isabelle tag does not" '[[ $(tags ../pkg 5) == 1 && $(tags . 5) == 0 ]]'
expect ok      "rerun after (e) completes"                       -- "$mp" -C . --package ../pkg R/feat 5
saw "reuses the feature repository's tag" "already in"
check "Isabelle tag at the tip" '[[ $(git rev-parse R/feat/5^{commit}) == $(git rev-parse R/feat) ]]'

echo "--- a package with component files (migration plan §0 item 32, plan §0 item 35)"
cpkg=$work/cpkg; git init -q "$cpkg"; mkdir -p "$cpkg/tools" "$cpkg/patches/R"
cp ../pkg/tools/patched_files.txt ../pkg/tools/signature_additions.txt ../pkg/tools/required_sessions.txt "$cpkg/tools/"
printf 'ROOT\nLight.thy\n' > "$cpkg/tools/component_files.txt"; echo 'session Light = HOL + theories Light' > "$cpkg/ROOT"; echo 'theory Light imports Main begin end' > "$cpkg/Light.thy"
echo stale > "$cpkg/patches/R/src-Pure-a.ML.patch"; echo stale > "$cpkg/patches/R/stale.patch"     # light's first-release shape: old files, no provenance
git -C "$cpkg" add -A; git -C "$cpkg" commit -q -m "component package"
new_tip "tip for 6"; tested HOL
expect refused "a record whose build did not use -d of the feature repository" -- "$mp" -C . --package "$cpkg" R/feat 6
saw "says why the record does not count" "not counted: the build did not use -d"
tested_with_dir "$cpkg" HOL
expect ok      "release 6 with a record that used -d"            -- "$mp" -C . --package "$cpkg" R/feat 6
saw "the stale file was removed" "removed stale.patch"
check "the tagged commit holds exactly the generated files" '[[ $(git -C "$cpkg" ls-tree -r --name-only R/feat/6^{commit} -- patches/R | sort | tr "\n" " ") == "patches/R/bin-tool.patch patches/R/etc-x.patch patches/R/provenance.txt patches/R/src-Pure-a.ML.patch patches/R/src-Pure-new.ML.patch " && ! -e $cpkg/patches/R/stale.patch ]]'
new_tip "tip for 7"; tested_with_dir "$cpkg" HOL
echo notes > "$cpkg/notes.md"; git -C "$cpkg" add notes.md; git -C "$cpkg" commit -q -m "unrelated"
expect ok      "an unrelated commit in the feature repository after the tested build" -- "$mp" -C . --package "$cpkg" R/feat 7
new_tip "tip for 8"; tested_with_dir "$cpkg" HOL
echo 'theory Light imports Main begin lemma True .. end' > "$cpkg/Light.thy"; git -C "$cpkg" commit -q -am "Light changed after the build"
expect refused "a component file changed and committed after the tested build" -- "$mp" -C . --package "$cpkg" R/feat 8
saw "names the difference" "differ between the build"
tested_with_dir "$cpkg" HOL
expect ok      "a new tested build of the changed component"     -- "$mp" -C . --package "$cpkg" R/feat 8
new_tip "tip for 9"
echo '(* edit *)' >> "$cpkg/ROOT"; tested_with_dir "$cpkg" HOL; echo 'session Light = HOL + theories Light' > "$cpkg/ROOT"   # built with an uncommitted ROOT, then undone
expect refused "the record shows a shipped file uncommitted during the build" -- "$mp" -C . --package "$cpkg" R/feat 9
saw "names the file" "uncommitted during the build: ROOT"
tested_with_dir "$cpkg" HOL
expect ok      "release 9 after a clean build"                   -- "$mp" -C . --package "$cpkg" R/feat 9
new_tip "tip for 10"; tested_with_dir "$cpkg" HOL
expect refused "fail after (e) on the component package"         -- env MAKE_PATCHES_FAIL_AFTER=e "$mp" -C . --package "$cpkg" R/feat 10
echo 'session Light = HOL + theories Light Extra' > "$cpkg/ROOT"; git -C "$cpkg" commit -q -am "ROOT changed between (e) and the rerun"
tested_with_dir "$cpkg" HOL
expect refused "rerun: the tagged commit has other component files" -- "$mp" -C . --package "$cpkg" R/feat 10
saw "says the version is spent" "this version number is spent: release 11"
check "no Isabelle tag 10" '[[ $(tags . 10) == 0 ]]'
new_tip "tip for 11"; tested_with_dir "$cpkg" HOL
expect ok      "release 11 instead"                              -- "$mp" -C . --package "$cpkg" R/feat 11

echo "--- $pass passed, $fail wrong (toy repository: $work/repo)"
[[ $fail == 0 ]]
