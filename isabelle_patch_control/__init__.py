"""isabelle-patch-control: applies the Isabelle feature packages installed in a conda environment
to its Isabelle tree, reverses them, and reports each feature's state.

The patch engine is `git apply`, run only on single-file copies inside directories this tool
creates; the tree itself is changed only by os.replace and os.unlink, one file at a time.
Plan: ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md (rev 6).
"""
