#!/usr/bin/env bash
# Toy run of `isabelle-patch-control make-patches`: a bare repository plays GitHub's isabelle-patched
# (url.<dir>.insteadOf) with R/pristine -> R/base -> R/feat and release tags; the feature repository
# H (a package directory in light locale's layout at its root, one with component files in comp/)
# registers R/feat's two trees (new-tree --home); every gate from both sides; the release commit by
# path with .gitmodules and the gitlinks, and what an outsider gets from the tag; the write order
# with a failure after each write (a held git lock file makes the next write fail; files ref
# backend) and the rerun completing (decision 16 point 8); then check (a) for pristine against a toy
# hg repository and tarball.  Usage: test_make_patches.sh [<scratch dir>]
set -euo pipefail
. "$(dirname "$0")/harness.sh" "$@"
cd "$work"; export HGUSER=t
mp() { isabelle-patch-control make-patches "$@"; }
new_tip() { git -C "$t" commit -q --allow-empty -m "$1"; }   # a new commit on the feature branch, same content
tags() { git -C "$1" tag -l "R/feat/$2" | wc -l; }
base_release() {  # base_release <version> <commands...>: a commit on R/base in the base's own clone, tagged, pushed
  local v=$1; shift
  (cd "$seed" && git switch -q R/base && eval "$*" && git commit -q -am "base fix $v" && git tag -a -m "v$v" "R/base/$v" && git push -q origin R/base "R/base/$v")
}
write_order() {  # write_order <package> <first version>: a failure after each write step, then the rerun completes
  local pkg=$1 v=$2 gd; gd=$(git -C "$t" rev-parse --absolute-git-dir)
  echo "--- the write order on $(basename "$pkg"): a failure after each write, then the rerun completes (decision 16 point 8)"
  new_tip "tip for $v"
  touch "$H/.git/index.lock"
  expect refused "fail after (b): files written, not committed"    -- mp --package "$pkg" R/feat "$v"
  saw "the failed write was git add" "git add"
  rm "$H/.git/index.lock"
  check "package has the files uncommitted, no tags" "/usr/bin/grep -q '^release_tag: R/feat/$v\$' '$pkg/patches/R/provenance.txt' && [[ -n \$(git -C '$H' status --porcelain) && \$(tags '$H' $v) == 0 && \$(tags '$t' $v) == 0 ]]"
  expect ok      "rerun after (b) completes"                       -- mp --package "$pkg" R/feat "$v"
  check "release $v done: both tags, feature repository clean" "[[ \$(tags '$H' $v) == 1 && \$(tags '$t' $v) == 1 && -z \$(git -C '$H' status --porcelain) ]]"
  v=$((v + 1)); new_tip "tip for $v"
  mkdir -p "$H/.git/refs/tags/R/feat"; touch "$H/.git/refs/tags/R/feat/$v.lock"
  expect refused "fail after (c): committed, no tags"              -- mp --package "$pkg" R/feat "$v"
  saw "the failed write was the feature repository's tag" "git tag"
  rm "$H/.git/refs/tags/R/feat/$v.lock"
  check "committed and clean, no tags" "[[ -z \$(git -C '$H' status --porcelain) && \$(tags '$H' $v) == 0 && \$(tags '$t' $v) == 0 ]]"
  local before; before=$(git -C "$H" rev-parse HEAD)
  expect ok      "rerun after (c) completes without a second commit" -- mp --package "$pkg" R/feat "$v"
  saw "says already committed" "already committed"
  check "no new commit; tags on that commit" "[[ \$(git -C '$H' rev-parse HEAD) == $before && \$(git -C '$H' rev-parse R/feat/$v^{commit}) == $before && \$(tags '$t' $v) == 1 ]]"
  v=$((v + 1)); new_tip "tip for $v"
  mkdir -p "$gd/refs/tags/R/feat"; touch "$gd/refs/tags/R/feat/$v.lock"
  expect refused "fail after (e): feature repository tagged, the private tree not" -- mp --package "$pkg" R/feat "$v"
  saw "the failed write was the private tree's tag" "git tag"
  rm "$gd/refs/tags/R/feat/$v.lock"
  check "feature tag exists, Isabelle tag does not" "[[ \$(tags '$H' $v) == 1 && \$(tags '$t' $v) == 0 ]]"
  expect ok      "rerun after (e) completes"                       -- mp --package "$pkg" R/feat "$v"
  saw "reuses the feature repository's tag" "already in"
  check "Isabelle tag at the tip" "[[ \$(git -C '$t' rev-parse R/feat/$v^{commit}) == \$(git -C '$t' rev-parse R/feat) ]]"
}

