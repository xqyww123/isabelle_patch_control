#!/usr/bin/env bash
# Toy run of make-patches: a chain R/pristine -> R/base -> R/feat with release tags, a package
# directory in light locale's layout, tested records as run-tree writes them; every gate from both
# sides; then check (a) for pristine against a toy hg repository and tarball.
# Usage: test_make_patches.sh [<scratch dir>]
set -euo pipefail
tools=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work"; cd "$work"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t HGUSER=t ISABELLE_GIT_OWNER=1
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
expect ok      "pristine equals hg + release files"              -- "$tools/make-patches" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
check "tag R/pristine/$node created" "git rev-parse -q --verify refs/tags/R/pristine/$node >/dev/null"
expect ok      "check (a) again with the tag in place"           -- "$tools/make-patches" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
saw "says the tag exists" "already exists"
expect refused "wrong hg id"                                     -- "$tools/make-patches" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine 0000000abcde
git switch -q -c R/wrong_pristine; echo changed >> src/Pure/b.ML; git commit -q -am oops
git branch -f R/pristine R/wrong_pristine 2>/dev/null; git switch -q R/pristine; git branch -D -q R/wrong_pristine
expect refused "a pristine that differs from hg"                 -- "$tools/make-patches" -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
git reset -q --hard "R/pristine/$node"   # toy repository only

echo "--- the feature chain"
git switch -q -c R/base; git branch -q -u R/pristine; echo "(* base fix *)" >> src/Pure/b.ML; git commit -q -am "base fix"
git tag -a -m v1 R/base/1
git switch -q -c R/feat; git branch -q -u R/base
printf 'signature A =\nsig\n  val a: int\n  val a2: string -> int\nend\n' > src/Pure/a.ML
printf 'signature NEW =\nsig\n  val n: int\nend\n' > src/Pure/new.ML; mkdir -p bin; printf '#!/bin/sh\necho tool\n' > bin/tool; chmod +x bin/tool
git rm -q etc/x; git add -A; git commit -q -m "feature"
git switch -q -c R/upper; git branch -q -u R/feat; git switch -q R/feat
mkdir -p ../pkg/tools
printf 'src/Pure/a.ML\nsrc/Pure/new.ML\nbin/tool\netc/x\n' > ../pkg/tools/patched_files.txt
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > ../pkg/tools/signature_additions.txt
printf 'Pure\nHOL\n' > ../pkg/tools/required_sessions.txt
expect refused "no tested record"                                -- "$tools/make-patches" -C . --package ../pkg feat 1
saw "gate (e) names the missing record" "no tested record"
tested HOL
expect ok      "release 1 of R/feat"                             -- "$tools/make-patches" -C . --package ../pkg feat 1
cat "$work/out"
check "four patch files, flat names" '[[ $(ls ../pkg/patches/R/*.patch | wc -l) == 4 && -f ../pkg/patches/R/src-Pure-new.ML.patch && -f ../pkg/patches/R/bin-tool.patch ]]'
check "provenance file" '/usr/bin/grep -q "^base_tag: R/base/1$" ../pkg/patches/R/provenance.txt && /usr/bin/grep -q "^base_pin: ==1=R_\*$" ../pkg/patches/R/provenance.txt'
check "tag R/feat/1 at the tip" '[[ $(git rev-parse R/feat/1^{commit}) == $(git rev-parse R/feat) ]]'
check "tree hash excludes the release files" '[[ $(/usr/bin/grep "^tree_hash: " ../pkg/patches/R/provenance.txt | cut -d" " -f2) != $(git rev-parse R/feat^{tree}) ]]'
expect refused "release 1 again (tag exists)"                    -- "$tools/make-patches" -C . --package ../pkg feat 1
expect refused "default line from a detached cwd"                -- "$tools/make-patches" -C "$work" --package ../pkg feat 2

echo "--- gates"
echo ZF >> ../pkg/tools/required_sessions.txt
expect refused "required session not covered"                    -- "$tools/make-patches" -C . --package ../pkg R/feat 2
saw "names ZF" "do not cover ZF"
printf 'Pure\nHOL\n' > ../pkg/tools/required_sessions.txt
sed -i '/bin\/tool/d' ../pkg/tools/patched_files.txt
expect refused "changed file not listed"                         -- "$tools/make-patches" -C . --package ../pkg R/feat 2
saw "names bin/tool" "changed but not listed: bin/tool"
echo bin/tool >> ../pkg/tools/patched_files.txt
sed -i '/new.ML/d' ../pkg/tools/signature_additions.txt
expect refused "signature addition not listed"                   -- "$tools/make-patches" -C . --package ../pkg R/feat 2
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > ../pkg/tools/signature_additions.txt
git switch -q R/upper; echo "(* upper *)" >> src/Pure/new.ML; git commit -q -am upper; git switch -q R/feat
git merge -q --no-ff --no-edit R/upper; tested HOL
expect refused "merge of the upper branch leaks its commit"      -- "$tools/make-patches" -C . --package ../pkg R/feat 2
saw "gate 1 names it" "gate 1"
git reset -q --hard R/feat/1   # toy repository only
git switch -q R/base; echo "(* base fix 2 *)" >> src/Pure/b.ML; git commit -q -am "base fix 2"; git switch -q R/feat
git merge -q --no-edit R/base; tested HOL
expect refused "merged an unreleased base commit"                -- "$tools/make-patches" -C . --package ../pkg R/feat 2
saw "gate 0 asks for a release of the base" "merge a release of R/base"
git tag -a -m v2 R/base/2 R/base
expect ok      "release 2 after the base released"               -- "$tools/make-patches" -C . --package ../pkg R/feat 2
saw "pinned to base 2" "base_pin: ==2=R_\*"
chmod +x src/Pure/b.ML; git commit -q -am "mode change of a base file"; tested HOL; echo src/Pure/b.ML >> ../pkg/tools/patched_files.txt
expect refused "a mode change is not released"                   -- "$tools/make-patches" -C . --package ../pkg R/feat 3
saw "names the mode change" "mode changes, renames and binary diffs are not released"
git reset -q --hard R/feat/2   # toy repository only

echo "--- $pass passed, $fail wrong (toy repository: $work/repo)"
[[ $fail == 0 ]]
