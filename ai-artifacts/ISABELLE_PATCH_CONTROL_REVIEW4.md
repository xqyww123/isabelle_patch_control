# isabelle_patch_control plan rev 4 — review 4 (workflow wf_9531e1ef-1d3, 2026-10-24)

Critics: 55 findings (5 lenses). Merge editor: 24 challenges, 1 dropped. One fresh defender per challenge. Judge: ready = False.

## Judge summary

Rev 4 is not ready for the owner's approval. It is close, though: most of the 24 challenges are text and test defects the author can fix under ruling 17 (the owner's delegation of wording and tests).

Four things stand in the way.

(1) Three challenges need owner answers.
- C3: the copy of the hook fragment inside the isabelle package is redundant. Ruling 26's re-run already runs every installed feature hook whenever isabelle is relinked.
- C4: ruling 26's "including indirect dependents" rests on a false statement the author made to the owner (jsonl 7364). isabelle-semantic-data is an indirect dependent whose post-link discards the user's shared vector cache.
- C10: binding the shipped HOL-side files to a tested build needs a change to run-tree, a migration-plan tool.

(2) Four challenges reshape decisions 9, 11 and 16, which the round-3 judge asked to re-review.
- C2: since ruling 30, decision 11's reuse key "(name, version, build string)" never matches, so every dispatch would rebuild and republish every feature.
- C6: nothing stops run mode with publish=true, and the one published artifact would carry the CI run's isabelle builds.
- C5: decision 6's promise that no released chain has a multi-level file holds only under the optional strong gate. The three-feature toy xf3 passes every mandatory gate and then reads CONFLICT for users.
- C13: make-patches' two-repository write cannot be resumed, and its path-limited commit silently drops new files. Light's first release would lose provenance.txt.

(3) §10 is untrue again in at least eight places, although the plan's header promises otherwise (plan:5-6):
- the C24 row: the .bat pre-unlink is still not written;
- the C27 row: the in-place-edit half of action (4) is not mentioned;
- the C11 row: the REVIEW2:584 note is missing;
- the C28 row: the old freeze reason was kept;
- the C30 row: 构建号 remains at plan:91, :108, :111;
- the C20 row: check_bytes is missing from the pytest hostile case and the hook-layer tests (REVIEW3:2670);
- the C29 row: plan:229-230 still miscites the checklist, and plan:463-465 does not present the .messages.txt redirect as this plan's own improvement;
- the round-2 C9 (2) contradiction survives in Appendix A (plan:921-922) and has no row.

(4) Several surviving defects come from new rulings colliding with older judge actions (C2, C3, C4). That is exactly what a re-review catches.

I checked the contested facts myself:
- conda writes package records only after all post-links, and removes the records of packages it unlinks (core/link.py:938-999; RemoveLinkedPackageRecordAction at path_actions.py:1209-1219).
- GitHub documents job.workflow_repository and job.workflow_sha. Re-running failed jobs uses the first attempt's SHA of a reusable workflow, which refutes the editor's doubt in C9.
- `git commit -m … -- patches/R/` returns 0 and leaves new files untracked (review-ipc4/judge/c13).
- The semantic-data hook only calls the isabelle-semantics console script, whose code ships in the small isabelle-semantic-embedding package, so C4's option (b) needs no 9.6 GB republish.
- The author's Q5 statement (jsonl 7577) holds in substance, so C2's requested §0 correction is refuted.

Recommendation: the author asks the three owner questions, applies the actions below, and then gets a targeted re-review of decisions 9, 11, 12 and 16 and of every §10 row against the judge actions. Not a full multi-critic round.

## Questions for the owner

Question 1 (C3): may the isabelle package stop carrying its own copy of the hook fragment?

The hook fragment is the short script, owned by the tool repository, that runs isabelle-patch-control and re-applies all installed feature packages. Rev 4 puts copies of it in two places: in every feature package's post-link, and in the isabelle package's post-link. The second copy is how rev 4 carries out your ruling 13 ('the new isabelle build's post-link re-applies the installed features').

Your later ruling 26 makes the same isabelle post-link re-run the post-link of every installed package that depends on isabelle. Every feature package depends on isabelle, through its exact build pin, and its post-link is that same fragment.

conda writes its package records only after all post-links have run, and removes the records of the packages it unlinks. So, during the isabelle post-link, ruling 26's scan sees exactly the installed packages that are not part of the current conda command, and the packages that are part of it run their own post-links anyway. The result: whenever isabelle is relinked, every installed feature's hook runs once, and the copy inside the isabelle package adds nothing.

Keeping the copy costs three things:
- a user who follows the plan's own repair, `conda install --force-reinstall isabelle`, gets the full CONFLICT diagnosis twice (measured);
- the release workflow must download the 0.8-1.1 GB isabelle packages just to check the copy byte for byte;
- the tool's command line is frozen into the isabelle package for all of 1.x.

(a) Recommended: drop the copy. The isabelle post-link becomes its existing hint, then ruling 26's re-run, then exit 0. Ruling 13's re-application is then done by that re-run: the first feature hook it runs re-applies the whole chain. Users see the same result, with one diagnosis instead of two.

(b) Keep both copies. The plan then fixes only the duplicate diagnosis, by letting only the top feature's hook write the full diagnosis.

Question 2 (C4): which installed packages should the isabelle post-link re-run?

Ruling 26 re-runs the post-links of packages that depend on isabelle 'including indirectly'. You accepted 'no marker' after I told you that this set is today exactly the component packages and the feature packages, and that every hook in the channel can safely be run again. That was wrong.

isabelle-semantic-data, the 9.6 GB semantic database that isabelle-ai pulls in, depends on isabelle only through isabelle-semantic-embedding. Its post-link runs `isabelle-semantics post-install-system-db`, which was designed to fire only when its payload changes. That command deletes the user's stand-in vectors: vectors the user's machine computed locally for keys that have no user record, stored under ~/.cache and shared by all environments.

Under ruling 26 it would fire at every isabelle relink: every new isabelle build, every `--force-reinstall isabelle` (the plan's universal repair) and the first upgrade off 2025.2-0. Nothing user-written is lost, because vectors are a lazy cache. The cost is re-embedding: paid API calls and latency, large mainly for users of an embedding model the payload ships no vector store for.

(a) Recommended: re-run only packages whose depends list names isabelle directly. Every component package and every feature package does; semantic-data does not. This works for every package already published, with no republishing. It goes with a written rule: a package whose post-link acts on Isabelle's tree or user directory must depend on isabelle directly, and running such a post-link again while the package's own files are unchanged must have no effect.

(b) Keep 'including indirect', and change the `isabelle-semantics post-install-system-db` command, which ships in the small isabelle-semantic-embedding package, so that it purges only when the installed payload's identity changed. This amends VECTOR_INVALIDATION_PLAN §7's approved 'no remembered created_at'. It would also fix a problem that exists today, independent of this plan: creating a second environment with the same payload already purges the shared cache.

(c) A 'do not re-run me' marker. It needs a republished semantic-data package, or a hard-coded exclusion list inside the isabelle package.

(a) and (b) can be combined.

Question 3 (C10): should the tested-build record also capture the state of the light repository?

Your ruling 21 ships light's HOL session (ROOT and Light_Locale.thy) inside isabelle-light-locale. A HOL-only change is released as a new light version, and the release procedure includes a tested build.

The tested record is the git note that run-tree writes on the Isabelle commit, and make-patches' gate (e) requires one. It records the build command and the sessions. It records neither the light repository's commit nor whether light's files were clean. make-patches checks only that the shipped light files are committed at the moment it runs.

Measured on toy repositories with the real run-tree and make-patches: a Light_Locale.thy committed after the tested build was released with no build of it ever made. The plan's own HOL-only procedure has this shape.

The fix needs run-tree, a tool of the approved migration plan and outside this plan's scope, to record more. So it amends the migration plan's definition of the tested record.

(a) Recommended: for every -d directory inside a git work tree, run-tree records its HEAD and its uncommitted files. Gate (e) then accepts only a record in which the shipped light files had no uncommitted changes and are byte-identical between the recorded HEAD and the commit being released. Comparing file contents means unrelated commits in the shared light repository do not force a rebuild that takes hours.

(b) Do not bind the record. Rely instead on the batch release workflow building the installed light session on linux-64, which the author will add either way. That build proves the shipped files compile against the patched Pure, but not that light's test sessions pass on them.

## Relaxations recommended

1. C3: remove the copy of the hook fragment from the isabelle package. Its post-link becomes the existing hint, ruling 26's re-run, then exit 0. The first feature hook the re-run runs re-applies the whole chain. The byte-for-byte cross-repository check and its isabelle download go away, the isabelle package no longer depends on the tool's command line, and the duplicate diagnoses disappear by construction. Needs the owner's confirmation (question 1).

2. C12, with or without C3: only the hook of the top feature of the installed chain writes the full diagnosis, and an unset or unknown PKG_NAME behaves like it. Ruling 26's re-run already runs that hook in every transaction that links isabelle. Decision 15's three diagnosis-count shapes become one invariant: exactly one full diagnosis whenever the transaction links isabelle or the top feature package.

3. C4 option (a): re-run only packages that depend on isabelle directly. The rule 'a post-link that acts on Isabelle's tree or user directory requires a direct dependency on isabelle' states the real contract, and it works for every already-published package without republishing anything. Needs the owner (question 2).

4. C5: make the strong form, 'every state of a released chain fits exactly one level, checked at every release on the chain ending at the new tag', the release gate. Keep the blob comparison only to choose ruling 28's message. One gate then backs decision 6's guarantee; today a weaker gate sits beside a claim it cannot support.

5. C6: publish an artifact that contains only noarch packages, asserted by the build job, and fail at once when run mode is combined with publish=true. 'Only the tool and feature packages reach publish-conda.yml' then becomes a property of the workflow's structure, not something the operator must remember.

6. C2: key reuse on the isabelle pin in each record's depends, in one unit-tested function, so ruling 30's build string needs no change.

7. C14: make --features-dir the only feature input of check-roundtrip. In CI, take that directory and the tool from an environment installed from the local channel, so the roundtrip check tests the shipped bytes and the shipped tool by construction.

8. C13: create the Isabelle release tag last, so that its existence marks a complete release and a rerun after any partial failure finishes the release.

9. C11: every residue block's recovery names the highest feature package whose directory is in features.d when the pre-unlink runs, so all blocks of one conda command give the same command and the order in which the user follows them no longer matters.

10. C16: replace the give-up branch with 'do the keep recovery, then conda remove the feature package'. One recovery path replaces two, and the tool, not the user, removes the files it created and the staging directory.

11. C18: choose the replay directory by lock mode (only an exclusive-lock holder uses the staging directory; every other replay uses a fresh mkdtemp), so 'only the lock holder touches the staging directory' holds by construction.

## Critics' overall notes

- conda: Lens: conda mechanics, hooks and packages (decisions 1, 2, 9, 10, 12; sections 2.3, 4, 6). I built a rev-4 toy channel with conda 25.11.1, a private HOME, CONDARC and pkgs directory, conda-forge python and git, and real git apply. Its hook fragment and pre-unlink are copied verbatim from plan:435-440 and :459-461. It has a noarch:python toy tool that is run as `python -I -X utf8 -m`. The toy isabelle builds are 0 (the old ID), 1 and 2 (pristine, depending on python, and running a decision-12.2 re-run script), plus a three-feature chain whose top feature carries a component payload, and an Isabelle_RPC-style component. The .bat fragment I checked under wine through conda's CALL wrapper. Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/ (src/mkchan4.py, src/toytool.py, src/rerun.py, run2-run5.sh/.out, bat/run.out, live/*.json, semdata-hooks.out). I modified no repository and no owner environment.

What holds (measured):
- The written .sh and .bat texts keep exit 0 inside the hook text. Installs succeed and history survives when the tool is absent or crashes at import. The elif and goto branches report correctly.
- Ruling 26's discovery through conda-meta/*.json is sound, by construction of conda's ordering. Records of the packages in the transaction are written only after all post-links (link.py:969-972). Unlinked records become .json.c~ (link.py:122-130, path_actions.py:1152-1164). So a fresh create and a clone find 0 records, `--force-reinstall isabelle` finds every dependent, and update --all finds only the untouched component. The first move off build 0 re-registers the component into the new hash-suffixed user directory. Light-style component lines register and unregister.
- Pruning runs the pre-unlinks top-down while the tool is still installed. git is found at sys.prefix even though the pre-unlink runs outside the activated environment. `conda remove isabelle` leaves no isa/ on POSIX. The exact pins move isabelle and the re-released features together on update --all.

What does not hold:
- (1) With ruling 26, the isabelle package's own copy of the fragment is redundant. It doubles the full diagnosis on the plan's own repair command and keeps tool-owned text, plus a byte check of about 1 GB, inside the CI's package.
- (2) The re-run silently deletes isabelle-semantic-data's user vector cache on every isabelle relink, because that published post-link assumes it runs only when its payload changes.
- (3) The new python dependency breaks five `--override-channels` installs in build.yml and release.yml, and decision 12 never says so.
- (4) Decision 11's reuse rule lost its key with ruling 30 and contradicts its own examples.
- (5) Residue blocks and their recovery assume a single removal. They are false on update and relink, a relink below a CONFLICT strips the upper features, and only the top block's recovery works.
- Minor: 链顶 is ambiguous in the diagnosis rule, the pre-unlink .bat is still unwritten (a silent partial in §10), `if errorlevel 1` misses negative exit codes, and the crash test is stale.

None of these needs a ruling reversed. Fix (1) shrinks the design, and fixes (2)-(5) are local.

- engine: I prototyped rev 4's decisions 3-8 literally (scratchpad review-ipc4/critic-engine/ipc4.py) and tested the prototype on the real chain. The chain was built with read-only `git diff-tree` between the current branches of contrib/Isabelle2025-2: expose_foreign, future_assign_interrupt, light_locale and dev_patches. local_type_abbrev, localized_record and local_datatype are empty today. That gives 42 patch files over 40 files, on a base made from the pristine tag plus pack.sh's etc/options edit.

The engine implements rulings 18, 24 and 28 soundly.
- A single private _git primitive is the only way git starts, including the --numstat/--summary listing and --version. It builds a whitelist environment, the -c flags, a ceiling and umask 022.
- Levels are defined over feature numbers, and both halves are sequential replays.
- One replay both computes the levels and supplies the snapshot that os.replace or os.unlink installs.
- Each file has its own target level T_p, apply is capped below the lowest CONFLICT feature, and unapply moves whatever it can.
Measured results:
- Exact round trip: the tree is byte-equal to the dev_patches tip and returns to the base. Partial runs (unapply --feature light_locale, then apply --feature light_locale) are also byte-exact. No staging directory is left behind.
- Each command makes 127-128 git calls and takes 0.17-0.19 s.
- On the fully applied tree, `apply --feature F --dry-run` lists 0 files for every F. The cap held at T=2 when a light file was in CONFLICT.
- Isolation holds when the tree is in a gitignored directory of an autocrlf repository with .gitattributes eol=crlf, the tool's cwd is a subdirectory of that work tree, TMPDIR is inside it, and HOME, XDG and GIT_DIR/GIT_WORK_TREE/GIT_CONFIG_* are exported (hostile.out).
- Every no-fit shape returns rc 1 (11 shapes), and a write failure returns 128 (rc.out). This supports the plan's rule for reading exit codes by phase.
- The blob form of the 'no revisit' gate finds 0 revisits on the real chain, and the strong form finds 0 bad states.
§10's rows for C2, C7, C17, C18, C19 and C22 match the text. The one unnamed narrowing is C2's 'git runs only in a directory the tool created': the glossary and decision 4 list two directories, while decision 5 uses three.

The main defect (engine-1, major): rev 4 asserts, but does not enforce, that no state of a released chain fits several levels. I found a two-feature chain that passes the mandatory blob gate and both gate (c) round trips, installs correctly, and then reads CONFLICT for both features with an irreversible pre-unlink. The optional strong form catches it cheaply and before any tag is created, so it should be mandatory.

The smaller findings:
- a CRLF-converted patch file passes the listing check (engine-2);
- where the lock-less level computation of a pre-unlink runs is unspecified (engine-3);
- make-patches' two-repository steps cannot be retried after a partial failure (engine-4);
- ruling 26's rerun prints the full diagnosis twice (engine-5);
- three inputs the model cannot represent are not refused (engine-6);
- §8's timing is stale and the Windows cost is unmeasured (engine-7);
- decision 7 states one property too broadly (engine-8).

Every experiment is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-engine/: ipc4.py, real/, real.out, xf.sh/xf.out, search/, rc/, hostile.sh/hostile.out, nd/, dup/ and revisit.py/revisit.out. No repository, Isabelle tree or conda environment was modified.

- consistency: Rev 4 records the seven new owner rulings (§0 items 26-32) faithfully in substance, with one quote attached to the wrong question (item 26) and one author decision placed inside a binding ruling (item 30). Most of §10's 34 rows match the text. These facts check out against the sources: the banner date (85dc11b at 2026-10-09T23:26Z; last publish across all PUBLISH_REPOS at 05:03Z the same day, verified with gh), the conda source line numbers, make-patches, the tool code and pyproject, and the pack.sh, recipe.yaml, build.yml and publish-conda.yml citations.

Three new rulings are not carried through to the decisions they touch:
- Ruling 26's re-run sits next to the isabelle package's own copy of the hook fragment. The force-reinstall repair, the plan's universal remedy, therefore applies the chain twice and prints two full diagnoses, a shape decision 15's count table omits; the copy is now redundant.
- Decision 12.2 turns ruling 26's permission into a python dependency without listing its consequences: every `--override-channels` install in build.yml and release.yml breaks.
- Ruling 30's build string breaks decision 11's reuse key, so every dispatch republishes every feature, contrary to the plan's own example.

Decision 6 claims ruling 28's gate makes multi-level files impossible. Only the optional form of the gate does: I reproduced a repeated-block chain that passes the mandatory gate and reads CONFLICT on a correctly applied tree.

Decision 12.5's banner fix would break every cross-repository caller of publish-conda.yml, including this plan's own batch workflow.

The pre-unlink .bat is still '同义' for the third round, while §10 says it is written.

The glossary's 链顶 (dev_patches) is reused for two other concepts, which, read literally, misdirects decision 9's diagnosis rule.

The smaller items are untrue §10 rows, stale facts, an acceptance check that cannot run, an interface mismatch in (b2), Appendix A contradicting itself, and two invariants the plan asks people to remember.

Not ready. Decisions 9, 11, 12 and 16 need another pass. The engine decisions, 4, 5 and 7, hold up under this lens.

- landing: Lens: landing order, release infrastructure and acceptance (decisions 11-17, §5, §6). Every repository was only read. Experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-landing/ (pydep/run.out, commit.out, shallow.out, live/*.json).

What holds:
- Rev 4 has the right shape for the batch workflow. One build on ubuntu feeds five accept legs from one artifact, the publish job makes a single publish-conda.yml call with the secrets passed explicitly, the build numbers come from the channel, and step 7 rehearses against a CI run's artifact before anything is published.
- The tokens are right. publish-conda.yml (:69-87) stays on the run-scoped token. isabelle-packaging-ci is public, so the cross-repository `uses:` works. Downloading another run's artifact needs an actions:read token. A depth-1 fetch of exactly two tags is enough for `git diff-tree` (measured).
- §5's order is consistent. The secrets and tokens are set at step 5, before the first dispatch at step 7. The banner fix comes at step 6, before the publication at step 8. The repositories and tags exist at step 3. Running (h) only on re-runs matches the hook-layer test's 'not yet re-released' case. (g)'s win-64 wording follows the judge.

What does not hold, three major defects:
- L1: run mode never says where the CI run's isabelle packages go. Combined with a single artifact that is published whole, publish=true with isabelle_from=run either publishes CI-run isabelle bytes or publishes features pinned to an unpublished build. Nothing forbids that combination.
- L2: ruling 26's python dependency makes every existing `--override-channels` install that lacks conda-forge silently fall back to isabelle-2025.2-0 (measured). That includes release.yml's smoke at step 8 and two component repositories' verify gates.
- L3: the reuse key is '(name, version, build string)', but under ruling 30 the build string no longer carries the isabelle build. As written, every run rebuilds every feature package. The judge's 'one unit-tested function' was also dropped without a note in §10.

Minor defects:
- L4: decision 17's interface does not fit decision 11's roundtrip job.
- L5: make-patches' two-repository write cannot be resumed after a failure, and a path-limited commit silently drops new patch files (measured).
- L6: both banner-step fixes that decision 12.5 offers fail for external callers, and nothing rehearses the publish path before step 8.
- L7: light's session is never built from the installed package before publication, by default.
- L8: §6 (k) after (b) and (g) cannot run as defined, and (h) has no trigger.

Verdict for this lens: not ready. L1-L3 must be fixed in decisions 11 and 12. None of the fixes reverses a ruling.

- user: I walked rev 4 from the end user's and the maintainer's side. I read the plan in full, the round-3 judge actions, the conda 25.11.1 source, the CI and component recipes, light's repository, the tool's tools/ scripts and the Isabelle sources. I then built a toy conda channel shaped like rev 4: decision 9's .sh fragment copied verbatim, ruling 26's re-run of dependents' post-links in the pristine isabelle post-link, the old 2025.2-0 build with its user-directory pre-unlink, the hashed user directory of ruling 31, three chained feature packages (the top one creates a file and registers a component), an Isabelle_RPC-like component, and a toy tool that follows the message rules of decision 9 and §4. All scripts and outputs are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-user/ (mkchan4.py, mkchan4b.py, lib.sh, run1-run7 with .out files). Nothing outside that directory was modified.

What holds, measured:
- A fresh `conda create isa fc` prints exactly one applied line and one heap notice, and registers the component.
- An environment on the old build with an RPC-like component, after `conda install fc`, moves to the pristine build. The old user directory is deleted, and the new hashed one ends up with both registrations, thanks to the re-run.
- While a new isabelle build is live but its features are not yet re-released, `conda update --all` stays put, an explicit install conflicts, and a feature install downgrades isabelle to the pinned build.
- The `--force-reinstall isabelle` remedy works for an edit that replaced the file, and the keep branch of the Ctrl-C recovery converges.

What does not hold, ordered by weight:
1. Ruling 26's re-run, as specified (it includes indirect dependents), also fires isabelle-semantic-data's post-link. That hook's approved design assumes it runs only when its payload changes. So every isabelle relink deletes the user's valid cached vectors, which must then be re-embedded through a paid API.
2. Edits written in place through the hard link: the CONFLICT remedy loops, and the edit spreads to every environment created from the same package cache. Round 3's judge action on this was not carried out, and §10 does not say so.
3. The update command `conda update --all`, typed as written, does nothing for users who installed the way the channel banner says (channels on the command line).
4. The fragment in the isabelle post-link is redundant now that ruling 26 re-runs every feature's post-link. Keeping it doubles the diagnoses (measured) and keeps a frozen copy of the hook text in another repository.
5. Since ruling 30, decision 11 no longer defines when an already-published feature package is downloaded instead of rebuilt; read literally, every feature is rebuilt in every batch.
6. In a HOL-only light release, nothing ties the shipped HOL files to a build.
7. Smaller defects: the residue block's recovery, the two meanings of 链顶, the Ctrl-C texts, the missing .bat pre-unlink (a silent deviation), the consequences of isabelle depending on python, the heap notices, several contradictory user-visible texts, and the build-number derivation ignoring packages that were uploaded but not indexed.

None of the fixes reverses a ruling. Two of them need an owner choice: which dependents the re-run covers, and whether the isabelle post-link keeps the fragment.

## Dropped by the merge editor

- engine-engine-8: Nitpick. It objects to the wording of a rationale sentence in decision 7 (plan:409-410), which says that files the target feature did not touch 'never move'. The property the plan actually tests is stated correctly in decision 15 (plan:621: on a fully applied tree, `apply --dry-run` lists no file), and the critic's own run shows that the defined behaviour (per-file target levels) is right. The author can fix the sentence while editing decision 7. It does not merit a challenge.

## Challenges

### C1 [major] The isabelle package's new python dependency makes every --override-channels install without conda-forge either fail or silently fall back to the patched 2025.2-0; decision 12 lists none of this, so release.yml's step-8 smoke and the component repositories' gates would test the wrong build

Section: Decision 12 points 2 and 4; §0 item 26; §5 steps 6-8  ·  merged from: conda-conda-3, consistency-CONS4-2, landing-L2, user-U11

**Statement.** Ruling 26 allows the isabelle package to depend on Python (plan:113). The owner said this after the author pointed out that the dependency scan would otherwise have to be written in bash and in bat (transcript lines 7318-7320). Decision 12 point 2 turns the permission into a run dependency, 'isabelle 包依赖 python' (plan:561), but lists none of the consequences. Today the package has no requirements (isabelle-packaging-ci/conda/recipe.yaml:235-237), and the live channel has no python in any subdir (review-ipc4/critic-conda/live/*.json; the plan itself says so at plan:533-534).

Every CI install of isabelle uses only the local channel or the live channel, with --override-channels: build.yml:1012 (Job F), :1203 and :1217 (Job G), :1286 (Job H), and release.yml:115 (the smoke test after publication). While 2025.2-0 (depends: []) stays on the channel, the solver does not fail. It silently picks 2025.2-0. Measured with conda 25.11.1 on a toy channel holding build 0 (no dependencies) and build 1 (depends on python): `conda create --override-channels -c file://chan isa` and `... comp` (where comp needs isa >=2025.2,<2025.3) both exit 0 and install ISABELLE_ID 5533cd83156e. Only an explicit `isa=2025.2=1` fails, with 'nothing provides python' (review-ipc4/critic-landing/pydep/run.out). Consequences:
(1) At §5 step 8, release.yml's smoke installs 2025.2-0. It still finds 'Isabelle is installed' (release.yml:116-117) and goes green, so the step-8 precondition 'release.yml 已把原版构建发到线上且绿' (plan:543) checks the wrong build.
(2) The verify and smoke jobs of component repositories keep testing against the expose_foreign build for good: Performant_Isabelle_ML release-conda.yml:423-425 and :527-529, auto_sledgehammer release-conda.yml:195-197. These workflows keep conda-forge out on purpose (Performant_Isabelle_ML release-conda.yml:420-422), so adding it there is not a mechanical edit.
(3) build.yml Jobs F, G and H fail outright, because their local channel holds only build N.
(4) Several statements become false: recipe.yaml:235-237 ('No requirements ... depends on nothing from the channel'), recipe.yaml:182-184 (the post-link is message-only), the user command in PACKAGING_DESIGN.md:87, and PACKAGING_DESIGN.md:737's rule that the CI package test is an offline, deterministic install from the local channel. RELEASE_CHECKLIST.md:298 already requires conda-forge in the channel list for anything with Python dependencies.
Decision 12's list of requirements for the CI plan (plan:553-579) contains none of this.

Fix. Add a point to decision 12 covering the following.
- Every install of isabelle, or of anything that depends on it, in isabelle-packaging-ci's workflows gains `-c conda-forge` after the local or live channel. The alternative is that the CI mirrors the exact python it needs into the local channel, which keeps PACKAGING_DESIGN.md:737's offline rule.
- release.yml's smoke installs `isabelle=2025.2=<the build it has just published>` and asserts that etc/ISABELLE_ID is 89701cf1768e, so a fallback cannot pass.
- Decision 12 point 4's rewrite list gains recipe.yaml:182-184 and :235-237, and PACKAGING_DESIGN.md:87 and :737.
- The same edit is listed for the maintainers of Performant_Isabelle_ML and auto_sledgehammer (the way decision 14 lists Isa-Mini's comments), to land before §5 step 8.
- §5 step 6 names this change, so that step 7's rehearsal exercises it.

**Editor.** CONS4-2 also proposes keeping isabelle free of dependencies and writing the scan in sh and bat. That stays within ruling 26, but the owner granted the Python dependency precisely to avoid it (transcript 7318-7320), and a JSON dependency scan written in cmd.exe is the kind of hack the elegance criterion counts against. The choice belongs to the CI plan. Whichever it makes, this plan must state the consequences. If the owner adopts C4's rule of re-running direct dependents only, the scan no longer needs a dependency graph. The CI plan may weigh that, but a python-free scan would still be a text match on JSON. U11's 'the documented user command stops solving' is overstated. A user whose condarc lists defaults or conda-forge gets python from there. The real hazard is the silent fallback that L2 measured, not a solver error.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute C1 and could not. Its core holds, but three of its sub-claims are overstated.

What I confirmed:
- The plan makes python a firm requirement. Ruling 26 only permits it ("isabelle 包可以依赖 Python", plan:113); decision 12 point 2 states it as a requirement ("isabelle 包依赖 python", plan:561).
- Today the isabelle package has no requirements at all (isabelle-packaging-ci conda/recipe.yaml:235-237), and the cached 2025.2-0 has "depends": [] (~/miniconda3/pkgs/isabelle-2025.2-0/info/index.json).
- The live channel has no python. The snapshots in review-ipc4/critic-conda/live/{linux-64,noarch,win-64}.json contain only isabelle 2025.2-0, the component packages and rocksdict, and the plan says so itself (plan:534).
- Every install below uses --override-channels without conda-forge:
  - build.yml:1012, :1203, :1217 and :1286;
  - release.yml:115;
  - Performant_Isabelle_ML release-conda.yml:423-425 and :527-529, whose comment at :420-422 keeps conda-forge out on purpose;
  - auto_sledgehammer release-conda.yml:195-197 and also :273-274, which C1 does not cite.
  - Isabelle_RPC, Isa-Mini, Isabelle-MCP and Semantic_Embedding already list conda-forge.
- My own measurement agrees with the critic's (defender-C1/run2.out, conda 25.11.1, both libmamba and classic):
  - With only a toy channel holding build 0 (no dependencies) and build 1 (depends on python), unpinned `isa`, and `comp` (which needs isa >=2025.2,<2025.3), both silently install build 0 (ISABELLE_ID 5533cd83156e).
  - `isa=2025.2=1` fails with "nothing provides python".
  - Once a channel also provides python, both solvers pick build 1.
  - Side finding: the first run without a pip package still fell back to build 0, because conda makes python require pip. So "mirror python into the local channel" means mirroring python plus pip plus python's own dependencies. That makes the alternative C1 offers heavier than it sounds.
- 2025.2-0's post-link prints "Isabelle is installed" (pkgs/isabelle-2025.2-0/bin/.isabelle-post-link.sh). So release.yml's grep at :116-117 goes green when the solver falls back.
- The plan expects 2025.2-0 to stay online (§6 (e), plan:793), and the sweep only removes packages the owner selects (sweep-old-versions.py:1-28). So the fallback is not temporary.
- Decision 12 (plan:553-579) names none of this. Its point-4 rewrite list leaves out recipe.yaml:235-237, which python makes false, and :182-184 ("message-ONLY"), which point 2's hook insertion makes false. It also leaves out PACKAGING_DESIGN.md:737, whose rule is an offline install from the local channel only.

The most serious confirmed consequence is in the component repositories. Neither plan covers them: the CI plan's scope is isabelle-packaging-ci (plan:8, :159), and this plan's decision 14 lists cross-repository edits only for Isa-Mini (plan:610). Performant_Isabelle_ML's verify job builds its sessions and calls Foreign. Testing against 2025.2-0, where Foreign is already exposed, never runs rescue_foreign.ML's pristine-Pure path, and that path is exactly what every user gets after this plan lands. That silent loss of test coverage persists indefinitely.

What is overstated:
1. PACKAGING_DESIGN.md:87 is not made false. The user command has no --override-channels, so python comes from the user's default channels. The editor already concedes this.
2. Jobs F, G and H fail loudly, inside isabelle-packaging-ci. The CI plan's own first ci.yml dispatch at §5 step 6 will reveal them, so this part is not a "tests the wrong build" hazard.
3. The step-8 precondition "release.yml green" (plan:543) is hollow as a check of build N, but this plan's own release is not gated on it:
   - The batch release workflow re-runs §6 against the online pristine build (plan:779).
   - Those runs pin the build exactly (§6 (a) `isabelle=2025.2=<b>`, plan:786) and list conda-forge (plan:533).
   - The `build` job compares the hook fragment byte for byte against the channel's isabelle package (plan:528).
   - Feature packages pin the exact build (ruling 22).
   So a broken N cannot slip through to the feature packages. The real loss is the CI repository's own post-publication smoke test.

On the editor's rebuttal: I agree that whether the scan is written in Python or shell is the CI plan's choice. I also agree that U11's "stops solving" applies only to explicitly pinned or override-only installs. Neither point removes the need to state the consequences.

Severity: medium-to-major. It is major for the component repositories (silent and lasting) and minor for the CI repository, where most failures are loud and a later reviewed plan exists.

Experiment: I wrote /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C1/mk.py and run.sh, with output in run.out and run2.out. The setup was conda 25.11.1 with a private HOME, CONDARC and CONDA_PKGS_DIRS.

- Toy channel `chan`: isa 2025.2 build 0 (depends [], ISABELLE_ID 5533cd83156e), isa 2025.2 build 1 (depends python, 89701cf1768e), comp 0.2.0 (depends isa >=2025.2,<2025.3).
- Toy channel `forge`: python 3.13.0 and pip 25.0.

Results, identical under the libmamba and classic solvers:
- `--override-channels -c chan isa` installs build 0 (rc 0).
- `... -c chan comp` installs build 0 (rc 0).
- `... -c chan isa=2025.2=1` fails with rc 1, "nothing provides python needed by isa-2025.2-1".
- `... -c chan -c forge isa` and `... -c chan -c forge comp` install build 1 (89701cf1768e).
- run.out: with python present but no pip, the solver still picked build 0, because conda's default add_pip_as_python_dependency makes python require pip.

I also checked:
- the 2025.2-0 post-link text in ~/miniconda3/pkgs/isabelle-2025.2-0;
- every --override-channels line in all workflows under contrib (only Performant_Isabelle_ML, auto_sledgehammer and isabelle-packaging-ci's build.yml, release.yml and probe workflows omit conda-forge);
- the Performant_Isabelle_ML verify steps (they build sessions and call Foreign);
- rescue_foreign.ML.

Recommended fix: The smallest fix has two parts.

(1) Add one point to decision 12:

"isabelle 依赖 python 的后果（线上渠道没有 python；只带本地或线上渠道的 --override-channels 安装在 2025.2-0 还在渠道上时静默装上 2025.2-0，钉死 build 则报 nothing provides python，实测 review-ipc4/defender-C1/run2.out）：
- build.yml:1012、1203、1217、1286 与 release.yml:115 的渠道列表加 -c conda-forge，或者 CI 计划把 python、pip 及其依赖镜像进本地渠道，二选一由 CI 计划定；
- release.yml 的冒烟改装 isabelle=2025.2=<刚发布的 build 号>，并断言 isa/etc/ISABELLE_ID 是 89701cf1768e；
- 第 4 点的改写清单加 recipe.yaml:182-184、235-237 和 PACKAGING_DESIGN.md:737。"

(2) In decision 14, next to the Isa-Mini item, list an edit for the maintainers of the two component repositories. It must land before their first release after §5 step 8:
- Performant_Isabelle_ML release-conda.yml:423-425 and :527-529;
- auto_sledgehammer release-conda.yml:195-197 and :273-274;
- each gains -c conda-forge, with the "keep conda-forge out" reason at :420-422 reconsidered;
- the verify job asserts that the installed isabelle's ISABELLE_ID is the official changeset, so a fallback can never pass silently.

Leave out PACKAGING_DESIGN.md:87. A §5 step 6 mention is optional, because the CI plan's own run there exposes the Job F, G and H failures loudly.

**Judge: partially_confirmed → author_fixes_no_rereview.** Add a point to decision 12 (plan:553-579) on the consequences of the python dependency stated at plan:561.

Facts to state:
- The live channel has no python (plan:533-534).
- An --override-channels install that names only the local or live channel silently installs 2025.2-0 while that build stays online (§6 (e), plan:793).
- An exact pin fails with 'nothing provides python' (review-ipc4/defender-C1/run2.out).

Requirements on the CI plan:
- build.yml:1012, :1203, :1217, :1286 and release.yml:115 add -c conda-forge. The CI plan may instead mirror python, pip and their dependencies into the local channel; conda makes python require pip, so a python-only mirror still falls back (defender-C1/run.out).
- release.yml's smoke installs isabelle=2025.2=<the build just published> and asserts that etc/ISABELLE_ID is 89701cf1768e.
- Point 4's rewrite list gains recipe.yaml:182-184 and :235-237, and PACKAGING_DESIGN.md:737.

In decision 14, next to the Isa-Mini item (plan:610), list one edit for each of two component repositories' maintainers, to land before their first release after §5 step 8:
- Performant_Isabelle_ML release-conda.yml:423-425 and :527-529 (reconsider the reason given at :420-422);
- auto_sledgehammer release-conda.yml:195-197 and :273-274.
Each adds -c conda-forge and asserts the installed ISABELLE_ID.

PACKAGING_DESIGN.md:87 stays as it is: the user command does not use --override-channels. Jobs F, G and H fail loudly, so naming the change in §5 step 6 is optional.

### C2 [major] Since ruling 30, decision 11's reuse key '(name, version, build string)' never matches, so every dispatch rebuilds and republishes every listed feature, against the plan's own example; the judge's unit-tested derivation was dropped silently, and the derivation ignores uploaded-but-unindexed files

Section: Decision 10 (build number); decision 11 build job and worked examples; §0 items 30 and 4; §10 row C3  ·  merged from: conda-conda-4, consistency-CONS4-4, landing-L3, user-U5, user-U14, landing-L9

**Statement.** Decision 11's build job downloads every already-published '(名, 版本, build string)' instead of rebuilding it (plan:524). Decision 10 gives every new feature build the number n = (highest build number of this package and version on the channel) + 1 (plan:496-497). The round-3 judge's C3 action set this reuse key (REVIEW3:633) when rev 3's build string was Isabelle2025_2_<isabelle build>_<n>. Ruling 30 restored Isabelle2025_2_<n> (plan:131-133). So the build string no longer says which isabelle build a feature package is pinned to, and the build string of a package about to be built is unpublished by construction.

Read literally, every feature listed in `features` is therefore rebuilt and republished with a new n on every dispatch. That contradicts the HOL-only example, in which expose_foreign and future_assign_interrupt '已发布、build 直接下载' (plan:547-548). Implemented literally, every user's `conda update --all` relinks the unchanged lower features. The pre-unlink of each relinked lower feature reverses the whole chain above it, and then the post-link re-applies it (plan:469). Measured: four heap notices for one such update (review-ipc4/critic-user/run2.out case c2).

The owner chose ruling 30 after the author said the two forms have no mechanical difference: '两种写法在机制上没有区别 ... isabelle 构建号写进去纯粹是给人看的' (transcript line 7577). Decision 11's reuse key shows that statement was wrong. Ruling 30 still stands, because the fix below needs no build-string change, but the statement belongs in §0's list of the author's corrections.

Further defects in the same derivation:
(a) The judge required 'The derivation is one unit-tested function' (REVIEW3:636). Neither decision 11 nor decision 15 (plan:612-661) contains such a function or test, and §10's C3 row (plan:880) does not mention that it was dropped.
(b) n is read from noarch/repodata.json (plan:523). publish-conda.yml uploads first (:193-203) and re-indexes afterwards (:205-236), while its guard lists the storage bucket (:159). Files that were uploaded but never indexed are invisible to the derivation. The plan itself predicts exactly that state from today's broken banner step (plan:243-245). Once the run's artifact has expired, every new dispatch derives the same n, builds different bytes, and is refused, because the plan allows resuming only by re-running the failed job (plan:539-540). The plan states no artifact retention for the batch workflow.
(c) No `concurrency:` group stops two dispatches from deriving the same n. The channel's convention has one (Isabelle_RPC release-conda.yml:38-41).
(d) The worked examples count wrongly. The chain has seven features (plan:15). The HOL-only example says '七个新 tag' while two of the seven are unchanged, so five are new (plan:547). The new-isabelle-build example says 'eight feature packages' (plan:549-550), but there are seven.

Fix. Write one function in tools/, tested with pytest.
- A feature (F, v) is reused when the live noarch repodata has a record of (F, v) whose depends contain exactly `isabelle 2025.2 <isabelle_build>` (and, for a feature with a base, the same base pin). The highest such record is downloaded unchanged.
- Otherwise n = 1 + the highest build_number of (F, v). Skip any n whose filename the channel already serves: an HTTP HEAD on https://conda.qiyuan.me/noarch/<file> works without credentials, and .conda files are not CDN-cached (PACKAGING_DESIGN.md:735-739).
- The tool package is reused by version.
- Check that `features` forms one complete chain from <R>/pristine/<ID of isabelle_build> to the top.
Then also: add a workflow-level concurrency group; state the artifact retention; correct the counts; record the key change in §10's C3 row as a consequence of ruling 30; and add the correction of the Q5 statement to §0.

**Editor.** U14 proposes deriving n from the bucket listing, the same source the guard uses. The build job cannot do that, because it holds no R2 credentials: decision 11 passes them only to the publish call (plan:535-536). An HTTP HEAD on the public domain reaches the same objects without credentials, which is why the fix uses L3's form. L3's optional `rerender` input is not required. The plan should only state the consequence: under the reuse rule, a README or template fix cannot be republished at the same (F, v, isabelle build); it needs a new release.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

The central claim holds. Several side claims are overstated, and one is refuted.

CONFIRMED (core). Decision 11 says to download every already-published "(名, 版本, build string)" instead of rebuilding it (plan:524). Decision 10 gives every new feature build n = 1 + the highest build number of (F, v) on the channel (plan:496-497), and the build string is Isabelle2025_2_<n> (plan:23, :131-133). So the build string the workflow wants is unpublished by construction, and no feature is ever reused. That contradicts the HOL-only example, where expose_foreign and future_assign_interrupt "已发布、build 直接下载" (plan:547-548).

The judge's phrase (REVIEW3:634, not :633) was loose even in rev 3. It only worked through the round-3 defender's prefix form, "a build Isabelle2025_2_<b>_*". Ruling 30 removed that prefix. Neither §10 row C3 (plan:880) nor row C14 (plan:891) records this consequence.

The information is still available. Every live noarch repodata record carries its depends list verbatim (defender-C2/noarch-repodata.json), so the key can be the pin "isabelle 2025.2 <b>". The prototype proto/derive.py shows the difference. Read literally, the plan builds every feature in the HOL-only example and on a repeated dispatch. The depends key reuses the two unchanged features there, and rebuilds all seven only for a new isabelle build.

If the literal reading were implemented, every dispatch would republish every listed feature, and `features` lists the whole chain (plan:547). Each user's `conda update --all` would then relink unchanged lower features: a full reverse and re-apply, with heap notices. Round-3 defender-C3 relink/run.out measured that hook order for a rebuild with unchanged content. The critic's run2.out case c2 is the wrong evidence: it is the new-isabelle-build case, where the pins change and the relink is required (plan:549-550).

CONFIRMED (a): a deviation not named in §10. REVIEW3:636 requires "The derivation is one unit-tested function". Decision 11, decision 15 (plan:612-661) and §10 row C3 say nothing about it. Ruling 17 delegates tests to the author, but plan:5-6 promises that §10 names every deviation.

CONFIRMED (c), minor: there is no `concurrency:` group. Every release workflow in the channel has one (Isabelle_RPC release-conda.yml:39-41; release-isabelle-ai.yml:33-35; also release-json-spec, release-semantic-db, release-nunchaku and release-rocksdict). Two overlapping dispatches would derive the same n. The guard then refuses the second (publish-conda.yml:182-187). That wastes the run but corrupts nothing. The plan's only protection is a manual precondition (plan:543-544).

CONFIRMED (d), trivial: plan:547 says "七个新 tag" (seven new tags), but only five are new. plan:549-550 says "八个 feature 包" (eight feature packages), but the chain has seven (plan:15, :493-495).

CONFIRMED (b), narrower than stated. n is read from repodata (plan:523), but the guard lists the bucket (publish-conda.yml:159). A file can be uploaded but missing from the index in two ways:
- one of the fallible steps after the upload fails (:138-140);
- a publish from another repository pushes a stale index over it (:293-297).

Such a file is invisible to the derivation, so a new dispatch picks the same n and is refused. Two escapes exist. A re-run of the failed job works, but needs the artifact, and the plan states no retention for this workflow (it states 7 days only for the CI artifact, plan:567). Alternatively, any later publish from any repository re-pulls the whole bucket and re-indexes it (:39-43, :205-212). An HTTP HEAD needs no credentials (head.out: 200 for an existing file, 404 for a missing one, cf-cache-status DYNAMIC).

REFUTED or overstated:
- The requested §0 correction of the author's Q5 statement (transcript line 7577) is refuted. That statement was right in substance: b is in every record's depends, so in both build-string forms the reuse test is a one-line lookup in the same repodata. The defect is a sentence that was not updated, not an owner misinformed. Ruling 30 is unaffected.
- "The plan predicts that state from today's banner step" is pre-empted. Decision 12 point 5 makes fixing the banner a prerequisite of §5 step 6 (plan:571-572), and the batch publish happens only in step 8.
- Two parts of the proposed fix are not needed for this defect. The base-pin condition is redundant, because base_pin is fixed per (F, v) by provenance (plan:499). The complete-chain check is optional: the accept legs already exit 3 on a broken chain (plan:325-327).

On the editor's note: it is right. The build job holds no R2 credentials (plan:535-536), so HEAD is the correct probe, and no rerender input is needed. The plan should state the consequence that a README or template fix at the same (F, v, isabelle build) is not republished.

Severity: major is defensible for the core, because decision 11 is under re-review and the literal implementation is costly for users. The fix is a few sentences.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C2/. Nothing outside it was modified.

1. noarch-repodata.json: a read-only GET of https://conda.qiyuan.me/noarch/repodata.json. Every record has `depends` verbatim, for example 'isabelle >=2025.2,<2025.3'.
2. proto/derive.py and proto/derive.out compare two readings of the derivation on that repodata, after adding seven v1 feature records pinned to isabelle build 1:
   - the plan's literal reading: n = max+1, then reuse if (name, version, build string) is already published;
   - the fixed reading: reuse a record whose depends contain 'isabelle 2025.2 <b>'; otherwise n = max+1, skipping any filename the channel already serves.
   Results:
   - HOL-only light 2 at build 1: the literal reading builds all seven; the fixed reading reuses expose_foreign and future_assign_interrupt.
   - New isabelle build 2: both readings build all seven with n=1.
   - The same dispatch again: the literal reading rebuilds; the fixed reading reuses.
   - A file that was uploaded but not indexed: with repodata alone the derivation picks n=1, which the guard would refuse; with the HEAD probe it picks n=2.
3. head.out: HEAD on an existing .conda gives 200, on a missing one 404, with cf-cache-status DYNAMIC and no credentials.
4. Read: plan:15, :23, :131-133, :496-499, :513-551, :567, :571-572, :612-661, :880, :891; REVIEW3:510-640; transcript line 7577 (python -I); publish-conda.yml:1-330; Isabelle_RPC release-conda.yml:1-80; grep of `concurrency:` and `retention-days` across the isabelle-packaging-ci workflows; PACKAGING_DESIGN.md:734-739; critic-user/run2.out case c2.

Recommended fix: 1. Decision 11 (plan:524) and decision 10 (plan:496-497): replace the reuse key with one rule.
   - A feature (F, v) is reused when the live noarch repodata has a record of (F, v) whose depends contain exactly `isabelle 2025.2 <isabelle_build>`. The highest such record is downloaded unchanged.
   - Otherwise n = 1 + the highest build_number of (F, v) in that repodata (0 if there is none), raised past any n whose filename https://conda.qiyuan.me/noarch/<file> answers HEAD 200. This needs no credentials.
   - The tool package stays reused by version.
2. Make this derivation one function with a pytest covering four cases: the HOL-only example, a new isabelle build, a repeated dispatch, and a file that was uploaded but not indexed. Either way, say so in §10 row C3.
3. Add a workflow-level `concurrency: {group: release-features, cancel-in-progress: false}`, following the channel's convention (Isabelle_RPC release-conda.yml:39-41).
4. State the artifact's retention, and that "re-run failed jobs" works only while the artifact exists.
5. Correct the counts: plan:547 should say seven tags, five of them new; plan:549-550 should say seven feature packages.
6. In §10 rows C3/C14, record that ruling 30 moved the reuse key from the build string to the isabelle pin in depends.
7. Add one sentence: a README or template fix at the same (F, v, isabelle build) is not republished; it needs a new release tag, or it arrives with the next isabelle build.
8. No §0 correction of the Q5 statement is needed, and no base-pin condition or chain check is required for this defect.

**Judge: partially_confirmed → author_decides_then_rereview.** Replace the reuse key of decision 11 (plan:524) and the derivation of decision 10 (plan:496-497) with one function in tools/, tested with pytest:
- reuse (F, v) when live noarch/repodata.json has a record of (F, v) whose depends contain exactly 'isabelle 2025.2 <isabelle_build>'; download the highest such record unchanged;
- otherwise n = 1 + the highest build_number of (F, v), or 0 if there is none, raised past any n whose filename https://conda.qiyuan.me/noarch/<file> answers HEAD 200 (no credentials needed);
- reuse the tool package by version.
The tests cover the HOL-only example, a new isabelle build, a repeated dispatch, and an uploaded-but-unindexed file (defender-C2/proto/derive.py).

Also:
- add a workflow-level concurrency group, as in Isabelle_RPC release-conda.yml:39-41;
- state the artifact retention, and that 'rerun failed jobs' works only while the artifact exists;
- correct plan:547 to seven tags, five of them new, and plan:549-550 to seven feature packages;
- state that a README or template fix at the same (F, v, isabelle build) is not republished.

§10 rows C3 and C14 record that ruling 30 moved the key from the build string to the isabelle pin in depends, and that the unit-tested function REVIEW3:636 asked for is now specified.

Refuted: the §0 correction of the author's Q5 statement (jsonl 7577) is not needed. The pin sits in every record's depends, so the two build-string forms really are equivalent once the key is fixed. The base-pin condition is redundant (plan:499), and the complete-chain check is optional.

### C3 [major] Ruling 26's re-run already re-runs every feature package's post-link, so the copy of the hook fragment in the isabelle post-link is redundant; keeping both doubles the full diagnosis on the plan's own universal repair and freezes a tool-owned text inside the CI's package

Section: Decision 9 (last bullet and PKG_NAME rule); decision 12 point 2; decision 11 build job; decision 1 frozen interface; decision 15 counts; Appendix A  ·  merged from: conda-conda-1, consistency-CONS4-1, engine-engine-5, user-U4

**Statement.** Rev 4 puts two mechanisms into the pristine isabelle post-link and never reconciles them. The first is the hook fragment, a whole-chain apply (decision 9, plan:486-488; decision 12 point 2, plan:560). The second, from ruling 26, re-runs the post-link of every installed package that depends on isabelle (plan:112-118, :561-563). Every feature package depends on isabelle through its exact pin (plan:498), and its post-link is that same fragment (plan:432-456, :467-468).

conda writes package records only after all post-links have run (core/link.py:969-999; plan:213-214), and it renames the records of unlinked packages to .c~ (path_actions.py:1152-1164). So during the isabelle post-link, the scan finds exactly the installed packages that are NOT in the current transaction. Whenever isabelle is relinked, each installed feature package is therefore in one of two cases. Either it is in the transaction, and its own post-link runs. Or it is not, and the scan re-runs its post-link. In neither case does the isabelle copy of the fragment do anything the feature hooks do not already do. Ruling 13 ('the new isabelle build's post-link re-applies the installed features', plan:66-67) is met by ruling 26's re-run alone. The author's own advice to the owner even listed feature packages in the set the scan would re-run ('今天这个集合恰好就是该重跑的那些：组件包（登记）和 feature 包（幂等 apply）', transcript line 7364).

The copy has costs.
(1) Duplicate diagnoses on the plan's own universal repair. The plan prescribes `conda install --force-reinstall isabelle` everywhere (plan:481, :736, :748). In that transaction, a CONFLICT that survives the repair produces two full diagnoses: one from PKG_NAME=isabelle, and one from the re-run of the top feature, which runs with its own PKG_NAME (plan:475-477). Every other feature adds a one-line notice. Measured on a toy channel built from the plan's verbatim hooks with conda 25.11.1: 'FULL: 2 ONE-LINE: 2' (review-ipc4/critic-conda/run2.out:58-69); critic-user/run2.out cases e2' and e3 agree. With the tool removed, the 'is not installed' line appears n+1 times (critic-user/run3.out case k). Decision 15's count list (plan:646) has no shape for 'isabelle linked, top feature not linked', which is exactly this repair.
(2) A tool-owned frozen text lives inside another repository's package. Decision 11 must check it byte for byte (plan:527-528). The .bat exists only in the win-64 isabelle package (recipe.yaml:89-170 is the Windows branch, :171-232 the unix branch), so the linux build job must download a package of about 0.8-1.1 GB just for that check (pkgs/isabelle-2025.2-0.conda is 770 MB; pkgs/isabelle-2025.2-89701cf1768e_0.conda is 1.1 GB). Decision 1 then binds the isabelle package to the tool's command line for all of 1.x (plan:294-296).
(3) Every relink pays for one extra whole-chain replay.

**Editor.** engine-5 proposes keeping both copies and letting the top hook write the full diagnosis only when its own conda-meta record is absent, that is, when conda is linking it now. This is rejected. It keys user-visible behaviour on conda's internal order of record writes (link.py:961-971), which is not an interface, and it keeps the redundant copy and its cross-repository byte check. conda-1's point (5), that calling the tool breaches ruling 2, overreaches: ruling 2 is about isabelle-packaging-ci not shipping patches. The coupling argument stands without it. Dropping the fragment does not reverse ruling 13: the pristine build's post-link still causes the re-application, through the re-run. But the owner approved ruling 13 when the fragment was the means, so the author must tell the owner about the change when presenting rev 5.

**Relaxation proposed by the editor.** Drop the fragment from the isabelle package. Its post-link becomes: the existing hint, then ruling 26's re-run, then exit 0. The first feature in the re-run order performs the whole-chain apply, which carries out ruling 13. Consequences:
- decision 12 point 2 asks only for the re-run;
- decision 11's byte check, and the isabelle download it needs, disappear;
- the isabelle package leaves decision 1's frozen interface and need not know the tool's command line;
- decision 9's PKG_NAME rule shrinks to 'only the hook of the highest installed feature writes the full diagnosis; an unset or unknown PKG_NAME behaves like it';
- decision 15's counts become: exactly one full diagnosis whenever that hook runs (as its own post-link or as a re-run), otherwise one-line notices only;
- add the `--force-reinstall isabelle` shape with a surviving CONFLICT to decision 15 and §6 (f), and update decision 15's toy isabelle package (plan:640) and Appendix A (plan:923-924).
This removes the duplicate diagnoses by construction and makes the CI package independent of the tool.

**Defender: confirmed** (needs owner: True).

I could not refute the core claim. Ruling 26's re-run makes the copy of the hook fragment in the isabelle post-link redundant.

1. Which packages the scan finds. conda first links every package in the transaction, then runs the post-links (conda core/link.py:938-967). It writes the new package records only after that (link.py:969-999). The old record of a package being unlinked is itself an UnlinkPathAction (link.py:125-130, path_actions.py:1209-1219), so it is renamed to *.json.c~ (path_actions.py:1152-1164). A conda-meta/*.json scan run inside the isabelle post-link therefore sees exactly the installed packages that are not in the transaction. I measured this: the scan found only the component package after `conda update --all` (my run-rev4.out:160-ish, rerun line 'found=isabelle-comp'), and found the component plus the non-transaction features in the B4 and B6 shapes. Every feature package depends on isabelle (plan:498), and its post-link always exists (plan:500-501) and is the fragment (plan:432, :467-468). So whenever isabelle is relinked, every installed feature's hook runs, either as its own post-link or as a re-run. The isabelle copy of the fragment adds nothing to ruling 13's effect (plan:66-67).

2. Arguments for keeping the copy, all rejected:
- Order dependence: component hooks only call `components -u`, which does not depend on patches (Isabelle_RPC/conda/recipe.yaml:148-158; plan:466).
- Defence in depth against a broken scan: both mechanisms use the same $PREFIX/bin/python. Component registration needs the scan to be correct anyway, and §6 (c) tests the scan on five legs.
- A 'tree not pristine' diagnosis from the isabelle hook: it cannot happen, because a pristine build's own post-link always runs on the official changeset.
- Record-order fragility: the relaxation's counts rely on conda writing records after post-links. The scan of ruling 26 already relies on that same order to avoid double runs, so the relaxation adds no new dependency.
- One edge case: in B6 (isabelle and a middle feature relinked), the records-only topological order re-ran dev_patches before feat_a. This is harmless, because every hook does a whole-chain apply.

3. The owner's intent supports dropping the copy. Ruling 26 came from the owner ('本质上我们是要重新执行后续依赖的 post link 脚本', jsonl 7303). The owner's marker proposal was aimed at feature packages (jsonl 7332). The author then told the owner that feature packages are in the re-run set ('feature 包（幂等 apply）', jsonl 7364). The same message also argued the reverse: that the feature re-run is unneeded because 'isabelle 的 post-link 本来就调工具'. With the no-marker ruling, the feature re-run cannot be avoided, so the fragment copy is the only one that can be removed.

4. The costs are confirmed.
- Duplicate diagnoses: rev 4's PKG_NAME rule (plan:475-477) gives two full diagnoses on the universal repair (critic-conda/run2.out:58-69, critic-user/run2.out:178,187). My own toy channel (hooks copied verbatim from the plan, conda 25.11.1) gives the same. With rev 4, FULL=2 in three shapes: isabelle alone, isabelle plus the top feature, and isabelle plus a middle feature (run-rev4.out:61,80,114). With the relaxation, FULL=1 in all three and also in the top-only shape (run-relaxed.out:56,73,105,114).
- Everything else is identical under the relaxation: one applied line, the same heap notices, components re-registered, `update --all` and the repair converge (run-relaxed.out:13-26,136-158).
- Plan:646 lists no shape for 'isabelle linked, top feature not linked', which is exactly the `--force-reinstall isabelle` repair.
- Coupling: the byte check (plan:527-528) ties a text the tool owns into the CI's package. Decision 1's frozen interface (plan:294-296) then covers the isabelle package, which has no upper bound on the tool version.

5. Narrowings:
(a) Download cost. The .bat exists only in the win-64 branch (recipe.yaml:89-170; .sh at :171-232). The check needs a unix package (770 MB) and the win-64 package (839,610,348 bytes, critic-conda/live/win-64.json). That download is pure overhead only with isabelle_from=channel, which is the publish mode and the mode of every re-release. With run:<id> the artifact is downloaded anyway. Moving the check to the accept legs would also avoid the download, but the coupling would remain.
(b) The relaxation removes only one of the n+1 'is not installed' lines: n remain (run-relaxed.out B2: 3 lines; rev 4: 4).
(c) The relaxation misses several places that need editing: glossary :35, §4 :731, §5 step 7 :776-777, §7 row (1) :811, §10 rows C8 :885 and C24 :901.

6. Why this is not a silent deviation. Rev 4 followed round-3 relaxations 5 and 9 (REVIEW3:121, :132), and those were written before ruling 26 existed. So rev 4 did not deviate silently; the redundancy is a new interaction between those relaxations and ruling 26. Rev 5 must say in §10 that it replaces them.

7. Engine-5's alternative (keying behaviour on whether the package's own record is absent) is rightly rejected. It keeps the redundant copy and the cross-repository check.

Experiment: I built a toy setup in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C3/ by copying critic-conda's channel generator and toy tool into src/. I added a 'relaxed' variant: the isabelle post-link is the hint, then the decision 12.2 re-run (src/rerun.py), then exit 0, with no fragment. In that variant the toy tool writes the full diagnosis only for the top feature's PKG_NAME, or for an unset or unknown one.

I ran the same scenario script (run.sh, run-slim.sh) with real conda 25.11.1 and a private HOME, CONDARC and pkgs, once per variant. The scenarios were: fresh create; --force-reinstall isabelle; tool removed with --force and then reinstalling isabelle; and, with an edited created file (CONFLICT), four relink shapes (isabelle alone, isabelle plus top, middle alone, isabelle plus middle, top alone); a tracked-file CONFLICT; the repair; and update --all to a new build with re-released features.

Results:
- run-rev4.out: FULL=2 ONE-LINE=2 for isabelle alone, isabelle+top and isabelle+middle (:61,:80,:114); 4 'not installed' lines (:39).
- run-relaxed.out: FULL=1 in the same shapes and in top-only (:56,:73,:105,:114); 3 'not installed' lines (:36).
- Both variants: one applied line and the same heap notices; component registrations kept (state lines :13-:158); the rerun log shows the scan finding exactly the packages outside the transaction.

I also read the conda source (link.py:125-130, 938-999; path_actions.py:1152-1164, 1209-1219), recipe.yaml:89-232, the live package sizes in critic-conda/live/*.json, REVIEW1:56, REVIEW3:121,132, and the session transcript at jsonl lines 7303, 7332 and 7364. I then deleted the toy environments and the package-cache copies to free space on /tmp.

Recommended fix: Adopt the editor's relaxation, with these edits.

(1) Decision 9, plan:486-488: the isabelle post-link is the existing hint, then ruling 26's re-run, then exit 0, with no fragment. Whichever feature hook runs first, as its own post-link or as a re-run, performs the whole-chain apply. Whenever isabelle is relinked, every installed feature's hook runs (link.py:969-999, path_actions.py:1152-1164).

(2) Plan:475-477: only the hook of the highest installed feature writes the full diagnosis. An unset or unknown PKG_NAME behaves like it.

(3) Decision 12 point 2, plan:560-563: require only the re-run.

(4) Decision 11, plan:527-528: delete the byte check.

(5) Decision 1, plan:294-296: the isabelle package is no longer bound to the tool's command line.

(6) Decision 15:
- plan:640: the toy isabelle package carries the re-run only.
- plan:646: exactly one full diagnosis whenever the top feature's hook runs, and it always runs when isabelle or the top feature is relinked; otherwise one-line notices only.
- Add the `--force-reinstall isabelle` shape with a surviving CONFLICT there and in §6 (f), plan:795.

(7) Reword plan:35 (glossary: 钩子片段 is copied only by feature packages), :731, :776-777, :811 and :923-924.

(8) In §10, rows C8 (:885) and C24 (:901): state that rev 5 replaces round-3 relaxations 5 and 9, because ruling 26 made them redundant.

(9) When presenting rev 5, ask the owner to confirm that ruling 13 is now carried out by ruling 26's re-run alone. The option the owner approved (REVIEW1:56) said the post-link 'calls the tool', and the author repeated that at jsonl 7364.

**Judge: confirmed → owner_decides.** Put owner question 1 first. If the owner confirms, make these edits.

- Decision 9 (plan:486-488). The isabelle post-link becomes: the existing hint, then ruling 26's re-run, then exit 0, with no copy of the fragment. State why every installed feature hook still runs on every isabelle relink: conda writes package records only after all post-links (link.py:938-999) and removes the record of every package it unlinks (RemoveLinkedPackageRecordAction, path_actions.py:1209-1219). So during the isabelle post-link the scan sees exactly the installed packages outside the transaction, and the packages inside it run their own post-links.
- Decision 12 point 2 (plan:560-563) asks only for the re-run.
- Delete decision 11's byte-for-byte check and the isabelle download it needs (plan:527-528).
- Decision 1 (plan:294-296) no longer binds the isabelle package to the tool's command line.
- The diagnosis rule (plan:475-477) becomes: only the hook of the top feature of the installed chain writes the full diagnosis; an unset or unknown PKG_NAME behaves like it.
- Decision 15 (plan:640, :646). The toy isabelle package carries only the re-run. The invariant becomes: exactly one full diagnosis whenever the transaction links isabelle or the top feature package, otherwise one-line notices only. Add the shape '--force-reinstall isabelle with a CONFLICT that survives' there and in §6 (f).
- Reword plan:35, :731, :776-777, :811 and Appendix A :923-924.
- §10 rows C8 and C24: rev 5 replaces round-3 relaxations 5 and 9, because ruling 26 made the copy redundant (review-ipc4/defender-C3/run-rev4.out against run-relaxed.out).

### C4 [major] Ruling 26's re-run includes indirect dependents, so every isabelle relink fires isabelle-semantic-data's post-link, which discards the user's cached vectors on the premise that it runs only when its payload changes; the owner's no-marker answer rested on the author's false statement that the re-run set contains only packages that should re-run

Section: §0 item 26; decision 12 points 2 and 7; §2.3; Appendix A; decision 15  ·  merged from: conda-conda-2, user-U1

**Statement.** Ruling 26's scan includes packages that depend on isabelle only indirectly ('含间接', plan:114; decision 12 point 2, plan:562). isabelle-semantic-data is one. Its only run dependency is isabelle-semantic-embedding >=0.3.0 (isabelle-packaging-ci/conda/data/isabelle-semantic-data/recipe.yaml:91-96), which in turn depends on isabelle >=2025.2,<2025.3 (Semantic_Embedding/conda/recipe.yaml:318). It is also a hard dependency of the isabelle-ai metapackage (live noarch repodata: isabelle-ai 0.3.0 depends on isabelle-semantic-data >=2026.10.9).

Its post-link runs `isabelle-semantics post-install-system-db` (recipe.yaml:80-89). The approved design of that hook relies on it firing 'exactly when the payload changes' (recipe.yaml:20-23; isabelle_semantics.py:1030-1037). The command deletes every real user-layer vector whose key has no user record (semantics.py:1567-1607). Those are the stand-in vectors the user's machine computed from the system database's text. A second run in a row deletes nothing, so the command passes decision 12 point 7's 'can be run again' requirement (plan:574). But each re-run with an unchanged payload throws away vectors that were still valid.

Ruling 26 fires the hook on every isabelle relink without any payload change: on every new isabelle build (routine under ruling 22), on every `--force-reinstall isabelle` (the plan's universal remedy), and on the first move off 2025.2-0. The user layer lives under ~/.cache and is shared by every environment on the machine, so a relink in one environment discards vectors that all environments use. Vectors are a lazy cache: missing ones are re-embedded on demand, and keys with user records are untouched. So the cost is repeated paid embedding-API calls and latency, not loss of user-written data. The plan mentions neither this package nor this command.

The owner accepted 'no marker' after the author stated that the set 'depends on isabelle (including indirectly) and has a post-link script' is today exactly the packages that should re-run, namely component packages and feature packages (transcript line 7364). This package shows that statement was false. In the same message the author named the one case in which a marker would be needed: 'a future package that depends on isabelle but whose post-link cannot be run again'. That package is already published.

Fix. Return to the owner with the corrected premise and three options:
(a) re-run only packages that depend on isabelle directly. Every component package and every feature package does: live repodata for isabelle-rpc, isabelle-performant-ml, isabelle-semantic-embedding, isabelle-minilang, auto-sledgehammer and isabelle-nunchaku, plus plan:498 for features. isabelle-semantic-data does not. This amends the '含间接' wording, which was the author's own proposal.
(b) make semantic-data's hook purge only when the installed payload's identity has changed. This amends VECTOR_INVALIDATION_PLAN §7's approved 'no remembered created_at'.
(c) the reverse 'do not re-run me' marker the author mentioned.
Published post-links are frozen. (b) and (c) therefore help only after every user has updated semantic-data, a 9.6 GB package. Only (a) also works for the versions already installed.
Whichever option is chosen:
- name isabelle-semantic-data in §2.3 and decision 12;
- reword decision 12 point 7 and the RELEASE_CHECKLIST addition to 'running it again when the package's own files did not change must have no effect';
- add a hook-layer case: an indirect dependent whose post-link counts its runs, followed by `--force-reinstall isabelle`.

**Editor.** conda-2's 'deletes the user vector cache' overstates the harm. User-authored records and their vectors are untouched (semantics.py docstring), and missing vectors are legal and re-embedded lazily. The severity stays major for three reasons: the cost recurs on every isabelle relink, it reaches every environment on the machine, and the owner's ruling rests on a premise that this package falsifies. That premise is why the case goes back to the owner rather than being fixed by the author.

**Relaxation proposed by the editor.** Option (a), re-running direct dependents only, states the real contract: a package whose post-link acts on isabelle's tree or user directory declares a direct dependency on isabelle. Under this rule, the topological order over indirect edges becomes a convenience rather than a correctness requirement, and the rule works for every already-published package without republishing anything. It needs the owner's approval, because it amends the '含间接' in ruling 26's text.

**Defender: confirmed** (needs owner: True).

I could not refute the defect. Each factual link checks out.

1. The scan includes indirect dependents. Plan:114 (ruling 26) and plan:562 (decision 12 point 2) both say "（含间接）". Plan:117 says every package that depends on isabelle and has a post-link re-runs.

2. isabelle-semantic-data is an indirect dependent with a post-link.
- Its only run dependency is isabelle-semantic-embedding >=0.3.0 (isabelle-packaging-ci/conda/data/isabelle-semantic-data/recipe.yaml:91-96). That package depends on `isabelle >=2025.2,<2025.3` (Semantic_Embedding/conda/recipe.yaml:318).
- Its post-link runs `isabelle-semantics post-install-system-db` (recipe.yaml:80-89).
- I range-fetched both published packages from conda.qiyuan.me. 2026.10.09.0024 (9.65 GB) ships the .sh and .bat hooks; 2026.07.26.1711 ships no link scripts.
- Live noarch repodata: isabelle-ai 0.3.0 depends on isabelle-semantic-data >=2026.10.9, so every isabelle-ai 0.3.0 user has the hook.
- Every other package in the channel that has hooks (isabelle-rpc, isabelle-performant-ml, isabelle-semantic-embedding, isabelle-minilang, auto-sledgehammer, isabelle-nunchaku) depends on isabelle directly. isabelle-ai and isabelle-mcp have no hooks. Feature packages pin isabelle directly (plan:498).

3. The hook's design assumes it fires only when the payload changes (recipe.yaml:20-23; isabelle_semantics.py:1033-1038). The command deletes every real user-layer vector whose key has no user-layer record (semantics.py:1581-1584, 1608-1631). Back-to-back runs are idempotent (:1607), so it meets plan:574's "可以重复执行" and plan:944-945. The plan never names the package or the command (grep).

4. The user layer is platformdirs' ~/.cache/Isabelle_Semantic_Embedding (Isabelle_RPC/Isabelle_RPC_Host/paths.py:41-47). Every environment of the user shares it.

5. The author's premise was false. Transcript JSONL line 7364 says the set "依赖 isabelle（含间接）、且环境里有它的 post-link 脚本" is today exactly the component and feature packages. Line 7318 says "这个渠道里所有钩子都是幂等的". The owner answered "很好" and moved on (line 7367). As a small aside, plan:117-118 quotes the owner's "赞同你的建议" for the no-marker point, but that reply (line 7404) answered the later question about pinning every package. The owner's own alternative (line 7320, a positive marker on feature packages) would not have selected semantic-data, so the false premise mattered to the decision.

6. Toy experiment (conda 25.11.1, run1.out):
- With the scan as written, `conda install --force-reinstall isabelle` found `toy-semantic-embedding toy-semantic-data` and re-ran the data hook, which logged `deleted=5` with the payload unchanged.
- With a direct-only scan, the same command re-ran only the embedding package. Its component registration came back, and the 5 stand-ins survived.

Corrections to the challenge:
(i) Option (b) does not wait on the 9.6 GB package. The frozen hook only calls `$PREFIX/bin/isabelle-semantics`, and that command's logic lives in the isabelle-semantic-embedding library (isabelle_semantics.py:1030-1063). That package is about 0.7 MB. So (b) would reach already-installed data versions through a library update. Option (c) does need a republished data package, or a hard-coded exclusion list in the isabelle package, which would be a hack.
(ii) The cost depends on the embedding model. The 2026.10.09 manifest ships a Qwen3-Embedding-8B vector store (1,434,689 entries against 1,444,606 records). Users on that default model (semantics.py:2944) lose only stand-ins for the small set of keys the system store lacks. The VECTOR_INVALIDATION_PLAN §7 measurement agrees: 14,688 of the 14,689 deleted vectors resolved again from the system store at no cost. The cost is large only for users of a model the payload does not ship (the L14 case).
(iii) "Routine new builds" overstates how often new isabelle builds happen.
(iv) The toy also shows a problem that exists today, independent of ruling 26: creating a second environment with the same payload already purges the shared cache. That belongs to Semantic_Embedding, not to this plan.

None of these weakens the defect. The plan has a new trigger set, an unnamed victim package, and a contract (decision 12 point 7) too weak to exclude it.

On the editor's relaxation: I agree that option (a) is the elegant fix. "Depends directly on isabelle" is a property that every package needing a re-run already has. It works for every package already published, and it needs no marker and no republishing. Two refinements:
- The contract must go both ways. A package whose post-link acts on $PREFIX/isa or on the Isabelle user directory must depend on isabelle directly. And every direct dependent's post-link must have no effect when re-run while the package's own files are unchanged. Otherwise a future direct dependent with a non-repeatable hook brings the problem back.
- Keep the topological order among the direct dependents. It costs nothing, matches conda's own link order and keeps etc/components in the same order. Correctness does not need it.

Experiment: All experiment files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C4/.

(1) Published packages, by HTTP range reads (rangehook.py, infohook.py, infopaths.py, rangemanifest.py with rclass.py):
- isabelle-semantic-data 2026.10.09.0024 contains bin/.isabelle-semantic-data-post-link.sh and Scripts/.isabelle-semantic-data-post-link.bat, both calling post-install-system-db. 2026.07.26.1711 contains no link scripts. Both depend only on isabelle-semantic-embedding >=0.3.0.
- The 2026.10.09 MANIFEST lists semantics.lmdb with 1,444,606 entries and vector_Qwen__Qwen3-Embedding-8B.lmdb with 1,434,689.

(2) Live repodata: noarch-live.json, fetched today. isabelle-ai 0.3.0 depends on isabelle-semantic-data >=2026.10.9. The critic's snapshot (critic-conda/live/*.json) shows every package with hooks except semantic-data depending on isabelle directly.

(3) Toy conda run: run1.sh, results in run1.out.
- Setup: the owner's conda 25.11.1 with private HOME, CONDARC and CONDA_PKGS_DIRS, and only a file:// channel. It skips conda-forge because /tmp is a nearly full tmpfs; I deleted my earlier download.
- Generator src/mkchan_c4.py is derived from the critic's mkchan4.py. Toy isabelle build 1 runs decision 12 point 2's transitive scan (src/rerun.py). Build 3 runs a direct-only scan (src/rerun_direct.py).
- toy-semantic-embedding depends on isabelle and runs `components -u`. toy-semantic-data depends only on the embedding package; its post-link deletes ~/.cache stand-ins and logs each run.
- Result A, scan as written: `--force-reinstall isabelle` gave RERUN-SCAN found=`toy-semantic-embedding toy-semantic-data` and `PURGE ... deleted=5` with the same payload. The registration was restored.
- Result A2: a second environment with the same payload also purged the shared cache (`deleted=5`). This happens today, independent of ruling 26.
- Result B, direct-only scan: found=`toy-semantic-embedding`. The registration was restored, no purge ran, and 5 stand-ins remained.

(4) Session transcript JSONL, extracted with ext.py (excerpt in t7364.txt): lines 7303, 7318, 7320/7332, 7364, 7367, 7402, 7404.

Recommended fix: Smallest fix. It needs the owner's approval, because "含间接" is in ruling 26's text.

1. Add an entry to the plan's list of corrections to the owner (plan:141-) and put the question to the owner. The statement at line 7364, that today's set is exactly the component and feature packages, was false: isabelle-semantic-data 2026.10.09.0024 depends on isabelle only through isabelle-semantic-embedding, and its post-link purges the user's shared vector cache. Recommend option (a).

2. If the owner approves (a): in §0 item 26 and decision 12 point 2, replace "（含间接）依赖 isabelle" with "直接依赖 isabelle（depends 里有名为 isabelle 的条目）". Keep the topological order among those packages.

3. Make the contract two-sided in decision 12 point 7, in the RELEASE_CHECKLIST §4 addition and in Appendix A (plan:944-945):
- A package whose post-link acts on $PREFIX/isa or on the Isabelle user directory must depend on isabelle directly.
- A direct dependent's post-link must have no effect when re-run while the package's own files are unchanged. "Can be run again" is not enough.
Add a release-time check: a hook that names isa/bin/isabelle or isabelle_patch_control requires `isabelle` among the run dependencies.

4. In §2.3 and decision 12, name isabelle-semantic-data (recipe.yaml:80-96, semantics.py:1567) as the indirect dependent whose post-link must not be re-run, and say why.

5. Add a hook-layer case to decision 15, the shape of run1.sh: a direct component package plus an indirect-only package whose post-link counts its runs. After `--force-reinstall isabelle`, the registration is restored and the run count does not change.

If the owner prefers (b) instead: it belongs to the Semantic_Embedding owner. It is a change to the library command (isabelle_semantics.py:1030), shipped in the small isabelle-semantic-embedding package; the 9.6 GB data package does not need republishing. It amends VECTOR_INVALIDATION_PLAN §7, and it would also fix the existing purge that fires when a second environment is created. Reject (c): it needs a republished data package or a hard-coded exclusion list in the isabelle package.

**Judge: confirmed → owner_decides.** Put owner question 2. Also add an entry to the author's corrections (plan:141-148): the statement at jsonl 7364, that the re-run set is today exactly the component and feature packages, was false.

Whatever the owner chooses:
- name isabelle-semantic-data in §2.3 and decision 12 (isabelle-packaging-ci conda/data/isabelle-semantic-data/recipe.yaml:16-23, :80-96; Semantic_Embedding/conda/recipe.yaml:318);
- reword decision 12 point 7, the RELEASE_CHECKLIST §4 addition and Appendix A plan:944-945 to: running it again while the package's own files are unchanged must have no effect;
- add a hook-layer case to decision 15. A direct component package plus an indirect-only package whose post-link counts its runs; after --force-reinstall isabelle, the registration is back and the count has not changed (defender-C4/run1.sh).

If the owner chooses (a), additionally:
- write '直接依赖 isabelle（depends 里有名为 isabelle 的条目）' in §0 item 26 and decision 12 point 2;
- keep the topological order;
- state the two-sided contract (a post-link that acts on isa/ or the Isabelle user directory requires a direct dependency on isabelle; a direct dependent's post-link has no effect when re-run with its own files unchanged), plus a release-time check.

Correction to the challenge: option (b) reaches already-installed data versions through the small isabelle-semantic-embedding package, because the frozen hook only calls $PREFIX/bin/isabelle-semantics.

### C5 [major] Decision 6 claims ruling 28's release gate keeps multi-level files out of every released chain, but only the optional strong form does; a repeated block, or a two-feature chain that passes every mandatory gate, installs correctly and then reads CONFLICT with an irreversible pre-unlink and a burned version

Section: Decision 6 (plan:385-386); decision 16 points 5 and 9; ruling 28 (plan:125-127); §4 CONFLICT text; decision 15 (plan:619)  ·  merged from: engine-engine-1, consistency-CONS4-3

**Statement.** Decision 6 says that under ruling 28's release gate no file on a normally released chain fits several levels, and that if one does, someone edited the tree ('出现就是有人改了树', plan:385-386). The only mandatory form of that gate, decision 16 point 5 (plan:671-672), compares blob ids. It therefore rejects only exact revisits, that is, a file whose content returns to its content at a lower tag.

A file can fit several levels without any revisit, when a text block repeats. The plan's own test list has this case reading CONFLICT (plan:619). The round-3 judge offered the strong form because it 'also catches a repeated block whose correctly applied tree would otherwise read CONFLICT' (REVIEW3:1148). Rev 4 keeps that form optional ('更强的可选形式', plan:672). Gate (c) (decision 16 point 1) applies and reverses one feature on its own base, so it sees only that feature's own two levels.

Two reproductions:
- One feature, a repeated block. The feature changes the first of two identical blocks. The blob ids at base and tip differ. On the tip content, `git apply -R` succeeds (level 1) and `git apply` also succeeds (level 0), and applying again writes a second change (review-ipc4/critic-consistency/repeat/; review-ipc3/defender-C7/repeattop.out).
- Two features, found by random search (13 hits in 11,400 trials, review-ipc4/critic-engine/search/). Feature A deletes a line. Feature B inserts, next to A's edit, a copy of A's original context. The three blob ids are distinct, both gate (c) round trips pass, and the whole-chain apply on a fresh tree gives exactly tag B. Then `status` reports CONFLICT for A and for B (`src/R.ML fits [0, 2]`), and B's pre-unlink moves nothing (critic-engine/xf.out).

In both cases a correctly installed release reads CONFLICT. The §4 text then tells the user that they edited the file and that `--force-reinstall isabelle` will fix it, but the reinstall restores the same CONFLICT (plan:733-737). Release tags cannot be moved (tools/hooks/reference-transaction:28-29; make-patches:86-88), so the version is burned. (b2) sees the problem only after the tags exist (plan:692; §5 steps 3-4).

Fix. Make the strong form mandatory in decision 16 point 5, and run it before anything is written or tagged:
- walk the chain below the new tag through the base_tag lines of the annotated release tags (make-patches:194-210), down to <R>/pristine/<ID>;
- for every changed file, take its content at every chain state (pristine, each lower tag, the tip) with `git show`;
- call the tool's own level function on each, imported the way gate (c) imports apply_to;
- require each state to fit exactly its own level.
Measured on today's chain: 0 bad states over 40 files, 305 git calls, 0.43 s (critic-engine/real.out). Then reword decision 6 to cite this gate, make the §4 CONFLICT text also cover 'fits several levels', and add both toys to decision 16 point 9's refusal tests.

**Editor.** engine-1's remark that 'optional' is not something an implementer can build is rhetoric. The substantive point is that decision 6's guarantee depends on that form. The fix adds to ruling 28's gate and does not reverse it. The owner ruled the blob comparison, and the stronger check refuses a strict superset of what it refuses.

**Relaxation proposed by the editor.** Let the strong check be the gate. An exact revisit always fits two levels, so the blob comparison becomes a special case of it. Keep the blob comparison only as the message that names the earlier tag. One gate, stated as the invariant decision 6 relies on (every state of a released chain fits exactly one level), replaces a weaker gate plus a claim it cannot back.

**Defender: partially_confirmed** (needs owner: False).

The core of the challenge holds, and in a stronger form than C5 states. But both of C5's own reproductions are caught before anything reaches users. Its account of the consequences needs correcting.

What is confirmed.
- Decision 6 claims that under ruling 28's release gate a normally released chain has no file that fits several levels, and that if one does, someone edited the tree (plan:385-386). The mandatory gates do not back this claim.
- I built a three-feature toy, xf3: critic-engine's xf chain plus a third feature F3 that edits the same file far away. It passes every mandatory gate in rev 4:
  - the blob comparison of decision 16 point 5 (plan:671-672);
  - gate (c) for each feature, run through the tool's own apply_to/unapply_from (plan:665-666, make-patches:184-195);
  - (b2) on the chain top (plan:685-692).
- Yet the published chain fails for users:
  - Installing the prefix up to F2 (the package isabelle-F2 on its own) gives exactly tag F2's bytes, and status then reads CONFLICT for F1 and F2 (src/R.ML fits [0, 2]).
  - Removing the top package F3 leaves the remaining chain in CONFLICT.
  - A pruning removal leaves a residue: its lower pre-unlinks still see F3 in features.d, because conda runs every pre-unlink before it unlinks any file (core/link.py:938-952).
  - For the prefix user, the §4 CONFLICT text says the file "matches no level" (plan:733). Its fix, `--force-reinstall isabelle`, re-applies onto pristine and lands in the same CONFLICT.
- Two reasons nothing else catches this:
  - (b2) checks only pristine to the chain top and back, never a middle state or a prefix chain.
  - §6 installs only light (plan:786) and the smoke job installs only the top (plan:537).
- Today's real chain has the needed shape: src/Pure/Syntax/syntax_phases.ML is changed by light_locale, local_type_abbrev and dev_patches. The strong form finds 0 bad states on it today (critic-engine/real.out, 0.43 s), so the defect is latent.
- Only the strong form catches xf3. It does so at F2's own release, which is before anything is written or tagged (point 8, plan:679).

What is refuted or overstated.
1. The one-feature repeated block passes no mandatory gate in rev 4. Rev 4 changed gate (c) to the tool's apply_to/unapply_from (plan:665). Those follow decisions 5-7 (plan:355, 413, 423) and so treat a multi-level file as CONFLICT. On the tip, unapply_from reads `CONFLICT src/R.ML fits [0, 1]`, the backward tree differs from the base, and make-patches refuses before writing or tagging. The variant where an upper feature makes the edit (repeattop) is refused the same way. The round-3 judge's remark that the strong form "also catches a repeated block" (REVIEW3:1148) dates from when gate (c) was a plain round trip.
2. The two-feature xf case does pass the blob gate and gate (c). But (b2) fails on it, because unapply cannot reverse the CONFLICT file, so the roundtrip job blocks publish and no user installs it. The real cost is late detection: §5 cuts every tag at step 3 and runs (b2) only at step 4 (plan:766, 772). The tag of the faulty feature, and of every feature tagged on top of it, is then used up, since tags never move (reference-transaction:28-29, make-patches:86-88).
3. "Irreversible pre-unlink" overstates it. After a full removal, the residue block's `--force-reinstall isabelle` does restore pristine. The real dead end is the prefix user's CONFLICT advice described above.

Section 10's C7 row (plan:884) honestly follows the judge's action, which kept the strong form optional. So this is not a silent deviation. The defect is that decision 6 claims more than the gates it cites can deliver.

The editor's relaxation is sound.
- An exact revisit always fits two levels. The tip content equals the content at a lower level j, and both its own level and level j replay exact recorded diffs.
- The strong form refused every revisit toy I tried: revert, a three-feature revert and create-then-delete.
- So the strong check refuses everything the blob comparison refuses, plus the offset-ambiguous chains. It stays inside ruling 28.
- One gate stated as decision 6's invariant is more elegant than a weaker gate plus a claim it cannot back.
- Keep the blob equality only to choose the message. The remedies differ: a revisit goes into a new release of the lower feature (ruling 28), while an offset ambiguity needs its change or context reworked.
- One caveat: run the check at every release, on the chain that ends at the new tag. A state's fitting levels on the full chain are only a subset of those on a prefix chain, so checking only the top chain could miss a prefix ambiguity.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C5/.

Setup:
- ipc4.py is critic-engine's literal prototype of rev 4 decisions 3-8, with gate-strong as the optional strong form. I copied it unchanged.
- harness.py builds a toy repository with tags, splits the patches the way make-patches does, and runs:
  - the blob gate;
  - gate (c) per feature: one-feature features.d, the tool's apply then unapply on `git archive <base>`, forward compared with the tip and backward compared with the base;
  - (b2) on the chain top: tool apply compared with `patch -p1 -F0` of the whole diff, then tool unapply compared with pristine;
  - the strong form at each release, on the prefix chain;
  - user scenarios.
- I used git 2.43.0 with an isolated environment.

Results in harness.out:
- repeat1 (one feature changes the first of two identical blocks): gate (c) REFUSED, `CONFLICT src/R.ML fits [0, 1]`.
- repeattop: gate (c) for F2 REFUSED.
- xf (critic-engine trial 1381): the blob gate and both gate (c) runs pass; (b2) FAILS with unapply≠pristine.
- xf3 (xf plus F3 changing line w5): the blob gate, all three gate (c) runs and (b2) all PASS. Then:
  - "user installs up to F2: tree==tag True; status rc 1: CONFLICT F1 … {'src/R.ML': [0, 2]} / CONFLICT F2";
  - removing the top F3 leaves the chain up to F2 in CONFLICT;
  - a pruning removal ends with "tree==pristine: False";
  - the strong form reports "content of level 2 fits [0, 2]" at F2's release and again at F3's.

Results in revisit.out:
- revert, revert3 and createdelete are refused by the blob gate and also by the strong form. This confirms the strong form covers the blob comparison.

Read-only checks:
- `git diff-tree` over the real chain refs in contrib/Isabelle2025-2: syntax_phases.ML is changed by 3 features, and six files by 2.
- conda's core/link.py:938-952: every pre-unlink runs before any file is unlinked.
- make-patches:86-88, 184-195 and reference-transaction:28-29.

/tmp filled up (24 GB tmpfs) from other reviewers' conda work. I freed only my own toy directories.

Recommended fix: 1. Decision 16 point 5 (plan:671-672): make the strong form the gate, as the editor proposes.
   - For each file the new feature changes, take its content (or absence) at <R>/pristine/<ID>, at each lower release tag (walk base_tag through the annotated tags' provenance) and at the tip, using `git show`.
   - On the chain ending at the new tag, require the tool's own level function to give each state exactly its own level. Run this at every release, before anything is written or tagged (point 8).
   - On refusal, name the file, the state's tag and the levels it fits.
   - If the other fitting level's content has the same blob id, give ruling 28's message: name the earlier tag and say the change belongs in a new release of the lower feature. Otherwise say the change's context is ambiguous and must be reworked.
   - Decision 8 (plan:426-229 region, the public API list) gains this level function, imported the same way as apply_to.
2. Decision 6 (plan:385-386): base the guarantee on decision 16 point 5. Every chain state of a released feature fits exactly one level, so a file that fits several levels means the tree was changed.
3. §4 (plan:733): change "matches no level" to "matches no level, or several levels,". This is wording, delegated to the author.
4. Decision 16 point 9 (plan:680): add refusal toys:
   - xf: two features, the tip fits {0,2}; today only the post-tag (b2) catches it;
   - xf3: three features, a middle state fits {0,2}; it passes gate (c) and (b2).
   Keep the repeated block as a gate (c) refusal case, and keep the tool CONFLICT tests at plan:619.
5. §10: add a line saying rev 4 makes the round-3 judge's optional form mandatory (REVIEW3:1148), and why. Gate (c) through apply_to already closes the repeated block, but neither gate (c) nor (b2) sees middle states or prefix chains.

**Judge: partially_confirmed → author_decides_then_rereview.** Make the strong form the gate in decision 16 point 5 (plan:671-672).

When it runs: at every release, before anything is written or tagged (point 8), on the chain that ends at the new tag.

What it checks:
- For each file the new feature changes, take its content, or its absence, with git show at three kinds of point: <R>/pristine/<ID>, every lower release tag (walk base_tag through the annotated tags, make-patches:194-210), and the tip.
- Require the tool's own level function to give each state exactly its own level. Import that function the way gate (c) imports apply_to, and add it to decision 8's public API.

On refusal, name the file, the state's tag and the levels it fits. If the other level it fits has the same blob id, print ruling 28's message (the change belongs in a new release of the lower feature). Otherwise say the change's context is ambiguous and must be reworked.

Other edits:
- Decision 6 (plan:385-386) rests its guarantee on this gate.
- The §4 CONFLICT text (plan:733) says 'matches no level, or several levels'.
- Decision 16 point 9 adds the xf and xf3 refusal toys (review-ipc4/defender-C5/harness.py and harness.out). The repeated block stays as a gate (c) refusal case.
- §10 says that rev 5 makes the round-3 optional form (REVIEW3:1148) mandatory, and why.
- Tell the owner this strictly extends ruling 28's gate.

Refuted: the one-feature repeated block is already refused by rev 4's gate (c), whose apply_to and unapply_from read a multi-level file as CONFLICT. The two-feature xf case is caught by (b2), but only after the tags exist.

### C6 [major] isabelle_from=run plus one artifact that is published whole: the CI run's isabelle packages are either published by the feature workflow or missing from the legs, and nothing forbids publish=true in run mode

Section: Decision 11 (inputs, build, accept and publish jobs); §5 steps 7-8; ruling 27  ·  merged from: consistency-CONS4-15, landing-L1

**Statement.** In run mode, the five accept legs install the CI run's isabelle packages from the local channel (plan:516-517, :533, :785). The build job uploads one artifact, and the publish job hands that whole artifact to publish-conda.yml once (plan:526-528, :535-536). publish-conda.yml uploads every *.conda in every subdir it is given (:148-151, :198-203); its package_name input selects nothing (:54-57). Decision 11 never says where the run's isabelle packages go.

If they are inside the one artifact, then dispatching with `isabelle_from=run:<id>` and publish=true uploads the CI run's isabelle builds to the channel. That bypasses release.yml, which rebuilds the packages instead of promoting a CI artifact (release.yml:9-11). And once release.yml has published N from its own rebuild, the same filenames with different bytes make the guard refuse the whole batch (publish-conda.yml:182-187). If they are not in the artifact, the legs have no isabelle to install.

Nothing forbids the combination of run mode and publish=true. Only §5's prose pairs run mode with publish=false and channel mode with publish=true (plan:776-779), which is an invariant the plan asks people to remember. Ruling 27's reason for one call, that all packages are noarch and share one repodata.json (plan:123), also holds only if the published artifact contains nothing but noarch packages, and nothing ensures that. The run's conda-packages artifact is one blob with all five platforms (build.yml:1108-1114; linux-64 alone is 770 MB), so every leg that downloads 'the same artifact' downloads all of it.

Fix.
- Upload two artifacts. `release-packages` holds exactly noarch/{tool, features}; it is the only artifact passed to publish-conda.yml, and the build job asserts that it holds only noarch files. `test-channel` holds release-packages plus, in run mode only, the run's isabelle packages. Alternatively, each leg fetches the run's artifact itself with the actions:read token.
- The legs and the roundtrip job install from test-channel.
- The publish job's condition is `inputs.publish && inputs.isabelle_from == 'channel'`, and the build job fails at once when publish=true is combined with run mode.
- State in decision 11 the size of the run artifact and which jobs download it.

**Editor.** 

**Relaxation proposed by the editor.** Splitting the artifacts and conditioning the publish job on channel mode makes 'only noarch feature and tool packages reach publish-conda.yml' a property of the workflow's structure, so nobody has to remember it.

**Defender: partially_confirmed** (needs owner: False).

Summary: the core of the challenge holds. Decision 11 never says where the CI run's isabelle packages go. The only reading under which run mode works puts them in the one artifact that gets published, and nothing in the workflow stops someone from dispatching run mode with publish=true. The harm is smaller than the challenge says, though, and the point about artifact size is not a defect.

WHAT IS CONFIRMED
1. Decision 11 does not say where the run's isabelle packages go, and only one reading works.
- The input text says only that run mode "下载那次运行的 conda-packages artifact" (downloads that run's conda-packages artifact). It names no job and no destination (plan:516-518).
- The build job checks the post-link of "isabelle_from 取到的 isabelle 包" (the isabelle package that isabelle_from fetched), then "上传一个 artifact" (uploads one artifact) (plan:527-528).
- The five accept legs each download "同一份 artifact" (that same artifact). Every environment uses exactly three channels: file://<local channel>, https://conda.qiyuan.me and conda-forge (plan:532-533). The roundtrip job also installs an environment (plan:530).
- In run mode, build N is not yet on conda.qiyuan.me, and every feature package pins `isabelle 2025.2 N` (plan:498). So the legs and the roundtrip job can only install isabelle if the run's packages sit in the local channel, which is the one artifact.
- §6 even describes the sources as "本地渠道加线上/artifact 的原版构建加 conda-forge" (the local channel, plus the online-or-artifact pristine build, plus conda-forge) (plan:785). That treats the artifact's build as a separate source, which decision 11's three-channel list does not have.
- How the gap arose: the round-3 defender's fix said "downloads that run's conda-packages artifact into the local channel" (REVIEW3, C10 recommended fix 1). The judge's action dropped "into the local channel", and rev 4 copied the judge's wording. So this is an inherited gap, not a silent deviation from §10.

2. Whatever the publish job is given gets uploaded, every subdirectory included.
- publish-conda.yml downloads the artifact by name with the run-scoped token (publish-conda.yml:80-87).
- Its guard, upload and verify steps loop over every `<subdir>/*.conda` (:148-151, :198-203, :251-284).
- `package_name` only labels the job (:54-57, :66, :78).
- The publish job runs whenever publish=true and nothing else (plan:535-536).

3. Nothing in the workflow forbids run mode together with publish=true. Three pieces of prose cover it, and nothing checks any of them:
- §5 pairs run mode with publish=false (step 7) and channel mode with publish=true (step 8) (plan:776-779);
- decision 11 states a precondition, "release.yml 已把原版构建发到线上且绿" (release.yml has already published the pristine build and is green) (plan:543-544);
- the build job's only checks on a run artifact are "build string = isabelle_build" and "not 0" (plan:516-517).
- In channel mode that precondition is enforced by the structure: the legs cannot resolve `isabelle 2025.2 N` unless N is online. In run mode it is not enforced at all.

4. Measured with the real publish-conda.yml step bodies, re-extracted and identical to round 3's copies, against R2 emulated as a local directory and indexed by the real conda_index. Output is in review-ipc4/defender-C6/scenario.out.
- R1: run mode with publish=true before release.yml has published N. All 13 files are "new": the CI run's isabelle-2025.2-1 for all five platforms, plus the eight noarch packages. linux-64 and win-64 then index isabelle-2025.2-1 with the CI run's bytes. Afterwards, step 8's release.yml publication of its own rebuild is refused by the guard, so §5 step 8 as written can no longer run.
- R2: release.yml publishes first, then run mode with publish=true. The guard refuses all five isabelle files, and nothing at all is uploaded (0 noarch files).
- R3: the fix shape, a noarch-only artifact in channel mode. Only noarch changes, and linux-64 keeps release.yml's bytes.
- release.yml really does rebuild rather than promote (release.yml:9-11, :38-48), so the bytes in R2 differ.

5. Ruling 27's stated reason, "所有包是 noarch、共用一个 repodata.json" (all packages are noarch and share one repodata.json) (plan:123), is false for the run-mode artifact: it has six subdirectories. Nothing makes it true in channel mode either; the plan never says the published artifact holds only noarch. The round-3 C6 defender had asked for "it holds only <subdir>/*.conda". That was advice to the judge, not a judge action, so its absence is not a silent deviation.

OVERSTATED OR REFUTED
a. The harm is bounded.
- If the operator honours the stated precondition (plan:543), run mode with publish=true fails closed: the guard refuses the whole batch before any upload (R2). The cost is one wasted run.
- The bad case (R1) needs two mistakes at once: choosing run mode and ignoring that precondition.
- The bytes R1 publishes are not broken. They come from the same build.yml with the same inputs (ci.yml:19-26 against release.yml:38-48), and they passed Jobs F/G/H and the five legs.
- What R1 really costs: release.yml is bypassed, so its four-platform smoke test never runs (release.yml:84-92), while the batch's smoke covers only linux-64 and win-64 (plan:537). release.yml can never publish N afterwards. And a run artifact can come from any dispatched ref, whereas release.yml is the owner's controlled path.
- So this is a real hole that an implementer would most likely fill in the hazardous way, but "major" overstates it. Moderate is fairer.

b. The size point is not a defect.
- The figures are correct: pkgs/isabelle-2025.2-0.conda is 770,243,724 bytes, and download-artifact cannot fetch part of an artifact (build.yml:414-415).
- But the CI repository already accepts this cost: Jobs G and H each download the whole multi-platform conda-packages artifact and then pick out their own subdirectory (build.yml:1156-1159, :1259-1262).
- At most this deserves one sentence in decision 11.

THE EDITOR'S RELAXATION, ON ITS MERITS
It is sound. Two separate guarantees are mixed in it, and both are worth having:
(i) Refusing run mode with publish=true turns the prose pairing and the plan:543 precondition into structure. In channel mode, the legs passing already proves that N is online.
(ii) A publish artifact that contains only noarch packages, asserted by the build job, makes "only the tool and feature packages reach publish-conda.yml" a property of the structure, whatever the mode. It also makes ruling 27's reason literally true.

Its "test-channel = release-packages + isabelle" duplicates the small packages. Uploading the run's packages as a second artifact, and having the consumers merge the two, is equivalent and slightly leaner. A fail-fast check alone is better than an `if:` on the publish job alone: an `if:` would silently skip publishing, and the operator might think the batch had been published.

Experiment: Work directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C6/. It ran locally only: no network, nothing installed, and the repositories were only read.

(1) Using PyYAML, I re-extracted the seven step bodies from the current isabelle-packaging-ci/.github/workflows/publish-conda.yml (guard, upload, pull, reindex, push, verify, audit). They are identical to round 3's copies in steps/; the only edit is that https://conda.qiyuan.me becomes file://$R2DIR. shim/rclone is the copy-only emulator from round 3. Indexing uses the real conda_index from ~/miniconda3.

(2) mk.py builds toy packages:
- five-platform isabelle builds: legacy build 0, the "CI run" build 1, and release.yml's "rebuild" build 1 with different bytes;
- the noarch tool plus seven features pinned to `isabelle 2025.2 1`.
The plan's one run-mode artifact is the feature batch plus the CI run's isabelle packages.

(3) scenario.sh, with output in scenario.out. Each scenario starts from a channel that holds the legacy build 0 on all five platforms.
- R1: run mode with publish=true before release.yml publishes. 13 files are "new". linux-64 and win-64 index isabelle-2025.2-1 with the CI run's bytes. A later release.yml publication of build 1 is refused ("ALREADY on the channel with DIFFERENT content").
- R2: release.yml publishes first, then run mode with publish=true. The guard refuses all five isabelle files, the call stops, and 0 noarch files are uploaded.
- R3: channel mode with a noarch-only artifact. Only noarch is uploaded, and linux-64 keeps release.yml's bytes.
- The proposed noarch-only assertion passes on the feature batch and fails on the run-mode artifact (5 non-noarch files).

(4) Read-only checks:
- plan:513-551, :123, :776-785, :887;
- publish-conda.yml:47-87, :132-345;
- release.yml:1-132;
- ci.yml:1-26;
- build.yml:48-80, :410-420, :1108-1115, :1156-1159, :1259-1262;
- REVIEW3 C6 and C10 (defender, judge);
- the size of ~/miniconda3/pkgs/isabelle-2025.2-0.conda (770,243,724 bytes).

Recommended fix: The smallest fix has three parts, all in decision 11.

1. Build job (plan:523-529). Upload two artifacts instead of one:
- `feature-packages` holds the tool and feature packages (noarch/*.conda only). The build job asserts that every file in it lies under noarch/, which makes ruling 27's reason (plan:123) true by construction. It is the only artifact passed to publish-conda.yml.
- In run mode only, `isabelle-run` holds the run's conda-packages exactly as downloaded, so the five legs' install the same bytes the CI run verified.
The roundtrip job and the five accept legs download both artifacts into one directory (`pattern` + `merge-multiple`), and that directory is the file:// local channel (plan:530-533).
Alternative: the consumers fetch the run's artifact themselves with the actions:read token. That avoids re-uploading about 4 GB, but it spreads the token to six jobs.

2. Make the first step of the build job fail at once when publish=true is combined with isabelle_from=run:<id>. The message should say that run mode is for rehearsal only and that publishing takes isabelle from the channel.
- This replaces the prose pairing in §5 steps 7-8 (plan:776-779) and the precondition at plan:543 with structure. In channel mode, the legs can only resolve `isabelle 2025.2 N` once release.yml has put N online.
- Prefer this check over an `if:` on the publish job alone. An `if:` alone would skip the publication silently.

3. Make the two statements that depend on this match the structure:
- §6's source list (plan:785) should say that in run mode the run's isabelle packages sit in the local channel;
- §10 row C10 should record that run mode never publishes, and that the published artifact holds only noarch packages.

Optional: one sentence noting that each leg downloads the whole multi-platform run artifact, which build.yml Jobs G and H already accept (build.yml:1156-1159, :1259-1262). Lower the severity from major to moderate. Nothing here touches an owner ruling.

**Judge: partially_confirmed → author_decides_then_rereview.** Decision 11 (plan:515-536).

- The build job uploads one artifact, feature-packages, holding noarch/*.conda only, and asserts that every file in it is under noarch/. It is the only artifact passed to publish-conda.yml, which makes ruling 27's reason at plan:123 true by construction.
- In run mode, the run's conda-packages reach the consumers as a second artifact, or each consumer fetches it with the actions:read token. The roundtrip job and the accept legs merge both into the file:// local channel.
- The build job's first step fails when publish=true is combined with isabelle_from=run:<id>. Use this failing check, not only an if: on the publish job, which would skip publication silently.
- Fix §6's source list (plan:785) and §10 row C10.
- Optionally add one sentence: every leg downloads the whole multi-platform run artifact, as build.yml:1156-1159 and :1259-1262 already accept.

Under C3's relaxation the build job no longer needs any isabelle package.

The measured harm is bounded (review-ipc4/defender-C6/scenario.out): when release.yml has published first, the guard refuses the whole batch. The size point is not a defect.

### C7 [major] The .bat pre-unlink is still not written ('.bat 同义') for the third round running while §10's C24 row says it is; the written .bat misses negative exit codes, the fragment's ending is ambiguous, and the Ctrl-C recovery's `touch` has no Windows form

Section: Decision 9 (fragment and pre-unlink); §4 interrupted-install text; Appendix A; §10 row C24  ·  merged from: conda-conda-7, consistency-CONS4-6, user-U10, user-U9

**Statement.** Round 2 required the exact Windows texts (REVIEW2:876). The round-3 judge's C24 action required them again: 'Write the exact .bat post-link fragment and .bat pre-unlink into decision 9: no parenthesised blocks, every %PREFIX% quoted, ending exit /b 0. Say that light's lines are appended after the end label' (REVIEW3:3083). Rev 4 writes the .bat post-link (plan:443-453), but gives the pre-unlink only as '.bat 同义' (plan:457). That is exactly the wording round 3 confirmed as the defect. §10's C24 row says '决定 9 写出 .bat 文本' (plan:901), so this is a partial deviation that §10 does not name, for the third round.

The pre-unlink is frozen into every published feature package. It is not trivially 'the same text': its fallback message needs Windows syntax (%PREFIX%\isa, not $PREFIX/isa, plan:460), and light's `components -x` lines, with the warm-up call and the /cygdrive/ path conversion (Isabelle_RPC/conda/recipe.yaml:165-176), have to be placed in it.

Three more defects in the Windows texts:
(a) `if errorlevel 1` (plan:447) is true only for an errorlevel of 1 or more. A negative NTSTATUS exit code of python.exe, for example 0xC0000135 (DLL not found, one of the 'python broken' cases plan:454-455 names), skips the message. No rollback follows, because exit /b 0 still ends the hook. This follows cmd's documented semantics; wine treated 0xC0000005 as ≥ 1 (critic-conda/bat/run.out), so it was not measured on real Windows.
(b) plan:442 says the .bat fragment ends with `exit /b 0`, but the text ends at `:end`, and plan:454 and :463 put the exit after `:end`. If hooks/post-link.bat itself contained the exit, light's component lines would be dead code, on Windows only.
(c) The recovery after an interrupted install, `touch $PREFIX/conda-meta/history` (§4 plan:755; Appendix A plan:941-942), has no cmd or PowerShell form, although ruling 18 requires every platform.

Fix.
- Write the exact pre-unlink .bat in decision 9: CRLF line endings, no parenthesised block, every %PREFIX% quoted, `if %errorlevel% neq 0 echo ... >> "%PREFIX%\.messages.txt"` on its own line, light's warm-up and `components -x` lines, and `exit /b 0`.
- Use the same errorlevel test in the post-link .bat.
- State that hooks/post-link.sh and hooks/post-link.bat end at `fi` and `:end` and contain no exit line, so every assembler appends its own lines and then the exit.
- Give the Windows form of the history recovery, for example `type nul > "%PREFIX%\conda-meta\history"`.
- Correct §10's C24 row.

**Editor.** U10 proposes writing the pre-unlink with `if errorlevel 1 echo ...`, which repeats defect (a). Use the %errorlevel% comparison instead.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

CONFIRMED: the main claim, which is a silent deviation from the round-3 judge's action.
- The round-3 judge's C24 action asked for the exact .bat post-link and the exact .bat pre-unlink (REVIEW3:3083).
- Rev 4 writes the .bat post-link (plan:443-453). For the pre-unlink it still gives only the .sh text and the words "`.bat` 同义" (plan:457-462).
- §10's C24 row says "决定 9 写出 `.bat` 文本" (plan:901) and names no deviation. Under the review rules that is a finding.
- The pre-unlink cannot be produced by mechanical transcription. Its message has to say "%PREFIX%\isa" where the .sh says $PREFIX/isa (plan:460). It also needs an exit-code test, because the .sh `||` has to be expressed somehow. And light's `components -x` lines (getenv warm-up, /cygdrive/ conversion, Isabelle_RPC/conda/recipe.yaml:166-176) must be placed in it. plan:466 only says "after the tool line".
- One part of the framing is overstated. "Third round running" is not true of the pre-unlink in particular. Round 2's judge demanded the .bat text of the isabelle post-link fragment (REVIEW2:862, :876). The first explicit demand for the .bat pre-unlink is REVIEW3:3083. It is true that every revision since rev 2 lacked it (rev2:305 "同理", rev3:372 "同义").

CONFIRMED: (a), and the evidence is stronger than the critic's.
- plan:447 uses `if errorlevel 1`. That test is true only when the errorlevel is ≥ 1, compared as a signed number.
- The critic's wine run, which seemed to show 0xC0000005 treated as ≥ 1, is an artifact of its test program. Its fake exe parses FAKE_RC with strtol, and on mingw `long` is 32 bits, so 0xC0000005 overflows to LONG_MAX. That exe actually exits with 2147483647 (my critic_fake.out).
- With a correct fake that calls ExitProcess(0xC0000135) and ExitProcess(0xC0000005), wine 9.0's cmd shows raw errorlevels of -1073741515 and -1073741819. `if errorlevel 1` is false for both; `if %errorlevel% neq 0` and `if not errorlevel 0` are true (run.out).
- I ran the plan's exact fragment through a replica of conda's activation wrapper (utils.py:224-269). For both negative codes the hook exits 0 and writes no message (frag.out). So the "python broken" case named at plan:454-455 fails silently.
- Severity is low. No rollback follows, and only the fallback message is lost.

MOSTLY REFUTED: (b).
- The glossary separates the hook from the hook fragment (plan:33-35). The plan says in four places that the fragment ends at `fi` / `:end` and that the hook file puts the exit after whatever is appended:
  - plan:454: "每个钩子文件以 exit 0/exit /b 0 结尾（.bat 在 :end 之后）";
  - plan:463: light's lines go "在钩子片段的 fi（.bat 的 :end 标签）之后、exit 0 之前";
  - plan:486-487 and :560-563: the isabelle package inserts the fragment before its own final exit, and the re-run step comes after the fragment.
- The .sh block (plan:434-440) also contains no exit.
- Only the parenthetical at plan:442 ("`exit /b 0` 结尾"), placed in the fragment's description, is misplaced. That is a one-phrase wording slip, not a design ambiguity. A fragment file containing an exit would contradict four explicit sentences.

PARTIALLY CONFIRMED: (c).
- `status` and the README print `touch $PREFIX/conda-meta/history` on every platform (plan:754-756). That is POSIX-only syntax, which is the same kind of defect as round 3's confirmed "POSIX notices on Windows" (REVIEW3:3074).
- But the same sentence already gives a recovery that works on every platform: `conda create -p $PREFIX <同一批包>`. It needs no touch. In review-ipc3/defender-C11/run2.sh, the variant named create runs `conda create -p` over the rolled-back prefix without touching anything, and run2.out shows it converging (all features applied, history correct).
- conda only asks "A directory already exists ... not a conda environment. Continue" (main_create.py:151-160).
- So the gap is sentence order, plus the missing Windows form of the optional touch step. Appendix A:941-942 is design prose, not an instruction to the user.

Severity: minor, not major.
- A pre-unlink that exits non-zero only produces a warning, and its .messages.txt is printed anyway (link.py:1647-1648, :1676-1683).
- The post-link fragment's exit 0 is already right.
- Every remaining defect only loses or mis-words a message.
- Each isabelle build re-renders every feature package (item 22), so a wrong text is replaced at the next batch release.

Editor's rebuttal: correct that U10's `if errorlevel 1` would repeat (a). `if %errorlevel% neq 0` is acceptable, and it is conda's own idiom (utils.py:250, :269). It has one weakness: conda copies the user's whole environment into hooks (link.py:1566), and %errorlevel% then reads an inherited variable named ERRORLEVEL. Under wine, with ERRORLEVEL=0 set in the environment, that test missed an exit code of 1 (frag.out).
- `if not errorlevel 1 if errorlevel 0 goto :end` is one line with no parentheses. It catches positive and negative codes and ignores the environment (nested.out, all 15 cases).
- A non-zero inherited ERRORLEVEL already breaks conda's own wrapper (wrapper rc=5, nested.out). So the gap between the two forms is small, and either is acceptable.

Experiment: Scratch: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C7/bat/ (wine 9.0, private WINEPREFIX, mingw-w64).

1. fake.c / fake.exe calls ExitProcess with the full 32-bit value of FAKE_RC. t.bat with run.out: for codes 0xC0000135 and 0xC0000005 the raw errorlevel is negative; `if errorlevel 1` is FALSE; `if %errorlevel% neq 0` and `if not errorlevel 0` are TRUE. For codes 1, 9009 and 0x7FFFFFFF, `if errorlevel 1` is TRUE.

2. critic_fake.out: the round-4 critic's python.exe, run with FAKE_RC=0xC0000005, actually exits 2147483647, because strtol overflows a 32-bit long. Its "wine treats 0xC0000005 as ≥ 1" result is therefore an artifact.

3. plan.bat is the fragment at plan:444-452 verbatim, with `exit /b 0` appended. fixed.bat is the same with `if %errorlevel% neq 0`. Both were run through conda's wrapper replica (wrap.bat, from utils.py:224-269). frag.out:
   - the plan's fragment writes NO message for either negative code; the hook exits 0;
   - fixed.bat catches them, but loses even an exit code of 1 when ERRORLEVEL=0 is inherited from the environment.

4. nested.bat uses `if not errorlevel 1 if errorlevel 0 goto :end`. nested.out: correct in all 15 cases (codes 0, 1, 9009, two negatives; inherited ERRORLEVEL unset, 0 or 5). Also, conda's wrapper itself exits 5 when ERRORLEVEL=5 is inherited.

5. preunlink.bat is a proposed exact pre-unlink for light: the generic part, then the component lines from Isabelle_RPC/conda/recipe.yaml:168-174, with a stub isabelle.bat that logs its calls and exits 7. preunlink.out: the hook exits 0 in every case, for prefixes plain, 'a b', 'a)b' and 'a!b'. The message is written for exit 1, for a negative code and for a missing python.exe, and not on success. The warm-up and `components -x "/cygdrive/C/envs/<p>/share/isabelle-light-locale"` run in every case.

6. Source reads (conda 25.11.1): link.py:1566 (environment copy), :1606-1625 (post-link wrapped, pre-unlink a bare `cmd /d /c`), :1647-1648 and :1676-1683 (non-zero pre-unlink: messages printed, warning only), utils.py:250 and :269 (conda's own `IF %ERRORLEVEL% NEQ 0`), main_create.py:133-160 (create over a prefix that is not an environment only asks for confirmation). Also review-ipc3/defender-C11/run2.sh and run2.out: the variant named create recovers with no touch.

Caveat: wine is not real Windows. The errorlevel results agree with cmd's documented signed `>=` semantics.

Recommended fix: 1. Decision 9 (plan:457). Replace "`.bat` 同义" with the exact CRLF text:
```
@echo off
"%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature>
if not errorlevel 1 if errorlevel 0 goto :end
echo isabelle-patch-control: could not run the pre-unlink hook of <feature>; files under "%PREFIX%\isa" may still carry its changes. Recovery: conda install --force-reinstall isabelle-patch-control; conda install <包名>; conda remove <包名>>> "%PREFIX%\.messages.txt"
:end
exit /b 0
```
Say that light's `components -x` lines (Isabelle_RPC/conda/recipe.yaml:168-174, without their `@echo off`) go between `:end` and `exit /b 0`. Tested under wine: preunlink.bat.

2. plan:447. Replace `if errorlevel 1 echo …` with `if not errorlevel 1 if errorlevel 0 goto :end` and put the echo on the next line, as tested in nested.bat. The editor's `if %errorlevel% neq 0 echo …` is an acceptable alternative: it is conda's own idiom (utils.py:250), but it reads an inherited ERRORLEVEL variable. Use the same test in both hooks.

3. plan:442. Move "`exit /b 0` 结尾" out of the fragment's description, for example: "片段以 `fi`/`:end` 结束、不含 exit；钩子文件在追加的行之后以 exit 结尾". No other change is needed: plan:454, :463 and :486 already say this.

4. plan:755-756 (README and `status`). Put first the recovery that works on every platform with no touch: `conda create -p <prefix> <every package to keep plus the interrupted one>`, answering y (measured: review-ipc3/defender-C11/run2.out). Keep `touch …/history` as the POSIX variant of the install route, or print the cmd form `type nul > "<prefix>\conda-meta\history"` on Windows. Appendix A:941-942 may stay as design prose.

5. §10 C24 row (plan:901). State that the .bat pre-unlink is added in rev 5, or, if it stays out, name the deviation.

Optional: in decision 15 (plan:654), add "tool cannot run during pre-unlink" to the cases that run on win-64, so the .bat failure branch runs on a real Windows leg.

Severity should be minor: every remaining defect only loses or mis-words a message, and the next batch release replaces the text.

**Judge: partially_confirmed → author_fixes_no_rereview.** Decision 9, plan:457: replace '.bat 同义' with the exact CRLF text:
- @echo off
- the python line
- if not errorlevel 1 if errorlevel 0 goto :end
- the echo with "%PREFIX%\isa", on its own line
- :end
- light's component lines from Isabelle_RPC/conda/recipe.yaml:168-174, without its @echo off, placed between :end and exit /b 0
- exit /b 0
This is tested under wine in defender-C7/bat/preunlink.bat. A wine run is not a run on real Windows; the results agree with cmd's documented signed comparison.

Other edits:
- plan:447 uses the same two-line test. `if errorlevel 1` is false for negative NTSTATUS exit codes (defender-C7/bat/run.out and frag.out). The critic's wine result was an artifact of its test program (defender-C7/bat/critic_fake.out).
- Move 'exit /b 0 结尾' out of the fragment's description at plan:442. Fragments end at fi or :end; the hook file supplies the exit (plan:454, :463 already say so).
- §4 (plan:754-756): put the recovery that needs no touch first, `conda create -p <prefix> <packages>` (review-ipc3/defender-C11/run2.out), or print `type nul > "<prefix>\conda-meta\history"` on Windows.
- Correct §10's C24 row.

Severity: minor.

### C8 [major] For an edit written in place through the hard link, the CONFLICT remedy loops and the edit spreads to every environment using that isabelle build; round 3's C27 action (4) was not carried out and §10 does not say so

Section: §4 CONFLICT text and residue block; decision 9 remedies (plan:481-483); decision 14 README list; decision 15; §10 row C27; Appendix A  ·  merged from: consistency-CONS4-9, user-U2

**Statement.** conda hard-links an environment's files from the package cache (plan:224-226). An editor that writes in place through the link therefore changes the cache copy too. vim's backupcopy=auto does this for a file with more than one link (round-3 judge, C27).

The §4 CONFLICT text and the residue block still promise that `conda install --force-reinstall isabelle` 'restores the package's files' (plan:736-737, :748-749). In this case the reinstall links the same edited file again. The post-link prints the same CONFLICT and the same remedy, so the user loops. Each round also deletes the environment's Isabelle user directory with its heaps (recipe.yaml:223-231), and conda shows a SafetyError warning only when the file size changed, with rc 0.

The edit also spreads. Every environment that uses this isabelle build shares the file, and a new environment created later reports the CONFLICT on its first feature install. Measured (review-ipc4/critic-user/run2.out): in case e2 the environment file and the pkgs-cache file have the same inode, 8787863; in case e2'' a new environment shows the CONFLICT; in case e2''', `rm -rf pkgs/isa-2025.2-2` followed by `--force-reinstall` repairs only that one environment.

The round-3 judge's C27 action (4) asked the author either to measure and state a real recovery (for example, deleting the extracted pkgs/isabelle-<b>/ directory before --force-reinstall) or to state the limitation (REVIEW3:3386). Rev 4 keeps the unconditional claim. It defers the recovery to '决定 15 实测后定稿' (plan:481-483) and to the README (plan:606), but decision 15 has no such case (plan:612-661). §10's C27 row (plan:904) mentions none of this, so the deviation is not named.

Fix. The tool can tell this case apart. For a CONFLICT file whose copy in the tree has st_nlink > 1 and whose sha256 differs from its paths_data entry in conda-meta/isabelle-*.json (a file check_bytes already reads, plan:634-636), print the measured repair: delete <pkgs dir>/isabelle-2025.2-<b>/ (conda re-extracts it from the archive), then run `conda install --force-reinstall isabelle` in this environment and in every other environment that uses this isabelle build. This uses paths_data only to choose the remedy text, not as a source of state, so it is consistent with §9 (plan:860-861). Then remove the unconditional claim from §4 and Appendix A (plan:943), add the measured case to decision 15, and record the choice in §10's C27 row.

**Editor.** Neither half of U2's detection is enough alone. Every untouched hard-linked file has st_nlink > 1, and a file the user replaced (new inode) also has a different sha256. Only the conjunction of the two identifies an edit of the cache copy. If the user has run `conda clean -p`, st_nlink is 1, the cache copy is gone, and the ordinary remedy is correct.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

The core of C8 holds. Three parts are wrong or overstated.

CONFIRMED
1. The user-visible texts are still unconditional, and the plan contradicts itself.
- §4's CONFLICT text (plan:736-737) and the residue block (plan:748-749) say `conda install --force-reinstall isabelle` "restores the package's files".
- The plan itself says this is false for an edit written in place through the hard link: §2.3 (plan:224-226), decision 9 (plan:481-483) and Appendix A (plan:943).
- In the state right after a normal install, the environment's file and the package-cache copy are one inode. There the reinstall restores nothing. My run.out step 3: two reinstalls, rc 0, no output for a same-size edit. critic-user/run2.out e2': only a SafetyError when the size changed, rc 0.
- The post-link of the pristine isabelle build then prints the same CONFLICT and the same remedy (run2.out:166-236), so a user who follows the text goes round in a loop.
- Each round runs the isabelle pre-unlink's `rm -rf` of the Isabelle user directory (recipe.yaml:222-231).
- The CONFLICT text points only to `status -v` and to `help` (plan:739), not to the README section on in-place edits (plan:606), so nothing in the output breaks the loop.

2. The deferred recovery points at nothing.
- Decision 9 says "决定 15 实测后定稿" (to be finalised after measurement in decision 15).
- Decision 15 (plan:612-661) has no such case. Its only inode line, plan:625, is about the tool's own writes.
- The residue test "用户改过文件后卸顶层" (plan:652-653) does not say what kind of edit it makes, and with an in-place edit it would fail.

3. A real recovery exists, and I measured it.
- Delete the extracted directory `pkgs/isa-2025.2-1` (the archive stays), then run `--force-reinstall` in environment A. A is restored, but B still has the edit (run.out step 5).
- `--force-reinstall` in B then restores B (step 6).
- `conda clean -p` does not help: it skips extracted directories whose files have more than one link (main_clean.py:121, :195-199; run.out step 4 prints "no unused package(s)").

4. §10 leaves part of judge action (4) unrecorded.
- §10's C27 row (plan:904) records only the "save edits first" half of judge action (4) (REVIEW3:3386). That half is done, at plan:735.
- The in-place-edit half is not mentioned. It is the judge's finding that every "restores the package's files" text is false (REVIEW3:44), plus "measure a recovery or state the limitation".
- plan:5-6 promises that every difference from a judge action is named in §10, so this unnamed partial implementation is a finding.

REFUTED OR NARROWED
a. Appendix A makes no unconditional claim. plan:943 already says "经硬链接原地写入的编辑连包缓存一起改了，重装恢复不了，README 写明" (an in-place edit through the hard link also changes the package cache, the reinstall cannot restore it, and the README says so). The proposed fix's "remove the unconditional claim from Appendix A" is wrong.

b. "Action (4) was not carried out" is overstated. The save-first half is done (plan:735). The limitation is stated in three internal places, which is the judge's "or state the limitation" branch. What is missing is the user-visible texts, the measurement and the §10 entry.

c. "The edit spreads to every environment using that isabelle build" is too broad.
- The edit reaches, at the moment it is written, every path that shares that inode. That comes from conda's hard links and the editor, not from the plan's remedy.
- It reaches only environments linked from the same extraction of the package.
- The owner's machine shows another shape today. `~/miniconda3/envs/isabelle` and `envs/isabelle-2` share inode 55605049 for `isa/src/Pure/Isar/locale.ML` (link count 2; all 3548 `isa/src` files have link count 2). But `pkgs/isabelle-2025.2-0` was re-extracted on 2026-08-25, after both environments were created, and all its files have link count 1.
- In that shape an edit reaches the other environment but not the cache, and the plain `--force-reinstall` works in each environment (run.out step 7). So the loop happens only while the cache copy is the same inode. That is the default state, but not the only one.

d. The editor's detection rule misfires in exactly the owner's shape.
- The rule fires when the file's link count (st_nlink) is above 1 and its sha256 differs from the paths_data entry. In run.out step 7 it chooses the cache remedy although the cache is clean.
- An exact, equally cheap test exists: `os.path.samefile(<prefix>/isa/<p>, <extracted_package_dir>/isa/<p>)`, combined with the sha256 mismatch. conda-meta/isabelle-*.json records `extracted_package_dir`; in both owner environments it is `/home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0`.
- This test is right in both shapes (run.out steps 2, 5 and 7), and it also names the directory to delete.
- The editor is right that link count alone is not enough.

Severity: this is a text and test defect that the author can fix under ruling 17. It is not a design flaw, and no data is lost: the user's edit survives, and heaps and component registrations come back through ruling 26. Calling it major is arguable; the cost is the loop and repeated heap rebuilds. No owner ruling is involved. The plan's refusal to use conda-meta as a source of state (§9) is the author's own choice and is not touched, because this only chooses the remedy text.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C8/
- Scripts: run.sh, detect.py, and mkchan.py (copied from review-ipc3/defender-C27).
- Output: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C8/run.out
- Setup: conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and a toy noarch package `isa` whose files are hard links.

Steps:
- (1) Created environments A and B from one cache. b.ML in A, in B and in the cache is one inode, 9740781, with link count 3.
- (2) A same-size write in place in A (`printf … 1<>`) changed B and the cache copy. Both detection rules chose the cache remedy.
- (3) `--force-reinstall isa` twice in A: rc 0, no output, still edited.
- (4) `conda clean -p -y` printed "There are no unused package(s) to remove".
- (5) `rm -rf pkgs/isa-2025.2-1` (archive kept), then `--force-reinstall` in A: A restored on a new inode 9740894, B still edited. Detection on B: link count 1, so the ordinary remedy.
- (6) `--force-reinstall` in B: B restored.
- (7) The owner-machine shape: environments X and Y share an inode, and the cache was re-extracted by creating a third environment. An in-place edit in X changed Y but not the cache. The editor's rule chose the cache remedy wrongly; the samefile rule chose the ordinary one. A plain `--force-reinstall` repaired X, and then Y.

Read-only checks on the owner's machine (python os.stat, json):
- envs/isabelle and envs/isabelle-2 share inode 55605049 for isa/src/Pure/Isar/locale.ML, with link count 2.
- pkgs/isabelle-2025.2-0 has inode 56390689 for that file; all 3548 of its isa/src files have link count 1.
- The extracted directory's birth time is 2026-08-25. The conda-meta records were written 2026-07-22 and 2026-07-28.
- Both conda-meta/isabelle-2025.2-0.json files hold `extracted_package_dir` and per-path sha256 in paths_data.

Sources checked:
- conda: path_actions.py:455-490 (size-only SafetyError unless extra_safety_checks) and main_clean.py:121, :195-199.
- recipe.yaml:222-231.
- plan:5-6, :224-226, :481-483, :606, :612-661, :652-653, :735-739, :748-750, :860-861, :904, :943.
- REVIEW3:44, :3317, :3366, :3386.
- critic-user/run2.out:134-300.

Recommended fix: All of this is the author's work under ruling 17; no owner question.

(1) §4 (plan:736-737, :748-749): drop the unconditional "(restores the package's files". When the CONFLICT file (or the residue file) passes both tests below, print the measured remedy instead of the reinstall line:
- the file is the same file as the cache copy: `os.path.samefile($PREFIX/isa/<p>, <extracted_package_dir>/isa/<p>)`, with extracted_package_dir read from conda-meta/isabelle-*.json;
- its sha256 differs from that record's paths_data entry.
Suggested text: "This file was edited in place through conda's hard link, so conda's package cache holds the edit too and a reinstall alone brings it back. Save your edit; delete <extracted_package_dir> (conda re-extracts it from the archive); then conda install --force-reinstall isabelle here and in every other environment that reports this CONFLICT."
In every other case keep today's text, which is then true.
Do not use the editor's rule (link count above 1 plus sha256 mismatch). It prints the cache remedy on a clean cache, which is the shape the owner's machine is in today.
A version with no new code is also acceptable: always add one static line, "If the file is still edited after the reinstall: delete conda's extracted copy of the isabelle package and reinstall in each environment that reports this CONFLICT."

(2) §9 (plan:860-861): add that conda-meta's `extracted_package_dir` and `paths_data` are also read to choose this remedy text, never as a source of state.

(3) Decision 9 (plan:481-483): replace "决定 15 实测后定稿" with the measured recovery.
Decision 15, hook-layer tests: add one case with these checks:
- two environments from one cache, same-size in-place write;
- the plain reinstall leaves the edit with rc 0;
- `conda clean -p` keeps the cache directory;
- deleting the extracted directory and reinstalling in each environment restores both;
- in the re-extracted-cache shape, the ordinary text is chosen and works.
Say that the edit in the residue case "用户改过文件" (plan:652-653) makes a new inode.

(4) §10 row C27 (plan:904): name the in-place-edit half of action (4) and the choice made.

(5) Appendix A (plan:943) needs no removal; optionally append the recovery.

**Judge: partially_confirmed → author_fixes_no_rereview.** §4 CONFLICT text and residue block (plan:736-737, :748-749): drop the unconditional '(restores the package's files'. Use one of two forms.
- Detection. The file is the cache copy, `os.path.samefile($PREFIX/isa/<p>, <extracted_package_dir>/isa/<p>)`, and its sha256 differs from conda-meta/isabelle-*.json paths_data. Then print the measured remedy: save the edit; delete <extracted_package_dir>; run --force-reinstall isabelle here and in every other environment that reports this CONFLICT.
- Or one static line saying the same.

Do not use the st_nlink rule. It picks the cache remedy on a clean cache, which is the owner's machine today (review-ipc4/defender-C8/run.out step 7).

Other edits:
- §9 (plan:860-861): conda-meta is read only to choose this remedy text.
- Decision 9, plan:481-483: replace '决定 15 实测后定稿' with the measured recovery.
- Decision 15 adds the two-environment case: a same-size in-place write; a plain reinstall leaves the edit with rc 0; conda clean -p keeps the extracted directory; delete and reinstall in each environment restores both; in the re-extracted-cache shape the ordinary text is chosen and works.
- Decision 15 also says that the residue case's edit makes a new inode.
- §10's C27 row names this half of action (4).

Appendix A plan:943 already states the limitation; nothing to remove there.

### C9 [major] Both banner-step fixes that decision 12 point 5 offers fail for cross-repository callers of publish-conda.yml, including this plan's own batch workflow, and no rehearsal runs the publish path before the real publication

Section: Decision 12 point 5; decision 11 publish job; §5 steps 6-8  ·  merged from: consistency-CONS4-5, landing-L6

**Statement.** Decision 12 point 5 tells the CI plan to fix the banner step by giving it a checkout, or by putting the script and the banner into the artifact (plan:571-572). publish-conda.yml is a reusable workflow that every component repository calls (:3-6). Its banner step runs `python3 scripts/banner-index.py ... conda/channel-banner.html` (:223-227), and the job has no checkout step.

In a called workflow, the github context belongs to the caller, so a plain actions/checkout fetches the caller's repository, not isabelle-packaging-ci. This is GitHub's documented behaviour; it was not measured here. Such a checkout would fix isabelle-packaging-ci's own callers (release.yml:57 and release-isabelle-ai.yml:121, both `uses: ./...`). It would fail for every cross-repository caller: the component repositories (Isabelle_RPC release-conda.yml:320, Performant_Isabelle_ML :479, auto_sledgehammer :225) and this plan's own batch workflow (plan:535). The second option would make every caller ship isabelle-packaging-ci's files, which defeats the workflow's single-source design.

The step runs after the .conda upload and before the index push (publish-conda.yml:193-203 against :229-236). §5 has no rehearsal of the publish path: step 7 runs with publish=false (plan:776), so the first cross-repository run of the fixed step is the real batch publication at step 8. A wrong fix leaves the batch uploaded but not indexed, a state C2 (b) shows is hard to resume.

Fix. Decision 12 point 5 requires one of two things: checking out `repository: xqyww123/isabelle-packaging-ci` (it is public, so no token is needed) at an explicit ref, or inlining the banner text into the step. Delete the artifact option. Require one cross-repository run of the fixed step before §5 step 8. Either a component repository's next release can serve, or a batch-workflow publish of an artifact that holds only already-published, byte-identical files: the guard treats that as a resume (:179-180), so nothing new becomes visible.

**Editor.** CONS4-5 claims that 'Re-run failed jobs' would fail the same way. That is not measured: whether a re-run resolves `@main` again is unverified, so the claim is dropped. The finding does not depend on it.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

What I checked and what holds up:

1. The plan text. Decision 12 point 5 (plan:571-572) says "给它 checkout，或把脚本与 banner 放进 artifact" (give the step a checkout, or put the script and banner into the artifact). It names no repository, no ref and no path. It does not say the step has to work for callers in other repositories. The workflow itself matches the challenge. publish-conda.yml has no checkout step. The banner step runs `python3 scripts/banner-index.py "$CH/index.html" conda/channel-banner.html` (publish-conda.yml:223-227), after the upload (:193-203) and before the index push (:229-236). Callers in other repositories pin `@main`: Isabelle_RPC release-conda.yml:320, Performant_Isabelle_ML :479, auto_sledgehammer :225, Semantic_Embedding :464, Isa-Mini :307, Isabelle-MCP :203, and the plan's own batch workflow (plan:535). Six callers inside isabelle-packaging-ci use `./` (release.yml:57, release-isabelle-ai.yml:121, release-json-spec.yml:114, release-rocksdict.yml:195, release-semantic-db.yml:285, release-nunchaku.yml:507). isabelle-packaging-ci is public, and GitHub's main branch carries the broken step (checked read-only with `gh api`).

2. The artifact option is broken. Confirmed. Every caller builds its own artifact. So this option makes six component repositories, the batch workflow and six internal callers all ship isabelle-packaging-ci's files, which defeats the single-source design (publish-conda.yml:3-6). Any caller that has not been changed fails. I also found that placing the files at their natural paths breaks a later step. The verify step loops over every top-level directory of the artifact (:251-255) and fetches `<dir>/repodata.json` for each. My simulation printed "::error::scripts has no repodata.json" and "::error::conda has no repodata.json" with rc=1, and https://conda.qiyuan.me/scripts/repodata.json returns 404.

3. The checkout option is under-specified, not inherently broken. GitHub's docs say "the `github` context is always associated with the caller workflow". actions/checkout defaults to `github.repository`. So the one-line `- uses: actions/checkout@v4` fetches the caller's repository whenever the caller is in another repository. That part is documented, not measured. The challenge's word "both" overstates this option: a checkout that names isabelle-packaging-ci works. There is a second trap the plan does not mention. actions/checkout v4 (src/git-directory-helper.ts, prepareExistingDirectory) deletes the contents of the target directory when it has no `.git`. The default target is `github.workspace`, and `$CH` is `github.workspace/channel` (:76). So a checkout to the default path placed next to the banner step, after the pull, would delete the multi-GB channel copy. I read this in the source; I did not run it.

4. Nothing tests the publish path from another repository before the real batch publication. Confirmed. Step 7 runs with publish=false (plan:776). In step 8, release.yml publishes first (plan:778), but it calls through `./`, the one case where even a plain checkout works. So a wrong fix shows up first in the real batch publish, after the whole batch has been uploaded.

5. The editor's rebuttal is wrong on the facts, though the finding does not depend on it. GitHub's docs (reusing-workflow-configurations) say re-running failed or specific jobs "will use the reusable workflow from the same commit SHA of the first attempt". Decision 11's only recovery path, re-running the failed job (plan:539), therefore cannot pick up a fix to publish-conda.yml. "Re-run all jobs" does pick up @main again, but it re-runs the `build` job. That job downloads only packages already named in repodata.json (plan:529). The uploaded but unindexed batch is not named there, so it gets rebuilt with different bytes, and the guard rejects it (:182-187). The real way out is that the next successful publish from any other caller re-indexes the whole channel (:205-221, :38-43). That way out runs outside the plan and never runs the batch's smoke job.

Not confirmed as stated: the claim that both options fail, and one of the challenge's two rehearsal routes. Before step 8 nothing from the batch is published yet (tool 1.0.0 and every feature package are new), and `build` always builds an unpublished tool package. So the batch workflow, with decision 11's inputs, cannot produce an artifact made only of already-published files. That rehearsal needs a separate minimal caller. Also, the challenge's "explicit ref" would skew if it is `main`: the script would come from the newest main while a re-run uses the first attempt's workflow text. A hard-coded SHA is impossible because the file would have to name its own commit. The documented context properties `job.workflow_repository` and `job.workflow_sha` solve this. Inlining the text would contradict RELEASE_CHECKLIST.md:23-25 ("Edit the banner file, never the generated page"), so checking out the workflow's own commit fits the existing rule better.

Side findings, both stale cross-references:
- plan:245 points to "决定 12 第 9 点" (decision 12 point 9); the banner fix is point 5, and point 9 is the optional audit.
- plan:572 says the fix is a prerequisite of "§5 第 6 步发布原版构建" (step 6 publishing the pristine build); in rev 4, step 6 does not publish, the publication is step 8 (plan:778). This is left over from rev 3, where the round-3 judge's "§5 step 6's release.yml" (REVIEW3:138, :1001) referred to the old numbering.

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C9/

(a) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C9/verify_sim.sh copies the verify step's directory loop (publish-conda.yml:251-255). I ran it on an artifact laid out as noarch/dummy.conda plus scripts/banner-index.py plus conda/channel-banner.html, fetching the real channel read-only. Output: "::error::conda has no repodata.json", "noarch: repodata fetched", "::error::scripts has no repodata.json", rc=1. A curl to https://conda.qiyuan.me/scripts/repodata.json returns 404; noarch/repodata.json returns 200.

(b) I ran banner-index.py on a stub index page and then the step's grep: "banner applied", grep rc=1. The asserted string is still missing, as the plan already says.

(c) Read-only `gh api` calls:
- isabelle-packaging-ci is public; main is de8f419; GitHub's publish-conda.yml at main still has the broken step at :223-227.
- The last runs are Isabelle_RPC 10-04, Performant_Isabelle_ML 10-03, and isabelle-packaging-ci release-isabelle-ai on 10-09 at 05:03Z. Nothing has published since 85dc11b.
- actions/checkout v4's src/git-directory-helper.ts deletes the target directory's contents when it has no .git ("Deleting the contents of ...").

(d) GitHub docs, read with WebFetch:
- reusing-workflow-configurations: "the `github` context is always associated with the caller workflow"; re-running failed or specific jobs "will use the reusable workflow from the same commit SHA of the first attempt"; re-running all jobs uses the specified reference.
- contexts: `job.workflow_repository` and `job.workflow_sha` give "the repository containing the workflow file that defines the current job" and that file's commit SHA. Neither is available on GitHub Enterprise Server.

Nothing was run on GitHub; the GitHub-side behaviour comes from the docs and the action's source.

Recommended fix: 1. Decision 12 point 5 (plan:571-572). Delete the artifact option. Replace it with a requirement: the banner step must work the same for callers in the same repository (`uses: ./…`) and in other repositories (`uses: xqyww123/isabelle-packaging-ci/…@main`, the batch workflow among them). It does this by checking out the commit that defines the workflow: `actions/checkout` with `repository: ${{ job.workflow_repository }}`, `ref: ${{ job.workflow_sha }}`, a `path:` subdirectory (for example `.publish-conda`) and sparse-checkout of `scripts/banner-index.py` and `conda/channel-banner.html`. The step then calls the files under that path. Never use the default path: actions/checkout empties a workspace that has no .git, which deletes `$CH` if the checkout comes after the pull. Never use a floating `ref: main`: the script would come from a different commit than the workflow text on a re-run of failed jobs. Inlining the script and banner is the alternative, but it would need RELEASE_CHECKLIST.md:23-25 rewritten. The grep must assert a string the banner really contains.

2. §5: add, between step 6 and step 8, one run of the fixed publish-conda.yml@main from another repository. Two ways:
   - the next real release of a component repository;
   - a minimal caller in the tool repository whose artifact holds one already-published .conda, downloaded byte-for-byte from the channel. The guard treats it as a resume (publish-conda.yml:179-180), so the run only re-indexes, re-applies the banner and pushes the index.

   Do not use the batch workflow for this: before step 8 none of its packages are published.

3. Decision 11 (plan:539): add one sentence. A re-run of failed jobs uses the first attempt's publish-conda.yml commit (GitHub docs), so a bug in that file cannot be fixed by the plan's recovery path. This is why item 2 has to happen before step 8.

4. Fix the two stale references: plan:245 "决定 12 第 9 点" should become 第 5 点; plan:572 "§5 第 6 步发布原版构建" should become 第 8 步.

**Judge: partially_confirmed → author_fixes_no_rereview.** Decision 12 point 5 (plan:571-572).

Delete the artifact option. It also breaks the verify loop at publish-conda.yml:251-255 (review-ipc4/defender-C9/verify_sim.sh).

Require that the banner step works the same for same-repository callers (uses: ./…) and cross-repository callers (…@main, the batch workflow among them). It does so by checking out the commit that defines the workflow:
- actions/checkout with repository: ${{ job.workflow_repository }} and ref: ${{ job.workflow_sha }}; both are documented on GitHub's contexts page, verified by the judge;
- a path: subdirectory, never the default path, because checkout empties a workspace without .git and the channel copy $CH lives there;
- sparse checkout of scripts/banner-index.py and conda/channel-banner.html;
- never a floating main.
The grep must assert a string the banner really contains.

§5: between steps 6 and 8, require one cross-repository run of the fixed publish-conda.yml. Either the next component release, or a minimal caller whose artifact holds one already-published .conda, downloaded byte for byte; the guard treats that as a resume. Not the batch workflow: none of its packages is published before step 8.

Decision 11 (plan:539): GitHub documents that re-running failed jobs uses the first attempt's SHA of a reusable workflow. So that recovery path cannot pick up a fix to publish-conda.yml. This refutes the editor's doubt.

Fix two stale references: plan:245 '决定 12 第 9 点' should be 第 5 点, and plan:572 '§5 第 6 步' should be 第 8 步.

### C10 [major] In a HOL-only light release, the only changed bytes (light's component payload) are tied to no tested build, no immutable record and no build from the installed package; round 3's confirmed C4 sub-point survived

Section: §0 item 21; decision 16 point 7; decision 11 inputs, build and accept jobs; §6 (a); §5 steps 7-8; §10 row C4  ·  merged from: user-U6, consistency-CONS4-16, landing-L7

**Statement.** Ruling 21 puts light's HOL session (ROOT, Light_Locale.thy) into isabelle-light-locale and makes a HOL-only change a normal release (plan:80-87). In such a release the only bytes that change are the component payload. Three gaps leave those bytes bound to nothing.
(1) No tested build. Gate (e) reads run-tree's tested records, which are git notes on the Isabelle commit (tools/common.py:174-186; make-patches:137-150). run-tree checks only the Isabelle work tree's git status, and it records the command and the session list (tools/run-tree:98-120). It records neither the HEAD nor the cleanliness of the light repository passed with -d. Decision 16 point 7 requires the files in component_files.txt to be committed and unchanged only at the moment make-patches runs (plan:675-676), which can be after an edit made after the build. So a Light_Locale.thy that no gate ever built can be released. Round 3's C4 raised exactly this, and its defender confirmed it (REVIEW3:685). The judge's action added only the commit-clean requirement, so the confirmed defect survives, and §10's C4 row (plan:881) does not say so.
(2) No immutable record. The batch workflow checks out the feature-repository release tag (plan:525-526). make-patches creates it (plan:677), but no hook protects it: only the Isabelle repository has the reference-transaction hook (tools/hooks/reference-transaction:28-29). The only check is that provenance.txt's release_tag string equals the tag (plan:506-507), and a moved tag passes that check. (b2) catches changed patch files, but not the payload.
(3) No build from the installed package. The channel's component checklist requires that 'the session builds from the installed package' (RELEASE_CHECKLIST.md:637), and decision 11 cites that checklist for its build-job checks (plan:527). But the session build runs only on the legs listed in `session_build_legs`, which defaults to empty (plan:519, :534, :786-788), and §5 steps 7-8 name no leg. A file missing from tools/component_files.txt would ship unnoticed.

Fix.
(1) run-tree records, for every -d directory inside a git work tree, its HEAD and whether the entries of component_files.txt are clean. Gate (e) then requires a tested record whose recorded feature-repository HEAD equals the commit that make-patches is about to extend.
(2) make-patches writes `package_commit: <sha>` into the annotation of the hook-protected Isabelle release tag; it already embeds the provenance lines there (make-patches:210). The batch workflow reads it through its depth-1 fetch of isabelle-patched and refuses a feature checkout whose HEAD differs.
(3) Default session_build_legs to linux-64, with build.yml:498's timeout, whenever the batch contains a feature with a component payload. Alternatively, the publish job refuses such a batch unless that leg built a theory that imports Light_Locale.Light_Locale.
Optionally, gate (e) accepts a tested record from any commit with the same git tree hash, so an upper feature whose merge left the Isabelle tree unchanged needs no new build.

**Editor.** 

**Relaxation proposed by the editor.** With (1) and (2), the release is bound to the tested and shipped bytes by construction, so it no longer depends on the maintainer remembering to rebuild after an edit.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the three parts. Parts (1) and (3) hold, and my experiments confirm them. In part (2) the fact holds, but the reason given for its fix is wrong and the risk is smaller than stated. The claim that §10 hides a deviation is refuted.

(1) No tested build. CONFIRMED with the real tools.
- Where the tested record lives:
  - run-tree compares git status and HEAD only in the Isabelle tree (run-tree:98-109).
  - The note holds only the time, the tree name, the command and the sessions (run-tree:116-119).
  - Gate (e) reads only notes on the Isabelle commit (common.py:174-186; make-patches:137-151).
  - Decision 16 point 7 checks that the component files are committed and unchanged only when make-patches runs (plan:675-676).
- Light_Locale.thy is in fact built by gate (e)'s sessions: Light_Locale_Base declares `sessions Light_Locale` (light tests/ROOT:17-22).
- The real record on light's private-tree HEAD (577e67d, 2026-10-24T15:26:57) lists Light_Locale among its sessions. It records neither light's HEAD nor its cleanliness. Its `-d contrib/light_locale` is even relative to a working directory the record does not name.
- e1.out runs the real run-tree, with a fake bin/isabelle, and then the real make-patches:
  - Scenario A: the build sees an uncommitted v2 of Light_Locale.thy. Then v3 is committed. The emulated point 7 passes, gate (e) passes, and R/light/1 is created. v3 ships and was never built.
  - Scenario B follows the plan's HOL-only procedure (plan:85-87, :545): an empty commit, a tested build, then make-patches. v4 is committed after the build, and R/light/2 ships v4, which was never built.
- So the procedure's tested build is never tied to the change it exists to test, and nothing stops a maintainer (or a concurrent agent in the shared light repo) from committing a new edit after that build.

(2) No immutable record. The fact is confirmed; the reason and the severity are narrowed.
- The feature tag has no hook (only the Isabelle repo has one, reference-transaction:28-29). The renderer compares only the release_tag string (plan:506-507). (b2) never touches share/<pkg> (plan:530-531, :685-691).
- But e2.out shows two things:
  - Moving the feature tag on the remote needs `git push --force`; without it git rejects the push with "already exists".
  - The Isabelle tag the workflow reads is the GitHub copy (plan:531). The local hook does not protect that copy: a force-push moved it while the local tag stayed put.
- Both remote anchors therefore rest on the same "never force-push" rule (migration plan :545, :719).
- The fix's premise ("hook-protected") is false for what the workflow reads. What the fix actually gives is narrower: the payload gets the same anchor the patch files already have, one ref instead of two.

(3) No build from the installed package. CONFIRMED.
- `session_build_legs` defaults to empty (plan:519, :534, :786-788), and §5 steps 7-8 never set it (plan:776-779).
- Registration does not catch a missing theory: `components -u` accepts any directory that has a ROOT (components.scala:252-260, :304-306).
- So the build is the only check of payload completeness that RELEASE_CHECKLIST.md:637 requires, and the plan cites that checklist (plan:527). The channel's own convention builds a component's session on Linux unconditionally (Isabelle_RPC release-conda.yml:432-444).
- With the default, round 2's confirmed "§6 (a) would pass a package without the commands" reopens.
- The default is the author's own choice: the round-3 judge only required an input. It is still a weak shape, because the check runs only if someone remembers to set the input.

Bookkeeping. REFUTED.
- The round-3 judge's actions for C4 did not include tying the tested build to the payload. That was the defender's optional item 4, and the judge's confirmed bullets omit it.
- Rev 4 implements every judge action (plan:675-678, :85-87, :515-521, :545-548, :594-595, :773-774).
- So §10's C4 row (plan:881) hides no deviation. The gap is a finding on its merits, not a silent deviation.

On the editor's relaxation:
- Fix (1) does make the release depend on the bytes that were built, by construction. But requiring the recorded light HEAD to equal the commit being extended is too strict for a shared repository. In e3.out, an unrelated light commit after the build would force a rebuild taking hours.
- Comparing only the component files' contents is exact. My prototype (e3.out) refuses A and B and passes the positive control C despite that unrelated commit.
- Fix (2) does not give immutability by construction (see e2.out).
- The optional reuse of a record across commits with the same tree hash is safe only if the reused record also binds the -d contents.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C10/. The tools were copied there; nothing was installed and no repository was modified.

- fake_isabelle.sh is a stub bin/isabelle. It answers `getenv` and `sessions`, and on `build` it logs the sha and text of the Light_Locale.thy it would build.
- e1.sh / e1.out (part 1) use the real run-tree and make-patches on a toy chain R/pristine -> R/light, with a toy light repository; point 7 is emulated.
  - A: build with v2 uncommitted, then commit v3. The tested note has no light information; point 7 passes; make-patches rc=0 creates R/light/1; v3 ships, v2 was built.
  - B (the plan's HOL-only procedure): empty commit, tested build of v3, commit v4. make-patches rc=0 creates R/light/2 shipping v4.
- e2.sh / e2.out (part 2):
  - The feature tag moves locally with only `-f`.
  - `git push` without force is rejected ("already exists"); `--force` moves the remote tag, and the moved commit still carries `release_tag: R/light/2`.
  - In the Isabelle repo the hook refuses a local `git tag -f`, but `git push --force <sha>:refs/tags/R/light/2` moves the remote copy while the local tag is unchanged.
- e3.sh / e3.out with fixtools/ prototype the smallest fix, about 30 lines in run-tree, common.py and make-patches.
  - A is refused: "built with uncommitted Light_Locale.thy".
  - B is refused: "component files changed since <head>".
  - Positive control C (commit, build, an unrelated light commit, make-patches) passes and creates R/light/3.
- Read-only checks:
  - `git -C contrib/Isabelle2025-2-light_locale notes --ref=tested show HEAD`: a real record with a relative `-d contrib/light_locale` and no light HEAD.
  - components.scala:252-260 and :304-306: a ROOT-only directory registers.
  - light tests/ROOT:17-22 and tools/required_sessions.txt.
  - Isabelle_RPC release-conda.yml:432-444.
  - REVIEW3:642-785 (C4) and :2676-2794 (C21).

Recommended fix: (1) Required.
- run-tree: for every `-d` directory inside a git work tree, resolve it, then add one line to the tested note: `dir: <toplevel> head <sha> dirty <paths|->`.
- run-tree: write no record if those lines change during the build.
- Gate (e), for a package with tools/component_files.txt: count only records that have that package's toplevel, where no listed entry was dirty, and where `git diff --quiet <recorded head> HEAD -- <entries>` holds.
- Compare file contents, not HEAD equality: the light repository is shared, and point 7 already chose per-file checks for that reason.
- Amend these to match: the migration plan glossary entry for the tested record (ISABELLE_GIT_MIGRATION_PLAN.md:33-36), run-tree's docstring, decision 16, and §10.

(3) Required.
- In decision 11 and §6 (a): whenever the batch contains a feature with a component payload, linux-64 always runs §6 (a)'s session build, with build.yml:498's timeout.
- `session_build_legs` only adds further legs. This follows Isabelle_RPC release-conda.yml:432-444 and RELEASE_CHECKLIST.md:637.
- Alternatively: refuse `publish=true` at dispatch when that leg is missing.

(2) Optional and minor.
- make-patches adds `package_commit: <sha>` to the Isabelle tag's annotation, not to provenance.txt. The workflow then checks out the feature repository at that sha.
- Describe it as giving the payload the same anchor as the patch files, not as immutability: the hook does not protect the GitHub copy.

Leave the optional reuse of a record across commits with the same tree hash out, unless it also requires matching `dir:` lines.

**Judge: partially_confirmed → owner_decides.** (1) Put owner question 3. If the owner approves:
- run-tree adds, for each -d directory inside a git work tree, a line 'dir: <toplevel> head <sha> dirty <paths|->', and writes no record if those lines change during the build;
- for a package with tools/component_files.txt, gate (e) counts only records with that toplevel, no listed entry dirty, and `git diff --quiet <recorded head> HEAD -- <entries>`. This compares contents, not HEAD equality, because the light repository is shared (review-ipc4/defender-C10/e3.out);
- amend the migration plan's tested-record glossary entry, run-tree's docstring, decision 16 and §10.

(3) Author, regardless of the answer: whenever the batch contains a feature with a component payload, linux-64 always runs §6 (a)'s session build, with build.yml:498's timeout. session_build_legs only adds further legs (RELEASE_CHECKLIST.md:637; Isabelle_RPC release-conda.yml:432-444).

(2) Optional: make-patches writes package_commit into the Isabelle release tag's annotation, and the batch workflow checks out that sha. Describe it as giving the payload the same anchor the patch files have, not as immutability: the GitHub copy of a tag can be force-pushed (defender-C10/e2.out).

Refuted: the 'silent deviation' claim. The round-3 judge's C4 actions (REVIEW3:757-790) never included this binding, so the gap is a finding on its merits.

### C11 [major] Residue blocks and their recovery are written for a lone removal: they are false when the package is replaced, a relink of a lower feature over a CONFLICT silently reverses the features above it, and in a pruning removal only the top block's recovery works, including in the frozen `||` text

Section: Decision 9 (pre-unlink rules and `||` text); decision 7 cap; §4 residue block and CONFLICT text; decision 15  ·  merged from: conda-conda-5, user-U7

**Statement.** A pre-unlink runs whenever its package is unlinked, and that includes replacement, not only removal. A pre-unlink cannot tell the two apart (link.py:1630-1634; REVIEW3:314). Every update to a new isabelle build relinks every feature package (ruling 22, plan:88-92), and the README recommends `--force-reinstall <feature>` to mark a package as explicitly requested (plan:603-604). The residue block and the rule 'move what can be moved' (plan:412-414, :478-480, §4 plan:742-751) are written as if a pre-unlink always meant removal.
(1) On `conda update --all` with any CONFLICT file, every pre-unlink at or below the CONFLICT feature writes a residue block. The block says the changes stayed 'before its package was removed', that 'status will not see them once the package is gone', and tells the user to run `--force-reinstall isabelle` and delete the created files. Yet the same transaction relinks the packages and ends applied (review-ipc4/critic-conda/run3.out: two residue blocks claiming removal, then 'applied: feat_a feat_b dev_patches').
(2) `--force-reinstall` of a feature below a CONFLICT. Its pre-unlink reverses that feature and every movable file above it (decision 7). The post-link's cap (plan:407-408) then re-applies nothing at or above the CONFLICT feature. The features above it end not-applied, while the CONFLICT text says 'light_locale and the features above it were left untouched' (plan:734). Only a one-line notice is printed, because PKG_NAME is not the top feature's (critic-conda/run3.out).
(3) A pruning removal runs the pre-unlinks from the top down (plan:650-651). When the lock is busy or the tool cannot start, every package writes a residue block. Each block's recovery, and the frozen `||` text of every pre-unlink (plan:460), names that block's own package: `conda install <包名>; conda remove <包名>`. Only the top block's recovery cleans the tree. Following the lowest block's recovery leaves the upper features' changes in the tree, and no installed package shows them any more (critic-conda/run5.out; critic-user/run3.out case j; critic-user/run4.out case j2: b=B2, d=D2, c=C2 and src/new.ML remain while features.d is empty). The `||` text is frozen in every published package, so a mistake there can never be fixed for installed versions.
(4) Decision 9 contradicts itself about what a block lists: 'pre-unlink 只列自己这个 feature 的文件' against the trigger 'F 或其上 feature 的文件还有层级 ≥ k' (plan:478-479).

Fix.
- Word the block for both cases ('before its package was removed or replaced'). Say 'if you are removing the feature' before 'delete the created files', since the tool cannot know which case it is in.
- Make every block's recovery name the highest feature package whose directory is in features.d at that moment. The pre-unlink can read this, because features.d still lists every package of the transaction (plan:469-470).
- Make the frozen `||` text say 'install this package together with every feature package the same command removed, then remove them'.
- Fix the file-list rule to one reading.
- Correct the CONFLICT text, or document in decision 7 and the README that relinking a lower feature over a CONFLICT reverses the features above it.
- Add the three shapes to decision 15, including 'follow the last block printed, then assert the tree is clean'.

**Editor.** Point (2) is the correct consequence of decision 7's cap, which refuses to apply anything above a CONFLICT feature. It is not a design defect; only the text that describes it is false.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

Bottom line: a residue block is the message a pre-unlink hook writes when it cannot fully reverse its feature before conda unlinks the package. Rev 4 writes it as if every pre-unlink meant "the package is being removed". It also gives each block a recovery that names that block's own package. Points (1), (3) and (4) are confirmed; I strengthened (3) with a new measurement. Point (2) is confirmed only as a text defect, as the editor's rebuttal says.

(1) CONFIRMED: the block is false when the package is replaced.
- conda gives a pre-unlink only ROOT_PREFIX, PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM (conda core/link.py:1630-1634).
- It runs a package's pre-unlink whenever that package is in the unlink set. An update that changes the build puts the package there (core/solve.py:1415-1416), and so does --force-reinstall (:1426-1432).
- Ruling 22 makes every new isabelle build relink every feature package (plan:88-92). The README recommends --force-reinstall of a feature to mark it explicitly requested (plan:603-604). The plan itself knows lower packages get relinked (plan:468).
- Yet the block says "before its package was removed" and "status will not see them once the package is gone". It then tells the user to delete the created files and, if the lock was busy, to `conda remove <pkg>` (plan:744-750). The block is written whenever F or a feature above it still has files at level ≥ k, the level of F itself (plan:478-480). Nothing limits it to removal.
- critic-conda/run3.out shows `conda update --all` printing two such blocks and then "applied: feat_a feat_b dev_patches".
- In a replacement, following the advice would remove a package the user is keeping, or would half-unapply it (delete files created by a feature that stays installed).
- The same "removed" wording was already in rev 3 (PLAN.rev3:583) and no earlier round raised it, so this is a new finding, not a silent deviation.

(2) The behaviour is decision 7's intended cap, so the editor's rebuttal holds. The texts describing it are false.
- Measured: x2.out case (2). A user edits feat_b's file, then runs --force-reinstall on the lower feat_a.
  - feat_a's pre-unlink prints "reversed: feat_a feat_b dev_patches".
  - The post-link then applies only feat_a, because the cap stops it below the CONFLICT feature (plan:407-408).
  - dev_patches ends not-applied, and conda prints only a one-line notice.
- False texts:
  - The CONFLICT text says the features above "were left untouched" (plan:734). That is false at transaction level, also under `conda update --all` when the conflicting file is untracked.
  - The README says the cost of --force-reinstall is "反打再重打" (reverse, then re-apply) (plan:603-604). Here the features above the CONFLICT are not re-applied.
- The challenge's own fix for (2) asks only for text changes, so it and the rebuttal agree.

(3) CONFIRMED and strengthened; partly narrowed.
- The only measurement behind the recovery, defender-C23 L3 (cited at plan:845 and :484-485), reinstalled the top package featc, which pulled in the two lower ones (review-ipc3/defender-C23/run.out:41-62). The plan generalizes that to each block's own <包名> (package name), both in the frozen `||` text (plan:460) and in §4 (plan:750).
- The critics' toy tools listed the files of F and every feature above it. That is only one reading of plan:478. So I re-ran the experiment with the literal "own files only" reading.
- My setup also has a file shared by a lower and an upper feature. The real chain has such files: light's tools/patched_files.txt:12,20 lists syntax_phases.ML and attrib.ML. show_types_nv patches both, and it moves into dev_patches (plan:587-590). Plan:619-620 confirms that syntax_phases.ML has the stacked-context shape.
- Result (x1.out): a pruning removal under a held lock prints three blocks, top-down.
  - Following them lowest first (the last one printed) ends with dev_patches' change SD6 still in s.ML, while features.d is empty. That is exactly the invisible leftover the block exists to prevent.
  - feat_a's own recovery printed only "reversed: feat_a" and silently left dev's part in a file its own block had listed.
  - After that, even the top block's recovery fails with CONFLICT.
  - Following the top block first cleans the whole tree.
- Narrowed: with unshared files, each block's own recovery does clean its own listed files, and following all blocks top-first converges. The defect is that the recovery depends on order, the plan names no order, and the order a user most likely follows (the last block printed) can leave an unfixable leftover. The `||` text is frozen once published (decision 1), so this must be right before the first release.

(4) CONFIRMED: plan:478 says "只列自己这个 feature 的文件" (list only this feature's own files), but triggers on "F 或其上 feature 的文件" (files of F or of features above it).
- Read literally, the tool prints a block with nothing in it. My toy did this in x1.out and x2.out ("listed: (no files of its own)").
- The cause is that two round-3 judge actions were combined literally: C8 (list only the feature's own files) and C23 (write the block when F or a feature above it leaves files behind). §10 records both as done but not that they collide.

Severity: (1), (2) and (4) are text defects. Only (3) can leave invisible changes, and only on rare paths (lock busy or a tool that cannot start, during a pruning removal). "Major" is defensible mainly because the `||` text is frozen.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C11/

Setup (common.sh, src/mkchan4.py, src/toytool.py):
- I copied critic-conda's toy channel and toy tool, which use real `git apply` with the plan's level rules, the hook fragment verbatim, and the build pins.
- I made two changes:
  - toytool.py lists only the feature's own files in the block, the literal reading of plan:478, while keeping the "F or above" trigger. It prints the block's own recovery.
  - mkchan4.py adds two shared files: s.ML, which feat_a and dev_patches change in separate hunks, and t.ML, which feat_b and dev_patches change with dev_patches' hunk context containing feat_b's added line (the syntax_phases.ML shape).
- Real conda 25.11.1, with private HOME, CONDARC, CONDA_PKGS_DIRS and envs directory.

x1.sh / x1.out (pruning removal with the lock held by another process; the toy's lock wait was set to 2 s):
- `conda remove isabelle-dev-patches` pruned all three features and printed three blocks, top-down. They listed (c, new_c, s, t), (b, t) and (a, s), each naming its own package.
- lowest-first, following the blocks in the order feat-a, feat-b, dev-patches:
  - feat-a's recovery printed only "reversed: feat_a" and left s.ML as s1,s2,s3,s4,s5,SD6,s7.
  - feat-b's install hit CONFLICT on t.ML; its removal printed a block with "listed: (no files of its own)".
  - dev-patches' install hit CONFLICT on s.ML.
  - Final state: s.ML still holds SD6, features.d is empty.
- top-first, starting with dev-patches' recovery: the whole tree came back clean. The two later recoveries only re-applied and reversed again.

x2.sh / x2.out case (2): with b.ML edited, `conda install --force-reinstall isabelle-feat-a`:
- The pre-unlink printed "reversed: feat_a feat_b dev_patches" and an empty block that says "removed".
- The post-link printed "applied: feat_a" and a one-line notice only.
- Final state: t.ML, c.ML and new_c are reversed, so dev_patches is not-applied.

Abandoned: x3 (`update --all` with the lock busy during the pre-unlinks only) failed with ENOSPC because the shared /tmp tmpfs was full. I deleted my environments and package cache to free space, so I rely on critic-conda/run3.out for the replacement case.

Sources read: conda core/link.py:938-967 and :1630-1634, core/solve.py:1413-1453; review-ipc3/defender-C23/run.out:41-62; REVIEW3 C8 (:1152-1320) and C23 (:2870-2975); PLAN.rev3:575,583.

Recommended fix: All of these are wording and test changes within ruling 17; no ruling is reversed.

1. §4 residue block (plan:744-750) and the frozen `||` text (plan:460):
   - Say "before its package was removed or replaced".
   - Put "If you are removing <feature> (not updating or reinstalling it):" before every recovery step.
   - Make "status will not see them" conditional on removal, or drop it.

2. One recovery that does not depend on order:
   - The block the tool computes names the highest feature package whose directory is in features.d when the pre-unlink runs. That is computable, because all pre-unlinks run before any unlink (link.py:938-947). So every block of a transaction gives the same command: `conda install <top>; conda remove <top>`.
   - The frozen `||` text cannot compute that, so it says: "make the tool runnable (conda install --force-reinstall isabelle-patch-control), then conda install this package together with every other feature package the same command removed, then conda remove them again."
   - Correct the evidence note at plan:845: the measurement reinstalled the top package.

3. Decision 9 (plan:478-479): make the trigger and the file list the same set.
   - Recommended: the feature's own files that did not return below k. Leftovers of an upper feature are reported by that feature's own pre-unlink, which runs first in a removal, or stay visible because that package is still installed.
   - In §10, record how the C8 and C23 judge actions were reconciled.

4. CONFLICT text (plan:734): change "left untouched" to "were not applied". Add one sentence to decision 7 and to the README text (plan:603-604): relinking a feature below a CONFLICT reverses the features above it, and they stay not-applied until the CONFLICT is repaired.

5. Decision 15 (plan:650-653):
   - Name which package the residue-recovery case reinstalls.
   - Add a pruning removal under a held lock with a file shared by a lower and an upper feature: follow only the LAST block printed, then assert the tree is clean and no feature directory remains.
   - Add `conda update --all` with a CONFLICT: assert the block's wording and the final applied state.
   - Add --force-reinstall of a feature below a CONFLICT: assert the final state and that the texts match it.

**Judge: confirmed → author_fixes_no_rereview.** §4 residue block (plan:744-750) and the frozen || text (plan:460):
- say 'removed or replaced';
- put 'If you are removing <feature>' before every recovery step;
- make 'status will not see them' conditional on removal.

Every block's recovery names the highest feature package whose directory is in features.d when the pre-unlink runs. All pre-unlinks run before any unlink (link.py:938-947), so every block of one transaction gives the same command. The frozen || text, which cannot compute this, says: make the tool runnable, install this package together with every other feature package the same command removed, then remove them again.

Other edits:
- Decision 9, plan:478-479: give the trigger and the file list one reading. Recommended: the feature's own files that did not return below k.
- CONFLICT text, plan:734: 'were not applied'.
- Decision 7 and the README text (plan:603-604): relinking a feature below a CONFLICT reverses the features above it, and they stay not-applied until the CONFLICT is repaired.
- Decision 15 (plan:650-653): name the reinstalled package. Add a pruning removal under a held lock with a file shared by a lower and an upper feature; follow only the last block printed; assert a clean tree and an empty features.d (review-ipc4/defender-C11/x1.out). Add update --all with a CONFLICT, and --force-reinstall of a feature below a CONFLICT (defender-C11/x2.out).
- Correct plan:845's evidence note: the measurement reinstalled the top package.

Point (2) is decision 7's intended cap; only the texts describing it are false.

### C12 [minor] 链顶 is defined as dev_patches but is also used for the highest installed feature (in the diagnosis rule), the releasing tip and the checked top; read by the glossary, users without qiyuan-dev-patches never get a full diagnosis from a feature hook

Section: Glossary (plan:16); §0 item 28; decision 9; §4; decision 15; decisions 11.2 and 17  ·  merged from: conda-conda-6, consistency-CONS4-7, user-U8

**Statement.** The glossary defines 链顶 as dev_patches (plan:16). Decision 9 and §4 give the full diagnosis to the isabelle hook and 'the hook of the 链顶 feature' (plan:475-476, :731). The intended meaning is the highest feature whose directory is currently in features.d. That is the refinement the round-3 judge adopted, which needs 'the next feature the user installs' to count as the top (REVIEW3:1306-1311). The plan uses other words for the same idea, and the same word for other ideas:
- decision 15 says 顶层 feature (plan:646);
- §4's apply line uses 链顶 for the top of the installed chain (plan:703);
- §0 item 28's paraphrase uses it for the releasing tip (plan:126), while decision 16 point 5 says tip (plan:671);
- decisions 11.2 and 17 use it for the top feature being checked (plan:531, :685).
Read by the authoritative glossary, a user without qiyuan-dev-patches, which is every user but the author, never receives the full diagnosis from a feature hook. `conda install isabelle-light-locale` over an edited file would then print only one-line notices that point at `status -v`, which prints levels, not remedies. CLAUDE.md requires one canonical term per concept.

Fix. Keep 链顶 = dev_patches. Add a glossary term for 'the highest feature whose directory is in features.d' (for example 已装链的最高 feature), and use it in decision 9, §4 and decision 15. Say that the tool maps $PKG_NAME to it through names.package_name. Write 'the releasing commit (tip)' in item 28's paraphrase.

**Editor.** CONS4-7's 'major' is too high. The intended reading can be recovered from the round-3 judge's action, from decision 15's case wording and from plan:703, so this is a terminology defect. The sub-point in conda-6 and CONS4-8, that §10's C8 row wrongly calls the rule round 2's, is dropped. The round-3 judge's own action (5) told the author to record 'the return to the judge's rule' (REVIEW3:1321).

**Relaxation proposed by the editor.** If C3's relaxation is adopted, the diagnosis rule needs only this one new term (the hook of the highest installed feature), and the isabelle-hook clause disappears.

**Defender: confirmed** (needs owner: False).

In short: 链顶 (the top of the chain) is used for two different things. The glossary binds it to the fixed last feature, dev_patches. The diagnosis rule needs it to mean the top of the chain the tool actually built. Read literally, the glossary brings back exactly the missing-diagnosis case the round-3 judge fixed. I tried to refute C12 and could not. Every factual claim holds. Two details need tightening, and the editor's relaxation turns out to hold even without C3.

WHAT IS CONFIRMED
1. The glossary says 链的两端叫链底（pristine）和链顶（dev_patches）: the chain's two ends are the bottom (pristine) and the top (dev_patches) (plan:16).
2. Decision 9 gives the full diagnosis to the isabelle hook and to 链顶 feature 的钩子, the hook of the 链顶 feature (plan:475-476). §4 says the same (plan:731).
3. The intended meaning is the last feature of the chain built from features.d:
   - the round-3 judge adopted the refinement because the next feature the user installs must count as the top (REVIEW3:1306, :1311);
   - the round-3 defender's prototype computes the top as `chain | tail -n1` (review-ipc3/defender-C8/mkchan.py:37).
4. The same concept also goes by other words:
   - 顶层 feature (plan:646, also :603, :650-651, :655);
   - 链顶 in the apply line (plan:703), whose target n counts installed features only (plan:380, :407).
5. Other concepts also go by 链顶:
   - the releasing commit in item 28's paraphrase (plan:126), where decision 16 point 5 says tip (plan:671) and so did the judge (REVIEW3 C7);
   - dev_patches in §7 (plan:830).
6. The consequence of a literal glossary reading is measured. My toy uses conda 25.11.1 and real git apply. The chain is a<b<c<d, where d stands for dev_patches and is never installed. The isa post-link carries the fragment plus ruling 26's re-run, implemented as decision 12.2 describes. Full diagnoses counted:
   - S1: edit b.ML, then install featc (a, b, c linked in one transaction): 0;
   - S2: a and b installed, edit b.ML, then install featc: 0.
   Each run printed only one-line notices (run.out:4-17). The one-liner points at `status -v`, which lists files and levels (plan:402-403). CLI `apply` prints only the CONFLICT files and git's output (plan:415). So the repair steps (plan:731-740) never reach such a user.

REFUTATION ATTEMPTS THAT ONLY LOWER THE SEVERITY (minor is right, major is too high)
- The intended reading can be recovered from the text:
  - decision 3 uses 链 for the built chain: 没装任何 feature 包时链只有链底, "with no feature package installed the chain is only the bottom" (plan:328);
  - decision 15's toy tests have no dev_patches at all (plan:615, :646);
  - a literal implementation would hard-code a feature name into the diagnosis rule, against the pure-framework ruling (plan:43).
- But the glossary is explicit, and the literal reading reproduces the S2 defect.

NUANCES
(a) The overloading starts at plan:15, not plan:16. 链 itself means the full release chain at plan:15, :37 and :127, and the built chain at plan:325, :328, :467, :477 and :707.
(b) Decisions 11.2 and 17 (plan:531, :685, :689) are not a fourth meaning. Both assemble a features.d, and 链顶 there is the top of that built chain, the same concept as plan:703.
(c) The proposed definition, "the highest feature whose directory is in features.d", is imprecise. A directory off the chain has no height. Say instead "the last feature of the chain decision 3 builds". The diagnosis rule needs it only after the chain is built; a broken chain is reported by every hook anyway (plan:477).
(d) The package_name point is only half missing. plan:297-298 already says the tool needs names.py at runtime, but decision 9 only implies the mapping from $PKG_NAME through the word 不认识, "unknown" (plan:476).

THE RELAXATION ON ITS MERITS: it holds now, independent of C3
I have not seen C3. Ruling 26's re-run runs the 链顶 feature's post-link, with its own PKG_NAME, in every transaction that links isabelle:
- isabelle only: the re-run order was feata, featb, featc (run.out:81);
- isabelle together with featc: the re-run skipped featc, because conda writes conda-meta records only after the post-links (plan:213), confirmed at run.out:96. Conda then ran featc itself.
So the isabelle-hook clause only adds copies. Full diagnoses counted under the plan's rule versus the 链顶-only rule:
- S1: 1 vs 1;
- S2: 1 vs 1;
- S7, `--force-reinstall isa` with a created file holding other content: 2 vs 1;
- S6, `--force-reinstall isa featc`: 2 vs 1;
- S5, `--force-reinstall feata`: 0 vs 0.
S7 is not among decision 15's three shapes, and it is what a user gets after following the plan's own remedy when the reinstall cannot fix the cause. With the 链顶-only rule, decision 15's three cases become one invariant: exactly one full diagnosis whenever the transaction links isabelle or the 链顶 package, and otherwise one-line notices. The one cost: in an isabelle-only transaction the diagnosis now relies on the re-run code in the CI plan, which ruling 26 already requires and decision 15 already tests.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C12/ (mkchan.py, run.sh, run.out). The scripts are adapted from review-ipc3/defender-C8.

Setup:
- conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and a file:// channel;
- the toy isa build 1 has post-link = the rev-4 fragment followed by ruling 26's re-run (a Python scan of conda-meta/*.json depends, topological order, PKG_NAME/PKG_VERSION/PKG_BUILDNUM set as conda sets them);
- features a<b<c<d, pinned like decision 10; b also creates src/nb.ML; d stands for dev_patches and is never installed;
- three toy tools that differ only in who writes the full CONFLICT diagnosis: 1.0 = isabelle or fixed d (the glossary reading); 2.0 = isabelle or the last feature of the built chain (the intended rev-4 rule); 3.0 = only that last feature (the editor's relaxation).

Full diagnoses, tools 1.0 / 2.0 / 3.0:
- S1: 0 / 1 / 1;
- S2: 0 / 1 / 1;
- S7: 1 / 2 / 1;
- S6: 1 / 2 / 1;
- S5: 0 / 0 / 0.

hooks.log shows:
- every hook got the right PKG_NAME;
- in S7 the re-run found and ran featc;
- in S6 conda-meta lacked featc during the isa post-link (run.out:96), so featc's hook ran once, by conda.

I also read plan:12-37, :297-298, :317-333, :380-403, :407-419, :430-488, :513-551, :612-661, :663-695, :697-756, :811-830, :871-914; REVIEW3:1152-1321 and the C7 section; migration plan :11-45 and :351; conda link.py:1630-1634.

Recommended fix: Smallest fix, terminology only. Ruling 17 lets the author make it.
1. Glossary (plan:15-16): define 链 (the chain) as the chain decision 3 builds by exact tags from a features.d. It is always a prefix of the order 链序, whose full form is pristine -> ... -> dev_patches. 链底 (the bottom) is pristine. 链顶 (the top) is the last feature of that chain; with no feature package installed, the chain is only 链底.
2. Rewrite the three places that mean something else:
   - plan:37: 整条链 -> 链序上的全部 feature 包 (all feature packages in the chain order);
   - plan:830: dev_patches 在链顶 -> dev_patches 在链序最末 (dev_patches is last in the chain order);
   - plan:126: 在链顶的内容 -> 在 tip（待发布的 commit）的内容 (the content at the tip, the commit being released), matching decision 16 point 5 (plan:671).
3. Replace 顶层 with 链顶 at plan:603, :646, :650-651 and :655.
4. Decision 9 (plan:475): add one clause saying the hook compares $PKG_NAME with names.package_name(链顶).
After this, 链顶 at plan:475, :531, :622, :685, :689, :703 and :731 is correct unchanged.

The challenge's own fix (keep 链顶 = dev_patches and add a new term) also works. But the new term must then also replace 链顶 at :531, :622, :685, :689 and :703, which is more edits. And its wording should be "the last feature of the chain decision 3 builds", not "the highest feature whose directory is in features.d".

Recommended alongside: adopt the relaxation now; it does not depend on C3.
- Drop the isabelle-hook clause at plan:475-476 and plan:731. Keep the fallback: when PKG_NAME is unset or unknown, behave like the 链顶 hook.
- Say in decision 9 that ruling 26's re-run (decision 12 point 2) runs the 链顶 package's post-link in every transaction that links isabelle.
- Replace decision 15's three shapes (plan:646) with one statement: exactly one full diagnosis whenever the transaction links isabelle or the 链顶 package, otherwise one-line notices.
- Add the isabelle-only case to the hook-layer test: `--force-reinstall isabelle` with a created file holding other content.

Optional wording, also under ruling 17: point the one-line notice at a command that prints the repair steps, not at `status -v`.

**Judge: confirmed → author_fixes_no_rereview.** Fix one canonical term for the last feature of the chain decision 3 builds from features.d, and a separate one for dev_patches. Two ways to do it.

- Fewer edits: redefine 链顶 in the glossary (plan:15-16) as the last feature of the built chain. Then write 链序上的全部 feature 包 at plan:37, 链序最末 at plan:830, and tip（待发布的 commit） at plan:126. Replace 顶层 with 链顶 at plan:603, :646, :650-651 and :655.
- Or keep 链顶 = dev_patches and add the new term at plan:475, :531, :622, :685, :689, :703, :731 and :646.

Decision 9 says the hook maps $PKG_NAME through names.package_name.

Drop the isabelle-hook clause from the diagnosis rule even if C3 is not adopted. Ruling 26's re-run already runs the top feature's post-link in every transaction that links isabelle (review-ipc4/defender-C12/run.out: S6 and S7 give 2 full diagnoses under rev 4, 1 under the rule without the clause).

Severity: minor.

### C13 [minor] make-patches' new two-repository write cannot be resumed after a partial failure, and its path-limited commit silently leaves new patch files out

Section: Decision 16 points 7-9  ·  merged from: engine-engine-4, landing-L5

**Statement.** Decision 16 point 7 orders three writes in two repositories (plan:677-678): commit patches/<R>/ in the feature repository, create the Isabelle release tag, and create the tag of the same name in the feature repository. Each write can fail separately.
- If the last write fails, a rerun stops at 'release tag ... already exists' (make-patches:86-88). The reference-transaction hook forbids moving the tag (tools/hooks/reference-transaction:28-29), and migration §7 rule 14 forbids hand-made release tags (ISABELLE_GIT_MIGRATION_PLAN.md:561). So no command can complete the release, and the batch workflow has no feature tag to check out.
- If the Isabelle tag fails, a rerun regenerates byte-identical files. The commit-by-path step then has nothing to commit, and `git commit` exits non-zero.
- '按路径提交 patches/<R>/' does not stage new files. In git 2.43, `git commit -m ... -- patches/R/` returns 0 and commits the rewritten provenance.txt and the deletion of the old patch, but leaves the new untracked patch file out (review-ipc4/critic-landing/commit.out). The tag would then point at a commit whose provenance names the new release while a patch file is missing.
- Point 7 lists the entries of component_files.txt as committed and unchanged, but not tools/component_files.txt itself, which the renderer reads at the tag (plan:505-506).
- 'tip 上已有同一 feature 的发布 tag' does not say whose tip.
This order is the round-3 judge's own (REVIEW3 C4 action (1)), so it is not a silent deviation, but the defect is real.

Fix.
- Stage every generated and deleted path by name.
- Before any tag, verify that `git ls-tree -r <new commit> -- patches/<R>/` lists exactly the generated blob ids.
- Commit only if the result differs from HEAD; a rerun with nothing left to commit is not an error.
- Create the feature-repository tag next, accepting an existing one on the same commit.
- Create the Isabelle release tag last, so that its existence marks the release complete. A rerun after any partial failure then completes the release.
- Add tools/component_files.txt to the committed-and-unchanged list, and write 'the tip of <R>/<feature> in the Isabelle repository'.
- Add these cases to make-patches' toy tests.

**Editor.** 

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute each part. Every part holds except the "whose tip" point, which is only a wording nit. Severity minor is right.

1. A failed feature-repository tag cannot be completed. CONFIRMED.
- Point 7 orders the three writes as: commit in the feature repository, then the Isabelle release tag, then the feature-repository tag (plan:675-678).
- A rerun is refused before any gate runs, because the Isabelle tag now exists (make-patches:86-88: "release tag ... already exists").
- The hook refuses to move the tag (tools/hooks/reference-transaction:28-29). It does let a tag be deleted (:13), but migration §7 rule 14 forbids creating, moving or deleting a release tag by hand (ISABELLE_GIT_MIGRATION_PLAN.md:561-562).
- The glossary defines a release tag by its name `<R>/<branch>/<version>` (migration:29). So the feature-repository tag of the same name is a release tag too, and it may not be typed by hand either.
- Rerunning with version v+1 is refused by point 7's own rule "tip 上已有同一 feature 的发布 tag 时拒绝" (refuse when the tip already carries a release tag of the feature). The only way out is a new Isabelle commit, a new tested build (for light: five light sessions plus FOL and ZF, plan §5 step 3), and a burned version number.
- Decision 11 checks out each feature repository at its tag (plan:524-525), so release v can never be published.
- The round-3 defender for C4 recommended "State the recovery: if the Isabelle tag exists and the package tag does not, a rerun only adds the package tag" (REVIEW3, defender recommended fix 1). The judge's action dropped that sentence. Rev 4 follows the judge, so this is not a silent deviation, but the gap survived.

2. A failed Isabelle tag cannot be completed either. CONFIRMED.
- Every provenance field is deterministic (make-patches:194-205), so a rerun regenerates byte-identical files.
- `git commit -- patches/R/` then exits 1 ("nothing to commit"). See commit_semantics.out case (2) and resume.out "rev 4 as written, fail=isabelle_tag".
- The plan nowhere says that "nothing to commit" is acceptable. I searched for git add, stage, ls-tree and rerun: the only hit is plan:85, which is unrelated.

3. The path-limited commit silently drops new files. CONFIRMED, and stronger than the critic stated.
- In git 2.43, `git commit -m ... -- patches/R/` returns 0. It commits the rewritten tracked files and the deletion of the old patch, but leaves new untracked files out (commit_semantics.out case (1)).
- Light hits this on its very first release:
  - light tracks 32 patch files in the old `diff -ruN` format and no provenance.txt (`git -C contrib/light_locale ls-files patches`; head of src-Pure-Isar-bundle.ML.patch);
  - make-patches rewrites all 32 as `diff --git` blocks and creates provenance.txt;
  - so the literal commit returns 0 without provenance.txt, and both tags land on that commit.
- The renderer reads patches/<R>/provenance.txt at the tag (plan:504-507), so isabelle-light-locale 1 can never be built.
- A feature that starts editing a new file loses that patch file. The batch workflow's roundtrip gate would catch the difference, but only after the immutable tags already exist. The file also stays untracked, so the next release drops it again.
- New repositories fail loudly instead: when nothing under patches/R/ is tracked, the commit fails with a pathspec error and rc 1 (case (3)).
- Migration §7 rule 5 (stage only by explicit path) points the right way, but plan point 8 (plan:679) lists only "删旧 *.patch、复制新文件、写 provenance.txt、提交、打 tag" (delete the old *.patch files, copy the new files, write provenance.txt, commit, tag). There is no staging step and no check of what was committed.

4. tools/component_files.txt itself is not checked. CONFIRMED.
- Point 7 requires the files listed in tools/component_files.txt to be committed and unchanged, but not component_files.txt itself (plan:675). The other three gate files are named as files.
- The renderer decides whether to ship the HOL session from component_files.txt at the tag (plan:501, :506).
- Light does not have that file yet; decision 13 adds it (plan:592; `ls contrib/light_locale/tools` shows no such file).
- If it is left uncommitted, make-patches passes on the working-tree copy, and the tagged commit ships no HOL session. §6 (a) would catch this only after the tags exist.

5. "Whose tip" is not said. Wording nit only, not a defect.
- In make-patches, "tip" is the Isabelle branch's commit (make-patches:89), and point 5 uses it the same way.
- §0 item 21 (plan:85-87) explains the refusal as needing a new commit on `<R>/light_locale`, which is the Isabelle branch.
- Point 7 sits under the heading "feature 仓库侧" (feature repository side), so saying "the Isabelle repository's tip of <R>/<feature>" is a harmless clarification. Nothing breaks without it.

Assessment of the critic's fix:
- Putting the Isabelle tag last fits make-patches' own docstring and code ("last the annotated tag ... is created", make-patches:20-21 and the comment "the tag, last" at :209) and migration rule 14 ("最后创建发布 tag", create the release tag last). With that order, make-patches:86-88's refusal stays correct as the "release complete" test. That is one marker instead of a memory rule, so the fix is more elegant.
- A dangling feature tag left by an abandoned run cannot be published. The roundtrip job fetches the top release tag from isabelle-patched, and the tool's exact-tag chain linking (decision 3) rejects a base nobody released.
- Two refinements are needed. First, accept an existing feature tag when its tree passes the same blob check, not only when it is "on the same commit": in this shared working tree another agent may commit between the two runs. Second, compare only patches/<R>/*.patch and provenance.txt, not "exactly" the whole directory: make-patches deletes only *.patch files (:159), and the tool reads only those two kinds of file (decision 2).

Experiment: Everything ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C13/ with git 2.43.0, GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1. Only toy repositories were used; no owner repository was modified.

(1) commit_semantics.sh, output in commit_semantics.out. The toy package repository has tracked old-format patches, which make-patches rewrites; a deleted old.patch; a new new.patch and provenance.txt; and another agent's staged edit.
- (1) The literal `git commit -m release -- patches/R/` gives rc=0. HEAD holds f1-f3, the deletion is committed, and new.patch and provenance.txt stay untracked.
- (2) Rerunning with nothing left to commit gives rc=1.
- (3) With nothing under patches/R/ tracked yet: pathspec error, rc=1.
- (4) Staging by name (`git add` the generated files, `git rm --cached` the removed one), committing only when `git diff --cached --quiet` says something differs, and comparing blob ids: everything is committed, the other agent's staged edit is untouched, and a rerun is a no-op with rc 0.
- (5) A path-limited `git add -- patches/R/` also works.

(2) resume.py, output in resume.out. A prototype of the three writes, with the real reference-transaction hook copied into the toy Isabelle repository. In each scenario one write fails, then a clean rerun follows.
- Rev 4 as written, success case: the feature tag lacks new.patch and provenance.txt.
- fail=isabelle_tag: the rerun stops at the empty commit (rc 1); no tags.
- fail=feature_tag: the rerun stops at "release tag R/light/1 already exists"; the Isabelle tag exists and the feature tag does not.
- Fixed order (stage by name, commit if different, verify blob ids, feature tag accepted if its tree matches, Isabelle tag last): the release completes after a rerun for every injected failure (commit, feature tag, Isabelle tag), with no missing files.
- The hook refuses `git tag -f` ("already exists and never changes") but allows `git tag -d` (rc 0), so only migration rule 14 stands in the way of deleting a tag by hand.

(3) Read-only checks.
- `git -C contrib/light_locale ls-files patches` lists 32 tracked `diff -ruN` patch files and no provenance.txt.
- contrib/light_locale/tools has no component_files.txt.
- tools/patched_files.txt lists the same 32 paths.
- light_locale has no tags.

Recommended fix: Edit decision 16 points 7-9 (plan:675-681).

(a) Point 8: after writing the files, stage each generated file by name (`git add -- <file>`). Remove from the index each tracked patches/<R>/*.patch that was not regenerated (`git rm --cached`). Commit with `git commit -- patches/<R>/` only if `git diff --cached --quiet -- patches/<R>/` reports a difference. A rerun with nothing to commit is not an error.

(b) Before any tag, check that the commit's patches/<R>/*.patch and provenance.txt blob ids are exactly the generated ones, and that the shipped and gate files are committed and unchanged.

(c) Create the feature-repository tag next. Accept an existing tag of that name if its tree passes the same check in (b).

(d) Create the Isabelle release tag last, so that its existence means the release is complete. This matches make-patches:20-21 and :209 and migration §7 rule 14. make-patches:86-88's refusal then stays correct, and a rerun after any partial failure finishes the release.

(e) Point 7: add tools/component_files.txt itself to the committed-and-unchanged list. Optionally write "the Isabelle repository's tip of <R>/<feature>" instead of "tip".

(f) Point 9: add toy tests that inject a failure after each of the three writes and check that a rerun completes. Add one test in light's first-release shape: tracked old-format patches rewritten plus a new provenance.txt, then assert the tagged commit holds every file.

(g) §10, row C4: name the reordering as a deviation from the round-3 judge's action (1).

**Judge: confirmed → author_fixes_no_rereview.** Decision 16 points 7-9 (plan:675-681).

(a) Stage each generated file by name, and git rm --cached each tracked patches/<R>/*.patch that was not regenerated. Commit only if `git diff --cached --quiet -- patches/<R>/` reports a difference. A rerun with nothing left to commit is not an error.
(b) Before any tag, verify that the commit's patches/<R>/*.patch and provenance.txt blob ids are exactly the generated ones.
(c) Create the feature-repository tag next. Accept an existing tag of that name whose tree passes the check in (b).
(d) Create the Isabelle release tag last, so that its existence marks the release complete. This matches make-patches:20-21 and :209 and migration §7 rule 14, and make-patches:86-88's refusal stays correct.
(e) Add tools/component_files.txt itself to the committed-and-unchanged list. Optionally write 'the Isabelle repository's tip of <R>/<feature>'.
(f) Toy tests inject a failure after each of the three writes and check that a rerun completes. One more test uses light's first-release shape: tracked old-format patches rewritten plus a new provenance.txt.
(g) Name the reordering in §10's C4 row.

The judge reproduced the silent omission: `git commit -- patches/R/` returns 0 and leaves new files untracked (review-ipc4/judge/c13). Light tracks 32 old-format patch files and no provenance.txt today, so its first release would hit this.

### C14 [minor] check-roundtrip's interface takes feature repository directories, but the CI roundtrip job must test a features.d assembled from the packages it ships; as specified, the gate tests sources rather than shipped bytes

Section: Decision 17; decision 11 roundtrip job  ·  merged from: consistency-CONS4-12, landing-L4

**Statement.** Decision 17 defines `tools/check-roundtrip <原版树> <链顶 feature> [-C ...] <feature 仓库目录...>`, which assembles features.d from each repository's patches/<R>/ (plan:685-686). Decision 11's roundtrip job, following the round-3 judge's C12 action, builds features.d 'from the packages just built' and claims to check the bytes CI ships (plan:530-531, :692). No argument of the script accepts a features.d or a package.
- In CI there are no feature-repository directories.
- Some packages are downloaded rather than built (plan:524).
- isabelle-base-features holds two packages in one repository (plan:583), which does not fit '<feature 仓库目录...>'.
- Locally, the script reads working trees. Those can differ from the tags whose diff copy B applies.
- In CI the tool under test runs from the checkout (plan:687), not from the shipped tool package.

Fix. Make `--features-dir FD` the script's only feature input. Add two thin assemblers: one that builds FD from the feature repositories at their release tags (`git show <tag>:patches/<R>/...`), and one that builds it from the feature packages in the test channel, whether built or downloaded. In CI, run the tool from the installed isabelle-patch-control package.

**Editor.** 

**Relaxation proposed by the editor.** With a single input shape, local runs and CI runs test the same bytes, and (b2) also covers the shipped tool.

**Defender: partially_confirmed** (needs owner: False).

The core defect is real. The plan says the CI roundtrip job checks the bytes CI ships, but the script's interface cannot take those bytes. Two of the five bullets are overstated.

CONFIRMED
1. The script's interface does not match the CI job.
   - Decision 17's only feature input is `<feature 仓库目录…>` (feature repository directories). The script assembles features.d from each one's `patches/<R>/` (plan:685-686).
   - Decision 11's roundtrip job says its features.d is built "由刚构建的包" (from the packages just built) (plan:530-531). Decision 17 itself says the job runs "对 CI 发出的字节" (on the bytes CI ships) (plan:692). That is also the round-3 judge's C12 action (REVIEW3:1810).
   - An extracted feature package has `share/isabelle_patch_control/features.d/<feature>/`, not `patches/<R>/` (plan:26, :500). So the script, as specified, refuses package contents. Experiment (i): REFUSED, rc 3.
   - The roundtrip job is a separate job (plan:530). It has no feature-repository checkouts; only the build job checks them out (plan:525).
   - The only way to fit the interface as written is to pass source checkouts. That tests sources, not shipped bytes, and the gap matters:
     - Experiment (ii): a package set with one patch file dropped passes when the check reads the sources.
     - Experiment (iii): the same set fails when features.d is assembled from the packages ("A != B: new.ML only in B").
     - Nothing else before publication would catch such a packaging defect. The build job's unpack check covers only hooks, line endings and the `share/<包名>` path (plan:526-528). `check_bytes` checks only files that installed patches touch (plan:634-636). §6 (a) installs only light (plan:786).
   - §10's C12 row (plan:889) reports the action as done and names no deviation, so this is an unimplemented piece rather than a named deviation.
2. "刚构建的包" leaves out the packages the build job downloads instead of building (plan:523-524). In the HOL-side example, expose_foreign and future_assign_interrupt are downloaded (plan:547-548). The chain from pristine needs them, so the wording must say: every feature package in the artifact's local channel.
3. The roundtrip job does not test the shipped tool.
   - (b2) runs the tool "从 checkout" (from the checkout) (plan:687). The plan never says which ref the roundtrip job checks out.
   - `tool_ref` defaults to the triggering ref (plan:518). The tool package is built only when that version is unpublished; otherwise it is downloaded (plan:525, :549).
   - So dispatching from main with an already-published version ships the downloaded old tool while (b2) runs main's code.
   - This matters because (b2) is the only full-chain check before publication. qiyuan-dev-patches is installed only in §6 (h), which runs only for a new isabelle build (plan:799), and in the smoke test after publication (plan:537).
   - Running the tool installed from the local channel closes this, as the relaxation says.

OVERSTATED
(a) "isabelle-base-features does not fit."
   - Each subdirectory follows light's layout, with its own `patches/Isabelle2025-2/` (plan:583-586).
   - make-patches calls this the package directory (`--package <dir>`, tools/make-patches:2, :6-7, :267). The renderer also takes "包目录" (plan:504).
   - Passing the two subdirectories works: experiment (iv) passes, and only the repository root is refused.
   - What is left is a terminology slip: decision 17 says "feature 仓库目录" where make-patches and decision 10 say package directory.
(b) "Locally the script reads working trees, which can differ from the tags."
   - True: round-3 S1 showed exactly this (REVIEW3:1762).
   - But in rev 4 the CI roundtrip job, which every publish job depends on (plan:535), is the gate. A local pass cannot let wrong bytes ship.
   - So an assembler that reads the tags locally is optional, not part of the smallest fix. The relaxation's claim that local and CI runs "test the same bytes" holds only with that optional assembler.

THE RELAXATION ON ITS MERITS
- A single `--features-dir FD` input is the right shape. It makes "the CI job tests the shipped bytes" true by construction, and it removes the repository/package-directory terminology from the script.
- The CI assembler need not be custom extraction code. The roundtrip job can:
  - create an environment with `isabelle` and `isabelle-patch-control` from the local channel;
  - copy its pristine `isa/` as the original tree;
  - then install the chain-top feature package into the same environment. Conda's exact pins pull in the whole chain, built or downloaded.
  Then FD is that environment's `share/isabelle_patch_control/features.d` (the bytes exactly as conda links them), and the tool under test is that environment's `isabelle-patch-control`, which is the shipped tool. The post-link patching that environment's own `isa/` does not matter.
- Two small assemblers, one per input source, remain fine; the local one can simply copy `<包目录>/patches/<R>/`.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C14/toy/

Setup:
- setup.sh is round 3's defender-C12 toy:
  - an isabelle-patched-like repository with tags R/pristine/ID0, R/f1/1 and R/f2/1; f2 edits etc/options and src/b.ML and creates src/new.ML;
  - two feature repositories with committed, tagged `patches/R/`;
  - pristine builds `build_n` and `build_n1`.
- b2core.sh is a (b2) prototype with one feature input, a features.d. The tags are derived: bottom = `R/pristine/<etc/ISABELLE_ID>`, top = the top feature's release_tag. Copy A uses isolated `git apply`; copy B uses `patch -p1 -F0` of `diff-tree` bottom..top. It compares with `diff -r` plus sorted `find -printf '%M %p'`, then unapplies A and compares again.
- b2-asspec.sh is decision 17 as written: it takes `<feature 仓库目录…>` and assembles features.d from `<dir>/patches/R/`.
- Real `.conda` packages were built with `~/miniconda3/bin/cph c` from `git archive <tag> patches/R`. They have the decision-10 layout `share/isabelle_patch_control/features.d/<f>/`.
  - chan_good: a correct set.
  - chan_bad: f2's package lacks `src-new.ML.patch`, standing in for any renderer or recipe defect.

Results:
- (i) b2-asspec.sh given the extracted packages: `REFUSED: … has no patches/R/provenance.txt`, rc 3.
- (ii) b2-asspec.sh given the feature-repository checkouts while chan_bad is what ships: `PASS: chain f1 f2`, rc 0.
- (iii) b2core.sh with features.d assembled from the channel:
  - good: PASS;
  - bad: `FAIL: A != B (new.ML only in B)`, rc 1.
- (iv) A two-package repository `basefeat/{f1,f2}/patches/R`:
  - passing the subdirectories: PASS;
  - passing the repository root: REFUSED.
  So that bullet is only a terminology issue.

Read checks:
- plan:518 (`tool_ref` defaults to the triggering ref), :523-525 (downloads; the tool is built only if unpublished), :530-531, :547-550, :583-586, :685-692, :786, :799, :889;
- tools/make-patches:2, :6-7, :267 (`--package <dir>`);
- REVIEW3:1797-1815 (judge's C12 action).

Nothing outside my scratch directory was modified.

Recommended fix: Smallest fix, in decisions 17 and 11:

1. Decision 17's signature becomes `tools/check-roundtrip <原版树> <链顶 feature> [-C <isabelle-patched 仓库>] --features-dir FD [--tool <isabelle-patch-control 命令>]`.
   - FD (a features.d) is the only feature input.
   - Delete "从各 feature 仓库的 patches/<R>/ 拼出".
   - The tool defaults to `python -m isabelle_patch_control` from the checkout, which is the local use.
2. Local use: FD is assembled by copying each package directory's `patches/<R>/` into `FD/<feature>/`. Use the term 包目录 (package directory), as decision 10 and make-patches do. For isabelle-base-features that is each subdirectory.
   - Optional: read `git archive <release tag> patches/<R>` instead of the working tree, so local runs see the tagged bytes.
3. Decision 11's roundtrip job:
   - create an environment with `isabelle 2025.2 <isabelle_build>` and `isabelle-patch-control` from the artifact's local channel, using the same channel list as `accept`;
   - `cp -a` its `isa/` as the original tree;
   - install the chain-top feature package into the same environment. Conda's exact pins pull in the whole chain, built or downloaded.
   - Run the script with `--features-dir $ENV/share/isabelle_patch_control/features.d` and `--tool $ENV/bin/isabelle-patch-control`.
   - Replace "由刚构建的包拼出" with "the features.d of an environment installed from the artifact's local channel (built and downloaded packages alike)".
   - State that the tool under test there is the shipped one.
4. Add one sentence to §10's C12 row naming this.

**Judge: partially_confirmed → author_fixes_no_rereview.** Decision 17's signature becomes `tools/check-roundtrip <原版树> <链顶 feature> [-C <repo>] --features-dir FD [--tool <command>]`. FD is the only feature input; delete '从各 feature 仓库的 patches/<R>/ 拼出'.

Local assembler: copy each package directory's patches/<R>/ into FD/<feature>/. Use the term 包目录, as make-patches:2 and :6-7 and decision 10 do; for isabelle-base-features that means each subdirectory. Reading the release tags with git archive is optional.

Decision 11's roundtrip job:
- create an environment with isabelle 2025.2 <b> and isabelle-patch-control from the artifact's local channel, using accept's channel list;
- cp -a its isa/ as the original tree;
- install the top feature package into the same environment; the exact pins pull in every built or downloaded package of the chain;
- run with FD = $ENV/share/isabelle_patch_control/features.d and --tool $ENV/bin/isabelle-patch-control, so the shipped tool and the shipped bytes are the ones tested.

Record this in §10's C12 row.

Refuted: the isabelle-base-features bullet is only a terminology issue; passing its subdirectories works (review-ipc4/defender-C14/toy).

### C15 [minor] Three acceptance or test items cannot run or cannot fail: check_bytes after (b) and (g), (g)'s win-64 target check, (h)'s trigger, and the 'broken script' crash test

Section: §6 (b), (g), (h), (k); decision 15 check_bytes and hook-layer crash case  ·  merged from: consistency-CONS4-11, landing-L8, conda-conda-8

**Statement.** (1) §6 (k) runs check_bytes after (b) and after (g) (plan:802). Its unapply half compares every file the chain touches with conda-meta/isabelle-*.json's paths_data, and checks that created files are absent (plan:634-636). After (b), features.d/light_locale has left with its package, so the check no longer knows light's targets or the files light created. After (g), `conda remove isabelle` has removed the isabelle record and, on POSIX, isa/ itself. On win-64, (g)'s 'no feature target path exists' (plan:796-797) likewise needs target lists from patch files that are already gone. These items come from the round-3 judge's C20 and C21 actions, but they still cannot run as written.
(2) (h) runs 'only on re-runs for a new isabelle build' (plan:799), but no input or derived value tells the accept job that a run is one (plan:515-520).
(3) Decision 15's 'the tool crashes at start-up (replaced by a broken script)' (plan:654). The hook runs `"$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control` and uses the entry-point script only for the `-x` test (plan:435-436, :455-456). Replacing the script changes nothing the hook executes, so the test passes whether the `||` branch works or not, on win-64 too (review-ipc4/critic-conda/run4.out: 'applied: feat_a' and zero 'could not run' lines). The branch is reached only by a module that fails at import (critic-conda/run2.out, scenario I).

Fix.
- Before each removal, snapshot the installed features' targets and created files (from `status -v` or the patch files) together with the isabelle record's paths_data, and run check_bytes and (g)'s win-64 assertion against that snapshot.
- Let the build job output whether this is a re-run for a new isabelle build: the channel holds builds of the listed (F, v) pinned to another isabelle build, which is the same lookup as C2's function. Run (h) exactly when that output is true.
- Build the 'broken tool' as a package whose isabelle_patch_control module raises at import, and add a separate win-64 case with python.exe missing.

**Editor.** 

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute each of the three parts. All three survive. The only correction is to part (1): the reference data is gone from the environment, but it is not lost, so the fix should read it from the package archives instead of taking a snapshot.

(1) check_bytes after (b) and (g), and (g)'s win-64 target list.
- What check_bytes is. It is defined by what it compares, but its inputs are never named (plan:634-636). After an apply, each touched file's git blob id must match the post-image `index` id of the highest patch that touches it. After an unapply, each touched file must have the sha256 recorded in `conda-meta/isabelle-*.json` paths_data, and every created file must be absent. §6 (k) runs it after (a), after (b) and after (g) (plan:802).
- After (g) it cannot run as written. `conda remove isabelle` removes the isabelle record, the feature packages that depend on it, their features.d entries, and on POSIX the whole isa/ directory. critic-conda/run2.out scenario H shows this: features.d=[], no isa/, and the env's conda-meta (run2.HQjm/envs/G/conda-meta) holds no isabelle-*.json and no feature records.
- The unapply half's expected values are also wrong at (g). Every tracked file should now be absent, not equal to a recorded sha256. conda deletes tracked paths whatever their content (round-3 C21 defender, path_actions.py:1156-1164).
- The round-3 C21 judge also ruled for (g): 'do not use the paths_data comparison' (REVIEW3 C21 judge). Running a paths_data-based check_bytes after (g) contradicts that ruling. The plan's §10 rows C20 and C21 (plan:897-898) do not mention the clash. It goes back to the C20 judge's own wording, '(a), (b) and (g)'.
- At (g), the only checkable remainder is 'created paths are absent'. (g)'s own assertions already say this (plan:796-797), so check_bytes after (g) adds nothing.
- After (b), light's features.d has left with its package. The natural implementation, check_bytes(tree, features.d) (the round-3 C20 defender's signature), would then not check light's 32 files at all. It would pass whether or not light was reversed cleanly. (b)'s own 'light 反打干净、新建文件消失' (plan:789) needs the same missing list.
- Partial refutation. The data survives in the conda package cache (pkgs/) and in the local-channel artifact that the accept job downloaded. critic-conda/pkgs-shared still holds isabelle-2025.2-1/info/paths.json with per-path sha256, and the feature's share/isabelle_patch_control/features.d/feat_a/*.patch and provenance.txt, after scenario H removed everything from the env. So the defect is an unnamed input and an ill-defined (g) check, not an impossibility. Reading from the archives needs no state. A snapshot has to be taken at the right moment.

(2) (h)'s trigger. The workflow inputs are isabelle_build, isabelle_from, tool_ref, features, session_build_legs and publish (plan:515-519). None says 'this is a re-run for a new isabelle build', and no job output says it either (plan:522-538). §5 steps 7 and 8 (plan:776-779) rely on (h) being skipped, which nothing decides.
The build job already reads the online noarch/repodata.json to derive build numbers (plan:523-525). So the condition can be derived: some listed (F, v) is already on the channel pinned to an isabelle build other than isabelle_build. At steps 7 and 8 this is automatically false.

(3) The 'broken script' crash test. rev 3's hook executed the entry-point script (rev3:366, `"$PREFIX/bin/isabelle-patch-control" conda-hook post-link || ...`). The test 'tool crashes at start-up (replaced by a broken script)' was written for that hook (rev3:509). rev 4 switched the hook to `"$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control` and keeps the entry point only for the `-x` / `if not exist` test (plan:435-436, :445-446, :455-456). It carried the test text over word for word (plan:654). The same applies to the pre-unlink case 'the tool cannot start' (plan:652).
Whether the test can fail now depends on how the 'broken tool' package (plan:639) is built:
- with the real module and a broken entry point, the `||` branch is never reached (critic-conda/run4.out: 'applied: feat_a', 0 'could not run');
- with a module that raises at import, the branch is reached (critic-conda/run2.out scenario I: 3 'could not run' lines, history kept).
A test that passes or fails depending on an unstated build detail is a defect. A separate case with python missing is optional: in the .bat a missing python.exe sets errorlevel 9009, which goes down the same `if errorlevel 1` line.

Severity minor is right. These are test and wording fixes inside ruling 17's delegation. There is no editor relaxation to weigh.

Outside C15: the C20 judge also asked for check_bytes in the pytest hostile case and in the hook-layer tests. The plan's hostile case is still only relative (plan:627-629), the hook-layer list never names check_bytes, and §10 row C20 does not say so.

Experiment: No new experiment. /tmp (tmpfs, 24G) was 100% full (`df -h /tmp`: 4.0K free), so I could not write to /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C15/. I did not delete anything belonging to other agents.

I re-read existing artifacts from earlier runs:
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/run2.out
  - scenario H, `conda remove isabelle`: isa/ is gone, features.d is empty, and the tool is pruned with the rest;
  - scenario I, a module that raises ImportError at import: 3 'the hook could not run' lines, exit 0, history kept.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/run2.HQjm/envs/G/conda-meta: after scenario H it holds no isabelle-*.json and no feature records.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/pkgs-shared/isabelle-2025.2-1/info/paths.json: still carries per-path sha256 (for example isa/etc/ISABELLE_ID 3ad1068464ff) after the removal.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/pkgs-shared/isabelle-feat-a-1-Isabelle2025_2_0/share/isabelle_patch_control/features.d/feat_a/ still holds src-a.ML.patch and provenance.txt.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/run4.sh and run4.out: the real module with only the entry point replaced gives 'applied: feat_a' and 0 'could not run' lines.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/critic-conda/src/mkchan4.py:79-81 and src/crash.py: how the crash_0 package was built.

Texts compared:
- plan:435-456, :515-538, :634-654, :776-802, :897-898;
- ISABELLE_PATCH_CONTROL_PLAN.rev3.md:360-372 (the hook ran the entry point) and :509 (the same test text);
- REVIEW3 C20 judge action ('(a), (b) and (g)', paths_data) and C21 judge action ('(g): do not use the paths_data comparison'; '(h) only on re-runs for a new isabelle_build').

Recommended fix: Smallest fix: three text edits plus §10 lines.

(1) Decision 15's check_bytes (plan:634-636) and §6 (k) (plan:802):
- Name check_bytes' inputs. It reads its reference data from the package archives of the packages the scenario installed: the patch files, the isabelle package's info/paths.json and its original file bytes. Take them from the conda package cache or the local-channel artifact, never from the environment's features.d or conda-meta, which removals delete. The caller states which features are expected to be applied.
- Run it after (a) and after each case of (b), including the three pruning cases.
- Drop '(g)' from (k). At (g) the expected state is absence, and (g)'s own assertions already check exactly that (POSIX `test ! -e "$PREFIX/isa"`; win-64 checks). Take win-64's target list from the same archived patch files.
- Add one line to §10 row C20: this departs from the C20 judge's '(a), (b) and (g)', because the C21 judge ruled out the paths_data comparison at (g).

(2) Decision 11 (plan:522-525) and §6 (h) (plan:799):
- The build job emits an output, for example `isabelle_rebuild`. It is true when the online repodata already holds a build of some listed (F, v) pinned to an isabelle build other than `isabelle_build`.
- The accept job runs (h) exactly when that output is true. At §5 steps 7 and 8 it comes out false by itself.

(3) Decision 15 (plan:639, :652, :654):
- Define the 'broken tool' package as a noarch python package that declares the same entry point, so `-x` and `if not exist ...exe` still pass, and whose `isabelle_patch_control/__init__.py` raises at import (the critic-conda crash_0 shape).
- Use it both for 'the tool crashes at start-up' and for the pre-unlink 'the tool cannot start' case, on linux-64 and win-64.
- Delete '替换成坏脚本'.
- A separate win-64 case with python.exe missing is optional: it goes down the same `if errorlevel 1` branch.

**Judge: confirmed → author_fixes_no_rereview.** Decision 15 check_bytes (plan:634-636) and §6 (k) (plan:802):
- Name the inputs. Reference data comes from the archives of the packages the scenario installed: the patch files and the isabelle package's info/paths.json. Take them from the package cache or the local-channel artifact, never from the environment's features.d or conda-meta, which removals delete (review-ipc4/critic-conda/pkgs-shared). The caller states which features are expected to be applied.
- Run it after (a) and after each case of (b), including the three pruning cases.
- Drop (g) from (k). At (g) the expected state is absence, which (g)'s own assertions already check, and the C21 judge ruled out the paths_data comparison there. Take win-64's target list from the same archived patch files. Name this departure from the C20 judge's '(a), (b) and (g)' in §10.
- Add check_bytes to the pytest hostile case (plan:627-629) and to the hook-layer tests, as the C20 judge required (REVIEW3:2670), or name the deviation in §10's C20 row. Rev 4 drops it silently.

Decision 11: the build job outputs isabelle_rebuild. It is true when the live repodata holds a build of some listed (F, v) pinned to an isabelle build other than isabelle_build (the same lookup as C2's function). §6 (h) runs exactly when that output is true.

Decision 15 (plan:639, :652, :654): define the 'broken tool' package as a module that raises at import while declaring the same entry point (the critic-conda crash_0 shape). Use it for 'the tool crashes at start-up' and for the pre-unlink 'the tool cannot start' case, on linux-64 and win-64. Delete '替换成坏脚本'.

### C16 [minor] The recovery after a Ctrl-C'd conda install: status cannot print the hint when the tool itself was rolled back, the give-up branch leaves created files and the staging directory behind forever, the touch step reads as optional, and a stale component line remains

Section: §4 interrupted conda install; decision 5; README list; Appendix A  ·  merged from: user-U9

**Statement.** §4's recovery after an interrupted `conda install` (plan:754-756; Appendix A plan:940-942) has four gaps.
(1) status prints the hint when conda-meta exists and conda-meta/history does not (plan:754). But when the interrupted transaction is the first feature install, the tool itself is rolled back. $PREFIX/bin then holds only python, nothing can print the hint, and the user sees only conda's DirectoryNotACondaEnvironmentError (review-ipc4/critic-user/run3.out case i1).
(2) The give-up branch, `--force-reinstall isabelle`, restores only the tracked files. The files the features created stay, and so does $PREFIX/isa.staging with a patched copy in it. Nothing removes them later, because the tool and features.d are gone, and they survive `conda remove isabelle` (critic-user/run4.out case i4: isa/src/new.ML remains after `conda remove isa rpc`).
(3) The give-up branch also needs the `touch` step first; without it, conda refuses with DirectoryNotACondaEnvironmentError. Yet the sentence reads as an alternative to the whole sequence.
(4) A registration line for the rolled-back share/ directory stays in the user directory's etc/components (run3.out case i1). Every isabelle command then prints '### Missing Isabelle component' (Isabelle2025-2/lib/scripts/getfunctions:262) until the user recovers.
The Windows form of `touch` is covered in C7.

Fix. Replace the give-up branch with 'recover with the keep branch, then `conda remove <the feature package>`'. The keep branch converges (run3.out case i2, run7.out), and the removal then reverses the created files and cleans the staging directory by construction. Say that only the README carries the hint when the tool itself was rolled back, and mention the 'Missing Isabelle component' warning, which the recovery clears.

**Editor.** 

**Relaxation proposed by the editor.** One recovery path replaces two. The tool, not the user, cleans up what it created.

**Defender: confirmed** (needs owner: False).

I could not refute any of the four parts. One sub-claim needs narrowing: the leftover staging directory depends on how the tool is implemented.

Where the text comes from. Rev 4's recovery (plan:754-756; Appendix A plan:940-942) copies the round-3 judge's C11 action almost word for word, including "To give the feature up instead: --force-reinstall isabelle" (REVIEW3:1677). That is why §10's C11 row (plan:888) names no deviation. But the round-3 toy changed only an existing file, f.ML, and created none (review-ipc3/critic-landing/rollback2/run.sh:10). The gap with feature-created files was never measured, so this is a new defect in text the judge prescribed, not a deviation the plan hid.

(1) Confirmed. When the interrupted transaction is the first feature install, the tool came in with that transaction. conda's rollback reverses every action group of the transaction (link.py:1038-1045), entry points included. After my run1 'move' case the prefix holds bin, conda-meta, etc, isa, isa.staging and share; the tool's lib/ is gone. critic-user/run3.out i1 shows only bin/python left. So `status` cannot run, and the feature package's share/doc README is gone too. The only hint the user sees is conda's own DirectoryNotACondaEnvironmentError, which points to `conda create` (run3.out i1). plan:754 says "README 与 status … 打印" without this limit. The first install is the common case, because one `conda create … isabelle-light-locale` pulls in the tool.

(2) Partly confirmed: the feature-created files are left behind; the staging directory may be.
- Created files: `touch` plus `--force-reinstall isabelle` restores only the files conda tracks. The feature's created files stay. Nothing removes them later, because unapply deletes a created file only while its feature directory exists (decision 6, plan:387-389), and that directory was rolled back. My run1 'hookfc' case left isa/src/new.ML after the give-up branch and after `conda remove isa rpc` (so did critic-user/run4.out i4). The plan has no list of these files to hand the user. Its residue block can say "delete the created files listed above" (plan:748-750) only because it prints the list while features.d still exists.
- A stale created file is not harmless. If a later version of the feature creates that file with different content, the file matches no level, so decision 6 (plan:387-388) puts that feature in CONFLICT.
- Staging directory: my run1 'move' case left isa.staging/src/a.ML forever after the give-up branch, but that toy deletes nothing on interrupt. plan:360 only says "结束时删掉". A real tool that cleans up in a `finally` would remove it on SIGINT, though not on SIGTERM, a second SIGINT or a kill. So this part depends on the implementation, not on the design.
- The give-up branch is also the only recovery the plan never tests: decision 15's SIGINT case checks the keep branch only (plan:655-656).

(3) Confirmed. Without `touch`, `conda install --force-reinstall isa` fails with DirectoryNotACondaEnvironmentError (run3.out i1). Both texts read as if the give-up branch replaces the whole sequence. In §4, "若不想要那个 feature：…" comes after a semicolon that closes the touch-then-install sequence. In Appendix A, "touch 后重装…，或 --force-reinstall isabelle" sets it against the whole sequence. (`conda create -p $PREFIX <pkgs>` works without touch, run7.out i5, so only the `conda install` forms need it.)

(4) Confirmed, and it is the likely outcome when Ctrl-C hits the long post-link.
- conda catches the CondaSignalInterrupt and reverses only the interrupted package at once (link.py:1115-1126). It then keeps running the later post-links (link.py:963-967) and only afterwards rolls back the whole transaction.
- So when the interrupt hits a lower feature's post-link (the first post-link applies the whole chain, so it runs longest), the top feature's `components -u` line still runs. Then the rollback deletes share/<pkg>.
- My run1 'move' case: etc/components lists share/fc after the rollback. Isabelle reads that catalogue on every command (getsettings:90) and prints '### Missing Isabelle component' for each missing directory (getfunctions:262).
- Both recoveries clear it. With keep-then-remove, fc's pre-unlink unregisters it; with the give-up branch, the user directory is deleted.

Aside, not part of C16. In the same 'move' timing, my toy follows decision 3's strict chain, and the later post-links each printed 'feature chain broken … Update the named package' twice, just before 'Rolling back transaction'. This is advice that is wrong in this situation, and round 3 had left it unmeasured (REVIEW3:1590). The README's interrupted-install paragraph could say so in one sentence.

The editor's relaxation holds up.
- What it means: in place of the give-up branch, the user runs the keep branch (touch, reinstall what they want to keep plus the interrupted package) and then `conda remove <the feature package>`.
- Measured in both interruption timings (run1): the tree ends pristine, with no created file, no isa.staging and no stale component line, and a later `conda remove isa rpc` leaves no isa/ at all.
- Why it works: the keep branch's first post-link clears the staging directory "在锁内开始时" (plan:360). The pre-unlink deletes created files (plan:389) and unregisters the component.
- It is the same shape the plan already uses for lock-busy and tool-failure residue: `conda install <包>; conda remove <包>` (plan:484-485, :750).
- It also avoids what `--force-reinstall isabelle` costs: it deletes the user directory with its heaps (plan:481-482).
- One recovery path replaces two, and nothing has to be remembered.

Experiment: My scratch directory is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C16/. I copied critic-user's toy channel generator mkchan4b.py and lib.sh there, with paths adjusted. The toy follows decisions 3, 5, 6, 7 and 9: a strict tag chain fa<fb<fc, fc creates src/new.ML and carries a component, and rpc is an Isabelle_RPC-like component. The runs use real conda 25.11.1 with a private HOME, CONDARC and CONDA_PKGS_DIRS.

run1.sh writes run1.out. In each case an env holds isa and rpc, `conda install fc` runs, and SIGINT goes to conda's process group. There are two timings:
- 'move': the signal arrives inside fa's tool, between git apply and os.replace. Later post-links print 'feature chain broken' twice, and etc/components keeps share/fc after the rollback.
- 'hookfc': the signal arrives in fc's post-link, after fa's post-link has applied the whole chain, so new.ML is present.

For each timing I tried two recoveries:
- Keep-then-remove (touch; conda install isa rpc fc; conda remove fc). Tree pristine, new.ML absent, no isa.staging, components lists only rpc, and `conda remove isa rpc` leaves no isa/.
- The give-up branch as written (touch; conda install --force-reinstall isa). 'move' leaves isa.staging/src/a.ML after `conda remove isa rpc`; 'hookfc' leaves isa/src/new.ML.

I re-read critic-user/run3.out: in i1 the tool was rolled back, bin holds only python, and --force-reinstall without touch fails with DirectoryNotACondaEnvironmentError. I also re-read run4.out i4 and run7.out i5 (conda create -p works without touch).

Sources read:
- conda: link.py:900-1060, :1103-1126, :1600-1712; conda/__init__.py:153-163;
- Isabelle2025-2: lib/scripts/getsettings:90 and getfunctions:245-281;
- REVIEW3 C11 (:1568-1690), where the give-up branch originates;
- critic-landing/rollback2/run.sh (the round-3 toy had no created file).

Recommended fix: These are wording and test changes, which ruling 17 delegates to the author. Because they replace part of the round-3 judge's C11 action (REVIEW3:1677), the plan's own rule requires naming the change in §10's C11 row.

1. §4 (plan:754-756): replace "若不想要那个 feature：`conda install --force-reinstall isabelle`" with "若不想要那个 feature：照上面做完，再 `conda remove <那个 feature 包>`（pre-unlink 把它的改动反打、删掉它新建的文件和组件登记）".
   Add two sentences:
   - When the interrupted transaction installed the tool itself (the first feature install), `status` was rolled back too. Only the README carries this hint; conda itself reports DirectoryNotACondaEnvironmentError.
   - Until the recovery, every isabelle command may print `### Missing Isabelle component: …/share/<包名>`, and the recovery clears it. Optionally add: any 'feature chain broken' lines printed just before 'Rolling back transaction' come from the interruption.

2. Appendix A (plan:940-942): "恢复是 touch conda-meta/history 后重装要保留的包与被中断的包；不想要该 feature 就接着 conda remove 它。"

3. Decision 15's SIGINT case (plan:655-656): add the give-up variant. After keep-then-remove, assert:
   - the feature's created file is absent;
   - there is no isa.staging;
   - etc/components does not list the package.

4. Optional, for robustness: decision 5 (plan:360) says that the tool removes the staging directory in a `finally` as well.

**Judge: confirmed → author_fixes_no_rereview.** §4 (plan:754-756) and Appendix A (plan:940-942): replace the give-up branch (`--force-reinstall isabelle`) with 'do the keep recovery, then conda remove <the feature package>'. Measured to converge with no created file, no isa.staging and no stale component line (review-ipc4/defender-C16/run1.out).

Add two sentences:
- When the interrupted transaction installed the tool itself, status is gone too. Only the README carries the hint, and conda reports DirectoryNotACondaEnvironmentError.
- Until the recovery, every isabelle command may print '### Missing Isabelle component' (Isabelle2025-2 lib/scripts/getfunctions:262), and the recovery clears it.

Decision 15's SIGINT case (plan:655-656) adds this variant, asserting that the created file is absent, there is no isa.staging, and etc/components does not list the package. Optionally, decision 5 removes the staging directory in a finally block.

Name the change to the round-3 judge's C11 text (REVIEW3:1677) in §10's C11 row.

### C17 [minor] The documented update command, a bare `conda update --all`, does nothing for users who installed the way the channel banner says; the README list gives no install command and omits that naming only the feature prunes Isabelle on removal

Section: Decision 14 README list; §4 not-pristine text; decision 3 point 2; ruling 22's paraphrase  ·  merged from: user-U3

**Statement.** The README list and the 'tree is not the pristine build' text tell users to update with a bare `conda update --all` (plan:604, :730; ruling 22, plan:92). conda searches only the channels in its configuration and the channels named on the command line, never the channel an installed package came from (conda_libmamba_solver/state.py:380-393, solver.py:217-236). The channel banner tells users to name the channel on the command line (channel-banner.html:6 and :10: `conda create -n ... -c https://conda.qiyuan.me -c conda-forge isabelle-ai` and `conda update -c https://conda.qiyuan.me -c conda-forge isabelle-ai`), which does not save it to .condarc. For those users, `conda update --all` answers 'All requested packages already installed' and never moves isabelle or the feature packages to a new build (review-ipc4/critic-user/run6b.out:9-11). With the channel named, the same command does move (run6.out).

The README list also gives no install command. A user who names only the feature package (`conda create ... isabelle-light-locale`) has isabelle only as a dependency, so a later `conda remove isabelle-light-locale` removes Isabelle as well (critic-user/run1.out case d3). The list's pruning sentence names only lower packages and the tool (plan:603).

Fix. Spell out the commands in the unified text and in §4. Install: `conda create -n <env> -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale`, with one sentence on why isabelle is named explicitly. Update: `conda update --all -c https://conda.qiyuan.me -c conda-forge`, or add the channel to .condarc once. This keeps ruling 22's `--all`.

**Editor.** U3's 'major' is too high. No tree becomes wrong: the exact pins keep the old set consistent, so the user simply does not receive updates. This is a documentation fix.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I could not refute any part of C17. Its severity, minor, is right.

1. The plan really gives a bare update command. The README list says "更新命令是 `conda update --all`" (plan:604). The §4 not-pristine text ends "Run: conda update --all" (plan:730). Decision 3 point 2 repeats it (plan:327), and the tests assert that the message contains this string (plan:617, :800). Nowhere does the plan give a user-facing command with the channel URL: grep for conda.qiyuan.me finds only the CI jobs at plan:533 and :537.

2. conda really ignores where an installed package came from. In conda 25.11.1 the channel list is the configured channels (`channel_urls: context.channels`, conda/cli/install.py:183,186). The libmamba solver adds only `self.channels`, plus `channel::pkg` specs from the current command, plus the free channel (conda_libmamba_solver/solver.py:217-237, state.py:380-403). state.py:383-385 even says that history channels are not kept. No function anywhere collects channels from installed packages.

3. The channel's own convention is to name the channels on the command line. The banner does it for install (channel-banner.html:6) and for update (:10). Neither writes them into .condarc. No package ships a .condarc either: I checked the paths.json of the cached isabelle-2025.2-0, isabelle-ai and isabelle-rpc packages, and grepped the recipes.

4. I reproduced the behaviour independently with my own toy channel (defender-C17/run1.out). A banner-style `create -c <chan> isabelle isabelle-light-locale` with condarc channels [forge] got build 1. After build 2 and the re-released light were published, a bare `conda update --all` answered "# All requested packages already installed", both with `-p` and with the environment activated. The set stayed unchanged and consistent. With `-c <chan>` added, the same command moved isabelle 2025.2-1→2 and light Isabelle2025_2_0→_1 (case 3).

5. Naming only the feature does prune Isabelle on removal. With `create -c <chan> isabelle-light-locale` alone, a later `conda remove isabelle-light-locale` removed isabelle-2025.2-2 and the tool too (run1.out case 5; it matches critic-user/run1.out d3). Because isabelle's pre-unlink deletes the user directory (plan:200), that removal also deletes it. The pruning sentence lists only "下层包与工具" (lower packages and the tool; plan:603). The plan's own tests always request isabelle explicitly (plan:537, :650, :785-786), but no install command tells users to do so.

6. This is not a re-raise of round 3. Round-3 C26 item (3) was a different point: the banner's `conda update ... isabelle-ai` does not move isabelle. It was judged optional. No round-3 experiment ran a bare command, because every toy helper passed `--override-channels -c file://...`.

7. On the editor's relaxation: I agree. Nothing becomes inconsistent, and users just stop getting updates. The one silent-failure spot that matters is the §4 not-pristine remedy (plan:730): a stuck user follows it and nothing happens, with no error. That state is only reachable outside the solver (for example `--no-deps`, or §6 (i)'s hand-placed feature directory). Documentation fix, minor.

8. The same omission appears outside C17's statement, so the fix should cover it too. These bare commands are: the hook fragment's `conda install isabelle-patch-control` and `conda install --force-reinstall isabelle-patch-control` (plan:437, :439, :447, :451); the pre-unlink and residue recovery `conda install <包名>` (plan:460, :750); and the release note `conda install isabelle-expose-foreign` (plan:576). These fail loudly rather than silently: after `remove --force`, `conda install isabelle-patch-control` without the channel gave PackagesNotFoundError (run1.out case 4b). But the hook fragment is copied verbatim and byte-checked into every package (plan:432, :527-528). Fixing it after the first publish therefore means re-releasing everything.

9. The challenge's ".condarc once" alternative works only in some forms. An env-level `$PREFIX/.condarc` or `$PREFIX/condarc.d/*.yml` is honoured with `-p` and when the environment is activated. It is not honoured with `-n` (run4.out; conda/base/context.py:557 is where conda fills `$CONDA_PREFIX` in the config search path). A global `conda config --add channels` works everywhere. So spelling out the `-c` flags is the robust form.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C17/.

Setup:
- Generator: src/mkchan.py, my own. Stage 1 has isabelle 2025.2 build 1, the tool 1.0.0, and isabelle-light-locale 1 Isabelle2025_2_0 pinned to `isabelle 2025.2 1`. Stage 2 adds isabelle build 2 and light Isabelle2025_2_1 pinned to build 2.
- Isolation: conda 25.11.1 (libmamba) with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS.
- The condarc lists only an empty stand-in channel "forge" (in place of conda-forge) and sets default_channels: [].

src/run1.sh, output in run1.out:
- Banner-style install, with the channel only on the create command line.
- Case 1/1b: a bare `conda update --all`, with `-p E` and activated, gives "All requested packages already installed", and the set stays at build 1.
- Case 2: an env-level .condarc listing the channel makes it update.
- Case 3: `conda update -p E --all -c <chan>` updates isabelle 1→2 and light _0→_1.
- Case 4b: `conda install isabelle-patch-control` after `remove --force`, without the channel, fails with PackagesNotFoundError.
- Case 5: `create -c <chan> isabelle-light-locale`, then `conda remove isabelle-light-locale`, also removes isabelle and the tool.

src/run3.sh and src/run4.sh, outputs in run3.out and run4.out:
- An env-level `condarc.d/*.yml` or `.condarc` is honoured with `-p` and when activated, but not with `-n`.

src/run2.sh is inconclusive: an `echo >` wrote through the hard link into the package cache, which is the round-3 C27 effect, and it is not used as evidence.

Sources read: plan in full; channel-banner.html:1-11; conda/cli/install.py:183-186; conda/base/constants.py:54-72; conda/base/context.py:550-560; conda/cli/main_config.py:116-121,823-825; conda_libmamba_solver/solver.py:217-237 and state.py:380-403; REVIEW3 C26 (:3200-3300).

Recommended fix: These are wording edits within ruling 17. They keep ruling 22's and ruling 29's `--all`.

1. Decision 14's unified text (plan:602-606) gains two commands:
   - Install: `conda create -n <env> -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale` (or `conda install -c … isabelle <feature>` into an existing environment). Add one sentence on why isabelle is named: otherwise removing the feature also removes Isabelle and its user directory.
   - Update: `conda update --all -c https://conda.qiyuan.me -c conda-forge`. Note that this works without the flags only if both channels are in the user's global .condarc (`conda config --add channels …`). An env-level .condarc is not honoured by `-n`.
   - Also widen the pruning parenthetical at plan:603 to include isabelle when it was not requested.
2. §4's not-pristine text (plan:730) and decision 3 (plan:327) become "Run: conda update --all -c https://conda.qiyuan.me -c conda-forge". The tests at plan:617 and :800 still match.
3. Before the first publish, add the same `-c https://conda.qiyuan.me -c conda-forge` to every other user-facing conda command. These are the hook fragment (plan:437, :439, :447, :451), the pre-unlink line (plan:460), the residue block (plan:750) and the release note (plan:576). The hook fragment is copied verbatim into every package, so fixing it later means a full re-release.
4. Optional, for elegance: write the channel flags once in the unified text, and have the smoke job (plan:537) run the README's install command verbatim, so the documented command is the tested one.
5. Record the change in §10 as an addition, not a deviation from ruling 22.

**Judge: confirmed → author_fixes_no_rereview.** Decision 14's unified text (plan:602-606) spells out two commands:
- install: `conda create -n <env> -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale`, with one sentence on why isabelle is named: otherwise removing the feature also removes Isabelle and its user directory (critic-user/run1.out d3);
- update: `conda update --all -c https://conda.qiyuan.me -c conda-forge`. Without the flags this works only if both channels are in the global .condarc; an environment-level .condarc is not honoured with -n (review-ipc4/defender-C17/run4.out).

Widen the pruning sentence at plan:603 to include isabelle when it was not requested.

§4 (plan:730) and decision 3 (plan:327) use the full update command. The tests at plan:617 and :800 still match.

Before the first publish, add the same channel flags to every other user-facing conda command: the hook fragment (plan:437, :439, :447, :451), the pre-unlink line (plan:460), the residue block (plan:750) and the release note (plan:576).

Optionally, the smoke job runs the README's install command verbatim. Record this in §10 as an addition, not a change to ruling 22.

### C18 [minor] Where git runs is listed incompletely, and the lock-less level computation of a pre-unlink after a lock timeout has no stated directory, so by decision 5 it would use the staging directory, which round 3 restricted to lock holders; --dry-run's lock mode is unstated

Section: Glossary (plan:31-32); decision 4 (plan:338); decision 5 (plan:359-362, :369-370); decision 9 (plan:480); §10 row C2  ·  merged from: engine-engine-3

**Statement.** The glossary (plan:32) and decision 4 (plan:338) say git runs only in the staging directory or the temporary directory, and they define the temporary directory as the tempfile.mkdtemp() that status and --dry-run use. Decision 5 adds a third place: the directory interface's per-run mkdtemp beside realpath(<dir>) (plan:361-362). The round-3 judge's wording was 'a directory the tool created' (REVIEW3:3677-3686), and §10 does not say that the list was narrowed.

More importantly, decision 9 says that after a lock timeout a pre-unlink computes levels without holding the lock (plan:480), but not where. conda-hook is a writing command, and decision 5 has writing commands replay in the staging directory, which is emptied at the start, inside the lock (plan:359-360). Round 3 ruled that the staging directory is used only under the lock, because an unlocked user of it deletes a locked run's copies (REVIEW3 C19; review-ipc3/defender-C19/race). A lock holder, for example a manual `apply` running during conda's pre-unlink, would lose its staging copies mid-run. Decision 5's lock modes (plan:369-370) also name status, apply, unapply and conda-hook, but not `apply --dry-run` or `unapply --dry-run`.

Fix. State one rule in decision 5 and in the glossary. A run that holds the exclusive lock replays in the staging directory. Every other replay replays in a fresh tempfile.mkdtemp(): that covers status, every --dry-run (read-only open, LOCK_SH), and a pre-unlink's level computation after a lock timeout. The directory interface replays in a mkdtemp beside realpath(<dir>). The glossary lists all three, and decision 4 says 'a directory the tool created'.

**Editor.** 

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of C18's three parts. The main part holds: the plan never says where a pre-unlink computes levels after its lock wait times out, and its own rule for choosing a directory points that computation at the staging directory. The --dry-run part also holds. The "third place" part is mostly refuted: what is left of it is a glossary entry worded too narrowly, not an unstated narrowing of the rule.

1. Where the lock-free level computation runs. CONFIRMED, and the effect is worse than C18 says.
- Decision 9 says: "锁超时时层级在不持锁的情况下算" (after a lock timeout, the levels are computed without holding the lock, plan:480). It does not say in which directory. No other line mentions this path (grep of 不持锁 and 锁超时: plan:478, :480, :484 only).
- Decision 5 chooses the directory by command name. The writing commands "apply、unapply、conda-hook" replay in the staging directory, which is "在锁内开始时清空、结束时删掉" (cleared at the start inside the lock, deleted at the end, plan:359-360). Only "status 和 --dry-run" use a temporary directory (plan:361). conda-hook pre-unlink is conda-hook, so the literal rule sends its lock-free computation to the staging directory. Done there, the computation either clears the directory without the lock or works next to another run's copies.
- The round-3 judge ordered "staging = realpath(tree) + '.staging', used only under the lock" (REVIEW3:2577). Rev 4 keeps only the clear-and-delete clause (plan:360), never states "used only under the lock" as a rule, and §10's C19 row (plan:896) does not mention it. The C23 action that created the lock-free path (REVIEW3:2945, :2968) did not name a directory either. Combined, the two actions leave the gap that rev 4 now has.
- Experiment (race.py, git 2.43.0, the decision 4 whitelist environment, a two-feature chain x→y→z). A lock holder (apply, target 2) has replayed in <realpath(tree)>.staging and is suspended just before os.replace. A pre-unlink then times out on LOCK_EX and computes levels without the lock:
  (a) It uses the staging directory as decision 5 says (clear, replay, delete). The holder's os.replace fails with FileNotFoundError. This is round 3's race again.
  (b) It is in the middle of replaying in the staging directory with the same copy layout. The holder installs 'y' (level 1) while it believes it installed 'z' (level 2): the wrong level, installed silently.
  (c) It uses a fresh mkdtemp. The holder installs 'z' correctly.
- How often this can happen: the lock is shared across environments through the package-cache inode (plan:373). The collision needs a holder on the same tree, for example a suspended manual apply in the same environment. That is rare, but the plan designs and tests this path itself (plan:652). Severity minor stands.

2. The --dry-run lock mode. CONFIRMED.
- plan:369-370 gives the lock mode by command: status opens read-only with LOCK_SH; "apply、unapply、conda-hook" open read-write with LOCK_EX. `apply --dry-run` and `unapply --dry-run` are apply and unapply commands, so read literally they open read-write. The plan names no lock mode for --dry-run anywhere, even though plan:361 groups --dry-run with status as writing nothing.
- Experiment (rotree.py, uid 1002, a read-only etc/ISABELLE_ID): opening read-only with LOCK_SH works; opening read-write fails with PermissionError. So, read literally, `apply --dry-run` fails on exactly the read-only tree where the plan tests that status works (plan:631).

3. "Decision 5 adds a third place; the list was narrowed silently." MOSTLY REFUTED.
- The plan already uses the general phrase "工具自己建的目录" (a directory the tool itself created) at plan:103, plan:153 and decision 4 (plan:338). The part of C18's fix that says "decision 4 says 'a directory the tool created'" is therefore already in the text.
- Decision 8 calls the directory interface's directory "per-run 临时目录" (plan:424), and §10's C19 row says "目录接口的临时目录" (plan:896). The plan treats it as a temporary directory created with mkdtemp(dir=…), not as a new kind of place, and §10 records it.
- The two-item list in the glossary matches the judge's own parenthesis "(staging for writing commands, a temporary directory for status and --dry-run)" (REVIEW3:3684).
- What remains: the glossary defines the temporary directory by who uses it, "status 和 --dry-run 重放用的" (plan:32). That definition leaves out the directory interface (plan:424) and decision 3's reading of targets "在一个临时目录里", which every command does (plan:330). This is a wording gap under the rule of one term per concept, not a deviation.

4. On C18's fix. Tying the choice of directory to the lock mode (only an exclusive-lock holder uses the staging directory; every other replay uses a fresh mkdtemp) is the right shape. It makes "only the lock holder touches the staging directory" true by construction instead of something each new code path must remember, which is the elegance criterion. It changes no ruling: ruling 24 is about the bytes that get installed, and neither the lock-free computation nor --dry-run installs anything.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C18/. git 2.43.0, Python 3 run with -I.

(1) race.py, output in race.out. A toy tree has etc/ISABELLE_ID and src/a.ML ("x"), with features f1 (x→y) and f2 (y→z). The `_git` wrapper builds decision 4's whitelist environment, including GIT_CEILING_DIRECTORIES and the fixed `-c` options. Process H takes LOCK_EX, clears <realpath(tree)>.staging, replays f1 and f2 on a copy under staging/up/, then is "suspended" before os.replace. U attempts LOCK_EX|LOCK_NB, which stands in for the 60 s timeout, and computes levels without the lock. Results:
- staging-clear (decision 5 literally: clear, replay, delete): H's os.replace fails with FileNotFoundError and the tree stays 'x'.
- staging-midrun (U mid-replay with the same layout): H installs 'y' while expecting 'z', the wrong level installed silently.
- mkdtemp: H installs 'z', correct.

(2) rotree.py, output in rotree.out. etc/ISABELLE_ID is 0444 in a 0555 directory, run as a non-root user. Opening it read-only with LOCK_SH works (status); opening it read-write fails with PermissionError (the apply lock mode, which a literal reading gives to apply --dry-run).

Read-only checks:
- plan:31-32, :103, :153, :330, :338, :359-375, :416, :424, :478-485, :631, :652, :744-753, :896, :907.
- REVIEW3:2577 (C19 judge: staging used only under the lock); REVIEW3:2945 and :2968 (C23: levels computed without the lock, no directory named); REVIEW3:3665 and :3684 (C30 judge's glossary wording).
- The current tool has no locking or staging code (grep of my_better_isabelle_prover/*.py).

No file outside my scratch directory was written, and no git command that changes state was run on any repository.

Recommended fix: Smallest fix: hand edits within the author's own design decisions and the authority delegated by ruling 17.

1. Decision 5 (plan:359-362): choose the directory by lock mode, not by command name.
- "暂存目录只由持 LOCK_EX 的运行使用：它在锁内清空、在其中重放、装入、结束时删掉。" (Only a run that holds LOCK_EX uses the staging directory: it clears it under the lock, replays there, installs, and deletes it at the end.)
- "其余每一次 `git` 调用都在新建的 `tempfile.mkdtemp()` 里：读目标（决定 3）、`status`、所有 `--dry-run`、pre-unlink 锁超时后的层级计算；目录接口的在 `realpath(<目录>)` 旁边建。" (Every other git call runs in a freshly created tempfile.mkdtemp(): reading targets (decision 3), status, every --dry-run, and a pre-unlink's level computation after a lock timeout. The directory interface creates its temporary directory beside realpath(<目录>).)

2. Decision 5's lock modes (plan:369-370): "`status` 与带 `--dry-run` 的 `apply`/`unapply` 只读打开、`LOCK_SH`；不带 `--dry-run` 的 `apply`、`unapply` 与 `conda-hook` 读写打开、`LOCK_EX`。" (status, and apply/unapply with --dry-run, open read-only with LOCK_SH; apply and unapply without --dry-run, and conda-hook, open read-write with LOCK_EX.)

3. Decision 9 (plan:480): "锁超时时层级在不持锁的情况下、在一个临时目录里算（决定 5）". (After a lock timeout the levels are computed without the lock, in a temporary directory, decision 5.)

4. Glossary (plan:31-32):
- 暂存目录 (staging directory): add "只由持排他锁的运行使用" (used only by a run that holds the exclusive lock).
- 临时目录 (temporary directory): redefine as "工具用 `tempfile.mkdtemp()` 新建的目录" (a directory the tool creates with tempfile.mkdtemp()) and list its users as in point 1. Keep "git 只在工具自己建的目录里运行" (git runs only in a directory the tool itself created), the wording already at plan:103 and :338.

5. Decision 15 (plan:631), two cases:
- `apply --dry-run` works on a read-only tree;
- a lock holder's installs survive a pre-unlink that times out and computes levels at the same moment: no FileNotFoundError, and no lower-level snapshot installed.

6. §10 C19 row (plan:896): record that the round-3 action "staging used only under the lock" (REVIEW3:2577) is now stated as this rule.

No change is needed to decision 4's "工具自己建的目录" (plan:338), which already holds.

**Judge: partially_confirmed → author_fixes_no_rereview.** Decision 5 (plan:359-362) chooses the directory by lock mode, not by command name:
- only a run holding LOCK_EX uses the staging directory; it clears it, replays, installs and deletes it;
- every other git call runs in a fresh tempfile.mkdtemp(): reading targets (decision 3), status, every --dry-run, and a pre-unlink's level computation after a lock timeout;
- the directory interface creates its temporary directory beside realpath(<dir>).

Lock modes (plan:369-370): status and --dry-run open read-only with LOCK_SH; apply and unapply without --dry-run, and conda-hook, open read-write with LOCK_EX. A literal reading fails `apply --dry-run` on a read-only tree (review-ipc4/defender-C18/rotree.out).

Other edits:
- Decision 9, plan:480: '在一个临时目录里算'.
- Glossary plan:31-32: the staging directory is used only by a run that holds the exclusive lock; define the temporary directory as one the tool creates with mkdtemp, and list its users.
- Decision 15 adds two cases: apply --dry-run on a read-only tree; a lock holder's installs survive a pre-unlink that timed out and computes levels at the same moment (defender-C18/race.out).
- §10's C19 row records that REVIEW3:2577's 'staging used only under the lock' is now this rule.

Refuted: the 'third place' bullet. Decision 4 already says 工具自己建的目录 (plan:338).

### C19 [minor] The engine accepts inputs its two-content model cannot represent: a non-regular target, two patch files for one target, a CRLF-converted creation patch; and new parent directories take the caller's umask despite plan:376

Section: Decision 2 refusals (plan:312-314); decision 3 (plan:330-333); decision 5 (plan:356-357, :376); decision 15 (plan:626); §2.4 (plan:263)  ·  merged from: engine-engine-6, engine-engine-2

**Statement.** The state model knows two kinds of content: a file's bytes, and absence (plan:383). Inputs outside the model are not refused.
(a) A target that exists but is not a regular file, such as a directory or a FIFO, passes the symlink refusal (plan:312-314). Copying it is undefined. In the copy, git creates a file over an empty directory with rc 0, and the later os.replace fails (review-ipc4/critic-engine/rc/rc.out).
(b) New parent directories are created under the caller's umask (plan:356-357). Under umask 077, a feature that creates a new directory leaves it with mode 0700 (critic-engine/nd/). That contradicts plan:376, which says the permission bits are the same for every caller, and decision 15's umask case checks only files (plan:626).
(c) Two patch files with one target in one feature directory, for example a stale file placed by hand in --features-dir, turn the file into CONFLICT. The diagnosis then blames the user's tree (critic-engine/dup/).
(d) §2.4 says a CRLF patch file is rejected by git apply (plan:263). That holds only for hunks with context or removed lines. A CRLF creation patch passes the listing step (rc 0, one target) and applies with rc 0, writing a file whose lines end in CR (critic-engine/rc/crlf.out; round 3 measured the same, REVIEW3 C20 judge).

Fix.
- Decision 2's refusals, checked alongside the symlink refusal, each with exit 3: a target that exists and is not a regular file (os.lstat with S_ISREG), and a feature directory with two patch files for one target.
- Decision 3: refuse, naming the file, any patch file whose `diff --git` header line ends in CR. That is the signature of a line-ending conversion. Content lines may legitimately carry CR: five pristine files do, for example src/HOL/Cardinals/document/root.bib.
- Decision 5: create missing parent directories with mode 0755 explicitly, and decision 15's umask case also checks new directories.
- Correct §2.4.

**Editor.** (c) and (d) reach little. make-patches names patch files by their target and deletes the old ones before writing new ones (decision 16 point 8), and the round-3 judge considered the CI route for CRLF closed by the single Linux build (REVIEW3 C20). They stay because each refusal is one line and turns a bad input into a refusal that names the file, instead of a CONFLICT blamed on the user. engine-2's request to put `*.patch -text` into every feature repository becomes optional once the CR refusal exists.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

C19 bundles four input gaps. I confirm (a), (c) and (d). I refute (b), and I reject its proposed 0755 fix. Severity is minor at most: none of the four can be reached through a correctly built package, but each is a premise of the state model that nothing enforces.

(a) A target that is not a regular file: CONFIRMED.
- The model knows two kinds of content: bytes, and absence ("不存在的 p 也是一种内容", plan:383).
- The only check on a target before replay is the symlink refusal, realpath(树/p) != realpath(树)/p (plan:312-314). A directory and a FIFO both pass it (e6.out: "symlink check passes: True ... S_ISREG: False").
- Reading a directory target raises IsADirectoryError, and os.replace onto it fails the same way (e6.out).
- Reading a FIFO blocks: still blocked after 3 s (e6.out). The tool holds the lock while it reads (plan:369-373), so a post-link would hang conda.
- I tried to refute the fix with a legitimate case: a feature that turns file src/A into directory src/A/ (it deletes src/A and creates src/A/B.ML). In the correctly applied tree, the target src/A is then a directory. The plan read literally applies this feature, and then status on the applied tree crashes with IsADirectoryError. An S_ISREG refusal would fire on that correct tree (e4.out).
- That case cannot be published once the fix exists. Decision 16 point 1 makes gate (c) round-trip through the tool's own apply_to/unapply_from (plan:665-666). unapply_from on the applied archive would hit the same refusal, so make-patches rejects any file-to-directory change. Today's GNU-patch gate (c) also happens to reject it ("File src/A is not a regular file -- refusing to patch", e4.out).
- So the refusal is self-consistent: it can never fire on a correctly applied tree. It should sit next to the symlink refusal. This mirrors the plan's own pattern for etc/ISABELLE_ID: a publish-time gate, with the runtime exit 3 as backstop (plan:670).

(b) New parent directories follow the caller's umask: REFUTED as a defect.
- plan:376 says "权限位对每个调用者相同" (the permission bits are the same for every caller). The callers there are the six commands that share one replay path (plan:375). The phrase descends from the round-2 judge's "identically for every caller including apply-to" (REVIEW2:2544).
- Under one umask, apply and apply-to create identical directories, so nothing contradicts plan:376. The umask test at plan:626 is explicitly about files.
- Directory modes that follow the umask are exactly conda's own rule. conda creates every directory of a package through LinkType.directory → mkdir_p → os.makedirs (core/path_actions.py:356-362; gateways/disk/create.py:361-370; gateways/disk/__init__.py:67-73). Measured with conda's own create_link: 755, 775 and 700 under umask 022, 002 and 077 (e3.out). This machine's environments have 775 directories everywhere.
- Under umask 077, then, conda itself makes isa/ and light's share/isabelle-light-locale/ 0700 (light's component payload: the `ROOT` and theory files under `share/<包名>/`). A 0700 directory created by the tool takes nothing away from anyone. This is the argument on which the round-2 judge refuted the same umask-027/077 point for created files (REVIEW2:2468-2471, :2540).
- Git records no directory modes, so no patch header offers a mode to copy.
- The plan already pins umask 022 where it compares directory modes, in (b2) (plan:686, :691).
- The proposed fix, an explicit 0755, would be harmful. It diverges from conda's 0775 under umask 002, the default on this machine. In a group-shared environment, a group member could then not unlink files inside a tool-created directory during unapply.
- Today's chain creates no new directory: light's three created files sit in the existing src/Pure and src/Pure/Isar.

(c) Two patch files for one target: CONFIRMED (nit).
- Decision 6 writes the features that touch p as t1 < … < tm with strict inequality (plan:380), which assumes one patch file per feature per target.
- Decision 3 checks only the converse: each patch file has exactly one target (plan:331-332).
- With a stale hand-placed copy, a pristine tree and a correctly applied tree both read CONFLICT (e5.out). The §4 diagnosis then tells the user "If you edited that file: conda install --force-reinstall isabelle" (plan:733-736).
- No conda route produces this: make-patches derives each name from the target and deletes old *.patch files first (make-patches:159-160, :169). Only a hand-edited --features-dir does.

(d) CRLF patches: CONFIRMED, and stronger than stated.
- §2.4 now says "CRLF 的 patch 文件本身会被 git apply 拒绝（rc 1）" (a CRLF patch file is rejected by git apply, rc 1; plan:263). §8 repeats it (plan:843). Neither sentence is in rev 3 (rev3:219-220).
- Both contradict round-3 findings: the C5 defender's refinement (REVIEW3:830) and the C20 judge's confirmed point that a CRLF creation patch applies with rc 0 and reads applied.
- Measured with decision 4's exact isolated call, a CRLF modification patch passes the listing step (rc 0, one target) and fails replay with rc 1. Decision 4 reads rc 1 as "does not match" (plan:349), so the file becomes CONFLICT, not a refusal. A CRLF creation patch passes both steps and writes CR line ends (e1.out). So neither shape is ever refused as a bad input.
- The single Linux build closes the CI route (REVIEW3:2674), and check_bytes catches CR output in acceptance. What remains is a developer on Windows using --features-dir or apply-to with an autocrlf checkout.
- The proposed signature is correct: the `diff --git` line ends in CR. git's autocrlf leaves alone any file that already contains CR. A patch file whose content lines carry CR (like a diff of root.bib) keeps an LF header after an autocrlf=true clone, while an LF-only patch gets a CR on every line (e2.out).
- So the refusal never fires on a legitimately CR-bearing patch. CR-bearing tracked files exist: src/HOL/Cardinals/document/root.bib and three SMT_Examples/*.b2i in contrib/Isabelle2025-2, by my grep.

The editor's rebuttal. I agree that (c) and (d) reach little and that each costs one line. I agree that `*.patch -text` in the feature repositories stays optional, as the round-3 C5 judge already said (REVIEW3:885). There is no relaxation to judge. §10 needs no row: C19 is a new finding, not a silent deviation.

Experiment: All runs are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C19/, using git 2.43.0. G.sh is decision 4's exact isolated call: an env -i whitelist with GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=/dev/null, GIT_ATTR_NOSYSTEM, LC_ALL=C and the ceiling, plus -c core.autocrlf=false -c core.attributesFile=/dev/null.

- e1.sh → e1.out: real git diff-tree patches, an LF and a CRLF version each.
  - Modification patch, CRLF: listing rc=0 with one target; replay rc=1, "patch does not apply".
  - Creation patch, CRLF: listing rc=0; replay rc=0; the result has 2 CR bytes.
- e2.sh → e2.out: two committed patch files, cloned with -c core.autocrlf=true.
  - A patch whose content lines carry CR: 4 CR bytes before and after; the first line does not end in CR.
  - An LF-only patch: 0 → 8 CR bytes; the first line ends in CR.
- e3.out: conda's own create_link(LinkType.directory), run via ~/miniconda3/bin/python under umask 022, 002 and 077, gives 755, 775 and 700.
- e4.sh → e4.out: a feature that deletes src/A and creates src/A/B.ML.
  - Today's GNU-patch gate (c) refuses the reverse pass: "File src/A is not a regular file".
  - critic-engine's ipc4.py, a literal reading of the plan (copied to ipc4.py), applies it on a fresh tree. In the applied tree src/A is a directory, and status then crashes with IsADirectoryError.
  - An S_ISREG check flags src/A on that correctly applied tree.
- e5.sh → e5.out: one feature directory with src-Y.ML.patch (v2) plus a stale src-Y.ML.v1.patch. status reads CONFLICT on a pristine tree and on a correctly applied tree.
- e6.py → e6.out:
  - A directory and a FIFO at target paths both pass the plan's realpath symlink check, with S_ISREG False.
  - Reading the directory gives IsADirectoryError, and so does os.replace onto it.
  - Reading the FIFO is still blocked after 3 s (timeout rc 124).

Sources read: the plan:263, :312-314, :331-333, :349, :357, :369-376, :380-383, :626, :665-672, :686-691, :712-736, :843; rev3:219-220; REVIEW2:2468-2471, :2540, :2544; REVIEW3:830, :885, :2674 and C20's judge; make-patches:62-68, :159-169, :172-184; conda gateways/disk/__init__.py:67-73, gateways/disk/create.py:361-370, core/path_actions.py:356-362; light's patches/Isabelle2025-2 (all three created files sit in existing directories).

A late check for exact line numbers could not run because the /tmp tmpfs filled up from other processes. The numbers above come from earlier reads and the Read tool.

Recommended fix: These are plan-text edits only; the tests are delegated to the author.

1. Decision 2's refusals (plan:312-314, and §4's exit-3 list at plan:713-715). Add, checked in the same pass as the symlink refusal and before any copy: "某个 patch 文件的目标存在而不是普通文件（os.lstat 不是 S_ISREG：目录、FIFO 等），exit 3，点名路径" (a patch file's target exists but is not a regular file; exit 3, naming the path). Add one clause saying that gate (c) round-trips through apply_to/unapply_from (decision 16 point 1). This refusal therefore also rejects, at publish time, a feature that turns a file into a directory or back, so it never fires on a correctly applied tree. Decision 15 gets a case for a directory target and a FIFO target.

2. Decision 3 (plan:331-332). Next to "每个 patch 文件必须恰好一个目标" (each patch file has exactly one target), add: "一个 feature 目录里两个 patch 文件的目标相同 → exit 3，点名两个文件" (two patch files in one feature directory with the same target → exit 3, naming both). This makes decision 6's t1 < … < tm an enforced invariant. Add one decision 15 case.

3. Decision 3. Refuse with exit 3, naming the file, any patch file whose first line (the `diff --git` line) ends in CR, because that is the signature of a line-ending conversion. Content lines may carry CR legitimately, and git's autocrlf never converts such a file, so the header stays LF. Correct §2.4 (plan:263) and §8 (plan:843) to say:
   - a CRLF-converted modification patch passes the listing and fails replay with rc 1, which decision 4 would read as a mismatch (CONFLICT);
   - a CRLF-converted creation patch passes both steps with rc 0 and writes CR line ends (REVIEW3 C5 defender, C20 judge).

   `*.patch -text` in the feature repositories stays optional.

4. Part (b): do NOT force 0755. Optionally add half a sentence to decision 5 (plan:357): "新建的父目录用 os.makedirs 按调用者的 umask 建，与 conda 自己建环境里每个目录的规则相同；git 不记录目录权限位" (new parent directories are created with os.makedirs under the caller's umask, the same rule conda applies to every directory it creates in the environment; git records no directory modes). The umask test at plan:626 needs no change.

**Judge: partially_confirmed → author_fixes_no_rereview.** Add three refusals, each exit 3, naming the file:
- Decision 2 (plan:312-314) and §4's exit-3 list: a target that exists and is not a regular file (os.lstat is not S_ISREG), checked in the same pass as the symlink refusal. Add one clause: gate (c) round-trips through apply_to and unapply_from, so this refusal also stops a file-to-directory change at release and never fires on a correctly applied tree.
- Decision 3 (plan:331-332): two patch files in one feature directory with the same target.
- Decision 3: a patch file whose first line (the diff --git header) ends in CR. Content lines may legitimately carry CR; autocrlf never converts such a file (review-ipc4/defender-C19/e2.out).

Correct §2.4 (plan:263) and §8 (plan:843): a CRLF-converted modification patch lists fine and replays with rc 1, which reads as CONFLICT; a CRLF-converted creation patch applies with rc 0 and writes CR line endings (defender-C19/e1.out). Decision 15 gets cases for directory and FIFO targets, a duplicate target, and a CRLF header.

Refuted: part (b). Do NOT force mode 0755. Directory modes that follow the umask are conda's own rule (gateways/disk/__init__.py:67-73; defender-C19/e3.out), and plan:376 is about callers sharing one replay path. Optionally add half a sentence saying so to decision 5.

### C20 [minor] Several user-visible texts are false or contradict each other: heap notices on update and reversal, help's target, the busy text, unmarked created files, 'registrations restored', and the chain-broken advice

Section: §4 heap notice, CONFLICT, busy and chain-broken texts; decision 5; decision 9 message rules; decision 14; decision 15  ·  merged from: user-U12, user-U13

**Statement.** Ruling 17 delegates wording to the author. These items are false statements, not matters of style.
(1) A routine `conda update --all` to a new isabelle build (ruling 22) prints three 'reversed' heap notices from the old packages' pre-unlinks and then one 'applied' notice. The last 'reversed' notice says that the heaps in the user directory came from the patched sources, seconds before the isabelle pre-unlink deletes that directory (review-ipc4/critic-user/run2.out case c2; run1.out case d1). Decision 15 asserts one notice per install (plan:643) and asserts nothing for an update.
(2) After a full reversal, the notice's only action is 'To do it now: isabelle build -b HOL' (plan:722, :724), a rebuild of several minutes, although the heaps shipped with the package match the sources again. Isabelle looks in the user heap directory first and checks the first log database it finds (Isabelle2025-2/src/Pure/Build/store.scala:334-336, :476-490), so a stale user heap hides the good shipped one. The cheap and correct advice is to delete the user-directory heaps.
(3) In a HOL-only light update, the Pure and HOL sources end byte-identical, yet the notices announce that Pure and HOL will be rebuilt.
(4) The command list says `help` prints AGENTS.md (plan:709; cli.py:118-120 does so today). Decision 14 says `help` prints the README's 'Coming from my-better-isabelle 0.x' section (plan:606). The CONFLICT text sends 0.x users to `help` (plan:739).
(5) Decision 5 says a busy post-link writes the retry command (plan:372-373), but §4's busy text ends 'Retry later.' with no command (plan:752-753).
(6) The CONFLICT text offers two branches, 'If you edited that file' and 'If a file created by a feature has other content', without marking which listed files a feature created (plan:733-738). The residue block does mark them (plan:747).
(7) 'features and component registrations are restored automatically' (plan:737, :749) holds only for registrations made by packages. The isabelle pre-unlink deletes the whole user directory (recipe.yaml:223-231), including the user's own `isabelle components -u` entries and settings.
(8) The chain-broken text says 'Update the named package' but names release tags, not packages (plan:727-728). With exact base pins (plan:499), only --no-deps or --force can produce this state, and then updating does not help.

Fix.
- A pre-unlink writes only the one line 'Isabelle sources under ... changed (reversed: X)'; only a post-link writes the heap paragraph.
- When the end state is the package's own sources, advise deleting $(isabelle getenv -b ISABELLE_HEAPS)/<ML_IDENTIFIER>.
- Decision 15 asserts the transcript of an update transaction.
- Choose one target for `help`, a document that contains the 0.x section.
- End the busy text with 'Then run: isabelle-patch-control apply'.
- Mark created files in the CONFLICT text.
- Qualify (7): registrations made by installed packages are restored; the user's own settings and entries are deleted.
- In (8), name the package through names.package_name and say 'install matching versions'.

**Editor.** 

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the eight parts. Seven survive in substance. Part (1) survives only as "unspecified and noisy", not as "false". Part (2) is costly advice rather than a false statement. Part (7) holds at one of its two citations. Severity minor is right. Ruling 17 gives wording to the author, so no owner decision is needed. The challenge's own fix has two gaps: its bullets for (1) and (2) conflict during a conda removal, and no bullet fixes (3).

(1) PARTLY CONFIRMED, as a gap, not a falsehood.
- Decision 9 makes every hook report its own change, and every pre-unlink report its own reversal (plan:472-474). The heap paragraph is printed whenever src/ changed (plan:717).
- So the routine `conda update --all` (ruling 22, plan:91-92) prints one paragraph per old feature pre-unlink, then one applied paragraph. The critic's prototype on real conda 25.11.1 shows this (critic-user/run2.out, case c2).
- Each notice is true when it is written. The defect is that the last reversal paragraph ('Heaps built earlier in the user directory...', plan:724) is moot: the isabelle pre-unlink deletes that directory moments later (recipe.yaml:223-231; run2.out shows heaps= empty afterwards).
- Neither decision 9 nor decision 15 describes or tests the update transcript. plan:643 asserts one notice per transaction, true only for installs. plan:648 and §6 (h) (plan:799) assert only that the features are re-applied.
- Refinement of the fix: the challenge says a pre-unlink writes only one line, but then `conda remove` of every feature package gets no heap advice at all. The delete-the-user-heaps advice from part (2) can only come from the last pre-unlink. So that pre-unlink must keep one advice line when it leaves the tree at the chain bottom.

(2) CONFIRMED as costly and incomplete advice.
- On full reversal, the notice keeps 'To do it now: isabelle build -b HOL' (plan:722, :724).
- Isabelle searches the user heap directory first (store.scala:334-336). It checks the first log database it finds (:488-492). It loads the first heap file it finds without any check (:358-360).
- The package ships Pure, HOL and Main log databases (pkgs/isabelle-2025.2-0/isa/heaps/polyml-5.9.2_x86_64-linux/log/*.db).
- So the stale patched user heaps hide the shipped heaps, which match the sources again. `isabelle build` then spends minutes rebuilding them. `isabelle process` silently loads the patched heap.
- Deleting heaps/ in the user directory is instant and correct. The cost is that heaps the user built before installing any feature, and that are still valid, also get deleted.
- The tool never runs isabelle (plan:310), so it cannot print the concrete path. The advice must be phrased via `isabelle getenv -b ISABELLE_HOME_USER`, as plan:721 already does, not as a POSIX `rm` command.

(3) CONFIRMED, and not covered by the challenge's fix.
- I added a stage to the prototype that re-releases fb and fc as version 2 with byte-identical patches. This is the shape of a light HOL-side-only release with its upper features re-released (ruling 21, plan:85-87).
- `conda update --all` printed three paragraphs, each saying 'Isabelle rebuilds Pure and HOL on first use'.
- The isa/ tree digest was identical before and after. The user directory and its heap survived, because isabelle was not in the transaction.
- Isabelle compares source digests (store.scala:553-559), so nothing would be rebuilt. The claim is false here. A post-link writes the same paragraph, so moving it to post-links does not fix this.

(4) CONFIRMED.
- §4 says `help` prints AGENTS.md (plan:709). Decision 14 says `help` prints the README's 0.x section (plan:606). The CONFLICT text's pointer depends on which is true (plan:739).
- Today's code prints AGENTS.md (cli.py:118-121). That file is the packaged one (pyproject.toml:40; my_better_isabelle_prover/AGENTS.md is a symlink to ../AGENTS.md); README is not packaged.
- The same split was already in rev 3 (rev3:475 vs :550). §10's C27 row marks the 0.x pointer as done (plan:904), but the pointer's target is undefined.

(5) CONFIRMED. Decision 5 says a busy post-link writes the busy text and the retry command (plan:372-373). The shared busy text ends 'Retry later.' with no command (plan:752-753). A user cannot retry the post-link itself; the right command is `isabelle-patch-control apply`.

(6) CONFIRMED.
- The CONFLICT text prints both remedies without saying which kind of file each listed file is (plan:733-738). The residue block marks created files (plan:747), and decision 9 says the remedy follows the cause (plan:481-483). The tool knows the kind: a created file does not exist at level 0.
- The prototype shows the harm (run2.out, case e4). For a created file, src/new.ML, the reader is offered `--force-reinstall isabelle` first. Running it changes nothing, and the same CONFLICT text is printed again.

(7) CONFIRMED at plan:737 only. plan:749 says 'the remaining features are re-applied automatically' and claims nothing about registrations.
- The plan's glossary defines a component registration as any line that `isabelle components -u` writes into the user directory's etc/components (plan:28; components.scala:294-302).
- The isabelle pre-unlink deletes the whole user directory (recipe.yaml:223-231). Ruling 26 re-runs only the post-links of packages.
- So the user's own registrations and settings are deleted and never restored. 'Component registrations are restored automatically' is false for them.
- The 'save your own edits' line covers only $PREFIX/isa (plan:735).

(8) CONFIRMED. The text says 'Update the named package' (plan:727-728) but names only release tags and a features.d path. Decision 9 intends a named package (plan:483), and names.package_name exists for this (plan:297-298).
- 'Update' is also the wrong verb for a reachable case. `conda remove --force <lower package>` removes only that package (plan:220), which leaves its base missing; the fix there is to install it.
- I did not verify the challenge's claim that "updating does not help" after --no-deps. The fix does not depend on it.

Outside C20: the CONFLICT and residue texts still say '(restores the package's files' without condition (plan:736, :748). Round 3 C27's judge asked to state the hard-link limitation; it is stated only in the README (plan:482-483).

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C20/

(a) Setup.
- I copied critic-user's prototype channel builder (mkchan4.py, which implements rev 4's hooks and the §4 texts) to mkchan.py, plus lib.sh.
- I added STAGE 4: fb and fc re-released as version 2 (release tags fb/2 and fc/2, fc's base fb/2) with byte-identical patches. It stands in for a light HOL-side-only release.
- run1.sh used real conda 25.11.1 with a private HOME, CONDARC and CONDA_PKGS_DIRS. It created an environment with isa=2025.2=1, fc and rpc, placed a heap marker in the user directory, switched to stage 4 and ran `conda update --all`.

(b) Result (run1.out).
- fb and fc went from version 1 to version 2.
- conda printed three heap paragraphs, each saying 'Isabelle rebuilds Pure and HOL on first use': reversed fc (its first line was swallowed by the progress-bar filter), reversed fb, then applied fb, fc.
- The isa/ tree digest was 223c93b8… both before and after.
- The user directory and its heaps/HOL marker survived, and status showed every feature applied.

(c) Read-only checks.
- Isabelle2025-2/src/Pure/Build/store.scala: user directory first (:334-336), first log database wins (:488-492), first heap file loaded without a check (:358-360), source digest comparison (:553-559).
- The package ships log/{Pure,HOL,Main}.db (pkgs/isabelle-2025.2-0/isa/heaps/polyml-5.9.2_x86_64-linux/log/).
- The isabelle pre-unlink deletes the whole user directory (recipe.yaml:223-231).
- components.scala:294-302.
- cli.py:118-121 prints AGENTS.md; pyproject.toml:40 packages it; my_better_isabelle_prover/AGENTS.md is a symlink to ../AGENTS.md.
- The `help` split is old: rev3:475 vs rev3:550, and it is still there at plan:606 vs plan:709.
- REVIEW3 C22 and C23: the judges' busy wording kept 'Retry later', while decision 5 promises a retry command.

(d) The critic's run2.out, cases c2 (the update transcript; the user directory empty afterwards) and e4 (the created-file CONFLICT and the --force-reinstall remedy, which does nothing).

Recommended fix: All of these are author wording under ruling 17.

(1) Heap notices.
- A pre-unlink writes only 'Isabelle sources under $PREFIX/isa changed (reversed: X).'.
- When a pre-unlink, or a command-line unapply, leaves the tree at the chain bottom, add one line in place of 'isabelle build -b HOL': 'No feature is applied now; delete heaps/ in this environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER), and the heaps shipped with the isabelle package match the sources again.'
- Post-links and command-line apply keep the paragraph.

(2) Make the rebuild sentence true in every case. Replace 'Isabelle rebuilds Pure and HOL on first use' with 'Isabelle rebuilds, on first use, every heap not built from exactly these sources'.

(3) Decision 15 asserts two transcripts:
- the `conda update --all` to a new isabelle build: one line per reversed feature, then one applied paragraph;
- the identical-patch re-release.

(4) Make plan:709 agree with decision 14. For example: `help` prints AGENTS.md, which carries the 'Coming from my-better-isabelle 0.x' section verbatim. The CONFLICT pointer names that section.

(5) The post-link busy text ends 'Then run: isabelle-patch-control apply'. The command-line busy text keeps 'Retry later.'.

(6) In the CONFLICT text, mark each file '(created by a feature)' as the residue block does, or print only the remedy that matches each file's kind.

(7) Change plan:737 to: 'registrations made by installed packages are restored; your own settings and `isabelle components -u` entries in that directory are deleted'. Extend 'save your own edits' to the user directory.

(8) In the chain-broken text, name the packages through names.package_name. Replace 'Update the named package' with 'install matching versions (e.g. conda install <base package>=<version>, or conda update --all)'.

**Judge: partially_confirmed → author_fixes_no_rereview.** Wording fixes under ruling 17:
- (1) A pre-unlink writes only 'Isabelle sources under … changed (reversed: X)'. When a pre-unlink or a command-line unapply leaves the tree at the chain bottom, it adds one line: delete heaps/ in the user directory (`isabelle getenv -b ISABELLE_HOME_USER`); the shipped heaps then match again (store.scala:334-336, :488-492). Post-links and command-line apply keep the paragraph.
- (2)/(3) The rebuild sentence becomes 'Isabelle rebuilds, on first use, every heap not built from exactly these sources' (review-ipc4/defender-C20/run1.out: identical tree, three notices).
- Decision 15 asserts the transcript of `update --all` to a new isabelle build and of an identical-patch re-release.
- (4) Make plan:709 and plan:606 agree on one help target that carries the 0.x section. Today's code prints AGENTS.md (cli.py:118-121).
- (5) The post-link busy text ends 'Then run: isabelle-patch-control apply'.
- (6) Mark created files in the CONFLICT text.
- (7) plan:737: registrations made by installed packages are restored; the user's own settings and `components -u` entries are deleted. Extend 'save your own edits' to the user directory.
- (8) The chain-broken text names packages through names.package_name and says 'install matching versions'.

### C21 [minor] §0 and §10 again record things untruly: a quote attached to the wrong owner reply, an author decision inside a binding ruling, three §10 rows that omit or misstate what was done, and a freeze reason the judge asked to drop

Section: §0 items 26 and 30; §5 step 0; §10 rows C11, C28, C30  ·  merged from: consistency-CONS4-8, consistency-CONS4-13, landing-L9

**Statement.** (1) Item 26 records the owner's answer to the no-marker advice as '赞同你的建议' (plan:117-118). The owner's reply to that advice was '很好，那么我建议所有包包括组件包也都钉死 isabelle 包的完整版本包括 build number 你觉得如何？' (transcript lines 7367 and 7387). '好的，赞同你的建议' (line 7404) answered the later no-pin advice (line 7402). The substance is unchanged.
(2) Item 30 adds to the binding ruling that 'build 号从渠道上该包该版本已有的最高号加一推出，跨 isabelle 构建严格递增（评审 C3）' (plan:132-133). Owner question 5 offered only (a) the new build-string form or (b) the old one (line 7577); the derivation was background taken from the judge's C3 action. An author decision placed inside a binding item gets frozen without the owner having ruled on it, the pattern round 3 flagged (C29 (3)).
(3) §10's C30 row says 'build 号' is used throughout, qualified by its package (plan:907). Yet '构建号' remains at plan:91, :108, :111, :132 and :880. At plan:91 it also replaces the wording the owner confirmed, 'isabelle build 号' (transcript line 6566). The round-3 judge's own C3 action prescribed 'isabelle 构建号输入' (REVIEW3:638), against its C30 action, which explains the slip, but the row is still untrue.
(4) §10's C11 row (plan:888) omits judge action (6): 'Record in §10 that REVIEW2:584's sentence was measured false' (REVIEW3:1682).
(5) §5 step 0 still gives the release freeze a safety reason: feature packages would be pinned to a patched build, and every feature user would get exit 3 (plan:760-761). The judge asked to restate the reason as ruling 11 itself, because §6 (a) would already turn red on a patched pin, so the freeze is no longer a safety rule (REVIEW3:3447, :3460). §10's C28 row (plan:905) does not mention the departure.
C2 adds a sixth item: the author's statement to the owner on question 5 needs a correction in §0.

Fix. Quote '很好' for the no-marker answer. Move the derivation from item 30 into decision 10, as the plan's own decision citing judge C3. Replace every '构建号' with '`isabelle` 包的 build 号', and quote the owner-confirmed wording at plan:91. Add the REVIEW2:584 note to the C11 row. Give the freeze ruling 11 as its only reason, and note this in the C28 row.

**Editor.** The C8-row sub-point raised by conda-6 and CONS4-8 is dropped. The round-3 judge's action (5) told the author to record 'the return to the judge's rule' (REVIEW3:1321), so the author followed the judge's wording.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

All five sub-points hold against the transcript and the review files. Two of them need a narrower fix than the challenge proposes.

(1) CONFIRMED. The no-marker advice is the assistant message at jsonl:7364, which ends "请你定". The owner's next messages are jsonl:7367 and its resend at jsonl:7387: "很好，那么我建议所有包包括组件包也都钉死 isabelle 包的完整版本包括 build number 你觉得如何？". No other user or assistant text lies between them. "好的，赞同你的建议" (jsonl:7404) answers the later no-pin advice at jsonl:7402. Plan:117-118 attaches "赞同你的建议" to the no-marker advice, which is the wrong reply. Plan:120 quotes "好的，赞同你的建议" correctly for the no-pin advice. The substance is unchanged.

(2) CONFIRMED, with a smaller harm than claimed. Question 5 (jsonl:7577) offered only (a) the new build-string form or (b) the old one. The channel derivation appeared only as background ("按评审 C3 的修法，build 号本来就要…"), and the owner answered "按你建议来" (jsonl:7580). So the derivation was never ruled, yet plan:132-133 puts it inside binding item 30.
- Mitigation: the sentence carries its source "（评审 C3）", unlike §7 row (7) in round 3's C29 (3), which carried the label "已裁定".
- Mitigation: "跨 isabelle 构建严格递增" restates owner-confirmed item 22, "各包 build 号加一" (plan:91; jsonl:6566 confirmed at 6569/6580). Only the "highest number on the channel plus one" mechanism is new.
- Mitigation: decision 10 already states that mechanism as the plan's own decision (plan:496-497).
- So "move it into decision 10" is already done. The fix is just to delete the sentence from item 30.
- Side note: my prototype (derive.py) shows the mechanism is not innocuous, which is a reason not to freeze it. Read literally, decision 11's "download a published (name, version, build string)" rule (plan:524), applied to a derived `Isabelle2025_2_<n>`, never downloads an unchanged feature package. That contradicts decision 11's own example at plan:548 ("已发布、build 直接下载"). Round 3's C3 test keyed on `Isabelle2025_2_<b>_*` and did download. This also gives C2's sixth item a basis: the author told the owner in question 5 that the two forms are mechanically the same (jsonl:7577).

(3) CONFIRMED for plan:91, :108 and :111. The §10 C30 row (plan:907) says "全文'build 号'点明所属包", and the glossary (plan:22) defines only "build 号". The migration plan never uses "构建号".
- plan:108 and :111 are exactly the rev-3 lines :99 and :102 that the round-3 C30 judge action named for replacement (REVIEW3:3659). They are unchanged, so this is a silent deviation.
- At plan:91 the author followed the C3 judge's wording "isabelle 构建号输入" (REVIEW3:638). That wording contradicts the C30 action. It also contradicts the message the owner confirmed, "workflow 接一个'isabelle build 号'输入" (jsonl:6566, confirmed 6569/6580).
- plan:132 and :880 are defensible as quotations: :132 repeats the author's own question-5 wording, and :880 quotes the judge. Rewording them is optional.

(4) CONFIRMED. Round-3 judge C11 action (6) says "Record in §10 that REVIEW2:584's sentence was measured false" (REVIEW3:1682). REVIEW2:584 is the round-2 judge's "reinstalling the feature completes it". The C11 row (plan:888) lists only decision 5, §2.3, §4, decision 15 and Appendix A. Grepping the plan for "584" finds nothing, and neither the §10 preamble (plan:873-874) nor the round-2 leftover rows mention it. This is a silent omission.

(5) CONFIRMED. Round-3 judge C28 says "Move the freeze to §5 step 0. Restate its reason (under ruling 22 it is no longer a safety rule)" (REVIEW3:3447, :3460). Plan:760-761 moved the freeze but kept the overtaken safety reason ("feature 包会钉到一个带补丁的构建上，每个 feature 用户都 exit 3").
- That reason is false under rev 4's own design. A patched CI build carries the hg-commit ISABELLE_ID (pack.sh:386-391). So decision 3.2 exits 3 (plan:249-250), §6 (a) turns red, and `publish` needs accept and roundtrip (plan:539-540).
- The C28 row (plan:905) says only "发布冻结移到 §5 第 0 步" and does not mention that the reason was kept.
- The judge also asked for a C26-row entry. The C28 row covers that in substance, so it is not a finding.

Editor's rebuttal (C8-row sub-point dropped): I agree. Rev 4's rule is the round-2 C17 rule (REVIEW2:2282) with round 3's measured top-feature refinement. The round-3 judge itself called it "the return to the judge's rule" (REVIEW3:1321), and the plan's C8 row and its "第二轮遗留：C17 规则" row say that. Adding "加链顶 feature 的细化" would make the row exact, but this is a phrasing difference, not a silent deviation.

Severity minor is right. These are record errors, and no mechanism depends on them.

Experiment: Scratch: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C21/.
- I read the session transcript ~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl read-only, using the critic's extractors (critic-consistency/userlines.py, which includes queued messages, and asstlines.py).
- Assistant text went to asst_7330_7410.txt (the no-marker advice at 7364, the no-pin advice at 7402), asst_7520_7650.txt (question 5 at 7577) and a6540.txt (the 6566 message containing "isabelle build 号" as the input name).
- User messages 7303-7643: 7367/7387 "很好，那么我建议…", 7404 "好的，赞同你的建议", 7580 "按你建议来"; 6569/6580 "确认".
- Grepped the plan for 构建号 (lines 91, 108, 111, 132, 880), for 584/REVIEW2 (no §10 note) and for 冻结 (lines 579, 760).
- Read REVIEW3 judge actions: C3 (:600-641), C11 (:1640-1684), C8 (:1296-1321), C28 (:3392-3461), C29 (:3462-3575) and C30 (:3640-3687). Read REVIEW2:578-588 and :2270-2290.
- Mapped the rev-3 line numbers the C30 action names (PLAN.rev3.md:99, :102) to rev 4's :108 and :111.
- derive.py/derive.out simulate decision 10/11's rule. With `Isabelle2025_2_<n>` and n = max+1, an unchanged published feature at the same isabelle build is never downloaded ("build Isabelle2025_2_1"). Round 3's C3 form downloads it ("download Isabelle2025_2_1_0"), and so does reading the pin from repodata depends.

Recommended fix: Hand edits only, no owner question:
1. plan:117-118: change the quoted reply for the no-marker advice to "很好" (jsonl:7367/7387). Keep "好的，赞同你的建议" for the no-pin advice.
2. plan:132-133: delete "build 号从渠道上该包该版本已有的最高号加一推出，跨 `isabelle` 构建严格递增（评审 C3）" from item 30. Decision 10 (plan:496-497) already states it; add "（评审 C3）" there.
3. Replace 构建号 with "`isabelle` 包的 build 号" at plan:91, :108 and :111. Note at :91 that this restores the wording the owner confirmed ("isabelle build 号", jsonl:6566). Optionally reword the quotations at :132 and :880 the same way.
4. §10 C11 row (plan:888): add "第二轮 judge 的 REVIEW2:584（重装 feature 即补完）实测为假，附录 A 已改".
5. plan:760-761: replace the reason with "（第 11 条）" alone. Add to the §10 C28 row: "理由按 judge 改为第 11 条本身：§6 (a) 在带补丁的钉死上本来就会变红，冻结已不是安全规则".
6. Optional: make the C8 row read "恢复第二轮 C17 的规则，加第三轮的链顶 feature 细化".

**Judge: confirmed → author_fixes_no_rereview.** Record fixes, all by hand:
- plan:117-118: quote '很好' (jsonl 7367 and 7387) as the owner's reply to the no-marker advice. '好的，赞同你的建议' (jsonl 7404) answered the later no-pin advice; the judge read the transcript.
- plan:132-133: delete the build-number derivation sentence from item 30. Decision 10 (plan:496-497) already states it; cite judge C3 there.
- Replace 构建号 with '`isabelle` 包的 build 号' at plan:91, :108 and :111. At :91 this restores the owner-confirmed wording 'isabelle build 号' (jsonl 6566).
- §10's C11 row (plan:888): add the note that REVIEW2:584 was measured false.
- plan:760-761: give the release freeze ruling 11 as its only reason, and say so in §10's C28 row.

No §0 correction of the Q5 statement is needed (see C2).

### C22 [minor] Appendix A, the argued exception ruling 14 asks for, says the 'no untracked post-link side effects' principle still holds for the isabelle package two sentences before saying its post-link patches the tree and runs other packages' scripts

Section: Appendix A (plan:921-924, :944-945)  ·  merged from: consistency-CONS4-14

**Statement.** Appendix A says that §3.1's and §9's principles (a post-link creates nothing conda does not track; nothing patches the user's Isabelle in place) remain the isabelle package's own principles (plan:921-922). The next sentence says the isabelle package's own post-link runs the hook fragment, which re-applies features in place and creates untracked files, and also re-runs the post-links of the packages that depend on it (plan:923-924). PACKAGING_DESIGN.md:52 cites conda-build's rules for post-links: touch only the files being installed, and depend only on rm, cp, mv and ln. Re-running other packages' scripts, and depending on python (decision 12 point 2), both depart from those rules, and the appendix argues neither. This is the third round in which Appendix A states something false (REVIEW3 C16).

Fix. Narrow the first sentence to the package's content: the isabelle package ships pristine sources. Add one argued paragraph on why its post-link re-runs dependents' post-links and depends on python, since that is the rule this exception actually breaks.

**Editor.** 

**Relaxation proposed by the editor.** With C3's relaxation, the isabelle post-link no longer patches the tree, so the contradiction about in-place patching disappears and only the re-run needs arguing.

**Defender: partially_confirmed** (needs owner: False).

The core of C22 holds: the first sentence of Appendix A contradicts the sentence after it. Two of its supporting claims are overstated, and the editor's relaxation does not remove the contradiction.

CONFIRMED (the contradiction):
- plan:921-922 says that the §3.1 and §9 principles ("一切随包装进去，post-link 不生成 conda 不跟踪的东西，不原地 patch 用户的 Isabelle") are still the isabelle package's own principles.
- plan:923-924 then says the isabelle package's own post-link calls the hook fragment, re-applies the installed features, and re-runs the post-links of the packages that depend on it.
- The hook fragment does a whole-chain apply (plan:467-468). conda links every package and creates the entry points first, then runs the post-links one by one (conda core/link.py:938-967). So in a fresh `conda create isabelle isabelle-light-locale`, the isabelle post-link runs first. It passes the `-x isabelle-patch-control` check (plan:435) and creates light's created files itself. conda does not track those files.
- In `--force-reinstall isabelle` or a build upgrade, the re-run (plan:560-563) runs two kinds of post-link:
  - the feature post-links, which patch $PREFIX/isa in place;
  - the component post-links, which write $ISABELLE_HOME_USER/etc/components (components.scala:294). That file is outside $PREFIX and untracked, which is exactly the objection in PACKAGING_DESIGN.md:1007.
- So "post-link 不生成 conda 不跟踪的东西" is plainly false for the isabelle package's own post-link.
- This is not new. Round-2 C9 item (2) raised the same contradiction (REVIEW2:1331, :1368), and the defender's fix replaced the sentence (REVIEW2:1408). The judge asked that "the isabelle package's own post-link takes part in the exception" (REVIEW2:1425). Rev 3 added the participation clause but kept the claim. Rev 4 kept both and added the re-run clause, which makes the contradiction worse.
- §10 has no row for this, even though it lists other leftovers from round 2. So a confirmed round-2 defect survived, and the plan does not name it.

PARTLY REFUTED OR OVERSTATED:
(a) "The appendix argues neither" is too strong for the re-run.
- The appendix gives a reason for the re-run: component registrations come back after a package swap (plan:924).
- It also states the cost: the post-links of packages that depend on isabelle must be safe to run more than once (plan:944-945).
- What is missing is one sentence saying WHY only the isabelle post-link can do this:
  - the isabelle pre-unlink deletes the whole user directory, etc/components included (recipe.yaml:223-231);
  - conda runs only the hooks of packages the transaction changes (plan:216-218, solve.py:1417-1418).
(b) The Python point is weak as a new departure from PACKAGING_DESIGN.md:52 (conda-build's rule that a post-link uses only rm, cp, mv and ln).
- The appendix never claims that rule still holds.
- The channel's hooks already break it without argument:
  - component post-links run `isabelle components`, a Scala tool (RELEASE_CHECKLIST.md §4, :250-268);
  - the isabelle pre-unlink runs `isabelle getenv` (recipe.yaml:225).
- The isabelle post-link has called python through the hook fragment since ruling 13.
- What ruling 26 adds is a declared python run dependency. That needs a clause saying it is there, not a separate argued paragraph.
(c) The "patches in place" half depends on how one reads the principle. §9's "原地 patch 用户自己的 Isabelle" (PACKAGING_DESIGN.md:1010-1016) means a self-installed Isabelle, and the appendix's boundary bullet (plan:935) keeps that true. The untracked-files clause, though, is contradicted on any reading.

RELAXATION: It removes the direct patching but not the contradiction. Suppose C3 dropped the hook fragment from the isabelle post-link. The re-run would still run every feature post-link (feature packages depend on isabelle, ruling 22), and each of those does a whole-chain apply. It would also still run the component post-links, which write the untracked etc/components. So the isabelle post-link would still cause in-place patching and untracked writes, and sentence 1 must be narrowed whatever happens to C3. The relaxation is right that the re-run is what needs arguing.

Severity: minor. Ruling 14 asks for this text to be argued in detail, and it will be copied into PACKAGING_DESIGN.md. Ruling 17 hands the wording to the author.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C22/. Nothing in any repository was modified.

1. I read plan:915-947 (Appendix A), decision 9 (plan:430-488), decision 12 (plan:553-579) and §10 (plan:858-912). I compared the opening sentence across PLAN.rev2.md:466, PLAN.rev3.md:724 and rev 4: the same sentence has been there since rev 2.
2. I read REVIEW2:1310-1430 (round-2 C9: the statement, the defender's reply and the judge's ruling) and REVIEW3:2154-2240 (round-3 C16). I also grepped all three review files for the earlier history of this sentence.
3. I read the sources:
   - PACKAGING_DESIGN.md:40-53 (§3.1, conda-build's rules at :52) and :999-1021 (§9);
   - isabelle-packaging-ci conda/recipe.yaml:1-60, :95-250 (the post-link is message-only, :182-183; the pre-unlink does `rm -rf` on the user directory, :223-231; "No requirements" at :235-237);
   - RELEASE_CHECKLIST.md:250-268;
   - conda core/link.py:925-1000 (all link actions, then entry points, then post-links run one by one);
   - Isabelle2025-2 components.scala:294 (etc/components lives under $ISABELLE_HOME_USER).
4. Toy conda run. I copied the round-4 critic's toy-channel generator (rev-4 hook fragment copied word for word), added probe lines to my copy (src/mkchan4.py) and wrote run.sh. The run could not finish because /tmp (a 24 GB tmpfs) filled to 100% from other agents' work. run.out shows ENOSPC and solver errors. I deleted my cache copies so as not to make the shortage worse.
5. I fell back to read-only inspection of the critic's existing toy run, review-ipc4/critic-conda/run1.out and run1.oxUb/envs/A:
   - Scenario A (fresh create): the hook log shows `HOOK post-link PKG_NAME=isabelle` running first, and conda's output then has "applied: feat_a feat_b dev_patches". So the isabelle post-link applied the whole chain and created isa/src/new_c.ML. RERUN-SCAN found records=0, because conda writes its package records only after the post-links.
   - A read-only grep of envs/A/conda-meta/*.json: no record lists isa/src/new_c.ML. Only share/.../dev_patches/src-new_c.ML.patch is tracked.
   - Scenario B (`--force-reinstall isabelle`): RERUN-SCAN found isabelle-comp, isabelle-feat-a, isabelle-feat-b and isabelle-dev-patches. So the isabelle post-link re-ran both the feature post-links and the component post-link, and the component registrations reappeared under $HOME/.isabelle/..., outside PREFIX.

Recommended fix: Smallest fix: hand-edit Appendix A, then add one row to §10.

(1) Plan:921-922: narrow the first sentence to what the package contains, and say its post-link is part of the exception. Suggested wording: "§3.1 的'一切随包装进去'仍然是 `isabelle` 包内容的原则：它从此是原版构建，不带任何补丁；它的 post-link 则参与下面这条例外。" Drop the claim that "post-link 不生成 conda 不跟踪的东西、不原地 patch" are still the isabelle package's own principles.

(2) Plan:924: turn the parenthetical into one argued sentence that covers four points:
- Why the re-run is needed: the isabelle pre-unlink deletes the environment's whole Isabelle user directory, etc/components included. conda runs only the hooks of packages the transaction changes, so after `--force-reinstall isabelle` or a build upgrade, only the isabelle package's own post-link can restore the features and the component registrations.
- The scan is written in Python, which is why the isabelle package depends on python (ruling 26).
- This is the same departure from conda-build's rules (PACKAGING_DESIGN.md:52) that the channel's component hooks already make (RELEASE_CHECKLIST.md §4).
- Keep the existing cost bullet at plan:944-945 (the post-links of packages that depend on isabelle must be safe to run more than once).
This wording holds whether or not C3 removes the hook fragment from the isabelle post-link. Either way, the re-run makes that post-link indirectly patch $PREFIX/isa and write the untracked etc/components.

(3) Optional, same root cause: decision 12 point 4 (plan:568-570) should also list two recipe.yaml passages that become false under ruling 26 and decision 12 point 2, so the CI plan rewrites them:
- recipe.yaml:182-183 ("message-ONLY … does not violate §3.1");
- recipe.yaml:235-237 ("No requirements at all — correct").

(4) §10: add a row "第二轮遗留：C9 (2) 附录 A 首句自相矛盾" that points to the edit in (1).

No owner decision is needed: rulings 14 and 17 leave this wording to the author.

**Judge: partially_confirmed → author_fixes_no_rereview.** Appendix A, plan:921-922: narrow the first sentence to the package's content. The isabelle package ships pristine sources, and its post-link takes part in the exception; drop the claim that 'post-link 不生成 conda 不跟踪的东西、不原地 patch' still holds for it.

plan:924: turn the parenthesis into one argued sentence covering four points:
- the isabelle pre-unlink deletes the whole user directory (recipe.yaml:223-231);
- conda runs only the hooks of packages the transaction changes, so only the isabelle post-link can restore features and registrations after --force-reinstall isabelle or a build upgrade;
- the re-run is written in Python, hence the python dependency;
- this departs from PACKAGING_DESIGN.md:52 in the same way the component hooks already do.

Keep the cost bullet at plan:944-945, as reworded by C4.

Add a §10 row for the round-2 C9 (2) leftover (REVIEW2:1331, :1408, :1425). This wording holds with or without C3's relaxation.

### C23 [minor] Stale or wrong facts: a false RELEASE_CHECKLIST citation, §2.3's 'update --all runs only isabelle's hooks', a difference list that omits the four .la files decision 12.1's hard assertion depends on, and a README that does not exist

Section: §2.3 (plan:195, :217-218, :229-230); decision 12 points 1 and 8  ·  merged from: consistency-CONS4-10, landing-L9

**Statement.** (1) plan:229-230 says that reporting through .messages.txt is 'RELEASE_CHECKLIST.md:259 的要求'. Line 259 actually reads 'Every hook ends exit 0. A nonzero post-link rolls the whole install back', and RELEASE_CHECKLIST.md never mentions .messages.txt (grep finds no match).
(2) plan:217-218 says that `conda update --all` and `--force-reinstall isabelle` run only isabelle's own hooks. Under ruling 22, an update to a new isabelle build relinks every feature package (plan:91-92; §6 (h), plan:799).
(3) §2.3 lists only lib/browser_info.db and src/Tools/Find_Facts/lib/isabelle.db as missing from the package (plan:195). The official tarball also contains contrib/polyml-5.9.2-2/{x86_64_32-linux,x86_64-linux}/{libpolyml,libpolymain}.la (`tar -tzf ~/isa_release_proto/Isabelle2025-2_linux.tar.gz`), which pkgs/isabelle-2025.2-0 lacks (find returns 0 files). The round-3 judge already noted this (REVIEW3:2202, :2224). Appendix A's list may be non-exhaustive, but decision 12 point 1 requires a hard CI assertion that the tree equals the tarball except for §2.3's differences (plan:555-556). With §2.3's list as written, that assertion would fail.
(4) Decision 12 point 8 assigns a sentence to the 'isabelle-packaging-ci README' (plan:575), but that repository has no README (`git ls-files` lists none).

Fix. (1) Say that the .messages.txt channel is this plan's own choice, with no checklist citation. (2) Limit plan:217-218 to component packages, and note that feature packages relink with every isabelle build. (3) Add the .la files to §2.3, and have decision 12 point 1's assertion compare against a list that the CI plan maintains and that names each failure, not against §2.3's prose. (4) Point decision 12 point 8 at RELEASE.md or PACKAGING_DESIGN.md, or say that the README is to be created.

**Editor.** 

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute each of the four parts from the sources and by experiment. All four hold. None of them breaks the design, so "minor" is the right severity. Part (1) is also a round-3 defect that survived and that §10 does not name, and it is wider than C23 says.

(1) CONFIRMED, and it is a round-3 residue. plan:229-230 says that reporting through `.messages.txt` "是 `RELEASE_CHECKLIST.md:259` 的要求" (is what RELEASE_CHECKLIST.md:259 requires). In fact RELEASE_CHECKLIST.md:259 reads only "Every hook ends `exit 0`. A nonzero post-link rolls the whole install back." `grep -i messages RELEASE_CHECKLIST.md` finds nothing, and the file's history has no such text either (`git log -S.messages.txt`). The Chinese sentence has one grammatical subject, "经 .messages.txt 说话" (reporting through .messages.txt), so it cannot be read as being about exit 0. Round 3 confirmed exactly this citation error (REVIEW3:3480). Its judge action (REVIEW3:3570) also required decision 9 to present the `>> .messages.txt` redirect as this plan's own improvement and to say what the `.bat` does on failure. Rev 4 still calls that line "`RELEASE_CHECKLIST.md` §4 的登记行" (§4's registration line, plan:463-465). For Windows it only says "照 Isabelle_RPC/conda/recipe.yaml:165-176" (as Isabelle_RPC does), and that `.bat` is silent: `>nul 2>&1`, no echo (Isabelle_RPC recipe.yaml:173-175). Yet §10's C29 row (plan:906) presents C29 as done. That is a silent deviation.

(2) CONFIRMED. plan:217-218 says that `conda update --all` and `--force-reinstall isabelle` run only isabelle's own hooks. conda runs hooks for exactly the packages that the transaction changes (`core/solve.py:1417-1418`). Under ruling 22, `update --all` to a new isabelle build also swaps every feature package. The plan says so itself: plan:91-92, plan:223 ("配套重发后 conda update --all 一起升"), and §6 (h) at plan:799. Measured on a toy channel:
- `conda update --all` ran the post-links of `isa` and of the exactly pinned feature, but not of the unpinned component.
- `conda update isa` alone did nothing ("All requested packages already installed").
- `--force-reinstall isa` ran only `isa`'s hook.
So the sentence is right for `--force-reinstall` and for components, and wrong for `update --all` in an environment with feature packages.

I checked whether the false sentence hides a design error. It does not. During `update --all`, `isa`'s post-link sees `conda-meta/` holding only the component and tool records. The feature's old record is already gone and its new one is not yet written. So ruling 26's re-run reaches the components, and conda runs the feature's own post-link anyway.

(3) CONFIRMED, with the cause found. `tar -tzf` on the official tarball lists contrib/polyml-5.9.2-2/{x86_64_32-linux,x86_64-linux}/{libpolyml,libpolymain}.la. `find pkgs/isabelle-2025.2-0 -name '*.la'` returns 0 files. Nothing in isabelle-packaging-ci mentions `.la` files. The cause is rattler-build itself: a toy recipe built with rattler-build 0.69.1 shipped the `.a` file and `browser_info.db` but silently dropped the `.la` file. build.yml:902 installs the latest rattler-build. So the pristine build will lack these four files too, and on other platforms probably the `.la` files of their own Poly/ML builds.

The round-3 judge recorded these four files (REVIEW3:2185, :2202, :2224). Appendix A is explicitly non-exhaustive, so it is fine. But decision 12.1 (plan:555-556) makes a hard assertion whose exceptions are "§2.3 列的差别" (the differences §2.3 lists), and §2.3 (plan:195) names only the two database files. Run on the packaged tree, the assertion would fail on linux-64. 12.1 also does not say which tree is checked. Before rattler-build runs, the `.la` files are still present; after it, they are gone. That is a further reason for the CI plan to own the list.

(4) CONFIRMED. isabelle-packaging-ci has no README: neither `git ls-files` nor `git ls-tree` of origin/main and sg-home/main lists one, and none is on disk. Its top-level documents are RELEASE.md, RELEASE_CHECKLIST.md, PACKAGING_DESIGN.md, COMPONENTS_DESIGN.md and ROLLOUT_STATUS.md. The isabelle-base-features README is created by decision 13, so naming it is fine.

Editor relaxation: there is none. On the fixes C23 proposes: (1)-(3) are right. For (4), RELEASE.md and PACKAGING_DESIGN.md are maintainer documents, not release notes for users. Saying "to be created", or pointing at a user-facing text, fits better.

Experiment: All experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C23/. They used a private HOME, CONDARC and CONDA_PKGS_DIRS, and modified nothing in any repository.

(a) Grepped RELEASE_CHECKLIST.md, PACKAGING_DESIGN.md, the isabelle recipe and pack.sh for "messages". There is no match in the checklist. Read RELEASE_CHECKLIST.md:250-268 and `git log -S'.messages.txt'`. Read REVIEW3:3462-3575 (round-3 C29) and plan:463-465 and :906.

(b) Built a toy channel with mk.py: a toy `isa` package (builds 1 and 2), a feature `feata` pinned exactly to `isa 1.0 1` and then `isa 1.0 2`, an unpinned component `comp` (`isa >=1.0,<2`), and a tool `ipc`. Every post-link appends to hooklog-<env>.
- `conda update --all`: log shows "post-link isa 1.0 2" and "post-link feata 1 1"; `comp` did not run (update-all.out).
- `conda update isa`: "All requested packages already installed", no hooks.
- `--force-reinstall isa`: only "post-link isa 1.0 1".
- mk2.py variant: `isa`'s post-link lists conda-meta/*.json. At create time the list is empty. During update --all it is "comp-1.0-0.json ipc-1.0-0.json".

(c) `tar -tzf ~/isa_release_proto/Isabelle2025-2_linux.tar.gz` (tarball.list) shows four `libpoly*.la` files. `find ~/miniconda3/pkgs/isabelle-2025.2-0 -name '*.la'` finds 0. `grep '\.la'` over the CI repo's scripts, recipe, build.yml and docs finds nothing.

(d) rb/: a toy recipe built with /var/tmp/claude-reverify-pkg/rattler-build (0.69.1) wrote `libpolyml.la`, `libpolyml.a` and `browser_info.db`. The resulting .conda holds only the `.a` and the `.db` ("2 content" files). build.yml:902 downloads rattler-build "latest".

(e) In isabelle-packaging-ci, `git ls-files` and `git ls-tree -r origin/main` / `sg-home/main` list no README.

Recommended fix: Hand edits only.

1. plan:229-230: write "经 `.messages.txt` 说话是本计划的做法（`RELEASE_CHECKLIST.md:259` 只要求 exit 0），不是它们今天的行为".
   At plan:463-465, do what round-3 C29's judge asked: call the line "§4 的登记行，另把失败警告追加进 `$PREFIX/.messages.txt`（本计划的改进）", and say what light's `.bat` registration line does on failure. Either it also appends to `.messages.txt`, or it stays silent like Isabelle_RPC's (`>nul 2>&1`).
   Name both changes in §10's C29 row.

2. plan:217-218: say that `--force-reinstall isabelle` runs only isabelle's hooks, and that under libmamba a bare `conda update isabelle` does not move. Say that `conda update --all` to a new isabelle build swaps every feature package with it and runs their hooks (ruling 22, plan:223), while the post-links of component packages, which are not in the transaction, do not run. Keep plan:201-202's conclusion, which is about components.

3. plan:195: add the four `contrib/polyml-5.9.2-2/*/libpoly{ml,main}.la` files, with the cause: rattler-build drops `*.la` files when it packages (measured with 0.69.1). Other platforms' bundles may have `.la` files of their own.
   Decision 12.1 (plan:555-556): say that the assertion checks the tree as packaged, and that its exact per-platform exception list is kept by the CI plan next to the assertion, starting from §2.3's list. The assertion should name every unexpected file.

4. plan:575: either write "isabelle-packaging-ci 新建的 README", or drop that target. The new isabelle package's description already carries the note, and the channel banner (`conda/channel-banner.html`) is the other user-facing text. RELEASE.md and PACKAGING_DESIGN.md are maintainer documents, not release notes.

**Judge: confirmed → author_fixes_no_rereview.** (1) plan:229-230: say that reporting through .messages.txt is this plan's own choice. RELEASE_CHECKLIST.md:259 requires only exit 0, and the file never mentions .messages.txt. At plan:463-465, do the round-3 C29 judge action (REVIEW3:3570): present the redirect as this plan's improvement, and say what light's .bat registration line does on failure. Name both in §10's C29 row.

(2) plan:217-218: --force-reinstall isabelle runs only isabelle's hooks. update --all to a new isabelle build also swaps and runs every feature package (ruling 22), but not the component packages (review-ipc4/defender-C23 update-all.out).

(3) plan:195: add the four contrib/polyml-5.9.2-2/*/libpoly{ml,main}.la files, with the cause: rattler-build drops *.la files (measured with 0.69.1, defender-C23/rb/). Decision 12 point 1 (plan:555-556) checks the tree as packaged, against a per-platform exception list the CI plan keeps next to the assertion, which names each unexpected file.

(4) plan:575: isabelle-packaging-ci has no README. Either say it is to be created, or drop that target; RELEASE.md and PACKAGING_DESIGN.md are maintainer documents.

### C24 [minor] §8 still cites a stale engine timing, and the win-64 cost of about 128 git process starts per hook, times one hook per feature, is measured and bounded nowhere

Section: §8 (plan:839); decision 5 (plan:374); decision 15 Windows leg (plan:659-661); §6  ·  merged from: engine-engine-7, consistency-CONS4-10

**Statement.** §8 still says that a per-file level replay on the real chain takes 1.3-2.3 s per `status` (plan:839). Round 3 measured 0.16-0.25 s and called the figure stale, because it came from round 2's prototype, which ran a check plus an apply for every step (REVIEW3:176). Decision 5 itself now says 0.2-0.3 s (plan:374).

As specified, one command on today's chain makes about 128 git process starts: 42 listing calls, 1 version probe and about 85 replays. On Linux that takes 0.17-0.19 s (review-ipc4/critic-engine/real.out). Every hook replays the whole chain. A fresh create with seven feature packages therefore runs seven or eight whole-chain replays. `--force-reinstall isabelle` runs one per installed feature (ruling 26), and `conda update --all` to a new isabelle build adds one pre-unlink per feature. On win-64, every git.exe start goes through the PortableGit/MSYS2 runtime (plan:233-236). Neither decision 15's Windows checks (plan:659-661) nor §6 measure or bound the time this takes.

Fix. Correct §8. Add a timing measurement on the win-64 leg for `status` and for `--force-reinstall isabelle` with the full chain, and state a bound in §6. If the measurement is too slow, batch the listing step: one `git apply --numstat --summary` call over all patch files of a feature directory, checking each listed target against its patch file's flat name.

**Editor.** engine-7's phrase 'each is about 1,000 git processes' is a mis-statement. A replay is about 128 starts; about 1,000 is the total for an eight-hook transaction. The severity is low until the measurement exists.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each part of the challenge against the plan text, the conda source, and my own measurements. The substance survives. The challenge is wrong on one fact: why git is slow to start on win-64.

CONFIRMED (1): §8 has a stale timing figure, and decision 5's figure has no source.
- plan:10 says the plan's facts are sourced in §8 ("事实出处见 §8").
- §8's round-2 bullet still records "1.3–2.3 秒" per status (plan:836-839).
- Decision 5 says a run holds the lock for "0.2–0.3 秒，评审实测" (plan:374).
- §8's round-3 bullet (plan:840-847) does not record that measurement, so the only timing in §8 contradicts decision 5.
- The old figure comes from round 2's prototype. It ran --check and then apply on every step, for every candidate level (review-ipc2/critic-engine/e5/levels.py: `ga(...check=True)` and then `ga(...)`). REVIEW3:176 already called the figure stale.
- §10 says nothing about it. Mitigation: REVIEW3:176 is a critic's note, not a numbered round-3 challenge, so this is not a "confirmed defect that survived". It is still a live inconsistency.
- My re-run of the round-4 critic's prototype on a private copy took 0.32-0.43 s with 127-128 git starts (42 listing calls, 1 version probe, the rest replays) at load average 3-6 (defender-C24/timing.out). The 0.2-0.3 s figure depends on load and was measured on Linux only, but the plan states it for every platform.

CONFIRMED (2): hooks replay the whole chain many times per transaction.
- Every hook replays the whole chain: post-link does a whole-chain apply, and pre-unlink runs `unapply --feature F`, which computes every file's level (plan:470-473; decisions 6-7).
- conda writes the conda-meta records only after the post-links (link.py:965 runs the post-links; :972 the record actions come after). So in a fresh create, ruling 26's scan of conda-meta finds nothing. A fresh create with seven features therefore runs 1+7 = 8 whole-chain replays.
- `--force-reinstall isabelle` runs 1 replay, plus 7 more because ruling 26 re-runs each feature's post-link: 8 in all.
- `conda update --all` to a new isabelle build runs 7 pre-unlinks, 1 replay for isabelle's post-link and 7 feature post-links: 15. The old feature records are unregistered before the link side runs (link.py:997), so isabelle's scan re-runs only component packages.
- So a transaction costs about 1,000-1,900 git starts. The editor's rebuttal (about 128 per replay) is right.
- No timing is measured or bounded on win-64. Decision 15's Windows checks (plan:659-661) and §6 (plan:782-803) contain no time measurement or bound. A search of the plan for 超时/时间/耗时 finds only the 60 s lock wait and the heap-job timeouts.

REFUTED (the reason given for the win-64 cost):
- The challenge says every git.exe start "goes through the PortableGit/MSYS2 runtime". That is false.
- I downloaded PortableGit-2.56.0-64-bit.7z.exe. Its sha256 eceb5e06… matches the feedstock's meta.yaml. I inspected it without running it (defender-C24/wrapper.out).
- `bin/git.exe` is the file the tool calls (plan:349: Library/bin/git.exe). It is a 29,696-byte redirector. Its strings show `UCRT64\bin`, `CreateProcessW` and `WaitForSingleObject`: it starts `ucrt64/bin/git.exe` (4.4 MB) and waits for it.
- The real git.exe imports only Windows and UCRT DLLs plus libiconv, libintl, libpcre2 and zlib1. It does not load msys-2.0.dll.
- The real cost on win-64 is therefore two native process creations per `_git` call (the redirector and the real git), on an OS where creating a process is much slower than on Linux. On Linux a bare git start costs about 1.25 ms (128 `git --version` in 0.16 s). I could not measure Windows here, so the cost there is still unknown. That is exactly the gap.

SEVERITY: minor, as the challenge says. Nothing is shown to be broken. What is missing is a measurement, and a bound for decision 5's own argument: decision 5 accepts that environments sharing the etc/ISABELLE_ID inode run one at a time because a run is short compared with the 60 s lock wait. That reasoning has not been checked on win-64.

Experiment: All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc4/defender-C24/.

(1) I copied review-ipc4/critic-engine/{ipc4.py, real/base, real/features.d} (today's 4-feature chain, 42 patch files) and ran status, apply and `unapply --feature light_locale`. Each run made 127-128 git starts (42 listing, 1 version, the rest replays) and took 0.32-0.43 s (timing.out, load average 3.4-6.3). 128 bare `git --version` took 0.16 s and 128 /bin/true took 0.10 s.

(2) I read review-ipc2/critic-engine/e5/levels.py. It does a --check plus an apply for every step, which explains where round 2's 1.3-2.3 s came from.

(3) I read conda 25.11.1 core/link.py:925-1000: the post-links run at :965, the conda-meta records are written afterwards at :972, and the unregister actions run at :997. From this I derived the replays per transaction: fresh create 8, `--force-reinstall isabelle` 8, `update --all` to a new build 15.

(4) I downloaded PortableGit-2.56.0-64-bit.7z.exe into its own directory (pg-dl/; sha256 eceb5e06… matches the conda-forge feedstock meta.yaml) and inspected it with 7z, strings and objdump without running it. bin/git.exe and cmd/git.exe are each 29,696 bytes. bin/git.exe's strings include UCRT64\bin, CreateProcessW and WaitForSingleObject. ucrt64/bin/git.exe (4,398,592 bytes) imports Windows/UCRT DLLs plus libiconv-2, libintl-8, libpcre2-8-0 and zlib1, and no msys-2.0.dll (wrapper.out).

(5) I checked that the challenge's fallback works. One `git apply --numstat --summary` over all 42 patch files gives rc 0 and 42 numstat lines in argument order, including the two paths touched by two features (attrib.ML, syntax_phases.ML) (batch.out). A create/delete/create toy on one path also lists 3 lines with rc 0 (batch/).

I did not measure on Windows; no Windows host was available.

Recommended fix: The smallest fix, in three parts, all wording and tests (ruling 17):

(a) Fix the timing figures in §8 and decision 5.
- In §8's round-2 bullet (plan:839), mark 1.3–2.3 s as coming from round 2's prototype, which ran --check plus apply on every step.
- In the round-3/4 bullets, add the current figures: 126-128 git starts per run on the 4-feature chain; 0.16-0.25 s (REVIEW3:176), 0.17-0.32 s (review-ipc3/defender-C22/timing.out), 0.17-0.19 s (review-ipc4/critic-engine/real.out) and 0.32-0.43 s under load (review-ipc4/defender-C24/timing.out).
- Change decision 5's "0.2–0.3 秒" (plan:374) to say it is a Linux figure, and cite §8.

(b) Measure on win-64 and state a bound.
- Add to decision 15's Windows checks (plan:659-661): the wall time of one whole-chain `status`, and of `conda install --force-reinstall isabelle`, on the full seven-feature chain. Record the results in §8.
- In §6, state the bound that decision 5's argument already needs: on every leg, one run holds the lock far below the 60 s wait. A concrete number such as ≤10 s is the author's call.
- Correct the reason for the win-64 cost wherever it is stated: Library\bin\git.exe is a redirector that starts Library\ucrt64\bin\git.exe, so each `_git` call costs two native process creations. MSYS2 is not involved.
- Do not bypass the redirector. The inner path changed from mingw64 to ucrt64, and conda-forge tests only bin\git.exe.

(c) Only if the measurement breaks the bound: batch decision 3's listing.
- Use one `git apply --numstat --summary` over all patch files of the chain. Require exactly one numstat line per file, in argument order.
- On a line-count mismatch or a nonzero rc, fall back to the current per-file call to name the bad file. This removes 41 of the 128 starts and keeps decision 3's diagnostics.
- Leave the replays as they are: ruling 24 fixes replay as the only source of state.

**Judge: partially_confirmed → author_fixes_no_rereview.** Correct §8 (plan:839): 1.3-2.3 s came from round 2's prototype, which ran --check plus apply on every step. Add the current figures:
- 126-128 git starts per run;
- 0.16-0.25 s (REVIEW3:176);
- 0.17-0.32 s (review-ipc3/defender-C22/timing.out);
- 0.17-0.19 s (review-ipc4/critic-engine/real.out);
- 0.32-0.43 s under load (review-ipc4/defender-C24/timing.out).
Decision 5 (plan:374) says its figure is a Linux measurement.

Decision 15's Windows checks (plan:659-661) measure the wall time of a whole-chain status and of `--force-reinstall isabelle` on the full chain, and record the results in §8. §6 states the bound decision 5's argument needs: one run holds the lock far below the 60 s wait; the number is the author's call.

Correct the stated reason for the win-64 cost. Library\bin\git.exe is a redirector that starts ucrt64\bin\git.exe, which loads no msys-2.0.dll (defender-C24/wrapper.out). So each call costs two native process creations; MSYS2 is not involved. Do not bypass the redirector.

Only if the bound is broken: batch the listing step into one `git apply --numstat --summary` call over all patch files, with a per-file fallback that names the bad file (defender-C24/batch.out).