# the toy line: hg "upstream" first, so that pristine can be checked against it
hg init hgrepo; cd hgrepo; mkdir -p Admin src/Pure etc lib/scripts
echo admin > Admin/x; echo repo > README_REPOSITORY; echo 'syntax: glob' > .hgignore
printf 'signature A =\nsig\n  val a: int\nend\n' > src/Pure/a.ML
printf 'signature B =\nsig\n  val b: int\nend\n' > src/Pure/b.ML
echo 'init_component built-in' > etc/components; echo x > etc/x; echo script > lib/scripts/getsettings
printf 'crlf 1\r\ncrlf 2\r\n' > etc/crlf.txt      # a CRLF file, as the release has a few
hg add -q; hg commit -q -m pristine; hg tag -q R; node=$(hg log -r "tag('R')" --template '{node|short}')
cd "$work"
mkdir -p rel/R/etc rel/R/lib/scripts
echo "$node" > rel/R/etc/ISABELLE_ID; echo R > rel/R/etc/ISABELLE_TAGS
printf 'init_component built-in\ninit_component bundled\n' > rel/R/etc/components
echo app > rel/R/lib/scripts/Isabelle_app; echo opts > rel/R/Isabelle.options
tar -czf R_linux.tar.gz -C rel R

# "GitHub", and the clone where pristine is made and the base is developed
git init -q --bare hub.git; git -C hub.git symbolic-ref HEAD refs/heads/R/pristine
seed=$work/seed; git init -q -b R/pristine "$seed"; cd "$seed"; git remote add origin "$URL"
hg -R ../hgrepo archive -r "tag('R')" -t files . >/dev/null; rm -rf Admin README_REPOSITORY .hg_archival.txt .hgignore .hgtags
cp ../rel/R/etc/ISABELLE_ID ../rel/R/etc/ISABELLE_TAGS ../rel/R/etc/components etc/; cp ../rel/R/lib/scripts/Isabelle_app lib/scripts/; cp ../rel/R/Isabelle.options .
printf '/contrib\n/heaps\n/lib/classes\n/src/Tools/Demo/lib\n/etc/ISABELLE_IDENTIFIER\n' > .gitignore
git add -A; git commit -q -m pristine

echo "--- check (a) for pristine"
expect ok      "pristine equals hg + release files"              -- mp -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
check "tag R/pristine/$node created" "git rev-parse -q --verify refs/tags/R/pristine/$node >/dev/null"
expect ok      "check (a) again with the tag in place"           -- mp -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
saw "says the tag exists" "already exists"
expect refused "wrong hg id"                                     -- mp -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine 0000000abcde
git switch -q -c R/wrong_pristine; echo changed >> src/Pure/b.ML; git commit -q -am oops
git branch -f R/pristine R/wrong_pristine 2>/dev/null; git switch -q R/pristine; git branch -D -q R/wrong_pristine
expect refused "a pristine that differs from hg"                 -- mp -C . --hg ../hgrepo --tarball ../R_linux.tar.gz R/pristine "$node"
git reset -q --hard "R/pristine/$node"   # toy repository only

