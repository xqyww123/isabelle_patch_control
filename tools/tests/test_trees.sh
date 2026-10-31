#!/usr/bin/env bash
# Toy run of `isabelle-patch-control new-tree`: a bare repository plays GitHub's isabelle-patched
# (git's url.<dir>.insteadOf points the real URL at it), a shared tree <work>/contrib/R with build
# products, feature repositories next to it; every documented behaviour exercised, on a second
# machine (a clone of the feature repository) too.  Usage: test_trees.sh [<scratch dir>]
set -euo pipefail
. "$(dirname "$0")/harness.sh" "$@"
commit() { echo "$1 $RANDOM" > "$1"; git add "$1"; git commit -q -m "$1"; }
head_of() { git -C "$1" rev-parse HEAD; }
nt() { isabelle-patch-control new-tree "$@"; }

# "GitHub": R/pristine -> R/base (release R/base/1) and R/other (on R/base/1), R/daily; its default branch R/daily
git init -q --bare "$work/hub.git"; git -C "$work/hub.git" symbolic-ref HEAD refs/heads/R/daily
git init -q -b R/pristine "$work/seed"; cd "$work/seed"
mkdir -p etc src; printf '%s\n' /contrib /lib/classes /src/Tools/Demo/lib /etc/ISABELLE_IDENTIFIER > .gitignore
echo settings > etc/settings; git add -A; git commit -q -m pristine
git switch -q -c R/base; commit src/base.ML; git tag -a -m 1 R/base/1
git switch -q -c R/other; commit src/other.ML
git switch -q -c R/daily R/base; commit src/daily.ML           # daily is ahead of every base: a fresh clone's default checkout
git push -q "$work/hub.git" R/pristine R/base R/other R/daily R/base/1
base1=$(git rev-parse R/base)

# the shared tree: a clone on R/daily with the build products
git clone -q -b R/daily "$URL" "$work/contrib/R"; shared=$work/contrib/R
mkdir -p "$shared/contrib/comp" "$shared/lib/classes" "$shared/src/Tools/Demo/lib"
echo jar > "$shared/lib/classes/isabelle.jar"; echo demo > "$shared/src/Tools/Demo/lib/demo.jar"; echo comp > "$shared/contrib/comp/x"
printf R > "$shared/etc/ISABELLE_IDENTIFIER"
check "toy shared tree: status empty with the products in place" '[[ -z $(git -C "$shared" status --porcelain) ]]'

# the feature repository H, its init.sh as every feature repository has it
H=$work/contrib/H; git init -q -b main "$H"; cd "$H"; echo readme > README.md
printf '#!/usr/bin/env bash\nisabelle-patch-control new-tree "$(dirname "$0")"\n' > init.sh; git add -A; git commit -q -m init
t=$H/worktrees/R-feat; s=$H/worktrees/R-feat-stock

echo "--- new-tree --home: a new feature"
expect refused "--home with a base of another line"                  -- nt --home "$H" --base R2/base R/feat
expect refused "--home without --base"                               -- nt --home "$H" R/feat
expect refused "--home with a base not on GitHub, a prefix of the branch" -- nt --home "$H" --base R/oth R/other
check "the refusals registered nothing" '[[ ! -e $H/.gitmodules && ! -e $H/worktrees ]]'
expect ok      "--home registers R/feat on base R/base"              -- nt --home "$H" --base R/base R/feat
saw "says to push the new branch before the registration commit" "push -u origin R/feat"
check ".gitmodules: url, branch, base, ignore on the private tree; url, ignore on the stock tree" '
  [[ $(git config -f .gitmodules submodule.worktrees/R-feat.url) == "$URL" && $(git config -f .gitmodules submodule.worktrees/R-feat.branch) == R/feat
  && $(git config -f .gitmodules submodule.worktrees/R-feat.base) == R/base && $(git config -f .gitmodules submodule.worktrees/R-feat.ignore) == all
  && $(git config -f .gitmodules submodule.worktrees/R-feat-stock.url) == "$URL" && $(git config -f .gitmodules submodule.worktrees/R-feat-stock.ignore) == all
  && -z $(git config -f .gitmodules submodule.worktrees/R-feat-stock.branch) ]]'
