# Developing

How the tool works inside, where things are, and how to test. The design is the plan
`ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md` (rev 6, with five plan reviews and the first code
review next to it); change the plan before changing the design. For what the tool does for a user
see [reference.md](reference.md).

## One path for every command

Every command runs the same sequence; `status` and `--dry-run` stop before the last step.

1. **Resolve** the tree and the `features.d` root (`cli.resolve` for the command line,
   `features.locate` for a conda prefix, plan decision 2); read `etc/ISABELLE_IDENTIFIER` and
   `etc/ISABELLE_ID`; refuse a tree with a `.git`.
2. **Link the chain** (`features.link_chain`, decision 3): every feature directory with a
   `provenance.txt` (a missing root is an empty chain), linked by exact tags from the tree's
   pristine tag upwards; `--feature F` is looked up here (`features.feature_number`), so every
   refusal of a command's start comes before the lock.
3. **Lock** `etc/ISABELLE_ID` (`engine.locked`, decision 5): shared for reads, exclusive for
   writes; 60 s, then `Busy`.
4. **Work directory**: the staging directory `<realpath(tree)>.staging` for the exclusive run,
   a fresh `tempfile.mkdtemp()` for everything else (`engine.staging_dir`, `engine.temp_dir`).
5. **Read every patch's target** with `git apply --numstat --summary` (`Replayer.read_target`):
   one path per patch file, and whether it creates or deletes the file and with which mode.
   Refuse symbolic links among the targets.
6. **Levels** (`Replayer.levels`, decision 6): for each touched file, for each candidate level L,
   reverse the patches `≤ L` top-down on one copy and forward-apply the patches `> L` bottom-up on
   another, each step a real `git apply` on the copy. Every successful candidate yields a table
   *level → content bytes*; exactly one successful candidate is the file's level, otherwise
   CONFLICT. The table is kept: it is what gets installed.
7. **Plan the moves** (`model.plan`, decision 7): each file's own target level, the cap below the
   lowest feature owning a CONFLICT file for `apply`.
8. **Install** (`Replayer.install`, decision 5): write the table's bytes for the target level into
   the work directory, set the permission bits (the tree file's own, or the patch header's for a
   file that does not exist), one `os.replace` into the tree; or one `os.unlink` and the removal of
   emptied directories.

`git` runs in exactly one place, `engine.Git.run`, with a whitelisted environment (`PATH` and, on
Windows, `SystemRoot`, `TEMP`, `TMP`), `GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_ATTR_NOSYSTEM`, `LC_ALL=C`, `GIT_CEILING_DIRECTORIES` at the work directory's parent, and the
fixed `-c core.autocrlf=false -c core.attributesFile=/dev/null`; umask 022. It never runs in the
tree or in the caller's directory (patch paths are made absolute first), so no repository above, no
user configuration and no attributes file can change the bytes. Exit code 1 of a replay is "does
not apply"; any other non-zero code is a write failure on the tool's own copy and aborts the run
before anything is installed. Every `OSError` on the shared path (`api._session`: the lock file on a
read-only file system, a full disk while writing a copy, an unwritable parent for the staging
directory) becomes `WriteFailed` there, so the API raises only `errors.Error`.

## Where things are

```
isabelle_patch_control/
  names.py       feature name <-> conda package name (tools/common.py imports it)
  errors.py      Error, NotFound (2), Refused (3), ChainBroken, Busy, WriteFailed
  engine.py      Git.run, the lock, staging/temp directories, PatchFile, Levels, Replayer
  features.py    Tree, FeatureDir (provenance), read_feature_dirs, link_chain
  model.py       feature states, Move, plan()
  api.py         status, apply, unapply, apply_to, unapply_from; Status, Moves  (never exits)
  texts.py       the plan's texts (§4, decision 9) and every frame a conda hook writes
  cli.py         argument parsing, output, exit codes
  conda_hook.py  conda-hook post-link / pre-unlink; the one reading of conda-meta
  hooks/         the hook texts the feature packages ship: post-link.sh/.bat (the fragment every
                 feature package's post-link copies verbatim), pre-unlink.sh/.bat (templates with
                 <feature>, <package>, <version> for the renderer); the .bat files are CRLF
  AGENTS.md      symlink to ../AGENTS.md; `help` prints it
common-readme.md the text every feature package's README starts with; README.md embeds it
tools/           the Isabelle source repository's scripts (make-patches, run-tree, ...) and their
                 toy tests, see README.md "Working in the Isabelle source repository";
                 check-roundtrip (plan decision 17: the tool against GNU patch on a copy of a
                 pristine tree); common.py also holds plan_builds, isabelle_pin, feature_pin
                 (decision 10) and conda_archive, and imports package_name from the Python package.
                 The release workflow's pieces (decisions 10, 11, 15, §6): render-feature-recipe
                 (the one recipe of every feature package), release-plan (reuse or build, which
                 number), check-packages (inside every .conda; the batch is the whole chain),
                 local-channel, check-bytes (the byte oracle), accept (§6 on one leg)
conda/recipe.yaml the tool's own package (noarch python; TOOL_VERSION and TOOL_BUILD_NUMBER from
                 the workflow)
.github/workflows/release-features.yml  the batch release (RELEASE.md)
tests/           pytest (the tool; also plan_builds, check-roundtrip, the renderer, check-bytes,
                 release-plan and check-packages)
```

