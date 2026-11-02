# Releasing

How to release a feature is in the SKILL
[`isabelle-patch-feature`](.claude/skills/isabelle-patch-feature/SKILL.md) (section 3.4); this file
is its reference: why each step and each checklist point is there, the files of the package
directory, and the batch release workflow.

**Status today: no feature package can be released.** This repository's batch release workflow
`.github/workflows/release-features.yml` is written (with the recipe renderer
`tools/render-feature-recipe` and the tool's own `conda/recipe.yaml`; plan §5 step 5, specified in
plan decisions 10 and 11, which this file only summarises) but has not run yet: its first run is the
rehearsal of plan §5 step 7. Before that, the pristine Isabelle build of `isabelle-packaging-ci`
(its `RELEASE.md`) and the one-time setup at the end of this file must land. Until then
`make-patches` can tag releases in the repositories, and nothing publishes them.

The tool and the feature packages are conda packages on <https://conda.qiyuan.me>, all `noarch`,
built, accepted and published **together** by the batch release workflow. Every feature package pins
one exact `isabelle` build (`isabelle ==<isabelle version> <build string>`, for example
`isabelle ==2025.2 1`), so every new `isabelle` build is followed by a re-release of every feature
package: same version, build number plus one, new pin.

Words. This file uses the SKILL's words (feature, feature repository, base, base tag, release line,
shared tree, private tree, stock tree; its section 1), and these. The *owner* is the person who owns
isabelle-patched, the feature repositories and the channel. A *release tag* `<R>/<feature>/<m>`
(`m` = 1, 2, 3, …) marks a released commit. A release line `<R>` has a *build string prefix*, `<R>`
with `-` turned into `_` (`Isabelle2025_2`), and an *`isabelle` version*, the prefix without
`Isabelle` and with `_` turned into `.` (`2025.2`; `Isabelle2026` gives `2026`). The package built
from `<R>/<feature>/<m>` has the version `<isabelle version>.<m>`, with `.0` inserted when the
`isabelle` version has one number: `Isabelle2026/light_locale/1` gives `2026.0.1`,
`Isabelle2025-2/light_locale/1` gives `2025.2.1` (`dev.package_version`); a newer line's versions
are higher. The *package directory* (`make-patches --package <dir>`) holds the
`tools/` lists and receives `patches/<R>/` (the patch files, one per changed path under a *flat
name*: the path with `/` replaced by `-`, plus `.patch`; and `provenance.txt`). For light locale the
package directory is the feature repository itself, `contrib/light_locale`;
`contrib/isabelle-base-features` holds several features, one subdirectory each (`expose_foreign/`,
`future_assign_interrupt/`, `fast_abbrev_printing/`; its `golden/` is the test harness they share,
not a package), so there `--package` names the subdirectory. A *level* is the tool's reading of one
file on a user's machine: the number of the highest feature whose change the file carries (0 for
the pristine content); a file that fits two levels reads as `CONFLICT`.

## First-time setup of a feature repository

Before a feature can be released, its package directory holds, committed:

- `tools/patched_files.txt`: every path the feature changes, relative to the Isabelle tree, one per
  line in any order (`make-patches` gate (f) requires the set to equal the output of
  `git diff-tree -r --no-renames --name-only <base tag> <tip>`, which is how the SKILL makes it).
- `tools/signature_additions.txt`: every signature entry the feature adds to an `.ML` file, as
  `<path> <SIGNATURE NAME> <keyword> <name>` (gate (d), `isabelle-patch-control check-signatures`);
  empty if none.
- `tools/required_sessions.txt`: the sessions to build before a release; at least one, for example
  `Pure` and `HOL`. The feature's `tools/release_build.sh` builds them.
- `tools/release_build.sh`, unless the feature has none: how the feature is built before a release, by
  the author and by the batch release workflow's `sessions` job; what it should do is in the SKILL
  `isabelle-patch-feature`, 3.4 step 4.
- `tools/component_files.txt`, only for a package that also ships an Isabelle component (today
  light locale: `ROOT`, `Light_Locale.thy`, `README.md`, `LICENSE`): the files to ship under
  `share/<package>/`; they must be committed. Nothing refuses a package that lacks this file: it
  simply ships no component.
