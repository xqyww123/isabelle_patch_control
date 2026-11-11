# Releasing

How to release a feature is in the SKILL
[`isabelle-patch-feature`](.claude/skills/isabelle-patch-feature/SKILL.md) (section 3.4); this file
is its reference: why each step and each checklist point is there, the files of the package
directory, and the batch release workflow.

The tool and the feature packages are conda packages on <https://conda.qiyuan.me>, all `noarch`,
built, accepted and published **together** by the batch release workflow. Every feature package pins
one exact `isabelle` build (`isabelle ==<isabelle version> <build string>`, for example
`isabelle ==2026 0`), so every new `isabelle` build is followed by a re-release of every feature
package: same version, build number plus one, new pin.

Words. This file uses the SKILL's words (feature, feature repository, base, base tag, base commit, release line,
shared tree, private tree, stock tree; its section 1), and these. The *owner* is the person who owns
isabelle-patched, the feature repositories and the channel. A *release tag* `<R>/<feature>/<m>`
(`m` = 1, 2, 3, …) marks a released commit. A release line `<R>` has a *build string prefix*, `<R>`
with `-` turned into `_` (`Isabelle2025_2`), and an *`isabelle` version*, the prefix without
`Isabelle` and with `_` turned into `.` (`2025.2`; `Isabelle2026` gives `2026`). The package built
from `<R>/<feature>/<m>` has the version `<isabelle version>.<m>`, with `.0` inserted when the
`isabelle` version has one number: `Isabelle2026/bicompose_rename_fix/1` gives `2026.0.1`;
`Isabelle2025-2/expose_foreign/1` gives `2025.2.1` (`dev.package_version`); a newer line's versions
are higher. The *package directory* (`make-patches --package <dir>`) holds the
`tools/` lists and receives `patches/<R>/` (the patch files, one per changed path under a *flat
name*: the path with `/` replaced by `-`, plus `.patch`; and `provenance.txt`). When a feature
repository holds one feature, its package directory is the repository itself; when it holds several,
each has its own subdirectory, and `--package` names it. A *level* is the tool's reading of one
file on a user's machine: the installed features whose changes the file carries (none for the
pristine content); a file that fits two levels reads as `CONFLICT`.

## First-time setup of a feature repository

Before a feature can be released, its package directory holds, committed:

- `tools/patched_files.txt`: every path the feature changes, relative to the Isabelle tree, one per
  line in any order (`make-patches` gate 3, changed files, requires the set to equal the output of
  `git diff-tree -r --no-renames --name-only <base commit> <tip>`, which is how the SKILL makes it).
- `tools/signature_additions.txt`: every signature entry the feature adds to an `.ML` file, as
  `<path> <SIGNATURE NAME> <keyword> <name>` (gate 4, signatures, `isabelle-patch-control check-signatures`);
  empty if none.
- `tools/required_sessions.txt`: the sessions to build before a release; at least one, for example
  `Pure` and `HOL`. The feature's `tools/release_build.sh` builds them.
- `tools/release_build.sh`, unless the feature has none: how the feature is built before a release, by
  the author and by the batch release workflow's `sessions` job; what it should do is in the SKILL
  `isabelle-patch-feature`, 3.4 step 4.
- `tools/component_files.txt`, only for a package that also ships an Isabelle component: the files to
  ship under `share/<package>/`; they must be committed. Nothing refuses a package that lacks this
  file: it simply ships no component.
- `tools/license.txt`, optional, read like the other lists: one SPDX license expression, or no entry
  for no license. The package's license file is the nearest file named exactly `LICENSE` from the
  package directory up to the repository's top; without one the package has no license file.
  rattler-build checks the expression only when the build job reads the recipe, after the tag, so a
  wrong or deprecated identifier (such as `GPL-2.0`) costs the feature's number `<m>`.
- `.gitattributes` with `*.patch -text`, in the package directory or at the top of the feature
  repository, so that a checkout on Windows does not CRLF-convert the patch files (the tool applies
  them byte for byte). Never hand-edit `patches/`: `make-patches` rewrites it on every release, one
  patch file per changed path.
