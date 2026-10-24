#!/usr/bin/env bash
# Toy run of advance-daily: shared tree <work>/contrib/R on R/daily, chain R/pristine ->
# R/dev_patches, tested records as run-tree writes them.  Usage: test_advance_daily.sh [<scratch dir>]
set -euo pipefail
tools=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work/contrib"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
unset ISABELLE_GIT_OWNER
pass=0; fail=0
expect() {  # expect ok|refused <description> <stdin> -- <command...>
  local want=$1 what=$2 answer=$3; shift 4
  if "$@" <<<"$answer" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
check() { if eval "$2"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1"; fail=$((fail + 1)); fi; }
commit() { echo "$1 $RANDOM" > "$1"; git add "$1"; git commit -q -m "$1"; }
tested() { git notes --ref=tested append -m "tested 2026-10-22T00:00:00+08:00 in R-dev_patches
command: isabelle build -b $*
sessions: Pure $*" "${REV:-HEAD}"; }
shared=$work/contrib/R

git init -q -b R/pristine "$shared"; cd "$shared"
commit base
git switch -q -c R/dev_patches; git branch -q -u R/pristine; commit dev1; tested HOL
git branch R/daily R/pristine; git switch -q R/daily
cp "$tools/hooks/reference-transaction" .git/hooks/; chmod +x .git/hooks/reference-transaction
dev1=$(git rev-parse R/dev_patches)

expect refused "not confirmed: nothing changes"            "no"       -- "$tools/advance-daily" -C "$shared" R HOL
check "daily unchanged" '[[ $(git rev-parse R/daily) == $(git rev-parse R/pristine) ]]'
expect refused "session not covered"                       "notified" -- "$tools/advance-daily" -C "$shared" R HOL ZF
expect ok      "advance to the tested tip"                 "notified" -- "$tools/advance-daily" -C "$shared" R HOL
check "daily at dev1, shared tree checked out there" '[[ $(git rev-parse R/daily) == $dev1 && $(git rev-parse HEAD) == $dev1 && -f dev1 ]]'
check "prints the rebuild command, does not run it" '/usr/bin/grep -q "bin/isabelle build -b HOL" "$work/out"'
expect ok      "already there is a no-op"                  "notified" -- "$tools/advance-daily" -C "$shared" R HOL
git switch -q R/dev_patches; commit dev2; git switch -q R/daily; dev2=$(git rev-parse R/dev_patches)
expect refused "tip without a tested record"               "notified" -- "$tools/advance-daily" -C "$shared" R HOL
echo dirty > base
expect refused "shared tree with a non-empty status"       "notified" -- "$tools/advance-daily" -C "$shared" R HOL
git show HEAD:base > base
( git switch -q R/dev_patches && REV=HEAD tested FOL && git switch -q R/daily )
expect refused "record does not cover HOL"                 "notified" -- "$tools/advance-daily" -C "$shared" R HOL
expect ok      "record covers FOL"                         "notified" -- "$tools/advance-daily" -C "$shared" R FOL
check "daily at dev2" '[[ $(git rev-parse R/daily) == $dev2 ]]'
ISABELLE_GIT_OWNER=1 git branch side R/pristine; git switch -q side; commit side1; side1=$(git rev-parse HEAD); git switch -q R/daily
expect refused "--to a commit off dev_patches"             "notified" -- "$tools/advance-daily" -C "$shared" --to "$side1" R FOL
expect refused "--to a commit behind daily"                "notified" -- "$tools/advance-daily" -C "$shared" --to "$dev1" R FOL
echo '# changed' >> .git/hooks/reference-transaction
expect refused "modified hook"                             "notified" -- "$tools/advance-daily" -C "$shared" R FOL

echo "--- $pass passed, $fail wrong (toy tree: $shared)"
[[ $fail == 0 ]]
