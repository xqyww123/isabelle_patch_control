---
name: isabelle-patch-feature
description: How to work on a patch-based Isabelle feature, one that changes Isabelle's own sources and ships as an isabelle-patch-control package (light_locale, local_datatype, dot_syntax, fast_abbrev_printing, ...). Read it before you edit, build or commit in such a feature's Isabelle trees, merge its base, release it, put its trees on a machine, move daily, open a feature, change its base, or upgrade it to a new Isabelle release.
---

# Working on a patch-based Isabelle feature

Every Isabelle tree here is a plain git clone of one GitHub repository, `xqyww123/isabelle-patched`.
Plain git does almost everything; the tool `isabelle-patch-control` adds three subcommands for what git
does not do: putting trees in place (`new-tree`), releasing (`make-patches`), checking signatures
(`check-signatures`).

## 1. The setup

**Branches.** A release line `<R>` (`Isabelle2025-2`, `Isabelle2026`) is a set of branches in
isabelle-patched:
- `<R>/pristine`: the official Isabelle release, unmodified; tagged `<R>/pristine/<id>`, where `<id>`
  is the release's `etc/ISABELLE_ID`.
- `<R>/<F>`: one branch per feature `<F>`; its releases are tagged `<R>/<F>/1`, `<R>/<F>/2`, ...,
  only by `make-patches`.
- `<R>/daily`: the branch the shared tree follows; it follows `<R>/dev_patches` (3.5).

**Base.** Every feature has exactly one *base* on each line: `pristine` or another feature. It is
recorded as `base =` in the feature repository's `.gitmodules`. The owner decides which features a
line carries and their bases.

**Feature repository.** Each feature has a git repository under MLML's `contrib/` (for example
`contrib/light_locale`; `contrib/isabelle-base-features` holds several features). It holds the
package (patch files, `tools/*.txt`, README) and registers two Isabelle trees per line as git
submodules:

| tree | path | checked out | for |
|---|---|---|---|
| shared tree | `contrib/<R>` | `<R>/daily` | the line's build products, which the other trees use; MLML's own tools run the one on `PATH` |
| private tree | `<feature repository>/worktrees/<R>-<F>` | `<R>/<F>` | the only place you edit, build and commit |
| stock tree | `<feature repository>/worktrees/<R>-<F>-stock` | detached at the merge base of `<R>/<F>` and its base | the sources without your feature: comparison runs, golden files |

A tree's `contrib` is a link to the shared tree's `contrib`: never write through it. `lib/classes` and
`src/Tools/Demo/lib` are copies. A module jar that a release adds is compiled by Isabelle on the tree's
first Scala tool run (for example `scalajs_demo.jar`, new in Isabelle2026); nothing fails. Each tree's user
directory is `~/.isabelle/<directory name>`; heaps live there.

**Base tag.** The base's release tag on the merge base of your branch and the base, that is, on the
last base commit your branch has merged; there is none when that commit is not a release. Each
`init.sh` run names it in the `ready:` line of your tree (`release tag <tag>`, or `not a release of
the base`); by hand, after `git -C <private tree> fetch`:

    git -C <private tree> tag --points-at $(git -C <private tree> merge-base origin/<R>/<base> HEAD) --list '<R>/<base>/*'

**Placeholders below.** `<R>`, `<F>`, `<base>` as above; `<feature repository>`: its path (for example
`contrib/light_locale`); `<private tree>`: `<feature repository>/worktrees/<R>-<F>`; `<package dir>`:
`<feature repository>`, or `<feature repository>/<F>` when it holds several features. Commands run
from MLML's root.

## 2. Rules

Inside the Isabelle trees these rules replace CLAUDE.md's section "Commit on `main` — never branch".
CLAUDE.md's bans on `git stash`, `git checkout`, `git reset --hard` and `git clean` still apply.

- Edit and commit only in your private tree. Never edit the shared tree or a stock tree. Plans and
  scratch files go to your project's `ai-artifacts/`, never into a tree.
- Never switch branches in a tree: no `git switch`, `git checkout <rev>`, `git reset <rev>`,
  `git bisect`. To read another revision use `git show <rev>:<path>` or the stock tree.
- Never create, delete or rename a branch or a tag, and never add, move or remove a tree, except in
  the steps of section 3 that do so, on the owner's order.
- Stage only your own changes, by explicit path. Commit and push only when the owner says so; the
  tools never push. Never amend, squash or rewrite a commit; never rebase, force-push, cherry-pick,
  or `git revert -m` a merge.