- `README.md`: the feature's own README; the package's `share/doc/<package>/README.md` is this
  repository's `common-readme.md` followed by it, with `<package>` and `<feature>` replaced by the
  package's own names in both. It also says where a release's sources are, by the
  tag only, no command: "The Isabelle sources a version of this package was made from, with this
  feature and the ones it is built on, are a tag of isabelle-patched named
  `<Isabelle release>/<feature>/<m>`, where `<m>` is the last number of the package's version:
  version `2026.0.1` was made from `Isabelle2026/<feature>/1`." Write `<m>`, not `<version>`:
  `common-readme.md` uses `<version>` for the `isabelle` version.

A feature's bases are recorded as `base =` in the feature repository's `.gitmodules`, separated by
spaces (SKILL, section 1); its package depends on each base's package at exactly that package's version
(`==<version>`, for example `==2026.0.1`), which the recipe renderer computes from `base_tag`.

## Why the release steps are in this order

The checklist comes before the build and before `make-patches`: a failed point means a new commit,
and `make-patches` tags the release, so a failed point after it would use up the number `<m>`.
`make-patches` checks its gates (committed files, base tags, changed files, signatures, round trip
through the tool; `make-patches --help`) before it writes anything; then each of its write steps can be rerun after a
failure, and the tag in the private tree comes last: it marks the release as done. The features
built on a released feature merge the release and are released in turn, because each package pins
its bases' packages at one exact version; and conda installs one version of a package, so a feature
takes a newer release of a feature below it only once each of its bases built on that feature has
released on it.

## Before releasing a feature: why each checklist point matters

The commands are in the SKILL, section 3.4 step 2. These points are about the *content* of the
feature and are not checked by code: feature packages are trusted. Points 1, 4 and 5 are checked by
nobody but you; points 2 and 3 are checked by `make-patches` for your own feature's files, but not
for files that features below yours change.

1. **No file is changed back to exactly what it was at some lower feature's release** (this includes
   deleting a file a lower feature created, or renaming it). The tool tells "which features are
   applied" from the bytes of each file alone; a file whose bytes with your feature equal its bytes
   at a lower release fits two levels and reads as `CONFLICT`. Changing a lower feature's file further, or editing lines a lower feature added, is fine.
2. **Every hunk's context occurs only once in the file it changes.** Otherwise the forward patch can
   apply a second time at another place, the file then fits two levels, and `status` reads
   `CONFLICT`. Add a few more lines of context that are unique. `make-patches` gate 5 (round trip) refuses this
   case too (the patches do not reverse cleanly), so for your own feature this point is also checked
   by code; for files that a feature below yours changes it is not.
3. **Only regular files, mode `100644` or `100755`; no change of mode.** No symbolic links, no
   gitlinks, no file turned into a directory. The tool replays and installs plain file bytes, taking
   the mode from the patch header: a symbolic link cannot be installed, and a change of mode alone
   leaves the bytes the same and reads as `CONFLICT` (the file fits two levels). `make-patches`
   refuses any change of mode, renames and binary diffs when it cuts the patch files, but only after
   the build.
