# Design: stage 1 — the release path for any set of feature packages, license metadata, and finished documents

Status: draft 3, 2026-11-04, approved by the owner ("如果不需要跟我讨论，我不予置评"; then "请再次通读计划，
确保自洽，详细，然后准备 compact 然后开始实现"). Draft 1 went through the owner's two-turn adversarial review
(wf_d9f4e434-c94); draft 2 carried its fixes and the owner's two answers and went through a focused
re-review (wf_f697d39a-316: "acceptance met", no owner question, every fix the author's, no further round);
draft 3 carries those fixes and a read-through for consistency. Paths are relative to the patch tool repository
(`/home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover`, HEAD 917df32); line numbers are HEAD's.

【2026-11-05, after the implementation: an over-engineering audit, and the owner: "全部按你建议来". These
parts of the design are withdrawn, and where the sections below say otherwise, this note wins:
- **tools/feature-sources and its `order` command (5.6, 6.6 step 2)**: gone. The build job uploads the tar and
  row of every release tag; the sessions step runs, for each release tag of the entry's
  `batch_release_tags`, that tag's `tools/release_build.sh` in its own repository at its own tag, with the
  check that the directory exists. The order of the scripts does not affect them.
- **Refusal (d), "every direct dependency is published" (3.2), and with it `--owner-channel`, the saved
  repodata files and `isabelle_build` in plan.json**: gone. The roundtrip, accept and sessions jobs install
  the packages before anything is published, and conda's solver cannot solve an environment whose
  dependency is not published for this `isabelle` build (measured), so the batch stops there.
  `OWNER_CHANNEL` stays in the install lists.
- **Two versions of one feature in one batch (3.4, R3)**: withdrawn. release-plan refuses it again ("the
  batch names a feature twice"); tools/accept has no `--top-version` and no pinning; RELEASE.md's `features`
  cell says to dispatch one batch per version.
- **Refusals (c) and (e) of check-packages (5.2)**: gone; the summary's `install` is the README's first
  `conda create -n ` line, the common text's.
- **The renderer's committed-files check (8)**: gone; the renderer renders a fresh clone of the tag.
- **smoke step 2, the heap-paragraph count (6.4)**: gone; accept (a) checks it.
- **Tests (10)**: the toy script's self-made expected summary, its second tag order, its license assertions
  and the {t_four} batch on two channels; the pytests of the workflows' strings, of accept's helpers and
  of `changes_src`; the renderer's refusal cases of the committed-files check; most of gate 1's cases in
  test_make_patches.sh (kept: README removed, an untracked LICENSE, an uncommitted edit of
  tools/license.txt, two entries in tools/license.txt).
- After review wf_e97159a4-b31: tests.yml has no smoke-2026 (the owner: "A 按你建议来"; `smoke`'s t_three
  command installs the Isabelle2026 line, so both lines are smoke-tested; 6.5); plan_builds is keyed by
  package name again, as at HEAD (R3 withdrawn); the build job's table has no MLML contrib-name column
  (the side-by-side layout is cancelled, 6.6), so each release tag is archived under `<package>-<version>/`
  and rows.txt holds tag, key and package directory; RELEASE.md's `features` cell splits a list that names
  a feature twice into batches that each name every feature at most once, dispatched one after another so
  that no release tag is in an earlier batch than a tag it is built on.】

## 0. What this design is

The release workflow stops assuming that the packages it releases form one chain with one top.
`features` lists exactly the release tags to publish. Each listed package's direct dependencies (the
feature packages it is directly built on) are either in the same list or already published for this
`isabelle` build. The build job computes, from the packages it is about to publish, one entry for each
package of the batch that no other package of the batch is built on; each entry stands for the
environment conda builds when that package is installed. roundtrip, accept, sessions and smoke run once
per entry; inside one entry's environment every check works as today. A batch that is one chain gives
one entry: today's jobs and today's runner time.

Stage 1 also adds license and homepage metadata to feature packages, makes `make-patches` refuse a
release whose README, license file, license expression or build script is not committed as it is,
publishes the tool as 1.0.1 in the same batch as `bicompose_rename_fix` release 2, and removes from every
document the sentences that are working notes, true only of today's features, or about packages that are
not on the channel.

Stage 2 (a feature directly built on several feature packages) changes the tool's core and is designed
separately. The release path assumes nowhere that a package has one direct dependency or that the features
of one environment form a line: it takes their order from the tool's `status`. check-bytes and
tools/accept, which check the tool core's behaviour, describe today's core and change with it in stage 2
(section 11).

## 1. The owner's decisions this design carries out

Plan §0 items 46 and 47 record them with the owner's words. In short:
- The framework (the tool, the release workflow and `tools/`, accept, the SKILL, the user documents)
  must not assume that a batch is one chain or has one top, nor which features exist, their names,
  number or order; examples never name a package the channel may lack. The owner: "我们自己的包是全都要
  成链的，但你的 SKILL 与框架设计不能这么假设！" and "我跟你说的是"不能假设"，而不是"拒绝"！": nothing refuses
  or warns about any shape; no document preaches; a chain keeps working exactly as today.
- Other people use the framework: they write their own features, possibly on top of the owner's
  published packages, and release them with their own copy of the release workflow (their table,
  channel and secrets) to their own channel.
- The owner's model of a release: "对每个 feature 包，用户只要 specify 这个包直接依赖哪几个 feature 包，然后
  发布流程应该检查这几个 feature 包是否已经发布，且其发布内容是否与 worktree 上，改动是基于这些已发布的内容的".
  A direct dependency in the same batch counts as published.
- A feature may be built directly on several feature packages (stage 2).
- The batch is exactly the release tags `features` lists, plus the tool package.
- In each environment the sessions job runs the scripts of the batch's features only; dependencies that
  come from a channel do not run theirs (C1 narrowed to the batch).
- One batch may hold two versions of one feature (R3).
- Tool 1.0.1 in the same batch as `bicompose_rename_fix` release 2, after stage 1 is on main.
- License from a file in the package directory; homepage and repository links from the release
  workflow's table; `make-patches`' committed-files gate (labelled 7 today, gate 1 after section 9's
  renaming) also covers `README.md` always and `tools/release_build.sh` when present; `BSD-3-Clause` for bicompose_rename_fix and the three features of isabelle-base-features; no
  copy of Isabelle's `COPYRIGHT`; a one-time hand check of the dry run's artifact by the author.
- The common README text with `<package>` and `<feature>` (wording in section 7); the two new files
  `.github/workflows/smoke.yml` and `tools/feature-sources`; tests.yml grows by its toy jobs.
- The commands the tool and the hooks print keep naming https://conda.qiyuan.me and conda-forge (the
  owner: "就这样我觉得问题也不大？可以接受？").
- Documents: the SKILL's dated note at 3.9 is deleted; the AGENTS.md examples become `<package>`; the
  0.x migration text is deleted everywhere ("老版本的包不要管了。都被丢弃了"); RELEASE.md's "today light
  locale" goes; every other sentence of that kind is found and fixed (section 9). The SKILL stays MLML's
  procedure and may rely on everything in MLML ("可以假设 MLML 仓库的一切的，毕竟 MLML 本身也是公开的。是可以针对
  MLML 的"; MLML's CLAUDE.md and `ai-artifacts/` may be named): the aim is finished text, not text
  stripped of MLML ("我只是希望你别搞得跟草稿一样").
- The release workflow assumes the owner's channel as the source of `isabelle` and the owner's feature
  packages, also in a copy (section 3.5).
- A script of the sessions job no longer finds other feature repositories beside its own (section 6.6;
  the owner: "问题二 批准").

## 2. Terms

- **batch**: the release tags of one dispatch's `features` input, and the tool package.
- **direct dependencies of a release tag**: the release tags of the feature packages it is directly
  built on, read from its provenance (`base_tag`; `pristine` means none). Stage 1 reads them as a list,
  which today has at most one element.
- **environment of a package**: the package and every feature package it is built on, directly or
  through others; conda installs it when the package is installed.
- **entries**: one for each package of the batch that no other package of the batch is built on.
- **the copy's own channel**: `CHANNEL` of release-features.yml, where a batch is published and from which
  `plan_builds` reuses files; https://conda-ci.qiyuan.me (the owner's channel, read at an address the
  download counter does not count) in the owner's workflow.

## 3. The batch and its checks

### 3.1 `features`

`features` (release-features.yml:38-41): "The feature release tags to publish, space-separated, in any
order". It need not list what they are built on when that is already published for this `isabelle`
build. RELEASE.md:129 and SKILL 3.4 step 8 follow.

### 3.2 Every direct dependency is published

For each release tag of the batch and each of its direct dependencies: the dependency is a release tag
of the batch, or one of the channels the batch installs from (section 3.5) indexes a package of that name
and version that pins this batch's `isabelle` build (`common.isabelle_pin`, the pin `plan_builds` already
reads). Otherwise `check-packages` refuses before anything is published:

    <tag> is built on <dependency tag>, which is neither in this batch nor, for isabelle <v> <b>, on <channels read>: add it to `features`, or release it first

