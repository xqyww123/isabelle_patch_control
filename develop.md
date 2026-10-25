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
                 pristine tree); common.py also holds plan_builds (decision 10) and imports
                 package_name from the Python package
tests/           pytest (the tool; also plan_builds and check-roundtrip)
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
python -m pytest            # about 25 seconds
tools/tests/run-all.sh      # the toy runs of tools/ (make-patches, run-tree, ...), about a minute
```

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
exclusive runs, no run without the exclusive lock touching the staging directory); the directory
interface; the hooks against a fake `$PREFIX` (post-link idempotence and single report, the
CONFLICT diagnostic from the top package only and naming the lowest stopped feature, lock busy, the
old build, refusals framed with the command to run, a write failure saying what was applied, the
ASCII `.messages.txt`, pre-unlink's success texts, residue blocks for the three reasons, the
chain's message when the packages do not link, a non-zero exit with nothing written when the
residue cannot be computed, the in-place edit through a hard link selecting the package-cache
wording); `check-roundtrip` on the toy chain, a CRLF and a Latin-1 file included, and a wrapped tool
with one fault each for the mode listing, the created-file check and the check after unapply (the
exit-code checks and the "A equals the pristine tree" guard have no fault test); `plan_builds`.

Not covered here: the hook layer against real conda (a toy channel; plan decision 15, §5 step 5),
`check_bytes` of the release workflow, and everything Windows-specific (`msvcrt` lock, `.bat`
hooks, `core.longpaths`, retries of `os.replace`): those run on the win-64 leg of the release
workflow.

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
python, `run: python >=3.12, git >=2.43`) are plan §5 step 5 and not written yet; `common.plan_builds`
and `common.isabelle_pin` are their first pieces.
