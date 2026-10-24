# my-better-isabelle-prover

A patch manager for Isabelle installations.

GitHub: <https://github.com/xqyww123/my_better_isabelle_prover>

It carries the patches that the surrounding Isabelle/ML research stack needs: the
SIMD FFI of `Semantic_Embedding`, and — for development —
[`Isa-REPL`](https://github.com/xqyww123/Isa-REPL) and Isa-Mini, notably an ML
loader function that Isabelle2025-2 removed. This tool keeps those edits as
version-keyed unified diffs and applies, reverses, and checks them idempotently,
then rebuilds the affected Scala when needed.

> [!NOTE]
> **[Isabelle-MCP](https://github.com/xqyww123/Isabelle-MCP) no longer needs any
> patch.** It used to: `pide_control` gave `vscode_server` the PIDE requests it
> lacked, and its ML half gave PIDE a global-cancel command. Isabelle-MCP now
> ships its own `isabelle mcp_server` Scala component (which carries those
> requests as its own code) and cancels through an ML prelude injected at prover
> startup, built from the public `EXECUTION` API alone. `pide_control` and
> `perspective_eof_clamp` were therefore retired on Isabelle2025-2, and
> **removed from this repository on 2026-09-08**; the last state carrying them is
> tagged `last-isabelle2024-support` in both repositories. No remaining feature
> edits Scala, so `patch` no longer runs `scala_build` at all.

> [!IMPORTANT]
> **Developing against Isa-REPL or Isa-Mini needs
> `my-better-isabelle patch --category all`** (see [Categories](#categories)).
>
> Before using this tool, make sure the `isabelle` command is available — on
> your `PATH`, or passed explicitly via `--isabelle-bin PATH`. Every command
> needs it (to detect the version and locate `ISABELLE_HOME`) and aborts with an
> error if it cannot be found. The system `patch` command must likewise be
> installed.

```bash
pip install -e .
my-better-isabelle patch          # apply the `user` patches for the detected version
my-better-isabelle patch --category all   # ... plus the `dev` ones
my-better-isabelle status         # show what is applied
my-better-isabelle unpatch        # reverse them all
```

The Python version constraint is declared in `pyproject.toml`. See
**[reference.md](reference.md)** for the full list of prerequisites and CLI
options.

## Features

A *feature* is one self-consistent bundle of patches, stored per Isabelle
version. Run `my-better-isabelle status` to see which are applied.

| Feature | Category | Isabelle2024 | Isabelle2025-2 | What it adds |
|---------|:---:|:---:|:---:|--------------|
| [`future_assign_interrupt`](my_better_isabelle_prover/patches/future_assign_interrupt.md) | user | ✓ | ✓ | **Bug fix.** Stop `Future.assign_result` from swallowing an interrupt raised inside `Single_Assignment.assign`, which then surfaced as `exception Option` |
| [`expose_foreign`](my_better_isabelle_prover/patches/expose_foreign.md) | user | native | ✓ | Stop hiding Poly/ML's `Foreign`/`RunCall`/`CInterface` FFI structures, which 2025-2 forgets during the Pure bootstrap |
| [`register_thy`](my_better_isabelle_prover/patches/Isabelle2025-2/register_thy.md) | dev | native | ✓ | Restores `Thy_Info.register_thy`, removed in 2025-2 |
| [`show_types_nv`](my_better_isabelle_prover/patches/show_types_nv.md) | dev | ✓ | ✓ | Custom `show_types_nv` option: suppress type annotations on free/fixed variables only |
| [`expose_map_syn`](my_better_isabelle_prover/patches/expose_map_syn.md) | dev | ✓ | ✓ | Export the private `Sign.map_syn` so ML can wholesale replace/clear a theory's inner syntax |

## Categories

Each feature is either `user` or `dev`, and `my-better-isabelle patch` applies
**only the `user` ones by default**.

- **`user`** — needed by the user-facing systems. On Isabelle2025-2 that is now
  only the SIMD FFI of `Semantic_Embedding` (`expose_foreign`); the two
  Isabelle-MCP features are retired there and survive for Isabelle2024 alone.
- **`dev`** — needed only by developer/experiment infrastructure: **Isa-REPL**,
  and Isa-Mini's translator and AoA agent injector.

> [!WARNING]
> The three `dev` patches are **compile-time** dependencies of that stack —
> `Thy_Info.register_thy`, `Printer.show_types_nv`, `Sign.map_syn` simply do not
> exist without them, so the ML fails to compile. If you are building or running
> Isa-REPL / Isa-Mini, apply everything:
>
> ```bash
> my-better-isabelle patch --category all
> ```

`status` always lists every feature regardless of category; its *exit code*
reflects only the selected category (`user` by default). Categories live in
[`patches/categories.toml`](my_better_isabelle_prover/patches/categories.toml).

### `future_assign_interrupt` — don't turn a cancelled future into `exception Option`

The one feature here that fixes a defect rather than adding a capability.
`Future.assign_result` re-raised only `Fail` and dropped every other exception
from `Single_Assignment.assign`. An asynchronous interrupt — from
`Timeout.apply`, or from cancelling a racer's future group — could land in that
call's interruptible window, get swallowed, and leave the result unassigned; the
`the` on the next line then raised `exception Option` at `General/basics.ML:84`,
naming neither the interrupt nor its origin. The patch re-raises every exception,
restoring the invariant that code past that point depends on.

Reachable from ordinary proof work, not just from code that touches futures:
Pure takes the vulnerable path from `Lazy.force`, promise fulfilment and
proof-term construction. Diagnosed 2026-09-08 — evidence, the exposed call
paths, and the open upstream question in
**[future_assign_interrupt.md](my_better_isabelle_prover/patches/future_assign_interrupt.md)**.

### `register_thy` — restore removed theory registration (Isabelle2025-2)

`Thy_Info.register_thy` existed in 2024 but was removed by the 2025-2
theory-loader refactoring. `Isa-REPL` needs it to inject an already-built,
in-memory `theory` value into Isabelle's global loader database. The patch
re-adds it, restored from the 2024 source with one node-type adaptation. Pure ML
change — no `scala_build`. Details in
**[register_thy.md](my_better_isabelle_prover/patches/Isabelle2025-2/register_thy.md)**.

## Supported versions & verification status

Patch targets are keyed by the exact output of `isabelle version`
(e.g. `Isabelle2024`, `Isabelle2025-2`).

- **Isabelle2024** — `register_thy` and `expose_foreign` ship natively, so no
  patch is needed for them.
- **Isabelle2025-2** — `register_thy` applies and reverse-detects cleanly. The
  two retired Scala features were reversed from this distribution before removal,
  verified byte-for-byte against the pristine sources with `isabelle scala_build
  -f` re-run, so its Scala is stock again.
- **`future_assign_interrupt`** — authored against pristine source for both
  versions (the same diff serves both: that region is byte-identical). Applied
  and runtime-verified on Isabelle2025-2: 15 consecutive corpus passes clean,
  against a pre-fix baseline that reproduced within 9 minutes.
- **`show_types_nv`** — recorded for Isabelle2024 (reverse-recorded from the
  existing hand edit) and ported to Isabelle2025-2. On 2025-2 it is applied, the
  Pure heap has been rebuilt, and it is runtime-verified (free-variable type
  annotation suppressed). The end-to-end consumer path
  (`Isa-Mini/.../print_formats.ML`, `show_markup=false`, HOL terms) is pending
  the HOL/Isa-Mini rebuild.

## Documentation

- **[reference.md](reference.md)** — CLI reference: subcommands, flags, examples,
  exit codes, and runtime prerequisites.
- **[develop.md](develop.md)** — how the manager works, the patch-repository
  layout, and how to add a new patch.
- **[RELEASE.md](RELEASE.md)** — how a version is cut and published to PyPI.
- Feature docs (rationale / evidence):
  [`future_assign_interrupt.md`](my_better_isabelle_prover/patches/future_assign_interrupt.md),
  [`expose_foreign.md`](my_better_isabelle_prover/patches/expose_foreign.md),
  [`register_thy.md`](my_better_isabelle_prover/patches/Isabelle2025-2/register_thy.md),
  [`show_types_nv.md`](my_better_isabelle_prover/patches/show_types_nv.md),
  [`expose_map_syn.md`](my_better_isabelle_prover/patches/expose_map_syn.md).

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
  build runs, do not commit, edit or create files in any repository given with `-d`:
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
  already present, and unpatches in reverse order. Once a higher feature has changed a
  file, a lower feature's patch for that file reads CONFLICT; that is inherent in
  stacking.
- The one exception to merging only your base branch: when the owner opens a new
  release line, each of its branches merges the same feature's branch of the previous
  line, in chain order, through `new-tree`; later fixes of the older line are carried
  forward the same way. A newer line is never merged into an older one.

The scripts (`new-tree`, `run-tree`, `make-patches`, `check-signatures`, `advance-daily`)
and the repository hook live in [`tools/`](tools/); their toy runs are `tools/tests/run-all.sh`.