The check answers the same for every shape. The match uses `common.isabelle_pin`, the rule `plan_builds`
uses through `Wanted.accepts`; `<b>` comes from plan.json, which gains `isabelle_build`. `release-plan` takes
`--owner-channel <url>` besides `--channel` and writes the noarch repodata of both to files, one per
distinct address (CHANNEL's file holds the bytes the plan was computed from), and `check-packages
--channel-repodata <file>` (repeatable) reads those files, so the plan and the check see the same channels.
A package uploaded but not yet indexed is not counted: conda could not install it either.

### 3.3 The published content is what the changes are based on

`make-patches`' base-tag gate (labelled 0 today, gate 2 after the renaming; make_patches.py:150-158)
already makes every release tag stand on a release tag of its base. What the release path adds is that the bytes conda installs for each dependency are the
ones that tag was made against. `check-roundtrip`, which the roundtrip job runs, does exactly this for
a whole environment: it applies every installed feature directory (the dependencies from a channel or
the batch, then the package) to a copy of the pristine tree and compares the result with
`git diff-tree <pristine tag> <the package's release tag>` applied to another copy
(check-roundtrip:2-16). A package whose changes were made against other contents of a dependency than
the published ones fails there. It runs once per entry, and every package of the batch lies in some
entry's environment, so every dependency is checked against everything built on it. No new check is
needed; RELEASE.md and the SKILL say what roundtrip checks.

### 3.4 Two versions of one feature

`release-plan`'s refusal "the batch names a feature twice" (release-plan:75-76) goes. `plan_builds`
keys its result by (name, version) (common.py:139-148, release-plan:97-100). The build job keys each
release tag's clone and render directory by `<package>-<version>` (6.1). roundtrip, accept and sessions
install each entry by its exact `<package>==<version>` (5.7, 6.2); smoke runs the entry's README line, as
users do.

### 3.5 The channels a batch installs from

`isabelle` and the owner's feature packages are on the owner's channel only (conda-forge has no
`isabelle`). The release workflow assumes that channel, as the SKILL assumes MLML (the owner: "为什么不直接
强制 conda.qiyuan.me 上的包？都在用我们提供的 skill 了为何不直接假设这整个一套环境？"): one fixed value,
`OWNER_CHANNEL: https://conda-ci.qiyuan.me` (the owner's channel at the address the download counter does
not count), and no new input.
- **One block holds every value a copy changes**: the top `env:` block of release-features.yml holds
  `CHANNEL`, `PUBLIC` (moved up from the smoke job, :427), `ISABELLE_REPOSITORY` (the Isabelle repository
  that holds the release tags; it replaces the literal at :285) and the fixed `OWNER_CHANNEL`. No address
  is written in a reusable workflow's `with:` (GitHub does not allow `env` there): the build job re-exports
  `CHANNEL`, `OWNER_CHANNEL` and `PUBLIC` as job outputs, and the accept and smoke calls read
  `needs.build.outputs.*`; `run:` steps read `env` directly.
- Every install list is: the local channel, `CHANNEL`, `OWNER_CHANNEL`, conda-forge (release-features.yml
  :272, :368; accept.yml receives both values and passes each as `--channel` and `--start-channel`, which
  tools/accept:587-588 already accepts; the toy run passes neither). In the owner's workflow `CHANNEL` is
  `OWNER_CHANNEL`; conda keeps the first of a repeated channel (conda/base/context.py, `validate_channels`),
  so the owner's batches solve, download and run as today.
- `release-plan` saves the repodata of both (section 3.2); its rehearsal check (release-plan:81-87) reads
  `--owner-channel`, where `isabelle` lives.
- `plan_builds`' reuse and numbering, the download of reused files and publish read `CHANNEL` only; smoke
  replaces `PUBLIC` (6.4).
- RELEASE.md's section "A copy of the release workflow" (Appendix A) says what a copy changes.

## 4. The summary of the build job

`check-packages` writes `summary.json` = `{"environments": [entry, ...]}`, sorted by release tag:

    {"release_tag": "Isabelle2026/x/1", "package": "isabelle-x", "version": "2026.0.1", "feature": "x",
     "batch_release_tags": ["Isabelle2026/b/2", "Isabelle2026/x/1"],
     "isabelle_old_build": "7",
     "install": "conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-x"}

- `batch_release_tags`: the release tags of the batch in that environment, sorted (no order is
  implied; section 6.6 takes the order from the installed tool).
- `isabelle_old_build`: that package's own value from plan.json (section 5.3).
- `install`: the one line starting with `conda create -n ` in `share/doc/<package>/README.md` inside
  that package's `.conda` (the key of release-features.yml:441 and tests/test_docs.py:23).

Names that must differ between entries or release tags use `<package>-<version>` where `/` is not allowed
(artifact names, directories): conda's own name for one release tag, unique within a batch, which is one
release line (release-plan:77-79).

## 5. Tools

### 5.1 tools/common.py (test-side helpers, nothing in the tool's core)

- `entries(bases)`, where `bases` maps each release tag of the batch to its list of direct dependency
  tags: for each tag that no other tag of the map is built on, the tags of the map reachable from it
  through the lists (itself included). Data only; it imports nothing from `isabelle_patch_control`.
  check-packages calls it.
- `ships_component(index, files)`: the rule of check-packages:100-101, used by check-packages and by
  tools/accept.
- `changes_src(patch files)`: whether some patch target lies under `src/`, the condition under which
  the tool prints its heap paragraph, stated on the test side (api.py:73-75 is not changed).
- 【code review wf_db7e8161-b32, generality-G4】`direct_dependencies(provenance fields)`: the direct
  dependencies of section 2 (`base_tag` as a list, empty for a pristine tag), read in this one place;
  check-packages (section 3.2) and the renderer's pins (5.5) call it, so what is checked is what is pinned.

### 5.2 tools/check-packages

`check-packages --plan plan.json --channel-repodata <file>... --summary summary.json <file.conda>...`
replaces `--chain` (:87, :93-94). Refusals, each the same for every shape:
(a) `problems_of`, unchanged (:27-59);
(b) the `.conda` files are exactly the plan's (the bash comparison of release-features.yml:205-206
    moves here);
(c) the release tags inside the packages are exactly the plan's;
(d) section 3.2;
(e) each entry's README has exactly one `conda create -n ` line, and it ends with the package's own name.
`chain_problems` (:61-82) and the keys chain/top/top_feature/components (:97-103) go; the docstring is
rewritten in these terms.

### 5.3 tools/release-plan

Each feature package of plan.json gets its own `isabelle_old_build`: the highest `isabelle` build other
than `<b>` that an indexed record of that package (any version) pins, or "" (today's :109-112 for every
package instead of `wanted[-1]`). The top-level key and `top` go (:109, :114). The refusal of section 3.4
goes. It takes `--owner-channel`, writes the noarch repodata it reads to files and `isabelle_build` into
plan.json (section 3.2).

### 5.4 tools/check-bytes

Unchanged. Its walk (check-bytes:44-60) is the byte oracle's own copy of the order the tool gives one
environment; it changes with the core in stage 2.

### 5.5 tools/render-feature-recipe

- `fill()` (:76-77) takes keywords and replaces only the given `<key>`s. The README (:178) becomes
  `fill(common-readme.md, feature=..., package=...)` + the feature's README; `<version>` (common-readme
  :47, :54) stays for the user. A README with `<package>` or `<feature>` left is refused, as :100-101 does
  for the hooks.
  【Amended after code review wf_db7e8161-b32 (correctness-G1, documents-G1, tests-T4), the owner: "按你建议来":
  the README is `fill(common-readme.md + "\n" + the feature's README, feature=..., package=...)`, so the
  feature's own part is filled too (RELEASE.md's sentence with `<feature>` comes out right) and no
  `<package>` or `<feature>` can be left; the refusal goes, since it could only ever fire on the feature's
  own README, after the tag. Refusal (e) of 5.2 stays as approved, and no document adds a rule about it
  (a sentence first added to RELEASE.md promised the refusal for every package, while (e) reads the
  entries' READMEs only; the owner, after the focused re-review wf_c45ce7eb-83f: delete the sentence, keep
  the code).】
