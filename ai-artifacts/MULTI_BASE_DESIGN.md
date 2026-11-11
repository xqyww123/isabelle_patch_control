# Design: stage 2 — a feature built directly on several feature packages

Status: draft 3, 2026-11-11, accepted. Draft 1 went through the two-turn adversarial review wf_ed25f7bd-be6 (19
concerns; the judge: the central idea holds, not accepted until the owner decides four questions and the
author makes his fixes, then a focused re-review). Draft 2 went through the focused re-review
wf_d7f09e27-b15 (11 concerns; the judge: accepted once the author's fixes are made, no further re-review,
nothing for the owner to decide); draft 3 makes those fixes (the owner: "不需要跟我讨论的我不予置评"). The
code review of the implementation (wf_7128a081-b5a) corrected two points of section 7's mechanism, marked
where they stand (developer-1, developer-2, developer-4, developer-5; the owner again: "不需要跟我讨论的话，
我不予置评"). The owner's answers to round 1, verbatim:
- the functional changes of section 12: "先这样来，之后有问题再改";
- two features that cannot be combined: "让我一般地回答：如果多个互不依赖的 features 无法被同时以任意顺序安装
  时，就直接报错，拒绝" (sections 4, 5);
- the base of a feature with several bases: "为什么要合并？the releasing target feature 就应该构建在这样一个合并上
  对吗？我建议是去检查 the releasing target feature 用于生成其 patches 的 base commit 刚好就是所有 dependent
  features' commits of the expected version 没有任何新的改动" (section 7), and for the command that makes
  that merge, `new-tree --merge`: "可以在 new-tree 里加一个小用法，语法让我看一眼", then "可以";
- the naming exception: "做完我们手头的之后就来做这个" (section 11).
Paths are relative to the patch tool repository (`/home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover`,
HEAD 1ee67e8); line numbers are HEAD's.

## 0. What this design is

Today every feature is built on exactly one thing, Isabelle itself or one other feature, so the features
installed in one environment form a line, and the tool refuses two features built on the same thing.
After this design a feature may be built on several features, its *bases*; the installed features then
form a graph in which every feature comes after the features it is built on.

The one idea that carries the change in the tool: **a file's level becomes the set of installed features
whose changes the file carries**, instead of the number of the highest one. For a line of features these
sets are exactly today's levels, the check that finds a file's level makes the same `git apply` calls in
the same order, and every command does what it does today.

Two features of which neither is built on the other may be installed together, also when they change the
same file, as long as their changes to it apply in every order with the same result; otherwise the tool
refuses them (exit 3), as it refuses two features on one base today.

A feature with several bases is built, in its own branch, on a merge commit of its bases' releases that
adds nothing to them; `make-patches` cuts the patches against that commit and checks that it adds
nothing.

## 1. The owner's words

- 2026-11-04: "一个 feature 能直接建在多个 feature 包上"; "对每个 feature 包，用户只要 specify 这个包直接
  依赖哪几个 feature 包，然后发布流程应该检查这几个 feature 包是否已经发布，且其发布内容是否与 worktree
  上，改动是基于这些已发布的内容的"; "你要考虑除我之外的用户怎么用"; "我们自己的包是全都要成链的，但你的
  SKILL 与框架设计不能这么假设！".
- 2026-11-10: "这个你还没支持？这个很重要的，必须做的！"; "我认为我的需求很清晰，请你自主设计，设计后评审，
  如果有功能性上的改变，必须得到我的批准；如果某个设计的代价很高，也需要我批准"; and the answers quoted
  in the status note.
- Standing (plan §0 item 46, the over-engineering audit): no check or test for a situation that is only
  hypothetical; where a sentence in a checklist does the job, no code. Feature packages are trusted (plan
  decision 37).

Stage 1 (RELEASE_PATH_STAGE1_DESIGN.md) already made the release path read direct dependencies as lists
and compute environments by reachability; its section 11 lists what stage 2 changes.

## 2. Words

- **Bases** of a feature: the features (or Isabelle itself, the pristine release) it is directly built
  on; `base =` in the feature repository's `.gitmodules`, `base_tag` in its provenance file. A base may
  also be below another base.
- **Below** a feature: its bases, their bases, and so on. **Above** it: the features it is below.
  (The help already defines both words this way, AGENTS.md:20-24; with one base they mean what they
  mean today.) **Unrelated**: neither is below the other.
- **Depth** of a feature: 1 when its only base is Isabelle itself, else one more than its deepest base.
- **The environment's order**: the installed features by depth, then by package name. This is the order
  in which conda links feature packages (a feature package depends only on the tool, `isabelle` and its
  bases, render-feature-recipe:162-163; checked against conda 25.11.1's PrefixGraph), and conda runs
  their pre-unlinks in the reverse order. For a line it is today's order. One function in features.py
  computes the order and the sets below each feature; `link`, check-bytes and tools/accept all use it.

## 3. Provenance, and how the tool links an environment

- `base_tag` holds the base tags separated by single spaces (one today, so every released provenance file
  reads as before); `base_commit` stays one commit (section 7). `features.FeatureDir.base_tag` becomes
  `base_tags`, a tuple.
- `features.link_chain` (features.py:95-124) becomes `link`, which checks, then orders:
  1. a base tag that is a pristine tag of another release or build: `not_pristine`, first, as today;
  2. a base tag that is neither the tree's pristine tag nor the `release_tag` of an installed directory:
     `chain_broken` for that directory and that base, as today (directories by name, bases in order);
  3. the environment's order (section 2).
  The refusal "… are both made for … cannot be installed together" (features.py:110-113) no longer fires
  for two features on one base; "cannot be installed together" now means section 4's refusal.
- No check for a cycle among bases: a release tag exists before anything can name it as a base.

## 4. Levels (engine.py, decision 6)

For a file p, let P be the installed features whose patches change p.

- A **level** of p is a set S ⊆ P that holds, with each of its features, every feature of P below it.
  (For a line: the sets {}, {t1}, {t1, t2}, …, today's levels 0, t1, t2, ….) Its **tops** are its
  features that no other feature of it is above.
- The content of p at a level is the pristine content with the level's patches applied. The owner's rule
  makes this independent of the order: unrelated features must apply in every order with the same result.
- **The check.** p is at level S when, on a copy of its current content:
  1. reversing the patches of S from the last to the first (in the environment's order) succeeds step by
     step; this gives the contents of the levels on the way down;
  2. every level T, except a level with one top on the way down (step 1 gave its content), is computed
     from T without one of its tops U, by forward-applying U's patch, smallest levels first. When T has
     one top, that one step must succeed, else S is not the file's level. When T has several tops, T is
     computed from T without each of them; these steps must all succeed and give the same content (also
     the content step 1 gave, when T is on the way down). When one fails or two differ, T has no content,
     and the tops involved **cannot be installed together** (below).
  When any S that passes recorded such a failure, the command refuses (below), however many S pass.
  Otherwise exactly one S that passes is the file's level, and none or several is CONFLICT, as today.
- **Why a hand edit is still CONFLICT**: a one-top level is computed from exactly the features below its
  top, the content its patch was cut against; a hand edit near the patch makes that step fail, so the
  candidate fails. Only the steps that add a feature to content carrying an unrelated one can report that
  two features cannot be installed together.
- **The refusal.** When any S that passes recorded such a failure, the command refuses (exit 3, as
  `ChainBroken`) before writing anything: ``<package a> <version> and <package b> <version> cannot be
  installed together: their changes to <file> cannot be applied in every order.`` It names the two tops
  of the first failure recorded; levels are checked smallest first, so that is the pair whose changes
  meet. This also refuses two unrelated features that make the same change (the second one applied finds
  it applied; when one of them is already applied, two levels pass, each with the failure). It is raised in
  `api._session`, after the lock, during the replay every command makes, before anything reads CONFLICT.
- **For a line** every level has one top, step 2 is today's forward chain from the file's level upwards,
  and nothing new is checked: the same `git apply` calls in the same order. `Levels.tables[S]` holds every
  level's content computed while checking S, so the install still writes what the replay computed
  (decision 5 unchanged).
- `Levels.created` stays "the first patch creates the file". `mode_at(S)`: the mode of the last patch of
  S that creates the file, else of the first patch outside S that deletes it (today: ≤ L and > L).
- Cost: for a line, unchanged (a file with n levels: at most n(n − 1) calls). Two unrelated features on one
  file: 4 levels, at most 17 calls (6 for two features in a line); three: 8 levels, at most about 100.

## 5. The commands (model.py, api.py, cli.py; decision 7)

- **States**: a feature is `applied` when every file it changes carries it (it is in the file's level),
  `not-applied` when none does, `half-applied` otherwise, `CONFLICT` when a file it changes has no level.
  "Applied, but X below it is not" names the features below it that are not applied.
- **apply [--feature F]**: the features asked for are F and those below it (all, without `--feature`).
  The features applied are those, minus every feature that owns a CONFLICT file and the features above
  it. A file at level S moves to S plus those of them that change it. `apply` only adds.
- **unapply [--feature F]**: the features taken away are F and those above it (all, without
  `--feature`). A file at level S moves to S minus them. `unapply` only takes away; a feature unrelated to
  F stays applied (today a line has no such feature).
- Both targets are levels: the features asked for are closed downwards, those taken away upwards.
- **In the way**: for `apply`, the CONFLICT files changed by a feature asked for; for `unapply`, those
  changed by a feature taken away (plan decision 7's rule, in these words).
- **Exit code and last lines** with `--feature F`: F and the features below it, as today's words say.
- `Moves.applied` / `reversed`: the features that a move added to / took away from some file;
  `at_bottom`: every file at the empty level.
- **What it prints**: the features in the environment's order. A level is shown by its tops:
  `level 0 (original)` for the empty level, `level 3 (f3)` for one top (today's text), `level 3+5 (f3, f5)`
  for two; a CONFLICT file under `-v`: `levels 1, 3+5`. For a line every text is today's.

## 6. The hooks (conda_hook.py, decision 9)

- post-link: apply everything, unchanged. The complete CONFLICT diagnostic for the lowest CONFLICT feature
  s is written by the post-link of the last feature, in the environment's order, among s and the features
  above it (today: the chain top, which is that feature in a line; PKG_NAME unset or unknown counts as it,
  as today). Exact pins make every command that links s or a feature below s relink everything above s,
  and plan §0 item 26 reruns every post-link when `isabelle` is linked, so those commands write it exactly
  once. Only a command that links neither `isabelle` nor that feature, for example an update of a feature
  above s that is not below the last one (only a graph has such a feature), writes only the one-line hint
  that sends the user to `status`.
- The refusal of section 4 reaches the hooks through their existing paths: post-link writes
  `post_link_failed`; pre-unlink writes `chain_broken_removal` (no residue block); after a lock timeout,
  pre-unlink's recomputation without the lock catches it the same way (one line). The help's existing
  bullet for `cannot be installed together` (AGENTS.md:68-73: remove the one installed last; its `was not
  undone` is expected) applies word for word.
- pre-unlink F: `unapply --feature F` as in section 5. After a lock timeout, the residue's recovery names,
  each at its version, every feature among F and those above it that no installed feature is built on, in
  one `conda install -p …` line and one `conda remove -p …` line (in a line: the top alone, today's text).
  `texts.residue` takes a list of (package, version) pairs. Plan decision 9's "every block of one command
  names the same package" becomes: the block of the lowest feature the command removes, which conda prints
  last, names the packages whose reinstall brings back everything the removal took.

## 7. The developer subcommands (new_tree.py, make_patches.py, dev.py)

**The base commit.** A feature with one base is cut, as today, against the last commit of its base that
it has merged. A feature with several bases is cut against a merge commit M in its own branch: M's parents
are exactly the last merged commit of each base, and M adds nothing to them. M is the commit
`new-tree --merge` makes. A new branch with several bases starts at M; later, the developer's own
`git merge` of M takes it into the branch (that merge commit's parents are the branch tip and M), and M
reaches GitHub with the branch.

**Putting the bases together.** `dev.combine(repo, commits)` gives the tree of the commits' changes put
together. It first keeps only the commits that no other of them contains (`git merge-base
--independent`); one commit left is its own tree. Otherwise each commit's changes are taken since what it
shares with the others: from `dev.combine` of its merge bases with them (`git merge-base --all <commit>
<the others>`; one merge base is its own tree, several give the tree git's own merge would use as their
virtual merge base, which may be a tree, as `git read-tree` and `git diff-tree` accept), and the start X
is `dev.combine` of all those merge bases. 【Code review wf_7128a081-b5a, developer-1: draft 3 took
every commit's changes from one common commit of all of them (`git merge-base --octopus`), so with three
bases of which two share a lower feature, that feature's changes were counted twice and bases that
install in every order were refused. With two commits nothing changes.】 In a temporary index
(`GIT_INDEX_FILE`, as make_patches.py already does): `git read-tree X`, then for each commit its diff
(`git diff-tree -r -p --binary --no-renames`) through `git apply --cached --allow-empty
--whitespace=nowarn --no-ignore-whitespace` (as the tool applies a patch, engine.py:274, so that the
developer's git configuration can neither change the tree nor change which bases it refuses; an empty
diff, a base that only merges what the others hold, applies nothing — re-review wf_e2139a75-4ac), then
`git write-tree`; in every order of the commits, which must all succeed and give the same tree, else
refused naming the base that failed and the other bases that, since their merge base with it, change a
file it changes, with git's line about the file. This is the owner's rule of section 4,
applied to the bases while the feature is developed; in unusual shapes of the bases (lower features on
different lines whose changes to one file interleave) it can differ from what the tool computes per
feature, and the release workflow's roundtrip and accept jobs stay the last check.

**new-tree.**
```
new-tree <feature repository>
new-tree --home <feature repository> --base <R>/<base> [--base <R>/<base> ...] <R>/<feature>
new-tree --home <feature repository> --merge <R>/<base> [--merge <R>/<base> ...] <R>/<feature>
```
- `--base` may be given several times; `.gitmodules` records `base = <R>/A <R>/B`. Every base must be on
  the repository, as today. A new branch starts at the bases' branch tips put together: one base,
  `origin/<base>`, as today; several, a merge commit of those tips made as `--merge` makes it (every base
  counts as named), in the shared tree's clone before anything is registered, so that a refusal leaves H
  as it was (code review developer-2).
- `--merge`, after a fetch: each base is taken at `git merge-base --all origin/<R>/<base> <R>/<feature>
  <the named bases' tips>`, which must be one commit, else refused as today: a named base at its branch
  tip (`origin/<R>/<base>`, what SKILL 3.3 merges today), any other base at the last commit of it that the
  branch and the named tips together contain, which is exactly what set_up and gate 2 compute after the
  merge (in code, an extra-commits argument to the existing `dev.merge_base`). With several bases it
  names the branch's commit that already merges exactly these commits, if there is one (so a rerun with
  nothing new makes nothing; code review developer-5), else it makes a commit (`git commit-tree`, the developer's own identity) whose tree is `dev.combine` of
  them and whose parents are exactly them, writes it into the private tree's repository only, and prints
  each base's commit (with its release tag, or that it is not a release), the commit's hash and the
  command to run next: `git -C <private tree> merge --no-commit <hash>`. With one base it prints that
  base's tip and the same command, which is today's 3.3. It changes no branch and no file and pushes
  nothing. Refused: a name that is not one of the feature's bases; bases that `dev.combine` refuses; a base
  with several merge bases, as today (for example `--merge A` alone in a diamond whose other base has
  already taken a newer release of a feature below both: name both bases).
- The stock tree stands at the base commit: one base, the merge base (as today); several, the most recent
  commit of the branch whose parents are exactly the merge base of the branch with each base, or that one
  commit when they are all the same commit (code review developer-4: a line just opened); refused when
  there is none (the bases were merged without `--merge`: SKILL 3.3). One function decides this for
  `--merge`, set_up and gate 2 alike. It is fetched into the stock tree's
  clone from the private tree by hash (`git -C <stock> fetch -q <private tree> <commit>`, in place of
  `git fetch -q origin`, new_tree.py:131), which serves one base and several alike. `set_up` installs both
  trees' build products before it computes the stock commit, so that a refusal leaves both trees usable.
- The `ready:` line names each base's commit, with its release tag or that it is not a release of the
  base, and the base commit's full hash.
- The Isabelle repository is the shared tree's `origin` instead of the fixed URL (new_tree.py:35), as
  stage 1 section 11 decided.

**make-patches, gate 2 (base tags).** For each base: `git merge-base --all origin/<base> <tip>` is one
commit, and exactly one release tag of that base points at it (today's check, made for each base). With
several bases, the base commit is the most recent commit of the tip's history whose parents are exactly
those commits (refused when there is none), and its tree must equal `dev.combine` of them (refused, naming
the files that differ, when it holds anything more: the owner's "没有任何新的改动"). The stock tree must
stand at the base commit (else rerun init.sh). Gates 3-5 and the patch files are cut against the base
commit (today against the base tag, which is the same commit). The provenance file records the base tags
in `base_tag` and the base commit in `base_commit`; H's release commit records the stock tree's gitlink at
the base commit, which is on GitHub once the branch is pushed (SKILL 3.4 step 6).

## 8. The release path and its checkers

- `common.direct_dependencies` splits `base_tag` (common.py:75-78); release-plan, check-packages, the
  renderer's pins and the workflows already take lists (stage 1).
- check-roundtrip: unchanged. An environment is everything below its top; the top's release commit is
  what the tool gives.
- check-bytes: orders the packages with section 2's function instead of walking a line (check-bytes:44-60).
  Each patch of a feature G on a file p records its pre-image for the set of features below G that change
  p, and its post-image for that set plus G. A file's expected blob is the one recorded for the set of
  applied features that change it (no feature applied: the isabelle package's content, as today); when no
  patch records that set, the file is not checked and is listed with the others it does not check. For a
  line this is today's rule. t_five's patch on b.ML records the blob for t_two and t_four together.
- tools/accept: reads below and above from section 2's function instead of positions in a line: (b) the
  subject's environment holds the features below it; (f) after the CONFLICT, the features above the
  subject are not applied and every other one is, and the file it edits is one no other installed
  feature changes. The pruning shapes and (i), (m) need no change (the environment of `--top` is
  everything below `--top`, and `--top` is last in its order).
- The tool becomes 1.1.0 (the hook interface is unchanged); the renderer pins `isabelle-patch-control
  >=1.1,<2`, since a 1.0 tool reads `A/1 B/1` as one tag. Released packages need no new release.

## 9. Documents

- common-readme.md:6-9 and README.md:21-24: "built on Isabelle itself or on other feature packages, which
  conda installs with it"; the sentence "Two feature packages built on the same feature package, or both
  directly on Isabelle, do not work together." becomes "Two feature packages, neither built on the other,
  that change the same part of a file do not work together."
- The help (isabelle_patch_control/AGENTS.md:20-27): :20-21 read "one or more *bases*: Isabelle itself or
  other features … together with its bases' packages"; the sentence at :21-23 becomes "Two feature
  packages, neither below the other, that change the same part of a file do not work together: conda
  installs both, but the tool then refuses (exit 3) until one of them is removed.", placed after the
  definition of below and above (the help defines "below", so it says "neither below the other", while
  the README keeps "neither built on the other"); numbering by the environment's order; the level as in
  section 5; the bullet at :68-73 unchanged.
- reference.md:38-66 and :97-130: linking, levels and the refusal as in sections 3-5; the environment's
  order in section 2's words. develop.md: `link`, the model.
- RELEASE.md:67-69, 78-79: "its bases' packages", each at one exact version; a feature takes a newer
  release of a feature below it only once each of its bases built on that feature has released on it.
  RELEASE.md's "A copy of the release workflow" gets one paragraph for publishers who build on the
  owner's packages: their Isabelle repository must hold each such base's branch and release tags, which a
  GitHub fork copies only once; before merging a new release of such a base they fetch it from
  `https://github.com/xqyww123/isabelle-patched` and push it to their own `origin`.
- The SKILL (general, no feature named):
  - section 1: one or more bases; the stock tree at the base commit; the base tags, one per base; every
    command of 3.4 that names `<base tag>` (steps 2 and 3) uses `<base commit>` (the stock tree's
    `git rev-parse HEAD`, or the full hash on the `ready:` line), and step 1's `<base tag>` becomes one base
    tag per base;
  - 3.3: `new-tree --merge <R>/<base>` for the bases you are told to merge, then the `git merge --no-commit`
    it prints (one base: the same as today); you can release only once each base's last merged commit is a
    release of that base. With several bases, take a newer release of a feature below them, directly or
    through one base, only once each of your bases built on that feature has released on it (check as in
    3.4 step 1), and then merge those bases together in one `new-tree --merge <R>/<A> --merge <R>/<C>`:
    merged one at a time, a base and your branch have two merge bases, and new-tree, init.sh and
    make-patches refuse. (This replaces round 1's "one base per merge" wording and keeps its intent: merge
    only the bases you are told to merge.);
  - 3.4 step 1: with several bases, run `git -C <private tree> tag --merged <base tag> --list '<R>/*/*'`
    for each base tag. A feature whose tags appear in two of these lists (a base's own tags included) must
    have the same highest number in each, because each package pins its bases at one exact version and
    conda installs one version of a package; otherwise tell the owner. Step 7: each feature on this one
    merges this release (3.3) and is released in turn, in the order 3.3 states; its grep finds a feature
    among several bases;
  - 3.6 and 3.9 pass `--base` once per base; 3.9 step 4: with several bases the new branch starts at a merge
    of the bases, so merging a base that moved since is a real merge, committed on order before init.sh;
  - 3.7: changing the `base` list.

## 10. Tests

- Unit: `link` (order by depth then name, a base not installed, two features on one base together);
  levels on a graph (two unrelated features apart on one file, installed in both orders; a feature built on
  both; changes too close giving the refusal; the same change in both, with one of them applied before the
  other is installed (two levels pass), giving the refusal; a hand edit next to an unrelated feature's
  change giving CONFLICT); the commands' targets (`unapply --feature` leaves an unrelated feature
  applied; `apply`'s cap leaves an unrelated feature applied); the hooks' pre-unlink of one of two unrelated
  features, and the residue after a lock timeout on a graph.
- tools/tests: test_trees.sh registers a feature on two bases (branch and stock tree at the merge), then
  `--merge` after a base advances, with one base below the other (a feature on R/base and R/other, where
  R/other is built on R/base; `--merge R/other` after R/other has merged and released a newer R/base); test_make_patches.sh releases it (provenance with two base tags) and
  refuses a merge commit that holds an extra change.
- The toy channel (Isabelle2025-2): t_five on t_two and t_four; t_two's and t_four's changes to b.ML are
  moved apart (b.ML gets more lines), and t_five changes b.ML too, so that the byte check covers b.ML at
  t_two and t_four together after pruning. Environments: t_three's and t_five's. accept and smoke then run
  a graph on GitHub.

## 11. Not done

- **The naming exception `dev_patches → qiyuan-dev-patches`** (names.py). Stage 1 section 11 put it in
  stage 2; it has nothing to do with several bases, and the owner: "做完我们手头的之后就来做这个". It gets
  its own design next (where a feature's package name comes from when its files are not installed:
  features.py:122, render-feature-recipe:163, conda_hook.py:67, check-packages:64).
- **Bases built on different releases of a lower feature**: a sentence in the SKILL and RELEASE.md, no
  code; the release workflow stops such a feature before publishing (conda cannot solve its environment).
- **The alternative not taken**: keep numbered levels and forbid unrelated features from changing the same
  file. The model, API and hooks would change the same way; it would only save the set-valued level, and
  it would forbid a feature on two bases that both change one file (the toy t_five on t_two and t_four)
  and two publishers' Pure features that each register an ML file in src/Pure/ROOT.ML, however far apart.

## 12. Approved by the owner ("先这样来，之后有问题再改")

1. The level of a file becomes a set of features (section 4); a line of features behaves as today.
2. Unrelated features may be installed together; when their changes to a file do not apply in every order
   with the same result, the tool refuses them (exit 3) (sections 4, 6).
3. `unapply --feature F` and removing F take away F and what is built on F only; `apply` with a CONFLICT
   still applies the features unrelated to it (sections 5, 6).
4. A feature with several bases is built on a merge commit of its bases in its own branch, made with
   `new-tree --merge`; make-patches checks that the merge adds nothing (section 7).
5. `-v` and `--dry-run` show a level with two or more tops as `level 3+5 (f3, f5)` (section 5).
6. Tool 1.1.0; feature packages pin `>=1.1,<2` (section 8).
7. Unrelated features are listed in conda's order: by depth, then by package name (section 2).

New user-visible texts, shown to the owner: the refusal of section 4; the README and help sentences of
section 9; `new-tree --merge`'s output (section 7, shown to the owner on 2026-11-10).

Costs: about 300-400 changed lines in the tool, tools/ and tests, plus the documents; for a line no change
in speed.