# the base and the feature, on GitHub
git switch -q -c R/base; echo "(* base fix *)" >> src/Pure/b.ML; git commit -q -am "base fix"; git tag -a -m v1 R/base/1
git switch -q -c R/feat
printf 'signature A =\nsig\n  val a: int\n  val a2: string -> int\nend\n' > src/Pure/a.ML
printf 'signature NEW =\nsig\n  val n: int\nend\n' > src/Pure/new.ML; mkdir -p bin; printf '#!/bin/sh\necho tool\n' > bin/tool; chmod +x bin/tool
printf 'crlf 1\r\ncrlf 2\r\ncrlf 3\r\n' > etc/crlf.txt; printf 'new\r\n' > etc/new_crlf.txt
git rm -q etc/x; git add -A; git commit -q -m "feature"
git push -q origin R/pristine R/base R/feat "R/pristine/$node" R/base/1; git switch -q R/base
base1=$(git rev-parse R/base)
mkdir -p "$work/contrib/R/contrib" "$work/contrib/R/lib/classes" "$work/contrib/R/src/Tools/Demo/lib"   # the shared tree's products

# the feature repository H: the package directory is its root
H=$work/contrib/H; git init -q -b main "$H"; mkdir -p "$H/tools"; cd "$H"
printf '#!/usr/bin/env bash\nisabelle-patch-control new-tree "$(dirname "$0")"\n' > init.sh; git add init.sh; git commit -q -m init
printf 'src/Pure/a.ML\nsrc/Pure/new.ML\nbin/tool\netc/x\netc/crlf.txt\netc/new_crlf.txt\n' > tools/patched_files.txt
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > tools/signature_additions.txt
printf 'Pure\nHOL\n' > tools/required_sessions.txt
t=$H/worktrees/R-feat; s=$H/worktrees/R-feat-stock

echo "--- gate 7: the feature repository and the two trees"
expect refused "a feature repository that registers no trees"   -- mp -C "$seed" --package "$H" R/feat 1
saw "says so" "registers no trees"
isabelle-patch-control new-tree --home "$H" --base R/base R/feat >/dev/null
cd "$t"
expect refused "lists not committed in the feature repository"   -- mp --package "$H" feat 1
saw "says commit first" "not committed in the feature repository"
git -C "$H" add tools; git -C "$H" commit -q -m tools -- tools     # the registration stays staged
echo '# later' >> "$H/tools/required_sessions.txt"
expect refused "an uncommitted change to a list"                 -- mp --package "$H" feat 1
saw "names the uncommitted change" "uncommitted changes in the feature repository"
printf 'Pure\nHOL\n' > "$H/tools/required_sessions.txt"
expect refused "run in the stock tree"                            -- mp -C "$s" --package "$H" R/feat 1
saw "names the private tree" "is not the private tree of R/feat"
echo x > untracked.txt
expect refused "an untracked file in the private tree"           -- mp --package "$H" feat 1
rm untracked.txt
git switch -q --detach
expect refused "the private tree off its branch"                 -- mp --package "$H" R/feat 1
git switch -q R/feat
git -C "$s" switch -q --detach origin/R/pristine
expect refused "the stock tree not at the base tag"              -- mp --package "$H" feat 1
saw "says to rerun init.sh" "rerun $H/init.sh"
bash "$H/init.sh" >/dev/null
check "refusals created no tag anywhere" '[[ $(tags "$t" 1) == 0 && $(tags "$H" 1) == 0 ]]'
tip1=$(git rev-parse R/feat)
expect ok      "release 1 of R/feat, the registration only staged" -- mp --package "$H" feat 1
cat "$work/out"
check "six patch files, flat names" '[[ $(ls "$H"/patches/R/*.patch | wc -l) == 6 && -f $H/patches/R/src-Pure-new.ML.patch && -f $H/patches/R/bin-tool.patch ]]'
check "the CRLF files' patch files keep their CRs" '[[ $(tr -cd "\r" < "$H/patches/R/etc-crlf.txt.patch" | wc -c) == 3 && $(tr -cd "\r" < "$H/patches/R/etc-new_crlf.txt.patch" | wc -c) == 1 ]]'
check "provenance file" '/usr/bin/grep -q "^base_tag: R/base/1$" "$H/patches/R/provenance.txt" && /usr/bin/grep -q "^base_pin: ==1 R_\*$" "$H/patches/R/provenance.txt"'
check "committed in the feature repository, clean" '[[ -z $(git -C "$H" status --porcelain) && $(git -C "$H" ls-tree -r --name-only HEAD -- patches/R | wc -l) == 7 ]]'
check "the release commit records the gitlinks: the tip and the base tag's commit" '[[ $(git -C "$H" rev-parse R/feat/1^{commit}:worktrees/R-feat) == "$tip1" && $(git -C "$H" rev-parse R/feat/1^{commit}:worktrees/R-feat-stock) == "$base1" ]]'
check "the release commit holds the staged registration" '[[ $(git -C "$H" show R/feat/1:.gitmodules | /usr/bin/grep -c "path = worktrees/R-feat") == 2 ]]'
check "feature repository tag R/feat/1 at its HEAD" '[[ $(git -C "$H" rev-parse R/feat/1^{commit}) == $(git -C "$H" rev-parse HEAD) ]]'
check "tag R/feat/1 at the tip, in the private tree" '[[ $(git rev-parse R/feat/1^{commit}) == "$tip1" ]]'
check "tree hash excludes the release files" '[[ $(/usr/bin/grep "^tree_hash: " "$H/patches/R/provenance.txt" | cut -d" " -f2) != $(git rev-parse R/feat^{tree}) ]]'
git push -q origin R/feat
git clone -q --recurse-submodules -b R/feat/1 "$H" "$work/outsider" 2>/dev/null
check "an outsider's clone of the tag has both trees at the release's commits" '[[ $(git -C "$work/outsider/worktrees/R-feat" rev-parse HEAD) == "$tip1" && $(git -C "$work/outsider/worktrees/R-feat-stock" rev-parse HEAD) == "$base1" ]]'
expect refused "release 1 again (tag exists)"                    -- mp --package "$H" feat 1
expect refused "release 2 on the same tip"                       -- mp --package "$H" feat 2
saw "asks for a commit first" "commit first"
expect refused "default line from a directory outside every repository" -- mp -C "$work" --package "$H" feat 2

