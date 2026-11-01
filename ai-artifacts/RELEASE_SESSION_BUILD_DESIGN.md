# Building sessions before a feature release (design, draft 10, 2026-11-01)

Draft 7 was reviewed (wf_76667951-cc1); draft 8 applied the author's fixes and put costs 6, 7 and 9 to
the owner; draft 9 recorded the owner's answers (2026-11-01): "A 发布时间不需要考虑"; "B 你在 SKILL 里写清就够了。
但要允许别人有特殊情况，就是不写构建脚本。你要灵活啊，别死脑筋只想着攻防！这里不是 cyber 场景！在我们场景里所有一切都是可信任的！写进
SKILL 里不牺牲任何而且又很灵活！"; "C 无所谓"; "D 可接受"; "E 可接受". Draft 9 had a focused re-review
(wf_38ceb3b1-6a0); draft 10 applies its fixes, all the author's; the judge ruled that no further design
review is needed (the code review re-reads the SKILL and document text).

## 1. What the owner decided

- **Build before publishing, on every platform.** Patch tool plan §0 item 42 (2026-10-30): "不能用 GitHub
  workers 在发布前真的编译一下吗？", "建议每个平台都做". Any failure stops the batch.
- **What is built.** "两类都编" (2026-11-01): HOL, and what each feature needs built (at least the sessions
  of its `tools/required_sessions.txt`; a feature without a script, a special case answer B allows, gets
  only HOL: cost 7).
