#!/usr/bin/env bash
# All toy runs of tools/: each in its own scratch directory under $TMPDIR (or /tmp).
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
base=${TMPDIR:-/tmp}/isabelle-tools-tests-$$
status=0; mkdir -p "$base"
for t in test_trees test_signatures test_make_patches; do
  echo "=== $t"
  "$here/$t.sh" "$base/$t" 2>&1 | tee "$base/$t.log" | /usr/bin/grep -E '^(WRONG|---|           )'   # WRONG lines and their indented diagnostics
  rc=${PIPESTATUS[0]}
  (( rc == 0 )) || { echo "WRONG    $t exited with status $rc; its last lines ($base/$t.log):"; tail -n 3 "$base/$t.log" | sed 's/^/           /'; status=1; }
done
exit $status
