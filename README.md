# isabelle-patch-control

GitHub: <https://github.com/xqyww123/isabelle_patch_control>

`isabelle-patch-control` applies the Isabelle *feature packages* installed in a conda environment
to that environment's Isabelle, reverses them when they are removed, and reports the state of
every feature. It is a framework: it carries no patches of its own. Each feature package carries
its patch files and a provenance file; the tool reads them from
`$PREFIX/share/isabelle_patch_control/features.d/<feature>/`, links the features into one chain by
their exact release tags, and moves each file of `$PREFIX/isa` to where the installed chain says it
should be. The engine is `git apply`, run only on single-file copies inside directories the tool
creates; Isabelle's tree is changed only by renaming a finished copy into place, one file at a time.

The text between the two rules below is the text every feature package's README starts with; it
lives in [`common-readme.md`](common-readme.md) and the release workflow copies it from there.

---

## Isabelle and its feature packages

Isabelle is the conda package `isabelle`, the official release unchanged. A *feature package*,
such as `isabelle-light-locale`, changes Isabelle's sources inside your environment when it is
installed and puts them back when it is removed. The tool that does this, `isabelle-patch-control`,
comes in with the feature packages as their dependency.

Two names used below: `<prefix>` is the environment's directory (`$CONDA_PREFIX` once the
environment is activated, `conda env list` shows it), and `isa/` is Isabelle's own directory inside
it, `<prefix>/isa`.

Install Isabelle with a feature (always name `isabelle` itself, see below):

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale
```

Update everything in the environment, then check:

```
conda update --all -c https://conda.qiyuan.me -c conda-forge
isabelle-patch-control status
```

If every feature line of the second command says `applied`, you are done. Give both `-c` arguments every time: the Isabelle channel has no `python` and no `git`, which the
tool needs, and conda-forge has them. (You can leave them out only if both channels are in your
global `.condarc`; a `.condarc` inside the environment does not apply to `conda ... -n`.) If you
forget them, conda does not see the Isabelle channel and cannot update `isabelle` or the feature
packages; run the command again with both.

Name `isabelle` in the install command: a feature package depends on one exact build of
`isabelle`, so conda would install Isabelle anyway, but only as a dependency. Removing the feature
package later would then remove Isabelle and its user directory with it, because conda removes
dependencies nobody asked for. Naming `isabelle` makes it a package you asked for, so it stays.

To see what is installed and whether every feature is in place, with the environment activated
(`conda activate isabelle`; without activating: `conda run -n isabelle isabelle-patch-control status`):

```
isabelle-patch-control status
```

The command exists only in an environment that has a feature package installed (it comes in as
their dependency); `command not found` means either that the environment is not activated or that
no feature package is installed there. A healthy environment looks like this, and the command
exits 0:

```
tree /home/you/miniconda3/envs/isabelle/isa   features.d /home/you/miniconda3/envs/isabelle/share/isabelle_patch_control/features.d
applied expose_foreign          Isabelle2025-2/expose_foreign/1          1 file
applied future_assign_interrupt Isabelle2025-2/future_assign_interrupt/1 1 file
applied light_locale            Isabelle2025-2/light_locale/1            32 files
```

The first line says where the tool looked; each line after it is one feature, listed from the
bottom of the chain upwards. `applied` on every feature line (and exit code 0) means everything is
fine. With no feature package installed the command prints `no feature packages installed` and
exits 0, which is also fine. Otherwise: `not-applied` means the feature's changes are not in
Isabelle's sources, and `half-applied` that some of its files have them and some do not; in both
cases run `isabelle-patch-control apply`, which puts in place whatever is missing and nothing else.
`CONFLICT` means a file has content the tool does not recognise; *When something went wrong* below
says how to fix it. `(hole below)` after an `applied` line means a feature printed above it in the
list is not fully applied; fix that feature first, as described for its state.
`isabelle-patch-control status -v` lists every changed file.

Installing, updating or removing packages applies and reverses the features by itself, so after
one of those commands you do not run `apply`; you run it when a message from conda asked you to
(the tool's messages are the paragraphs of conda's output that start with `isabelle-patch-control:`;
they say when the tool could not run or another run held its lock), or after `status` showed
`not-applied` or `half-applied`.

After a feature is applied or reversed, Isabelle rebuilds every heap that was not built from
exactly these sources on first use (HOL takes several minutes). To do it right away:
`isabelle build -b HOL`.

## Removing, re-installing, and what conda does on its own

- `conda remove isabelle-light-locale` reverses the feature's changes and deletes the files it
  created. conda also removes every package that was installed only as a dependency and that
  nothing you asked for still needs: the feature packages below it in the chain,
  `isabelle-patch-control`, and `isabelle` itself if you never named it. `conda remove --force
  <package>` removes that one package and nothing else; the tool still reverses its changes.
- Installing a package that is already installed changes nothing and does not make it a package
  you asked for (`conda env export --from-history` lists the packages you did ask for by name).
  `conda install --force-reinstall <package>` does, at the price of reversing and re-applying its
  changes. For `isabelle` the price is higher: the `isabelle` package deletes the environment's
  Isabelle user directory whenever it is removed or replaced (see below).
- Every `conda install` / `conda update` of `isabelle` or of a feature package re-applies the
  installed features by itself: a new `isabelle` build re-applies every feature, and a new version
  of one feature package re-applies it and the features above it.
- Features form a chain, each built on the one below. When a feature reports `CONFLICT`, the tool
  applies none of the features above it until the CONFLICT is fixed. Re-installing a feature
  package below the CONFLICT reverses it and everything above it, then re-applies up to the
  CONFLICT again. `isabelle-patch-control status -v` names the file; *You edited a file under
  `isa/`* below says how to fix it.
- Only conda runs the step that reverses a feature on removal. mamba 2.x, micromamba and pixi do
  not, so a feature removed with them leaves its changes in Isabelle, and the files it created stay.
  To get the original sources back and the remaining features re-applied, reinstall `isabelle` as
  described under *You edited a file under `isa/`*; the created files stay even then, but nothing
  loads them any more.

## When something went wrong

**A conda command was interrupted (Ctrl-C).** conda rolls the whole command back and deletes
`conda-meta/history`, after which it no longer treats the directory as an environment; the
changes the command had already made under `isa/` stay. Until repaired, every `isabelle` command
may print `### Missing Isabelle component`. `isabelle-patch-control status` prints the repair
while `history` is missing. Either recreate the environment in place,