- License and the release-tag check: section 8.
- The base dependency (:159-162) becomes one exact pin per direct dependency (a list of one today).

### 5.6 tools/feature-sources (new; approved)

Run in the build job. Input: summary.json and the rows the clone loop writes, one per release tag of the
batch: `<release tag> <package>-<version> <contrib name> <package dir>`. For each entry it writes
`sources/<entry package>-<entry version>/`: for each release tag of the entry's `batch_release_tags`, its
repository at that tag as a tar made by `git archive --prefix="<package>-<version>/<contrib name>/" HEAD`
in the clone loop, and `scripts.txt`, one line per such tag: `<feature>
<package>-<version>/<contrib name>/<package dir>` (with `/.` dropped). For a chain batch every script still
finds its repository at its own release tag.

A second command, `tools/feature-sources order <scripts.txt>`, is the sessions step's order call (6.6),
run by the entry environment's own interpreter with `-I`. The file imports only the standard library at
module level, never tools/common.py (common.py:16 puts the checkout's package first on `sys.path`).
`ordered(status_out, lines)` refuses, naming the line, any scripts.txt line whose feature
`cli.read_status` does not name, then returns the lines sorted by that feature's position in `status`
(sorting cannot drop a line); the command runs `[sys.executable, "-I", "-m", "isabelle_patch_control",
"status"]` (the package has `__main__.py`, so win-64 needs no `Scripts/` path) and imports the installed
`isabelle_patch_control.cli` inside the function. This is a second use of the approved file, flagged to
the owner.

### 5.7 tools/accept

- `--component` goes (:582). `--top` stays a package name, "the package (a) installs; every scenario works
  in that package's environment", and `--top-version` comes from the entry. Every environment created from
  the top asks for `<top>==<top-version>`. After (a), every create or install that names a feature package
  builds its specs through one Leg helper, which pins each package at the version (a)'s environment holds
  (`Leg.records`, from conda-meta): (b1), (b2), (f)'s lower packages and subject, (m)'s reinstall.
  `conda remove` keeps names; (h)'s first environment keeps bare names, because it starts from the online
  channel at the old build. The docstring loses "(light locale today)" (:10).
- `Leg.components(e)`: the installed feature packages of the environment that ship a component
  (`ships_component`). (a) and (c) check that each of them is registered (:240-241, :335-336).
- (b1), (f1), (f2) run on one subject: the highest package of `leg.chain` of (a)'s environment that ships
  a component, else `--top` (replaces `a.component or a.top` at :291, :353, :365).
- (a) expects the heap paragraph once when `changes_src` holds for the environment's patch files, else
  not at all (replaces :237); (n) targets the first file that a feature of the environment changes
  without creating, and skips when there is none (replaces :530-532).
- (e) installs `--top`; (h) uses the entry's own old build.

## 6. Workflows

### 6.1 release-features.yml, build

- Header (:1-14) rewritten in the terms of section 2.
- Outputs (:66-73): isabelle_version, isabelle_non_pristine_build, run_id, environments
  (`jq -c .environments summary.json`). top, top_feature, component and isabelle_old_build go.
- The clone loop (:155-194): the fixed table and its loud failure stay (:161-172, :177); each release tag
  gets one directory key, `<package>-<version>`, for its clone (`src/$key`) and its render
  (`recipes/$key`); HIGHEST and batch.txt go; each clone writes its tar and its row (5.6).
  `render-feature-recipe` gets `--homepage "https://github.com/$repo"` (section 8).
- Check step: `check-packages --plan plan.json --channel-repodata <each saved file> --summary
  summary.json out/noarch/*.conda`, then `tools/feature-sources summary.json rows.txt sources/`.

### 6.2 roundtrip, accept, sessions, publish, smoke

- roundtrip: matrix `environment: fromJSON(needs.build.outputs.environments)`, fail-fast false; installs
  `<package>==<version>`; `check-roundtrip` with the entry's feature (its interface is unchanged).
- accept: `accept.yml` takes `environments` instead of top, component and old_build; matrix entry × leg;
  `--top-version` from the entry; artifact names gain `<package>-<version>`.
- sessions: matrix entry × the four legs; installs `<package>==<version>`; then section 6.6.
- publish: `package_name: feature-packages` (the input is only the job's label, publish-conda.yml:56-58).
- smoke: `uses: ./.github/workflows/smoke.yml` (6.4). The qiyuan-dev-patches step (:448-450) is deleted.

### 6.3 Why matrix cells, not loops inside a leg

An osx-64 sessions job takes 29-62 min per environment; a runner that dies loses one cell; a red cell
names its environment; a re-run redoes one cell.

### 6.4 .github/workflows/smoke.yml (new; approved)

Inputs: environments, channel, the public address it replaces (default https://conda.qiyuan.me, so
tests.yml does not change; a second input added to the approved file, flagged to the owner), tool_ref, and
an optional artifact for the toy channel (made into a `file://` channel by tools/local-channel). Matrix
entry × [ubuntu-latest, windows-latest]. Steps:
1. the entry's `install`, passed through `env`, with the public address replaced by the channel (keeping
   the check that the replacement changed something, :443), run and recorded;
   【Corrected after code review wf_db7e8161-b32, generality-G1: keeping the check that the command names
   the public address, tested directly, and refusing an empty public address; "the replacement changed
   something" falsely fails a copy whose `CHANNEL` and `PUBLIC` are one address. The owner accepted the
   remaining limitation for copies (review item B, "建议接受这个局限，不修"): the toy smoke replaces only the
   public address, so a copy's own online channel stays in a toy install command.】
2. the expected number of heap paragraphs (`changes_src` over the environment's installed patches) and
   the count of the installed tool's `texts.HEAP_PARAGRAPH` in the output, in two `python -I` processes
   (tools/common.py would shadow the installed package otherwise). This replaces the literal of :446,
   which the tool has not printed since a13cab3;
3. `status`, whose last line is `texts.ALL_APPLIED` (:451-458).

### 6.5 accept.yml and tests.yml

accept.yml: inputs top, component and old_build (:27-39) go; `environments` comes in; `online_channel`
gives way to the two channel addresses from the build job's outputs (3.5); the matrix is entry × leg; TOP,
the top version and OLD come from the entry. tests.yml: the toy-channel job outputs
environments for each line; accept and accept-2026 pass them; smoke and smoke-2026 call smoke.yml with the
toy artifact; lint (actionlint) checks every call against the reusable workflows' inputs.

### 6.6 The sessions step

1. Extract every tar of the entry's directory once, as release-features.yml:375 does today.
2. Before `isabelle build -b HOL`: `"$T/env/bin/python" -I tool/tools/feature-sources order
   <entry>/scripts.txt | tr -d '\r' > order.txt` (`$T/env/python.exe` on win-64), under today's `set -euo
   pipefail`, so a failing `status` or a refused line fails the step (5.6).
3. `isabelle build -b HOL`, then `while read -r feature dir` over order.txt with today's if/else and
   messages ("has no tools/release_build.sh: only HOL is built for it"), each script run as `(cd "$dir" &&
   ISABELLE=$isabelle bash tools/release_build.sh </dev/null)`, so that a script cannot read the order file.
   Nothing beyond bash 3.2. 【Code review wf_db7e8161-b32, tests-T2: before the if/else, a `dir` that is not
   in the sources fails the step ("::error::<feature>: <dir> is not in the sources"), so a mismatch between
   the build job's rows and feature-sources cannot pass as "only HOL is built".】

The order is the installed tool's, so the release path never sorts features itself. Each script runs with
its own repository at its own release tag, which SKILL 3.4 step 4 already promises ("the workflow takes
the feature repository at its release tag"); today a lower feature of a shared repository ran from a
higher feature's tag (release-features.yml:173, :191-193), and that goes. A script no longer finds other
feature repositories beside its own (approved by the owner): dependencies from a channel bring no sources (C1
narrowed), and sessions shipped as components are known to Isabelle in the environment anyway. SKILL 3.4
step 4's "reach another one … by a relative path such as `../light_locale/tests`" and §0 item 43's
side-by-side layout go. No script today reaches another repository
(isabelle-base-features/fast_abbrev_printing/tools/release_build.sh reaches `../golden`, inside its own
repository).

## 7. The common README text (approved wording)

- common-readme.md:3-4: "A *feature package* changes Isabelle's sources inside your environment when it
  is installed and puts them back when it is removed."
- :11: "Install Isabelle with the feature package `<package>`:"; :14: `conda create -n isabelle -c
  https://conda.qiyuan.me -c conda-forge isabelle <package>`.
- :31-42: "(`command not found` means that the environment is not activated, or that it has no feature
  package.) It names every feature in the environment, first the ones `<package>` is built on, then
  `<feature>`. A healthy environment ends like this:" followed by the block "Feature `<feature>` is
  applied." / blank line / "Everything is in order.".
- README.md:10-11: "… the text every feature package's README starts with, with `<package>` and
  `<feature>` replaced by that package's own names; …".
- common-readme.md:6-9 ("built on Isabelle itself or on one other feature package … do not work
  together") stays true in stage 1 and changes in stage 2.

## 8. License metadata and make-patches' committed-files gate (gate 1)

The gates of `make-patches` are numbered 1-5 in the order they run and named by what they check
(committed files, base tag, changed files, signatures, round trip; today labelled 7, 0, (f), (d), (c));
F5 in Appendix A is the new `--help` text. This section uses the new numbers.

- **One definition of what a release reads from a package directory.** `release_inputs(package)` in
  isabelle_patch_control/dev.py, next to `shipped_files` (dev.py:117-120), returns two lists of fixed
  relative paths:
  - required: `tools/patched_files.txt`, `tools/signature_additions.txt`, `tools/required_sessions.txt`,
    `README.md`, and the files `tools/component_files.txt` lists;
  - checked when present: `tools/component_files.txt`, `tools/release_build.sh`, `tools/license.txt`, and
    every `LICENSE` from the package directory up to the repository's top.
- **One check**, in dev.py, replacing `require_committed` (make_patches.py:97-106): it refuses a missing
  required path ("… is missing"); refuses any present path of either list that `git ls-files
  --error-unmatch` does not know; and runs one `git status --porcelain --untracked-files=all` over both
  lists, present or not, so that a staged or unstaged deletion is refused. Gate 1 and the renderer's
  release-tag check (render-feature-recipe:152-157, which adds `patches/<R>`) call it; write step (d)
  compares both lists between H and the commit to tag. `shipped_files` keeps its meaning (the renderer
  reads `payload[1:]` as the component list). The fixed path `tools/component_files.txt` also closes the
  earlier license review's open item: an uncommitted deletion of that list is now refused.
- **`tools/license.txt`**: read with `dev.listed()` like every `tools/*.txt` (`#` starts a comment):
  no entry means no license; one entry is the package's SPDX expression; more than one is refused by the
  shared reader at gate 1, before the tag.
- **The license file**: the nearest file named exactly `LICENSE` on disk from the package directory up to
  the repository's top, copied to `<out>/LICENSE` next to recipe.yaml; `about.license_file: LICENSE` only
  when one was copied. Measured with rattler-build 0.69.1 (judge of review wf_296d22d8-b8c): it lands byte
  for byte in `info/licenses/LICENSE`; `license` reaches `info/index.json` and repodata; `license_file`
  without the file fails the build; `license` alone builds.
- **homepage and repository**: `--homepage <url>` sets both; the workflow passes
  `https://github.com/<repo>` from its table row. Without the argument neither is written.
- **SPDX validity** is checked by rattler-build when the build job parses the recipe, after the tag: a
  misspelt or deprecated identifier (such as `GPL-2.0`) costs that feature's number `<m>`.
- The tool becomes **1.0.1** (pyproject.toml): gate 1, the gate names and the user texts of section 9
  are in the package.

## 9. Documents: finished text only

Every sentence that is a working note, true only of today's features, lines, machines or channel, a
reference a stranger cannot use, or an example naming a package the channel may lack, is deleted or
rewritten as finished documentation; no sentence warns or preaches. The list, checked file by file, is
Appendix A. Already decided:
- SKILL 3.9: the paragraph "**Isabelle2026 (2026-10-31):** …" (SKILL.md:347-348) is deleted.
- SKILL.md:100's "(cslh19)" stays (the owner's ruling of 11-02, MLML's
  ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md:1739).
- Before implementation the author amends by hand, in the plan's inline-amendment style, every passage of
  the plan's body that stage 1 makes false: decision 11 (`features` in any order; `isabelle_old_build` per
  package; `feature-sources` per release tag with scripts.txt; roundtrip, accept, sessions and smoke per
  entry; smoke without qiyuan-dev-patches; `OWNER_CHANNEL` in the install lists); §6 (h) (it starts from the
  entry's own package); decisions 10 and 14 (the README placeholders, license and homepage, one pin per
  direct dependency); decision 16 point 7 (the gate names, gate 1's inputs). The pointers to those
  decisions then stay. (Done 2026-11-04, before compaction: inline 【2026-11-04 …】 amendments in decisions 10,
  11, 14, 15, 16 point 7, the head of §6 and §6 (h).)
- AGENTS.md:17 and :95: `<package>`, defined where it first appears as a feature package's name.
- The 0.x text: AGENTS.md "## Coming from my-better-isabelle 0.x" (:161-184), README.md's section of that
  name (:77-82), the last line of the CONFLICT diagnostic "Upgrading from my-better-isabelle 0.x? See:
  isabelle-patch-control help" (texts.py:242), and their tests (tests/test_docs.py:36-37,
  tests/test_hooks.py:92) are deleted.
