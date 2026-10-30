# isabelle-patch-control

For users and AI agents that meet `isabelle-patch-control` in a conda environment;
`isabelle-patch-control help` prints this file. More in the tool's repository
<https://github.com/xqyww123/isabelle_patch_control>: reference.md (every command and exit code,
and the main messages) and RELEASE.md (for whoever releases a feature package). Working on the tool itself? Read
develop.md there first.

## What this is

`isabelle-patch-control` applies the Isabelle *feature packages* installed in a conda environment
to that environment's Isabelle, the directory `<prefix>/isa`, reverses them when they are removed,
and reports the state of every feature. `<prefix>` is the environment's directory
(`$CONDA_PREFIX` once the environment is activated; `conda env list` shows it). The tool carries no
patches itself: each feature package (for example `isabelle-light-locale`) ships its own, and
conda runs the tool from the package's install and removal hooks. So in normal use nobody runs
`apply` or `unapply` by hand: installing, updating or removing packages does it.

Features form a chain, each built on the one below (for example `expose_foreign`,
`future_assign_interrupt`, …, `dev_patches`), numbered 1, 2, … from the bottom.
`status -v` shows each file's *level*: the number of the highest feature whose change the file
carries (0: the original sources).

## Read the state first

```
isabelle-patch-control status        # changes nothing; the exit code says whether all is applied
isabelle-patch-control status -v     # ... plus every file each feature changes, and its level
```

The first sentence names the Isabelle sources the tool checked. Then one sentence per feature, in
chain order, ``Feature `<name>` <state>…``; the last lines say what to do.

| The sentence says | Meaning |
|---|---|
| `is applied` | every file this feature changes carries its change |
| `is not applied yet` | none does |
| `is only partly applied` | some do, some do not: an interrupted run; `apply` finishes it |
| `cannot be applied` | a file was changed by something other than the installed feature packages (usually a conda command that was interrupted or rolled back); the sentence names the file |
| ``is applied, but `<feature>` below it is not`` | a feature below it is not fully applied |

`No feature packages are installed` (exit 0): there is nothing to apply, and the tool does not
check the files, so it cannot report changes that a removal left behind; see the last item of
*What to do in each situation*.

## What to do in each situation

- **conda printed `Rolling back transaction`.** A conda command that failed or was interrupted
  (Ctrl-C) took a feature package back out but left its changes in the sources, where `status`
  may not see them (it checks only the installed features). Reinstall `isabelle`:
  `conda install -p <prefix> -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle`.
  This deletes this environment's Isabelle user directory (the heaps built there, `etc/settings`,
  preferences, and components registered by hand): an AI agent asks the user before running it.
  Then run `isabelle-patch-control status`.
- **A feature `cannot be applied`.** Do what the last lines of `status` say; they give the exact
  commands for this environment. Usually that is the same reinstall; a file a feature created is
  not part of the `isabelle` package, so `status` says to delete it first. Do not edit files under
  `<prefix>/isa` by hand, and do not run `unapply`: it cannot undo a file that something else
  changed.
- **`is not applied yet` or `is only partly applied`, and nothing `cannot be applied`.**
  `isabelle-patch-control apply --dry-run` lists what would move; `isabelle-patch-control apply`
  does it. Both are idempotent.
- **A message says `Install matching versions of these packages`, or `is not the Isabelle build the
  feature packages were made for` (exit 3).** For the first, install the versions it names; for the
  second, run the `conda update` command it gives.
- **"another isabelle-patch-control run holds the lock".** Another run (possibly in another
  environment sharing the same package cache) is working; wait and retry.
- **A removal said `could not be fully undone`.** Do what that message said, right away: once the
  last feature package is gone, `isabelle-patch-control` is gone too, and nothing else will find
  those files. After a removal with mamba, micromamba or pixi (they print no message), reinstall
  `isabelle` as in the first item; the files the removed feature created stay behind, but nothing
  loads them.

## Removing, re-installing, and what conda does on its own

- The tool's messages are the paragraphs of conda's output that start with `isabelle-patch-control`.
  After installing, updating or removing packages, run `apply` only when one of them asks you to,
  or when `status` says so.
- `conda remove isabelle-light-locale` reverses the feature's changes and deletes the files it
  created. conda also removes the feature packages above it in the chain (they depend on it), and
  the tool reverses those too; and it removes every package that was installed only as a
  dependency and that nothing you asked for still needs: the feature packages below it,
  `isabelle-patch-control`, and `isabelle` itself if you never named it.
- `conda remove --force <package>` removes only that package. The tool still reverses its changes
  and those of every feature above it; those packages stay installed but can no longer be applied
  (`status` then says `Install matching versions of these packages`).