- `.gitattributes` with `*.patch -text`, in the package directory or at the top of the feature
  repository (`contrib/isabelle-base-features` has one there for all its features), so that a
  checkout on Windows does not CRLF-convert the patch files (the tool applies them byte for byte). Never hand-edit `patches/`: `make-patches`
  rewrites it on every release, one patch file per changed path.
- `README.md`: the feature's own README; the package's `share/doc/<package>/README.md` is this
  repository's `common-readme.md` followed by it. It also says where a release's sources are, by the
  tag only, no command: "The Isabelle sources a version of this package was made from, with this
  feature and the ones it is built on, are a tag of isabelle-patched named
  `<Isabelle release>/<feature>/<m>`, where `<m>` is the last number of the package's version:
  version `2026.0.1` was made from `Isabelle2026/<feature>/1`." Write `<m>`, not `<version>`:
  `common-readme.md` uses `<version>` for the `isabelle` version.

A feature's base is recorded as `base =` in the feature repository's `.gitmodules` (SKILL, section
1); its package depends on the base's package at exactly that package's version (`==<version>`,
for example `==2026.0.1`), which the recipe renderer computes from `base_tag`.

## Why the release steps are in this order

The checklist comes before the build and before `make-patches`: a failed point means a new commit,
and `make-patches` tags the release, so a failed point after it would use up the number `<m>`.
`make-patches` checks the repository-side gates (base tag, changed files, signatures, round trip
through the tool) before it writes anything; then each of its write steps can be rerun after a
failure, and the tag in the private tree comes last: it marks the release as done. The features
built on a released feature merge the release and are released in turn, because each package pins
its base's package at one exact version.

## Before releasing a feature: why each checklist point matters

The commands are in the SKILL, section 3.4 step 2. These points are about the *content* of the
feature and are not checked by code: feature packages are trusted. Points 1 and 4 are checked by
nobody but you; points 2 and 3 are checked by `make-patches` for your own feature's files, but not
for files that features below yours change.

1. **No file is changed back to exactly what it was at some lower feature's release** (this includes
   deleting a file a lower feature created, or renaming it). The tool tells "which features are
   applied" from the bytes of each file alone; a file whose bytes with your feature equal its bytes
   at a lower release fits two levels and reads as `CONFLICT`. Changing a lower feature's file further, or editing lines a lower feature added, is fine.
2. **Every hunk's context occurs only once in the file it changes.** Otherwise the forward patch can
   apply a second time at another place, the file then fits two levels, and `status` reads
   `CONFLICT`. Add a few more lines of context that are unique. `make-patches` gate (c) refuses this
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

The workflow's `roundtrip` and `accept` jobs run `status` with the whole batch installed before
anything is published, so a file that fits two levels with every feature installed shows up there
as `CONFLICT` and stops the batch (the number `<m>` is then spent: release m+1); `smoke` repeats
the check after publishing, on what the README's command installs, and can only report. The states
*between* two releases (a user who has only the lower packages installed) are protected by this list
alone.

## The batch release workflow

Inputs:

