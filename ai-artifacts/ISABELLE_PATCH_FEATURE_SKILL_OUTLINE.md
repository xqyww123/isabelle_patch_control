# Outline of the SKILL `isabelle-patch-feature`

Status (2026-10-31): the owner approved the structure ("很好") and asked for an Opus team review. The
review (wf_4c12d3ef-015; record in `/var/tmp/claude-review9/`, never in a repository) found no section
in the wrong place; this second version applies the fixes the owner agreed to, the owner's answers
(changing a base stays, at the drafted length; the new-release section splits into the foundation and
the upgrade of a feature), and what the "git 2026" session did when it opened Isabelle2026 (its
messages are recorded at the end). The second review, a two-round debate (wf_6a5cad49-d01; record
`/var/tmp/claude-review9/review10-result.json`), did not pass it yet; this third version applies its
rulings (the owner, 2026-11-01: option (a) for the conversion; no comment on the rest) and goes to a
debate review of the changed points: 3.9 step 4, 3.3, section 2's exception with 3.1's
existing-machine step 3, 3.7 step 1, and `init.sh`'s conversion. That third review (wf_08c1961a-55c;
`/var/tmp/claude-review9/review11-result.json`) ruled three sentence-level fixes, applied here without
another round (3.6 step 4's reference, 3.9 step 4's condition for a base implemented afresh, 3.1
step 3's notice and heap rebuild), and one owner question, answered (2026-11-01, "按你建议来"):
`init.sh` removes a leftover `contrib/<R>.clone` before cloning. With these the judge rules the
outline ready to be written into the SKILL.

## What the SKILL is, where it lives, what it replaces

- **Essence.** An operating manual for an agent working on a *patch-based Isabelle feature*: a feature
  that changes Isabelle's own sources and ships as a patch package of `isabelle-patch-control`
  (light_locale, local_datatype, dot_syntax, fast_abbrev_printing, ...). It says what the setup looks
  like, then the rules that always hold, then the steps for each situation, one command per step. Each
  feature's agent will follow it to upgrade its feature to Isabelle2026 (owner, through the "git 2026"
  session: "SKILL 要写清该怎么做，然后等 SKILL 就绪后跟各个 agent 说一下").
- **Reasons.** The release steps name the RELEASE.md section that holds their reasons and corner
  cases. The other steps give at most one clause of reason inline; the tools' own reasons are in
  their `--help`. No step points to the migration plan (git does not track it; other machines cannot
  read it).
- **File.** `contrib/my_better_isabelle_prover/.claude/skills/isabelle-patch-feature/SKILL.md`, one
  file, in English. MLML's `.claude/skills/isabelle-patch-feature` is a symbolic link to that
  directory (test first that Claude Code accepts a linked SKILL directory).
- **Division of labour (owner, 2026-10-30).** "The main knowledge goes into the SKILL; RELEASE.md is
  only for reference ... another agent releasing or building such a patch-based feature reads only the
  SKILL to know what to do, and needs RELEASE.md only for bug shooting and the like." RELEASE.md keeps
  its name and begins with one sentence: how to do it is in the SKILL; this file is its reference.
- **Replaces** the README section "Working in the Isabelle source repository" (the README keeps one
  sentence pointing to the SKILL), and the migration plan's §7 and Appendix A, which get the mark
  "replaced by the SKILL isabelle-patch-feature" (owner, 2026-10-31: "赞同标'已由 SKILL 取代'").
- **Provenance marks.** *(carried over)*: from that README section, approved 2026-10-18. *(fourth
  draft)*: from the owner's decisions in the fourth draft (MLML `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`
  §12, "第四稿"). *(review)*: a fix from the outline review that changes no decision. *(Isabelle2026)*:
  what the "git 2026" session did on the owner's orders.

## Frontmatter

- `name: isabelle-patch-feature`
- `description`: read it when you edit, build or commit in the Isabelle trees of a patch-based
  feature; merge its base; release it; put its trees on a machine; move `daily`; open a feature,
  change its base, or upgrade it to a new Isabelle release.

## 1. What this is (about 20 lines)

- One sentence of essence: the Isabelle source repository is `xqyww123/isabelle-patched` on GitHub,
  and every tree is a plain clone of it; the tool only does what git does not: the build products,
  the stock tree's position, the release.
- No other repository: every `contrib/<R>` and every tree is a clone of isabelle-patched, and a release
  line `<R>` (for example `Isabelle2026`) is a set of branches in it. *(Isabelle2026)*