4. **`etc/ISABELLE_ID` is not changed.** The tool locks on it.
5. **The longest new patch file's path in the package cache stays within 198 characters** on
   Windows: `<package>-<Y>.<k>.99-<build string prefix>_99/share/isabelle_patch_control/features.d/<feature>/<flat name>.patch`
   (`<Y>.<k>` the first two numbers of the package's version, `m` 99 and build 99 for the estimate).

roundtrip and accept run `status` before anything is published, in one fresh environment for each
package of the batch that no other package of the batch is built on, so a file that fits two levels
there shows up as `CONFLICT` and stops the batch (the number `<m>` is then spent: release m+1); smoke
repeats it after publishing with each such package's README command, and can only report. The states
*between* two releases (a user who has only the lower packages installed) are protected by this list
alone.

## The batch release workflow

Inputs:

| Input | Meaning |
|---|---|
| `isabelle_build` | the build string of the pristine `isabelle` build to pin (required) |
| `isabelle_from` | `channel` (the build is on conda.qiyuan.me) or `run:<isabelle-packaging-ci run id>` (rehearsal against that run's `conda-packages` artifact, which must carry `isabelle_build` of the batch's `isabelle` version (`local-channel` refuses otherwise), a build the channel does not serve yet (`release-plan --rehearsal` refuses otherwise)) |
| `tool_ref` | the tag of this repository to build the tool from (default: the triggering ref) |
| `features` | the features to publish, space-separated, in any order; no default. Each is `<GitHub repository>@<release tag>`: the feature repository on GitHub, then `@` and the release tag, for example `xqyww123/Global_Form@Isabelle2026/global_form/1`; the build job finds the package directory there by itself. A release tag that a listed one is built on, directly or through others, need not be listed when its package is already on the channel for this `isabelle` build (if one is missing, conda cannot solve the environments of the roundtrip, accept and sessions jobs, and the batch stops before anything is published). The tags are all of one release line `<R>` (`release-plan` refuses a batch that spans two). When every feature package is republished for a new `isabelle` build of `<R>`, list, for each feature package with builds of `<R>` on the channel (build string `<build string prefix>_<n>`, for example `Isabelle2026_0`), the release tag `<R>/<feature>/<m>` of its highest version among those builds (`<m>` is that version's last number; `git tag --list` would also bring in tags not yet published), and every release tag those are built on, directly or through others, whose package is on that channel too. Give each as `<GitHub repository>@<release tag>`, where `https://github.com/<GitHub repository>` is the homepage of its package on the channel (the build job sets it from the `features` word; the owner's channel lists it as `home` in its `channeldata.json`). List them all in one dispatch; when that list would name a feature twice, split it into batches that each name every feature at most once, and dispatch them one after another, each once the batch before it is published, so that no release tag is in an earlier batch than a tag it is built on |
| `other_component` | an Isabelle_RPC-style component package on the channel that installs on this `isabelle` version, for `tools/accept`'s scenarios (c) and (e), which install a second component; default `isabelle-performant-ml`. GitHub gives an input dispatched empty its default. On a release line the component has no release for yet, (c) fails at creating its environment: release the component for that line first, or name another component that installs |
| `publish` | default `false`; `publish=true` together with `isabelle_from=run:…` fails at once |

The workflow's top `env:` block names two channels: `CHANNEL`, which the batch is published to and
reuses files from, and `OWNER_CHANNEL`, which serves `isabelle` and the owner's feature packages. In
this repository both are the owner's channel, read at https://conda-ci.qiyuan.me, which serves the
same files as https://conda.qiyuan.me but does not count their downloads; a copy sets `CHANNEL` to
its own ("A copy of the release workflow").

Jobs, in order: **build** (one `ubuntu-latest` job, `rattler-build` 0.69.1) reads the
`noarch/repodata.json` of `CHANNEL`, decides for every package of the batch, tool
included, whether to reuse the file already on `CHANNEL` or to build a new one and with which build
number (`tools/common.py: plan_builds`: reuse what is on the channel and is exactly what this batch wants,
skip served files that are not, build the rest with the next number; a feature package is exactly what the
batch wants when it pins this batch's `isabelle` build, `common.isabelle_pin`), checks out each release
tag of the batch from the feature repository that `features` names with it, where the package directory is
the one directory whose `patches/<R>/provenance.txt` has the line `release_tag: <release tag>`, renders
each recipe to build (`tools/render-feature-recipe`: version, the pins of its direct dependencies, the
`isabelle` pin, build string `<build string prefix>_<n>`, hooks, the common README text with the package's
own names, license and homepage, the component payload if
`tools/component_files.txt` exists), builds everything into one local channel, and checks the packages
(`tools/check-packages`: hooks present, `.bat` CRLF, `.sh` LF; exactly the planned files). It computes one entry for
each package of the batch that no other package of the batch is built on, uploads the artifact
`feature-packages` containing only `noarch/*.conda`, and uploads the artifact `feature-sources`: the
feature repository of each release tag of the batch, at that tag.
The next jobs run once per entry, each in a fresh environment that installs the entry's package at its
exact version. **roundtrip** (linux-64) copies the environment's `isa/` before the package is installed,
as the pristine tree, and runs `tools/check-roundtrip` against the installed tool and `features.d`; this
also shows that the published packages the entry is built on are the contents its changes were made
against. **accept** (linux-64, linux-aarch64, win-64; no macOS leg, whose runners are too slow; defined once
in the reusable `.github/workflows/accept.yml`, which `tests.yml` also runs on the toy channel) checks,
through `status` and the bytes of every touched file, that the environment is applied, that removing a
package reverses it, and that `--force-reinstall isabelle` re-applies it (the scenarios listed in
`tools/accept`). **sessions** (the same legs) builds HOL and runs the
`tools/release_build.sh` of each feature of the batch in the environment, each in its own repository at
its own release tag (a feature without one gets only HOL). `roundtrip`,
`accept` and `sessions` stop the batch; a failure whose fix changes a feature's tagged files costs that
feature's number `<m>`. **publish** (only `publish=true`) calls
`xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main` once with the artifact and the
two R2 secrets. **smoke** (linux-64, win-64) runs, for each entry, the install command of that package's
README, then `status`; it runs after publishing and only reports.

Versions and build numbers: a feature package's version is computed from its release tag (Words); its
build string is `<build string prefix>_<n>`; `n` is never typed by hand. Nothing is published if the same
(feature, version, `isabelle` build) is already on the channel: to change a README or template,
release a new version.

Recovery: a failed publish is resumed by **dispatching the same inputs again**; the files already on
the channel (indexed or merely uploaded) are reused byte for byte, so the upload guard of
`publish-conda.yml` does not refuse them. Re-running failed jobs of the same run works only while
the artifact exists (30 days).

Before `publish=true`, two conditions: the pristine `isabelle` build is published and green on the
channel, and no other publish is running in any repository that publishes to the channel
(`PUBLISH_REPOS` in `isabelle-packaging-ci`'s `scripts/sweep-old-versions.py` lists them; `publish-conda.yml`
rebuilds the channel index, so two publishes at once would overwrite each other's index).

## Secrets of the release workflow

- `CONDA_R2_ACCESS_KEY_ID` and `CONDA_R2_SECRET_ACCESS_KEY`, for `publish`
  (`gh secret set CONDA_R2_ACCESS_KEY_ID -R xqyww123/isabelle_patch_control`, which asks for the value;
  the same for the other);
- `PACKAGING_CI_ACTIONS_READ_TOKEN`, a token with Actions: read on `xqyww123/isabelle-packaging-ci`,
  for rehearsals only (`isabelle_from=run:…`);
- `ISABELLE_PATCHED_READ_TOKEN`, Contents: read, only when a feature repository is private.

This repository is in `PUBLISH_REPOS` of `isabelle-packaging-ci`'s `scripts/sweep-old-versions.py`.

## A copy of the release workflow

To release your own feature packages to your own channel, fork this repository. In the top `env:`
block of `.github/workflows/release-features.yml`, set `CHANNEL` (the address the workflow reads your
channel at), `PUBLIC` (the address your users install from) and `ISABELLE_REPOSITORY` (the Isabelle
repository that holds your release tags and the pristine tag they stand on; a fork of isabelle-patched
does). Keep `OWNER_CHANNEL`: it serves `isabelle` and the owner's feature packages, which yours may be
built on. Replace the publish job and its secrets with your channel's. In `common-readme.md` and its copy
in `README.md`, put `-c <your channel>` in front of `-c https://conda.qiyuan.me` in the install and update
commands, and write "all three `-c` arguments" where it says "both" (`tests/test_docs.py` checks the two commands).
Every batch of your fork also builds the tool package from your fork and publishes it to your channel.
The repair commands the tool and the hooks print name https://conda.qiyuan.me and conda-forge; for a
package from your channel, your users add it to them.

When your features are built on the owner's feature packages, your Isabelle repository is also the
`origin` of your shared trees, so it must hold the branch of each such base, up to the release you
merge, and its release tags; a GitHub fork copies them only once. Before merging a new release of
such a base, bring it over, in a clone of your Isabelle repository (your shared tree will do):

    git fetch https://github.com/xqyww123/isabelle-patched '+refs/heads/<R>/<base>:refs/heads/<R>/<base>' '+refs/tags/<R>/<base>/*:refs/tags/<R>/<base>/*'
    git push origin <R>/<base> 'refs/tags/<R>/<base>/*'