- RELEASE.md:56-57: "(today light locale: …)" is deleted.
- SKILL 3.4: step 3 "A first release first adds the files of 3.6 step 4" → "A release first adds the files
  of 3.6 step 4"; 3.6 step 4 gains `tools/license.txt` and `LICENSE` (formats in RELEASE.md); step 4's
  bullets follow 6.6; step 8 follows 3.1 and 6.2. A release of the same sources under a new number (only
  the feature repository changed) starts with an empty commit in the private tree, on order, as
  `make-patches` already says (make_patches.py:143-146): `git -C <private tree> commit --allow-empty -m
  "<R>/<F>: release <m>"`.
- RELEASE.md's list of package-directory files gains: "`tools/license.txt`, optional, read like the other
  lists: one SPDX license expression, or no entry for no license. The package's license file is the
  nearest file named exactly `LICENSE` from the package directory up to the repository's top; without one
  the package has no license file. rattler-build checks the expression only when the build job reads the
  recipe, after the tag, so a wrong or deprecated identifier (such as `GPL-2.0`) costs the feature's number
  `<m>`."

## 10. Tests (offline; nothing touches https://conda.qiyuan.me)

- **Toy channel** (tools/tests/toy-channel.sh): toy features name their bases; t_four on t_one beside t_two
  on Isabelle2025-2 only; one toy feature has a `LICENSE` and `tools/license.txt`. The summary is made as
  the build job makes it, in two tag orders, and compared with `cmp` against an expected summary.json the
  script writes from its own variables. On Isabelle2025-2 the script also makes the summary of the batch
  {t_four} alone (release-plan against a file:// channel saving its repodata, check-packages reading it;
  one entry, `batch_release_tags` [t_four]) and compares it with an expected file; t_one sits only on a
  second file:// channel given as `OWNER_CHANNEL`. The license assertions:
  that feature's `.conda` has the license in `info/index.json`, `info/licenses/LICENSE` equal to the
  committed bytes, and the license in the channel's repodata; another feature has none and still builds.
  The {t_four} run is an end-to-end run of the command-line wiring; no mutant is credited to it.
