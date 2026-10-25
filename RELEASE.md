# Releasing

**Status today: no feature package can be released.** Two things must land first: this repository's
batch release workflow `.github/workflows/release-features.yml` (together with the recipe renderer
`tools/render-feature-recipe` and the tool's own `conda/recipe.yaml`; plan §5 step 5, specified in
plan decisions 10 and 11, which this file only summarises), and the pristine Isabelle build of
`isabelle-packaging-ci` (its `RELEASE.md`). Until then `make-patches` can tag releases in the
repositories, and nothing publishes them.

The tool and the feature packages are conda packages on <https://conda.qiyuan.me>, all `noarch`,
built, accepted and published **together** by the batch release workflow. Every feature package pins
one exact `isabelle` build (`isabelle 2025.2 <build string>`), so every new `isabelle` build is
followed by a re-release of every feature package: same version, build number plus one, new pin.

Words used below. The *owner* is the person who owns the Isabelle source repository and the
channel; every build and release below runs on the owner's order. The *Isabelle source repository*
is the owner's git repository of Isabelle's sources (`contrib/Isabelle2025-2` and its worktrees
`contrib/Isabelle2025-2-*` in the owner's checkout; README.md, section *Working in the Isabelle
source repository*); the commands below run from that checkout's root unless they say otherwise. A
*feature* is one patch package; its branch `<R>/<feature>` (for example
`Isabelle2025-2/light_locale`) is checked out in its *private tree* `contrib/<R>-<feature>`, the
only place where it is edited and built. Its *base* is the branch it is built on; a *release tag*
`<R>/<feature>/<version>` marks a released commit (versions are positive integers: 1, 2, 3, …), and
the *base tag* is the base's release tag at the merge base. A *feature repository* is the feature's
own git repository, which holds its `tools/` lists and receives `patches/<R>/` (the patch files, one
per changed path under a *flat name*: the path with `/` replaced by `-`, plus `.patch`; and
`provenance.txt`). A *level* is the tool's reading of one file on a user's machine: the number of
the highest feature whose change the file carries (0 for the pristine content); a file that fits two
levels reads as `CONFLICT`.

## First-time setup of a feature repository

Before a feature can be released, its repository holds, committed:

- `tools/patched_files.txt`: every path the feature changes, relative to the Isabelle tree, one per
  line in any order (`make-patches` gate (f) requires the set to equal the output of
  `git diff-tree -r --no-renames --name-only <base tag> <tip>`; generate the file with that command).
- `tools/signature_additions.txt`: every signature entry the feature adds to an `.ML` file, as
  `<path> <SIGNATURE NAME> <keyword> <name>` (gate (d), `tools/check-signatures`); empty if none.
- `tools/required_sessions.txt`: the sessions a tested build must have covered (gate (e)); at
  least one, for example `Pure` and `HOL`.
- `tools/component_files.txt`, only for a package that also ships an Isabelle component (today
  light locale: `ROOT`, `Light_Locale.thy`, `README.md`, `LICENSE`): the files to ship under
  `share/<package>/`; they must be committed, and the tested build must have used `-d <this
  repository>` (gate (e)).
- `.gitattributes` with `*.patch -text`, so that a checkout on Windows does not CRLF-convert the
  patch files (the tool applies them byte for byte). Never hand-edit `patches/`: `make-patches`
  rewrites it on every release, one patch file per changed path.
- `README.md`: the feature's own README; the package's `share/doc/<package>/README.md` is this
  repository's `common-readme.md` followed by it.

A feature's place in the chain is its branch's base in the Isabelle source repository (`new-tree
--base`, owner only); its package depends on the base's package at the exact version of the base
tag, which `make-patches` writes into `provenance.txt` as `base_pin`.

## Before releasing a feature (checklist)

`make-patches` checks the repository-side gates (base tag, own commits, changed files, signatures,
tested record, round trip through the tool). The points below are about the *content* of the
feature and are not checked by code: feature packages are trusted, and the person releasing goes
through this list **before** the build and before `make-patches`: a failed point means a new commit,
and the tested record must be for that new commit; `make-patches` tags the release, so a failed
point after it would cost the version number. Every point is a question about
`git diff-tree -r --no-renames <base tag> HEAD` in the feature's private tree; `<base tag>` is
`git tag --points-at $(git merge-base <base branch> HEAD) --list '<R>/<base>/*'`, and the diff
itself is `git diff-tree -r -p --no-renames <base tag> HEAD > /tmp/f.diff`. Each point says why it
matters and how to check it. Points 1 and 4 are checked by nobody but you; points 2 and 3 are
checked by `make-patches` for your own feature's files, but not for files that features below yours
change.