| Input | Meaning |
|---|---|
| `isabelle_build` | the build string of the pristine `isabelle` build to pin (required) |
| `isabelle_from` | `channel` (the build is on conda.qiyuan.me) or `run:<isabelle-packaging-ci run id>` (rehearsal against that run's `conda-packages` artifact, which must carry `isabelle_build` of the batch's `isabelle` version (`local-channel` refuses otherwise), a build the channel does not serve yet (`release-plan --rehearsal` refuses otherwise)) |
| `tool_ref` | the tag of this repository to build the tool from (default: the triggering ref) |
| `features` | the explicit list of feature release tags to publish, bottom first: the first one built on pristine, each next one built on the one before (`check-packages` refuses any other list); no default. Two features built on the same base go into separate batches, each from the bottom up to its own feature; the later batch reuses the lower packages the earlier one published. The tags are all of one release line `<R>` (`release-plan` refuses a batch that spans two). When every feature package is republished for a new `isabelle` build of `<R>`, take, for each feature package with builds of `<R>` on the channel (build string `<build string prefix>_<n>`, for example `Isabelle2025_2_3`), the release tag `<R>/<feature>/<m>` of its highest version among those builds (`<m>` is that version's last number; `git tag --list` would also bring in tags not yet published), and split these tags into batches as above: one batch for each of them that no other is built on, listing it and the features below it, bottom first |
| `other_component` | an Isabelle_RPC-style component package on the channel that installs on this `isabelle` version, for the `accept` scenarios that install a second component (plan §6 (c), (e)); default `isabelle-performant-ml`; on an `isabelle` version that no record of it installs on (a new release line before the component is ported), (c) fails at creating its environment: name another component, or give it empty to skip (c) and (e) |
| `publish` | default `false`; `publish=true` together with `isabelle_from=run:…` fails at once |

Jobs, in order: **build** (one `ubuntu-latest` job, `rattler-build` 0.69.1) reads the channel's
`noarch/repodata.json`, decides for every package of the batch, tool included, whether to reuse the
file already on the channel or to build a new one and with which build number
(`tools/common.py: plan_builds`: reuse what is on the channel and is exactly what this batch wants,
skip served files that are not, build the rest with the next number; a feature package is exactly
what the batch wants when it pins this batch's `isabelle` build, `common.isabelle_pin`), checks out
every feature of the batch at its tag, renders each recipe to build (`tools/render-feature-recipe`:
version, base pin, `isabelle` pin, build string `<build string prefix>_<n>`, hooks, the common README
text, the component payload if `tools/component_files.txt` exists), builds everything into one local
channel, checks each `.conda` (hooks present, `.bat` CRLF, `.sh` LF), uploads the artifact
`feature-packages` containing only `noarch/*.conda`, and uploads the feature repositories as the
artifact `feature-sources`: each repository once, at the tag of its highest feature in the batch, under
its directory name in MLML's `contrib/`. **roundtrip** (linux-64) installs `isabelle`
and the tool into a fresh environment, copies its `isa/` as the pristine tree, installs the top
feature, and runs `tools/check-roundtrip` against the installed tool and `features.d`. **accept**
(linux-64, linux-aarch64, osx-arm64, osx-64 on an Intel runner, win-64; defined once in the reusable
`.github/workflows/accept.yml`, which `tests.yml` also runs on the toy channel) installs the batch
into a fresh environment and checks, through `status` and the bytes of every touched file, that the batch
is applied, that removing a package reverses it, and that `--force-reinstall isabelle` re-applies
it (plan §6). **sessions** (the same five legs) installs the batch into a fresh environment, builds
HOL, and runs each feature's `tools/release_build.sh` in its package directory, in the order of the
batch (a feature without one gets only HOL). `roundtrip`, `accept` and `sessions` stop the batch; a
failure whose fix changes a feature's tagged files costs that feature's number `<m>`. **publish**
(only `publish=true`) calls
`xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main` once with the artifact and
the two R2 secrets. **smoke** (linux-64, win-64) runs the install command read from the copied
common README text and installs `qiyuan-dev-patches` on top, then `status`; it runs after
publishing and only reports.

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

## One-time setup still to do (by the owner)

Done 2026-11-02: this repository is in `PUBLISH_REPOS` (`isabelle-packaging-ci`'s
`scripts/sweep-old-versions.py`); `.gitattributes`. Left, because they need values only the owner has:

- the two R2 secrets: `gh secret set CONDA_R2_ACCESS_KEY_ID -R xqyww123/isabelle_patch_control` and
  `gh secret set CONDA_R2_SECRET_ACCESS_KEY -R xqyww123/isabelle_patch_control` (each asks for the
  value);
- for rehearsals only (`isabelle_from=run:…`): a token with Actions: read on
  `xqyww123/isabelle-packaging-ci`, set as `PACKAGING_CI_ACTIONS_READ_TOKEN` the same way.

`ISABELLE_PATCHED_READ_TOKEN` is needed only when a feature repository is private; every one is
public today.