- Branches: `<R>/pristine` (the official release, unmodified), `<R>/<F>` for each feature,
  `<R>/dev_patches` (the top feature), `<R>/daily` (follows `dev_patches`). Tags: a feature's release
  tags `<R>/<F>/<v>` are made only by `make-patches`; the pristine tag `<R>/pristine/<id>` (`<id>` =
  the release's `etc/ISABELLE_ID`) is made by hand when a release's foundation is laid (3.8).
  *(fourth draft; the pristine tag: Isabelle2026)*
- Every feature has exactly one base on each line, recorded as `base =` in its feature repository's
  `.gitmodules`; several features may share a base; which features a line carries, and their bases,
  the owner decides per line (Isabelle2026 carries no expose_foreign and no future_assign_interrupt).
  No "chain" in the wording. *(fourth draft; per line: Isabelle2026)*
- The *base tag*: the base's release tag at the merge base, printed (after `git fetch` in the private
  tree) by `git tag --points-at $(git merge-base origin/<R>/<base> HEAD) --list '<R>/<base>/*'`; it is
  the tag that `init.sh`'s `ready:` line names. *(review)*
- The three kinds of tree, as a table (path, what is checked out, what it is for):
  - shared tree `contrib/<R>`, on `<R>/daily`;
  - private tree `<feature repository>/worktrees/<R>-<F>`, on `<R>/<F>`, the only place to edit;
  - stock tree `<feature repository>/worktrees/<R>-<F>-stock`, detached at the merge base of the
    feature branch and its base: the sources without your feature, for comparison runs and golden
    files.
  The private and the stock tree are submodules of the feature repository, with `ignore = all`.
- Build products: `contrib` is a symbolic link to the shared tree's `contrib` (never write through
  it); `lib/classes` and `src/Tools/Demo/lib` are copies; `etc/ISABELLE_IDENTIFIER` is the directory
  name, so each tree's user directory is `~/.isabelle/<directory name>`. Module jars a release adds
  are compiled by Isabelle on the first Scala tool run (Isabelle2026: `scalajs_demo.jar`, about 6 s).
- The tool: the subcommands `new-tree`, `make-patches`, `check-signatures` of
  `isabelle-patch-control`; everything else is plain git.
- Words, each defined once and used throughout: owner, feature, feature repository, base, base tag,
  release line, shared tree, private tree, stock tree, package directory.

## 2. Rules (they always hold)

Git:
- Inside the Isabelle trees these rules replace CLAUDE.md's section "Commit on `main` — never branch",
  including its sentence that sweeping another agent's uncommitted changes into a commit is
  acceptable. CLAUDE.md's bans on `git stash`, `git checkout`, `git reset --hard` and `git clean`
  apply word for word. One exception covers the rules of this section: a shared tree unpacked from a
  release tarball and not yet a clone holds nobody's work, so turning it into a clone (3.1, with its
  `git checkout -f -B`) and laying a release's foundation in it (3.8: writing `.gitignore`,
  committing, pointing HEAD at `<R2>/daily`) are done, on the owner's order, outside them.
  *(carried over; the exception: review, reconciling it with the fourth draft's steps)*
- Edit and commit only in your feature's private tree; never edit the shared tree or a stock tree.
  Plans and scratch files go to your project repository's `ai-artifacts/`, never into a tree.
  *(carried over)*
- Never switch branches in a tree: no `git switch`, `git checkout <rev>`, `git reset <rev>`,
  `git bisect`. To read another revision, use `git show <rev>:<path>` or the stock tree. Never create,
  delete or rename a branch or a tag, and never add, move or remove a tree, except in the steps of
  section 3 that do so, each on the owner's order (putting a shared tree on a machine, opening a
  feature, laying a release's foundation, upgrading a feature). *(carried over, without the hook and
  `ISABELLE_GIT_OWNER`)*
- Stage only your own changes, by explicit path; commit only when the owner says so; never amend,
  squash or rewrite a commit; never rebase, force-push, cherry-pick, or `git revert -m` a merge.
  *(carried over)*
- Push when you judge it right; it needs no order from the owner. Push only to `origin`. The tools
  never push. *(fourth draft; replaces "push only on the owner's order")*
- Take in other work in exactly three ways: `git merge` of your base branch (3.3); `git pull --ff-only`
  of your own branch's commits that another machine pushed (3.2); on a newer release line, a merge of
  the same feature's branch of the older line (3.9). A newer line is never merged into an older one.
  *(carried over; the second way: fourth draft)*

