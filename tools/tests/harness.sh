# Sourced by the toy runs of the developer subcommands (`. harness.sh "$@"`): the scratch directory
# $work (the run's first argument, else a new one), git's environment with a toy GitHub (a bare
# repository $work/hub.git that url.<dir>.insteadOf puts in place of $URL), isabelle-patch-control
# of this checkout on PATH, and the checks expect, check and saw.
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
work=${1:-$(mktemp -d)}; rm -rf "$work"; mkdir -p "$work/contrib" "$work/home" "$work/bin"; work=$(cd "$work" && pwd -P)
URL=https://github.com/xqyww123/isabelle-patched.git
export GIT_CONFIG_GLOBAL=$work/home/gitconfig GIT_CONFIG_NOSYSTEM=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t \
  GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t HOME=$work/home PATH=$work/bin:$PATH
git config --global url."$work/hub.git".insteadOf "$URL"; git config --global protocol.file.allow always
git config --global advice.detachedHead false
printf '#!/usr/bin/env bash\nPYTHONPATH=%q exec python3 -m isabelle_patch_control "$@"\n' "$root" > "$work/bin/isabelle-patch-control"
chmod +x "$work/bin/isabelle-patch-control"
pass=0; fail=0
expect() {  # expect ok|refused <description> -- <command...>
  local want=$1 what=$2; shift 3
  if "$@" >"$work/out" 2>&1; then got=ok; else got=refused; fi
  if [[ $got == "$want" ]]; then echo "ok       $what ($got)"; pass=$((pass + 1))
  else echo "WRONG    $what: expected $want, got $got"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi
}
check() { if eval "$2"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1"; fail=$((fail + 1)); fi; }
saw() { if /usr/bin/grep -q -- "$2" "$work/out"; then echo "ok       $1"; pass=$((pass + 1)); else echo "WRONG    $1 (output lacks: $2)"; sed 's/^/           /' "$work/out"; fail=$((fail + 1)); fi; }
