# Command reference

```
isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>
```

The same entry point is `python -m isabelle_patch_control`; the hooks of the feature packages call
it that way (`"$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook …`).

## Requirements

- A conda environment with the `isabelle` package (the tree is `$PREFIX/isa`). Isabelle
  installations outside conda are not supported; the directory interface and `--features-dir` exist
  for scripts, not for them.
- `git` 2.43 or newer, found at `<prefix>/bin/git` first (`<prefix>\Library\bin\git.exe` on
  Windows), then on `PATH`. The conda package depends on it. Python 3.12 or newer.
- Only conda runs the removal hook. mamba 2.x, micromamba and pixi do not.

## Where the tree and the features come from

A prefix `P` decides both. In `conda-hook`, `P` is `$PREFIX`. Otherwise `P` is the parent of
`--isabelle-home DIR` when given, else the Python prefix the tool runs from (`sys.prefix`). The tree
is `--isabelle-home DIR`, else `P/isa`; it must have `etc/ISABELLE_IDENTIFIER` and
`etc/ISABELLE_ID` (exit 2 otherwise). The features come from `--features-dir DIR` (must exist,
exit 3 otherwise); without it, from `P/share/isabelle_patch_control/features.d`, but only when
`P/conda-meta` is a directory, that is when `P` is a conda environment: if `features.d` does not
exist there, no feature package is installed. A `P` that is not a conda environment and no
`--features-dir` is exit 3 with a message asking for `--features-dir`. So the tree and the features
can never come from two different environments, and the tool of one environment can read another
environment's state with `--isabelle-home <that prefix>/isa`.

Of each feature directory the tool reads `provenance.txt` and `*.patch` only. Conda's `*.c~`
leftovers, editor files and subdirectories without a `provenance.txt` are not looked at. The
release line is read from `etc/ISABELLE_IDENTIFIER`, the build from `etc/ISABELLE_ID`; the tool
never runs `isabelle` and reads neither `ISABELLE_HOME` nor `CONDA_PREFIX`.

## The chain and the levels

The installed feature directories must link into one chain: the bottom is the tree's own tag
`<release>/pristine/<etc/ISABELLE_ID>`; at each step exactly one directory's `base_tag` equals the
current tag, and its `release_tag` is the next. A directory whose base is a different pristine
build means the tree is not the build the packages were made for (`conda update --all` fixes it);
a directory whose base is missing or has another version means the chain is broken (install
matching versions). Both are exit 3. No feature directory at all is `no feature packages installed`,
exit 0, whatever the build.

Every patch file changes exactly one path. A file that features `t1 < … < tm` change is *at level L*
(L one of `0, t1, …, tm`) when, on a copy of its current content, reversing the patches of the
features `≤ L` from the top down succeeds step by step, and forward-applying the patches of the
features `> L` from the bottom up succeeds step by step. Exactly one such L is the file's level; none
or several is `CONFLICT` (a file that fits two levels is one whose content is the same at two points
of the chain, which the release checklist in [RELEASE.md](RELEASE.md) rules out for released
features; a hand edit is the usual cause of fitting none). A file that does not exist is a content
like any other, so a created file is at its creator's level when present with that content and one
level lower when absent.

A feature's state follows from its files: `applied` when all are at or above its number,
`not-applied` when all are below, `half-applied` otherwise, `CONFLICT` when any of its files is.

## Commands

### `status [--feature F]`

Prints `tree <path>   features.d <path>`, then one line per feature in chain order:
state, feature name, release tag, and `N files` (for `half-applied` also `, k below`; for
`CONFLICT` the conflicting files instead), with `(hole below)` appended to an applied feature that
has a not-applied one below it. With `-v`, each feature's files follow, with their level, files
the feature creates marked `(created by the feature)`, and for a CONFLICT file the levels it fits or
`no level` and git's complaint per rejected level.

When the environment has `conda-meta` but no `conda-meta/history`, a conda command was interrupted;
`status` then also prints how to repair that.

Exit code: 0 when every feature is `applied` and none has a hole; with `--feature F`, 0 when F is
`applied` without a hole; 1 otherwise; 0 with `no feature packages installed`.

### `apply [--feature F] [--dry-run]`

Moves every file whose level is below its target up to it. The target is the top of the chain, or F,
and never above the lowest feature that owns a CONFLICT file: that feature and the ones above it are
left alone. A file's own target is the highest level `≤` that target among the levels the file can
have, so a file no feature in range changes is not touched, and on a fully applied tree nothing
moves and `--dry-run` lists nothing.

Prints each move as `  <path>  level a -> b` under `-v` (always with `--dry-run`), then, if anything
moved, `Isabelle sources under <tree> changed (applied: …)` and, if a file under `src/` changed, the
heap hint. CONFLICT files in the way are printed as `CONFLICT  <path>  …` with git's complaints.
Exit code: 1 when a CONFLICT file is in the way, else 0. `--dry-run` has the same exit code and
changes nothing; it also runs on a read-only tree.