check "private tree on the new branch R/feat at origin/R/base, without upstream" '[[ $(git -C "$t" symbolic-ref --short HEAD) == R/feat && $(head_of "$t") == "$base1" ]] && ! git -C "$t" rev-parse -q --verify "R/feat@{upstream}" >/dev/null 2>&1'
check "stock tree detached at merge-base(origin/R/base, R/feat)" '! git -C "$s" symbolic-ref -q HEAD >/dev/null && [[ $(head_of "$s") == "$base1" ]]'
saw "ready line names the base release" "release tag R/base/1"
check "both trees: identifier = directory name, no newline" 'cmp -s "$t/etc/ISABELLE_IDENTIFIER" <(printf R-feat) && cmp -s "$s/etc/ISABELLE_IDENTIFIER" <(printf R-feat-stock)'
check "contrib is the relative link ../../../R/contrib" '[[ $(readlink "$t/contrib") == ../../../R/contrib && -f $t/contrib/comp/x && $(readlink "$s/contrib") == ../../../R/contrib ]]'
check "lib/classes and Demo lib copied (real directories, new inodes)" '[[ -d $t/lib/classes && ! -L $t/lib/classes && $(stat -c %i "$t/lib/classes/isabelle.jar") != $(stat -c %i "$shared/lib/classes/isabelle.jar") && -f $t/src/Tools/Demo/lib/demo.jar && ! -L $s/src/Tools/Demo/lib ]]'
check "both trees' status empty with the products in place" '[[ -z $(git -C "$t" status --porcelain) && -z $(git -C "$s" status --porcelain) ]]'
check "H has .gitmodules and both gitlinks staged, at the trees' HEADs" '[[ $(git diff --cached --name-only --ignore-submodules=none | tr "\n" " ") == ".gitmodules worktrees/R-feat worktrees/R-feat-stock " && $(git rev-parse :worktrees/R-feat) == $(head_of "$t") && $(git rev-parse :worktrees/R-feat-stock) == "$base1" ]] && git diff --quiet -- .gitmodules'
inode=$(stat -c %i "$t/lib/classes/isabelle.jar" 2>/dev/null || echo none)
expect ok      "--home again with the same arguments"                -- nt --home "$H" --base R/base R/feat
check "--home again moved, cloned and switched nothing" '! /usr/bin/grep -q "moved\|cloned\|switched" "$work/out"'
expect refused "--home of the registered feature with another base" -- nt --home "$H" --base R/pristine R/feat
expect ok      "new-tree H (init.sh) right after: nothing to do"     -- bash "$H/init.sh"
check "the reruns kept the copied jar and moved nothing" '[[ $(stat -c %i "$t/lib/classes/isabelle.jar") == "$inode" && $(head_of "$s") == "$base1" ]] && ! /usr/bin/grep -q "moved\|cloned\|switched" "$work/out"'
cd "$t"; commit src/feat.ML; git push -q -u origin R/feat; cd "$H"
check "after the push R/feat tracks origin/R/feat" '[[ $(git -C "$t" rev-parse --abbrev-ref "R/feat@{upstream}") == origin/R/feat ]]'

echo "--- new-tree --home: a feature whose branch is on GitHub"
expect ok      "--home registers R/other (branch from GitHub)"       -- nt --home "$H" --base R/base R/other
check "private tree on R/other, upstream origin/R/other" '[[ $(git -C "$H/worktrees/R-other" symbolic-ref --short HEAD) == R/other && $(git -C "$H/worktrees/R-other" rev-parse --abbrev-ref "R/other@{upstream}") == origin/R/other ]]'
git commit -q -m "register R/feat and R/other" -- .gitmodules worktrees
check "the registration commit records the trees' HEADs; H is clean" '[[ $(git rev-parse HEAD:worktrees/R-feat) == $(head_of "$t") && $(git rev-parse HEAD:worktrees/R-feat-stock) == "$base1" && -z $(git status --porcelain) ]]'
cd "$t"; commit src/feat2.ML; unpushed=$(git rev-parse HEAD); cd "$H"
git commit -q -m "gitlink at an unpushed commit" -- worktrees/R-feat
check "a commit by path recorded the unpushed private HEAD (allowed between releases)" '[[ $(git rev-parse HEAD:worktrees/R-feat) == "$unpushed" ]]'
git submodule update -q --remote -- worktrees/R-feat    # detaches it at GitHub's tip; the unpushed commit stays on R/feat
check "the private tree is detached at origin/R/feat" '! git -C "$t" symbolic-ref -q HEAD >/dev/null && [[ $(head_of "$t") == $(git -C "$t" rev-parse origin/R/feat) ]]'
expect ok      "init.sh puts a detached private tree back on its branch" -- bash "$H/init.sh"
check "on R/feat at the unpushed commit" '[[ $(git -C "$t" symbolic-ref --short HEAD) == R/feat && $(head_of "$t") == "$unpushed" ]]'