- **tools/tests/test_make_patches.sh**, its fixture shaped like the real layouts: H has a committed
  README.md from the start, so releases 1-5 run with the optional inputs absent; the component package's
  commit adds comp/README.md, comp/tools/license.txt with a `#` line and one entry, and
  comp/tools/release_build.sh, plus a `LICENSE` at H's top only (the isabelle-base-features shape), so
  comp's releases, write_order's reruns included, run with every input present. Each refusal is paired
  with a `saw` naming the file: README.md removed by a commit (a repository that never had one), refused
  with "… README.md is missing"; a listed component file removed by a commit; an
  uncommitted deletion of tools/component_files.txt; an uncommitted deletion of a package-directory
  `LICENSE` while the top one exists; an uncommitted edit of each optional input; an untracked nearer
  `LICENSE`; a present but gitignored release_build.sh; two entries in license.txt (refused, no tag); a
  change to the top `LICENSE` after the release commit, refused at write step (d).
- **pytest**: `entries()` on a chain, a tree, a forest, one feature and a deeper tree, under every
  permutation, byte-equal; check-packages's refusals (a dependency neither in the batch nor in any repodata
  file; a dependency whose name and version are indexed but whose `isabelle` pin is another build; a
  dependency indexed only at another version; plan/file and plan/tag mismatches; an install line naming
  another package) and its acceptance of a dependency indexed only in a second repodata file, with a record
  that pins the batch's build; the hand-over from release-plan to check-packages in
  tests/test_release_tools.py (`rp.cli` with argv as :156-159 does, `channel()` with a directory-name
  parameter): (a) the owner's setting, one address with the dependency on it, exactly one file saved; (b)
  the dependency only on a second channel; `feature-sources order` through `load()`: lines out of order
  come back in `status` order, and an unknown line is refused, naming it; release-plan with one feature at two versions whose
  next build numbers differ, one reused and one built, giving two files (replacing the refusal case at
  test_release_tools.py:175); `isabelle_old_build` per package; render: placeholders, `<version>` kept,
  license and homepage, the nearest of two LICENSEs (package directory and repository top with different
  bytes), `files/` unchanged, and two `test_refusals` parameters that delete a path which may be absent, so
  only the status check can see the deletion (tools/license.txt deleted in the working tree; the
  package-directory `LICENSE` removed with `git rm` while the repository-top one exists), each refused by
  the status check, not by "… is missing"; `changes_src`;
  accept's subject and its spec helper; feature-sources on fake repositories (two features of one
  repository at two tags, branching entries sharing a repository, any tag order); a static test that every
  `matrix.environment.<key>` used is a summary key, every artifact name in an entry matrix and every clone
  and render directory contains `<package>-<version>`.
- **Mutation checks** on the tests themselves (pytest: only FAILED lines count; the bash suites: a WRONG
  line; a mutant that does not load is reported separately): one entry from the last tag typed; entries in
  typed order; today's chain_problems; the old build of `wanted[-1]` for every package; install read from
  common-readme.md; the dependency check removed; a dependency on a channel refused; a dependency counted by
  name and version with any `isabelle` pin; `OWNER_CHANNEL`'s repodata ignored and release-plan saving an
  empty repodata file (both credited to the hand-over test); plan_builds keyed by name; an order-call line
  whose feature `status` does not name is dropped; order-call lines kept in scripts.txt's order; README copied
  verbatim; the component taken from the batch; feature-sources taking one tag per repository;
  `changes_src` always true; license read without `listed()`; gate 1 skipping absent required paths; the
  renderer's status check over present files only; write step (d) without the new inputs; a missing
  README.md accepted. 【After code review wf_db7e8161-b32: "README copied verbatim" is now the README
  without the fill (the refusal of 5.5 is gone); added "order-call lines sorted by feature name" (the order
  test uses a `status` order that is not by name, tests-T1) and "check-packages giving every entry one
  package's old build" (the fixture gives each package its own, tests-T3).】
- **Local runs** on linux-64: both toy lines, tools/accept --strict per entry, smoke.yml's steps by hand,
  one run of `feature-sources order` under a toy environment's interpreter with `-I` (showing that the
  installed package is the one imported), test_conda_hooks.sh, test_make_patches.sh, pytest, run-all,
  actionlint.
- **tests.yml on GitHub** (toy only): accept entry × five legs and smoke entry × two OS on both lines.
- **Not exercised before the first real dispatch**: release-features.yml's own wiring. The next real
  dispatch with publish=false runs all of it before anything is published; the author then checks its
  artifact by hand (section 12).

## 11. Stage 2 readiness