echo "--- gates"
new_tip "tip for 2"
sed -i '/bin\/tool/d' "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "drop tool"
expect refused "changed file not listed"                         -- mp --package "$H" R/feat 2
saw "names bin/tool" "changed but not listed: bin/tool"
echo bin/tool >> "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "tool back"
sed -i '/new.ML/d' "$H/tools/signature_additions.txt"; git -C "$H" commit -q -am "drop sig"
expect refused "signature addition not listed"                   -- mp --package "$H" R/feat 2
saw "gate (d) names it" "not listed: src/Pure/new.ML NEW val n"
printf 'src/Pure/a.ML A val a2\nsrc/Pure/new.ML NEW val n\n' > "$H/tools/signature_additions.txt"; git -C "$H" commit -q -am "sig back"
(cd "$seed" && echo "(* base fix 2 *)" >> src/Pure/b.ML && git commit -q -am "base fix 2" && git push -q origin R/base)
git fetch -q; git merge -q --no-edit origin/R/base
expect refused "merged an unreleased base commit"                -- mp --package "$H" R/feat 2
saw "gate 0 asks for a release of the base" "merge a release of R/base"
(cd "$seed" && git tag -a -m v2 R/base/2 && git push -q origin R/base/2); base2=$(git -C "$seed" rev-parse R/base)
expect refused "the base released elsewhere, not fetched"        -- mp --package "$H" R/feat 2
saw "says to fetch first" "fetch first"
git fetch -q
expect refused "fetched, the stock tree still at release 1"      -- mp --package "$H" R/feat 2
saw "says to rerun init.sh" "rerun $H/init.sh"
bash "$H/init.sh" >/dev/null
echo unrelated > "$H/unrelated.txt"; git -C "$H" add unrelated.txt       # staged, not part of the release
expect ok      "release 2 after the base released"               -- mp --package "$H" R/feat 2
saw "pinned to base 2" "base_pin: ==2 R_\*"
check "the gitlinks: the tip and R/base/2's commit" '[[ $(git -C "$H" rev-parse R/feat/2^{commit}:worktrees/R-feat) == $(git rev-parse R/feat) && $(git -C "$H" rev-parse R/feat/2^{commit}:worktrees/R-feat-stock) == "$base2" ]]'
check "an unrelated staged file stays out of the release commit" '! git -C "$H" ls-tree --name-only HEAD unrelated.txt | /usr/bin/grep -q . && git -C "$H" status --porcelain | /usr/bin/grep -q "^A  unrelated.txt$"'
git -C "$H" rm -q --cached unrelated.txt; rm "$H/unrelated.txt"
git push -q origin R/feat; git -C "$work/outsider" fetch -q --tags
git -C "$work/outsider" checkout -q R/feat/2
check "an existing clone after checkout of the tag alone: the trees stay, and status does not show it (ignore = all)" '[[ $(git -C "$work/outsider/worktrees/R-feat" rev-parse HEAD) == "$tip1" && -z $(git -C "$work/outsider" status --porcelain) ]]'
git -C "$work/outsider" submodule update -q --init
check "and after git submodule update --init: at the release's commits" '[[ $(git -C "$work/outsider/worktrees/R-feat" rev-parse HEAD) == $(git rev-parse R/feat) && $(git -C "$work/outsider/worktrees/R-feat-stock" rev-parse HEAD) == "$base2" ]]'
chmod +x src/Pure/b.ML; git commit -q -am "mode change of a base file"; echo src/Pure/b.ML >> "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "list b"
expect refused "a mode change is not released"                   -- mp --package "$H" R/feat 3
saw "names the mode change" "mode changes, renames and binary diffs are not released"
check "nothing written to the package by a refused run" '[[ -z $(git -C "$H" status --porcelain) && $(tags "$H" 3) == 0 ]]'
git reset -q --hard R/feat/2   # toy repository only
sed -i '/src\/Pure\/b.ML/d' "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "unlist b"

