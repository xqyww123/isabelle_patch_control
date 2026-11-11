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

Of each feature directory the tool reads `provenance.txt` (its `release_tag` and `base_tag`; the
feature's name is the middle part of `release_tag`) and `*.patch` only. Conda's `*.c~` leftovers,
editor files and subdirectories without a `provenance.txt` are not looked at. The release line is
read from `etc/ISABELLE_IDENTIFIER`, the build from `etc/ISABELLE_ID`; the tool never runs
`isabelle` and reads neither `ISABELLE_HOME` nor `CONDA_PREFIX`.

## How the installed features fit together, and the levels

Each feature directory's `base_tag` names the tags it is built on, its *bases*, separated by spaces:
the tree's own pristine tag `<release>/pristine/<etc/ISABELLE_ID>`, or the `release_tag` of other
feature directories. A feature's bases, their bases and so on are *below* it, and it is *above* them.
A directory whose base is a pristine tag of another release or build means the tree is not the build
the packages were made for (the `conda install --update-all` command the message gives fixes it);
this is reported first, whatever else is wrong. Otherwise a directory with a base that no installed
directory releases means that base is not installed at the version it needs (`… Install matching
versions of these packages.`, naming the package, its version and the base version it needs). Both
are exit 3. No feature directory at all is `No feature packages are installed, so there is nothing to
apply.`, exit 0, whatever the build. The installed features are numbered 1, 2, … in the order conda
installs them: by depth (1 for a feature built on Isabelle itself, otherwise one more than its
deepest base), then by package name; so every feature comes after the features below it.

Every patch file changes exactly one path. For a file, let P be the features whose patches change
it. A *level* of the file is a set of features of P that holds, with each of its features, every
feature of P below it; its *tops* are its features that no other feature of it is above; its content
is the original content with the level's patches applied. The file *is at level S* when, on a copy of
its current content, reversing the patches of S from the last to the first succeeds step by step, and
from the contents this gives every other level is computed, smallest first, from the level without
one of its tops by forward-applying that top's patch: a level with one top in one step that must
succeed, a level with several tops from each of them. Exactly one such S is the file's level; none or
several is `CONFLICT` (a file that fits two levels is one whose content is the same at two levels,
which the release checklist in [RELEASE.md](RELEASE.md) rules out for released features; a hand edit
is the usual cause of fitting none). For features that form a line, the levels are `0, t1, …, tm` as
numbers and the check is the same `git apply` calls in the same order. A file that does not exist is
a content like any other, so a created file is at its creator's level when present with that content
and one level lower when absent.

Two features, neither below the other, that change one file must apply in every order with the same
result: when one of the several ways of computing a level with several tops fails, or two of them give
different contents, every command refuses before it writes anything (exit 3, `<package> <version> and
<package> <version> cannot be installed together: their changes to <file> cannot be applied in every
order.`, naming the first pair whose changes meet; AGENTS.md says which one to remove). Two features
that make the same change are refused this way too.

A feature's state follows from its files: `applied` when every file it changes carries it (it is in
the file's level), `not-applied` when none does, `half-applied` otherwise, `CONFLICT` when any of its
files is.
`--feature F` names a feature by its feature name (`<feature>`) or by its package name
(`<package>`).

## Commands

### `status [--feature F]`

Prints the tree it checked and the number of feature packages, then one sentence per feature,
in their order, ``Feature `<name>` <phrase>…``, where the phrase gives the state: `is applied`
(`applied`; it goes on with ``, but `<feature>` below it is not`` when a feature below it is not
applied), `is not applied yet` (`not-applied`), `is only partly applied` (`half-applied`, with how
many of its files lack its changes), `cannot be applied` (`CONFLICT`, naming the files). The last
lines say what to do, for the features the command was asked about (with `--feature F`, F and
those below it, like the exit code): `Everything is in order.` (with `--feature F`: ``Everything up
to `F` is in order.``), the `apply` command (with `--feature F` when given), or, for a CONFLICT, the
repair. A file not in the `isabelle` package (a feature creates it) is deleted; a file of the
package is restored, in a conda environment by reinstalling `isabelle` (the created files are
deleted first, and the reinstall applies the features again), elsewhere by hand followed by
`apply`; with created files only, deleting them is followed by `apply`. A command these lines give
repeats `--isabelle-home` and `--features-dir` when they were given, so that it reaches the same
tree. The texts are in `isabelle_patch_control/texts.py`. With `-v`, the `features.d` root follows
the first sentence, and after each feature its package name, release tag and files, with their
level by its tops (`level 3 (f3)`, `level 3+5 (f3, f5)`, `level 0 (original)`), files not in the
`isabelle` package marked `(created by a feature)`, and for a CONFLICT file the levels it fits or
`no level` and git's complaint per rejected level.

Exit code: 0 when every feature is `applied`; with `--feature F`, 0 when F and every feature below
it are `applied`; 1 otherwise; 0 with no feature packages installed. An unknown `--feature` name
is refused (exit 3) before the lock is taken and before anything is printed.

### `apply [--feature F] [--dry-run]`

Adds to every file the features asked for (every feature, or F and the features below it) that
change it, except every feature that owns a CONFLICT file and the features above it, which are left
alone; a feature unrelated to those is still applied. `apply` only adds, so a file no feature in
range changes is not touched, and on a fully applied tree nothing moves and `--dry-run` prints
`Nothing would change.`

Prints, under `-v`, the same first line as `status` and the `features.d` root, then `These files
changed:` and each move as `  <path>  level a (<feature>) -> level b (<feature>)`; `--dry-run` prints
the moves under `These files would change:`. Then, if anything moved, `Isabelle
sources under <tree> changed (applied: …)` and, if a file under `src/` changed, the heap hint. Last,
for every CONFLICT feature up to F (without `--feature`, every one), the `status` sentence ``Feature
`<name>` cannot be applied: …`` followed by `Run isabelle-patch-control status for what to do.`;
under `-v` each of its CONFLICT files follows with git's complaints (without git's warnings). Those
files are the CONFLICT files in the way: touched by F or by a feature below it (without
`--feature`, every CONFLICT file). Exit code: 1 when a CONFLICT file is in the way or a file could
not be written, else 0 (refusals: see *Exit codes*). When a file cannot be written, `apply` prints
the error and then the `status` report, to show where it stopped (not with `-q`); `unapply` prints
only the error. `--dry-run` has the same exit code and changes
nothing; it also runs on a read-only tree.