The release path reads direct dependencies as lists, computes entries by reachability (not by walking a
line), keys everything by release tag or `<package>-<version>`, and takes the order of an environment's
features from the installed tool's `status`. Stage 2 changes the tool's core (provenance's single
`base_tag`, make-patches' base-tag gate, new-tree `--base`, `link_chain` and the level model, the renderer's pins,
common-readme.md:6-9, AGENTS.md:21-28, reference.md:40-58) and with it the two checkers of the core's
behaviour: check-bytes, whose walk (check-bytes:44-60) is the byte oracle's own copy of the order the tool
gives one environment, and tools/accept, whose scenarios speak of the features below a feature or of the
lowest one ((b) with its pruning, (f), (n), and 5.7's subject). It also moves the naming exception
`dev_patches → qiyuan-dev-patches` (names.py) out of the tool, since it applies to any publisher's feature
of that name. 【After code review wf_db7e8161-b32: "the renderer's pins" means the reading of direct
dependencies, `common.direct_dependencies` (5.1), which the renderer's pins and check-packages share
(generality-G4); and when stage 2 reworks new-tree `--base`, new-tree takes the Isabelle repository from the
release line's shared tree's `origin` instead of its fixed URL (new_tree.py:35), the same address for the
owner, so that a copy's developers reach their own repository (generality-G3).】

## 12. Cost and the first release

- k = the number of entries (1 for every chain). Jobs per release: 2 + 12k; runner minutes about
  5 + 140k; each osx-64 sessions cell needs what one does today. tests.yml: +11 jobs, about +52 runner
  minutes (free on this public repository), macOS jobs 5 → 7.
- bicompose_rename_fix release 2 is made by its feature agent following the SKILL once stage 1 is on main
  and tests.yml is green on it. After its publish=false run, the author downloads `feature-packages` and
  checks `isabelle-bicompose-rename-fix-2026.0.2-Isabelle2026_0.conda`: license `BSD-3-Clause` in
  `info/index.json`, `info/licenses/LICENSE` equal to the repository's `LICENSE`, home and dev_url
  `https://github.com/xqyww123/Bicompose_Rename_Fix` in `info/about.json`; the owner then orders
  publish=true.

## Appendix A. Sentences to fix

From the author's own reading of the SKILL and two independent sweeps of every reader-facing text
(2026-11-04), merged, checked against the sources, the channel (`noarch/repodata.json` of
https://conda-ci.qiyuan.me: the only feature package is `isabelle-bicompose-rename-fix 2026.0.1`; the
`isabelle` builds are 2026 build 0 and the non-pristine 2025.2 build 0) and the feature repositories (no
`tools/component_files.txt` anywhere; light_locale's session is `Concepts`), and corrected by review
wf_d9f4e434-c94. A replacement is finished text. An item is labelled "stage 2" only when it describes the
tool's core (link_chain, the single base_tag, the base-tag gate, new-tree --base, the level model).

**Citation rule.** A citation of this repository's tracked plan (`ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md`,
"decision N", "plan §N") stays as a pointer to the rationale; it is rewritten only where the label stands
in for the reason the sentence needs, or for a thing the repository names itself (then the reason in a few
words, or the repository's own name, such as "tools/accept's scenario (h)"). Citations of documents this
repository does not hold are replaced by the reason: MLML's `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`
(make_patches.py:34-37, new_tree.py:23-24, check_signatures.py:15-16, check-roundtrip:4, the "migration plan
§0 item 32" of tools/tests/test_make_patches.sh:189), the review files (develop.md:4-5), and "the CI plan"
(tools/tests/toy-channel.sh:101, tools/tests/toy_isabelle.py:14). Draft history ("rev 6", "§12's fourth
draft", dates as history) and run ids given as reasons are replaced by the reason or deleted. The sweep was
`git grep -n -E "ISABELLE_PATCH_CONTROL_PLAN|ISABELLE_GIT_MIGRATION_PLAN|CODE_REVIEW|REVIEW[0-9]|plan
(decision|§)|decision [0-9]+|decisions [0-9]+|§[0-9]|patch tool plan|migration plan|rev [0-9]|\(b2\)" --
':!ai-artifacts'` (2026-11-04, HEAD 917df32); its 139 hits: the comments and docstrings of
isabelle_patch_control/, tests/, tools/ and conda/recipe.yaml that cite a decision of the tracked plan stay;
the workflow headers stay except where named below; develop.md's pointers to the plan and README.md:93
stay; every `§6 (x)` that names one of tools/accept's scenarios becomes "tools/accept's scenario (x)"
("scenario (x)" inside tools/accept): release-plan:22, :24, RELEASE.md:130, tools/tests/toy-channel.sh:195,
tests/test_release_tools.py:125, tools/accept:381, tools/tests/test_conda_hooks.sh:153; check-bytes:4's
"§6 (k)" stays as a pointer; the hits named in this appendix change as given.

**SKILL.md**
- :21 "`<R>/dev_patches`: the top feature; `<R>/daily` follows it." → "`<R>/daily`: the branch the
  shared tree follows; it follows `<R>/dev_patches` (3.5)."
- :23 "exactly one *base*": stage 2.
- :25 "(Isabelle2026 has no expose_foreign and no future_assign_interrupt)": delete.
- :40 "(Isabelle2026: `scalajs_demo.jar`, about 6 s)" → "(for example `scalajs_demo.jar`, new in
  Isabelle2026)".
- :211-212 → "The release workflow (step 8) runs it too, in every environment of a batch that holds this
  feature, and a failure there stops that release:".
- :215-224 step 4's bullets: finished text F4 below.
- :231-237 step 8: per 3.1 and 6.2 ("its roundtrip, accept and sessions jobs are green"; "Its `features`
  input lists the release tags to publish, in any order, with those they are built on that are not yet
  published for this `isabelle` build").
- :243-244 → "Build dev_patches as in 3.4 step 4 (when it has no `tools/required_sessions.txt`, the sessions
  the owner names) in its private tree, …".
- :262-263 3.6 step 4's list: "(light_locale does)": delete; add `tools/license.txt` and `LICENSE`.
- :306 "(Isabelle2026 added `/src/Tools/Scalajs_Demo/lib`)" → "(for example `/src/Tools/Scalajs_Demo/lib`,
  new in Isabelle2026)".
- :334-335 "(for Isabelle2026 a fast-forward, no commit; …)" → "(a fast-forward, with nothing to commit,
  while `<R2>/<F>` has no commit of its own; run `bash <feature repository>/init.sh` right after it)".
- :338-339 "(on Isabelle2026, for fast_abbrev_printing: expose_foreign and future_assign_interrupt)":
  delete.
- :347-348: delete (decided).
- :355 "Each feature repository's design document." → "Each feature repository's own documents: its
  README, and its `details.md` or the plans in its `ai-artifacts/` where it has them."

**common-readme.md and README.md** (README.md:15-72 embeds common-readme.md byte for byte)
- :3-4, :11, :14, :31-42: section 7 (decided).
- :48 (README :62) "such as `2025.2`" → "such as `2026`" (no feature package can exist for 2025.2: the
  channel has no pristine 2025.2 build).
- README.md:77-82, the 0.x section: delete (decided).
- README.md:88-89 the SKILL pointer → "how the features in MLML (<https://github.com/xqyww123/MLML>) are
  developed, released and upgraded to a new Isabelle release".

**AGENTS.md** (printed by `isabelle-patch-control help`; isabelle_patch_control/AGENTS.md is a symlink)
- :6-8 "for the developers of feature packages (developing a feature, releasing it, upgrading it to a new
  Isabelle release), the SKILL" → "for developing, releasing and upgrading the features in MLML
  (<https://github.com/xqyww123/MLML>), the SKILL".
- :17, :95: `<package>`, defined at :17 (decided).
- :77 "such as `2025.2`" → "such as `2026`".
- :161-184, the 0.x section: delete (decided).
- :21-28, :38 ("one *base*", "numbered … from the bottom", "bottom first"): stage 2.

**RELEASE.md**
- :8-14 "**Status today: no feature package can be released.** …": delete (the workflow has published).
- :18-19 "for example `isabelle ==2025.2 1`" → "for example `isabelle ==2026 0`".
- :28-31 the version examples from light_locale tags (none exists) → "`Isabelle2026/bicompose_rename_fix/1`
  gives `2026.0.1`; `Isabelle2025-2/expose_foreign/1` gives `2025.2.1`" (both tags exist).
- :33-39 "For light locale the package directory is …" → "When a feature repository holds one feature,
  its package directory is the repository itself; when it holds several, each has its own subdirectory,
  and `--package` names it."
- :46, :49, :99, :80 "gate (f)", "gate (d)", "gate (c)" and the list of gates: the gate names of
  make-patches (below).
- :56-57: delete the parenthesis (decided); :61 "(`contrib/isabelle-base-features` has one there for all
  its features)": delete; the list gains `tools/license.txt` (section 9).
- :89-91 "Points 1 and 4 are checked by nobody but you" → "Points 1, 4 and 5 are checked by nobody but you"
  (point 5, the Windows path length, is checked by no code).
- :113-116 → "roundtrip and accept run `status` before anything is published, in one fresh environment for
  each package of the batch that no other package of the batch is built on; smoke repeats it after
  publishing with each such package's README command."
- :129 the `features` cell: finished text F2 below.
- :130 "(plan §6 (c), (e)); … which has releases for Isabelle2025-2 (0.2.0) and Isabelle2026 (0.2.1)" →
  "for `tools/accept`'s scenarios (c) and (e), which install a second component; default
  `isabelle-performant-ml`."