echo "--- a second machine: a clone of H"
git clone -q "$H" "$work/contrib/H2"; H2=$work/contrib/H2; t2=$H2/worktrees/R-feat; s2=$H2/worktrees/R-feat-stock
check "the clone's tree directories are empty" '[[ -z $(ls -A "$t2") && -z $(ls -A "$s2") ]]'
expect ok      "H2's init.sh builds both features' trees (gitlink at an unpushed commit: --remote)" -- bash "$H2/init.sh"
check "H2's private tree on R/feat at GitHub's tip, upstream origin/R/feat" '[[ $(git -C "$t2" symbolic-ref --short HEAD) == R/feat && $(head_of "$t2") == $(git -C "$work/hub.git" rev-parse R/feat) && $(git -C "$t2" rev-parse --abbrev-ref "R/feat@{upstream}") == origin/R/feat ]]'
check "H2's stock trees detached at their merge bases" '[[ $(head_of "$s2") == "$base1" && $(head_of "$H2/worktrees/R-other-stock") == "$base1" ]] && ! git -C "$s2" symbolic-ref -q HEAD >/dev/null'
check "H2's trees have their products" '[[ -L $t2/contrib && -d $s2/lib/classes && $(cat "$H2/worktrees/R-other/etc/ISABELLE_IDENTIFIER") == R-other ]]'
check "H2 is clean" '[[ -z $(git -C "$H2" status --porcelain) ]]'

echo "--- the stock tree follows the base"
cd "$work/seed"; git switch -q R/base; commit src/base2.ML; git tag -a -m 2 R/base/2; git push -q "$work/hub.git" R/base R/base/2; base2=$(git rev-parse R/base)
cd "$t"; git fetch -q; git merge -q --no-edit origin/R/base; cd "$H"
expect ok      "init.sh after an unpushed merge of base release 2"   -- bash "$H/init.sh"
check "the stock tree moved to R/base/2 (merge base computed in the private tree)" '[[ $(head_of "$s") == "$base2" ]]'
saw "names the release" "release tag R/base/2"
check "R/other's stock tree stayed at R/base/1" '[[ $(head_of "$H/worktrees/R-other-stock") == "$base1" ]]'
git -C "$t" push -q
git -C "$t2" pull -q --no-rebase origin R/feat
check "on H2, after git pull origin R/feat, origin/R/base is stale" '[[ $(git -C "$t2" rev-parse origin/R/base) == "$base1" ]]'
expect ok      "H2's init.sh fetches before computing the merge base" -- bash "$H2/init.sh"
check "H2's stock tree at R/base/2" '[[ $(head_of "$s2") == "$base2" ]]'