echo "--- gate (c): the round trip through the tool's directory interface refuses what the tool cannot reproduce"
ln -s /dev/null lib/link; git add lib/link; git commit -q -m "a symbolic link"     # a target the replay copy can read: the tool installs a regular file
echo lib/link >> "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "list the link"
expect refused "a symbolic link in the feature"                  -- mp --package "$H" R/feat 3
saw "gate (c) names the forward comparison" "gate (c): forward application gives tree"
check "nothing written, no tag" '[[ -z $(git -C "$H" status --porcelain) && $(tags "$H" 3) == 0 && $(tags "$t" 3) == 0 ]]'
git reset -q --hard R/feat/2   # toy repository only
sed -i '/lib\/link/d' "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "unlist the link"
base_release 3 "printf 'head\nx1\nx2\nx3\nA\ny1\ny2\ny3\nz\nz\nz\nx1\nx2\nx3\nA\ny1\ny2\ny3\n' > etc/r.txt && git add etc/r.txt"   # a file with a repeated block, part of the base
git fetch -q; git merge -q --no-edit origin/R/base; bash "$H/init.sh" >/dev/null
sed -i '5s/A/C/' etc/r.txt; git commit -q -am "the first occurrence changed: the hunk's context occurs twice"
echo etc/r.txt >> "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "list r"
expect refused "the checklist's repeated-context case"           -- mp --package "$H" R/feat 3
saw "gate (c): the forward patch applies at the other place too, so the file fits two levels" "gate (c): the patches do not reverse cleanly"
check "nothing written, no tag" '[[ -z $(git -C "$H" status --porcelain) && $(tags "$H" 3) == 0 && $(tags "$t" 3) == 0 ]]'
git reset -q --hard R/feat/2; bash "$H/init.sh" >/dev/null   # toy repository only; the stock tree back at R/base/2
sed -i '/etc\/r.txt/d' "$H/tools/patched_files.txt"; git -C "$H" commit -q -am "unlist r"

write_order "$H" 3