- :131-161 the jobs paragraph: finished text F3 below. 【After code review wf_db7e8161-b32, documents-G3: F3
  is preceded by "The workflow's top `env:` block names two channels: `CHANNEL`, which the batch is published
  to and reuses files from, and `OWNER_CHANNEL`, which serves `isabelle` and the owner's feature packages. In
  this repository both are the owner's channel, read at https://conda-ci.qiyuan.me, which serves the same
  files as https://conda.qiyuan.me but does not count their downloads; a copy sets `CHANNEL` to its own ("A
  copy of the release workflow")." And, after the owner's answer to review item A, the README entry
  (:62-65) says the replacement covers both parts.】
- :178-190 "## One-time setup still to do (by the owner)" with "Done 2026-11-02 …" → "## Secrets of the
  release workflow": `CONDA_R2_ACCESS_KEY_ID` and `CONDA_R2_SECRET_ACCESS_KEY` for `publish`;
  `PACKAGING_CI_ACTIONS_READ_TOKEN` (Actions: read on xqyww123/isabelle-packaging-ci) for rehearsals only;
  `ISABELLE_PATCHED_READ_TOKEN` (Contents: read) only when a feature repository is private; this repository
  in `PUBLISH_REPOS` of isabelle-packaging-ci's `scripts/sweep-old-versions.py`. Plus the new section F1
  below.

**develop.md**
- :3-6 → "The design is the plan `ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md`; change the plan before
  changing the design." ("rev 6, with five plan reviews and the first code review next to it" and "No
  `isabelle build` in this repository without the owner's word." go).
- :72-78 the map of tools/: add tools/feature-sources and smoke.yml; :77 → "check-packages (inside every
  .conda; exactly the plan's files and release tags; every direct dependency in the batch or on a channel;
  the entries of summary.json)"; accept → "accept (the acceptance scenarios on one platform leg)".
- :97-105 the history of the texts' proofreading ("Three independent readers proofread …; the rest were
  written by the author and read once by three readers after code review 1."): delete that sentence; the
  rules for writing messages and "change the plan's §4 first" stay.
- :116-121 the test jobs: add `accept-2026`, `smoke` and `smoke-2026`; :121-122 "Kept local and uncommitted:
  …": delete.
- :138-140 "on the author's machine … (one run also stalled for an hour …)" → "about half an hour, most of
  it conda's solving."
- :152 "the scenarios of the first review's C3" → "stacked features that change the same file (a lower
  feature's lines inside an upper feature's hunk context; an upper feature moving a line a lower one added
  or renaming its file)".
- :154 "(the approved texts are compared word for word at least once)" → "(the texts are compared word for
  word at least once)".
- :182-186 "A check against the real features, done once by hand: … 34 paths …" → "The release workflow's
  `roundtrip` job runs `tools/check-roundtrip` against the real features of every batch."
- :190 "(run on the owner's order in a feature's private tree)" → "(run in a feature's private tree)".
- :196-200 "… the workflow itself runs for the first time in the rehearsal of plan §5 step 7." → "The conda
  recipe of the tool itself is `conda/recipe.yaml` (noarch python, `run: python >=3.12, git >=2.43`); the
  renderer and that recipe build the toy channel of tests.yml."; :200-203 the pin example → `isabelle
  ==2026 0`.
- :15-18, :27, :31-32, :142, :150, :167, :171-172 ("Link the chain", …): stage 2.

**reference.md**
- :67-68 `light_locale` / `isabelle-light-locale` → `<feature>` / `<package>`, as AGENTS.md.
- :203-205 "holds the texts of the design plan (`ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md` §4,
  decision 9) and every frame" → "holds every text the tool prints and every frame". 【Corrected after code
  review wf_db7e8161-b32, documents-G2 (that replacement contradicted the next sentence on refusals): →
  "holds the messages that `status`, `apply`, `unapply` and the hooks print, other than refusals and the
  lines `-v` and `--dry-run` print about each package, file and level (cli.py composes those), and every
  frame" (the focused re-review wf_c45ce7eb-83f, broke-4: those lines are composed in cli.py).】
- :40-58, :99-100, :128-129, :152-153: stage 2.

**The tool's help texts and code** (in the package: 1.0.1)
- make_patches.py docstring (`make-patches --help`, :1-31): finished text F5 below (the gates "7. … 0. … (f)
  … (d) … (c)" are labels of a plan outside this repository, make_patches.py:34-37); the refusal texts that
  say "gate 0" say "gate 2 (base tag)"; RELEASE.md, cli.py:20 ("release gate (d) on its own" → "the
  signature gate of make-patches, on its own") and check_signatures.py:3 ("Release gate (d) of
  make-patches" → "The signature gate of make-patches") use the names. The shared check of section 8 keeps
  today's refusal texts ("<path> is missing"; "<path> is not committed in the feature repository <H>: commit
  it first"; "uncommitted changes in the feature repository <H>: commit them first" with the status lines);
  the one new text is "<path> holds more than one entry: give one SPDX license expression, or none".
- make_patches.py:34-37, new_tree.py:23-24, check_signatures.py:15-16: the citation of MLML's migration
  plan, its draft history and its date → the reason in a few words.
- isabelle_patch_control/__init__.py:6 "Plan: ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md (rev 6)." →
  without "(rev 6)".
- render-feature-recipe:137 "(the feature's README, decision 10)" → "(the feature's README)".

**tools/, tests/ and workflows** (developer-facing)
- check-roundtrip:4 "Check (b2) of the migration plan (patch tool plan decision 17):" → "The round-trip
  check (patch tool plan decision 17):".
- release-plan:22, :24 "§6 (h)", "§6 (e) and (i)" → "tools/accept's scenario (h)", "scenarios (e) and (i)".
- accept:33 and :588 "(decision 11's one exception)" → "(the one scenario that starts from the online
  channel)"; accept:10 "(light locale today)": delete; accept:20, :22 "(k)" → "the byte check
  (tools/check-bytes)"; accept:492 "so far measured only under wine": delete.
- accept.yml:58 the job name "Accept (§6) on …" → "Accept on …".
- release-features.yml:17-18 "(… public since 2026-10-30)" → "(public)"; :319 "(run 41424597268)" → "# no
  osx-arm64: HOL alone takes about three hours on macos-15 (3 cores, 7 GB); arm64 is linux-aarch64's,
  macOS osx-64's"; :152-154: per 6.6.
- tests.yml:106-108 and toy-channel.sh:12-13 "after the first Isabelle2026 publish" / "as the online
  channel will" → "as the online channel serves them"; tests.yml's header gains smoke, smoke-2026 and
  accept-2026.
- tools/tests/toy-channel.sh:101 and tools/tests/toy_isabelle.py:14 "the CI plan" → "isabelle-packaging-ci's
  isabelle package"; tools/tests/test_make_patches.sh:189 "(migration plan §0 item 32, plan §0 item 35)" →
  "(a package that ships an Isabelle component, plan §0 item 35)".
- common.py `isabelle_pin` "e.g. `isabelle ==2025.2 1`" → "`isabelle ==2026 0`".

**Finished texts** (the RELEASE.md items above say "F1 … F5"; the jobs paragraph starts at RELEASE.md:133,
so the item ":131-161" means :133-161)

F1, RELEASE.md, new section after "Secrets of the release workflow":

> ## A copy of the release workflow
>
> To release your own feature packages to your own channel, fork this repository. In the top `env:`
> block of `.github/workflows/release-features.yml`, set `CHANNEL` (the address the workflow reads your
> channel at), `PUBLIC` (the address your users install from) and `ISABELLE_REPOSITORY` (the Isabelle
> repository that holds your release tags and the pristine tag they stand on; a fork of isabelle-patched
> does). Keep `OWNER_CHANNEL`: it serves `isabelle` and the owner's feature packages, which yours may be
> built on. Put your feature repositories in the build job's table, and replace the publish job and its
> secrets with your channel's. In `common-readme.md` and its copy in `README.md`, put
> `-c <your channel>` in front of `-c https://conda.qiyuan.me` in the install and update commands, and
> write "all three `-c` arguments" where it says "both" (`tests/test_docs.py` checks the two commands).
> Every batch of your fork also builds the tool package from your fork and publishes it to your channel.
> The repair commands the tool and the hooks print name https://conda.qiyuan.me and conda-forge; for a
> package from your channel, your users add it to them.