- Take in other work only by: merging your base (3.3); `git pull --ff-only` of your own branch (3.2);
  on a newer line, merging the same feature's branch of the older line (3.9). Never merge a newer
  line into an older one.
- Exception: a shared tree unpacked from a release tarball and not yet a clone holds nobody's work.
  Turning it into a clone (3.1) and laying a release's foundation in it (3.8) are done on the owner's
  order outside these rules.

Running Isabelle:
- Run a tree with that tree's own `<tree>/bin/isabelle`, from a shell where `env | grep ^ISABELLE_`
  prints nothing (an inherited `ISABELLE_SETTINGS_PRESENT` makes Isabelle use another tree's
  settings).
- Every `isabelle build`, also one that another command triggers, needs the owner's command or a
  standing authorization that names that tree.
- Isa-REPL and isabelle-mcp run only the shared tree whose `bin` MLML's `envir.sh` puts on `PATH`. So
  restarting the REPL never loads your tree's edits; your sources are tested only by a build in your
  tree. Use those tools only for probes of Isabelle without your feature, on that line, and only
  before any commit of your feature reaches that line's `daily`. Every other comparison uses the
  stock tree.
- Before a release (3.4) and before moving `daily` (3.5), build the sessions named there and check
  the result yourself.
- When a tool refuses, stop and ask the owner. Never work around it.

## 3. What to do

### 3.1 Putting the trees on a machine

**A new machine:** clone MLML and run `./init.sh`. Besides MLML's own setup it installs the patch
tool, downloads the newest release line the feature repositories use, makes every shared tree a
clone, and runs each feature repository's `init.sh`.