echo "--- a package with component files (migration plan §0 item 32, plan §0 item 35)"
cpkg=$H/comp; mkdir -p "$cpkg/tools" "$cpkg/patches/R"
cp "$H"/tools/patched_files.txt "$H"/tools/signature_additions.txt "$H"/tools/required_sessions.txt "$cpkg/tools/"
printf 'ROOT\nLight.thy\n' > "$cpkg/tools/component_files.txt"; echo 'session Light = HOL + theories Light' > "$cpkg/ROOT"; echo 'theory Light imports Main begin end' > "$cpkg/Light.thy"
echo stale > "$cpkg/patches/R/src-Pure-a.ML.patch"; echo stale > "$cpkg/patches/R/stale.patch"     # light's first-release shape: old files, no provenance
git -C "$H" add comp; git -C "$H" commit -q -m "component package"
write_order "$cpkg" 6     # release 6 is light's first-release shape: the tracked stale.patch goes
check "the tagged commit holds exactly the generated files" '[[ $(git -C "$H" ls-tree -r --name-only R/feat/6^{commit} -- comp/patches/R | sort | tr "\n" " ") == "comp/patches/R/bin-tool.patch comp/patches/R/etc-crlf.txt.patch comp/patches/R/etc-new_crlf.txt.patch comp/patches/R/etc-x.patch comp/patches/R/provenance.txt comp/patches/R/src-Pure-a.ML.patch comp/patches/R/src-Pure-new.ML.patch " && ! -e $cpkg/patches/R/stale.patch ]]'
new_tip "tip for 9"
echo notes > "$H/notes.md"; git -C "$H" add notes.md; git -C "$H" commit -q -m "unrelated"
expect ok      "an unrelated commit in the feature repository"   -- mp --package "$cpkg" R/feat 9
new_tip "tip for 10"
printf '#!/bin/sh\nflag=%s/commit-root-once\nif [ -f "$flag" ]; then rm "$flag"; echo "(* by the hook *)" >> comp/ROOT; git commit -q -am "ROOT changed between the gates and the commit"; fi\n' "$work" > "$H/.git/hooks/post-commit"
chmod +x "$H/.git/hooks/post-commit"; touch "$work/commit-root-once"
expect refused "a component file committed between the gates and write step (c)" -- mp --package "$cpkg" R/feat 10
saw "names the component files" "(component files)"
check "no tag anywhere" '[[ $(tags "$H" 10) == 0 && $(tags "$t" 10) == 0 && ! -e $work/commit-root-once ]]'
rm "$H/.git/hooks/post-commit"
expect ok      "release 10 of what was committed"                -- mp --package "$cpkg" R/feat 10
new_tip "tip for 11"; gd=$(git rev-parse --absolute-git-dir)
mkdir -p "$gd/refs/tags/R/feat"; touch "$gd/refs/tags/R/feat/11.lock"
expect refused "fail after (e) on the component package"         -- mp --package "$cpkg" R/feat 11
rm "$gd/refs/tags/R/feat/11.lock"
echo 'session Light = HOL + theories Light Extra' > "$cpkg/ROOT"; git -C "$H" commit -q -am "ROOT changed between (e) and the rerun"
expect refused "rerun: the tagged commit has other component files" -- mp --package "$cpkg" R/feat 11
saw "says the version is spent" "this version number is spent: release 12"
check "no Isabelle tag 11" '[[ $(tags "$t" 11) == 0 ]]'
new_tip "tip for 12"
expect ok      "release 12 instead"                              -- mp --package "$cpkg" R/feat 12
new_tip "tip for 13"; touch "$gd/refs/tags/R/feat/13.lock"
expect refused "fail after (e) again"                            -- mp --package "$cpkg" R/feat 13
rm "$gd/refs/tags/R/feat/13.lock"; new_tip "a commit between (e) and the rerun"
expect refused "rerun with another tip: the tagged commit has another gitlink" -- mp --package "$cpkg" R/feat 13
saw "names the gitlink" "worktrees/R-feat (gitlink)"

echo "--- $pass passed, $fail wrong (toy repository: $work)"
[[ $fail == 0 ]]