- If `isabelle` came in only as a feature package's dependency (`conda env export --from-history`
  does not list it), conda removes it, with this environment's Isabelle user directory, together
  with the last feature package. `conda install isabelle` does not change that: installing a
  package that is already installed changes nothing. `conda install --force-reinstall isabelle`
  does, but a reinstall of `isabelle` deletes this environment's Isabelle user directory.
- Every `conda install` / `conda update` of `isabelle` or of a feature package re-applies the
  installed features by itself: a new `isabelle` build re-applies every feature, and a new version
  of one feature package re-applies it and the features above it.
- When a feature cannot be applied, the tool applies none of the features above it in the chain
  until that is fixed.
- After a feature is applied or reversed, Isabelle rebuilds the heaps that were not built from
  exactly these sources on first use (HOL takes several minutes); `isabelle build -b HOL` does it
  right away.
- Both `-c` arguments can be left out only when both channels are in the global `.condarc`; a
  `.condarc` inside the environment does not apply to `conda ... -n`.

## Rules to keep

- Never edit files under `<prefix>/isa` by hand and never run `git` inside it; the tool refuses a
  tree that has a `.git`.
- Never remove `<prefix>/isa.staging` while a tool run is going on; a leftover one from a killed
  run is removed by the next `apply`, `unapply` or conda hook.
- Only conda applies and reverses features correctly; mamba 2.x, micromamba and pixi skip the
  removal step.
- The tool never builds heaps; Isabelle rebuilds them on first use. An AI agent runs
  `isabelle build -b HOL` (several minutes) only when the user asks for it.

## Commands

```
isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]               one line per feature; exit 0 when F and every feature below it (or everything) is applied
  apply    [--feature F] [--dry-run]   put the installed features' changes in place, up to F (or all)
  unapply  [--feature F] [--dry-run]   take them out again, from F upwards (or all of them)
  help                                 what to do when a feature cannot be applied, and in other situations

Not for hand use:
  apply-to      <dir> <feature dir>    one feature directory onto any directory, no lock, no provenance
  unapply-from  <dir> <feature dir>    the reverse
  conda-hook    post-link | pre-unlink <feature>     what the feature packages' hooks run
```

The tree is `--isabelle-home` or `<prefix>/isa`; the features come from `--features-dir` or the
environment's `share/isabelle_patch_control/features.d` (the prefix is `--isabelle-home`'s parent,
else the Python prefix the tool runs from). `--feature F` takes a feature name or its package name.
A tree outside any conda environment needs `--features-dir`. A command that the output gives
repeats `--isabelle-home` and `--features-dir` when you gave them. Details: reference.md.

**Exit codes** (check these, do not parse the lines): `0` the selected feature and every feature
below it applied (all of them by default), or nothing in the way of `apply`/`unapply`, or no
feature packages; `1` a feature is not (fully) applied, or one below it is not, or a file could not
be moved, or the lock is busy; `2` no Isabelle tree where expected, `git` missing or older than
2.43, or a wrong command line; `3` refused: the installed packages do not link into one chain, the
tree is not the build the packages were made for, the tree has a `.git`, a patch target is a
symbolic link, a patch file cannot be read, a name is unknown, the prefix is not a conda
environment and no `--features-dir` is given, or `--features-dir` is not a directory.

## Coming from my-better-isabelle 0.x

`my-better-isabelle` (PyPI `my-better-isabelle-prover`, 0.x) carried its patches itself and applied
them with GNU `patch`. It stays at 0.3.0 on PyPI for Isabelle2024 and for Isabelle installations
outside conda; it is not updated. The new tool exists only as the conda package
`isabelle-patch-control`, and it does **not** see patches that 0.x applied: a 0.x patch left in
`<prefix>/isa` makes a feature read `cannot be applied` (or `is applied`, when a feature package
carries the same change).

Before installing any feature package into an environment where 0.x was used:

1. If you ran `my-better-isabelle patch --category all`, reverse the dev patches first:
   `my-better-isabelle unpatch --category dev`. Never run a bare `my-better-isabelle unpatch` on
   conda's `isabelle`: the `2025.2-0` build ships with `expose_foreign` built in, and reversing it
   leaves a tree that is neither the package's nor any feature's.
2. `pip uninstall my-better-isabelle-prover`. This touches only 0.x; the new tool has a different
   distribution name.
3. Install the feature packages. The dev patches of 0.x (`register_thy`, `show_types_nv`,
   `expose_map_syn`) are now part of the feature package `qiyuan-dev-patches`, which also carries
   `skip_nitpick_examples`; `expose_foreign` is now `isabelle-expose-foreign`.

If `status` then says a feature `cannot be applied`, a 0.x patch is still in the tree: save
anything of your own under `<prefix>/isa`, then do what the last lines of `status` say (they give
the reinstall command for this environment and what the reinstall deletes).
