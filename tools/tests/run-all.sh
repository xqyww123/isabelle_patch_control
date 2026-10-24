#!/usr/bin/env bash
# All toy runs of tools/: each in its own scratch directory under $TMPDIR (or /tmp).
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
base=${TMPDIR:-/tmp}/isabelle-tools-tests-$$
status=0
for t in test_hook test_trees test_signatures test_make_patches test_advance_daily; do
  echo "=== $t"
  "$here/$t.sh" "$base/$t" 2>&1 | /usr/bin/grep -E '^(ok|WRONG|---)' | /usr/bin/grep -v '^ok' || true
  [[ ${PIPESTATUS[0]} == 0 ]] || status=1
done
exit $status