### `unapply [--feature F] [--dry-run]`

Moves every file whose level is above its target down to it: to level 0 (the pristine sources),
or, with F, to just below F, which reverses F and every feature above it. CONFLICT files cannot be
moved; everything else is, and the CONFLICT files are listed, exit 1. Prints
`Isabelle sources under <tree> changed (reversed: …)` and, when the whole tree is back at the
pristine sources, the line about deleting `heaps/` so that the shipped heaps are used again.

### `apply-to <dir> <feature dir>` / `unapply-from <dir> <feature dir>`

The directory interface: `<dir>` is the tree and `<feature dir>` the only feature; no provenance
file is read, no lock is taken, the copies live in a temporary directory next to `<dir>`. Used by
the release gates (`tools/make-patches`) on an archive of the base release. Exit 1 on a CONFLICT.

### `conda-hook post-link` / `conda-hook pre-unlink <feature>`

What the feature packages' hooks run; not for hand use. They read `$PREFIX` (and `$PKG_NAME`),
report only through `$PREFIX/.messages.txt`, which conda prints, and always exit 0 so that conda
never rolls a transaction back because of them. post-link applies the whole chain; a hook writes
only what its run changed, and the complete diagnostic of a CONFLICT is written by the hook of the
top feature package only (the others write one line). pre-unlink reverses the feature and
everything above it and never applies; when some of the feature's files still carry its changes
afterwards (a CONFLICT, the lock held by another run, a chain that does not link, a file that could
not be written) it writes which files, why, and what to do, with separate instructions for the
case that the package is being updated and for the case that it is being removed.

### `help`

Prints [AGENTS.md](AGENTS.md).

## Global options

| Option | Meaning |
|---|---|
| `--isabelle-home DIR` | the tree; its parent is the prefix |
| `--features-dir DIR` | the `features.d` root to read instead of the environment's |
| `-v`, `--verbose` | `status`: files and levels; `apply`/`unapply`: the first line and every move |
| `-q`, `--quiet` | no output but errors; exit codes only |

`-v`/`-q` may also follow the command, as in `isabelle-patch-control status -v`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success; `status` with everything applied; no feature packages installed |
| 1 | `status` found `not-applied`, `half-applied`, `CONFLICT` or a hole; `apply`/`unapply` could not move a file; git could not write a copy; the tree could not be written; the lock was busy for 60 s |
| 2 | no tree where expected; `git` missing or older than 2.43 |
| 3 | refused: chain does not link, tree is another build than the packages were made for, tree has a `.git`, a target is a symbolic link, a patch file cannot be read or changes other than one path, a feature directory has no patch file, `--features-dir` does not exist, not a conda environment and no `--features-dir`, unknown `--feature` name |

`conda-hook` always exits 0.

## The lock and the work directories

Every run holds a lock on the tree's `etc/ISABELLE_ID` (an existing file; nothing is created):
shared for `status` and any `--dry-run`, exclusive for `apply`, `unapply` and the hooks. A run
waits up to 60 seconds, then reports `another isabelle-patch-control run holds the lock on …`
(exit 1; in a post-link the message adds `Then run: isabelle-patch-control apply`). Environments
built from the same package cache share that file's inode, so they also share the lock.

Only the run holding the exclusive lock uses the staging directory `<tree>.staging`
(`$PREFIX/isa.staging`), on the same file system as the tree, emptied before and removed after;
every other git call runs in a fresh temporary directory. Each file moved into the tree is one
`os.replace` of a finished copy (or one `os.unlink`), so a killed run leaves every file either old
or new, and the next `apply` or `unapply` finishes the job.

## Messages

Every text a user sees is in `isabelle_patch_control/texts.py`, word for word as proofread;
the plan's §4 is their origin. The ones met most often:

- the heap hint after `src/` changed: `Isabelle sources under <tree> changed (applied: …).` followed
  by three lines on rebuilding heaps, or `(reversed: …)` with the line about `heaps/` when the tree
  is back at the pristine sources;
- `feature chain broken: <package> <version> (features.d/<dir>) needs <package> <version> (<tag>);
  installed: …. Install matching versions of these packages.`;
- `<tree> has etc/ISABELLE_ID <id>, but features.d/<dir> was made for <release> pristine <id>.
  Feature packages exist only for the pristine isabelle build. Run: conda update --all …`;
- the CONFLICT diagnostic `isabelle-patch-control: <feature> was NOT applied: <file> under <tree> has
  content the tool does not recognise …`, with the repair steps;
- the pre-unlink texts `<feature> was undone …` and the residue block `<feature> could not be fully
  undone (reason: …)`.
