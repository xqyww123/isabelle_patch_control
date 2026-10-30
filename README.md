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

Install Isabelle with a feature package:

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale
```

Name `isabelle` itself, as above: otherwise conda installs it only as a dependency, and removing
the last feature package later removes Isabelle too, with this environment's Isabelle user
directory. Give both `-c` arguments to every `conda create`, `conda install` and `conda update`:
without them conda does not see the Isabelle packages, or lacks the `python` and `git` the tool
needs. (You can leave them out if both channels are in your global `.condarc`.)

Check that every feature is in place:

```
conda activate isabelle
isabelle-patch-control status
```

(`command not found` means that the environment is not activated, or that it has no feature
package.) A healthy environment looks like this:

```
Checked the Isabelle sources in /home/you/miniconda3/envs/isabelle/isa against 3 feature packages.

Feature `expose_foreign` is applied.
Feature `future_assign_interrupt` is applied.
Feature `light_locale` is applied.

Everything is in order.
```

If it ends with `Everything is in order.`, you are done; otherwise its last lines say what to do.

With the environment activated, update everything in it later with this, then run
`isabelle-patch-control status` again:

```
conda update --all -c https://conda.qiyuan.me -c conda-forge
```

What to do when a feature cannot be applied or conda printed `Rolling back transaction`, how
removing and re-installing packages work, and more: `isabelle-patch-control help`.


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
- [AGENTS.md](AGENTS.md): what to do in each situation, for users and AI agents; `isabelle-patch-control help` prints it.
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