### `unapply [--feature F] [--dry-run]`

Takes away from every file the features asked for: every feature (back to the pristine sources), or,
with F, F and every feature above it; a feature neither below nor above F stays applied. CONFLICT files
cannot be moved; everything else is. Prints `Isabelle sources under <tree> changed (undone: …)`, listing
the features it fully reversed (not a CONFLICT feature, even when some of its other files moved),
and, when the whole tree is back at the pristine sources, the line about deleting `heaps/` so that
the shipped heaps are used again. Last, for every CONFLICT feature from F up, ``Feature `<name>`
cannot be undone: …`` and the same `status` hint as `apply` (git's complaints under `-v`), exit 1.
Its CONFLICT files are those in the way: touched by F or by a feature above it (without
`--feature`, every CONFLICT file); a CONFLICT file that only features below F touch is left alone,
not listed, and does not change the exit code.

### `apply-to <dir> <feature dir>` / `unapply-from <dir> <feature dir>`

The directory interface: `<dir>` is the tree and `<feature dir>` the only feature; no provenance
file is read, no lock is taken, the copies live in a temporary directory next to `<dir>`. Used by
the release gates (`make-patches`) on an archive of the base commit. Prints the moves under
`-v` and the CONFLICT sentence as `apply` does, without the `status` hint, nothing else: success is
exit 0 and silence (the texts about heaps and the conda environment do not apply to an arbitrary
directory). Exit 1 on a CONFLICT.

### `conda-hook post-link` / `conda-hook pre-unlink <feature>`

What the feature packages' hooks run; not for hand use. They read `$PREFIX` (and `$PKG_NAME`) and
report only through `$PREFIX/.messages.txt`, which conda prints; every paragraph there starts with
`isabelle-patch-control:`, and the file is written as ASCII (non-ASCII path characters appear as
`\uXXXX`) because conda reads it with the platform's default encoding. The hook scripts of the
feature packages always exit 0, so conda never rolls a transaction back because of them:
`conda-hook` exits 0 whenever it wrote its own message, and when it cannot finish (a crash, or
pre-unlink cannot tell which files still carry the feature's changes) it writes nothing and exits
non-zero, and the hook script's own fallback line speaks instead. post-link applies every installed feature;
a hook writes only what its run changed, and the complete diagnostic of a CONFLICT is written by the
hook of the last feature package, in the order of the installed features, among the stopped feature
and those above it (the others write one line); any refusal is reported with the
command to run afterwards. pre-unlink reverses the feature and everything above it and never
applies; when some of the feature's files still carry its changes afterwards (a CONFLICT, the lock
held by another run, a file that could not be written) it writes which files, why, and what to do,
with separate instructions for the case that the package is being updated and for the case that it
is being removed. When the installed packages do not fit together it reverses nothing and writes
the refusal's message with those same two cases.

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
| 1 | `status` found a feature not applied yet, only partly applied, or one that cannot be applied (`not-applied`, `half-applied`, `CONFLICT`), or applied above one that is not; `apply`/`unapply` could not move a file; git could not write a copy; the tree, the lock file or a work directory could not be written or read (a read-only file system, a full disk); the lock was busy for 60 s |
| 2 | no tree where expected; `git` missing or older than 2.43; a wrong command line |
| 3 | refused: the installed packages do not fit together, tree is another build than the packages were made for, tree has a `.git`, a target is a symbolic link, a patch file cannot be read or changes other than one path, a feature directory has no patch file, `--features-dir` does not exist, not a conda environment and no `--features-dir`, unknown `--feature` name |

`conda-hook` exits 0 whenever it wrote its own message (see above).

## The lock and the work directories

Every run holds a lock on the tree's `etc/ISABELLE_ID` (an existing file; nothing is created):
shared for `status` and any `--dry-run`, exclusive for `apply`, `unapply` and the hooks. A run
waits up to 60 seconds, then reports `another isabelle-patch-control run holds the lock on …`
(exit 1; it ends `Wait for that run to finish, then retry.`, in a post-link `…, then run:
isabelle-patch-control apply.`). Environments
built from the same package cache share that file's inode, so they also share the lock.

Only the run holding the exclusive lock uses the staging directory `<tree>.staging`
(`$PREFIX/isa.staging`), on the same file system as the tree, emptied before and removed after;
every other git call runs in a fresh temporary directory. Each file moved into the tree is one
`os.replace` of a finished copy (or one `os.unlink`), so a killed run leaves every file either old
or new, and the next `apply` or `unapply` finishes the job.

## Messages

`isabelle_patch_control/texts.py` holds the messages that `status`, `apply`, `unapply` and the hooks
print, other than refusals and the lines `-v` and `--dry-run` print about each package, file and level
(cli.py composes those), and every frame `conda-hook` writes (the hook scripts' own fallback lines are
in `isabelle_patch_control/hooks/`); develop.md says how they are written. The refusals (an unknown name, a patch file git cannot read, a tree with a `.git`,
...) are written next to their checks, and a hook frame quotes them. The ones met most often:

- the heap hint after `src/` changed: `Isabelle sources under <tree> changed (applied: …).` followed
  by two lines on rebuilding heaps, or `(undone: …)` with the line about `heaps/` when the tree
  is back at the pristine sources;
- `<package> <version> needs <package> <version>, which is not installed. Install matching versions
  of these packages.` (or `, but <package> <version> is installed.`);
- `<tree> is not the Isabelle build the feature packages were made for: they need the unmodified
  <release> build of the isabelle package (this tree has etc/ISABELLE_ID <id>; …). To fix it, run:
  conda install -p <prefix> --update-all "isabelle==<isabelle version>" …`;
- the CONFLICT diagnostic ``isabelle-patch-control: Feature `<feature>` cannot be applied: <file> was
  changed by something other than the installed feature packages.``, then what it stops and the
  same repair as `status` prints (deleting the files a feature creates, then reinstalling `isabelle`
  when a file of the package changed);
- the pre-unlink texts `<feature> was undone …` and the residue block `<feature> could not be fully
  undone (reason: …)`.