F2, RELEASE.md:129, the `features` cell:

> | `features` | the feature release tags to publish, space-separated, in any order; no default. A release
> tag that a listed one is built on, directly or through others, need not be listed when its package is
> already on the channel for this `isabelle` build (`check-packages` refuses a list that lacks one that is
> not). The tags are all of one release line `<R>` (`release-plan` refuses a batch that spans two). When
> every feature package is republished for a new `isabelle` build of `<R>`, list, for each feature package
> with builds of `<R>` on the channel (build string `<build string prefix>_<n>`, for example
> `Isabelle2026_0`), the release tag `<R>/<feature>/<m>` of its highest version among those builds (`<m>` is
> that version's last number; `git tag --list` would also bring in tags not yet published), and every
> release tag those are built on, directly or through others, whose package is on that channel too, all in
> one dispatch |

F3, RELEASE.md:133-161, the jobs paragraph:

> Jobs, in order: **build** (one `ubuntu-latest` job, `rattler-build` 0.69.1) reads the
> `noarch/repodata.json` of `CHANNEL` and `OWNER_CHANNEL`, decides for every package of the batch, tool
> included, whether to reuse the file already on `CHANNEL` or to build a new one and with which build
> number (`tools/common.py: plan_builds`: reuse what is on the channel and is exactly what this batch wants,
> skip served files that are not, build the rest with the next number; a feature package is exactly what the
> batch wants when it pins this batch's `isabelle` build, `common.isabelle_pin`), checks out every feature
> of the batch at its tag, renders each recipe to build (`tools/render-feature-recipe`: version, the pins of
> its direct dependencies, the `isabelle` pin, build string `<build string prefix>_<n>`, hooks, the common
> README text with the package's own names, license and homepage, the component payload if
> `tools/component_files.txt` exists), builds everything into one local channel, and checks the packages
> (`tools/check-packages`: hooks present, `.bat` CRLF, `.sh` LF; exactly the planned files and release tags;
> every direct dependency in the batch or on a channel for this `isabelle` build). It computes one entry for
> each package of the batch that no other package of the batch is built on, uploads the artifact
> `feature-packages` containing only `noarch/*.conda`, and uploads the artifact `feature-sources`: for each
> entry, the feature repository of each release tag of the batch in the entry's environment, at that tag.
> The next jobs run once per entry, each in a fresh environment that installs the entry's package at its
> exact version. **roundtrip** (linux-64) copies the environment's `isa/` before the package is installed,
> as the pristine tree, and runs `tools/check-roundtrip` against the installed tool and `features.d`; this
> also shows that the published packages the entry is built on are the contents its changes were made
> against. **accept** (linux-64, linux-aarch64, osx-arm64, osx-64 on an Intel runner, win-64; defined once
> in the reusable `.github/workflows/accept.yml`, which `tests.yml` also runs on the toy channel) checks,
> through `status` and the bytes of every touched file, that the environment is applied, that removing a
> package reverses it, and that `--force-reinstall isabelle` re-applies it (the scenarios listed in
> `tools/accept`). **sessions** (the same legs but osx-arm64, where HOL alone takes about three hours on
> GitHub's macos-15 runner; Poly/ML on arm64 is linux-aarch64's, macOS osx-64's) builds HOL and runs the
> `tools/release_build.sh` of each feature of the batch in the environment, each in its own repository at
> its own release tag, in the order `status` gives (a feature without one gets only HOL). `roundtrip`,
> `accept` and `sessions` stop the batch; a failure whose fix changes a feature's tagged files costs that
> feature's number `<m>`. **publish** (only `publish=true`) calls
> `xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main` once with the artifact and the
> two R2 secrets. **smoke** (linux-64, win-64) runs, for each entry, the install command of that package's
> README, then `status`; it runs after publishing and only reports.

F4, SKILL.md:211-224, step 4 from "The release workflow" on:

>    … The release workflow (step 8) runs it too, in every environment of a batch that holds this
>    feature, and a failure there stops that release:
>    - Commit the script and every file it reads, on order, before step 5: the workflow takes the
>      feature repository at its release tag, without `.git`, so the script cannot call git.
>    - Give every `-d` by a relative path inside the feature repository (Isabelle refuses Windows paths).
>    - The feature packages of that environment are installed there, so Isabelle already knows every
>      session they ship as an Isabelle component; give a `-d` for such a session only when Isabelle does
>      not know it yet: `dirs=; "$ISABELLE" sessions <session> >/dev/null 2>&1 || dirs="-d ."`.
>    - macOS has Apple's bash 3.2 and BSD tools, Windows Git Bash (`$ISABELLE` is `isabelle.bat`), and
>      the machines are slow (HOL takes about an hour on GitHub's macOS runners): give session `timeout`s
>      and ML `Timeout.apply` room, for example with `-o timeout_scale=<n>`.

F5, make_patches.py's docstring (what `make-patches --help` prints):

> make-patches [-C <tree>] --package <dir> [<R>/]<feature> <m>
>
> Release <m> (1, 2, 3, ...) of a feature, run in the feature's private tree <tree> (default: the current
> directory).  No network, nothing pushed.  <R> defaults to the release line of the branch checked out
> there.  The package directory <dir> lies in the feature repository H that registers the tree (new-tree
> --home); it receives patches/<R>/*.patch and patches/<R>/provenance.txt.  The base is the one H's
> .gitmodules records; branches and tags are the private tree's own (fetch first when the base was
> released elsewhere).
>
> Gates, in order, all before anything is written or tagged:
>   1. committed files: in H, <dir>'s README.md, tools/patched_files.txt, tools/signature_additions.txt,
>      tools/required_sessions.txt and the files tools/component_files.txt lists exist; these and, when
>      present, tools/component_files.txt, tools/release_build.sh, tools/license.txt (at most one entry)
>      and every LICENSE from <dir> up to H's top are committed and unchanged (see RELEASE.md, "First-time
>      setup of a feature repository"); H's .gitmodules registers the feature's two trees and <tree> is the
>      private one, clean and on <R>/<feature>, whose tip carries no release tag of this feature yet
>      (commit first; an empty commit releases the same sources under the new number).
>   2. base tag: `git merge-base --all origin/<base> <tip>` is one commit, exactly one release tag
>      <base>/* points at it, and the stock tree stands there (else rerun <H>/init.sh).  Every gate below
>      is relative to that tag.
>   3. changed files: `git diff-tree -r --no-renames --name-only` between the two equals
>      tools/patched_files.txt.
>   4. signatures: check-signatures with tools/signature_additions.txt.
>   5. round trip: the patch files (one `git diff-tree -p` block per file, under its flat name: the path
>      with `/` as `-`, plus `.patch`), generated into a temporary directory, replayed through the patch
>      tool's directory interface on `git archive <base tag>` forward and backward, compared by tree hash.
> Then, each step repeatable after a failure: the package's patches/<R>/ receives the files and the
> provenance file; H's release commit is made by path, of those files, .gitmodules and the two trees,
> whose gitlinks record the tip and the base tag's commit; the commit to tag (the new one, or the one an
> existing tag of this number points at) is checked to hold exactly the generated files, gate 1's files
> and those gitlinks; the annotated tag <R>/<feature>/<m> is created in H; and last in the private tree,
> whose tag marks the release as done.

Stage 2 rewrites gate 2's single `<base>`.