- **A feature may use the sessions of the features it is built on** (2026-11-01: "只要这个 feature 是我的依赖项我
  就可以用呀").
- **How a feature is built is its repository's to configure; the patch tool gives at most a guiding
  principle** (2026-11-01: "既然是在 Github worker 上执行 isabelle build，那有很多配置方法啊，把这些放开交给具体的
  feature 仓库去配置不就好了。你最多给一个指导性的原则不好吗？干嘛写那么死？"). No restriction without a benefit
  ("为什么不能有 AFP？…你设置这种局限是不是毫无收益？"), nothing that holds only for today's features ("你不能只假设
  已开发的 features 啊还有未来的 features 啊"), no framework ("需要这个框架吗？"). Drafts 1–5's fixed `-d` rule, AFP
  input, generated argument list, Python scenario and toy Isabelle are all dropped.
- **Features may form a graph, not one chain** (2026-10-30: "设计上是可以允许分叉的；在给用户的文档中不能假设/要求一条
  链"; 2026-11-01: "你不能在 SKILL 里假设一个链式的结构啊"). Each feature has one base; several features can share
  a base. A batch is the path from `pristine` up to one feature: the release workflow's `features` input
  lists it, each feature after the one it is built on (`check-packages` refuses any other list; two
  features on the same base go into separate batches, RELEASE.md).
- **C1 confirmed** (2026-11-01, "确认 C1"): a feature's sessions are built with the features built on it
  installed as well.
- **Only the costs this brings to the process need the owner's approval**; the rest is the author's
  ("我只想知道你给整个流程带来的代价，需要我批准"). Section 6 lists them.

## 2. Facts this design rests on

- The `isabelle` package is the official release with its official heaps (isabelle-packaging-ci
  a45692f). Once a feature package patches Pure, `isabelle build` rebuilds Pure and every session above
  it from the patched sources, into the environment's user directory; later builds in the same
  environment reuse those heaps.
- A feature package installs its patches and, if its package directory has
  `tools/component_files.txt`, an Isabelle component under `share/<package>/`, which its post-link
  registers. Isabelle then knows the component's sessions. Test sessions are not in packages; they exist
  only in feature repositories.
- Isabelle refuses a session defined twice, for example once by a registered component and once by a
  `-d` directory with the same ROOT elsewhere (`src/Pure/Build/sessions.scala:824-850`).
- `isabelle build -d <dir>` reads `<dir>` with `Path.explode`, which refuses `:` and `\` in a path
  element (`src/Pure/Build/build.scala:433`, `src/Pure/General/path.scala:29`): a Windows path such as
  `D:\a\x` or `D:/a/x` is refused, a relative path such as `../light_locale/tests` is accepted.
- GitHub's Windows runners run steps under Git Bash; `isa\bin\isabelle.bat` keeps the working directory
  (`CHERE_INVOKING`, isabelle-packaging-ci `windows/isabelle.bat:51`).
- Feature repositories in MLML: `contrib/isabelle-base-features` (several features, one package
  directory each: `expose_foreign/`, `future_assign_interrupt/`, `fast_abbrev_printing/`; shared
  `golden/`), and one repository per other feature, whose package directory is the repository root
  (`contrib/light_locale`, `contrib/local_type_abbrev`, ...).
- The release workflow's build job (`release-features.yml` 151-175) clones, each at its tag, only the
  features whose package it builds, and has a table feature → (GitHub repository, package directory)
  without rows for fast_abbrev_printing, local_type_abbrev, localized_record, local_datatype and
  dot_syntax (their repositories exist on GitHub and are public).
- `make-patches` requires a committed `tools/required_sessions.txt` (gate 7).
- No feature repository has a build script today.
- A GitHub job stops after 360 minutes. In the old packaging CI, HOL took 7–11 min on Linux and
  Windows and 59 min natively on macos-14 (3 cores, 7 GB).

## 3. Design

### 3.1 In one paragraph

The release workflow gets a new job, `sessions`. On each of the five platforms it installs the whole
batch in a new conda environment, builds HOL, and then runs each feature's own script,
`tools/release_build.sh`, which builds what that feature needs. The scripts find the feature
repositories of the batch side by side, named as under MLML's `contrib/`, so one script serves both
places (3.5 says what differs). Publishing waits for this job on all five platforms.

### 3.2 The build job (changed)

1. The table gains a third column, the repository's directory name under MLML's `contrib/`, and the
   five missing rows. A row: `[light_locale]="xqyww123/Light_Locale . light_locale"`.
2. Its loop goes over every feature of the plan (today: only the ones to build). For each feature it
   clones the feature's repository at the feature's release tag, as today, and renders and builds the
   package only if the plan says to build it.
3. After the loop, for each repository it writes the tracked files at the tag of the repository's
   highest feature in the batch (for a repository with one feature: that feature's tag) as one tar file,
   `git archive --prefix=<contrib name>/ -o sources/<contrib name>.tar <tag>` (a tar keeps file modes
   and dotfiles, which an artifact of plain files loses).
4. The loop also writes `sources/batch.txt`: one line `<contrib name>/<package dir>` per feature, in the
   order of the `features` input, so that the table stays the only place the mapping is written.
5. It uploads `sources/` as the artifact `feature-sources` (kept 30 days, like `feature-packages`).
   `feature-packages` stays the only artifact `publish` publishes.

### 3.3 The `sessions` job (new)

`needs: build`; the five legs of the accept job (linux-64, linux-aarch64, osx-arm64, osx-64 on an Intel
runner, win-64); `timeout-minutes: 360`; `fail-fast: false`. On each leg:

1. Download `feature-packages` (and, for a rehearsal, the packaging CI run's `isabelle` package, as
   `roundtrip` does), index the local channel (`tools/local-channel`), and create a new environment with
   `isabelle=<version>=<build>` and the batch's top feature from the local channel, the online channel
   and conda-forge (the local channel's URL computed as `accept.yml` does, so that it also works on
   Windows).
2. Download `feature-sources` into `sources/` and unpack each tar file there (relative file names: on
   Windows, GNU tar reads `D:` as a host name).
3. `<env>/isa/bin/isabelle build -b HOL` (`isabelle.bat` on Windows).
4. For each line of `sources/batch.txt`, in order: if `sources/<line>` has `tools/release_build.sh`, run
   `bash tools/release_build.sh` there, with `ISABELLE` set to the environment's `isa/bin/isabelle`
   (`.bat` on Windows); otherwise print that the feature has no build script and go on.
5. A failure of step 3 or of any script fails the leg. Isabelle's output goes to the job log as it runs.
   On a failure the job uploads `sources/` (what the scripts wrote there, such as golden `.actual`
   files).

### 3.4 `publish`

`needs: [build, roundtrip, accept, sessions]`.

### 3.5 The guiding principle (written once, in the SKILL, 3.4 step 4; RELEASE.md points there)

`tools/release_build.sh` in a feature's package directory is how a feature is built before its release.
Write one. A feature may go without one in a special case, for example when it needs nothing built
beyond HOL; the release workflow then builds only HOL for it. The release workflow runs the script with
bash on all five platforms, in the package directory, with the whole batch installed and `ISABELLE`
naming the environment's Isabelle; a non-zero exit stops the batch. The script runs
`"$ISABELLE" build -b ...` on what must build before the feature is released, at least the sessions of
`tools/required_sessions.txt` (read the list rather than repeat it).

- **Where things are.** The feature repositories of the batch sit side by side under their MLML
  `contrib/` names, each at the release tag of its highest feature in the batch (so in a repository with
  several features, every feature's script runs from that one commit). A relative path such as
  `../light_locale/tests` reaches another repository both on GitHub and in MLML; give `-d` relative
  paths (Isabelle refuses Windows paths). Anything else the script needs (the AFP, another repository,
  options) it brings itself.
- **Sessions the batch ships as components.** In the release environment every package of the batch is
  installed, so Isabelle already knows every session any of them ships as a component (light_locale's
  `Light_Locale`, once it ships one); a `-d` for that session's source directory there defines it twice,
  while locally the same `-d` is needed. Give it only when Isabelle does not know the session yet, for
  example `dirs=; "$ISABELLE" sessions Light_Locale >/dev/null 2>&1 || dirs="-d ../light_locale"`.
- **The machines.** GitHub's standard runners: on macOS, Apple's bash 3.2 and BSD tools, 3 cores and
  7 GB (HOL takes about an hour there, minutes on a workstation), so a session `timeout` or an ML
  `Timeout.apply` that passes locally can fire: give it room, for example with `-o timeout_scale=<n>`;
  on Windows, Git Bash, with `$ISABELLE` being `isabelle.bat`.

### 3.6 Local use (SKILL)

- 3.4 step 4 carries the guiding principle of 3.5: build by running the feature's script in its package
  directory, with `ISABELLE` set to the private tree's `bin/isabelle` (an absolute path); a feature without
  one builds by hand as today. In MLML the other feature repositories are where the relative paths expect
  them (`contrib/`), as checked out; the release workflow takes each at the release tag of its highest
  feature in the batch.
- 3.4 step 8: unchanged procedure (`publish=false`, then `publish=true`; release time does not matter,
  owner's answer A); the five `sessions` legs join the checks it waits for.
- 3.5 step 1 (moving `daily`): run dev_patches' script the same way.
- 3.6 step 4 (opening a feature): `tools/release_build.sh` (3.4 step 4) is among the first files; the
  feature's row goes into the table of `release-features.yml`.

### 3.7 accept (changed: a build removed)

Today's accept builds a session `Accept_Light_Locale` only when the batch's component is literally
`isabelle-light-locale`, on linux-64 and the legs of the input `session_build_legs`; on win-64 it cannot
work (`-D` gets a `D:\...` path). The `sessions` job replaces it: removed are the step at
`accept.yml:107-115` and its line 139, the input `session_build_legs` (`accept.yml:48-50`,
`release-features.yml:39-42, 279`) and `--session-dir` in `tools/accept` (docstring, 247-249, 575). The
component registration checks of (a) stay.

### 3.8 Unchanged

The rest of accept, the toy channel, `tests.yml`, `roundtrip`, `smoke`, `make-patches`, and
`tools/required_sessions.txt` (still required by gate 7; the scripts read it).

## 4. Documents

- `release-features.yml`: the header comment (`build` also clones every feature of the batch and uploads
  `feature-sources`, `feature-packages` staying the one artifact published; the `sessions` job); the
  `publish` input's description ("when every check job is green").
- RELEASE.md: the jobs paragraph of "The batch release workflow" (`build` clones every feature of the
  batch and also uploads `feature-sources`; `sessions` stops the batch like `roundtrip` and `accept`;
  `publish` waits for it); the inputs table loses `session_build_legs`; "First-time setup of a feature
  repository": one bullet for `tools/release_build.sh`, conditional like the `tools/component_files.txt`
  bullet ("unless the feature has none"), pointing to SKILL 3.4 step 4; the `required_sessions.txt` bullet
  points to the script.
- SKILL: 3.4 step 4 (the guiding principle), step 8 (the five `sessions` legs), 3.5 step 1, 3.6 step 4.
- Patch tool plan: a new §0 item 43 (2026-11-01, revising the first bullet of item 42), quoting "两类都编",
  "只要这个 feature 是我的依赖项我就可以用呀", "你最多给一个指导性的原则", "确认 C1" and answers A–E, and stating: the
  `sessions` job builds HOL and runs each feature's `tools/release_build.sh`; the script, not the
  workflow, reads `required_sessions.txt`; a feature may have no script and then gets only HOL. Item 42
  then reads as done in decision 11, as revised by item 43, superseding item 35's session build.
  Decision 11 (the build job clones every feature and uploads `feature-sources`; the `sessions` job; the
  table's third column; `session_build_legs` and the sentence that linux-64 always runs (a)'s session
  build go); §6 (a)'s session sentence and decision 15's mention of it go. All by hand.

## 5. Testing

- The build job's new lines run locally against the real feature repositories (a plan of
  fast_abbrev_printing and light_locale at their current commits instead of release tags);
  `sources/` checked by hand.
- The `sessions` job's step 4 runs locally on that `sources/` with a stand-in `ISABELLE` that prints its
  arguments and a stand-in script.
- actionlint, locally and in `tests.yml` on GitHub.
- The new job first really runs at the first `publish=false` dispatch, as the rest of the release
  workflow. No `isabelle build` locally.

## 6. Costs for the owner

Approved (draft 4, "全都接受"; C1 "确认 C1"), with the wording the owner read restored:
1. Each run of the release workflow takes longer: Linux and Windows some ten to several tens of minutes,
   macOS possibly 2–3 hours (estimates). A batch builds HOL plus what its features' scripts build, which
   grows with the features on its path; if a leg reaches GitHub's 6-hour limit, the scripts must build
   less, and that failure costs a version as in 2.
2. A failure found at release time comes after the tag and costs a version of the feature that needs the
   fix. A feature's sessions are built with the features built on it installed (C1), so a lower feature
   can fail first in another feature's batch; the batch then waits, and a fix in the lower feature's tests
   or script is a new version of it, which every feature built on it merges and is released again (the
   existing coupling, plan §0 item 21).
3. Five more GitHub runners per run (free).

Answered 2026-11-01:
4. A feature's package directory gets `tools/release_build.sh`, written by its own authors (a feature may
   have none, cost 7); SKILL 3.4 step 4 and 3.5 step 1 run it where there is one, and otherwise build by
   hand as today. Accepted ("D 可接受").
5. Opening a feature includes adding its row (GitHub repository, package directory, `contrib/` name) to
   the table in `release-features.yml`. Accepted ("E 可接受").
6. The download counter stays paused, and real users' downloads go uncounted, for the whole of these
   longer runs; a run that outlasts the 6-hour pause needs the pause set again. Accepted ("C 无所谓").
7. A feature without the script: the SKILL says when to write one, and a feature may have none in a
   special case; the release then builds only HOL for it. No check anywhere ("B 你在 SKILL 里写清就够了。但要
   允许别人有特殊情况…在我们场景里所有一切都是可信任的").
8. Removed, no approval needed: accept's light_locale-only session build and the input
   `session_build_legs` (3.7).
9. Dispatches per release stay as they are (`publish=false`, then `publish=true`): the multi-hour job runs
   twice per release, and a new `isabelle` build's rehearsal run waits for it too. Release time does not
   matter ("A 发布时间不需要考虑").

Gone since draft 4: the fixed `-d` rule and the rules it put on feature authors, the AFP input, SKILL
section 1's new term.

## 7. After this change (not part of it)

The feature repositories' sessions write their own scripts (new files, on the owner's order); the author
tells them through the session "git 2026".
