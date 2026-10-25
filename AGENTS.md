# AGENTS.md

Orientation for an AI agent that meets `isabelle-patch-control` in a conda environment, or works
in this repository. `isabelle-patch-control help` prints this file. Human-facing detail, in the
tool's repository <https://github.com/xqyww123/isabelle_patch_control>: README.md (the user's
guide, also shipped as `share/doc/<feature package>/README.md`), reference.md, develop.md,
RELEASE.md (for whoever releases a feature package).

## What this is

`isabelle-patch-control` applies the Isabelle *feature packages* installed in a conda environment
to that environment's Isabelle, the tree `$PREFIX/isa`, reverses them when they are removed, and
reports the state of every feature. It carries no patches itself. Each feature package (for example
`isabelle-light-locale`) ships its patch files and a provenance file under
`$PREFIX/share/isabelle_patch_control/features.d/<feature>/`, and conda runs the tool from the
package's own install and removal hooks. So in normal use nobody runs `apply` or `unapply` by hand:
installing, updating or removing packages does it, and `conda install --force-reinstall isabelle`
re-applies everything that is installed.

Features form a chain, each built on the one below (today: `expose_foreign`,
`future_assign_interrupt`, `light_locale`, …, `dev_patches`). The tool links the installed
packages into that chain by their exact release tags and gives every file of the tree a *level*:
the number of the highest feature whose change the file carries. `apply` moves files up to where
the installed chain says they belong, `unapply` moves them down. Both move only the files that are
not already there, one file at a time, by renaming a finished copy into place; the patch engine is
`git apply`, run only on copies inside directories the tool creates.

## Read the state first

```
isabelle-patch-control status        # non-destructive; exit code says whether all is applied
isabelle-patch-control status -v     # ... plus every changed file and its level
```

The first line names the tree and the `features.d` root the tool read. Then one line per feature in
chain order: state, feature name, release tag, file count.

| State | Meaning |
|---|---|
| `applied` | every file this feature changes carries its change |
| `not-applied` | none does |
| `half-applied` | some do, some do not (`N files, k below`): an interrupted run; `apply` finishes it |
| `CONFLICT` | a file has content the tool recognises as no level (a hand edit, usually); the install's message or `status -v` names the file |
| `(hole below)` | this feature is applied while one below it is not fully applied (`not-applied`, `half-applied` or `CONFLICT`) |

`no feature packages installed` with exit 0 means exactly that: nothing for the tool to apply,
whatever build the tree is. The tool then does not look at the tree, so changes that a removal
could not undo (its message said `could not be fully undone`), or that mamba, micromamba or pixi
left behind, are not reported; follow that message, or README's section *Removing, re-installing,
and what conda does on its own*.