Running Isabelle:
- Run a tree with that tree's own `<tree>/bin/isabelle`, from a shell that has no `ISABELLE_*`
  variable. One clause of reason: with `ISABELLE_SETTINGS_PRESENT` inherited, Isabelle skips its whole
  settings step and runs with another tree's settings. *(fourth draft; replaces `run-tree`)*
- Tools that find `isabelle` on `PATH` by themselves (Isa-REPL, isabelle-mcp) run only the shared tree
  whose `bin` MLML's `envir.sh` puts on `PATH`; so restarting the REPL (CLAUDE.md, "Reloading `.ML`
  changes") never loads a tree's edits, and a tree's own sources are tested only by a build in that
  tree. Probes that need those tools, to see how Isabelle behaves without your feature, run only on
  that line, and only before any commit of your feature reaches that line's `daily`; every other
  comparison run uses the stock tree. *(carried over, without `run-tree`; the REPL clause and the
  line: review)*
- Every `isabelle build` needs the owner's command or a standing authorization that names that tree,
  including a heap build another command triggers. *(carried over)*
- Build, and check the result yourself, before a release: the sessions of the package's
  `tools/required_sessions.txt` (3.4); before moving `daily`: those of dev_patches'
  `contrib/qiyuan_dev_patches/tools/required_sessions.txt`, a file made with dev_patches' first-release
  files; until it exists, the owner names the sessions (3.5). *(fourth draft; replaces the tested
  record)*
- When a tool refuses, stop and ask the owner; never work around it. *(carried over)*

## 3. Procedures (by situation, one command per step)

### 3.1 Putting the trees on a machine
New machine: clone MLML and run MLML's `init.sh`. Besides MLML's own setup it installs the patch
tool, downloads the newest release line the feature repositories register, turns every registered
line's shared tree into a clone of isabelle-patched on `<R>/daily`, puts each feature repository back
on its default branch, and runs each feature repository's `init.sh`. *(fourth draft; the owner,
2026-10-31: the branch step, and "我的意思就是 .gitmodules 中最新的 R")*
A machine that already has MLML (do not run MLML's `init.sh` there):
1. `git pull` in MLML; skip it where the owner has said MLML is not to be pulled (cslh19 today).
2. `git -C contrib/my_better_isabelle_prover pull --ff-only origin main` (it works whether that
   checkout is on a branch or not), then `pip install -e contrib/my_better_isabelle_prover` (an old
   checkout has no `new-tree`).
3. A release line new to the machine, or a shared tree that is not a clone: unpack
   `https://isabelle.in.tum.de/website-<R>/dist/<R>_linux.tar.gz` into `contrib/` if `contrib/<R>`
   is missing; then in `contrib/<R>`: `git init`; `git remote add origin
   https://github.com/xqyww123/isabelle-patched.git`; `git fetch origin`; `git checkout -f -B <R>/daily
   --track origin/<R>/daily`; `git config branch.<R>/daily.mergeoptions --ff-only`. Then rerun the
   `init.sh` of each feature repository that registers trees of that line. On an official release
   tarball `git status` is empty afterwards. A shared tree that is not a clone is the Isabelle this
   machine's sessions run, and the conversion changes its sources to daily's, as moving `daily` does:
   notify every session first, and afterwards rebuild its heaps with the owner's authorization (3.5
   steps 2 and 4).
4. A feature repository new to the machine: `git clone <url> contrib/<feature repository>` (a clone is
   on its default branch; `git submodule update` would leave it on none), then its `init.sh`.
5. After `git -C contrib/<feature repository> pull --ff-only` brings newly registered trees, rerun its
   `init.sh`.
*(fourth draft, D7; the clone, the patch tool update and the order: review)*

### 3.2 Everyday work in the private tree
1. Before starting: `git -C <feature repository> pull --ff-only`; in the private tree,
   `git pull --ff-only`. If it refuses, the branch moved on two machines and only a merge commit can
   join them: ask the owner. Then rerun `<feature repository>/init.sh` (a pulled merge of the base
   moves the stock tree). *(review)*
2. Edit; build on order; commit on order; push when it is right.

### 3.3 Merging the base
From an empty `git status` in the private tree: `git fetch`; `git merge --no-commit origin/<R>/<base>`
(a plain merge commits at once); resolve conflicts by editing; build and test on order; commit on
order; rerun `<feature repository>/init.sh` (the stock tree moves to the new merge base); push when it
is right. Until that commit and that rerun the stock tree stays at the old merge base, so comparison
runs and golden recordings against the new merge base come after them; if a test cannot pass
without them, tell the owner. You may merge base commits that no release tag contains yet, but you
can release only when the base tag (section 1) exists. *(carried over; `--no-commit`, the order and
the stock tree's lag: review; test before commit: the owner's "只有测试过的才能提交")*