**A machine that already has MLML** (never run MLML's `init.sh` there):
1. `git pull`, unless the owner has said that this machine's MLML is not to be pulled (cslh19).
2. `git -C contrib/my_better_isabelle_prover pull --ff-only origin main`, then
   `pip install -e contrib/my_better_isabelle_prover`.
3. A release line new to the machine, or a shared tree that is not a clone (on the owner's order).
   If `contrib/<R>` is missing, unpack `https://isabelle.in.tum.de/website-<R>/dist/<R>_linux.tar.gz`
   into `contrib/`. If it was already there, sessions on this machine may be running it, and the
   commands below change its sources to daily's: notify every session first. Then:

       git -C contrib/<R> init
       git -C contrib/<R> remote add origin https://github.com/xqyww123/isabelle-patched.git
       git -C contrib/<R> fetch origin
       git -C contrib/<R> checkout -f -B <R>/daily --track origin/<R>/daily
       git -C contrib/<R> config branch.<R>/daily.mergeoptions --ff-only

   On an official release tarball `git status` is empty afterwards. Run
   `bash <feature repository>/init.sh` for each feature repository that has trees of that line; for
   a tree that was already there, rebuild its heaps afterwards with the owner's authorization.
4. A feature repository new to the machine: `git clone <its GitHub url> <feature repository>` (a clone
   is on its default branch; `git submodule update` would leave it on none), then
   `bash <feature repository>/init.sh`.
5. When `git -C <feature repository> pull --ff-only` brings newly registered trees:
   `bash <feature repository>/init.sh`.

### 3.2 Everyday work

Before you start:

    git -C <feature repository> pull --ff-only
    git -C <private tree> pull --ff-only
    bash <feature repository>/init.sh

If a pull says it cannot fast-forward, the branch moved on two machines and only a merge commit can
join them: ask the owner. While a merge of yours in the private tree (3.3, 3.9) waits for its commit,
pull the private tree after that commit. `init.sh` moves the stock tree when a merge of the base came
in. Then edit in the private tree, build on order, commit on order, push on order.

### 3.3 Merging the base

From an empty `git -C <private tree> status`:

    git -C <private tree> fetch
    git -C <private tree> merge --no-commit origin/<R>/<base>

(A plain `git merge` would commit at once.) Resolve conflicts by editing; build and test on order;
commit on order; `bash <feature repository>/init.sh`, which moves the stock tree to the new merge
base; push on order. Until that commit and that `init.sh`, the stock tree stays at the old
merge base, so comparison runs and golden recordings against the new one come after them; if a test
cannot pass without them, tell the owner.

You may merge base commits that no release contains yet, but you can release only once there is a
base tag (section 1).

### 3.4 Releasing a feature (on the owner's order)

Any new commit on the branch (a fix for a checklist point or for the build) starts again at step 2.
A release of the same sources under a new number (only the feature repository changed) starts with an
empty commit in the private tree, on order:

    git -C <private tree> commit --allow-empty -m "<R>/<F>: release <m>"

1. **The base tag** (section 1) must be exactly one tag; it is `<base tag>` in the commands below. If
   there is none, the last base commit you merged is not a release of the base: tell the owner.
2. **The checklist** (RELEASE.md, "Before releasing a feature: why each checklist point matters").
   Each command must print nothing.
   - No file goes back to the bytes of a lower feature's release or of the pristine release
     (deleting a file a lower feature created counts):

         for t in $(git -C <private tree> tag --merged HEAD --list '<R>/*/*' | grep -v '^<R>/<F>/'); do
           for p in $(git -C <private tree> diff-tree -r --no-renames --name-only <base tag> HEAD); do
             [ "$(git -C <private tree> rev-parse -q --verify "$t:$p")" = "$(git -C <private tree> rev-parse -q --verify "HEAD:$p")" ] && echo "$p equals $t"
           done
         done

   - Every hunk's context occurs only once in its file:

         d=$(mktemp -d); git -C <private tree> diff-tree -r -p --no-renames <base tag> HEAD > $d/f.diff
         mkdir $d/tree; git -C <private tree> archive HEAD | tar -x -C $d/tree
         for p in $(git -C <private tree> diff-tree -r --no-renames --name-only <base tag> HEAD); do
           (cd $d/tree && git apply --check --include="$p" ../f.diff 2>/dev/null) && echo "$p: a hunk applies twice"
         done
         rm -rf $d

   - Only regular files, mode 100644 or 100755, and no change of mode:

         git -C <private tree> diff-tree -r --no-renames <base tag> HEAD | awk '$1 !~ /^:(100644|100755|000000)$/ || $2 !~ /^(100644|100755|000000)$/ || ($5 == "M" && $1 != ":" $2)'

   - `etc/ISABELLE_ID` is unchanged:

         git -C <private tree> diff-tree -r --name-only <base tag> HEAD | grep -x etc/ISABELLE_ID

   - Every patch file's path stays within 198 characters on Windows (`<package name>`: `isabelle-`
     plus `<F>` with `_` as `-`, but `qiyuan-dev-patches` for dev_patches; `<prefix>`: `<R>` with
     `-` as `_`; `<Y>.<k>`: the first two numbers of the package version, `2026.0` for Isabelle2026,
     `2025.2` for Isabelle2025-2):

         git -C <private tree> diff-tree -r --no-renames --name-only <base tag> HEAD | sed 's,/,-,g' |
           awk -v pre='<package name>-<Y>.<k>.99-<prefix>_99/share/isabelle_patch_control/features.d/<F>/' 'length(pre $0 ".patch") > 198'

3. **The package directory.** A release first adds the files of 3.6 step 4 that `<package dir>`
   lacks (new files: on order). Then bring the two lists up to date and commit them in the feature
   repository on order:

       git -C <private tree> diff-tree -r --no-renames --name-only <base tag> HEAD > <package dir>/tools/patched_files.txt
       isabelle-patch-control check-signatures -C <private tree> <base tag> HEAD <package dir>/tools/signature_additions.txt

   Correct `signature_additions.txt` until `check-signatures` exits 0. Formats: RELEASE.md,
   "First-time setup of a feature repository".
4. **Build**, on order, by running the feature's build script in its package directory:

       (export ISABELLE=$PWD/<private tree>/bin/isabelle; cd <package dir> && bash tools/release_build.sh)

   Every feature should have `tools/release_build.sh`; one that needs nothing built beyond HOL may go
   without it and build the sessions of `tools/required_sessions.txt` by hand. The script runs
   `"$ISABELLE" build -b ...` on what must build before the release, at least the sessions of
   `tools/required_sessions.txt` (read the list, skipping its `#` comment lines, rather than repeat
   it); anything else it needs (the AFP, options) it brings itself. The release workflow (step 8) runs
   it too, in every environment of a batch that holds this feature, and a failure there stops that
   release:
   - Commit the script and every file it reads, on order, before step 5: the workflow takes the
     feature repository at its release tag, without `.git`, so the script cannot call git.
   - Give every `-d` by a relative path inside the feature repository (Isabelle refuses Windows paths).
   - The feature packages of that environment are installed there, so Isabelle already knows every
     session they ship as an Isabelle component; give a `-d` for such a session only when Isabelle does
     not know it yet: `dirs=; "$ISABELLE" sessions <session> >/dev/null 2>&1 || dirs="-d ."`.
   - macOS has Apple's bash 3.2 and BSD tools, Windows Git Bash (`$ISABELLE` is `isabelle.bat`), and
     the machines are slow (HOL takes about an hour on GitHub's macOS runners): give session `timeout`s
     and ML `Timeout.apply` room, for example with `-o timeout_scale=<n>`.
5. **Release:** `isabelle-patch-control make-patches -C <private tree> --package <package dir> <F> <m>`
   (`<m>` = 1 for the first release on the line, then 2, 3, …).
   Rerun it after a failure.
6. **Push**, on order: `git -C <private tree> push origin <R>/<F> <R>/<F>/<m>` and
   `git -C <feature repository> push origin main <R>/<F>/<m>`.
7. **The features on this one:** `grep -l 'base = <R>/<F>$' contrib/*/.gitmodules`. Tell the owner;
   each of them merges this release (3.3) and is released in turn, in its own private tree.
8. **Publishing to the conda channel**, on order. Before the first dispatch, run the check of the
   SKILL conda-release, "4. Before: check where the workflows download from", on the patch tool's
   checkout, `contrib/my_better_isabelle_prover` (it holds `release-features.yml`; a feature
   repository has no workflows). Dispatch the patch tool's `release-features.yml` with
   `publish=false`; when its roundtrip, accept and sessions jobs are green, dispatch it again with
   `publish=true`. Its `features` input lists the release tags to publish, in any order, with those
   they are built on that are not yet published for this `isabelle` build. When the `isabelle` conda
   package gets a new build, every feature package is re-released the same way, with the same
   versions. The inputs, jobs and recovery: RELEASE.md, "The batch release workflow".

### 3.5 Moving `daily` (on the owner's order)

1. Build dev_patches as in 3.4 step 4 (when it has no `tools/required_sessions.txt`, the sessions the
   owner names) in its private tree, on order, with its HEAD equal to `origin/<R>/dev_patches` and an
   empty `git status`.
2. Notify every session.
3. `git -C contrib/<R> fetch`, then `git -C contrib/<R> merge --ff-only origin/<R>/dev_patches`.
   On another machine: `git -C contrib/<R> pull --ff-only`.
4. Rebuild the shared tree's heaps with the owner's authorization.
5. Push `daily` on order: `git -C contrib/<R> push origin <R>/daily`.

### 3.6 Opening a new feature (on the owner's order)

1. The owner creates the GitHub repository; clone it as `<feature repository>`, directly in `contrib/`
   next to `contrib/<R>` (new-tree looks for the shared tree there).
2. `isabelle-patch-control new-tree --home <feature repository> --base <R>/<base> <R>/<F>`
3. Push the new branch on order: `git -C <private tree> push -u origin <R>/<F>`. Ask for that order
   at once: features opened on this one, and other machines, need the branch on GitHub.
4. Add the files the first release needs: `init.sh` (the two lines `#!/usr/bin/env bash` and
   `isabelle-patch-control new-tree "$(dirname "$0")"`), `tools/patched_files.txt` and
   `tools/signature_additions.txt` (made as in 3.4 step 3), `tools/required_sessions.txt`,
   `tools/release_build.sh` (3.4 step 4), `tools/component_files.txt` if the package also ships an
   Isabelle component, `tools/license.txt` and a `LICENSE` when the package has a license,
   `.gitattributes` (`*.patch -text`), a README. Formats:
   RELEASE.md, "First-time setup of a feature repository". Add the feature's row to the table in the
   patch tool's `.github/workflows/release-features.yml`, on order.
5. The registration commit, on order:

       git -C <feature repository> add -- <the new files>
       git -C <feature repository> commit -- .gitmodules worktrees/<R>-<F> worktrees/<R>-<F>-stock <the new files>

   (new-tree has staged `.gitmodules` and the two trees), then push the feature repository on order.
6. Registering in MLML, on order: `git submodule add -f <url> <feature repository>`.

### 3.7 Changing a feature's base (on the owner's order)

Example: a new feature N goes between A and the feature F that is built on A. N is opened on A (3.6);
then F's base changes from A to N.
1. Check that the new base contains everything of the old base that F has merged: in F's private
   tree, `git fetch`, then `git merge-base --is-ancestor $(git merge-base origin/<R>/<old base> HEAD)
   origin/<R>/<new base>` must exit 0. Otherwise F's branch keeps commits of the old base that the new
   base lacks, F's release patches would carry them, and `make-patches` does not notice: ask the
   owner.
2. In F's feature repository: `git config -f .gitmodules submodule.worktrees/<R>-<F>.base <R>/<new
   base>`; commit `.gitmodules` on order; push on order.
3. Merge the new base into F's private tree as in 3.3. F can be released only once the last merged
   commit of N is a release of N.
4. Rerun `<feature repository>/init.sh`: the stock tree moves to the new merge base.

F's next release depends on N's package, through the base tag that `make-patches` records.

### 3.8 A new Isabelle release: the foundation (on the owner's order, once per release)

The owner decides which features the new line `<R2>` carries and their bases. Unpack the official
release `https://isabelle.in.tum.de/website-<R2>/dist/<R2>_linux.tar.gz` into `contrib/` and, in
`contrib/<R2>`, without rewriting any file:

    git init --initial-branch=<R2>/pristine
    git remote add origin https://github.com/xqyww123/isabelle-patched.git
    git fetch origin
    git update-ref refs/heads/<R2>/pristine refs/remotes/origin/<R>/pristine    # parent: the old line's pristine
    git read-tree HEAD                                                           # the index only

Write `.gitignore`: the old line's, with its launcher line `/<R>` renamed to `/<R2>`, plus every build
product the release adds. Before committing, look at the binaries `git add -A` would take
(`git add -A -n | grep -E '\.(jar|so|dll|dylib|exe)'`) and at every `module =` line of an
`etc/build.props`; ignore those directories (for example `/src/Tools/Scalajs_Demo/lib`, new in
Isabelle2026). Then:

    git add -A
    git commit -m "<R2> pristine: the official release"
    git tag -a <R2>/pristine/<id> -m "<R2> pristine"       # <id> = the contents of etc/ISABELLE_ID
    git branch <R2>/daily
    git symbolic-ref HEAD refs/heads/<R2>/daily
    git config branch.<R2>/daily.mergeoptions --ff-only
    git push origin <R2>/pristine <R2>/daily <R2>/pristine/<id>
    git branch -u origin/<R2>/daily

`git status` is empty afterwards. No hg repository is involved, and no new repository: the new line
is new branches in isabelle-patched. Other machines get `contrib/<R2>` by 3.1.

### 3.9 Upgrading a feature to a new Isabelle release

Each feature's agent does this for its feature, a base before the features on it. Before you start,
the foundation (3.8) exists, and your base on the new line has its `<R2>` branch on GitHub.
1. `isabelle-patch-control new-tree --home <feature repository> --base <R2>/<base> <R2>/<F>`
2. Push the new branch on order, and ask for that order at once:
   `git -C <feature repository>/worktrees/<R2>-<F> push -u origin <R2>/<F>`.
3. The registration commit, on order: `git -C <feature repository> commit -- .gitmodules
   worktrees/<R2>-<F> worktrees/<R2>-<F>-stock`; push the feature repository on order.
4. Bring your work over; decide with the owner:
   - **Merge the old line's branch.** Wait until, after `git fetch`, `git merge-base --is-ancestor
     origin/<R>/<base> origin/<R2>/<base>` exits 0 (your base's `<R2>` branch has merged its old
     line's branch and been pushed; true at once for `pristine`), or `git tag --list '<R2>/<base>/*'`
     prints a tag (your base was implemented afresh and has released on the new line). Then, in your
     private tree on the new line: merge `origin/<R2>/<base>` as in 3.3 (a fast-forward, with nothing
     to commit, while `<R2>/<F>` has no commit of its own; run `bash <feature repository>/init.sh`
     right after it); then
     `git merge --no-commit origin/<R>/<F>`. In the other order there are two merge bases, and new-tree
     and make-patches refuse. The merge brings your old-line work, plus any old-line work below it that
     your base's `<R2>` branch does not contain. Remove by editing what the new line does not carry;
     `make-patches` does not notice what is left. `git diff --cached --stat` shows what came in.
   - **Or implement the feature afresh** on the new line.
5. Build and test on order; commit on order; push on order.
6. Release by 3.4 once your base has released on the new line.

Later fixes of the old line come over by the same merge.

## 4. Where the details are

- The patch tool's `RELEASE.md`: the reason and corner cases of each checklist point; the formats of
  the package directory's files; the batch release workflow's inputs, jobs and recovery.
- `isabelle-patch-control <subcommand> --help`.
- Each feature repository's own documents: its README, and its `details.md` or the plans in its
  `ai-artifacts/` where it has them.