- [ ] **No file is changed back to exactly what it was at some lower feature's release** (this
      includes deleting a file a lower feature created, or renaming it). The tool tells "which
      features are applied" from the bytes of each file alone; two points of the chain with
      identical bytes cannot be told apart. Changing a lower feature's file further, or editing lines
      a lower feature added, is fine. Check, with `<lower tags>` = every release tag of a feature
      below yours plus the pristine tag (`git tag --list '<R>/*/*'` lists them all; the ones below
      yours are the base tag and, recursively, its base's tags, read from each `provenance.txt`):
      ```
      for p in $(git diff-tree -r --no-renames --name-only <base tag> HEAD); do
        for t in <lower tags>; do
          [ "$(git rev-parse -q --verify "$t:$p" 2>/dev/null)" = "$(git rev-parse HEAD:$p)" ] && echo "$p equals $t"
        done
      done
      for p in $(git diff-tree -r --no-renames --diff-filter=D --name-only <base tag> HEAD); do
        git cat-file -e "<pristine tag>:$p" 2>/dev/null || echo "$p was created by a lower feature"
      done
      ```
      Both loops must print nothing.
- [ ] **Every hunk's context occurs only once in the file it changes.** Otherwise the forward patch
      can apply a second time at another place, the file then fits two levels, and `status` reads
      `CONFLICT`. Add a few more lines of context that are unique. Check: extract `git archive HEAD`
      into an empty directory and, in it, run `git apply --check --include=<p> /tmp/f.diff` for every
      changed path `p`; every run must *fail* (re-applying a hunk to the file that already carries
      it can only succeed when its context occurs elsewhere). `make-patches` gate (c) refuses this
      case too (the patches do not reverse cleanly), so for your own feature this point is also
      checked by code; for files that a feature below yours changes it is not.
- [ ] **Only regular files, mode `100644` or `100755`; no change of mode alone.** No symbolic links,
      no gitlinks, no file turned into a directory. The tool replays and installs plain file bytes,
      taking the mode from the patch header: a symbolic link cannot be installed, and a change of mode
      alone leaves the bytes the same and reads as `CONFLICT` (the file fits two levels). Check: in
      `git diff-tree -r --no-renames <base tag> HEAD` every line's two modes are `100644`, `100755`
      or `000000`, and no line has equal blob hashes. (`make-patches` refuses mode changes, renames
      and binary diffs when it cuts the patch files.)
- [ ] **`etc/ISABELLE_ID` is not changed.** The tool locks on it. Check:
      `git diff-tree -r --name-only <base tag> HEAD | grep -x etc/ISABELLE_ID` prints nothing.
- [ ] **The longest new patch file's path in the package cache stays within 198 characters** on
      Windows: `<package>-99-Isabelle2025_2_99/share/isabelle_patch_control/features.d/<feature>/<flat name>.patch`
      (version 99 and build 99 for the estimate). Check: `git diff-tree -r --name-only --no-renames
      <base tag> HEAD | sed 's,/,-,g'`, prefix each name with that path and count.

The workflow's `roundtrip` and `accept` jobs run `status` on the whole installed chain before
anything is published, so a file that fits two levels *at the chain top* shows up there as
`CONFLICT` and stops the batch (the version number is then spent: release v+1); `smoke` repeats the
check after publishing and can only report. The states *between* two releases of the chain (a user
who has only the lower packages installed) are protected by this list alone.

## Releasing a feature

Example values, for light locale's first release on Isabelle2025-2: `<R>` = `Isabelle2025-2`,
feature `light_locale`, base branch `Isabelle2025-2/future_assign_interrupt`, base tag
`Isabelle2025-2/future_assign_interrupt/1`, version `1`, private tree
`contrib/Isabelle2025-2-light_locale`, feature repository `contrib/light_locale`.

1. Go through the checklist above on the commit you want to release. A failed point means a new
   commit on the feature's branch; start again from here.
2. In the feature's private tree, on the owner's order, build the sessions `tools/required_sessions.txt`
   names through `run-tree`, which writes the tested record when the build exits 0 with an empty
   `git status` and an unmoved HEAD (for a package with component files, the build must pass `-d
   <feature repository>`):
   ```
   tools/run-tree contrib/Isabelle2025-2-light_locale build -d contrib/light_locale -b HOL
   ```
3. On the owner's order, release: it runs the gates on the tested commit, writes the package's
   `patches/<R>/` and `provenance.txt`, commits them in the feature repository, tags both
   repositories (the Isabelle source repository last: that tag marks the release as done), and can be
   rerun after any failure:
   ```
   tools/make-patches -C contrib/Isabelle2025-2-light_locale --package contrib/light_locale light_locale 1
   ```
   (`make-patches --help` lists the gates it runs.)
4. For every feature above this one in the chain: merge the new release into its branch, then do
   steps 1 to 3 for it with its next version (for example 1 becomes 2).
5. Push the feature repositories' branches and tags and the Isabelle source repository's tags.
6. Dispatch `release-features.yml` with `publish=false`, then, when the `roundtrip` job and the four
   `accept` legs are green, with `publish=true` (see below). Its `features` input names every
   feature release tag the channel should end up with, lower features included; packages already on
   the channel with this `isabelle` pin are reused, not rebuilt.

## The batch release workflow

Inputs:

| Input | Meaning |
|---|---|
| `isabelle_build` | the build string of the pristine `isabelle` build to pin (required) |
| `isabelle_from` | `channel` (the build is on conda.qiyuan.me) or `run:<isabelle-packaging-ci run id>` (rehearsal against that run's `conda-packages` artifact, which must carry `isabelle_build`, not build 0) |
| `tool_ref` | the tag of this repository to build the tool from (default: the triggering ref) |
| `features` | the explicit list of feature release tags to publish, the whole chain (lower features included); no default |
| `session_build_legs` | legs besides linux-64 that also build the component session |
| `publish` | default `false`; `publish=true` together with `isabelle_from=run:…` fails at once |

Jobs, in order: **build** (one `ubuntu-latest` job, `rattler-build` 0.69.1) reads the channel's
`noarch/repodata.json`, decides for every package of the batch, tool included, whether to reuse the
file already on the channel or to build a new one and with which build number
(`tools/common.py: plan_builds`: reuse what is on the channel and is exactly what this batch wants,
skip served files that are not, build the rest with the next number; a feature package is exactly
what the batch wants when it pins this batch's `isabelle` build, `common.isabelle_pin`), checks out
the feature repositories at their tags, renders each recipe (`tools/render-feature-recipe`: version,
base pin, `isabelle` pin, build string `Isabelle2025_2_<n>`, hooks, the common README text, the
component payload if `tools/component_files.txt` exists), builds everything into one local channel,
checks each `.conda` (hooks present, `.bat` CRLF, `.sh` LF), uploads one artifact
`feature-packages` containing only `noarch/*.conda`. **roundtrip** (linux-64) installs `isabelle`
and the tool into a fresh environment, copies its `isa/` as the pristine tree, installs the chain
top, and runs `tools/check-roundtrip` against the installed tool and `features.d`. **accept**
(linux-64, linux-aarch64, osx-arm64 with osx-64 under Rosetta, win-64) installs the batch into a
fresh environment and checks, through `status` and the bytes of every touched file, that the chain
is applied, that removing a package reverses it, and that `--force-reinstall isabelle` re-applies
it (plan §6). `roundtrip` and `accept` stop the batch. **publish** (only `publish=true`) calls
`xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main` once with the artifact and
the two R2 secrets. **smoke** (linux-64, win-64) runs the install command read from the copied
common README text and installs `qiyuan-dev-patches` on top, then `status`; it runs after
publishing and only reports.

Versions and build numbers: a feature package's version is the version in its release tag; its
build string is `Isabelle2025_2_<n>`; `n` is never typed by hand. Nothing is published if the same
(feature, version, `isabelle` build) is already on the channel: to change a README or template,
release a new version.

Recovery: a failed publish is resumed by **dispatching the same inputs again**; the files already on
the channel (indexed or merely uploaded) are reused byte for byte, so the upload guard of
`publish-conda.yml` does not refuse them. Re-running failed jobs of the same run works only while
the artifact exists (30 days).

Before `publish=true`, two conditions: the pristine `isabelle` build is published and green on the
channel, and no other publish is running in any repository that publishes to the channel
(`PUBLISH_REPOS` in `isabelle-packaging-ci`'s `RELEASE_CHECKLIST.md` lists them; `publish-conda.yml`
rebuilds the channel index, so two publishes at once would overwrite each other's index).

## One-time setup still to do (on the owner's order)

- This repository enters `PUBLISH_REPOS` and the channel's `RELEASE_CHECKLIST.md`; two R2 secrets,
  a read-only token for the private feature repositories, an `actions:read` token for
  `isabelle-packaging-ci`; `.gitattributes` with `*.sh text eol=lf`, `*.bat -text`, `*.patch -text`.
