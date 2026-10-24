# isabelle_patch_control plan rev 1 — review 1 (workflow wf_7579dcdd-4ea, 2026-10-23)

Critics: 84 findings (5 lenses). Merge editor: 29 challenges, 0 dropped. One fresh defender per challenge. Judge: ready = False.

## Judge summary

The plan is not ready for the owner's approval. Its central mechanism has two parts: each feature package's conda hooks call the tool with a one-directional command, and the tool works out each feature's state from per-feature dry-runs plus an "applied (covered)" heuristic. Both parts break in states users will reach in normal use. The states are: a routine `conda update isabelle` (C1); a failing hook (C2); a fresh stacked install on the real chain (C3); and a relink of a lower feature package (C4). Several smaller defects add to this. The plan cites some facts that are wrong (C13, C14, C16, C29), misstates owner records (C9, C10), contradicts itself on ordering and the Isabelle2024 sets (C11, C12), and publishes before it verifies (C19).

I re-checked the sources the defenders and the editor disagree on:
- conda 25.11.1 runs every pre-unlink before any unlink, and every post-link after all links (core/link.py:938-967).
- A failing post-link triggers a rollback that runs no script and deletes conda-meta/history (core/path_actions.py:1075-1080).
- A failing pre-unlink only logs a warning (link.py:1676-1683).
- Hooks get stdin, stdout and stderr all as PIPE (gateways/subprocess.py:83-117).
- In a pseudo-terminal, GNU patch with captured stdout answers its prompts at once. It hangs only when POSIXLY_CORRECT is set. My run is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/judge/c8.
- libmamba's remove keeps only packages named in the environment's history (conda_libmamba_solver/solver.py:558-582).
- conda-meta records a sha256 for all 24538 paths of the isabelle package.
- v0.3.0 and HEAD carry different Isabelle2024 sets, so a final old-line release must be 0.4.0, not 0.3.x.
- The owner already settled post-link installation (LIGHT_LOCALE_HANDOFF.md:84, :1958; LIGHT_LOCALE_PLAN_REV37.md:7796).
- PACKAGING_DESIGN §9 and §7.9 say what the critics claim they say.

Three structural changes, all supported by the defenders' experiments, fix most of the blocking and major findings together.

(1) One state model. Each file gets a level by replaying that file's own stack of patches. A half-applied feature becomes a named state that apply completes and unapply undoes. A file that a feature created, and that is present with exactly the patch's content, counts as consistent with both applied and not-applied. The applied features above k must form a prefix of the chain, and "covered" disappears. All three rules are needed. Without the third, a relinked tree would read as a hole and be refused.

(2) One writer routine. Every patch call goes through it, with fixed flags (-f, --read-only=ignore, -r -), captured output, POSIXLY_CORRECT scrubbed, and a check that the binary is GNU patch 2.7 or later. It dry-runs every file first and rolls back on any exception. It does no chmod and no copy. make-patches gate (c) imports this routine from the checkout.

(3) Hooks become one generated line calling a tool-owned `conda-hook` entry point:
- post-link runs an idempotent apply of the whole chain;
- pre-unlink stays a pure reverse of the feature and everything above it, and never applies anything (the editor's "reconcile" on pre-unlink is wrong, because at that point features.d still lists every package that is leaving);
- future isabelle builds' post-link calls the same entry point;
- the dependency on the tool gets an upper bound, <2.

Only the owner can settle nine things:
- the hook exit code (D4 items 16 and 2);
- the PACKAGING_DESIGN exception (D4 item 15);
- how to read D1's "逐步", and what happens to Isabelle2024;
- failing closed on unidentified conda builds, plus a release freeze;
- platform scope;
- support for Isabelle trees users installed themselves;
- whether light is published at step 4;
- a lower bound on the isabelle build for later versions of built-in features.

Everything else is author work. The state model, the hook design, tree discovery, the chain-by-tag rule, the recipe rendering and the tests need a focused re-review after revision. The remaining items are text and citation fixes.

## Questions for the owner

1. Hook exit code and pre-unlink failures (D4 items 16 and 2).
Background: conda runs every post-link only after it has linked every package of the transaction. When one post-link exits non-zero, conda unlinks every package of the transaction again, but it runs no script while doing so. Patches that earlier post-links in the same transaction applied therefore stay in the Isabelle tree, with no package recording them. On conda 25.11.1 that rollback also deletes conda-meta/history, after which conda no longer treats the directory as an environment. A non-zero pre-unlink is only a warning: the package is removed anyway.
Choose one:
(a) Recommended. Every feature hook exits 0, as RELEASE_CHECKLIST.md:259 already requires of all other hooks. The hook writes the tool's verdict and the remedy to $PREFIX/.messages.txt, which conda prints. A failed post-link then leaves the package installed but not applied: `status` shows this and `apply` repairs it. A failed pre-unlink's message lists the files under isa/ that stay modified or created.
(b) Post-link exits non-zero on failure, as decision 8 proposes, accepting the orphaned patches and the damaged environment.

2. What happens to the features when only the `isabelle` package is replaced (D4 item 1)?
Background: `conda update isabelle`, `conda update --all`, `conda install --force-reinstall isabelle` and `conda create --clone` relink the Isabelle tree but run no feature package's hook. Every applied feature silently disappears, while `conda list` still shows the feature packages.
Choose one:
(a) Recommended. Future `isabelle` builds' post-link calls the tool, when it is installed, to re-apply the installed features. The tool treats a leftover file that a feature created, and whose content is unchanged, as consistent with not-applied, so the relinked tree can be repaired. On the existing isabelle-2025.2-0, which cannot be changed, the user runs `isabelle-patch-control apply` once; the README documents this.
(b) A runtime check on the HOL side that refuses to start when a feature package is installed but its patches are not applied.
(Pinning feature packages to an exact `isabelle` build is excluded by ruling 21.)

3. Should isabelle-packaging-ci/PACKAGING_DESIGN.md record an exception for feature packages (D4 item 15)?
You already decided, on 2026-09-14 and 2026-10-11, that feature patches are installed by post-link and reversed by pre-unlink; this is not being reopened. But the document's §3.1 (:48-52) and §9 (:1007-1014) object to post-links that change files conda tracks for another package, or create files conda does not track. Its §7.9 (:876-882) already allows Isa-REPL's install script to patch register_thy.
Choose one:
(a) Record the exception. Name the narrower target: the channel's own tree in $PREFIX/isa, not an Isabelle the user installed. Name the accepted costs: heaps go stale and are rebuilt, and cleanup depends on pre-unlink succeeding.
(b) Leave the document unchanged.

4. How to read D1's "逐步" (step by step) for the Isabelle2025-2 dev patches.
Background: migration §5.3 (ISABELLE_GIT_MIGRATION_PLAN.md:410-411) says the tool release that drops the dev patches comes after qiyuan-dev-patches is first released. Under the plan, isabelle-patch-control 1.0.0 already ships and reads no Isabelle2025-2 patches, and qiyuan-dev-patches comes much later.
Choose one:
(a) Recommended. isabelle-patch-control has no patches from 1.0.0 on. The old my-better-isabelle-prover stays on PyPI, not yanked, and is documented as the carrier of the dev patches until qiyuan-dev-patches is released. That is 0.3.0, or the final 0.4.0 if you choose it in the next question. It serves only trees without isabelle-light-locale, because on a light tree the dev patches conflict in syntax_phases.ML. §5 step 7 becomes a repository cleanup with no release.
(b) Carry the dev patches inside isabelle-patch-control 1.x until qiyuan-dev-patches exists. This needs a special case: on a tree with light installed, the dev patches would sit on the same base as light, which the chain rule forbids.

5. Isabelle2024 support (the question ruling 25 left open).
Choose one:
(a) Recommended. Cut one final my-better-isabelle-prover 0.4.0 from today's tool HEAD, before the refactor. Compared with 0.3.0 it adds Isabelle2024/future_assign_interrupt and drops pide_control and perspective_eof_clamp. That is a behavioural break, so RELEASE.md's rule makes it 0.4.0, not 0.3.1. It keeps the user/dev categories with the user-only default, and becomes the supported tool for Isabelle2024. isabelle-patch-control then carries no patches at all.
(b) Drop Isabelle2024 support now. 0.3.0 and the git tag last-isabelle2024-support remain.
(c) Bundle the three sets inside isabelle-patch-control, as decision 9 proposes. Not recommended. As written it makes status, apply and unapply exit 3 on Isabelle2024. Fixing that needs either invented provenance, which also grows the default from one user patch to all three, or a separate mode outside the chain with its own user-only default, which re-creates categories.

6. Builds the tool cannot identify (C13).
Background: until the CI plan lands, every CI run makes a fresh hg commit. Any `isabelle` rebuild in that window therefore carries expose_foreign under an ISABELLE_ID the tool does not know. Migration §5.3 then says k=0, so `unapply`, or the pre-unlink of isabelle-expose-foreign, reverses expose_foreign and breaks Semantic_Embedding's SIMD FFI.
Choose one:
(a) Recommended. Do both of the following. First, publish no `isabelle` package from now until the first build that carries the built-in manifest, and record that rule in isabelle-packaging-ci/RELEASE.md. Second, refuse with exit 3 and "update isabelle" any tree inside a conda prefix that has neither the manifest nor a known ISABELLE_ID; this changes §5.3's "unidentified means k=0" for conda trees only, and keeps k=0 for trees outside conda.
(b) Only the release freeze.
(c) Neither: the plan as written.

7. Platform scope for 1.0 (D4 item 10).
Background: feature packages are noarch, so as written they install on all five platforms. Windows has no GNU patch, and its hook description in the plan is wrong. macOS's BSD-derived patch reads unpatched files as applied, and in a terminal it waits for an answer nobody sees.
Choose one:
(a) Recommended. Linux only. The tool's conda package depends on `__linux` and conda-forge `patch`, every feature package inherits that through its dependency on the tool, and no .bat hooks are shipped.
(b) Linux and macOS: `__unix`, conda-forge patch, and an acceptance leg on a macOS runner.
(c) All five platforms, which needs a separate Windows design: m2-patch, cygdrive paths, .bat hooks, the path-length budget, and a windows-latest leg.

8. Isabelle2025-2 trees that users install themselves, outside conda (D4 item 17).
Choose one:
(a) Unsupported. The README says Isabelle2025-2 features are conda-only, and the tool refuses such a tree unless --features-dir is given.
(b) Supported through --features-dir. The README documents the git route: clone each chain repository at its release tag and link <dir>/<feature> to <repo>/patches/Isabelle2025-2. The exact-tag chain check then replaces the version pins conda would otherwise enforce.
In both cases, a missing explicit --features-dir is an error, not a silent success.

9. Publication at §5 step 4.
Should isabelle-light-locale be published then? Light plan §9 (LIGHT_LOCALE_PLAN_REV37.md:5803-5805) says distribution is not done in this phase, and light is in milestone 3.
(a) Recommended. Step 4 publishes only isabelle-patch-control and the two base packages. Light is built and tested only in a local file:// channel.
(b) Publish light too.
Please also confirm the order: every package is first built locally and accepted from a local file:// channel, and is published only on your order after that, with the tool's conda package going out no later than its PyPI upload.

10. Dependencies of feature packages on `isabelle` (D4 item 9).
First: should every feature package declare `isabelle >=2025.2,<2025.3`? This is a range for the release line, not a pin; the consumer packages already do the same. Without it the solver can pair a future Isabelle with the 2025-2 chain. Recommended: yes.
Second: a later version of a feature that isabelle-2025.2-0 already has built in at version 1 (for example expose_foreign 2) will be solved onto that build, which has no constraints and can never get any. Choose one:
(a) The later version's package declares a lower bound on the isabelle build number. This touches ruling 21's wording that the pin is on the base feature package, "not isabelle's version or build number".
(b) Accept the residue. The tool refuses with exit 3, and with exit-0 hooks the user is told to update isabelle.

11. Two smaller D4 items.
(13) Should the tool take a lock so that two runs on one tree cannot interleave? The proposal is `fcntl.flock` on the ISABELLE_HOME directory itself, which creates no file. Measured without a lock, a race leaves a .rej file and a spurious failure. Choose yes or no.
(14) pixi and micromamba may not run link scripts. Choose one: (a) document that feature packages are supported only under conda; (b) test them and support them.

12. User-visible words.
The revised plan will list verbatim English text for your approval: the status labels, the heap notice, and the refusal messages. Please decide one naming point now. The plan's status label "built-in", and the proposed file etc/ISABELLE_BUILT_IN_FEATURES, reuse the word in the "#built-in components" heading of etc/components, in the same etc/ directory, where it means something else.
(a) Keep "built-in".
(b) Choose another label and file name. The documents would then use the migration glossary's phrase "前 k 节" for the concept.

13. skip_nitpick_examples.
Ruling 15 Q4 registers it as a patch directory inside dev_patches. The plan merges dev_patches into one flat feature, so skip_nitpick_examples survives as git commit 30aab6e and a README section, not as a directory. The migration plan :385-386 leaves the layout to this plan. Is that acceptable?

## Relaxations recommended

- One state model in place of the per-feature verdict and the "applied (covered)" heuristic. It has three rules:
(a) Each file above k gets a level by replaying its own stack: reversing the lower features on one scratch copy, and forward-applying the upper features on another (C3).
(b) A half-applied feature is a named state. apply completes it and unapply undoes it, file by file (C7).
(c) A file a feature created, present with exactly the patch's content, counts as consistent with both applied and not-applied, and unapply deletes it (C1).
The applied features above k must form a prefix of the chain, with at most one half-applied feature directly above it. All three rules are needed. Without (c), a tree relinked by conda would look like a hole and be refused.

- One writer routine, patch_tree, behind status, apply, unapply, apply-to and make-patches gate (c).
- It always passes `-f -p1 -F0 --no-backup-if-mismatch --read-only=ignore -r -`.
- It captures output and removes POSIXLY_CORRECT from the child's environment.
- It checks that `patch` is GNU patch 2.7 or later.
- It refuses symlinked targets and git trees.
- It reads the patch texts into memory and dry-runs every file before writing.
- It rolls back on any BaseException.
- It does no chmod and no copy, so other hard links cannot change by construction.
gate (c) imports it from the checkout (C7, C8, C14, C15, C16, C17).

- Hooks as one generated line calling a tool-owned entry point, e.g. `isabelle-patch-control conda-hook post-link|pre-unlink <feature>`.
- Post-link runs an idempotent apply of the whole chain.
- Pre-unlink is a pure reverse of the feature and everything above it, and never applies anything. Do not make it a reconcile.
- The entry point owns finding the tree, the .messages.txt channel and the exit policy.
- The tool dependency is `>=1.0,<2`.
- Future `isabelle` builds' post-link calls the same entry point, guarded by `[ -x ... ]`; their pre-unlink calls nothing.
(C1, C4, C18; the exit policy is the owner's choice, and exit 0 is recommended.)

- Link the chain by exact tags. Its bottom is the manifest, the legacy entry or the pristine tag. Every base_tag must equal the release_tag of the entry directly below it, and the release <R> is checked at the bottom. Manifest lines become `<release_tag> <commit>`. This replaces both name chaining and decision 4's special version-mismatch check (C6).

- Find the tree from files, never by running `isabelle`. Use `--isabelle-home DIR`, defaulting to sys.prefix/isa inside a conda env, and read the identity from etc/ISABELLE_IDENTIFIER, etc/ISABELLE_ID and the manifest. Use the default features.d only inside a conda env (conda-meta/history exists); an explicit directory that is missing is exit 3 (C14, C22).

- Use conda's own per-file sha256 record for the isabelle package (conda-meta paths_data) as optional evidence. It can verify that a claimed built-in feature is really baked into the build (C13). It can also report files under isa/ that changed with no installed feature explaining them, without any new untracked ledger (C2, D4 item 2).

- Render each feature-package recipe at build time from provenance.txt, using one template and one renderer in tools/. The renderer is used both by local builds and by one reusable release workflow, so no pin is ever typed or committed by hand (C21). Every feature package bounds `isabelle >=2025.2,<2025.3`, and the run_constraints on the isabelle side carry the build-string prefix (C5).

- Changes to make-patches that keep its output format:
- generate into gate (c)'s temporary directory, and write patches/<R>/ and provenance.txt only after every gate has passed;
- refuse blocks with no ---/+++ pair (empty files);
- add a gate on path length;
- import patch_tree instead of calling `patch` through PATH.
(C17, C24, C25, C27)

- Build every package locally, run the whole acceptance from a local file:// channel, and publish only after that and on the owner's order. Add tests of the hook layer on a toy channel in tools/tests, covering a failed post-link, relinks, pruning on removal, and that sibling envs and the pkgs cache stay untouched (C19, C20).

- Leave both Isabelle2024 and the Isabelle2025-2 dev-patch gap with the old package: one final my-better-isabelle-prover 0.4.0 cut from today's HEAD, so that isabelle-patch-control carries no patches at all (C11, C12; this is the owner's choice).

- Freeze `isabelle` releases until the first build carrying the manifest, and refuse unidentified builds inside a conda prefix, so that the built-in expose_foreign cannot be reversed by construction (C13; this is the owner's choice).

- Limit 1.0 to Linux in exactly one place, the tool's conda package: `__linux` plus conda-forge `patch`. Feature packages inherit it and ship no .bat hooks (C15; this is the owner's choice).

## Critics' overall notes

- conda: Through the conda lens, the plan's core mechanism is decision 8: patching inside per-package link hooks, with a non-zero exit that is supposed to trigger rollback. That mechanism rests on conda guarantees that do not exist. Rollback does not undo hook side effects, failed pre-unlinks are ignored, replacing or cloning the `isabelle` package never re-runs feature hooks, and files a feature creates are invisible to conda. I verified each point against the local conda 25.11.1 source and in isolated toy channels; outputs are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-conda/. The more elegant shape is one idempotent reconcile command that never fails a transaction, called by every feature hook and by the `isabelle` package's own hooks, together with a per-file state rule that tolerates new files left behind and constraints that tie each feature chain to its Isabelle release. It would make 'the tree carries exactly the installed features' hold by construction rather than by hook ordering and user discipline.

- design: The plan's outer shape is right: feature directories plus provenance files, a built-in prefix, and a directory interface that does not call isabelle. Its core is not: status is a heuristic over raw dry-runs that misreads stacked features in both directions, and the misreading reproduces on the real chain. Several states the design can reach are left unhandled: half-applied features, patches orphaned by conda rollback or by a failed pre-unlink, chains that mix versions or release lines, and the bundled Isabelle2024 sets. Five changes would turn most of these from invariants people must remember into ones that cannot be violated: compute the applied-prefix length by replaying each file's stack on a scratch copy; make apply all-or-nothing; link the chain by full tags; pass -f on every patch call; delete decision 7's chmod and copy step.

- consistency: The plan covers every §5.3 interface item, and its facts about make-patches' output and the current tool code are mostly right. Seen through the consistency lens, though, it misreads or leaves out several owner rulings. It answers only six of the nineteen D4 items while claiming to list them all. It reopens the post-link/pre-unlink direction that the light plan already settled, breaks D1's "逐步" ordering, contradicts the Appendix A sentence the owner approved word for word, and loses ruling 27's separation of release lines in its run_constrained and isabelle dependency. It also states several things that are false when checked: the old build's ISABELLE_ID, how the Windows hooks work, the claim that a failed apply leaves no .rej, the mode leak, and whether conda rollback leaves a clean state. Some of its decisions rest on those errors (decision 7, the post-link exit code, the k=0 fallback).

- landing: From the landing and operations angle, the tool design is mostly sound, but the conda side rests on three beliefs about conda that I measured as false on the local conda 25.11.1. First, a failed post-link does not undo the earlier post-links, and conda's rollback deletes conda-meta/history, the file conda uses to recognise an environment. Second, updating isabelle does not re-run the feature packages' scripts. Third, hook output is not shown to the user. On top of that, the landing order publishes permanently before verifying, and it leaves several windows in which users get an inconsistent set: an isabelle rebuild, trees patched by 0.3.0, the other four platforms, and the next release line. Most fixes are small: bracket every isabelle relink with the tool, check the whole chain before the first change, verify from a local channel before uploading, pin isabelle to its release line, and import the tool by path in make-patches.

- user: From the end user's and the maintainer's side, the plan's mechanism (hooks apply and reverse patches, `status` derives state from dry-runs) fails in routine conda use: `conda update isabelle` silently drops every applied feature and leaves light in a CONFLICT the tool cannot repair, nothing the hooks print reaches the user, and a failed hook leaves conda and the tree disagreeing. Three of the plan's claims are wrong as written: the recovery path in decision 8 (b), the contradiction between decision 9 and decision 3 that would make every Isabelle2024 command exit 3, and the facts given for the old build. Further gaps: dependencies that do not tie a package to its Isabelle release, a chain check by name only, a feature-level 'covered' rule, no Windows or macOS story, and no route for non-conda users. Most fixes are small and make invariants hold by construction: a per-file covered rule, a base_tag equality check, an `isabelle ==2025.2` pin, one hook entry point owned by the tool, `-r -` and `--read-only=ignore` for GNU patch, and re-apply hooks on new `isabelle` builds. All of them were checked against conda 25.11.1 source and a toy local channel in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-user.

## Challenges

### C1 [blocking] Replacing the `isabelle` package silently removes every applied feature, and light's created files then leave a CONFLICT state that the tool refuses to repair

Section: Decision 8 (b) (plan:209-211); decision 3 state rule (plan:139-140, 147-151); decision 11 (plan:243-249); §6 (plan:296-298)  ·  merged from: conda-conda-2, conda-conda-3, design-D3, landing-L1, user-U1

**Statement.** The plan relies on one invariant: the Isabelle tree carries exactly the installed feature packages, kept true by each feature package's own post-link and pre-unlink. That invariant breaks every time conda replaces the files of the `isabelle` package without touching the feature packages. This happens on `conda update isabelle`, `conda update --all`, a build bump the solver picks while installing something else, `conda install --force-reinstall isabelle`, and `conda create --clone`. Conda unlinks and relinks only packages whose records change (conda/core/solve.py:1417-1418) and runs scripts only for those packages (conda/core/link.py:938-967). So every patched file under `$PREFIX/isa` goes back to the build's original content, no feature hook runs, and `conda list` still shows the features. Files that a feature created are not in the `isabelle` package's file list, so they stay on disk. light creates three such files (ai-artifacts/isabelle-git-migration/RECORD.md:19-20: light_locale_axiom_facts.ML, exported_premises.ML, more_exported_premises.ML). Decision 3 calls a feature whose files disagree CONFLICT (plan:139-140); `apply` stops at CONFLICT and has no --force (plan:147-148); `unapply` reverses only applied features (plan:150). So the repair that decision 8 (b) promises, 'status shows not-applied and apply repairs it' (plan:210-211), does not happen: status shows CONFLICT and apply refuses. The plan's own §5 step 5 publishes the next `isabelle` build (plan:286; the k=2 build is announced at ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md:215-216), so every user with features will hit this on a routine update. The old build's pre-unlink also deletes `~/.isabelle/Isabelle2025-2-conda-<env>` (isabelle-packaging-ci/conda/recipe.yaml:210-231). The shipped heaps, which do not contain the features, therefore load at once, and Isabelle silently runs without light. `conda create --clone` copies untracked files before it links packages (conda/misc.py:276, 322-357), so light's post-link inside the clone reads CONFLICT and the clone fails. Evidence: three critics reproduced this independently against conda 25.11.1 in isolated toy channels. See /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-conda/run4.clean (T3 build bump, T4 force-reinstall, T6 clone), /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/conda-toy/update.log, and /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-user/envs/hooklog-e3.txt (no hook line during the update). On the real chain, /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/force_reinstall.py gives light_locale 29 files not-applied plus 3 applied, so CONFLICT, and dev_patches CONFLICT.

**Editor.** Every critic is right, and the evidence is strong: the conda source, three independent toy reproductions, and a run on the real chain. The plan considered only --force-reinstall, and it got even that case wrong. The critics split the fix into two halves, and both are needed. (1) The `isabelle` package's own pre-unlink and post-link must call the tool around every relink. Only future builds can get this; isabelle-2025.2-0 cannot be changed. (2) The state model must accept a created file whose content equals the patch's content as consistent with both applied and not-applied. Only then does the tree after a relink read as not-applied, so that it can be repaired. The critics missed that the two halves compose. Once (2) is in place, the new build's own post-link from (1) repairs even the first update away from isabelle-2025.2-0 automatically. Without (2), every user's first update needs manual deletion of files inside $PREFIX/isa. The alternative in conda-3, shipping created files as tracked files of the feature package, is rightly rejected: it changes make-patches' output, which plan:332 rules out.

**Relaxation proposed by the editor.** Replace the per-package directional hook commands with one idempotent command that makes the tree carry exactly the chain found in features.d and never fails the conda transaction. Call it from every feature package's hooks, and also from the post-link and pre-unlink of future `isabelle` builds, guarded by `[ -x "$PREFIX/bin/isabelle-patch-control" ]`. Pair it with a per-file state rule in which a created file with identical content counts as consistent with both states. Then 'the tree carries exactly the installed features' holds after any relink, clone or update by construction, no longer depending on which hooks happen to run.

**Defender: confirmed** (needs owner: False).

I tried to refute the challenge and could not, apart from one minor sub-claim. The editor's relaxation is right on the post-link side and wrong on the pre-unlink side.

1. Conda replaces `isabelle` and runs no feature hook. When `isabelle` changes, it is the only package conda unlinks and relinks. The solver diff is `unlink_precs = previous_records - final_precs` and `link_precs = final_precs - previous_records` (conda/core/solve.py:1417-1418). Scripts run only for the packages in those groups (conda/core/link.py:938-947 pre-unlink, :949 link, :964-967 post-link). The feature packages depend on `isabelle` of any version (plan:197-198), so their records never change. I checked this in an isolated toy channel under conda 25.11.1 (condatoy/run.out):
   - `conda update --all` and `conda update isa` both moved isa 1.0-0 to 1.0-1. The hook log has only `PREUNLINK isa build 0` and `POSTLINK isa build 1`.
   - The patched file went back to `a1 a2 a3`, the created `new.ML` stayed, and conda-meta still lists feat.
   - The plan's case (b), `--force-reinstall` (plan:210-211), is the same unlink-and-relink of one package (solve.py:1420-1432).
   - Decision 7's hard-link copy keeps the cache pristine (plan:187-188), so a relink always restores unpatched content.

2. The relinked tree reads CONFLICT under the plan's rules. Under decision 3 a feature with mixed file states is CONFLICT (plan:139-140). Decision 6 reads a present created file as applied (plan:180-181).
   - GNU patch 2.7.6, called with patcher.py:28-42's flags after a simulated relink, gives: modified file not-applied, created file applied (gnupatch experiment). A forward apply of a creation patch onto the existing file fails with rc=1.
   - Real chain, using read-only git on contrib/Isabelle2025-2: light_locale_branch adds 3 files and modifies 29 (`git diff-tree --name-status`, matching RECORD.md:19-20).
   - real/relink.out: after the relink, light_locale has 29 files not-applied and 3 applied, so CONFLICT. dev_patches reads CONFLICT because it shares attrib.ML with light.
   - `apply` stops at CONFLICT and has no --force (plan:147-148). `unapply` reverses only applied features (plan:150). So the repair promised at plan:210-211 does not happen.

3. Routine updates hit this. The next build is k=2 (migration plan:215-216), and plan:286 publishes it. The pre-unlink of the old build runs on update as well as on remove. It deletes `~/.isabelle/*-conda-*` (recipe.yaml:221-231; the published script is pkgs/isabelle-2025.2-0/bin/.isabelle-pre-unlink.sh). The shipped heaps then match the reverted tree, so Isabelle runs without light.

4. `conda create --clone` fails. Clone copies untracked files, including light's created files (misc.py:276, 322-349), before it links the packages through `explicit` (misc.py:351). My toy clone ran both post-links and `new.ML` was already present, so under the plan's rule light's post-link reads CONFLICT and exits non-zero (plan:206-207). critic-conda T6 shows the rollback.

5. The one overstated sub-claim: "a build bump the solver picks while installing something else" did not reproduce. `conda install other` kept isa-1.0-0, because conda tries a frozen solve first (condatoy/run.out). It happens only when the request needs a different `isabelle`. The other four paths do reproduce.

6. The plan has no defence against this. `run_constrained` only constrains feature versions. Migration ruling 21 (migration plan:87-90) rules out pinning feature packages to an exact `isabelle` build, which would have forced conda to relink the features. The §6 acceptance (plan:296-298) does not test update, force-reinstall or clone.

7. The editor's relaxation.
   - Half (2), the state rule, is right. It is also enough: on the real chain, the relaxed rule plus an apply in chain order repairs the relinked tree to exactly the dev_patches tip (relink.out: "repaired tree == tip tree: True").
   - The rule needs three details. `apply` must skip created files already present, because GNU patch rejects them. `apply` must re-evaluate each feature after the ones below it are applied: a snapshot taken after the relink still reads dev_patches as CONFLICT. `unapply` must also delete identical created files of a feature that reads not-applied; otherwise `conda remove isabelle` leaves `isa/` behind, which breaks plan:297-298.
   - Half (1) is right on the post-link side. At every post-link, features.d already holds all the transaction's features, including at isa's own post-link (condatoy/run2.out). So one idempotent `apply` with no --feature is correct there. The `isabelle` post-link must exit 0, because a rollback relinks the old, unpatched build, and failing repairs nothing.
   - Half (1) is wrong on the pre-unlink side. Conda runs every pre-unlink before it removes any file (link.py:938-951). In run2.out, `PREUNLINK f1 sees features.d: f1 f2` and `PREUNLINK isa sees features.d: f1 f2`. A command that "makes the tree carry exactly features.d" therefore does nothing at a feature's pre-unlink: the patches stay applied while their patch files are deleted. At isa's pre-unlink during `conda remove isabelle` it would re-apply everything and leave the created files behind. The feature pre-unlink must keep the plan's directional `unapply --feature F`, and `isabelle`'s pre-unlink should call nothing.
   - "Never fail" for the feature hooks is not needed to fix C1. Changing it would change decision 8's exit-code proposal, which is still waiting for the owner (plan:302).

Experiment: All work is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C1/.

(1) gnupatch/: toy git repo with patches in the make-patches format, one modified file and one created file (`--- /dev/null`). I ran the status rule with patcher.py:28-42's flags (setsid, stdin closed). Pristine: both files not-applied. Applied: both applied. After the simulated relink (modified file restored, created file kept): mod not-applied, new applied, so the feature is CONFLICT. Forward apply of the creation patch onto the existing file: "already exists ... Skipping patch", rc=1.

(2) real/relink.py, output in real/relink.out: read-only git diff-tree/archive on contrib/Isabelle2025-2 for the chain future_assign_interrupt, light_locale, dev_patches on the expose_foreign tree. After the relink: created files left on disk; plan status {fai: not-applied, light: CONFLICT (29 not-applied, 3 applied), dev: CONFLICT (7 not-applied, 1 CONFLICT)}. With the relaxed rule and an apply that re-evaluates each feature in chain order, all three apply and the tree equals the dev_patches tip. A snapshot status taken before that apply still shows dev CONFLICT.

(3) condatoy/run.sh, output in run.out: conda 25.11.1 with fake HOME, private pkgs cache and a file:// channel. Installing an unrelated package kept isa build 0. `update --all` and `update isa` bumped isa; hooks: only PREUNLINK isa 0 and POSTLINK isa 1; a.ML reverted, new.ML kept, feat still in conda-meta. In `--clone`, new.ML was present when the post-links ran.

(4) condatoy/run2.sh, output in run2.out: every hook logs which feature directories it sees. Every post-link sees all features. Every pre-unlink, including isa's during `conda remove isa`, still sees all leaving features.

Recommended fix: Five changes to the plan:

(a) Decisions 3 and 6, state rule. A created file (`--- /dev/null`) that is present with exactly the patch's content is consistent with both applied and not-applied. A feature whose other files are all not-applied reads not-applied. A feature made only of such files reads applied.

(b) Decision 3, how `apply` and `unapply` act.
- `apply` works file by file and skips created files that are already present.
- `apply` judges each feature only after the features below it are applied.
- "applied (covered)" is always computed over the whole chain, even when `--feature` is given.
- `unapply` also deletes such a created file when its feature reads not-applied.

(c) Decision 8, hooks.
- Every feature post-link runs the same idempotent `apply`, without `--feature`.
- Feature pre-unlink keeps `unapply --feature <F>`. Reason: at pre-unlink time features.d still lists every package leaving in the same transaction (link.py:938-951), so a command that reconciles the tree to features.d would do nothing there.

(d) Decision 11, a third requirement on the CI plan. Future `isabelle` builds' post-link runs `[ -x "$PREFIX/bin/isabelle-patch-control" ] && isabelle-patch-control --isabelle-bin "$PREFIX/isa/bin/isabelle" apply` and always exits 0. Their pre-unlink calls nothing. With (a) in place, this also repairs the first update away from isabelle-2025.2-0.

(e) Rewrite decision 8 (b) and the acceptance tests.
- Decision 8 (b) names `conda update isabelle`, `conda update --all`, `--force-reinstall` and `--clone`.
- On isabelle-2025.2-0 itself, after a force-reinstall, a manual `apply` is needed, and it now works.
- §6 and decision 12 add real-environment and pytest cases for a build bump, a force-reinstall and a clone.

Do not adopt the editor's version for pre-unlink hooks, and do not adopt "never fail" for feature hooks. The second one belongs to the owner's pending decision on install timing (§7 item 1).

**Judge: confirmed → author_decides_then_rereview.** Rewrite decision 8 (b) and the state rule in decisions 3 and 6.
(1) A file created by a feature (`--- /dev/null`) that is present with exactly the patch's content is consistent with both applied and not-applied. The feature's verdict comes from its other files. `apply` skips such a file, and `unapply` of a not-applied feature deletes it, so `conda remove isabelle` leaves nothing behind.
(2) Every feature post-link runs the same idempotent apply of the whole chain, without --feature. The feature pre-unlink stays a pure reverse of F and everything above it. Do not make it a reconcile: at pre-unlink time features.d still lists every package that is leaving (link.py:938-947).
(3) Add a third requirement to decision 11: future `isabelle` builds' post-link calls the tool's conda-hook entry point, guarded by `[ -x "$PREFIX/bin/isabelle-patch-control" ]`, and always exits 0. Their pre-unlink calls nothing.
(4) Name the real triggers: `conda update isabelle`, `update --all`, `--force-reinstall isabelle` and `create --clone`. Document that on isabelle-2025.2-0 itself the first repair is a manual `apply`.
(5) Add pytest and §6 cases for a build bump, a force-reinstall and a clone.
Drop the claim that the solver changes isabelle while installing an unrelated package; it did not reproduce. The choice of remedy is D4 item 1 and goes to the owner as a question.

### C2 [blocking] A failing hook does not keep conda and the tree consistent: rollback never undoes earlier post-links, it deletes conda-meta/history, and pre-unlink failures are ignored

Section: Decision 8, post-link exit code (plan:206-207); §2.3 (plan:90-91); decision 3 unapply (plan:150-151); §6 (plan:297-298)  ·  merged from: conda-conda-1, conda-conda-4, design-D4, consistency-C3, landing-L2, user-U3

**Statement.** Decision 8 makes the post-link exit non-zero on CONFLICT 'so that conda rolls back this install' (plan:206-207), and §2.3 says a non-zero exit rolls back the whole install (plan:90-91). Conda 25.11.1 does something else. (a) Conda links every package of the transaction first and only then runs the post-links, one after another. A failing post-link is recorded and the remaining post-links still run (conda/core/link.py:949-967; the loop stops only at :1006-1007). (b) The rollback only reverses file actions. No script runs during it (link.py:1038-1045, 1129-1160; run_script is called only at :942 and :1109). So patches that earlier post-links in the same transaction applied stay in the tree, while their packages and features.d entries are removed. If the tool was installed in the same transaction, it is removed too. Example: an env holds only `isabelle`, and the user runs `conda install isabelle-light-locale`. Conda also links isabelle-future-assign-interrupt, whose post-link patches future.ML. Then light's post-link fails. Afterwards future.ML is patched, and nothing on the machine knows why. (c) The rollback also deletes conda-meta/history. UpdateHistoryAction.reverse puts the saved copy back and then unconditionally rm_rf's the file (conda/core/path_actions.py:1075-1080). That file is how conda recognises an env (conda/base/constants.py:334). So after one failed feature install into an existing env, such as a user's AoA env, conda rejects the prefix with DirectoryNotACondaEnvironmentError (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/conda-toy/rollback4.log). (d) In an update transaction, the old features' pre-unlinks have already reversed their patches. The rollback relinks the old packages without running their post-links, so conda reports light v1 as installed while the tree has no light (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-user/envs/e6). (e) A failing pre-unlink only logs a warning, and the removal goes ahead (link.py:1647-1683; the return value is ignored at :942). The plan states no exit policy for pre-unlink. `unapply` walks down from the chain tail and stops at the first CONFLICT, so one upper feature that cannot be reversed also blocks independent lower features that could be (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-conda/t7.out). Realistic triggers: a user edit, the leftover states of C1, a cross-line pairing (C5), and the exit-3 version mismatch of decision 4 (plan:160-162). The project's own checklist says 'Every hook ends exit 0. A nonzero post-link rolls the whole install back' (isabelle-packaging-ci/RELEASE_CHECKLIST.md:259), and both published consumer packages obey it (Semantic_Embedding/conda/recipe.yaml:264-271; Isabelle_RPC/conda/recipe.yaml:148-176).

**Editor.** Every particular I checked in the conda source is correct (link.py:938-1045, 1095-1160, 1625-1708; path_actions.py:1075-1080). The history deletion is a conda bug, not a defect of the plan. It still belongs here, because it turns the plan's chosen exit policy from 'clean rollback' into 'damaged env'. Two critics overreach. consistency-C3 and landing-L2 suggest keeping a non-zero exit when a whole-chain dry-run fails before anything has been written. Even that path goes through the rollback and deletes conda-meta/history (point c), so it is not clean either. On this conda, only exit 0 is safe. The choice of exit code is also D4 item 16, which the owner reserved (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979). The plan decided it on its own authority; C9 covers that consistency defect.

**Relaxation proposed by the editor.** Every hook exits 0 and reports through $PREFIX/.messages.txt. The tool's single reconcile command (C1, C4) is all-or-nothing within one invocation, so the tree is always a valid prefix of the chain. A failure then leaves the state 'installed but not applied', which `status` shows and the next run repairs. It no longer leaves orphaned patches with no package, and possibly no conda env.

**Defender: confirmed** (needs owner: True).

I tried to refute C2 and could not. Points (a) to (d) hold, both in the conda source and in my own toy-channel runs. Point (e) holds except for one inferred sub-claim.

What the plan relies on. Decision 8 makes post-link exit non-zero on CONFLICT "so that conda rolls back this install", because an unappliable package is "worse than rollback" (plan:206-207). §2.3 states the fact as "非零退出让 conda 回滚整次安装" (plan:90-91). The plan's own trigger for this path is "the user's Isabelle has incompatible changes", so the plan expects this path to be taken, not just in theory. The plan gives pre-unlink only a command and no exit policy (plan:202-203). Decision 8 (a) and §6 promise no residue (plan:210, 297-298).

(a) Post-link order and failure handling, conda 25.11.1 (_version.py). All pre-unlink and pre-link scripts of a group run first (link.py:938-946). Then the files are linked (:949-953), then entry points (:957-959). Then every post-link runs serially and failures are only collected (:964-967). The failing package's own files are reversed at once (:1116-1119), and the loop goes on. The register group, which holds the history action (:582-594), still runs (:994-1003). The loop breaks only after that (:1006-1007).

(b) The rollback reverses file actions and runs no script (:1038-1045, _reverse_actions :1129-1160 calls only action.reverse()). Experiment S1: env holds base only; install feat-b with feat-a=1. Afterwards tree.txt reads "pristine A", but feat-a is gone from conda-meta and features.d is empty. So a patch stays in the tree with no package behind it.

(c) UpdateHistoryAction.reverse puts the saved copy back and then deletes conda-meta/history unconditionally (path_actions.py:1075-1080). That file is how conda recognises an env (constants.py:334; cli/common.py:223-225). In S1 and S2, `conda list` and `conda install` then fail with DirectoryNotACondaEnvironmentError. The same code is in the cached conda 26.5.3 (path_actions.py:1121-1126), so this is not a one-version accident. Even without this conda bug, (a), (b) and (d) alone make a non-zero exit unsafe.

(d) Update transaction, experiment S2: env holds feat-a 1, applied; install feat-a=2, whose post-link fails. Afterwards feat-a-1-0.json is restored but tree.txt reads "pristine". The old pre-unlink had already reversed the patch, and the old post-link was never re-run.

(e) A non-zero pre-unlink only logs a warning: run_script raises only for pre-link and post-link (link.py:1649,1675); otherwise it warns and returns False (:1677-1683), and the caller ignores that (:942). Experiment S3: the pre-unlink failed, the package was removed, and "C" stayed in the tree. Experiment e7: a pre-unlink that cannot reverse, then `conda remove base feat-f`, leaves isa/src/New/new.ML behind. This contradicts the "no residue" promise (plan:210, 297-298). This case is exactly D4 item (2), and the exit-0 rule is D4 item (16). The owner reserved both (LIGHT_LOCALE_HANDOFF.md:1979). The plan's §7 item 6 (plan:307-309) answers neither, although §0 item 9 promises to list every D4 item (plan:36-37).

The sub-claim I do not accept. C2 says `unapply` stops at the first CONFLICT and so blocks independent lower features. The plan never says that; it only says successors must be removed first (plan:150-151). Refusing to reverse a lower feature under an upper feature that cannot be reversed keeps the tree a valid prefix of the chain, so that refusal is the correct behaviour. The real defect is that conda removes the package anyway. One nuance strengthens C2: all pre-unlinks run before any unlink (:938-946 runs before :949-953). So when fai's pre-unlink runs, light's features.d is still present, and light's CONFLICT makes fai fail too.

There is no alternative way to fail safely with a non-zero exit. A pre-link check aborts cleanly only when the transaction unlinks nothing (e5). In e6 it ran after the unlink side and nothing was rolled back: isa/tree.txt was deleted and conda-meta was left with base-1-0.json.c~. Pre-link also runs before anything in the transaction is linked, so neither the tool nor the other feature directories exist yet. Conclusion: only exit 0 is safe. The project already says so (RELEASE_CHECKLIST.md:259; isabelle recipe.yaml:118-122; Semantic_Embedding/conda/recipe.yaml:264-271; Isabelle_RPC/conda/recipe.yaml:150-176).

The editor's relaxation is right for post-link but incomplete. Experiment S4: post-link exits 0 and reports through .messages.txt. The env stays a conda env, both packages stay listed, the message is printed, and the tree is a valid prefix of the chain ("pristine A"). The claim that it "no longer leaves orphaned patches with no package" is false for pre-unlink: conda removes the package whatever the exit code (S3, e7). So the relaxation also needs a pre-unlink policy. Conda does print .messages.txt from a pre-unlink that exits 0 (link.py:1685, 1697; seen in e7).

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C2/. mkchan.py builds a toy noarch channel. Package base holds isa/tree.txt (mode 444). Package feat-a 1 applies "A" by write-and-rename, and its pre-unlink reverses it. Package feat-a 2's post-link fails. Package feat-b depends on feat-a, and its post-link fails. Package feat-c's pre-unlink fails. Package feat-d's post-link exits 0 and reports through .messages.txt. Package feat-e's pre-link fails. Package feat-f's post-link creates a new file, and its pre-unlink cannot reverse it. The runs (run.sh, run-prelink.sh, run-prelink2.sh, run-residue.sh) used conda 25.11.1 with a private CONDA_PKGS_DIRS and CONDA_REGISTER_ENVS=false. Outputs are in run2.out, run-prelink.out, run-prelink2.out and run-residue.out. S1 (install feat-b with feat-a=1 into an env holding base): the tree keeps A, feat-a is gone from conda-meta, conda-meta/history is deleted, and conda raises DirectoryNotACondaEnvironmentError. S2 (update feat-a 1 to 2, whose post-link fails): feat-a-1-0.json is restored, the tree has no A, and history is deleted. S3 (pre-unlink fails): a warning only, the package is removed, and C stays in the tree. S4 (the relaxation, exit 0): the env stays consistent, the message is printed, and the tree reads "pristine A". e5 (pre-link fails, install only): clean abort. e6 (pre-link fails in a transaction that also unlinks): no rollback; isa/tree.txt is gone and conda-meta/base-1-0.json.c~ is left. e7 (pre-unlink cannot reverse, then base is removed too): isa/src/New/new.ML remains. I also grepped the cached conda 26.5.3: it has the same history rm_rf (path_actions.py:1121-1126) and the same post-link loop and pre-unlink warning. And I read envs/isabelle/conda-meta/isabelle-2025.2-0.json: it records sha256 for every one of its 24538 paths.

Recommended fix: 1. §2.3 (plan:90-91): replace "非零退出让 conda 回滚整次安装" with the measured facts. A non-zero post-link makes conda unlink every package of the transaction. No hook runs during the rollback, so patches applied by earlier post-links stay in the tree. On conda 25.11.1 and 26.5.3 the rollback also deletes conda-meta/history, and conda then rejects the prefix (path_actions.py:1075-1080). A non-zero pre-unlink only logs a warning, and the package is removed anyway (link.py:1677-1683, :942).

2. Decision 8 (plan:206-207): put the hook exit policy to the owner as D4 item (16), with the proposal that post-link and pre-unlink always exit 0, as RELEASE_CHECKLIST.md:259 and both consumer recipes do. On failure, the hook writes the tool's verdict and the remedy to "$PREFIX/.messages.txt". A failed post-link then leaves the package installed but not applied: `status` shows it and exits 1, and `apply` repairs it once the cause is fixed. Also add a pre-unlink policy and put it to the owner as D4 item (2). Conda removes the package regardless of the exit code, so the message must name the files that stay modified or newly created under isa/, and say how to restore them. Optionally, without a ledger or any untracked file, `status` could compare isa/ against the per-file sha256 in conda-meta/isabelle-*.json and report changes that no installed feature explains.

3. Decision 8 (a) (plan:210) and §6 (plan:297-298): say that "no residue" holds only when every hook succeeds. Add failure-path acceptance tests on a toy channel: (i) a post-link CONFLICT leaves conda-meta/history in place, all packages listed, and `status` reporting the feature as not applied; (ii) a pre-unlink CONFLICT prints the message naming the leftover files. Do not offer pre-link as a way to fail safely with a non-zero exit: when the transaction also unlinks packages, a pre-link failure is not rolled back.

**Judge: confirmed → owner_decides.** Replace §2.3's "非零退出让 conda 回滚整次安装" (plan:90-91) with the measured facts:
- conda collects post-link failures, and the post-links after a failing one still run (link.py:949-967);
- the rollback reverses only file actions and runs no script (link.py:1038-1045, 1129-1160), so patches applied by earlier post-links stay in the tree with no package behind them;
- the rollback deletes conda-meta/history (path_actions.py:1075-1080), after which conda rejects the env;
- a non-zero pre-unlink only logs a warning, and the package is removed anyway (link.py:1676-1683).
Move the exit-code choice out of decision 8 into §7 as D4 item 16. Recommend that every hook exits 0 and writes the verdict and the remedy to $PREFIX/.messages.txt.
Add a pre-unlink policy as D4 item 2: the message lists the files under isa/ that stay modified or created. Optionally, `status` reports isa/ files whose sha256 differs from the isabelle package's conda-meta paths_data and that no installed feature explains. That is a ledger conda already keeps, so no new untracked file is needed.
State that "no residue" (plan:210, 297-298) holds only when every hook succeeds, and add failure-path tests on a toy channel. Do not offer pre-link as a safe way to fail.
Keep unapply's refusal to reverse a feature that sits beneath one that cannot be reversed. That sub-claim of the challenge is refuted: the refusal is what keeps the tree a prefix of the chain.

### C3 [blocking] The 'applied (covered)' rule misreads stacked features in both directions, and it does so on the real chain

Section: Decision 3 (plan:137-151); §4 (plan:265, 273-274)  ·  merged from: design-D1, consistency-C6, consistency-C7, user-U6, user-U17

**Statement.** Decision 3 first gives each feature a raw verdict: the conjunction of per-file dry-runs, where any mix of states is CONFLICT (plan:139-140). It then walks back from the chain tail. Once a later feature reads applied, every earlier feature that reads CONFLICT is relabelled 'applied (covered)', while an earlier feature that reads not-applied is called 'a hole, a real error' (plan:143-146). The rule decides covering per feature. It never asks whether the later applied feature patches the same file. That fails in three reachable ways. (1) It hides real problems. A real conflict, or a lost change, in a file that no upper feature touches is reported as 'applied (covered)', which is exactly how a correct stacked install looks. Reproduced in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/status_proto.py (scenario A), /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-consistency/covered_sim.sh and /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-user/covered/. The pre-migration shared tree is a real example: future.ML had been edited by hand, and the old tool reported CONFLICT (ISABELLE_GIT_MIGRATION_PLAN.md:350-351). Under the plan, light above it would hide that. (2) It reports false conflicts. When an upper feature's hunk context includes lines added by a lower feature, the upper feature reads CONFLICT whenever the lower one is not applied. This happens on the real chain. I re-ran /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/real_chain.py, which only reads git (archive, diff-tree) and patches a temporary directory. With only expose_foreign built in, the plan's rule gives {future_assign_interrupt: not-applied, light_locale: not-applied, dev_patches: CONFLICT}, caused by src/Pure/Syntax/syntax_phases.ML. So `status` exits 1 on a fresh install. `apply --dry-run` and `unapply --dry-run`, which test each feature against the unchanged tree, fail. (3) It can double-apply. Suppose an upper feature deletes or moves a line that a lower feature added. The correct state then reads lower = not-applied, which the plan calls a hole. `apply` forward-applies the lower feature again, and GNU patch silently duplicates the text (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/scenario_b2.py). The plan also leaves three things open: whether apply and unapply re-evaluate status between steps; whether covered counts as success for the exit code (plan:142 names only built-in and applied); and why the status line format lists four states (plan:141) while §4 lists five (plan:265). Finally, the owner approved word for word the Appendix A sentence 'Once a higher feature has changed a file, a lower feature's patch for that file reads CONFLICT; that is inherent in stacking' (ruling 23, ISABELLE_GIT_MIGRATION_PLAN.md:93-94 and :732-735; README.md:218-221; §7 rule 15 at :546-547). The plan changes what users see without proposing new wording.

**Editor.** I reproduced this on the real chain myself. `status` is the tool's only correctness check, and it is wrong in exactly the states users will have. The per-file fix in consistency-C7 and user-U6 says that a CONFLICT on file p is expected if and only if some later applied feature also patches p. It only patches the heuristic: it fixes (1) but not (2) or (3). D1's fix replaces the heuristic with a computed quantity, and that is the right fix. The critic measured about 0.9 s on the real chain's 41 files. consistency-C6 overreaches in calling this a contradiction of a ruling. The approved sentence describes what a raw dry-run reads, and that stays true. But the sentence is user-facing text the owner approved, so any change to the displayed status must come with proposed replacement wording for the owner. That part stands.

**Relaxation proposed by the editor.** Drop the five labels and the covering heuristic, and compute one number instead: L, the length of the applied prefix of the chain (k <= L <= n). For each file touched above k, replay that file's own stack on a scratch copy. First reverse, in reverse order, the features <= L that touch it, then forward-apply the features > L that touch it. The tree is at L when every file agrees. A file with no consistent level is CONFLICT, reported with that file and the first feature that fails on it. Features <= L are applied and the rest are not-applied. A half-applied feature shows up file by file (C7). `--dry-run` is the same replay without writing. 'Covered' stops being a concept, so it cannot be misapplied.

**Defender: partially_confirmed** (needs owner: False).

I could not refute the core of the challenge. All three failure modes follow from the plan text, and two of them reproduce on the real chain content. The only part that does not hold is the demand for replacement wording of the owner-approved sentence.

What the plan says. A feature's raw verdict is the conjunction of its per-file readings, and any mix is CONFLICT (plan:139-140). Covering is then decided per feature: once a later feature reads applied, every earlier feature that reads CONFLICT becomes 'applied (covered)', and an earlier not-applied feature stays not-applied as 'a hole, a real error' (plan:144-146). No step asks whether the later feature touches the same file. That is also a misreading of the rule it cites. Migration §7 rule 15 (ISABELLE_GIT_MIGRATION_PLAN.md:546-547), §5.3 (:426) and the approved Appendix A sentence (:732-735 = README.md:218-221) all talk about one file at a time ('上层 feature 改过的文件', '同一文件', 'a lower feature's patch for that file'). None of them licenses covering a whole feature.

(1) It hides real problems, and this reproduces on the real chain. I generated the chain the same way make-patches does (make-patches:154, `git diff-tree -r -p --no-renames`, one block per file) and patched a temp copy. In the tree, future.ML is patched only by future_assign_interrupt. With all three features applied and future.ML then hand-edited inside its hunk, the plan reports {future_assign_interrupt: applied (covered), light_locale: applied (covered), dev_patches: applied}, so the exit code is 0 for a broken tree. This is exactly the pre-migration case the old tool caught as CONFLICT (migration plan :350-351). A second case: morphism.ML, which only light touches, is restored to its base content (a lost change). The plan again reports everything applied or covered.

(2) It reports false conflicts on a fresh tree. With only expose_foreign built in, the plan gives dev_patches CONFLICT. I confirmed this with the tool's own flags (patcher.py:31,37): '1 out of 3 hunks FAILED'. The failing dev hunk `@@ -739,9` has context lines `else main arg;` and `in Ast.mk_appl c (map mark_arg args) end)`, which light's hunk `@@ -694,8 +729,15` adds. Consequences:
- `status` exits 1 on a fresh install. Plan:44-45 promises a correct status at any time.
- Plan:211 claims that after `--force-reinstall` the status 'shows not-applied'. That claim is false.
- `--dry-run` is kept as is (plan:149). Today's dry-run tests each patch against the unchanged tree (patcher.py:67,86-87). So `apply --dry-run` fails on dev_patches on a fresh tree, and `unapply --dry-run` fails on light_locale when all three are applied. I measured both.
- The per-file rule proposed in consistency-C7 and user-U6 still gives dev_patches CONFLICT on the fresh tree, so it does not fix (2). It does fix (1).

(3) It can double-apply. This does not happen on today's chain: once dev is applied, light's files read applied, except syntax_phases.ML, which reads CONFLICT. It is still reachable through the plan's own install flow:
- In a toy case where the upper feature moves a line that the lower feature added, the lower feature reads not-applied, and forward-applying it duplicates the line.
- A more natural case: the upper feature renames a file that the lower feature created. The lower feature reads not-applied, and forward-applying it recreates the deleted file. The upper feature then reads CONFLICT.
- Plan:147-148 forward-applies every not-applied predecessor of `--feature F`, and every post-link runs `apply --feature <its feature>` (plan:202). So installing any later package silently 'repairs' the reported hole into corruption. The plan calls a hole a real error (plan:146) and then fills it (plan:147), which contradicts itself.

The open points are confirmed:
- Whether apply and unapply re-read status between steps is unspecified. Today's code re-reads per patch (patcher.py:67), but a whole-chain covering verdict cannot be computed that way.
- The exit-code rule names only built-in and applied (plan:142). Plan:145 does say covered '不算错误' (is not an error), so this is a weak ambiguity.
- The status line lists four states (plan:141), §4 lists five (plan:265), and the test list at plan:255 says '四种状态与 covered' (four states and covered).

Refuted part: no replacement wording for ruling 23 is required. The approved sentence describes how one lower patch file reads on a raw dry-run, and that stays true under any fix. In fact it explains why status must replay each file's stack. The fix does not need to touch Appendix A, so this is not an owner decision.

The editor's relaxation is right in substance, with three corrections:
(a) Read as one sequence on one copy, 'first reverse the features <= L, then forward-apply those > L' is wrong. After reversing down to the base, the upper patches whose context comes from lower features fail. The two checks must each start from the file's current content, which is what the prototype's two temp dirs do.
(b) One global L gives poor diagnostics. For a single hand-edited future.ML the prototype prints CONFLICT for all three features. Computing a level per file and then deriving each feature's verdict gives the same answer whenever the tree is consistent, and otherwise names the broken file and feature.
(c) The case where a file fits more than one level must be defined.

The replay took 0.5-0.8 s on the real chain's 41 files.

Experiment: I worked in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C3/ with GNU patch 2.7.6. Git was used read-only: archive, diff-tree, show, ls-tree, merge-base. The branch chain is linear, and local_type_abbrev, localized_record and local_datatype currently equal light_locale (7983d8a).

1. I re-ran the critic's real_chain.py and confirmed its results. Fresh tree, plan's rule: {fai: not-applied, light: not-applied, dev: CONFLICT}, caused by syntax_phases.ML. Fresh tree, replay: all not-applied.

2. my_exp.py, on the real chain with dev's base set to local_datatype:
   - Fresh tree: the plan's rule and the per-file rule both say dev CONFLICT; the replay gives L=0 (0.54 s). Apply dry-run per feature: dev False.
   - All three applied: the plan says light 'applied (covered)'; the replay gives L=3 (0.77 s). Unapply dry-run: light False.
   - All applied, then future.ML hand-edited: the plan says fai and light 'applied (covered)', dev applied (exit 0). The per-file rule says fai CONFLICT. The replay finds no consistent L.
   - All applied, then morphism.ML restored to its base: the plan says light covered (exit 0). The per-file rule says light CONFLICT. The replay finds no consistent L.

3. The tool's exact flags with stdin from /dev/null: dev's syntax_phases.ML forward dry-run fails ('1 out of 3 hunks FAILED') on the fresh file and passes after light is applied.

4. scenario_b2.py (the upper feature moves a line the lower one added): the plan says [not-applied, applied]; forward-applying the lower feature leaves the line twice. The replay gives L=2.

5. rename_exp.py (the lower feature creates new.ML, the upper renames it to moved.ML): the plan says [not-applied, applied]; forward-applying the lower feature recreates new.ML, after which the plan reads [applied, CONFLICT]. The replay gives L=2.

6. status_proto.py scenarios A, B, C and D reproduce as the critic reported.

Recommended fix: Replace plan:139-146 (the per-feature conjunction and the 'applied (covered)' rule) with a status computed by replaying each file's own stack.

For each file p patched by features above k, let t1 < ... < tm be the features that patch p, in chain order (each patch file is one feature-and-file pair, make-patches:154). The level of p is the j for which two checks both succeed, each on its own scratch copy of p's current content:
- reversing t_j, ..., t_1 in that order;
- forward-applying t_{j+1}, ..., t_m in that order.

If no j works, p is CONFLICT; report p and the first feature that fails on it. If more than one j works, that is also an error, reported as ambiguous.

From the file levels:
- A feature is applied if every one of its files has a level at or above that feature.
- A feature is not-applied if every one of its files has a level below that feature.
- Otherwise the feature is CONFLICT, and the report lists the files on each side (a half-applied feature).
- The applied features above k must form a prefix of the chain. If they do not, status reports the not-applied feature and the applied feature above it, exits 1, and apply and unapply refuse. The tool never forward-applies a feature beneath an applied one.

`apply`, `unapply` and `--dry-run` run that same per-file sequence: first on scratch copies, and for the real run they then write. This settles the re-evaluation question. Then:
- Remove 'applied (covered)' from plan:145, plan:265 and the test list at plan:255. The states stay 'built-in | applied | not-applied | CONFLICT' (plan:141), and the exit-code rule at plan:142 stands as written.
- Correct plan:211.
- Add the five reproduced scenarios to the decision 12 tests: fresh stacked tree, the covered case, a hand edit in a file only the lower feature patches, a lost change, and an upper feature that moves or renames a lower feature's addition.
- Leave the approved Appendix A and §7 rule 15 wording unchanged. In decision 3, add one sentence saying that the per-file raw reading that rule describes is why status replays each file's stack.

**Judge: partially_confirmed → author_decides_then_rereview.** Replace plan:139-146 and the "applied (covered)" label with a per-file replay.
- For each file p that features above k patch, let t1..tm be those features in chain order. The level of p is the j for which two checks both succeed: reversing t_j..t_1, and forward-applying t_{j+1}..t_m. Each check starts from p's current content on its own scratch copy, not one after the other on a single copy.
- A feature is applied, not-applied or half-applied (C7) according to the levels of its files.
- A file with no level is CONFLICT; report the file and the first feature that fails on it. A file with more than one level is an error, except under C1's rule for created files.
- The non-built-in applied features must form a prefix of the chain, with at most one half-applied feature directly above it. Otherwise status exits 1 and apply and unapply refuse. The tool never forward-applies a feature beneath an applied one.
- apply, unapply and --dry-run run the same per-file sequences: on scratch copies first, then for real. This also settles whether status is re-evaluated between steps.
Correct plan:211. Remove "covered" from plan:145, 255 and 265. Add the five reproduced scenarios to decision 12's tests.
Leave Appendix A and §7 rule 15 unchanged; no replacement wording is needed, because the approved sentence describes a raw per-file dry-run, which stays true. Add one sentence explaining that this raw reading is why status replays each file's stack.

### C4 [major] Each feature package encodes a one-directional CLI call in immutable hook text: relinking a lower feature drops everything above it, and policy fixes can never reach installed packages

Section: Decision 8 hooks and dependency (plan:197, 201-205); decision 3 `--feature` (plan:148-151); §8 link order (plan:318-320)  ·  merged from: conda-conda-5, user-U10

**Statement.** In decision 8, each feature package's post-link runs `apply --feature <F>`, which applies F and every feature below it. Its pre-unlink runs `unapply --feature <F>`, which reverses F and every feature above it (plan:201-205, 148-151). The two directions are asymmetric. So relinking a lower feature package on its own reverses everything above it and puts back only the lower feature itself. Two ordinary ways this happens: `conda install --force-reinstall isabelle-future-assign-interrupt`, and a build-number bump of a lower feature package. The base pin `==<v>=Isabelle2025_2_*` (tools/make-patches:201) accepts any build number of the base, so the upper packages are not relinked. Measured in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-conda/run4.clean (T5): feat-b stays installed, yet b.ML is unpatched and feat-b's created file is gone. The plan justifies the hook design by conda's link order (§8, plan:318-320). But conda links every package before it runs any post-link (conda/core/link.py:949-967), and it runs all pre-unlinks before any unlink (:938-947). So every hook already sees the whole features.d. Order is not the problem; the direction written into the flags is. Second, each package's hook text spells out the CLI flags, the exit policy and where messages go. Published packages are immutable (PACKAGING_DESIGN.md:946-952; RELEASE_CHECKLIST.md:36-41). Every later fix to that policy, such as .messages.txt (C18), the exit code (C2), Windows (C15) or tree discovery (C14), therefore needs every feature package rebuilt, and already-installed packages keep the old hooks for good. Third, the dependency `isabelle-patch-control >=1.0` (plan:197) has no upper bound, so a 2.x that renames `apply` or `--feature` breaks every published hook.

**Editor.** Correct; I verified the ordering in link.py. This is decision 8's central elegance defect. The invariant 'tree = installed features' is enforced by choreographing per-package directional commands, when it should be a single function of the installed set. user-U10's hook entry point and conda-5's reconcile command are the same fix seen from two sides.

**Relaxation proposed by the editor.** Every hook becomes one identical, generated line that calls a stable entry point owned by the tool, for example `isabelle-patch-control conda-hook post-link|pre-unlink <feature>`. The entry point runs one idempotent reconcile. In a post-link, the target is the whole chain found in features.d. In a pre-unlink, the target is the chain below this package's feature. The entry point finds the tree from $PREFIX, writes to .messages.txt, and owns the exit policy, which is always 0. `--feature` stays for manual use. The tool dependency becomes `isabelle-patch-control >=1.0,<2`. Policy fixes then ship with the tool, and the `isabelle` package's own hooks (C1) call the same entry point.

**Defender: confirmed** (needs owner: False).

I tried to refute C4 and could not. All three parts hold. One wording in the challenge goes too far, and one part of the editor's relaxation is wrong. Both are noted below.

PART 1: the hook commands point in opposite directions. Confirmed from the conda source and by measurement.
- What the plan says. The post-link hook runs `apply --feature <F>` and the pre-unlink hook runs `unapply --feature <F>` (plan:201-203). `apply --feature F` applies F and every feature below it (plan:148). `unapply --feature F` reverses F and every feature above it (plan:150; also plan:116-117).
- What conda relinks. conda relinks only the packages that changed: unlink_precs = previous - final and link_precs = final - previous (conda/core/solve.py:1417-1418). `--force-reinstall` adds only the specs the user named (solve.py:1426-1432). The base pin `==<v>=Isabelle2025_2_*` (tools/make-patches:201; owner ruling 27, migration plan:106-108 and 220-222) accepts any build number. So a build-number bump of a lower feature package relinks that package alone.
- The resulting transaction. The pre-unlink of the old lower package reverses everything above it. The post-link of the new package then applies only the chain up to itself. conda exits 0.
- My own measurement (plan.out). The toy channel has a feat-a with builds T_0 and T_1, and a feat-b pinned to `feat-a ==1=T_*`. Under the plan's hooks, three cases end the same way: S2 `--force-reinstall feat-a`, S3 `install feat-a=1=T_1`, and S8 `conda update --all`, where the solver output was only `feat-a 1-T_0 --> 1-T_1`. In all three, b.ML ends unpatched and feat-b's newly created file is gone, while feat-b is still listed as installed.
- Worse in the real chain. For the built-in feature `isabelle-expose-foreign`, the pre-unlink reverses every feature above it. The post-link then applies nothing, because built-in features are never applied (plan:147, 150, 165). So a rebuilt `isabelle-expose-foreign` silently strips every installed feature.
- No warning anywhere. The plan's only recovery note covers reinstalling `isabelle` (plan:210-211). Neither the tests (plan:253-256) nor the acceptance checks (plan:290-298) cover these cases.
- The plan's justification misreads conda. It says decision 8 depends on link order (plan:318-320). In fact conda runs every pre-unlink before any unlink (conda/core/link.py:938-947, with the unlink block at :949-955). It runs post-links only after every link and every entry point (:957-967). So every hook sees the whole features.d: the pre-transaction set during pre-unlink, the post-transaction set during post-link.
- Even the plan's own flags do not depend on order. I ran the post-link commands in reverse, `apply --feature b` and then `apply --feature a`, and both features ended up applied. What the plan really depends on, without saying so, is that every package above a relinked one is relinked too. conda does not guarantee that.

PART 2: hook policy is frozen into each package's hook text. Confirmed in substance; one claim is overstated.
- What sits in each package's hook. The hook text fixes the CLI flags, the tree location (`--isabelle-bin "$PREFIX/isa/bin/isabelle"`), the exit-code policy (non-zero on CONFLICT, plan:206-207), the printed message (plan:213) and the Windows path through cygwin bash (plan:203-204).
- Why a fix is expensive. Published filenames are permanent (RELEASE_CHECKLIST.md:36), so any change needs a build-number bump (PACKAGING_DESIGN.md:946-952), i.e. N rebuilt packages.
- The overstatement. "Keep the old hooks for good" is too strong: updating to a rebuilt build does replace the hooks. But the old pre-unlink text still runs once during that update.
- An irony the challenge does not mention. Under the plan's hooks, shipping a hook fix to a lower package through a build bump is itself an instance of the bug in Part 1. Unless every package in the chain is rebuilt and updated together, the update strips the features above.

PART 3: the tool dependency has no upper bound. Confirmed.
- The plan declares `isabelle-patch-control >=1.0` with no upper bound (plan:197).
- A post-link failure raises LinkError, so conda rolls the install back (link.py:1675).
- A pre-unlink failure only logs "consider notifying the package maintainer" and returns False (link.py:1676-1682). The return value is ignored (:942-947).
- So a 2.x release that renames a subcommand would make removals silently leave patches applied. The feature directory is deleted along with the package, so `status` can no longer even see those patches.

Assessment of the editor's relaxation.
- Accept: one identical generated hook line that calls a stable entry point owned by the tool.
- Accept: in post-link, the target is the whole chain found in features.d. This is just `apply` with no `--feature`.
- Accept: the bound `<2`.
- Correct: the pre-unlink as "one idempotent reconcile" to the chain below F. A reconcile may apply as well as reverse, and that is the wrong shape for a pre-unlink:
  - (i) It depends on order. If the pre-unlinks run bottom-up, b's reconcile re-applies a's old patches. I measured this directly with the toy tool. It is safe today only because conda sorts unlinks top-down (solve.py:1450-1452). That is exactly the kind of order dependence the challenge says should not matter.
  - (ii) It applies features during a removal. S10: the user had unapplied everything, then ran `conda remove feat-b`, and that applied a.
  - The plan's existing pre-unlink, "reverse F and everything above it", never applies. In both experiments it was order-independent. So only the post-link half of decision 8 is wrong.
- Not C4's call: "exit policy always 0". It overrides the plan's pending proposal (plan:206-207; plan §7 question 1 at :302). The entry point should own whatever exit policy the owner picks. That policy matters only for post-link, because conda ignores pre-unlink exit codes.
- Outside C4: having the `isabelle` package's own hooks call the same entry point. That is C1's question, and that package has no requirements (isabelle-packaging-ci conda/recipe.yaml:235-237).
- No conflict with owner rulings. The fix leaves the build-string pin (ruling 27) alone. It keeps chain order derived from dependencies, with no `after` (plan §0 item 8). The hook design itself is still a proposal awaiting the owner (plan:201).

Experiment: All experiments ran in the scratch directory /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C4/. They used the local conda 25.11.1, fully isolated: HOME, the package cache, the environment directory and TMPDIR were redirected, and environments were not registered.

Setup.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C4/mkchan.py builds a toy channel per hook design:
  - `isa`: stands in for the `isabelle` package.
  - `ftool`: a toy tool with the plan's status semantics.
  - feat-a: builds T_0 and T_1, identical patches.
  - feat-b: pinned `feat-a ==1=T_*`; also creates a new file.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C4/run.sh runs nine scenarios against each design.
- The three designs:
  - "plan": the plan's hooks, `apply --feature F` / `unapply --feature F`.
  - "min": post-link `apply` with no `--feature`; pre-unlink `unapply --feature F`.
  - "recon": the editor's reconcile, as `conda-hook post-link|pre-unlink F`.

Results (outputs in plan.out, min.out and recon.out in the same directory).
- "plan" loses feat-b in three scenarios: S2 `--force-reinstall feat-a`, S3 `install feat-a=1=T_1`, and S8 `update --all`. The solver showed only `feat-a 1-T_0 --> 1-T_1`, and the final tree was `b.ML=[b1 b2 b3] new.ML=absent` while feat-b was still installed. conda exited 0 every time.
- "min" and "recon" both keep a and b applied in S2, S3 and S8.
- All three designs agree on the other cases: a fresh install (S1), adding b later (S6), force-reinstalling b (S7), removing b (S4), removing isa (S5) and `remove --force feat-a` (S9).
- Order test. Running the pre-unlinks bottom-up (a, then b) leaves a re-applied under "recon" and nothing applied under "min".
- Reverse post-link order under the plan's flags (`apply --feature b`, then `--feature a`) ends with both features applied. So the plan's §8 claim that decision 8 relies on order is beside the point.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C4/s10.sh: a manual `unapply` of everything followed by `conda remove feat-b` applies a under "recon". Under "min" nothing changes.

Recommended fix: Decision 8 (plan:197, 201-205):
(1) The post-link should run `apply` over the whole chain found in features.d, with no `--feature`. The pre-unlink should keep "reverse this feature and everything above it", which is today's `unapply --feature F`. It must stay a pure reverse and never apply, so do not turn it into a reconcile to the chain below F.
(2) Every feature package should carry the same generated one-line hook that calls an entry point owned by the tool, for example `isabelle-patch-control conda-hook post-link|pre-unlink <feature>`. That entry point takes over what the hook text holds today: the flags, finding the tree from $PREFIX, where messages go, the Windows path, and the post-link exit policy, whichever one the owner chooses under §7 question 1. It must not be hard-coded to "always 0". `--feature` stays for manual use.
(3) Change the dependency to `isabelle-patch-control >=1.0,<2`, and state that the `conda-hook` contract is part of the 1.x compatibility promise.

Rewrite the justification in §8 (plan:318-320). The hooks rely on conda running every pre-unlink before any unlink and every post-link after all links (conda/core/link.py:938-967), not on link order. Also state that conda relinks only changed or named packages (solve.py:1417-1432).

Add three scenarios to decision 12's tests and §6's acceptance checks:
- `--force-reinstall` of a lower feature package;
- a build-number bump of a lower feature package, including the built-in `isabelle-expose-foreign`;
- `conda update --all`.
After each, the tree must equal the full installed chain.

**Judge: confirmed → author_decides_then_rereview.** Decision 8:
- post-link runs the idempotent whole-chain apply;
- pre-unlink keeps "reverse F and everything above it" and never applies anything;
- every feature package carries one identical generated line calling a tool-owned entry point, e.g. `isabelle-patch-control conda-hook post-link|pre-unlink <feature>`. The entry point owns the flags, finding the tree from $PREFIX, the message channel, and the exit policy the owner chooses (C2).
Change the dependency to `isabelle-patch-control >=1.0,<2`, and make the conda-hook contract part of the 1.x compatibility promise.
Rewrite §8's justification (plan:318-320). conda runs every pre-unlink before any unlink and every post-link after all links (link.py:938-967), and it relinks only changed or named packages (solve.py:1417-1432).
Add tests for three cases: a force-reinstall of a lower feature package; a build-number bump of a lower package, including isabelle-expose-foreign; and `conda update --all`.

### C5 [major] The conda metadata does not tie a feature chain to its Isabelle release line

Section: Decision 8 dependencies (plan:197-198); decision 4 (plan:160-162); decision 11 item 1 (plan:245-247)  ·  merged from: conda-conda-6, consistency-C8, landing-L6, user-U4, design-D5

**Statement.** Feature packages depend on `isabelle` of any version (plan:197-198). The chain head, expose_foreign, is based on pristine and so has no base pin at all (tools/make-patches:200-201 writes `base_pin: none`). Ruling 27 makes the build string the only thing that tells release lines apart, because versions are numbered per line (ISABELLE_GIT_MIGRATION_PLAN.md:106-108, :219-221). Yet decision 11's weak constraint is `isabelle-<feature> ==<version>`, with no build-string part (plan:245-246). So once a later line exists, the solver can pair an Isabelle 2026 `isabelle` with the 2025-2 chain, since it prefers the newest `isabelle`. The 2026 build's constraint `==1` is then satisfied by a 2025-2 package. An upgrade of `isabelle` across lines also leaves the old-line features in place without relinking them, so none of their hooks run. Toy solver test: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-conda/xline.py and xline.out. With the plan's constraints, `conda create isa=2.0 feat-x` resolves to the line-1 build. Every consumer package on the channel bounds `isabelle >=2025.2,<2025.3`, and Isabelle_RPC/conda/recipe.yaml:189-192 gives the reason: an unbounded dependency 'would let conda pair this with a future Isabelle'. D4 item 9 proposed `isabelle 2025.2.*` (LIGHT_LOCALE_HANDOFF.md:1979). Decision 4 claims that a mismatched built-in version 'should not occur' because of run_constrained (plan:160-162). For the only published build that has no basis: isabelle-2025.2-0 has empty `depends` and no `constrains` (~/miniconda3/pkgs/isabelle-2025.2-0/info/index.json, checked). So a future isabelle-expose-foreign 2 will be solved onto it and hit exit 3 in the post-link. The spelling that decision 11 leaves open (plan:246-247) is settled: rattler-build recipes write `run_constraints`. The cached anyio package shows `run_constraints:` at info/recipe/recipe.yaml:33, which becomes `constrains` in info/index.json.

**Editor.** Correct. Migration decision 3 says correctness rests on the tool's checks, not on the solver (ISABELLE_GIT_MIGRATION_PLAN.md:217-218). That makes the tool-side check in C6 essential. It does not excuse leaving the solver free to build pairs that are wrong by construction. landing-L6 suggests that a later version of a built-in feature should require an `isabelle` build that carries the built-in manifest. That is reasonable, but it is CI-plan work, so it belongs in the list of requirements under decision 11.

**Defender: confirmed** (needs owner: False).

I tried to refute C5 and could not. Every factual claim checks out, and my own toy channels reproduce the failure without the build-number difference the critic's test relied on.

1. The plan text, checked claim by claim.
- Decision 8 gives every feature package the dependency `isabelle` with no version: "isabelle（任意版本；内置清单与 run_constrained 管匹配）" (plan:197-198).
- The chain head has no pin at all. make-patches writes `base_pin: none` when the base is pristine (tools/make-patches:200-201).
- That leaves the build string as the only conda-level marker of a release line:
  - The build-string prefix is derived from `<R>` (make-patches:191).
  - Ruling 27 says the build string tells release lines apart (ISABELLE_GIT_MIGRATION_PLAN.md:106-108).
  - Migration decision 3 says outright that same-name, same-version packages of different lines are told apart by it ("不同发行版线的同名同版本包由它区分", :219-221).
- Decision 11's weak constraint is `isabelle-<feature> ==<version>`, with no build-string part (plan:245-246). A later line's `==1` is therefore satisfied by the 2025-2 line's version 1.
- Decision 4 claims the version-mismatch combination "不该出现" because the run_constrained constraint steers the solver away (plan:160-162). That is false in the two cases below.

2. The published build and the consumer recipes.
- ~/miniconda3/pkgs/isabelle-2025.2-0/info/index.json has `depends: []` and no `constrains` key. Its repodata_record.json has `constrains: []` and comes from https://conda.qiyuan.me.
- Its tree already carries expose_foreign: `hidden_structures = ["Signal"]` at isa/src/Pure/ML/ml_name_space.ML:67.
- The older build isabelle-2025.2-89701cf1768e_0 came from a local file channel (file:///home/qiyuan/ci-work/channel), so it was never published.
- Both consumer recipes bound `isabelle >=2025.2,<2025.3` and give the reason:
  - Isabelle_RPC/conda/recipe.yaml:189-192: an unbounded dependency "would let conda pair this with a future Isabelle".
  - Semantic_Embedding/conda/recipe.yaml:314-318: same bound, same reason.
- D4 item (9), which proposes the dependency `isabelle 2025.2.*`, is at ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979. The challenge cites the root-level file of that name, which has only 3 lines.
- The plan promises to lay out every D4 item for the owner (plan:36-37). Yet §7 item 6 (plan:307-309) never mentions item (9), and decision 8 silently does the opposite.

3. The spelling question is settled.
- The cached anyio package's recipe has `schema_version: 1` (info/recipe/recipe.yaml:2) and `run_constraints:` at :33.
- Its index.json then has `constrains: ['trio >=0.32.0', ...]`.
- The isabelle recipe is the same rattler-build format (isabelle-packaging-ci/conda/recipe.yaml:1).

4. Solver experiments (conda 25.11.1, libmamba solver; details in the experiment field).
- The default command goes wrong. While the next line has expose_foreign 1 and future_assign_interrupt 1 but no light_locale yet, `conda create isabelle-light-locale` resolves to isabelle-2026-0 plus the entire 2025-2 chain.
- With equal build numbers, `conda create isabelle=2026 isabelle-expose-foreign` picks the 2025-2 build even though a 2026 build exists.
- Upgrading `isabelle` across lines skips every feature hook:
  - In a real environment, `conda install isabelle=2026` runs only isabelle's own two hooks, and no feature hook. conda-meta still lists the 2025-2 features.
  - Files that the old line's patches created stay in the new isa/ tree, and the command exits 0.
  - On a legacy environment, `conda update --all` does the same cross-line upgrade without being asked.
- The legacy build is a separate hole. In an environment holding isabelle-2025.2-0, `conda install isabelle-light-locale=2` keeps that build and installs expose_foreign 2. Under decision 4 that is a version mismatch, and the post-link exits 3.

5. Rollback does not undo the damage, which makes this worse than the challenge says.
- conda's rollback only calls `action.reverse()` on file actions (conda/core/link.py:1039-1045 and :1129-1160). It re-runs no hook.
- The post-links after the failing one still run (link.py:964-967).
- The pre-unlink hooks of the replaced packages have already run, between link.py:928 and :947.
- Measured result: conda-meta lists version 1 of all three features again, but the modelled tree holds future-assign-interrupt 2 and light-locale 2, and expose-foreign is not recorded as applied at all.
- So "the tool's check is the last line" (plan:162) fires inside a transaction whose rollback leaves the tree out of step with conda-meta. Decision 8's reason for exiting non-zero, that rolling back beats installing a package that cannot be applied (plan:206-207), assumes a clean rollback. That belongs to another challenge, but it means the legacy case is not harmless.

6. What fixes what, measured.
- A release-series bound on `isabelle` in every feature package fixes every cross-line case, in both directions. That includes the later line's chain head landing on the legacy build, which happens once the 2026 build is rebuilt and wins the tie-break.
- A build-string-qualified constraint on the `isabelle` side alone fixes the cases that involve new builds. It cannot protect the legacy build, which has no constraint and can never get one: the recipe says never to overwrite a published file (recipe.yaml:42).
- Neither fixes the legacy case with a later expose_foreign.

7. No owner ruling stands in the way of the series bound.
- Ruling 14 is about pinning the base package exactly.
- Ruling 21 (migration:87-90) says a feature package pins its base feature's version, not isabelle's version or build number. A bound on the release series does not identify which patches a build carries, so it does not conflict.
- Migration decision 3 (:217-218) says correctness rests on the tool's check, not on the solver. That does not forbid metadata that keeps the solver off pairs that are wrong by construction. Every consumer package already does exactly this.

8. The editor's relaxation, on its merits.
- I agree that the core is correct.
- I disagree that landing-L6 is work for the CI plan. CI cannot change the legacy build's metadata (recipe.yaml:42).
- A repodata patch on the channel does not help either. I measured that the patched `constrains` reaches a fresh `create` but not an environment that already has the build installed.
- The only place a solver-level guard could live is the later expose_foreign package's own `depends`, written as a lower bound on the `isabelle` build. That runs against the letter of ruling 21 ("不是 isabelle 的版本或 build 号", migration:90). So whether to add it is for the owner to decide, not something to quietly hand to the CI plan.

Experiment: All conda state was isolated under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C5/: HOME, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS all pointed there, with `--override-channels` and a file:// channel. The conda used was /home/qiyuan/miniconda3/bin/conda 25.11.1 with the libmamba solver. Nothing outside the scratch directory was written.

The toy channel is built by /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C5/mkchan.py. It holds:
- three `isabelle` builds: 2025.2 build 0 (legacy, no constraints), 2025.2 build 1 (expose_foreign 1 and future_assign_interrupt 1 built in, with constraints), and 2026 build 0 (both built in);
- the 2025-2 chain: expose-foreign 1, future-assign-interrupt 1, light-locale 1;
- the 2026 chain: expose-foreign 1 and future-assign-interrupt 1, with light-locale not yet released;
- optionally, version 2 of the 2025-2 chain plus 2025.2 build 2.

It has four variants:
- plan: as written;
- f1: the `isabelle`-side constraint gains `=<line>_*`;
- f2: every feature package depends on the `isabelle` series of its line;
- f12: both.
Every package has post-link and pre-unlink hooks that log to $PREFIX/hooks.log.

run.sh, results in run.out:
- Plan variant:
  - `conda create isabelle-light-locale` gives isabelle-2026-0 plus the 2025-2 chain.
  - `conda create isabelle=2026 isabelle-expose-foreign` gives isabelle-expose-foreign-1-Isabelle2025_2_0. Build numbers were equal.
  - A real `conda install isabelle=2026` on an environment with 2025.2 build 1 and light runs only the pre-unlink of isabelle-2025.2-1 and the post-link of isabelle-2026-0. The three features stay installed.
  - On the legacy environment, `conda install isabelle-light-locale=2` keeps isabelle-2025.2-0 and installs expose-foreign 2.
  - On the legacy environment, `conda update --all` gives isabelle-2026-0 with the features unchanged.
- f1, f2 and f12: the fresh create picks isabelle-2025.2-1. Upgrading to 2026 is refused while light is installed. `update --all` moves to 2025.2 build 2 together with the version-2 chain. The legacy environment's `install light-locale=2` is unchanged in all three.

run3.sh, results in run3.out: once the 2026 expose-foreign is rebuilt (build string Isabelle2026_1), `conda create isabelle=2025.2=0 isabelle-expose-foreign` picks the 2026 build under both plan and f1. Under f2 it picks the 2025-2 build.

run2.sh, results in run2.out (S5): a repodata hotfix that adds `constrains` to isabelle-2025.2-0 does not change the installed environment's solution (S5b is the same as S5a). It does make a fresh create unsatisfiable (S5c).

run4.sh, results in run4.out: the hooks model `apply`/`unapply` on a state file, and expose-foreign 2 exits 3 on the legacy build. `conda install isabelle-light-locale=2` exits 1 with "Rolling back transaction". conda-meta then lists version 1 of all three features again, but the state file holds "future-assign-interrupt 2" and "light-locale 2", and expose-foreign is gone.

run5.sh, results in run5.out: after `conda install isabelle=2026`, which exits 0, the files that the 2025-2 features' post-links created under isa/ remain beside the 2026 isa/etc/ISABELLE_ID.

Read-only checks:
- index.json and repodata_record.json of pkgs/isabelle-2025.2-0, which have no depends and no constrains;
- pkgs/anyio-4.14.*/info/recipe/recipe.yaml:33 `run_constraints:`, which becomes index.json `constrains`.

Recommended fix: 1. Decision 8, dependencies (plan:197-198). Replace "isabelle（任意版本）" with a release-series bound in every feature package. For Isabelle2025-2 that is `isabelle >=2025.2,<2025.3`, the spelling the consumer recipes use (Isabelle_RPC/conda/recipe.yaml:192). The recipe template should derive it from the provenance field `build_string_prefix`, using the same Isabelle2025-2 → 2025.2 rule as isabelle-packaging-ci/conda/recipe.yaml:18. That way the line is stated once and make-patches' output format stays unchanged, as plan:332 requires. Put the bound in every package, not only the chain head, so that no package's line depends on reaching the head through the chain.

2. Decision 11 item 1 (plan:245-247). Write the constraint as `isabelle-<feature> ==<version>=<build_string_prefix>_*`, the same form as the base pin in ruling 27 (migration:221). Settle the spelling as rattler-build `run_constraints`.

3. Decision 4 (plan:160-162). Drop "这种组合不该出现". State plainly that isabelle-2025.2-0 has no constrains and can never get one: published files are immutable (recipe.yaml:42), and a repodata patch on the channel does not reach environments that already have it installed. So on that build, a later expose_foreign version reaches the tool's exit-3 check, and conda's rollback does not restore the tree.

4. Add to §7 one question for the owner: may a later version of a built-in feature carry a lower bound on the `isabelle` build? This touches the wording of ruling 21 (migration:90). The alternative is to accept the residual for the legacy build. This is not work for the CI plan.

5. In §7 item 6 (plan:307-309), name D4 item (9) and say it is answered by fix 1.

**Judge: confirmed → owner_decides.** Every feature package, not only the head of the chain, depends on `isabelle >=2025.2,<2025.3`, derived from build_string_prefix. Use the spelling of Isabelle_RPC/conda/recipe.yaml:192.
Decision 11's constraint becomes `isabelle-<feature> ==<version>=<build_string_prefix>_*`, written as rattler-build `run_constraints` (anyio's cached recipe.yaml:33 settles that spelling).
Delete "这种组合不该出现" from decision 4. State instead that isabelle-2025.2-0 has no constrains and can never get one, so a later expose_foreign reaches the tool's exit-3 check on that build.
List D4 item 9 as answered by the series bound.
Put to the owner whether a later version of a built-in feature may carry a lower bound on the isabelle build, which touches ruling 21's wording, or whether the residue is accepted. This is not CI-plan work, because CI cannot change the legacy build.

### C6 [major] The tool links the chain by feature names only and never checks base_tag or the release line

Section: Decision 3 chain derivation (plan:133-136); decision 4 version check (plan:160-162)  ·  merged from: design-D5, consistency-C9, user-U5, consistency-C8, user-U4

**Statement.** The tool builds the chain from the second segment of each base_tag, which is just the base feature's name (plan:133-135). Its only version check compares an installed package with the built-in manifest (plan:160-162). Two things are never checked. First, that a feature's base_tag equals the release_tag of the base feature directory actually present. Second, that the feature's release `<R>` (provenance field `feature: <R>/<f>`, tools/make-patches:195) equals the tree's release. Today's tool refuses a version it has no patches for (my_better_isabelle_prover/cli.py:25-32). Without conda's pins, which is the case with --features-dir, pixi, non-conda installs and the (b2) gate, a patch made against light_locale/1 gets applied on light_locale/2. GNU patch under -F0 still accepts offsets (ISABELLE_GIT_MIGRATION_PLAN.md:448-449), so it can read applied and produce a tree that no git commit ever had. The walk 'from pristine' (plan:134) also reaches nothing when the bottom features are built in and their package directories are absent. That is the normal state after conda removes dependency-only packages (C20).

**Editor.** Correct. The provenance file already carries the exact tags (tools/make-patches:194-205), so the check costs nothing. Of all the fixes in this review, this one most directly turns 'people must remember to pin correctly' into a rule that cannot be broken.

**Relaxation proposed by the editor.** Replace both name chaining and decision 4's special mismatch check with one rule. The tree's own bottom is the `<R>/pristine/*` tag or the release tags listed in the built-in manifest. Every feature's base_tag must equal exactly the release_tag of the entry directly below it, and every tag's `<R>` must equal the tree's release. Anything else is exit 3, naming both tags. Each manifest line then needs only `<release_tag> <commit>`, because the feature name is the tag's second segment.

**Defender: partially_confirmed** (needs owner: False).

WHAT IS CONFIRMED (the core).
1. The tool links the chain only by feature names. plan:133 says "base_tag 的第二段是基 feature 的名字", and plan:134-135 walks "谁以我为基" from pristine. The only errors are a fork, or a base that is missing and is neither built-in nor pristine. Nothing compares a feature's base_tag with the release_tag of the base directory that is actually present. The data is already there: make-patches writes feature, release_tag and base_tag (tools/make-patches:195-198), and plan:132 says the tool already reads all three.
2. The only exact-tag check is the built-in one: plan:160-162 compares an installed package with the built-in manifest. It fires only "若环境里也装了该 feature 的 feature 包".
3. Nothing compares a feature's release <R> with the tree's release. Today's tool refuses an Isabelle version it has no patches for (my_better_isabelle_prover/cli.py:25-32). The plan drops that refusal and puts nothing in its place. The only remaining use of `isabelle version` is picking the bundled Isabelle2024 sets (plan:221).
4. The plan describes the tool as the backstop that these missing checks would make it. plan:162 calls it "最后一道". Migration plan:218 says "正确性不靠它，靠补丁工具的状态检查". Owner ruling 14 (migration plan:73) is the exact pin. plan:124-125 explicitly supports `--features-dir` for non-conda installs, where no solver enforces that pin. Feature packages also depend on `isabelle` of any version (plan:197).
5. GNU patch with -F0 accepts offsets (migration plan:448-449). My experiments show this produces silent wrong trees: see the experiment field. The mixed case reaches exit 0 with every feature reading applied, and the hunk lands at the wrong place. The built-in boundary with the directory absent also passes silently. The tag rule refuses both.
6. Elegance: the plan checks one link of the chain (the built-in one) by exact tag and every other link by name. One uniform rule is simpler, and it makes the exact pin hold in every install path, not only where conda's solver runs.

WHAT IS OVERSTATED OR REFUTED.
a. Pixi does not remove the pins. It solves the same `depends`, so it is not an exposure. This comes from my own knowledge; pixi is not installed on this machine, so I could not test it.
b. The (b2) gate does not miss the error. It compares copy A with copy B, a git-derived copy (migration plan:392-395), so a mismatched features.d makes A differ from B. The new rule only gives an earlier and clearer message there.
c. In normal conda use, the base packages are always installed. The base pin (plan:197-198) makes every lower feature package a run dependency of the one above it. So "built-in package directories absent" is not "the normal state after conda removes dependency-only packages". A conda environment gets a mismatched or incomplete set only through `--no-deps` (conda/cli/helpers.py:355-361) or `--force-remove` (conda/cli/main_remove.py:88-95).
d. The worry that the walk "from pristine reaches nothing" is a wording gap, not a design hole. plan:135 already accepts a built-in base, and plan:157 lists the manifest "按链序". The text just never says the walk continues from the top manifest entry.
e. "A tree that no git commit ever had" is only sometimes literally true. In my first toy variant the hunk landed in the right place, and the result matched an untagged intermediate merge commit that does not build. The accurate claim is "a combination that no release tag, gate or tested record covers". My second variant does produce a tree that matches no commit at all.
f. Cross-release mixing inside conda is already caught at the built-in boundary when k>=1, because the manifest tags include <R> (plan:157,160). The real gap is k=0 trees and non-conda installs. In a k=0 tree, release-agnostic patches really do apply across releases. Isabelle2025-2's future_assign_interrupt and expose_map_syn patches dry-run cleanly on Isabelle2024 files. Isabelle2025-2's expose_foreign patch fails there, which would stop that particular chain with a CONFLICT message (misleading, but not silent).

ON THE EDITOR'S RELAXATION (adopt it, with four precisions).
(1) State the dedupe rule explicitly: a feature directory whose release_tag equals a manifest entry *is* that built-in entry. Any other directory for a built-in feature then either forks or has no matching base, so it hits exit 3. With that sentence, plan:160-162 can be deleted.
(2) Once every link is an exact tag match, all tags share the bottom's <R>. So the <R> check is needed only at the bottom. When k>=1 nothing extra is needed: the manifest is the tree's own record. When k=0 the first feature's base_tag must be `<R>/pristine/<id>` with <R> equal to `isabelle version`. Caveat: `isabelle version` prints the tree's ISABELLE_IDENTIFIER (contrib/Isabelle2025-2/lib/Tools/version:65, lib/scripts/getsettings:71-76). That is `Isabelle2025-2` for the published build (pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_IDENTIFIER). In a private tree it is the directory name (migration plan:247), and in a bare hg checkout it is "Isabelle" (build.yml:223-227). So for k=0, refuse when the name is not a release name. Checking <R> on "every tag" is harmless but redundant.
(3) Manifest lines `<release_tag> <commit>`, and LEGACY_BUILDS entries as bare release tags, remove a redundant field that could disagree with the tag. Good.
(4) Decision 9 has to change anyway. plan:219-220 gives all three bundled Isabelle2024 directories `base_tag: Isabelle2024/pristine/none` and `release_tag: none (bundled)`. That already breaks the plan's own fork rule (plan:135), and it cannot link by tag. The bundled provenance files need chained tags such as `Isabelle2024/<f>/bundled`, each base_tag naming the one before. The relaxation exposes this existing inconsistency; it does not create it.

The directory interface (plan:169-171) rightly stays free of checks; the CI tree-hash assertion covers it there.

One limit, not tested: the rule proves that the feature directories match the tree's base. It does not prove which version is actually applied in the tree, because status still comes from patch dry-runs plus the covered rule (plan:143-146).

Experiment: All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C6/.

(1) Cross-release test, in xrel/. I copied the target files of every tool patch out of contrib/Isabelle2024 and contrib/Isabelle2025-2 and ran `patch --dry-run -p1 -F0` against the copies. On the Isabelle2024 copies, the Isabelle2025-2 patches future_assign_interrupt/future.ML.patch ("Hunk #1 succeeded at 427") and expose_map_syn/sign.ML.patch ("succeeded at 12") apply cleanly; their hunk bodies are byte-identical to the Isabelle2024 patches. expose_foreign, register_thy and show_types_nv fail.

(2) Toy release line, in toy/build.sh and toy/proto.py; the run is in toy/run2. The repo has R/pristine/0 → R/light_locale/1 → R/local_type_abbrev/1, plus R/light_locale/2 (renames foo to foo' and inserts a copy of local_type_abbrev's context lines) and an honest R/local_type_abbrev/2 (merges light_locale/2 and follows foo'). I wrote make-patches-style feature directories: one `git diff-tree -p` block per file, plus a provenance file. proto.py implements the plan's name-based chain (plan:133-135), status with covered (plan:139-146) and apply (plan:147), next to the editor's tag rule.
- Mixed directories (light_locale/2 + local_type_abbrev/1), name rule: both apply with rc=0. local_type_abbrev's hunk "succeeded at 25 (offset -1 lines)", which is the WRONG copy of the context (it should be line 47). It calls the now-undefined `foo`. Status: light_locale 'applied (covered)', local_type_abbrev 'applied'. The tree hash matches NO commit.
- Mixed directories, tag rule: "exit 3: local_type_abbrev sits on R/light_locale/1, which is not R/light_locale/2".
- Honest directories, both rules: the tree equals the R/local_type_abbrev/2 commit.
- An earlier variant with the duplicated context far away applied at the right place, and the result matched an untagged intermediate merge commit that still calls `foo`.

(3) Built-in boundary, in toy/builtin.py. The user tree is the light_locale/1 tree, with the manifest built-in [R/light_locale/1]. features.d holds only local_type_abbrev/2, which sits on light_locale/2, and has no light_locale directory, so plan:160 does not fire. Name rule: the hunk applies at "offset -18", status 'applied', and the tree uses foo' without defining it. Tag rule: "exit 3: local_type_abbrev sits on R/light_locale/2, which is not R/light_locale/1".

(4) Source reads. conda's `--no-deps` is at conda/cli/helpers.py:355-361 and `--force-remove` at conda/cli/main_remove.py:88-95. `isabelle version` prints ISABELLE_NAME (lib/Tools/version:65, getsettings:71-76). pixi and rattler-build are not installed on this machine.

Recommended fix: In decision 3, replace the name-based chain derivation (plan:133-135). In decision 4, delete the special mismatch check (plan:160-162). Put one rule in their place, under status, apply and unapply:

"The chain is linked by exact tags. Its bottom is the tree's own record. For a k>=1 tree that is the release tags in etc/ISABELLE_BUILT_IN_FEATURES (or the LEGACY_BUILDS entry), in chain order. Otherwise it is a `<R>/pristine/<id>` tag, where <R> equals `isabelle version` (refuse if that is not a release name). Every feature directory's base_tag must equal the release_tag of the entry directly below it. A directory whose release_tag is a manifest entry is that built-in entry: only its provenance file is read. A fork, a directory whose base_tag matches no entry, or a different <R> is exit 3, naming both tags."

Change the manifest and LEGACY_BUILDS lines to `<release_tag> <commit>`; the feature name is the tag's second segment. Give decision 9's three bundled Isabelle2024 provenance files chained tags, e.g. `release_tag: Isabelle2024/<f>/bundled`, each base_tag naming the previous one's release_tag. This also removes their existing clash with plan:135's fork rule. Leave the directory interface (plan:169-171) without checks.

Add three pytest cases to decision 12: a mixed base version, a built-in boundary with the built-in directory absent, and a cross-release <R>.

Finally, correct the plan's own wording: the walk starts at the top built-in entry, not literally at pristine.

**Judge: partially_confirmed → author_decides_then_rereview.** Replace name chaining (plan:133-135) and decision 4's special mismatch check (plan:160-162) with one rule: the chain is linked by exact tags.
- Its bottom is the tree's own record: the manifest's release tags, the LEGACY_BUILDS entry, or `<R>/pristine/<id>`, where <R> comes from etc/ISABELLE_IDENTIFIER. Refuse a name that is not a release name.
- Every feature directory's base_tag must equal the release_tag of the entry directly below it.
- A directory whose release_tag is a manifest entry is that built-in entry.
- A fork, an unmatched base_tag or a different <R> is exit 3, naming both tags.
Manifest and LEGACY_BUILDS lines become `<release_tag> <commit>`. Say that the walk starts at the top built-in entry, not at pristine.
Add tests for a mixed base version, a built-in boundary whose directory is absent, and a cross-release mix.
Two corrections to the challenge: pixi solves the same `depends`, and (b2) would catch a mismatch. Also, base packages are not pruned in normal use. Chained bundled tags for Isabelle2024 are needed only if the owner keeps the bundled sets (C12).

### C7 [major] Apply is not all-or-nothing, the claim that a failure leaves no .rej is false, and no command can get out of a half-applied feature

Section: Decisions 3 and 5 (plan:139-151, 169-171); §7 item 6 (plan:307)  ·  merged from: design-D3, consistency-C14, user-U15

**Statement.** (1) Apply patches a feature file by file with no rollback (patcher.py:96-128 today; the plan keeps this code, plan:139, 147). An interruption, such as Ctrl-C during a post-link, or an I/O error leaves the feature half applied. (2) The plan answers D4 item 5 with: under `--no-backup-if-mismatch` and `-F0`, a failure just stops and leaves no debris (plan:307). That is false. With exactly those flags, GNU patch applies the hunks that fit, writes the file, and saves the failed hunk to `<file>.rej`; the flag suppresses only `.orig`. I reproduced this in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/merge/t2: '1 out of 2 hunks FAILED -- saving rejects to file f.rej', rc=1, hunk 1 applied. D4 item 5 had proposed `--reject-file=-` (LIGHT_LOCALE_HANDOFF.md:1979). The directory interface explicitly does not roll back (plan:171). (3) A half-applied feature reads CONFLICT (plan:140). `apply` stops at CONFLICT, `unapply` reverses only applied features, and --force is removed (plan:147-151). So no command of the tool can leave this state. D4 item 4 had proposed: dry-run everything first, and roll back what this run applied if something fails.

**Editor.** Correct, and verified. Together with C2, this is what makes a failed hook leave an orphaned partial state.

**Relaxation proposed by the editor.** patch_tree, the one routine every path uses, first dry-runs every file of the feature (with C8's flags) and changes nothing if any file fails. It then applies inside a try/finally that, on any exception including KeyboardInterrupt, reverses the files already done. With C3's per-file replay, a half-applied feature becomes a named state: apply completes it and unapply undoes it, file by file. CONFLICT is reserved for a file that fits no level.

**Defender: partially_confirmed** (needs owner: False).

Verdict in one sentence: the plan's `apply`/`unapply` do NOT half-apply a feature or leave a `.rej` on an ordinary patch conflict, so that part of the challenge is refuted; but every other part survives. Plan:307 gives the wrong reason for its "no debris" claim. The directory interface does leave debris. And a feature left half-applied by an interruption or I/O failure is a trap that the plan itself creates, because today's tool can already get out of that state.

What is refuted. A feature is only applied when it reads "not-applied", and that means every one of its files passed the forward dry-run (plan:139-140, 147). Likewise `unapply` only reverses a feature that reads "applied", meaning every file passed the reverse dry-run (plan:150). make-patches writes exactly one patch file per target path (make-patches:154-171), and every bundled set also has one file per target (checked with find/grep), so the per-file dry-runs together are an exact precondition for the whole feature applying. Experiment e2 case A: a 3-file feature where file 2 conflicts gives "stop rc=1", no file changed and no `.rej`. So in substance the plan already contains the "dry-run everything first" half of D4 item 4, for `apply`/`unapply`, although it never says so. This is better than today: today's apply_all (patcher.py:108-128) applies file by file, so a conflict in file k leaves files 1..k-1 applied.

What is confirmed.
(1) No rollback. Nothing in the plan rolls back failures that a dry-run cannot see: Ctrl-C between files, ENOSPC, a directory that is not writable, or a race (there is no lock; D4 item 13). Experiment e2 case B (KeyboardInterrupt after file 1) gives per-file states [applied, not-applied, not-applied], and the feature reads CONFLICT. Case C (dry-run passes, then the real write fails in a read-only directory) leaves the same half-applied state with no interruption at all.
(2) Plan:307 is wrong about the flags. With `-p1 -F0 --no-backup-if-mismatch`, a real (not dry-run) patch writes the hunks that fit and saves the rest to f.rej, with rc=1 (e1, GNU patch 2.7.6). `--reject-file=-` (D4 item 5, ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979) only drops the `.rej`: the partly patched file stays (e1). Only a dry-run gate gives "no debris", and the directory interface has no such gate (plan:169-171 says "已打上的文件不回滚", i.e. files already applied are not rolled back). Reverse-patching a file that was never applied also writes `.rej` ("1 out of 1 hunk ignored -- saving rejects", e2 treeD). Plan:307 also never answers D4 item 4 (atomicity), even though plan:36-37 promises to lay out every D4 item.
(3) No way out, and this is a regression. Plan:140 says a mixed feature reads CONFLICT ("半打的 feature 不是一个合法状态", a half-applied feature is not a legal state). Plan:147 stops at CONFLICT, plan:150 reverses only applied features, and --force is removed (plan:147-148). Today's per-file skip (patcher.py:70-75) does recover. Experiment e3 runs the real patcher.py (copied to scratch) on the half-applied tree: `patch` gives [applied, applied, applied] and `unpatch` gives [not-applied x3]. So the plan's feature-level conjunction (all files must agree) removes a recovery path that already works. Misusing the directory interface is no clean escape either: it stops at the first failure and leaves `.rej` files (e2 treeD, treeE).

Worse in the conda hook path. If a post-link exits non-zero, conda reverses that package's files at once and runs no pre-unlink (conda/core/link.py:1115-1120, 1129-1159), so features.d/F disappears. A half-applied F is then left behind with nothing pointing to it, and `status` cannot see it. On SIGINT, conda forwards the signal to the script and raises CondaSignalInterrupt (conda/__init__.py:153-163). That is an Exception (conda/__init__.py:70), so the same handler deletes F's files while the tool may still be rolling back. Any rollback therefore must not re-read features.d.

The editor's relaxation, on its merits:
- First part: one routine, patch_tree, used by every path, that dry-runs every file first and changes nothing on failure. This is right. It makes plan:307 true for `apply-to` as well.
- Second part: rollback inside a try/finally. Also right, because a non-zero exit from the hook deletes the inputs. Three corrections: it must be `except BaseException`, since a `finally` would also reverse on success; the patch texts must be read into memory first (e4 test 2: rollback still works after the directory is deleted); and SIGTERM needs a handler, because conda forwards SIGTERM too (conda/common/signals.py:12-18).
- Third part: make the half-applied feature a named state that `apply` completes and `unapply` undoes. This is the only backstop for SIGKILL, power loss or a second Ctrl-C, and it is simply today's per-file skip restored. It is the most elegant of the three because it makes an interruption harmless instead of asking every code path to remember to roll back. Naming it does not coin a word: plan:140 already says "半打" (half-applied).
- One gap the relaxation misses. When an upper feature G is half-applied, a lower feature F that shares files with it reads CONFLICT. The covering rule (plan:145-146) only fires when the upper feature is fully applied, so `apply` would stop at F before ever reaching G. Covering must also fire for a half-applied upper feature, or be done per file. "CONFLICT is reserved for a file that fits no level" depends on C3 being adopted; without C3 it would read "fits neither direction after covering".

Experiment: All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C7/.
- e1: GNU patch 2.7.6 with `-p1 -F0 --no-backup-if-mismatch` on a 2-hunk patch where hunk 2 does not fit. `--dry-run` writes nothing (rc=1). The real run applies hunk 1, writes f.rej, rc=1. Adding `--reject-file=-` removes the .rej, but hunk 1 is still applied.
- e2/proto.py: a model of the plan's feature-level apply. (A) Conflict in file 2: nothing is changed and no .rej is written. (B) KeyboardInterrupt after file 1: states [applied, not-applied, not-applied], feature reads CONFLICT; `apply` stops with rc=1 and `unapply` skips, so the state is stuck. (C) A read-only directory: the dry-run passes, the real write fails, and the feature is left half-applied. treeD/treeE: per-file `patch -R` and forward runs (the directory interface) leave f2.rej/f3.rej or f1.rej.
- e3: today's patcher.py (copied, run with python -I -B) on the half-applied tree: `patch` gives all applied, `unpatch` gives all not-applied.
- e4/fix.py: a prototype fix with per-file states, a dry-run gate, per-file skip, rollback on BaseException and patch texts held in memory. Results: Ctrl-C rolls back fully; rollback works after the feature directory is deleted mid-run; a half-applied feature is completed by apply and undone by unapply; a conflict changes nothing and writes no .rej.
- conda source read: core/link.py:961-966, 1039-1045, 1103-1159; __init__.py:153-163; common/signals.py:12-18; gateways/subprocess.py:108-117.

Recommended fix: Smallest set of plan edits:
(1) Decision 3, plan:140. Replace "混合状态也是 CONFLICT：半打的 feature 不是一个合法状态" (a mixed feature is CONFLICT; a half-applied feature is not a legal state) with a state of its own: a feature whose files all read applied or not-applied, with both present, is **half-applied**. It gets its own `status` token and exit 1. CONFLICT is kept for a file that fits neither direction after covering. At plan:145-146, covering also fires below a half-applied upper feature (or is done per file, if C3 is adopted).
(2) Plan:147-151. `apply` treats a half-applied feature like a not-applied one and applies only its not-applied files. `unapply` treats it like an applied one and reverses only its applied files. This is today's per-file skip (patcher.py:70-75). Re-running the interrupted command always converges.
(3) Decision 5, plan:169-172. patch_tree is the one routine used by apply, unapply, apply-to and unapply-from. It reads the patch texts into memory and dry-runs every file first; if any file is CONFLICT it changes nothing. On any BaseException (plus a SIGTERM handler that raises) it reverses the files this call changed and re-raises; if a reversal fails, it reports the files involved. Delete "已打上的文件不回滚" (files already applied are not rolled back). Rule to state in the plan: exit 0 means the target state is fully reached; non-zero means the tree is as it was found.
(4) §7 item 6, plan:307. Give the correct reason: nothing changes until every file's dry-run passes, and a failure after that is reversed. `--no-backup-if-mismatch` only stops `.orig`; without the gate, GNU patch writes the hunks that fit plus a `.rej`. List D4 item 4 explicitly for the owner's ruling, add the e1 result to §8, and add tests to decision 12: interrupt after file k, then apply and unapply both converge; Ctrl-C rollback; rollback after the feature directory is deleted.

**Judge: partially_confirmed → author_decides_then_rereview.** Make half-applied a named state, with its own status token and exit 1. apply completes it by applying only its not-applied files; unapply undoes it by reversing only its applied files. That is today's per-file skip (patcher.py:70-75) and matches Appendix A's "skipping patches already present".
Make patch_tree the one routine behind apply, unapply, apply-to, unapply-from and gate (c). It:
- reads the patch texts into memory;
- dry-runs every file first and changes nothing if any file fails;
- on any BaseException, plus a SIGTERM handler, reverses the files this call changed and re-raises.
Delete "已打上的文件不回滚" (plan:171).
Correct plan:307. There is no debris because of the dry-run gate, not because of the flags: otherwise GNU patch writes the hunks that fit plus a .rej. List D4 items 4 and 5 explicitly.
Add tests: after an interrupt at file k, apply and unapply both converge; Ctrl-C rolls back; rollback works after the feature directory vanishes.
Refuted part: an ordinary conflict already changes nothing under the plan's apply, because the per-file dry-runs are an exact precondition.

### C8 [major] The tool's calls to GNU patch can stop and wait for an answer on the terminal

Section: Decision 3 (inherits patcher.py:28-42, plan:139); decision 6 (plan:180-181); make-patches gate (c)  ·  merged from: design-D2

**Statement.** check_status (patcher.py:30-39) and the apply call (patcher.py:83) run GNU patch without -f or -t, and the plan keeps that code (plan:139). In the states this plan evaluates, GNU patch then asks a question on /dev/tty, for example 'Reversed (or previously applied) patch detected! Assume -R? [n]' and 'Apply anyway? [n]'. Those states are a half-applied file and a creation patch whose target exists with other content; plan:180-181 covers only the absent and identical cases. In a terminal, the call blocks there. I reproduced the hang under `script`, which provides a pseudo-terminal (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/merge/t2): without -f the dry-run hits the 5 s timeout (rc=124); with -f it answers at once. Conda runs hooks with inherited stdin (PACKAGING_DESIGN.md:32 records stdin=None). So a post-link started from the user's terminal can hang `conda install`, or a keystroke can change the verdict. make-patches' gate (c) has the same omission (tools/make-patches:63-69).

**Editor.** Correct, and confirmed. A small fix with a large effect.

**Relaxation proposed by the editor.** Route every patch invocation (status, apply, unapply, apply-to, and make-patches gate (c)) through one helper that always passes `-f --read-only=ignore --no-backup-if-mismatch -r -`. Then no call site can forget a flag.

**Defender: partially_confirmed** (needs owner: False).

What is confirmed. None of the GNU patch calls passes -f or -t: patcher.py:31 and :37 (the two status dry-runs), patcher.py:83 (apply and reverse), and tools/make-patches:66 (gate (c)). The plan keeps the status logic as it is ("沿用 patcher.py:28-42", plan:139). In the two states the challenge names, GNU patch 2.7.6 really does ask its questions. On a half-applied file the forward dry-run prints "Reversed (or previously applied) patch detected! Assume -R? [n] / Apply anyway? [n]". For a creation patch whose target exists with other content it prints "The next patch would create the file g, which already exists! Assume -R? [n]". plan:180-181 covers only the absent and identical cases.

What is refuted: the hang, and the idea that a keystroke can change the verdict, at every call site that exists today or that the plan inherits.
(1) GNU patch reads its answers from /dev/tty, not from stdin (man patch, FILES: "/dev/tty controlling terminal; used to get answers"). It also opens /dev/tty only when its own stdout is a terminal or POSIXLY_CORRECT is set. Otherwise it prints the question and takes the default answer "n".
(2) Every call site captures stdout: patcher.py:32, :38 and :97 use capture_output=True, and make-patches runs patch through common.run, which uses capture_output=True (tools/common.py:32). So patch's stdout is always a pipe.
Experiment B: inside a pseudo-terminal that is the controlling terminal, the forward dry-run on the half-applied file, called the way patcher.py calls it, returned rc=1 in 0.00 s with the question text in the captured stdout. Running patch directly with its stdout on the pseudo-terminal (experiment A, which is what the merge t2 reproduction did) blocks until the timeout (rc=124). So the t2 reproduction does not match how any call site runs patch.
(3) The conda claim is also wrong. Conda runs hook scripts through subprocess_call (conda/core/link.py:1644-1646). capture_output defaults to True there (conda/gateways/subprocess.py:83), so stdin, stdout and stderr are all PIPE, and communicate(input=None) closes stdin (subprocess.py:99-121). The hook's stdin is therefore not inherited. PACKAGING_DESIGN.md records this at :46, not :32, and its "stdin=None" refers to any_subprocess, which is not the function that runs hooks. Experiment F1: a conda-like hook wrapper calling a tool that does NOT capture patch's output still returns at once in a pseudo-terminal, because patch's stdout is conda's pipe. A post-link hook cannot hang conda install this way.
(4) The verdict does not change with -f. In seven states (modification patch: not applied, applied, half applied, target missing; creation patch: target absent, identical, other content), check_status with captured output gives exactly the same answer with and without -f (experiment table).

What survives, at minor severity rather than major.
(a) If POSIXLY_CORRECT is set in the caller's environment, patch opens /dev/tty even when its stdout is a pipe. Experiment D: the captured dry-run in a pseudo-terminal times out after 5 s. Experiment F2: the same inside a conda-like hook wrapper. Conda copies the user's environment into the hook (link.py:1566), so this does reach a post-link hook. Adding -f removes the hang (experiment D-f).
I also found something worse that -f does not fix. Under POSIXLY_CORRECT, GNU patch cannot apply the `--- /dev/null` creation patches that §0 rule 4 (plan:27) adopts: it prints "can't find file to patch ... No file to patch. Skipping patch." with rc=1, in both directions. And a deletion patch leaves an empty file behind instead of removing it. So the behaviour of the patch calls depends on the caller's environment.
(b) The calls do not stop for an answer only because each call site happens to capture output. Nothing in the plan states that every patch call must capture output, so each new call site has to remember it. The plan's new call sites are patch_tree / apply-to / unapply-from (plan:169-172) and the rewritten status/apply/unapply. That is exactly the kind of shape the elegance criterion objects to.

On the editor's relaxation. One helper used by every call site is the right shape. -f is the right flag. Never use -t / --batch: experiment G shows that `-t --dry-run` on a fully applied patch "assumes -R" and exits 0, so it would report an applied patch as applicable. --no-backup-if-mismatch is already used at make-patches:66 and plan:170. `-r -` works in 2.7.6 (no .rej was left after a failing apply). It belongs to the .rej question in plan §7 item 6, not to this challenge, but it is harmless in the helper. --read-only=ignore has nothing to do with prompts; it belongs to decision 7 (hard links and modes). The relaxation misses two things: the helper must itself capture output, and it must remove POSIXLY_CORRECT from patch's environment. make-patches gate (c) needs no separate fix: plan:173-174 already makes it call apply-to, so it gets the helper automatically.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C8/ (GNU patch 2.7.6).
Fixtures: half/ (a two-hunk modification patch, plus a file with only the first hunk applied), create/ (a git-style `--- /dev/null` creation patch, plus an existing target with other content), del/ (a deletion patch).
Wrappers: call.py runs patch with subprocess.run(capture_output=True), the way patcher.py does. call_inherit.py runs it without capturing. conda_like.py runs a command with Popen(stdin=PIPE, stdout=PIPE, stderr=PIPE) and communicate(input=None), like conda/gateways/subprocess.py:99-121. Everything ran inside `script -qec` so that a pseudo-terminal is the controlling terminal.
Results:
A. patch run directly, stdout on the pseudo-terminal: prompts and times out, rc=124 (this reproduces merge t2).
B. Same call through capture_output: rc=1 in 0.00 s; the question appears in the captured stdout, followed by the default answers.
B-R. Reverse dry-run with capture: rc=1, no question.
E. Tool without capture, run directly: prompts and times out.
F1. Conda-like hook, then a tool without capture: no hang (rc=1 inside, hook rc=0 in 0.06 s).
D. POSIXLY_CORRECT=1 with capture: times out after 5 s.
F2. POSIXLY_CORRECT=1 through the conda-like hook: times out.
D-f. POSIXLY_CORRECT=1 with -f: rc=1 immediately.
G. `-t --dry-run` on a fully applied patch: rc=0 ("Assuming -R"). With -f: rc=1.
Verdict table (verdicts.py): check_status with and without -f gives the same result in all 7 states (modification patch: not applied, applied, half applied, target missing; creation patch: target absent, identical, other content).
POSIXLY_CORRECT=1 with -f: applying the /dev/null creation patch fails ("No file to patch", rc=1) in both directions; the deletion patch leaves an empty file. Without POSIXLY_CORRECT, both work.
`-r -` on a failing apply: no .rej file is left.

Recommended fix: Add one sentence to decisions 3 and 5. Every GNU patch invocation goes through one function in patcher.py, for example _run_patch(tree, patch_file, *, reverse=False, dry_run=False). That function:
- always passes `-f -p1 -F0 --no-backup-if-mismatch -r -` (and `-s` for status), with -f and never -t/--batch;
- always captures stdout and stderr;
- runs patch with POSIXLY_CORRECT removed from its environment.

check_status, apply, unapply and patch_tree (apply-to / unapply-from) are the only callers. make-patches gate (c) already moves to apply-to (plan:173-174), so it needs no change of its own.

Add two pytest cases to decision 12:
(i) Inside a pseudo-terminal (pty.fork), with POSIXLY_CORRECT=1 set, status on the half-applied fixture and on the creation-over-existing-content fixture returns CONFLICT within a short timeout.
(ii) With POSIXLY_CORRECT=1 set, apply and then unapply of a creation patch and of a deletion patch round-trips.

Leave --read-only=ignore to decision 7. Correct the evidence: the conda hook stdio is in conda/gateways/subprocess.py:99-121 (stdin, stdout and stderr are all PIPE), not "inherited stdin" from PACKAGING_DESIGN.md:32.

**Judge: partially_confirmed → author_fixes_no_rereview.** Add to decisions 3 and 5: every GNU patch call goes through one function in patcher.py. It:
- always passes `-f -p1 -F0 --no-backup-if-mismatch --read-only=ignore -r -`, and never -t or --batch (with -t, a dry-run on an applied patch exits 0);
- always captures stdout and stderr;
- removes POSIXLY_CORRECT from the child's environment.
gate (c) reaches this function through patch_tree (C17).
Correct the evidence and lower the severity to minor. With stdout captured, GNU patch takes its default answer at once: I re-ran it in a pty and got rc=1 in 0.00 s. It hangs only when POSIXLY_CORRECT is set. conda hooks get stdin, stdout and stderr all as PIPE (conda/gateways/subprocess.py:83-117), not an inherited stdin.
Add two pytest cases: (i) in a pty with POSIXLY_CORRECT=1, status on the half-applied fixture and on the creation-over-existing-content fixture returns CONFLICT promptly; (ii) with POSIXLY_CORRECT=1, a creation patch and a deletion patch each round-trip through apply and unapply.

### C9 [major] Owner ruling D4 is not honoured: most of its nineteen tool-level items are missing from §7, and one is decided without asking

Section: §0 item 9 (plan:36-37); §7 item 6 (plan:307-309); decision 8 (plan:206-207)  ·  merged from: consistency-C1

**Statement.** In owner ruling D4, about nineteen tool-level items are to be put to the owner one by one when the tool is changed: '动手改 isabelle_patch_control 时逐条请用户定' (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979; also LIGHT_LOCALE_PLAN_REV37.md:7796 item 6). The plan quotes D4 second-hand and adds '钉死' (pinning), which is not in the list. It then claims '本计划把它们逐条摆出来（§7）' (plan:36-37). But §7 item 6 answers only six things: .orig/.rej (wrongly, see C7), after/order.txt, the version key, pinning, --force and scala_build (plan:307-309). The last two are not D4 items. Missing from §7: (1) updating only the `isabelle` package loses the patches (C1); (2) a failed pre-unlink only warns, and the handoff proposed an untracked record of applied patches (C2); (3) pre-unlink runs without activation, so hooks should use $PREFIX (C14); (4) a feature with several patch files is not applied atomically (C7); (10) platforms (C15); (13) there is no concurrency lock (flock), and the plan says nothing about two runs of the tool on one tree; (14) pixi and micromamba may not run link scripts, and the plan says nothing about what such a user gets; (15) the PACKAGING_DESIGN §9 exception (C10); (16) whether patch hooks are exempt from the project's exit-0 rule (RELEASE_CHECKLIST.md:259), which decision 8 decides on its own authority (plan:206-207); (17) how a non-conda tree finds feature directories (C22); (18) what bare apply/unapply mean for external features. Item 9's proposed `isabelle 2025.2.*` dependency is contradicted by plan:197-198.

**Editor.** I verified the handoff's list. The consistency critic rated this blocking. I rate it major, because most of the substantive gaps are captured separately in this review. But items 13 and 14 appear nowhere else, and the plan's claim of completeness misleads the owner about what they are approving. The non-zero exit in decision 8 has to move into §7 as a question.

**Defender: partially_confirmed** (needs owner: False).

WHAT D4 REQUIRES. The owner's ruling D4 (LIGHT_LOCALE_PLAN_REV37.md:7796, item (6)) defers about ten tool-level items "推迟到动手改工具时逐条请用户定，清单在交接文件". The list it points to is LIGHT_LOCALE_HANDOFF.md:1979. It has 19 numbered items, with details in ai-artifacts/readers_impl0/reader2_patch_scheme.md:147-224. The approved migration plan repeats D4 in shortened form, keeps it deferred, and settles only two items: the new-file header (ruling 13) and pinning (ruling 14) (ISABELLE_GIT_MIGRATION_PLAN.md:137-138). The tool plan is exactly the "time the tool is changed". Its §0 item 9 copies the migration plan's short form and then says "本计划把它们逐条摆出来（§7）" (plan:36-37). The plan never cites the handoff or the reader2 report (grep for HANDOFF, 交接, reader2 and 7796 in the plan finds nothing).

WHAT §7 ITEM 6 ACTUALLY COVERS (plan:307-309). It gives six answers.
- Two of them, `--force` and `scala_build`, are not D4 items.
- Of the remaining four:
  - The .orig/.rej answer is wrong. Experiment 1 shows that `-F0 --no-backup-if-mismatch` still leaves a half-patched file plus `f.rej`.
  - The "version key check" answer misreads item (9). Item (9) is the per-Isabelle-release directory key and the `--feature` check against the union of internal and external features (reader2:147-153; today at cli.py:25-43). The plan answers a different question, the version match of built-in features.

COVERAGE OF ALL 19 ITEMS ACROSS THE WHOLE PLAN. Each item is listed with where the plan treats it, if anywhere.
- (1) Updating only `isabelle` silently loses the patches.
  - Real: conda's diff only unlinks and links records that changed (conda core/solve.py:1417-1418), so the post-link of an unchanged feature package never runs again.
  - The plan touches only the `--force-reinstall` case (plan:210-211). The §7 answer "钉死——base_pin" pins the base *feature* package, not `isabelle`. Ruling 21 rules out the remedy "pin the exact `isabelle` build" (migration plan:90). The other two remedies (the base package's post-link re-applies the external features; a run-time check on the HOL side) are never put to the owner.
- (2) A failed pre-unlink only warns; the reader proposed an untracked record of applied patches. Real: conda core/link.py:1675-1680 raises an error only for pre-link and post-link; any other script gets a log.warning. The plan says nothing about it.
- (3) Hooks must use `$PREFIX`. Answered by the design: plan:122-125 derives features.d from ISABELLE_HOME, and plan:202 uses `$PREFIX`. pack.sh:174-176 also derives ISABELLE_HOME_USER from ISABELLE_HOME. It is just not labelled as a D4 answer.
- (4) A feature with several patch files is not applied atomically. Partly answered: the all-files dry-run check (plan:139-140, 147) acts as a pre-check. Rollback after a partial failure is not addressed for `apply`, and plan:171 rejects it for `apply-to`. Not put to the owner.
- (5) Answered wrongly (see above).
- (6), (12), (19) Settled by owner rulings or by the design.
- (7) Owned by the migration plan's gates.
- (8) Half answered. `unapply --feature F` also unapplies F's successors and never re-applies them (plan:150). That is a choice between the reader2:163 options that nobody put to the owner.
- (9) Misread. plan:197 also decides "`isabelle` 任意版本" against the D4 proposal `isabelle 2025.2.*`, without asking. The plan never says what happens when a feature directory's `<R>` does not match the user's Isabelle release.
- (10) Platforms. Only the `.bat` hook is covered (plan:203). Missing are Windows having no GNU patch and `isabelle getenv` returning /cygdrive paths (RELEASE_CHECKLIST.md:305), even though the plan's glossary locates the tree that way (plan:19). Platform scope is not asked.
- (11) Answered by decision 7.
- (13) No lock: nothing in the plan (no flock, 锁 or 并发). Real: experiment 2 shows two runs on one tree leave `f.rej` and exit 1 in the second run. Under decision 8 that would roll back an install.
- (14) pixi/micromamba may not run link scripts: nothing in the plan. Not testable here, because neither is installed.
- (15) The PACKAGING_DESIGN §9 exception.
  - Decision 8 argues only against the PACKAGING_DESIGN.md:5-9 stance (plan:208-213).
  - plan:330 cites PACKAGING_DESIGN.md:1011-1013, which is the very paragraph that rejects patching the user's Isabelle in place, for a different point.
  - The §7.9 exception (PACKAGING_DESIGN.md:876-882) and the question "should the exception be recorded" are never raised.
- (16) The exit-0 rule for hooks (RELEASE_CHECKLIST.md:259).
  - plan:206-207 picks a non-zero exit and states openly that this differs from the rule. It sits under the "待用户定" heading (plan:201).
  - But §7 item 1 (plan:302) asks only "post-link or manual", so an owner who answers "post-link" approves the exit code without being asked.
  - The plan's reason ("让 conda 回滚") also misses a fact from the D4 details (reader2 "已核实"): conda's rollback (core/link.py:1037-1043, 1129-1160) only reverses file actions and runs no scripts. Two consequences follow:
    - In an upgrade, the old pre-unlink has already unapplied the patches, so the rollback leaves the old package installed and unpatched.
    - In a single transaction, a feature applied by an earlier post-link keeps its patches on a pre-existing tree while its package is removed. That is exactly the invisible leftover of item (2).
- (17) Feature directories on a non-conda tree. Answered by `--features-dir` (plan:124-125), and §7 item 5 asks about the directory name.
- (18) Bare apply/unapply. Answered for Isabelle2025-2 (plan:147-151). But one result is not raised: with categories gone, a bare `apply` on Isabelle2024 now also applies the dev-category bundled `show_types_nv` and `expose_map_syn` (categories.toml:20-22; cli.py:150 defaults to `user`; plan:218-221).

WHAT IS REFUTED.
1. "The plan adds 钉死" is wrong. The word is copied verbatim from the approved migration plan:137. "钉确切 build" is one of the remedies listed in D4 item (1) (handoff:1979), and the migration plan records pinning as settled by ruling 14 (migration plan:73, 138).
2. Items (3), (17) and (18) are answered in the plan's decisions. They are missing from §7, not from the plan.
3. "Decides on its own authority" is overstated for the exit code. It is formally part of a proposal awaiting the owner, and the deviation is flagged at plan:207. The real defect is that §7 does not ask about it and the plan omits the rollback hazard.

WHAT IS CONFIRMED.
1. The completeness claim at plan:36-37 is false.
2. Items (2), (13) and (14) appear nowhere in the plan.
3. Items (1), (4), (10), (15) and (16) are partly treated but never put to the owner.
4. Item (9) is misread, and its `isabelle` dependency part is decided silently (plan:197).
5. The `.orig`/`.rej` answer is wrong.
6. `--force` and `scala_build` are passed off as D4 items.

The editor's "major" rating fits. This is a gap in following an owner ruling, and it misleads the owner about what they are approving; the substance of several items is handled in other challenges. The relaxation field is empty, so there is nothing to weigh.

Experiment: The scratch directory is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C9/. GNU patch is version 2.7.6.

Experiment 1 (t1/): a two-hunk patch where hunk 2's context was edited in the target tree, applied with the tool's flags plus `--no-backup-if-mismatch` (`setsid patch -p1 -F0 --no-backup-if-mismatch`, stdin from /dev/null).
- Result: "Hunk #2 FAILED ... saving rejects to file f.rej", rc=1.
- `f` keeps hunk 1 applied (it contains L2), and `f.rej` is left behind.
- So the §7 answer "失败即停，不留碎片" is false.

Experiment 2 (t2/): tool.sh copies the logic of patcher.apply_patch (a reverse dry-run, then a forward dry-run, then the real apply). Two copies run on one tree.
- When both run at the same instant, both exit 0.
- When B's dry-run check comes before A's apply but B applies after A has finished, B prints "Reversed (or previously applied) patch detected! ... Skipping patch ... saving rejects to file f.rej" and exits 1.
- So without a lock (D4 item 13) a run fails for no real reason and leaves `.rej` debris. Under the non-zero exit that decision 8 picks for post-link, that failure would roll back a conda install.

Source reading of the local conda (miniconda3/lib/python3.13/site-packages/conda):
- core/solve.py:1417-1418: only changed records are unlinked or linked, so updating `isabelle` does not re-run a feature package's post-link.
- core/link.py:1675-1680: only pre-link and post-link failures raise; a failed pre-unlink only logs a warning.
- core/link.py:1037-1043 and 1129-1160: rollback reverses file actions only and runs no scripts.

pixi and micromamba are not installed, so D4 item 14 could not be tested.

Recommended fix: 1. In §0 item 9 (plan:36-37), replace the shortened D4 quote with a pointer to the full 19-item list (LIGHT_LOCALE_HANDOFF.md:1979, with details in readers_impl0/reader2_patch_scheme.md). Note that migration plan:137-138 records items (6) and the pinning remedy as settled by rulings 13, 14 and 21.

2. Rewrite §7 item 6 (plan:307-309) as a 19-row list using the handoff's numbering. Mark each row as one of three kinds:

   a. Settled by an owner ruling:
      - (6) by ruling 13.
      - (12).
      - (19) by ruling 8.
      - The pinning half of (1) by rulings 14 and 21. Ruling 21 rules out pinning the exact `isabelle` build.

   b. Answered by a plan decision, awaiting the owner's approval:
      - (3) by decisions 2 and 8.
      - (4): the dry-run pre-check exists; there is no rollback.
      - (8): `unapply --feature` also unapplies the successors and does not re-apply them.
      - (11) by decision 7.
      - (17) by `--features-dir`.
      - (18) by decision 3. Add the Isabelle2024 consequence: a bare `apply` now also applies `show_types_nv` and `expose_map_syn`.

   c. An explicit question for the owner, with options:
      - (1): the two remedies still open.
      - (2): pre-unlink failure, and whether to keep a record of applied patches.
      - (5): corrected answer (C7).
      - (9): whether the tool checks the release in the `feature` field against `isabelle version`, and whether feature packages depend on `isabelle 2025.2.*` instead of "any version" (plan:197).
      - (10): platform scope.
      - (13): a lock, yes or no.
      - (14): what pixi/micromamba users get.
      - (15): whether to record the patch-package exception in PACKAGING_DESIGN §9.
      - (16): the post-link exit code. Move it out of decision 8 into §7, with the warning that conda's rollback runs no scripts.

3. Move `--force` and `scala_build` out of the D4 row into their own lines.

**Judge: partially_confirmed → author_fixes_no_rereview.** Replace §0 item 9's paraphrase with a pointer to the full 19-item D4 list (LIGHT_LOCALE_HANDOFF.md:1979; details in readers_impl0/reader2_patch_scheme.md).
Rewrite §7 item 6 as 19 rows in the handoff's numbering. Mark each row as one of: settled by a ruling; answered by a plan decision awaiting approval; or an open question with options. At least items 1, 2, 5, 9, 10, 13, 14, 15 and 16 are open, and decision 8's exit code moves into item 16.
Move --force and scala_build onto their own lines; they are not D4 items.
Fix the misreading of item 9. It covers the per-release directory key, --feature validation, the rules for duplicate names, and the `isabelle 2025.2.*` dependency.
Refuted part: "钉死" is copied verbatim from migration plan:137.

### C10 [major] The plan misstates the record on post-link patching: the owner already chose it, and PACKAGING_DESIGN §9 vetoes it

Section: §0 (plan:22-40); §2.3 (plan:93-94); decision 8 (plan:201-214); §7 item 1 (plan:302); §9 (plan:330)  ·  merged from: consistency-C2, consistency-C4

**Statement.** Two records about post-link patching are misread. (1) The owner already settled how features are installed. LIGHT_LOCALE_PLAN_REV37.md:5805 says '方向已定：补丁文件加 conda 包的 post-link/pre-unlink 安装' (direction settled: patch files installed by the conda package's post-link/pre-unlink). The light plan's 2026-10-11 ruling (1) records that conda packages' post_link/pre_unlink call isabelle_patch_control to apply and reverse, and that 'heap 全部失效、按需重建，用户接受' (all heaps go stale and are rebuilt on demand; user accepted) (:7796). The handoff records the same (LIGHT_LOCALE_HANDOFF.md:1958 item 4). Entry (44) replaces only the development side (:7864). Yet §0 omits this decision, and §7 item 1 reopens it with a manual-apply fallback (plan:214, 302). (2) The plan cites PACKAGING_DESIGN.md:5-9 for the stance that post-link must not create untracked files. It then argues that modifying the `isabelle` package's files falls outside that stance (plan:93-94, 208-209). The authoritative document's §9 says the opposite. Its reason 2 says that patching the user's Isabelle in place is a deeper form of the same untracked side effect, and that no package manager endorses it (PACKAGING_DESIGN.md:1010-1015). Line 4 of the document points to that veto, and §9 also gives the objection that cleanup through pre-unlink is unreliable (:1006-1008; also the table at :33). D4 item 15 left exactly this conflict to the owner: whether to record an exception for patch-type packages (LIGHT_LOCALE_HANDOFF.md:1979). The plan cites :1011-1013, which is part of the veto's own text, for an unrelated point (plan:330), and never surfaces the veto.

**Editor.** The critics are right that the plan misstates both records. The harm differs. Reopening a settled question costs the owner a second answer, not a wrong outcome, so point (1) on its own would be minor. Misrepresenting §9 matters more, because it hides exactly the objections (untracked modification, unreliable cleanup) that C1 and C2 now confirm. A correction to consistency-C4: §9's veto was aimed at patching a foreign Isabelle the user installed themselves. Feature packages patch the channel's own package in $PREFIX/isa, which is a narrower case. The honest framing is: the same objection, a narrower target, and the owner accepted the heap cost on 2026-10-11. It is not 'the stance does not cover this'. The plan should record the ruling in §0, keep in §7 only the sub-questions that are really open (exit code, platforms, pixi), and put the PACKAGING_DESIGN exception to the owner.

**Defender: confirmed** (needs owner: True).

I tried to refute both halves of the challenge. Both survive. The editor's narrowing is correct, and the sources add two more facts against the plan.

Point (1): the owner already chose post-link installation, the plan's §0 omits it, and §7 reopens it.
- The owner ruled on this twice. On 2026-09-14 the handoff records "用户决定：… 补丁经 conda post-link/pre-unlink 安装" (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:84). On 2026-10-11 it records "2026-10-11 用户定 … (4) … post_link/pre_unlink 打/反打补丁；heap 全部失效、下次用时自动重建——用户接受" (:1958). The light plan records the same ruling as (1) "补丁管理定案" (ai-artifacts/LIGHT_LOCALE_PLAN_REV37.md:7796). Its §9 says "方向已定：补丁文件加 conda 包的 post-link/pre-unlink 安装" (:5805).
- Refutation attempt 1: was the ruling superseded? Entry (1) says "2026-10-22 起由 git 补丁管理取代，(44)" (:7796). But (44) lists what it replaces: the private trees, the stock trees, run-tree and make-patches take the place of editing the shared tree, the stock copy and light's own patch scripts (:7864). It says nothing about conda installation. Migration plan §0 rule 5 says "发布方式不变" (ISABELLE_GIT_MIGRATION_PLAN.md:57). Not superseded.
- Refutation attempt 2: did the plan only inherit what the migration plan quoted? The migration plan quotes just two items, D1 and D4, as "中与本方案相关的两条" (:109). Install timing did not matter to the migration, but it matters to this tool plan. The plan's §0 heading names "light 计划" as a source (plan:22), so the omission is the plan's own.
- The binding §5.3 interface also assumes that installing a package patches the tree. It says the packages that install the first k segments do not change files: "装前 k 节的包不改文件，卸它们…" (migration plan:413). The plan's paraphrase in §0 item 10 drops that clause (plan:38-40).
- Result: §0 omits the ruling. Decision 8 calls post-link "本计划的主要提案，待用户定" and offers manual apply as the fallback (plan:201, 214). §7 item 1 asks the settled question again (plan:302).

Point (2): the plan misreads PACKAGING_DESIGN and hides its objections.
- The plan cites PACKAGING_DESIGN.md:5-9 for the "nothing untracked" stance (plan:93-94). Lines 5-9 are the status note and the §1 heading. The stance is actually at :32 and :48-52. Line :52 quotes the conda-build rule "只碰正在安装的文件" (touch only the files being installed). A post-link that edits the `isabelle` package's files breaks that rule directly.
- §9 reason 1 says pre-unlink cleanup is not guaranteed (:1007-1009). Reason 2 says in-place patching is "同一个「不跟踪的副作用」问题的更深版本" and that no package manager endorses it (:1010-1014). Line :4 points to §9.
- The plan argues that its post-link "不产生新文件" (creates no new files) (plan:208). That is false, and decision 6 itself handles new-file patches (plan:178-181). Light's current patch set creates three files that the `isabelle` package does not ship: src/Pure/exported_premises.ML, more_exported_premises.ML and Isar/light_locale_axiom_facts.ML (contrib/light_locale/tools/patched_files.txt; patch headers show `@@ -0,0`; none exists under pkgs/isabelle-2025.2-0/isa).
- The plan cites :1011-1013, which is the veto text itself, for "conda 没有这种机制" (plan:330).
- §7 item 6 claims to answer the deferred D4 items (plan:307-309). It leaves out item 15, "PACKAGING_DESIGN.md §9 否决…而 §7.9 开口子——要不要记'补丁类外部包的例外'" (LIGHT_LOCALE_HANDOFF.md:1979). Items 1, 2 and 14 are also missing. Yet §0 item 9 promises "逐条摆出来" (plan:36-37).
- The plan's consequence (a), "conda remove isabelle … 没有残留" (plan:209-210), holds only when pre-unlink succeeds. conda turns a failed pre-unlink into a warning and carries on with the removal (miniconda3/lib/python3.13/site-packages/conda/core/link.py:1675-1683). It only removes empty parent directories (gateways/disk/delete.py:190-196).

Corrections to the challenge:
- The editor's narrowing holds. §9 targets "复用用户已装的 Isabelle" (:1001-1003) and "原地 patch 用户自己的 Isabelle" (:1011). Feature packages patch the channel's own tree in $PREFIX/isa, so deleting the environment does remove it.
- The same document also contains a user-confirmed exception: §7.9 says the Isa-REPL package "会在自己的安装脚本里自动打 register_thy 补丁", with heaps going stale and rebuilt on demand (PACKAGING_DESIGN.md:876-882). The document is split, which is why D4 item 15 exists. "§9 vetoes it" therefore means "an open conflict the owner must settle", not "already forbidden".
- The challenge's "table at :33" is a miscitation. The table rows are :48-49.

None of this refutes the substance. The plan misstates both records and hides the very objections that decide the question.

Experiment: All work was in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C10/exp/. Nothing outside that directory was modified.
(1) I built a toy prefix with one file the "isabelle package" records, isa/src/Pure/ROOT.ML. I applied a git-style `--- /dev/null` new-file patch with `patch -p1 -F0 --no-backup-if-mismatch`. It created isa/src/Pure/more_exported_premises.ML.
(2) With miniconda's own python (`-I`), I called conda's own `conda.gateways.disk.delete.rm_rf(..., clean_empty_parents=True)` on the recorded path only, as conda's unlink does. What was left: ['isa/src/Pure/more_exported_premises.ML'], and the directories isa/src/Pure stayed.
(3) I called conda's own `conda.core.link.run_script` with a fake package record whose script exits 1. For pre-unlink it printed "pre-unlink script failed … consider notifying the package maintainer" and returned False, so the removal continues. For post-link it raised LinkError, so the transaction rolls back.
Conclusion: a failed unapply in pre-unlink leaves the patch, including any new files, on the tree. The package is still removed, and `status` can no longer see the feature because its features.d entry is gone.
Script: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C10/exp/conda_probe.py

Recommended fix: The text fixes below are author edits. Only (5) needs the owner.

(1) Add an item to §0: "Owner ruling, 2026-09-14 and 2026-10-11: feature patches are installed by the conda package's post-link and removed by its pre-unlink, which call isabelle_patch_control. All heaps go stale and are rebuilt on demand; the user accepted this (LIGHT_LOCALE_HANDOFF.md:84, :1958 item 4; LIGHT_LOCALE_PLAN_REV37.md:5805, :7796 item 1). Entry (44) replaced only the development side (:7864)."

(2) Decision 8: delete "（本计划的主要提案，待用户定）" (plan:201) and the fallback bullet (plan:214). Replace plan:208-209 with an honest paragraph covering four facts:
- Post-link both edits another package's files and creates files conda does not track. New-file patches do this; light creates three today. PACKAGING_DESIGN.md §3.1 (:48-52) and §9 reasons 1-2 (:1007-1014) object to both.
- The target is narrower than §9's: the channel's own tree in $PREFIX/isa, not the user's own Isabelle.
- §7.9 (:881-882) already records a precedent: an install script that patches the tree, with heaps rebuilt on demand.
- A failed pre-unlink only warns (conda/core/link.py:1675-1683). Consequence (a) therefore holds only when pre-unlink succeeds.

(3) §7 item 1: replace "post-link or manual" with D4 item 15, "should PACKAGING_DESIGN record an exception for feature packages?". Put the open D4 sub-questions next to it: item 16 (the nonzero exit code against RELEASE_CHECKLIST.md:259), item 2 (pre-unlink failure), item 1 (an update of only the `isabelle` package does not re-run post-link), item 14 (pixi/micromamba), and item 10 (platforms).

(4) Fix the citations. Change plan:93-94 to cite PACKAGING_DESIGN.md:32 and :48-52. At plan:330, drop :1011-1013 or cite a source that actually supports the point.

(5) The owner decides D4 item 15.

**Judge: confirmed → owner_decides.** (1) Add to §0 the owner's ruling, made 2026-09-14 and 2026-10-11: feature patches are installed by the conda package's post-link and reversed by its pre-unlink, which call isabelle_patch_control, and all heaps going stale is accepted (LIGHT_LOCALE_HANDOFF.md:84, :1958 item 4; LIGHT_LOCALE_PLAN_REV37.md:5805, :7796 item 1). Entry (44) at :7864 replaced only the development side.
(2) Delete "本计划的主要提案，待用户定" (plan:201) and the fallback bullet (plan:214).
(3) Replace plan:208-209 with an honest paragraph:
- the post-link both edits files of another package and creates untracked files (light creates three);
- PACKAGING_DESIGN §3.1 (:48-52) and §9 (:1007-1014) object to both;
- the target is narrower than §9's, the channel's own tree in $PREFIX/isa;
- §7.9 (:876-882) is a precedent;
- a failed pre-unlink only warns.
(4) Replace §7 item 1 with D4 item 15 for the owner.
(5) Fix the citations at plan:93-94 (use PACKAGING_DESIGN.md:32, 48-52) and plan:330.

### C11 [major] Release 1.0.0 already drops the Isabelle2025-2 dev patches, before qiyuan-dev-patches exists, which breaks D1's 'step by step' ordering

Section: §0 item 8 (plan:33-35); decisions 2, 10, 12 (plan:121, 239-241, 258); §5 steps 1, 4, 6, 7 (plan:278, 283, 287-288)  ·  merged from: consistency-C5, landing-L3

**Statement.** Migration §5.3 and D1 fix an order: the tool release that removes the Isabelle2025-2 dev patches must come after the first release of qiyuan_dev_patches (ISABELLE_GIT_MIGRATION_PLAN.md:410-411; D1 '逐步' at :127-131). The plan says the step-7 release is that removal (plan:288). But step 1 already lands decision 12 (package-data becomes only bundled/** and AGENTS.md, plan:258) and decision 2 (the only input is features.d; no categories.toml, plan:121, 136). So the 1.0.0 published in step 4 (plan:283) neither ships nor reads patches/Isabelle2025-2 or categories.toml, and it cannot apply the dev patches. qiyuan-dev-patches is released only in step 6 (plan:287). The step-7 release therefore deletes files that no released isabelle-patch-control has shipped since 1.0.0. In substance, 1.0.0 is the removal release. The wording 'do not touch patches/Isabelle2025-2/ (deleted in step 7)' (plan:278) hides this. The dev patches are a documented workflow today: README.md:27-28 and :79 tell developers to run `patch --category all`, and so does contrib/Isa-Mini/Agent/Injector/ROOT:24-26.

**Editor.** Correct. Note that the dev patches no longer apply on top of light anyway. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/devfirst.sh shows src/Pure/Syntax/syntax_phases.ML hunk #4 failing. So carrying them in 1.x as bundled feature directories helps only trees without light. That makes the simpler resolution the more honest one, but it needs the owner's confirmation that it satisfies D1.

**Relaxation proposed by the editor.** Declare my-better-isabelle-prover 0.3.0 the dev-patch carrier until qiyuan-dev-patches is released, and make step 7 a repository cleanup with no release. Put this reading of D1's '逐步' to the owner explicitly. Do not keep a release that changes nothing and present it as the ruling's endpoint.

**Defender: confirmed** (needs owner: True).

I tried to refute C11 and could not. Every factual claim in it holds. The plan says it satisfies the ordering rule, but its own steps do not.

1. The rule. Migration plan ISABELLE_GIT_MIGRATION_PLAN.md:410-411 says the tool release that removes the Isabelle2025-2 dev patches must come after the first release of qiyuan_dev_patches. It calls this D1's "逐步" (step by step). The word itself is at :121, and the plan keeps it at :131. (C11 cites :127-131, which is slightly off.) This plan repeats the rule as an owner ruling (plan:33-35) and as an interface it must satisfy (plan:38-40).

2. What release 1.0.0 contains. Step 1 (plan:278) lands decisions 2, 9 and 12:
- the only input is features.d (plan:121); there is no categories.toml (plan:136);
- "Isabelle2025-2 什么都不附带" (nothing is bundled for Isabelle2025-2, plan:221);
- package-data is only bundled/** and AGENTS.md (plan:258);
- the category options are gone and the commands are renamed (plan:115-116).

Step 4 publishes 1.0.0 (plan:283), and it cannot be delayed, because every feature package depends on isabelle-patch-control >=1.0 (plan:197). qiyuan-dev-patches comes only at step 6 (plan:287). Ruling 25 makes it wait for three more feature releases (migration :96-97; plan:31). So the first isabelle-patch-control release already cannot apply the dev patches, long before qiyuan-dev-patches exists. In substance, 1.0.0 is the removal release.

3. Step 7 changes nothing for users. Step 7 (plan:288) deletes repository files that no isabelle-patch-control release has ever shipped or read. Calling it "发版, 逐步的终点" (a release, the end point of the step-by-step rule) is a misreading. "不碰 patches/Isabelle2025-2/（第 7 步才删）" ("do not touch it until step 7", plan:278) and plan:239-241 present these dead files as if they were still live.

4. The plan does not even keep the old package as the carrier. plan:114 keeps 0.3.0 only "给今天的 CI 用到 CI 计划落地为止" (for today's CI, until the CI plan lands). That is step 5 (plan:286), which is before step 6. So the reading "0.3.0 carries the dev patches until then" is not what the plan says either.

5. The delay also makes the docs wrong. plan:239-241 also postpones removing the README's feature table and category section until step 7. README is the PyPI long description (pyproject.toml:9). So the 1.0.0 PyPI page would still tell developers to run `my-better-isabelle patch --category all` (README.md:27-28, :39, :79), a command 1.0.0 does not install, with an option it removed. The same goes for reference.md:66-150.

6. The dev patches really are a documented workflow today: README.md:27-28 and :79; Isa-Mini/Agent/Injector/ROOT:24-26; Isa-Mini/ROOT:15; Isa-Mini/conda/recipe.yaml:32, :142, :152.

Refutation attempts, and why each fails:
(a) "isabelle-patch-control is a new distribution, so no release of my-better-isabelle-prover ever removes anything." The plan itself defines isabelle_patch_control as the renamed tool (plan:17-18, :111-113), migration §5.3 names it the same way (:407), and plan:288 calls step 7 a release of the tool. Under either reading, the step-7 release is empty and the plan's claim to comply is wrong.
(b) "The shared tree already gets the dev patches through git." This is true: daily = 30aab6e, RECORD.md:48-49, and ruling 25 says there is no early need. It lowers the practical harm, but it does not make the plan's text correct.
(c) "The dev patches no longer apply on top of light anyway." I reproduced this independently (see experiment). It means no ordering could give light trees the dev patches before qiyuan-dev-patches exists. It limits what any fix can deliver; it does not rescue the plan's wording.

The editor's relaxation, on its merits: it is sound and the cleanest option.
- 0.3.0 is on PyPI and cannot change. It ships exactly the dev patches plus categories.toml (pyproject.toml:6-7, :39-40), and it can be installed next to 1.0.0: the distribution, import package and command names are all different (pyproject.toml:6, :34, :37 versus plan:111).
- The alternative, carrying the dev patches in 1.x as a bundled feature directory, would be a dirty hack. Those patches sit below light in the chain. In any environment with isabelle-light-locale, two features would then share one base, which decision 3 makes an exit-3 error (plan:134-135). Avoiding that would need a special case.

The relaxation needs three additions:
(i) plan:114 must keep 0.3.0 installable (not yanked) and documented as the dev-patch carrier until qiyuan-dev-patches is first released.
(ii) The docs must state its scope: only trees without isabelle-light-locale. On a light tree, 0.3.0's `patch --category all` goes in alphabetical order and stops at the syntax_phases.ML CONFLICT without rolling back (patcher.py:76-81, :122-127). By then it has already applied sign.ML, thy_info.ML, attrib.ML, etc/options and printer.ML, so show_types_nv is left half applied.
(iii) The README, reference.md and AGENTS.md shipped with 1.0.0 must drop the category workflow and point to 0.3.0 instead.

needs_owner: whether "0.3.0 stays the carrier" satisfies the owner-approved rule at :411 is a new reading of an approved plan. Only the owner can confirm it.

A side citation error, outside C11: plan:70 cites pyproject.toml:44-46 for package-data, but it is at :39-40.

Experiment: All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C11/. The only git commands I ran were read-only (`git show`, `git diff-tree`).

1. dev-on-light.log: I copied the six files the dev patches touch from the light_locale branch (`git show Isabelle2025-2/light_locale:<f>`) and dry-ran 0.3.0's patches with `patch --dry-run -p1 -F0`. thy_info, attrib (offset 16), etc-options, printer and sign all pass. show_types_nv/syntax_phases.ML.patch fails: "Hunk #3 FAILED at 698", rc=1.

2. dev-on-k1.log: the same six files copied from ~/miniconda3/pkgs/isabelle-2025.2-0/isa (the published build). All six dev patches pass. So 0.3.0 can carry the dev patches only on trees without light.

3. `git diff-tree` from future_assign_interrupt to light_locale shows light also changes attrib.ML and syntax_phases.ML.

4. mixed/: I applied 0.3.0's attrib.ML patch on top of light, and light's attrib diff still reverse-applies. So the only clash is syntax_phases.ML, where 0.3.0 stops after partly applying show_types_nv.

Recommended fix: The smallest change that removes the contradiction, pending the owner's confirmation of how to read "逐步":

(1) Replace plan:114 with: "my-better-isabelle-prover 0.3.0 gets no new releases and is not yanked. Until qiyuan-dev-patches is first released, it is the documented carrier of the Isabelle2025-2 dev patches, and only for trees without isabelle-light-locale or later (on a light tree syntax_phases.ML conflicts under -F0). It can be installed next to isabelle-patch-control."

(2) In decision 10 (plan:239-241) and step 1 (plan:278): the README, reference.md and AGENTS.md shipped with 1.0.0 drop the feature table, the category section and `--category all`, and add one paragraph pointing developers to 0.3.0 with that scope.

(3) Rewrite step 7 (plan:288) as a cleanup with no release, done after qiyuan-dev-patches is published: remove the pointer to 0.3.0 and update the Isa-Mini comments (ROOT:15, Agent/Injector/ROOT:24-26, conda/recipe.yaml:32/142/152). Do not call it the end point of the ruling. Rewrite plan:35 and plan:240-241 to say that 1.0.0 is in substance the removal, and that 0.3.0 covers the gap.

Optional, for elegance: delete patches/Isabelle2025-2/*.patch and categories.toml in step 1, together with the code that reads them. From step 1 on, nothing reads them, and their content is already on the dev_patches branch (ab6006e, RECORD.md:48). Keep only the three .md docs until step 6 moves them into qiyuan_dev_patches. Then the repository never holds dead patch files that look live.

Put the reading of D1/§5.3:411 to the owner explicitly: "the tool's first release without the dev patches (1.0.0) comes before qiyuan-dev-patches; 0.3.0 bridges the gap".

**Judge: confirmed → owner_decides.** Pending the owner's reading of D1's "逐步", rewrite three places:
- plan:114: my-better-isabelle-prover is not yanked. It stays the documented carrier of the Isabelle2025-2 dev patches until qiyuan-dev-patches is first released, but only for trees without isabelle-light-locale, where syntax_phases.ML conflicts. That carrier is 0.3.0, or the final 0.4.0 if the owner picks it in C12.
- plan:35 and plan:240-241: say that 1.0.0 is in substance the removal.
- Step 7: a repository cleanup with no release.
The README, reference.md and AGENTS.md shipped with 1.0.0 drop the category workflow and point developers to the old package, with that scope.
Optionally delete patches/Isabelle2025-2/*.patch and categories.toml already in step 1, so that no dead files look live.

### C12 [major] Decision 9's bundled Isabelle2024 sets contradict decision 3, so every Isabelle2024 command would exit 3, and they silently drop the user/dev default

Section: Decision 9 (plan:216-223) against decision 3 (plan:134-136); §6  ·  merged from: design-D7, consistency-C11, landing-L11, user-U9, landing-L8

**Statement.** Decision 9 gives each of the three bundled directories `base_tag: Isabelle2024/pristine/none` and states an alphabetical order separately (plan:218-221). Decision 3 derives order only from base_tag and makes 'two features on the same base' an exit-3 error (plan:134-136). Implemented as written, `status`, `apply` and `unapply` all exit 3 on Isabelle2024. Making the three a chain would need invented base tags, and it would create dependencies that three independent features do not have. `apply --feature future_assign_interrupt`, the only user-category feature there, would then also apply a dev patch, and `unapply --feature expose_map_syn` would also reverse show_types_nv. Without categories, a plain `apply` on Isabelle2024 applies all three bundled sets. Today the default applies only future_assign_interrupt (cli.py:150, `_add_category(p_patch, "user", ...)`; categories.toml:17-22). That silently grows the default to include two dev-only patches, and no owner approved it. Migration §5.3 removes the categories only for the 2025-2 line, and says the Isabelle2024 sets are to be decided separately (ISABELLE_GIT_MIGRATION_PLAN.md:408-409). Values such as `release_tag: none (bundled)` and an invented pristine tag misuse the provenance file, which the glossary defines as recording real git tags and shas (:45-46). This machine's Isabelle2024 tree has show_types_nv applied and the other two not applied (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/i2024/). Under an alphabetical chain, that state is the 'hole' of plan:146, and `apply` would fill it with the dev patch expose_map_syn. No acceptance step runs the tool on Isabelle2024, although contrib/Isabelle2024 exists locally.

**Editor.** Correct. The judge's suggestion, keeping the sets in the tool until Isabelle2024 is no longer supported, is a legitimate open question (§7 item 2). Decision 9 implements it in a broken way. The critics' alternative fix, chaining the three explicitly with future_assign_interrupt first and keeping a user-only default, works. But it fabricates provenance and re-creates categories under another name.

**Relaxation proposed by the editor.** Leave Isabelle2024 with the old tool. Make one last my-better-isabelle-prover 0.3.x release that adds Isabelle2024/future_assign_interrupt, which v0.3.0 lacks (ISABELLE_GIT_MIGRATION_PLAN.md:599), and keeps the user/dev categories. isabelle-patch-control then carries no patches at all, which is ruling 2 taken literally. No provenance has to be invented, and the chain model never meets independent features.

**Defender: confirmed** (needs owner: True).

I tried to refute the challenge and could not. It holds under both readings of decision 9. Three small corrections are noted at the end.

1. The literal reading contradicts decision 3. Decision 9 gives every bundled directory a provenance file with `base_tag: Isabelle2024/pristine/none` (plan:218-219). Plan:133 says the second segment of `base_tag` names the base feature, and `pristine` marks the head of the chain. Plan:134-135 derives the order only from `base_tag`, and makes "two features on the same base" an exit-3 error. `pristine` gets no exception. Plan:221 tells the tool to treat the bundled directories as if they were in `<features.d>`, so this derivation applies to them. Result: `status`, `apply` and `unapply` exit 3 on Isabelle2024. My prototype printed "exit 3: two features on the same base: {'pristine': [...all three...]}".

2. The charitable reading does not rescue it. Suppose the alphabetical order the plan states separately (plan:219-220) is meant to be encoded. Then the bases have to be invented tags such as `Isabelle2024/expose_map_syn/none`. Nothing like that exists: the Isabelle git repository has only `refs/heads/Isabelle2025-2/*` and one tag, `Isabelle2025-2/pristine/89701cf1768e`, so `Isabelle2024/pristine/none` names no tag either. The chain also creates dependencies that do not exist. The plan itself says the three "互不相干，任何顺序都行" (are independent; any order works; plan:220), and they touch disjoint files (future.ML; sign.ML; options/attrib/printer/syntax_phases). Under the chain rules:
   - `apply --feature F` also applies F's predecessors (plan:148).
   - `unapply --feature F` also reverses F's successors (plan:150).
   - A plain `apply` applies every not-applied feature (plan:147).
   Today the default category is user (cli.py:150 patch, cli.py:163 status gate). On Isabelle2024 that selects only future_assign_interrupt (categories.toml:18-22). So the default silently grows to include two dev-only features. Nothing in the plan says so, and §7 item 2 (plan:303) asks the owner to choose without mentioning this consequence. Migration §5.3 removes the user/dev classification only for the Isabelle2025-2 line, and leaves Isabelle2024 to be decided separately (ISABELLE_GIT_MIGRATION_PLAN.md:407-409). Rule 25 (:97-99) does the same.

3. The provenance values break the plan's own invariants:
   - The glossary defines the provenance file as recording real tags and shas (ISABELLE_GIT_MIGRATION_PLAN.md:45-46).
   - Decision 2 says a feature directory contains exactly what `make-patches` writes (plan:121). The `make-patches` source writes real tags (tools/make-patches:192-206).
   - So `release_tag: none (bundled)` and a pristine tag that does not exist are placeholders made up to get past the parser.
   - It also clashes with plan §0 item 2, "工具变成不带任何补丁的纯框架" (the tool becomes a pure framework with no patches at all; plan:25), and with migration :211.

4. On this machine's Isabelle2024 tree, show_types_nv reads applied (all 4 files), and expose_map_syn and future_assign_interrupt read not-applied. I checked this independently on copies of the six target files. Under the alphabetical chain that is the "hole" of plan:146, and `apply` (even `--feature future_assign_interrupt`) would fill it with the dev patch expose_map_syn.

5. No acceptance step touches Isabelle2024. §6 (plan:290-298) covers only 2025-2. Decision 12's pytest (plan:253-256) tests only toy chains, not the bundled directories.

Corrections:
- "Every Isabelle2024 command exits 3" is too strong. `apply-to`, `unapply-from` and `help` do not derive the chain (plan:170). The affected commands are `status`, `apply` and `unapply`.
- On this tree, `unapply --feature expose_map_syn` reverses only show_types_nv, because the other two are not applied. It still reverses something the user did not ask for.
- The editor's "0.3.x" should be 0.4.0. RELEASE.md:44-47 says a behavioural break bumps the MINOR version. Compared with v0.3.0, HEAD drops pide_control and perspective_eof_clamp on Isabelle2024, and v0.3.0 had those in the user category (git show v0.3.0:.../categories.toml). It also adds future_assign_interrupt (commit cc3a3a8). ISABELLE_GIT_MIGRATION_PLAN.md:599 confirms v0.3.0 lacks it.

The editor's relaxation, judged on its merits: it is the most elegant option.
- The new tool keeps a single input model, so the invariant "every feature directory is `make-patches` output with real provenance" can no longer be violated.
- The tool no longer needs to check `isabelle version` to pick bundled sets (plan:221).
- `bundled/**` leaves the package data (plan:258).
- Isabelle2024 users keep exactly today's behaviour, including the user-only default.
- It satisfies rule 25 / judge's suggestion in spirit (Isabelle2024 stays supported by the tool's last pre-framework release), and plan §0 item 2 literally.
- CI is unaffected: it pins MBI_VERSION 0.3.0 (build.yml:218), and check_patch_sync.sh:27-33 compares against that pin.
- The two tools can coexist in one environment because their command and import names differ.
- Its only cost is changing decision 1's "旧 PyPI 包不再发版" (the old PyPI package is not released again; plan:114). That is the plan's own proposal, not a ruling.

The Isabelle2024 question itself is reserved for the owner (rule 25; plan §7 item 2), so the replacement shape needs the owner's choice.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C12/.

1. Status of the Isabelle2024 tree. I copied the six target files from contrib/Isabelle2024 (future.ML, etc/options, attrib.ML, sign.ML, printer.ML, syntax_phases.ML) into i2024/. On the copies I ran the same checks as patcher.py:28-42 (`patch --dry-run -R -p1 -F0`, then the forward dry run) for every Isabelle2024 patch. Result: show_types_nv applied (4/4 files); expose_map_syn and future_assign_interrupt not-applied.

2. chain_proto.py. A prototype of plan:134-150 (chain derivation, the "covered"/hole rule, and the `apply`/`unapply --feature` selection), fed with the decision 9 provenance and run on i2024/:
   - Literal `base_tag` = pristine for all three: exit 3, "two features on the same base".
   - Charitable alphabetical chain: both lower features flagged as a hole. A plain `apply` patches [expose_map_syn, future_assign_interrupt]. `apply --feature future_assign_interrupt` also patches expose_map_syn. `unapply --feature expose_map_syn` reverses show_types_nv.
   - For comparison, the categories.toml selection today picks only [future_assign_interrupt].

3. Read-only git checks:
   - `git for-each-ref` in contrib/Isabelle2025-2 shows only Isabelle2025-2/* refs; there is no Isabelle2024 line or tag.
   - In the tool repository, `git ls-tree v0.3.0` shows Isabelle2024 = {expose_map_syn, perspective_eof_clamp, pide_control, show_types_nv} with no future_assign_interrupt, while HEAD shows {expose_map_syn, future_assign_interrupt, show_types_nv}. A tag `last-isabelle2024-support` also exists.

Recommended fix: 1. Replace decision 9 with the editor's relaxation, corrected to 0.4.0. Before step 1 of §5 (the refactor), cut one final `my-better-isabelle-prover` 0.4.0 from today's pre-refactor HEAD. That release keeps the user/dev categories and the user-only default, and is the supported tool for Isabelle2024 from then on. 0.4.0 rather than 0.3.x is required by RELEASE.md:44-47: compared with 0.3.0, it drops the user-category pide_control and perspective_eof_clamp on Isabelle2024.
2. `isabelle-patch-control` then carries no patches at all:
   - Delete `bundled/**` from plan:258.
   - Delete the Isabelle2024 switch at plan:221.
   - Change decision 1's "旧 PyPI 包不再发版" (plan:114) to "one final 0.4.0 for Isabelle2024, then frozen".
   - Add one README line that points Isabelle2024 users to it.
3. Reword §7 item 2 so the owner chooses between (a) this final old-tool release and (b) deleting Isabelle2024 support now. State explicitly that bundling the sets into the new tool would need a separate mode outside the chain, with a user-only default, which means re-creating the categories.
4. Add an acceptance step that builds nothing. Run the 0.4.0 wheel with the stub isabelle from tools/tests/stub-isabelle on a scratch copy of the Isabelle2024 target files. `status` must list the three features with their real states, and `patch --dry-run` must select only future_assign_interrupt.

**Judge: confirmed → owner_decides.** Replace decision 9. Propose to the owner one final my-better-isabelle-prover release cut from today's pre-refactor HEAD. It must be 0.4.0, not 0.3.x: compared with v0.3.0, HEAD drops pide_control and perspective_eof_clamp on Isabelle2024, and RELEASE.md's rule makes a behavioural break a MINOR bump. That release keeps the user/dev categories and the user-only default, and is the supported tool for Isabelle2024.
isabelle-patch-control then carries no patches:
- delete bundled/** (plan:258) and the Isabelle2024 switch (plan:221);
- change plan:114 accordingly;
- add one README line pointing Isabelle2024 users to 0.4.0.
Reword §7 item 2 with the alternatives. Say explicitly that bundling in the new tool, as written, makes status, apply and unapply exit 3 on Isabelle2024. Chaining the three sets instead would invent provenance and grow the default from one user patch to all three.
Add an acceptance step that builds nothing: run the 0.4.0 wheel against a scratch copy of the Isabelle2024 target files.

### C13 [major] Identifying built-in features by ISABELLE_ID, with k=0 as the fallback, will reverse a built-in feature on real builds

Section: §2.3 and §8 facts (plan:85-87, 315-316); decision 4 (plan:157-165); decision 2 (plan:122); §5 ordering (plan:278, 286)  ·  merged from: conda-conda-10, design-D9, consistency-C10, user-U12, landing-L7, design-D10

**Statement.** Decision 4 identifies the first k chain nodes in two ways: by a manifest file in new builds, and, for older builds, by looking up etc/ISABELLE_ID in a table LEGACY_BUILDS. If neither works it falls back to k=0 (plan:157-165). Three defects. (1) The plan's facts about the older cached build are wrong. §2.3 and §8 say `isabelle-2025.2-89701cf1768e_0` has an empty ISABELLE_ID (plan:86, 316). I checked: the build has no `isa/` directory; its tree is `opt/Isabelle2025-2`, and its etc/ISABELLE_ID is `89701cf1768e`. That is the pristine Isabelle2025-2 changeset (ISABELLE_GIT_MIGRATION_PLAN.md:11-12). Its src/Pure/ML/ml_name_space.ML is byte-identical to the 2025.2-0 build's, so it carries expose_foreign. It came from a local file channel (info/repodata_record.json: file:///home/qiyuan/ci-work/channel/linux-64). ISABELLE_ID therefore cannot tell this build apart from the official tarball. k=0 would treat its built-in expose_foreign as tool-applied and reverse it on unapply, which is the very hazard migration §5.3 exists to prevent (ISABELLE_GIT_MIGRATION_PLAN.md:412-415). Decision 2's `$ISABELLE_HOME/../share/...` resolves to `$PREFIX/opt/share/...` there. (2) A more serious window: until step 5 the CI still pins 0.3.0 and applies expose_foreign (isabelle-packaging-ci/.github/workflows/build.yml:218-219, :253). Each run makes a fresh hg commit, and that commit becomes ISABELLE_ID (build.yml:292-300, :370-373). Any `isabelle` rebuild between step 1 and step 5, for example for an unrelated platform fix, yields a build that carries expose_foreign under an ID missing from LEGACY_BUILDS. Then k=0, and the pre-unlink of isabelle-expose-foreign, or a plain unapply, reverses it. That breaks Semantic_Embedding's SIMD FFI (README.md:66-67). The plan neither freezes `isabelle` releases in that window nor says who maintains LEGACY_BUILDS. (3) The tool never reads a built-in feature's files (plan:165), so it never verifies the claim. The old tool 0.3.0 reads conda's built-in expose_foreign as APPLIED (ISABELLE_GIT_MIGRATION_PLAN.md:600), and its `unpatch` defaults to all categories (reference.md:121). A plain `my-better-isabelle unpatch` on a conda env therefore removes the built-in feature, and the new tool would still print built-in and exit 0.

**Editor.** I verified the facts myself. The old build matters little: the critics report that the cached repodata for conda.qiyuan.me lists only isabelle-2025.2-0. The CI-rerun window in (2) is the real hazard. Some critics overreach. consistency-C10 proposes identifying old builds by a content check. Content can confirm that a feature is present, but it cannot by itself tell 'baked in by the build' from 'applied by the tool', because the bytes are identical; so it cannot replace the manifest. A content check is still worth adding, as a verification of a claimed built-in, as design-D10 proposes. The safe direction is to fail closed.

**Relaxation proposed by the editor.** Freeze `isabelle` releases from step 1 until the CI plan lands, and write that rule into isabelle-packaging-ci/RELEASE.md. LEGACY_BUILDS then has exactly one entry forever. Then fail closed: a tree inside a conda prefix that has neither the manifest nor a legacy entry is refused with exit 3 and the advice 'update isabelle'. k=0 is kept only for trees outside conda, such as the official tarball, where it is true.

**Defender: partially_confirmed** (needs owner: True).

I tried to refute each of the challenge's three parts.

Part (1): the plan's facts about the older build are wrong, but the build cannot actually be harmed.
- The facts are wrong. The plan says `isabelle-2025.2-89701cf1768e_0` has an empty ISABELLE_ID (plan:86, :316). In reality:
  - The tree is `pkgs/isabelle-2025.2-89701cf1768e_0/opt/Isabelle2025-2`. There is no `isa/` directory, and `bin/isabelle` points to `../opt/Isabelle2025-2/bin/isabelle`.
  - Its `etc/ISABELLE_ID` is `89701cf1768e` (12 bytes). That is the Isabelle2025-2 release changeset (ISABELLE_GIT_MIGRATION_PLAN.md:11-12, :29). The git pristine tree carries the same ID.
  - Its `src/Pure/ML/ml_name_space.ML` is byte-identical (`cmp`) to the one in the 2025.2-0 build. On both copies, `patch -R --dry-run` of tool 0.3.0's `expose_foreign/ml_name_space.ML.patch` succeeds, so both builds carry expose_foreign.
  - The plan most likely read `isa/etc/ISABELLE_ID`, which does not exist in this build.
  - ISABELLE_ID therefore cannot tell this build apart from the official tarball. Adding `89701cf1768e` to LEGACY_BUILDS would mark the official tarball's expose_foreign as built-in, which is false there.
- The consequence does not follow, for three reasons:
  - The build only ever came from a local file channel (`info/repodata_record.json`: `file:///home/qiyuan/ci-work/channel/linux-64`). The cached conda.qiyuan.me repodata (`pkgs/cache/3013e91f`) lists only `isabelle-2025.2-0.conda`. No environment has it installed (envs isabelle, isabelle-2, py313, smoke and base all checked).
  - With the `opt/` layout, decision 2's default `$ISABELLE_HOME/../share/...` (plan:122) resolves to `$PREFIX/opt/share/...`, so the tool would find no feature packages.
  - Decision 8's post-link passes `--isabelle-bin "$PREFIX/isa/bin/isabelle"` (plan:202). That path does not exist in this build, so the hook fails with exit 2 (plan:273) and conda rolls back.
- So the reversal can only happen if someone deliberately points `--features-dir` at it. What survives of part (1) is the factual error in §2.3/§8, plus the general lesson that ISABELLE_ID is not a unique key.

Part (2), the rebuild window: confirmed. This is the real hazard.
- Until the CI plan lands, CI pins 0.3.0 and applies `--category user`, which is expose_foreign (build.yml:218-219, :253). It then runs `hg commit -u ci -m ...` with no `-d` (build.yml:296-300) and asserts ISABELLE_ID == that commit (build.yml:370-373).
- I checked with hg 6.7.2 that the commit hash differs on every run: the same base and the same content gave patched=3843319a7ed0 on one run and 2c98c06993b0 on the next. The hash includes the commit date.
- So any `isabelle` rebuild before step 5 (plan:286) produces a build that carries expose_foreign under an ID missing from LEGACY_BUILDS (plan:163). Decision 4 then gives k=0 (plan:164).
- With k=0, decision 3's `unapply` reverses every applied feature that is not built-in. With no `--feature` it removes all of them (plan:150-151). So expose_foreign gets reversed, either by a plain `unapply` or by the pre-unlink of `isabelle-expose-foreign` (plan:202-203). That breaks Semantic_Embedding's FFI (tool README.md:66-67; simd_vector.ML:68,76 use `Foreign`). This is exactly the case migration §5.3 was written to prevent (ISABELLE_GIT_MIGRATION_PLAN.md:412-415).
- Nothing in the plan closes this window:
  - Feature packages depend on `isabelle` "any version" (plan:197-198).
  - `run_constrained` exists only in new builds (plan:245-247).
  - The CI's own release rule invites rebuilds ("bump build_number", isabelle-packaging-ci/RELEASE.md:14-26).
  - Plan:164 says the table "only grows", but names no owner. A new entry would need a tool release, and installed 1.0.0 tools would never see it. That relies on people remembering, which the review criteria count as a defect.
- My prototype reproduces this with the real patch: on a copy with ID 3843319a7ed0, `unapply` reverses expose_foreign, which then reads not-applied.

Part (3), built-in claims are never checked: confirmed, but minor.
- Plan:165 says the tool never reads a built-in feature's patch files.
- Tool 0.3.0 reads conda's built-in expose_foreign as APPLIED (ISABELLE_GIT_MIGRATION_PLAN.md:600), and its `unpatch` defaults to `--category all` (reference.md:121-122; cli.py:157). So a leftover 0.3.0 install can strip the built-in feature, and the new tool will still print `built-in` and exit 0. My prototype's scenario D shows this.
- The reversal itself is caused by the old tool, not by the plan. The plan's own gap is only that it reports a claim it never checked.

The editor's relaxation, on its merits:
- Freezing `isabelle` releases until step 5 closes part (2) without changing any ruling. LEGACY_BUILDS then really has one entry forever. But a freeze is a process rule that people must remember.
- Failing closed inside a conda prefix (exit 3) makes the hazard impossible regardless of the freeze. It also fits decision 8: a non-zero post-link rolls the install back. However, it changes the approved interface. Migration §5.3 says unidentified builds get k=0 (ISABELLE_GIT_MIGRATION_PLAN.md:414-415), and this plan's §0 item 10 lists that as fixed (plan:38-40). So only the owner can adopt it.
- The relaxation's test for "inside conda", `$ISABELLE_HOME/../conda-meta`, would misclassify the old `opt/` build as outside conda. That does not matter because that build is unsupported.
- The editor says file content alone cannot tell "baked in by the build" from "applied by the tool". That is only partly right. `conda-meta/isabelle-2025.2-0.json` `paths_data` records the shipped sha256 of every file; for `isa/src/Pure/ML/ml_name_space.ML` it is a06c3422…, which equals the file in the environment. A file that still matches the package's record, and on which the patch reads applied, was baked in, as long as no later feature touched that file. That is a third way to identify built-in features beyond the two in §5.3, so it is an option to offer the owner, not part of the smallest fix.
- A check of claimed built-in features (the challenge's design-D10) fixes part (3) but not part (2). On a rebuilt build the feature reads applied either way.

Overall: part (2) is confirmed and is the major problem, part (3) is confirmed and minor, and part (1) is a real factual error whose claimed consequence is refuted. Hence partially confirmed.

Experiment: All experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C13/.
(a) Inspected both cached builds:
  - `isabelle-2025.2-0`: ISABELLE_ID = 5533cd83156e, channel https://conda.qiyuan.me.
  - `isabelle-2025.2-89701cf1768e_0`: tree at opt/Isabelle2025-2, no isa/, ISABELLE_ID = 89701cf1768e, channel file:///home/qiyuan/ci-work/channel, and its etc/settings has no conda suffix.
  - `cmp` shows the two builds' ml_name_space.ML are identical. `patch -R --dry-run` of the 0.3.0 expose_foreign patch succeeds on copies from both builds. The old build's future.ML equals pristine.
(b) Mapped the cached repodata: conda.qiyuan.me lists only isabelle-2025.2-0. The old build appears only in the local file channel. No environment has it installed.
(c) hg/ (hg 6.7.2): two runs of an identical base plus identical patched content, each committed with `hg commit -u ci -m "our patches ..."`, gave different hashes (3843319a7ed0 and 2c98c06993b0). So every CI rerun produces a new ISABELLE_ID.
(d) proto/sim.py: models plan decision 4 (manifest, then LEGACY_BUILDS, else k=0) and decision 3's unapply, using GNU patch and the real 0.3.0 patch on copies of the shipped ml_name_space.ML. Results:
  - A: ID 5533cd83156e: skipped as built-in.
  - B: rebuild ID: expose_foreign REVERSED.
  - C: ID 89701cf1768e: REVERSED. This needs a manual --features-dir; the default paths do not reach that build.
  - B': fail-closed variant: exit 3.
  - D: manifest present but file reverted by a 0.3.0-style unpatch: still reported as built-in.
  - D': with verification of built-in features: exit 3.
(e) conda-meta/isabelle-2025.2-0.json paths_data records sha256 a06c3422… for isa/src/Pure/ML/ml_name_space.ML, which equals the file in the environment.

Recommended fix: 1. In §2.3 (plan:85-87) and §8 (plan:315-316), correct the facts about the older build. Its tree is `opt/Isabelle2025-2`. Its ISABELLE_ID is `89701cf1768e`, the release changeset, the same as the official tarball. It carries expose_foreign. It came only from the local file channel and is installed nowhere. Declare it unsupported, and state that its ID must never enter LEGACY_BUILDS.
2. Add a precondition to §5: no `isabelle` package is published from now until step 5's first build that carries `etc/ISABELLE_BUILT_IN_FEATURES`. Record this rule in isabelle-packaging-ci/RELEASE.md §2. In decision 4 (plan:164), replace "the table only grows" with "LEGACY_BUILDS has exactly one entry, 5533cd83156e, and never grows".
3. In decision 4 (plan:165), "built-in" should mean only "never apply, never reverse". Whenever a built-in feature's directory is present, still compute its state with the same dry-run and the same covered logic. If a built-in feature reads not-applied, or reads CONFLICT with no later applied feature to explain it, exit 3 with "built-in feature X is missing from this Isabelle; reinstall isabelle". Add a README line telling users to uninstall `my-better-isabelle-prover` before using the new tool on a conda Isabelle.
4. Add a §7 question for the owner: should the "unidentified build means k=0" fallback (migration §5.3, this plan's §0 item 10) become "refuse with exit 3" for trees inside a conda prefix, keeping k=0 outside conda? A tree is inside a conda prefix when a `conda-meta/isabelle-*.json` record owns its `etc/ISABELLE_ID`. If the owner agrees, the hazard becomes structurally impossible and the freeze in item 2 becomes a convenience rather than a safety rule.

**Judge: partially_confirmed → owner_decides.** Correct the facts in §2.3 and §8 about isabelle-2025.2-89701cf1768e_0:
- its tree is opt/Isabelle2025-2, with no isa/;
- its ISABELLE_ID is 89701cf1768e, the release changeset;
- it carries expose_foreign;
- it came only from a local file channel and is installed nowhere.
Declare it unsupported, and state that its ID never enters LEGACY_BUILDS. The harm claimed for this build is refuted.
The CI-rerun window is the real hazard. Every CI run makes a new hg commit, and therefore a new ISABELLE_ID (build.yml:296-300, 370-373). Put to the owner:
- (a) a freeze on publishing `isabelle` until the first build that carries the manifest, recorded in isabelle-packaging-ci/RELEASE.md;
- (b) refusing with exit 3 ("update isabelle") a tree inside a conda prefix that has neither the manifest nor a legacy entry. This changes migration §5.3's "unidentified means k=0".
Verify claimed built-in features: if a built-in feature's directory is present and its files do not read applied, exit 3 with "built-in feature X is missing; reinstall isabelle". Optionally use the conda-meta paths_data sha256 as the evidence that a file is still as the build shipped it. Add a README warning against using 0.x's bare `unpatch` on conda trees.

### C14 [major] The tool finds its tree through `isabelle` on PATH and Isabelle's settings machinery; the hooks do not need this, (b2) contradicts itself, and the shared git tree is unguarded

Section: Terminology (plan:19); decision 2 (plan:122-125); decision 5 (plan:169-174); §4 (plan:263); §5 step 3 and §6 (plan:281-282, 294-295)  ·  merged from: conda-conda-11, landing-L10, consistency-C17, consistency-C20

**Statement.** The tool finds its target through `shutil.which("isabelle")` or --isabelle-bin. It then runs `isabelle version` and `isabelle getenv -b ISABELLE_HOME` (isabelle.py:12-55; plan:19, 66-67, 263). This causes five problems. (1) The hooks already know ISABELLE_HOME, which is $PREFIX/isa, yet they run Isabelle's whole settings machinery, including the user's own settings. A broken user .bash_profile can make getenv fail (isabelle-packaging-ci/conda/recipe.yaml:144-146). On Windows, the first `isabelle` call cannot run a Scala tool (Isabelle_RPC/conda/recipe.yaml:160-165). (2) Run by hand, the tool's tree is whichever `isabelle` PATH finds first. The plan derives features.d from ISABELLE_HOME rather than CONDA_PREFIX because the user may not have activated the env (plan:122-125). But which() reads PATH, and PATH is exactly what activation sets. (3) In this workspace, `which isabelle` is /home/qiyuan/Current/MLML/contrib/Isabelle2025-2/bin/isabelle, the shared tree. After the migration, that tree may change only through advance-daily (ISABELLE_GIT_MIGRATION_PLAN.md:543, rule 13), and any other tree may be run only through run-tree (rule 9, :535-536). With --features-dir, apply would write the shared tree, and nothing refuses. (4) When the tool is called from a process that Isabelle started, the inherited ISABELLE_SETTINGS_PRESENT makes getsettings skip everything (isa/lib/scripts/getsettings:13-16). `isabelle version` then reflects the outer process. (5) The plan contradicts itself on (b2). Decision 5 says (b2) switches to the directory interface (plan:173), which by definition ignores the chain and the built-in manifest (plan:170-171). But (b2) copy A exists precisely to test chain order and the first k nodes (ISABELLE_GIT_MIGRATION_PLAN.md:392-396). So §5 step 3 and §6 actually run the chain-aware apply with LEGACY_BUILDS (plan:281-282, 294-295), and that apply calls `isabelle`. Migration §5.3 says that (c) and (b2) use an interface that does not call `isabelle` (:416-417). §6 also omits a check that migration §5.1 requires on the first (b2) run: that status shows the real target paths of created files (:395-396).

**Editor.** Valid. The guard in (3) is cheap and makes a workspace rule impossible to break. Point (4) is niche. The plan's choice to place features.d relative to ISABELLE_HOME is fine. What is wrong is how it finds ISABELLE_HOME.

**Relaxation proposed by the editor.** Add `--isabelle-home DIR`. With it, the tool reads the release and the build identity from files (etc/ISABELLE_IDENTIFIER, which holds 'Isabelle2025-2' in the conda tree; etc/ISABELLE_ID; the manifest) and never runs `isabelle`. When the tool itself runs from a conda env (sys.prefix/conda-meta and sys.prefix/isa both exist), default to sys.prefix/isa. Hooks pass "$PREFIX/isa" explicitly. (b2) copy A runs the full chain-aware apply with --isabelle-home. apply and unapply refuse a tree whose ISABELLE_HOME contains `.git`. No code path then depends on PATH or on Isabelle's settings machinery.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the five points. Four hold, and my experiments made them stronger. One supporting detail in point (1) is wrong, and the relaxation's closing sentence claims a little too much. The severity stays major.

How the plan locates the tree. The plan defines "the user's Isabelle" through `isabelle getenv -b ISABELLE_HOME` (plan:19) and keeps `--isabelle-bin` (plan:263). The current code finds the binary with `shutil.which("isabelle")` (isabelle.py:19), then runs `isabelle version` (isabelle.py:30-39) and `isabelle getenv` (isabelle.py:42-55). Both calls use check=True and exit 1 on a non-zero status. Two other things the plan needs are already read from files: the built-in manifest (plan:157) and etc/ISABELLE_ID (plan:163). `isabelle` is used only to learn the tree root and the release name. The release name drives decision 9 (plan:220-221).

(1) Confirmed for Linux, with one sub-claim refuted.
- The hook already passes `$PREFIX/isa/bin/isabelle` (plan:202). The tool then asks Isabelle's settings machinery to work out a path the hook already knew.
- getsettings sources the user's own settings: `init_component "$ISABELLE_HOME_USER"` (pkgs/isabelle-2025.2-0/isa/lib/scripts/getsettings:89-90).
- Experiment: I put a syntax error in a toy user settings file. `isabelle getenv -b ISABELLE_HOME` then exited 2 and printed nothing on stdout; `exit 1` in the file gave exit 1.
- Under decision 8 (plan:206), that failure would make every post-link fail and conda would roll back the install.
- On Windows, a broken .bash_profile can make getenv exit non-zero even when it prints the right answer (isabelle-packaging-ci/conda/recipe.yaml:144-146). check=True turns that into a failure.
- REFUTED: the Windows "first call cannot run a Scala tool" problem (Isabelle_RPC/conda/recipe.yaml:160-165) does not reach the tool. lib/Tools/version and lib/Tools/getenv are bash scripts. bin/isabelle runs shell tools at :25-43, before it reaches scala_build at :48.
- Plausible but not tested: plan:202-203 hands the Windows hook the bash script `isa/bin/isabelle`, and native Windows Python cannot start a bash script through subprocess.

(2) Confirmed.
- plan:122-125 says features.d is derived from ISABELLE_HOME and not from CONDA_PREFIX because the user may not have activated the env (CONDA_ISABELLE_BRIDGE.md:121-127).
- The bridge's own measurement (CONDA_ISABELLE_BRIDGE.md:192) shows that activation changes only CONDA_PREFIX and PATH. which() reads PATH.
- Experiment: I ran envs/isabelle/bin/python with the env not activated and this workspace's PATH. `shutil.which('isabelle')` returned contrib/Isabelle2025-2/bin/isabelle, which is the shared tree. sys.prefix/isa was the env's own tree.

(3) Confirmed.
- `which -a isabelle` gives only the shared tree. That tree has a `.git` directory, and RECORD.md:54-55 says its HEAD is Isabelle2025-2/daily.
- Sessions were told "do not edit the shared tree" (RECORD.md:88-89). Rule 13 is at migration :543; rule 9 is at :535-536.
- The danger is concrete in (b2), the workflow that passes --features-dir. Take (b2) for future_assign_interrupt and suppose --isabelle-bin is forgotten. The shared tree's ISABELLE_ID is 89701cf1768e, which is not in LEGACY_BUILDS, so k=0. Both features read as applied, and `unapply` (plan:150) would reverse future.ML and the expose_foreign files in the shared tree. Nothing in the plan refuses this.
- Private and stock trees have a `.git` FILE; the shared tree has a `.git` directory. Any guard must test existence, not is_dir.

(4) Confirmed by experiment; it is niche.
- I ran an inner toy tree's bin/isabelle inside an outer toy tree's `isabelle env`. `version` printed the OUTER "Isabelle2024", and ISABELLE_HOME_USER was the outer one.
- ISABELLE_HOME was correct, because bin/isabelle:19 recomputes it.
- The cause is getsettings:13 and :71, the same hazard run-tree's own docstring names (run-tree:10-12).
- Consequence: decision 9 could mix the bundled Isabelle2024 sets into a 2025-2 tree.

(5) Confirmed.
- plan:173 sends (b2) to `apply-to`. That command ignores the manifest and every other feature (plan:170-171).
- plan:281-282 and plan:294-295 instead run the chain-aware apply and unapply, using LEGACY_BUILDS.
- Migration §5.1 requires chain order and recognition of the first k features for copy A (:392-394). Migration §5.3 requires an interface for (b2) that does not call isabelle (:416-417). Only a chain-aware path that does not call isabelle satisfies both.
- Rule 9 (:535-536) forbids calling bin/isabelle of copy A directly, and forbids tools that find `isabelle` on their own. run-tree refuses anything that is not a worktree (run-tree:34-58). So the plan's (b2) cannot comply as written.
- Calling copy A's getenv has a side effect: it creates ~/.isabelle/Isabelle2025-2-conda-<parent dir name> (getsettings:89-93 plus etc/settings:98; seen in my experiment). A leftover ~/.isabelle/Isabelle2025-2-conda-isabelle-2025.2-0 already exists on this machine.
- §6 also omits the check migration :395-396 requires on the first (b2) run: that `status` shows the real target paths of created files.

The relaxation, on its merits.
- It is sound and elegant. My prototype resolves the env's tree without activation and reads identity ('Isabelle2025-2', '5533cd83156e') from files. It reads 'Isabelle2024' from contrib/Isabelle2024. It refuses both the shared tree and the light_locale private tree.
- Using sys.prefix follows the same principle as the bridge's "component-relative path" (CONDA_ISABELLE_BRIDGE.md:124).
- The tests no longer need a fake bin/isabelle (plan:253-254).
- Corrections to the relaxation:
  - `patch` is still looked up on PATH (patcher.py:22-25). "No code path depends on PATH" is true only of the target tree.
  - It must not fall back to the ISABELLE_HOME environment variable. getsettings:7 exports it, so inside an Isabelle-spawned process it names the outer tree.
  - The `.git` guard belongs in the single function that writes files, so apply-to and unapply-from are covered too. Gate (c) works in a git-archive directory with no `.git` (make-patches:175-183), and CI works in an hg checkout, so neither is blocked.
  - The message at plan:152-153 cannot print ISABELLE_HOME_USER without running Isabelle. It should point to `isabelle getenv ISABELLE_HOME_USER` instead.

Incidental finding: plan:85-86 and :316 say the older build isabelle-2025.2-89701cf1768e_0 has an empty ISABELLE_ID. In fact it uses the layout opt/Isabelle2025-2, and its etc/ISABELLE_ID is 89701cf1768e. It has no isa/ directory.

Experiment: All work was in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C14/.

(a) exp1/: I copied bin/, lib/scripts/, etc/ and lib/Tools/{getenv,version,env} of pkgs/isabelle-2025.2-0/isa into exp1/isabelle/isa, and redirected HOME and USER_HOME into the scratch directory.
- Under `env -i`, getenv returned the right ISABELLE_HOME and version printed Isabelle2025-2.
- getenv also created exp1/home/.isabelle/Isabelle2025-2-conda-isabelle as a side effect.

(b) I put broken content in the toy user settings file at ISABELLE_HOME_USER/etc/settings.
- `FOO=$(` made getenv exit 2 with empty stdout.
- `exit 1` made it exit 1.
- `set -u` with an undefined variable made it exit 1.

(c) I made a second toy tree, outer/, whose ISABELLE_IDENTIFIER is Isabelle2024, and ran the inner tree's version and getenv inside `outer/isa/bin/isabelle env`.
- version printed "Isabelle2024".
- getenv gave the correct inner ISABELLE_HOME, but ISABELLE_HOME_USER was ~/.isabelle/Isabelle2024-conda-outer.

(d) I ran envs/isabelle/bin/python -I with no env activation and a PATH that includes the shared tree.
- shutil.which('isabelle') returned the shared tree.
- sys.prefix was envs/isabelle, which has conda-meta/ and isa/.

(e) proto/resolve.py: a file-only home resolver plus the `.git` guard.
- The sys.prefix default resolves envs/isabelle/isa with identity ('Isabelle2025-2', '5533cd83156e').
- The shared tree (`.git` directory) and the light_locale private tree (`.git` file) are refused.
- pkgs/isabelle-2025.2-0/isa is accepted.
- contrib/Isabelle2024 is read as 'Isabelle2024'.
- System python outside any conda env refuses with no default.

(f) Read-only checks.
- lib/Tools/version and lib/Tools/getenv are bash scripts, so no scala_build runs.
- Private and stock trees have a `.git` file.
- Shared tree etc/ISABELLE_ID is 89701cf1768e.
- The old build pkgs/isabelle-2025.2-89701cf1768e_0 is laid out as opt/Isabelle2025-2, with ISABELLE_ID 89701cf1768e.
- ~/.isabelle/ already contains Isabelle2025-2-conda-isabelle-2025.2-0.

I never ran any `isabelle` command of a real tree.

Recommended fix: 1. Terminology (plan:19) and §4 (plan:263): replace `--isabelle-bin` with `--isabelle-home DIR`.
   - Default: sys.prefix/isa, used only when both sys.prefix/conda-meta and sys.prefix/isa exist. Otherwise refuse (exit 2) and suggest `--isabelle-home "$(isabelle getenv -b ISABELLE_HOME)"`.
   - Never use which(), and never use the ISABELLE_HOME environment variable.
   - Read the release from DIR/etc/ISABELLE_IDENTIFIER. Decision 9's "isabelle version is Isabelle2024" becomes "that file says Isabelle2024".
   - Build identity stays as planned: etc/ISABELLE_ID plus the manifest.
   - The tool never runs `isabelle`, so the decision 12 tests need only a toy tree, not a fake bin/isabelle.
2. Decision 8 hooks (plan:202-203): pass `--isabelle-home "$PREFIX/isa"` (on Windows, `"%PREFIX%\isa"`).
3. Decision 5 (plan:173): only gate (c) uses `apply-to`.
   - (b2) copy A runs `isabelle-patch-control --isabelle-home <copyA>/isa --features-dir <dir> apply --feature <f>`, then `unapply`.
   - This meets migration §5.1 (:392-394), §5.3 (:416-417) and rule 9 (:535-536), because no bin/isabelle of the copy ever runs.
   - Optional: refuse `--features-dir` given without `--isabelle-home`, so the features and the tree come either both from the defaults or both from explicit flags.
4. §6 (plan:294-295): add the migration :395-396 check. On the first (b2) run, `status` must show the real target paths of the created files.
5. Guard, placed in the single function that writes files (used by apply, unapply, apply-to and unapply-from): refuse a tree for which `(home/".git").exists()`. That is true of a directory in the shared tree and of a file in private and stock trees. Error text: "a git working tree changes only through git".
6. plan:152-153: do not print a computed ISABELLE_HOME_USER. Name the command `isabelle getenv ISABELLE_HOME_USER` instead.
7. Incidental: correct plan:85-86 and :316. The old build is laid out as opt/Isabelle2025-2, and its ISABELLE_ID is 89701cf1768e, not empty.

**Judge: partially_confirmed → author_decides_then_rereview.** Replace `--isabelle-bin` with `--isabelle-home DIR`.
- The default is sys.prefix/isa, used only when both sys.prefix/conda-meta and sys.prefix/isa exist. Otherwise refuse with exit 2 and suggest the flag.
- Never use which(), and never read the ISABELLE_HOME environment variable.
- Read the release from DIR/etc/ISABELLE_IDENTIFIER and the build identity from etc/ISABELLE_ID and the manifest. The tool never runs `isabelle`, so the tests need only a toy tree, not a fake bin/isabelle.
- Hooks pass `--isabelle-home "$PREFIX/isa"`.
- (b2) copy A runs the chain-aware apply and unapply with --isabelle-home and --features-dir. This satisfies migration §5.1 (:392-394), §5.3 (:416-417) and rule 9 (:535-536). Note in the plan that §5.3's "(b2) uses the directory interface" is read as "(b2) uses an interface that does not call isabelle".
- The single writer routine refuses a tree where (home/'.git').exists(). That catches both the shared tree's .git directory and the .git file of private and stock trees.
- The heap notice names the command `isabelle getenv ISABELLE_HOME_USER` instead of printing a computed path.
- Add migration :395-396's check to §6: on the first (b2) run, status shows the real target paths of created files.
Refuted part: the Windows Scala-tool sub-claim does not reach the tool (version and getenv are bash scripts).

### C15 [major] Feature packages are noarch and install on all five platforms, but the Windows hook is described wrongly, and GNU patch is an unmanaged machine dependency

Section: Decision 8 Windows hook and dependencies (plan:196-198, 203-204); decision 6; §6  ·  merged from: conda-conda-7, consistency-C12, landing-L9, user-U7

**Statement.** Feature packages are noarch generic (plan:196), so they install on every platform the `isabelle` package is published for: linux-64, linux-aarch64, osx-64, osx-arm64 and win-64. Decision 8 says the Windows .bat runs 'the same command' through `isa\contrib\cygwin\bin\bash`, 'consistent with isabelle-rpc's .bat' (plan:203-204). Every part of that is wrong. (a) The published .bat hooks never call Cygwin bash. They call `%PREFIX%\isa\bin\isabelle.bat` after a throwaway getenv warm-up, convert paths to /cygdrive form, and end with `exit /b 0` (Isabelle_RPC/conda/recipe.yaml:160-176; Semantic_Embedding/conda/recipe.yaml:276-288). (b) The command does not exist on Windows at that path. A noarch python entry point lands in Scripts\, not bin/ (Isabelle_RPC recipe.yaml:49-52). And `--isabelle-bin $PREFIX/isa/bin/isabelle` names a bash script, which subprocess.run from native Windows Python cannot execute (isabelle.py:32-35, 44-47; isabelle-packaging-ci/conda/recipe.yaml:89-98). (c) On Windows, `isabelle getenv` returns /cygdrive paths (recipe.yaml:144-147), which pathlib cannot use. (d) The tool runs whatever `patch` is first on PATH (patcher.py:22-25). Isabelle's Cygwin component requests only curl, libgmp-devel, nano, openssh and perl (contrib/Isabelle2025-2/src/Pure/Admin/component_cygwin.scala:13). macOS's system patch has never been measured against these flags and headers; the GNU patch 2.7.6 tests ran on Linux only (ISABELLE_GIT_MIGRATION_PLAN.md:620-621, 629). (e) Conda picks hook files by the running platform and silently succeeds when a file is absent. So a noarch package must ship both hook sets unconditionally, and copying the `isabelle` recipe's `case $target_platform` would silently drop the Windows hooks (Isabelle_RPC recipe.yaml:142-145; RELEASE_CHECKLIST.md:255-258). With decision 8's non-zero exit, any platform where the hook cannot run makes the package uninstallable there, with C2's leftovers. GNU patch exists as conda packages: conda-forge `patch` 2.8 for the unix subdirs, and `m2-patch` 2.7.6.3 for win-64 (per the critics' repodata checks). §6 has no leg on any platform other than Linux.

**Editor.** Correct; I checked the consumer recipes myself. D4 item 10 put exactly these platform points to the owner (LIGHT_LOCALE_HANDOFF.md:1979), and the plan skipped them.

**Relaxation proposed by the editor.** Until a platform has passed acceptance, keep feature packages off it with a virtual-package dependency: `__linux` now, `__unix` once macOS passes. Make the tool's conda package depend on a known GNU patch (conda-forge `patch` on unix, `m2-patch` on Windows), and call it by absolute path from $PREFIX. A Windows leg is then added deliberately, with a windows-latest run, instead of being described by analogy.

**Defender: confirmed** (needs owner: True).

I tried to refute the challenge and could not. All three claims in its title hold. Two side remarks need correcting, and for macOS the risk is worse than the challenge says.

1. Feature packages would install on all five platforms. Decision 8 makes them noarch generic (plan:196). Their dependencies are `isabelle-patch-control >=1.0` (noarch python) and `isabelle` at any version (plan:197-198). conda adds the noarch subdir to every platform's solve (conda/base/context.py:719-720). `isabelle` is published for linux-64, linux-aarch64, osx-64, osx-arm64 and win-64 (isabelle-packaging-ci build.yml:937-941). The plan never limits the platforms. Its only mentions of Windows are plan:84, 90 and 203-204, and it never mentions macOS.

2. The Windows hook is described wrongly (plan:203-204).
(a) The published consumer .bat hooks do not start Cygwin bash themselves. They set the component path, convert it to /cygdrive form, do a throwaway `getenv` warm-up, call `isa\bin\isabelle.bat`, and end with `exit /b 0` (Isabelle_RPC/conda/recipe.yaml:160-176; Semantic_Embedding/conda/recipe.yaml:276-288). Cygwin bash appears only inside isabelle.bat (isabelle-packaging-ci/windows/isabelle.bat:55,83), and it is needed there only because `isabelle` is a bash script. So "consistent with isabelle-rpc's .bat" is false on every point except the file name, and the plan's non-zero exit is the opposite of their `exit /b 0`.
(b) "The same command" does not exist on Windows. conda puts noarch python entry points in Scripts\ as `<cmd>-script.py` plus an `.exe` (conda/common/path/__init__.py:139; core/path_actions.py:810-815), so `$PREFIX/bin/isabelle-patch-control` is not there. `--isabelle-bin $PREFIX/isa/bin/isabelle` names the unix launcher, which is a bash script. RELEASE_CHECKLIST.md:302-304 says outright that the Windows entry point is `Scripts/isabelle.bat`, "not <prefix>/isa/bin/isabelle". Native Windows Python's `subprocess.run([isa_bin, ...])` (isabelle.py:32-35, 44-47) cannot execute a bash script.
(c) `isabelle getenv` returns /cygdrive paths on Windows (isabelle recipe.yaml:144-147; RELEASE_CHECKLIST.md:305). `PureWindowsPath('/cygdrive/c/...')` has no drive letter, so it means `C:\cygdrive\c\...` on the current drive. `is_dir()` is then false and isabelle.py:51-54 exits 1. The default features directory (plan:122) is derived from the same wrong path.

3. GNU patch is a machine dependency nobody manages. patcher.py:22-25 only checks that some `patch` is on PATH, then runs it (:31, :37, :83). make-patches:66 does the same. Isabelle's Cygwin component asks for only five packages (component_cygwin.scala:13, 44). In Cygwin's own package index, `patch` is in the Devel category, and the dependency closure of Base plus those five (148 packages) does not include it (experiment). The GNU patch measurements were Linux-only, with 2.7.6 (ISABELLE_GIT_MIGRATION_PLAN.md:620-621, 629).

On macOS it is worse than "unmeasured". I compiled FreeBSD's patch (`patch 2.0-12u11 FreeBSD`) and measured three things:
- It rejects `--no-backup-if-mismatch` (the flag decision 5 uses).
- When the tool's rule (patcher.py:28-42) asks "does the patch reverse-apply?" on an UNPATCHED tree, every patch says yes, so every patch reads as applied. The cause is that `patch -R --dry-run` notices the patch is not applied yet, answers its own "Ignore -R? [y]" prompt with the default "yes", and exits 0 (FreeBSD patch.c:328-336, and util.c:286-290 when there is no terminal). The plan's `apply` would then skip everything, the hook would exit 0, and `status` would report the feature as applied when nothing was patched.
- In a terminal session (simulated with a pty) with output captured, as the tool does, the check blocks on /dev/tty waiting for an answer nobody can see. GNU 2.7.6 and 2.8 return at once, because GNU patch opens /dev/tty only when stdout is a terminal.

Apple's published patch_cmds source has the same prompt logic and the same terminal-reading code (patch.c:495-501, util.c:338-346), but it does accept `--no-backup-if-mismatch` (patch.c:836-838). I did not check on a Mac which binary a given macOS release ships.

4. The plan also contradicts itself. §0 item 9 (plan:36-37) promises to set out the deferred tool-level list ("D4") point by point in §7. Item (10) of that list is exactly this platform question: Windows has no GNU patch, getenv gives cygdrive paths, the .bat hooks (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979). An earlier reader's report gave the same finding and fix, and left the platform-scope question to the owner (readers_impl0/reader2_patch_scheme.md:167-174, 221). §7 item 6 (plan:307-309) answers only some of the items and leaves out (10). The Windows path-length question that the migration plan §9 handed to this plan (ISABELLE_GIT_MIGRATION_PLAN.md:569-572) is not answered either. §6 (plan:290-298) tests only on this Linux machine.

Corrections to the challenge:
- (e) conda does pick the hook file by running platform and does treat a missing hook as success (core/link.py:1558-1564). But the plan does not propose copying the `case $target_platform` guard; it names the .bat explicitly. That part is a warning, not a defect in the plan.
- "Uninstallable with leftovers" is wrong for Windows. There the tool fails before touching any file (isabelle.py:51-54 or patcher.py:22-25), so conda rolls back cleanly. On macOS, by the measurements above, the outcome is a hang or a silent no-op, not a failed install.

The editor's relaxation, on its merits:
- A virtual-package dependency is the right shape. conda exports `__linux` only on linux-* and `__unix` on linux-* and osx-* (plugins/virtual_packages/linux.py:47-61, osx.py:31-33). It belongs on the tool's own conda package, not in each feature recipe. Every feature package already depends on the tool (plan:197), so it inherits the limit, and a new feature recipe cannot forget it. With it in place, no .bat is needed, so the missing-hook trap and the Windows path-length question go away until a Windows leg exists. linux-aarch64 uses the same mechanism (a bash hook plus conda-forge patch for aarch64), so `__linux` is acceptable for it.
- Depending on conda-forge `patch` is sound. It exists for linux-64, linux-aarch64, osx-64 and osx-arm64 at version 2.8. In my toy round trip 2.8 behaved exactly like the 2.7.6 that was tested. conda-forge is already a required channel for anything with Python dependencies (RELEASE_CHECKLIST.md:298).
- `m2-patch` is premature. Its 2.7.6.3 build is noarch and depends on m2-msys2-runtime and m2-conda-epoch, which exist only on Windows; the win-64 subdir itself holds only 2.7.5. Leave it out until a Windows leg exists.
- "Call it by absolute path from $PREFIX" is unnecessary for the hooks. conda puts `$PREFIX/bin` first on PATH for every link script (core/link.py:1638) and activates the environment for post-link (link.py:1109-1114).
- What the relaxation lacks is a check that the `patch` found is GNU patch. The plan's status rule depends on GNU patch's default answer of "no", which BSD-derived patches invert. A conda dependency does not cover installs from PyPI, use with `--features-dir`, or make-patches calling the directory interface.

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C15/.

(1) scripts/roundtrip.sh builds a toy git repo. Its feature modifies a file, edits an executable, creates a new executable, creates a new file and deletes one. The script writes one `git diff-tree -p` patch per file, as make-patches does, then for a given patch binary it checks status with the tool's rule (reverse dry-run, then forward dry-run), applies forward with `-p1 -F0 --no-backup-if-mismatch`, compares content and mode with the git tree, reverses, and compares again.
- GNU patch 2.7.6 (/usr/bin) and conda-forge GNU patch 2.8 (extracted into patch28/): identical results. Status is right before and after; forward equals the feature tree and reverse equals the base tree, modes included; no .orig/.rej files left.
- FreeBSD patch 2.0-12u11, compiled in bsdpatch-build/ with three small porting fixes: `--no-backup-if-mismatch` is rejected as unrecognized, so every forward apply fails. On the unpatched tree all 5 patches read as "applied". Without that flag, the forward run leaves 5 .orig files, creates bin/new as 644 instead of 755, and leaves an empty d.ML instead of deleting it.

(2) scripts/status_in_pty.py runs the tool's reverse dry-run with captured output inside a pty (`sleep 8 | timeout 6 script ...`). GNU 2.7.6 and 2.8 return rc 1 immediately (correct). FreeBSD patch blocks reading /dev/tty until killed at 6 s.

(3) I read FreeBSD and Apple (patch_cmds) patch sources from GitHub. Both handle a not-yet-applied patch under -R the same way: prompt default "yes", and default answer when there is no terminal. Apple's version accepts `--no-backup-if-mismatch`.

(4) scripts/cyg_closure.py over the current Cygwin setup.ini: `patch` is in category Devel, and it is not in the 148-package closure of Base plus curl, libgmp-devel, nano, openssh, perl. Isabelle's own mirror could not be reached; this used a public mirror.

(5) anaconda.org API: conda-forge `patch` 2.8 is available for linux-64, linux-aarch64, osx-64, osx-arm64, ppc64le and riscv64. `m2-patch` 2.7.6.3 is noarch and depends on m2-msys2-runtime and m2-conda-epoch (win-64/win-arm64 only); win-64 itself has only 2.7.5.

(6) `PureWindowsPath('/cygdrive/c/...')` has drive '' and means `C:\cygdrive\c\...`.

Recommended fix: 1. Decision 8: delete the Windows sentence (plan:203-204). In its place, say that feature packages ship only `bin/.<pkg>-post-link.sh` and `bin/.<pkg>-pre-unlink.sh` (no .bat), and that platforms are limited in exactly one place: the tool's own conda recipe gets `run: [python, __linux, patch >=2.7.6]` (conda-forge `patch`). Every feature package inherits this through its `isabelle-patch-control >=1.0` dependency (plan:197), so feature recipes never repeat it.

2. Decision 1 (tool code): replace the existence check at patcher.py:22-25 with an identity check. Run `patch --version` once, require the first line to start with `GNU patch`, and otherwise exit 2 with a message saying a non-GNU patch makes reverse dry-runs succeed on unpatched files. No absolute-path logic is needed: conda puts `$PREFIX/bin` first on PATH for both hooks (conda core/link.py:1638).

3. §7: add the missing question from the deferred tool-level list, item (10) (LIGHT_LOCALE_HANDOFF.md:1979), and fix §0 item 9's claim that every item is set out. The question to put to the owner: is 1.0 Linux-only (proposed)? macOS later = `__unix` plus an osx leg on the macos-14 runner. Windows later = a separate noarch variant with `__win` plus `m2-patch`, a windows-latest leg, and the path-length question from migration plan §9:571-572.

4. §6: state that acceptance covers linux-64 only, and run the real-environment leg with the conda-forge patch the package depends on (2.8), not /usr/bin/patch 2.7.6.

**Judge: confirmed → owner_decides.** Delete decision 8's Windows sentence (plan:203-204); it is wrong on every point. Put the platform limit in exactly one place, the tool's own conda recipe: `run: [python, __linux, patch >=2.7.6]` from conda-forge. Every feature package inherits it through its dependency on the tool, ships only the two .sh hooks, and ships no .bat.
Replace the existence check for `patch` (patcher.py:22-25) with an identity check: `patch --version` must report GNU patch 2.7 or later, otherwise exit 2. With BSD-derived patch, the reverse dry-run reads unpatched files as applied.
Add D4 item 10 to §7 as the platform question. State that §6 covers linux-64 only, using the conda-forge patch the package depends on.
Do not add m2-patch until a Windows leg exists. Absolute paths are unnecessary, because conda puts $PREFIX/bin first on PATH for hooks (link.py:1637).

### C16 [major] Decision 7's copy-and-rename step works around a leak that only the tool's own chmod causes

Section: Decision 7 (plan:185-190); §2.3 (plan:95-96); §8 (plan:313-314)  ·  merged from: conda-conda-8, design-D6, consistency-C13, landing-L15, user-U16

**Statement.** GNU patch always writes a new file and renames it over the target. The env's copy therefore always gets a new inode, and the other hard link keeps its content; plan:95-96 measures this itself. The only thing that leaks into the other link is the tool's own `chmod u+w` on the shared inode (patcher.py:45-56, 89-100). GNU patch 2.7.6 patches a read-only, hard-linked file without any chmod. I reproduced this in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/merge/t1. Before: both names on inode 5315350, links=2, mode 444. `patch -p1 -F0` printed 'File f is read-only; trying to patch anyway', rc=0. After: the cache file kept inode 5315350, mode 444 and its original content, now with links=1; the env file had a new inode, mode 444, and the patched content. Reversing with `--read-only=ignore` gave a byte-identical file without a warning. Decision 7 keeps the chmod and adds `cp -p` plus `mv -f` to repair its side effect (plan:187-188). That adds a window in which an interruption leaves an untracked temporary file in the tree. It also adds a second code path that gate (c) never exercises (make-patches:63-69 uses bare patch). Moreover, every file under isa/src in the published package is user-writable (find ... ! -perm -u=w gives 0, checked), so with the real package the chmod is a no-op and the measured leak cannot happen. The actual sharing is between envs: envs/isabelle and envs/isabelle-2 share inode 55605093 for ml_name_space.ML, while the cache copy is a separate inode (critic measurement). §6 never checks the sibling env. Decision 7 also misses symlinked targets under conda's always_softlink setting (conda/base/context.py:450): GNU patch refuses them with 'not a regular file'.

**Editor.** Five critics converged, and my own run confirms it. This is a workaround stacked on a workaround: the textbook case of a dirty hack the review criteria single out. Severity is major on elegance grounds. Nothing breaks today, but the extra step and the second code path are exactly the kind of thing people must remember.

**Relaxation proposed by the editor.** Delete `_make_writable`, `_restore_mode` and decision 7's copy step, and pass `--read-only=ignore`. 'The tool never writes through a shared inode' then holds by construction, because the only writer is GNU patch's write-and-rename. Keep a pytest post-condition: after apply, the target has nlink=1, and the other link's inode, mode and content are unchanged. Refuse symlinked targets with a clear message.

**Defender: confirmed** (needs owner: False).

I tried to refute the challenge and could not. Its main claim holds: decision 7's copy step exists only to undo a side effect of the tool's own `chmod`. GNU patch never writes through a shared inode.

1. GNU patch always writes a new file and renames it over the target. Under strace, patch 2.7.6 creates `f.oQfiold` (O_CREAT|O_EXCL) in the target's own directory, sets its mode with `fchmodat`, then calls `renameat` onto `f`. It never opens `f` for writing. A deletion patch only unlinks the env's name; the cache inode is untouched (experiment t4). The plan records the same fact itself (plan:95-96, plan:313-314).

2. The only write that reaches the other link is the tool's own `chmod`. `_make_writable` runs before patch, on the shared inode (patcher.py:45-51, 89-92). `_restore_mode` runs after patch, on the new inode (patcher.py:54-56, 98-100). Replaying that sequence, the cache file went from 444 to 644 while the env file stayed 444. That is exactly the leak in plan:313-314. Decision 7 keeps the `chmod` and the mode restore, and adds `cp -p` plus `mv -f` to repair the leak (plan:187-188). It removes the symptom, not the cause.

3. The `chmod` is not needed, even for read-only files. A file at mode 444 with links=3 (cache, env, env2) was patched with no `chmod` at all: rc=0, with the warning 'File f is read-only; trying to patch anyway'. The env file got a new inode and kept mode 444. Cache and env2 kept their inode, mode and content, and links dropped to 2. With `--read-only=ignore` the warning disappears and the reverse patch gives a byte-identical file. The tool's stated reason for the `chmod`, "Isabelle distribution files are often read-only" (develop.md:31-33, AGENTS.md:111-112, reference.md:100-101), is a real situation: the official tree contrib/Isabelle2025-2 has 2940 of 4720 src files without u+w. But GNU patch's default `--read-only=warn` handles those files anyway.

4. In the real conda package the `chmod` does nothing and the leak cannot happen. All 3548 files under isa/src are user-writable in pkgs/isabelle-2025.2-0, envs/isabelle and envs/isabelle-2 (`find ! -perm -u=w` gives 0 in each).

5. The real sharing is between envs, not with the cache. `ml_name_space.ML` is inode 55605093 (links=2) in both envs/isabelle and envs/isabelle-2. The cache copy is a separate inode, 56390733 (links=1). All 3548 src files in each env have several links; the cache has none. The plan describes only the cache-to-env case (plan:95-96, 313-314), and §6 never checks the sibling env (plan:294-298).

6. The mode restore is also latently wrong. I applied a git patch that changes a file from 100644 to 100755. GNU patch set mode 755, then `_restore_mode` set it back to 644, and `patch -R --dry-run` still reported the file as applied. So decision 7's "恢复 mode" step (restore the mode) silently undoes a git mode change. This cannot fire today, because make-patches refuses mode changes (make-patches:167-168). It does mean deleting `_restore_mode` loses nothing.

7. Symlinked targets are not covered. conda's `always_softlink` setting (conda/base/context.py:450) makes `determine_link_type` symlink every file (conda/core/link.py:98-99). GNU patch refuses a symlink with 'not a regular file -- refusing to patch' and rc=1 in both directions. The tool would then report a misleading CONFLICT, and decision 7's `st_nlink` check does not catch this case. This is a gap, not a leak: `check_status` returns before the `chmod` (patcher.py:67-81).

Two supporting points in the challenge are overstated:
- "A second code path that gate (c) never exercises": true for gate (c), which replays on a fresh `git archive` extraction where nlink=1 (make-patches:176-185). But decision 12 does plan a pytest for "硬链接文件的 inode 与 mode" (the hard-linked file's inode and mode, plan:256).
- "An interruption leaves an untracked temporary file": true, but GNU patch already keeps its own temporary file in the same directory (strace above), so the extra window is small.

These do not weaken the core finding. Under the relaxation, the user-side `apply`, `apply-to` (plan:169-171) and gate (c)'s bare `patch -p1 -F0 --no-backup-if-mismatch` (make-patches:63-69) become the same command. Gate (c) then tests the user's own write path, which decision 7's extra branch would prevent.

One addition the editor's relaxation needs: once the copy step is gone, the invariant rests on GNU patch's write-then-rename behaviour, and `--read-only` exists only in GNU patch 2.7 and later. So `_ensure_patch_binary` (patcher.py:22-25) should check that `patch --version` reports GNU patch 2.7 or later, and otherwise exit with code 2. Without that check, a non-GNU `patch` would make every dry-run fail and every feature would show as CONFLICT.

A side note: plan:102-103 and plan:173 cite make-patches:78-84 for `apply_patches`, but the function is at make-patches:63-69.

On the owner's rulings: §0 of either plan does not touch decision 7, so this fix reverses nothing the owner has ruled.

Experiment: All work is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C16/. The system patch is GNU patch 2.7.6 (/usr/bin/patch).

- t1, no `chmod`: cache/f, env/f and env2/f were one inode, links=3, mode 444. Running `patch -p1 -F0 --no-backup-if-mismatch` in env/ printed 'File f is read-only; trying to patch anyway' and returned 0. Afterwards cache and env2 kept the old inode (links=2), mode 444 and original content; env/f had a new inode (links=1), mode 444 and patched content. Reversing with `--read-only=ignore` gave a byte-identical file and no warning.
- t1, the tool's `chmod` sequence (c2/e2): `chmod u+w`, then patch, then `chmod 444` left the cache file at 644 and the env file at 444. This reproduces the plan's §8 leak.
- strace: patch runs openat("f.oQfiold", O_CREAT|O_EXCL), then openat("f", O_RDONLY|O_NOFOLLOW), then fchmodat on the temporary file, then renameat onto "f". It never writes to the target inode.
- t2, git mode change 100644 to 100755: bare patch gives 755. The tool's `_make_writable` and `_restore_mode` sequence gives 644, and `patch -R --dry-run` still returns 0 (reported as applied).
- t3, symlinked target: `patch --dry-run` forward and reverse both print 'not a regular file -- refusing to patch' and return 1. `--follow-symlinks` replaces the symlink with a regular file and leaves the cache file alone. I still recommend refusing symlinks, because `--follow-symlinks` breaks git-style symlink diffs.
- t4, deletion patch on a hard-linked read-only file: only the env's name is unlinked; the cache inode, mode and content are unchanged.
- proto.py, a prototype of the relaxed apply (no `chmod`, no copy, `--read-only=ignore`), run with three links at modes 644 and 444. Forward and reverse both passed: the target has nlink=1 and keeps its mode, cache and env2 keep inode, mode and bytes, and the round trip is byte-identical.
- Read-only checks of the real trees: pkgs/isabelle-2025.2-0, envs/isabelle and envs/isabelle-2 each have 3548 files under isa/src with 0 lacking u+w and 0 symlinks. contrib/Isabelle2025-2/src has 2940 of 4720 files without u+w. The envs share inode 55605093 for ml_name_space.ML (links=2); the cache copy is inode 56390733 (links=1).

Recommended fix: Rewrite decision 7 (plan:185-190) as follows.

1. The tool never touches the metadata or content of an existing target file. It deletes `_make_writable` and `_restore_mode` (patcher.py:45-56, 89-100), and decision 7 has no `cp -p`/`mv -f` step. GNU patch is the only writer: it writes a new file and renames it over the target, or unlinks the name for a deletion. So the other hard links (the pkgs cache or a sibling env) cannot change, by construction.
2. Every `patch` call (status dry-runs, `apply`/`unapply`, `apply-to`) uses the same option list, `-p1 -F0 --no-backup-if-mismatch --read-only=ignore`. The user-side apply is then the same command that gate (c) and `apply-to` run.
3. `_ensure_patch_binary` (patcher.py:22-25) requires `patch --version` to report GNU patch 2.7 or later, and otherwise exits with code 2 (plan §4). The safety argument relies on GNU patch's write-then-rename, and `--read-only` only exists from 2.7 on.
4. Before computing status, if a target is a symlink (`os.lstat`), exit 3 with a message that names conda's `always_softlink`, instead of a misleading CONFLICT.
5. In decision 12 (plan:256), replace "硬链接文件的 inode 与 mode" (the hard-linked file's inode and mode) with a post-condition test. Set up a target with two other hard links (modelling the cache and a sibling env), at mode 644 and at mode 444. After `apply` and after `unapply`, the target has nlink=1 and keeps its mode, and both other links keep their inode, mode and bytes. Add a symlinked target that must be refused.
6. Correct plan:95-96 and plan:313-314: the measured leak comes from the tool's `chmod`. The published package's files are all writable, and the real sharing is between envs (inode 55605093).
7. Update develop.md:31-33, AGENTS.md:111-112 and reference.md:100-101 so they no longer describe the `chmod`.
8. Fix the make-patches citation at plan:102-103 and plan:173 to make-patches:63-69.

**Judge: confirmed → author_fixes_no_rereview.** Rewrite decision 7. Delete _make_writable and _restore_mode (patcher.py:45-56, 89-100) and the cp -p / mv -f step. GNU patch, which writes a new file and renames it over the target (or unlinks it for a deletion), is the only writer, so other hard links cannot change by construction.
Every patch call gets `--read-only=ignore`, through C8's single helper. Require GNU patch 2.7 or later (C15).
Refuse symlinked targets (conda always_softlink) with exit 3 and a clear message, instead of reporting a misleading CONFLICT.
Replace decision 12's "硬链接文件的 inode 与 mode" with a post-condition test: a target with two other hard links, at mode 644 and at mode 444. After apply and after unapply, the target has nlink=1 and keeps its mode, and the other links keep their inode, mode and bytes.
Correct plan:95-96 and plan:313-314: the measured leak comes from the tool's own chmod. Every file in the published package is user-writable, and the real sharing is between environments (inode 55605093), not with the cache. Update develop.md, AGENTS.md and reference.md, and fix the make-patches:78-84 citation to :63-69.

### C17 [major] Gate (c) would test whatever tool version is on PATH, and step 2 cannot even run, because nothing installs the renamed tool before step 4

Section: Decision 5 (plan:172-174); §5 steps 1-2 (plan:278-280)  ·  merged from: design-D12, consistency-C16, landing-L5, user-U18

**Statement.** Decision 5 makes make-patches' gate (c) call `isabelle-patch-control apply-to` from PATH and refuse to run without it (plan:173-174). Before step 4 nothing publishes the tool, and no step installs the renamed tool. The two existing installs, /home/qiyuan/Current/MLML/.venv/bin/my-better-isabelle and /home/qiyuan/miniconda3/bin/my-better-isabelle, are editable installs that map to the old package directory, and step 1's rename breaks them (critic-landing measurement). Step 2 therefore fails as written. And even once something is installed, the release gate runs whichever copy comes first on PATH, so its behaviour depends on the shell. make-patches lives in the same repository and already imports its sibling module (tools/make-patches:37; tools/common.py:18, TOOLS_DIR). The toy tests also call make-patches directly (tools/tests/test_make_patches.sh:71). In addition, `apply` would run chmod and the decision 7 copy step, which patch_tree does not, so gate (c) would test a different code path from the one users run (plan:147-149, 169-172, 187-188). make-patches writes provenance.txt only after gate (c) (make-patches:175-206), so the directory interface must not require provenance.txt; the plan does not say so. plan:174 still contains a drafting self-correction ('退回……——不，……', 'fall back ... no, ...').

**Editor.** Correct. The PATH lookup also adds a failure mode, 'refuse if not on PATH', that has no reason to exist.

**Relaxation proposed by the editor.** make-patches puts TOOLS_DIR.parent on sys.path and calls `isabelle_patch_control.patcher.patch_tree` directly. Gate (c) then always runs the code of the same commit, needs no install, and step 2 no longer depends on any publication. apply and unapply call that same patch_tree after the state check, so the gate exercises the code users run.

**Defender: confirmed** (needs owner: False).

I tried to refute each part of the challenge. Nearly all of it holds; one sub-claim goes slightly further than the plan text supports.

1. Gate (c) depends on PATH and refuses without the tool. Confirmed. Decision 5 says `make-patches` gate (c) and (b2) will "改调这个 CLI" ("call this CLI instead"): `apply_patches` becomes a call to `isabelle-patch-control apply-to`, and "要求工具在 PATH，否则拒绝" ("the tool must be on PATH, otherwise refuse") (plan:173-174). Today gate (c) calls `apply_patches`, which runs plain `patch -p1 -F0` (tools/make-patches:63-69, called at :179 and :183). Side finding: the plan cites `make-patches:78-84` for `apply_patches` twice (plan:103, plan:173). Those lines are the end of `archive` and the start of `feature_release`, so the citation is wrong.

2. Nothing installs the renamed tool before step 4, so step 2 fails as written. Confirmed. Step 1 is the tool refactor plus green pytest (plan:278); step 2 is `make-patches expose_foreign 1` with gate (c) "已改走目录接口" ("already routed through the directory interface") (plan:279-280); the first publication is step 4 (plan:283). No step installs the renamed tool. `which -a isabelle-patch-control` finds nothing. The two existing commands are old editable installs:
   - /home/qiyuan/Current/MLML/.venv/bin/my-better-isabelle, version 0.1.0;
   - /home/qiyuan/miniconda3/bin/my-better-isabelle, version 0.1.1.
   Both import `my_better_isabelle_prover.cli`. Their finders map `my_better_isabelle_prover` to `.../my_better_isabelle_prover/my_better_isabelle_prover` (site-packages `__editable___my_better_isabelle_prover_0_1_{0,1}_finder.py:9`), and neither provides an `isabelle-patch-control` entry point. A green pytest run does not imply an install either (pyproject.toml has no pytest configuration today).

3. Gate (c) would run whichever copy comes first on PATH. Confirmed, with a bound on how bad it is. PATH lists `.venv/bin` before `miniconda3/bin`, so with two installs the gate runs whichever comes first. The tree-hash comparison (make-patches:180-186) means a different tool version cannot make bad patch files pass. What it can do: (a) refuse when nothing is wrong with the files, or (b) certify the files against a tool version other than this checkout's. In case (b), a regression in this checkout's directory interface goes unnoticed and ships to CI (decision 11.2, plan:248). There is also an inconsistency in the same script: gate (d) already runs its sibling by path, not through PATH (`run([sys.executable, TOOLS_DIR / "check-signatures", ...])`, make-patches:131; TOOLS_DIR is defined at tools/common.py:18 and imported at make-patches:37).

4. The toy tests depend on the shell. Confirmed. test_make_patches.sh:71 runs `$tools/make-patches` directly, and run-all.sh:7-11 installs nothing. So the acceptance criterion "28 项仍全过" ("all 28 still pass", plan:293) would depend on the shell's PATH.

5. Gate (c) may exercise a different code path from the one users run. Partly confirmed; this is the slight overstatement. The challenge says that `patch_tree` does not run chmod or the decision 7 copy step. The plan never says that. It is silent on both questions:
   - decision 5 defines `patch_tree` only as `patch -p1 -F0 --no-backup-if-mismatch` in file-name order (plan:169-172);
   - decision 7 says "打一个文件之前" ("before patching a file"), without saying which command (plan:187-188);
   - decision 3 never says that `apply`/`unapply` are built on `patch_tree` (plan:147-151).
   So the confirmed defect is that the plan leaves room for two code paths that touch files, and gate (c) need not exercise the one users run.

6. Gate (c) runs before `provenance.txt` is written. Confirmed, and the measurement makes it stronger than stated. `make-patches` deletes only old `*.patch` files (make-patches:159-160) and writes `provenance.txt` after gate (c) (make-patches:206). So during gate (c), `provenance.txt` is absent at the first release and left over from the previous release at later ones. Decision 2 says a feature directory holds exactly `*.patch` plus `provenance.txt` (plan:121). The plan never says that the directory interface must ignore `provenance.txt`.

7. Drafting self-correction. Confirmed. plan:174 contains "退回今天的裸 `patch`——不，退回会让门禁悄悄变弱" ("fall back to today's plain `patch` — no, falling back would quietly weaken the gate").

8. Adjacent inconsistency (not raised by the challenge). plan:173 says (b2) also calls `apply-to`. But `apply-to` "不看内置清单" ("does not read the built-in manifest", plan:170). Meanwhile step 3 and §6 describe (b2) as the tool's chain-order `apply`, which recognises `expose_foreign` as built in through LEGACY_BUILDS (plan:281-282, 294-295). Only `apply --features-dir` can do that. The same mismatch exists in the migration plan: §5.3 line 417 says "(c) 与 (b2) 用它" ("(c) and (b2) use it"), while its §5.1 (lines 392-393) describes (b2) as chain-order application.

The editor's relaxation, on its merits: it is sound, and it satisfies migration plan §5.1(c), "经补丁工具的目录接口" ("through the patch tool's directory interface"), because plan:172 makes `patch_tree` itself the interface and the CLI only a wrapper around it. It does not contradict decision 6 or rejected proposal 11.3: the scripts stay in `tools/`, outside the package. It is safe to import: the package has `dependencies = []` and `requires-python >=3.12` (pyproject.toml:10,26), and `env python3` is 3.12.3. Three refinements are needed:
   - The checkout must go first on the module search path, with `sys.path.insert(0, …)`. Appending loses to an installed copy (experiment 2). Editable finders are appended to `sys.meta_path` (finder file :75-76), so `sys.path[0]` also wins over them.
   - `patch_tree` needs a raised-exception contract. Today's `patcher` calls `sys.exit(1)` (patcher.py:22-25), which would bypass make-patches' `Refused` handling (common.py:43-49).
   - The editor says gate (c) then runs "the same commit". More precisely, it runs the same checkout that `make-patches` itself runs from.
Finally, the cleanest shape puts decision 7 inside `patch_tree`, so there is exactly one function that touches files. My prototype shows this is harmless for gate (c) (28 of 28 toy checks pass) and keeps the package-cache copy at mode 444, whereas plan §8 measured it leaking to 644.

Experiment: All experiments ran under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C17/. Nothing in the repositories was modified.

exp1: I made a toy editable install (setuptools 82, same layout as the tool's pyproject) and then renamed the package directory, as step 1 will. The console script then fails with "ModuleNotFoundError: No module named 'oldpkg'", and no new command appears.

exp2: I installed a non-editable `isabelle-patch-control` "1.0.0" into a venv, next to a checkout that has `tools/`. A script that does `sys.path.insert(0, TOOLS_DIR.parent)` imports the checkout; `sys.path.append` imports the installed copy instead.

exp3: I copied tools/ and instrumented the copy of `apply_patches`, then ran the 28-check toy test (`test_make_patches.sh`). During gate (c) of release R/feat/1, `provenance.txt` is absent. During gate (c) of release R/feat/2, `provenance.txt` is present but stale ("release_tag: R/feat/1"). All 28 checks still pass.

exp4: I made `apply_patches` behave as decision 5 is written (`shutil.which` lookup plus `apply-to` from PATH):
- nothing on PATH: 3 WRONG ("release 1 of R/feat: expected ok, got refused", plus the two checks that follow from it);
- a correct stand-in first on PATH: 28 passed;
- a different stand-in first on PATH: 3 WRONG.
So the result depends on PATH.

exp5: I prototyped the relaxation. The repo gets `isabelle_patch_control/patcher.py` with a `patch_tree` that reads only `*.patch`, puts decision 7 (break the hard link if the link count is above 1, `chmod u+w`, restore the mode) inside, and raises `PatchFailed`. The copy of `make-patches` puts TOOLS_DIR.parent at `sys.path[0]` and wraps `PatchFailed` into `Refused`.
- With no tool on PATH: 28 passed.
- Mutation check (the checkout's `patch_tree` drops `-R`): 3 WRONG, so the gate now catches a regression in this checkout.
- Hard-link toy (cache file mode 444, hard-linked into env): after forward and then reverse application, the cache keeps the same inode, content "a b c" and mode 444; env gets its own inode, mode 444.

Recommended fix: The smallest change to the plan:

1. Rewrite decision 5's last sentence (plan:173-174) and drop the self-correction. Proposed text:
   "`make-patches` gate (c) calls `isabelle_patch_control.patcher.patch_tree` directly: `sys.path.insert(0, str(TOOLS_DIR.parent))`, then import it, replacing `apply_patches` (make-patches:63-69, calls at :179/:183). It needs no install and no PATH lookup, and always runs the code of the same checkout as `make-patches`. `patch_tree` reads only `<feature dir>/*.patch` and never `provenance.txt` (at gate (c) time that file is absent or left over from the previous release, make-patches:159-160,206). On failure it raises `PatchFailed(patch, output)`, never `sys.exit`; the `apply-to`/`unapply-from` CLI maps that to exit 1, and `make-patches` maps it to `Refused`."

2. Make `patch_tree` the only code that touches files:
   - move decision 7's hard-link split and `chmod u+w`/mode restore into `patch_tree` (plan:187-188);
   - state that `apply`/`unapply` are "state check, then `patch_tree`" (plan:147-151).
   Gate (c) then exercises the code users run.

3. Fix (b2): plan:173 should not claim that (b2) uses `apply-to`. (b2) is `apply`/`unapply --features-dir <tmp> --isabelle-bin <copy>/bin/isabelle --feature <F>` (plan:281-282, 294), run from the checkout as `python -m isabelle_patch_control` (the package already has `__main__.py`). Add one line to step 1 saying that the old editable `my-better-isabelle-prover` installs in .venv and miniconda base break at the rename, and what is done with them.

4. Correct the citation `make-patches:78-84` to `make-patches:63-69` at plan:103 and plan:173.

**Judge: confirmed → author_fixes_no_rereview.** Rewrite decision 5's last sentence and delete the drafting self-correction. gate (c) puts TOOLS_DIR.parent at sys.path[0], with insert(0) and not append, and calls isabelle_patch_control.patcher.patch_tree directly. It needs no install and no PATH lookup.
patch_tree:
- reads only *.patch and never provenance.txt (at gate (c) time that file is absent or left over from the previous release);
- raises PatchFailed instead of calling sys.exit. The CLI maps that to exit 1, and make-patches maps it to Refused.
State that apply and unapply are "state check, then patch_tree", so gate (c) runs the code users run. With C16 there is no chmod or copy step left to diverge.
(b2) runs the chain-aware apply with --isabelle-home (C14), not --isabelle-bin, and not apply-to.
Add to step 1 what happens to the old editable installs in .venv and miniconda base, which break at the rename. Fix the citation make-patches:78-84 to :63-69.
One correction to the challenge: the plan does not say patch_tree lacks chmod; it says nothing either way.

### C18 [major] Hook output never reaches the user, and the heap notice fires only for src/Pure

Section: Decision 3 last bullet (plan:152-153); decision 8 (c) (plan:211-213)  ·  merged from: conda-conda-9, landing-L14, user-U2, design-D11, consistency-C18, user-U14

**Statement.** The plan's only mitigation for stale heaps is a line that the tool, and therefore the post-link, prints: Pure changed, and heaps will be rebuilt on demand (plan:152-153, 213). Conda captures a hook's stdout and stderr (conda/gateways/subprocess.py:99-117). On success it shows the user only $PREFIX/.messages.txt, which it prints and then deletes (conda/core/link.py:1684-1686, 1697-1708). Captured output appears only inside the LinkError text of a failed post-link (:1647-1675). For a failing pre-unlink, the user sees only conda's generic 'consider notifying the package maintainer' warning (:1676-1683). PACKAGING_DESIGN.md:33 already records that post-link stdout is not shown reliably, and the `isabelle` recipe uses .messages.txt for exactly this reason (isabelle-packaging-ci/conda/recipe.yaml:179-182). Toy runs show the hook's stdout line absent from conda's output and the .messages.txt line present (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/conda-toy/create1.log:26). So after `conda install isabelle-light-locale`, the user is never told that the first start will rebuild Pure and HOL, which took 6 minutes for HOL in a `-j 3` run on this machine (ai-artifacts/isabelle-git-migration/RECORD.md:82), and that start looks like a hang. The trigger is also wrong. The notice fires only for features that touch src/Pure (plan:152), but the package ships HOL and Main heaps too (isabelle-packaging-ci/conda/recipe.yaml:3-4, 246-247). local_datatype changes only src/HOL/Tools/BNF/bnf_fp_def_sugar.ML (RECORD.md:125), and dev_patches changes etc/options, src/HOL/IMP/Abs_Int3.thy and src/HOL/ex/Sudoku.thy, among others. Each of these makes the shipped HOL heap stale, and none prints the notice.

**Editor.** Correct; the conda source and PACKAGING_DESIGN itself both say so. user-U14 also claims that `isabelle ML_process -l HOL` loads the stale heap silently, and that after unapply the stale user heaps shadow the shipped ones, which are valid again. Both are plausible from Isabelle's sources (src/Pure/Build/store.scala:334-335, 538-560), but nobody has measured them, so they are guidance for the wording, not verified defects. The message text is user-facing and must be proposed to the owner verbatim, in English.

**Relaxation proposed by the editor.** The reconcile command (C4) appends the notice to $PREFIX/.messages.txt once per transaction, whenever any file under src/ changed. The notice names the features and the user directory. §6 checks that `conda install` actually shows it.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute both of the challenge's main claims. Both survive. Two of the supporting examples in the statement are wrong, and so is one citation.

Claim 1: the hook's output never reaches the user. Confirmed.
- What the plan relies on. The plan's only stale-heap mitigation is a line that the tool prints (plan:152-153). Decision 8 (c) says "post-link 打印这一句" ("the post-link prints this sentence") (plan:213). The plan never mentions `.messages.txt`.
- Conda captures hook output. `run_script` calls `subprocess_call(..., raise_on_error=False)` (conda/core/link.py:1644-1646). `capture_output` defaults to True (gateways/subprocess.py:83), so stdout and stderr both go to pipes (subprocess.py:100-117).
- On success, conda shows only `.messages.txt`. It calls only `messages(prefix)` (link.py:1685), which prints `$PREFIX/.messages.txt` and then deletes it (link.py:1697-1708). It does this after every successful script, for post-link and pre-unlink alike.
- Captured stdout and stderr appear only in the LinkError text of a failed pre-link or post-link (link.py:1649-1675). They are also logged at TRACE level, which needs `-vvv` (subprocess.py:125-131).
- The isabelle recipe already relies on this. It writes its hint to `.messages.txt` and says that was "verified against conda 25.11" (isabelle-packaging-ci/conda/recipe.yaml:179-194).
- My own run (conda 25.11.1) shows the same:
  - Successful installs and removes print every `MSG-*` line and none of the `STDOUT-*` or `STDERR-*` lines (toy/create.log:48,50; toy/remove.log:39,41).
  - The messages come out in chain order on install and in reverse order on remove.
- The plan's acceptance checks would not catch this. §6 checks that the rebuild works (plan:296-297) but never checks that the user is told about it.

Claim 2: the notice is triggered only by src/Pure. Confirmed for HOL-only features.
- Which heaps can go stale. The package ships Pure, HOL and Main heaps (recipe.yaml:3-4,246-247; on disk in pkgs/isabelle-2025.2-0/isa/heaps/*/{Pure,HOL,Main}).
- local_datatype is HOL-only. It patches only `src/HOL/Tools/BNF/bnf_fp_def_sugar.ML` (RECORD.md:125; LOCAL_DATATYPE_PLAN.md:558). That file is an `ML_file` of the HOL session (src/HOL/BNF_Fixpoint_Base.thy:293).
- localized_record is HOL-only. It patches `src/HOL/Tools/record.ML` and `typedef.ML` (LOCALIZED_RECORD_PLAN.md:158), which are loaded at Record.thy:461 and Typedef.thy:110.
- light_locale also changes HOL-session files: `src/Tools/induct.ML` (loaded by HOL.thy:1568) and `src/HOL/Tools/*` (from `git diff --name-only future_assign_interrupt light_locale`). Its src/Pure changes trigger the notice anyway.
- Why the notice is skipped. Isabelle compares session source digests (store.scala:538-560; sessions.scala:674-680). So applying or upgrading only local_datatype or localized_record makes the shipped HOL and Main heaps stale (or a user HOL heap built earlier), and the notice does not fire.

Parts of the statement that I refuted:
- The dev_patches example is wrong in three ways:
  - dev_patches does print the notice, because it changes five src/Pure files (attrib.ML, printer.ML, syntax_phases.ML, thy_info.ML, sign.ML).
  - Abs_Int3.thy belongs to HOL-IMP and Sudoku.thy to HOL-ex (src/HOL/ROOT). Neither of those heaps ships, so neither change makes a shipped heap stale.
  - The etc/options change adds a new option with its default value. Session digests count only options that differ from the defaults (sessions.scala:641-643), and the non-thorough comparison drops those entries anyway (sessions.scala:595-600). I read this from source; I did not measure it.
- On a failing pre-unlink, the user also sees `.messages.txt`. `messages(prefix)` runs before the action branch (link.py:1648). My run shows the generic warning followed by the MSG line (toy/badun-remove.log:39).
- Citation fix: the "stdout is not shown reliably" row is PACKAGING_DESIGN.md:47, not :33.

Why this still matters (from source, not measured): `isabelle process`/ML_process loads whatever heap it finds without checking freshness (store.scala:370-379; ml_process.scala:173-176). So a headless consumer may run on stale heaps without any sign of it, and "rebuilt on demand" (plan:152-153) is not true for that path. User heaps are also searched before system heaps (store.scala:332-334), which bears on what to say after unapply. This is guidance for the wording only.

The editor's proposed relaxation, on its merits:
- Writing to `.messages.txt` is right. It is conda's own message channel, it is consistent with PACKAGING_DESIGN's rule against untracked post-link output, and it has precedent in recipe.yaml:179-185.
- "Any file under src/" is a sound over-approximation. Every source of the shipped heaps lives there, and it needs no knowledge of Isabelle's session structure.
- "Once per transaction" holds only under C4's reconcile command, where the first hook does all the work. That works because conda links every package before running any post-link (link.py:927-966). In the plan's current per-feature hooks, the result is one line per feature that changed files, and that is acceptable.
- The tool cannot remove duplicates through the file, because conda deletes it after each script (link.py:1708).
- Who should write the file. The hook should redirect into `.messages.txt`, not the tool. If the tool wrote `$PREFIX/.messages.txt` itself, a manual `apply` would leave a file that conda prints at some later, unrelated hook. A redirect in the one generated recipe template keeps the tool independent of conda. It also fixes the channel for every feature package, so no package can get it wrong.
- The wording is user-facing. The plan's draft line is Chinese (plan:152-153). The English text must be put to the owner verbatim as part of plan approval; that is the normal process, not a separate owner decision.
- Not verified: whether mamba, micromamba or pixi show `.messages.txt`. None of them is installed here.

Experiment: I built a toy local channel with hand-made noarch .tar.bz2 packages, using /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C18/mkpkgs.py. The packages were `isatoy`, `featx` (depends on isatoy), `featy` (depends on featx), `featbad` (its post-link exits 1) and `featbadun` (its pre-unlink exits 1). Each hook echoes one line to stdout, one to stderr, and one MSG line to `$PREFIX/.messages.txt`. I used conda 25.11.1 with CONDA_PKGS_DIRS pointed at scratch, so the real package cache was not touched. All logs are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C18/toy/.

- `conda create featy` (create.log:48,50): MSG-FEATX-POST-LINK, then MSG-FEATY-POST-LINK. No STDOUT or STDERR line appears anywhere, and `.messages.txt` is deleted afterwards.
- `conda remove featx featy` (remove.log:39,41): MSG-FEATY-PRE-UNLINK, then MSG-FEATX-PRE-UNLINK. No stdout.
- Failing post-link (bad.log:33-47): rollback, then a LinkError that contains the script messages and the captured stdout and stderr.
- Failing pre-unlink (badun-remove.log): the warning "consider notifying the package maintainer", followed by the MSG line.

I also read Isabelle sources, without building anything:
- `git diff --name-only` between chain tags in contrib/Isabelle2025-2.
- src/HOL/ROOT, to find which sessions contain Abs_Int3 and Sudoku.
- The `ML_file` lines that load the HOL-only feature files.
- sessions.scala, store.scala and ml_process.scala, for heap freshness checks.

Recommended fix: Three changes to the plan:

1. Decision 3, last bullet (plan:152-153): change the trigger from "touches src/Pure" to "the run changed any file under src/" (both apply and unapply). The notice names the features that changed and `<ISABELLE_HOME_USER>/heaps`. It tells the user to run `isabelle build -b HOL` once before using headless tools, because `isabelle process` does not rebuild. Propose the English text verbatim to the owner.

2. Decision 8 (plan:201-205 and 213): the post-link and pre-unlink template appends the tool's stdout to conda's message channel: `"$PREFIX/bin/isabelle-patch-control" ... >> "$PREFIX/.messages.txt"`. On Windows it is `>>"%PREFIX%\.messages.txt"`, as in isabelle recipe.yaml:127-135. stderr is left alone, so it shows up in the LinkError when a hook fails. Replace "post-link 打印这一句" ("post-link prints this sentence") with this channel. If C4's reconcile command is adopted, the same redirect applies to it, and "once per transaction" then holds by construction.

3. §6 (plan:296): add a check that the `conda install isabelle-light-locale` output contains the notice line, and that a HOL-only feature (for example, the toy feature in the pytest suite) also produces it.

**Judge: partially_confirmed → author_fixes_no_rereview.** Change the trigger for the heap notice from "touches src/Pure" to "this run changed any file under src/", for both apply and unapply.
The conda-hook entry point (C4) appends the notice to $PREFIX/.messages.txt. A manual apply only prints it.
The notice names:
- the features that changed;
- `isabelle getenv ISABELLE_HOME_USER`;
- that headless use should run `isabelle build -b HOL` once, on the user's own order.
Propose the exact English text to the owner.
Add to §6 a check that `conda install isabelle-light-locale` shows the notice, and add a toy HOL-only feature to pytest.
Two corrections to the challenge. dev_patches does print the notice, because it changes five src/Pure files, and its HOL-IMP and HOL-ex edits stale no shipped heap. A failing pre-unlink also shows .messages.txt (link.py:1648). Mark the claims about `isabelle process` and the order in which user heaps are searched as unmeasured guidance.

### C19 [major] Step 4 publishes permanently to PyPI and the channel first and verifies afterwards

Section: §5 step 4 (plan:283-285); §6 real environment (plan:296-298)  ·  merged from: landing-L4

**Statement.** Step 4 uploads isabelle-patch-control 1.0.0 to PyPI and conda, and three feature packages to the channel. Only then does it install them into a fresh env to verify them (plan:283-285). A PyPI version can be used only once (contrib/my_better_isabelle_prover/RELEASE.md:7-10). A channel filename is permanent, and a bad release is corrected only by a new version (isabelle-packaging-ci/RELEASE_CHECKLIST.md:36-41). So any failure the acceptance finds leaves a permanent broken artifact and forces a version bump, and C1, C2 and C15 make failures likely. The acceptance does not need public publication. Conda installs from a local file:// channel offline. The isabelle CI already verifies that way before it publishes (.github/workflows/build.yml:12-14). The isabelle-2025.2-0 .conda is in the local package cache and can be copied into such a channel. Step 4 also publishes isabelle-light-locale while light is still in milestone 3 (MLML commit 59b0ec83), and the migration plan schedules no early release.

**Editor.** Correct on the ordering. The critic stretches ruling 25 ('没有提前发布的需求，会等一切都做完的'), which concerned empty 0-version packages, not light. Whether light is published at step 4 is still a real question for the owner. A toy run confirmed that a local file:// channel install with a private CONDA_PKGS_DIRS leaves ~/.conda/environments.txt unchanged.

**Relaxation proposed by the editor.** Build every package locally, run the whole §6 acceptance from a local file:// channel, and publish only after it passes and only on the owner's order, the tool first. Put to the owner whether isabelle-light-locale is published at step 4 at all.

**Defender: confirmed** (needs owner: True).

Verdict: the main claim holds. Step 4 publishes first and runs the acceptance afterwards, and the acceptance does not need anything published. I tried to refute it and could not. Three supporting claims are overstated and are corrected below.

1. The order is as the challenge says. Plan:283-284 publishes isabelle-patch-control 1.0.0 to PyPI and conda, and three feature packages to the channel. Only then does it install into a fresh env "从渠道" (from the channel) and verify. §6's real-environment check uses that same post-publication env (plan:296-298). Publication cannot be undone:
- A PyPI version can be used once (RELEASE.md:7-10).
- A channel filename is permanent, and a bad release is corrected by a new version, not a retraction (RELEASE_CHECKLIST.md:7-9, 36-41).
- The packaging design calls publication "近乎不可逆" (nearly irreversible) (PACKAGING_DESIGN.md:715-716).

The ecosystem's fixed split is: check package correctness from a local file:// channel BEFORE upload, and check only the bytes afterwards (PACKAGING_DESIGN.md:734-738; build.yml:12-14). Every component repo enforces this: "Install and USE the package BEFORE it is published. Publishing is the point of no return" (Isabelle_RPC/.github/workflows/release-conda.yml:179-184), with a dry_run input (:17-20) and a publish job gated on verify (:311-319). The plan reverses that order. On elegance: putting the irreversible step after the check makes "publish something broken" impossible. The plan's order instead relies on someone remembering.

2. Refutation attempts that failed.
(a) Decision 12 (plan:257-258) says the tool's conda package follows RELEASE_CHECKLIST.md. That brings in a per-package verify job, but it covers only the tool installing itself. The feature packages get only a recipe template (plan:192-214). The standard verify job also takes run dependencies from the live channel (RELEASE_CHECKLIST.md:400-401), so the tool would have to be published before any feature package could be checked that way. The integrated §6 acceptance is explicitly after publication. On the PyPI side, before upload RELEASE.md only lists the wheel's contents (:61-75); the functional check runs from PyPI after upload (:77-83).
(b) The plan does not say step 4 needs an owner order (step 2 says "用户下令" (on the owner's order), step 4 does not).

3. Corrections to the statement.
(i) "Any failure forces a version bump" is too strong. A feature package's version is its release-tag number, and the build number lives in the build string (migration plan :219-221). "一个补丁版本可对应多个 build" (one patch version can have several builds) (:425), and there is a precedent: isabelle-ai 0.3.0 build 1 (RELEASE_CHECKLIST.md:189). So a defect in a feature package's recipe or post-link costs a build-number bump. Only the tool's PyPI 1.0.0 is burned outright. Some acceptance failures are wrong expectations, not broken packages.
(ii) A separate finding, outside C19, still shows that surprises on the first acceptance run are likely. I measured that with conda 25.11 (libmamba), `conda remove isabelle-light-locale` also removes isabelle-future-assign-interrupt, isabelle-expose-foreign and isabelle-patch-control. The solver keeps only specs in the env history and "delete[s] requested and their deps" (conda_libmamba_solver/solver.py:565-581). So under plan:284's install command, plan:297's "status 剩两行" (status shows two rows left) cannot hold, and the status command itself is gone.
(iii) "Offline" is imprecise; "unpublished" is the accurate word. On a first run, `--offline` with a file:// channel fails, because libmamba ignores a channel with no cached repodata in offline mode (index.py:535-543, PackagesNotFoundError). Without `--offline`, a channel list made only of file:// works with no network. The tool is noarch python, so it needs python from conda-forge, as Isabelle_RPC's verify does (release-conda.yml:217-230).
(iv) The cached isabelle-2025.2-0.conda has sha256 d99193953fcc…, which equals the published record in pkgs/isabelle-2025.2-0/info/repodata_record.json. So a local channel serves exactly the published bytes.

4. Publishing light.
- Light is in milestone 3: commit 59b0ec83 reads "milestone 3 first item, second version", and the header implicit_structure work is "to be implemented next".
- Migration step 4 only runs make-patches light_locale (which creates a tag) and (b2) (:498-502). §5.1 item 5 (:390) says a release tag means the git gates passed, not that the package is published. No migration step publishes anything.
- The light plan's §9 分发 (Distribution) says "本期不做，另立计划" (not done in this phase; separate plan) (LIGHT_LOCALE_PLAN_REV37.md:5803-5805).
- The editor is right that ruling 25 (migration plan :97-99) was about empty 0-version packages. The firmer basis is light §9.
- The plan's §7 (plan:300-309) never asks the owner this question, and no later step needs light published: the next CI build has k=2 (migration plan :215-216) and needs only the two base packages (plan:248).

5. The editor's relaxation is sound. Three refinements:
- rattler-build is not installed (plan:247), but rattler-build-0.68.0 is in pkgs/. The repos' release workflows with dry_run=true are an alternative.
- "Tool first" should mean the tool's conda package goes out no later than PyPI, because conda must never fall behind PyPI (RELEASE_CHECKLIST.md:243-245). The feature packages then follow in chain order.
- Keep a check after publication: a bytes check and a smoke install from the live channel (PACKAGING_DESIGN.md:738).

Experiment: Scratch: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C19/.

(1) I hand-built toy noarch conda packages with scripts/mkpkg.py: isabelle, isabelle-patch-control 1.0.0, and isabelle-expose-foreign / -future-assign-interrupt / -light-locale 1, each with build Isabelle2025_2_0, the plan's pins, and post-link/pre-unlink scripts that call the toy tool. I added a broken isabelle-light-locale 2 whose tool call exits 1. I indexed them into channel/ with conda_index 0.12.1. HOME, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS all pointed at scratch. My envs are recorded only in scratch home/.conda/environments.txt. The real ~/.conda/environments.txt changed during the run, but its only new lines are defender-C18 envs (another agent); it has no defender-C19 entries.

(2) `conda create -c file://channel --override-channels isabelle-light-locale=1` with no network ran the post-links in chain order: expose_foreign, then future_assign_interrupt, then light_locale. The first try with `--offline` failed with PackagesNotFoundError ("Could not load repodata"); a later `--offline` create worked once the repodata was cached.

(3) Installing the broken version 2 gave "LinkError: post-link script failed ... Rolling back transaction", and conda-meta was left empty. So a defect is caught with nothing published.

(4) I created env3 with `isabelle isabelle-light-locale=1` (the plan's install command), then ran `conda remove isabelle-light-locale`. The pre-unlinks ran in reverse order: light, then future, then expose. Afterwards conda-meta held only isabelle-2025.2-0: both lower feature packages and the tool had been removed too.

(5) I symlinked the cached pkgs/isabelle-2025.2-0.conda into channel2/linux-64. Its sha256 d99193953fcc21e6… equals the published repodata_record.json. conda_index indexed it, and a `conda create --dry-run -c file://channel2 --override-channels isabelle isabelle-light-locale=1` resolved every package from the local channel.

Recommended fix: Split §5 step 4 into three parts, and fix §6 to match.

4a. Build the tool's wheel and its conda package, plus isabelle-expose-foreign 1, isabelle-future-assign-interrupt 1 and isabelle-light-locale, into a local channel. Use rattler-build from the pkgs cache, or the repos' release workflows with dry_run=true. Copy the cached isabelle-2025.2-0.conda into that channel's linux-64/.

4b. Run §6's whole real-environment acceptance in a fresh env created with `-c file://<local channel> -c conda-forge --override-channels`, using a private CONDA_PKGS_DIRS. Change §6's "从渠道" (from the channel) to "from the local channel".

4c. Only after 4b passes, and only on the owner's order, publish in dependency order. The tool's conda package goes first, no later than its PyPI upload (RELEASE_CHECKLIST.md:243-245). Then isabelle-expose-foreign 1 and isabelle-future-assign-interrupt 1. Finish with a smoke install from the live channel.

Light: remove isabelle-light-locale from step 4's publication. It stays in the local acceptance. Add a §7 question asking the owner whether to publish it now. Light plan §9 says distribution is not done in this phase.

Separately, outside C19: plan:297 expects that removing light leaves two status rows. That cannot hold, because conda's libmamba solver also removes dependencies the user did not request, including the tool.

**Judge: confirmed → owner_decides.** Split §5 step 4 into three parts:
- 4a: build the tool's wheel and conda package, plus the feature packages, into a local file:// channel, and copy the cached isabelle-2025.2-0.conda into it (its sha256 equals the published record);
- 4b: run the whole §6 acceptance from that local channel, with conda-forge and a private CONDA_PKGS_DIRS, and without --offline on the first run;
- 4c: only after 4b passes and on the owner's order, publish in dependency order. The tool's conda package goes first and no later than its PyPI upload (RELEASE_CHECKLIST.md:243-245). Finish with a smoke install from the live channel.
Take isabelle-light-locale out of step 4's publication pending the owner's answer: light plan §9 (LIGHT_LOCALE_PLAN_REV37.md:5803-5805) says distribution is not done in this phase.
Correction to the challenge: a defect in a feature package's recipe costs a build-number bump, not a new version. Only the tool's PyPI version is burned outright.

### C20 [major] Nothing tests the conda hook layer; §6 is one happy path, includes builds that need the owner's order, and expects the wrong output

Section: Decision 12 (plan:253-256); §5 step 4 (plan:285); §6 (plan:294-298)  ·  merged from: landing-L12, consistency-C19, user-U13

**Statement.** Decision 12's pytest runs the tool against a fake isabelle, and §6 runs one fresh env in which everything applies cleanly (plan:253-256, 294-298). The failures in C1, C2, C4 and C18 do not live in the tool's Python. They live in the generated hook scripts and in how conda behaves around them, and neither test touches that layer. A toy channel of hand-built noarch packages installs offline in seconds with conda itself, using a private CONDA_PKGS_DIRS and --offline. One reviewer built it in about 70 lines (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/conda-toy-src/mkchan.py). Three more gaps in §6. (a) It lists `isabelle build -b HOL` and 'heaps rebuilt on demand' as plain steps (plan:285, 297). Every isabelle build, including one another command triggers implicitly, needs the owner's command (CLAUDE.md; ISABELLE_GIT_MIGRATION_PLAN.md:537, rule 10). (b) 'Whole tree equal, including modes' names no comparison method, and diff -r ignores modes. (c) It expects `status` to show two rows after `conda remove isabelle-light-locale` (plan:297). In a toy env created with only the top package requested, conda 25.11 also removed the dependency-only base packages and ran their pre-unlinks in reverse chain order (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-user/envs/hooklog-e7.txt). On k=1, removing light therefore also silently reverses future_assign_interrupt, a correctness fix the user may want to keep. The plan neither expects nor documents this. There is no Isabelle2024 case, and no check that sibling envs and the pkgs cache are unchanged after apply and unapply.

**Editor.** Correct. The pruning of dependency-only packages comes from one toy measurement, but it matches how conda's history-based removal works, and the plan should at least document it.

**Defender: partially_confirmed** (needs owner: False).

Most of C20 holds up. Two parts are wrong or overstated: the claim that nothing touches the hook layer, and the sibling-env and cache check.

1. Is the hook layer really untested? Mostly yes, but the title says too much. Decision 12's pytest uses a toy tree with a fake bin/isabelle, and CI "不碰真 Isabelle" (plan:253-256). The statement says "neither test touches that layer". That is false. §5 step 4 and §6 do install from the channel and check that post-link applied the patches and that `conda remove` reversed them cleanly (plan:284-285, 296-298). So the hooks are exercised once, on the happy path. What is true:
- That one run comes after publishing. Step 4 publishes to the channel first and verifies afterwards (plan:283-285).
- None of decision 8's claims about conda behaviour is tested. These are: a non-zero post-link rolls the install back (plan:206-207), the force-reinstall case (plan:210-211), and the Windows .bat hook (plan:203). The only support is §8's reading of the link order in conda's source (plan:318-320).
- The migration plan tests hooks and scripts on a toy repo first (ISABELLE_GIT_MIGRATION_PLAN.md:113, 443). This plan does not follow that pattern for the conda hooks.
- §6 has no Windows run, although isabelle-packaging-ci/RELEASE_CHECKLIST.md:254-256 and 641-642 say Windows hook failures are silent and need their own smoke test.

My experiment E6 shows the kind of defect that only a hook-layer test can find. A toy env already had isa. I installed a top package whose post-link exits 1. conda rolled back every package in the transaction, and no pre-unlink ran. The lower features' edits were left in isa/f.txt ("applied-fe", "applied-ff"), with no package recording them. I did not see C1, C2, C4 or C18, so I do not judge them.

2. (a) Confirmed. The plan lists `isabelle build -b HOL` (plan:297) and "heap 按需重建" (plan:285) as plain steps. Rule 10 (ISABELLE_GIT_MIGRATION_PLAN.md:537, English at :716-717) and CLAUDE.md require the owner's command for every build, including one another command triggers. The plan knows the rule (plan:153, 329) and labels the owner's order in step 2 (plan:279), but not here. RECORD.md:58, 91 and 99 show that builds really do wait for explicit authorization.

3. (b) Confirmed. The wording "整树（含 mode）相同" (plan:295) names no comparison method. It copies the approved migration plan's (b2) wording (:394), so the plan does not misread it, but this plan is where the method should be named. My mode check: `diff -r` exits 0 when files differ only as 444 vs 644 or 755 vs 644. `git diff --no-index`, and so also the tree hash that gate (c) uses (:375-376), sees only the executable bit. Only a listing such as `find -printf '%M %p'` sees every bit. In practice the executable bit is all that varies today: pkgs/isabelle-2025.2-0/isa has 0 files without u+w.

4. (c) Confirmed, and worse than the statement says. Source:
- conda_libmamba_solver/solver.py:558-582 adds Keep only for specs in the env history ("delete requested and their deps").
- libmambapy's `Request.Remove` defaults to `clean_dependencies=True` (I printed it).

The isabelle package depends on nothing (packaging-ci conda/recipe.yaml:235-237; pkgs/isabelle-2025.2-0/info/index.json `depends: []`). So the tool, and python with it, are in the env only because the feature packages pull them in.

Toy runs with conda 25.11.1:
- E1: create the env with `isa fl` (the plan's setup, plan:284), then `conda remove fl`. Only isa remained. fl, ff, fe and the tool package were all removed. Pre-unlinks ran in order fl, ff, fe, with the tool still present each time.
- E2: the classic solver gave the same result.

So in §6 there is no `isabelle-patch-control` left to print "two rows" at all, and future_assign_interrupt is silently reversed.
- E3: running `conda install ipc ff` afterwards does NOT mark them as requested. They were already installed, so conda wrote no history entry, and removing fl still pruned them.
- E4: requesting them at create time keeps them. Only fl's pre-unlink runs, and the plan's two rows would be right.
- E7: `conda remove --force fl` removes only fl.

The repo's own isabelle-packaging-ci/RELEASE_CHECKLIST.md:312-313 records the same effect ("conda remove without --force takes base isabelle with it"). On the editor's note: this is no longer one toy measurement. It is the solver source, two solvers, and the project's own release checklist.

5. Isabelle2024 is missing. Confirmed. Decision 9 adds a separate code path: bundled directories with synthesized provenance files, chosen by `isabelle version` (plan:218-221). Neither the pytest list (plan:253-256) nor §6 covers it.

6. Sibling envs and the pkgs cache: partly true. The pytest already covers the hard-link inode and mode mechanism (plan:256). §6 has no before/after check on the real machine. What I found there: envs `isabelle` and `isabelle-2` share inode 55604874 with each other (links=2), while the pkgs cache copy is a different inode, 56390514 (links=1). So the cache-vs-env model in the plan's hard-link evidence (plan:95-96, 313-314) is not how files are shared on this machine. Today the risk is low, because GNU patch writes a new inode and every file is already u+w.

7. A detail of the statement's recipe is wrong. With `--offline`, my file:// channel would not load (conda_libmamba_solver/index.py:533-544 skips repodata that is not already cached when offline). Without `--offline` it works, and still uses no network.

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/

Setup:
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/src/mkchan.py builds a toy noarch channel shaped like the plan: isa with no deps, ipc as the tool, and the chain fe -> ff -> fl with exact pins. Every hook logs whether the tool binary is present.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/src/mkchan2.py is a variant whose hooks edit isa/f.txt by temp file plus rename, and whose top package's post-link exits 1.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/src/c.sh wraps /home/qiyuan/miniconda3/bin/conda 25.11.1 (libmamba solver) with a private HOME, CONDARC and CONDA_PKGS_DIRS and register_envs=false. Every env uses -p under run/.

Results (hook logs in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/run/hooklog-E*.txt):
- E1: `create isa fl` then `remove fl` left only isa. Pre-unlinks ran fl, ff, fe, with the tool present each time.
- E2: same with --solver classic, same result.
- E3: `install ipc ff` after the fact wrote no history entry, and they were still pruned.
- E4: `create isa ipc ff fl` then `remove fl` kept fe, ff and ipc; only fl's pre-unlink ran.
- E5: `remove isa` removed everything; pre-unlinks ran fl, ff, fe.
- E6: in an env with isa, `install fx` where fx's post-link fails. The rollback removed fe, ff, fx and ipc, ran no pre-unlink, and left isa/f.txt holding applied-fe and applied-ff. The env's conda-meta/history was also gone, so `conda list` errors.
- E7: `remove --force fl` removed only fl.
- --offline with a file:// channel fails with "Could not load repodata".

Source checks:
- libmambapy `Request.Remove` signature shows clean_dependencies=True by default.
- conda_libmamba_solver/solver.py:558-582 was read.

Mode check (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C20/modes/):
- diff -r exits 0 for 444 vs 644 and for 755 vs 644.
- git diff --no-index reports only 100755 => 100644.
- A find -printf '%M' listing catches both.

Read-only stats on the real machine:
- envs/isabelle and envs/isabelle-2 share inode 55604874 for future.ML (links=2). The pkgs cache copy is inode 56390514 (links=1).
- pkgs/isabelle-2025.2-0/isa has 0 files without u+w.

Recommended fix: 1. Decision 12 / §6: add a pre-publication hook-layer test in tools/tests/, next to the existing toy tests. It reuses the toy-channel generator (about 70 lines, file:// channel, private HOME, CONDARC and CONDA_PKGS_DIRS, no --offline). Its packages carry decision 8's real hook text, which calls the real tool on a toy Isabelle tree. It asserts:
   - post-link order equals chain order;
   - after a failing post-link, the tree is byte-identical to before (E6 shows the current design fails this);
   - what removing the top package does when only it was requested;
   - the force-reinstall case;
   - a before/after listing (sha256, mode, inode) of the private pkgs dir and of a sibling env is unchanged.

   §5 step 4 publishes only after this test is green. The real-channel run stays as the last smoke test, run on Windows as well as Linux (RELEASE_CHECKLIST.md:641-642).

2. §6 expectation: create the env with everything to keep requested explicitly (`isabelle isabelle-patch-control isabelle-future-assign-interrupt isabelle-light-locale`), then expect two rows after `conda remove isabelle-light-locale`. Also add one case for the plan's current setup, which expects conda to remove the dependency-only feature packages and the tool. The feature packages' README documents three things:
   - removing a package also removes dependency-only feature packages and reverses them;
   - running `conda install` on an already-installed package does not mark it as requested;
   - `conda remove --force <pkg>` removes only that package.

3. Label `isabelle build -b HOL` (plan:297) and the on-demand heap check (plan:285) "（用户下令）", following rule 10 (migration plan :537).

4. Name the (b2) comparison: `diff -r` for content, plus a diff of sorted `find -printf '%M %p'` listings for modes. If only the executable bit is meant, say "可执行位" and reuse make-patches' tree hash.

5. Add an Isabelle2024 pytest case: the fake isabelle answers `version` with Isabelle2024, which exercises decision 9's bundled directories.

**Judge: partially_confirmed → author_decides_then_rereview.** Add a test of the hook layer, run before anything is published, in tools/tests. It uses a toy channel generator (file:// channel, private HOME, CONDARC and CONDA_PKGS_DIRS) whose packages carry decision 8's real generated hook line and call the real tool on a toy tree. It asserts:
- post-link order and idempotence;
- what a failing post-link leaves behind;
- the C1 and C4 relink cases;
- what removing the top package does;
- that a before/after listing of the private pkgs dir and of a sibling env (sha256, mode, inode) is unchanged.
Fix §6's expectations. When only light was requested, `conda remove isabelle-light-locale` also removes the dependency-only feature packages and the tool (conda_libmamba_solver/solver.py:558-582; RELEASE_CHECKLIST.md:312-313). Either create the env with everything that should stay requested explicitly, or expect the pruning. Document both behaviours, and that `--force` removes only the named package.
Mark `isabelle build -b HOL` and the on-demand heap check as run on the owner's order (rule 10).
Name the method for the (b2) comparison: `diff -r` for content plus a diff of sorted `find -printf '%M %p'` listings for modes.
If the owner keeps Isabelle2024 in the new tool, add an Isabelle2024 case.
Correction to the challenge: §6 does exercise the happy path once, after publication.

### C21 [major] No one is assigned to build and publish the new packages, recipes and pins would be typed by hand in several repositories, and the rename's scope is not stated

Section: Decisions 1, 8, 10, 12 (plan:111-114, 192-214, 225-241, 251-258); §5 (plan:276-288)  ·  merged from: landing-L13, consistency-C21, user-U11, consistency-C25

**Statement.** Step 4 needs several things for the tool and for each repository that holds feature packages: a conda recipe, a release workflow with the channel's publish secrets, and an entry in the sweep tool's PUBLISH_REPOS list, which the checklist calls 'the one manual sync point' (isabelle-packaging-ci/RELEASE_CHECKLIST.md:171-174). None of these exists and none is assigned. contrib/light_locale has no conda/ and no .github/, and the tool repository has no workflows. Decision 8's 'template' has no home and no generator (plan:197-200), so each of at least three repositories would copy version, base pin and base package name by hand. The pre-publish check (b2) is required for every release (ISABELLE_GIT_MIGRATION_PLAN.md:392-396), but the plan treats it as a one-off acceptance item with no script (plan:281-282, 294-295). The ordering constraint created by the k=2 build is not stated either. Once future_assign_interrupt is built in at version 1, a future_assign_interrupt 2 makes every package above it that pins 2 uninstallable on existing builds until a new `isabelle` build exists. §5 names no executor for any step and does not mark which steps need the owner's order (make-patches, every publication, the HOL build). The GitHub rename of decision 1 appears in no step. The plan does not say whether the local directory contrib/my_better_isabelle_prover moves, yet light's record_golden_metadata.sh:11 and README.md:10, .gitmodules:39-41, and contrib/isabelle-packaging-ci/scripts/check_patch_sync.sh:57-60 depend on that path. check_patch_sync.sh is a listed release step in isabelle-packaging-ci/RELEASE.md:6 and breaks at step 1. The rewrite list in decision 10 (plan:239-240) omits AGENTS.md, which `help` prints and which documents categories, order.txt and --force (AGENTS.md:15, 27, 76-100), and develop.md (:14, 36-50). The five landed scripts are still untracked in the tool repository (`git status --short` shows `?? tools/`), and step 1 starts editing make-patches. Finally, decision 12 publishes on both PyPI and conda without the project's rule that the conda version never falls behind PyPI. That rule exists because a newer PyPI version lets `pip install -U` orphan conda's files (Isabelle_RPC/conda/recipe.yaml:24-33), and the hooks call the conda entry point.

**Editor.** Correct. Each item is small, but together they mean step 4 cannot be carried out as written. The generator is the one part that also improves the design.

**Relaxation proposed by the editor.** Add a tools/ generator that writes each feature package's conda/recipe.yaml (dependencies, pins, build string, and the one-line hooks of C4) from provenance.txt and a single template in the tool repository. No pin is ever typed by hand, and every feature repository's recipe is identical by construction.

**Defender: partially_confirmed** (needs owner: False).

I checked each sub-claim against the sources and tried to refute it. Ten survive, one is refuted, and one is real but has to be restated.

1. Nobody builds or publishes the feature packages. CONFIRMED. Step 4 publishes four packages (plan:283-285). For the tool itself, decision 12 says the conda package follows "RELEASE_CHECKLIST.md 的流程" (plan:257-258). That checklist already requires the per-repo secrets (RELEASE_CHECKLIST.md:299-301) and the PUBLISH_REPOS entry (RELEASE_CHECKLIST.md:171-174; sweep-old-versions.py:59-69, a list that today has seven repos and not the tool's). So the tool repository is covered by reference, although it has no .github/ today (verified with ls). The feature repositories are not covered at all. Decision 10 gives their layouts (plan:227-237) with conda/recipe.yaml but no workflow, no secrets and no PUBLISH_REPOS entry. contrib/light_locale has neither conda/ nor .github/ (verified). Light's own plan postpones its conda packaging to a separate plan ("本期不做，另立计划", LIGHT_LOCALE_PLAN_REV37.md:5805), and this plan puts the feature projects' own work out of scope (plan:51-52). So isabelle-light-locale in step 4 has no producer. The existing per-repo release workflows are 361-615 lines each, and the checklist says copies of them diverge and that the divergences are defects (RELEASE_CHECKLIST.md:291-292).

2. The template has no home and no generator. CONFIRMED. The plan refers to "决定 8 的配方模板" and says the dependencies are "由来历文件生成" (plan:126, 197, 230, 236), but names no file and no program. make-patches writes only the patch files and provenance.txt (make-patches:189-207), and plan:332 freezes its outputs. Every value a recipe needs can be computed from provenance.txt (make-patches:194-205): the version is the last part of release_tag, the base package name comes from base_tag, and base_pin and build_string_prefix are already fields.

3. (b2) is a gate for every release but the plan runs it only once. CONFIRMED. The migration plan requires it before every package publication ("发布包之前", ISABELLE_GIT_MIGRATION_PLAN.md:392-396). This plan places it only in step 3 and in the acceptance list (plan:281-282, 294-295), plus one mention in decision 5 (plan:173). Nothing in tools/ implements it (grep for b2 finds nothing).

4. Ordering constraint once two features are built in. CONFIRMED, but the claim's wording is wrong and the real behaviour is worse. The packages above do not become uninstallable; the solver quietly falls back. I measured this with a toy channel. On a fresh install, `isabelle isabelle-light-locale` resolves to the k=2 build with the OLD light 1, while `isabelle-light-locale` alone resolves to light 2 on the legacy k=1 build 0. In an existing k=2 environment, both `conda update --all` and `conda update isabelle-light-locale` answer "All requested packages already installed", and `conda install isabelle-light-locale=2` silently downgrades isabelle from build 1 to build 0. A new version of expose_foreign (the k=1 feature) is worse still. The solver picks build 0, which has no run_constrained and cannot be changed, so the install fails at post-link on the tool's version-mismatch exit 3 (plan:160-161). The plan says run_constrained "会让求解器避开" (plan:161-162) and never states the consequence. Decision 3's release order (ISABELLE_GIT_MIGRATION_PLAN.md:224-228) covers only base-before-dependent.

5. No executor named and owner-ordered steps not marked. WEAK. Step 2 does mark the owner's order (plan:279). make-patches runs on the owner's order under an already-approved standing rule (ISABELLE_GIT_MIGRATION_PLAN.md:544, :728), and CLAUDE.md's build rule binds every session regardless of what §5 says. The one gap: §6:297 schedules `isabelle build -b HOL` without saying it needs the owner's command.

6. The GitHub rename is in no step. CONFIRMED, low impact. The rename (plan:113) is still owner question 4 (plan:305), and GitHub redirects the old name, so .gitmodules:41 keeps working. It should still be placed before the first publish so that PUBLISH_REPOS records the final name.

7. Whether the local directory moves. CONFIRMED as an ambiguity. These files depend on the path contrib/my_better_isabelle_prover: light's record_golden_metadata.sh:11 and README.md:10, .gitmodules:39-41, check_patch_sync.sh:16-21, and the local_datatype plan. If the directory stays, nothing breaks, but the plan never says which.

8. check_patch_sync.sh breaks at step 1. CONFIRMED, but the cause is the Python package rename (decision 1, plan:111), not the directory question. Line 60 of check_patch_sync.sh aborts with "no my_better_isabelle_prover/ in $LOCAL". Even without the rename, hash_payload (:50-55) hashes the *.py files, which step 1 rewrites. RELEASE.md:3-8 makes this script release step 1 for isabelle. plan:222-223 knows the script retires with the CI plan but says nothing about the window between step 1 and step 5. This matters only if an isabelle release is cut in that window.

9. AGENTS.md and develop.md are missing from the rewrite list. CONFIRMED. `help` prints AGENTS.md (plan:270), and it documents categories, the patch/unpatch/build commands and the --category, --no-build and --force flags (AGENTS.md:15-28, 72-101, 124-131). develop.md documents order.txt, categories, scala_build and the patches/ layout (develop.md:12-15, 35-52, 54-131). Neither file appears in plan:239-240 or :258; :258 mentions AGENTS.md only as package-data.

10. The five scripts are untracked. CONFIRMED. `git status --short` shows `?? tools/`, and the tip commit c7f9eb6 contains no tools/, yet plan:30 says "已落地". Step 1 edits make-patches (plan:173-174) with no committed baseline to diff against. .gitignore already excludes __pycache__.

11. Conda must not fall behind PyPI. REFUTED. plan:257-258 publishes the conda package by the RELEASE_CHECKLIST.md procedure, and that checklist states the rule (RELEASE_CHECKLIST.md:243-245).

On the editor's relaxation (a generator that writes each repo's recipe): the direction is right, and it is the one item that improves the design. But it would commit generated recipe.yaml copies into each repository. That still leaves a step to remember, because someone must rerun the generator after every make-patches, and nothing would catch a hand edit. It also does nothing about the 361-615-line workflows. The better shape is one recipe template and one reusable release workflow in the tool repository. The workflow reads the calling repository's patches/<R>/provenance.txt and renders the recipe at build time; the values can be passed in through env, as Isabelle_RPC/conda/recipe.yaml:35-36 already does with env.get. It then builds and calls publish-conda.yml. Each feature repository would carry only a short caller workflow, two secrets and a PUBLISH_REPOS line. With no recipe file in any repository, the rule "every package's pins match its provenance" holds by construction. rattler-build is not installed on this machine (plan:247), so the templating of source.path must be checked on CI.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C21/. I pointed CONDA_PKGS_DIRS at that directory and checked afterwards that /home/qiyuan/miniconda3/pkgs/cache was not touched.

(1) Solver test, metadata only. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C21/mkrepo.py writes the index of a toy channel with: isabelle 2025.2 build 0 (no constraints, like isabelle-2025.2-0) and build 1 (constraining expose-foreign ==1 and future-assign-interrupt ==1, i.e. k=2); expose-foreign 1; future-assign-interrupt 1 and 2; light-locale 1 (pinning future-assign-interrupt ==1=Isabelle2025_2_*) and 2 (pinning ==2). With conda 25.11.1 (libmamba), `create --dry-run`:
- `isabelle isabelle-light-locale` -> isabelle build 1 + light 1 (the old light).
- `isabelle-light-locale` -> isabelle build 0 + future-assign-interrupt 2 + light 2.
- `isabelle=2025.2=1 isabelle-light-locale=2` -> unsatisfiable.
After adding expose-foreign 2, future-assign-interrupt 3 and light 3, `isabelle-light-locale` -> build 0 + expose-foreign 2. On that build the tool's built-in check reports a version mismatch (exit 3), so post-link rolls the install back.

(2) Real install with toy packages. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C21/real/build.py builds actual .tar.bz2 packages. I created an environment with build 1 + light 1:
- `conda update --all` and `conda update isabelle-light-locale` -> "All requested packages already installed".
- `conda install isabelle-light-locale=2` -> UNLINK isabelle build 1, LINK isabelle build 0, plus future-assign-interrupt 2 and light 2: a silent downgrade.
- Incidental, outside C21: `conda install isabelle=2025.2=0` unlinks and links ONLY isabelle. No feature package is relinked, so no post-link runs and the patches would vanish silently on any isabelle build change, not only on --force-reinstall (plan:210-211).

(3) Read-only inspection: `git status --short` in the tool repo shows `?? tools/`; ls confirms no .github/ in the tool repo and no conda/ or .github/ in light_locale; existing release-conda.yml files are 361-615 lines long; the isabelle package in pkgs/ is 2.1G.

Recommended fix: Nine changes to the plan, smallest first in importance:
(a) Decision 8: give the template a home. Put one feature-package recipe template and one reusable workflow (release-feature.yml) in the tool repository. At build time the workflow renders the recipe from the calling repo's patches/<R>/provenance.txt (version from release_tag, base package name from base_tag, plus base_pin and build_string_prefix), builds it and calls publish-conda.yml. Drop conda/recipe.yaml from decision 10's layouts (plan:230, 236); no pin is ever typed by hand. This is the editor's relaxation, except the recipe is rendered at build time instead of committed.
(b) §5 step 4: for each publishing repo (the tool repo, isabelle-base-features, light_locale), list its caller workflow, the two `gh secret set` calls, and the PUBLISH_REPOS entry plus the checklist list entry (RELEASE_CHECKLIST.md:171-174). Say who adds light's caller workflow.
(c) Add a (b2) script to tools/ and require it before every feature package publication (ISABELLE_GIT_MIGRATION_PLAN.md:392).
(d) Decision 11: add one rule with the measured behaviour. A new version of a built-in feature must be followed by a new isabelle build before anything above it pins that version. Otherwise the solver silently keeps the old packages or downgrades isabelle, and with the legacy build 0 the install fails at post-link.
(e) Decision 1: say whether contrib/my_better_isabelle_prover stays where it is (or add that to owner question 4), and put the GitHub rename before the first publish.
(f) Add AGENTS.md and develop.md to the rewrite list.
(g) Add a step 0: commit tools/ before step 1 edits make-patches.
(h) Until step 5, run check_patch_sync.sh with $1 set to a worktree at the 0.3.0 tag, or cut no isabelle release in that window.
(i) §6:297: mark `isabelle build -b HOL` as run on the owner's command.

**Judge: partially_confirmed → author_decides_then_rereview.** Give the feature-package recipe a single home. Put one template and one renderer script in the tool repo's tools/. The renderer computes the recipe from patches/<R>/provenance.txt:
- the version from release_tag;
- the base package from base_tag;
- base_pin and build_string_prefix;
- the isabelle series bound from C5;
- the one-line hooks from C4.
It runs at build time, both locally for C19's local channel and from one reusable release workflow in the tool repo. Remove conda/recipe.yaml from decision 10's layouts, so no repository commits a derived recipe and no pin is typed by hand.
In §5 step 4, list for each publishing repo its caller workflow, its secrets, and its PUBLISH_REPOS entry plus checklist entry (RELEASE_CHECKLIST.md:171-174), and say who adds light's.
Add a (b2) script to tools/ and require it before every feature-package publication.
Add to decision 11 the measured ordering rule: a new version of a built-in feature must be followed by a new isabelle build before anything above it pins that version. Otherwise the solver silently keeps old packages or downgrades isabelle.
Also:
- say whether contrib/my_better_isabelle_prover moves, and schedule the GitHub rename before the first publication;
- add AGENTS.md and develop.md to the rewrite list;
- add a step 0 that commits tools/;
- keep check_patch_sync.sh working against a 0.3.0 worktree, or publish no isabelle release, until step 5;
- mark which steps need the owner's order.
Refuted part: the conda-not-behind-PyPI rule is already covered, through RELEASE_CHECKLIST.md:243-245.

### C22 [major] Users with a self-installed Isabelle lose the tool's documented use, with no route to feature directories, and a missing directory is a silent success

Section: Decision 2 (plan:122-126); §1 (plan:45)  ·  merged from: user-U8

**Statement.** Today `pip install` and `my-better-isabelle patch` patch any Isabelle (README.md:36-42). After the change, the PyPI tool carries nothing for Isabelle2025-2 (plan:45), and feature directories ship only inside conda packages (plan:126, 199). The plan names `--features-dir` for non-conda users (plan:124-125) but not where they would get the directories. They would have to unpack the `.conda` archives (a zip of zstd tarballs) of the whole chain and lay them out as `<dir>/<feature>/`, while the package repositories use `patches/<R>/` (tools/make-patches:157). Worse, a user who omits `--features-dir` gets the default `$ISABELLE_HOME/../share/isabelle_patch_control/features.d`, for example `~/share/...` for `~/Isabelle2025-2`. That path does not exist, so the tool says 'no feature packages' and exits 0 (plan:125), and `apply` 'succeeds' having done nothing. D4 item 17 reserved exactly this question, how a non-conda tree finds features, for the owner (LIGHT_LOCALE_HANDOFF.md:1979).

**Editor.** Correct as a gap. Whether non-conda users are still supported is the owner's decision, not the plan's. The plan dropped a documented use case without saying so. The silent exit 0 of apply is a defect whatever the owner decides.

**Defender: partially_confirmed** (needs owner: True).

The challenge makes two complaints: that users of a self-installed Isabelle lose the tool, and that a missing feature directory counts as success. Some of the wording is refuted, but the core of both complaints holds up in a narrower form.

WHAT IS REFUTED OR OVERSTATED

(a) "Feature directories ship only inside conda packages; users would have to unpack .conda archives." The .conda format claim itself is true: the local isabelle-rpc-0.3.2 .conda file is a zip holding metadata.json plus two .tar.zst files. But there is a second route. make-patches writes the patch files into the feature's own repository at <package>/patches/<R>/ (tools/make-patches:8, :157). Those files are tracked in git: `git ls-files patches` in contrib/light_locale lists 32 patch files, and `gh repo view` reports xqyww123/Light_Locale as PUBLIC. The plan puts patches/Isabelle2025-2/ into every new repository (plan:230, plan:236). So a non-conda user can clone the chain's repositories at their release tags. The layout still differs: the repositories use patches/<R>/, the tool expects <dir>/<feature>/, and --features-dir takes only one directory (plan:263). A symlink <dir>/<feature> -> <repo>/patches/Isabelle2025-2 is enough to bridge that; my experiment shows the directory resolves through the link.

(b) "The plan dropped the use case without saying so." Not quite. The plan does say that --features-dir is meant for non-conda Isabelle installations (plan:124-125). What it fails to say is where such users get the feature directories, and it does not document the route anywhere: decision 10 removes the README feature table and the category section (plan:239) but adds no install text.

(c) "A missing directory is a silent success" as a blanket defect. In a conda environment, a missing default directory is the normal state when no feature package is installed:
- When conda removes a package it deletes the parent directories that become empty (conda core/path_actions.py:1176-1178, which calls rm_rf(..., clean_empty_parents=True); gateways/disk/delete.py:190-196 and :220-221). My experiment, using conda's own rm_rf, shows share/isabelle_patch_control disappears together with the last feature package.
- The live environment ~/miniconda3/envs/isabelle has no share/isabelle_patch_control directory today.
So `status` printing "no feature packages" and exiting 0 is correct there. The message is also not literally silent: status prints it (plan:125).

WHAT IS CONFIRMED

1. Today's tool works on any tree whose `isabelle version` matches a patch set it carries (README.md:3, README.md:30-42; cli.py:25-32). The README tells Isa-REPL and Isa-Mini developers to run `patch --category all` (README.md:27-28). After the change, PyPI carries nothing for Isabelle2025-2 (plan:45). That part is owner ruling migration plan:408 and is fixed. But the plan does not say where a self-installed Isabelle2025-2 tree gets its feature directories. Once directories are found, the rest of the plan's machinery works on such a tree:
- The official tree's etc/ISABELLE_ID is 89701cf1768e, which is not in LEGACY_BUILDS (plan:163), so k=0 and expose_foreign is applied as a normal feature.
- The hard-link step only acts when st_nlink > 1 (plan:187), so it does nothing on a non-conda tree.
Feature discovery is the only gap.

2. The plan answers the D4 question about how a non-conda tree finds features without putting it to the owner. That question is item (17), "非 conda 的共享树上引擎怎么找 feature（--features-dir 可重复 + 环境变量）" ("on the non-conda shared tree, how does the engine find features (--features-dir repeatable + an environment variable)"), at ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979. The plan promises to lay out every D4 item for the owner in §7 (plan:36-37), but §7 item 6 (plan:306-309) leaves item 17 out. Decision 2 settles it on its own: one --features-dir, not repeatable, and no environment variable (plan:124, plan:263). One nuance: item 17 was originally about the shared tree, and after the migration the shared tree is a git checkout that no longer needs the tool (migration plan glossary :38-39, ruling 5 at :59). But the question still applies in general, and the plan itself names non-conda installations as a use of --features-dir.

3. A missing directory counting as success IS a defect in two cases:
- A self-installed ~/Isabelle2025-2 run without --features-dir. The default path becomes ~/share/isabelle_patch_control/features.d. That directory does not exist, so the tool reports "no feature packages" and exits 0 (plan:125, plan:142, plan:147, plan:273), and `apply` reports success having done nothing.
- An explicit --features-dir with a typo. plan:125 makes no distinction between an explicit directory and the default one, so the typo also exits 0.
The plan also does not say what `--feature F` does when F is absent. All of this is a regression: today the tool exits 1 when it has nothing for the detected Isabelle version (cli.py:25-32) or does not know the feature (cli.py:34-43).
The editor's point that the exit 0 is a defect "whatever the owner decides" holds in both branches. If non-conda trees are unsupported, the tool should refuse clearly. If they are supported, it should require --features-dir. Either way, the deciding question is whether $ISABELLE_HOME/.. is a conda environment, and conda answers that itself with conda-meta/history (conda base/constants.py:334, PREFIX_MAGIC_FILE).

ADJACENT GAP (outside the challenge's wording, but it matters if the owner keeps non-conda support): under conda, the exact base version is guaranteed by base_pin (plan:197-198). The tool's chain check uses only the name part of base_tag (plan:133-135). It compares versions only for built-in features (plan:160-162). So a set of feature directories assembled by hand from different repository versions is never version-checked.

The editor's relaxation field is empty, so there is nothing to weigh there.

Experiment: All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C22/.

(1) conda_empty_parents.py, run with ~/miniconda3/bin/python -I. It builds a toy environment containing share/isabelle_patch_control/features.d/light_locale/{patch, provenance.txt}. It then removes those files with conda's own rm_rf(..., clean_empty_parents=True), the same call conda's UnlinkPathAction.cleanup makes. Result: features.d and share/isabelle_patch_control are both gone, and share/ stays. So in conda, a missing default directory means "no feature packages", which is legitimate. `ls` also confirms that ~/miniconda3/envs/isabelle has no share/isabelle_patch_control today.

(2) resolve_proto.py runs the plan's rule and a proposed rule on three toy layouts:
- Conda environment with no feature packages: the plan's rule and the proposed rule both give exit 0.
- Self-installed home/Isabelle2025-2 with no flag: the plan's rule looks in home/share/... and exits 0. The proposed rule refuses with "not in a conda environment; pass --features-dir".
- --features-dir with a typo: the plan's rule exits 0. The proposed rule exits 3.

(3) The .conda format: the namelist of pkgs/isabelle-rpc-0.3.2-pyh4616a5c_0.conda is metadata.json, pkg-*.tar.zst and info-*.tar.zst.

(4) The git route: `git ls-files patches` in contrib/light_locale lists 32 tracked patch files under patches/Isabelle2025-2/. `gh repo view` reports xqyww123/Light_Locale as PUBLIC. A symlink features/light_locale -> repo/patches/Isabelle2025-2 resolves as a feature directory with both files visible.

(5) contrib/Isabelle2025-2/etc/ISABELLE_ID is 89701cf1768e and the conda environment's isa/etc/ISABELLE_ID is 5533cd83156e. So an official tree is not in LEGACY_BUILDS and gets k=0.

Recommended fix: 1. Decision 2 (plan:122-125): replace "目录不存在时视为没有任何 feature 包" ("a missing directory counts as having no feature packages") with a rule that checks, in order:
   - An explicit --features-dir must exist; if it does not, exit 3.
   - Otherwise, on Isabelle2024, use the bundled sets (decision 9).
   - Otherwise, use the default $ISABELLE_HOME/../share/isabelle_patch_control/features.d only when $ISABELLE_HOME/.. is a conda environment, meaning $ISABELLE_HOME/../conda-meta/history exists (conda's own test, base/constants.py:334). In that case a missing directory is the normal state with no feature packages, because conda deletes it together with the last feature package, so print that and exit 0.
   - Otherwise, refuse with exit 3: "<ISABELLE_HOME> is not in a conda environment; pass --features-dir".
   In addition, status, apply and unapply should all print the features.d path they read. And --feature F naming a feature that is neither in features.d nor built in should exit 3, as cli.py:34-43 does today.

2. §7: add D4 item 17 (LIGHT_LOCALE_HANDOFF.md:1979) as an owner question: are self-installed Isabelle2025-2 trees supported?
   - If yes: add a README section on the git route (clone each chain repository at its release tag and link <dir>/<feature> to <repo>/patches/Isabelle2025-2). Also make the chain check require each feature's base_tag to equal its base's release_tag, or the tag in the built-in list, because without conda's base_pin nothing else checks it.
   - If no: the README says Isabelle2025-2 is conda-only, and the refusal in item 1 says so too.

**Judge: partially_confirmed → owner_decides.** Rewrite the rule at decision 2 (plan:122-125):
- an explicit --features-dir must exist, otherwise exit 3;
- the default $ISABELLE_HOME/../share/isabelle_patch_control/features.d is used only when $ISABELLE_HOME/.. is a conda env, i.e. conda-meta/history exists. There, a missing directory is the normal "no feature packages" state and exits 0, because conda deletes the directory together with the last package;
- in every other case, refuse with exit 3: "not in a conda environment; pass --features-dir".
status, apply and unapply print the features.d path they read. `--feature F` for an unknown F exits 3.
Put D4 item 17 to the owner: are Isabelle2025-2 trees that users install themselves supported?
- If yes: document the git route (clone each chain repo at its release tag and link <dir>/<feature> to <repo>/patches/<R>). C6's tag rule then supplies the missing pin check.
- If no: the README says Isabelle2025-2 is conda-only.
Correction to the challenge: the patch files are tracked in public git repositories, so the directories are not reachable only by unpacking .conda archives.

### C23 [minor] Today's 0.3.0 users get no migration path

Section: Decision 1 (plan:114); §5 step 4  ·  merged from: landing-L8

**Statement.** README.md:27-28 and :79 and contrib/Isa-Mini/Agent/Injector/ROOT:24-26 tell developers to run `my-better-isabelle patch --category all`. On an isabelle-2025.2-0 tree patched that way, light_locale no longer applies: after 0.3.0's register_thy, show_types_nv and expose_map_syn, the expose_foreign-to-light patch fails in src/Pure/Syntax/syntax_phases.ML ('Hunk #4 FAILED at 729', /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-landing/devfirst.sh). Installing isabelle-light-locale there fails in the post-link and leaves C2's orphaned patches. The obvious cleanup is a trap. 0.3.0's bare `unpatch` defaults to all categories (cli.py at v0.3.0 line 157), so on 2025.2-0 it also reverses the build's own expose_foreign, and the new tool still reports expose_foreign as built-in (C13). Patches applied by 0.3.0 are invisible to the new tool. And since decision 1 ends the 0.3.0 line (plan:114), nothing on PyPI tells its users any of this.

**Editor.** Valid but low impact. The affected users are mostly developers on the shared tree, which the migration has already moved to git. Conda envs patched with `--category all` are probably rare. A README section is enough.

**Defender: confirmed** (needs owner: False).

I tried to refute C23 and could not. The core defect stands. One supporting inference is wrong, and the affected population is small.

1. The plan has no migration path anywhere (confirmed).
- I searched the plan for 0.3/旧/老/my-better-isabelle/pip uninstall. The only hits about the old line are plan:113-114: the GitHub rename, and "the old PyPI package gets no more releases; 0.3.0 stays for CI".
- Decision 10 deletes the README feature table and the category section (plan:239-241) and puts nothing in their place.
- §2.2 "谁在用它" (plan:72-79) lists only CI, the shared tree, Isabelle-MCP and Isa-Mini's recipe comments. It leaves out pip-installed end users. Two groups of them exist:
  - Isa-Mini invites conda users to run `--category all` to get the Injector session (Agent/Injector/ROOT:24-26, ROOT:15, conda/recipe.yaml:150-152).
  - Isabelle-MCP told its 0.2.x users that "Any patches it already applied stay applied" (Isabelle-MCP CHANGELOG.md:395-399). Their 0.2.0 `patch` had no categories, so it applied show_types_nv by default (`git ls-tree v0.2.0`; categories came later in commit 4923927).

2. The documents point developers at `--category all` (confirmed).
- README.md:26-28, :39, :79; AGENTS.md:80; reference.md:66,108.
- The quick start offers `my-better-isabelle unpatch  # reverse them all` (README.md:41).

3. After a `--category all` patch, light_locale no longer applies (confirmed, measured by me).
- I ran the real v0.3.0 tool on copies of the isabelle-2025.2-0 files with a stub `isabelle`.
- Its `patch --category all` skipped expose_foreign as already applied and applied the six dev patches.
- future_assign_interrupt (f8d760a..6d8be01) still applies. light_locale (6d8be01..7983d8a) fails only in src/Pure/Syntax/syntax_phases.ML with "Hunk #4 FAILED at 729".
- On the untouched copy both patches apply (rc=0).
- Under decision 3 this is CONFLICT, and `apply` stops (plan:147). The post-link then exits non-zero by design (plan:206-207).
- The orphaned patch that C2 describes follows from how conda works:
  - pre-unlink scripts run only in the forward pass (conda/core/link.py:938-946).
  - post-links run one after another (link.py:964-967), so future_assign_interrupt's post-link has already patched future.ML.
  - Rollback only calls `action.reverse()` on file actions (link.py:1038-1045, 1129-1160). No scripts run, so future.ML stays patched.

4. The obvious cleanup is a trap (confirmed, measured).
- A bare `unpatch` defaults to `--category all` (v0.3.0 cli.py:157) and reverses everything it reads as applied (v0.3.0 patcher.py:73-75,120).
- On the copy it reversed the six dev patches and also expose_foreign. Afterwards `hidden_structures` again lists "Foreign" (ml_name_space.ML:67), and the tree differs from the build.
- After that, future_assign_interrupt and light_locale still apply cleanly, because light does not touch ml_name_space.ML.
- The new tool would show everything green: it takes built-in status from LEGACY_BUILDS by ISABELLE_ID and never reads those patches' contents (plan:163-165). That root cause is C13.
- The correct command, `unpatch --category dev`, restored the build copy exactly (`diff -rq` rc=0). Nothing in the documents names it as the way to clean up.

5. Patches applied by 0.3.0 are invisible to the new tool (confirmed).
- Its only input is `<features.d>`, and the chain order comes from provenance files (plan:121,134-136).

What does not hold:
- "Since decision 1 ends the 0.3.0 line, nothing on PyPI can tell its users" is wrong as a reason. The 0.3.0 metadata sends PyPI visitors to GitHub (v0.3.0 pyproject.toml:28-31), and GitHub redirects the renamed repo (plan:113). A section in the new README is therefore reachable from PyPI without any new 0.x release.
- Conda also prints a failed post-link's stdout and stderr (link.py:1644-1675). So a pointer inside the CONFLICT message reaches exactly the users who hit the failure.

The editor's view of the population is right:
- The shared tree is now git-managed, with daily = dev_patches (RECORD.md:46-55), so it is not a tool user.
- Both local conda envs, isabelle and isabelle-2, are untouched. All seven relevant files have links=2 and are identical to pkgs/isabelle-2025.2-0.
- Severity minor is fair.

"A README section is enough" is almost right. To be enough, the section must:
- name the exact safe command;
- warn against a bare `unpatch` and say how to recover from one;
- be printed by `help` (AGENTS.md);
- be pointed to from the CONFLICT error.

On elegance: if C13 is fixed so that built-in features are checked against the tree, the bare-unpatch trap shows itself, and the warning becomes a convenience rather than the only defence.

A related point the orchestrator may want to route elsewhere: 1.0.0, released at step 4, already ships and applies no Isabelle2025-2 patches (plan:221,258,283). Keeping `patches/Isabelle2025-2/` in the repo until step 7 (plan:278,288) is removal in name only. So the dev patches effectively leave before qiyuan-dev-patches is published (step 6), although plan:35 and migration §5.3 say that release comes after it. Between steps 4 and 6, the only remaining carrier of the dev patches is 0.3.0, and it conflicts with light_locale (measured above).

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C23/

Setup:
- Extracted the v0.3.0 tool with `git archive` (read-only) and ran it as is.
- Wrote a stub `bin/isabelle` that answers `version` and `getenv`.
- Built the scratch tree from copies (not hard links) of the touched files in pkgs/isabelle-2025.2-0/isa. That cache's ml_name_space.ML is byte-identical to expose_foreign f8d760a, so k=1.
- Took fai.patch (f8d760a..6d8be01) and light.patch (6d8be01..7983d8a) from the Isabelle repo with read-only `git --no-optional-locks diff-tree`.

Results:
- 0.3.0 `status`: user 1/1 applied, dev 0/6.
- Control on the untouched copy: future_assign_interrupt, then light_locale, both rc=0.
- 0.3.0 `patch --category all`: skipped expose_foreign, applied the six dev patches.
- Then future_assign_interrupt dry-run is OK, but light_locale fails in syntax_phases.ML only ("Hunk #4 FAILED at 729", 1 of 6 hunks).
- 0.3.0 bare `unpatch`: reversed the dev patches and expose_foreign. Status became user 0/1, `diff -rq` against the build copy flagged ml_name_space.ML, and `hidden_structures` lists Foreign again.
- After that bare unpatch, future_assign_interrupt and light_locale still apply cleanly.
- 0.3.0 `unpatch --category dev` on a fresh copy of the dev state: the tree equals the build copy (`diff -rq` rc=0).
- Local envs isabelle and isabelle-2: thy_info, sign, printer, syntax_phases, ml_name_space, etc/options and future.ML all have links=2 and are identical to the cache, so neither env was patched.
- Read conda 25.11's link.py:
  - Rollback only reverses file actions (no pre-unlink).
  - post-links run one after another.
  - A failed post-link's stdout and stderr go into the LinkError message.

Recommended fix: 1. Decisions 10 and 12: add a section "Coming from my-better-isabelle 0.x" to README.md and to AGENTS.md (so `help` prints it). It is reachable from the 0.3.0 PyPI page through its Homepage link and GitHub's rename redirect, so no 0.x release is needed. It should say:
   - isabelle-patch-control cannot see patches that 0.x applied.
   - Before you install any feature package into an Isabelle that 0.x patched (`--category all`, or a 0.2.x `patch`), run `my-better-isabelle unpatch --category dev`, then `pip uninstall my-better-isabelle-prover`.
   - Never run a bare `unpatch`: on isabelle-2025.2-0 it also reverses the build's own expose_foreign. If you already did, `conda install --force-reinstall isabelle` restores it.
   - The dev patches come back only with qiyuan-dev-patches (§5 step 6). Until then they cannot coexist with light_locale (they conflict in syntax_phases.ML).
2. Decision 3: the CONFLICT error ends with one line pointing to that section. Conda prints a failed post-link's output, so this is where affected users will see it.
3. §2.2: add the pip-installed end users (Isa-Mini's Injector invitation, the users Isabelle-MCP 0.2.x left with patches applied).
4. §5 step 7: rewrite Isa-Mini's `--category all` comments (Agent/Injector/ROOT:24, ROOT:15, conda/recipe.yaml:32,142,152) to point to qiyuan-dev-patches.

**Judge: confirmed → author_fixes_no_rereview.** Add a section "Coming from my-better-isabelle 0.x" to README.md and AGENTS.md, so that `help` prints it. Users reach it from the 0.3.0 PyPI page through the repository link and GitHub's rename redirect. It says:
- the new tool cannot see patches that 0.x applied;
- before installing feature packages on a tree patched with `--category all`, run `my-better-isabelle unpatch --category dev`, then `pip uninstall my-better-isabelle-prover`;
- never run a bare `unpatch` on a conda isabelle: it also reverses the build's own expose_foreign. If you did, `conda install --force-reinstall isabelle` restores it;
- the dev patches return only with qiyuan-dev-patches.
The CONFLICT message ends with a pointer to that section; conda shows a failed post-link's output. Add pip-installed end users to §2.2, and update Isa-Mini's `--category all` comments in step 7.

### C24 [minor] Git blocks without hunks (empty created or deleted files) are rejected by decision 6's parser and invisible to dry-run status

Section: Decision 6 (plan:178-183)  ·  merged from: design-D8

**Statement.** For an empty created or deleted file, git emits no ---/+++ lines, only `diff --git`, `new file mode`/`deleted file mode` and `index` (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/critic-design/hdr/all.diff). make-patches does not reject such blocks; it rejects only mode changes, binary diffs and similarity (tools/make-patches:167). GNU patch applies them, so gate (c) passes. Decision 6 makes 'no paired header' exit 3 (plan:178-179), so the tool would refuse a package that make-patches released. Dry-run status cannot see such a block either: forward and reverse dry-runs both succeed whether or not the file exists, so it always reads applied. The bundled Isabelle2024 patches have no `diff --git` line at all, so the parser must handle both header forms.

**Editor.** Valid edge case. Empty files in Isabelle sources are rare. The fix makes the invariant 'every released block has a hunk' structural.

**Relaxation proposed by the editor.** Make make-patches reject hunkless blocks, the same way it rejects mode changes; that is a gate, not a change of output format. Read the target from the `diff --git a/X b/X` line (make-patches:164-166 already requires a == b), and fall back to the ---/+++ pair only for the bundled non-git patches.

**Defender: partially_confirmed** (needs owner: False).

The challenge makes four claims. I tested each one: two are confirmed, one is wrong, and one is true but is not a defect.

1. CONFIRMED: git writes no ---/+++ lines for an empty file, and make-patches does not refuse such a block. In a toy repository (git 2.43.0), `git diff-tree -r -p --no-renames` gives only the `diff --git`, `new file mode`/`deleted file mode` and `index` lines for an empty created file, an empty deleted file and an empty created file with mode 755. make-patches splits the diff on `diff --git` (tools/make-patches:154-156). Its only header refusals are the a==b check (:164-166) and the regex `^(old mode|new mode|GIT binary patch|similarity index)` (:167-168). That regex does not match `new file mode`. I replayed lines 154-187 verbatim (gate.py): all three hunkless blocks were written out.

2. CONFIRMED: gate (c) passes on these blocks. GNU patch 2.7.6 with `-p1 -F0 --no-backup-if-mismatch` (the command at :66) creates the empty files, including the 0755 one, and deletes the empty one. The forward and the backward tree hashes both match (:180-186).

3. CONFIRMED: the parser in decision 6 refuses these blocks. Decision 6 reads the first `--- ` line and the `+++ ` line right after it. A missing pair is exit 3 (plan:178-179, plan:273-274). A prototype of that parser (d6_parser.py) prints "NO PAIRED HEADER: exit 3" for all three hunkless toy patches. So the tool would refuse a feature directory that make-patches released and gate (c) accepted: the release gate and the tool accept different sets of patch files. The tool needs the target path for the `status` display (plan:141-142) and for the hard-link handling in decision 7 (plan:187), so it cannot simply skip the line.

4. REFUTED: the claim that dry-run status cannot see such a block. I copied the two subprocess calls of patcher.py:28-42 exactly (status_exact.py), with stdout captured. GNU patch 2.7.6 tells the states apart correctly:
   - Empty created file: absent reads not-applied, present and empty reads applied, present with content reads CONFLICT.
   - Empty deleted file: present and empty reads not-applied, absent reads applied, present with content reads CONFLICT.
   - The 0755 empty file behaves like the 0644 one.
   Patch's own messages (for example "would empty out the file ..., which is already empty!" and "would delete the file ..., which does not exist!") show it checks whether the file exists and whether it is empty. "Both dry-runs succeed, so it always reads applied" is false. The new-file status rule at plan:180-181 holds for empty files too. The critic's directory critic-design/hdr contains only all.diff and empty.patch, with no status run behind this claim.

5. TRUE, NOT A DEFECT: the bundled Isabelle2024 patches have no `diff --git` line. All six start with `--- a/`/`+++ b/` (patches/Isabelle2024/*/*.patch; zero `diff --git` lines). But the parser in decision 6 already reads the ---/+++ pair, and my prototype resolves all six correctly. So the parser does not need to understand two header forms.

How often this happens: zero tracked files of size 0 exist on Isabelle2025-2/pristine or on Isabelle2025-2/light_locale (`git ls-tree -r -l HEAD`, read-only). An empty deleted file can therefore only appear if some lower feature creates one. The case is rare, as the editor says, but the release gate and the tool's parser disagree, and that disagreement is a real gap.

On the relaxation:
- First half (make-patches refuses hunkless blocks): good, and the smallest fix. It is one more refusal next to :167-168, the same kind as the refusal of mode changes. The migration plan already lists refusals at this point (migration plan:384-385). It does not change make-patches' output format, so plan:332 still holds. And the plan already edits make-patches in decision 5 (plan:173). With this refusal in place, every released patch file has a ---/+++ pair by construction. The exit 3 in decision 6 then only guards hand-made `--features-dir` input.
- Second half (read the target from `diff --git a/X b/X`, fall back to ---/+++ for the bundled patches): unnecessary once the refusal exists, and less elegant. It gives the parser two header forms and two code paths. The ---/+++ pair is already the one form that the git blocks (after the refusal) and the Isabelle2024 patches share. Reading from `diff --git` would only be the better choice if the owner wanted empty files to be releasable; status (point 4) would then already work.

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C24/ and was run with GNU patch 2.7.6 and git 2.43.0.
(1) repo/ is a toy git repository. Base: keep.ML, empty_old, old.ML, mod.ML. Tip: deletes empty_old and old.ML, creates empty_new.ML, an empty 0755 empty_exec and a non-empty new.ML, and modifies mod.ML. all.diff is its `git diff-tree -r -p --no-renames`. The three empty-file blocks have no ---/+++ lines.
(2) gate.py replays make-patches:154-187 verbatim: block split, header checks, then gate (c) with `patch -p1 -F0 --no-backup-if-mismatch` forward and back, compared with a temporary-index tree hash. All 6 blocks were written to out/; forward and backward hashes both matched; empty_exec came out 0755.
(3) status_exact.py copies the two dry-run calls of patcher.py:28-42. Results: empty create gives absent=not-applied, empty=applied, content=CONFLICT. Empty delete gives absent=applied, empty=not-applied, content=CONFLICT. The 0755 create gives the same as the 0644 one. Plain `patch --dry-run` messages confirm patch checks existence and emptiness.
(4) d6_parser.py implements the parser of plan:178-179. All three hunkless toy patches give exit 3. The six Isabelle2024 patches and the three ordinary toy patches resolve to their correct targets.
(5) gate_fixed.py is gate.py plus one refusal: `if not re.search(r"(?m)^--- .*\n\+\+\+ ", block)`. It refuses repo/ at the first hunkless block. On repo2/, which has no empty files, it passes gate (c) both ways.
(6) Read-only `git ls-tree -r -l HEAD`: 0 zero-size files on Isabelle2025-2/pristine and 0 on Isabelle2025-2/light_locale.

Recommended fix: Add one refusal to make-patches and one sentence to decision 6. Do not add a second header form to the parser.
(a) In tools/make-patches, next to the refusal at :167-168, refuse any block that has no `--- `/`+++ ` pair, for example:
`if not re.search(r"(?m)^--- .*\n\+\+\+ ", block): raise Refused(f"{m.group(1)}: an empty file has no ---/+++ pair; empty files are not released")`
Add a matching toy test in tools/tests/test_make_patches.sh, alongside the mode-change test at :104-106.
(b) In plan decision 6 (plan:178-183), say that make-patches refuses blocks without the pair (empty created or deleted files), so every released patch file has one. The exit 3 then only covers hand-made feature directories. Also add this refusal to the list of make-patches edits in decision 5 (plan:173).
Leave the parser in decision 6 as it is: it already handles the bundled Isabelle2024 patches. Drop the challenge's sentence that dry-run status cannot see such blocks: GNU patch 2.7.6 reports their state correctly.

**Judge: partially_confirmed → author_fixes_no_rereview.** Add one refusal to make-patches, next to :167-168: refuse any block that has no `--- `/`+++ ` pair, which is how git writes an empty created or deleted file. Add a matching toy test.
In decision 6, say that every released patch file therefore has the pair, so the exit 3 there guards only hand-made directories. List this refusal among decision 5's changes to make-patches. Keep the parser at one header form, the ---/+++ pair, which the Isabelle2024 patches already share.
Refuted parts: GNU patch 2.7.6's dry-runs do read hunkless blocks correctly, so status can see them. The parser does not need a second header form.

### C25 [minor] The Windows path-length question that migration §9 delegated to this plan is not answered

Section: Decision 8 build string (plan:196); decision 2 features.d path (plan:122)  ·  merged from: conda-conda-12, consistency-C15

**Statement.** Migration §9 asks this plan whether the build string `Isabelle2025_2_<n>` is feasible under Windows MAX_PATH (ISABELLE_GIT_MIGRATION_PLAN.md:569-572). The plan only cites ruling 27. Critics computed two figures. Relative to the pkgs cache, the worst path across the current features is 153 characters (`isabelle-future-assign-interrupt-99-Isabelle2025_2_99/share/isabelle_patch_control/features.d/future_assign_interrupt/src-Pure-Concurrent-future.ML.patch`). The `isabelle` package's own budget is 198 (isabelle-packaging-ci/scripts/pack.sh:357). With a typical cache prefix such as `C:\Users\abcdefgh\miniconda3\pkgs\`, today's patch files come to 162-185 characters. A hypothetical patch for the longest tracked path (83 characters) would reach about 228, while the `isabelle` package once failed at 262 (isabelle-packaging-ci/conda/recipe.yaml:30-37). So the answer today is 'it fits', but the features.d prefix adds roughly 80-100 characters per file, and nothing guards against a future deep new file.

**Editor.** The two critics' numbers differ only in whether the cache prefix is included; both agree that it fits today and is unguarded. Minor, but it was explicitly delegated to this plan.

**Defender: confirmed** (needs owner: False).

I tried to refute this challenge and could not. The plan does not answer the question that migration §9 handed to it, and nothing guards against the limit. The challenge's figures are correct; if anything they understate the risk.

1. The question really was handed to this plan. Migration §9 says (ISABELLE_GIT_MIGRATION_PLAN.md:569-572) that the patch-tool plan is left with one question: is the feature-package build string `Isabelle2025_2_<n>` feasible under the Windows path-length limit? It notes that the `isabelle` package cut its own build string to a bare number for this reason (recipe.yaml:29-36) and only guesses "feature packages have few, shallow files, so probably fine". Ruling 27 (migration :106-108) fixes the name of the build string. It does not settle whether the paths fit. If they did not fit, the plan's own choices would have to give way, chiefly the features.d location in decision 2 (plan:122,126).

2. The plan does not answer it. MAX_PATH appears only once, as background on the `isabelle` package (plan:84). Decision 8 restates the build string and cites only §0 item 5 (plan:196). The evidence section §8 (plan:311-325) has no path-length measurement. The owner questions in §7 do not mention it, and §7 Q5 (plan:306) asks the owner to approve `share/isabelle_patch_control/features.d/` without saying what that costs in path length. Yet Windows is clearly a target: decision 8 specifies a Windows `.bat` post-link (plan:203).

3. The limit, from the sources:
- conda extracts each package into `<pkgs>/<name>-<version>-<build>/` (conda/gateways/disk/create.py, `extract_tarball`: destination = tarball path minus `.conda`).
- This happens before any script runs, so a post-link cannot work around it (recipe.yaml:34-37; PACKAGING_DESIGN.md:401-410).
- The `isabelle` package once failed at 262 characters (recipe.yaml:35).
- pack.sh enforces MAX_REL=180, counted from `isa/` (pack.sh:357-360). Adding `isabelle-2025.2-0/` (18 characters) gives 198 relative to the pkgs cache. The challenge cites 198 at pack.sh:357; that is this derived figure, not the literal value on that line.
- That budget was designed for a pkgs prefix of up to 60 characters, `C:\Users\<20 chars>\AppData\Local\miniconda3\pkgs\` (pack.sh:335-339). 60 + 198 = 258, within the 259 usable characters.

4. The flat patch names do not make the files shallow. make-patches names each file by replacing `/` with `-` and adding `.patch` (make-patches:169). The file name is therefore as long as the full target path plus 6. Overhead before the target path, version 1, build 0:
- `isabelle` package's own files: 22 characters (`isabelle-2025.2-0/isa/`).
- feature packages: 96 (qiyuan-dev-patches) to 122 (future_assign_interrupt).

Within the same 198 budget, a feature package can therefore patch a target path of only 76 to 102 characters, against 176 for the `isabelle` package. Of the per-file overhead, the build string adds 15 characters over a bare number and `share/isabelle_patch_control/features.d/` adds 40.

5. Measured results:
- Today's worst path relative to the pkgs cache is 151 characters (153 at version 99, build 99). The file is `isabelle-future-assign-interrupt-1-Isabelle2025_2_0/share/isabelle_patch_control/features.d/future_assign_interrupt/src-Pure-Concurrent-future.ML.patch`. It fits, with about 45 characters to spare under the 198 design budget.
- Adding prefixes: with the critics' 34-character prefix, the paths are 141-185. With pack.sh's 60-character design prefix, they are 167-211.
- The longest tracked file is 83 characters (`src/Benchmarks/Quickcheck_Benchmark/Needham_Schroeder_Unguided_Attacker_Example.thy`). A hypothetical patch to it would reach 239 with the typical prefix in future_assign_interrupt (225 in localized_record). With the design prefix it would reach 265, which is over 259 and would fail.
- So the challenge's "about 228" is optimistic. A deep file that a future feature changes or creates can break Windows installs for exactly the users the `isabelle` package was built to support.

6. Nothing guards against it. make-patches has no length check (make-patches:153-172; a grep of tools/ finds nothing). The recipe template in decision 8 has none either. pack.sh checks only the `isabelle` package. Release tags never change once created, and make-patches creates them last, after its gates (make-patches:18-21; migration glossary :29-30). An over-long name found only when the package is built would therefore already have burned a release version.

There was no relaxation to weigh. The editor's rebuttal is accurate: the two critics differ only in whether the prefix is counted. The severity stays minor because everything fits today.

Experiment: All of this was read-only, done in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C25/.

(1) In contrib/Isabelle2025-2 I listed which files each feature changes against its base, using `git merge-base` and `git diff-tree -r --name-only` on each pair of neighbouring chain branches; the output is changed.txt. I also ran `git ls-files` to find the longest tracked paths: 83, 81 and 77 characters, all under src/Benchmarks/Quickcheck_Benchmark.

(2) lengths.py builds each feature-package path in the cache, `<name>-<ver>-Isabelle2025_2_<n>/share/isabelle_patch_control/features.d/<feature>/<flat>.patch`, using the names from decision 8 and make-patches:169. Results:
- worst path: 151 at version 1, build 0, and 153 at version 99, build 99 (the challenge's example measures exactly 153);
- with the critics' 34-character prefix: 141-185;
- with pack.sh's 60-character design prefix: 167-211;
- room left for the target path, per feature: 76 to 102 characters;
- a hypothetical patch to the 83-character file, design prefix: 265 for future_assign_interrupt, 251 for localized_record, 243 for light_locale.

(3) Read conda 25.11's `extract_tarball` (site-packages/conda/gateways/disk/create.py). It extracts each package into `pkgs/<dist>/`, the tarball path minus `.conda`, which confirms the path formula.

Recommended fix: Two additions. Neither reverses a ruling.

(a) In decision 8 (plan:196), add the answer to migration §9 (ISABELLE_GIT_MIGRATION_PLAN.md:569-572), with the numbers recorded in §8:
- Inside the pkgs cache, every feature-package file is `<name>-<version>-Isabelle2025_2_<n>/share/isabelle_patch_control/features.d/<feature>/<target path with / as ->.patch`.
- The `isabelle` package budgets 198 characters relative to the pkgs cache: MAX_REL 180, counted from `isa/`, plus `isabelle-2025.2-0/` (pack.sh:335-339,357).
- Today's worst feature path is 151, so the build string is feasible.
- Per feature, the target path may then be at most 76 to 102 characters.
- Mention in §7 Q5 that the features.d location takes 40 characters of that budget.

(b) Add one gate to make-patches, before it creates the release tag: the longest such path, assuming a build number of at most 3 digits, must be at most 198, the same budget pack.sh enforces for `isabelle`; otherwise make-patches refuses and lists the longest paths. make-patches already uses conda conventions: it writes `build_string_prefix` and `base_pin` into provenance.txt. Checking before the tag matters because a release tag never changes: a name found too long only when the package is built would already have used up a release version.

**Judge: confirmed → author_fixes_no_rereview.** Answer migration §9's question in decision 8, with the numbers in §8. Within the pkgs cache, a feature file's path is `<name>-<version>-Isabelle2025_2_<n>/share/isabelle_patch_control/features.d/<feature>/<flat>.patch`.
- The worst path today is 151 characters, against the 198-character budget the isabelle package uses (pack.sh:335-339, 357), so the build string is feasible.
- Per feature, a target path may be at most about 76 to 102 characters.
- The features.d prefix costs 40 of them. Mention this in §7 item 5.
Add a gate to make-patches, before the tag: the longest such path, assuming a build number of at most 3 digits, must be at most 198. This still applies even if 1.0 is Linux-only (C15), so a future Windows leg does not inherit a released name that is too long.

### C26 [minor] Keying the per-env user directory on the env's basename lets envs with different feature sets overwrite each other's heaps

Section: Decision 8 (c) (plan:212-213); decision 11  ·  merged from: conda-conda-13

**Statement.** Each env's user directory is `~/.isabelle/<R>-conda-$(basename prefix)` (pkgs/isabelle-2025.2-0/isa/etc/settings:98; isabelle-packaging-ci/scripts/pack.sh:168-189). Before feature packages existed, two envs on the same build had identical sources, so a basename collision cost little. With feature packages, two envs whose prefixes share a basename (`-p ~/a/env` and `-p ~/b/env`) share one heap directory while having different Pure sources. Each start then rebuilds Pure and HOL over the other env's heaps, and either env's `isabelle` pre-unlink deletes the shared directory (isabelle-packaging-ci/conda/recipe.yaml:223-231). Plan:212-213 assumes the directory is per env.

**Editor.** The naming predates this plan (it is a property of the `isabelle` package), but the plan turns a harmless collision into a costly one. It belongs in decision 11 as a requirement or a stated limitation for the CI plan.

**Defender: confirmed** (needs owner: False).

I tried to refute the challenge and could not. Every factual claim in it holds. Three refinements follow at the end.

1. The directory is named after the basename of the install prefix, not after the environment. The published build appends `-conda-$(basename "$(dirname "$ISABELLE_HOME")")` to the stock `~/.isabelle/$ISABELLE_IDENTIFIER` (pkgs/isabelle-2025.2-0/isa/etc/settings:78-81 and :98). Since ISABELLE_HOME = <prefix>/isa, the suffix is basename(<prefix>). pack.sh:188 is the sed that writes this. The comment at pack.sh:174-175 says "each conda env gets its own" directory, and that is the claim the plan copies: plan:88 says `~/.isabelle/Isabelle2025-2-conda-<env>` and plan:212 says `~/.isabelle/<R>-conda-<env>/heaps`. Neither line mentions that two prefixes with the same basename collide.

2. Collisions are realistic, not hypothetical. The base package supports `conda create -p <path>` envs explicitly (isabelle-packaging-ci/conda/recipe.yaml:185-187), and the owner's own procedure creates one: RELEASE_CHECKLIST.md:589 runs `micromamba create -p env` for an environment that installs isabelle-semantic-embedding. Other cases that collide:
   - two conda installations that each have an env with the same name;
   - pixi projects. Pixi's default env path is `.pixi/envs/default` for every project. That is general knowledge about pixi; I did not check it on this machine.

3. The collision really does cost repeated rebuilds, and even the env with no Pure-touching feature pays. Isabelle reads the user heap directory before the system one (store.scala:334-336). `try_open_database` takes the first log db it finds in that order (store.scala:486-493), and `check_output` compares that db's recorded sources with the current sources (store.scala:538-563). So env B finds env A's `Pure.db` in the shared user directory, sees a sources mismatch, and rebuilds Pure and HOL into that directory (output_dir, store.scala:331-332). B's own shipped system heaps would have been current, but they are never consulted. The execution record confirms that the user directory is read first (RECORD.md:82-83) and that HOL takes 6 minutes (RECORD.md:82). The plan's sentence "rebuilt on demand on first use" (plan:211-213) is therefore false under a collision: the rebuild happens on every switch between the two envs.

4. Uninstalling isabelle from either env deletes the shared directory. Its pre-unlink resolves ISABELLE_HOME_USER and runs `rm -rf` whenever the path matches `*/.isabelle/*-conda-*` (recipe.yaml:223-231; Windows equivalent at :139-169). That wipes the other env's heaps, its preferences, and its `etc/components` registrations (COMPONENTS_DESIGN.md:67-69).

5. The plan does turn a cheap collision into a costly one. Before this plan, every env on a given build had the same Pure: the published isabelle package deliberately carries no dev patches (Isa-Mini/conda/recipe.yaml:31-33, 140-144), and the old tool's README never mentions conda. Decision 8 (plan:201-213) makes "two envs on one build with different Pure sources" a normal, supported state.

Things I checked that do not refute the challenge:
- plan:331 (one Isabelle per environment) and CONDA_ISABELLE_BRIDGE.md:75-77 (only one active env at a time) do not cover this. The rebuild loop happens with strictly one-at-a-time use, and the bridge's own claim that serial switching is clean assumed a fixed user directory (bridge:27).
- The plan scopes the packaging-ci changes out (plan:51), but decision 11 (plan:243-249) is exactly where it lists what the isabelle package must provide. So the fix belongs there, as the editor says.

Refinements:
- (a) The deletion by pre-unlink and the mixing of component registrations already existed before this plan. The plan only raises the cost: the shared directory now also holds rebuilt Pure and HOL heaps.
- (b) The challenge's "before feature packages, same build ⇒ identical sources" holds only within one build. Decision 11 lets k (the number of built-in features) grow across builds, so two builds can also differ in Pure, and same-basename envs on different builds will collide even without any feature package installed.
- (c) Elegance: if the directory name is unique per prefix, the collision cannot happen at all. A documented limitation asks users to remember not to reuse basenames.

Experiment: All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C26/.

(1) sim.sh evaluates the published etc/settings line 98, copied verbatim into line98.sh, on top of the stock settings:78-81 logic, for seven prefixes.
- /home/u/a/env and /home/u/b/env both give /home/u/.isabelle/Isabelle2025-2-conda-env.
- ~/miniconda3/envs/isabelle and ~/miniforge3/envs/isabelle both give ...-conda-isabelle.
- projA/.pixi/envs/default and projB/.pixi/envs/default both give ...-conda-default.
- Every result matches the pre-unlink rm -rf guard `*/.isabelle/*-conda-*`.
Output is in sim.out.

(2) store_model.py is a small model of store.scala:334-336, :486-493 and :538-563 (user directory read first; the first db found decides; a mismatch rebuilds into the user directory). Setup: one env with only the built-in features and one env with light_locale share a user directory, and are used alternately four times. Result: 8 rebuilds (Pure and HOL on every switch, including in the built-ins-only env, whose system heaps are current). With separate directories there are 2 rebuilds (only the light_locale env, once). Output is in store_model.out.

I ran no isabelle command and no conda environment operation.

Recommended fix: Two text changes to the plan.

(1) plan:88 and plan:212: write the directory as `~/.isabelle/<R>-conda-$(basename <prefix>)` instead of `-conda-<env>`, and add one sentence. The sentence should say: the name is keyed on the prefix's basename, not on the environment. Two envs whose prefixes share a basename (`-p ~/a/env` and `-p ~/b/env`, or same-named envs in two conda installations) share one heap directory. If their feature sets differ, they rebuild each other's Pure and HOL on every switch, because the user directory is read first (store.scala:334-336). And `conda remove isabelle` in either env deletes the shared directory (recipe.yaml:223-231).

(2) Decision 11 (plan:243-249): add a third requirement for the CI plan, recommending the first alternative:
- make the user directory unique per prefix, for example by appending a short hash of the absolute prefix path to the existing basename suffix. The existing pre-unlink guard still matches such a name.
- or, failing that, state the limitation in the isabelle package's post-link message and documentation.
Under the first alternative the collision cannot happen at all. Its one-time migration cost (existing `-conda-<env>` directories, with their heaps, preferences and etc/components registrations, are left behind on upgrade) should be weighed in the CI plan.

The tool itself needs no change.

**Judge: confirmed → author_fixes_no_rereview.** At plan:88 and plan:212, write the user directory as `~/.isabelle/<R>-conda-$(basename <prefix>)`, and add one sentence on the collision. Two envs whose prefixes share a basename share one heap directory. With different feature sets, they rebuild each other's Pure and HOL on every switch, because the user directory is read first (store.scala:334-336). Removing isabelle from either env deletes the shared directory (recipe.yaml:223-231).
Add to decision 11 a requirement for the CI plan, recommending a directory name unique per prefix (for example the basename plus a short hash of the absolute prefix). The alternative is a documented limitation.

### C27 [minor] When gate (c) fails, make-patches leaves new patch files next to the previous release's provenance.txt

Section: Decision 5 (make-patches change); decision 8 files (plan:199-200)  ·  merged from: landing-L16

**Statement.** make-patches deletes the old patch files and writes the new ones before gate (c), and it writes provenance.txt only after the gate passes (tools/make-patches:157-171, 175-187, 189-206). When (c) fails, the package directory holds new patch files together with the previous release's provenance.txt. Decision 8's recipe copies the directory verbatim, and the tool never checks the patch files against the provenance file. If that state is ever committed, it builds a package with wrong provenance.

**Editor.** This takes a human error (committing after a refused run) to matter. The fix, though, is a one-line structural guarantee and does not change the output format.

**Relaxation proposed by the editor.** Generate into a temporary directory and move it into patches/<R>/ only after gate (c) passes.

**Defender: confirmed** (needs owner: False).

I tried to refute this challenge and could not. The facts are as stated, and the window is in fact wider than the challenge says.

1. The order of operations in the current code (tools/make-patches):
- It creates patches/<R>/ and deletes every old *.patch (make-patches:157-160).
- It then writes the new blocks one by one (make-patches:162-171). Two refusals sit inside that loop: an unexpected diff header (make-patches:165-166), and a mode change, binary diff or rename (make-patches:167-168).
- Gate (c) runs only after that (make-patches:175-186). It can refuse in apply_patches (make-patches:68-69) and at the two tree-hash comparisons (make-patches:182, 186).
- provenance.txt is written after gate (c) (make-patches:190-206), and the tag is created last (make-patches:210).
- The docstring's promise "all before anything is written or tagged" (make-patches:10) covers only gates 0, 1, (f), (d) and (e). Gate (c) is described as running after generation (make-patches:18-21).

So any refusal from line 165 onward leaves the package directory changed but without a matching provenance.txt.

2. The plan makes the incoherent directory the tool's input and adds no consistency check:
- The feature directory is "exactly what make-patches wrote" (plan:121).
- The tool reads only feature, release_tag and base_tag from provenance.txt (plan:132). For built-in features it reads only provenance.txt (plan:165).
- The recipe copies the directory as is ("原样副本", plan:199).
- The provenance fields have no list of patch files and no hashes of them (plan:130-133). Nothing downstream can tell a stale provenance.txt apart.

3. The plan adds a new post-write refusal. Decision 5 makes gate (c) call `isabelle-patch-control apply-to` and refuse when the tool is not on PATH (plan:173-174). It does not say when that check runs. If it replaces apply_patches in place, "tool missing" becomes another refusal after the writes, and probably the most common one, because the tool is new.

4. Experiments (in my scratch directory, on copies of tools/) reproduce both failure shapes.

(a) The repository's own toy test already produces the bad state on every run:
- Its case "a mode change is not released" (test_make_patches.sh:102-106) is refused inside the generation loop.
- Afterwards pkg/patches/R holds 3 of the 4 patch files of R/feat/2: src-Pure-new.ML.patch was deleted and never rewritten.
- provenance.txt still says release_tag R/feat/2.
- No check in the test notices this.

(b) A forced gate (c) failure (a `patch` on PATH that fails with -R):
- The run printed "refused: gate (c)" and exited 1.
- src-Pure-new.ML.patch now carries the uncommitted v4 hunk.
- provenance.txt still says release_tag R/feat/3 with the v3 commit.
- No tag R/feat/4 exists.

5. Why it stays minor:
- The package directory is under git: light_locale tracks 32 patch files under patches/Isabelle2025-2.
- The refusal is printed, and a re-run regenerates everything.
- (b2) must run before publishing (migration plan:392-396). It compares "the make-patches product applied by the tool" against `git diff-tree <k-th tag> <feature tag>`, so any content mismatch fails there.
- The CI build assertion (migration plan:422-424) catches the same mismatch for built-in features.
- So shipping a wrong package takes two human slips: committing after a refusal, and skipping or misrunning (b2).

6. Why it is still a real finding: (b2) is a manual procedure, not a script in tools/. The guarantee "patches/<R>/*.patch belong to provenance.txt" therefore rests on people remembering two steps, while a reorder makes it impossible to break from make-patches. That is the elegance criterion. The fix keeps the output format unchanged, as plan:332 requires, and decision 5 already edits this same code.

7. The editor's relaxation is right in substance, with three cautions:
- "Move the directory into patches/<R>/" taken literally does not work. tempfile puts the directory on /tmp, which is tmpfs while the package directories are on ext4, so a rename crosses filesystems. os.rename onto a non-empty directory fails with ENOTEMPTY. shutil.move nests the source inside the destination (I observed ['old', 'src']).
- The final step should therefore be: delete the old *.patch, copy the staged files, write provenance.txt. Deleting only *.patch keeps today's behaviour for any other file in patches/<R>/.
- Keep the tag last. A tag created before the files are written would block every re-run: make-patches refuses an existing tag (make-patches:87-88), and the hook forbids moving tags (test_hook.sh:43-44).
- Crash atomicity (a staging directory on the same filesystem plus renames) is not needed, because no tag exists until the end and a re-run regenerates everything.

Two side notes, outside this challenge's scope:
- plan:103 and plan:173 cite make-patches:78-84 for apply_patches. The function is actually at make-patches:63-69.
- `git diff-tree -p` for a new empty file emits no ---/+++ lines (I observed this). plan:178-179 makes a missing ---/+++ pair an exit-3 error. If the directory interface that gate (c) calls parses targets, that is one more way for (c) to fail after the writes.

Experiment: All work was done in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C27/. I copied tools/ to toolscopy/ and set PYTHONDONTWRITEBYTECODE=1. The real repositories were not touched.

(1) Ran toolscopy/tests/test_make_patches.sh in mp-work/: 28 passed. Afterwards mp-work/pkg/patches/R holds bin-tool.patch, etc-x.patch and src-Pure-a.ML.patch, but not src-Pure-new.ML.patch. provenance.txt says release_tag R/feat/2, although `git diff-tree --name-only R/base/2 R/feat/2` lists 4 files. The refused mode-change run deleted the fourth file.

(2) The script /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C27/scenario.sh continues from that state:
- It makes a clean release 3.
- It then runs release 4 with a fake `patch` on PATH that fails when given -R.
- Result with the original script: "refused: gate (c): bin-tool.patch does not apply in reverse", exit 1. The sha256 of src-Pure-new.ML.patch changed, and the file now contains '+(* v4 *)'. provenance.txt still says release_tag R/feat/3 with the v3 commit. The tags are only R/feat/1, 2 and 3.

(3) A prototype fix at /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C27/toolsfixed/make-patches generates the patches into the temporary directory of gate (c) and copies them into patches/<R>/ only after (c) passes. Results:
- The same scenario prints "UNCHANGED" (identical sha256 before and after).
- The toy test still passes 28 of 28, and after the mode-change refusal the package directory still holds all 4 patch files of R/feat/2 plus their provenance.txt.

(4) Python os.rename of a directory onto a non-empty directory fails with Errno 39 (ENOTEMPTY). shutil.move nests the source inside the destination (['old', 'src']). /tmp is tmpfs while the package directories are on ext4.

(5) GNU patch 2.7.6 applies the git blocks for a new symlink and a new empty file correctly (the tree hashes match), so gate (c) does not fail on those. But the empty-file block has no ---/+++ lines.

Recommended fix: Change make-patches so that nothing touches the package directory until every check, gate (c) included, has passed:

1. Generate the split patch blocks into the TemporaryDirectory that gate (c) already creates (make-patches:175), and keep the header, mode and binary checks inside that loop.
2. Run gate (c) on the generated files there.
3. Compute the provenance text, including tree_hash_excluding.
4. Only then delete the old patches/<R>/*.patch, copy the generated files in, and write provenance.txt.
5. Create the tag last, as today.

Do not literally move the directory: rename fails on a non-empty target and across filesystems, and shutil.move nests the source inside the destination.

Also:
- Put the "isabelle-patch-control must be on PATH" check from decision 5 together with the other gates, before generation.
- Update the docstring at make-patches:10 to say this.
- Add one toy check: after the existing "a mode change is not released" case (test_make_patches.sh:105), and after one forced gate (c) failure, the sha256 of every file under pkg/patches is unchanged.

In the plan, decision 5 (plan:173-174) should state this guarantee in one sentence, and §6 should list the toy check. Also correct the plan's citation make-patches:78-84 (plan:103 and plan:173) to make-patches:63-69. The output format does not change, as plan:332 requires.

**Judge: confirmed → author_fixes_no_rereview.** Change make-patches so that nothing touches the package directory until gate (c) has passed:
- generate the blocks into gate (c)'s temporary directory, keeping the header, mode and binary checks there;
- run gate (c) there;
- compute the provenance;
- only then delete the old patches/<R>/*.patch, copy the new files in, and write provenance.txt;
- create the tag last, as today.
Do not rename the directory into place: rename fails on a non-empty target and across filesystems, and shutil.move nests the source inside the destination.
State this guarantee in decision 5, and update the docstring at make-patches:10. Add a toy check that a refused mode change and a forced gate (c) failure leave every file under pkg/patches unchanged (by sha256).

### C28 [minor] New terms duplicate glossary concepts, and the status words collide with existing ones

Section: Terminology (plan:14-15); decisions 3, 4, 9; §4 (plan:141, 218, 265)  ·  merged from: consistency-C22

**Statement.** The migration glossary already names the concept of the first k chain nodes pre-applied in the build, and the file that records it: 'k ... 写在 isabelle 包内的一个文件里' (ISABELLE_GIT_MIGRATION_PLAN.md:47), called 'the k file inside the package' at :570. The plan coins '内置 feature' and '内置清单', plus the status words 'built-in', 'bundled' and 'covered'. In the same glossary, 'built-in' and 'bundled' already name the two sections of etc/components (:13-15). The plan then uses 'bundled' a second time, for the Isabelle2024 directories (plan:218). The owner's rule forbids coining words and makes the glossary authoritative (CLAUDE.md 'Consistent Terminology'). Status words are also user-facing text, which must be proposed to the owner (§7 item 5 lists only file names).

**Editor.** Valid. The plan does define its new terms, which softens the defect. The collision of 'built-in'/'bundled' with the etc/components sections is the real problem. If C3's relaxation is adopted, 'covered' disappears anyway.

**Defender: partially_confirmed** (needs owner: True).

Short version: the challenge is right that the plan gives a second name to something the migration plan already names, and right about one real word collision ("built-in"). Several of its specific claims do not hold.

What survives:

1. Two names for one concept. In the migration plan, the features the conda build has already applied are always called "前 k 节" (the first k chain nodes): ISABELLE_GIT_MIGRATION_PLAN.md:133, 215-216, 393, 412-413, 421, 424. Its §6 step 4 (:496) and RECORD.md:152 call the tool's job here "前 k 节识别" (recognising the first k nodes). The plan adds a new noun for the same thing, "内置 feature" (plan:14, 15, 47, 135, 151, 155, 157, 165, 245), and still uses "前 k 节" alongside it (plan:14, 26, 39, 155, 158, 248). The decision 4 heading, "内置 feature 的识别（前 k 节）" (plan:155), shows the two are meant as synonyms. The same happens with the file: migration :570 calls it "包内 k 文件" (the k file inside the package), while the plan says "内置清单" twelve times (plan:15, 138, 157, 163, 170, 197, 245, 255, 273, 286, 306, 308). CLAUDE.md "Consistent Terminology" asks for one name per concept. Two things soften this. The plan defines both nouns up front (plan:6, 14-15), so they were not coined on the fly. And migration :570 explicitly leaves the file name to this plan, which supplies one (plan:157, §7 item 5 at plan:306). But it only had to supply a file name, not a second concept noun.

2. A real word collision on "built-in". The plan's status label "built-in" (plan:138, 141, 265) and its file name etc/ISABELLE_BUILT_IN_FEATURES (plan:157) reuse the heading "#built-in components". That heading is on line 1 of etc/components, both in the shared tree and in the published build (/home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0/isa/etc/components:1). The migration glossary refers to it at :13-14. The new file would sit in that same etc/ directory, and the CI script already edits etc/components there (pack.sh:214). The two uses mean different things. In Isabelle, "built-in" means "part of the source repository", and anything a packaging step adds on top is "bundled" (build_release.scala:173-188). The pre-applied features are added on top by the conda CI before its hg commit (plan:158), so by Isabelle's own split they are not "built-in". No approved document uses "built-in" or "内置" for features (grep of the migration plan, rev3, the light plan and the handoff). The harm is small, because every use is qualified ("components" versus "features").

3. The plan's own list of statuses is inconsistent. The status-line format at plan:141 lists four labels. plan:145-146 and §4 (plan:265) add a fifth, "applied (covered)". The exit-code rule at plan:142 names only built-in/applied, and leaves it to plan:146 ("不算错误", not an error) to imply that "covered" also exits 0.

4. Bolded new terms missing from the glossary. plan:6 promises that every new term is defined in the glossary. But "随包附带的 feature 目录" (feature directories shipped inside the tool's package, plan:218) and "applied (covered)" (plan:145) are bolded as new terms and are not in the glossary at plan:8-20.

What does not hold:

(a) "The migration glossary already names the concept and the file." It does not. The glossary defines only k, the number of pre-applied chain nodes (:47), and says k is written in some file inside the isabelle package. Neither the set of nodes nor the file has a glossary entry. What exists is a phrase used throughout the migration plan ("前 k 节"), plus one noun phrase in the open-questions list (:570).

(b) "'bundled' is a status word." It is not. The statuses are those at plan:141 and plan:265. "bundled" appears only as a directory name and as a provenance-file value (plan:218-219, 258).

(c) "Using 'bundled' for the Isabelle2024 directories is a coinage or collision." The tool already uses "bundled" in exactly this sense, "shipped inside the tool's Python package": cli.py:119 says "Print the bundled agent/usage guide (AGENTS.md)" and reference.md:165 says "Prints the bundled `AGENTS.md`". plan:218 just continues that sense. Isabelle's own "bundled" has the same plain-English meaning ("shipped along with it, not part of the source"), only applied to a different thing. One residual point: "built-in" and "bundled" are near-synonyms in English, and both reach status output — "built-in" as a status, and "none (bundled)" in the release_tag column on Isabelle2024 (plan:141, 219). That is a naming question for the owner, not a defect in "bundled".

(d) "Status words must be proposed, and §7 item 5 lists only file names." The whole plan is a draft awaiting the owner's approval (plan:3), so its status labels are proposals. The same holds for other user-facing text that §7 also does not list, such as the subcommand renames (plan:115) and the messages at plan:125 and plan:152-153. The memory rule requires proposing user-visible text before it is implemented, and the plan does that. Listing the labels in §7 is still the cheap and sensible place for the owner to rule on them.

(e) "'covered' collides with something." No collision found. The migration plan describes this situation (a lower feature's patch reading CONFLICT once a higher feature has changed the same file) only in full sentences (:426, :546-547), and no document I checked uses "covered" as a term. I did not see C3, so I cannot judge the editor's note that C3's relaxation would remove "covered". On its own merits the label is a legitimate proposal.

On the editor's rebuttal: I agree on "built-in" and disagree on "bundled", for the reason in (c). The more substantive part of this challenge is the double naming in point 1, plus the inconsistent status list in point 3. The relaxation field is empty, so there is no relaxation to weigh.

Experiment: I used read-only greps and wrote the results to /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C28/term-occurrences.txt.

For each term — 前 k 节, 内置 feature, 内置清单, built-in, bundled, covered, 随包附带, 包内 k 文件 — I recorded the line numbers where it occurs in the plan and in the migration plan.
- "内置 feature" and "内置清单" appear only in the plan.
- "前 k 节" appears in both.
- "包内 k 文件" appears only at migration :570.
- "built-in" and "bundled" appear in the migration plan only as names of etc/components sections (:14, :611).
- "covered" does not appear in the migration plan.

In the tool repository, "bundled" appears only at cli.py:119 and reference.md:165, both meaning "shipped inside the Python package".

The etc/components headers are "#built-in components" (line 1) and "#bundled components" (line 14), both in the shared tree and in the published build /home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0/isa/etc/components. That build's etc/ directory contains build.props, components, isabelle.css, ISABELLE_ID, ISABELLE_IDENTIFIER, ISABELLE_TAGS, options, settings and symbols, so the proposed ISABELLE_BUILT_IN_FEATURES file would sit next to components.

Finally, I grepped the light plan, the handoff document and the migration plan rev3 for 内置, built-in, bundled and covered. None of them uses these words for features.

Recommended fix: These edits are done by hand, as CLAUDE.md requires for plan documents.

(1) Use the migration plan's existing phrases instead of the two new nouns. Write "前 k 节" wherever the plan says "内置 feature", or "前 k 节中的 feature" when one member is meant. Rename the decision 4 heading to "前 k 节识别", as in migration :496. Write "包内 k 文件" (migration :570) wherever the plan says "内置清单", keeping etc/ISABELLE_BUILT_IN_FEATURES as its proposed file name. Then delete the glossary entries at plan:14-15, or turn them into pointers to migration :47 and :570.

(2) Make plan:141 list the same five statuses as plan:265, and state in plan:142 that applied (covered) counts as ok for the exit code.

(3) Either add "随包附带的 feature 目录" and "applied (covered)" to the glossary, or remove their bold.

(4) Extend §7 item 5 so the owner rules on all the new user-visible words: the status labels built-in and applied (covered), the Isabelle2024 directory name bundled/, and the provenance value none (bundled). Note there that etc/ISABELLE_BUILT_IN_FEATURES and the built-in label reuse the word in the "#built-in components" heading of etc/components next door. Leave the bundled/ name as it is unless the owner says otherwise, because it matches the tool's existing "bundled" (cli.py:119, reference.md:165).

**Judge: partially_confirmed → author_fixes_no_rereview.** Use the migration plan's existing phrases: "前 k 节" (the first k chain nodes) for the concept, and "包内 k 文件" (the k file inside the package, migration :570) for the file. Keep etc/ISABELLE_BUILT_IN_FEATURES only as the proposed file name. Turn the glossary entries at plan:14-15 into pointers to the migration glossary.
After C3 and C7, the status labels are built-in | applied | half-applied | not-applied | CONFLICT. Make plan:141, plan:265 and the exit-code rule agree with that list.
In §7 item 5, list every new user-visible word and message for the owner to approve verbatim. Note there that "built-in" collides with the "#built-in components" heading of etc/components, which sits in the same etc/ directory as the proposed manifest.
Refuted parts: "bundled" is not a status word, and it continues the tool's existing sense (cli.py:119, reference.md:165). The migration glossary does not name the set or the file.

### C29 [minor] Several rulings are attributed to the wrong source, and several citations are wrong or stale

Section: §0 items 2, 8, 9; §2; §8; §9; decision 10  ·  merged from: consistency-C23, consistency-C24

**Statement.** Substantive errors. (1) §0.2 attributes the tool's patch-free status to ruling 8 (plan:25), which concerns isabelle-packaging-ci (ISABELLE_GIT_MIGRATION_PLAN.md:64). For the tool it comes from D1 and §5.3. Stated without qualification, it also contradicts decision 9's bundled patches. (2) Ruling 15 (Q4) registers skip_nitpick_examples as a patch directory inside dev_patches (:74-76). Decision 10 merges the four directories into one flat set plus a README section (plan:237) without noting that this changes the ruled form. (3) The plan relies on CONDA_ISABELLE_BRIDGE.md as a constraint (plan:124, 331), but PACKAGING_DESIGN.md:1026 marks that document as superseded. (4) §8 rests decision 8 on link order and cites link.py's `reversed(...)` for unlink order (plan:318-320). That reversed() (link.py:1042) is the rollback; unlink order comes from conda/core/solve.py:1450-1452, and in any case all packages are linked before any post-link runs (C4). (5) The gate (c) stand-in is at tools/make-patches:63-69, not :78-84 (plan:103, 173). Trivial offsets, also wrong: pyproject.toml name and version are at :6-7 and package-data at :39-40, not :5-6 and :44-46 (plan:70); `:11,47-75` are patches/__init__.py lines, not categories.toml lines (plan:59); there are four patches/*.md files plus patches/Isabelle2025-2/register_thy.md, not 'five patches/*.md' (plan:239); and '14 cores' does not appear at RECORD.md:82, where HOL took 6 minutes within a `-j 3` run of 16 sessions (plan:212, 324).

**Editor.** Items (1)-(4) matter, because §0 is meant to be an exact record of rulings and §8 is meant to be the evidence. The line-offset items are nitpicks, kept only because the plan's own convention is file:line for every claim.

**Defender: partially_confirmed** (needs owner: False).

I tested each sub-item against the sources.

(1) The attribution error is real; the contradiction claim is weak. The plan's §0.2 (plan:25) cites only ruling 8 for "the tool becomes a pure framework with no patches". Ruling 8 (ISABELLE_GIT_MIGRATION_PLAN.md:64) and the ruling it confirms, ruling 7 (:63), only talk about isabelle-packaging-ci. For the tool, the source is D1 clause 3, "isabelle_patch_control 逐步改成不带任何预置补丁的纯框架" (:121), which :131 keeps via §5.3 (:408-409).
- Mitigation: the approved migration plan itself lumps the two together at :211 ("补丁工具与 CI 不再带任何补丁（第 8、21 条，§5.3）"), so the plan inherited the lumping. But it also dropped the two parts that actually cover the tool (ruling 21 and §5.3).
- On the contradiction with decision 9: D1's end state is unqualified but reached gradually ("逐步"). The same §0 qualifies item 2 in three places: item 7 (plan:31-32) leaves the Isabelle2024 question open, item 8 (plan:35) restates "逐步", and item 10 (plan:38) says "Isabelle2025-2 这条线上不再带补丁". So decision 9 (plan:218-222) is an interim state D1 allows, not a breach of a ruling. What remains is wording: item 2 alone reads as if version 1.0.0 is patch-free, yet decision 9 ships the Isabelle2024 patches inside 1.0.0.

(2) The letter of the claim is refuted; the substance is confirmed. The plan does note the merge explicitly: "四个补丁目录在包里不再区分：一个 feature、一份清单" (plan:237). So "without noting" is false. The migration plan also hands the layout to this plan: "目录布局按补丁工具 features.d 的设计" (:385-386). So the plan may choose a flat layout.
- What is missing: ruling 15 Q4 (:74-76) and the glossary (:19-21) name skip_nitpick_examples as a patch directory inside dev_patches. The plan never says that its choice changes the form this binding ruling names, and it does not put the question to the owner in §7.
- What survives anyway: the name lives on as its own commit 30aab6e (RECORD.md:49) and as a README section (plan:237).

(3) Confirmed, with one addition. PACKAGING_DESIGN.md:1026 marks CONDA_ISABELLE_BRIDGE.md as "探索期产物,均已被本文档取代,仅供考古" (exploration-era, superseded, for archaeology only).
- Addition: plan:331 also misreads bridge :75-77. That passage says only one aoa env can be active at a time, because the old design shared one global etc/components under a fixed ISABELLE_HOME_USER. It says nothing about two Isabelle trees in one env. The current design gives each env its own ISABELLE_HOME_USER (pack.sh:174-176).
- The design choices themselves survive under current sources:
  - pack.sh:175-176 derives paths from ISABELLE_HOME, "correct even without conda activate".
  - Isabelle_RPC conda/recipe.yaml:122 finds the env via `$COMPONENT/../..`, not CONDA_PREFIX.
  - isabelle conda/recipe.yaml:118-121 records that a nonzero post-link exit rolls back the install, and :179-181 records that scripts get only PREFIX and PKG_NAME.
- So the fix is re-citation (plan:91, 124, 331), not redesign.

(4) Confirmed. link.py calls `reversed` in only two places, :1042 and :1154, and both are rollback (the second inside _reverse_actions). The unlink order comes from solve.py:1450-1452: reverse topological order over `previous_records = IndexedSet(PrefixGraph(...).graph)` (:1412). The link order comes from :1453.
- In link.py `_execute`, every pre-unlink script runs before any package is unlinked (:938-947).
- Packages are linked in a block that may run in parallel (:949-954), and only afterwards do post-link scripts run, one at a time, in the link-group order (:961-967). So the reason given at plan:204-205 ("conda 按依赖顺序链接包，所以…") is wrong.
- The conclusion still holds (see the experiment), so only the evidence and that sentence need fixing.

(5) Mostly confirmed, one sub-item refuted, the rest trivial.
- Gate (c) stand-in: confirmed. `apply_patches` is at tools/make-patches:63-69 and is called at :179 and :183. The plan's :78-84 (plan:103, 173) falls on `archive`/`feature_release`.
- pyproject.toml: confirmed. name and version are at :6-7, not :5-6, and package-data is at :39-40, not :44-46. The file has only 40 lines and was last changed 2026-07-12, so this is a plain error, not a stale offset.
- `:11,47-75` (plan:59): refuted. The plan's convention is that a bare `:N` continues the last file it cited, as with `:106-121` (plan:59) and `:82-103` (plan:62). Read that way, these are patches/__init__.py lines, and they cite the right code: CATEGORIES at :11, and the table loader plus the exit-3 check for unregistered features at :47-75. At most the reference could be spelled out for clarity.
- "五份 patches/*.md" (plan:239): the count of five documents is right; only the glob is wrong, since register_thy.md lives in patches/Isabelle2025-2/. That directory is deleted in the same sentence, so nothing is missed.
- "14 核" (plan:212, 324): it is not in RECORD.md:82, which says only "HOL 6 分" inside a 31-minute `-j 3` run. The machine has 14 logical CPUs but 12 physical cores (`nproc` = 14; `LANG=C lscpu`: 12 cores per socket). step2-heaps.log:26-31 shows HOL took 5:55 with factor 3.93, and only two sessions of 3 s and 5 s ran beside it. So the 6-minute figure is fair, but "14 核" is both unsourced and inaccurate.

The editor's rebuttal is right that items (1)-(4) matter, because §0 is meant to record the rulings exactly and §8 is meant to be the evidence. But (1) and (2) are narrower than stated, as shown above. The relaxation is empty.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc/defender-C29/

order.py builds a toy chain of PackageRecords (isabelle, isabelle-patch-control, and three feature packages pinned in a chain) using conda 25.11.1's own PrefixGraph, then applies the sorting from solve.py:1450-1453. Over 5 random input orders, the link order was always isabelle, patch-control, expose-foreign, future-assign-interrupt, light-locale, and the unlink order was always the exact reverse. So the plan's conclusion in §8 is right; only its citation (link.py's rollback `reversed`) is wrong.

I also read link.py:885-1060. Pre-unlink scripts all run before any unlink. All links finish before the post-link scripts, which then run one at a time in group order.

Other checks:
- `grep reversed core/link.py` finds only :1042 and :1154.
- tools/ is untracked; make-patches mtime is 2026-10-22 19:40, earlier than the plan's 23:01, so :78-84 was already wrong when the plan was saved.
- pyproject.toml is 40 lines, last commit 2026-07-12.
- `find patches -name '*.md'` lists 4 at top level plus Isabelle2025-2/register_thy.md.
- nproc = 14; `LANG=C lscpu` shows 12 cores per socket.
- step2-heaps.log:23-31: HOL 0:05:55, factor 3.93, built essentially alone.
- PACKAGING_DESIGN.md:1026 has the supersession line; pack.sh:175-176 has the "correct even without conda activate" comment.

Recommended fix: Hand edits only, no scripts:
1. §0.2 (plan:25): split the item. The tool becomes, step by step, a pure framework with no patches, and from 1.0.0 it carries no Isabelle2025-2 patches (D1 clause 3, migration plan :121/:131; §5.3 :408-409; Isabelle2024 is item 7). isabelle-packaging-ci becomes a pure framework (ruling 8).
2. Decision 10 (plan:237): add one sentence: "Ruling 15 (Q4) names skip_nitpick_examples a patch directory inside dev_patches; in the package it survives as commit 30aab6e and as a README section, not as a directory (the migration plan :385-386 leaves the layout to this plan)." Add this as a question in §7.
3. Replace CONDA_ISABELLE_BRIDGE.md citations: plan:91 → recipe.yaml:118-121,179-181; plan:124 → pack.sh:175-176 and Isabelle_RPC conda/recipe.yaml:122. At plan:331, drop the bridge citation and say one env holds one tree at $PREFIX/isa (recipe.yaml:75-87).
4. §8 (plan:318-320) and decision 8 (plan:204-205): cite solve.py:1450-1453 for the unlink and link order, and link.py:938-967 for "every pre-unlink before any unlink; every package linked before the post-link scripts, which run one at a time in dependency order". Drop the link.py `reversed` citation.
5. Offsets: make-patches:78-84 → :63-69 (called at :179, :183), at plan:103 and plan:173. pyproject.toml :5-6 → :6-7 and :44-46 → :39-40. Optionally spell out `patches/__init__.py:11,47-75` at plan:59. At plan:239 write "four patches/*.md plus patches/Isabelle2025-2/register_thy.md". At plan:212 and plan:324, drop "14 核" (or write "this machine, 14 logical CPUs, HOL built essentially alone, step2-heaps.log:31").

**Judge: partially_confirmed → author_fixes_no_rereview.** Fix the attributions and citations by hand:
- §0.2: split it. The tool becomes patch-free step by step, per D1 clause 3 (migration :121, :131) and §5.3 (:408-409); isabelle-packaging-ci becomes patch-free per ruling 8.
- Decision 10: note that ruling 15 Q4 names skip_nitpick_examples a patch directory inside dev_patches, which in the package survives as commit 30aab6e and a README section, and add this to §7.
- Replace citations of the superseded CONDA_ISABELLE_BRIDGE.md: plan:91 by recipe.yaml:118-121, 179-181; plan:124 by pack.sh:175-176; plan:331 by recipe.yaml:75-87.
- §8 and decision 8: cite solve.py:1450-1453 for the link and unlink order, and link.py:938-967 for when scripts run; the `reversed` at link.py:1042 is the rollback.
- Offsets: make-patches :63-69; pyproject.toml :6-7 and :39-40; four patches/*.md plus patches/Isabelle2025-2/register_thy.md.
- Drop "14 核" (the machine has 14 logical CPUs and 12 cores; HOL took 5:55, built essentially alone).
Refuted part: `:11,47-75` at plan:59 correctly continues patches/__init__.py.