`make-patches` runs gate (c) through `api.apply_to` / `api.unapply_from` on `git archive <base tag>`,
writes the package only after every gate passed, and then commits by name, checks the commit to tag,
tags the feature repository and last the Isabelle repository (decision 16 point 8; each step can be
rerun after a failure, and the toy test makes each write fail by holding git's own lock file for it).
The diff is cut into patch files by `common.patch_blocks`, in bytes, so CRs and non-UTF-8 bytes
survive; the test fixtures use the same function. `run-tree` records the state of every `-d`
directory that a git worktree covers (does not ignore) in the tested record (`dir:` lines: top
directory, HEAD, tracked files with uncommitted changes) and writes no record when a tracked file of
one of them changed during the build (migration plan §0 item 32).

Texts: `texts.py` holds the plan's texts (§4, decision 9) and every frame a conda hook writes; a
frame quotes the refusal's own sentence, which is written next to its check (features.py, engine.py,
api.py). Three independent readers proofread the five texts named in plan §8 from the reader's
standpoint (plan decision 9, "文案的写法"); the rest were written by the author and read once by
three readers after code review 1. Hook messages say what happened and then the command to run,
put the common and safe case first, destructive consequences on their own line before the command,
and only the branch that applies; they avoid the tool's inner words (`level`, `hook`, `below/above`),
while `status -v` and `--dry-run` do speak of levels, as §4 says. Do not reword any of them in
passing; change the plan's §4 first.

## Tests

```
python -m pytest            # about 35 seconds; needs the zstandard module (conda's own dependency)
tools/tests/run-all.sh      # the toy runs of tools/ (make-patches, run-tree, ...), about a minute
RATTLER_BUILD=<rattler-build 0.69.1> CONDA_EXE=<conda> HOOKS_TEST_CACHE=<dir kept between runs> \
  tools/tests/test_conda_hooks.sh [<scratch dir>] [<scenario>...]   # the hook layer, real conda
```

