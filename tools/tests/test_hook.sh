#!/usr/bin/env bash
# Toy run of tools/hooks/reference-transaction (migration plan §6 step 1.0b): a repository with
# the chain R/pristine -> R/dev_patches and the branch R/daily, the hook installed, each rule
# exercised once from both sides.  Usage: test_hook.sh [<scratch dir>]
set -euo pipefail
hook=$(cd "$(dirname "$0")/.." && pwd)/hooks/reference-transaction
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work"; cd "$work"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
unset ISABELLE_GIT_OWNER
pass=0; fail=0
expect() {  # expect ok|refused <description> -- <command...>
  local want=$1 what=$2; shift 3
  if "$@" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
commit() { echo "$1" > "$1"; git add "$1"; git commit -q -m "$1"; }

git init -q -b R/pristine repo; cd repo
commit base
git branch R/dev_patches
git switch -q R/dev_patches; commit dev1
git branch R/daily R/pristine
git switch -q -c side R/pristine; commit side1   # a commit that is not on R/dev_patches
git switch -q R/dev_patches
cp "$hook" .git/hooks/reference-transaction; chmod +x .git/hooks/reference-transaction
dev1=$(git rev-parse R/dev_patches); side1=$(git rev-parse side); pristine=$(git rev-parse R/pristine)

echo "--- R/daily: forward only, onto R/dev_patches only"
expect refused "daily onto a commit off dev_patches"  -- git update-ref refs/heads/R/daily "$side1"
expect ok      "daily fast-forward onto dev_patches"  -- git update-ref refs/heads/R/daily "$dev1"
expect refused "daily backwards"                       -- git update-ref refs/heads/R/daily "$pristine"
commit dev2; dev2=$(git rev-parse R/dev_patches)
expect ok      "daily fast-forward again"              -- git update-ref refs/heads/R/daily "$dev2"
expect refused "daily by merge --no-ff of a side branch" -- git -c branch.R/daily.mergeOptions=--ff-only \
  -C "$(git worktree list --porcelain | head -1 | cut -c10-)" bash -c 'git switch -q R/daily && git merge --no-ff -q side'
git switch -q R/dev_patches 2>/dev/null || true
echo "         (R/daily is at $(git rev-parse --short R/daily), dev2 is $(git rev-parse --short "$dev2"))"

echo "--- release tags: immutable once created (deleting is the documented gap)"
expect ok      "create release tag"                    -- git tag -a -m v1 R/dev_patches/1 "$dev1"
expect refused "move release tag"                      -- git tag -f -a -m v1 R/dev_patches/1 "$dev2"
expect refused "move release tag by update-ref"        -- git update-ref refs/tags/R/dev_patches/1 "$dev2"
expect ok      "lightweight non-release tag"           -- git tag scratch "$dev2"
expect ok      "delete release tag (gap, covered by the rules)" -- git tag -d R/dev_patches/1

echo "--- branch creation needs ISABELLE_GIT_OWNER=1"
expect refused "git branch without the variable"       -- git branch R/light_locale "$dev1"
expect refused "worktree add -b without the variable"  -- git worktree add -q -b R/foo ../wt_foo "$dev1"
expect ok      "git branch with ISABELLE_GIT_OWNER=1"  -- env ISABELLE_GIT_OWNER=1 git branch R/light_locale "$dev1"
expect ok      "existing branch moves freely"          -- git update-ref refs/heads/R/light_locale "$dev2"
expect ok      "worktree add of an existing branch"    -- git worktree add -q ../wt_light R/light_locale

echo "--- maintenance and unrelated refs pass"
expect ok      "git pack-refs --all"                   -- git pack-refs --all
expect ok      "git gc"                                -- git gc -q
expect ok      "notes ref"                             -- git notes --ref=tested add -m tested "$dev2"
expect ok      "snapshot ref"                          -- git update-ref refs/snapshot/pre-migration "$dev2"

echo "--- $pass passed, $fail wrong (toy repository: $work/repo)"
[[ $fail == 0 ]]
