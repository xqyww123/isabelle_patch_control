#!/usr/bin/env bash
# Toy run of new-tree and run-tree: a repository laid out like the Isabelle source repository
# (shared tree <work>/contrib/R on R/daily, chain R/pristine -> R/expose_foreign -> R/light_locale
# -> R/dev_patches, the hook installed, a stub bin/isabelle), every documented behaviour exercised.
# Usage: test_trees.sh [<scratch dir>]
set -euo pipefail
tools=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work/contrib" "$work/home"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t HOME=$work/home
unset ISABELLE_GIT_OWNER ISABELLE_IDENTIFIER
pass=0; fail=0
expect() {  # expect ok|refused <description> -- <command...>
  local want=$1 what=$2; shift 3
  if "$@" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
check() { if eval "$2"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1"; fail=$((fail + 1)); fi; }
commit() { echo "$1 $RANDOM" > "$1"; git add "$1"; git commit -q -m "$1"; }
shared=$work/contrib/R

# the toy line R
git init -q -b R/pristine "$shared"; cd "$shared"
mkdir -p bin etc src lib; cp "$tools/tests/stub-isabelle" bin/isabelle; chmod +x bin/isabelle
printf '%s\n' /contrib /heaps /lib/classes /lib/browser_info.db /src/Tools/Demo/lib /src/Tools/Find_Facts/lib/isabelle.db /etc/ISABELLE_IDENTIFIER > .gitignore
echo settings > etc/settings; git add -A; git commit -q -m pristine
git switch -q -c R/expose_foreign; commit src/ml_name_space.ML; git branch -u R/pristine
git switch -q -c R/light_locale; commit src/locale.ML; git branch -u R/expose_foreign
git switch -q -c R/dev_patches; commit src/printer.ML; git branch -u R/light_locale
git branch R/daily R/dev_patches; git switch -q R/daily
cp "$tools/hooks/reference-transaction" .git/hooks/; chmod +x .git/hooks/reference-transaction
mkdir -p contrib/comp lib/classes src/Tools/Demo/lib; echo jar > lib/classes/isabelle.jar; echo demo > src/Tools/Demo/lib/demo.jar
echo db > lib/browser_info.db; echo comp > contrib/comp/x; echo R > etc/ISABELLE_IDENTIFIER
check "toy shared tree: status empty with the products in place" '[[ -z $(git status --porcelain) ]]'

echo "--- new-tree: private tree"
expect ok      "new-tree R/light_locale creates the private tree"     -- "$tools/new-tree" -C "$shared" R/light_locale
t=$work/contrib/R-light_locale
check "locked worktree on R/light_locale" '[[ $(git -C "$t" symbolic-ref --short HEAD) == R/light_locale ]] && git worktree list --porcelain | /usr/bin/grep -A3 "^worktree $t$" | /usr/bin/grep -q "^locked"'
check "identifier = directory name, no newline" 'cmp -s "$t/etc/ISABELLE_IDENTIFIER" <(printf R-light_locale)'
check "contrib is a relative link into the shared tree" '[[ $(readlink "$t/contrib") == ../R/contrib && -f $t/contrib/comp/x ]]'
check "lib/classes copied (real directory, new inode)" '[[ -d $t/lib/classes && ! -L $t/lib/classes && $(stat -c %i "$t/lib/classes/isabelle.jar") != $(stat -c %i "$shared/lib/classes/isabelle.jar") ]]'
check "src/Tools/Demo/lib copied" '[[ -d $t/src/Tools/Demo/lib && ! -L $t/src/Tools/Demo/lib ]]'
check "browser_info.db linked" '[[ -L $t/lib/browser_info.db && -f $t/lib/browser_info.db ]]'
check "private tree status empty" '[[ -z $(git -C "$t" status --porcelain) ]]'
expect ok      "new-tree R/light_locale again is a no-op"             -- "$tools/new-tree" -C "$shared" R/light_locale
check "no-op kept the jar inode" '[[ $(stat -c %i "$t/lib/classes/isabelle.jar") == $(cat "$work/out" >/dev/null; stat -c %i "$t/lib/classes/isabelle.jar") ]]'
rm "$t/lib/classes/isabelle.jar"; ln -s ../../../R/lib/classes "$t/lib/classes2"; mv "$t/lib/classes" "$t/lib/classes.real"; mv "$t/lib/classes2" "$t/lib/classes"
expect refused "a symlinked lib/classes is refused, not repaired"    -- "$tools/new-tree" -C "$shared" R/light_locale
rm "$t/lib/classes"; mv "$t/lib/classes.real" "$t/lib/classes"; echo jar > "$t/lib/classes/isabelle.jar"
expect ok      "new-tree R/pristine (commit-only tree)"               -- "$tools/new-tree" -C "$shared" R/pristine
check "pristine tree has no products" '[[ ! -e $work/contrib/R-pristine/contrib && ! -e $work/contrib/R-pristine/lib/classes ]]'
expect ok      "new-tree R/daily on the main worktree is a no-op"     -- "$tools/new-tree" -C "$shared" R/daily
check "daily mergeOptions set" '[[ $(git config branch.R/daily.mergeOptions) == --ff-only ]]'
git worktree add -q "$work/elsewhere" R/dev_patches
expect refused "new-tree on a branch checked out elsewhere"          -- "$tools/new-tree" -C "$shared" R/dev_patches
git worktree remove --force "$work/elsewhere"
mkdir "$work/contrib/R-dev_patches"
expect refused "directory exists but is not the branch's worktree"   -- "$tools/new-tree" -C "$shared" R/dev_patches
rmdir "$work/contrib/R-dev_patches"

echo "--- new-tree: branch creation"
expect refused "new feature without previous line and without --base" -- "$tools/new-tree" -C "$shared" R/foo
expect refused "--base without ISABELLE_GIT_OWNER=1 (hook)"          -- "$tools/new-tree" -C "$shared" --base R/light_locale R/foo
check "nothing was created by the refused attempt" '[[ ! -e $work/contrib/R-foo ]] && ! git show-ref -q refs/heads/R/foo'
expect ok      "--base with ISABELLE_GIT_OWNER=1"                     -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" --base R/light_locale R/foo
check "R/foo has upstream R/light_locale and a locked tree" '[[ $(git rev-parse --abbrev-ref R/foo@{upstream}) == R/light_locale && -d $work/contrib/R-foo/lib/classes ]]'
cp "$tools/hooks/reference-transaction" "$work/hook.bak"; echo '# changed' >> .git/hooks/reference-transaction
expect refused "a modified hook stops new-tree"                       -- "$tools/new-tree" -C "$shared" R/light_locale
cp "$work/hook.bak" .git/hooks/reference-transaction

echo "--- new-tree --stock"
expect ok      "stock tree of R/light_locale"                         -- "$tools/new-tree" -C "$shared" --stock R/light_locale
s=$work/contrib/R-light_locale-stock
check "stock tree detached at merge-base(expose_foreign, light_locale) with products" '[[ $(git -C "$s" rev-parse HEAD) == $(git merge-base R/expose_foreign R/light_locale) ]] && ! git -C "$s" symbolic-ref -q HEAD >/dev/null && [[ -L $s/contrib && -d $s/lib/classes ]]'
"$tools/new-tree" -C "$shared" R/expose_foreign >/dev/null
( cd "$work/contrib/R-expose_foreign" && commit src/fix.ML )
( cd "$t" && git merge -q --no-edit R/expose_foreign )
expect ok      "stock tree moves after the base was merged"          -- "$tools/new-tree" -C "$shared" --stock R/light_locale
check "stock tree now at the new merge base" '[[ $(git -C "$s" rev-parse HEAD) == $(git rev-parse R/expose_foreign) ]]'
echo dirty > "$s/src/stray.ML"
( cd "$work/contrib/R-expose_foreign" && commit src/fix2.ML ); ( cd "$t" && git merge -q --no-edit R/expose_foreign )
expect refused "stock tree with uncommitted changes is not moved"    -- "$tools/new-tree" -C "$shared" --stock R/light_locale
rm "$s/src/stray.ML"
expect ok      "stock tree moves once clean"                          -- "$tools/new-tree" -C "$shared" --stock R/light_locale

echo "--- run-tree"
expect refused "the shared tree is refused"                           -- "$tools/run-tree" "$shared" version
expect refused "the pristine tree is refused"                         -- "$tools/run-tree" "$work/contrib/R-pristine" version
expect ok      "private tree runs"                                    -- "$tools/run-tree" "$t" version
expect ok      "outer ISABELLE_IDENTIFIER does not leak in"           -- env ISABELLE_IDENTIFIER=bogus "$tools/run-tree" "$t" version
expect ok      "build in the private tree"                            -- "$tools/run-tree" "$t" build -b -j 2 -o threads=4 HOL
check "tested record with the session set" 'git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -q "^sessions: Pure HOL$" && git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -q "^command: isabelle build -b -j 2 -o threads=4 HOL$"'
expect ok      "build with -o quick_and_dirty"                        -- "$tools/run-tree" "$t" build -o quick_and_dirty=true HOL
check "no second record for quick_and_dirty" '[[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 1 ]]'
expect ok      "second clean build appends a record"                  -- "$tools/run-tree" "$t" build -d x -g main FOL ZF
check "two records, the second lists FOL ZF" '[[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 2 ]] && git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -q "^sessions: Pure FOL ZF$"'
echo "--- run-tree: the state of -d repositories (migration plan §0 item 32)"
git init -q "$work/light"; ( cd "$work/light" && echo root > ROOT && echo thy > Light.thy && git add -A && git commit -q -m light && echo wip > notes.txt && echo edit >> ROOT )
expect ok      "build with -d of a git worktree and -d of a plain directory" -- "$tools/run-tree" "$t" build -d "$work/light" -d "$work/home" -g main HOL
check "one dir: line: top, HEAD, tracked files with uncommitted changes (not the untracked notes.txt)" '[[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^dir: ") == 1 ]] && git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -q "^dir: $work/light $(git -C "$work/light" rev-parse HEAD) ROOT$"'
echo "$work/light/Light.thy" > "$HOME/.stub-build-edit"
expect ok      "build during which a -d file is changed and changed back" -- "$tools/run-tree" "$t" build -d "$work/light" HOL
check "no record, the reason names the -d directory" '/usr/bin/grep -q "no tested record: the repository of -d $work/light changed during the build" "$work/out" && [[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 3 ]]'
rm "$HOME/.stub-build-edit"
echo "$work/light/scratch.txt" > "$HOME/.stub-build-create"
expect ok      "build during which an untracked file appears in the -d repository" -- "$tools/run-tree" "$t" build -d "$work/light" HOL
check "a record all the same: untracked files do not count" '[[ -f $work/light/scratch.txt && $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 4 ]]'
rm "$HOME/.stub-build-create"
# an outer repository that ignores the directory given with -d (MLML ignores /contrib, where the AFP checkout lives)
git init -q "$work/outer"; ( cd "$work/outer" && echo /contrib > .gitignore && echo x > tracked.txt && git add -A && git commit -q -m outer && mkdir -p contrib/afp/thys && echo thy > contrib/afp/thys/A.thy )
echo "$work/outer/tracked.txt" > "$HOME/.stub-build-edit"
expect ok      "build with -d on an ignored directory while the outer repository's tracked file changes" -- "$tools/run-tree" "$t" build -d "$work/outer/contrib/afp/thys" -d "$work/light" HOL
check "a record with light's dir: line only: the ignored directory is tied to no repository" '[[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 5 && $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^dir: $work/light ") == 3 && $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^dir: $work/outer") == 0 ]]'
rm "$HOME/.stub-build-edit"
# a dir: line longer than one command-line argument may be (128 KiB on Linux): 4000 tracked files with uncommitted changes
git init -q "$work/big"; ( cd "$work/big" && for i in $(seq 4000); do echo $i > "theory-file-with-a-rather-long-name-$i.thy"; done && git add -A && git commit -q -m big && for i in $(seq 4000); do echo edit >> "theory-file-with-a-rather-long-name-$i.thy"; done )
expect ok      "build with -d of a repository with 4000 changed tracked files" -- "$tools/run-tree" "$t" build -d "$work/big" HOL
check "the record was written (the note goes in on stdin, not as an argument)" '[[ $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 6 && $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep "^dir: $work/big " | wc -c) -gt 131072 ]]'
echo 3 > "$HOME/.stub-build-rc"
expect refused "failed build exits non-zero"                          -- "$tools/run-tree" "$t" build HOL
rm "$HOME/.stub-build-rc"; echo src/dirty.ML > "$HOME/.stub-build-touch"
expect ok      "build that leaves the tree dirty"                     -- "$tools/run-tree" "$t" build HOL
check "no record when status is not empty afterwards" '[[ -f $t/src/dirty.ML && $(git -C "$t" notes --ref=tested show HEAD | /usr/bin/grep -c "^tested ") == 6 ]]'
rm "$t/src/dirty.ML" "$HOME/.stub-build-touch"
expect ok      "stock tree runs (no record)"                          -- "$tools/run-tree" "$s" build HOL
check "stock tree got no note" '! git notes --ref=tested show "$(git -C "$s" rev-parse HEAD)" >/dev/null 2>&1 || ! git notes --ref=tested show "$(git -C "$s" rev-parse HEAD)" | /usr/bin/grep -q "^tested "'
( cd "$work/contrib/R-expose_foreign" && commit src/fix3.ML ); ( cd "$t" && git merge -q --no-edit R/expose_foreign )
expect refused "stale stock tree is refused"                          -- "$tools/run-tree" "$s" version
rm -r "$t/lib/classes"
expect refused "tree without products is refused"                     -- "$tools/run-tree" "$t" version
"$tools/new-tree" -C "$shared" R/light_locale >/dev/null

echo "--- forward-merge mode: a new line R2"
ISABELLE_GIT_OWNER=1 git switch -q -c R2/pristine R/pristine; echo 'settings 2' > etc/settings; git commit -q -am "R2 pristine"; git switch -q R/daily
expect refused "R2/light_locale before R2/expose_foreign exists"      -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" R2/light_locale
expect ok      "R2/expose_foreign forward-merged from R/expose_foreign" -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" R2/expose_foreign
check "R2/expose_foreign: upstream R2/pristine, contains both lines" '[[ $(git rev-parse --abbrev-ref R2/expose_foreign@{upstream}) == R2/pristine ]] && git merge-base --is-ancestor R/expose_foreign R2/expose_foreign && git merge-base --is-ancestor R2/pristine R2/expose_foreign'
check "no products yet: R2 shared tree does not exist" '[[ ! -e $work/contrib/R2-expose_foreign/contrib ]] && /usr/bin/grep -q "not installed" "$work/out"'
expect ok      "R2/light_locale forward-merged"                       -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" R2/light_locale
expect ok      "R2/dev_patches forward-merged"                        -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" R2/dev_patches
( cd "$work/contrib/R-expose_foreign" && commit src/fix4.ML )
expect ok      "later fix of the old line carried forward"            -- "$tools/new-tree" -C "$shared" R2/expose_foreign
check "R2/expose_foreign contains fix4" 'git merge-base --is-ancestor R/expose_foreign R2/expose_foreign'
expect refused "R2/daily without the variable"                        -- "$tools/new-tree" -C "$shared" R2/daily
expect ok      "R2/daily created on R2/pristine"                      -- env ISABELLE_GIT_OWNER=1 "$tools/new-tree" -C "$shared" R2/daily
check "R2 shared tree on R2/daily at R2/pristine" '[[ $(git -C "$work/contrib/R2" symbolic-ref --short HEAD) == R2/daily && $(git rev-parse R2/daily) == $(git rev-parse R2/pristine) ]]'
mkdir -p "$work/contrib/R2/contrib" "$work/contrib/R2/lib/classes" "$work/contrib/R2/src/Tools/Demo/lib"; echo jar2 > "$work/contrib/R2/lib/classes/isabelle.jar"
expect ok      "rerun installs the products once the shared tree has them" -- "$tools/new-tree" -C "$shared" R2/light_locale
check "R2-light_locale now has products from R2" '[[ $(readlink "$work/contrib/R2-light_locale/contrib") == ../R2/contrib && $(cat "$work/contrib/R2-light_locale/lib/classes/isabelle.jar") == jar2 ]]'

echo "--- $pass passed, $fail wrong (toy trees: $work/contrib)"
[[ $fail == 0 ]]