**Exit codes** (check these, do not parse the lines): `0` the selected feature and every feature
below it applied (all of them by default), or no feature packages; `1` something is `not-applied`,
`half-applied`, `CONFLICT`, or a hole, or a file could not be moved, or the lock is busy; `2` no
Isabelle tree where expected, or `git` missing or older than 2.43; `3` refused: the installed
packages do not link into one chain, the tree is not the build the packages were made for, the tree
has a `.git`, a patch target is a symbolic link, a patch file cannot be read, or a name is unknown.
`conda-hook` exits 0 whenever it wrote its own message into conda's output; when it cannot finish
(a crash, or it cannot tell which files still carry a feature's changes) it exits non-zero and the
hook's own fallback line speaks instead.

## What to do in each situation

- **`CONFLICT`.** Do not edit anything under `$PREFIX/isa` to fix it, and do not run `unapply`:
  the tool cannot move a file it does not recognise. If the unrecognised file is one the feature
  itself creates (marked `(created by the feature)` in `status -v`), move it aside and run
  `isabelle-patch-control apply`. Otherwise reinstall `isabelle`. Before that, save anything of the
  user's own under `$PREFIX/isa` and in the environment's Isabelle user directory (`isabelle getenv
  -b ISABELLE_HOME_USER`): the reinstall deletes that directory, with the heaps built in it, its
  `etc/settings` and preferences, and every component registered by hand with `isabelle components
  -u`; installed packages register their components again, the user's own settings do not come
  back. Then `conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle`,
  which replaces every file of the `isabelle` package and re-applies the installed features, and
  `isabelle-patch-control status`. If the install's message said the edit went into conda's package
  cache (an in-place edit through a hard link), delete the directory it names first. The install's
  message, when you have it, gives these same steps.
- **`half-applied` or `not-applied` without any CONFLICT.** `isabelle-patch-control apply --dry-run`
  lists what would move; `isabelle-patch-control apply` does it. Both are idempotent.
- **The chain does not link (exit 3).** The message names the package and the version it needs;
  install matching versions. If it says the tree is not the pristine build: `conda update --all -c
  https://conda.qiyuan.me -c conda-forge`.
- **"another isabelle-patch-control run holds the lock".** Another run (possibly in another
  environment sharing the same package cache) is working; wait and retry.
- **A conda command was interrupted (Ctrl-C).** `status` prints the repair while
  `conda-meta/history` is missing; README.md has the same steps.
- **`no feature packages installed` after a removal that said `could not be fully undone`.** Do
  what that message said: its steps restore the tree exactly and keep the user directory. After a
  removal with mamba, micromamba or pixi (no message), reinstall `isabelle` as in the CONFLICT case
  and delete the files the removed feature created (it listed none; `isabelle-patch-control status -v`
  cannot help once the package is gone, so look for the feature's new files in its documentation).

## Rules to keep

- Never edit files under `$PREFIX/isa` by hand and never run `git` inside it; the tool refuses a
  tree that has a `.git`.
- Never remove `$PREFIX/isa.staging` while a tool run is going on; a leftover one from a killed
  run is removed by the next run.
- Only conda applies and reverses features correctly; mamba 2.x, micromamba and pixi skip the
  removal step.
- The tool never builds anything. Heaps rebuild on first use; `isabelle build -b HOL` does it now,
  and only when asked for.
- In this repository: no `isabelle build` without the owner's word. `isabelle_patch_control/texts.py`
  holds the plan's texts and every frame a conda hook writes (a frame quotes the refusal's own
  sentence, written next to its check); readers proofread the five texts named in plan §8 and read
  the rest once after code review 1; do not reword any of them in passing. The plan
  `ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md` is the design; change the plan before changing the
  design.

## Commands

```
isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]               the state of every feature; exit 0 when F and everything below it (or all) is applied
  apply    [--feature F] [--dry-run]   move every file up to the chain top (or to F)
  unapply  [--feature F] [--dry-run]   move every file down to the bottom (or to just below F)
  apply-to      <dir> <feature dir>    directory interface: <dir> is the tree, one feature only
  unapply-from  <dir> <feature dir>    directory interface: reverse
  conda-hook    post-link              for the hooks: whole-chain apply, reported in conda's output
  conda-hook    pre-unlink <feature>   for the hooks: reverse <feature> and everything above it
  help                                 print this file
```

The tree is `--isabelle-home` or `<prefix>/isa`; the features come from `--features-dir` or the
environment's `share/isabelle_patch_control/features.d` (the prefix is `--isabelle-home`'s parent,
else the Python prefix the tool runs from). `--feature F` takes a feature name or its package name.
A tree outside any conda environment needs `--features-dir`. Details: reference.md.

## Coming from my-better-isabelle 0.x

`my-better-isabelle` (PyPI `my-better-isabelle-prover`, 0.x) carried its patches itself and applied
them with GNU `patch`. It stays at 0.3.0 on PyPI for Isabelle2024 and for Isabelle installations
outside conda; it is not updated. The new tool exists only as the conda package
`isabelle-patch-control`, and it does **not** see patches that 0.x applied: a 0.x patch left in
`$PREFIX/isa` reads as `CONFLICT` (or as `applied`, when a feature package carries the same change).

Before installing any feature package into an environment where 0.x was used:

1. If you ran `my-better-isabelle patch --category all`, reverse the dev patches first:
   `my-better-isabelle unpatch --category dev`. Never run a bare `my-better-isabelle unpatch` on
   conda's `isabelle`: the `2025.2-0` build ships with `expose_foreign` built in, and reversing it
   leaves a tree that is neither the package's nor any feature's.
2. `pip uninstall my-better-isabelle-prover`. This touches only 0.x; the new tool has a different
   distribution name.
3. Install the feature packages. The dev patches of 0.x (`register_thy`, `show_types_nv`,
   `expose_map_syn`) are now part of the feature package `qiyuan-dev-patches`, which also carries
   `skip_nitpick_examples`; `expose_foreign` and `future_assign_interrupt` are
   `isabelle-expose-foreign` and `isabelle-future-assign-interrupt`.

A tree that 0.x left in a state the new tool does not recognise is repaired by reinstalling
`isabelle`. Before that, save anything of the user's own under `$PREFIX/isa` and in the
environment's Isabelle user directory (`isabelle getenv -b ISABELLE_HOME_USER`): the reinstall
deletes that directory, with the heaps built in it, its `etc/settings` and preferences, and every
component registered by hand; the user's own settings do not come back. Then
`conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle`: the pristine
build re-applies the installed features by itself. pip users keep using 0.3.0; nothing of the new
tool is on PyPI.