echo "--- each feature on its own"
cd "$work/seed"; commit src/base3.ML; git tag -a -m 3 R/base/3; git push -q "$work/hub.git" R/base R/base/3; base3=$(git rev-parse R/base)
o=$H/worktrees/R-other; cd "$o"; echo conflict > src/other.ML; git commit -q -am mine; git switch -q -c side HEAD~1; echo theirs > src/other.ML; git commit -q -am theirs; git switch -q R/other
git merge -q side >/dev/null 2>&1 || true
check "R/other's private tree has a conflicted merge in progress" '[[ -f $(git -C "$o" rev-parse --absolute-git-dir)/MERGE_HEAD ]]'
cd "$t"; git fetch -q; git merge -q --no-edit origin/R/base; echo wip >> src/feat.ML; echo new > untracked.txt; cd "$H"
expect ok      "init.sh with a merge in progress in R/other and edits in R/feat's private tree" -- bash "$H/init.sh"
check "R/feat's stock tree moved to R/base/3" '[[ $(head_of "$s") == "$base3" ]]'
check "the edits in R/feat's private tree are untouched" '/usr/bin/grep -q wip "$t/src/feat.ML" && [[ -f $t/untracked.txt ]]'
git -C "$o" merge --abort; git -C "$t" checkout -q -- src/feat.ML; rm "$t/untracked.txt"
echo edit >> "$s/etc/settings"
expect ok      "a stock tree with uncommitted changes already in place is left alone" -- bash "$H/init.sh"
git -C "$t" reset -q --hard HEAD~1                       # toy repository only: back to the merge of R/base/2
expect refused "a stock tree with uncommitted changes that must move" -- bash "$H/init.sh"
saw "says why" "a stock tree is not edited"
check "the stock tree stayed; R/other was still set up" '[[ $(head_of "$s") == "$base3" ]] && /usr/bin/grep -q "ready: worktrees/R-other on R/other" "$work/out"'
git -C "$s" checkout -q -- etc/settings
expect ok      "once clean, init.sh moves it back"                   -- bash "$H/init.sh"
check "stock tree at R/base/2 again" '[[ $(head_of "$s") == "$base2" ]]'
git -C "$s" switch -q -c R/base2; printf wrong > "$t/etc/ISABELLE_IDENTIFIER"   # on a branch at its commit, as `git submodule add` leaves it when GitHub's default branch is there
expect ok      "init.sh with the stock tree on a branch at its commit and a wrong identifier" -- bash "$H/init.sh"
check "the stock tree detached at R/base/2; the identifier rewritten" '! git -C "$s" symbolic-ref -q HEAD >/dev/null && [[ $(head_of "$s") == "$base2" ]] && cmp -s "$t/etc/ISABELLE_IDENTIFIER" <(printf R-feat)'

echo "--- shapes that are refused, not repaired"
mv "$t/lib/classes" "$t/lib/classes.real"; ln -s ../../../R/lib/classes "$t/lib/classes"
expect refused "a symlinked lib/classes"                             -- nt "$H"
rm "$t/lib/classes"; mv "$t/lib/classes.real" "$t/lib/classes"
rm "$t/contrib"; ln -s /elsewhere "$t/contrib"
expect refused "a contrib link elsewhere"                            -- nt "$H"
rm "$t/contrib"
expect ok      "a missing link is installed again"                   -- nt "$H"
mv "$shared/lib/classes" "$shared/lib/classes.away"
git clone -q "$H" "$work/contrib/H3"; H3=$work/contrib/H3
expect refused "a shared tree without build products"               -- nt "$H3"
saw "names the shared tree" "$shared has no build products"
mv "$shared/lib/classes.away" "$shared/lib/classes"
rm -rf "$H3/worktrees/R-other"; mkdir -p "$H3/worktrees/R-other/x"
expect refused "a tree directory that is not empty and not a clone" -- nt "$H3"
check "the other feature was set up: its trees got the build products" '[[ -L $H3/worktrees/R-feat/contrib && -d $H3/worktrees/R-feat-stock/lib/classes ]]'
cp .gitmodules "$work/gitmodules"
git config -f .gitmodules --unset submodule.worktrees/R-other.base
expect refused "a private tree registered without base"              -- nt "$H"
cp "$work/gitmodules" .gitmodules; git config -f .gitmodules --unset submodule.worktrees/R-other.branch
expect refused "a tree under worktrees/ that is neither private nor stock" -- nt "$H"
cp "$work/gitmodules" .gitmodules; git config -f .gitmodules --remove-section submodule.worktrees/R-other-stock
expect refused "a private tree without its stock tree"                -- nt "$H"
cp "$work/gitmodules" .gitmodules
expect refused "a directory that is not a feature repository's top"  -- nt "$H/worktrees"
expect refused "--base without --home"                               -- nt --base R/base "$H"

echo "--- two merge bases"
cd "$work/seed"; git switch -q -c x R/other; commit src/x.ML; git switch -q R/base; commit src/b4.ML; b4=$(git rev-parse HEAD)
git merge -q --no-edit x; git push -q "$work/hub.git" R/base; git switch -q R/other; git merge -q --no-edit "$b4"; git push -q "$work/hub.git" R/other
git -C "$o" pull -q --no-rebase
expect refused "a feature with two merge bases with its base"       -- nt "$H"
saw "says how many" "have 2 merge bases"

echo "--- $pass passed, $fail wrong (toy trees: $work/contrib)"
[[ $fail == 0 ]]