On GitHub, `.github/workflows/tests.yml` runs all of it on every push to `main` (and weekly):
`lint` (actionlint over the workflows), `unit` (pytest on Linux at the tool's declared floors,
python 3.12 and git 2.43, and on macOS at the latest; `run-all.sh` on Linux), `toy-channel`
(`toy-channel.sh` with the release's rattler-build), `hooks` (`test_conda_hooks.sh`) and `accept`
(`tools/accept --strict` on the toy channel on the five legs, through the release's own
`accept.yml`). Kept local and uncommitted: mutation checks of new tests and one-off negative
controls (plan decision 15).

`test_conda_hooks.sh` (plan decision 15) runs on the toy channels of `tools/tests/toy-channel.sh`:
the tool from `conda/recipe.yaml` (with its recipe's tests); a toy `isabelle` package in three
builds (0 with the old `ISABELLE_ID`, 1 and 2 pristine) whose `isa/bin/isabelle` and
`isa/bin/isabelle.bat` run one Python stub (`tools/tests/toy_isabelle.py`: `getenv`, `version`,
`components`), whose two pre-unlinks are the real ones and whose post-link only re-runs the direct
dependents' post-links (plan §0 items 26, 33, 34); three toy features cut from a toy source
repository and rendered by the real renderer (each creates a file, the middle one ships a
component); a component package of the Isabelle_RPC kind; a package that depends on `isabelle`
only indirectly; a broken tool in a channel of its own; and a channel without the re-release for
build 2. Every package is noarch, so `tools/accept` runs on the same channel on all five platforms.
Every scenario starts from a new environment with a private `HOME`, `CONDARC` and package cache
(`s_hardlink` has one of its own, so a failure cannot leave the shared one edited) and reads conda's
own output; the tree's bytes are checked by `tools/check-bytes`. The lock scenarios (`s_residue`,
`s_rule`) wait for the tool's 60-second lock timeout three times each; the twelve scenarios take
about half an hour on the author's machine, most of it conda's solving (one run also stalled for
an hour inside a single conda command).

`tests/conftest.py` builds a toy Isabelle tree and a toy chain of three features the way
`make-patches` builds real ones: commits in a toy git repository, `git diff-tree -r -p --no-renames`
cut into one patch file per path with flat names by the same `common.patch_blocks`, a
`provenance.txt` per feature; trees are `git archive` extractions (with `tar.umask=022`, so files
are 0644/0755 like the conda package's). No Isabelle is needed and nothing runs `isabelle` or
`isabelle build`.

What is covered (plan decision 15, tool layer): the linking rules and every refusal, with
directory names that sort out of chain order; the derivation of the tree and `features.d`, the
default invocation, relative paths through the API; the four states, holes (any feature below that
is not applied), the scenarios of the first review's C3; a CONFLICT file that two features touch
(the cap, what is in the way of `apply --feature` and `unapply --feature`, which feature post-link
names); the two multi-level cases (created then deleted; a hunk whose context occurs twice);
stacked hunk context on fresh, half and fully applied trees with both dry runs; created files and a
simulated relink; a run killed after the k-th file (`tests/kill_after.py`) leaving every file old or
new and the next run converging; a git write failure leaving the tree alone; EROFS and ENOSPC
reported with the status, never a traceback; permission bits under umask 002 and 077, a deleted
0755 file restored; a hard-linked changed file keeping its content and mode; five hostile git
environments giving the clean result, git looked up at the prefix first and refused below 2.43; the
lock (read-only tree and parent, busy within a shortened `engine.LOCK_TIMEOUT`, shared, two
exclusive runs, no run without the exclusive lock touching the staging directory); the retry of
`os.replace` on a target held open on Windows (with `engine.WINDOWS` patched); the directory
interface; the hooks against a fake `$PREFIX` (post-link idempotence and single report, the
CONFLICT diagnostic from the top package only and naming the lowest stopped feature, lock busy, the
old build, refusals framed with the command to run, a write failure saying what was applied, the
ASCII `.messages.txt`, pre-unlink's success texts, residue blocks for the three reasons, the
chain's message when the packages do not link, a non-zero exit with nothing written when the
residue cannot be computed, the in-place edit through a hard link selecting the package-cache
wording, and the same wording without the directory in a post-link that has no `isabelle` record
because the command is linking isabelle itself); `check-roundtrip` on the toy chain, a CRLF and a Latin-1 file included, and a wrapped tool
with one fault each for the mode listing, the created-file check and the check after unapply (the
exit-code checks and the "A equals the pristine tree" guard have no fault test); `plan_builds`.

Not covered by pytest: the hook layer against real conda (`test_conda_hooks.sh`), and the
Windows-specific behaviour, which `tools/accept` checks on the win-64 leg: the `msvcrt` lock while
`type` and `isabelle version -i` read `etc/ISABELLE_ID`, a read-only and an in-use target, the
`.bat` hooks including a negative exit code, the git the tool runs, and `core.longpaths` taking
effect (a patch and its target over 260 characters apply, and fail with the flag turned off).

A check against the real chain, done once by hand: build `features.d` from the Isabelle source
repository's branches with `git diff-tree` (read-only), extract the touched files of the official
tarball, run `status`, `apply`, `status`, `unapply`, and compare every file with
`git rev-parse <tip>:<path>` / `git hash-object`. All 34 paths of expose_foreign +
future_assign_interrupt + light_locale round-tripped byte for byte, each command in 0.2 s.

## Making feature packages

Feature packages are not made here. `tools/make-patches` (run on the owner's order in the Isabelle
source repository) writes a feature's `patches/<release>/*.patch` and `provenance.txt` into the
feature's own repository and tags the release; the release workflow of this repository renders a
conda recipe from them, builds all packages into one channel, runs the acceptance on five
platforms, and publishes. See [RELEASE.md](RELEASE.md). The workflow, the renderer
`tools/render-feature-recipe` and the conda recipe of the tool itself (`conda/recipe.yaml`, noarch
python, `run: python >=3.12, git >=2.43`) are plan §5 step 5; the hook layer is tested locally
against the toy channel, the workflow itself runs for the first time in the rehearsal of plan §5
step 7. The pins are written the way rattler-build accepts them, `isabelle ==2025.2 <b>` and
`<base package> ==<version> Isabelle2025_2_*` (`common.isabelle_pin`, `common.feature_pin`); conda
reads them exactly as the older `isabelle 2025.2 <b>` and `==1=Isabelle2025_2_*`.
