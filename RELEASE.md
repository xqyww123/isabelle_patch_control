# Releasing

The tool and the feature packages are conda packages on <https://conda.qiyuan.me>, all `noarch`,
built, accepted and published **together** by the batch release workflow
`.github/workflows/release-features.yml` of this repository (plan decision 11). Nothing goes to
PyPI any more: `my-better-isabelle-prover` 0.3.0 stays there untouched for pip users.

> The workflow is written in plan §5 step 5; until it lands, this file is the specification it
> follows, and no feature package can be published.

> **Release freeze.** No `isabelle` build is published until `isabelle-packaging-ci` builds the
> pristine Isabelle (its `RELEASE.md`). Every feature package pins one exact `isabelle` build
> (`isabelle 2025.2 <build string>`), so every new `isabelle` build is followed by a re-release of
> every feature package: same version, build number plus one, new pin.

## Before releasing a feature (checklist)

`make-patches` checks the repository-side gates (base tag, own commits, changed files, signatures,
tested record, round trip). The points below are about the *content* of the feature and are not
checked by code: feature packages are trusted, and the person releasing goes through this list
after `make-patches` and before dispatching the workflow. Each point says why it matters.

- [ ] **No file is changed back to exactly what it was at the bottom of the chain or at some lower
      feature's release** (this includes deleting a file a lower feature created, or renaming it).
      The tool tells "which features are applied" from the bytes of each file alone; two points of
      the chain with identical bytes cannot be told apart. Changing a lower feature's file further,
      or editing lines a lower feature added, is fine.
- [ ] **Every hunk's context occurs only once in the file it changes.** Otherwise the forward patch
      can apply a second time at another place, the file then fits two levels, and `status` reads
      `CONFLICT`. Add a few more lines of context that are unique.
- [ ] **No empty file is created or deleted.** git's block for an empty file has no `---`/`+++`
      pair and the tool cannot read its target.
- [ ] **Only regular files, mode `100644` or `100755`.** No symbolic links, no gitlinks, no file
      turned into a directory.
- [ ] **`etc/ISABELLE_ID` is not changed.** The tool locks on it.
- [ ] **The longest new patch file's path in the package cache stays within 198 characters** on
      Windows: `<package>-99-Isabelle2025_2_99/share/isabelle_patch_control/features.d/<feature>/<flat name>.patch`
      (use version 99 and build 99 for the estimate).
- [ ] **Patch files are not CRLF-converted and every changed path has exactly one patch file.**
      The feature repository's `.gitattributes` has `*.patch -text`; `make-patches` writes one
      block per path, so re-check after any hand edit under `patches/`.

The workflow's `roundtrip`, `accept` and `smoke` jobs run `status` on the whole installed chain, so
a multi-level file at the chain top shows up there as `CONFLICT` and stops the batch (the version
number is then spent: release v+1). Intermediate states are protected only by this list.

## Releasing a feature

1. In the Isabelle source repository, on the owner's order: `run-tree … build …` on the feature's
   private tree (writes the tested record), then `make-patches <feature> <version>`. It writes the
   package's `patches/<release>/` and `provenance.txt`, commits them in the feature repository, tags
   both repositories.
2. Go through the checklist above.
3. For every feature above this one in the chain: merge the new release into its branch, build,
   `make-patches` it with its next version (plan decision 11's example).
4. Push the feature repositories' branches and tags and the Isabelle source repository's tags.
5. Dispatch `release-features.yml` with `publish=false`, then, when all five legs are green, with
   `publish=true` (see below).

## The batch release workflow

Inputs:

| Input | Meaning |
|---|---|
| `isabelle_build` | the build string of the pristine `isabelle` build to pin (required) |
| `isabelle_from` | `channel` (the build is on conda.qiyuan.me) or `run:<isabelle-packaging-ci run id>` (rehearsal against that run's `conda-packages` artifact, which must carry `isabelle_build`, not build 0) |
| `tool_ref` | the tag of this repository to build the tool from (default: the triggering ref) |
| `features` | the explicit list of feature release tags to publish; no default |
| `session_build_legs` | legs besides linux-64 that also build the component session |
| `publish` | default `false`; `publish=true` together with `isabelle_from=run:…` fails at once |

Jobs, in order: **build** (one `ubuntu-latest` job, `rattler-build` 0.69.1) reads the channel's
`noarch/repodata.json`, decides for every package of the batch, tool included, whether to reuse the
file already on the channel or to build a new one and with which build number
(`tools/common.py: plan_builds`: reuse what is on the channel and is exactly what this batch wants,
skip served files that are not, build the rest with the next number), checks out the feature
repositories at their tags, renders each recipe (`tools/render-feature-recipe`: version, base pin,
`isabelle` pin, build string `Isabelle2025_2_<n>`, hooks, the common README text, the component
payload if `tools/component_files.txt` exists), builds everything into one local channel, checks
each `.conda` (hooks present, `.bat` CRLF, `.sh` LF), uploads one artifact `feature-packages`
containing only `noarch/*.conda`. **roundtrip** (linux-64) installs the batch into a fresh
environment and runs `tools/check-roundtrip` against the installed tool and `features.d`.
**accept** (linux-64, linux-aarch64, osx-arm64 with osx-64 under Rosetta, win-64) runs the
acceptance of plan §6. **publish** (only `publish=true`) calls
`xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main` once with the artifact and
the two R2 secrets. **smoke** (linux-64, win-64) runs the install command read from the copied
common README text and installs `qiyuan-dev-patches` on top, then `status`.

Versions and build numbers: a feature package's version is the version in its release tag; its
build string is `Isabelle2025_2_<n>`; `n` is never typed by hand. Nothing is published if the same
(feature, version, `isabelle` build) is already on the channel: to change a README or template,
release a new version.

Recovery: a failed publish is resumed by **dispatching the same inputs again**; the files already on
the channel (indexed or merely uploaded) are reused byte for byte, so the upload guard of
`publish-conda.yml` does not refuse them. Re-running failed jobs of the same run works only while
the artifact exists (30 days).

Before `publish=true`: the pristine `isabelle` build is published and green on the channel; no
other publish is running in any repository of `PUBLISH_REPOS`; the repaired `publish-conda.yml` has
been called across repositories successfully once.

## One-time setup (done, or on the owner's order)

- GitHub repository renamed `xqyww123/isabelle_patch_control` (done 2026-10-25, before any workflow
  referenced it); the superproject's `.gitmodules` follows.
- This repository enters `PUBLISH_REPOS` and the channel's `RELEASE_CHECKLIST.md`; two R2 secrets,
  a read-only token for the private feature repositories, an `actions:read` token for
  `isabelle-packaging-ci`; `.gitattributes` with `*.sh text eol=lf`, `*.bat -text`, `*.patch -text`.