```
conda create -p <prefix> -c https://conda.qiyuan.me -c conda-forge <every package you want to keep, and the one that was being installed>
```

(conda itself will not list the environment's packages while `history` is missing; `ls
<prefix>/conda-meta` shows one `<package>-<version>-<build>.json` per installed package), or
restore the file and install again:

```
touch <prefix>/conda-meta/history        # Windows: type nul > "<prefix>\conda-meta\history"
conda install -c https://conda.qiyuan.me -c conda-forge <those same packages>
```

If you do not want that feature after all, repair first, then `conda remove <its package>`: the
tool then reverses its changes and deletes its files, which a reinstall of `isabelle` alone would
not do for files the feature created.

**You edited a file under `isa/`.** `isabelle-patch-control status` reports the file as
`CONFLICT` (if `status -v` marks the file `(created by the feature)`, see the next paragraph
instead: a reinstall does not fix that case and costs the user directory). If you remember exactly
what you changed, undo it and run `isabelle-patch-control apply`. Otherwise save your edit elsewhere
and reinstall `isabelle`. Before that, copy anything of your own out of `isa/` and out of this
environment's Isabelle user directory (`isabelle getenv -b ISABELLE_HOME_USER` prints it; it is a
directory under `~/.isabelle` that belongs to this environment alone): the reinstall deletes that
directory, with the heaps built in it, its `etc/settings` and preferences, and every component you
registered by hand with `isabelle components -u`. Installed packages register their components
again; your own settings do not come back. Then:

```
conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle
```

Every file of the `isabelle` package is replaced and the installed features are re-applied; run
`isabelle-patch-control status` afterwards. If the edit was made *in place* (an editor that writes
into the existing file, such as vim with `backupcopy=auto`), it went through the hard link into
conda's package cache, and a plain reinstall would bring the edit back. The CONFLICT message
detects this case and names the cache directory to delete first; conda re-creates it from the
downloaded archive. Other environments built from the same cache (`conda env list`) may share the
edited file without reporting anything; reinstall `isabelle` there too. A personal edit of a file
that a feature also changes reads `CONFLICT` again every time; make such experiments in a separate
Isabelle installation (for example the official release), not under `isa/`.

**You edited a file a feature created.** Move your copy aside, then `isabelle-patch-control apply`.

---

## Coming from my-better-isabelle 0.x

See the section of that name in [AGENTS.md](AGENTS.md), which `isabelle-patch-control help` prints:
the new tool does not see patches applied by the old one; if you applied the old tool's dev patches
(`--category all`), reverse those, and only those, and uninstall the old package before installing
feature packages; the dev patches are now the package `qiyuan-dev-patches`.

## Documentation

- [reference.md](reference.md): every command, option, message and exit code.
- [develop.md](develop.md): how the tool works inside, the layout of the package, the tests.
- [RELEASE.md](RELEASE.md): the checklist before releasing a feature, and how the packages are
  built and published.
- [AGENTS.md](AGENTS.md): orientation for an AI agent; `isabelle-patch-control help` prints it.
- Plan and review record: `ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md`.

## Working in the Isabelle source repository

The Isabelle source repository is `contrib/Isabelle2025-2` plus its worktrees
`contrib/Isabelle2025-2-*`. A *feature* is one patch package. Its branches form one
chain, each based on the one before it (its *base branch*):
pristine → expose_foreign → future_assign_interrupt → light_locale → local_type_abbrev
→ localized_record → local_datatype → dev_patches. Branch names carry the Isabelle
release, as in `Isabelle2025-2/light_locale`; the branches of one release form a
*release line*.

- *Shared tree*: `contrib/Isabelle2025-2`, on branch `daily`, which only fast-forwards.
- *Private tree*: `contrib/Isabelle2025-2-<feature>`, the one worktree of that feature's
  branch. Its `contrib` is a link into the shared tree: never write through it.
- *Stock tree*: `contrib/Isabelle2025-2-<feature>-stock`, detached at
  `git merge-base <base branch> <feature branch>`: the tree without your feature, for
  comparison runs and golden files.

Inside the Isabelle source repository these rules replace CLAUDE.md's section
"Commit on `main` — never branch", including its sentence that sweeping another
agent's uncommitted changes into a commit is acceptable. CLAUDE.md's bans apply here
word for word: "Never use git stash, git checkout, git reset --hard, or any command
that discards or hides uncommitted changes" and "NEVER run `git clean` (in any form:
`-f`, `-d`, `-x`, `-X`, etc.)".

**Trees and branches**
- Edit and commit only in your feature's private tree. Never edit the shared tree or a
  stock tree. Plans and scratch files go to your project repository's `ai-artifacts/`,
  never into a tree.
- Never create, switch, rename or delete a branch, and never add, move or remove a
  worktree. The repository's hook refuses a new branch unless `ISABELLE_GIT_OWNER=1`
  is set; only the owner sets it.
- Only these move a tree's HEAD: your commits and merges in your private tree,
  `new-tree --stock` for your stock tree, `advance-daily` for the shared tree. Never
  `git switch`, `git checkout <rev>`, `git reset <rev>` or `git bisect`. To read another
  revision use `git show <rev>:<path>` or your stock tree.
- If a hook or script refuses, stop and ask the owner. Never work around it.

**Commits and merges**
- Stage only changes you made yourself, by explicit path: no `git add -A`, `git add .`,
  `git commit -a`. Commit only when the owner says so. Never amend, squash or rewrite
  a commit; never rebase, force-push, cherry-pick, or `git revert -m` a merge.
- Take in other work only by `git merge` of your base branch, starting from an empty
  `git status`. Resolve conflicts by editing, commit the merge, then build and test
  through `run-tree`, then move your stock tree with `new-tree --stock <feature>`.
- You may merge base commits that no release tag contains yet. You can release only
  when the last base commit you merged is a base release; merge again once the base
  has released.
- Push only on the owner's order.

**Running Isabelle**
- Run any tree other than the shared tree, stock trees included, only through
  `run-tree`: it starts Isabelle in a clean environment and asserts the tree's own user
  directory. Never call that tree's `bin/isabelle`, and never use a tool that finds
  `isabelle` by itself (Isa-REPL, isabelle-mcp, test drivers).
- Every `isabelle build` in any tree, including a heap build another command triggers,
  needs the owner's command or a standing authorization that names that exact tree.
- After a successful build in a private tree with an empty `git status`, `run-tree`
  marks the commit tested with a git note. Never write that note yourself. While such a
  build runs, do not commit or change tracked files in any repository given with `-d`:
  the note is not written if one of them changed, and `run-tree` names that directory.
- Probes that need the REPL or isabelle-mcp run on the shared tree only, and only
  before any commit of your feature reaches `daily`. Every other comparison run uses
  your stock tree.

**Daily and releases**
- `daily` advances only through `advance-daily`, run on the owner's order. It lists the
  sessions that depend on the shared tree; notify them before confirming, and rebuild
  the heaps with the command it prints afterwards.
- Release only through `make-patches <feature> <version>`, run on the owner's order. It
  runs the release gates on a tested commit, creates the release tag last, and
  generates the package's exact pin on its base package. Never create, move or delete
  a release tag by hand.
- On a user's machine the patch tool applies packages in chain order, skipping patches
  already present, and unpatches in reverse order.
- The one exception to merging only your base branch: when the owner opens a new
  release line, each of its branches merges the same feature's branch of the previous
  line, in chain order, through `new-tree`; later fixes of the older line are carried
  forward the same way. A newer line is never merged into an older one.

The scripts (`new-tree`, `run-tree`, `make-patches`, `check-signatures`, `advance-daily`,
`check-roundtrip`) and the repository hook live in [`tools/`](tools/); their toy runs are
`tools/tests/run-all.sh` and, for `check-roundtrip`, `tests/test_roundtrip.py`.
