# Design: the release workflow without a table of features

Status: draft 3, 2026-11-12, accepted. Draft 2 went through the focused re-review wf_f34599df-3e0 (3 concerns,
merged into two text fixes of section 6, marked where they stand; the judge: accepted once they are made, no
further re-review, nothing for the owner to decide). Draft 1 went through the two-turn adversarial review wf_9a50ccf2-533 (11 concerns;
the judge: the mechanism holds and needs no change, not accepted until four places of the proposed text are
corrected, then a focused re-review). Draft 2 makes the judge's seven author fixes. The owner on them: "不需要跟我
讨论的我不予置评"; on the two functional changes and their cost (section 10): "好". Paths are relative to the
patch tool repository (`/home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover`, HEAD dd94e20); line numbers
are HEAD's (the working tree also holds one uncommitted row, `[global_form]=...`, after line 184, which this
design removes with the table).

The owner's words this design answers, verbatim:
- the order: "请去掉那张"feature → 仓库"的表" (2026-11-12), after "这个投诉是真的，我需要严厉斥责你" about the
  complaint below;
- the principle the table breaks: "isabelle_patch_control 是通用的 / 我说构建成一条链只是针对我们自己的
  features，管理起来方便，但设计上是可以允许分叉的 / 在给用户的文档中不能假设/要求一条链，而是允许用户自己选择"
  (2026-10-30); "啥？肯定不是啊？你怎么能假设这个！我不是说了要通用的吗！" (2026-11-03); "你记得我跟你说过 SKILL
  必须是通用的吗？" (2026-11-05);
- the complaint, relayed by the session "global form" (a report, not an order): the release workflow
  "hard-codes a table of features, so a new feature cannot be released to conda without a commit to the patch
  tool's repository — contrary to the owner's order that the patch tool be general."

## 0. What this design is

The release workflow stops keeping a list of features. Whoever dispatches it names, with each release tag, the
feature repository on GitHub: each word of the `features` input becomes `<GitHub repository>@<release tag>`,
for example `xqyww123/Global_Form@Isabelle2026/global_form/1`. The build job clones that repository at that tag
and finds the package directory there by itself: the one directory whose `patches/<R>/provenance.txt` has the
line `release_tag: <release tag>`, which `make-patches` wrote when it made the tag.

After this, the release path names no feature repository and no package directory, and a new feature, the
owner's or anyone else's, is released without a commit to the patch tool's repository. One feature name stays
on the release path: the tool package gives dev_patches the package name `qiyuan-dev-patches`
(`isabelle_patch_control/names.py:3`, which release-plan and render-feature-recipe use through `package_name`).
Removing it is the separate item that comes next, on the owner's word (the patch tool plan, item 46: "做完我们
手头的之后就来做这个").

## 1. Today

- `.github/workflows/release-features.yml:172-185`, in the build job, is a bash table
  `declare -A REPO=( [expose_foreign]="xqyww123/isabelle-base-features expose_foreign" ... )`: feature name ->
  (GitHub repository, package directory). A feature not in it stops the batch at line 189
  (`::error::no repository for $feature in the table`).
