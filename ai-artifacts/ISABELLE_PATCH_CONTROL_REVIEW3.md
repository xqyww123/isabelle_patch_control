# isabelle_patch_control plan rev 3 — review 3 (workflow wf_130068f2-2bb, 2026-10-24)

Critics: 62 findings (5 lenses). Merge editor: 32 challenges, 3 dropped. One fresh defender per challenge. Judge: ready = False.

## Judge summary

Verdict: rev 3 is NOT ready for the owner's approval. Section 0 records the owner's rulings faithfully, but three of the mechanisms that implement them do not do what the plan says. On top of that, seven questions are open that only the owner can answer.

THE THREE BROKEN MECHANISMS
(1) The conda hook layer.
- The isabelle package's pre-unlink deletes the environment's whole Isabelle user directory (isabelle-packaging-ci/conda/recipe.yaml:223-230), and that directory holds every component registration.
- So the plan's universal repair command, `conda install --force-reinstall isabelle` (plan:367, :450, :549-550, :560-561), leaves light's patches applied but its Light_Locale session unregistered. Every isabelle relink also unregisters the AoA component packages, including the first move off 2025.2-0 (C1).
- Removing duplicate diagnoses by re-reading .messages.txt cannot work, because conda prints and deletes that file after every script (link.py:1685, :1697-1708) (C8).
- conda's rollback of an interrupted transaction deletes conda-meta/history, so Appendix A's recovery is false (C11).
(2) The engine.
- The target-listing call `git apply --numstat --summary` runs outside decision 4's isolation. From any subdirectory of a git work tree it prints nothing with rc 0, so every feature reads applied. I reproduced this in review-ipc3/judge/ns/ (C2).
- The tie-break for a file that sits at several levels fails at every intermediate target, including each pre-unlink (C7).
- The level definition uses a feature number as a position in the list of features that touch the file (C18).
- An exit code of 128 during a write-mode replay blames a correct patch file (C17).
- The write path is exported in pieces and replays every file twice (C19).
(3) The batch release workflow (decision 11).
- Each of the five legs builds its own noarch bytes, so 'the same artifact' is undefined (C5).
- A re-run for a new isabelle build rebuilds the tool package under its already-published filename, and the publish guard refuses the whole batch (C3).
- The eight 'serial' publish-conda.yml calls are in reality one publish followed by seven no-ops, because publish-conda.yml uploads every .conda in the artifact (publish-conda.yml:148-203) (C6).
- The release tags it checks out are created by nothing, and two of the package repositories do not exist (C4).
- (b2), the round-trip check, is bound to a release only by an unverified checkbox (C12).
- All five-leg acceptance, including the first ever run of the .bat hooks, happens only after the pristine isabelle build is irreversibly published (C10).

SILENT DEVIATIONS
Several round-2 and round-1 judge actions were dropped or replaced without §10 saying so:
- the C17 diagnosis rule (C8);
- 'the Windows leg compares bytes' (C20);
- the CI artifact of a named run (C10);
- the build string Isabelle2025_2_N (C14);
- the 0.x pointer in the CONFLICT text, and always printing the tree (C27);
- the private package cache for the smoke test (C15);
- round-1 C26's consequence sentence on shared user directories (C25);
- the fix of rev 2's plan:221-222 (C19).
One contradiction stands with a recorded ruling: ruling 22 says 'any other ISABELLE_ID exits 3', but decisions 2 and 3 exit 0 in a tool-only environment (C9).

WHERE I RE-CHECKED SOURCES BECAUSE DEFENDER AND EDITOR DISAGREED
- C3: deleting the feature build_number input does NOT contradict ruling 22. The input the owner approved is the isabelle build number (jsonl 6566: 'workflow 接一个“isabelle build 号”输入'). The build_number input came from the round-2 C21 judge (REVIEW2:2699), so replacing it by a derivation is allowed, but §10 must say so.
- C20: the C20 defender's claim that 'no feature touches etc/' is false. `git diff --name-only Isabelle2025-2/pristine/89701cf1768e Isabelle2025-2/dev_patches -- etc` lists etc/options, and pack.sh also edits that file (defender-C19 measured the ML_system_64 difference at etc/options:193). So any absolute byte oracle needs an exception for files the packaging also edits.
- C27: the defender's hard-link finding holds (defender-C27/run.out). An edit written in place through the hard link, as vim's backupcopy=auto does, also changes the package cache. `--force-reinstall isabelle` then does not restore the file, so every 'restores the package's files' remedy text is false in that case.
- C1: the defender is right that light's own registration survives `conda update --all` and the first feature install, because the exact pin relinks light. The loss of light's registration happens only after `--force-reinstall isabelle`.
- C6: §0 item 25 quotes text the owner approved (jsonl 6818, approved at 6823). So changing to one publish call is an owner question, not an error in the paraphrase.
- C29: I checked the second cached build: ISABELLE_ID 89701cf1768e and ml_name_space.ML:67 '["Signal"]'.
- C16: I checked that lib/browser_info.db and Find_Facts' isabelle.db are in the official tarball but not in the package.

TWO FINDINGS OF MY OWN, OUTSIDE THE CHALLENGES
(a) The Banner step of publish-conda.yml (:223-227) breaks every publication, including §5 step 6's release.yml.
- It runs scripts/banner-index.py in a job that has no checkout step (grep finds no 'checkout' in the file).
- It then asserts the string 'conda install -c https://conda.qiyuan.me', which neither conda/channel-banner.html nor the script contains (the banner says 'conda update', at channel-banner.html:10).
- So, as written, the step fails after the .conda files are uploaded (:193-203) and before the index is pushed (:229). I did not run this on GitHub.
- Decision 12 must require the CI plan to fix it before step 6.
(b) Files of packages being unlinked can still be on disk while post-link hooks run.
- conda renames each unlinked file to <path>.c~ (path_actions.py:1152-1164, constants.py:180) and deletes those copies only after every post-link has run (link.py:1057-1060).
- So during a post-link, features.d/<f>/ can hold *.patch.c~ and provenance.txt.c~ copies.
- Decisions 2 and 3 must say that the tool reads exactly provenance.txt and *.patch, and that a feature subdirectory without provenance.txt counts as absent, not as an error. Add one hook-layer case.

CHALLENGE OUTCOMES
- None of the 32 challenges is refuted outright.
- Many are narrowed. The most important narrowings are C1's scope, C9's §4 sub-claim, C10's harm, C22's cross-environment point (round 2 already accepted it), C28's race (impossible by data dependency) and C32's consequence.
- The author should make the owner-independent fixes and put questions Q1-Q7 to the owner. A round-4 review should then re-check decisions 4-7, 9, 11, 12 and 16.

## Questions for the owner

Q1 (C1, component registrations). When the isabelle package is relinked, its pre-unlink deletes the environment's whole Isabelle user directory, including the file etc/components in which `isabelle components -u` records every component (isabelle-packaging-ci/conda/recipe.yaml:223-230). A relink happens on `conda install --force-reinstall isabelle` (the plan's repair command) and on every update to a new isabelle build. After it, Isabelle_RPC, Performant_Isabelle_ML, Semantic_Embedding, Isa-Mini, auto_sledgehammer and, after a force-reinstall, Light_Locale are silently no longer registered. Which fix should the CI plan carry?
(a) Recommended: from the pristine build on, the isabelle pre-unlink keeps etc/components and deletes it only when it lists nothing. On a real removal, conda runs every component's own `components -x` first, so nothing is left behind (measured). This is one recipe change, with no change to any component recipe.
(b) Every component package ships a marker file, and the isabelle post-link re-registers every marker. This needs a re-release of every component package and a filter for conda's temporary .c~ files.
(c) Nothing changes in CI; every repair text names the component packages to reinstall along with isabelle.
Under (a) and (c), the first move off the already published isabelle-2025.2-0 still unregisters every component once, because 2025.2-0's own pre-unlink cannot be changed. The release note would tell users to run `conda install --force-reinstall <their component packages>`. Under (b), components re-released with markers recover by themselves.

Q2 (C6, publishing order). You approved calling publish-conda.yml once per package, in dependency order (question 6, option (a)). publish-conda.yml uploads every package in the artifact it is given, so in practice eight calls on one artifact are one publish followed by seven calls that do nothing. Which shape do you want?
(a) Recommended: a single call on the whole tested batch. All the packages are noarch and share one index file, so one index push makes the whole batch visible at once; no feature is ever visible before its base. The batch is refused all or nothing, and the channel is pulled once.
(b) Keep one call per package: cut the tested artifact into one artifact per package. The order then becomes real, at the cost of eight whole-channel pulls and a half-released batch if one call is refused.

Q3 (C7, what a feature may contain). May an upper feature delete, rename or fully revert a change made by a lower feature, for example dev_patches deleting a file that light_locale created? Such a file looks the same at two levels (before the lower feature and after the upper one), and no rule can tell which is meant: the plan's rule gives false conflicts or wrong moves at intermediate targets, including each package's pre-unlink.
(a) Recommended: no. make-patches refuses such a feature, the change goes into a new release of the lower feature instead (rulings 21 and 22 re-release in batch anyway), and the tool treats any file that fits several levels as CONFLICT. The real chain passes this today (0 revisits).
(b) Yes. Then the plan needs a different state model, for example a record of what was applied, which you rejected earlier.

Q4 (C9, a tool-only environment on the old build). Ruling 22 as recorded says the tool exits 3 on any tree whose etc/ISABELLE_ID is not the official changeset. But in an environment on isabelle-2025.2-0 that holds only the tool and no feature package, the design prints 'no feature packages installed' and exits 0. What should happen?
(a) Exit 3 with the hint `conda update --all`, as recorded. The tool then has to carry a small table from release name to official changeset.
(b) Recommended: exit 0 with 'no feature packages installed', because there is nothing to apply. Whenever a feature package is present on such a tree, the tool still exits 3 with the hint. This amends the recorded consequence of ruling 22.

Q5 (C14, feature build string). Migration ruling 27 fixes the feature package build string as Isabelle2025_2_<build number>, for example Isabelle2025_2_0. Rev 3 proposes Isabelle2025_2_<isabelle build number>_<build number>, for example Isabelle2025_2_1_0, so that `conda list` shows which isabelle build each feature package belongs to. The cost is an amendment of ruling 27 and a few more path characters, which still fit the Windows budget. Published filenames are permanent, so this must be settled before the first release.
(a) Approve the new form.
(b) Keep Isabelle2025_2_<n>.

Q6 (C25, shared user directories). The isabelle package names each environment's Isabelle user directory after the last component of its prefix (`~/.isabelle/Isabelle2025-2-conda-<basename>`), a packaging edit that ruling 20 keeps. Two environments such as `-p ~/a/env` and `-p ~/b/env` therefore share heaps and component registrations. With feature packages, one environment can silently load the other's patched heap, and either one's isabelle reinstall deletes the other's state. This already breaks today with 'Duplicate session'.
(a) Allow the CI plan to append a short hash of the resolved prefix to that suffix.
(b) Keep the suffix and document the limitation in the post-link message and the README.

Q7 (C31, confirm a reading). Ruling 23 says 'pyproject.toml 的名字保留'. Please confirm that this means the field stays (unpublished) with the renamed value `isabelle-patch-control`. If the old value `my-better-isabelle-prover` were kept, the README's own instruction `pip uninstall my-better-isabelle-prover` would remove the new conda tool (measured).

## Relaxations recommended

1. Engine (C2, C17, C19, C30):
- One private primitive is the only code that starts git. It builds the whitelist environment, the -c flags, the ceiling and the umask, and runs only in a directory the engine created.
- Every patch file must list exactly one target.
- The level replay runs once, and the tool installs its own snapshot, so the bytes status predicts are the bytes installed by construction.
- Exit codes are classified by phase: parse errors only in the listing pass; during the replay, 1 means 'does not fit' and anything else means a write failure.

2. Levels (C7, C18):
- Define levels over sets of feature numbers, with a per-file target level T_p, so files the target feature does not touch never move.
- With the owner's consent, a make-patches gate refuses content revisits, and any file at several levels is CONFLICT everywhere.

3. Batch workflow (C3, C5, C6, C10, C12):
- Build once on ubuntu and test the same artifact on five legs.
- Reuse packages already on the channel and derive each new build number from the channel.
- Publish the tested artifact with one publish-conda.yml call, if the owner agrees.
- Rehearse against a named isabelle-packaging-ci run's artifact before anything is published.
- Run (b2) as a gating CI job on the shipped bytes, with both tags derived from the tree and the provenance files.

4. Package repositories (C4):
- make-patches commits patches/<R>/ and creates the same release tag in the package repository.
- It refuses a second release tag of the same feature on one commit.
- A fixed table maps each feature to its (repository, subdirectory), and `features` is an explicit list of tags.

5. Hooks and messages (C8, C23):
- Diagnoses are assigned by $PKG_NAME: only the isabelle hook and the chain-top feature's hook write the full diagnosis.
- Every pre-unlink that leaves its own feature's files behind writes the residue block, whatever the cause; 'Retry later' is never written by a pre-unlink.

6. Component registrations survive an isabelle relink by construction (C1): preferably the isabelle pre-unlink keeps etc/components until it is empty (owner question Q1).

7. Bytes (C20): an absolute byte check from the patch files' `index` blob ids after apply, and from conda-meta paths_data sha256 after unapply, with an explicit exception for files the packaging also edits (today etc/options).

8. Windows lock (C22): lock one byte at the fixed offset 0x40000000, so no reader of etc/ISABELLE_ID can ever overlap it.

9. Single sources of truth:
- one tool-owned README text, copied verbatim into every feature package (C26);
- a byte-for-byte check of the published isabelle post-link against the tool's hook fragment files (C24);
- one engine constant for the lock file, shared by make-patches' release gate and the runtime refusal (C32).

10. Judge's addition: the tool reads exactly provenance.txt and *.patch in each feature directory, and treats a directory without provenance.txt as absent. During post-link, conda keeps unlinked files as <path>.c~ (path_actions.py:1152-1164; cleanup at link.py:1057-1060).

11. Decision 12 additions for the CI plan:
- fix publish-conda.yml's Banner step (no checkout step; it asserts a string nobody writes; publish-conda.yml:223-227) before §5 step 6;
- correct publish-conda.yml's stale package_name description (:55);
- correct recipe.yaml:106's 'no untracked files' claim.

## Critics' overall notes

- conda: I re-checked rev 3 through the conda lens: conda 25.11.1 source, the CI and consumer recipes, and toy file:// channels built with the plan's hook texts copied verbatim and a toy tool that applies the patches with real git apply. Scripts and outputs are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/critic-conda/: mkchan.py, run.sh/run.out, run2.sh/run2.out/run2-tie.out, run3.sh/run3.out, run4.sh/run4.out, crlf/, pyshadow/, gen-naive.sh.

**What holds, measured:**
- **Rulings 20-25 in the hook layer.** The post-link fragment ends in exit 0 in its own text. Installs succeed, with conda-meta/history intact, when the tool is absent and when it crashes at start-up. The elif branch reports correctly. The pre-unlink fallback exits 0. The fragment works before the CI post-link's final exit 0.
- **light's component lines** register and unregister in a normal install and removal.
- **Fresh install:** one applied line and one heap notice.
- **clone:** reproduces the same tree and the same registrations.
- **conda remove isabelle:** leaves no isa/.
- **Exact build pins (item 22).** On the old 5533cd83156e build, installing a feature upgrades isabelle. A new build without re-released features does not move under `conda update --all`, and an explicit install conflicts. After a re-release with a raised build number, `conda update --all` moves everything, and `conda update isa` alone does not.
- **Smaller checks:** the prefix pin `==1=Isabelle2025_2_*` resolves; the single prefix P and the conda-meta directory test are sound; the path lengths are fine (I measure 155, not 154).

**What does not hold:**
- **Message rules.** Deduping full diagnoses by re-reading .messages.txt cannot work, because conda deletes that file after every script; I measured three identical diagnoses. The round-2 judge's rule was replaced without saying so (conda-5).
- **Relinking isabelle.** Its pre-unlink wipes the user directory. So the plan's own remedy, `--force-reinstall isabelle`, unregisters light's session. Every item-22 isabelle update unregisters all AoA component packages (conda-1).
- **Release workflow.** Four defects:
  - every leg builds its own noarch packages, against ruling 25's order and the CI's 'test the bytes you publish' rule; on win-64 this produces CRLF patches that git apply rejects (conda-3);
  - the rebuilt tool trips publish-conda's immutability guard, so a re-release for a new isabelle build publishes nothing (conda-2);
  - leaving the build number as a manual input that defaults to 0 leaves existing environments stuck on the old isabelle build (conda-4, measured);
  - the eight serial publish calls do not publish in that order, and the smoke test cannot solve without conda-forge (conda-12, conda-6).
- **Hook text, all minor:**
  - the .bat texts are frozen but never written (conda-7);
  - the fragment cannot be copied verbatim into the CI's printf idiom (conda-8);
  - the hook calls the entry point, which can be replaced through PYTHONPATH or the user site (conda-9);
  - lock-busy and tool-missing pre-unlinks leave residue status cannot see, with no recovery steps (conda-10);
  - §6 (i) contradicts decisions 2 and 3 (conda-11).

None of these needs a ruling reversed. Most of the fixes make the invariant hold by construction: build once and test that artifact, compute the build number from the channel, use $PKG_NAME for who writes what, keep the component registrations across a relink, and write the exact .bat text.

- engine: Rev 3 follows rulings 18 and 24 in its overall structure. git apply is the only program that produces patched content. Each file is replayed on a copy in <tree>.staging, then installed with os.replace or os.unlink, one file at a time. git's environment is built from a whitelist, a .git tree is refused, a symlinked target is refused before any replay, the lock is taken on etc/ISABELLE_ID, levels are computed per file with both halves as sequential replays, apply only moves files up under a cap and unapply only moves them down. Nearly all round-2 engine actions for C1, C2, C5, C6, C7, C19 and C20 are in the text.

I prototyped decisions 3-7 as written (scratchpad review-ipc3/critic-engine/ipc.py). The input was the real chain: 42 per-file patches from git diff-tree between the branches of contrib/Isabelle2025-2, applied to a base extracted from the official tarball with pack.sh's etc/options edit. Results:
- status, --dry-run, apply, `unapply --feature dev_patches` and unapply give an exact round trip: byte-equal to the dev_patches tip, then back to the base. Modes stay 0644, no file fits several levels, and no staging directory is left behind.
- Each run makes 126 git calls (42 for target discovery, 84 for the replay) and takes 0.16-0.25 s on Linux. §8's figure of 1.3-2.3 s is stale: it came from round 2's prototype, which ran check plus apply for every step.
- Isolation through the whitelist held in every hostile case: HOME, XDG, GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_COUNT and GIT_CONFIG_PARAMETERS exported; a gitignored prefix with TMPDIR inside the repository; and $PREFIX itself a work-tree root with autocrlf=true. A positive control without the ceiling reproduced round 2's silent no-op.

The remaining defects are in the state model and in where the invariants are enforced:
- (E1, major) The 'same result from every fitting level' rule is right only for the whole-chain targets. At every intermediate target, and each feature's pre-unlink is one, it either reports a false CONFLICT or moves a file down, and status has no word for the state. The plan's own tests (create then delete; rev 1's rename scenario) would fail. The elegant fix: a make-patches gate that forbids content revisits (it passes the real chain today), plus rev 1's 'several fitting levels = CONFLICT'. It restricts what a feature may contain, so the owner should confirm it.
- (E2, major) Target discovery with --numstat --summary is outside git_apply's isolation. Inside a work tree it silently returns no targets, which brings back round 2's silent 'applied'.
- Smaller defects: a write failure that returns 128 is misreported as a corrupt patch (E3); the level notation is ambiguous (E4); the write path is exported in pieces, so 'git only in staging' and 'one path' are left to memory, and the directory interface writes the shared staging path without the lock (E5); the round-2 action to compare bytes on the Windows leg was dropped without saying so (E6); on Windows the tool's own read of ISABELLE_ID overlaps its lock past EOF (E7, not measured).

Performance is acceptable on Linux. A fresh `conda create` with every feature runs about nine hooks, roughly 1,100 git processes. Process-start cost on Windows is not measured.

Experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/critic-engine/: ipc.py, real/gen.py, mktoy.sh, multilevel.sh (output in multilevel.out), revisit_gate.py, hostile/run.sh, hostile/numstat.sh and rc128/run.sh, each with its .out file. Every command against the shared repository was read-only.

- consistency: Lens: consistency with the rulings and the sources. "plan:N" means line N of /home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover/ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md. conda paths are relative to ~/miniconda3/lib/python3.13/site-packages/. All my experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/critic-consistency/.

**What holds up.**
- The quotes of the six new rulings match the transcript word for word (jsonl lines 6307, 6437, 6468, 6569, 6713, 6755, 6823, 6896), and so do their attributions: "作者曾改推荐 isabelle-packaging-ci" and the earlier answer "建议 (2)" are both right.
- Both corrections in §0 are true. Performant_Isabelle_ML.thy:7 loads rescue_foreign.ML, which is in v0.2.0, and Semantic_Embedding/conda/recipe.yaml:338 is a run requirement.
- These line citations are accurate: pack.sh, recipe.yaml, build.yml, make-patches, the tool code, and almost all of the conda source.
- Light creates exactly three files.
- The official tarball carries ISABELLE_ID 89701cf1768e and ISABELLE_IDENTIFIER, so decision 17's base works.
- Two of my measurements back the plan:
  - conda-meta/ exists during the first post-link of a fresh create, so decision 2's test works.
  - §6 (e) works: the solver upgrades isabelle even when the history holds the spec isabelle=2025.2=0.

**What does not hold up.** Several rev-3 mechanisms contradict the very sources they cite, and §10 marks C6, C13 and C17 as resolved when they are not:
- **Messages.** Decision 9 avoids repeated messages by reading .messages.txt first. That cannot work, because conda prints and deletes the file after every single script. I measured it: three hooks printed three diagnoses.
- **Publication.** The batch publish passes "the same artifact" to publish-conda.yml once per package, in dependency order. But publish-conda.yml uploads every .conda file in the artifact on its first call, so the order has no effect. On top of that, the noarch packages are built on all five legs, so "the same artifact" is not defined.
- **Release tags.** The workflow checks out "each feature repository at its release tag". No such tags exist: make-patches tags only isabelle-patched. And a light release that changes only the HOL side (ruling 21) would put two tags on one commit, which gate 0 rejects for every feature above light.
- **Light's session after a repair.** The repair the plan offers everywhere, `--force-reinstall isabelle`, deletes the user directory. That directory holds the record that registers light's session (the `isabelle components -u` entry). The patches come back after the repair; the session does not.
- **git isolation.** `git apply --numstat --summary` (decision 3) runs outside the single isolated git_apply. Inside an enclosing repository it prints nothing and exits 0 (measured). That brings back C1's silent no-op.
- **Ruling 22.** The ruling, as the owner confirmed it, says the tool refuses any other ISABELLE_ID with exit 3. The plan gives exit 0 when no feature package is installed, so §6 (i) cannot pass.
- **Build string.** The new build string Isabelle2025_2_<b>_<n> amends owner ruling 27. The author's own message (jsonl 6566) asked the owner to review it in rev 3, yet the plan records it as settled.
- **Appendix A.** It again states false facts:
  - its list of differences from the official release leaves out two of pack.sh's edits;
  - it misdescribes §7.9;
  - it claims that reinstalling recovers from an interrupted post-link, which is impossible once conda-meta/history is gone.

The smaller findings are: silently dropped judge actions, stale facts, an undefined multi-level display rule, terminology drift, a lock shared across hard-linked environments, an unsolvable smoke command, and a likely Windows failure of §6 (g).

**Verdict.** Not ready. Most fixes are local and leave the design as it is.

- landing: Lens: landing order, release infrastructure and acceptance (decisions 11-17, sections 5 and 6). Abbreviations used in citations: plan = /home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover/ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md; REVIEW2 = the round-2 review file in the same directory; publish-conda.yml, build.yml, release.yml = files under contrib/isabelle-packaging-ci/.github/workflows/; make-patches = contrib/my_better_isabelle_prover/tools/make-patches. My experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/critic-landing/ (pubreplay/, rollback/, rollback2/, smoke/, live/). I modified no repository, installed nothing, and confirmed the owner's conda package cache was untouched.

Verdict for this lens: rev 3 follows the owner's rulings on where things live. There is one batch workflow in the tool repository, the GitHub rename comes first, nothing commits rendered recipes, rattler-build 0.69.1 is listed, there is a live smoke install, and a (b2) script exists. But the release machinery as written does not work, and several acceptance items cannot run or cannot be judged:

(1) The eight "serial" publish-conda.yml calls on one artifact do not happen in order. The first call uploads and indexes every package; the other seven re-publish nothing. I replayed the real step bodies to show this. The author also replaced round-2 relaxation 9 ("one call") without saying so.
(2) Every one of the five legs builds its own packages, so the "same artifact" does not exist, and four legs accept bytes that never ship.
(3) Re-running the workflow for each new isabelle build is routine under ruling 22, yet every such re-run is refused at its first package. The rebuilt isabelle-patch-control 1.0.0 has the same filename with new bytes (replayed).
(4) The workflow checks out tags in package repositories, but no step creates those tags: make-patches tags only the Isabelle repository. Five of the six package repositories have no GitHub remote. This defect was confirmed in round 2 (C12) and is still there.
(5) The whole five-leg acceptance runs only after the pristine isabelle build is published. Until the feature packages follow, the channel serves a pristine isabelle with no features, and its description points users to a package that does not exist. Decision 12 point 7 contradicts decision 11 on this.
(6) The (b2) round-trip check is bound to a release only by a checkbox. The reason given for keeping it off CI is contradicted by the read token that decision 11 itself already requires.

On acceptance:
- Light's component payload (ruling 21) has no registration or unregistration test anywhere.
- Appendix A's recovery "re-install the feature package" after a rolled-back post-link is false. Measured: conda then refuses the prefix as "not a conda environment".
- §6 (i) can never pass: decisions 2 and 3 make a tool-only install on 2025.2-0 exit 0 with "no feature packages installed". This also contradicts ruling 22's stated "every other ISABELLE_ID exits 3".
- §6 (h) cannot run before or at the first release, because only one pristine build will exist.
- The live smoke command cannot be solved, because python and git are not on conda.qiyuan.me (measured).

Smaller items: the secrets are scheduled after the first dry runs need them; no gate keeps the publication in step 8 from racing release.yml's publication in step 6; make-patches has no release-time refusal of patches that touch etc/ISABELLE_ID.

Re-review of decisions 11, 17, §5 and §6 is needed after the fixes. The engine and hook decisions are outside this lens.

- user: From the end user's and maintainer's side, rev 3 follows the owner's rulings 11-25 in shape:
- the pristine isabelle package;
- one package for light's patches and its session;
- exact build pins;
- a conda-only tool;
- staging plus atomic rename;
- one batch workflow in the tool repository.

The happy paths work in a rev-3-shaped toy channel (conda 25.11.1, real git apply). A fresh `conda create isabelle isabelle-light-locale` prints exactly one applied line and one heap notice, and registers the light session. Installing a feature package on the old build makes the solver upgrade isabelle, and the chain gets applied.

The walk-throughs found one blocking defect and six major ones. U1 (blocking): every isabelle relink deletes the per-env user directory and with it every component registration. That covers the CONFLICT remedy `--force-reinstall isabelle`, `conda update --all` to a new build, and the solver's automatic upgrade on the first feature install. Light's own session and the whole hook-registered AoA stack are lost, and conda says nothing. The six major ones:
- U2: rev 3's '.messages.txt' dedupe cannot work, because conda deletes the file after every script. It replaced the round-2 C17 rule without saying so, and conda's PKG_NAME makes that rule implementable without changing the frozen hook fragment.
- U3: Ctrl-C during an install leaves a half-patched tree in an environment conda no longer accepts. The plan's convergence claims are false on that path.
- U4: the batch workflow cannot publish one feature's new version without colliding on the tool or republishing everything.
- U5: feature repositories have no tags to check out, light's shipped HOL files are tied to no tested build, and a HOL-only light release breaks the upper features' gate 0.
- U6: the README misses conda-only/micromamba, how to keep lower packages, and the banner's conflicting update command.
- U7: environments that share a prefix basename now share a user directory across differing trees.

Six minor items cover the publish mechanics, testing the frozen fragment before publication, the exit-3 contradiction, message wording, Windows, and the (b2) checkbox. Evidence (scripts and outputs) is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/critic-user/ (mkchan3.py; run3.sh/run3.out; run4.sh/run4.out; run5.sh/run5.out; run6.sh/run6.out; rd-*.json). No repository, Isabelle tree or owner environment was modified.

## Dropped by the merge editor

- landing-L12: Partial drop: its third point (the workflow name must match the sweep's PUBLISH_WORKFLOW_RE) is wrong in practice. The file is release-features.yml, and without a name: GitHub names its runs by the file path, which matches 'release' (sweep-old-versions.py:70). Its other points are merged into C28.

- consistency-CONS-11: Partial drop: items (e) (155 against 154 path characters; the 198 budget's derivation) and (f) (the dates of the two corrections) are nitpicks. The make-patches gate computes path lengths itself (plan:494-495), and the dates affect no decision. Items (a), (b), (c) and (d) are merged into C28, C29 and C10.

- user-U8: Partial drop: the proposed extra case 'install light into a 2025.2-0 environment' already exists as §6 (e) (plan:594). The rest of U8 is merged into C5, C6 and C15.

## Challenges

### C1 [blocking] Every relink of isabelle unregisters every component, including light's own Light_Locale session, while the plan's remedy and update texts promise automatic recovery

Section: Decision 9 (plan:353-355, :367-371); §4 CONFLICT and residue texts (plan:549-550, :560-561); decision 14 0.x section (plan:450); decision 12 (plan:411-427); §6 (c), (e) (plan:592, :594)  ·  merged from: user-U1, conda-conda-1, consistency-CONS-5

**Statement.** Conventions for all challenges: plan:N is line N of /home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover/ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md; review-ipc3/ is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/; conda source paths are under ~/miniconda3/lib/python3.13/site-packages/conda/; jsonl N is line N of ~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl.

Essence: light's session registration lives in a file that the isabelle package's pre-unlink deletes. So every transaction that relinks isabelle without relinking light leaves light's patches applied but its session unregistered, and every other component package in the environment loses its registration too.

Mechanism. Light's post-link registers share/isabelle-light-locale with `isabelle components -u` (plan:353-355). That command writes $ISABELLE_HOME_USER/etc/components (Isabelle2025-2 src/Pure/System/components.scala:294, :305-318). The isabelle package's pre-unlink runs `rm -rf` on that whole per-environment user directory (isabelle-packaging-ci/conda/recipe.yaml:223-230; the .bat at :153-169). Only relinked packages run hooks (plan:162-163). Three flows in the plan relink isabelle without relinking the component packages:
(1) `conda install --force-reinstall isabelle`, which the plan prints as the remedy in the CONFLICT text, the residue text, decision 9 and the 0.x section (plan:549-550, :560-561, :367-368, :450). The CONFLICT text adds 'the installed features are re-applied automatically'.
(2) `conda update --all` to a new isabelle build. Ruling 22 makes this recur with every build (plan:83-85), and only the re-released feature packages are relinked.
(3) The solver's automatic upgrade from 2025.2-0 when an existing user first installs any feature package (§6 (e), plan:594).
The AoA component packages pin isabelle loosely and are never relinked in these flows: Isabelle_RPC registers at recipe.yaml:148-158 and pins `isabelle >=2025.2,<2025.3` at :192; Semantic_Embedding/conda/recipe.yaml:318 and the Performant_Isabelle_ML, Isa-Mini and auto_sledgehammer recipes carry the same pin.

Measured on toy channels built with the plan's hook texts and the CI pre-unlink text:
- after `--force-reinstall isa`, etc/components is empty while status shows every feature applied (review-ipc3/critic-user/run3.out lines 78-108; review-ipc3/critic-conda/run3.out:5-7);
- after `conda update --all` to isa build 2 with re-released features, only the feature's registration remains and a plain component is gone (critic-conda/run3.out:18; critic-user/run5.out).
conda prints nothing about it, and §6 (c) checks only status (plan:592), so acceptance would pass.

Consequence: the first feature install in an existing isabelle-ai environment silently unregisters Isabelle_RPC, Performant_Isabelle_ML, Semantic_Embedding, Isa-Mini and auto_sledgehammer. And the plan's own repair breaks the session that ruling 21 put into isabelle-light-locale.

**Editor.** Verified recipe.yaml:223-230 (the rm -rf), link.py:1630-1634 (a pre-unlink receives only PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM, so it cannot tell a removal from a relink), and the measurements.

One correction to the framing. The root cause is in the CI recipe and predates this plan: any second isabelle build would trigger it, and RELEASE_CHECKLIST.md:312-313 already records that the pre-unlink wipes the user directory. But this plan makes the relink mandatory (ruling 22 and §6 (e)), schedules the first one in the field (§5 steps 6 and 8), and prescribes it as the universal remedy. It also owns decision 12, the list of requirements on the CI plan. So the requirement belongs here.

I rate it blocking, above the critics' 'major', because it silently breaks every existing AoA environment on the first feature install, not only light's session.

**Relaxation proposed by the editor.** Make registration survive a relink by construction, through a requirement in decision 12. The simplest shape that holds by construction: each component recipe ships a tracked marker $PREFIX/share/isabelle-components.d/<pkg>, and the isabelle package's own post-link re-registers every marker. That post-link already gains the hook fragment under decision 12 point 2.

A cleaner variant has the isabelle package's etc/settings read those markers, so no hook registers anything. That is a new packaging edit beyond ruling 20's three and needs the owner.

A weaker option keeps etc/components when the pre-unlink deletes the user directory. It leaves stale entries after a real environment removal.

Until one of these lands:
- every remedy text names the component packages: `conda install --force-reinstall isabelle isabelle-light-locale <installed component packages>`, and says that component sessions are unregistered otherwise;
- §6 (c), §6 (e), the CONFLICT-remedy case and the hook-layer tests assert that `isabelle components -l` still lists share/isabelle-light-locale and one Isabelle_RPC-like component after the relink.

**Defender: partially_confirmed** (needs owner: True).

In short: the defect is real. The isabelle package's pre-unlink deletes the file that holds every component registration. The plan's own repair command, `--force-reinstall isabelle`, then leaves light's patches applied but its Light_Locale session unregistered, and the plan's texts and acceptance checks miss this. Three parts of the challenge are overstated or misattributed, though, and they change what the fix has to be.

CONFIRMED (sources and my own toy channel):
1. Mechanism.
   - `isabelle components -u` writes `$ISABELLE_HOME_USER/etc/components` (Isabelle2025-2 src/Pure/System/components.scala:294, :300-318), and getsettings reads user components only from `$ISABELLE_HOME_USER` (pkgs/isabelle-2025.2-0/isa/lib/scripts/getsettings:89-90).
   - The isabelle pre-unlink runs `rm -rf` on that whole directory (isabelle-packaging-ci/conda/recipe.yaml:223-230; .bat :153-169). The published file is identical (pkgs/isabelle-2025.2-0/bin/.isabelle-pre-unlink.sh).
   - conda runs every pre-unlink of a transaction before any link or post-link (core/link.py:928-967). A script gets only PREFIX and PKG_* (link.py:1630-1634), so the pre-unlink cannot tell a relink from a removal.
   - `--force-reinstall` adds the package to the unlink set (core/solve.py:1427-1432).
2. Measured with the plan's hook fragment and the CI pre-unlink: `conda install --force-reinstall isa` on an env with light-like `fc` and plain components rpc and pml.
   - Before: `registered: pml rpc fc` (defender-C1/run-orig-0.out:5).
   - After: `<no etc/components>`, user directory absent (:11-12), while the tree stays patched.
   - `conda update --all` to a new build keeps only fc (:41). A first feature install on build 0 keeps only fc (:55).
3. Plan text.
   - The CONFLICT remedy says "deletes this environment's Isabelle user directory; the installed features are re-applied automatically" (plan:549-550). Decision 9 says the same (plan:367-368, :370-371), and so does the 0.x section (plan:450).
   - Decision 12 point 2 explicitly requires the CI plan to keep the pre-unlink unchanged ("pre-unlink 不变", plan:416-417).
   - §6 (c) checks only `status` (plan:592), and the hook-layer tests check only that patches are re-applied (plan:478, :481).
   - Ruling 21 put light's session into the feature package (plan:75-79), so after the plan's universal remedy, `imports Light_Locale.Light_Locale` breaks silently.
   - Round 2's judge asked only to say that the user directory is deleted (REVIEW2:2285). Rev 3 did that, then added the false "re-applied automatically" claim. So this is a new defect created by implementing ruling 21, not an ignored judge action.

REFUTED OR NARROWED:
(a) The headline overstates the scope. Light's session is lost only when isabelle is relinked while light is not. In the plan's flows that is only flow (1), `--force-reinstall isabelle`.
   - In flows (2) and (3), ruling 22's exact pin (plan:80-86; decision 10, plan:380) forces every feature package to relink whenever isabelle's build changes.
   - All pre-unlinks run first, so light's own post-link re-registers after the wipe: `registered: fc` (run-orig-0.out:41, :55; critic-conda/run3.out:18; critic-user/run5.out:33).
   - Flow (1) is still the plan's remedy in four places, so light's part stands.
(b) The loss of the non-feature components is not caused by this plan. It happens on any isabelle build change, with or without feature packages. An existing AoA env loses them on its first plain `conda update --all` once ruling 11's pristine build ships (plan:57-59).
   - In flow (3), the pre-unlink that runs is the one already published in 2025.2-0, so no requirement in decision 12 on future builds can prevent it.
   - Only a release note, or a post-link-side re-registration, can address it.
   - So "blocking, because the first feature install breaks every AoA env" misattributes the cause. I rate it major: there is a small fix and the design stands.
(c) The editor's objection to the "weaker option" (keep etc/components) is wrong if the rule is: keep it only while it still lists an entry. conda unlinks dependents first (solve.py:1450-1452) and runs every pre-unlink before unlinking anything (link.py:938-947). On `conda remove isabelle`, every component's own `-x` has therefore already run.
   - Measured (run-keep-0.out): force-reinstall keeps all three registrations and deletes the heaps (:11-12).
   - update --all keeps all three (:41).
   - remove isa runs the hooks in the order fc, fb, rpc, pml, fa, isa and leaves no user directory (:68-72).
   - The only leftover is a few-byte etc/components when a hookless, runtime-registered component was installed (Isabelle-MCP/conda/recipe.yaml:10-18). Isabelle-MCP re-registers itself on every start, so it is unaffected by relinks anyway.
(d) The editor's marker relaxation has a trap, measured in run-orig-1.out.
   - During post-link, files conda is unlinking still exist renamed to `<path>.c~` (path_actions.py:1152-1164; constants.py:180). A plain glob over the marker directory re-registered `fc.c~`, `pml.c~` and `rpc.c~` (run-orig-1.out:24, :41). A rule people must remember.
   - It also needs a recipe change in every component repository, gives each registration line two writers, and still misses flow (3) for packages already published, none of which carry markers.
   - The keep-etc/components shape is one change in one recipe. It covers every existing and future component package without touching their recipes, and keeps one owner per line (the component's own hooks), so the invariant cannot be broken.

One related point: decision 12 point 6 (change the user-directory suffix, plan:423) would also orphan every registration on the build that changes it.

Experiment: I built a toy noarch channel under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C1/:
- the generator is mkchan.py and the driver is run.sh;
- I used conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and real git 2.43.0.

The channel holds:
- isa build 0: the old ID 5533cd83156e and the published rm -rf pre-unlink;
- isa builds 1 and 2: pristine, with the plan's hook fragment in the post-link;
- a toy tool;
- features fa<fb<fc pinned exactly to their isa build and re-released for build 2, with fc carrying a component payload registered as plan:353-355 says;
- plain components rpc and pml pinned `isa >=2025.2,<2025.3`, like Isabelle_RPC/conda/recipe.yaml:192.

Every hook logs its name, so the logs show the order. Three variants:
- orig: the CI pre-unlink as it is;
- keep: the pre-unlink deletes everything except etc/components, and deletes that too when it lists no entry;
- markers: each component ships share/isabelle-components.d/<pkg>, and the isa post-link re-registers every marker.

Scenarios: S1 force-reinstall isa; S1b force-reinstall isa together with every component package; S2 update --all to build 2; S3 a build-0 env with components installs fc; S4 conda remove isa; S5 conda remove fc.

Results:
- run-orig-0.out: S1 loses every registration (:11-12); S2 and S3 keep only fc (:41, :55); S1b keeps all (:24); S4 runs dependents' pre-unlinks before isa's (:72).
- run-keep-0.out: S1 and S2 keep all and delete the heaps (:11-12, :41); S4 leaves no user directory (:68-69); S3 still keeps only fc, because build 0's own pre-unlink ran (:55).
- run-orig-1.out: markers restore the registrations, but the glob also picks up conda's `.c~` trash markers (:24, :41).

I also re-read the critics' critic-conda/run3.out and critic-user/run3.out and run5.out, and read these sources: components.scala:185-318, getsettings:87-93, recipe.yaml:111-231, link.py:900-1010 and :1600-1708, solve.py:1405-1454, path_actions.py:1140-1175, RELEASE_CHECKLIST.md:250-313, REVIEW2:2180-2290, and the component recipes' isabelle pins.

Recommended fix: The smallest fix, in four parts.

(1) Decision 12 point 2 (plan:416-417). Replace "pre-unlink 不变" with this requirement: the pristine build's pre-unlink (.sh and .bat) deletes the environment's user directory except etc/components, and deletes etc/components too when it lists no component.
- Reason to state: conda runs every dependent's pre-unlink, and so its `components -x`, before isabelle's (solve.py:1450-1452, link.py:938-947). So a removal still leaves nothing, while a relink keeps every registration.
- Add that the user-directory suffix rule (point 6) must not change after the first pristine build, or the registrations are orphaned the same way.
- The .bat must be checked on the Windows leg.
- Prefer this over the marker scheme: one recipe changes instead of every component recipe, there is a single writer per line, and no `.c~` trap.

(2) Texts (plan:549-550, :560-561, :367-371, :450; README).
- Say that `--force-reinstall isabelle` deletes the environment's heaps and keeps component registrations only on builds that meet point (1).
- Drop the unqualified "re-applied automatically" for sessions.

(3) Release note (decision 12 point 8) and the README's 0.x and update sections. The first move off isabelle-2025.2-0, whether by `conda update --all` or by installing any feature package, unregisters every component session, because 2025.2-0's own pre-unlink deletes the user directory. Recover with `conda install --force-reinstall <the installed component packages>`. No requirement on future builds can prevent this one-time loss.

(4) Tests:
- §6 (c) and the hook-layer tests (plan:478, :481) assert that `isabelle components -l` (or etc/components) still lists share/isabelle-light-locale and one Isabelle_RPC-like component after `--force-reinstall isabelle` and after `conda update --all`;
- §6 (g) asserts that no user directory remains after `conda remove isabelle`;
- §6 (e) asserts the documented loss for a plain component and the documented recovery.

Points (2)–(4) are wording and tests (ruling 17). Point (1) changes how the CI package's hook behaves, so the owner should pick it, or the marker scheme with a `.c~` filter.

**Judge: partially_confirmed → owner_decides.** The defect is real, and its scope is narrower than stated; severity is major, not blocking.

What is narrower:
- Light's own registration survives `conda update --all` and the first feature install. Ruling 22's exact pin relinks every feature, and light's post-link re-registers after isabelle's pre-unlink has run (defender-C1/run-orig-0.out:41, :55).
- Light's registration is lost after `--force-reinstall isabelle` (run-orig-0.out:11-12).

What stands in full:
- Every non-feature component loses its registration on every isabelle relink. These packages pin `isabelle >=2025.2,<2025.3` (Isabelle_RPC/conda/recipe.yaml:192) and are never relinked in these flows.
- This includes the first move off 2025.2-0, whose published pre-unlink (recipe.yaml:223-230) no future build can change.
- The root cause predates this plan, but the plan schedules the relinks and prescribes them as the repair.

After the owner answers Q1:
(1) Decision 12 point 2 (plan:416-417): replace 'pre-unlink 不变' with the chosen mechanism. Decision 12 point 6 must say that changing the user-directory suffix orphans registrations in the same way.
(2) Every --force-reinstall remedy (plan:367-368, :450, :549-550, :560-561):
- drop 'the installed features are re-applied automatically' for sessions;
- until the mechanism lands, name the installed component packages in the command, e.g. `conda install --force-reinstall isabelle isabelle-light-locale <component packages>` (measured to keep the registrations, run-orig-0.out S1b).
(3) Decision 12 point 8 release note, plus the README's update and 0.x sections: the first update off isabelle-2025.2-0, whether by `conda update --all` or by installing any feature package, unregisters every component session once. Recovery: `conda install --force-reinstall <installed component packages>`.
(4) Tests:
- the hook-layer tests and §6 (c) and (e) assert that etc/components still names share/isabelle-light-locale and one Isabelle_RPC-like component after `--force-reinstall isabelle` and after `update --all`;
- §6 (g) asserts that no user directory remains.
(5) If the marker scheme is chosen, filter conda's `.c~` holding files (path_actions.py:1152-1164; constants.py:180).

### C2 [major] Target discovery (`git apply --numstat --summary`) runs outside git_apply's isolation; inside a work tree it prints nothing with rc 0, so every feature reads applied and round 2's silent no-op returns

Section: Decision 3 last point (plan:253-254); decision 4 (plan:258-268); decision 2 symlink refusal (plan:233-235); §6 (j) (plan:599); §10 row C20 (plan:683)  ·  merged from: engine-E2, consistency-CONS-6

**Statement.** Decision 4 isolates exactly one command line, inside `git_apply(workdir, patch_file, *, reverse=False, check=False)`, with an environment built from a whitelist and a workdir that is 'always the staging directory or status's temporary directory' (plan:258-266). Decision 3 adds a second git call, `git apply --numstat --summary <patch file>`, to find each patch file's target (plan:253-254). The plan gives that call no workdir and no environment, and the signature cannot express it. `git --version` (plan:267-268) is a third unisolated call.

conda runs hook scripts with cwd = dirname(script) = $PREFIX/bin (link.py:1644-1646). Users run status from their own project directories. With an inherited environment and a cwd inside a git work tree, the listing call prints nothing and exits 0.
- Reproduced here with git 2.43.0 (review-ipc3/merge/ns/): with cwd repo/env/bin inside an initialised repository the output is empty, rc=0; from /tmp it is '1 0 src/a.ML' plus ' create mode 100644 src/a.ML'.
- Also measured with two of light's real patches (review-ipc3/critic-engine/hostile/numstat.out) and in critic-consistency/numstat/.

What follows from zero targets:
- 'all of its files are >= k' is vacuously true, so every feature reads applied (plan:300);
- apply moves nothing, and the hooks write nothing (plan:361-362);
- decision 2's symlink refusal, computed from the same target list (plan:233-234), checks nothing.

This is round 2's blocking C1 symptom (success reported for an untouched tree, REVIEW2:304-311), brought back through the call that rev 3 added on round 2's suggestion. §6 (j) (plan:599) is exactly the layout that triggers it. The hostile-environment pytest case varies where the tree lives, not the cwd of the tool's own git calls (plan:467-468), so it would not catch this.

**Editor.** Reproduced independently (review-ipc3/merge/ns/). No overreach. The replay itself is isolated correctly when it goes through the whitelist (critic-engine/hostile/run.out: identical bytes under a hostile HOME, XDG, GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_COUNT/PARAMETERS and an autocrlf repository); only the listing call and the version probe escape.

**Relaxation proposed by the editor.** Let one private primitive own every git child process. It alone builds the whitelist environment, the `-c core.autocrlf=false -c core.attributesFile=<devnull>` flags, the ceiling and the umask, and it runs git only in a directory the engine itself created (a fresh mkdtemp for the listing call). Then the isolation holds by construction for the replay, the listing and the version probe alike.

Also make the silent case impossible. make-patches writes exactly one block per patch file (tools/make-patches:162-171), so the tool should require every patch file to yield exactly one target: zero or several is exit 3, naming the file. A feature directory with no patch file is also exit 3, which removes the vacuous 'applied'.

Add a hostile-environment case in which the tool's own cwd is inside a work tree.

**Defender: confirmed** (needs owner: False).

I could not refute C2. The core defect is real, I reproduced it, and it is slightly worse than stated. Two side details are overstated.

What the plan says. Decision 4 puts all isolation inside one function, git_apply(workdir, patch_file, *, reverse=False, check=False). That function builds the whitelist environment, the -c flags and GIT_CEILING_DIRECTORIES, and its workdir is "always the staging directory or status's temporary directory" (plan:258-266). Decision 3 adds a second git call, `git apply --numstat --summary <patch file>`, to read each patch file's target (plan:253-254). The plan gives that call no workdir and no environment. git_apply's signature cannot express it either: it only offers --check and -R. The listing runs "when the feature directory is read, before the replay" (plan:234), so no staging or temporary directory exists yet. The plan's own sources show the gap. Round 2's relaxation 2 puts the whitelist "inside git_apply" (REVIEW2:88), relaxation 11 adds the listing call separately (REVIEW2:125), and round 2's C20 defender measured it only with GIT_DIR=/nonexistent outside any repository (REVIEW2:2588). Rev 3 carried both relaxations over word for word. Section 10 row C1 (plan:664) therefore claims an isolation that covers only git_apply. The plan's summary of ruling 24, "git always runs only in the staging directory" (plan:94), is also false for the listing call.

Where the listing actually runs. conda starts hook scripts with cwd = dirname(script) = $PREFIX/bin (link.py:1644-1646, which subprocess.py:89,110 passes to Popen as cwd). The hook calls the tool from that shell, so the tool and the listing call inherit that cwd and the caller's environment. git 2.43.0, measured in defender-C2/e1/numstat.out:
- cwd outside any repository, or at the top level of a work tree: the list is complete.
- cwd in any subdirectory of a work tree: git drops every patch path outside that subdirectory, with rc=0 and nothing on stderr. Only -v prints "Skipped patch" (hostile.out case C). From userrepo/env/bin the output is empty. From userrepo/src it keeps src/... and silently drops etc/settings, a partial list.
- A broken .git file in the cwd, or a malformed GIT_CONFIG_COUNT that the caller exported, gives rc=128 (hostile.out cases H and I). Under plan:260 the tool would then blame a good patch file with exit 3.

What follows. I prototyped the plan's own rules: plan:253 for targets, plan:291 for levels, plan:300 for the displayed state, plan:311-312 for the exit code (proto/proto.out). On an unpatched tree with cwd = <repo>/env/bin, the tool reads targets=0, so "all files >= k" holds vacuously: the feature reads applied and status exits 0. apply then has no file to move, and by plan:361-362 the hook writes nothing. The symlink refusal at plan:233-234 uses the same empty target list, so it checks nothing. This is round 2's C1(a) symptom (REVIEW2:304-311) coming back through a different call. §6 (j) (plan:599) is exactly the layout that triggers it.

New aggravation: the environment does not have to be inside a repository. proto/usercwd.out puts the environment outside any repository. A user who runs `isabelle-patch-control status` or `apply` from a subdirectory of any unrelated git checkout still gets 0 targets, applied, exit 0. So the trigger is any user's ordinary working directory, not a rare layout.

Isolation fixes it. With the whitelist environment and a ceiling, the listing is complete even with cwd = env/bin (hostile.out case F) and in a mkdtemp created inside the repository (case D). Without isolation, the same mkdtemp gives an empty list (case E).

What is overstated:
1. The title says "inside a work tree". The precise trigger is a subdirectory of a work tree, or an exported GIT_WORK_TREE that contains the cwd (case B). At the top level the list is correct (case A and the userrepo rows).
2. "git --version is a third unisolated call" is true but harmless. It printed "git version 2.43.0", rc=0, under GIT_DIR=/nonexistent, GIT_WORK_TREE, a garbage GIT_CONFIG_PARAMETERS, GIT_CONFIG_COUNT=abc and a broken .git in the cwd (case G). Routing it through one primitive is only for uniformity.
3. "The hostile-environment pytest case would not catch this" is slightly too strong. plan:468 does export GIT_WORK_TREE, so the test would catch it if its cwd happened to lie inside that work tree. The plan leaves that cwd unspecified, so the accurate claim is "not guaranteed to catch it".

None of these changes the severity.

The editor's relaxation, on its merits. I endorse all three parts.
(a) One private primitive that owns every git child process and runs only in a directory the engine itself created. This is the shape that makes the invariant impossible to violate, and it makes the summary at plan:94 and plan:258 true. The engine-created directory is needed, not cosmetic: a ceiling does not stop git from finding a .git in the cwd itself (REVIEW2:311). It also makes plan:260's "rc 128 means the patch file cannot be parsed" true by construction for the listing too, because cases H and I can no longer happen.
(b) Every patch file must list exactly one target. This is an invariant of make-patches: it splits the diff at each `diff --git` and writes each block to its own file (tools/make-patches:154-171). A feature directory with no patch file is exit 3. Together these remove the zero-file case at plan:300, where both "all >= k" and "all < k" are vacuously true. They also catch the partial list, since each dropped file lists zero targets. This check is a safety net, not the fix: on its own it would turn §6 (j) into an exit 3 that blames a good patch file, so (a) is needed as well.
(c) A hostile-environment case where the tool's own cwd is a subdirectory of a work tree. It is needed because no case at plan:467-468 fixes the cwd.

Experiment: All under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C2/, git 2.43.0.
- e1/numstat.out: a toy patch set with a change to src/Pure/x.ML, a new src/Pure/new.ML and a change to etc/settings. `git apply --numstat --summary` from four cwds: /tmp gives the full list; the repo top level gives the full list; userrepo/env/bin gives empty output, rc=0; userrepo/src keeps both src/Pure targets and drops etc/settings, rc=0.
- e1/hostile.out:
  - A: GIT_DIR and GIT_WORK_TREE exported, cwd outside the work tree: correct list.
  - B: the same, with cwd inside the work tree: empty, rc=0.
  - C: -v prints "Skipped patch" for every file, rc=0.
  - D: whitelist environment plus ceiling, in a mkdtemp created inside the repository: correct list.
  - E: the same mkdtemp with the inherited environment: empty.
  - F: whitelist environment plus ceiling with cwd = env/bin: correct list.
  - G: `git --version` under a hostile GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_PARAMETERS and GIT_CONFIG_COUNT and a broken .git: unaffected, rc=0.
  - H: broken .git file in the cwd: listing rc=128.
  - I: GIT_CONFIG_COUNT=abc: listing rc=128.
- proto/proto.py with proto/proto.out: a prototype of the plan's rules (plan:253, 291, 300, 311-312). With the listing as the plan leaves it and cwd = <repo>/env/bin, an unpatched tree reads targets=0, levels=[], applied, status exit 0. With the relaxation (engine mkdtemp, whitelist environment, exactly one target per file) it reads targets=3, not-applied, exit 1, from both cwds.
- proto/usercwd.out: the environment outside any repository, and the user's cwd = a subdirectory of an unrelated repository. The result is targets=0, applied, exit 0.
- Source checks: conda link.py:1635,1644-1646 and gateways/subprocess.py:89,110 (hook cwd = $PREFIX/bin); tools/make-patches:154-171 (one block per patch file); REVIEW2:88, :125, :2584-2600 (where the listing call came from); light's 32 patch files all lie under src/ (contrib/light_locale/patches/).

Recommended fix: Smallest fix, three edits.
(1) Decision 4 (plan:258-268). Replace "every patch operation goes through one function git_apply" with this: one private primitive, for example _run_git(args, workdir), is the only place in the tool that starts git. It alone builds the whitelist environment, the flags `-c core.autocrlf=false -c core.attributesFile=<devnull>`, GIT_CEILING_DIRECTORIES (the realpath of workdir's parent) and umask 022. It runs only in a directory the engine itself created: the staging directory, or a fresh mkdtemp that it creates and deletes itself. git_apply, the target listing (`git apply --numstat --summary`) and the version probe are thin callers of it. Reword plan:94 and plan:258 to "git runs only in a directory the engine created, through one primitive". Then rc 128 from the listing really does mean the patch file is corrupt.
(2) Decision 3, last point (plan:253-254). Every patch file must list exactly one target in --numstat; zero or several is exit 3, naming the file (make-patches writes one block per file, tools/make-patches:162-171). A feature directory with no *.patch file is also exit 3. Add both to the exit-3 list in §4 (plan:527-528). The zero-file case at plan:300 then cannot occur.
(3) Decision 15 isolation case (plan:467-468). Add the tool's own cwd as a subdirectory, not the top level, of a git work tree, and a cwd that holds a broken .git file. Results must be byte-identical to a clean run. Update §10 rows C1 and C20 (plan:664, 683) to name the single primitive.
Do not rely on check (2) alone: without (1), the §6 (j) layout would give an exit 3 that blames a good patch file.

**Judge: confirmed → author_decides_then_rereview.** Confirmed and reproduced by the judge (review-ipc3/judge/ns/): from repo/env/bin, `git apply --numstat --summary` prints nothing with rc=0; with the whitelist environment and GIT_CEILING_DIRECTORIES it lists the target.

The trigger is a cwd in any subdirectory of a work tree, and conda runs hooks with cwd $PREFIX/bin (link.py:1644-1646). An exported GIT_WORK_TREE that contains the cwd also triggers it. `git --version` is unaffected, but should go through the same path for uniformity.

Author:
(1) Decision 4 (plan:258-268):
- one private primitive is the only place in the tool that starts git;
- it alone builds the whitelist environment, the -c flags, GIT_CEILING_DIRECTORIES and umask 022;
- it runs only in a directory the engine itself created: the staging root, or a fresh mkdtemp;
- git_apply, the listing call (plan:253) and the version probe (plan:267-268) are thin callers of it;
- reword plan:28, :94, :115 and :258 to 'git runs only in a directory the tool created'.
(2) Decision 3 (plan:253-254):
- every patch file must list exactly one target; zero or several is exit 3, naming the file;
- a feature directory with no *.patch is exit 3;
- add both cases to §4's exit-3 list (plan:527-528).
(3) Decision 15 (plan:467-468): add hostile cases where the tool's own cwd is a subdirectory of a work tree, and where the cwd holds a broken .git file. Results must be byte-identical to a clean run.
(4) §10 rows C1 and C20 (plan:664, :683) name the primitive.

### C3 [major] A re-run of the batch workflow, which ruling 22 makes routine, publishes nothing: the rebuilt tool collides with its published filename. The build number is a manual input that, when not raised, leaves existing environments on the old isabelle build

Section: Decision 11 inputs and steps (plan:395-404, :407-408); decision 10 build string (plan:378-381); ruling 22 (plan:83-85); ruling 21 (plan:79)  ·  merged from: conda-conda-2, landing-L3, user-U4, conda-conda-4

**Statement.** Every run of the batch workflow builds the tool package at tool_ref and every feature package, then publishes them in a chain that starts with isabelle-patch-control (plan:398-404). Ruling 22 makes re-runs routine: one for each new isabelle build, 'version unchanged, build_number plus one' (plan:83-85, :408). Four defects follow.

(1) Re-run for a new isabelle build. The tool keeps version 1.0.0 and its own build number, because build_number feeds only the feature build string (plan:378, :396). The rebuilt tool therefore has the published filename with new bytes; rattler-build stamps a build time into info/index.json (e.g. pkgs/isabelle-2025.2-0/info/index.json, "timestamp": 1784303812202). publish-conda.yml's guard refuses it ('ALREADY on the channel with DIFFERENT content', publish-conda.yml:177-187) and exits before the upload step (:191). So nothing is published, and the new isabelle build has no feature packages. Replayed with the real step bodies: review-ipc3/critic-landing/pubreplay/scenario.out (batch 2's guard exits 1; R2 afterwards holds only batch 1).

(2) Releases that change one package. Two examples: a tool bugfix (1.0.1), or ruling 21's light version 2, which re-releases only light and the packages above it (plan:79). Either way every unchanged package is rebuilt under its published filename and refused. The only escape is to raise the build number of all eight packages, which republishes unchanged packages. Every user's next `conda update --all` then relinks every feature: a full reverse and re-apply, with heap notices.

(3) The build number is one manual input, default 0, shared by all features (plan:396), although features accumulate different build histories. When the operator does not raise it, a re-release has the same build number as the builds pinned to the old isabelle. Measured with the verbatim pins:
- under libmamba, `conda update --all` reports '# All requested packages already installed' and isa stays on the old build (review-ipc3/critic-conda/run2-tie.out:23-26);
- with timestamps 2 ms apart, a fresh create resolved to the old builds, and `conda install featc` downgraded 'isa 2025.2-2 --> 2025.2-1' (critic-conda/run2.out).
The channel sweep orders builds by the trailing _N of the build string (sweep-old-versions.py:20-24), so a lower n would be swept as superseded.

(4) No rule says how a partially failed publication resumes. The guard's resume accepts only byte-identical files (publish-conda.yml:135-142), and those exist only in the same run's artifact; a re-dispatch rebuilds and is refused.

**Editor.** Verified publish-conda.yml:132-191 (the guard runs over every file before any upload) and the replay. The plan's intent is right ('build_number 加一', plan:408). The defect is that correctness rests on the operator remembering the number and on the tool never being rebuilt. No overreach.

**Relaxation proposed by the editor.** Let the workflow derive what to build, and with which build numbers, from the live channel, so the operator chooses neither.
- Read the channel's repodata.
- A package whose wanted (name, version, build string) is already published is downloaded into the local channel, so the legs test the published bytes, and it is left out of the publish artifact.
- Each new feature build gets n = 1 + the highest build number of that package version on the channel, written into Isabelle2025_2_<b>_<n>. Refuse to publish if any n is not strictly greater.
- Build the tool only when tool_ref names a version that is not on the channel.
- Delete the build_number input.
- State that a failed publication is resumed with 'Re-run failed jobs' of the same run, never with a new dispatch.

Also write scenario (f), 'light 2 and the packages above it', into decision 11 as a worked run, and add a hook-layer case asserting that `conda update --all` moves an existing environment to the new isabelle build.

**Defender: partially_confirmed** (needs owner: False).

Parts (1), (2) and (3) survive and keep the severity at major. Part (4) is largely refuted. Two pieces of the editor's relaxation need correcting.

(1) A re-run publishes nothing. CONFIRMED.
- Every run builds the tool and every feature package into one local channel (plan:399-400). The publish chain starts with isabelle-patch-control (plan:402-404).
- build_number feeds only the feature build string `Isabelle2025_2_<b>_<n>` (plan:378, :385). The tool's recipe is a fixed, committed file (plan:212), and the plan never gives it the input.
- So a re-run for a new isabelle build (plan:83-85, :408) rebuilds the tool under its published filename with new bytes.
- I measured this with rattler-build 0.68.0 from the package cache. Version 0.69.1 exists there only as a .partial, so I could not run it.
  - A noarch generic recipe built four times gave four different sha256 values under one filename, toy-tool-1.0.0-h4616a5c_0.conda. The info/index.json timestamps were 1792811940240 and 1792811949722. Setting SOURCE_DATE_EPOCH=1700000000 did not help: out3 and out4 still differ.
  - A noarch python recipe shaped like decision 1's tool (pip install . --no-deps; run: python >=3.12, git >=2.43) built twice: same name pyh4616a5c_0, different sha256.
- The channel's own documentation says the same thing: RELEASE_CHECKLIST.md:565-566.
- publish-conda.yml checks every file in the artifact before any upload (:147-191; the upload step is at :193). A same-name file with different bytes sets fail=1 (:182-187). The critic's replay with the real step bodies shows the same outcome.
- No sentence in the plan avoids this. plan:396 knows the guard exists but covers only the feature filenames.

(2) A release that changes one package. CONFIRMED.
- A tool bugfix (1.0.1): the tool gets a new filename, but every unchanged feature collides unless n is raised.
- Light version 2 (ruling 21, plan:79): it cannot be published at all, because tool 1.0.0 is rebuilt and collides, and n does not reach the tool's filename.
- `features` defaults to the whole chain (plan:396), and the publish list is fixed (plan:403-404).
- The cost of raising n is real. relink/run.out: content unchanged, build number 0 to 1, then `conda update --all`. It relinked both features and ran "pre-unlink featb 0, pre-unlink feata 0, post-link feata 1, post-link featb 1".
- Under plan:358, the first pre-unlink reverses its feature and everything above it, and the post-link re-applies the whole chain. Each hook writes a heap notice (plan:361), which is false here because the content is unchanged.

(3) A manual build number. CONFIRMED as an invariant that nothing enforces.
- The input defaults to 0 (plan:396). Raising it is only a sentence (plan:408).
- Because b changes, the new filenames differ, so the guard prints "new" and refuses nothing.
- The critic's measurements under libmamba with n tied (critic-conda/run2-tie.out, run2.out run2.gyfM):
  - `update --all` printed "All requested packages already installed";
  - a fresh create picked builds by timestamp;
  - `install featc` downgraded isa 2025.2-2 to 2025.2-1.
- A lower n becomes a sweep candidate (sweep-old-versions.py:20-24).
- The precedent the round-2 judge cited, release-isabelle-ai.yml:24-27 and :62, builds one package per run. Ruling 25 (eight packages, the tool included, in every run) is what breaks it. The author followed REVIEW2:2718 faithfully, so this is a new defect, not a silent deviation.
- Overstated: "features accumulate different histories". One counter raised on every run is monotonic for every package, and an n higher than needed does no harm. The defect is the unchecked default, not that the number is shared.

(4) Resuming a failed publication. LARGELY REFUTED.
- The channel already has the rule. RELEASE_CHECKLIST.md:564-567: "re-run failed jobs ... a fresh dispatch does not substitute — ... the re-dispatch dead-ends". The same appears at :576-578 and publish-conda.yml:41-43, :138-142, :280.
- The plan goes into that checklist's list (plan:407).
- What survives: the plan does not cite the rule. Also, the checklist's alternative "or bump build_number" (:564) does not work for this workflow, because the tool's filename does not carry the input.

The editor's relaxation:
- Sound: derive the reuse decision and n from the live channel. That makes the invariant impossible to violate.
  - Reusing published packages needs no new publish logic. Downloaded files are byte-identical, so publish-conda.yml's guard resumes them (:179-180).
  - rattler-build already provides the "already published" test. With `--skip-existing all -c <channel>` it printed "Skipping build for toy-tool-1.0.0-h4616a5c_0".
- Wrong: "Delete the build_number input". §0 item 22 records "批量发布 workflow 接 build 号输入" (the batch workflow takes a build-number input, plan:84), so deleting it contradicts a binding ruling. Keep it as an optional override for a re-render at the same version and isabelle build (a template fix), and refuse it unless it is strictly greater.
- Redundant: the hook-layer case. plan:478 and §6 (h) at plan:597 already test `update --all`. What is missing is a unit test of the derivation.
- Compatible with ruling 25: the one local channel still holds the tool and every feature package. Some arrive by download instead of a rebuild. The plan should say so in decision 11.
- Same root cause, not raised in this challenge: plan:398-400 puts the build step under each of the five legs. Rebuilt noarch bytes differ, so "同一份 artifact" (one shared artifact, plan:401) can only be one leg's, and the other four legs tested different bytes. Build once, in one job.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C3/. HOME, CONDARC and CONDA_PKGS_DIRS were private, and no owner repository or environment was modified.

1. rb/: rattler-build 0.68.0, run from /home/qiyuan/miniconda3/pkgs/rattler-build-0.68.0-ha759004_0/bin, on a toy noarch generic recipe.
   - out1 and out2: same filename toy-tool-1.0.0-h4616a5c_0.conda, sha256 7111d62a… and bf7be5c9…; index.json timestamps 1792811940240 and 1792811949722.
   - out3 and out4, with SOURCE_DATE_EPOCH=1700000000: still different (81d143f9… and 212bb659…).
   - out5, built with `--skip-existing all -c file://rb/chan` against a channel already holding out1: "Skipping build for toy-tool-1.0.0-h4616a5c_0".
   - out6, with --build-num 1: produced …_1.conda.
2. rbpy/: a noarch python recipe like decision 1's tool (pip install . --no-deps; run: python >=3.12, git >=2.43), built twice with -c conda-forge. Both builds are named toy-tool-py-1.0.0-pyh4616a5c_0.conda; sha256 f5d77954… and 2298ec61….
3. relink/run.sh and run.out: a toy channel with featA and featB pinned to `isa 2025.2 1`, carrying logging pre-unlink and post-link hooks. Adding same-content builds with build number 1 and running `conda update --all` (classic config, default libmamba) changed both features from Isabelle2025_2_1_0 to Isabelle2025_2_1_1. It ran pre-unlink featb, then pre-unlink feata, then post-link feata, then post-link featb.
4. Read and checked:
   - publish-conda.yml:132-193;
   - RELEASE_CHECKLIST.md:564-567, :576-578;
   - release-isabelle-ai.yml:24-27, :59-63;
   - sweep-old-versions.py:20-24;
   - pkgs/isabelle-2025.2-0/info/index.json ("timestamp": 1784303812202);
   - REVIEW2:2635-2720 (the round-2 C21 judge action);
   - the critic outputs critic-landing/pubreplay/{mk.py,scenario.out} and critic-conda/{run2.out,run2-tie.out}. pubreplay's mk.py only assumed that rebuilt bytes differ; experiments 1 and 2 above measure it.

Recommended fix: Decision 11 (plan:395-408), plus one line in decision 10 (plan:378, :385):

1. One job assembles the local channel once, since all eight packages are noarch. The five legs and the publish chain use that single artifact; the legs do not rebuild.

2. That job reads https://conda.qiyuan.me/noarch/repodata.json and decides each package from it:
   - The tool: if isabelle-patch-control at tool_ref's version is already published, download that file into the local channel instead of building it.
   - Feature F at version v (from provenance) and isabelle build b:
     - if (F, v) already has a build `Isabelle2025_2_<b>_*`, download it;
     - otherwise build it with n = 1 + the highest build_number of (F, v) on the channel, or 0 if there is none.
   - The renderer takes n from this derivation, which is one function with a unit test.
   - `rattler-build --skip-existing all -c https://conda.qiyuan.me` can serve as the "already published" test.
   - Downloaded files pass publish-conda.yml's guard as "resume" (:179-180), so the publish chain needs no change.

3. Keep `build_number`, because §0 item 22 records the input (plan:84). Make it an optional override for re-rendering at the same (v, b), for example after a template fix. The workflow refuses it unless it is strictly greater than that highest build_number. Do not delete it as the relaxation proposes.

4. Add one sentence: a failed publication resumes with "Re-run failed jobs" of the same run (RELEASE_CHECKLIST.md:564-567). The checklist's "or bump build_number" alternative does not apply to this workflow.

5. Optionally, write the run "light 2 and the packages above it" into decision 11 as a worked example. No new hook-layer case is needed: plan:478 and plan:597 already cover `conda update --all`.

**Judge: partially_confirmed → author_decides_then_rereview.** Parts (1)-(3) confirmed.
- A rebuilt noarch package gets new bytes under the same filename (defender-C3/rb, rbpy).
- The guard checks every file before any upload (publish-conda.yml:148-191) and refuses the batch.
- A tied build number leaves users on the old isabelle build (critic-conda/run2-tie.out).

Part (4) is largely refuted: RELEASE_CHECKLIST.md:564-567 already says to resume with 'Re-run failed jobs' of the same run.

Correction to the defender: ruling 22 does not require a feature build_number input. The input the owner approved is the isabelle build number (jsonl 6566). The build_number input came from the round-2 C21 judge (REVIEW2:2699).

Author, in decision 11 (plan:395-408), together with C5:
- One build job reads the live repodata.
- It downloads into the local channel every (name, version, build string) that is already published, instead of rebuilding it. publish-conda.yml:179-180 resumes byte-identical files.
- It builds the tool only when tool_ref's version is unpublished.
- It gives each new feature build n = 1 + the highest build number of that package version on the channel, strictly increasing across isabelle builds too. The derivation is one unit-tested function.
- Replace the build_number input by this derivation. Optionally keep an override that is refused unless strictly greater. Record the change in §10's C21 row.
- Fix §0 item 22's paraphrase (plan:84) to 'isabelle 构建号输入'.
- Cite RELEASE_CHECKLIST.md:564-567 for resuming, and say that its 'bump build_number' alternative does not apply here.
- Optionally write the run 'light 2 and the packages above it' as a worked example.

### C4 [major] The workflow checks out feature repositories at release tags that nothing creates; five package repositories have no remote or no commits; light's shipped HOL files are tied to no tested build; a HOL-only light release breaks gate 0 for every feature above light

Section: §0 items 21 and 25 (plan:79, :99); decision 11 (plan:396-399); decision 13 (plan:429-441); decision 16 (plan:488-497); §5 steps 3, 5, 8 (plan:572-583); §10 row C12 (plan:675)  ·  merged from: consistency-CONS-4, landing-L6, user-U5

**Statement.** Decision 11 checks out 'each feature repository at its release tag' (plan:398-399). But make-patches writes patches/<R>/ and provenance.txt into the package directory without any git operation there (tools/make-patches:157-171, :206), and creates the annotated release tag only in the Isabelle repository (:209-211). The state today:
- `git -C contrib/light_locale tag` prints nothing;
- contrib/Isabelle2025-2 carries only Isabelle2025-2/pristine/89701cf1768e;
- contrib/isabelle-base-features and contrib/qiyuan_dev_patches do not exist;
- local_type_abbrev and local_datatype have no commits, localized_record has one, and none of the three has a remote (landing critic's read-only git queries).

No step in the plan:
- creates the GitHub repositories, an owner action that the author's own approved question-6 text listed as a prerequisite ('先建好各 feature 的 GitHub 仓库（按你命令）', 'first create each feature's GitHub repository, on your order', jsonl 6818);
- commits make-patches' output in the package repository;
- creates or pushes package-repository tags;
- seeds the read token that step 5's first run already needs (plan:578 against :582).

The `features` input (plan:396) has no table mapping a feature to its (repository, subdirectory), although isabelle-base-features holds two packages, and its default '缺省为链上全部' (the whole chain by default) names no tags. Round 2 confirmed this gap ('repositories, remotes and callers are unassigned', REVIEW2:1729); §10's C12 row (plan:675) does not address it.

Ruling 21 adds two problems.
(1) light's component payload (ROOT, Light_Locale.thy) ships from whatever commit the light checkout is at. Gate (e)'s tested records are git notes on the Isabelle commit (tools/common.py:174-176), so nothing ties the HOL files that ship to a tested build.
(2) Ruling 21 sends a HOL-only change through a new light release (plan:79). Tagged on the same Isabelle commit as light/1, the new tag would put two light tags on the merge base, and gate 0 then refuses every feature above light ('not exactly one', tools/make-patches:96-102). The plan states no procedure for this path, although the author told the owner the patch content could stay unchanged.

**Editor.** Verified make-patches:96-102, :157-171 and :209-211, and the empty tag lists. No overreach.

**Relaxation proposed by the editor.** Make the package repository's state part of the release by construction.
- make-patches (decision 16) requires the package directory to be committed and clean, records its commit in provenance.txt, commits patches/<R>/ after every gate has passed, and creates the same release-tag name in the package repository.
- The renderer refuses when the checked-out provenance.txt's release_tag differs from the input tag.
- Decision 11 gets a fixed table feature → (repository, subdirectory), and `features` becomes an explicit list of tags.
- §5 step 3, on the owner's order: create the missing GitHub repositories, then push branches and tags. Step 5: seed a fine-grained read-only token covering the package repositories and isabelle-patched.
- For a HOL-only light release, write the mechanism down: a new commit on <R>/light_locale (an empty commit is enough), a tested build, and the merge into each upper branch before its make-patches. Alternatively, give make-patches a mode for this case.

**Defender: confirmed** (needs owner: False).

I tried to refute each part. Every main claim survives. Four details need small corrections, and none of them weakens the core.

1. The release tags the workflow checks out are never created. CONFIRMED. Decision 11 checks out "每个 feature 仓库" (each feature repository) by tag (plan:398-399), and ruling 25 says the same (plan:99). make-patches writes patches/<R>/*.patch and provenance.txt into the package directory with plain file writes (tools/make-patches:157-171, :206). The only git write is `repo.git("tag", ...)`, which runs in the Isabelle repository's common dir (:209-211; common.py:65-66). Decision 16 point 5 (plan:496) only reorders that same tag. A search of the plan for 推送/push/提交/commit finds no step that commits or tags a package repository. `git -C contrib/light_locale tag` is empty, and `git ls-remote --tags` on github.com/xqyww123/Light_Locale is empty too. The author told the owner the feature repos need "只要有发布 tag" (only release tags, jsonl 6863), and the plan never creates them.

2. The repositories do not exist yet. CONFIRMED. isabelle-base-features and qiyuan_dev_patches exist neither locally nor on GitHub (`gh repo view` cannot resolve them). local_type_abbrev and local_datatype have 0 commits and no remote. localized_record has 1 commit and no remote. Of the relevant repos, only Light_Locale (PUBLIC) and isabelle-patched (PRIVATE, RECORD.md:144) exist on GitHub. Correction: local_type_abbrev and local_datatype create their own GitHub repos in their own plans (LOCAL_TYPE_ABBREV_PLAN.md:1185, LOCAL_DATATYPE_PLAN.md:561). The repos this plan owns (migration plan:173: base features and qiyuan_dev_patches) have no creation step: §5 step 3 only creates local directories (plan:572-575). localized_record's repo has no owner at all. Step 7 still needs all of them. The author's own question-6 text says "两种形状都要：先建好各 feature 的 GitHub 仓库（按你命令）" (either shape needs each feature's GitHub repo created first, on your order, jsonl 6818). The plan dropped that without saying so.

3. The read token is never scheduled. CONFIRMED, with two corrections. Decision 11 says "用户设" (the user sets it, plan:399), but no step in §5 does it; step 8 sets only the R2 keys (plan:582). Correction (a): the first scheduled run of the workflow is step 7 (plan:581), not step 5 (plan:578 only writes the workflow). Correction (b): the token is needed only for private package repos. Light_Locale is public, and the workflow as written never checks out isabelle-patched.

4. The `features` input is underspecified. CONFIRMED. `features` (plan:396) has no map from feature to (repository, subdirectory), although decision 13 puts two packages in one repo (plan:431). Its default "缺省为链上全部" (the whole chain) names no tags. Round 2 confirmed "repositories, remotes and callers are unassigned" (REVIEW2:1729). §10's C12 row (plan:675) cites only ruling 25, decision 11 and the rename.

5. Ruling 21 (1): the shipped HOL files are not tied to a tested build. CONFIRMED in substance. run-tree checks only the Isabelle tree's git status (run-tree:100-107) and records no commit for `-d` directories. Gate (e) reads only notes on the Isabelle commit (common.py:174-176; make-patches:141-151). Light_Locale.thy is uncommitted right now (+98/-40), so a tested build today would use HOL files that differ from the committed ones. My toy shows that gate (e) is vacuous for a HOL change: a re-release with no new Isabelle commit passes on the old record. Partial mitigation the challenge omits: §6 (a) builds the shipped component (plan:589-590), but only "在用户授权的腿上" (on legs the user authorises), and only as a smoke theory, not light's required sessions.

6. Ruling 21 (2): a HOL-only release breaks every feature above light. CONFIRMED by experiment. make-patches refuses an existing tag name (:86-88) but not a tip that already carries a release tag of the same feature. So `make-patches light 2` with no new commit succeeds and puts R/light/1 and R/light/2 on the same commit. `make-patches upper 2` then fails gate 0: "carries 2 release tags ... not exactly one" (:96-102). This is exactly the procedure the author gave the owner: "重跑 make-patches 得到新 tag，补丁内容可以不变" (rerun make-patches for a new tag; patch content can stay the same, jsonl 6466). An empty commit on R/light, a tested build, a merge into upper and a tested build there, then make-patches for both, works.

Elegance: the plan relies on people remembering to commit and tag the package repo and to add a commit for a HOL-only release, and the current code lets both be forgotten. Making make-patches own both steps makes the invariants impossible to violate.

The editor's relaxation is right in direction, with four refinements:
- "Package directory clean" is too strict in a shared working directory: light's tests/ is dirty from another agent right now. Require cleanliness only of the files that ship and the gate inputs.
- "Record its commit in provenance.txt" duplicates the package tag, and a file cannot name the commit that contains it. Drop it.
- The token need not cover isabelle-patched unless the workflow is changed to verify the Isabelle tag.
- No special make-patches mode is needed. Refusing a second release tag on one commit enforces gate 0's invariant at the source, and the plan states the empty-commit procedure.

Experiment: Everything ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C4/. tools/ was copied there and run with PYTHONDONTWRITEBYTECODE=1. No repository was modified and nothing was installed.

(1) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C4/hol_only.sh builds a toy chain R/pristine -> R/light -> R/upper with the real make-patches and reference-transaction hook, and fakes tested notes. Output is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C4/hol_only.out.
- light/1 and upper/1 release normally.
- After editing only the package's Light_Locale.thy, `make-patches light 2` exits 0. Gate (e) passes on the old record, and R/light/2 lands on the same commit as R/light/1. `git tag --points-at R/light` prints both tags. `git merge R/light` in upper is already up to date.
- `make-patches upper 2` is refused: "gate 0: merge-base(R/light, R/upper) = c25381a2fcf0 carries 2 release tags of R/light (R/light/1 R/light/2), not exactly one".
- Alternative: `git commit --allow-empty` on R/light, a tested note, `make-patches light 3`, a merge into upper, a tested note, then `make-patches upper 2` all exit 0 (base_pin ==3=R_*).

(2) Read-only state checks:
- `git -C contrib/<repo> tag / remote -v / rev-list --count --all`: light_locale has no tags, an origin, 13 commits. Isabelle2025-2 has only the tag Isabelle2025-2/pristine/89701cf1768e. local_type_abbrev and local_datatype have 0 commits and no remote. localized_record has 1 commit and no remote. isabelle-base-features and qiyuan_dev_patches are missing.
- `gh repo view`: Light_Locale is PUBLIC, isabelle-patched is PRIVATE, my_better_isabelle_prover is PUBLIC. isabelle-base-features, qiyuan_dev_patches, local_type_abbrev, localized_record, local_datatype and isabelle_patch_control cannot be resolved.
- `git ls-remote --tags` on Light_Locale is empty.
- `git status` in light_locale shows Light_Locale.thy modified (+98/-40).

(3) Transcript f1ebd39a….jsonl:
- 6466: the author tells the owner a HOL-only change means "重跑 make-patches 得到新 tag，补丁内容可以不变" (rerun make-patches for a new tag; patch content can stay the same).
- 6818: "两种形状都要：先建好各 feature 的 GitHub 仓库（按你命令）" (either shape needs each feature's GitHub repo created first, on your order).
- 6863: the feature repos "只要有发布 tag" (only need release tags).
- 6896: the user answers "建议 (2)" (suggestion (2), the tool repository).

Recommended fix: Smallest set of plan edits:

1. New point in decision 16, so that make-patches owns the package repository's release state.
   - Before writing anything, refuse unless the files that ship or feed the gates are committed and unchanged in the package repository. These are the entries of tools/component_files.txt plus tools/patched_files.txt, signature_additions.txt and required_sessions.txt.
   - After every gate passes:
     - commit patches/<R>/ by explicit path in the package repository;
     - create the Isabelle release tag, last as today;
     - create an annotated tag with the same name, <R>/<feature>/<v>, on that package commit.
   - State the recovery: if the Isabelle tag exists and the package tag does not, a rerun only adds the package tag.
   - Package tags are then never typed by hand (migration §7 rule 14).

2. make-patches refuses when the tip already carries a release tag of the same feature: "commit first". This makes gate 0's "exactly one tag" invariant impossible to violate.

3. Rewrite ruling 21's sentence (plan:79) as the HOL-only procedure, in chain order:
   - a commit on <R>/light_locale (an empty commit whose message names the light package commit);
   - a run-tree tested build of light's required sessions;
   - make-patches light_locale <v+1>;
   - for each upper branch: merge, tested build, make-patches.
   Add a §0 correction that the author's "补丁内容可以不变、重跑即可" (patch content can stay the same; just rerun, jsonl 6466) needs that new commit.

4. Optional, to tie the HOL side to gate (e): run-tree writes no tested record when a `-d` directory inside a git work tree is dirty, and records that directory's HEAD.

5. Decision 11:
   - Add a fixed table, feature → (GitHub repository, subdirectory):
     - expose_foreign → isabelle-base-features/expose_foreign
     - future_assign_interrupt → isabelle-base-features/future_assign_interrupt
     - light_locale → Light_Locale/.
     - local_type_abbrev, localized_record, local_datatype → their own repositories at the root
     - dev_patches → qiyuan_dev_patches/.
   - `features` becomes an explicit list of release tags with no default.
   - The renderer refuses when provenance.txt's release_tag differs from the tag it was checked out at.

6. §5, before step 7, on the owner's order:
   - create the GitHub repositories isabelle-base-features and qiyuan_dev_patches (this plan's, migration plan:173);
   - name who creates localized_record's repository (local_type_abbrev and local_datatype follow their own plans);
   - push main and the release tags (migration §7 rule 8);
   - only if one of these repositories is private, set a fine-grained read-only token on the tool repository.

7. Update §10's C12 row to point to these edits.

**Judge: confirmed → author_decides_then_rereview.** Confirmed:
- make-patches tags only the Isabelle repository (tools/make-patches:209-211);
- Light_Locale has no tags;
- isabelle-base-features and qiyuan_dev_patches do not exist;
- a HOL-only re-release puts two release tags of light on one commit, and gate 0 then refuses every feature above it (defender-C4/hol_only.out).

Author:
(1) Decision 16, new point:
- make-patches refuses unless the files that ship or feed the gates are committed and unchanged in the package repository: the entries of component_files.txt, patched_files.txt, signature_additions.txt and required_sessions.txt. Do not require the whole directory clean, because the working tree is shared.
- After every gate passes, it commits patches/<R>/ by explicit path, creates the Isabelle release tag, and creates the same annotated tag name on that package commit.
- It refuses when the tip already carries a release tag of the same feature ('commit first').
- Do not record the package commit in provenance.txt: a file cannot name the commit that contains it.
(2) Rewrite ruling 21's consequence (plan:79) as the HOL-only release procedure:
- a commit on <R>/light_locale (an empty commit is enough);
- a tested build;
- make-patches light <v+1>;
- then, for each upper branch: merge, tested build, make-patches.
Add a §0 correction of the author's statement at jsonl 6466.
(3) Decision 11:
- a fixed table feature → (GitHub repository, subdirectory);
- `features` becomes an explicit list of release tags with no default;
- the renderer refuses when provenance.txt's release_tag differs from the checked-out tag.
(4) §5, before step 7, on the owner's order:
- create isabelle-base-features and qiyuan_dev_patches on GitHub;
- name who creates localized_record's repository;
- push branches and tags to the package repositories and to isabelle-patched;
- seed the read token (C12, C28).
Note that jsonl 6818 listed repository creation as a prerequisite, and fix §10's C12 row (plan:675).

### C5 [major] Each of the five legs builds its own noarch packages, so 'the same artifact' is undefined, four legs accept bytes that are never published, and a win-64 build would ship CRLF patch files that git apply rejects

Section: Decision 11 steps (plan:398-401) against ruling 25 as recorded (plan:99-100)  ·  merged from: conda-conda-3, landing-L2, consistency-CONS-3, user-U8

**Statement.** Decision 11 lists, as the steps of each of the five platform legs: render the recipes, build the tool and all feature packages into a local channel, fetch isabelle, run §6, and upload the local channel as an artifact (plan:398-400). That is five rattler-build runs of the same noarch packages, which give five byte sets under one set of filenames: a rebuilt .conda is never byte-identical (RELEASE_CHECKLIST.md:361-364). actions/upload-artifact@v4 names must be unique within a run, and 'the same artifact' (plan:401) names none of the five. Whichever one is published, four legs accepted other bytes.

Ruling 25 as approved builds into one local channel and then runs §6 on five legs (plan:99-100; the approved option (a) at jsonl 6818). The house pattern is the same: build once, test those bytes everywhere (build.yml:1109-1114 and :1126-1130, 'the EXACT byte-for-byte package that would be published'; Isabelle_RPC release-conda.yml:44-46 and :173-176).

Building on win-64 adds concrete failures:
- the Windows build environment has no bash (RELEASE_CHECKLIST.md:339);
- the rattler-build fetch the plan copies 'the way the existing workflows do' is the Linux musl binary (Isabelle_RPC release-conda.yml:92-100);
- actions/checkout on Windows writes text files with core.autocrlf=true, Git for Windows' default (the plan states the same default for PortableGit, plan:176-177), and the feature repositories have no .gitattributes (contrib/light_locale has only .gitignore). The .patch files would become CRLF, which git apply rejects: the LF patch gives rc=0, the same patch in CRLF gives 'error: patch failed', rc=1 (review-ipc3/critic-conda/crlf/). Every file would read CONFLICT.

**Editor.** Partly a rebuttal of the critics' framing. Round 2's relaxation 9 itself said 'it builds every package into one local channel per leg and runs §6' (REVIEW2:118), so rev 3 followed the judge's wording, not a whim of its own. But the same relaxation's stated reason ('The accepted bytes are then the published bytes', REVIEW2:121) and ruling 25's approved text (one local channel, then five legs) both require a single build. The defect stands.

The CRLF failure arises only if packages are built on Windows; with a single Linux build it cannot occur. The .gitattributes is still cheap defence in depth.

**Relaxation proposed by the editor.** Split the workflow.
1. One build job on ubuntu-latest (every package here is noarch) renders the recipes, builds all packages and uploads one artifact. Only this job needs rattler-build.
2. Five test legs download that artifact, add the isabelle build and run §6: linux-64; linux-aarch64 on ubuntu-24.04-arm; osx-arm64 natively and osx-64 through Rosetta on macos-14, as Job G does; win-64.
3. Publication takes that same artifact, or per-package cuts of it (C6).

Also add a .gitattributes marking *.patch, provenance.txt and the hook fragments `-text` in the tool repository and in every feature repository, so that no checkout can rewrite them.

**Defender: confirmed** (needs owner: False).

I tried to refute C5 and could not. The core defect stands, the CRLF failure reproduces on light's real patch files, and one supporting bullet is wrong.

1. Decision 11 builds on every leg. The step list hangs off "步骤（五个平台腿：…）" and runs checkout → rattler-build → render → build "一个本地渠道" → fetch isabelle → §6 → "上传本地渠道为 artifact" (plan:398-400). The upload comes after §6 in the same job, so the text cannot be read as "one build, five tests". Then publish takes "同一份 artifact" (plan:401), which names none of the five uploads.
   - upload-artifact v4 does not allow uploading to the same artifact name from several jobs (README: "uploading to the same artifact via multiple jobs is not supported with v4"), so five same-named uploads cannot coexist.
   - The only house workflow that builds on all five platforms is Semantic_Embedding's. Its collect job merges the per-leg artifacts with `cp` into one `<subdir>/` layout (Semantic_Embedding release-conda.yml:431-454). That works there because each leg writes a different subdir. For noarch packages every leg writes the same `noarch/<name>.conda`, so copying that pattern would keep whichever leg's bytes were copied last, without any error.
   - The house rule says a rebuilt .conda "is not guaranteed byte-identical" (RELEASE_CHECKLIST.md:362-364). C5 says "never", which overstates it slightly.

2. This contradicts ruling 25 as the plan records it and as the owner approved it.
   - Plan:99-100 records the order: build into one local channel, then run §6 on five legs, then upload the same batch.
   - The approved option (a) (transcript line 6818) gives "验收过的字节就是发布的字节" as its reason.
   - Round 2's relaxation 9 also wrote "one local channel per leg" (REVIEW2:119) next to "The accepted bytes are then the published bytes" (REVIEW2:121), so rev 3 copied a wording that contradicts itself. The editor concedes this. It is not a judge action the author silently skipped; it is a real defect.
   - House precedent is to build once and test those exact bytes: build.yml:1121-1130 (Job F cross-builds; Jobs G and H install "the EXACT byte-for-byte package that would be published"), and Isabelle_RPC release-conda.yml:44-46, :173-176, :185-197.

3. The CRLF failure, reproduced in review-ipc3/defender-C5/ (run.sh, run.out).
   - Windows runners check out with core.autocrlf=true: actions/checkout#135, where a maintainer says runners match Git for Windows' default. The house says the same in isabelle-packaging-ci/.gitattributes:1-6, and the plan says it for PortableGit at plan:176-177.
   - Neither light_locale nor the tool repository has a .gitattributes.
   - Cloning contrib/light_locale with -c core.autocrlf=true turned all 32 committed patches/Isabelle2025-2/*.patch files CRLF; a plain clone gave 0.
   - I ran them on files from the official tarball with decision 4's exact isolated call (whitelist env, ceiling, -c core.autocrlf=false -c core.attributesFile=/dev/null). LF patches: rc=0 for variable/morphism/induct/drule. CRLF copies: rc=1, "patch does not apply".
   - Refinement: the CRLF patch that creates src-Pure-Isar-light_locale_axiom_facts.ML applies with rc=0 but writes a file with 98 CR lines. So "every file would read CONFLICT" holds for modified files only; created files come out silently with wrong bytes.
   - On a Windows-built package the post-link.sh would also be CRLF. My test: CRLF post-link.sh exits with rc=2 under both sh and bash, the shell conda uses (link.py:1617-1628), which would make conda roll back on Linux/macOS.
   - The win-64 leg's own §6 run would fail first, so the practical result is a workflow that can never go green, not corrupt bytes being published.

4. Partly refuted bullet. "The rattler-build fetch the plan copies is the Linux musl binary" is true of Isabelle_RPC (release-conda.yml:97-98) and Isa-Mini. But Semantic_Embedding release-conda.yml:134-142 maps all five platforms, including rattler-build-x86_64-pc-windows-msvc.exe, so "照现有 workflow 的取法" does not by itself force a Linux-only binary. The "no bash in the Windows build environment" fact (RELEASE_CHECKLIST.md:339) is real, but a python build script gets around it. Both are costs of building five times, not proofs that it is impossible.

The editor's relaxation is correct and is simply ruling 25 as approved:
- Every package is noarch: the tool is noarch python, and Isabelle_RPC already ships one built on ubuntu that installs on Windows (release-conda.yml:46, :347-358). One Linux build therefore serves all five platforms.
- macos-14 for osx-arm64 plus osx-64 through Rosetta matches Job G (build.yml:1126).
- Once the build is single, a .gitattributes in each feature repository is not needed for correctness, because no Windows checkout feeds a package. It is optional defence, and the kind of rule people have to remember.
- The tool repository does need it: the Windows test leg may run its scripts and fixtures from a checkout, and its CRLF post-link.bat fragment must not be normalised. That is the house convention (isabelle-packaging-ci/.gitattributes: `*.sh text eol=lf`, `*.bat -text`).

Experiment: Directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C5/

1. Clones of /home/qiyuan/Current/MLML/contrib/light_locale (read-only on the source).
   - win-clone/ with -c core.autocrlf=true: 32 of 32 patches contain CR.
   - lf-clone/ plain: 0 contain CR.
2. tb/: src/Pure/{variable,morphism,drule}.ML and src/Tools/induct.ML extracted from ~/isa_release_proto/Isabelle2025-2_linux.tar.gz.
3. run.sh / run.out: decision 4's isolated call
   `env -i PATH=… GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 LC_ALL=C GIT_CEILING_DIRECTORIES=… git -c core.autocrlf=false -c core.attributesFile=/dev/null apply [--check] --whitespace=nowarn` (git 2.43.0).
   - LF patches: rc=0 for all four.
   - CRLF patches: rc=1, "patch failed … patch does not apply", for all four.
   - Created-file patch light_locale_axiom_facts.ML: rc=0 in both cases; the CRLF version wrote 98 CR lines, the LF version 0.
4. hookcrlf/: a CRLF copy of the decision 9 post-link shape exits rc=2 ("end of file unexpected") under both sh and bash.
5. Sources read:
   - plan:97-101, :393-409
   - transcript line 6818 (approved option (a))
   - REVIEW2:115-121
   - RELEASE_CHECKLIST.md:339, :362-364
   - build.yml:1108-1130
   - Isabelle_RPC release-conda.yml:44-197
   - Semantic_Embedding release-conda.yml:87-142, :431-460
   - publish-conda.yml:1-80, :120-190
   - isabelle-packaging-ci/.gitattributes
   - conda core/link.py:1617-1628
   - actions/checkout#135
   - the actions/upload-artifact README (v4 does not allow uploading to the same artifact name from several jobs)

Recommended fix: Rewrite decision 11's step bullet (plan:398-401) as three jobs, and state the reason from ruling 25: the accepted bytes are the published bytes.

(1) `build` on ubuntu-latest, the only job that fetches rattler-build. Name the asset: rattler-build-x86_64-unknown-linux-musl 0.69.1, as Isabelle_RPC release-conda.yml:97-98 does.
- Check out the tool repository, and each feature repository at its tag.
- Render all recipes and build the tool package and every feature package into one local channel.
- Assert that the .bat hooks are CRLF and the .sh hooks are LF, as Isabelle_RPC release-conda.yml:167-171 does.
- Upload exactly one artifact, `conda-packages`.

(2) `accept`, a five-leg matrix, needs build:
- ubuntu-latest for linux-64;
- ubuntu-24.04-arm for linux-aarch64;
- macos-14 for osx-arm64 natively and osx-64 through Rosetta, as build.yml Job G does;
- windows-latest for win-64.
Each leg downloads `conda-packages`, adds `isabelle 2025.2 <isabelle_build>` from the online channel, and runs §6. No leg renders or builds. Any logs a leg uploads get leg-suffixed names.

(3) `publish`, needs accept: publishes that same `conda-packages` artifact. How that one artifact is cut per package is C6's business.

Also add to the tool repository a .gitattributes with `*.sh text eol=lf`, `*.bat -text` and `*.patch -text`, following the house convention in isabelle-packaging-ci/.gitattributes. This keeps the scripts, the CRLF post-link.bat fragment and the toy patch fixtures byte-exact when the Windows leg checks them out. In the feature repositories it is optional.

Drop the phrase "照现有 workflow 的取法": two existing workflows fetch rattler-build in different ways.

**Judge: confirmed → author_decides_then_rereview.** Confirmed.

The step list builds the packages on every leg (plan:398-400). The approved text of ruling 25 (plan:99-100; jsonl 6818) and the house pattern (build.yml:1109-1130) both mean build once and test those bytes everywhere. The win-64 CRLF failure is reproduced on light's real patches (defender-C5/run.out).

The 'Linux musl binary only' bullet is refuted: Semantic_Embedding's release-conda.yml fetches all five platform binaries. It does not change the verdict.

Author: rewrite decision 11's step bullet (plan:398-401) as three jobs, stating the reason that the accepted bytes are the published bytes.
(1) `build` on ubuntu-latest, the only job that fetches rattler-build:
- name the asset, rattler-build-x86_64-unknown-linux-musl 0.69.1;
- render, build every package, and check that .bat hooks are CRLF and .sh hooks are LF;
- upload one artifact.
(2) `accept`, a matrix of five legs, each of which downloads that artifact and runs §6:
- ubuntu-latest for linux-64;
- ubuntu-24.04-arm for linux-aarch64;
- macos-14 for osx-arm64 natively and osx-64 under Rosetta, as Job G does;
- windows-latest for win-64.
(3) `publish` uses that same artifact (C6).

Also:
- add a .gitattributes to the tool repository with `*.sh text eol=lf`, `*.bat -text` and `*.patch -text`, following isabelle-packaging-ci/.gitattributes; it is optional in the feature repositories;
- drop the phrase '照现有 workflow 的取法', because the existing workflows fetch rattler-build in different ways.

### C6 [major] The eight 'serial, dependency-ordered' publish-conda.yml calls on one artifact do not publish in order: the first call uploads and indexes every package

Section: Decision 11 publish bullet (plan:401-404); §0 item 25 (plan:100); §10 row C13 (plan:676)  ·  merged from: conda-conda-12, landing-L1, consistency-CONS-3, user-U8

**Statement.** Decision 11 hands 'the same artifact' to eight publish-conda.yml jobs chained with needs:, one per package in dependency order, and each starts only after the previous one is green, audit line included (plan:401-404). publish-conda.yml does not select what it uploads by package_name: the input is used only in the job name and in env PKG (publish-conda.yml:54-57, :66, :78), and the guard, upload and verify loops each iterate over every $RUNNER_TEMP/pkgs/*/*.conda (:148-191, :198-203, :251-284).

So job 1 (package_name=isabelle-patch-control) uploads and indexes all eight packages in a single index push. Jobs 2 to 8 find their bytes already there ('resume … byte-identical', :179-180), and each one pulls the whole multi-GB channel again (:205-214). Replayed with the real step bodies, R2 replaced by a local directory and the real conda_index (review-ipc3/critic-landing/pubreplay/scenario.out): serial call 1 prints 'new' for every package, call 2 prints 'resume' for every package.

The dependency order and the per-package gate therefore do not exist, and §10's C13 row (plan:676) claims a property the reused workflow does not have.

**Editor.** Rebutting L1's 'relaxation 9 was dropped silently'. The round-2 report pointed two ways:
- C13's judge action asked to publish one run at a time, in dependency order (REVIEW2:1817-1820);
- relaxation 9 asked for one publish-conda.yml call (REVIEW2:116-121).
The owner then approved option (a) of the author's question 6, whose text says the same batch is uploaded '按依赖顺序逐个调 publish-conda.yml' (calling publish-conda.yml once per package, in dependency order; jsonl 6818, approved at jsonl 6823 '赞同你的建议'), and the plan records it in ruling 25 (plan:100).

So rev 3 followed the approved wording, and a single call would change that wording, which needs the owner. The real defect is that the mechanism does not deliver the approved order.

**Relaxation proposed by the editor.** Two shapes.
(a) Keep ruling 25's order and make it real: give each publish call an artifact that holds only its own package (conda-pkg-<name>, cut from the one tested artifact).
(b) Ask the owner to accept one publish-conda.yml call on the whole set. A single index push makes every package appear together with its base, so 'no feature is indexed before its base' holds by construction, and the batch pulls the channel once.

(b) is simpler and clearly better, but it changes the text the owner approved, so it is an owner question. Either way, fix §0 item 25's paraphrase and §10's C13 row.

**Defender: confirmed** (needs owner: True).

In one sentence: the reusable publish workflow publishes whatever is in the artifact it is given, and `package_name` is only a label, so eight calls on the same artifact are one real publish followed by seven repeats that do nothing.

WHAT HOLDS (every factual claim in the statement)
1. `package_name` selects nothing. It is declared at publish-conda.yml:54-57 and used only in the job name (:66) and in `env PKG` (:78). I extracted every step body from the real YAML with PyYAML. None of them reads `$PKG`; the only other mention is a comment saying NOT to use `conda search "$PKG"` (:248). The input's own description, "asserted to be resolvable on the channel afterwards" (:55), is stale. Nothing asserts that any more (:245-250).
2. Every loop covers the whole artifact. The guard (:148-191), the upload (:198-203, `rclone copy "$d"` with `--include '*.conda'`) and the verify step (:251-284) each walk every `$RUNNER_TEMP/pkgs/*/*.conda`. The pull (:205-214) fetches the whole channel on every call.
3. The plan really does pass the same artifact to every call. Decision 11 says "把**同一份 artifact** 按依赖顺序逐个调 … publish-conda.yml"; the calls are chained with `needs:`, in the order tool → expose-foreign → … → qiyuan-dev-patches, and "前一个绿了（含它的审计行）才发下一个" (plan:401-404). Ruling 25 says the same (plan:100). So call 1 uploads and indexes all eight packages, and calls 2-8 find only byte-identical files ("resume", :179-180). The per-package gate and the dependency order are both fictitious, and §10's C13 row, "决定 11 串行顺序" (plan:676), claims a property the reused workflow does not have.
4. My replay, independent of the critic's, gives the same result. I re-extracted the step bodies (they are byte-identical to the critic's copies), built a toy channel of all eight packages, and ran the real conda_index 0.12.1. In scenario S1 (the plan as written), call 1 printed "8 new" and indexed all 8; calls 2-8 each printed "0 new, 8 resume" and pulled all 8 files again.

WHAT I COULD NOT REFUTE, AND WHAT TEMPERS IT
- No user is harmed by what actually happens. All eight packages are noarch (tool: plan:211; features: plan:379), so they share one object, noarch/repodata.json, and a single index push makes them appear at the same instant. No feature can be visible before its base. That meets the intent of migration decision 3 ("发布它的包要求基包已经发布（钉死指向它）", ISABELLE_GIT_MIGRATION_PLAN.md:239) and of the checklist rule "dependencies first" (RELEASE_CHECKLIST.md:399-401), whose reason is that a live-channel verify needs its dependencies. In the batch workflow, §6 runs on the local channel, and the only live-channel check is the final smoke install. So the defect is not a hazard. It is a false design claim given as the fix for a confirmed round-2 challenge, plus waste and misleading logs: seven extra whole-channel pulls on every run, and ruling 22 makes runs recur with every new isabelle build (plan:83-84, :408); jobs named "Publish isabelle-light-locale" publish nothing. Calling it "major" is defensible because the plan tells implementers to build a mechanism that does not do what it says.
- The editor's rebuttal is correct. The owner approved a proposal whose text says "把同一批文件按依赖顺序逐个调 `publish-conda.yml` 上传" (session transcript line 6818), with "赞同你的建议" (line 6823). So rev 3 recorded ruling 25 faithfully. Correction to the relaxation: §0 item 25 is not a mistaken paraphrase. It quotes what the owner approved. It needs no change under shape (a), and changes under shape (b) only after the owner agrees.
- The round-2 actions are honoured. The judge's "isabelle last" was replaced by "isabelle first" under ruling 22 (plan:85), and the plan says so (plan:676). Relaxation 9's "one publish-conda.yml call" (REVIEW2:116-121, :1721) was an optional alternative, so not taking it is not a silent deviation. The real slip is that C13's action "run one publish at a time" (REVIEW2:1817-1820) was written for eight repositories each publishing its own packages. Inside one workflow that publishes one artifact, the author applied it literally as one call per package and got a chain that does nothing.

THE TWO RELAXATION SHAPES, ON THEIR MERITS (replay scenarios S2-S4)
- Shape (a), one artifact per package: this makes the order real. In S2 the index grew 1, 2, …, 8 packages over the eight calls. It still pulls the whole channel eight times. A refusal halfway through leaves a half-released batch: in S4a, light's guard refused, the chain stopped, and the tool, expose-foreign and future-assign-interrupt stayed published for the new build. The order is also a hand-written list of jobs (plan:403-404) that someone must keep correct whenever a feature is added.
- Shape (b), one call on the whole set: the batch is all-or-nothing by construction. In S4b the guard refused the whole batch and nothing was uploaded. Visibility is all-or-nothing as well, because there is one repodata.json per subdir. The channel is pulled once, and there is no order list to maintain. By the repo's elegance rule (a shape that makes an invariant impossible to violate beats one that asks people to remember it), (b) is clearly better. But it changes text the owner approved, so it needs the owner.

ADJACENT POINTS (outside C6's statement; for the judge)
- Five platform legs each "构建进一个本地渠道 … 上传本地渠道为 artifact" (plan:398-400). That gives five builds with different bytes, so "the same artifact" is undefined until the plan says which leg's build gets published.
- The artifact must hold only `<subdir>/*.conda` (:51). The verify step fails for any subdirectory that has no repodata.json on the channel (:251-255).
- A fresh run at an unchanged tool version rebuilds isabelle-patch-control with new bytes, and the guard then refuses it (the critic's batch-2 run). That affects both shapes.
- Found incidentally, and it affects every caller: publish-conda.yml's Banner step (:223-227, added in 85dc11b on 2026-10-09) runs `scripts/banner-index.py` in a job that has no checkout step. It also asserts the text 'conda install -c https://conda.qiyuan.me', which neither the banner file nor conda-index 0.12.1's page contains. When I ran the script and the assertion locally, the assertion returned rc=1. I did not run anything on GitHub.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C6/. It ran locally only: no network, no credentials, nothing installed, and the repositories were only read.
(1) I extracted the step bodies of the real publish-conda.yml with PyYAML into steps/*.sh. The only change was replacing https://conda.qiyuan.me with file://$R2DIR. I checked that no body reads $PKG, and that the bodies are byte-identical to the critic's steps/ copies.
(2) shim/rclone is a copy-only rclone emulator that maps R2:conda to a local directory (copied from the critic's kit). Re-indexing uses the real conda_index 0.12.1 from ~/miniconda3. mk.py builds the plan's eight packages as toy noarch packages, with the exact isabelle-build pin and base pins. call.sh runs one publish call through guard, upload, pull, reindex, push, verify and audit.
(3) scenario.sh, with output in scenario.out:
- S1, the plan as written (eight calls on one artifact): call 1 printed "8 new" and indexed 8 packages; calls 2-8 each printed "0 new, 8 resume" and re-pulled all 8.
- S2, shape (a) (one artifact per package): the index grew 1, 2, …, 8.
- S3, shape (b) (one call): all 8 indexed in one push.
- S4, light already on the channel with different bytes: under (a) the chain stopped at light, leaving the tool, expose-foreign and future-assign-interrupt published (a half batch); under (b) the guard refused everything and nothing was uploaded.
(4) banner/: I ran isabelle-packaging-ci/scripts/banner-index.py on a scratch copy of the generated index.html, then the step's grep assertion, which returned rc=1.
(5) I read the session transcript (~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-….jsonl), lines 6818 and 6823: the owner approved the "按依赖顺序逐个调" wording. I also read REVIEW2:116-121, :1721 and :1741-1820, migration plan :239, and RELEASE_CHECKLIST.md:399-401.

Recommended fix: The smallest honest fix needs the owner, because the better shape changes text the owner approved.
1. In §0, under "作者对用户的更正" (plan:104-110), add a third correction:
   - What the author proposed and the owner approved (transcript lines 6818 and 6823): call publish-conda.yml once per package, in dependency order.
   - Why that does not do what it says: publish-conda.yml uploads and indexes every .conda in the artifact, and `package_name` only labels the job (publish-conda.yml:54-57, :66, :78, :148-191, :198-203, :251-284).
   - The question to the owner: replace the eight calls with one call on the whole batch?
2. If the owner agrees (shape (b), recommended), rewrite three places:
   - Decision 11's publish bullet (plan:401-404): "publish=true 时：把同一份 artifact 交给一次 publish-conda.yml 调用；八个包都是 noarch（plan:211, :379），同在 noarch/repodata.json 一个对象里，一次索引推送让整批同时可见，任何时刻都没有 feature 先于它的基可见；guard 对整批全有或全无。" Then the live-channel smoke job runs with `needs: publish`.
   - Ruling 25 (plan:100): "逐个调" becomes "一次调".
   - §10's C13 row (plan:676): "决定 11 一次索引推送（整批同时可见）、线上冒烟；第 22 条原版构建先发".
3. If the owner declines (shape (a)): keep the wording of ruling 25, and change decision 11 to:
   - add a step that cuts the one tested artifact into conda-pkg-<name> artifacts, each holding only noarch/<file>.conda;
   - give each of the eight calls its own conda-pkg-<name>;
   - derive the order of the `needs:` chain from the provenance files' base_pin, not from a hand-written list;
   - state the costs: eight whole-channel pulls, and a half-released batch if any call is refused.
4. Either way, the artifact handed to publish-conda.yml must be named and must be one build: say which leg's build is the published one (plan:398-400), and that it holds only <subdir>/*.conda (publish-conda.yml:51, :251-255).
5. Give the CI plan (decision 12) two items for publish-conda.yml:
   - the `package_name` description is stale;
   - the Banner step has no checkout, and it asserts a string that the page does not contain.

**Judge: confirmed → owner_decides.** Confirmed.

`package_name` only labels the job (publish-conda.yml:54-57, :66, :78), while the guard, the upload and the verify step all loop over every .conda in the artifact (:148-203, :251-284). Call 1 publishes all eight packages and calls 2-8 do nothing (defender-C6/scenario.out S1).

The editor's rebuttal holds: §0 item 25 quotes the approved text ('按依赖顺序逐个调', jsonl 6818, approved at 6823). Changing it is therefore an owner question (Q2).

After Q2:
- If one call (recommended): rewrite decision 11's publish bullet (plan:401-404), ruling 25's '逐个调' (plan:100) and §10's C13 row (plan:676). The reason to state: all packages are noarch and share one noarch/repodata.json, so one index push makes the whole batch visible at once, and the guard is all-or-nothing for the batch.
- If per-package calls: cut the one tested artifact into conda-pkg-<name> artifacts, each holding only noarch/<file>.conda. Derive the `needs:` order from base_pin rather than from a hand-written list. State the costs: eight whole-channel pulls, and a half-released batch if a call is refused.

Either way, decision 12 gains two CI-plan items:
(a) the `package_name` description is stale (publish-conda.yml:55);
(b) the Banner step (publish-conda.yml:223-227) has no checkout step and asserts a string that neither channel-banner.html nor banner-index.py contains. As written it fails every publication after the upload step and before the index push, including step 6's release.yml. It must be fixed before step 6 (verified by the judge by reading; not run on GitHub).

### C7 [major] The 'same result from every fitting level' rule fails at every intermediate target, including each feature's pre-unlink; status has no word for a file at several levels

Section: Decision 6 (plan:291-302); decision 7 (plan:316-322); decision 9 pre-unlink (plan:358-359); decision 15 tests (plan:461-463); §10 row C6 (plan:669)  ·  merged from: engine-E1, consistency-CONS-12

**Statement.** Essence: whether a file is 'deleted by B' or 'not yet created by A' cannot be told from its content alone, and the plan's tie-break rule only works when the target is the whole chain.

The several-levels rule (plan:295-296, :318-319) says: compute the result of moving the file to T from each fitting level, and use it if all results agree. It is correct only for the whole-chain targets 0 and n.

Running example: feature A (number 1) creates X, feature B (number 2) deletes X. On a fully applied tree X is absent, which is both level 0 (before A) and level 2 (after B).
(i) `unapply --feature B` (T=1) is exactly B's pre-unlink (plan:358). It must reverse B and restore X. The unapply bullet (plan:320-321) has no several-levels rule at all.
- If level 0 contributes 'unchanged', the two results differ, giving a false CONFLICT: X stays missing and A is half-applied once B's package is gone. The residue message then prescribes `--force-reinstall isabelle` (which, by C1, also unregisters components), where a plain apply would have repaired the tree.
- If only movable levels count, unapply leaves X absent.
(ii) `apply --feature A` (T=1).
- Under the 'all levels' reading, a fresh tree gives CONFLICT: the cap falls below A and nothing is applied.
- Under the 'movable levels only' reading, on a fully applied tree apply re-creates X and so moves B down, against 'apply only moves up' (plan:318).
(iii) Display. Decision 6's words compare a file's level with k (plan:300-301). The level set {0,2} against k=1 is neither 'all ≥ 1' nor 'all < 1', so on a correctly fully applied tree A's and B's words, and status's exit code (plan:311-312), are undefined.
(iv) '封顶随之调整' (the cap is adjusted accordingly, plan:319) is circular: whether a file is ambiguous depends on T, and T depends on the cap.

The plan's own tests would fail: 'a file created and then deleted' (plan:461) and rev 1 C3's rename scenario (plan:463; REVIEW1:395).

Measured with a literal prototype of decisions 3-7 (review-ipc3/critic-engine/ipc.py; multilevel.sh, output multilevel.out) on three toy chains (B deletes X, B renames X, B reverts A's edit):
- under one reading, CONFLICT on `apply --feature A` on a fresh tree and on `unapply --feature B`, and A half-applied after B's package is removed;
- under the other, X moves [0,2] → 1 and B reads half-applied;
- under both, status is undefined;
- whole-chain apply is correct in every case.
The real chain has no file at several levels: revisit_gate.py reports '4 features checked, 0 revisits'.

**Editor.** The rule comes from round 2's judge (REVIEW2:100, relaxation 3), so rev 3 followed it faithfully; the defect is in the rule, not in rev 3's transcription.

The real chain is unaffected today, so this is a design defect, not a live bug. It is still major, because the plan advertises the case as supported (plan:295), tests for it, and its failure mode is exactly the pre-unlink.

The fix below restricts what a feature may contain, so it is outside ruling 17's delegation and needs the owner's confirmation.

**Relaxation proposed by the editor.** Make content revisits impossible by construction, and delete the rule.
- A make-patches gate (decision 16) refuses a feature in which any changed file's content at the tip, or its absence, equals that file's content at any lower release tag of the chain. The check compares blob ids, as revisit_gate.py does, and the real chain passes it.
- Several fitting levels can then come only from offset matching, where every choice may write the wrong block. So restore rev 1's rule (REVIEW1:401): such a file is CONFLICT, listed with its levels, for status, apply and unapply alike. Decision 6 needs no new display case, and the cap is no longer circular.

Cost: an upper feature can no longer delete, rename or revert a lower feature's change; that change goes into a new release of the lower feature, which rulings 21-22 re-release in batch anyway. Ask the owner to confirm the restriction.

Replace the test at plan:461 with a make-patches refusal test, keep the repeated-block toy as a CONFLICT case, and move rev 1's rename scenario to the gate's tests.

**Defender: confirmed** (needs owner: True).

The core of C7 holds, and my experiments make it stronger. Two sub-claims need correcting.

The problem in one sentence: a per-file, content-only state model cannot tell "X was deleted by B" from "X has not yet been created by A". The rule rev 3 took from round 2's judge (REVIEW2:100, :998) therefore works only when the target is level 0 or level n.

What the plan says:
- Decision 6 allows a file to be at several levels and gives "created by one feature, deleted by a later one" as the example (plan:295-296).
- The only tie-break is in the apply bullet: compute the move to T from every fitting level, use it if the results agree, otherwise CONFLICT, "封顶随之调整" (the cap is adjusted accordingly) (plan:318-319).
- The unapply bullet has no rule for several levels (plan:320-322). Yet every pre-unlink is an unapply to T = k-1 (plan:358).
- The display words compare "the file's level" with k (plan:300-301), and the exit code depends on those words (plan:311-312). Neither is defined for a level set such as {0,2}.
- §10 row C6 places the rule in decision 6 (plan:669). It is in decision 7, and only for apply.

Experiments (defender-C7/readings.out). I ran four toy chains: create-then-delete, rename, revert, and "pure", where A only creates X and B only deletes it. Each ran under three readings at T=1:
- "all" reading (a level on the side the command does not move counts as "unchanged"). Every T=1 case gives CONFLICT, including B's pre-unlink on a correctly applied tree. After B's package is gone, A reads half-applied. status is undefined.
- "movable only" reading, and a direction-agnostic replay restricted to files at several levels (the two give identical results):
  - `apply --feature A` on a fresh tree is correct.
  - B's pre-unlink on a fully applied tree is correct.
  - `apply --feature A` on a fully applied tree re-creates X, so B drops to half-applied. That breaks "apply only moves up" (plan:318).
  - `unapply --feature B` on a fresh tree creates A's X. That breaks "unapply only moves down" and the pre-unlink's "只反打、永不打" (only reverses, never applies) (plan:321, :358).
- Proof that no tie-break rule can work. In the pure chain, the fresh tree and the fully applied tree are byte-identical, yet the plan's own semantics require `apply --feature A` to create X on one and do nothing on the other. Only two sound options are left without a ledger, which §9 rejects (plan:650-651): forbid such chains, or refuse with CONFLICT.
- New: the reading that rescues the pre-unlink is unsafe.
  - Setup: a repeated-block toy whose top feature changes the first of two identical blocks (repeattop.out).
  - The first whole-chain apply is correct.
  - Under the "movable" reading, the second whole-chain apply (any later post-link, plan:356) silently writes the second block too. X ends up at lines 8 and 19, rc=0.
  - `apply --feature A` does the same (repeat2.out).
  - The "all" reading is safe there, but fails at intermediate targets.
  - So no reading of plan:318-319 is both safe and correct.
- The real chain is unaffected. I re-ran revisit_gate.py on 1113ce6 f8d760a 6d8be01 7983d8a 30aab6e: "4 features checked, 173 git calls, 0 revisits".

Corrections to C7:
- (i) "If only movable levels count, unapply leaves X absent" is wrong. The critic's own multilevel.out case (4) under "movable" restores X, and A reads applied. The cost of that reading lies elsewhere: case (5) above, and the silent corruption in repeattop.out.
- (iv) "Circular" overstates it. There is a terminating monotone reading: a CONFLICT stays a CONFLICT and the cap only goes down (ipc.py plan_moves implements it). The real defect is that the plan never says which reading it means.

The plan's own tests hit the bad cases: the create-then-delete example (plan:461) and rev 1's rename scenario (plan:463, REVIEW1:395).

The editor's relaxation is right on its merits. Making exact content revisits impossible removes the only cases that the "same result" exception exists for. Restoring rev 1's rule (REVIEW1:401) then:
- removes decision 7's sentence;
- closes the gap in the display words;
- makes the cap independent of T.

It needs three amendments:
1. The gate must also compare against the chain bottom `<R>/pristine/<ID>`. That is a base tag, not a release tag in the glossary. revisit_gate.py already does this.
2. "Several levels then come only from offset matching, where every choice may write the wrong block" is right about safety. But such a file can be the correct, canonical applied content (repeat.out: the first apply is correct, then every later apply reads CONFLICT). A published feature with that shape would show a CONFLICT diagnostic on every post-link, and its pre-unlink could not reverse it. Optionally, the gate can state the invariant itself, which closes this case as well: on every chain state from the bottom to the new tip, the tool's own level function gives each file the new feature touches exactly its own level. This covers exact revisits, because an exact revisit fits two levels, and it also covers canonical offset ambiguity. The real chain passes it (REVIEW2:1037: 40 files, one level on each of 5 prefixes).
3. Rev 3 must say that it deviates from the round-2 judge's C5 exception (REVIEW2:998), and why.

The gate restricts what a feature may contain: an upper feature may no longer delete, rename or fully revert a lower feature's change. That goes beyond ruling 17's delegation, so the owner has to confirm it.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C7/. I copied critic-engine's ipc.py, mktoy.sh and revisit_gate.py, using git 2.43.0 with an isolated environment.

1. ipc.py gained a third reading, `--multi=replay`: for a file at several levels, every fitting level contributes its replay to T, whatever the direction.

2. mktoy.sh gained three scenarios:
- `pure`: A only creates X, B only deletes X;
- `repeat`: A changes the first of two identical 7-line blocks;
- `repeattop`: the same change made by the chain-top feature B.

3. readings.sh produced readings.out and readings-replay.out: four chains × three readings, with these cases:
- (1) fresh tree, `apply --feature A`;
- (3) fully applied tree, `apply --feature A`;
- (4) fully applied tree, `unapply --feature B` (B's pre-unlink);
- (5) fresh tree, `unapply --feature B`.

Results:
- "all": CONFLICT in every case. Status reads UNDEFINED(multi-level).
- "movable" and "replay": (1) and (4) correct. In (3), B goes half-applied. In (5), A's file is created, so A reads half-applied.
- For `pure`: "fresh tree and fully applied tree are BYTE-IDENTICAL".

4. repeat.sh, repeat2.sh and repeattop.sh produced the matching .out files:
- The first apply is correct.
- On the second whole-chain apply, "all" gives CONFLICT on the correct tree, and "movable" silently writes the second block: X at lines 8 and 19, the file no longer equals tag B's R.ML, rc=0.
- `apply --feature A` on the correctly applied `repeat` tree does the same under "movable".

5. revisit_gate.py on the real chain, using read-only rev-parse and diff-tree in contrib/Isabelle2025-2 at 1113ce6 f8d760a 6d8be01 7983d8a 30aab6e: "4 features checked, 173 git calls, 0 revisits".

6. I checked the critic's multilevel.out case (4) under "movable": X is restored and A is applied. This refutes C7's sentence "unapply leaves X absent".

Recommended fix: This is the editor's relaxation with three amendments; the owner must confirm the restriction.

1. Decision 6 (plan:295-296): replace the sentence about several levels with rev 1's rule (REVIEW1:401). A file that fits more than one level is CONFLICT, and `status -v` lists its levels. Delete the "created, then deleted" example and keep offset matching and user edits as the causes. The display words at plan:300-301 then need no new case.

2. Decision 7 (plan:318-319): delete "p 同时处于几个层级时……（封顶随之调整）" (when p is at several levels … the cap is adjusted accordingly). With that gone, whether a file is CONFLICT no longer depends on T, so the cap is well defined, and apply and unapply treat such a file alike.

3. Decision 16, new item 7, a revisit gate. make-patches refuses a feature if, for any file it changes, the content at its tip (or the file's absence there) has the same blob id as that file at the chain bottom `<R>/pristine/<ID>` or at any lower release tag. The refusal message names the file and the earlier tag, and says that the change belongs in a new release of the lower feature. revisit_gate.py is the prototype; the real chain passes.
   Optional, stronger form: assert, using the tool's own level function (export it next to git_apply and install_files, plan:331), that on every chain state from the bottom to the new tip each file the new feature changes has exactly its own level. This replaces the blob comparison, which it covers. It also catches a repeated block, whose correctly applied tree would otherwise read CONFLICT on every post-link after the first.

4. Tests:
- plan:461: replace the "新建后被删" (created, then deleted) case with make-patches refusal toys: create-then-delete, rename and revert, from mktoy.sh.
- Keep the repeated-block toy as a tool CONFLICT case in pytest.
- In rev 1's rename scenario (plan:463, REVIEW1:395), the pytest toy now expects CONFLICT plus the gate's refusal.

5. §10 row C6 (plan:669): say that the multi-level rule is rev 1's, and that rev 3 deliberately does not follow the round-2 judge's "unless moving it from each gives the same content" exception (REVIEW2:998). Reason: the files that exception covers can be byte-identical on a fresh tree and on a fully applied tree, yet the plan requires different actions for the two.

6. Owner question, to be answered before any of this: may an upper feature delete, rename or fully revert a lower feature's change? The proposed answer is no; such a change goes into a new release of the lower feature, which rulings 21-22 re-release in batch anyway.

**Judge: confirmed → owner_decides.** Confirmed. Two sub-claims are corrected.
- Under the 'movable levels' reading, unapply does restore X. The real costs of that reading are elsewhere: apply moves B down, unapply creates A's file, and a repeated block is silently double-written on the second whole-chain apply (defender-C7/repeattop.out).
- The cap is not strictly circular, but the plan never says which reading it means.

No reading of plan:318-319 is both safe and correct. The 'pure' chain is byte-identical on a fresh tree and on a fully applied tree, yet the plan's semantics require different actions on the two. The real chain has no file at several levels (revisit_gate.py: 0 revisits).

After the owner answers Q3:
- Decision 6 (plan:295-296): a file that fits several levels is CONFLICT for status, apply and unapply alike, and `status -v` lists its levels (rev 1 rule, REVIEW1:401). Delete the 'created then deleted' example.
- Decision 7: delete plan:318-319's 'same result' rule.
- Decision 16, new gate: make-patches refuses a feature in which any changed file's content at the tip, or its absence, has the same blob id as that file at the chain bottom <R>/pristine/<ID> or at any lower release tag. The message names the file and the earlier tag. A stronger optional form: the tool's own level function must give each changed file exactly its own level on every chain state; this also catches a repeated block whose correctly applied tree would otherwise read CONFLICT.
- Tests: replace plan:461's 'created then deleted' case with make-patches refusal toys; keep the repeated-block toy as a CONFLICT case; move rev 1's rename scenario to the gate's tests.
- §10's C6 row: record the deliberate deviation from REVIEW2:998, and why.

### C8 [major] De-duplicating diagnoses by re-reading .messages.txt cannot work, because conda prints and deletes that file after every script; the round-2 C17 rule was replaced without saying so

Section: Decision 9 message rules (plan:360-366); decision 15 (plan:476-477); §6 (f) (plan:595); §10 row C17 (plan:680)  ·  merged from: conda-conda-5, consistency-CONS-1, user-U2

**Statement.** Decision 9 makes a hook skip a full diagnosis (CONFLICT, broken chain, non-pristine tree, busy) when .messages.txt already contains an identical paragraph, and concludes that 'each diagnosis appears once per transaction' (plan:363-364). But conda calls messages() after every successful script (link.py:1685), and messages() prints the file and then deletes it in a finally block (:1697-1708). The plan's own §2.3 states this (plan:158-159). So every later hook finds no file and writes the diagnosis again. Measured:
- one `conda install` of a three-feature chain after a user edit printed three identical diagnoses, and each hook logged 'msgfile=absent' (review-ipc3/critic-conda/run.out scenario C; critic-consistency/msgdedupe/run.out; critic-user/run3.out T1);
- the full chain would print up to eight.
Decision 15's 'exactly one diagnosis' (plan:477) and §6 (f) (plan:595) cannot pass.

The same paragraph claims that 'on removal only the topmost pre-unlink speaks' (plan:362). That is false: in a pruning removal each pre-unlink, top-down, reverses its own feature (plan:358) and writes its own line and heap notice (critic-conda run.out scenario D; critic-user/run6.out). The residue rule (plan:365-366) would also make lower pre-unlinks list an upper feature's unreversible file under their own names.

The round-2 judge's C17 rule was different: the full diagnosis comes only from the hook whose own feature is in CONFLICT, or from the isabelle hook; the others write one line (REVIEW2:2282-2285). Rev 3 replaced it on the premise that a hook cannot know which feature's hook it is (plan:364), and §10's C17 row (plan:680) does not record the deviation. The premise is false: conda sets PKG_NAME for every link script (link.py:1632), so the frozen fragment can stay argument-free.

**Editor.** Verified link.py:1632 and :1685-1708. The repeated reports on removal are a different matter: the round-2 judge accepted them as unavoidable ('the duplicate notices on removal cannot be avoided', REVIEW2:2285). So for removal the fix is to state the repetition, not to remove it.

One practical detail none of the critics resolved: when the isabelle package and a CONFLICT feature are in the same transaction, both hooks qualify under the judge's rule. 'Exactly one' then needs either an allowance for one extra copy or a narrower rule.

**Relaxation proposed by the editor.** Implement the judge's rule with $PKG_NAME.
- Map PKG_NAME to a feature through one package_name() function. Move it from tools/common.py (plan:375) into the tool package and have common.py import it, the same direction decision 8 already uses for the engine.
- Only the hook of the lowest CONFLICT feature, or the isabelle package's hook, writes the full diagnosis. Accept at most one extra copy when both run in one transaction, and say so in decision 15 and §6 (f).
- A pre-unlink lists only the files its own feature still holds.
- Delete the read-before-write rule and plan:362's sentence, and state the top-down repetition on removal.
- Record in §10 that rev 3 first deviated from C17 and now follows it.

**Defender: confirmed** (needs owner: False).

I tried to refute every part of C8. Each factual part holds. Two small citation slips do not change the substance. My own experiment also turned up one weakness in the editor's relaxation, which I describe after the confirmed parts.

WHAT IS CONFIRMED

1. Removing duplicates by re-reading .messages.txt cannot work.
- conda runs each hook through run_script. After every successful script it calls messages(prefix) (conda/core/link.py:1685).
- messages() reads the file, prints it, and deletes it in a finally block (link.py:1697-1708).
- This applies to post-link and pre-unlink alike. The post-links run one after another (link.py:964-967, which calls run_script at :1109-1114).
- So when a later hook starts, the earlier hook's paragraph is already gone, and the check at plan:363-364 can never find it.
- The plan states the deletion itself twice (plan:159, plan:475), so it contradicts its own rule.
- Measured three times, each hook logging that the file was absent:
  - critic-conda/run.out scenario C: 3 identical diagnoses;
  - critic-consistency/msgdedupe/run.out: 3;
  - my own run, defender-C8/run.out S1 under the rev-3 rule: three FULLDIAG paragraphs, every hook logging msgfile=absent.
- Therefore decision 15's "exactly one diagnosis" (plan:477) and §6 (f)'s "恰一段诊断" (exactly one diagnosis, plan:595) fail whenever more than one feature package is linked in the transaction.

2. The claim that "on removal only the topmost pre-unlink speaks" (plan:362) is false.
- Each pre-unlink runs `unapply --feature F`, which reverses F and everything above it (plan:358).
- conda unlinks in reverse dependency order (core/solve.py:1450-1452) and runs every pre-unlink before any file is unlinked (link.py:938-947).
- So in a pruning removal, the top feature's hook reverses only itself, then the next one down reverses its own feature, and so on. Each one writes its own line and its own heap notice.
- Measured: critic-conda run.out scenario D and my S4 (three "reversed" lines and three heap notices).
- The round-2 judge called this repetition unavoidable. The right reference is REVIEW2:2276; the editor's ":2285" is the remedies line. So the repetition should be stated, not removed.

3. The residue rule blames the wrong feature.
- plan:365 lists "the files that did not return below F's level". That set covers F's files and the files of every feature above F.
- In my S4 under the rev-3 rule, c.ML belongs only to feature c and the user has edited it. It is listed three times, under c, b and a.
- §4 tells the user that each listed file "still carr[ies] its changes" (the changes of the feature being removed). For b and a that is false.
- Under the rule "a pre-unlink lists only its own feature's files", c.ML is listed once. Nothing is lost: if the upper package stays installed, `status` still sees the file (my S5).

4. A round-2 judge action was not followed, and the plan does not say so.
- The judge's rule: the full diagnosis comes only from the hook whose own feature is in CONFLICT, or from the isabelle hook; the other hooks write one line (REVIEW2:2282-2283).
- Rev 3 replaced this with the read-before-write rule. §10's C17 row (plan:680) records no deviation.
- The plan's reason was that the hook then "does not need to know which feature's hook it is" (plan:364). C8 overstates this slightly: the plan says "need not", not "cannot".
- The substance holds anyway. conda sets PKG_NAME for every script (link.py:1632). In both my run and the critic's, the variable reached the tool (hooks.log shows PKG_NAME=feata and so on). So the hook fragment can stay argument-free (plan:336) and the tool can still learn whose hook it is.

5. The relaxation's packaging step is needed.
- `package_name()` lives in tools/common.py (plan:375).
- The installed tool cannot import it, because the package build ships only the Python package (pyproject.toml:36-37).
- Moving the function into the package and having common.py import it follows the direction decision 8 already uses (plan:332).

THE RELAXATION ON ITS MERITS

No rule a hook can follow guarantees exactly one diagnosis in every transaction. A hook cannot see which other packages are in the same transaction, because conda tells a script only ROOT_PREFIX, PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM (link.py:1630-1634). So the choice of rule only decides which kinds of transaction miss.

I counted full diagnoses under three rules (defender-C8/run.out):

| Scenario | rev 3 rule | relaxation (lowest-CONFLICT feature's hook, or the isabelle hook) | chain-top feature's hook, or the isabelle hook |
|---|---|---|---|
| S1: user edits b.ML, then installs featc, which pulls in a and b | 3 | 1 | 1 |
| S2: a and b already installed, user edits b.ML, then installs featc | 1 | 0 | 1 |
| S3: `--force-reinstall isa featb`, a created file has other content | 2 | 2 | 1 |
| S5: user edits c.ML, then `--force-reinstall feata` | 1 | 0 (one line) | 0 (one line) |
| S6: `--force-reinstall isa featc` | 2 | 1 | 2 |

What the table shows:
- S2 is a typical §6 (f) situation: the user edits a file of a feature that is already installed, then installs the next feature. There the relaxation prints only a one-line pointer, and the remedy text never appears. The round-2 judge's own rule gives 0 in S2 as well, because featc's own feature is not-applied, not CONFLICT.
- The variant "the chain-top feature's hook, or the isabelle hook" gives exactly one full diagnosis in S1, S2 and S3. That covers the shapes §6 (f) tests (a package install that does not include isabelle).
- Under the top rule, two copies appear only when the isabelle package and the top feature are relinked together. Zero full diagnoses (one line instead) appear only when neither is in the transaction.
- In S5, the judge's strict "others write one line" would leave feata's hook silent about c, because feata's own feature ends up applied. The one-line rule therefore has to cover every hook that sees a CONFLICT.

Everything else in the relaxation is sound:
- read PKG_NAME;
- move package_name() into the tool package;
- a pre-unlink lists only its own feature's files;
- delete plan:362-364 and state the repetition on removal;
- record the deviation in §10.

Severity: the effect is repeated or missing messages, never a wrong tree. But as written the plan cannot pass its own decision 15 and §6 (f) checks, and it silently deviates from a judge action. So the finding stands. Round 2 graded C17 minor; "major" is defensible only because those acceptance checks block.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C8/ (scripts mkchan.py and run.sh, output in run.out).

Setup:
- conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and a local file:// channel.
- `isa` stands in for the pristine isabelle build. Its post-link contains the rev-3 hook fragment verbatim.
- Three chained features a < b < c, pinned like decision 10. Feature b also creates src/nb.ML.
- Three toy tools, each using real `git apply`:
  - 1.0: rev 3's rules (the read-before-write check, and the residue list from plan:365);
  - 2.0: the editor's relaxation;
  - 3.0: the chain-top variant.
- Every tool call logs PKG_NAME and whether .messages.txt exists when the hook starts.

Results (number of full diagnoses printed):
- S1, edit b.ML then install featc: rev 3 = 3, every hook logging msgfile=absent; relaxation = 1; top = 1.
- S2, a and b installed, edit b.ML, install featc: 1 / 0 / 1.
- S3, `--force-reinstall isa featb` with nb.ML holding other content: 2 / 2 / 1.
- S4, pruning `conda remove featc` after editing c.ML: rev 3 lists c's file under c, b and a (3 residue lists); the own-feature rule lists it once. Every rule prints three "reversed" lines and three heap notices.
- S5, `--force-reinstall feata` after editing c.ML: 1 / 0 plus one line / 0 plus one line.
- S6, `--force-reinstall isa featc`: 2 / 1 / 2.

I also re-read the critics' logs (critic-conda/run.out scenarios A, C and D; critic-consistency/msgdedupe/run.out; critic-user/run3.out T1) and these sources:
- conda/core/link.py:938-967, 1103-1114, 1547-1708;
- conda/core/solve.py:1413-1453;
- pyproject.toml:36-37;
- REVIEW2:2269-2289.

Recommended fix: These are the smallest edits. The author can make them under ruling 17, because they are the round-2 judge's design with one refinement.

1. Decision 9 (plan:360-366):
- Delete the read-before-write bullet (plan:363-364).
- Delete the second half of plan:362, "卸载时只有最上面那个 pre-unlink 说话" (on removal only the topmost pre-unlink speaks).
- Replace them with:
  - (a) `conda-hook` learns whose hook it is from $PKG_NAME, which conda sets for every script (link.py:1632). The fragment stays argument-free. If PKG_NAME is unset or names an unknown package, the hook behaves like the isabelle hook.
  - (b) The full CONFLICT diagnosis is written only by the isabelle package's hook and by the hook of the chain's top feature. Every other hook that sees a CONFLICT writes one line naming the feature, the file, and `isabelle-patch-control status -v`. This refines the judge's rule (REVIEW2:2282-2283): the judge's rule, and the editor's lowest-CONFLICT version, print no full diagnosis when the user edits a file of an installed feature and then installs the next feature (defender-C8 S2).
  - (c) A pre-unlink lists only its own feature's files that did not return below its level.
  - (d) When several feature packages are removed, each pre-unlink, from the top down, reports its own reversal and heap notice. This is unavoidable (REVIEW2:2276).
  - The rare diagnoses that stop before any chain exists (broken chain, tree not the pristine build, busy) may repeat once per hook. Say so.

2. Move `package_name()` from tools/common.py (plan:375, :494) into the isabelle_patch_control package and have common.py import it. This is the same direction decision 8 already uses for the engine (plan:332). The installed tool cannot import tools/ (pyproject.toml:36-37).

3. Decision 1's frozen 1.x interface (plan:220): add that `conda-hook` reads $PREFIX and $PKG_NAME.

4. Decision 15 (plan:477) and §6 (f) (plan:595): spell out what each transaction shape should print, and test each one:
- a transaction that links the top feature package without the isabelle package (the (f) scenario): exactly one full diagnosis;
- a transaction that links both: at most two;
- a transaction that links neither: no full diagnosis, plus the one-line notice.

5. §10, row C17 (plan:680): record three things:
- rev 3 first replaced the judge's rule with a read-before-write rule, which cannot work because conda deletes .messages.txt after every script (link.py:1685, :1697-1708);
- the plan now follows the judge's rule, with the top-feature refinement and the reason for it;
- the removal repetition is stated rather than removed.

**Judge: confirmed → author_decides_then_rereview.** Confirmed:
- conda prints and deletes .messages.txt after every script (link.py:1685, :1697-1708), so the read-before-write rule (plan:363-364) can never fire;
- 'only the topmost pre-unlink speaks' (plan:362) is false;
- the residue rule lists an upper feature's files under the lower features' names;
- the round-2 C17 rule (REVIEW2:2282-2283) was replaced without §10 saying so;
- PKG_NAME is set for every script (link.py:1632).

I adopt the defender's measured refinement (defender-C8/run.out). The judge's rule, and the editor's 'lowest CONFLICT feature' variant, print no full diagnosis in the common §6 (f) shape: edit a file of an installed feature, then install the next feature.

Author:
(1) Decision 9 (plan:360-366): delete plan:363-364 and the second half of plan:362. Then:
- conda-hook learns whose hook it is from $PKG_NAME; if it is unset or unknown, the hook behaves like the isabelle hook;
- the full diagnosis comes only from the isabelle package's hook and from the hook of the chain's top feature; every other hook that sees a CONFLICT writes one line naming the feature, the file and `status -v`;
- a pre-unlink lists only its own feature's files that did not return below its level;
- state that each pre-unlink, from the top down, reports its own reversal and heap notice on a removal (REVIEW2:2276);
- diagnoses that occur before any chain exists may repeat once per hook; say so.
(2) Move package_name() from tools/common.py into the tool package, and have common.py import it (pyproject.toml:36-37 ships only the package).
(3) Decision 1 (plan:220): conda-hook reads $PREFIX and $PKG_NAME.
(4) Decision 15 (plan:477) and §6 (f) (plan:595): state the expected count for each transaction shape:
- the top feature linked without isabelle: exactly one full diagnosis;
- both linked: at most two;
- neither linked: none, only the one-line notice.
(5) §10's C17 row records the deviation and the return to the judge's rule.

### C9 [major] Ruling 22's 'any other ISABELLE_ID exits 3' and §6 (i) contradict decisions 2 and 3, which give 'no feature packages installed', exit 0, when only the tool is installed

Section: §0 item 22 (plan:82-83); decision 2 (plan:227-229); decision 3 points 1-3 (plan:245-251); §4 exit codes (plan:527); §6 (i) (plan:598); decision 15 (plan:459)  ·  merged from: conda-conda-11, consistency-CONS-2, landing-L9, user-U10

**Statement.** Ruling 22, as recorded, says the tool accepts only a tree whose etc/ISABELLE_ID is the official changeset, and exits 3 with a hint to run `conda update --all` on any other ID (plan:82-83). This is the author's wording, which the owner confirmed (jsonl 6566 '别的 ID 一律 exit 3' (any other ID exits 3); jsonl 6569 '确认' (confirmed)). §6 (i) tests it: in a 2025.2-0 environment holding only the tool, status exits 3 (plan:598).

But:
- decision 3 point 1 says the tool does not need to know which changeset is pristine; it detects a non-pristine tree only because no feature directory's base_tag matches the chain bottom (plan:245-246);
- decision 2 and point 3 make a missing features.d print 'no feature packages installed' and exit 0 (plan:227-228, :251);
- the tool package ships no features.d, and conda creates no empty directories.
So in that environment §6 (i) cannot pass, and the ruling's wording is not implemented.

§4 lists 'the tree is not a pristine build' as an exit-3 cause in its own right (plan:527), which only a tool that knows the official ID can detect. The pytest case at plan:459 does not say whether its toy tree has features installed.

**Editor.** No overreach. Both behaviours are defensible: a tool-only environment really has nothing to do. The defect is the contradiction with the ruling as recorded and confirmed, and an acceptance item that cannot pass.

**Relaxation proposed by the editor.** (a) Implement the ruling as worded. The tool carries one small table, release name → official changeset ({'Isabelle2025-2': '89701cf1768e'}), and checks it before the chain walk on every command, including when features.d is absent. Add a pytest case 'only the tool on 5533cd83156e → exit 3'. The chain-bottom check then no longer depends on feature directories.
(b) Keep decision 3, and change §6 (i), §4 and ruling 22's recorded consequence to 'no feature packages installed', exit 0. This deviates from the confirmed wording and needs the owner.

Either way, say which in §0 item 22. Note, from C29, that ISABELLE_ID equal to the official changeset does not by itself prove a pristine tree.

**Defender: partially_confirmed** (needs owner: True).

The central defect is confirmed. I could not refute it. Two of the statement's supporting sub-claims do not hold.

CONFIRMED.
(1) Section 0 item 22 records "工具只认 etc/ISABELLE_ID 等于官方 changeset 的原版构建，别的 ID 一律 exit 3 并提示 conda update --all" (the tool accepts only a tree whose etc/ISABELLE_ID is the official changeset; any other ID exits 3 with a hint to run conda update --all) (plan:82-83). This is the author's own sentence from the message the owner answered. Transcript jsonl line 6566 says "工具只认一种树…别的 ID 一律 exit 3，提示…conda update --all". Line 6569 is the owner's "确认" (confirmed). The explicit request in that message was "按'feature 包精确钉死 isabelle 构建'定" (decide on exact pinning of the isabelle build). Still, the plan records the exit-3 sentence as part of a binding ruling.
(2) The design never checks the ID unless some feature directory exists:
- Decision 2 makes a missing features.d mean "no feature packages installed", exit 0 (plan:226-228).
- Decision 3 point 1 says the tool does not need to know which changeset is pristine (plan:245-246).
- Decision 3 point 3 covers an existing but empty features.d (plan:251).
- The only exit-3 checks at command start are .git, symlink targets and an unknown --feature name (plan:233-236).
(3) A tool-only environment on 2025.2-0 can really be built. The tool depends only on python and git (plan:213-214), so nothing pulls isabelle up. Conda creates directories only as the leaf parents of the files it links (conda core/path_actions.py:340-363, core/link.py:1226-1235). So features.d is absent, and if it existed it would be empty anyway.
(4) Section 6 (i) expects status to exit 3 with a message containing conda update --all (plan:598). Under decisions 2 and 3 it gets exit 0. The acceptance item cannot pass, and the recorded wording of the ruling is not implemented in the one realistic case. When features are installed, conda's exact pins (plan:82, :403) already force isabelle to the pristine build. So on a 2025.2-0 tree the exit-3 sentence can only fire through --no-deps, --force or --features-dir.

REFUTED or softened.
(a) The statement says section 4 lists 'tree is not a pristine build' as an exit-3 cause (plan:526) "which only a tool that knows the official ID can detect". That is wrong. The case is the sub-case that decision 3 point 2 already names in parentheses (plan:248). It can be detected without any table: make-patches writes base_tag "<R>/pristine/<hg id>" for every feature whose base is pristine (tools/make-patches:98-102, 192-201). Whenever any feature is installed, expose_foreign is present with base_tag Isabelle2025-2/pristine/89701cf1768e. If a directory's base_tag is <R>/pristine/X with X different from etc/ISABELLE_ID, the tree is not the pristine build. My prototype produces exactly section 4's message this way. The plan does not state this test, though: plan:249 says "树不是原版构建时另加一句" (when the tree is not a pristine build, add a sentence) without saying how the tool decides that. This is a small gap in the specification, not a contradiction.
(b) The pytest case at plan:458 is consistent with decision 3. The fixture defined just before it (plan:456-457) has three chained features, so a toy tree with ID 5533cd83156e has a non-matching chain bottom and gets exit 3. The only loose end is that "没装 feature 包" (no feature packages installed) at plan:459 has no stated expected result.

The editor's relaxations, judged on their merits.
- (b) Keep decision 3. This is the more elegant option. "No feature is ever applied to a non-pristine tree" holds by construction, because a non-pristine chain bottom matches no base_tag. The only behaviour that differs from the recorded ruling is the tool-only environment, where the tool has nothing to write, so an exit 3 there protects nothing. But it deviates from the wording the owner confirmed, so it needs the owner.
- (a) Implement the wording. This works only with a refinement. The table must be keyed by release name and consulted only when R is a key. Otherwise tool 1.0, which every future feature package admits through isabelle-patch-control >=1.0,<2 (plan:403), would refuse the next Isabelle release. It also brings back a per-release table, the kind of tool-side build knowledge ruling 22 removed together with LEGACY_BUILDS.
- C29's caveat applies to both: an etc/ISABELLE_ID equal to the official changeset does not prove a tree is pristine.

Severity: the contradiction is real and leaves an acceptance item that cannot pass. The behavioural harm is small, since the tool has nothing to write in that environment. "Major" is defensible only because it misimplements a recorded ruling and needs an owner decision.

Experiment: Prototype: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C9/proto/walk.py, output in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C9/proto/run.out.

- walk.py transcribes decision 2 (plan:225-229) and decision 3 points 1-3 (plan:244-251) literally. It does no git apply.
- --table adds relaxation (a): a {release name: changeset} table, consulted only for a known release.
- The table-free test for "tree is not a pristine build" is: some base_tag has the form <R>/pristine/X with X different from the tree's ID (from make-patches:192-201).
- The toy environments have conda-meta/, isa/etc/ISABELLE_IDENTIFIER=Isabelle2025-2 and ISABELLE_ID set to 5533cd83156e or 89701cf1768e. Some also have features.d with expose_foreign (base Isabelle2025-2/pristine/89701cf1768e) and future_assign_interrupt.

Results:
- Tool only on 5533cd83156e: the rev-3 rules give rc=0 "no feature packages installed", so section 6 (i) fails. The table gives rc=3 with section 4's message.
- Empty features.d on 5533cd83156e: the same.
- Features installed on 5533cd83156e: the rev-3 rules give rc=3 "feature chain broken … needs base Isabelle2025-2/pristine/89701cf1768e", plus section 4's not-pristine sentence detected without a table. The table also gives rc=3.
- On 89701cf1768e: both give rc=0, either "no feature packages installed" or "chain: expose_foreign -> future_assign_interrupt".

Sources and checks:
- I read the conda 25.11.1 sources: path_actions.py:340-363 and link.py:1226-1235 create only leaf directories of file paths.
- The cached pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_ID is 5533cd83156e.
- The transcript /home/qiyuan/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl has the author's proposal at line 6566 and the owner's "确认" at line 6569.

Recommended fix: The smallest fix is a text change, but the author must choose which way, say so in section 0 item 22, and get the owner's answer before the option that deviates.

Option (b), preferred for elegance; it deviates from the wording confirmed at jsonl 6566/6569, so the owner must approve:
- Rewrite the clause at plan:82-83. Suggested text: "非原版构建的树上没有任何 feature 的 base_tag 能对上链底 <R>/pristine/<ISABELLE_ID>，所以装着 feature 时 exit 3 并提示 conda update --all；没装 feature 包时无事可做，status 打印 no feature packages installed、exit 0" (on a non-pristine tree no feature's base_tag can match the chain bottom, so with features installed the tool exits 3 and hints conda update --all; with no feature packages installed there is nothing to do, and status prints "no feature packages installed" and exits 0).
- Replace section 6 (i) (plan:598) with one of two checks. The first is "只装工具的 2025.2-0 环境里 status → exit 0、no feature packages installed" (in a 2025.2-0 environment holding only the tool, status exits 0 and prints "no feature packages installed"). The second is the exit-3 case on a 2025.2-0 tree that really holds a feature directory, for example with --features-dir or --no-deps.

Option (a), if the owner keeps the wording:
- Add one constant, PRISTINE = {"Isabelle2025-2": "89701cf1768e"}. Check it right after reading etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID, before the features.d-absent shortcut in decision 2. Consult it only when R is a key, so that unknown releases fall through to the chain walk and tool 1.0 does not block a later release admitted by >=1.0,<2.
- Delete "工具不需要知道哪个 changeset 是原版" (the tool need not know which changeset is pristine) at plan:245-246.
- Add the pytest case "only the tool, ID 5533cd83156e → exit 3".

Either way:
- Write down in decision 3 point 2 (plan:249) how the tool decides "树不是原版构建" (the tree is not a pristine build): a feature directory's base_tag is <R>/pristine/X with X different from etc/ISABELLE_ID. Under (a), it is the table check instead.
- Give "没装 feature 包" (no feature packages installed) in decision 15 (plan:459) an explicit expected exit code.
- Note C29: an etc/ISABELLE_ID equal to the official changeset does not prove a tree is pristine.

**Judge: partially_confirmed → owner_decides.** The contradiction is confirmed.
- Ruling 22 as recorded (plan:82-83, from the author's text at jsonl 6566, confirmed at 6569) says any other ID exits 3.
- Decisions 2 and 3 (plan:227-228, :245-246, :251) give 'no feature packages installed', exit 0, when only the tool is installed.
- So §6 (i) (plan:598) cannot pass.

Refuted sub-claim: 'tree is not a pristine build' (plan:527) can be detected without a table. A feature directory's base_tag <R>/pristine/X with X different from etc/ISABELLE_ID shows it (make-patches:192-201).

After the owner answers Q4, record the choice in §0 item 22.
- Option (b), recommended:
  - rewrite plan:82-83 to say that with features installed the tool exits 3 and hints `conda update --all`, and with none installed it prints 'no feature packages installed' and exits 0;
  - replace §6 (i) with that check, or with the exit-3 case on a 2025.2-0 tree that really holds a feature directory.
- Option (a):
  - add one constant {'Isabelle2025-2': '89701cf1768e'}, consulted only when R is a key and before the features.d shortcut, so that tool 1.0 does not block a later release admitted by >=1.0,<2;
  - delete plan:245-246's 'need not know';
  - add the pytest case 'tool only, 5533cd83156e → exit 3'.
- Either way:
  - decision 3 point 2 (plan:249) states how 'not a pristine build' is decided;
  - decision 15 (plan:459) gives 'no feature packages installed' an expected exit code;
  - note C29: an ISABELLE_ID equal to the official changeset does not prove a tree pristine.

### C10 [major] The whole five-leg acceptance runs only after the pristine isabelle build is published, leaving an unbounded window in which the channel serves it without any feature package; decision 12.7 contradicts decision 11; round 2's C15 action was dropped silently

Section: §5 steps 5-8 (plan:578-583); decision 11 (plan:400, :407-408); decision 12 points 7-8 (plan:424-427); §10 row C15 (plan:678)  ·  merged from: landing-L4, user-U9, consistency-CONS-11

**Statement.** Decision 11 takes isabelle only from the live channel (plan:400). Before step 6 the only live build is 2025.2-0, on which no feature package installs (ruling 22). So the step-5 run (plan:578) exercises no feature package on a real isabelle.

The first five-leg run happens at step 7 (plan:581), after release.yml has published the pristine build (plan:579). That run is also the first execution of the .bat hooks, and the first run of the CI's copy of the frozen fragment with the tool present: the CI's own smoke installs isabelle alone (release.yml:114-115).

From step 6 until step 8:
- `conda update --all` moves 2025.2-0 users to a build without expose_foreign (and, by C1, unregisters their components);
- decision 12.8's release note tells them `conda install isabelle-expose-foreign` (plan:426-427), a package that is not on the channel yet.
Every failure in step 7 extends that window without bound. A defect found then in the published isabelle's frozen fragment costs a new isabelle build plus a re-release of every feature (ruling 22).

Ruling 22 fixes only the publication order ('先发原版 isabelle 再发 feature 包', the pristine isabelle first, then the feature packages, plan:85). It does not say acceptance must wait until after publication, and ruling 16 wants all packages released together on the owner's command (plan:65).

Decision 12.7 still says §6 uses the 7-day CI artifact (plan:424-425), which contradicts decision 11. The round-2 C15 judge required step 6 to name 'the CI artifact of a named run' (REVIEW2:2019); §10's C15 row (plan:678) does not record the change.

**Editor.** Two qualifications.

First, the author did tell the owner that publishing the pristine build first is harmless to 2025.2-0 users, because they have no feature packages and Performant_Isabelle_ML rescues Foreign (jsonl 6566). That covers the ecosystem's own Foreign use. It does not cover the unbounded window, the release note naming an absent package, or the risk to the frozen fragment.

Second, the proposed cross-repository artifact download needs a token with actions:read on isabelle-packaging-ci. publish-conda.yml:69-74 notes that callers cannot grant that scope to the run token, so the read token of C4 must carry it.

Also note that release.yml rebuilds rather than promotes (release.yml:9-11). Round 2 judged this acceptable, because ISABELLE_ID and the post-link text come deterministically from the recipe (REVIEW2 C15, change (2)).

**Relaxation proposed by the editor.** Give the workflow an input that says where isabelle comes from: either the conda-packages artifact of a named build.yml run in isabelle-packaging-ci, downloaded across repositories with the read token, or the live channel.

Step 7 then becomes the full five-leg rehearsal against that artifact, before release.yml publishes anything. Step 6's publication and step 8's publish=true then run back to back, and step 8's run re-checks §6 against the published build.

Rewrite decision 12.7 to match, and release the release-note sentence only together with step 8. Ruling 22's order, isabelle first, is kept.

**Defender: partially_confirmed** (needs owner: False).

The core of the challenge holds. The harm it describes is overstated. I would lower the severity from major to minor-moderate.

CONFIRMED
1. Acceptance runs only after the irreversible publication.
- Decision 11 takes isabelle only from the live channel (plan:399-400).
- Step 6 publishes the pristine build with release.yml (plan:579). Step 7 then runs §6 "对已发布的原版构建" (plan:581).
- Nothing before publication runs the CI's copy of the post-link fragment with the tool present.
- No automated Windows install happens before publication at all. build.yml:1121-1123 covers only macOS and linux-aarch64 and says "win-64 was covered by hand". The windows-latest smoke runs after publish (release.yml:84-92) and installs isabelle alone (release.yml:114-115).
- Decision 15's hook-layer test is a .sh script (plan:473), and the Windows checks are assigned to the §6 legs (plan:485-486). So step 7 is also the first run of the .bat hooks.
- Publication cannot be undone (release.yml:5-7). This inverts the CI repo's own rule, "what we publish is exactly the bytes just verified" (release.yml:9-11).
- It also stretches ruling 16, "全部就绪后…一次发布" (plan:65). The owner said "没有提前发布的需求，会等一切都做完的" (session jsonl line 2297).
- Ruling 22 only fixes the publication order. The author's stated reason was "否则 feature 包有一段时间无解" (jsonl 6566). It says nothing about when acceptance runs.

2. The window between step 6 and step 8 has no bound, and its release note is wrong during it.
- No limit and no fallback are stated.
- Decision 12.8's sentence (plan:426-427) is part of the isabelle package description, which ships with the build (recipe.yaml:254-264). For the whole window it names isabelle-expose-foreign, which is not on the channel.

3. Decision 12.7 is left over from an earlier design, and §10 is inaccurate.
- Rev 3 has no §6 use of the CI artifact left, so 12.7's sentence "§6 用它时要重新下载或重跑" (plan:424-425) describes nothing.
- §10's C15 row (plan:678) cites 12.7 as the implemented change. It does not record that rev 3 replaced the judge's "CI artifact of a named run" (REVIEW2:2019) with the live channel.
- This is not fully silent: decision 11 gives the reason inline, "（第 22 条：原版构建先发）" (plan:400). Round 2 had the pristine build published last (REVIEW2:121), and ruling 22 reversed that.

REFUTED OR OVERSTATED
a. "Costs a new isabelle build plus a re-release of every feature": the second half is false at step 7.
- Step 7 is publish=false, so no feature package exists on the channel yet. The cost is one more isabelle build number.
- A defective published build stays harmless afterwards: no feature pins it, and installing a feature upgrades isabelle automatically (plan:87, :166, pintest/).

b. "By C1, unregisters their components" does not come from the window.
- It is caused by 2025.2-0's frozen pre-unlink (recipe.yaml:223-231). That runs on any isabelle update, including updates after step 8.

c. The harm inside the window is small.
- 2025.2-0 carries only expose_foreign. The cached isa/src/Pure/ML/ml_name_space.ML:67 is ["Signal"], and future.ML:422-433 does not have future_assign_interrupt.
- The ecosystem names only Foreign at the top level. The RunCall uses in Semantic_Embedding/Tools/simd_vector.ML:104-113 are inside a comment.
- rescue_foreign.ML:34-37 rebinds Foreign.
- Users outside the ecosystem can pin isabelle=2025.2=0, which stays on the channel.
- "No feature package on the channel" is also the situation before step 6.

d. That step 5 exercises nothing on a real isabelle is a description, not a defect: step 5 never claims to run an acceptance (plan:578).

THE EDITOR'S RELAXATION
It is sound and costs no extra §6 run. The plan already runs §6 twice: at step 7, and again in step 8's publish=true run (plan:398-401). Under the relaxation, decision 12.7 becomes true again.

But it is incomplete. Today the only non-publishing builds come from ci.yml, which passes no build_number (ci.yml:19-23), so build.yml uses its default "0" (build.yml:59-62). The artifact would then be named isabelle-2025.2-0, the same name as the legacy build. My toy channel experiment shows what that does:
- T3: the artifact's pristine 1.0-0 shadows the live legacy 1.0-0.
- T4: in an environment on the live legacy build, a feature pinned to `isa 1.0 0` installs onto the legacy tree (ISABELLE_ID stays 5533cd83156e) and does not upgrade it. That breaks ruling 22's guarantee inside the rehearsal, and scenario (e) can no longer be tested.
- T1 and T2: with an artifact at build 1, features resolve to the artifact, and scenario (e) upgrades the legacy environment correctly.

isabelle-packaging-ci is public (gh api), but a cross-repository artifact download still takes a token. The read-only token of plan:399 would need actions:read; I did not verify whether the run's own GITHUB_TOKEN would be enough.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C10/.

1. Toy conda channels: e1/mk.py, e1/run.sh, output in e1/run.out.
- Setup: conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS; prefix environments only in the scratch directory.
- Channel "live" holds isa-1.0-0 with ID 5533cd83156e, standing for the legacy build.
- Channel "art0" holds isa-1.0-0 with ID 89701cf1768e (the ci.yml default build number) plus a feature pinned to `isa 1.0 0`.
- Channel "art1" holds isa-1.0-1 plus a feature pinned to `isa 1.0 1`.
- T1: create feat from art1 plus live. Result: isa 1.0-1 from art1, ID 89701cf1768e.
- T2: start from an environment on the live legacy build, then install feat. The solver upgrades it to the art1 build.
- T3: create isa=1.0=0 from art0 plus live. The artifact's pristine build shadows the legacy one.
- T4: start from an environment on the live legacy build, then install feat from art0. rc=0, and the feature lands on the legacy tree (ID 5533cd83156e); isa is not upgraded.

2. Read-only checks.
- Fetched the live repodata: only isabelle-2025.2-0 is published, and the consumer packages require isabelle >=2025.2,<2025.3.
- gh api reports both isabelle-packaging-ci and my_better_isabelle_prover as public.
- Read the cached pkgs/isabelle-2025.2-0: ml_name_space.ML:67, future.ML:422-433, ISABELLE_ID.
- Searched the ecosystem's .ML and .thy files for Foreign, RunCall and CInterface.
- Read the session transcript at lines 2297, 5268 and 6566.

3. Sources read: release.yml, ci.yml, build.yml:1-80 and :1090-1140, publish-conda.yml:1-140, conda/recipe.yaml, rescue_foreign.ML, REVIEW2 C15 and its judge's architecture point 9, and the migration plan's rulings 30 and 31.

Recommended fix: Smallest fix: adopt the editor's relaxation, completed with a requirement on the build number.

1. Decision 11 (plan:395-401): add an input `isabelle_from`, with the values `run:<isabelle-packaging-ci run id>` or `channel`.
- With `run`, the workflow downloads that run's `conda-packages` artifact into the local channel, using plan:399's read-only token with actions:read.
- It then asserts that the artifact's isabelle build string equals `isabelle_build` and is not 0.

2. Decision 12: add a point. The non-publishing CI path, a ci.yml workflow_dispatch, accepts `build_number` (ci.yml:19-23 passes none today, so the build falls back to build.yml's default "0"). release.yml is later run with the same number.
- Rewrite 12.7: "§5 step 7 rehearses against that run's artifact; it is kept for 7 days (build.yml:1113), so re-run the build if it has expired."

3. §5:
- Step 6: the CI plan lands, then one non-publishing run with build_number b. (b2) runs on that build's isa/.
- Step 7: publish=false with isabelle_from=run:<id>, all five legs green. Nothing is published yet.
- Step 8: on the owner's command, release.yml with build_number b, immediately followed by publish=true with isabelle_from=channel (its §6 run re-checks the rebuilt package), then the online smoke test.
- 12.8's two README sentences go out at step 8.
- Ruling 22's order, isabelle first, is kept.

4. §10 row C15: record that rev 3 first took the live channel because of ruling 22's order, and now rehearses against the artifact.

Fallback, if the author prefers a single source: keep decision 11 as it is, but
- state the window and its bounded harm in the plan;
- run pytest and the hook-layer tests, both .sh and .bat, on all five legs at step 5;
- have decision 12 require a win-64 install before publication;
- delete 12.7;
- record the deviation in §10.

**Judge: partially_confirmed → author_decides_then_rereview.** The core is confirmed.
- The first five-leg run happens after the irreversible step-6 publication (plan:579-581). It is also the first run of the .bat hooks and the first run of the CI's copy of the frozen fragment with the tool present.
- Decision 12.7 (plan:424-425) describes nothing in rev 3.
- §10's C15 row hides the change from 'the CI artifact of a named run' (REVIEW2:2019).

Overstated: 'a re-release of every feature' is false at step 7, where nothing is published yet. And C1's loss of registrations is caused by 2025.2-0's own pre-unlink, not by the window.

Author, adopting the defender's completed relaxation:
- Decision 11 gains an input `isabelle_from` = run:<isabelle-packaging-ci run id> | channel. With a run id, the workflow downloads that run's conda-packages artifact using a token with actions:read on isabelle-packaging-ci (publish-conda.yml:69-74: the run token cannot be widened). It asserts that the artifact's build string equals isabelle_build and is not 0. A build-0 artifact would shadow the live 2025.2-0 and break scenario (e) (defender-C10/e1/run.out T3-T4).
- Decision 12 gains a point: a non-publishing ci.yml dispatch accepts build_number (ci.yml:19-23 passes none today), and release.yml later uses the same number. Rewrite 12.7 accordingly.
- §5:
  - step 7 rehearses all five legs against that artifact before anything is published;
  - step 6's release.yml publication and step 8's publish=true then run back to back, and step 8 re-checks §6 against the published build;
  - decision 12.8's release-note sentences ship at step 8.
- Ruling 22's order, isabelle first, is kept.
- Record the change in §10's C15 row.

### C11 [major] An interrupted conda transaction is rolled back whole and conda-meta/history is deleted: Appendix A's recovery ('re-install the feature package') is false, and decision 5's convergence claim does not hold on this path

Section: Appendix A, 4th bullet of 边界与代价 (plan:714-715); decision 5 guarantee (plan:279-281); §2.3 (plan:155-157); decision 15 and §6 coverage (plan:473-484, :600)  ·  merged from: landing-L8, user-U3, consistency-CONS-8

**Statement.** Appendix A, which is to be copied into PACKAGING_DESIGN.md, says that when conda rolls back an interrupted post-link, it removes the feature directory and keeps the file changes, and that reinstalling the feature package completes the job (plan:714-715). Two facts make this false, and the plan's own §2.3 states the second (plan:155-157):
- the rollback reverses every action group of the transaction (link.py:1038-1045), not only the feature directory;
- UpdateHistoryAction.reverse deletes conda-meta/history even for an environment that already existed (core/path_actions.py:1075-1080). After that, conda refuses the prefix with DirectoryNotACondaEnvironmentError.

Writing exit 0 into the hook text (plan:345) prevents a failed post-link only while the hook shell survives. Ctrl-C reaches the whole process group, so the hook shell dies too. conda turns the signal into CondaSignalInterrupt, reverses the interrupted package (link.py:1115-1126), keeps running the remaining post-links, then rolls back the whole transaction without running any scripts.

Measured, with SIGINT sent to conda's process group during the first feature's post-link (review-ipc3/critic-user/run4.sh, run4.out):
- b.ML, c.ML and d.ML stay patched;
- the tool and every feature package of the transaction are gone;
- conda-meta/history is missing, so the next `conda install` and `conda remove` both fail with DirectoryNotACondaEnvironmentError.
In critic-landing/rollback2/run.out, reinstalling the feature package, which is Appendix A's recovery, returns rc=1 'not a conda environment'.

Decision 5's guarantee that the next apply or unapply completes the move (plan:279-281) is about a killed tool. After this rollback the tool itself is gone. The plan's interruption tests kill only the tool, never conda (plan:600).

Two recoveries were measured:
- `touch conda-meta/history`, then repeating the same conda command, converges (critic-user/run4.out);
- `conda create -p <prefix> <specs>`, then `--force-reinstall isabelle`, restores the files (critic-landing/rollback2/run.out).
`conda create -p` alone, conda's own suggestion, leaves the patched files behind with no package that owns them.

**Editor.** U3's derived claim that later post-links would print 'Update the named package' was not measured with the real tool; it is inference.

The scenario requires conda itself to be interrupted, so it is an edge case. But Appendix A states the recovery as a property, and copying a false recovery into PACKAGING_DESIGN.md is what round 2's C9 already objected to.

**Relaxation proposed by the editor.** Rewrite decision 5 and Appendix A to say what is true:
- the convergence claim holds for an interrupted apply or unapply command;
- an interrupted conda transaction is rolled back whole, and conda-meta/history is deleted;
- the recovery is `touch $PREFIX/conda-meta/history` and then the same conda command again (or re-creating the environment over the prefix, then `--force-reinstall isabelle`).

Put that recovery in the README. Add a hook-layer case that sends SIGINT to conda's process group during a post-link and checks that the documented recovery ends with status all applied. Optionally, let status report a leftover isa.staging as 'an earlier run was interrupted'.

**Defender: confirmed** (needs owner: False).

I could not refute the defect. Four corrections apply: one to the mechanism, one to the scope, one to the evidence, and one to the editor's relaxation.

Where the false sentence comes from. Rev 3 did not invent it. The round-2 judge's C2 action ordered it almost word for word: "conda's rollback after an interrupted post-link removes the feature directory while the file changes stay, and reinstalling the feature completes it" (REVIEW2:584). That action took it from defender-C2's caveat (REVIEW2:532, :568). The author followed the judge but put the sentence in Appendix A (plan:714-715) instead of the write-path decision, which was decision 8 in rev 2 and is decision 5 now. The sentence is still false, and Appendix A is the text to be copied into PACKAGING_DESIGN.md (plan:692). It also contradicts the plan's own §2.3, which says a rollback deletes conda-meta/history and conda then stops treating the directory as an environment (plan:157).

What is confirmed (conda 25.11.1):
1. A whole-transaction rollback. conda installs its own handler for SIGINT, SIGTERM, SIGQUIT and SIGABRT around the transaction (link.py:916; common/signals.py:12-18). The handler forwards the signal to its direct child and then raises CondaSignalInterrupt (conda/__init__.py:153-163). `_execute_post_link_actions` catches that exception, reverses the interrupted package (link.py:1115-1126), and the loop keeps running the remaining post-links (:964-967). At the end, every action group of the transaction is reversed (:1038-1045) and no scripts run. The register group carries UpdateHistoryAction (link.py:582-595). Its reverse puts the held copy back and then deletes it (path_actions.py:1075-1080), so even the history from before the transaction is lost. Without history, `is_environment` is false (prefix_data.py:216-223; base/constants.py:334).
2. The mechanism is stronger than the challenge says. My test E1 (defender-C11/run.out) used a post-link that ignores SIGINT (`trap '' INT TERM`) and ends with `exit 0`. conda still rolled it back, and history went MISSING. The `exit 0` in the hook text (plan:345) has no effect on this path; "only while the hook shell survives" is too weak. E1 also showed the hook kept running after conda had exited (trapper-done appeared later). With SIGTERM sent to conda alone, conda forwards it only to the hook shell, not to the tool (round-2 defender-C2 e5), so the tool can go on writing the tree after the rollback.
3. Orphaned changes and a refused environment. critic-user/run4.out and my E3 both show b.ML, c.ML and d.ML patched, only isa's package record left, and history MISSING. The next `conda install fc` and `conda remove isa` both fail with DirectoryNotACondaEnvironmentError. Re-installing the feature, which is Appendix A's recovery, returns rc=1 (critic-landing/rollback2 c3.log; my E2).

Corrections:
- Which files stay patched. The toy tool does not enforce decision 3's strict chain, so its later post-links applied fb and fc. The real tool would find the chain broken, because fa's directory has been reversed, and would only leave the files the interrupted post-link had already replaced. Orphaned changes remain whenever the interrupt falls between two `os.replace` calls.
- "After this rollback the tool itself is gone" holds only when the tool came in the same transaction (E3). In E2 the env already had the tool, fa and fb, and I installed fc alone. The tool survived, but fc's feature directory was gone: `status` lists only fa and fb, and `apply` does nothing. The tool cannot see the rolled-back feature's changes. So decision 5's promise that the next apply or unapply finishes the move (plan:279-281) fails on this path in both cases.
- No test covers this. The pytest interruption case kills only the tool (plan:464). The hook-layer list (plan:473-484) has no case that interrupts conda, yet plan:600 claims interruptions are covered there.
- Wrong citation. The "touch, then repeat" recovery is not in critic-user/run4.out (run4.sh never touches history). I measured it myself.

The relaxation's recovery is incomplete. `touch conda-meta/history` followed by the same `conda install fc` does bring the tree back to all applied (E2, E3). But history then lists only ['fc']. `conda remove fc --dry-run` would then remove isa, the tool, fa, fb and fc. In an env built the same way without the interruption, the same dry run removes only fc (run.out). Two recoveries name every package to keep and restore those explicit requests; both converged:
- `touch conda-meta/history; conda install isa fc` (run2.out variant install_all);
- `conda create -p <prefix> isa fc` over the prefix (run2.out variant create).
In both, history records ['fc','isa'] and `conda remove fc` keeps isa. This depends on the transaction having something to link, because conda does not record anything when there is nothing to do (cli/install.py:525-536; plan:451). `--force-reinstall isabelle` is only needed when the user gives up the feature (critic-landing c5.log). Of the editor's optional ideas, a leftover isa.staging is a weak signal: it cannot say which feature's changes are orphaned, and a plain killed apply, which decision 5 already handles, leaves it too.

Severity: the trigger is rare, since it needs Ctrl-C or SIGTERM during the post-link window. But the consequence is an environment conda refuses plus untracked patches. And a false recovery would be written into a binding design document, the same objection round-2 C9 raised. Major is defensible.

Experiment: All runs are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C11/. They use real conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and a file:// toy channel. The channel is built by mkchan4.py, which is critic-user's mkchan3.py plus a package `trapper` whose post-link runs `trap '' INT TERM; sleep 3; exit 0`. SIGINT goes to conda's process group, the way Ctrl-C does.

run.sh → run.out:
- E1: the trapping post-link is rolled back anyway (CondaSignalInterrupt; history MISSING), and the hook keeps running after conda exits.
- E2: an env with isa, tool, fa and fb; `conda install fc`; interrupted during fc's post-link. Only fc is reversed, the tool stays, history is MISSING. `status` shows only fa and fb, and `apply` does nothing. `conda install fc` gives DirectoryNotACondaEnvironmentError. After `touch history`, the same `conda install fc` converges to all applied, but history then has only ['fc'], and `conda remove fc --dry-run` would remove isa too. The reference env built without the interruption would remove only fc.
- E3: the run4 shape; the same orphaned b, c and d; touch plus the same command converges, with the same pruning side effect.

run2.sh → run2.out: after the run4-shaped rollback, two recoveries both reach all applied, with history ['fc','isa'], and `conda remove fc` keeps isa:
- `touch history; conda install isa fc`;
- `conda create -p <prefix> isa fc`.

Source reads:
- link.py:916, :964-967, :1006, :1038-1045, :1115-1126, :582-595;
- conda/__init__.py:153-163; common/signals.py:12-18;
- path_actions.py:1075-1080; prefix_data.py:216-223; base/constants.py:334;
- cli/install.py:525-536.

Prior evidence re-read:
- critic-user/run4.sh and run4.out (no touch step in them);
- critic-landing/rollback2 run.out and c1-c5.log;
- REVIEW2:532, :568, :584 (where the false sentence comes from).

Recommended fix: The wording and the test fall under ruling 17 (the author may decide wording and tests without changing the design).

1. Appendix A (plan:714-715). Keep the first clause: an interrupted apply or unapply converges on the next run. Replace the rollback clause with something like:
   "When conda itself is interrupted (Ctrl-C, SIGTERM) during the post-links, it rolls back the whole transaction. Every package of that transaction is removed, possibly including the tool, while the changes the post-links already wrote under `$PREFIX/isa` stay. The `exit 0` in the hooks does not prevent this. conda 25.11.1's rollback also deletes conda-meta/history, so conda refuses the environment until it is repaired. Recovery: `touch $PREFIX/conda-meta/history`, then `conda install` again, listing every package you want to keep plus the interrupted one (or `conda create -p $PREFIX <the same packages>`). The chain then re-applies itself. To give up the feature instead: `conda install --force-reinstall isabelle`."

2. Decision 5 (plan:279-281). Limit the convergence promise to an interrupted command of the tool. Add one sentence: inside a hook, conda's rollback removes the feature directories, so the tool cannot see those changes; the recovery is re-running the conda transaction (Appendix A). Add the signal path to §2.3 (plan:155-157) with the citations link.py:916 and conda/__init__.py:153-163.

3. README (decision 14, plan:450-452): put the same recovery there. Note that listing every package to keep matters, because the explicit requests stored in history are lost.

4. Decision 15, hook-layer tests: add one case. Use an env that already has isabelle and a lower feature; install a two-file feature; send SIGINT to conda's process group between the two file moves. Assert that history is missing. Run the documented recovery. Assert `status` is all applied and `conda remove <top> --dry-run` keeps isabelle. Change plan:600 so it does not claim coverage this case lacks. The shape of defender-C11/run2.sh is about 30 lines.

5. §10, C2 row: record that the round-2 judge's sentence (REVIEW2:584) was measured false and replaced.

Optional:
- Outside conda-hook mode, when `P/conda-meta` is a directory but `conda-meta/history` is missing, `status`/`apply` print the recovery line. This test is reliable: history is missing only during the hooks of a fresh create (plan:161, :227). It is more useful than reporting a leftover isa.staging, which I would not require.
- State that `conda-hook` keeps Python's default SIGINT and SIGTERM handling and never masks them.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed. The false sentence in Appendix A (plan:714-715) traces back to the round-2 judge's C2 action (REVIEW2:584).
- conda reverses the whole transaction (link.py:1038-1045) and deletes conda-meta/history (path_actions.py:1075-1080).
- `exit 0` in the hook does not help: a hook that traps SIGINT was rolled back anyway (defender-C11/run.out E1).
- When the tool survives, it cannot see the rolled-back feature's changes (E2).

The editor's recovery is incomplete. After `touch history`, repeating the same command records only that package as requested, so a later `conda remove` prunes isabelle too.

Author:
(1) Appendix A and decision 5 (plan:279-281) limit the convergence claim to an interrupted command of the tool. They state that an interrupted conda transaction:
- is rolled back whole, possibly removing the tool;
- leaves the files the post-links already wrote;
- deletes conda-meta/history.
Recovery: `touch $PREFIX/conda-meta/history`, then `conda install` listing every package to keep plus the interrupted one, or `conda create -p $PREFIX <the same packages>`. Both are measured to converge with the history correct (defender-C11/run2.out). To give the feature up instead: `--force-reinstall isabelle`.
(2) Add the signal path to §2.3, citing link.py:916 and conda/__init__.py:153-163.
(3) Put the same recovery in the README.
(4) Add a hook-layer case: send SIGINT to conda's process group between two file moves; assert history is missing; run the documented recovery; assert status is all applied and that `conda remove <top> --dry-run` keeps isabelle.
(5) plan:600 must not claim this case is covered.
(6) Record in §10 that REVIEW2:584's sentence was measured false.
(7) Optional: status prints the recovery line when conda-meta exists but conda-meta/history does not, outside conda-hook mode.

### C12 [major] (b2) is tied to a release only by the roundtrip_checked checkbox, which binds no tags, no isabelle build and none of the bytes built; the stated reason (b2) cannot run in CI no longer holds

Section: Decision 11 input roundtrip_checked (plan:397); decision 17 (plan:499-509)  ·  merged from: consistency-CONS-14, landing-L5, user-U13

**Statement.** Migration §5.1 requires (b2), the round-trip check, before every feature-package publication (ISABELLE_GIT_MIGRATION_PLAN.md:409-413). Decision 11 enforces this only with a boolean input that the operator ticks after running (b2) locally (plan:397, :502). The box binds nothing: it records neither the tags checked, nor the isabelle build, nor the bytes built.

(b2) reads the local package checkouts (plan:501), while the workflow packages the files it finds at the input tags (plan:398). The two can differ, so the bytes that ship are never round-tripped.

The reasons the plan gives for keeping (b2) local (plan:501-502) are that it needs the private isabelle-patched repository and the local conda cache. Neither still holds:
- decision 11 already requires a read-only token for private repositories (plan:398-399), and the same token can read isabelle-patched, which is private (ai-artifacts/isabelle-git-migration/RECORD.md:144-145);
- every leg already installs the pristine build (plan:400), and decision 17's other base is the downloadable official tarball (plan:508).

The script's signature also names no Isabelle repository and no tags for its `git diff-tree` (plan:501, :506).

**Editor.** No overreach. Under the owner's elegance rule, a checkbox that asks people to remember a gate is the shape to replace.

**Relaxation proposed by the editor.** Run tools/check-roundtrip as a job of the batch workflow, on linux-64, after the build:
- assemble features.d from the packages just built, so the check covers the shipped bytes;
- copy A is that leg's installed pristine isa/;
- copy B is `patch -p1 -F0` of `git diff-tree -r -p --no-renames <bottom tag> <top tag>`, fetched from isabelle-patched with the same token;
- the publish jobs depend on it.

Delete roundtrip_checked. Keep the script for local use, with explicit --repo and tag arguments.

**Defender: partially_confirmed** (needs owner: False).

The main defect holds, at major severity. In rev 3, the only thing that ties (b2), the round-trip check, to a release is an attestation flag. Two details of the challenge are overstated, and one part of the relaxation should change.

CONFIRMED.
1. Migration §5.1 requires (b2) before every package publication, and on the build itself, so that dev_patches' etc/options hunk is covered (ISABELLE_GIT_MIGRATION_PLAN.md:409-413, especially :411-412). Rev 3 enforces this only through `roundtrip_checked`, a boolean the operator sets after running (b2) locally (plan:397, :501-502). The flag records nothing: no tags, no isabelle build, no hash of the patch bytes.
2. The checked inputs and the shipped inputs are different objects.
   - (b2) reads local feature-repository directories (plan:501, :503) and some copy of a pristine build (plan:508).
   - The workflow packages the feature repositories checked out at the input tags (plan:398), against the build named by `isabelle_build` (plan:395, :400).
   - Ruling 22 makes every new isabelle build a republication of every feature package (plan:84, :408), and each republication is a publication under migration :409. The flag can be ticked from a run on an older build.
   - Toy experiment S2: a packaging edit next to dev_patches' etc/options context. (b2) passes on build n and fails on build n+1.
   - Toy experiment S1: the tagged commit carries a stale patch file while the local checkout is correct. (b2) on the local checkout passes; (b2) on the bytes at the tag fails.
   - Nothing else gates this before upload. §6 (a) installs only isabelle-light-locale (plan:589). qiyuan-dev-patches is first installed by the smoke test after publication (plan:404-406).
3. The local-only rationale has mostly lapsed.
   - "The local conda cache" no longer applies: every leg installs `isabelle 2025.2 <isabelle_build>` from the channel (plan:400), and the other base, the official tarball, can be downloaded (plan:508).
   - CI already apt-installs GNU patch (isabelle-packaging-ci build.yml:119-124).
   - Fetching the two tags is cheap. Measured: a depth-1 fetch of the pristine tag plus the dev_patches tip from the local isabelle-patched clone took 19 MB of objects and 0.6 s, and the diff-tree between them is 40 files, 157 KB. GitHub reports isabelle-patched's diskUsage as 18915 KB.
4. Under the owner's elegance rule, a flag that asks the operator to remember a gate is the shape to replace.

OVERSTATED.
(a) "The same token can read isabelle-patched."
   - Decision 11's token is conditional: it is needed only for private feature repositories (plan:398-399). `gh repo view` today: Light_Locale is PUBLIC and isabelle-patched is PRIVATE. The other feature repositories do not exist yet (REVIEW2 C12 defender, `gh repo list`).
   - So the token may never exist. CI needs a credential whose scope includes isabelle-patched.
   - This is surmountable, not a blocker: the round-2 judge explicitly allowed "name a read-only credential for CI" (REVIEW2:1566), and the owner already runs `gh secret set` in the same step (plan:407).
   - The tags must also be pushed to isabelle-patched: make-patches creates them only locally (tools/make-patches:210), and RECORD.md:144-146 records a single push.
(b) "The signature names no Isabelle repository and no tags."
   - Every tools/ script locates the repository with `-C`, defaulting to the current directory (make-patches:266, check-signatures:103, new-tree:158, advance-daily:29).
   - Both tags can be derived from the inputs. The bottom tag is `<R>/pristine/<etc/ISABELLE_ID>`, read from the tree exactly as decision 3 point 1 does (plan:245). The top tag is the top feature's provenance `release_tag` (plan:241-243).
   - This is a wording gap: the plan should state the derivation.
   - The relaxation's explicit tag arguments are worse: they add a way to check a pair of tags that is not the pair the packages under test claim.

NOT A SILENT DEVIATION. Rev 3 literally took the round-2 judge's first option, "runs locally on the owner's order" (REVIEW2:1566). The defect is that rev 3 then added a workflow, with a token and installed builds, that removes that option's rationale.

ADJACENT (outside C12). Plan:332 still says the (b2) script imports git_apply and install_files. Decision 17 runs the chain-aware command line instead (plan:504). The round-2 judge asked for this sentence to be reworded (REVIEW2:1543, :1567).

THE RELAXATION ON ITS MERITS. Running (b2) in CI is sound.
- Running it on linux-64 only suffices: the patch files are noarch, and the mode-bit comparison is POSIX-only.
- Publish jobs that `needs:` the check make an unchecked publication impossible.
- It adds a gate and does not contradict ruling 25 (plan:97-101).
- Change: derive the tags rather than pass them, and name the credential and the tag push.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C12/

(1) toy/setup.sh builds the toy:
- an isabelle-patched-like repository with tags R/pristine/ID0, R/f1/1 and R/f2/1; f2 changes etc/options line 5, changes src/b.ML and creates src/new.ML;
- two feature repositories with committed and tagged patches/R/ plus provenance;
- two "pristine builds" that differ only by a packaging edit to etc/options: line 25 in build n, line 6 in build n+1.

toy/b2.sh is a (b2) prototype. It assembles features.d, orders the chain by exact tags, and builds copy A with isolated git apply (GIT_CEILING_DIRECTORIES, white-listed environment). Copy B is `patch -p1 -F0` of diff-tree bottom..top. It compares with `diff -r` plus sorted `find -printf '%M %p'`, asserts that A differs from the original, unapplies A and compares again. Both tags are derived: the bottom from etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID, the top from the top feature's release_tag.

Results:
- Baseline on build n: PASS.
- S2, same packages on build n+1: "FAIL: copy A: f2 etc-options.patch does not apply". A flag ticked from the build-n run would let this republication through.
- S1, fr2b's tag points at a commit with a stale src-b.ML.patch (+Bx), while HEAD is correct (+B2). (b2) on the local checkout: PASS. (b2) on `git archive R/f2/1`, which is what the workflow packages: "FAIL: A != B" (Bx vs B2).
- CI shape: a bare repository with a depth-1 fetch of only the two derived tags. (b2): PASS.

(2) Real cost. A depth-1 fetch of refs/tags/Isabelle2025-2/pristine/89701cf1768e plus refs/heads/Isabelle2025-2/dev_patches from file:///home/qiyuan/Current/MLML/contrib/Isabelle2025-2 into a scratch bare repository:
- 19 MB of objects, 0.6 s;
- `git diff-tree -r -p --no-renames` between them: 40 files, 157093 bytes.
This only read the source repository.

(3) `gh repo view` (read-only): Light_Locale PUBLIC; isabelle-patched PRIVATE, diskUsage 18915; my_better_isabelle_prover PUBLIC.

(4) Read checks:
- Light_Locale has no tags.
- make-patches tags only the local Isabelle repository (make-patches:210).
- build.yml:119-124 installs GNU patch on ubuntu-latest.

Recommended fix: Decision 11 and decision 17:

1. Delete `roundtrip_checked` (plan:397). Also delete "CI 不跑；… 由操作者据此勾选" (plan:501-502).

2. Add a job `roundtrip` to release-features.yml. It runs on linux-64, after the build and before any publish job; every publish job `needs:` it. It runs `tools/check-roundtrip` with these inputs:
   - the original tree: a `cp -a` copy of that leg's installed `isabelle 2025.2 <isabelle_build>` `isa/`;
   - the features.d: taken from the feature packages just built (the shipped bytes);
   - the Isabelle repository: `-C` pointing at a depth-1 fetch, from isabelle-patched, of exactly the two tags.
   The tags are derived, not passed:
   - bottom = `<R>/pristine/<etc/ISABELLE_ID>`, read from the tree (decision 3 point 1);
   - top = the top feature's provenance `release_tag`.

3. Name the credential: a read-only (Contents: read) token whose scope includes isabelle-patched, set by the owner with `gh secret set` together with the R2 keys (plan:407). Decision 11's conditional token for private feature repositories becomes this one token.

4. Add to the release procedure that the release tags are pushed to isabelle-patched before the run (make-patches:210 tags only locally).

5. Keep the script for local use under the same signature, with `-C` per the tools/ convention. Use it for §5 step 4 (the tarball tree) and for step 6. State in decision 17 how both tags are derived.

6. Adjacent: plan:332 still says the (b2) script imports git_apply and install_files. Replace it with "(b2) runs the tool's command line from the checkout; copy B uses `patch -p1 -F0`" (REVIEW2:1543).

**Judge: partially_confirmed → author_decides_then_rereview.** The main defect is confirmed.
- roundtrip_checked binds nothing (plan:397, :501-502).
- (b2) checks local checkouts against some build, while the workflow ships the bytes at the tags built against isabelle_build. defender-C12's S1 and S2 show both gaps.
- The local-only rationale has lapsed.

Overstated:
- The token is conditional (plan:398-399) and may never exist. CI needs a named credential whose scope includes the private isabelle-patched.
- The tags can be derived; they need not be passed.

Author:
- Delete roundtrip_checked and plan:501-502's 'CI 不跑'.
- Add a job to the batch workflow, on linux-64, after the build and before every publish job (each publish job `needs:` it). It runs tools/check-roundtrip on:
  - a copy of that leg's installed isa/;
  - a features.d assembled from the packages just built;
  - `-C` pointing at a depth-1 fetch of exactly two tags from isabelle-patched: bottom = <R>/pristine/<etc/ISABELLE_ID> read from the tree, and top = the top feature's provenance release_tag.
- Name one read-only Contents:read token covering isabelle-patched and any private package repository, seeded at §5 step 5 (C28).
- State that release tags are pushed to isabelle-patched before the run (make-patches:209-211 tags only locally).
- Keep the script for local use with the tools/ `-C` convention.
- Fix plan:332's 'the (b2) script imports git_apply/install_files' (REVIEW2:1543, :1567; see C19).

### C13 [major] The hook-layer tests do not test what the renderer emits, and light's component payload has no registration or unregistration check anywhere, although the channel requires both for every component package

Section: Decision 15 hook-layer tests (plan:473-486); decision 9 component lines (plan:353-355); decision 10 renderer (plan:385-387); §6 (a), (b) (plan:589-591)  ·  merged from: landing-L7

**Statement.** The hook-layer tests build their packages with 'a small generator' (plan:473). So the renderer, the only producer of feature-package recipes and hooks (plan:385-387), is first executed by conda in the five-leg acceptance, which by C10 comes after the pristine publication.

The component payload added by ruling 21 is tested nowhere:
- the hook-layer list (plan:476-484) has no package with share/<pkg>/ and `components -u/-x` lines;
- §6 (a) asks for a theory importing Light_Locale to build 'on the legs the user authorizes' (plan:590), which names no leg;
- §6 (b) does not check unregistration.

The channel requires, for every component package (RELEASE_CHECKLIST.md:634-642):
- both hook sets present, the .bat in CRLF;
- the component registered, confirmed by reading etc/components;
- the session building from the installed package;
- the pre-unlink unregistering it, non-vacuously;
- a smoke on windows-latest as well as ubuntu-latest.
The reason is that a Windows registration failure is silent (Isabelle_RPC release-conda.yml:336-345). A plain `conda remove` takes isabelle's pre-unlink with it, so an 'entry is gone' check proves nothing (RELEASE_CHECKLIST.md:312-313).

The plan also does not say where the generator's tool package gets python>=3.12 and git>=2.43 under a file:// channel (see C15).

**Editor.** Verified plan:473 and RELEASE_CHECKLIST.md:634-642. No overreach.

**Relaxation proposed by the editor.** Build the hook-layer toy packages with the real renderer and rattler-build 0.69.1, with conda-forge in the channel list, and include one toy feature that carries a component payload.

Assert that etc/components names share/<pkg> after install, and no longer names it after `conda remove --force <pkg>`, with isabelle kept installed so the check is not vacuous. Repeat the registration and unregistration check on the win-64 leg in §6. Name the legs, and give a timeout, for §6 (a)'s session build.

**Defender: partially_confirmed** (needs owner: False).

The core of C13 holds, and an experiment makes it stronger than stated. Three details of the statement and of the relaxation do not hold.

WHAT IS CONFIRMED

1. The hook-layer tests do not use the renderer.
- Decision 15 builds the hook-layer test channel with "小生成器" (a small generator, plan:473). The packages carry "决定 9 的真实钩子文本" (decision 9's real hook text, plan:474).
- The renderer is a separately defined thing, tools/render-feature-recipe (plan:385-387). Its only named caller is the batch workflow (plan:399). It is what joins the fragment to the component registration lines and lays out share/<pkg>/ (plan:383-386).
- So the hook text that light actually ships (fragment plus `components -u/-x`) is never run by the hook-layer tests. Rendered recipes are first built and installed at §5 step 7 (plan:581).
- This is the channel's own anti-pattern: "the code under test is not on the path the test takes" (RELEASE_CHECKLIST.md:647-651).
- The round-1 judge also put the renderer on the local path: "It runs at build time, both locally ... and from one reusable release workflow" (REVIEW1:1921).

2. Registration and unregistration of the component are checked nowhere.
- No hook-layer case has a package with share/<pkg>/ or `components` lines (plan:476-484).
- The batch workflow has no payload check (plan:398-400). The channel requires: unpack the package, both hook sets present, the .bat in CRLF, and the hook's path literal matching the install location (RELEASE_CHECKLIST.md:633-634). Isabelle_RPC does exactly this (release-conda.yml:115-171).
- §6 (a) never reads etc/components (plan:589-590), and §6 (b) never checks unregistration (plan:591).
- The win-64 checks list only git.exe, the ceiling directories, longpaths, the lock and os.replace (plan:485-486).
- The channel requires: "the component is registered — read etc/components, don't infer"; the pre-unlink unregisters, non-vacuously; and a smoke on windows-latest, because a Windows failure is silent (RELEASE_CHECKLIST.md:636, :640-642; Isabelle_RPC release-conda.yml:339-343, :404-430, :544-581).
- The only indirect check is the session build in (a), and only "在用户授权的腿上" (on the legs the user authorizes). Isabelle_RPC itself builds only on Linux, "too slow on Windows" (release-conda.yml:432-433). So a Windows registration failure for light would ship unnoticed.

3. New evidence: the missing check hides a real defect.
- In toy experiment D, `conda install --force-reinstall isabelle` left isabelle-light-locale installed but deleted etc/components entirely.
- Mechanism: isabelle's pre-unlink runs `rm -rf` on the environment's user directory (isabelle-packaging-ci/conda/recipe.yaml:223-231). `isabelle components -u` writes into exactly that directory: components_path = $ISABELLE_HOME_USER/etc/components (Isabelle2025-2/src/Pure/System/components.scala:294). Only isabelle's own hooks run (plan:162-163), and the tool never runs isabelle (plan:231). So light's post-link never re-registers the session.
- Yet the plan gives this command as the repair in several places: plan:367, :450, :549-550 (which says "the installed features are re-applied automatically") and :560-561. It is also §6 (c) (plan:592) and a hook-layer case (plan:478).
- After following that advice, a light user has every feature `applied` and an unknown Light_Locale session.
- Experiment G: `conda install --force-reinstall isabelle isabelle-light-locale` restores the registration.

WHAT IS REFUTED OR NARROWED

(a) "After the pristine publication" causes little harm for the renderer.
- Step 6 does publish the pristine build (plan:579) before step 7 (plan:581).
- But nothing in the pristine package comes from the renderer, and feature packages are published only at step 8 (plan:582). So a renderer bug costs a slower five-leg CI loop, not a defective release.
- The one place this ordering does bite is a different item, probably C10's: the fragment's .bat is frozen into the published pristine build (plan:220-221, :369) before anything runs its tool branch on Windows.

(b) "Names no leg" is not a defect on its own.
- "在用户授权的腿上" (on the legs the user authorizes) is the round-2 judge's own instruction: "on an authorised runner" (REVIEW2:1641).
- The fix is to put the cheap registration read on every leg, not to name build legs.

(c) Vacuity is already prevented in §6.
- §6 requires every package that should remain to be explicitly requested (plan:588), and (a) requests isabelle explicitly (plan:589).
- Experiment A: in that setup a plain `conda remove isabelle-light-locale` keeps isabelle, and etc/components still exists without the entry.
- Negative control: with a pre-unlink that lacks `-x`, the stale entry is caught.
- Only when the component alone was requested does a plain remove take isabelle with it and make an "entry is gone" check vacuous (experiment B, matching RELEASE_CHECKLIST.md:312-313).
- So `--force` is one valid method, not a requirement. The check just has to assert that etc/components still exists.

(d) Not judged here: where the toy tool package gets python and git (deferred to C15).

ON THE EDITOR'S RELAXATION
- Right: render the toy feature packages with the real renderer and build them with rattler-build 0.69.1 (`--no-test`, which avoids the HOME problem in RELEASE_CHECKLIST.md:328-337). This makes what is tested the same as what ships.
- Right: include one component-carrying toy, and check registration and unregistration on win-64.
- Missing: a toy tree has no real Isabelle, so a toy registration check only means something if the toy isabelle carries a stub `isa/bin/isabelle` (answering `getenv -b ISABELLE_HOME_USER` and doing `components -u/-x`) plus the real pre-unlink text, as my generator does.
- Missing: it leaves out the payload check and the `--force-reinstall isabelle` assertion, which is the one that finds the real defect.
- Unneeded: it requires `--force` and named legs for the build.

ASIDE FOR THE JUDGE (outside C13)
- Experiment F: in an environment holding today's kind of component package (`isabelle >=2025.2,<2025.3`, Isabelle_RPC/conda/recipe.yaml:192) and no feature package, `conda update --all` from one isabelle build to the next also deletes etc/components.
- The new pristine build of step 6, with `conda update --all` as the documented update command (ruling 22), makes this reachable for every existing component user. It belongs to the CI plan.

Experiment: Everything was read-only except my scratch directory, /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C13/. I installed nothing into the owner's environments and ran no isabelle command.

Reading:
- the plan in full;
- REVIEW2 (C11 judge at :1639-1643, summary at :1-200);
- REVIEW1 (C20 and C21 judges at :1839-1850 and :1915-1922);
- RELEASE_CHECKLIST.md:250-337 and :629-651;
- Isabelle_RPC/.github/workflows/release-conda.yml:100-581 and conda/recipe.yaml:140-192;
- Semantic_Embedding/conda/recipe.yaml:264-300;
- isabelle-packaging-ci/conda/recipe.yaml:170-260;
- Isabelle2025-2/src/Pure/System/components.scala:290-320;
- contrib/light_locale/ROOT and tools/patched_files.txt (no Scala files are patched, so `isabelle components` is not affected by the patches).

Toy conda channel:
- Tools: conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS, CONDA_ENVS_DIRS and TMPDIR; environments not registered.
- Generator: mkchan.py. It builds an `isabelle` 2025.2 build 1 whose stub isa/bin/isabelle answers `getenv -b ISABELLE_HOME_USER` (keyed by the prefix basename, as pack.sh does) and does `components -u/-x` on $ISABELLE_HOME_USER/etc/components. It carries the verbatim pre-unlink of recipe.yaml:223-231. It also builds `isabelle-light-locale` 1 (build Isabelle2025_2_1_0, pinned to `isabelle 2025.2 1`) with share/isabelle-light-locale/ROOT and the registration lines of plan:353-355.

Results (run.sh: run-pos.out, run-neg.out):
- A: isabelle and light both explicitly requested. Registered after install. After a plain `conda remove isabelle-light-locale`, isabelle stays and etc/components exists and is empty, so the check is non-vacuous.
- A, negative control (pre-unlink without -x): the stale entry is still there, so the check catches the broken pre-unlink.
- B: only light requested. A plain remove also removes isabelle, and etc/components is absent. An "entry is gone" check would be vacuous; with the negative control it still passes, wrongly.
- C: `remove --force` keeps isabelle, and the entry is gone. The negative control is caught.
- D: `conda install --force-reinstall isabelle`. etc/components is absent while isabelle-light-locale stays installed: the registration is silently lost.

run2.sh (mkchan2.py adds isabelle build 2 and an isabelle-rpc-shaped package; output run2.out):
- E: with light pinned to build 1, `update --all` does not move (consistent with ruling 22), and the registrations stay.
- F: isabelle plus isabelle-rpc only. `conda update --all` moves isabelle 2025.2-1 to 2025.2-2, and etc/components is absent.

run3.sh (output run3.out):
- G: `conda install --force-reinstall isabelle isabelle-light-locale` keeps the registration.

Recommended fix: Smallest set of changes. All of them are test and wording work under ruling 17, except the optional change to the CI plan in item 2.

1. Decision 15, hook-layer tests (plan:473-484).
- Build the toy feature packages with tools/render-feature-recipe, from toy feature directories (patches/<R>/provenance.txt, and for one of them tools/component_files.txt), using rattler-build 0.69.1 with `--no-test`, fetched the way the existing workflows fetch it.
- Only the toy isabelle packages and the broken-tool variant come from the small generator.
- The toy isabelle carries a stub isa/bin/isabelle that answers `getenv -b ISABELLE_HOME_USER` and does `components -u/-x` on $ISABELLE_HOME_USER/etc/components. It also carries the real pre-unlink of isabelle-packaging-ci/conda/recipe.yaml:223-231.
- Add three assertions:
  (i) after install, etc/components names share/<pkg>;
  (ii) after `conda remove <pkg>` with isabelle explicitly requested, etc/components still exists and no longer names share/<pkg>;
  (iii) after `conda install --force-reinstall isabelle`, the component is still registered.

2. Decision 9 and the repair texts (plan:367, :450, :549-550, :560-561; §6 (c) at plan:592).
- Assertion (iii) fails under today's design: isabelle's pre-unlink deletes etc/components, and light's post-link does not run again.
- Smallest answer: the repair command also reinstalls the feature packages that carry a component, e.g. `conda install --force-reinstall isabelle isabelle-light-locale` (measured to keep the registration). The text then stops claiming that everything is restored automatically.
- The alternative is for isabelle's pre-unlink to keep etc/components. That belongs to the CI plan (decision 12).

3. Decision 11 (plan:398-400). After building, unpack each .conda and check:
- that both hook sets are present;
- that the .bat files are CRLF;
- that the component hooks name share/<pkg>.
This follows RELEASE_CHECKLIST.md:633-634 and Isabelle_RPC release-conda.yml:115-171.

4. §6 (a)-(c) on all five legs (plan:589-592). Read etc/components through the environment's entry point, `<prefix>/bin/isabelle` or `Scripts\isabelle.bat`, converting /cygdrive paths (RELEASE_CHECKLIST.md:302-305):
- after (a) and (c), share/isabelle-light-locale is registered;
- after (b), the file still exists and no longer names it.
The explicit requests in the §6 preamble (plan:588) already keep isabelle installed, so `--force` is not needed. The session build stays on the legs the owner authorizes, as the round-2 judge allowed.

Separately for the judge (outside C13): `conda update --all` to a new isabelle build silently unregisters today's component packages that are not re-released. The CI plan should own that.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- the hook-layer tests use 'a small generator' (plan:473), so the renderer's output is first run in the five-leg acceptance;
- the component payload's registration and unregistration are checked nowhere, against RELEASE_CHECKLIST.md:633-642;
- defender-C13 experiment D shows the check would have found C1's defect.

Narrowed:
- the ordering relative to the pristine publication costs only CI time;
- 'names no leg' is the round-2 judge's own wording;
- vacuity is already prevented by §6's explicit requests (plan:588), so `--force` is not required.

Author:
(1) Build the hook-layer feature packages with tools/render-feature-recipe and rattler-build 0.69.1 `--no-test`. Only the toy isabelle package and the broken-tool variant come from the small generator. The toy isabelle carries:
- a stub isa/bin/isabelle that answers `getenv -b ISABELLE_HOME_USER` and does `components -u/-x`;
- the real pre-unlink of recipe.yaml:223-231.
Assert:
- after install, etc/components names share/<pkg>;
- after `conda remove <pkg>` with isabelle explicitly requested, the file still exists and no longer names it;
- after `--force-reinstall isabelle`, the registration is kept as Q1 decides.
(2) Decision 11's build job unpacks each .conda and checks the hook sets, the CRLF .bat files and the share/<pkg> literal (Isabelle_RPC release-conda.yml:115-171).
(3) §6 (a)-(c) read etc/components on every leg through the environment's entry point, converting /cygdrive paths.

### C14 [major] The new build string Isabelle2025_2_<isabelle build>_<n> amends owner ruling 27 without a ruling; the author deferred it to the owner's review of rev 3, but the plan records it as settled

Section: §0 item 4 (plan:44); decision 10 (plan:378); §9 (plan:657-658)  ·  merged from: consistency-CONS-7

**Statement.** Migration ruling 27 fixes the feature build string as <release name with - replaced by _>_<build number>, e.g. Isabelle2025_2_0. The owner chose that exact name: '名字是 Isabelle2025_2_0 而非 isa2025_2_0' (the name is Isabelle2025_2_0, not isa2025_2_0; ISABELLE_GIT_MIGRATION_PLAN.md:106-108). Migration decision 3 repeats it (:237), and so does its §5.1 (:406).

Rev 3 changes the build string to Isabelle2025_2_<isabelle build>_<n> (plan:378) and paraphrases ruling 27 as only 'starts with Isabelle2025_2_' to make room (plan:44).

The transcript shows the author deferred the change. He called it 'a small follow-on change I plan to write in rev 3, for you to look at then' (jsonl 6566: '一个随之而来的小改动我打算在 rev 3 里写、你到时看') and asked the owner to confirm only the exact isabelle pin. The owner's '确认' (confirmed, jsonl 6569) answered that question. Migration §0 item 31, which records ruling 22, says nothing about the build string (:128-133), and §9 (plan:657-658) does not list it as an open question.

Published filenames are immutable, so this is a naming decision users will see.

**Editor.** Whether '确认' also covered the build string is ambiguous. The author's own words put it up for later review, and CLAUDE.md requires asking when in doubt.

This is not a design defect: the change is reasonable, since `conda list` then shows which isabelle build a package belongs to, and the base pins are prefix matches, so they are unaffected. It is major only because it rewrites an owner ruling's text.

**Relaxation proposed by the editor.** List it in §9 as an owner question, with its reason (the isabelle build is visible in `conda list`) and its cost (an amendment of ruling 27, three more path characters). Quote ruling 27 exactly in §0 item 4. If the owner approves, record it in migration §0 item 31, and update migration :237 and :406.

**Defender: partially_confirmed** (needs owner: True).

CONFIRMED (the substance):
(1) Migration ruling 27 fixes the format: build string = `<release name with - replaced by _>_<build number>`, e.g. `Isabelle2025_2_0`, with the owner's quote "赞同 (a) 但名字是 Isabelle2025_2_0 而非 isa2025_2_0" (ISABELLE_GIT_MIGRATION_PLAN.md:106-108). Decision 3 (:237) and §5.1 step 4 (:406) repeat `Isabelle2025_2_<build 号>`.
(2) Rev 3's decision 10 changes the format to `Isabelle2025_2_<isabelle build>_<n>`, e.g. `Isabelle2025_2_1_0` (plan:378). So the owner's own example name never occurs as a feature build string.
(3) §0 item 4 (plan:43-44) sits under the heading "用户已裁定的事（不再重议）" (things the user has ruled, not up for debate). It shortens ruling 27 to "以 `Isabelle2025_2_` 开头" (starts with Isabelle2025_2_), which misquotes it. The plan marks its amendment of ruling 21 explicitly ("已被第 22 条修订", plan:41-42; "这修订迁移方案 §0 第 21 条的后半句", plan:86) but writes no such note for ruling 27.
(4) Transcript f1ebd39a….jsonl line 6566 (2026-10-23T11:26Z): the author wrote "一个随之而来的小改动我打算在 rev 3 里写、你到时看" (a small follow-on change I plan to write in rev 3; you look at it then). He then asked only "请确认：按'feature 包精确钉死 isabelle 构建'定" (please confirm the exact isabelle pin). Both owner replies answer that question: "确认" (confirmed) at 6569 and "确认 / 请讲下一个问题" (confirmed, present the next question) at 6580. I listed every user and queued message from line 6560 to the end of the file (7093); none touches the build string.
(5) Nothing flags it as open. §9 "待用户在发布时定" (to be decided by the user at release, plan:657-658) does not list it. The handoff file does not list it. Migration §0 item 31 (:128-133) does not mention it, and migration :237 and :406 still carry the old format.
(6) It was not delegated. Migration §9 (:586-589) handed the patch-tool plan only the question whether `Isabelle2025_2_<n>` fits within Windows path-length limits, not the format itself. Ruling 17's delegation covers wording and tests "在不改设计的前提下" (without changing the design, plan:66-67). A published, immutable filename is neither wording nor a test.
(7) Additional, supporting: the round-2 judge's recommended fix for C21(b) says "The renderer writes build.number: N and string: Isabelle2025_2_N" (REVIEW2.md:2699). Rev 3's §10 row for C21 (plan:684) lists `--build-number` but does not say rev 3 departs from that build string. This is a judge action not followed, with no deviation stated.

REFUTED / OVERSTATED:
(a) "The plan records it as settled": half right. Plan:44 attributes the addition to "本计划决定 10" (this plan's decision 10), not to the owner. The author's rev 3 announcement to the owner (jsonl line 7092) also says "build string 带构建号（决定 10）" (the build string carries the build number, decision 10). The owner has been told, but has not answered. What the plan does wrong is misquote ruling 27 inside the list of rulings and fail to flag the change as needing approval.
(b) Severity "major" is too high; this is not a design defect.
- Ruling 22 alone does not require the change: it bumps the build number on every new isabelle build (plan:84), so `Isabelle2025_2_<n>` already keeps filenames distinct.
- The `isabelle` pin is a separate dependency (plan:380).
- Base-package pins are glob prefix matches. I verified with conda 25.11.1's MatchSpec that `==1=Isabelle2025_2_*` matches `Isabelle2025_2_1_0` and `Isabelle2025_2_0` and rejects `Isabelle2024_1_0`.
- The only other dependent is the path-length gate formula (plan:389-391, :494).
- So it is a cosmetic naming choice that can still be reverted until the first publication. It does need the owner's decision before then, because published filenames are immutable. Minor rather than major.

Experiment: 1. Transcript read with python -I: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C14/extract.py and users.py over ~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl.
- Lines 6566 (author defers the build-string change), 6569 and 6580 (both "确认", answering the pin question).
- Every user, queue-operation and queued_command entry from line 6560 to the end (7093): none mentions the build string.
- grep_asst.py: the only later assistant mention is the rev 3 summary at line 7092.
2. Grep of the plan, rev2, REVIEW2, the handoff, migration plan and tools/make-patches for build-string text. Findings: rev 2 had `Isabelle2025_2_<n>` (rev2:33, :279); the round-2 judge's C21(b) says `string: Isabelle2025_2_N` (REVIEW2:2699); make-patches writes only `build_string_prefix` (tools/make-patches:191,202).
3. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C14/ms.py imports conda 25.11.1's MatchSpec read-only under env -i with private HOME, CONDARC and CONDA_PKGS_DIRS. Results: `isabelle-future-assign-interrupt ==1=Isabelle2025_2_*` vs build Isabelle2025_2_1_0 -> True; vs Isabelle2025_2_0 -> True; vs Isabelle2024_1_0 -> False. `isabelle 2025.2 1` vs build 1 -> True; vs 12 -> False.

Recommended fix: Smallest fix (the editor's suggested fix plus one item):
1. Plan §0 item 4 (plan:43-44): quote ruling 27 exactly, e.g. "build string 为 `<发行版名把 - 换成 _>_<build 号>`，如 `Isabelle2025_2_0`（迁移方案第 27 条）". Then add "决定 10 提议改为 `Isabelle2025_2_<isabelle 构建号>_<n>`，修订第 27 条，待用户批准（§9）" (decision 10 proposes the new format; it amends ruling 27; awaiting owner approval, see §9).
2. Plan §9: add an owner question.
- Benefit: `conda list` shows which isabelle build each feature package is for.
- Cost: it amends ruling 27; the first release is named Isabelle2025_2_1_0 instead of Isabelle2025_2_0; paths get a few characters longer, already within the 154-of-198 budget.
- If the owner says no: keep `Isabelle2025_2_<n>` and set the path-length gate (plan:391, :494) back. Nothing else changes; base pins are prefix matches either way.
- Ask it with the round-3 report, before the first publication, because published filenames are immutable.
3. Plan §10 row C21 (plan:684): state that rev 3 departs from the round-2 judge's `string: Isabelle2025_2_N` (REVIEW2:2699), and why.
4. If the owner approves: record it in migration §0 item 31 (or a new item amending ruling 27) and update migration :237, :406 and :588. If the owner declines: revert plan:378 and :389-391.
Severity should be minor (a process and consistency defect), not major.

**Judge: partially_confirmed → owner_decides.** The substance is confirmed.
- Ruling 27 fixes `<release with - replaced by _>_<build number>`, e.g. Isabelle2025_2_0 (ISABELLE_GIT_MIGRATION_PLAN.md:106-108).
- Decision 10 changes it (plan:378).
- §0 item 4 misquotes the ruling inside the list of binding rulings (plan:43-44).
- The author deferred the change to the owner's review (jsonl 6566), and no owner message answers it.
- §10's C21 row hides the departure from REVIEW2:2699's `string: Isabelle2025_2_N`.

Severity is minor. The change is cosmetic, because base pins are prefix matches (verified with conda's MatchSpec, defender-C14/ms.py). It still needs the owner before the first publication, because published filenames are immutable.

Author:
- Quote ruling 27 exactly in §0 item 4, and mark decision 10's format as a proposal awaiting approval.
- Add Q5 to §9.
- Record the departure in §10's C21 row.
- If approved: amend migration §0 item 31 (or add an item amending ruling 27) and update migration :237, :406 and :588.
- If declined: revert plan:378 and the path-length formula (plan:389-391, :494).

### C15 [minor] The final live smoke install cannot be solved: --override-channels drops conda-forge, but the tool needs python and git

Section: Decision 11 final smoke job (plan:404-406); decision 1 (plan:211-212)  ·  merged from: conda-conda-6, consistency-CONS-10, landing-L11, user-U8

**Statement.** The last job runs `conda create -n t --override-channels -c https://conda.qiyuan.me isabelle qiyuan-dev-patches` (plan:404-405). qiyuan-dev-patches pulls in isabelle-patch-control, which needs python >=3.12 and git >=2.43 (plan:211-212). The live channel carries neither: in the 2026-10-24 repodata snapshot, noarch has 8 names and linux-64 has 4, with no python and no git (review-ipc3/critic-landing/live/). A dry run of the same form for isabelle-rpc fails with 'LibMambaUnsatisfiableError: nothing provides python >=3.10' (critic-landing/smoke/).

The house rule is that conda-forge must be in the channel list for anything with Python dependencies (RELEASE_CHECKLIST.md:298); Isabelle_RPC's smoke uses `-c https://conda.qiyuan.me -c conda-forge --override-channels` (release-conda.yml:375). release.yml's isabelle-only smoke can drop conda-forge only because isabelle has no requirements (recipe.yaml:235-237). So the release's final gate would be red on every run, after the packages are already public.

Round 2's C13 judge also asked for a private CONDA_PKGS_DIRS and for C16's update case (REVIEW2:1826-1828). Both were dropped without comment.

**Editor.** U8 also asks for 'a case that installs light into a 2025.2-0 environment'. §6 (e) already does exactly that from the live channel (plan:594), so that sub-item is dropped.

**Relaxation proposed by the editor.** Use `--override-channels -c https://conda.qiyuan.me -c conda-forge` with a private CONDA_PKGS_DIRS. State that every §6 and hook-layer environment uses the local channel, the live channel and conda-forge, in that order, and give the README's install line the same channel pair. Add the update case, or say why it is dropped.

**Defender: partially_confirmed** (needs owner: False).

The main defect is fully confirmed: as written, the final smoke install can never be solved. One side point is also confirmed, but it matters little. The other side point is refuted.

**1. Confirmed: the smoke command cannot be solved.**
- The plan's last job runs `conda create -n t --override-channels -c https://conda.qiyuan.me isabelle qiyuan-dev-patches` on linux-64 and win-64 (plan:404-406).
- qiyuan-dev-patches depends on `isabelle-patch-control >=1.0,<2` (plan:380). The tool is noarch python and needs `python >=3.12` and `git >=2.43` (plan:211-212).
- I fetched the live repodata today (defender-C15/live/{noarch,linux-64,win-64}.json). The only names on the channel are:
  - noarch: auto-sledgehammer, isabelle-ai, isabelle-mcp, isabelle-minilang, isabelle-performant-ml, isabelle-rpc, isabelle-semantic-data, json-spec;
  - linux-64: isabelle, isabelle-nunchaku, isabelle-semantic-embedding, rocksdict;
  - win-64: isabelle, isabelle-semantic-embedding, rocksdict.
  There is no python and no git.
- publish-conda.yml only uploads and re-indexes (plan:178), so publishing the batch cannot add them.
- So after publication the solve fails on every run. The packages are already public by then.
- The house rule says conda-forge must be in the channel list for anything with Python dependencies (RELEASE_CHECKLIST.md:298). Every Python-dependent smoke in the ecosystem follows it, live channel first and conda-forge second:
  - Isabelle_RPC release-conda.yml:229 and :375;
  - Semantic_Embedding release-conda.yml:305-307;
  - Isa-Mini release-conda.yml:234-235 and :340-342.
- release.yml:114-115 can drop conda-forge only because isabelle has no requirements (isabelle-packaging-ci conda/recipe.yaml:235-237).
- The plan's own §10 row C13 (plan:676) claims the "线上冒烟" (live smoke) answers round 2. It cannot, because the smoke cannot pass.

**2. Confirmed but low-weight: the private CONDA_PKGS_DIRS was dropped without comment.**
- The round-2 C13 judge required a private CONDA_PKGS_DIRS for the live smoke (REVIEW2:1826-1828). The rev-1 C19 judge required "conda-forge and a private CONDA_PKGS_DIRS" for the whole §6 run (REVIEW1:1739).
- Rev 3 mentions neither, either at plan:400 or at plan:405, and §10 is silent on it.
- In substance it matters little. The smoke is a separate job (plan:404), so it starts on a fresh GitHub-hosted runner with an empty package cache.
- Still, the author dropped a judge action without saying so. Either add the cache directory or state why it is not needed.

**3. Refuted as a defect: "C16's update case was dropped without comment".**
- Ruling 22 means no feature package can be installed on isabelle-2025.2-0 (plan:80-88). So the rev-2 C16 transition (an environment on 2025.2-0 with features installed, then `conda update isabelle`) can no longer exist.
- Its successor is §6 (e): install light into a 2025.2-0 environment and let the solver upgrade isabelle (plan:594). That case already takes 2025.2-0 and the pristine build from the live channel (plan:400, :594). §6 (h) covers a build bump (plan:597).
- §10's C16 row maps C16 to exactly these cases (plan:679), so the case was not dropped silently.
- Repeating (e) after publication would only re-check the uploaded bytes. The qiyuan-dev-patches smoke already does that for the whole chain.
- At most, §10's C13 row could add one clause pointing to (e).

**4. On the editor's rebuttal.** It is right: U8's request for an install of light into 2025.2-0 is covered by §6 (e) (plan:594).

**5. On the editor's proposed relaxation.**
- Adding `-c conda-forge` after the live channel is necessary, and it is enough (experiment B).
- Keep the order live channel first, conda-forge second. conda-forge also carries json-spec and rocksdict, and the house convention puts the live channel first.
- Naming the channel list for §6 is warranted:
  - plan:400 names only the local channel and the live channel;
  - plan:485 silently assumes git comes from conda-forge;
  - the rev-1 judge required conda-forge there (REVIEW1:1739).
- Naming it for the hook-layer tests is also warranted, and I found an extra reason. Those tests use a private CONDARC (plan:473) and call the real tool, which needs python and git. With an empty private CONDARC, conda 25.11.1 falls back to the `defaults` channels and fails with CondaToSNonInteractiveError (experiment C). So those environments must name their channels explicitly.
- The README install line is optional. Ruling 17 gives wording to the author, and the plan gives no install line at all. The convention to copy is Semantic_Embedding/README.md:13 (`-c https://conda.qiyuan.me -c conda-forge`).

**Severity.** Minor is right. The failure is certain, but it shows up on the first run with an explicit error, and the fix is one token. It does not damage the published packages.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C15/.

**Setup.**
- Every conda run used conda 25.11.1 (~/miniconda3/bin/conda) under `env -i` with a private HOME, an empty private CONDARC and a private CONDA_PKGS_DIRS. All solves were `conda create --dry-run -p <scratch>`. Nothing was installed, and no owner environment or cache was touched.
- live/*.json: today's repodata from https://conda.qiyuan.me for noarch, linux-64 and win-64. There is no python and no git on any of them.
- scripts/mk.py builds a toy channel, chan/noarch, indexed with ~/miniconda3's conda_index. It models the channel after publication with three packages:
  - isabelle-patch-control-1.0.0 (noarch python, depends `python >=3.12`, `git >=2.43`);
  - isabelle-expose-foreign-1-Isabelle2025_2_0_0;
  - qiyuan-dev-patches-1-Isabelle2025_2_0_0, pinned to `isabelle 2025.2 0` and depending on the tool.

**Results.**
- **A.out:** `--override-channels -c file://chan -c https://conda.qiyuan.me isabelle qiyuan-dev-patches` (the plan's channel list). rc=1, with "LibMambaUnsatisfiableError: nothing provides python >=3.12 needed by isabelle-patch-control-1.0.0".
- **B.out:** the same command plus `-c conda-forge` after the live channel. rc=0. git-2.56.0 and python come from conda-forge, isabelle-2025.2-0 from conda.qiyuan.me, and the chain from the toy channel.
- **D_rpc.out:** `--override-channels -c https://conda.qiyuan.me isabelle isabelle-rpc`. rc=1, with "nothing provides python >=3.10 needed by isabelle-rpc-0.4.0", which reproduces the critic's result.
- **C.out:** with the empty private CONDARC and no `--override-channels`, `-c file://chan isabelle-patch-control` fails with CondaToSNonInteractiveError for repo.anaconda.com/pkgs/main and pkgs/r. `conda config --show` reports `channels: [defaults]`.
- **Name collisions.** The cached conda-forge repodata from run B has no `isabelle` and no `isabelle-patch-control`. Its only overlaps with the live channel are json-spec and rocksdict.

Recommended fix: 1. **Decision 11 (plan:405).** Change the smoke command to `conda create -n t --override-channels -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches`, keeping the live channel first as in Isabelle_RPC release-conda.yml:375. Either add a private CONDA_PKGS_DIRS, or state that the job runs on a fresh runner so the package cache is empty.
2. **Decision 11 step list (plan:400).** State the channel list for every §6 environment: `--override-channels -c file://<local channel> -c https://conda.qiyuan.me -c conda-forge`, in that order. This also gives decision 15's "git as resolved by conda-forge" (plan:485) a stated source.
3. **Decision 15 hook-layer test (plan:473).** These tests use a private CONDARC and call the real tool, so name their channels explicitly: `--override-channels -c file://<toy channel> -c conda-forge`. An empty CONDARC falls back to `defaults` and fails on conda 25.11.1 with CondaToSNonInteractiveError.
4. **§10 row C13 (plan:676).** Mention the conda-forge correction and the package-cache decision. Note that C16's update case became §6 (e) under ruling 22 (row C16, plan:679), so the live smoke needs no extra case.
5. **README (optional).** The install line in the README rewrite can follow Semantic_Embedding/README.md:13: `-c https://conda.qiyuan.me -c conda-forge`.

**Judge: partially_confirmed → author_fixes_no_rereview.** The main defect is confirmed.
- The live channel carries no python and no git (defender-C15/live/), so the final smoke install fails on every run: 'nothing provides python >=3.12' (defender-C15/A.out).
- Adding conda-forge after the live channel solves it (B.out).
- The dropped private package cache is confirmed but of little weight, since the job runs on a fresh runner.
- The C16 update case is refuted as 'dropped': it became §6 (e) under ruling 22 (plan:594, :679).

Author:
- Decision 11's smoke (plan:405) becomes `--override-channels -c https://conda.qiyuan.me -c conda-forge`, live channel first (Isabelle_RPC release-conda.yml:375). Either give it a private CONDA_PKGS_DIRS, or state that the job runs on a fresh runner.
- Every §6 environment uses `--override-channels -c file://<local> -c https://conda.qiyuan.me -c conda-forge`.
- The hook-layer tests use `--override-channels -c file://<toy> -c conda-forge`. Otherwise an empty private CONDARC falls back to `defaults` and fails with CondaToSNonInteractiveError (C.out).
- §10's C13 row mentions the correction.
- Optionally, the README install line follows Semantic_Embedding/README.md:13.

### C16 [minor] Appendix A, the argued exception the owner asked for, again states two false facts: an incomplete list of differences from the release and a misdescribed §7.9 precedent

Section: Appendix A (plan:704-706, :711-712); decision 12.4 (plan:419)  ·  merged from: consistency-CONS-8

**Statement.** (1) Appendix A says the only differences from the official release are the three file edits, isabelle.bat and the CI-built heaps (plan:704-706). pack.sh also:
- deletes VSCodium's obj/ directories under contrib/ (scripts/pack.sh:122-139);
- adds .conda-keep marker files to every directory that was empty in the bundle (:284-324).

(2) It calls the cleanup of feature-created files 'the same kind as §7.9's component packages cleaning up their registrations with isabelle components -x' (plan:711-712). PACKAGING_DESIGN.md §7.9 (:876-882) says something else: it is the ruling to apply only user-category patches, with a note that Isa-REPL's conda package patches register_thy in its own install script, at the cost of heap rebuilds. That is in fact a closer precedent for the exception (a package that patches Pure at install time), but the appendix misstates it. And decision 12.4 has the CI plan rewrite §7.9 (plan:419), so the citation will point at text that is about to change.

(The third false statement in this passage, the interrupted-post-link recovery, is C11.)

**Editor.** Ruling 20 keeps pack.sh's three file edits (plan:71-74). The obj/ purge and the markers do not touch Isabelle's source, so they are consistent with 'Isabelle 源码一字不动' (Isabelle's source untouched); only the sentence claiming 'the only differences' is false.

**Relaxation proposed by the editor.** Rewrite the two passages by hand: list the obj/ purge and the .conda-keep markers among the packaging differences, and cite §7.9 for what it actually says (a package that patches Pure in its install script), or drop the citation.

**Defender: confirmed** (needs owner: False).

I tried to refute both halves and could not. Both are wording defects. Neither needs an owner decision.

(1) The list of differences is incomplete.
- Appendix A item 2 says the only differences from the official release are: the etc/settings suffix, ML_system_64, the nunchaku line, Windows bin/isabelle.bat, and the CI-built heaps (plan:704-706). It says "只有" (only), so the list claims to be complete.
- pack.sh also deletes VSCodium's obj/ directories under contrib/ (scripts/pack.sh:122-139).
- pack.sh also writes a .conda-keep marker into every directory that was empty in the bundle (scripts/pack.sh:103-120, :284-324).
- I measured this. The official linux tarball has exactly two empty directories, and the cached pkgs/isabelle-2025.2-0/isa has exactly those two .conda-keep files: contrib/jedit-20251128/jedit5.7.0-patched/jEdit/jars and contrib/vampire-4.8/src/z3.
- The linux tarball has no obj/ entries. The purge matters on win-64, where the obj/ files held the 212-character path (pack.sh:128-129).
- The editor's rebuttal holds, and it supports the challenge rather than refuting it. Neither step touches Isabelle source; pack.sh:132 says it touches nothing else in the tree. Ruling 20 defines "原汁原味" (pristine) as the sources unchanged plus the official ISABELLE_ID (plan:71-74), and both steps fit that. So the design is fine; only the sentence is false.

One more incompleteness the challenge did not name. It matters for the fix.
- The official tarball carries lib/browser_info.db (165 MB) and src/Tools/Find_Facts/lib/isabelle.db (170 MB). Both are produced by build_release -L/-F (build_release.scala:491-536 in Isabelle2025-2-pristine).
- CI's Job A runs build_release without -F or -L (build.yml:321). Both files are absent from the cached package.
- The four contrib/polyml-5.9.2-2/*/libpoly*.la files are also absent from the package. No script in isabelle-packaging-ci mentions .la files.
- So adding only obj/ and .conda-keep would still leave an exhaustive "只有" claim false.
- The same short list also appears in §2.3 (plan:150-153) and decision 12.1 (plan:413-415). That does no harm, because decision 12.1 lists what is kept, not what to remove. But three copies of one list will drift apart.

(2) The §7.9 citation is wrong.
- Plan:711-712 calls the cleanup of feature-created files the same kind as "§7.9's component packages cleaning up their registration with isabelle components -x".
- PACKAGING_DESIGN.md §7.9 (:876-882) never mentions components. It records the user-only patch ruling and says Isa-REPL's conda package would patch register_thy in its own install script, with heaps rebuilt.
- The components -u/-x convention lives in RELEASE_CHECKLIST.md §4 (:250-252). The plan itself cites it correctly elsewhere (plan:77, :170-172, :353-355).
- Decision 12.4 asks the CI plan to rewrite §7.9 (plan:419), so even a correct description would soon point at changed text.
- The citation comes from the round-2 judge's action "cite the §7.9 precedent (PACKAGING_DESIGN.md:876-882)" (REVIEW2:1426). The author cited §7.9 but described something §7.9 does not say. The §10 row for C9 (plan:672) claims the appendix was rewritten and does not flag this.

What I could not establish. I did not verify the claim that obj/ directories exist in the official win-64 bundle by experiment; it rests on pack.sh:125-130 and PACKAGING_DESIGN.md §3.6.

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C16/. Nothing in any repository was modified.

1. I listed /home/qiyuan/isa_release_proto/Isabelle2025-2_linux.tar.gz with `tar tzvf` into tarball_listing.txt (27125 entries) and compared its file set with `find` over ~/miniconda3/pkgs/isabelle-2025.2-0/isa. The result is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C16/tarball_vs_pkg_filesets.txt.
   - Only in the package: two .conda-keep files and the 64-bit heaps/log.
   - Only in the tarball: the x86_64_32 heaps, lib/browser_info.db, src/Tools/Find_Facts/lib/isabelle.db, and four polyml .la files.
   - The vscodium "Regular Expressions" line in that file is an artifact of my parsing a filename with spaces, not a real difference.
2. I computed the empty directories of the tarball from its listing. There are two, and they match the package's two .conda-keep files exactly. `grep -c /obj/` on the tarball listing gives 0.
3. I read pack.sh:103-139 and :284-324, PACKAGING_DESIGN.md:876-882 and its headings, RELEASE_CHECKLIST.md:250-268, and build.yml:313-321. I also read build_release.scala:491-545 and :905-925, plus components.scala:294, in contrib/Isabelle2025-2-pristine. That last file shows components -u writes $ISABELLE_HOME_USER/etc/components, which conda does not track. That is why RELEASE_CHECKLIST §4 is a real precedent for the appendix's analogy.
4. I grepped contrib/ for an Isa-REPL conda recipe and found none. Isa-Mini/conda/recipe.yaml:30-31 says "Isa_REPL, which we do not publish". The §7.9 Isa-REPL allowance was never used, and its register_thy patch now ships in qiyuan-dev-patches (plan:436-438).

Recommended fix: Two hand edits to Appendix A, plus one line in §10.

(a) Plan:704-706. Instead of an exhaustive list, state the checkable invariant that ruling 20 defines, and make the list explicitly non-exhaustive. Suggested shape: "Isabelle 的源码与官方发行版相同，etc/ISABELLE_ID 是官方 changeset（89701cf1768e），任何人都能核对；其余差别都在打包层面、不碰源码：pack.sh 的三个文件改动、Windows 的 bin/isabelle.bat、删去 VSCodium 的 obj/ 构建残留（Windows 路径长度）、给空目录放的 .conda-keep 标记，以及 CI 自己跑 build_release 带来的差别（CI 编的 64 位 Pure/HOL/Main heap 取代官方 heap；不带官方包的 lib/browser_info.db 与 Find_Facts 索引）。"
- The editor's relaxation of adding only obj/ and .conda-keep while keeping "只有" would still be false, because of the browser_info/Find_Facts databases.
- Optionally, add obj/ and .conda-keep to decision 12.1's kept list (plan:413-415) and to §2.3 (plan:150-153), so the three copies agree.

(b) Plan:711-712. Change "§7.9 组件包" to "RELEASE_CHECKLIST.md §4 的组件包（`isabelle components -x` 清理自己登记的 `$ISABELLE_HOME_USER/etc/components` 条目）". The sentence then becomes true, and the citation points at text decision 12.4 does not rewrite.
- If the author still wants the §7.9 link the round-2 judge asked for, state it the other way round: this exception replaces §7.9's never-used allowance for Isa-REPL's install script to patch register_thy, which now ships in qiyuan-dev-patches. That is consistent with decision 12.4's rewrite of §7.9.
- I do not recommend the editor's other option, "cite §7.9 for what it actually says": it cites a passage this plan makes obsolete.

(c) In §10's C9 row (plan:672), say that the round-2 instruction "cite the §7.9 precedent" was carried out in the form described in (b).

No owner question is needed. The appendix wording is delegated to the author (plan:692, ruling 17), and both pack.sh steps fit ruling 20's definition.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed, and wider than stated.

Besides the obj/ purge (pack.sh:122-139) and the .conda-keep markers (:284-324), the package also lacks the official tarball's lib/browser_info.db and src/Tools/Find_Facts/lib/isabelle.db (verified by the judge: present in the tarball, absent from pkgs/isabelle-2025.2-0) and four polyml .la files. Replacing 'only' (plan:704-706) with two more items would therefore still be false.

The §7.9 citation (plan:711-712) misdescribes PACKAGING_DESIGN.md:876-882, which decision 12.4 rewrites anyway.

Author, by hand:
- Appendix A item 2 states the checkable invariant from ruling 20 (sources identical, ISABELLE_ID official), then lists the packaging differences explicitly as non-exhaustive:
  - pack.sh's three file edits;
  - bin/isabelle.bat;
  - the obj/ purge;
  - the .conda-keep markers;
  - the differences from CI's own build_release run (its heaps; no browser_info/Find_Facts databases).
- Cite RELEASE_CHECKLIST.md §4 (`components -x`) instead of §7.9. Or state that this exception replaces §7.9's never-used Isa-REPL allowance.
- Record in §10's C9 row how the round-2 'cite §7.9' instruction was carried out.

### C17 [minor] Exit code 128 during the replay means the staging or temporary copy could not be written, not a corrupt patch, yet decision 4 reports it as exit 3 blaming a correct patch file

Section: Decision 4 (plan:259-261); decision 5 (plan:280-281); decision 6 (plan:292-293); §4 exit codes (plan:526-528)  ·  merged from: engine-E3

**Statement.** Decision 4 maps git's exit codes: 0 is success, 1 'does not fit', 128 'the patch file cannot be parsed, exit 3 naming the file', and any other value 'like 128' (plan:259-261). This copies the round-2 judge's rule, which was stated for check mode (REVIEW2:2630). Rev 3 no longer replays in check mode: both halves of the level computation really apply each patch to the copy (plan:292-293), and install replays in staging (plan:274).

In write mode git also returns 128 for 'unable to write file', and a child killed by a signal shows up as a negative returncode in Python. Measured with light's real locale.ML patch and the whitelist environment (review-ipc3/critic-engine/rc128/run.out):
- a read-only directory in the staging copy gives 'error: unable to write file … Permission denied', rc=128;
- a file-size limit kills git with SIGXFSZ and leaves a truncated 4096-byte staging file;
- a corrupt patch gives rc=128 from both --numstat and apply;
- a patch that does not fit gives rc=1.

Decision 3 already parses every patch file up front with --numstat --summary (plan:253-254), so a 128 during the replay can never be a parse error. As written, a full /tmp makes status, apply or a hook report a correct package file as corrupt (exit 3) and send the user to reinstall it. That contradicts decision 5's 'a write failure can only happen in staging (exit 1, tree unchanged)' (plan:280-281).

The `check` parameter is unused by decisions 5-7, and it invites the per-feature --check that round 2 showed never chains (REVIEW2:1007-1015).

**Editor.** Verified plan:259-261 and REVIEW2:2630. No overreach.

**Relaxation proposed by the editor.** Classify by phase, not by code alone.
- A parse error can be found only in the --numstat --summary pass: exit 3, naming the file.
- During the replay, 1 means 'does not fit this level'. Any other outcome means the scratch copy could not be written: exit 1 (exit 2 when git is missing), with git's message and the staging path, naming no patch file.

Drop `check` from git_apply.

**Defender: confirmed** (needs owner: False).

In short: rev 3 copied a rule that round 2 wrote for check mode (`git apply --check`, which only tests whether a patch fits and writes nothing) into a design that no longer uses check mode. Every claim that matters in C17 holds. I could not refute it.

What the plan says.
- Decision 4 (ISABELLE_PATCH_CONTROL_PLAN.md:258-261) defines `git_apply(workdir, patch_file, *, reverse=False, check=False)`. Its exit-code rule: 0 is success; 1 is "does not fit"; 128 means "the patch file cannot be parsed", and the caller exits 3 naming the file; any other value is treated like 128. §4 repeats "patch file cannot be parsed" in the exit-3 list (plan:526-528). The test list asks for "corrupt patch file: exit 3, named" (plan:469).
- The rule comes from the round-2 judge, who scoped it explicitly: "In check mode, 1 feeds the replay; 128 means the patch file cannot be parsed" (REVIEW2:2630). Rev 2 did compute levels with `--check` (PLAN.rev2.md:204-205, 220-221).
- Rev 3 dropped check mode. Both halves of the level test now really apply each patch to a copy before testing the next one (plan:290-293). Install replays in staging (plan:275, step 2). `--dry-run` is the same replay without the install steps (decision 7). So every `git_apply` call now writes to a scratch copy, and in write mode git's 128 has a second meaning.
- Decision 3 already reads every patch file up front with `git apply --numstat --summary` (plan:253-254). Decision 2 puts that read before any replay (the symlink check happens "when reading the feature directory, before the replay"). A parse error therefore surfaces in that first pass and never during the replay.
- Decision 5 says a write failure can only happen in staging and gives exit 1 with the tree unchanged (plan:280-281). That follows the judge's second line (REVIEW2:2631). For the same event, a failed write in staging, decision 4 gives exit 3 and blames the patch file. The plan contradicts itself.

What I measured (git 2.43.0, the whitelist environment from decision 4, umask 022, light's real locale.ML patch).
Files: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C17/e1.out, e2.out, e3.out, e4.out.
- Write failures in the scratch copy, all with a correct patch:
  - Disk full, simulated with an LD_PRELOAD shim that makes `write` fail with ENOSPC: rc=128, "failed to write to … No space left on device". A truncated staging file is left behind (8192 or 0 bytes).
  - File-size limit, under Python's default `restore_signals`: git is killed by SIGXFSZ, so Python sees returncode -25. The staging file is truncated to 4096 bytes.
  - File-size limit with SIGXFSZ ignored: rc=128, "File too large".
  - A read-only parent directory: rc=128, "unable to write file … Permission denied".
- Every way a patch can fail to fit gives rc=1:
  - forward on an already-patched file, and reverse on the base;
  - a modification patch whose target is missing;
  - a creation patch when the file already exists, with the same or different content;
  - a creation patch reversed when the file is missing, or when it has other content.
- A corrupt patch gives 128 already in the `--numstat --summary` pass, even inside an enclosing git repository.

So during the replay, an exit code of 1 always meant "does not fit", and every other result I produced was a failure to write. Under the plan as written, a full disk, a quota or a size limit while running status, apply or a hook is reported as exit 3 with a correct package file named as the cause. Severity minor is right. The plan's rule does stop before anything is installed, so the tree stays safe; what is wrong is the diagnosis.

The unused `check` parameter is confirmed too. Searching the plan, `check=` and `[--check]` appear only in the signature (plan:258-259). Decisions 5-8 never call check mode, and neither does make-patches gate (c): today it really applies the patch (tools/make-patches:63-69), and decision 16.1 only replaces that with `git_apply`/`install_files`. The (b2) round-trip script calls the CLI (decision 17). The flag keeps a wrong implementation one keyword away: testing each feature with `--check` against an unchanged copy, which round 2 showed does not chain (REVIEW2:1013).

Where I refined the challenge.
1. Its line "send the user to reinstall it" is an inference, not plan text. §4 and decision 9 give no fix-it message for an unparseable patch file. The substance still holds: the diagnosis names the wrong cause.
2. "A 128 during the replay can never be a parse error" is literally true. But a 128 during the replay can still be a defect in the patch file. A path containing `.git` or `..` passes `--numstat` (rc=0) and fails apply with rc=128 "invalid path" (e2.out). Neither can reach a released package: git refuses to index such paths (gitpath test: "Invalid path", rc=128), so make-patches cannot produce them, and decision 2's realpath check already refuses `..` paths. The relaxation's wording "any other outcome means the scratch copy could not be written" is therefore slightly too strong. A message that quotes git's own output, without the tool asserting a cause, is accurate in every case.
3. The rule "1 means does not fit" relies on the tool making the copies itself. A copy git cannot read also gives rc=1 (e3.out: mode 000 and an unsearchable directory). Decision 5 step 1 has the tool create the copies in its own directory, so this cannot happen in practice. Worth one clause in the plan.
4. Related observation, outside C17 proper. Inside an enclosing git work tree without `GIT_CEILING_DIRECTORIES`, `git apply --numstat --summary` on a good patch prints nothing and returns 0 (e4.out). The feature would then look as if it touches no files. Decision 4 says "all patch operations go through one function", but that function's signature has no slot for `--numstat`, and its workdir is "always staging or temp". So the plan never says the first pass runs with the same isolation. The fix above relies on that pass being the parse check, so it must state this.

On the editor's relaxation. Classifying by phase is the right shape: the meaning of an exit code belongs to the phase that produced it. Two changes to it: name the patch file being replayed as context instead of naming none, and quote git's message as-is. Exit 1 for a write failure is consistent with decision 5. Exit 2 (environment) would be defensible too, but would need decision 5 changed to match; the author can decide that under §0 item 17. Dropping `check` is right.

Experiment: All experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C17/. Inputs are copies of light's real patches and the base locale.ML, taken from the critic-engine/real scratch directory.
- gitapply_lib.py implements the plan's git_apply: whitelist environment, `-c core.autocrlf=false`, `core.attributesFile=/dev/null`, ceiling, umask 022.
- e1.py / e1.out, write mode on a scratch copy:
  - write failures: ENOSPC via shim/enospc.so gives rc=128 and a truncated file; RLIMIT_FSIZE gives rc=-25 (signal) and a truncated file; EFBIG with SIGXFSZ ignored gives rc=128; a read-only directory gives rc=128;
  - all 8 does-not-fit cases give rc=1 (forward or reverse mismatch, missing target, creation patch on an existing file with the same or other content, reversed creation patch on a missing file or other content);
  - a mode mismatch gives only a warning, rc=0.
- e2.py / e2.out: `.git`-component and `..` paths pass numstat (rc=0) but apply gives rc=128 "invalid path"; a binary patch without a full index line gives numstat 0, apply 1.
- e3.py / e3.out: an unreadable scratch copy or an unsearchable directory gives rc=1.
- e4.sh / e4.out: numstat inside an enclosing repo without a ceiling: good patch prints nothing, rc=0; corrupt patch rc=128; with a ceiling it lists the target.
- gitpath test: `git update-index` refuses `src/.git/x` and `src/../x` ("Invalid path", rc=128).
- Read-only checks: the plan at :253-254, :258-261, :275, :280-281, :290-293, :464, :469, :526-528; PLAN.rev2.md:204-205, :220-221; REVIEW2:2630-2631, :1013; tools/make-patches:63-69.

Recommended fix: Classify git's exit code by phase, in four edits.

(1) Decision 4 (plan:258-261):
- Drop `check`. The signature becomes `git_apply(workdir, patch_file, *, reverse=False)`, and every call writes to the copy.
- Replace the exit-code parenthetical with: 0 is success. 1 is "does not fit" and feeds the level computation; this is sound because the tool creates every copy itself, in its own directory, so git can always read it. Any other result, including a negative value for a child killed by a signal, means git could not finish the replay on the copy. In practice that is a write failure: disk full, quota, file-size limit. Stop and install nothing. Print git's output verbatim, the copy's path and the patch file being replayed, without saying the patch file is broken. Exit 1, as decision 5 already says (plan:280-281).
- Build one private runner, for example `_git(workdir, *args)`, that constructs the whitelist environment and ceiling. Both `git_apply` and decision 3's target listing call it, so the isolation is built into the code rather than left to each caller.

(2) Decision 3 (plan:253-254):
- The `--numstat --summary` pass is the only parse check. A non-zero exit there gives exit 3, naming the patch file.
- The pass runs through the same runner, with a temporary directory as its working directory. In an enclosing repository without the ceiling it prints nothing and returns 0 (e4.out).

(3) §4 (plan:526-528):
- The exit-3 item becomes "a patch file cannot be parsed (when the feature directories are read)".
- The exit-1 list gains "git could not write the scratch copy during the replay".

(4) Decision 15 (plan:464): the test "write failure in staging leaves the tree unchanged" also asserts exit 1 and git's own message, and that no patch file is called corrupt.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed.
- Rev 3 copied a check-mode rule (REVIEW2:2630) into a write-mode replay.
- Measured: ENOSPC, a read-only directory and EFBIG each give rc=128; RLIMIT_FSIZE gives rc=-25 with a truncated file; every does-not-fit case gives rc=1 (defender-C17/e1.out).
- The rule contradicts decision 5's exit 1 for a write failure in staging (plan:280-281).

Author, together with C2's primitive:
- Drop `check` from git_apply.
- Decision 3's --numstat --summary pass, run through the primitive in a temporary directory the tool created, is the only parse check. A non-zero result there is exit 3, naming the file.
- During the replay, 1 means 'does not fit'. This is sound because the tool creates every copy itself, in its own directory.
- Any other result during the replay, including a negative signal code, means git could not finish the replay on the copy. In that case:
  - install nothing;
  - print git's output verbatim, the copy's path and the patch file being replayed, without calling the patch file broken;
  - exit 1.
- Update §4's exit-1 and exit-3 lists (plan:526-528).
- Decision 15's write-failure case (plan:464) asserts exit 1 and that no patch file is called corrupt.

### C18 [minor] The level definition uses a feature number as an index into the list of features that touch the file, so decisions 6 and 7, read literally, replay patches that do not exist

Section: Decision 6 (plan:291-294); decision 7 (plan:317, :321)  ·  merged from: engine-E4, consistency-CONS-12

**Statement.** Decision 6 defines t1 < … < tm as the feature numbers that touch p, and a level j ∈ {0, t1, …, tm}, which is a feature number (plan:291). It then reverses 't_j, …, t_1' and forward-applies 't_{j+1}, …, t_m' (plan:292-293), using j as an index into the t-list.

Example: syntax_phases.ML is touched by light (number 3) and dev (number 4), so t1=3 and t2=4. At level j=4 the text asks to reverse t_4, t_3, t_2, t_1, and t_4 and t_3 do not exist.

Decision 7 repeats it: forward-apply 't_i (j < i ≤ T)' (plan:317) and reverse 't_i (T < i ≤ j)' (plan:321). The display rule needs j to be a feature number ('levels ≥ k', plan:300), so no single reading of the symbols makes all three rules consistent.

This is the very definition that round 2's C6 rewrote because its literal reading was wrong (REVIEW2:1007-1015).

**Editor.** Verified the text. Minor because the intent is recoverable, but this is the plan's central definition.

**Relaxation proposed by the editor.** State it over sets. p is at level L (L = 0 or the number of a feature touching p) iff:
- on one copy, reversing in descending chain order p's patches whose feature number is ≤ L succeeds, each really applied before the next; and
- on another copy, forward-applying in ascending order those whose feature number is > L succeeds likewise.

Decision 7 then reads: apply forward-applies, in chain order, p's patches whose feature number lies in (L, T]; unapply reverses, in reverse chain order, those in (T, L].

**Defender: confirmed** (needs owner: False).

I tried to refute C18 and could not. The severity "minor" is right.

What the text says.
- Decision 6 defines t1 < … < tm as the feature numbers that touch p, and puts the level j in {0, t1, …, tm}, so j is a feature number (plan:291). The same sentence then uses j as a position in the t-list: reverse "t_j, …, t_1" and forward-apply "t_{j+1}, …, t_m" (plan:292-293).
- Decision 7 sets T to a feature number: n, or F's number (plan:316), or F's number minus one (plan:320). It then bounds the subscript i by j and T: "t_i (j < i ≤ T)" (plan:317) and "t_i (T < i ≤ j)" (plan:321).
- The display rule compares a file's level with F's feature number k (plan:300), so it needs levels to be feature numbers.

Attempted refutations, all failed.
(a) Index reading (j in 0..m is a position in the t-list). This is how rev 1's judge wrote it (REVIEW1:380-382, :399) and how rev 2 wrote it (rev2:219, with display "层级 ≥ F 的位置", the position of F, at rev2:225). Under that reading the sets in decision 6 are right, but plan:291's "j ∈ {0, t1, …, tm}", the display rule at plan:300 and the feature-number T at plan:316/:320 are wrong. Concretely: `apply --feature light_locale` (T=3) on a tree with features 1..2 would apply t_1 and t_2 to syntax_phases.ML, that is light AND dev_patches, overshooting F. My prototype shows this.
(b) Feature-number reading. On the real chain (expose=1, future=2, light=3, dev=4), syntax_phases.ML has t1=3, t2=4, m=2. The candidates j=3 and j=4 name t_3 and t_4, which do not exist. The only candidate that can be evaluated is j=0, and it fails on the fully applied tree. So a literal implementation either crashes, or calls the file CONFLICT and apply stops. That is rev 1's false CONFLICT again.
(c) "By value" reading (t_x means the feature numbered x; features that do not touch p are skipped). Then "t_{j+1}, …, t_m" ends at feature m=2, so at j=0 the forward set is empty instead of {3, 4}. A reading that works has to take the subscript j as a value but the subscripts 1 and m as positions. So no single reading works, as the challenge says.

Context. Rev 3 introduced this defect. To make the display rule (≥ k) and the feature-number T work, it changed the domain of j to feature numbers, but kept the index formulas inherited from REVIEW1:399 and rev2:219-220. The §10 row for C6 (plan:669) is right that both halves are now sequential, but nothing records the domain change. The glossary entry at plan:26 ("the content equals what the first j features give") already says what was meant, and it agrees with the editor's set relaxation, because features that do not touch p do not change p.

The editor's relaxation is correct. I ran it on the real patches (levels.out): every one of the 40 files has exactly one level on the full tree, and syntax_phases.ML gets level 0, 3 and 4 on the trees with features 1..2, 1..3 and 1..4.

One gap remains that the relaxation does not close. Under it, levels are only the numbers {0, t1..tm}, but T is a global feature number. So decision 7's selection test "层级 < T 的文件" ("files whose level is below T", plan:317) and the phrase "移到 T" ("move it to T") are wrong for every file that the top feature does not touch. On the fully applied real tree, `apply` with T=n=4 selects 32 of the 40 files, and all 32 have an empty patch sequence. Decision 5 would then copy them and `os.replace` them unchanged (plan:273-276). `--dry-run` would list them as moving, for example ml_name_space.ML "from level 1 to level 4" (plan:323). The heap hint (plan:324) can fire on every idempotent post-link. And plan:325's "部分文件已在 T" ("some files are already at T") cannot hold, because p never reaches a level that is not in {0, t1..tm}. The relaxation also needs one clause saying which files move.

Experiment: Directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C18/

Setup: the real per-feature patches, copied from round 2's review-ipc2/critic-engine/real (base tree plus features.d for expose_foreign, future_assign_interrupt, light_locale and dev_patches, numbered 1-4). git 2.43.0, run with a whitelist environment: GIT_DIR=/nonexistent, no system or global config, core.attributesFile=/dev/null.

Script: levels.py. Output: levels.out.

Results:
- syntax_phases.ML has touching features [3, 4], so m=2.
  - Literal rev 3 reading: on all three trees (features 1..2, 1..3, 1..4), the candidates j=3 and j=4 are "t_3 undefined (m=2)" and "t_4 undefined (m=2)". j=0 passes only on the 1..2 tree, so on the 1..3 and 1..4 trees the file gets no level.
  - Set reading (editor's relaxation): levels [0], [3] and [4] on those three trees.
- Full tree, set reading: 40 files, none with zero or several levels.
- Index reading of decision 7 with T = F's number: `apply --feature light_locale` (T=3) on the 1..2 tree applies features [3, 4] to syntax_phases.ML. The set reading applies [3].
- Decision 7's selection test "level < T" on the full tree, with T=n=4: 32 files are selected, and all 32 have an empty patch sequence (for example ml_name_space.ML at level 1, future.ML at level 2, lifting_setup.ML at level 3).

Recommended fix: Smallest fix, all hand edits to the plan text (no design change):

1. plan:291-293. Replace the formulas with sets, in the editor's wording: "p 处于层级 L（L = 0 或某个改 p 的 feature 的编号）iff 在一份副本上按链序倒序逐个反打 p 的编号 ≤ L 的 patch 文件、每成功一个就真的反打到副本上，全部成功；且在另一份副本上按链序逐个正打编号 > L 的、同样真打，全部成功。" ("p is at level L, where L is 0 or the number of a feature that changes p, iff two replays succeed. On one copy, reverse p's patch files with number ≤ L one by one in reverse chain order, really reversing each before the next. On another copy, apply those with number > L one by one in chain order, really applying each.") Keep the sentence about the sequential reading of both halves.

2. plan:316-321. Define a per-file target level instead of using T directly. T_p is the largest element of {0, t1, …, tm} that is ≤ T, where T is the global feature number decision 7 already defines.
   - apply moves p iff L < T_p, forward-applying in chain order p's patch files whose number lies in (L, T].
   - unapply moves p iff L > T_p, reversing in reverse chain order those in (T, L].
   - Files with L = T_p are not touched.
   (Equivalently: a file moves only when that set of patch files is non-empty.)

3. plan:27 and plan:325. The target level is per file. Change "部分文件已在 T" ("some files are already at T") to "已在各自的目标层级" ("already at their own target levels").

4. Decision 15 (plan:461-462). Make the stacked-context pair sit at feature numbers that differ from their positions in the file's t-list, as on the real chain (3 and 4 of n=4). Add one assertion: `apply --dry-run` on a fully applied tree lists no files.

5. §10 row C6 (plan:669). Note that rev 3 changed the domain of j to feature numbers.

**Judge: confirmed → author_decides_then_rereview.** Confirmed. No single reading of the symbols makes plan:291-293, :300, :317 and :321 all consistent (defender-C18/levels.out).

The defender adds a real defect: decision 7's test 'level < T' selects every file the target feature does not touch. On the fully applied real tree that is 32 of 40 files, each with an empty patch sequence. The consequences:
- --dry-run lists them as moving;
- the idempotent post-link would os.replace them;
- the heap notice may fire, against plan:361-362's 'writes nothing'.

Author:
- Decision 6: define levels over sets. p is at level L (L = 0 or the number of a feature touching p) iff:
  - reversing, in descending chain order, p's patch files numbered ≤ L succeeds sequentially on one copy; and
  - applying, in ascending order, those numbered > L succeeds sequentially on another copy.
- Decision 7:
  - per-file target T_p = the largest element of {0, t1..tm} that is ≤ T;
  - apply moves p only when L < T_p, applying the patches in (L, T];
  - unapply moves p only when L > T_p, reversing those in (T, L];
  - files with L = T_p are untouched.
- Change plan:27 and plan:325 to 'each file's own target level'.
- Decision 15: put the stacked-context pair at feature numbers that differ from their positions in the file's list, and add 'apply --dry-run on a fully applied tree lists no files'.
- Note the domain change in §10's C6 row.

### C19 [minor] The write path is exported in pieces (git_apply plus an undefined install_files), so 'one path' and 'git only in the staging directory' are left for callers to remember; the directory interface writes the shared staging path without the lock; decisions 8 and 17 contradict each other

Section: Decision 8 (plan:329-332); decision 16.1 (plan:490); decision 17 (plan:504); decision 4 (plan:258-259); decision 5 (plan:273-278, :286-287); ruling 24 (plan:94)  ·  merged from: engine-E5, consistency-CONS-13

**Statement.** Ruling 24 as recorded says that status, --dry-run, apply, unapply and the directory interface share one path, and that git only ever runs in the staging directory (plan:94). Decision 4 states the workdir rule as a promise about callers (plan:258-259).

Decision 8 then exports git_apply and install_files as the API that make-patches gate (c) and the (b2) script compose themselves (plan:331-332, :490). install_files is defined nowhere else: plan:331 and :490 are its only mentions.

Gate (c) today runs `patch -p1 -F0` in the archive tree (tools/make-patches:63-69, :179-183). Its natural port, `git_apply(work, p)`, runs git in a tree, which the ruling forbids. Gate (c) would then test a composition other than the shipped apply-to/unapply-from (no level replay, no staging), which is round 1 C17's concern.

Decision 8 says (b2) imports these functions (plan:332), while decision 17 runs `python -m isabelle_patch_control … apply` (plan:504). The two contradict each other.

Three more places rely on care instead of shape:
- The directory interface does not lock (plan:330), yet it writes the same fixed path <dir>.staging that apply and unapply clear under the lock (plan:277-278). An `apply-to` on $PREFIX/isa running while a hook runs can delete the hook's staging files.
- <tree>.staging is formed from the unresolved tree path, while the symlink check resolves realpath(tree) (plan:234). A symlinked --isabelle-home therefore puts staging on the link's filesystem, and os.replace fails with EXDEV.
- Decision 5 step (2) replays again in staging (plan:274) after decision 6 has already replayed in a temporary directory (plan:294). 'status predicts exactly the bytes that are installed' (plan:287) then rests on determinism instead of construction, and costs a second replay: on the real chain, 42 extra git calls on top of 126. A single replay gave exact round trips on the real chain (review-ipc3/critic-engine/ipc.py on real/: 'tip compare fail=0', then 'SAME_AS_BASE').

**Editor.** Verified install_files has no definition, and that plan:332 and :504 conflict. No overreach.

**Relaxation proposed by the editor.** Export only the operations the CLI runs: engine.apply_to/unapply_from, and the chain-level apply/unapply. Gate (c) calls exactly those; (b2) uses `python -m`, as decision 17 already says (fix decision 8).

Make the git primitive private and give it content plus a relative path instead of a workdir: it creates its own directory under the staging root, or under mkdtemp for status. Then git cannot be pointed at a tree at all.

Run the level replay once, in the staging root for writing commands, and install the snapshot at T from that same replay, so the predicted bytes are the installed bytes by construction.

Derive staging as realpath(tree) + '.staging', and give the directory interface either a per-run mkdtemp(dir=parent) staging or the same lock.

**Defender: confirmed** (needs owner: False).

I tried to refute each part of C19. Every factual claim holds. One supporting argument carries less weight than the challenge gives it. Severity minor, as the editor rated it.

1. install_files has no definition. CONFIRMED. A grep of the plan finds it only at plan:331 and plan:490. Decision 5 describes four steps (plan:273-276) but never says which of them install_files does, what arguments it takes, or how it reports failure.

2. The primitive is exported, and "git only in staging" is a promise about callers rather than a property of the code. CONFIRMED.
- git_apply takes any workdir. The rule appears only as a parenthesis: "workdir (always the staging directory or status's temporary directory)" (plan:258-259), restated as prose at plan:269 and plan:654.
- Decision 8 then exports git_apply and install_files as the shared base layer, for make-patches to compose (plan:331-332, :490).
- Ruling 24 says git only ever runs in the staging directory (plan:94). Nothing in the code shape enforces that.

3. Gate (c) would test a composition other than the one users run. CONFIRMED, with one softening.
- The migration plan requires gate (c) to go "经补丁工具的目录接口", that is, through the directory interface (ISABELLE_GIT_MIGRATION_PLAN.md:392, :433-434).
- The round-1 judge for C17 ordered that "gate (c) runs the code users run" (REVIEW1:1577-1581).
- Rev 3's glossary now defines the directory interface as subcommands only (plan:31). Gate (c), however, imports the two lower functions (plan:490). Nothing makes it go through level replay or staging.
- The softening: running git apply in gate (c)'s throwaway archive would be harmless in practice. make-patches already runs `git add` with the archive as GIT_WORK_TREE (common.py:155-162). The archive sits in a TemporaryDirectory (make-patches:175), and git_apply's ceiling setting isolates it. So the clash with ruling 24 is only in the letter. The real defect is the exported shape, which leaves the composition up to each caller.

4. Decision 8 and decision 17 contradict each other. CONFIRMED.
- Decision 8 says the (b2) script imports git_apply and install_files (plan:332).
- Decision 17 runs copy A through `python -m isabelle_patch_control … apply` and copy B through `patch -p1 -F0` (plan:504-506). Neither copy uses either function.
- This is a round-2 judge action that was only half followed. The C10 judge ordered "Fix plan:221-222 and :314 ('(b2) 同')" (REVIEW2:1567).
  - Rev 2's :314 text, decision 15.1's "(b2) 同", is gone: plan:490 no longer mentions (b2).
  - Rev 2's :221-222 sentence (rev2 plan:252-255) survives unchanged at plan:332.
  - §10's C10 row claims the item is done and does not mention this.

5. The directory interface writes the shared staging path without the lock. CONFIRMED.
- Decision 5 clears `<tree>.staging` "在锁内" (under the lock) at the start of every writing run (plan:277-278).
- Decision 8 gives the directory interface the same path, `<dir>.staging`, and says "不加锁" (no lock) (plan:330).
- This also departs from the round-2 C2 judge action "Clear it under the lock at the start of every writing run" (REVIEW2:574), and from ruling 17's "工具运行时对树加锁" (the tool locks the tree when it runs, plan:67). Neither departure is stated.
- My simulation (race/race.py): A holds LOCK_EX and has staged src/a.ML; then an unlocked apply-to clears the staging directory. A's os.replace fails with FileNotFoundError, and the tree file stays old.
- So the damage is a spurious failure, not corruption. The invariant "only the lock holder touches the fixed staging path" still depends on care, not on shape.

6. A symlinked tree path puts staging on another filesystem. CONFIRMED.
- The plan explicitly expects the tree path itself to be a symlink: its check compares against realpath(tree) (plan:234).
- But staging is formed as `<tree>.staging` from the unresolved path (plan:277).
- Measured: with `link -> /proc/sys`, os.replace(link.staging/f, link/f) fails with errno 18 EXDEV ("Invalid cross-device link").
- Reachability: the hooks pass the real directory $PREFIX/isa, so they never hit this. Only an explicit symlinked `--isabelle-home` together with `--features-dir`, or `apply-to <link>`, reaches it. The tree stays unchanged; the plan's claim that staging is "same filesystem" (plan:28, :277) is simply not true by construction.

7. The level replay runs twice. CONFIRMED.
- Decision 6 replays each file to find its level, in a temporary directory (plan:291-294).
- Decision 5 then copies the tree file again and replays a second time, "按决定 7 算出的顺序" (in the order decision 7 computed, plan:273-274).
- Decision 7's "--dry-run：同一次重放" (the same replay, skipping steps (3) and (4)) shows that this second replay is part of the path.
- Measured on the real four-feature chain, applying from base:
  - single replay, installing the snapshot at the target level T: 126 git calls;
  - the plan's literal double replay: 168 calls, so 42 extra;
  - predicted bytes differed from installed bytes 0 times, and both variants give identical trees;
  - unapply returns the tree to base exactly in both variants.
- So nothing is wrong today. The point is elegance: "status predicts exactly the installed bytes" (plan:287) holds only because git apply is deterministic, not by construction. Ruling 24's "先重放、再决定装不装" (first replay, then decide whether to install, plan:94) most naturally means one replay whose result is installed or not. The cost on Linux is small (0.22 s versus 0.23 s here); on Windows each git call costs more.

The editor's relaxation, judged on its merits:
- Export only the operations the CLI runs; gate (c) calls apply_to and unapply_from; (b2) uses `python -m`. Sound. It matches migration §5.1(c) and the round-1 C17 judge action. One thing must be added: the imported functions raise an exception or return a result instead of calling sys.exit. The round-1 C17 judge already asked for this (REVIEW1:1577-1580); rev 3 states it only for git_apply's return code (plan:259-261).
- Make git_apply private, and let the engine create its working directory itself. Sound, and this is the part that makes "git only in staging" impossible to violate. The further step to a content-plus-relative-path signature is cleaner still but optional.
- Run one replay, in the staging root for writing commands, and install the snapshot at T from it. Sound and consistent with ruling 24 (git still runs only in staging; status still uses mkdtemp). It also handles decision 7's rule for files that sit on several levels, because the replay from each fitting level already yields that level's snapshot at T (the prototype does exactly this).
- Staging at realpath(tree) + ".staging", plus either a per-run mkdtemp or the lock for the directory interface. Sound. I prefer the per-run mkdtemp next to realpath(dir): the directory interface's target may have no etc/ISABELLE_ID to lock, and the fixed path then stays reserved for whoever holds the lock.

None of this touches an owner ruling.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C19/. git 2.43.0 throughout.

(1) Single replay versus the plan's double replay on the real chain.
- real/ is a copy of the critic-engine's real chain: the expose_foreign, future_assign_interrupt, light_locale and dev_patches feature directories over a 41-file base.
- ipc_single.py is a copy of review-ipc3/critic-engine/ipc.py. It installs the snapshot at T taken from the level replay.
- ipc_double.py wraps it to do decision 5 literally: after the level computation, copy tree/p into <tree>.staging and replay t_{j+1..T} there with git_apply.
- tip/ holds the 40 paths of the Isabelle2025-2/dev_patches branch, extracted with read-only `git show`.
- Single replay, apply: 126 git calls. Compared with tip/, the only difference is etc/options:193 (ML_system_64 true versus false). That is pack.sh's edit, present in the conda-derived base, so it is expected. Unapply: 127 calls, and `diff -r` against base shows no difference.
- Double replay, apply: 168 calls. That is 42 extra, all of them second replays in staging. Predicted bytes differed from installed bytes 0 times, and the tree equals the single-replay tree. Unapply: 169 calls, identical to base.

(2) exdev/: a symlink `link -> /proc/sys`, with staging formed from the unresolved path as `link.staging`. os.replace(link.staging/f, link/f) raised OSError errno 18, "Invalid cross-device link". realpath(link) + '.staging' would have been /proc/sys.staging.

(3) race/race.py: process A takes LOCK_EX on etc/ISABELLE_ID, clears the staging directory under the lock, and stages src/a.ML. Then an unlocked apply-to clears <dir>.staging, which decision 8 permits. A's os.replace then fails with FileNotFoundError, and the tree file stays "old".

(4) Read-only checks:
- grep of the plan: install_files appears only at :331 and :490.
- plan :28, :67, :94, :234, :258-261, :269, :273-278, :286-287, :291-294, :329-332, :490, :496, :502-507, :654.
- rev2 plan :252-255 and :347.
- REVIEW2 :574 (the C2 judge: clear staging under the lock) and :1567 (the C10 judge: fix rev 2's plan:221-222 and :314).
- REVIEW1 :1577-1581 (the C17 judge).
- migration plan :392 and :433-434.
- tools/make-patches :63-69 and :175-186; tools/common.py :155-162 (tree_hash_of_dir already runs git with the archive as its work tree).

Nothing outside the defender-C19 directory was written. No git command that changes state was run on any repository.

Recommended fix: Smallest fix, all within the author's own design decisions:

1. Decision 8 (plan:331-332):
- Replace the export sentence. The engine's public API is exactly what the CLI runs: `engine.apply_to(dir, feature_dir)` and `engine.unapply_from(dir, feature_dir)`, plus the chain-level apply, unapply and status.
- These functions return a result or raise a `PatchFailed`-style exception, never sys.exit. The CLI maps that to exit 1 or 3; make-patches maps it to Refused.
- git_apply becomes private to the engine. Delete install_files from the text, or define it as a private helper for decision 5's steps (3)-(4).
- Delete "(b2) 脚本直接 import 这两个函数" (the (b2) script imports these two functions). (b2) uses `python -m`, as decision 17 already says.

2. Decision 16.1 (plan:490): gate (c) calls apply_to and then unapply_from on the archive. This is migration §5.1(c)'s "经目录接口" (through the directory interface), and it means gate (c) runs the code users run.

3. Decision 4 (plan:258-259): git_apply takes no directory chosen by its caller. Only the engine's replay helper calls it, and that helper creates its own working directory: under the staging root for writing commands, under mkdtemp for status and --dry-run. Optionally, give it content plus a relative path in, and content out.

4. Decisions 5 to 7 (plan:273-276, :286-287, :294):
- The level replay runs once. For writing commands it runs under the staging root.
- Steps (3)-(4) install the snapshot at T from that same replay; with several fitting levels, the snapshots are compared as decision 7 says.
- Delete the second copy-and-replay from steps (1)-(2). "--dry-run predicts the installed bytes" then holds by construction, and the real chain saves 42 of 168 git calls.

5. Decision 5 (plan:277) and decision 8 (plan:330):
- Staging is realpath(tree) + ".staging", used only while the lock is held.
- The directory interface stages in a per-run mkdtemp next to realpath(dir), or else takes the same lock. The plan should state either choice as a deliberate exception to ruling 17's "the tool locks the tree".

6. §10: record that the round-2 C10 judge action on rev 2's plan:221-222 and the C2 judge's "clear it under the lock" for the directory interface are now honoured.

**Judge: confirmed → author_decides_then_rereview.** Confirmed:
- install_files is used at plan:331 and :490 and defined nowhere;
- plan:332 contradicts decision 17 (plan:504), a half-followed round-2 C10 action (REVIEW2:1567);
- the unlocked directory interface can delete a locked run's staging (defender-C19/race);
- a symlinked tree path gives EXDEV (exdev/);
- the double replay costs 42 extra git calls of 168 on the real chain and gains nothing.

Author:
- Decision 8: the public API is exactly what the CLI runs: apply_to/unapply_from and the chain-level apply/unapply/status. These return a result or raise, and never call sys.exit. git_apply becomes private. Delete or privately define install_files. Delete plan:332's (b2) sentence.
- Decision 16.1: gate (c) calls apply_to then unapply_from on the archive (migration §5.1(c); REVIEW1:1577-1581).
- Decisions 4-7: the replay helper creates its own working directory (C2). The level replay runs once, under the staging root for writing commands, and steps (3)-(4) install the snapshot at T from that same replay.
- Decisions 5 and 8: staging = realpath(tree) + '.staging', used only under the lock. The directory interface stages in a per-run mkdtemp next to realpath(dir); state this as a deliberate exception to 'the tool locks the tree'.
- Record the round-2 C2 and C10 actions in §10.

### C20 [minor] No acceptance item checks bytes: the round-2 action 'the Windows leg compares file bytes after apply and after unapply' was dropped without saying so, and package-cache invariance is asserted nowhere on real conda

Section: Decision 15 (plan:465, :467-468, :485-486); §6 (plan:588-600); §10 row C1 (plan:664)  ·  merged from: engine-E6, consistency-CONS-13, landing-L10

**Statement.** Among its C1 changes, round 2's judge required: 'The Windows leg compares file bytes after apply and after unapply' (REVIEW2:443). §10's C1 row (plan:664) lists the other C1 changes but not this one. Neither decision 15's Windows checks (plan:485-486) nor §6 (plan:588-599) compares bytes, and §6 leaves hostile environments to pytest (plan:600).

The pytest hostile case is relative: hostile result == clean result (plan:467). On win-64 the clean run also uses PortableGit, whose system config sets core.autocrlf=true (plan:176-177). If GIT_CONFIG_NOSYSTEM or the -c override failed on Git for Windows, both runs would write CRLF and the test would still pass. The channel has already pulled a win-64 package over a CRLF etc/settings (RELEASE_CHECKLIST.md:180).

More generally, §6 (b) 'reversed cleanly' and (c) 'status unchanged' (plan:591-592) name no bytes. status replays the tree against itself, so a CRLF or mode regression still reads 'all applied'.

The package-cache invariance that §2.3 relies on (hard links, plan:168-169) is simulated only in pytest (plan:465). A toy hook that wrote in place changed the shared inode: pkgs/base-1-0/isa/src/f.ML became 'patched' (inode 8539344, link count 2), and `--force-reinstall` then 'restored' the patched bytes (review-ipc3/critic-landing/rollback/). The rename-based hook in rollback2/ left the cache at 'orig'. Only a cache assertion tells the two apart.

**Editor.** The author may deviate from a judge action, but must say so; §10 does not. On Linux the whitelist gives 0 CR bytes under hostile settings (critic-engine/hostile/run.out); nothing measures this on Windows.

**Relaxation proposed by the editor.** Add an absolute byte oracle on every leg, not only win-64:
- after apply, every file outside etc/ equals `git show <tip tag>:<path>`, and etc/options equals it plus pack.sh's ML_system_64 edit (or every leg equals the linux-64 leg's bytes);
- after unapply, every tracked file matches the sha256 in conda-meta/isabelle-*.json's paths_data, and the created files are absent;
- a sorted mode listing is compared as well;
- the package-cache copies of every file the chain touches still have the package's sha256.

**Defender: partially_confirmed** (needs owner: False).

CONFIRMED (the core).
1. The round-2 judge action was dropped, and the plan does not say so. Round 2 required "The Windows leg compares file bytes after apply and after unapply" in three places: the challenge (REVIEW2:337), the defender's fix 5 (:424) and the judge's change list (:443). In rev 3:
- §10's C1 row (plan:664) lists the whitelist, the -c flags, the ceiling, the .git refusal, §2.4 and the pytest hostile case, but not this action.
- Decision 15's Windows checks (plan:485-486) cover git.exe, the ceiling, longpaths, the lock and os.replace. None of them compares bytes.
- §6 (a)-(j) (plan:588-599) assert status words and conda output only, and plan:600 sends hostile environments to pytest.
- Nothing records a deviation. Ruling 17 lets the author decide test matters, but the deviation still had to be stated.

2. No CI leg has a check that is independent of the code under test. status and apply share one replay path by design (plan:286-287), so a byte error that git_apply makes consistently is invisible to status. Round 2 measured that `-R --check` passes on CRLF output (REVIEW2:318). The only absolute check is (b2), which runs locally on Linux with the owner's git and is excluded from CI (plan:501-507). The pytest hostile case only compares against the clean run (plan:467).

3. New evidence: a Windows-only route that no isolation flag can stop. Every leg checks out each feature repository and builds the packages there (plan:398-400). Neither light_locale nor the tool repository has a .gitattributes file. The channel's own repository documents that Git for Windows checks out with core.autocrlf=true (isabelle-packaging-ci/.gitattributes:1-6, .github/scripts/nunchaku-pins.sh:34-36), and its history records a pulled CRLF package (RELEASE_CHECKLIST.md:47-50, :180). My run used the plan's exact git_apply invocation on a CRLF-converted patch:
- a patch for a modified file fails loudly (rc=1, so it shows up as CONFLICT);
- a patch that creates a file applies with rc=0 and writes CRLF;
- `-R --check` then passes, so status reads applied;
- `--numstat --summary` still prints the clean path.
light creates three files (plan:711). The CR sits in the patch bytes themselves, so whitelists and -c flags cannot help; only a byte check sees it. I measured this on Linux with CRLF converted by sed, not on a Windows runner.

REFUTED OR WEAKENED.
- "If GIT_CONFIG_NOSYSTEM or the -c override failed, both runs would write CRLF" is overstated. The two guards back each other up: a `-c core.autocrlf=false` on the command line overrides any system config file (plan:259, :262-264). A consistent CRLF in the clean run needs both guards to fail. The realistic route is the checkout route in point 3.
- The package-cache invariance is not a defect. It holds by construction:
  - the tool changes tree files only by os.replace or os.unlink (plan:269, :273-276);
  - git runs only in the staging directory, and git apply itself unlinks and creates new files (plan:194).
  The pytest case (plan:464-465) runs exactly this write path against a shared inode, and a shared inode is all conda adds (plan:168-169). The cited experiments support the design rather than refute it: critic-landing/rollback (a hook that writes in place) left the cache file "patched" (inode 8539344, 2 links), while rollback2 (a hook that renames) left it "orig". A real-conda cache assertion would duplicate the pytest case.
- "Mode regression" on win-64 has no meaning (no executable bits), and on POSIX the pytest umask cases cover it (plan:466).

THE EDITOR'S RELAXATION is heavier than needed.
- `git show <tip tag>:<path>` needs the private isabelle-patched repository in CI, which the plan keeps out of CI on purpose (plan:501-502).
- The etc/options clause is moot: no feature touches etc/ (light's tools/patched_files.txt lists only src/ files, and a patch touching etc/ISABELLE_ID is refused, plan:254).
- Comparing every leg to linux-64 needs extra plumbing between CI jobs, and it is still only a comparison against another run of the same tool.
- The mode listing and the cache check are redundant (see above).
- Hashing against conda-meta works, but it is unnecessary. The shipped patch files already carry an absolute oracle: every git diff-tree block has an `index <pre>..<post>` line (plan:201, :492; make-patches:154). These are the blob ids of the file before and after that feature. Since make-patches' output format must not change (plan:653), the oracle matches on prefixes.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C20/ (git 2.43.0).
- crlf.sh (output in crlf.out): a toy repository gives a real `git diff-tree -r -p --no-renames` patch for a modified file and one for a created file. Each patch is also converted to CRLF, which is what a Windows checkout with autocrlf=true produces. Every call uses the plan's exact git_apply form: `env -i` whitelist with GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=/dev/null, GIT_ATTR_NOSYSTEM, the ceiling and LC_ALL=C, plus `-c core.autocrlf=false -c core.attributesFile=/dev/null --whitespace=nowarn`. Results:
  - modified file, CRLF patch: `--check` rc=1, "patch does not apply";
  - created file, CRLF patch: apply rc=0 and writes `new1\r\nnew2\r\n`;
  - `-R --check` rc=0, so status would say applied;
  - `--numstat --summary` prints the clean path s/n.ML;
  - the reverse apply deletes the file.
- oracle.py with oracle.sh (output in oracle.out) compares three checks:
  - (1) the status-style replay says "applied" in every case;
  - (2) the relative "hostile == clean" comparison PASSes even when both runs wrote CRLF;
  - (3) an absolute check of about 25 lines of Python: the git blob id of each file (sha1 of "blob <len>\0" plus the bytes, no git involved) must start with the index-line id of the topmost patch after apply and of the lowest patch after unapply, and 0000000 means the file is absent. It flags the CRLF created file (blob 0ccf29ca0ad4 != index 80ce8d9) and a modified file written with CRLF by a git that is not isolated (7bd16be6f59a != 7c86744). It passes on correct LF bytes, both at the top and at the bottom. It gives the same verdict when it reads the CRLF patch file itself.
- Read-only checks: plan:201, :254, :259-269, :273-287, :398-400, :464-468, :485-486, :492, :501-507, :588-600, :653, :664, :711; REVIEW2:304-337, :424, :443; make-patches:154-170; light_locale/tools/patched_files.txt (src/ only); no .gitattributes in light_locale or my_better_isabelle_prover; isabelle-packaging-ci/.gitattributes:1-6, nunchaku-pins.sh:34-36, win-crlf-hunt.yml:1-25, RELEASE_CHECKLIST.md:47-50, :180; critic-landing/rollback/{run.out, recover2.sh} plus stat (inode 8539344, 2 links, cache file reads "patched"); rollback2/run.out (cache file reads "orig").

Recommended fix: Smallest fix: one check, and one sentence in §10.
(1) Add one helper, check_bytes(tree, features.d, at_top). It reads only the installed patch files. For every path the chain touches:
- after apply to the chain top, the file's git blob id (sha1 of "blob <len>\0" plus the bytes, computed in Python) must start with the `index` post-image id of the topmost patch that touches the path;
- after unapply to the chain bottom, it must start with the pre-image id of the lowest such patch;
- 0000000 means the file must be absent.
It needs no git, no config, no private repository and no conda-meta. Use it in three places:
- §6 (a), (b) and (g) on all five legs, which covers the round-2 Windows action and goes further;
- the pytest hostile case, so that it checks absolute bytes as well as "equal to clean";
- the hook-layer tests.
(2) In §10's C1 row, say that this check replaces the round-2 judge's "Windows leg compares bytes", or that the author deviates.
(3) Optional, because it is the realistic Windows CRLF route: before checking out the feature repositories, the batch release workflow runs `git config --global core.autocrlf false`. That is one line in one place, and it covers every feature repository and the tool's hook fragment.
Do not add the cache-sha256 check, the mode listing, `git show <tip>` or the comparison against the linux-64 leg: the construction and the pytest case already cover them, or they need the private repository.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- the round-2 action 'the Windows leg compares file bytes after apply and after unapply' (REVIEW2:443) was dropped without §10 saying so;
- no CI check is independent of the code under test;
- a CRLF creation patch applies with rc=0 and then reads applied (defender-C20/crlf.out).

Refuted:
- the package-cache check: the cache stays intact by construction (os.replace only) and is covered by pytest;
- the mode listing on win-64.

The judge also refutes the defender's claim that 'no feature touches etc/'. dev_patches changes etc/options (`git diff --name-only Isabelle2025-2/pristine/89701cf1768e Isabelle2025-2/dev_patches -- etc` lists it), and pack.sh edits the same file (ML_system_64; defender-C19 found the difference at etc/options:193).

Author: add one absolute check, check_bytes, used in §6 (a), (b) and (g) on all five legs, in the pytest hostile case and in the hook-layer tests.
- After apply, every touched file's git blob id (computed in Python) must start with the `index` post-image id of the topmost patch that touches it. A file whose blob before apply differs from its lowest patch's pre-image id is edited by the packaging (today etc/options). For such a file, compare against the linux-64 leg's bytes, or leave it to the unapply-side check.
- After unapply, every file the chain touches must have the sha256 recorded for it in conda-meta/isabelle-*.json paths_data, and created files must be absent.
- Record in §10's C1 row that this replaces the round-2 Windows action.
- Under C5's single Linux build, the CRLF route through a Windows checkout disappears.

### C21 [minor] Three §6 items cannot run or cannot pass as written: (h) needs a second pristine build that will not exist, (a) names no leg, and (g) probably fails on win-64 because isabelle.bat recreates untracked Cygwin symlinks inside isa/

Section: §6 (a), (g), (h) (plan:589-590, :596-597); five legs (plan:588)  ·  merged from: landing-L10, consistency-CONS-17

**Statement.** (1) §6 (h)'s first half, 'a new isabelle build is published and the features are not re-released: update stays put, an explicit install conflicts' (plan:597), needs a second pristine build. At steps 7 and 8 only one exists, and no feature package can pin 2025.2-0 (ruling 22). So (h) cannot run before or at the first release; only the author's scratch experiment pintest/ covers it.

(2) §6 (a)'s session build runs 'on the legs the user authorizes' (plan:590). That names no leg and states no time budget, although rebuilding Pure and HOL from light's patched Pure on win-64 or under Rosetta is long.

(3) §6 (g) asserts `test ! -e "$PREFIX/isa"` after `conda remove isabelle`, on all five legs (plan:596). On Windows, the isabelle pre-unlink calls isabelle.bat version and getenv (recipe.yaml:153-158), and light's post-link calls isabelle.bat too. The first Isabelle call on Windows recreates 947 Cygwin symlinks inside the tree, which the package does not contain (PACKAGING_DESIGN.md:479-492; pack.sh:153-157). conda removes only the files it tracks, so isa/contrib/cygwin/…, and with it isa/, plausibly survives whatever the tool does. Not measured: no Windows host was available.

**Editor.** (3) is marked plausible, not confirmed, and it concerns the isabelle package's behaviour rather than the tool's; it still makes the plan's acceptance item unpassable on one leg if true.

**Relaxation proposed by the editor.** Move (h)'s 'not yet re-released' half to the hook-layer tests, with toy packages, and keep only the 'after re-release, update --all moves everything together' half for the first real re-release. Name (a)'s legs and give each a timeout. Measure (g) on win-64 first; if confirmed, restrict it to the POSIX legs, and on win-64 assert instead that no file a feature created or modified remains (compared against paths_data).

**Defender: confirmed** (needs owner: False).

I tried to refute each of the three parts. All three hold. Part (3) is stronger than the challenge says. Part (2)'s worry about build time is weaker than stated. The editor's fix for (g) needs correcting.

(1) §6 (h) cannot run when the plan schedules it.
- Step 7 runs all of §6 and requires all five platform legs to pass (plan:581).
- (h) needs an isabelle build newer than the one the feature packages pin (plan:597).
- At steps 6-8 only one pristine build exists (plan:579-582). Under ruling 22 no feature package may pin 2025.2-0 (plan:82-84). The online smoke in step 8 does not run (h) either (plan:401-405).
- The first half of (h), "the features are not re-released yet", is not among the hook-layer tests. Plan:478 covers only the re-released case, and plan:483 covers the move from 2025.2-0 to the pristine build.
- So before the first re-release, that first half is covered only by the author's scratch experiment pintest/.
- Defence that does not hold: both halves of (h) can run with real packages on every later run of the workflow for a new isabelle build (plan:408). By then ruling 22 has the new build published first, while the old feature packages still pin the previous build (plan:85). That makes (h) a scheduling defect, not a design defect.
- Round 2's (h) went from 2025.2-0 to the pristine build and could run at step 7 (REVIEW2 C16 judge). The rev-3 reshaping after ruling 22 removed that property without saying so.
- I re-ran both halves on toy packages in seconds (h/run.out): `update --all` stays put; an explicit install fails with LibMambaUnsatisfiableError; after the re-release, `update --all` moves isa and both features together. A hook-layer test is therefore cheap and is the right home.

(2) §6 (a) runs its session build "on the legs the user authorizes" (plan:590).
- The workflow inputs are isabelle_build, tool_ref, features, build_number, publish and roundtrip_checked (plan:395-397). None of them names legs.
- So the user's authorization has nothing to travel through.
- The time-budget point is true but not serious. The packaging CI already builds HOL on all five subdirs within measured timeouts:
  - heaps-linux: 180 min (build.yml:498)
  - heaps-macos: 330 min, arm64 and the x86_64 pass in one job (build.yml:583, :626-635)
  - heaps-windows: 240 min (build.yml:677)
- Light_Locale is just `HOL +` (light ROOT:4), so its check costs Pure plus HOL, the same as those jobs. The timeout only has to be copied, not discovered.

(3) §6 (g) fails on win-64 for a reason that has nothing to do with the tool.
How it happens:
- The isabelle package's win-64 pre-unlink calls `isabelle.bat version` and `getenv` (recipe.yaml:156, :158).
- Isabelle's first call runs cygwin_init (Environment.java:303-331). It writes every symlink listed in contrib/cygwin/isabelle/symlinks as a "!<symlink>" file inside the tree (:296-301, :311-323), then runs rebaseall and postinstall.
- These 947 files are not in the package. On a real conda-installed VM they were missing before the first call and present after it (PACKAGING_DESIGN.md:484-492; pack.sh:152-157).
- conda unlinks only tracked paths and removes only parent directories that are empty (path_actions.py:1156-1178; delete.py:190-196, :199-226).
- So isa/ survives `conda remove isabelle` on win-64, with or without feature packages, because the package's own pre-unlink creates the files.
- I reproduced the conda half on Linux with toy packages (run.out):
  - W1, a pre-unlink that imitates cygwin_init: isa/ survives.
  - W2, the control: isa/ is gone.
  - W3, Isabelle run once before removal: isa/ survives.
- recipe.yaml:106 says "no untracked files", which is wrong.
- Only an actual `conda remove` on Windows has not been run. The mechanism is the same platform-independent conda code.

The editor's relaxation:
- (h): right in substance. Both halves can also stay as checks on the re-release runs.
- (a): right.
- (g): the win-64 assertion needs to change.
  - "No modified file remains" is always true: conda deletes tracked paths whatever their content (path_actions.py:1156-1164).
  - Files a feature created are, by definition, not in paths_data, so comparing against paths_data cannot find them. The right list comes from the patch files (decision 3, plan:304-305).
  - The staging directory at `$PREFIX/isa.staging` is not checked at all.
  - "Measure first" is not needed before changing the plan. The win-64 leg will show the leftover files anyway.

Experiment: All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C21/. They used the owner's conda 25.11.1 binary with a private HOME, CONDARC, CONDA_PKGS_DIRS and TMPDIR, `-p` prefixes inside my scratch directory, and local file:// channels. I installed nothing into the owner's environments.

(A) Leftover files after `conda remove` (mk.py, run.sh, run.out).
- A toy linux-64 package "isa" ships isa/etc/ISABELLE_ID, isa/contrib/cygwin/isabelle/{uninitialized,symlinks} and a Cygwin binary.
- Its pre-unlink imitates recipe.yaml:156 followed by cygwin_init: it deletes the marker and writes the listed "symlink" files, none of which are in the package.
- W1: after `conda remove`, isa/contrib/cygwin/usr/{bin/awk,lib/libfoo.so} remain, so isa/ survives.
- W2, the same package without that pre-unlink: isa/ is gone.
- W3, an untracked file created before removal, as by any earlier Isabelle call: isa/ survives.

(B) Both halves of (h) on toy packages (h/mk.py copied from pintest/, h/run.sh, h/run.out).
- isa builds 0, 1 and 2; feata and featb pin `isa 1.0 1`.
- `conda update --all` reports "All requested packages already installed".
- `conda install isa=1.0=2` fails with LibMambaUnsatisfiableError ("featb-1-T_0 requires isa 1.0 1").
- After re-releasing the features pinned to `isa 1.0 2`, `conda update --all` moves isa to build 2 and both features to T_1.

Sources read:
- plan:395-408, :473-485, :579-582, :588-600
- isabelle-packaging-ci recipe.yaml:100-169; PACKAGING_DESIGN.md:440-492; pack.sh:152-165; build.yml:494-498, :579-635, :673-677; preunlink-probe.yml (it never checks for leftover files under isa/)
- Isabelle2025-2 Environment.java:286-332; getsettings:30 (Isabelle's temp directory on Windows is under LOCALAPPDATA, outside isa/)
- conda path_actions.py:1140-1178; delete.py:190-226; update.py:58-64
- light ROOT:4; REVIEW2 C15 and the C16 judge; REVIEW1:258-264

Recommended fix: These are edits to text and tests, all within ruling 17's delegation.

(1) (h):
- In decision 15's hook-layer list, next to plan:478, add: "a new toy isabelle build is published and the features are not re-released: `conda update --all` stays put, an explicit `conda install isabelle=<new>` fails with an unsatisfiable error, and no feature is removed". This is the pintest/ shape.
- In §6 (h) (plan:597), add a condition: it runs only when the batch release workflow is re-run for a new isabelle_build (decision 11, plan:408). At that point both halves can run with real packages: the online channel has the new build plus the old feature packages, and the local channel has the re-released ones.
- In step 7 (plan:581), say that §6 runs without (h).

(2) (a):
- Add a workflow input to decision 11 (plan:395-397), for example `session_check_legs`, with a default chosen by the author. Have plan:590 refer to that input instead of "the legs the user authorizes".
- Give each such leg the timeout of the matching heaps job in build.yml: 180, 330 or 240 minutes (build.yml:498, :583, :677).
- Optional: on all five legs, check that the component is registered with `isabelle sessions Light_Locale`, which does not build.

(3) (g):
- Keep `test ! -e "$PREFIX/isa"` on the four POSIX legs.
- On win-64, assert three things instead:
  - none of the paths created by the installed features' patch files (the `--- /dev/null` targets from decision 3's `--numstat --summary`) exists;
  - `$PREFIX/isa.staging` does not exist;
  - every path left under `$PREFIX/isa` is under `contrib/cygwin/`.
- Add one sentence explaining that this leftover comes from the isabelle package itself: its win-64 pre-unlink calls isabelle.bat (recipe.yaml:156), which runs cygwin_init. It occurs with no feature installed. Whether to clean it up is the CI plan's business (decision 12), and recipe.yaml:106's "no untracked files" should be corrected there.
- Do not use the "compared against paths_data" check.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed:
- §6 (h)'s first half needs a second pristine build that does not exist at steps 7 and 8;
- §6 (a)'s session build names no leg, and the workflow has no input through which a leg could be authorised;
- §6 (g) cannot pass on win-64. The isabelle pre-unlink calls isabelle.bat (recipe.yaml:156, :158), whose cygwin_init writes untracked files into isa/, and conda removes only tracked paths (defender-C21/run.out W1-W3 reproduce the conda half).

Author:
- Move (h)'s 'not yet re-released' half to the hook-layer tests (the pintest/ shape). Run both halves of §6 (h) only on re-runs for a new isabelle_build, and say in step 7 that §6 runs without (h).
- Add a workflow input naming the session-build legs. Give each such leg the timeout of the matching heaps job (build.yml:498, :583, :677).
- §6 (g):
  - keep `test ! -e $PREFIX/isa` on the four POSIX legs;
  - on win-64, assert that no path created by a feature's patch files exists, that isa.staging is absent, and that everything left under isa/ is under contrib/cygwin/;
  - state that this residue comes from the isabelle package itself;
  - do not use the paths_data comparison;
  - give the CI plan a note that recipe.yaml:106's 'no untracked files' is wrong.

### C22 [minor] The lock is on etc/ISABELLE_ID, a package-cache inode that every hard-linked environment shares, so environments block each other; on Windows the tool's own read of that file overlaps its 1-byte lock past EOF

Section: Decision 5 lock (plan:282-285); decision 2 (plan:231-232); §2.3 hard links (plan:168-169); §4 busy text (plan:563)  ·  merged from: consistency-CONS-9, engine-E7

**Statement.** The lock is taken on etc/ISABELLE_ID (plan:282-285). conda hard-links that file from pkgs/ into every environment (plan:168-169), and the tool never replaces it.

On POSIX, flock conflicts are decided per inode, so runs in different environments built from the same isabelle package block each other. Measured: envA's and envB's ISABELLE_ID share inode 8538434, and LOCK_EX in A makes a non-blocking LOCK_SH in B fail with BlockingIOError (review-ipc3/critic-consistency/flock/). A hook in B then waits up to 60 s, reports busy and applies nothing, and the busy text 'another run holds $PREFIX/isa' (plan:563) names the wrong tree.

On Windows the plan locks 1 byte just past the end of the file with msvcrt.locking (plan:283-284). Isabelle itself reads exactly the file's length (bytes.scala:84-111), so it is unaffected. But the tool also reads etc/ISABELLE_ID (plan:231-232, :245), and CPython's readall asks for size+1 bytes to detect EOF (_pyio.py:1666-1669; the C FileIO does the same). That range covers the locked byte. Windows byte-range locks are mandatory and per handle, so:
- if the tool locks first and then reads through another handle, the read fails;
- if it reads before locking, a concurrent run gets PermissionError instead of 'busy'.
Not measured on Windows. msvcrt has no shared mode, so even status locks exclusively there.

**Editor.** The cross-environment serialisation is mostly a false-contention problem: an apply takes well under a second (critic-engine: 0.16-0.25 s). It matters through the 60-second give-up in hooks and the wrong busy text. The Windows part is plausible, not measured.

**Relaxation proposed by the editor.** Lock one byte at a fixed far offset, for example 0x40000000 as SQLite does, so that no reader's range can ever reach it. Then reading the identity before or after locking, through any handle, is safe by construction.

Either accept the cross-environment serialisation and say so in the busy text, or on POSIX take the flock on a descriptor of the tree directory itself, which conda never hard-links.

Add a Windows-leg test: while one process holds the lock, a second status reports busy within the bound, and `type etc\ISABELLE_ID` succeeds.

**Defender: partially_confirmed** (needs owner: False).

Verdict: partly confirmed. The cross-environment serialisation is not a new design defect. Two smaller defects are real: the busy message is wrong when the run holding the lock is in another environment, and on Windows the plan locks the one byte that every read-to-end reader touches. Severity minor is right.

What I refuted or reduced:
1. Round 2 already accepted cross-environment serialisation. The round-2 editor wrote "Two environments that share the hard-linked inode merely serialise, which is harmless" (ISABELLE_PATCH_CONTROL_REVIEW2.md:1128). The round-2 defender measured it (REVIEW2:1166-1167), and judge action 6 adopted the lock on etc/ISABELLE_ID (REVIEW2:110). The brief says not to re-raise a point whose substance was covered.
2. Correctness is not affected. Every write to a tree is an os.replace or os.unlink of a path inside that environment (plan:277-281). os.replace gives the path a new inode and leaves other environments' links untouched (plan:168-169). So no state shared across environments needs the lock; the lock across environments only adds a delay.
3. The delay is short. On a copy of the real chain, the critic-engine prototype holds the tree for 0.17-0.32 s per status, apply or unapply (126-127 git calls; defender-C22/timing.out). A hook in another environment therefore waits a fraction of a second. The 60-second give-up fires only when the lock is held for 60 s, for example by a stopped process. That case blocks a run in the same environment just as well, and the bounded wait is what round 2 required (REVIEW2:1123).
4. The relaxation's alternative of taking flock on the tree directory should be rejected. I measured that a directory descriptor's flock is separate per tree on a local filesystem (flock.out). But on NFS, flock is emulated as a byte-range lock, and an exclusive lock needs a descriptor opened for writing (man 2 flock, "NFS details"). A directory cannot be opened for writing. The plan opens the file read-write precisely for NFS (plan:283). msvcrt also cannot lock a directory handle (REVIEW2:1126). So this option would split the lock into two mechanisms and break NFS.

What is confirmed:
A. The inode really is shared. pkgs/isabelle-2025.2-0/info/paths.json lists isa/etc/ISABELLE_ID with path_type "hardlink". The owner's real environments `isabelle` and `isabelle-2` share inode 53740046 with link count 2 (real_env_inodes.out). On hard links, an exclusive flock makes a non-blocking shared flock fail with BlockingIOError (flock.out). The plan never states this serialisation: decision 5 (plan:282-285) is silent, and §2.3 (plan:168-169) mentions the sharing only for os.replace. The busy text "another isabelle-patch-control run holds $PREFIX/isa" (plan:563) is false when the holder is a run in another environment. This is a wording defect.
B. The byte the plan locks on Windows (offset = file size, plan:283) is exactly the byte every read-to-end reader asks for:
   - CPython's Path.read_text on the 12-byte file issues read(fd, 13) and then read(fd, 1) at offset 12 (py.strace; _pyio.py:1666-1669).
   - `cat` issues read(131072) and then a read at offset 12 (cat.strace).
   - `isabelle version -i` reads the file with cat (Isabelle2025-2/lib/Tools/version:74-75).
   So the plan's claim that the lock does not block Isabelle's reads of ISABELLE_ID (plan:283-284) holds only for the Scala reader. That reader reads exactly the file's length and stops (bytes.scala:84-111, via isabelle_system.scala:85-105).
   On Windows, a read through another handle whose range overlaps a locked region fails (this is documented Windows behaviour; I did not measure it). The consequences:
   - The tool's own identity read (plan:232, :245) fails if it goes through any handle other than the one holding the lock.
   - A concurrent run that reads the identity before locking gets PermissionError instead of busy.
   - `isabelle version -i` fails while any tool run holds the lock.
   The plan's tests, the pytest lock case (plan:470) and the Windows-leg check (plan:485-486), would catch the tool's own ordering trap. They would not catch the cat reader. They also leave an invariant people must remember: read ISABELLE_ID only through the lock handle, and only after locking.
   This half follows round-2 judge action 6 to the letter (REVIEW2:110), so the author did not silently deviate. The judge's reasoning (REVIEW2:1155) compared only byte 0 with the Scala reader.
   The Windows half is not measured. Wine 9.0 does not enforce read conflicts even for a lock on byte 0 (win/wine_results.out), so it cannot settle the question either way.

On the relaxation: the fixed far offset is right. One constant makes it impossible for any reader, of any buffer size, to overlap the locked byte. POSIX flock ignores the offset, so the same code serves both platforms. Under Wine, a lock at 0x40000000 still excludes a second locker (error 33) and does not change the file's size (far.out). That is weak evidence, since Wine is not Windows, but it shows the API call is accepted.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C22/.
(1) flock_test.py makes a toy pkgs/ file with two hard links, envA and envB. LOCK_EX on envA makes a non-blocking LOCK_SH on envB fail with BlockingIOError. flock on the two tree-directory descriptors is independent across environments, and two descriptors of the same tree directory do conflict (flock.out).
(2) stat on the owner's real environments, read-only: envs/isabelle and envs/isabelle-2 share the ISABELLE_ID inode 53740046 with link count 2 (real_env_inodes.out). pkgs/isabelle-2025.2-0/info/paths.json gives `isa/etc/ISABELLE_ID` path_type hardlink, 12 bytes.
(3) A copy of critic-engine/ipc.py run on a copy of critic-engine/real/base with the real features.d. Status, apply and unapply take 0.17-0.32 s each, with 126-127 git calls (timing.out).
(4) strace of `python3 -I -c Path.read_text()` on the 12-byte file shows read(3, 13) and then read(3, 1) at offset 12 (py.strace). strace of `cat` shows read(3, 131072) and then a read at offset 12 (cat.strace). Isabelle2025-2/lib/Tools/version:74-75 reads ISABELLE_ID with cat; bytes.scala:84-111 reads exactly the file's length.
(5) win/locktest.c, cross-compiled with mingw and run under Wine 9.0 with a private WINEPREFIX. The lock is placed at offset 0, 12 or 0x40000000. All reads through a second handle succeed even with byte 0 locked, so Wine does not enforce read conflicts and cannot decide the Windows question. A second LockFile gets error 33 at every offset, and the file stays 12 bytes (win/wine_results.out, win/far.out).
I did not touch any repository, conda environment or Isabelle tree.

Recommended fix: These are the smallest fixes. All are wording or one constant, within the author's delegated authority (§0 item 17; plan:620).
1. Decision 5 (plan:283-284). Replace "Windows msvcrt.locking 锁文件末尾之后的 1 字节" with this: msvcrt.locking on 1 byte at the fixed offset 0x40000000 (seek there first; locking past the end of the file is allowed). Then no reader of the file, whatever its buffer size, overlaps the locked byte. Reading the identity before or after locking, through any handle, is then safe by construction. Keep the offset below 2^31: msvcrt.locking starts from the C runtime's current file position, and I have not checked positions beyond that. POSIX flock ignores the offset, so a single constant serves both platforms. Narrow the claim "不挡 Isabelle 自己读" accordingly: today it holds only for the Scala reader (bytes.scala:84-111), not for `isabelle version -i` (lib/Tools/version:74-75).
2. Decision 5. Add one sentence saying the serialisation is accepted: etc/ISABELLE_ID is hard-linked from the package cache (§2.3), so runs in environments that share it serialise. A run holds the lock well under a second, so this only delays; each environment writes only its own paths.
3. §4 busy text (plan:563). Make it true when the holder is elsewhere, for example: `another isabelle-patch-control run holds the lock on $PREFIX/isa/etc/ISABELLE_ID (the file may be shared with other conda environments installed from the same package cache); gave up after 60 s. Retry later.`
4. Decision 15, Windows leg (plan:485-486). Add one case: while one process holds the lock, a second `status` reports busy within the bound, and both `type etc\ISABELLE_ID` and `isabelle version -i` succeed.
Do not adopt the relaxation's lock on the tree directory. It breaks exclusive locks on NFS, where a writable descriptor is needed (man 2 flock, "NFS details"; plan:283), and Windows cannot lock a directory handle.

**Judge: partially_confirmed → author_fixes_no_rereview.** Cross-environment serialisation is not a new defect. Round 2 accepted it (REVIEW2:1128), and a run holds the lock for 0.17-0.32 s (defender-C22/timing.out).

What holds:
- the busy text (plan:563) names the wrong tree when the holder is a run in another environment;
- on Windows the plan locks the one byte that every read-to-end reader touches: CPython's read_text and `cat` both read at offset = size (py.strace, cat.strace), and `isabelle version -i` reads with cat (lib/Tools/version:74-75).

Author:
- Decision 5 (plan:283-284): lock 1 byte at the fixed offset 0x40000000 (msvcrt.locking after a seek; flock ignores the offset). Narrow the claim 'does not block Isabelle's reads' accordingly.
- Add one sentence accepting the serialisation, with its reason: the inode is shared through the package cache.
- Reword the busy text to name the locked file and say it may be shared with other environments.
- Windows-leg test: while one process holds the lock, a second status reports busy within the bound, and both `type etc\ISABELLE_ID` and `isabelle version -i` succeed.
- Do not lock the tree directory: it breaks exclusive locks on NFS, and Windows cannot lock a directory handle.

### C23 [minor] A pre-unlink that cannot run (lock busy, or the tool will not start) leaves changes that status can never see, and its message gives no recovery

Section: Decision 5 lock (plan:283-285); decision 9 pre-unlink (plan:349-351, :365-366); §4 busy text (plan:563)  ·  merged from: conda-conda-10

**Statement.** The residue list and its recovery steps are written only when a reverse runs into CONFLICT (plan:365-366).

When the lock is held, the pre-unlink waits 60 s and writes 'gave up after 60 s. Retry later.' (plan:284-285, :563). conda then removes the package anyway, so there is nothing left to retry, and status will never see the feature's changes in isa/.

When the tool cannot start, the frozen fallback (plan:350) says only that files 'may still carry its changes', with no list and no recovery. Measured: with the tool removed, `conda remove --force featc` printed only that generic line, exited 0, and the tree kept the change (review-ipc3/critic-conda/run.out scenario E).

Hook output is captured (plan:158), so a transaction with several feature hooks and a held lock can hang for minutes with no output.

**Editor.** When the tool cannot start, no file list can be produced, so the fallback can only add a recovery clause. That part of the critic's proposal is the most that is possible.

**Relaxation proposed by the editor.** In conda-hook pre-unlink, treat a busy lock like 'could not fully reverse': compute the feature's affected files without the lock (reading only) and write the §4 residue block with its recovery steps. Never write 'Retry later' from a pre-unlink. Use a short lock wait, a few seconds, inside hooks. Add a recovery clause to the frozen fallback echo ('… to restore: conda install --force-reinstall isabelle …', amended per C1).

**Defender: partially_confirmed** (needs owner: False).

The core of C23 holds: when the lock is busy, the pre-unlink tells the user to retry, but nothing is left to retry. Two side claims do not hold: the "minutes with no output" claim, and the critic's reading of scenario E.

CONFIRMED 1: a pre-unlink that cannot get the lock leaves changes nobody can see, and its message is wrong.
- What the plan says: after 60 s of waiting, "conda-hook" writes "busy and the retry command" and exits 0 (plan:284-285). Busy is listed as its own kind of diagnosis (plan:363). Its only text ends "gave up after 60 s. Retry later." (plan:563).
- The residue list is written only "when the pre-unlink cannot finish reversing" (plan:365-366, block at plan:554-562). Under decision 7 that means files in CONFLICT (plan:318-319). A busy hook never reaches unapply.
- The plan also gives no lock-free way to compute the list: even `status` takes LOCK_SH (plan:282-283), and a busy LOCK_EX blocks that too. So the plan as written cannot write the residue list in the busy case without an exception it never states.
- conda runs every pre-unlink first and only then unlinks anything (core/link.py:938-947, then :949). Once a package is removed its features.d entry is gone. "Retry later" therefore names no command that can work.
- Measured (toy channel with the plan's verbatim hooks; the toy tool does `flock -w 5` on isa/etc/ISABELLE_ID). File: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C23/run.out
  - Scenario L1, lines 3-15: `conda remove featc` pruned three packages. All three printed "Retry later". Afterwards the tree was still A2 B2 C2 and features.d was empty, so status can no longer see those changes.
- How reachable is this? flock is released when its holder dies, so a stale lock cannot happen. A busy lock needs a live holder that runs longer than the wait, for example a suspended run. That is rare, but the plan designs and tests this path itself (plan:470, :484).
- One new fact makes it more reachable. etc/ISABELLE_ID is hardlinked from the package cache (info/paths.json gives path_type hardlink). The owner's real environments `isabelle` and `isabelle-2` share inode 53740046.
  - flock on one hardlinked path blocks the other path for both LOCK_EX and LOCK_SH (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C23/hardlink-flock.out).
  - So the lock covers every environment with that isabelle build on the machine, and "another run holds $PREFIX/isa" (plan:563) can name the wrong tree. This goes beyond C23; the judge may want to file it with the lock challenge.

CONFIRMED 2: the frozen fallback text gives no way to recover.
- The post-link fallback names a fix: "run status and apply" (plan:340). The pre-unlink fallback does not (plan:350). That breaks the plan's own rule that every diagnosis gives a fix for its cause (plan:367-368).
- Measured, scenario E′ (run.out lines 63-74): the feature was applied, then the tool was removed with --force, then `conda remove --force featc`. Only the generic line was printed, the tree kept C2, and features.d no longer had c.

REFUTED or overstated:
- (a) "Can hang for minutes with no output." conda prints and deletes .messages.txt after every successful script (core/link.py:1685 and :1697-1708). Measured: each hook's busy line appeared as soon as that hook ended, at t=21, 26 and 31 s (run.out L1). The user sees one line per wait, not silence. The total time of N × 60 s is real, but it is a side effect.
- (b) The cited evidence, scenario E, does not show a kept change. In critic-conda/run.out:77 and :82 the tree was already pristine (a=a2 b=b2 c=c2) before the removal, because `--force-reinstall isa` had restored it. My scenario E′ does show the kept change.
- (c) The editor's claim that "no file list can be produced" when the tool cannot start is wrong. The renderer writes each feature's pre-unlink and knows that feature's patch files (plan:385). Still, no list is needed if the recovery is the one below.

On the editor's relaxation:
- "Treat busy like could-not-fully-reverse" and "never write Retry later from a pre-unlink": both right, and the more elegant shape. One rule — every pre-unlink that leaves files of F or a feature above it at a level ≥ k writes the residue block, whatever the cause — removes the special case.
  - Reading without the lock is sound because every write to the tree is a single os.replace or os.unlink (plan:276-279), so a reader always sees each file whole.
- "A few seconds' wait inside hooks" is backwards for pre-unlink. The pre-unlink is the last moment the reversal can happen, so a shorter wait turns more short contentions into leftover changes. conda's own lock waits about 10 s (gateways/disk/lock.py:17-18,64-77). Shorten only the post-link wait if at all: a busy post-link leaves a state that `isabelle-patch-control apply` repairs (run.out scenario P).
- "Add a recovery clause to the fallback": yes. Measured (scenario L3, run.out:41-62): reinstalling the removed package and then removing it again reversed everything, back to a2 b2 c2.
  - This route needs no file list.
  - It also removes files the feature created, which `--force-reinstall isabelle` leaves behind.
  - It does not delete the user's Isabelle directory.
  - L3's reinstall step itself ran under a still-held lock: a leftover holder from an earlier step was still alive, an artefact of my script. That did no harm, because the files were already at the applied level.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C23/

Setup:
- mkchan.py is the critic's toy channel generator (verbatim plan hook fragment and pre-unlink, exact build pins). I added one change to the toy tool: `exec 9<>isa/etc/ISABELLE_ID; flock -x -w 5 9`. On timeout it writes the plan's busy text and exits 0.
- run.sh drives conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and envs directory, and PYTHONUNBUFFERED=1. Every line of conda output is timestamped. Results are in run.out.

Scenarios:
- L1: hold the lock on env A, then `conda remove featc`, which prunes feata and featb too. Three busy lines appeared at 5 s intervals, each saying "Retry later". Afterwards the tree was A2 B2 C2 with features.d empty.
- L2: hold the lock through env B's path (same inode) and remove in a third env. Same result.
- L3: reinstall featc in env A, then remove it. The tree reversed to a2 b2 c2.
- E′: create the env, `conda remove --force isabelle-patch-control`, then `conda remove --force featc`. Only the generic fallback line was printed; the tree kept C2 and features.d was a b.
- P: post-link while the lock was held. Three busy lines appeared and the tree was left unapplied, which `apply` can repair.

Lock sharing across hardlinks:
- hardlink-flock.out: on a file with two hardlinked paths, LOCK_EX on one path blocks both LOCK_EX|LOCK_NB and LOCK_SH|LOCK_NB on the other.
- `stat` on the real environments: /home/qiyuan/miniconda3/envs/isabelle and /home/qiyuan/miniconda3/envs/isabelle-2 share inode 53740046 for isa/etc/ISABELLE_ID.

conda source read: core/link.py:938-953 (all pre-unlinks run before any unlink), :1685 and :1697-1708 (.messages.txt printed and deleted after every script), gateways/disk/lock.py:17-18 (conda's own lock waits about 10 s). I also re-read critic-conda/run.out:68-82.

Recommended fix: Smallest fix, all within the author's delegated authority:

1. Decision 5 (plan:284-285), decision 9 (plan:363-366) and §4 (plan:563):
   - In `conda-hook pre-unlink`, a lock timeout is not a "busy" diagnosis and never writes "Retry later".
   - Replace plan:365 with one rule: whenever a pre-unlink leaves files of F or a feature above it at a level ≥ k, for any reason (CONFLICT, lock timeout, a failed os.replace), it writes the residue block.
   - On a lock timeout, the levels are computed without the lock. State the reason: every write to the tree is a single os.replace or os.unlink (plan:276-279), so an unlocked reader sees whole files.
   - "Retry later" stays for post-link and interactive commands only.
   - Keep the 60 s wait in pre-unlink; do not shorten it there. Shorten the post-link wait if desired.

2. Recovery text:
   - For a residue left by a lock timeout, or by a tool that could not start, say: "reinstall <pkg> (with isabelle-patch-control installed and working), then conda remove <pkg> again". This was measured to reverse everything, including the files the feature created.
   - Keep the plan:367-368 route (amended per C1) for residues caused by the user's own edits (CONFLICT).

3. The fallback at plan:350: append the clause from point 2 with <pkg> filled in by the renderer, for example "…may still carry its changes; to undo: make isabelle-patch-control runnable, conda install <pkg>, then conda remove <pkg>". No file list is needed.

4. Add a hook-layer test (plan:484): lock busy during the pre-unlink of a removal with pruning. Assert the residue block and the absence of "Retry later".

Separately, for the judge: etc/ISABELLE_ID is hardlinked from the package cache, so the lock is shared by every environment of the same isabelle build on the machine. The busy text "another run holds $PREFIX/isa" can therefore name the wrong tree. This is outside C23; consider routing it to the lock challenge.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- a pre-unlink whose lock wait times out writes 'Retry later', but nothing is left to retry, and the changes stay invisible (defender-C23/run.out L1);
- the frozen fallback (plan:350) gives no recovery (E′).

Refuted:
- the 'minutes with no output' claim: each hook's line appears when that hook ends;
- the editor's 'no file list possible'.

Author:
- Decision 9 gets one rule: whenever a pre-unlink leaves files of F or of a feature above it at a level ≥ k, for any reason (CONFLICT, lock timeout, a failed os.replace), it writes the residue block. On a lock timeout the levels are computed without the lock. That is sound because every write to the tree is a single os.replace or os.unlink.
- 'Retry later' is never written by a pre-unlink.
- Keep the 60 s wait in pre-unlink; shorten only the post-link wait, if at all.
- For a residue left by a lock timeout or by a tool that could not start, the recovery is: make the tool runnable, `conda install <pkg>`, then `conda remove <pkg>`. This was measured to reverse everything, created files included (L3).
- The renderer fills this into the fallback text (plan:350).
- Keep the C1-amended route for residues the user caused.
- Add a hook-layer case: lock busy during a pruning removal; assert the residue block and no 'Retry later'.

### C24 [minor] The frozen hook texts are incomplete and their copies are unchecked: the .bat texts are never written, the fragment cannot be copied verbatim into the CI's printf idiom, the entry point can be replaced through PYTHONPATH, and the Windows notices use POSIX syntax

Section: Decision 9 (plan:336-355); decision 1 freeze (plan:220-221); decision 12.2 (plan:416-417); decision 5 (plan:281); §4 (plan:532-539); §10 row C4 (plan:667)  ·  merged from: conda-conda-7, conda-conda-8, conda-conda-9, user-U12

**Statement.** Decision 1 freezes the hook interface for 1.x (plan:220-221), because published hook text can never change. Four gaps remain.

(1) The .bat texts are not written. The plan gives the .sh fragment and the .sh pre-unlink, says the .bat is 'the same' (同义, plan:345), and gives no .bat for light's component lines. Round 2's judge required the exact .sh and .bat text (REVIEW2:876), and §10's C4 row (plan:667) says it is done. cmd is where this channel's exit-0 guarantee has already broken once (recipe.yaml:118-122). A parenthesised `if exist … ( … ) else …` block expands %PREFIX% when cmd parses the block, so a prefix containing ')' ends the block early. The hook-layer tests are bash on Linux, so the .bat's tool-absent, tool-crash and elif branches run on no leg.

(2) The fragment cannot be copied verbatim into the CI. The CI recipe writes the isabelle post-link with printf '%s\n' and every line single-quoted (recipe.yaml:188-209), and fragment line 3 contains single quotes (plan:340). A literal transcription still passes bash -n, but the message loses its quotes and is split over three lines (review-ipc3/critic-conda/gen-naive.sh, post-link.out.sh). Nothing checks the built isabelle post-link against the tool repository's fragment.

(3) The entry point can be replaced. The fragment and the pre-unlink call the entry-point script. conda gives every hook a copy of the user's environment (link.py:1566), and entry points honour PYTHONPATH and the user site directory. So a checkout or a `pip install --user -e` of isabelle_patch_control runs instead of the installed tool in every hook (measured with the owner's isabelle-mcp entry point, critic-conda/pyshadow/). Decision 4 builds git's environment from a whitelist for exactly this kind of reason (plan:262-265).

(4) The Windows notices use POSIX syntax. The §4 notices print `$(isabelle getenv -b ISABELLE_HOME_USER)` and $PREFIX, while Windows users are told to use PowerShell or cmd (recipe.yaml:130), and getenv returns /cygdrive paths there. Separately, os.replace is attempted once (plan:281), while conda retries its own Windows file operations with backoff because of virus scanners (gateways/disk/__init__.py:19-20, gateways/disk/update.py:134-135).

**Editor.** (3) is mostly a hazard for developers. But the frozen form cannot be fixed later, so the choice belongs in the plan now. (1) could not be run (no Windows host).

**Relaxation proposed by the editor.** - Write the exact .bat fragment, .bat pre-unlink and light's .bat component lines into decision 9, with no parenthesised blocks: one-line `if exist … call … || >>file echo …` forms, or goto labels.
- Behind the existing presence test, invoke `"$PREFIX/bin/python" -I -m isabelle_patch_control conda-hook …` (Windows: `"%PREFIX%\python.exe" -I -m …`), and freeze that form in decision 1.
- Keep single quotes out of the fragment, and have the CI recipe copy the fragment file instead of retyping it. Add a §6 check that the published isabelle package's post-link contains hooks/post-link.{sh,bat} byte for byte.
- Run the 'tool absent' and 'tool crashes at start-up' cases on win-64.
- Give each notice its Windows text.
- Retry os.replace and os.unlink on Windows with a short bounded backoff before reporting a failure.

**Defender: partially_confirmed** (needs owner: False).

Part (1), the .bat texts. CONFIRMED that they are missing; two sub-claims are REFUTED.
- The plan gives the exact .sh post-link fragment and .sh pre-unlink (plan:336-344, :347-351). For Windows it only says the .bat "means the same" (`.bat` 同义, plan:345), naming the exe path and CRLF.
- Round 2's judge asked for the exact text: "Decision 11.2 gives the exact .sh and .bat text" (REVIEW2:876, also :862). §10's C4 row (plan:667) presents C4 as fully handled and never says the .bat text was put off. That is an unacknowledged deviation from a judge action.
- It matters for two reasons. Published hook text never changes (plan:220). And this .bat has to branch: if tool present / elif features.d present. No existing hook on the channel branches inside a parenthesised block. The isabelle pre-unlink uses one-line `|| exit /b 0` forms, and its comment explains why it avoids blocks (recipe.yaml:148-149, :159-161). cmd is also where the exit-0 guarantee broke once (recipe.yaml:118-122).
- REFUTED: "no .bat for light's component lines". plan:353-355 points to the channel's component convention, which has concrete, Windows-verified .bat text (RELEASE_CHECKLIST.md:250-266; Isabelle_RPC/conda/recipe.yaml:165-176; Semantic_Embedding/conda/recipe.yaml:274-285).
- REFUTED as stated: the claim that a `)` in the prefix ends the block. It only happens when %PREFIX% appears unquoted inside a block. I ran this under wine 9.0 (defender-C24/bat/parse.out):
  - variant P.bat (the natural transcription, every %PREFIX% in double quotes) works with prefix `C:\envs\a)b`;
  - only P2.bat, which echoes %PREFIX% unquoted inside the block, breaks.
- Prefixes where `)` comes with a space, or that contain `&` or `^`, already stop conda's own `cmd /d /c <path>` call (link.py:1615) before our script runs. The same harness showed this.
- Coverage: the claim that the .bat branches "run on no leg" is overstated. §6 (plan:587) includes the hook-layer tests, and decision 11 runs §6 on five legs (plan:400). §6 (c) and (g) do exercise the real isabelle .bat's tool-present branch and its silent no-tool branch on win-64.
- What is actually missing: decision 15 (plan:473-486) never says the toy channel carries .bat hooks or that the tool-crash and tool-absent cases run on win-64.

Part (2), the copy into the CI recipe. "Cannot be copied verbatim" is FALSE; "unchecked" is CONFIRMED.
- The copy can be made exact. The recipe's own escape idiom `'"'"'` (already used at recipe.yaml:158) gives an exact copy, and so does a quoted heredoc. Both are cmp-identical to the fragment (defender-C24/frag/escaped.sh, heredoc.sh).
- A naive transcription passes `bash -n` and keeps exit 0, but it corrupts the failure message, splitting it over three lines without its quotes (frag/naive.sh).
- No check in the plan compares the published isabelle post-link with the tool repository's fragment. Plan:336 and :416 only say "copy verbatim".
- Impact is cosmetic: only the failure-branch message is affected.
- The relaxation's "have the CI recipe copy the file" would give isabelle-packaging-ci a build-time dependency on the tool repository, and the CI changes are another plan's business (plan §1). The batch workflow already downloads the published isabelle package (plan:400) and owns the fragment files, so a check there is the smaller fix.

Part (3), PYTHONPATH. The mechanism is CONFIRMED; the impact is narrow, and the editor's "cannot be fixed later" is overstated.
- conda copies the whole user environment into every hook (link.py:1566). Python lets PYTHONPATH and the user site directory shadow an entry point's package (my run: defender-C24/pyshadow).
- Who is exposed: the tool is not on PyPI (item 23), so a second importable copy exists only in developer setups. If PYTHONPATH or PYTHONHOME merely breaks start-up, the fragment's `||` fallback still writes its message and exits 0.
- Decision 1 freezes the command lines (plan:220-221), not how Python is invoked. A later render can switch to `python -I -m isabelle_patch_control` at no compatibility cost, because `__main__` exists (plan:504) and item 22 re-releases every feature package for each isabelle build.
- The relaxation's bare `-I` has a side effect it does not mention. On Windows, conda's post-link wrapper sets PYTHONUTF8=1 and PYTHONIOENCODING=utf-8 (utils.py:225-226), and `-I` drops both. Measured: utf8_mode is 0 under `-I` and 1 under `-I -X utf8`. So `-X utf8` would be required too.

Part (4a), the Windows wording of the notices. CONFIRMED but cosmetic.
- The heap notice prints the literal `$(isabelle getenv -b ISABELLE_HOME_USER)/heaps` (plan:534, :539). That is POSIX syntax, and on Windows getenv returns /cygdrive paths (recipe.yaml:144).
- One platform-neutral sentence fixes it; separate Windows texts are not needed. The wording itself is delegated to the author (item 17).

Part (4b), Windows retries. CONFIRMED.
- Plan:281 tries os.replace once and then prints status.
- conda retries its own Windows file operations with exponential backoff because of virus scanners (gateways/disk/__init__.py:16-20; update.py:134-135). A staging file that git has just written is exactly what a scanner opens.
- The damage is bounded by decision 5's convergence: the tree is left half-applied with a message, and the user re-runs apply. Still, this is an avoidable intermittent failure inside `conda install`.

Experiment: All files are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C24/.

(a) cmd parsing under wine 9.0, with a private WINEPREFIX in wineprefix/.
- bat/fake.c is built into bat/fake.exe with mingw; it logs its argv and exits with $FAKE_RC.
- Variants: bat/P.bat (parenthesised if / else-if, every %PREFIX% quoted), bat/P2.bat (the same, but echoing %PREFIX% unquoted inside the block) and bat/G.bat (goto labels).
- Driver: bat/run.sh. Results: bat/P.out and bat/parse.out.
  - P and G behave correctly with prefixes `C:\envs\plain` and `C:\envs\a)b`.
  - P2 breaks the block at `a)`: stray commands run and the else-branch logic is lost.
  - Prefixes `x (y)`, `a&b` and `a^b` fail in conda's own `cmd /d /c <path>` call before the script runs.
- Caveat: wine 9.0's cmd evaluates `||` and `&&` wrongly for external commands (bat/t2.bat: `cmd /c exit 0 || echo FAILED4` prints FAILED4). So only the parse results count as evidence, not the branch outcomes.

(b) The fragment's transcription into the CI's printf idiom (frag/).
- I wrote the fragment three ways: naive (the critic's gen-naive.sh), with `'"'"'` escapes (gen-escaped.sh), and as a quoted heredoc (gen-heredoc.sh).
- All three pass `bash -n`. escaped.sh and heredoc.sh are cmp-identical to the canonical fragment.
- With a failing fake tool, naive.sh exits 0 but writes the message over three lines without its quotes; escaped.sh writes it intact.

(c) Python shadowing (pyshadow/).
- A conda-style entry point imports the shadow copy when PYTHONPATH points at a checkout.
- `python -I` imports the installed copy.
- `PYTHONUTF8=1 python -I` gives utf8_mode 0; adding `-X utf8` restores 1.

(d) conda 25.11.1 source read:
- link.py:1566 (environment copy), :1615 (`cmd /d /c`), :1109-1114 (post-link runs activated);
- utils.py:225-226 (the Windows wrapper sets PYTHONUTF8 and PYTHONIOENCODING);
- gateways/disk/__init__.py:16-20 and update.py:134-135 (exp_backoff_fn);
- cli/install.py:107-130 and core/prefix_data.py:326-336 (prefixes may contain `( ) & ^ !`; only the path separator is refused).

Recommended fix: Smallest fix, in priority order:
1. Decision 9 (plan:345): write out the exact .bat post-link fragment and .bat pre-unlink, in the channel's branch-free style. That means `if not exist "…exe" goto absent` / goto labels, or one-line `if exist "…" "…exe" conda-hook post-link || >>"%PREFIX%\.messages.txt" echo …` forms. Every %PREFIX% goes inside double quotes, no message echoes %PREFIX% unquoted, and the file ends with `exit /b 0`. Say that light's component lines are appended after the fragment's end label, copied from Isabelle_RPC/conda/recipe.yaml:165-176. Amend §10's C4 row so it says the .bat text was added in this revision.
2. §6 / decision 11: add one check run by the batch workflow, which already downloads the published isabelle package (plan:400). The check asserts that the package's `bin/.isabelle-post-link.sh` and `Scripts/.isabelle-post-link.bat` contain `hooks/post-link.sh` and `hooks/post-link.bat` byte for byte. With this check, the CI may transcribe the fragment however it likes, so neither a single-quote ban nor a cross-repo file copy is needed.
3. Decision 15: state that the toy channel's packages carry the real .bat hooks and that the "tool crashes at start-up" and "tool absent" cases run on the win-64 leg.
4. Decision 5 (plan:281): on Windows, wrap os.replace and os.unlink in a short bounded retry, about 7 tries over about 6 s like conda's MAX_TRIES. Only after that fall back to "recompute and print status".
5. §4 (plan:534, :539): replace the literal `$(isabelle getenv -b ISABELLE_HOME_USER)/heaps` with platform-neutral wording, e.g. "the heaps folder of this environment's Isabelle user directory (shown by: isabelle getenv -b ISABELLE_HOME_USER)".
6. Optional, the author's choice: have the hooks invoke `"$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook …` (Windows: `"%PREFIX%\python.exe" -I -X utf8 -m …`), kept behind the existing presence test. `-X utf8` is mandatory if `-I` is used, because `-I` would otherwise drop the PYTHONUTF8 and PYTHONIOENCODING settings conda gives Windows post-links. The change can also be made later, since decision 1 freezes only the command lines.

**Judge: partially_confirmed → author_decides_then_rereview.** Confirmed:
- the .bat texts are never written ('同义', plan:345), against REVIEW2:876, while §10's C4 row (plan:667) claims C4 is done;
- nothing checks the CI's copy of the fragment;
- PYTHONPATH can shadow the entry point;
- the notices use POSIX syntax on Windows;
- os.replace is tried once on Windows.

Refuted:
- 'cannot be copied verbatim': the `'"'"'` idiom and a quoted heredoc both give an exact copy (defender-C24/frag);
- a ')' in the prefix breaks only an unquoted %PREFIX% inside a block (bat/parse.out);
- light's component .bat lines exist in the channel's convention (Isabelle_RPC/conda/recipe.yaml:165-176).

Author:
- Write the exact .bat post-link fragment and .bat pre-unlink into decision 9: no parenthesised blocks (goto labels or one-line forms), every %PREFIX% quoted, ending `exit /b 0`. Say that light's lines are appended after the end label. Amend §10's C4 row.
- The batch workflow asserts that the downloaded isabelle package's post-link .sh and .bat contain hooks/post-link.sh and hooks/post-link.bat byte for byte.
- Decision 15: the toy packages carry the real .bat hooks, and the 'tool crashes' and 'tool absent' cases run on win-64.
- Decision 5: a bounded retry of os.replace and os.unlink on Windows (about 7 tries over about 6 s, like conda).
- §4: platform-neutral wording for the heap directory.
- Optional: invoke `python -I -X utf8 -m isabelle_patch_control`; `-X utf8` is mandatory with `-I` (utils.py:225-226).

### C25 [minor] Environments whose prefixes share a basename share one Isabelle user directory; with feature packages their trees differ, so they cross-register sessions, invalidate each other's heaps and delete each other's state, yet decision 12.6 only suggests a fix

Section: Decision 12 point 6 (plan:423); §2.3 (plan:151); §6 (j) (plan:599)  ·  merged from: user-U7

**Statement.** ISABELLE_HOME_USER is keyed by the basename of the prefix (pack.sh:188; plan:151). So two prefixes called env in different directories, which is the `conda create -p <repo>/env` pattern of §6 (j) (plan:599), share one user directory.

Before feature packages every tree was identical, so the sharing cost little. With feature packages the trees differ:
- the environment with light registers …/A/env/share/isabelle-light-locale in the shared etc/components, so the other environment sees a Light_Locale session whose Pure patches it lacks;
- each environment invalidates the HOL heap the other built in the shared user directory, at every switch;
- any isabelle relink or removal in one environment runs `rm -rf` on the other environment's heaps and registrations (recipe.yaml:225-227), which compounds C1.

Decision 12 point 6 leaves the fix as a suggestion to the CI plan (plan:423).

**Editor.** The collision predates this plan, and the plan already identified it, so I downgrade it from the critic's 'major' to minor. The finding is that feature packages turn it from shared caches into cross-environment corruption, so it must become a requirement.

**Relaxation proposed by the editor.** Make decision 12 point 6 a requirement that lands before feature packages ship, for example a key derived from a hash of the prefix. Add a §6 case with two `-p …/env` environments, one with isabelle-light-locale and one without, checking that their registrations and heaps stay separate.

**Defender: partially_confirmed** (needs owner: False).

In short: every fact the challenge states is true, and one is worse than it says. Its claim that the collision was cheap before feature packages is wrong. Its demand that the fix become a binding requirement goes further than the round-1 ruling it re-raises, and further than ruling 20 allows without asking the owner. What survives is a regression: rev 3 dropped part of a confirmed round-1 judge action and never says so.

CONFIRMED
1. The key really is the prefix's basename, the last part of the path. The published settings line is `ISABELLE_HOME_USER="${ISABELLE_HOME_USER}-conda-$(basename "$(dirname "$ISABELLE_HOME")")"` (pkgs/isabelle-2025.2-0/isa/etc/settings:98, written by pack.sh:188). ISABELLE_HOME is the resolved real path (bin/isabelle:19). My simulation maps `/home/u/a/env` and `/home/u/b/env` to the same `~/.isabelle/Isabelle2025-2-conda-env`. The same happens to two rattler-build test environments, which are always named `test_run_env`, and to same-named environments in two conda installations (sim.out).
2. Component registrations are shared.
   - `isabelle components -u` writes `$ISABELLE_HOME_USER/etc/components` (components.scala:294, :305-319).
   - Isabelle reads that file at every start (getsettings:89-90, getfunctions:278-280).
   - Every registered directory with a ROOT supplies sessions (sessions.scala:1285).
   - Light's component payload carries `session Light_Locale = HOL` (light_locale/ROOT:4; plan:384).
   - So an environment without light sees a Light_Locale session whose Pure patches it lacks.
3. Heaps are shared, and the damage is worse than the challenge says.
   - Isabelle searches the user heap directory before the shipped one (store.scala:334-336).
   - Tools that build first rebuild Pure and HOL at every switch between the two environments.
   - Tools that do not build, such as `isabelle process` (ml_process.scala:171-176) and `isabelle console -n` (ml_console.scala:78-80), load the first heap file found without checking its sources (store.scala:357-360, :370-378).
   - So a plain environment can silently run the other environment's light-patched HOL. The light environment can silently run a plain HOL while `status` reports applied.
   - Isa-REPL builds first (repl_tool.scala:108-112), so it only pays the rebuilds.
4. `rm -rf` of the shared directory is at recipe.yaml:225-227. Three of the plan's own user-facing texts say `--force-reinstall isabelle` deletes "this environment's" user directory (plan:367, :549-550, :561). Under a collision that is false: it also deletes the other environment's heaps and its Light_Locale registration.
5. Rev 3 dropped part of a round-1 judge action without saying so.
   - REVIEW1:2291-2292 (C26, confirmed, author fixes without re-review) required one sentence on the consequences: rebuilds at every switch, and removing isabelle deletes the shared directory. It also required a recommendation to the CI plan, with "documented limitation" as the alternative.
   - Rev 2 carried the sentence (rev2:131-133). Rev 3 cut it to "两个 basename 相同的 prefix 共用 heap 目录" (plan:151).
   - §10's row for rev-1 omissions (plan:690) does not mention it.
   - The documented-limitation alternative appears nowhere: not in decision 12 point 6 (plan:423), not in decision 14's README list (plan:448-452). The CI repository still claims "each conda env gets its own" directory (pack.sh:174-175).

REFUTED OR NARROWED
a. "Before feature packages every tree was identical, so the sharing cost little" is wrong. The collision already breaks environments today, with no feature package involved.
   - The ecosystem's component packages ship a ROOT (envs/isabelle/share/isabelle-rpc/ROOT, isabelle-semantic-embedding/ROOT).
   - So two same-basename environments that both install them register two directories defining the same sessions. That is a hard "Duplicate session" error in both environments (sessions.scala:869-872).
   - Live evidence on this machine: `~/.isabelle/Isabelle2025-2-conda-test_run_env/etc/components` holds 24 isabelle-nunchaku registrations from 24 different `test_run_env` prefixes. 21 of those prefixes are gone, so every Isabelle start in such an environment prints 21 "### Missing Isabelle component" lines (getfunctions:262).
   - Also, `2025.2-0` carries expose_foreign (plan:149). So same-basename environments on that build and on the pristine build already rebuild each other's heaps, with no feature package installed.
   - Feature packages add one more case (same build, different feature sets) and one more component (light). They do not add a new kind of failure.
b. That decision 12 point 6 "only suggests" is not itself a defect.
   - It matches the round-1 judge's word "recommending" (REVIEW1:2292).
   - Making it a binding requirement in this plan would change a packaging edit that ruling 20 names explicitly: the "-conda-<环境名>" suffix (plan:72). The CI plan must put that change to the owner.
   - "Before feature packages ship" is not forced either. On update, the old build's pre-unlink works out the old directory name from the old tree and deletes it (recipe.yaml:225-227). So changing the suffix in any later isabelle build leaves nothing behind. And ruling 22 already republishes every feature package with each new build.
c. The editor's proposed §6 case is more than needed. If two environments get different ISABELLE_HOME_USER values, their heaps (settings:99) and component registrations (components.scala:294) are separate by construction. One `isabelle getenv -b ISABELLE_HOME_USER` comparison proves it without any build. Since it tests pack.sh, it belongs in the CI plan's package tests, not in the tool's §6.

Elegance: a directory name that is unique per prefix makes the collision impossible, which is better than a documented limitation. But that is a CI-plan decision that needs the owner, not a defect in this tool plan.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C25/

(1) line98.sh is the published etc/settings:98, copied verbatim from the read-only package cache. sim.sh evaluates it for six prefixes: /home/u/a/env and /home/u/b/env, two test_run_env prefixes, and the same envs/isabelle name under miniconda3 and under miniforge3. Each pair maps to one shared directory. The same script tries the prototype fix `-conda-$(basename P)-$(printf %s P | cksum | cut -d' ' -f1)`: all six directories differ, and all still match the pre-unlink guard `*/.isabelle/*-conda-*`. Output is in sim.out.

(2) Read-only inspection of ~/.isabelle: Isabelle2025-2-conda-test_run_env/etc/components has 24 lines, one per distinct rattler-build test_run_env prefix. 21 of those directories no longer exist and 3 do.

(3) Source reading in pkgs/isabelle-2025.2-0/isa (read-only):
- components.scala:294-319, where `components -u` writes;
- getsettings:89-90 and getfunctions:244-281, how the user components file is read;
- sessions.scala:869-872 (Duplicate session error) and :1285 (components supply sessions);
- store.scala:334-336, :357-360, :370-378 (heap search order; first heap taken without a source check);
- ml_process.scala:171-176 and ml_console.scala:58-62, :78-80 (which tools build first);
- bin/isabelle:19 (ISABELLE_HOME is the resolved path).

(4) Other files read:
- Isa-REPL repl_tool.scala:108-112: it builds before loading heaps.
- isabelle-rpc and isabelle-semantic-embedding ship a ROOT in envs/isabelle/share.
- light_locale/ROOT:4.
- REVIEW1:2234-2292 (round-1 C26 and its judge ruling); rev2 plan:131-133 and :307; rev 3 plan:151, :367, :423, :549-561, :690.
- pack.sh:174-175, :188; recipe.yaml:212-231.

I ran no isabelle command and no conda operation, and modified nothing outside the scratch directory.

Recommended fix: These are text changes only. The tool itself needs no change.

(1) plan:151: restore the consequence sentence the round-1 judge required (REVIEW1:2291; rev 2 had it at rev2:131-133), extended for ruling 21. Proposed text:
"两个 basename 相同的 prefix（`-p ~/a/env` 与 `-p ~/b/env`、两个 conda 安装里的同名环境、rattler-build 的 `test_run_env`）共用整个用户目录：heap、偏好、`etc/components` 的组件登记（含 light 的 Light_Locale）。装的 feature 不同时，会先构建的工具每次切换都重建 Pure/HOL（store.scala:334-336），不构建的 `isabelle process` 直接载入另一个环境的 heap（store.scala:357-360）；任一环境卸载或 `--force-reinstall` `isabelle` 都删掉这个共用目录（recipe.yaml:225-227）。这个问题早于本计划：两个这样的环境装同一个带 session 的组件包已经报 Duplicate session（sessions.scala:869-872）。"
Also add the round-1 C26 row to §10.

(2) Decision 12 point 6 (plan:423): keep "由 CI 计划定", but name both alternatives from REVIEW1:2292.
- (i) Recommended: append a short hash of the resolved prefix to the existing suffix, `-conda-$(basename P)-$(printf %s P | cksum | cut -d' ' -f1)`. This keeps the pre-unlink guard working. It leaves nothing behind on update, because the old build's pre-unlink deletes the old directory. Because ruling 20 names this suffix, the CI plan must ask the owner first. Check `cksum` on the Windows leg.
- (ii) Otherwise: state the limitation in the isabelle package's post-link message and in the README (add it to decision 14's README list).

(3) plan:367, :549-550, :561: add to "this environment's Isabelle user directory" the qualifier "(shared with other environments whose prefix ends in the same directory name)" until (i) lands. Exact wording is the author's under ruling 17.

(4) Do not add the editor's two-environment build case to §6. If (i) lands, the CI plan's package test compares `isabelle getenv -b ISABELLE_HOME_USER` for `-p X/a/env` and `-p X/b/env`; that needs no build.

**Judge: partially_confirmed → author_fixes_no_rereview.** All facts confirmed, and the problem is worse than stated:
- `isabelle process` loads another environment's heap without checking its sources (store.scala:357-360);
- two prefixes with the same basename already break today: two installs of a component with a ROOT give 'Duplicate session' (sessions.scala:869-872), and ~/.isabelle/Isabelle2025-2-conda-test_run_env lists 24 registrations;
- rev 3 dropped the consequence sentence that round 1's C26 judge required (REVIEW1:2291-2292; rev2:131-133), without saying so.

Refuted: 'decision 12.6 only suggests' is not a defect in itself. The `-conda-<basename>` suffix is a packaging edit that ruling 20 keeps, so changing it needs the owner (Q6).

Author:
- Restore and extend the consequence sentence at plan:151: what is shared, rebuilds at every switch, silent loading of the other environment's heap, the rm -rf by either environment, and that the problem predates this plan.
- Decision 12.6 names both alternatives:
  - (i) a hash of the resolved prefix appended to the suffix, which keeps the pre-unlink guard working and leaves nothing behind on update;
  - (ii) a documented limitation, also added to decision 14's README list.
- Qualify 'this environment's user directory' at plan:367, :549-550 and :561.
- Add the round-1 C26 row to §10.
- Do not add a §6 build case. If (i) lands, the CI plan's package test compares `getenv -b ISABELLE_HOME_USER` for two prefixes.

### C26 [minor] The README lists leave out facts users need to stay safe: conda only (micromamba leaves invisible patches on removal), how to keep lower packages, the channel banner's conflicting update command, the feature-package README content round 2 required, and light's session

Section: Decision 14 README list (plan:447-452); decision 10 share/doc README (plan:382); decision 12; §2.3 (plan:173)  ·  merged from: user-U6, consistency-CONS-13

**Statement.** Decision 14's README list (plan:447-452) and decision 10's feature-package README (plan:382, content unspecified) omit:
(1) That only conda is supported, and why. micromamba runs post-link but not pre-unlink (plan:173), so `micromamba remove isabelle-light-locale` leaves light's patches in the tree with no feature package, invisible to status; pixi runs no link scripts at all. Yet the channel's own docs treat micromamba as an install client (RELEASE_CHECKLIST.md:383, :589). mamba 2.x shares libmamba with micromamba (unverified).
(2) How to make a lower package explicitly requested. Measured: `conda install --force-reinstall <pkg>` adds it to the history specs, and a later removal of the top package keeps it, at the cost of reversing and re-applying that feature and everything above it (review-ipc3/critic-user/run3.out T4 and following).
(3) The channel banner tells users to run `conda update -c https://conda.qiyuan.me -c conda-forge isabelle-ai` (conda/channel-banner.html:10). That does not move isabelle to a new build, while the plan's update command is `conda update --all`; decision 12 does not ask the CI plan to align the banner.
(4) Round 2's C14 judge required the feature-package README, not only the tool README, to document pruning, --force, and that reinstalling an installed package does not mark it as requested (REVIEW2:1937). Rev 3 puts this only in the tool README.
(5) light's README: the session name, `imports Light_Locale.Light_Locale`, and that the registration is per environment (C1, C25).
(6) Why `conda update isabelle` answers 'All requested packages already installed' while a new build is listed, and why an explicit install of that build conflicts until the feature packages are re-released.
(7) The recovery after an interrupted transaction (C11).

**Editor.** Wording is delegated to the author (ruling 17, plan:66-67), but these are missing facts, not wording. Severity is minor, not the critic's 'major'.

**Relaxation proposed by the editor.** Extend decision 14's list and decision 10's feature-package README with items (1)-(7), using the measured command for (2). Add to decision 12 that the CI plan updates channel-banner.html with the update command for environments that hold feature packages, and states that only conda is supported. Mark the mamba 2.x behaviour as unverified, or measure it.

**Defender: partially_confirmed** (needs owner: False).

Short version: some of C26 holds and some does not. Three of its seven items are confirmed. The other four are refuted or belong to other challenges. Severity "minor" is right.

CONFIRMED
(4) The plan silently skips a round-2 judge action. Round 2's C14 judge required two READMEs to document pruning, `conda remove --force`, and that installing an already-installed package does not mark it as requested: the feature-package README and the tool README (REVIEW2:1937, from the defender's fix 5 at :1920). Rev 3 has that paragraph only in the tool README (plan:451-452). Decision 10 names the file `share/doc/<包名>/README.md` (plan:382), but nowhere says what goes in it or where it comes from. The renderer's job list (plan:385-387) leaves it out too. The §10 row for C14 says only "决定 14 README" (plan:677) and does not admit the deviation.
(1) The plan never tells users that only conda is supported. Ruling 17 decided "conda only" (plan:67), and §2.3 and §9 record that micromamba skips pre-unlink and pixi skips link scripts (plan:173, :652). But neither decision 14's README list (plan:447-452) nor any feature-package text tells users. The 0.x section's "新工具只在 conda 里" (plan:450-451) is about pip, not about other conda front ends. Round 2 measured micromamba 2.8.1: it ran post-link and printed nothing for pre-unlink (review-ipc2/defender-C26/mamba/run.out). So `micromamba remove isabelle-light-locale` leaves light's changes in `$PREFIX/isa` and deletes features.d, after which status reports nothing. mamba 2.x is missing from both lists (plan:173, :652). Static evidence says it behaves the same: `strings` on pkgs/libmamba-2.8.1-hd28c85e_0/lib/libmamba.so.4.0.1 (and on micromamba-2.8.1-0/bin/micromamba) finds "pre-link", "post-link" and "mamba does not support pre-link scripts", and no "pre-unlink" string at all. I did not run mamba itself, because it is not in the local cache. The critic's supporting citations RELEASE_CHECKLIST.md:383 and :589 are weak. They are maintainer notes about the semantic-data package, not user instructions for feature packages. The real exposure is mamba 2.x as a common client.
(5) light's user-facing README is missing. The component payload ships light's README.md (plan:384). That file (contrib/light_locale/README.md:1-22) is developer-only. It never names the session `Light_Locale` (ROOT:4) or `imports Light_Locale.Light_Locale`, although §6 (a) relies on exactly that import (plan:590). Decision 13 gives the two new repositories detailed README contents (plan:434, :438), but for light it adds only component_files.txt (plan:440). The part of item (5) saying the registration is per environment depends on how C1/C25 resolve.

REFUTED OR MOSTLY REFUTED
(2) Keeping the lower packages is already covered. The README list includes `conda remove --force` (plan:451). I measured it (run.out, case B). After `conda remove --force fc`, only fc is removed. The left-over packages fa, fb and the tool are dependencies that no requested package needs any more. They survive a later `conda remove rpc` and a later `conda update --all`. I also reproduced the critic's extra route (runA.out). `conda install --force-reinstall fa` adds 'fa' to the history specs, and a later `conda remove fc` keeps fa and the tool. The cost is "reversed: fc, fb, fa" then "applied: fa, fb, fc", with two heap notices. Plain `conda install fa` and `conda install fa==1=<build>` print "All requested packages already installed" and do not add fa to the history specs (run.out case C; critic run3.out T4). What remains is a precision point in the wording, which ruling 17 delegates to the author: "再装一遍已装的包" must not read as covering `--force-reinstall`, which does mark the package as requested.
(3) The channel banner. Its command `conda update ... isabelle-ai` (channel-banner.html:10) addresses isabelle-ai users. It leaves isabelle on its current build, for users with feature packages and without them alike, and that behaviour predates this plan. Nothing breaks, so this is not a safety fact. Aligning the banner is optional, and the place for it would be decision 12 point 8 (plan:426-427).
(6) The action is already documented: the README's update command is `conda update --all` (plan:84, :452). Explaining why `conda update isabelle` does nothing, and why an explicit install conflicts during the short window before the batch re-release, is optional wording.
(7) Recovery after an interrupted transaction is C11's substance. critic-user/run4.out shows that the appendix A recovery fails with DirectoryNotACondaEnvironmentError. The README should carry whatever recovery C11's fix produces. It should not be counted again here.

ON THE EDITOR'S RELAXATION
Adding all seven items to two hand-written lists would create two texts that drift apart. A better shape follows the hook fragment's model: one text owned by the tool repository, copied verbatim by the renderer. With it, each feature package's README and the tool README cannot disagree. Asking people to keep two lists in step does not give that guarantee.

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C26/

Setup: conda 25.11.1 with the libmamba solver, private HOME/CONDARC/CONDA_PKGS_DIRS/CONDA_ENVS_DIRS, and a toy file:// channel. The channel generator is a copy of critic-user/mkchan3.py, read in full before use, saved as mkchan.py. It provides: isa build 1 (the pristine build, whose post-link carries decision 9's hook fragment), a toy tool, the chain fa < fb < fc pinned to 'isa 2025.2 1', and rpc, a toy component package.

run.sh, output in run.out:
- Case A. Env created with 'isa fc'. `conda install --force-reinstall fa` adds "# update specs: ['fa']" to the history. A later `conda remove fc` removes only fb and fc; fa and the tool stay.
- Case B. Env created with 'isa fc rpc'. `conda remove --force fc` removes only fc. A later `conda remove rpc` and a later `conda update --all` leave fa, fb and the tool in place, and the tree keeps A2/B2/D2.
- Case C. `conda install "fa==1=Isabelle2025_2_1_0"` prints "All requested packages already installed", and the history is unchanged.

runA.sh, output in runA.out: the raw output of case A. The tool printed "changed (reversed: fc, fb, fa)" and then "changed (applied: fa, fb, fc)".

Static check: `strings` on /home/qiyuan/miniconda3/pkgs/libmamba-2.8.1-hd28c85e_0/lib/libmamba.so.4.0.1 and on micromamba-2.8.1-0/bin/micromamba. Both contain "pre-link", "post-link" and "mamba does not support pre-link scripts", and neither contains "pre-unlink".

Re-read as evidence:
- review-ipc2/defender-C26/mamba/run.out: micromamba 2.8.1 ran post-link and no pre-unlink.
- critic-user/run3.out T4, run4.out (the interrupted transaction ends with DirectoryNotACondaEnvironmentError), and run6.out (pruning).

Sources read: contrib/light_locale/{README.md,ROOT,Light_Locale.thy}, isabelle-packaging-ci/conda/channel-banner.html, RELEASE_CHECKLIST.md:375-392 and :580-595, conda/metapackage/isabelle-ai/recipe.yaml, conda_libmamba_solver/solver.py:558-582, and REVIEW2 C14 (:1831-1937) and C11 (judge action).

Recommended fix: These are the smallest edits. All of them are wording or documentation and fall within ruling 17.

1. Decision 10 (plan:382, :385-387): the renderer writes `share/doc/<包名>/README.md` itself. The file starts with one text owned by the tool repository and copied verbatim, the way the hook fragment is copied. The feature repository's README.md follows it. Decision 14's README paragraph (plan:451-452) embeds the same text. The shared text says:
   (a) Removing a feature package also removes the lower feature packages that were installed only as dependencies, and the tool, and reverses them.
   (b) `conda remove --force <top package>` removes only that package.
   (c) `conda install <pkg>` on an installed package does not mark it as requested. `conda install --force-reinstall <pkg>` does, at the cost of reversing and re-applying that feature and every feature above it.
   (d) The update command is `conda update --all`; `conda update isabelle` on its own changes nothing.
   (e) Only conda is supported. mamba 2.x and micromamba run no pre-unlink, and pixi runs no link scripts, so removing a feature package with them leaves its changes in `$PREFIX/isa`, where status can no longer see them. Restore with `conda install --force-reinstall isabelle`.
   If C11 produces a recovery procedure for an interrupted transaction, it goes into this text too.
2. §2.3 (plan:173) and §9 (plan:652): name mamba 2.x next to micromamba. Cite libmamba 2.8.1, which has no pre-unlink code path ("pre-unlink" is absent from the strings of libmamba.so.4.0.1), and mark it as not run.
3. Decision 13 (plan:440): light's README gains a user section that gives the session `Light_Locale` and `imports Light_Locale.Light_Locale`. Add the scope of the component registration once C1/C25 settle it.
4. §10, row C14 (plan:677): add "the feature-package README via decision 10's rendered text".
Optional: decision 12 point 8 also updates conda/channel-banner.html with the update command and the conda-only note. This is not a safety fact.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- (1) conda-only is never told to users. mamba 2.x is also missing from §2.3 and §9; libmamba 2.8.1 has no pre-unlink code path ('pre-unlink' is absent from its strings; not run).
- (4) the feature-package README content that the round-2 C14 judge required (REVIEW2:1937) was silently dropped.
- (5) light's README never names the Light_Locale session or its import.

Refuted or covered elsewhere:
- (2) is covered by `conda remove --force` (defender-C26/run.out case B);
- (3) is optional;
- (6) is optional;
- (7) belongs to C11.

Author:
- The renderer writes share/doc/<pkg>/README.md starting with ONE text owned by the tool repository and copied verbatim, the same text decision 14's README embeds. It covers:
  - pruning;
  - `conda remove --force`;
  - plain `conda install` of an installed package does not mark it as requested, while `--force-reinstall` does, at the cost of reversing and re-applying;
  - the update command is `conda update --all`;
  - only conda is supported: mamba 2.x, micromamba and pixi leave a removed feature's changes in the tree; restore with the C1-amended force-reinstall;
  - C11's recovery.
- Name mamba 2.x at plan:173 and :652.
- Decision 13 gives light's README a user section: session Light_Locale, `imports Light_Locale.Light_Locale`, and the registration scope (C1/C25).
- Amend §10's C14 row.

### C27 [minor] Several user-visible texts are unspecified or misleading, and two round-2 text actions (the 0.x pointer and always printing the tree) were dropped without saying so

Section: §4 (plan:530-563); decision 9 fragment (plan:340, :342); decision 2 (plan:236); decision 14 (plan:451)  ·  merged from: user-U11, consistency-CONS-13

**Statement.** (1) The heap-notice example '(applied: light_locale)' (plan:532) does not define the list format when one hook applies three features.
(2) A partial reversal, for example removing light while the lower features stay applied, fits neither notice: the reversal text is defined for 'back to the package's original state' (plan:536).
(3) '$PREFIX/isa is Isabelle2025-2 build 5533cd83156e' (plan:543) calls an hg changeset a 'build'; users know that build as conda's 2025.2-0.
(4) The CONFLICT remedy 'If you edited that file: conda install --force-reinstall isabelle' (plan:549-550) does not say to save the edit first, although the reinstall overwrites the edited file. The residue text does say it (plan:560).
(5) The fragment's elif line says the tool is not installed but gives no command. Its || line suggests status and apply, which fail the same way when the tool cannot start (plan:340, :342). The remedy is `conda install --force-reinstall isabelle-patch-control`.
(6) Round 2's C23 judge and round 1 required the CONFLICT message to end with a pointer to the 0.x section (REVIEW2:2847, :2907; REVIEW1:2106-2110). Decision 14 says '失败报文指向这一节' (the failure message points to this section, plan:451), but §4's CONFLICT text has no pointer.
(7) Round 2's C18 judge required status, apply and unapply to print the tree and the features.d they read (REVIEW2 C18 Changes, '§4: status, apply and unapply print the tree and the features.d they read'). Rev 3 prints them only under -v (plan:236), with no reason given.

**Editor.** Wording is the author's under ruling 17. (4) is the one item with real consequence (a lost user edit). (6) and (7) are dropped judge actions, which the author may override only if §10 says so.

**Relaxation proposed by the editor.** Fix each text: define the multi-feature list format; add a partial-reversal notice; write 'the isabelle build whose etc/ISABELLE_ID is 5533cd83156e (conda 2025.2-0)'; add 'save your own edits under $PREFIX/isa first' to the CONFLICT remedy; give both fragment messages a concrete conda command; add the 0.x pointer line. For (7), print the tree and features.d always, or record the deviation and its reason in §10. Apply C1's amendment to every --force-reinstall remedy.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the seven parts. Part (1) is refuted. Part (2) is narrowed to a label problem. Part (3) is confirmed only as a wording clash. Parts (4)-(7) survive. Severity minor is right.

(1) REFUTED. The list format for several features is a wording detail, and ruling 17 gives wording to the author (plan:17 item 17, :66-67). A comma-separated list is the obvious form. The hook-layer test asserts one applied line per transaction (plan:476), and that does not depend on the format. This is not a design gap.

(2) NARROWED. The trigger already covers a partial reversal: the notice prints after any apply or unapply that changed src/ (plan:530, :324, :361). The reversal text is also true after a partial reversal (plan:538-539). Heaps in the user directory are rebuilt, and the text claims nothing about the heaps shipped in the package. What is wrong is only the label "反打回包的原样之后" ("after reversing back to the package's original state", plan:536). It is narrower than the trigger. The common case, a pre-unlink that removes light while the lower features stay applied, therefore has no defined text. The ambiguity shows up in practice: the round-3 critic's prototype printed "(reversed: fc)" together with the applied text's sentence about stale shipped heaps (review-ipc3/critic-user/run6.out). Round 2's C17 judge said to drop the stale-heap sentence only when no feature above the chain bottom stays applied (REVIEW2:2133-2137 area). By that rule the sentence should stay for a partial reversal.

(3) CONFIRMED AS WORDING ONLY. plan:543-544 uses "build" twice in one message. "Isabelle2025-2 build 5533cd83156e" means an ISABELLE_ID. "the pristine isabelle build" means a conda package, as in the glossary (plan:20) and decision 10's build number (plan:378-380). Every pristine build has the same ISABELLE_ID 89701cf1768e, so "build <ID>" does not name a build. That breaks the one-term-per-concept rule. I reject the editor's "(conda 2025.2-0)": the tool cannot compute it. Ruling 22 deleted the LEGACY table (plan:82), and §9 declines reading conda-meta internals (plan:650-651). Hard-coding the mapping would bring the deleted table back.

(4) CONFIRMED, and worse than stated. I ran a toy conda 25.11.1 channel (defender-C27/run.out). An edit by `sed -i`, which writes a new file, was overwritten by `conda install --force-reinstall`. So the CONFLICT remedy (plan:549-550) loses the user's edit without the warning that the residue text gives (plan:560). The remedy also restores every package file under isa, not only "that file". A related point outside C27's statement: an edit written in place through the hard link changes the pkgs cache file itself. vim does this by default (backupcopy=auto keeps the inode of a hard-linked file; defender-C27/vimtest). `--force-reinstall` then does NOT restore the file:
- same size: silently kept;
- different size: a SafetyError warning, rc=0, the file still edited (rerun.out).
conda checks only the size unless extra_safety_checks is on (conda/core/path_actions.py:464, :485; context.py:294-295, where safety_checks defaults to warn). So "restores the package's files" (plan:549, :560, :367) is false for in-place edits. The judge should route this point.

(5) CONFIRMED. The `||` line (plan:340) fires only when the tool exits non-zero. conda-hook always exits 0 (plan:360, :528), so non-zero means start-up failure, the case decision 15 tests (plan:482). Its advice, status and apply, fails the same way. The elif line (plan:342) gives no command. The editor's remedy is incomplete: the tool package has no post-link of its own (plan:211-212; hooks belong only to feature packages, plan:382), so reinstalling it applies nothing. `isabelle-patch-control apply` must follow.

(6) CONFIRMED. Decision 14 says "失败报文指向这一节" ("the failure messages point to this section", plan:451), and §10 marks C23 as done (plan:686). No §4 text has the pointer: grep finds "help" and "0.x" only at plan:143, :218, :447-451, :523 and :686. Both judges required it (REVIEW1:2110; REVIEW2:2847, :2907). Ruling 22 does not make it moot:
- decision 14 itself expects 0.x-patched trees (plan:448-449);
- 0.3.0 still runs on the pristine build;
- its show_types_nv changes syntax_phases.ML (patches/Isabelle2025-2/show_types_nv/syntax_phases.ML.patch), which light also changes;
- that gives exactly the CONFLICT whose first remedy line ("If you edited that file") does not describe these users.

(7) CONFIRMED as a deviation §10 does not record, with little substance. Both judges required status, apply and unapply to print the paths they read (REVIEW1:2005; REVIEW2:2413). Rev 3 prints them only under -v (plan:236, :311), and "no feature packages installed" names no path (plan:228, :251). The §10 row for C18 lists only the one prefix P (plan:682). That one-prefix rule removes the cross-environment mismatch that motivated the judges, so -v is a defensible wording choice under ruling 17. But the author must say so in §10.

The editor's "apply C1's amendment" is a sound consistency step if C1 stands. defender-C1/run-orig-0.out shows `--force-reinstall isa` deleting the component registrations. The same bare remedy appears at plan:367, :450, :549 and :560.

Outside C27 (for the judge): decision 3 says the tool never knows the pristine changeset (plan:245-246), and plan:228 and :251 say that with no features.d the result is "no feature packages installed", exit 0. Yet §6 (i) (plan:598) expects exit 3 with `conda update --all` on a 2025.2-0 environment that has only the tool. The message at plan:543 cannot be produced in that case.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C27/

(a) mkchan.py builds a toy noarch package `isa` (isa/src/a.ML, isa/src/b.ML, hardlink path type). run.sh uses conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS. Output is in run.out and rerun.out.
- After create, both env files are hard links into pkgs (link count 2).
- `sed -i` on a.ML makes a new inode. `--force-reinstall isa` restored a.ML, so the user's edit was lost.
- A same-size edit written in place on b.ML changed the pkgs cache copy as well. `--force-reinstall` kept the edit and printed nothing.
- A size-changing edit written in place gave "SafetyError ... has an incorrect size". The transaction still executed with rc=0, and b.ML stayed edited.
- `conda config --show` reports safety_checks: warn and extra_safety_checks: False.

(b) vimtest/: `vim -u NONE -N -es` (backupcopy=auto) edited one name of a two-link file. The inode was kept and the other link showed the edit.

(c) Read-only greps of the plan:
- "help", "0.x" and "Coming from" appear only at plan:143, :218, :447-451, :523 and :686, so no §4 text has the pointer;
- the -v-only path printing is at plan:236 and :311;
- §10 rows: C18 at plan:682, C23 at plan:686.

(d) Judge requirements: REVIEW1:2005 and :2110; REVIEW2:2413, :2847 and :2907.

(e) conda source: core/path_actions.py:464 and :485; base/context.py:294-295.

(f) The 0.x patch set at my_better_isabelle_prover/patches/Isabelle2025-2 creates no files, and show_types_nv patches syntax_phases.ML.

(g) The critic prototype mixing the two heap notices: review-ipc3/critic-user/run6.out.

Recommended fix: The smallest set of fixes, all author work under ruling 17.

(2) Relabel the second heap notice "反打之后" ("after a reversal"). Add one rule: when some feature above the chain bottom is still applied after the run, keep the sentence "The heaps shipped with the isabelle package no longer match them", as round 2's C17 judge said. Better still, use one template with "(applied: …)" or "(reversed: …)" and make that sentence depend on the end state, not on the action.

(3) Avoid "build <ID>". Write: "$PREFIX/isa has etc/ISABELLE_ID 5533cd83156e; the installed feature packages need the isabelle build whose etc/ISABELLE_ID is 89701cf1768e (their base_tag). Run: conda update --all". Do not add "(conda 2025.2-0)": the tool cannot compute it without the LEGACY table that ruling 22 deleted.

(4) Start the CONFLICT remedy with "save your own edits under $PREFIX/isa (the reinstall replaces every file of the package, not only this one); then …", to match plan:560. Separately, decide what to do about in-place edits through the hard link, which `--force-reinstall` does not undo (defender-C27/run.out): at least drop the unconditional "restores the package's files", or name a real recovery.

(5) The `||` line: "if `isabelle-patch-control status` also fails: conda install --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply". The elif line: "Run: conda install isabelle-patch-control; then: isabelle-patch-control apply". The second command is needed because the tool package has no post-link.

(6) End the CONFLICT text in §4 (and, if wanted, the chain-broken text) with: "Patched with my-better-isabelle 0.x before? See: isabelle-patch-control help, section 'Coming from my-better-isabelle 0.x'". The other route is to delete "失败报文指向这一节" at plan:451 and record the deviation in §10.

(7) Either print one header line with the tree and the features.d root by default (also in "no feature packages installed"), or add to §10's C18 row that the paths are printed only under -v, and why: with one prefix P, the tree and features.d can no longer come from two environments.

(1) Needs no change. Apply C1's amendment, if confirmed, at plan:367, :450, :549 and :560 alike.

**Judge: partially_confirmed → author_fixes_no_rereview.** (1) is refuted: the list format is wording. (2) narrows to a label problem, and (3) to wording. (4)-(7) are confirmed.

(4) is worse than stated, and the judge checked defender-C27/run.out.
- An edit written in place through the hard link changes the package cache too. vim's backupcopy=auto keeps the inode of a hard-linked file, so vim edits this way.
- `--force-reinstall isabelle` then leaves the edit in place: silently when the size is unchanged, and with only a SafetyError warning and rc=0 when it changed.
- So 'restores the package's files' (plan:367, :549, :560) is false in that case.

Author:
- (2) One heap-notice template with 'applied: …' or 'reversed: …'. The 'shipped heaps no longer match' sentence depends on the end state: it is kept while any feature above the chain bottom stays applied.
- (3) Write 'has etc/ISABELLE_ID 5533cd83156e', not 'build'. Do not add '(conda 2025.2-0)': the tool cannot compute it without the deleted LEGACY table.
- (4) The CONFLICT remedy starts with 'save your own edits (the reinstall replaces every file of the package)'. Measure and state a real recovery for in-place edits, for example removing the extracted pkgs/isabelle-<b>/ directory so conda re-extracts it from the .conda archive before --force-reinstall, or state the limitation.
- (5) The `||` line gives `conda install --force-reinstall isabelle-patch-control` and then `isabelle-patch-control apply`. The elif line gives `conda install isabelle-patch-control` and then apply, because the tool package has no post-link.
- (6) Add the 0.x pointer line to the CONFLICT text, or delete plan:451's '失败报文指向这一节' and record the deviation.
- (7) Print the tree and features.d always, or record in §10's C18 row why -v suffices.
- Apply C1's amendment to every force-reinstall remedy.

### C28 [minor] Release procedure gaps: secrets are seeded only at step 8 though earlier dry runs name them, nothing keeps step 8 from racing release.yml's publication in step 6, and the release freeze sits in step 6 although the judge asked for it now

Section: §5 steps 5-8 (plan:578-583); decision 11 (plan:402, :407-408); decision 12.5 (plan:421); §2.3 (plan:178-180)  ·  merged from: landing-L12, consistency-CONS-11, consistency-CONS-13

**Statement.** (1) The publish jobs pass both R2 secrets explicitly (plan:402). Naming them re-arms `required: true`, so an unseeded repository fails at workflow resolution with a named error (RELEASE_CHECKLIST.md:299-301; Isabelle_RPC release-conda.yml:324-330). For permissions, the checklist records that a called workflow's requirements are validated while the run is built, before any `if:` (RELEASE_CHECKLIST.md:320-322). So the publish=false runs of steps 5 and 7 plausibly fail to start until step 8 seeds the secrets (plan:582). Not measured on GitHub.

(2) Step 6 publishes isabelle from isabelle-packaging-ci, and step 8 publishes the batch from the tool repository. publish-conda.yml cannot see an overlap between two repositories (publish-conda.yml:29-43; the round-2 C13 replay). §2.3 says publishers check that no other repository is publishing (plan:179-180), but in fact only the sweep script gates on PUBLISH_REPOS (sweep-old-versions.py:59-69, :208-237), and no step of the plan performs that check.

(3) Round 2's C26 (10) judge asked to record the release freeze in isabelle-packaging-ci/RELEASE.md now, as a §5 step 0 or a decision-11 item (REVIEW2:3189, :3202). Decision 12.5 says '现在就（按用户命令）' (right now, on the owner's order; plan:421), but §5 puts it in step 6 (plan:579), and RELEASE.md contains no freeze today (grep for freeze/冻结 finds nothing).

**Editor.** L12's third point, that the workflow's name must match the sweep's PUBLISH_WORKFLOW_RE, is dropped. The file is release-features.yml, and when a workflow has no name:, GitHub names its runs by the file path, which matches 'release' (sweep-old-versions.py:70).

The freeze's hazard is smaller after ruling 22: feature packages pin the pristine build, so a stray isabelle build can never become their base. (3) is therefore a scheduling inconsistency, not a live risk.

**Relaxation proposed by the editor.** Seed both R2 secrets and the read token at step 5, before the first dispatch. Start step 8 only when release.yml's publish and smoke jobs have finished and no run is in flight across PUBLISH_REPOS (using the sweep's gate, or gh run list). Correct §2.3 to state PUBLISH_REPOS's real role: it keeps sweeps out of a running publish. Move the freeze to §5 step 0.

**Defender: partially_confirmed** (needs owner: False).

Part (1), secrets seeded too late: plausible and unrefuted, but not measured. Decision 11 passes both R2 secrets explicitly to publish-conda.yml (plan:401-402). That workflow declares both secrets `required: true` (publish-conda.yml:58-62). The channel's own recorded rule says that passing them by name "re-arms `required: true`, so an unseeded repo fails at resolution with a named error" (RELEASE_CHECKLIST.md:299-301; release.yml:61-63; Isabelle_RPC release-conda.yml:324-330). The same checklist says that resolution happens "while the run is built, before any `if:`", at least for permissions (RELEASE_CHECKLIST.md:320-322). The plan seeds the secrets only at step 8 (plan:407, :582). The `publish=false` dispatches come earlier: step 7 runs the five-leg acceptance on GitHub (plan:581), and step 5 may dispatch too (plan:578). If the channel's model is right, step 7 dies with startup_failure. I could not settle GitHub's behaviour with a skipped calling job. A web search turned up the error text "Secret X is required, but not provided while calling" on runs where the secret is empty (actions/runner#2709, which includes Dependabot cases), but no source covers the case where the calling job's `if:` is false. There is no local evidence either: every repo that has a dry_run input had its secrets before that input was added (git log: ae739f6, d84a56a). The failure would be loud and easy to fix. Still, the plan's own convention predicts it, and avoiding it costs nothing. The private-repo read token has the same gap: decision 11 needs it on every dispatch (plan:399), but no step in §5 sets it.

Part (2), a race between step 8 and release.yml: the hazard is REFUTED; the §2.3 sentence is CONFIRMED wrong.
- Why the race cannot happen. Every run of the batch workflow, including the publish=true run, first resolves `isabelle 2025.2 <isabelle_build>` from the live channel and runs §6 on it, before any publish job (plan:400-401). The live repodata can name that build only after release.yml's publish job has pushed its index (publish-conda.yml:229-236). Nothing in release.yml writes to R2 after that push. The only R2 writes are at publish-conda.yml:200 and :234; the verify and audit steps (:238-345) only read, and so does the smoke job (release.yml:84-132). The batch's first upload is therefore causally after release.yml's last write. That ordering comes from a data dependency, not from discipline. Step 7, which requires the already-published build (plan:581), also sits in between.
- Leftovers. Only two cases remain: a re-run of release.yml's publish job, and the general cross-repo race with some unrelated repo's release. Round 2's judge confirmed that this race can hide a package while both runs stay green (REVIEW2:1817-1827).
- The wrong sentence. On that general race, §2.3 is factually wrong: it says publishers check, before publishing, that no other repo is publishing (plan:179-180). Only the sweep checks. `gate_no_publish_running` is called only from `cmd_execute` (sweep-old-versions.py:232-237, :492, :528). publish-conda.yml has no such gate and says GitHub cannot serialise across repos (:29-43). No §5 step performs the check the sentence implies.
- On the relaxation. Its "wait for release.yml's smoke" clause is unnecessary: smoke only reads.

Part (3), the release freeze: CONFIRMED, but only as a placement inconsistency.
- The plan does say what round 2's confirmed action asked: "现在就（按用户命令）" (right now, on the owner's order), recorded in RELEASE.md (plan:421; REVIEW2:3202).
- But the item sits in decision 12, the list of requirements for the CI plan, and in §5 step 6, the CI-plan step (plan:579). Structurally that is "through the CI plan", which the judge ruled out. The plan also ignores the judge's suggested home, step 0 (REVIEW2:3189), and §10 does not say so: the C26 row has no freeze entry (plan:689), and the "冻结" (freeze) in the rev-1 row maps to decision 1, which is the 1.x interface freeze (plan:690).
- RELEASE.md has no freeze today (grep for freeze, frozen and 冻结 finds nothing). That is expected while the owner has given no order, so it is not a defect by itself.
- The editor's rebuttal is right that there is no live risk. Decision 12.5's own justification, that feature packages would pin a patched build and every user would get exit 3 (plan:421-422), has been overtaken. Under ruling 22 the operator picks the pin (plan:395), and §6 (a) would turn red with exit 3 on a non-pristine build before anything is published (plan:589; decision 3.2, plan:247-249).

Experiment: I created /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C28/. No toy experiment applies: the disputed behaviour is GitHub's server-side workflow resolution, which cannot be reproduced locally. What I did instead:
- Source reads:
  - publish-conda.yml:8-26 and :58-62 (required secrets); :125-130 (a runtime empty-credential check); :193-236 (the only R2 writes, at :200 and :234); :238-345 (read-only verify and audit).
  - release.yml:54-66 (the publish job) and :84-132 (the read-only smoke job).
  - sweep-old-versions.py:59-70, :211-237, :492, :528 (the PUBLISH_REPOS gate is used only by `execute`).
  - RELEASE_CHECKLIST.md:152-174, :299-301, :320-322, :666.
  - Isabelle_RPC release-conda.yml:311-333.
- Greps:
  - RELEASE.md, RELEASE_CHECKLIST.md and PACKAGING_DESIGN.md for freeze, frozen and 冻结: nothing found.
  - The plan for 密钥 (secret key), secret, token, PUBLISH_REPOS and 冻结 (freeze): secrets appear only at :101, :178, :399, :402, :407 and :582; the freeze at :421 and :579; §10 has no freeze row for C26.
- git log --grep across the six publishing repos: no recorded dry run on a repo without secrets.
- Review cross-check: REVIEW2:1741-1827 (C13 judge) and :3189 and :3202 (C26 (10)).
- Web search for GitHub's "Secret X is required, but not provided while calling": the error is reported when the passed secret is empty (actions/runner#2709, which includes Dependabot cases). No source says whether a calling job whose `if:` is false avoids it. That question is still open.

Recommended fix: Three hand edits, all author-level:
(1) §5 step 5 (plan:578), before the first dispatch:
- Add "用户下令：工具仓库 `gh secret set` 两个 R2 密钥与只读 token，进 `PUBLISH_REPOS` 与 `RELEASE_CHECKLIST.md:172` 的清单" (on the owner's order: set the two R2 secrets and the read-only token on the tool repository, and add it to `PUBLISH_REPOS` and to the list at `RELEASE_CHECKLIST.md:172`).
- Remove the same items from step 8 (plan:582) and decision 11 (plan:407).
- Keep the secrets and PUBLISH_REPOS in the same step. PUBLISH_REPOS is defined as "every repo whose CI can write to the channel" (sweep-old-versions.py:59-60), so the step that gives the tool repo write access must also register it.
(2) Fix §2.3 (plan:179-180) to say: PUBLISH_REPOS lets the sweep refuse to run while any publish-shaped run is in flight. Publishers do not check, and GitHub cannot serialise runs across repositories (publish-conda.yml:29-43).
- Add one precondition to step 8: release.yml's run is green, including its "audited N subdir(s)" line, and `gh run list` shows no release/publish run in flight across PUBLISH_REPOS (the same query as sweep-old-versions.py:211-229).
- Do not add a wait for release.yml's smoke job. It only reads, and the batch's own resolution of the live isabelle build already orders it after release.yml's last write.
(3) Move "记下发布冻结" (record the release freeze) into §5 step 0 (plan:567) and delete it from step 6 (plan:579). Either move decision 12.5 out of the CI-plan requirements or say there that it runs before the CI plan.
- Restate its reason as ruling 11 itself: §6 (a) would already turn red on a patched pin, so the freeze is no longer a safety rule.
- Add the freeze to §10's C26 row.

**Judge: partially_confirmed → author_fixes_no_rereview.** (1) is plausible and not measured. RELEASE_CHECKLIST.md:299-301 and :320-322 predict that a publish=false run fails at resolution when the secrets passed by name are unseeded. The read token has the same gap.

(2) is refuted as a hazard. The batch's §6 run resolves the isabelle build from the live repodata, which exists only after release.yml's index push. release.yml's later steps only read (publish-conda.yml:238-345; release.yml:84-132). But §2.3's sentence that publishers check that no other repository is publishing (plan:179-180) is false: only the sweep gates on PUBLISH_REPOS (sweep-old-versions.py:232-237, :492, :528).

(3) is confirmed as placement: decision 12.5 says 'now', but it sits in the CI-plan requirements and in step 6.

Author:
- Seed both R2 secrets and the read token, and add the tool repository to PUBLISH_REPOS and RELEASE_CHECKLIST.md:172, at §5 step 5 before the first dispatch, on the owner's order. Remove these items from step 8 and decision 11 (plan:407, :582).
- Correct §2.3 to say what PUBLISH_REPOS really does.
- Add a precondition to step 8: release.yml green including its audit line, and no publish run in flight across PUBLISH_REPOS (the sweep's query at sweep-old-versions.py:211-229). No wait for release.yml's smoke job.
- Move the freeze to §5 step 0. Restate its reason (under ruling 22 it is no longer a safety rule), and add it to §10's C26 row.

### C29 [minor] Stale or wrong facts: the existing component hooks do not report through .messages.txt; the package cache holds a second build whose ISABELLE_ID is the official changeset although it carries expose_foreign; §7 row (7) marks the plan's own choice as an owner ruling

Section: §2.3 (plan:148, :170-172); decision 9 (plan:353-354); glossary (plan:20); §7 row (7) (plan:614)  ·  merged from: consistency-CONS-11, consistency-CONS-13

**Statement.** (1) plan:170-172 says the channel's component hooks report through .messages.txt. Isabelle_RPC's .sh hook echoes its warning to stdout, which conda swallows, and its .bat is silent (Isabelle_RPC/conda/recipe.yaml:151-156, :166-175). RELEASE_CHECKLIST.md requires only exit 0. Decision 9 therefore labels its own improved line (with >> .messages.txt, plan:354) as 'RELEASE_CHECKLIST §4's registration line'.

(2) plan:148 says the package cache holds only isabelle-2025.2-0. Verified here: it also holds isabelle-2025.2-89701cf1768e_0 (~/miniconda3/pkgs/isabelle-2025.2-89701cf1768e_0/info/index.json, build '89701cf1768e_0'). Its etc/ISABELLE_ID is the official 89701cf1768e, while its src/Pure/ML/ml_name_space.ML:67 reads `hidden_structures = ["Signal"]`, that is, with expose_foreign applied; the official tarball has `["CInterface", "Foreign", "RunCall", "Signal"]`. That build is not on the live channel (repodata snapshot), but it shows that an ISABELLE_ID equal to the official changeset has already labelled a patched build. So the glossary's identity rule (plan:20) rests on CI discipline alone (decision 12.1).

(3) §7 row (7) marks (b2)'s base as '已裁定' (ruled, plan:614). Migration §5.1 rules that (b2) uses the published conda isabelle build (ISABELLE_GIT_MIGRATION_PLAN.md:409). Using the official tarball before that build exists is decision 17's own choice.

**Editor.** CONS-11's item (d) is merged into C10; item (a) into C28. Items (e) (155 against 154 characters, and the unexplained 198) and (f) (the dates of the two corrections) are dropped as nitpicks: the make-patches gate computes path lengths itself (plan:494-495), and the dates affect no decision.

**Relaxation proposed by the editor.** Correct the three statements by hand: describe the existing component hooks accurately and present the .messages.txt redirection as the plan's own improvement; mention the second cached build and that ISABELLE_ID alone proves nothing (optionally ask in decision 12.1 for a CI assertion that the packaged src/ equals the official tarball's); mark §7 row (7) as '本计划' (this plan).

**Defender: partially_confirmed** (needs owner: False).

All three factual errors hold. Only the side conclusion in part (2), that the identity rule "rests on CI discipline alone", goes too far.

(1) CONFIRMED. plan:170-172 says the component-hook convention "经 .messages.txt 说话" (reports through .messages.txt) and cites RELEASE_CHECKLIST.md:259. That line only says "Every hook ends `exit 0`. A nonzero post-link rolls the whole install back." RELEASE_CHECKLIST.md and PACKAGING_DESIGN.md never mention .messages.txt (grep finds nothing).
- Isabelle_RPC's .sh hook (Isabelle_RPC/conda/recipe.yaml:152-157) echoes its warning to stdout. auto_sledgehammer (:87-89), Performant_Isabelle_ML (:143-145), Semantic_Embedding (:267-270) and Isa-Mini (:252-254) do the same.
- conda captures hook stdout through a pipe (gateways/subprocess.py:100-113). When the hook succeeds it prints only .messages.txt and drops stdout (core/link.py:1684-1686, :1697-1708).
- The .bat runs `components` with `>nul 2>&1` and has no echo at all (Isabelle_RPC recipe.yaml:173-175).
- The one partial precedent is isabelle-nunchaku: it sends stderr to .messages.txt, but its warning echo still goes to stdout (components/isabelle-nunchaku/recipe.yaml:493-502).
- So the `>> "$PREFIX/.messages.txt"` at plan:354 is the plan's own improvement, not "RELEASE_CHECKLIST.md §4 的登记行" (§4's registration line). §4 contains no echo line at all (RELEASE_CHECKLIST.md:250-268).
- There is a knock-on gap. plan:355 describes the Windows registration only as warm-up plus /cygdrive/ conversion. Copied from the convention, light's .bat registration failure would therefore stay silent while the .sh reports it. The plan does not say which one it wants.

(2) The plan:148 sentence is CONFIRMED wrong, and it is a regression. The cache also holds isabelle-2025.2-89701cf1768e_0:
- index.json gives build 89701cf1768e_0, linux-64.
- repodata_record.json gives the channel file:///home/qiyuan/ci-work/channel/linux-64, a local channel.
- Its tree is opt/Isabelle2025-2/, with no isa/.
- etc/ISABELLE_ID is 89701cf1768e.
- src/Pure/ML/ml_name_space.ML:67 is `["Signal"]`, while the official tarball (sha a20a507b…) has `["CInterface", "Foreign", "RunCall", "Signal"]`.

The round-1 judge ordered exactly these facts recorded (REVIEW1:1226-1230), and rev 2 had them (PLAN.rev2.md:128-130). Rev 3 dropped that paragraph, rightly so since the LEGACY record is gone under ruling 22, but replaced it with a false sentence, and §10 does not mention it.

Operationally the build is harmless. It has no isa/, so the tool's tree P/isa does not exist there. Its build string 89701cf1768e_0 cannot satisfy any feature package's exact pin `isabelle 2025.2 <build string>` (decision 10).

The conclusion "rests on CI discipline alone" is overstated. Decision 17's (b2) runs on a copy of the pristine build's isa/ (plan:503-504, §5 step 6 at :582, §6 at :588). Copy B uses `patch -p1 -F0`, which refuses a hunk that is already applied. I reproduced the case where a chain feature is pre-applied under the official ID: rc=1, "Reversed (or previously applied) patch detected … Skipping patch". The unapply-versus-original comparison would also fail. So the very failure the cached build shows (old-tool patches left in) is caught for every file the chain touches. Two things remain uncovered:
- edits to files outside the chain;
- the fact that (b2) is a local, self-attested step (`roundtrip_checked`, plan:401) rather than a check inside the CI that makes the isabelle package.

Decision 12.1's only stated identity check is "ISABELLE_ID == 89701cf1768e", and the cached patched build would pass it. An optional CI assertion that the packaged tree equals the official tarball apart from ruling 20's packaging edits remains worthwhile. It would make the plan:20 invariant mechanical, and it does not conflict with 12.1's "不需要树哈希断言" (no tree-hash assertion needed), which refers to the retired k-prefix assertion (migration :439-441, ruling 30).

(3) CONFIRMED. Row (7) is labelled "已裁定" (ruled) (plan:614). Two of its three parts are ruled: gate (c) on the base tag's archive (migration :392) and (b2) before each publication on "该发行版线已发布的 conda isabelle 构建" (the already-published conda isabelle build of that release line) (migration :409). The official tarball as the interim base is decision 17's own choice (plan:503-504). No ruling in migration §0 items 30-31 (:119-133) or in plan §0 items 11-25 covers it. Row (6) already shows how a mixed row should be labelled: "已裁定；本计划" (ruled; this plan).

Related: the round-2 judge required (b2) on "a copy of 2025.2-0 and on the CI's pristine conda build" (REVIEW2:1563). Rev 3 substitutes the official tarball for the 2025.2-0 copy. That substitution is forced: the tool exits 3 on ID 5533cd83156e (decision 3.2), so it cannot run on 2025.2-0. But the plan never says it is departing from that judge action.

On the editor's relaxation: it is right on the merits, with two refinements. Row (7) should read "已裁定；本计划", not bare "本计划". The fix for (1) should also say what the .bat registration line does on failure.

Severity minor is fair. No design invariant breaks; these are wrong statements an implementer might copy.

Experiment: Scratch: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C29/.

(a) hook/drive.py calls conda 25.11.1's own core.link.run_script, with a private HOME/CONDARC/CONDA_PKGS_DIRS, on a toy prefix whose fake isa/bin/isabelle exits 1. Two hooks were compared:
- the Isabelle_RPC-convention post-link, generated by the same printf text as recipe.yaml:152-157: returns True and prints nothing, so the warning is swallowed;
- the plan:354 variant with `>> "$PREFIX/.messages.txt"`: returns True and prints "warning: planpkg registration failed".

(b) Inspected ~/miniconda3/pkgs/isabelle-2025.2-89701cf1768e_0:
- info/index.json: build 89701cf1768e_0, linux-64;
- info/repodata_record.json: url file:///home/qiyuan/ci-work/channel/linux-64/…;
- tree opt/Isabelle2025-2 with no isa/; etc/ISABELLE_ID 89701cf1768e;
- ml_name_space.ML:67 is `["Signal"]`;
- about.json reads "with the my-better-isabelle-prover `user` patch category applied".

(c) Extracted Isabelle2025-2/src/Pure/ML/ml_name_space.ML and etc/ISABELLE_ID from the official tarball into tarball/: line 67 is `["CInterface", "Foreign", "RunCall", "Signal"]`, ID 89701cf1768e.

(d) b2/: GNU patch `setsid patch -p1 -F0 -i d.patch </dev/null` on a toy tree that already carries the expose_foreign hunk gives rc=1 ("Reversed (or previously applied) patch detected … Skipping patch", a .rej is written). On the unpatched control tree it gives rc=0. So decision 17's copy B catches a pre-applied chain feature.

(e) Grepped every recipe with post-link hooks under contrib/ and RELEASE_CHECKLIST.md/PACKAGING_DESIGN.md for .messages.txt. Only the isabelle package itself (recipe.yaml:127-135, :194) and isabelle-nunchaku's stderr (:493-500) use it; no component hook's warning echo does.

Also read REVIEW1:1226-1230 and PLAN.rev2.md:128-130 (the earlier correct description of the cached build), REVIEW2:1547-1566 (round-2 judge on the (b2) base), and migration plan :392 and :409.

Recommended fix: Hand edits only.

1. plan:170-172: replace "…一律 exit 0/exit /b 0，经 .messages.txt 说话（RELEASE_CHECKLIST.md:259）" with an accurate description:
   - RELEASE_CHECKLIST.md:259 requires only exit 0.
   - The existing component .sh hooks echo their failure warning to stdout, which conda drops on success (Isabelle_RPC recipe.yaml:154-155; conda core/link.py:1684-1686).
   - The .bat hooks are silent (`>nul 2>&1`, :173-175).
   - Only isabelle-nunchaku appends stderr to .messages.txt.

2. plan:353-355: present the line as "§4 的登记行，另把失败警告追加进 $PREFIX/.messages.txt（本计划的改进）" (§4's registration line, plus appending the failure warning to $PREFIX/.messages.txt as this plan's improvement). Also say what the Windows registration line does: either `|| >>"%PREFIX%\.messages.txt" echo warning: …`, or that it stays silent like the convention.

3. plan:148: replace "pkgs 缓存只有 linux-64 的 isabelle-2025.2-0" (the pkgs cache holds only linux-64's isabelle-2025.2-0) with a sentence saying:
   - the cache also holds the local-channel prototype isabelle-2025.2-89701cf1768e_0 (file:///home/qiyuan/ci-work/channel; tree opt/Isabelle2025-2, no isa/);
   - its ISABELLE_ID is the official 89701cf1768e although it carries expose_foreign (ml_name_space.ML:67);
   - so ISABELLE_ID alone does not prove a build is pristine;
   - the build is unusable with the tool (no isa/) and with every feature package (its build string matches no exact pin).
   Optional: add to decision 12.1 a CI assertion that the packaged tree equals the official tarball except the edits listed in ruling 20 (etc/settings, etc/options, etc/components, bin/isabelle.bat, heaps). Note in decision 17 that (b2) on the pristine build already catches a pre-applied chain feature.

4. plan:614: change "已裁定" to "已裁定；本计划", and say the official-tarball interim base is decision 17's choice (migration §5.1 :409 rules the published conda build).

5. decision 17 (plan:503-504): add one sentence stating that it replaces the round-2 judge's "copy of 2025.2-0" because the tool exits 3 on 5533cd83156e (decision 3.2).

**Judge: partially_confirmed → author_fixes_no_rereview.** All three statements are confirmed wrong.

(1) The component hooks do not report through .messages.txt. Their .sh echoes to stdout, which conda drops (Isabelle_RPC/conda/recipe.yaml:152-157; link.py:1684-1686), and their .bat is silent (:173-175).

(2) plan:148 is wrong, and the judge verified the facts. The cache also holds isabelle-2025.2-89701cf1768e_0:
- its tree is opt/Isabelle2025-2 with no isa/;
- its ISABELLE_ID is 89701cf1768e;
- its ml_name_space.ML:67 reads ["Signal"], i.e. it carries expose_foreign.
This is a regression from rev 2 (PLAN.rev2.md:128-130).

(3) §7 row (7) mixes a ruled part and this plan's own choice.

Only the conclusion that the identity rule 'rests on CI discipline alone' is overstated: (b2) with `patch -F0` catches a pre-applied chain feature (defender-C29/b2).

Author, by hand:
- plan:170-172 describes the existing hooks accurately, and plan:353-355 presents the .messages.txt redirect as this plan's improvement, including what the .bat line does on failure.
- plan:148 describes the second cached build, and says ISABELLE_ID alone proves nothing.
- Optionally, decision 12.1 asks for a CI assertion that the packaged tree equals the official tarball apart from ruling 20's edits.
- Change plan:614 to '已裁定；本计划'.
- Decision 17 states that it replaces REVIEW2:1563's '2025.2-0 copy', and why.

### C30 [minor] Terminology drift: two words for the conda build number, one word for three kinds of build, an undefined 临时目录 (temporary directory) beside the glossary's 'git runs only in the staging directory', and 原版树 (pristine tree) defined nowhere

Section: Glossary (plan:20, :28); §0 item 24 (plan:94); decisions 4-6, 10, 16, 17; §4 (plan:543)  ·  merged from: consistency-CONS-15

**Statement.** The project rule is one fixed term per concept, with the glossary authoritative (CLAUDE.md, 'Consistent Terminology — Never Coin Words'). Rev 3 breaks it in five places.
(1) The conda build number is called both '构建号' (plan:378, :385, :391, :494) and 'build 号' (plan:85, :378, :494).
(2) '构建' (build) means three things: a published isabelle package build (原版构建), an Isabelle session build (plan:573, :590), and a rattler-build package build (plan:386, :399).
(3) The glossary (plan:28) and the paraphrase of ruling 24 (plan:94) say git runs only in the staging directory. Decisions 4-6 and 16 also run it in an undefined '临时目录' (temporary directory): status's tempfile.mkdtemp(), the level copies, and gate (c)'s directory (plan:258, :278, :294, :496).
(4) Decision 17's '原版树' (pristine tree, plan:501, :508) is neither the migration glossary's 原版 (the hg source) nor the plan's 原版构建 (pristine build).
(5) '$PREFIX/isa is Isabelle2025-2 build 5533cd83156e' (plan:543) calls a changeset a build.

**Editor.** For (3), status must not write under the prefix and must run on a read-only tree (plan:278, :470), so it cannot replay in the staging directory. The fix is therefore to the glossary and to the paraphrase's wording, not to the design. Ruling 24's substance, that staging plus atomic rename is the only write path, is unaffected.

**Relaxation proposed by the editor.** Use one term for the conda build number everywhere (for example 'build 号', qualified by the package it belongs to), and 'session 构建' or 'isabelle build' for session builds. Add 临时目录 to the glossary and say in the glossary and in ruling 24's paraphrase that git runs only in a directory the tool created: the staging directory for writing commands, a temporary directory for status and --dry-run. Replace 原版树 with the defined term plus a qualifier, and write 'ISABELLE_ID 5533cd83156e'.

**Defender: partially_confirmed** (needs owner: False).

C30 makes five claims. Parts (1), (3) and (5) are confirmed. Part (2) is refuted. Part (4) is refuted as stated ("defined nowhere"), and only a one-line remnant survives. Part (3) is worse than the editor's rebuttal assumes: the wording that says git runs only in the staging directory hides one git call that has no stated working directory and no isolation, and I measured that call failing silently.

(1) CONFIRMED: two words for the conda build number.
- The authoritative migration plan uses only "build 号" (ISABELLE_GIT_MIGRATION_PLAN.md:90, :106, :130, :237, :406, :665). It never uses "构建号". So "构建号" is a second name coined by this plan.
- The `isabelle` package's build number is called "构建号" at plan:44, :99, :102, :378, :380, :385, :391, :494 and :616. The same number is called "build 号" at plan:85 ("CI 五个平台腿同一个 build 号"), :148 and :418.
- At plan:391 and :494 ("构建号 99、build 号 99"), the two words stand side by side for the build numbers of two different packages. The choice of word is then the only thing that tells the reader which package is meant. That is a fragile shape: nothing makes the distinction hold.
- The pin slot also has a third name. Ruling 22 (plan:81) and migration ruling 31 (:130) write `isabelle 2025.2 <build string>`, while decision 10 writes `<isabelle 构建号>` (plan:380, :616).
- Nothing is functionally wrong: the CI recipe makes the build string equal to the build number (isabelle-packaging-ci/conda/recipe.yaml:30-41, `string: ${{ build_number }}`).
- One citation in the challenge is wrong: plan:378 contains "build string" and "构建号", not "build 号".

(2) REFUTED: "构建 (build) means three things."
- This is one ordinary verb with several senses, not two names for one concept. The consistent-terminology rule forbids the second kind.
- The authoritative migration plan itself uses 构建 in all these senses. Conda package builds: :47, :123, :128, :232. Session builds: :34, :37, :325, :351. Build artifacts: the glossary entry 构建产物 at :17.
- Every occurrence in the plan is pinned down by its immediate context. plan:573 names the `run-tree … build …` command. plan:386 and :399 are the package build into a local channel. At plan:590, "在用户授权的腿上" (on the legs the user authorizes) marks a session build.
- One optional observation. The identifiers `isabelle_build` (plan:395) and `--isabelle-build` (plan:385) read like the command `isabelle build`. Renaming them along with fix (1) would remove that echo. It is not required.

(3) CONFIRMED, and more than wording.
- Three places claim that git runs only in the staging directory: the glossary (plan:28, "`git apply` 只在这里运行"), the paraphrase of ruling 24 (plan:94, "`git` 永远只在暂存目录里跑"), and §1, which the challenge did not cite (plan:115).
- The decisions contradict this. Decision 4 says the working directory is the staging directory or status's temporary directory (plan:258). Decision 5 says status and --dry-run replay in `tempfile.mkdtemp()` (plan:278). Decision 6 puts the level copies in an undefined 临时目录 (temporary directory) for every command, and never says which directory apply and unapply use (plan:294).
- One cited line is fine. Gate (c)'s temporary directory (plan:496) is not a counterexample: under decision 8 its git runs in `<tmp>/tree.staging`.
- The clause at plan:94 also overstates what the owner approved. Q5 asked only about the write path (REVIEW2.md:77). The round-2 judge's phrase was generic: "a staging directory the tool creates" (REVIEW2.md:435). Because §0 is binding, an over-claim placed inside a §0 item is especially misleading.
- The editor is right that status cannot replay in `<tree>.staging`, because status must work on a read-only tree (plan:278, :470). The editor is also right that the substance of ruling 24 is unaffected.
- But the wording is not the whole defect. Decision 3 runs `git apply --numstat --summary <patch file>` (plan:253) with no stated working directory. That call also sits outside decision 4's single function: the signature `git_apply(workdir, patch_file, *, reverse, check)` (plan:258) cannot express --numstat or --summary.
- conda runs hooks with cwd = `$PREFIX/bin` (conda core/link.py:1644-1645, gateways/subprocess.py:89).
- Measured with git 2.43.0, using a prefix inside a git work tree, the shape of §6 (j). With the caller's environment, from `<repo>/env/bin`, `--numstat --summary` printed nothing and returned rc 0. With the plan's whitelist environment plus `GIT_CEILING_DIRECTORIES`, it listed both files.
- If an implementer leaves that call un-isolated, every feature lists zero files. Decision 6 then reports "applied", because all of zero files are at level k or above (plan:300). apply moves nothing, and the hook prints nothing (plan:361-362). That is round-2 C1's silent no-op coming back through a call the plan left outside the isolation.

(4) REFUTED as stated, one remnant survives.
- 原版树 (pristine tree) is defined at plan:508, in the decision that uses it and seven lines after its first use (:501). plan:509 also says why the git archive is not used.
- Its use of 原版 matches the owner's own sense (plan:57) and the shared term 原版构建 (plan:20; migration :132).
- What survives: plan:507 twice writes bare "原版" (pristine) for this tree. In the migration glossary (:11-12), bare 原版 means the Mercurial source at tag Isabelle2025-2. That is exactly the git-archive content plan:509 rejects.

(5) CONFIRMED (minor).
- The message at plan:543 uses "build" for the ISABELLE_ID ("Isabelle2025-2 build 5533cd83156e (etc/ISABELLE_ID)"). In the next clause it uses "build" for the conda package build ("the pristine isabelle build").
- Isabelle calls this value the distribution identification, "derived from Mercurial id" (isabelle_system.scala:97-105, lib/Tools/version:17). The CI recipe says the changeset is not in the build string (recipe.yaml:30-41).
- A user who checks `conda list` sees `isabelle 2025.2 0`, which does not match.
- The internal uses "旧构建（5533cd83156e）" (old build) at plan:474 and :483 are harmless: they name the one published build by its ID, in parentheses.

Aside, outside C30, not examined further: decision 3 says the tool never needs to know which changeset is pristine (plan:245-246), and decision 2 says an absent features.d gives "no feature packages installed", exit 0 (plan:227-228). Yet §6 (i) (plan:598), decision 15 (plan:459) and ruling 22 (plan:83) expect exit 3 on a 2025.2-0 tree where only the tool is installed.

On the relaxation: its suggestions for (1), (3) and (5) are right. Its suggestion for (2) is unnecessary. Its suggestion for (4) is unnecessary beyond plan:507. For (3) it is insufficient unless decision 3's git call is also routed through decision 4's isolation.

Experiment: All work was read-only greps of the plan, REVIEW2, the migration plan, RECORD, the CI recipe, conda 25.11.1 source and the Isabelle tree, plus one git experiment in my scratch directory.

1. Term occurrences, with /usr/bin/grep -n:
- 构建号: plan:44, :99, :102, :378, :380, :385, :391, :494, :616.
- build 号: plan:41, :44, :84, :85, :148, :391, :418, :494.
- build string: plan:43, :81, :148, :378, :386, :395, :418.
- In the migration plan, "build 号" appears at :90, :106, :130, :237, :406, :665, and 构建号 appears nowhere.
- 构建 in the migration plan is used for conda builds, session builds and build artifacts (:17, :34, :37, :47, :123, :128, :232, :325, :351).
- 临时 in the plan: :258, :294, :387, :496. 暂存: :28, :91-94, :115, :258, :271-280, :330, :464.
- 原版树: :501, with its definition at :508. Bare 原版: :507.

2. Where conda runs hooks: core/link.py:1644-1645 calls `subprocess_call(..., path=dirname(path))`, and gateways/subprocess.py:89 sets `cwd = abspath(path)`. So a hook's cwd is $PREFIX/bin.

3. git 2.43.0 reproduction. Script: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C30/numstat.sh. Output: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C30/numstat.out. The patch modifies src/a.ML and creates src/n.ML.
- Outside any repository: `git apply --numstat --summary` lists both files and the create.
- From `<repo>/env/bin` with the inherited environment: no output, rc=0.
- Same cwd with the plan's whitelist environment (decision 4) plus GIT_CEILING_DIRECTORIES=<repo>/env: lists both files.
- An earlier variant run from a repository subdirectory gave the same empty output with rc=0; it is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C30/numstat/.

4. ISABELLE_ID naming: contrib/Isabelle2025-2/src/Pure/System/isabelle_system.scala:97-105 ("Isabelle distribution identification") and lib/Tools/version:17.

Recommended fix: All of these are hand edits to the plan, which CLAUDE.md requires for plan documents.

(1) Use one term for the build number: "build 号", the migration plan's word, qualified by the package it belongs to.
- Write "`isabelle` 的 build 号" in place of "构建号" at plan:44, :99, :102, :378, :380, :385, :391, :494 and :616.
- At :391 and :494, write "`isabelle` 的 build 号 99、feature 包自己的 build 号 99".
- At :380 and :616, write the pin as ruling 22 and migration :130 do: `isabelle 2025.2 <build string>`. Add once that, for `isabelle`, the build string equals its build 号 (decision 12, point 3).
- Optional: rename `--isabelle-build` and `isabelle_build` to `--isabelle-build-number` and `isabelle_build_number`.

(3) Fix the wording, and close the gap it hides.
- Add a glossary entry for 临时目录 (temporary directory): a directory the tool creates with `tempfile.mkdtemp()`, used by commands that do not write the tree.
- Reword the glossary entry at :28, the end of ruling 24's paraphrase at :94, and §1 at :115 to say: git runs only in a directory the tool itself created, the staging directory for commands that write the tree and a temporary directory for status and --dry-run.
- In decision 6 (:294), say that the level copies live in that same directory.
- In decision 4 (:258), state that every git invocation goes through the same child-process builder, including decision 3's `git apply --numstat --summary` (:253) and `git --version` (:268). The builder supplies the whitelist environment, `GIT_CEILING_DIRECTORIES` and a working directory the tool created. One way is to let `git_apply` take the numstat/summary mode, or to add a second function that shares the builder.
- Add a pytest case that runs status and apply from a cwd inside a git repository's subdirectory.

(4) At plan:507, write 原版树 in both places where it says "原版". Optionally add 原版树 to the glossary with the definition already at :508.

(5) Reword the message at plan:543, which is the author's to word under ruling 17: "$PREFIX/isa has ISABELLE_ID 5533cd83156e (etc/ISABELLE_ID); feature packages exist only for the pristine isabelle build. Run: conda update --all".

(2) No change is required.

**Judge: partially_confirmed → author_fixes_no_rereview.** (1), (3) and (5) are confirmed. (2) is refuted: 构建 is an ordinary verb, and the migration plan uses it the same way. (4) is refuted except for the bare '原版' at plan:507.

(3) is more than wording: it hides decision 3's unisolated git call (C2).

Author, by hand:
- Use 'build 号', qualified by the package it belongs to, everywhere: at plan:44, :99, :102, :378, :380, :385, :391, :494 and :616.
- Write the pin as `isabelle 2025.2 <build string>`, and say once that for isabelle the build string equals the build 号.
- Add 临时目录 to the glossary. Reword plan:28, :94 and :115 to 'git runs only in a directory the tool created (staging for writing commands, a temporary directory for status and --dry-run)', and say at plan:294 that the level copies live there.
- Write 原版树 at plan:507.
- Reword plan:543 (also C27 (3)).

### C31 [minor] Ruling 23's 'the name is kept' leaves pyproject's distribution name unstated; if it stays my-better-isabelle-prover, the 0.x section's `pip uninstall` removes the new conda tool

Section: §0 item 23 (plan:89-90); decision 1 (plan:211); decision 14 0.x section (plan:448-449)  ·  merged from: consistency-CONS-16

**Statement.** Ruling 23 says pyproject.toml's name is kept and used only for the conda recipe's `pip install . --no-deps` and for developers' editable installs (plan:89-90). The owner approved the author's option (a), which contained exactly this sentence (jsonl 6711, approved at jsonl 6713). Decision 1 names the Python package, the command and the conda package, but not [project].name, which today is 'my-better-isabelle-prover' (pyproject.toml:6).

If that value stays:
- conda's 1.0.0 installs a my_better_isabelle_prover-1.0.0.dist-info, under the same distribution name as PyPI's 0.3.0;
- the 0.x section's instruction `pip uninstall my-better-isabelle-prover` (plan:449), run in an environment that already has the conda tool, removes the new tool's files;
- a leftover 0.x dist-info collides with the new one, the case RELEASE_CHECKLIST.md:280-286 warns about.

**Editor.** The ruling's sentence can be read two ways: 'the field stays, unpublished' or 'the value stays'. A rename contradicts nothing only under the first reading. The plan must say which reading it takes; under the second, the remedy is a warning, not a rename, unless the owner agrees.

**Relaxation proposed by the editor.** Decision 1 states [project].name = "isabelle-patch-control" and records that ruling 23's '名字保留' is read as 'the field stays and is not published'. If the owner meant the value, the 0.x section must instead warn against `pip uninstall my-better-isabelle-prover` in any environment that has the conda tool.

**Defender: confirmed** (needs owner: False).

I could not refute C31. Rev 3 never states the new tool's distribution name (the `[project].name` in pyproject.toml). The one sentence that touches it, read against today's file, keeps the old name, and my experiments show that the old name breaks the new tool.

1. Rev 3 lost a fact that rev 1 and rev 2 both stated.
- Rev 1 decision 1 said "PyPI 名 `isabelle-patch-control`" (plan.rev1:110). Rev 2 said "PyPI 与 conda 包名都是 `isabelle-patch-control`" (plan.rev2:170). The PyPI name is the `[project].name` value, so both fixed it.
- When rev 3 removed PyPI, decision 1 kept only the Python package, the command and the conda package name (plan:211-212). It now has no distribution name.
- The only remaining sentence is ruling 23's "`pyproject.toml` 的名字保留" ("pyproject.toml's name is kept", plan:89-90). The file today says `name = "my-better-isabelle-prover"` (pyproject.toml:6). An implementer reading "keep the name" against that file would most naturally leave it as it is.
- Nothing in the channel's conventions forces a rename either. Isa-Mini ships the distribution `IsaMini` (Isa-Mini/pyproject.toml:10) as the conda package `isabelle-minilang` (Isa-Mini/conda/recipe.yaml:52).

2. A silent deviation from a round-2 judge action.
- The round-2 judge told the author to write the pyproject sentence into decision 1 (REVIEW2:2991). The round-2 defender's proposed wording was "pyproject 的 `project.name` 仍是 `isabelle-patch-control`" (REVIEW2:2974).
- Rev 3's §10 row for C24 says the change is in "决定 1" (plan:687). Decision 1 has no pyproject sentence at all (plan:211-221), and the plan does not say it deviated.

3. Which reading is right: the record settles it, so the owner does not need to be asked.
- The owner approved the rename. The author's accompanying note gave the package name as `isabelle-patch-control` (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1958, approved at :1962).
- The question the owner approved as ruling 23 opens with "改造后工具改名 `isabelle-patch-control`" ("after the rework the tool is renamed `isabelle-patch-control`", transcript jsonl line 6711; "赞同 (a)" at 6713). It was written against rev 2, where pyproject's name was `isabelle-patch-control`.
- The clause "只用于 conda recipe 内部的 `pip install . --no-deps` 与开发者的 editable 安装" ("used only for …") is false for the value `my-better-isabelle-prover`, because 0.3.0 on PyPI also uses that name.
- The glossary says the tool is "今天叫 `my-better-isabelle-prover` … 改造后叫 `isabelle_patch_control`" ("called … today, called … after the rework", plan:18-19).
- So "名字保留" means "the field stays and is not published", and its value is `isabelle-patch-control`. The editor's request that the plan state this is right. The second branch of the relaxation (warn users instead of renaming) is not needed, and it would be inelegant: users would have to remember not to run a command that the plan's own 0.x section tells them to run (plan:449).

4. The harm under the old name is real, and worse than C31 says.
- The 0.x section is printed by the new tool's own `help` (plan:448), and failure messages point to it (plan:451). Its readers are therefore usually in an environment that already has the conda tool.
- Under the old name, the instruction `pip uninstall my-better-isabelle-prover` (plan:449) removes the new tool (S1).
- When the pip 0.3.0 and the conda 1.0.0 are both installed, it removes the new tool and keeps the old one (S2, pip 24 and pip 26).
- Under the old name, PyPI's 0.3.0 can also replace the conda tool: `pip install my-better-isabelle-prover==0.3.0` uninstalls it (S5). This is the takeover that RELEASE_CHECKLIST.md:243-245 warns about, which ruling 23 was meant to remove.
- The channel's own check "`pip install NAME` saying already satisfied" (RELEASE_CHECKLIST.md:639) fails for NAME=`isabelle-patch-control` (S5).
- Under the name `isabelle-patch-control`, all of these are harmless (S3, S4, S6).

Experiment: I worked in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C31/: the driver is sim.sh, the toy projects are in src/, the wheels in wh/, and the outputs in out/s1-s6.out.

Setup:
- Three toy setuptools projects built into wheels: `my-better-isabelle-prover` 0.3.0 (package my_better_isabelle_prover); 1.0.0 under the same name (package isabelle_patch_control); and 1.0.0 under the name `isabelle-patch-control`.
- The conda install is simulated the way a rattler-build package is made: `pip install --no-deps --prefix` into a build prefix, copy the new files into the environment, set INSTALLER=conda. Real channel packages look exactly like this: envs/isabelle/.../isamini-0.6.0.dist-info has INSTALLER=conda and a full RECORD.
- Fresh venvs, system pip 24.0; scenario S2b repeated with pip 26.0.1 via `--python`.

Results:
- S1, old name, conda tool only: `pip uninstall -y my-better-isabelle-prover` printed "Successfully uninstalled my-better-isabelle-prover-1.0.0". isabelle_patch_control/, its dist-info and bin/isabelle-patch-control were all gone.
- S2/S2b, pip 0.3.0 plus conda 1.0.0 under the old name: two my_better_isabelle_prover-*.dist-info. The first uninstall removed 1.0.0 (the new tool) and left 0.3.0 with its `my-better-isabelle` command. Same with pip 24 and pip 26.
- S3, new name, conda tool only: "WARNING: Skipping my-better-isabelle-prover as it is not installed"; the tool is intact.
- S4, new name, both installed: the uninstall removed only 0.3.0.
- S5, old name: `pip install --no-index isabelle-patch-control` gave "No matching distribution" (the checklist :639 check fails). `pip install my-better-isabelle-prover==0.3.0` uninstalled the conda 1.0.0 and installed 0.3.0.
- S6, new name: "Requirement already satisfied: isabelle-patch-control (1.0.0)", and 0.3.0 installs next to it without touching it.

Source checks:
- plan:18-19, :89-90, :211-221, :448-451, :687; plan.rev1:110; plan.rev2:170; REVIEW2:2974, :2991.
- Transcript jsonl lines 6711 and 6713; LIGHT_LOCALE_HANDOFF.md:1958, :1962.
- pyproject.toml:6; RELEASE_CHECKLIST.md:243-245, :286-287, :639; Isa-Mini pyproject.toml:10 against recipe.yaml:52.

Recommended fix: The smallest fix, with no owner question, because it restores what rev 1 and rev 2 stated and what the owner approved in context:

(1) Decision 1 (plan:211-212): add "`pyproject.toml` 的 `[project].name` 改为 `isabelle-patch-control`（不发布，只供 conda recipe 的 `pip install . --no-deps` 写出 `isabelle_patch_control-<版本>.dist-info` 与开发者的 editable 安装；与旧分发名 `my-better-isabelle-prover` 不同，所以 0.3.0 与 1.x 可以并存，`pip uninstall my-better-isabelle-prover` 只碰 0.x）". This sentence:
- sets the distribution name to `isabelle-patch-control`;
- says it is never published and serves only the recipe's `pip install . --no-deps` and editable installs;
- notes that it differs from the old name, so `pip uninstall my-better-isabelle-prover` only ever touches 0.x.

(2) Ruling 23 (plan:90): append an author's note, leaving the owner's words untouched: "（"名字保留"指这个字段不发布也不删；值是改名后的 `isabelle-patch-control`，见决定 1）".

(3) §10's C24 row (plan:687) then becomes true. Alternatively, it should say that the pyproject sentence sits in ruling 23 rather than in decision 1.

Optional, but it makes the invariant mechanically checked instead of remembered: decision 15 or §6 asserts, in the tool package's test, that `pip install isabelle-patch-control` says "already satisfied" (RELEASE_CHECKLIST.md:639) and that `pip show my-better-isabelle-prover` reports nothing in a fresh feature environment.

Of the editor's relaxation, take the first half. Reject the warning-only alternative: the record rules out the "value stays" reading, and warning users against the plan's own instruction would be a hack.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed. Rev 1 (plan.rev1:110) and rev 2 (plan.rev2:170) fixed the distribution name; rev 3 no longer states it, and the round-2 action REVIEW2:2991 was not followed.

Under the old value my-better-isabelle-prover (pyproject.toml:6):
- the 0.x section's `pip uninstall my-better-isabelle-prover` (plan:449) removes the conda tool;
- `pip install my-better-isabelle-prover==0.3.0` replaces it (defender-C31/out/s1, s2, s5).

The record supports reading ruling 23's '名字保留' as 'the field stays and is not published', with the value isabelle-patch-control: jsonl 6711 opens with the rename, and the clause 'used only for' is false for the old value.

Author:
- Decision 1 states `[project].name = "isabelle-patch-control"`: not published, used by the recipe's `pip install . --no-deps` and by editable installs, and different from the old name, so `pip uninstall my-better-isabelle-prover` only ever touches 0.x.
- Add an author's note after ruling 23 (plan:90) explaining this reading, leaving the owner's words untouched. Ask the owner to confirm it (Q7).
- Make §10's C24 row true.
- Optional test: `pip install isabelle-patch-control` says 'already satisfied', and `pip show my-better-isabelle-prover` reports nothing in a fresh feature environment.

### C32 [minor] make-patches has no release-time refusal of patches that touch etc/ISABELLE_ID, so a forbidden feature can be published and then fail in every user's hooks

Section: Decision 16 (plan:488-497); decision 3 last point (plan:253-254)  ·  merged from: landing-L13

**Statement.** Decision 3 makes a feature whose patch touches etc/ISABELLE_ID a runtime exit 3, because the tool locks that file (plan:253-254). Decision 16's new gates cover empty files, modes and path lengths (plan:488-497), but not this. make-patches' gate (f) only compares the changed files with tools/patched_files.txt (tools/make-patches:118-128), so a feature that lists etc/ISABELLE_ID passes. Its package would then refuse the whole chain in every hook, reported only through .messages.txt with exit 0. This invariant can be enforced at release time, before any user sees it.

**Editor.** Verified make-patches:118-128 and :167-168. No overreach.

**Relaxation proposed by the editor.** Make make-patches refuse any block whose path is etc/ISABELLE_ID, with a toy test. Keep the runtime exit 3 as a backstop.

**Defender: partially_confirmed** (needs owner: False).

What is confirmed. Rev 3 has a runtime refusal but no release-time refusal of a feature that touches etc/ISABELLE_ID.
- The runtime rule: decision 3's last point says any feature whose patch files touch etc/ISABELLE_ID is exit 3, because decision 5 locks that file (plan:253-254, plan:282-285; listed again among the exit-3 cases at plan:528).
- No release gate catches it. Decision 16 adds six changes to make-patches (plan:488-497): gate (c) on the engine, empty files, modes, path length, gates-before-writes, toy tests. None looks at this path.
- Gate (f) in today's make-patches only checks that the changed files equal tools/patched_files.txt (tools/make-patches:118-128). The header check only rejects mode changes, renames and binary diffs (make-patches:167-168).
- Experiment: I copied tools/ into scratch and built a toy chain modelled on tools/tests/test_make_patches.sh. Its feature commit edits src/Pure/a.ML and etc/ISABELLE_ID, and both are listed in patched_files.txt. `make-patches feat 1` returned 0: gate (f) said "2 changed files, exactly tools/patched_files.txt", gate (c) passed, it wrote etc-ISABELLE_ID.patch, and it created the annotated release tag R/feat/1.
- Swapping in the plan's own engine does not catch it either. I ran the plan-style git apply (decision 4's whitelisted environment and -c flags) on the base archive: both patch files applied with rc=0, and `git apply --numstat --summary` names etc/ISABELLE_ID. So decision 16 point 1 does not close the gap.

Two extra points support the finding.
- The release tag is permanent. The reference-transaction hook refuses to change any existing release tag (tools/hooks/reference-transaction:28-29), and make-patches creates that tag last, after every gate (make-patches:209-211). Every later check therefore finds the problem only after the version number is used up.
- The plan already accepts this kind of gate. Decision 16 point 4 (path length) is the same kind of check: an install-time failure that can be predicted from the diff alone and is refused at release time. Leaving etc/ISABELLE_ID out is inconsistent with that.

What I refute: the claimed consequence, "can be published and then fail in every user's hooks", is overstated.
- The (b2) round-trip check (decision 17, plan:501-507) runs the tool's `apply` over the whole chain up to its top on copy A. The decision-3 refusal makes that exit 3, so A stays pristine while copy B is patched, and the `diff -r` fails. Decision 17 requires this check before every feature release, and publishing requires roundtrip_checked=true (plan:397).
- The batch release workflow runs §6 on all five platform legs before it publishes (plan:100, plan:398-401). §6 (a) installs isabelle-light-locale and asserts every feature is applied (plan:589). So a forbidden feature at or below light_locale fails CI.
- The online smoke test after publishing installs qiyuan-dev-patches, which is the whole chain, and asserts every feature is applied (plan:404-406).

A forbidden feature therefore reaches users only when two things both happen. First, the operator ticks roundtrip_checked without having run (b2) or despite its failure; that box is the operator's own say-so, nothing verifies it. Second, the bad feature sits above light_locale (local_type_abbrev, localized_record, local_datatype or dev_patches), because pre-publish §6 never installs those (plan:589-599). Even then the post-publish smoke test fails at once.

Also:
- The defect is purely preventive today. I ran read-only `git diff --name-only` from Isabelle2025-2/pristine/89701cf1768e to each of the seven feature branches in contrib/Isabelle2025-2-dev_patches: none touches etc/ISABELLE_ID. Only dev_patches touches an etc/ file, etc/options, and that hunk (lines 55-62) is far from pack.sh's ML_system_64 edit at line 193.
- The plan did not silently skip a judge action. The round-2 judge asked only for the runtime exit 3 (REVIEW2:1156, :1176, :1193), and rev 3 does exactly that.

So this is a minor gap and an elegance point, not a correctness hole. It is checked at runtime but only noticed at release time through indirect, partly honour-system checks, after an irrevocable tag already exists.

The editor's relaxation, on its merits: it is correct and sufficient. I would sharpen it in three ways:
- Put the check at gate (f), the earliest point, before generation, writing or tagging.
- Take the path from the same tool constant that decision 5 locks and decision 3 refuses, instead of writing a second literal "etc/ISABELLE_ID". make-patches already imports isabelle_patch_control.engine under decision 16 point 1, so the rule would live in one place.
- Have the toy test also assert that no release tag was created.

The runtime exit 3 should stay. It is the real guard for --features-dir trees and for packages built by any other route. etc/ISABELLE_IDENTIFIER does not need the gate: it is gitignored in the source repository (.gitignore:10 of every contrib/Isabelle2025-2* git tree), so `git diff-tree` never emits it.

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc3/defender-C32/

(1) Copied the tool's tools/ to the scratch dir as tools-copy/.

(2) Wrote test_isabelle_id.sh, modelled on tools/tests/test_make_patches.sh:1-71. It builds a toy hg upstream, a git R/pristine with the release text files and the reference-transaction hook, and runs check (a). Then a branch R/feat edits src/Pure/a.ML and changes etc/ISABELLE_ID to deadbeef0000. The package lists both files in patched_files.txt and has a matching signature addition and a tested record. `make-patches feat 1` returned 0: gate (f) passed with "2 changed files", gate (c) passed, it wrote run1/pkg/patches/R/etc-ISABELLE_ID.patch, and it created the tag R/feat/1.

(3) Extracted `git archive` of the base tag into gitapply/w/tree. Ran `git -c core.autocrlf=false -c core.attributesFile=/dev/null apply --whitespace=nowarn` under env -i with GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=/dev/null, GIT_ATTR_NOSYSTEM, LC_ALL=C and GIT_CEILING_DIRECTORIES (decision 4's isolation). Both patch files gave rc=0 and etc/ISABELLE_ID became deadbeef0000. `git apply --numstat --summary` reports etc/ISABELLE_ID. So decision 16 point 1's engine-based gate (c) also passes it.

(4) Read-only `git diff --name-only Isabelle2025-2/pristine/89701cf1768e Isabelle2025-2/<f>` for all seven features in contrib/Isabelle2025-2-dev_patches: none touches etc/ISABELLE_ID; dev_patches touches only etc/options. `git ls-files` confirms etc/ISABELLE_ID is tracked and etc/ISABELLE_IDENTIFIER is ignored (.gitignore:10).

Nothing outside the scratch dir was modified.

Recommended fix: Add a point 7 to decision 16 (plan:488-497):
- Gate (f) refuses a feature whose changed files include the tree's lock and identity file etc/ISABELLE_ID. It fires before any patch file is generated, written or tagged.
- The path comes from the same isabelle_patch_control.engine constant that decision 5 locks and decision 3 refuses at runtime, imported the way point 1 already imports git_apply. The rule then exists in one place.
- Keep decision 3's runtime exit 3 as the backstop for --features-dir trees and for any package not built by make-patches.

Add a toy case to tools/tests/test_make_patches.sh: a feature commit edits etc/ISABELLE_ID, the file is listed in patched_files.txt, make-patches is refused, and no release tag <R>/<feature>/<v> exists afterwards. That tag can never be rewritten (hooks/reference-transaction:28-29).

Optionally, add a row to §10 noting that this extends the round-2 C7 action from runtime to release time.

**Judge: partially_confirmed → author_fixes_no_rereview.** The gap is confirmed. make-patches releases a feature that touches etc/ISABELLE_ID and creates its permanent tag (defender-C32/test_isabelle_id.sh). The plan's engine-based gate (c) passes it too.

The consequence is overstated. (b2), §6 (a) and the post-publication smoke test would catch it, unless the checkbox is ticked dishonestly and the feature sits above light_locale. Today no feature touches the file.

Author:
- Decision 16, new point: gate (f) refuses any changed file equal to the lock and identity file, before generating, writing or tagging anything. The path comes from the same isabelle_patch_control.engine constant that decision 5 locks and decision 3 refuses at runtime, so the rule lives in one place.
- Keep the runtime exit 3 as the backstop.
- Add a toy test asserting the refusal and that no release tag exists afterwards (hooks/reference-transaction:28-29).