### 3.4 Releasing a feature (on the owner's order)
1. The base tag (section 1) must print one tag. If it prints nothing, the last base commit merged is
   not a release of the base: tell the owner before building (`make-patches` gate 0 would refuse).
   *(review)*
2. The pre-release checklist, five points; each says what to check, the command (with the base tag of
   section 1), the expected result, and points to RELEASE.md, "Before releasing a feature", for its
   reason. *(moved from RELEASE.md; owner agreed)* A new commit on the branch, for a failed point or
   a failed build, starts this section again here.
3. Bring the package directory up to date. The package directory (`--package`) is the feature
   repository, or its `<F>/` subdirectory when it holds several features (isabelle-base-features). A
   first release first adds the files of 3.6 step 4 that it lacks (new files: on order). Then
   `git -C <private tree> diff-tree -r --no-renames --name-only <base tag> HEAD >
   <package dir>/tools/patched_files.txt`; `isabelle-patch-control check-signatures -C <private tree>
   <base tag> HEAD <package dir>/tools/signature_additions.txt`, correcting the file until it exits
   0; commit both in the feature repository on order. Formats: RELEASE.md, "First-time setup of a
   feature repository". *(review)*
4. On order, from a shell with no `ISABELLE_*` variable: `<private tree>/bin/isabelle build -b -d <dir>
   ... <the sessions of tools/required_sessions.txt>`, one `-d` for each directory whose ROOT defines a
   session the build needs: a listed one, or one a listed session builds on as parent or under
   `sessions` (light_locale: `-d contrib/light_locale -d contrib/light_locale/tests`). *(review)*
5. `isabelle-patch-control make-patches -C <private tree> --package <package dir> <F> <v>`; rerun it
   after a failure (its gates: `--help`).
6. Push: the private tree's branch and tag, the feature repository's branch and tag.
7. The features whose base is this one: `grep -l 'base = <R>/<F>$' contrib/*/.gitmodules`; tell the
   owner. Each one merges the release (3.3) and is released (this section) in its own private tree, on
   order. *(review)*
8. Publishing to the conda channel, on order: "Pause the download counter while you release
   (isabelle-packaging-ci's `RELEASE_CHECKLIST.md`, "The channel host")." (the owner's sentence, word
   for word); dispatch `release-features.yml` with `publish=false`; when `roundtrip` and the five
   `accept` legs are green, dispatch it again with `publish=true`; its `features` input names every
   feature release tag the channel should end up with, lower features included. After a new
   `isabelle` build every feature package is re-released the same way, same versions; RELEASE.md's
   inputs table says how to list `features` then. The inputs, jobs and recovery: RELEASE.md, "The
   batch release workflow". *(moved from RELEASE.md, "Releasing a feature" step 6: review)*

### 3.5 Moving `daily` (on the owner's order)
1. Build dev_patches' sessions (section 2) in its private tree, on order, with HEAD =
   `origin/<R>/dev_patches` and an empty `git status`.
2. Notify every session (each knows whether it uses the shared tree).
3. `git -C contrib/<R> fetch`, then `git -C contrib/<R> merge --ff-only origin/<R>/dev_patches`; on
   another machine, `git -C contrib/<R> pull --ff-only`.
4. Rebuild the shared tree's heaps with the owner's authorization.
5. Push `daily` when it is right.
*(fourth draft; the steps: review)*

### 3.6 Opening a new feature (on the owner's order)
1. Create the feature repository as MLML's `contrib/<directory>`, next to `contrib/<R>` (new-tree finds
   the shared tree there); the owner creates its GitHub repository. *(review)*
2. `isabelle-patch-control new-tree --home contrib/<feature repository> --base <R>/<base> <R>/<F>`.
3. At once, `git -C <private tree> push -u origin <R>/<F>`: a feature opened on this one needs it on
   GitHub, and so does another machine's `init.sh` once the registration is committed.