- The table feeds three things: the clone URL (line 191, `https://github.com/$repo.git`, with the token when
  set), the package directory (`rows.txt`, line 196, which the sessions job reads at lines 385-389, and the
  renderer's argument, line 198), and the renderer's `--homepage https://github.com/$repo` (line 199).
- The `features` input (lines 42-45) holds only release tags. A release tag `<R>/<feature>/<m>` names the
  feature, not the repository that holds its package files.
- Two commits of other sessions only added rows (84e1d60, 7de9d22), and the docs make adding a row a step:
  RELEASE.md:200 ("Put your feature repositories in the build job's table") for a copy of the workflow, and
  SKILL 3.6 step 4 (`.claude/skills/isabelle-patch-feature/SKILL.md:286-287`, "Add the feature's row to the
  table in the patch tool's `.github/workflows/release-features.yml`, on order").
- `make-patches` makes the annotated tag `<R>/<feature>/<m>` in the feature repository at the commit that
  holds the package's `patches/<R>/` (`isabelle_patch_control/make_patches.py:240-260`), and that commit's
  `patches/<R>/provenance.txt` has the line `release_tag: <R>/<feature>/<m>` (lines 177-183). So at the tag,
  the package directory is the directory whose `patches/<R>/provenance.txt` has that line. Checked on every
  release tag of the local feature repositories, which `git ls-remote --tags` shows are all their tags on GitHub:
  `isabelle-base-features`, 5 tags of two lines, among them `Isabelle2026/fast_abbrev_printing/2`, where
  `fast_abbrev_printing/` is found and none of the other features' directories; `bicompose_rename_fix` and
  `sledgehammer_fact_trigger`, 2 tags each; `global_form` and `default_fact_qualifiers`, 1 each; all six of these
  give `.`; 11 tags in all. `light_locale`, `dot_syntax`, `local_type_abbrev`, `localized_record`,
  `local_datatype` and `qiyuan_dev_patches` hold no release tag yet. Each tag gives exactly one directory, the
  one in the table.

## 2. The input

`features`: the features to publish, space-separated, in any order, no default (as today); each is
`<GitHub repository>@<release tag>`: the feature repository on GitHub, written as GitHub writes it
(`xqyww123/Global_Form`), then `@` and the release tag. `@` because `<owner>/<repository>@<ref>` is GitHub's own
way to name a ref of a repository (a workflow's `uses:`). The repository is on GitHub, as today: the clone URL,
the read token and the homepage are GitHub's.

The input's description in the workflow (line 43) becomes: "The features to publish, space-separated, in any
order, each as <GitHub repository>@<release tag>: the feature repository on GitHub, then @ and the release tag
(xqyww123/Global_Form@Isabelle2026/global_form/1)".

A word without `<GitHub repository>@` (a dispatch in today's form) is refused by the plan step, before anything
is built (section 3).

## 3. `tools/release-plan` reads the input

`release-plan` already reads the `features` words (its positional arguments) and refuses a word that is not a
release tag (`tools/release-plan:79-83`). It now reads `<GitHub repository>@<release tag>`:

```python
ENTRY = re.compile(r"^([A-Za-z0-9-]+/[A-Za-z0-9_.-]+)@(.*)$")
...
for word in words:
    e = ENTRY.match(word)
    if not e:
        raise Refused(f"{word!r} is not <GitHub repository>@<release tag>")
    tag, m = e[2], TAG.match(e[2])
    if not m:
        raise Refused(f"{tag!r} is not a release tag <R>/<feature>/<m>")
    features.append((tag, m[2], build_string_prefix(m[1]), e[1]))
```

Each feature package of `plan.json` carries `"tag"` and `"repository"` (`xqyww123/Global_Form`);
`"repository"` takes the place of `"feature"`, whose only reader, the table lookup (release-features.yml:187-189),
goes (release-plan:115 and the docstring at :15 change to match). The refusals that follow (a feature named
twice, two release lines) are unchanged. The usage line and the docstring say
`<GitHub repository>@<release tag>...` and that `plan.json` carries the repository on to the build job, which
clones the tag from it.

Why `release-plan` and not the workflow's shell: the input is then read and checked in one place, which
pytest covers, and `plan.json` stays the one description of the batch that the build step reads, package by
package; the shell would otherwise split the words in two steps (the plan step's tags, the build step's
repositories) and join them back by tag.

## 4. The build step

The table goes. The loop reads the repository from `plan.json` instead of the table and finds the package
directory in the clone:

```bash
features=$(jq -r '.packages[] | select(.tag) | "\(.tag) \(.repository) \(.name)-\(.version) \(.file) \(.build_number) \(.action)"' plan.json)
while read -r tag repo key file n action; do
  url="https://github.com/$repo.git"
  [ -z "$TOKEN" ] || url="https://x-access-token:$TOKEN@github.com/$repo.git"
  git -c advice.detachedHead=false clone -q --depth 1 --branch "$tag" "$url" "src/$key" \
    || { echo "::error::cannot clone release tag $tag of $repo"; exit 1; }
  # the package directory: the one whose patches/<R>/provenance.txt make-patches wrote for this tag
  mapfile -t found < <(cd "src/$key" && find . -path "*/patches/${tag%%/*}/provenance.txt" -exec grep -lxF "release_tag: $tag" {} +)
  [ "${#found[@]}" = 1 ] || { echo "::error::$repo at $tag: ${#found[@]} package directories have patches/${tag%%/*}/provenance.txt of $tag (${found[*]}), not one"; exit 1; }
  dir=$(dirname "$(dirname "$(dirname "${found[0]}")")"); dir=${dir#./}
  ... (archive, rows.txt, render with --homepage "https://github.com/$repo", build: unchanged)
done <<< "$features"
```

`dir` is `.` or a path such as `fast_abbrev_printing`, the same values the table holds, so `rows.txt`, the
renderer call and the sessions job (lines 385-389) are unchanged. summary.json's `feature` (check-packages:79,
which the roundtrip job reads at release-features.yml:285) stays.
The comment above the step (lines 164-165) becomes: "Each release tag is cloned from the feature repository
that `features` names with it; its package directory is the one whose patches/<R>/provenance.txt is that
release's (make-patches writes `release_tag: <tag>` there). Each is archived under its key <package>-<version>."
The header comment (line 4) becomes "A batch is the feature release tags `features` lists, each with its
feature repository on GitHub, in any order, and the tool package."

The `::error::` after the clone names the input's two parts; git's own message (for example "Remote branch
... not found in upstream origin") is printed above it. The table was never a safeguard: only someone with
write access to this repository can dispatch, and that person already chooses the tags.

## 5. What does not change

- The tool package (`isabelle_patch_control/`): `tools/` and the workflow are not in it (`pyproject.toml:38-39`),
  so its version stays 1.1.0.
- `make-patches`, the provenance file, the tags, `render-feature-recipe`, `check-packages`, the jobs after build.
- `ISABELLE_PATCHED_READ_TOKEN` reads a private feature repository, as today.

## 6. The documents (new text)

- RELEASE.md:126, the `features` row, begins: "the features to publish, space-separated, in any order; no
  default. Each is `<GitHub repository>@<release tag>`: the feature repository on GitHub, then `@` and the
  release tag, for example `xqyww123/Global_Form@Isabelle2026/global_form/1`; the build job finds the package
  directory there by itself." The re-release sentence is split after "whose package is on that channel too",
  and a new sentence goes in there: "... and every release tag those are built on, directly or through others,
  whose package is on that channel too. Give each as `<GitHub repository>@<release tag>`, where
  `https://github.com/<GitHub repository>` is the homepage of its package on the channel (the build job sets it
  from the `features` word; the owner's channel lists it as `home` in its `channeldata.json`). List them all in
  one dispatch; when that list would name a feature twice, split it ...". The rest of the row stays unchanged.
  [Re-review wf_f34599df-3e0: draft 2 had put this sentence at the end of the row, where "each of them" read as
  the batches and the sentence seemed to apply to a first release too; this is round 1's placement.]
- RELEASE.md:141, the build job: "checks out every feature of the batch at its tag" becomes "checks out each
  release tag of the batch from the feature repository that `features` names with it, where the package
  directory is the one directory whose `patches/<R>/provenance.txt` has the line `release_tag: <release tag>`".
- RELEASE.md:200, a copy of the workflow: "Put your feature repositories in the build job's table, and replace
  the publish job and its secrets with your channel's." becomes "Replace the publish job and its secrets with
  your channel's."
- SKILL 3.4 step 8 (SKILL.md:256-257): "Its `features` input lists the release tags to publish, in any order,
  with those they are built on that are not yet published for this `isabelle` build." becomes "Its `features`
  input lists the release tags to publish, in any order, with those they are built on that are not yet
  published for this `isabelle` build, each as `<GitHub repository>@<release tag>` (for example
  `xqyww123/Global_Form@Isabelle2026/global_form/1`), where `<GitHub repository>` is the one that the `origin` of
  the feature repository of that release tag names." The next sentence and the pointer to RELEASE.md stay.
  [Re-review wf_f34599df-3e0: draft 2 named the `origin` of `<feature repository>`, the repository of the feature
  being released, also for its bases' tags, which live in their own repositories.]
- SKILL 3.6 step 4 (SKILL.md:286-287): the sentence "Add the feature's row to the table in the patch tool's
  `.github/workflows/release-features.yml`, on order." goes.
- `develop.md` names release-plan as "(reuse or build, which number)" (line 81): unchanged; it still is that.

## 7. Tests

- `tests/test_release_tools.py`: the `rp.plan` calls give `<GitHub repository>@<tag>` words. The existing
  assertion at :113 checks `p.get("repository")` instead of `p.get("feature")`: that is the check that the
  repository reaches `plan.json`, so no new assertion is added. `test_plan_refusals` gets one more row, a bare
  release tag (today's form), refused with "is not <GitHub repository>@<release tag>", and its row
  `light_locale/1` keeps "is not a release tag" by being given with a repository.
- `tools/tests/toy-channel.sh:279-282` calls `release-plan` the way the build job plans: its words become
  `toy/$f@$R/$f/1` (the toy packages are built from local directories; the repository is not read there).
- The build step's shell is not run locally; before the change goes to the owner, its lines run against every
  release tag of the local feature repositories, as in section 1, and actionlint checks the workflow. The real
  check is the next dispatch with `publish=false`, on order.
- No mutation check is planned for the shell lines (no test runs them); the pytest rows are mutation-checked
  (a parser that drops the repository, one that accepts a bare tag).

## 8. Internal documents, after approval

The patch tool plan (`ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md`) gets inline corrections by hand, pointing
here, at (HEAD's line numbers): decision 11, :1412-1416 ("固定表 `feature → (GitHub 仓库, 子目录, MLML contrib/
下的目录名)`"); the homepage-link note, :781 ("从发布 workflow 的固定表取"); :1371 ("发布 workflow 的固定表给
`--homepage`"); and the review table's row C4, :2269 ("决定 11 固定表与显式 `features`"). The dated history entry
at :651 stays as it is.

## 9. Rejected alternatives

- **The release tag records the repository** (`make-patches` writes the feature repository's address and the
  package directory into the tag's message or the provenance file; the workflow reads them from
  `ISABELLE_REPOSITORY`). Every tag that exists today lacks them, a tag cannot be changed, and every new
  `isabelle` build re-releases every feature under its existing tag; so the workflow would need a second way to
  find these tags' repositories, for as long as the line lives.
- **The dispatcher also gives the package directory** (`<tag>=<owner/repo>[:<dir>]`, the complaint's
  suggestion): one more thing to type and get wrong, while the tag's own commit already says which directory
  it is, without ambiguity.
- **The list kept elsewhere** (a repository variable, a file in isabelle-patched): the same table, in another
  place.
- **The repository read from the channel by the workflow** (the homepage link of a published package): a
  feature's first release has no package yet, and packages rendered before tool 1.0.1 have no link. A person
  re-releasing reads it there (section 6), because every package a re-release names is on the channel.

## 10. Approved by the owner ("好")

Functional changes:
1. The `features` input's words change from `<release tag>` to `<GitHub repository>@<release tag>`; a dispatch
   in today's form is refused at the plan step, before anything is built.
2. The build job finds each release tag's package directory in its repository (section 4) instead of reading it
   from the table.

Cost: whoever dispatches types each tag's repository. On a re-release of a whole line for a new `isabelle`
build, about ten words, each now about twice as long, the repository of each is read from its package's
homepage on the channel. Nothing else costs more than today.

The uncommitted `global_form` row goes away with the table; global_form is then dispatched as
`xqyww123/Global_Form@Isabelle2026/global_form/1`.