4. Add the one-line `init.sh` and the files the first release needs: `tools/patched_files.txt` and
   `tools/signature_additions.txt` (made as in 3.4), `tools/required_sessions.txt`, `.gitattributes`, a README (formats: RELEASE.md, "First-time setup
   of a feature repository").
5. The registration commit, by path, on order: `git add -- <the new files of step 4>`, then
   `git commit -- .gitmodules worktrees/<R>-<F> worktrees/<R>-<F>-stock <the new files>` (new-tree has
   staged the rest); push the feature repository.
6. Registering in MLML, on order: `git submodule add -f <url> contrib/<directory>` (no `branch`).
*(fourth draft)*

### 3.7 Changing a feature's base (on the owner's order)
The paragraph the owner approved at this length (about 150 words; step 1 corrected by the second
review: fetch first, and compare against what F has merged, not against the old base's tip):

> Example: a new feature N goes between A and the feature F that is built on A. N is opened on A
> (3.6); then F's base changes from A to N.
> 1. Check that the new base contains everything of the old base that F has merged: in F's private
>    tree, `git fetch`, then `git merge-base --is-ancestor $(git merge-base origin/<R>/<old base> HEAD)
>    origin/<R>/<new base>` must exit 0. Otherwise F's branch keeps commits of the old base that the
>    new base lacks, F's release patches would carry them, and `make-patches` does not notice: ask the
>    owner.
> 2. In F's feature repository: `git config -f .gitmodules submodule.worktrees/<R>-<F>.base <R>/<new
>    base>`; commit `.gitmodules` on order; push.
> 3. Merge the new base into F's private tree as in 3.3. F can be released only once the last merged
>    commit of N is a release of N.
> 4. Rerun `<feature repository>/init.sh`: the stock tree moves to the new merge base.
>
> F's next release depends on N's package; `make-patches` derives this from the base tag.

### 3.8 A new Isabelle release: the foundation (on the owner's order, once per release)
In `contrib/<R2>`, the official release tarball unpacked, in place, without rewriting any file:
1. `git init --initial-branch=<R2>/pristine`; `git remote add origin
   https://github.com/xqyww123/isabelle-patched.git`; `git fetch origin`.
2. `git update-ref refs/heads/<R2>/pristine refs/remotes/origin/<R>/pristine` (the parent is the old
   line's pristine); `git read-tree HEAD` (the index only).
3. `.gitignore`: the old line's, with the launcher line renamed, plus every build product the release
   adds: before committing, list the binaries `git add -A` would take (`*.jar` and the like) and every
   `module =` of an `etc/build.props` (Isabelle2026: `/src/Tools/Scalajs_Demo/lib`).
4. `git add -A`; `git commit`; `git tag -a <R2>/pristine/<id>`, `<id>` = the release's `etc/ISABELLE_ID`.
5. `git branch <R2>/daily`; `git symbolic-ref HEAD refs/heads/<R2>/daily`; `git config
   branch.<R2>/daily.mergeoptions --ff-only`.
6. Push both branches and the tag; `git branch -u origin/<R2>/daily`. `git status` is empty.
Other machines put `contrib/<R2>` in place by 3.1. No hg repository is involved: the channel packages
the official release unmodified (isabelle-packaging-ci 0f52b4d). *(Isabelle2026; the owner: "跟最初我们改造
contrib/Isabelle2025-2 同一个做法啊！", "不要新建仓库，还是用 isabelle-patched 这个仓库", "不要 clone hg 仓库")*

### 3.9 Upgrading a feature to a new Isabelle release (each feature's agent; a base before the features on it)
Before: the foundation (3.8) exists, and the feature's base on the new line, which the owner decides,
has its `<R2>` branch on GitHub.
1. `isabelle-patch-control new-tree --home contrib/<feature repository> --base <R2>/<base> <R2>/<F>`.
2. At once, `git -C <feature repository>/worktrees/<R2>-<F> push -u origin <R2>/<F>` (a feature
   upgraded onto this one needs it on GitHub).
3. The registration commit as in 3.6 step 5; push the feature repository.
4. Bring the work over; the agent decides with the owner:
   - merge the old line's branch, once your base's `<R2>` branch has merged its old line's branch and
     been pushed, or, if your base was implemented afresh, once it has released on the new line
     (`git tag --list '<R2>/<base>/*'` after `git fetch`): `git fetch`; first merge
     `origin/<R2>/<base>` as in 3.3 (for Isabelle2026 a fast-forward, no commit); then
     `git merge --no-commit origin/<R>/<F>`. In the other order there are two merge bases, and new-tree
     and make-patches refuse. The merge brings your old-line work, plus any old-line work below it
     that your base's `<R2>` branch does not contain (on Isabelle2026, for fast_abbrev_printing:
     expose_foreign and future_assign_interrupt; below a base implemented afresh: that base's old
     work). Remove by editing what the new line does not carry; `make-patches` does not notice what
     is left. `git diff --cached --stat` shows what came in. *(fourth draft item 9)*
   - or implement the feature afresh on the new line (the owner's plan for the features with no work
     on Isabelle2025-2).
5. Build and test on order; commit on order; push.
6. Release by 3.4 once the base has released on the new line.
Later fixes of the old line come over by the same merge; a newer line is never merged into an older
one. *(fourth draft item 9; Isabelle2026)* For Isabelle2026, the "git 2026" session did steps 1 and 2
for every feature; start at step 3.

## 4. Where the details are (a few lines)
- RELEASE.md: the reason and corner cases of each checklist point; the formats of the package
  directory's files; the batch release workflow's inputs, jobs and recovery.
- `isabelle-patch-control <subcommand> --help`.
- Each feature repository's design document.

## Dropped from the old README section
The hook and `ISABELLE_GIT_OWNER`; `run-tree`; the tested record and the rule against changing `-d`
directories during a build; `advance-daily`; `new-tree --stock`; "push only on the owner's order";
every "in chain order"; the bullet on how a user's machine applies and reverses packages (it is
about the end user, and reference.md and AGENTS.md cover it).

## Related changes to other files
They are listed once, in the migration plan's step (vi) list ("下一步" item 7), not here.

## Settled open question
A new machine and a second release line: MLML's `init.sh` installed only Isabelle2025-2, so new-tree
refused the Isabelle2026 trees and `set -e` stopped `init.sh` at the first feature repository. Solved
by the `init.sh` change (the owner, 2026-10-31: "我的意思就是 .gitmodules 中最新的 R", "同意"; the
conversion by a clone whose `.git` moves in last: the owner, 2026-11-01, "第一部分按你建议来").

## Record of the "git 2026" session's messages (2026-10-31; the source of 3.8 and 3.9)

What it did (owner: "跟最初我们改造 contrib/Isabelle2025-2 同一个做法啊！", "不要新建仓库，还是用
isabelle-patched 这个仓库"): `contrib/Isabelle2026` is the official Linux release tarball, unpacked;
in place, no file rewritten: `git init --initial-branch=Isabelle2026/pristine`; `git remote add
origin https://github.com/xqyww123/isabelle-patched.git`; `git fetch origin`; `git update-ref
refs/heads/Isabelle2026/pristine refs/remotes/origin/Isabelle2025-2/pristine`; `git read-tree HEAD`;
`.gitignore` = 2025-2's with the launcher line changed and `/src/Tools/Scalajs_Demo/lib` added;
`git add -A`; `git commit` (7d475f7, 3806 files); `git tag -a Isabelle2026/pristine/096842708b28`;
`git branch Isabelle2026/daily`; `git symbolic-ref HEAD refs/heads/Isabelle2026/daily`;
`mergeoptions --ff-only`; push both branches and the tag; `git branch -u origin/Isabelle2026/daily`.

Its confusions, for the SKILL: (1) no hg; `make-patches pristine` (check (a), needs `--hg`) is no
longer part of the workflow; whether to delete that code is the owner's call, not yet proposed;
(2) give the conversion commands; (3) no new repository; (4) new build products; (5) the features of
a line are the owner's decision per line; (6) features start at their base's tip; old work is merged
or reimplemented by the feature's agent; (7) no temporary pristine tree.

The features' branches: in base order, `new-tree --home` then at once `push -u`; the push must come
before the next feature's `--home` (it checks the base with `ls-remote` and branches from
`origin/<R>/<base>`). Order: fast_abbrev_printing (in isabelle-base-features, base
`Isabelle2026/pristine`), light_locale, local_type_abbrev, localized_record, local_datatype,
dot_syntax, dev_patches (in qiyuan_dev_patches). new-tree refused nothing. All branches and stock
trees at 7d475f7; registrations staged, not committed. A 2026 tree without `scalajs_demo.jar`: the
first Scala tool run compiles it (about 6 s), nothing fails, `PRODUCT_COPIES` need not change.

Owner (relayed): "七个 feature 仓库不用你管。之后我会让各个 agent 自己去升级的。不过你可以告诉 the git agent
所写得 SKILL 要写清该怎么做，然后等 SKILL 就绪后跟各个 agent 说一下"; "dev_patches 等一切完成后你来做".
Open for the owner, not to be written into the SKILL: what happens to the 2025-2 trees and their
registrations now that 2025-2 is not continued.
