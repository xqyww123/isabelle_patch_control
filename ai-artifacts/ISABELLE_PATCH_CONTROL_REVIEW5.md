# isabelle_patch_control plan rev 5 — review 5, targeted re-review (workflow wf_573a4702-2df, 2026-10-24)

Scope: decisions 9, 11, 12, 16 and every §10 row, as the round-4 judge asked. Critics: 33 findings (3 lenses: consistency, hooks, release). Merge editor: 11 challenges, 6 dropped. One fresh defender per challenge. Judge: ready = True.

## Judge summary

Verdict: rev 5 is ready for the owner's approval once the author applies the actions below. No further review round is needed.

Every remaining item is wording, a test, or a small correction to a mechanism whose exact shape this judgement now fixes and a defender has prototyped. The four mechanism corrections are:
- C2, the reuse rule in plan_builds;
- C5, which feature-repository commit is released and the path list it commits;
- C6, a level function that works on one file;
- C9, one output of the build job.

Two owner questions remain. Neither changes the design, so the owner can answer them at approval time:
- the wording of the re-run contract (C11);
- whether the strong release gate may refuse one more kind of release than ruling 28 names (C4 item 5).

Verdicts: 7 confirmed (C1, C3, C5, C6, C8, C9, C11) and 4 partially confirmed (C2, C4, C7, C10). The core of every challenge holds; the partial ones carry overstated side claims. I checked the following myself:
- conda runs every pre-unlink before any unlink, and a script's environment carries only ROOT_PREFIX, PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM (core/link.py:938-947, :1630-1634). So a pre-unlink cannot tell a removal from a replacement.
- The guard in publish-conda.yml (:147-191) refuses a file whose name is already on the channel with different bytes, and the upload step (:193-203) runs before the re-index (:205-221).
- Plan lines 37, 39, 128, 674, 713, 881, 896, 939, 989 and 1032 still hold the stale text the challenges quote.
- The plan has 10 rows marked 【订正】, not 8.
- The rev-4 archive was modified at 16:30, after REVIEW4.md (16:14), and contains §0 items 33-35.
- The cited lines in Performant_Isabelle_ML, auto_sledgehammer and Isabelle_RPC are correct.
- `git commit -- patches/R/` also commits unstaged edits to tracked files under patches/R/, and leaves README.md, staged outside that directory, uncommitted (judge/c5).
- Rev 5's new citations into the CI repository and Semantic_Embedding are accurate. One exception: isabelle-minilang is at Isa-Mini recipe.yaml:52, and plan:260 calls the package minilang.

The three new rulings:
- Ruling 33 (the isabelle package's post-link carries no copy of the hook fragment) is implemented everywhere except the authoritative glossary entry at plan:37 (C3).
- Ruling 34 (the re-run covers only packages whose depends name isabelle directly) is implemented consistently. Only the wording of the contract is flawed, and that wording comes from the round-4 judge (C11).
- Ruling 35 (the tested record captures the state of each -d repository) is in decision 16, §5 and migration item 32. Missing:
  - pointers from the migration plan's glossary entry, its run-tree description and the gate (e) text;
  - acceptance tests;
  - a definition of 'the commit to be released' (C5, C10).

The largest recurring defect is §10.1 again: for the third round in a row it contains untrue rows. The fix is structural: one line per judge action (relaxation 4).

The pre-unlink texts (C1) must be right in the first published batch. Each published build's text is permanent, and it runs when that build leaves an environment, most often during `conda update --all`, which is a replacement.

Scratch evidence from this judgement is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/judge/. /tmp has only about 380 MB free, so I ran no new conda transactions; the conda behaviour above rests on the source reading and on the defenders' toy channels.

## Questions for the owner

Question 1 (C11): may the wording of the re-run contract change? Background: under rulings 26 and 34, whenever the isabelle package is linked again (an update to a new build, or `conda install --force-reinstall isabelle`), its post-link re-runs the post-link of every installed package whose depends name isabelle directly. Ruling 34's record, decision 12 point 7, the planned RELEASE_CHECKLIST §4 rule and Appendix A state what such packages must do: '直接依赖者的 post-link 在自己的文件没变时重跑必须无效果' (re-run while its own files are unchanged, it must have no effect). The problem: the re-run exists precisely to have an effect while those files are unchanged. isabelle's pre-unlink has just deleted the Isabelle user directory and every component registration in it, and the re-run must write them back. Measured on a toy channel: a component package that obeys the sentence literally (it skips when its files are unchanged) lost its registration after `--force-reinstall isabelle`. Read the other way, as 'running it twice in a row changes nothing', the sentence admits isabelle-semantic-data's purge, which is idempotent in that sense yet deletes the stand-in vectors the user created since. The design does not change under any answer; only the rule that future package authors read does. (a) Recommended: replace the sentence with '直接依赖 isabelle 的包的 post-link 必须能在任何时候重跑：重跑只把它自己装包时建立的东西（组件登记、补丁）恢复回来，除此之外什么都不改' (it may be re-run at any time; a re-run only restores what the package's own installation set up, and changes nothing else). (b) Keep the sentence and add the clarification after it as an explanation. (c) Keep it as it is.

Question 2 (C4 item 5): may make-patches' release gate refuse one more kind of release than your ruling 28 names? Background: ruling 28 refuses a release in which an upper feature undoes a lower feature's change, that is, a changed file's content at the release commit equals its content at the chain bottom or at a lower release tag. Rev 5 makes a stronger check mandatory, as the round-4 review required. For every file the new feature changes, the file's content at the chain bottom, at every lower release tag and at the release commit must each fit exactly one level of the chain. This also refuses a release that undoes nothing but whose patch context happens to match two levels at once. A three-feature toy of this shape passed every weaker check, and users of that chain then saw CONFLICT (review-ipc4/defender-C5/harness.out). The refusal message says the change's context is ambiguous and must be reworked. (a) Recommended: accept the stronger gate. It is the only check that makes decision 6's promise true: a released chain never contains a file that fits several levels. (b) Refuse only ruling 28's case, release the ambiguous case with a warning, and weaken decision 6's promise accordingly.

## Relaxations recommended

1. C1: use one rule for every pre-unlink text. A pre-unlink cannot tell a removal from a replacement (core/link.py:938-947, :1630-1634). So every recovery step, the sentence 'status will not see them' and the heap line 'the tree is back at the shipped sources' stand under 'If this command removes <feature>:', and every pre-unlink text also carries 'If it replaces <feature>: when it finishes, run isabelle-patch-control status'. The residue block, both || texts and the heap line then follow the same rule. For a replacement, the question of which block to follow never comes up.

2. C2: use one rule for every package the batch publishes, the tool included: a file the channel already serves is reused when it is what the batch wants (the same tool version, or a feature whose depends pin the wanted isabelle build), and a feature file is skipped only when it is not. A new dispatch then always resumes byte for byte, so the recovery text no longer depends on re-running a failed job or on artifact retention.

3. C6: replace the public levels(tree, features_dir) with a function that computes the levels of one file from its content and the patch blocks that touch it. status and make-patches' gate then share exactly decision 6's code, and the gate needs no synthesized tree, features.d or provenance.

4. C4: restate §10.1 as one line per judge action, each marked 'done at plan:N' or '偏离：reason'. A silent omission then becomes visible to the owner, which free-text rows have failed to do for three rounds.

5. C8: the smoke job reads its install command from the unified README text file that the renderer copies, so the documented command and the tested command cannot drift apart.

6. C9: replace the build job's boolean isabelle_rebuild with an output isabelle_old_build, the old build string, empty meaning skip. §6 (h) then has a defined starting state, and one output replaces the boolean.

7. C5: make-patches uses one per-file path list for staging, for the 'is there anything to commit' check and for the commit itself, and write step (d) checks the commit that is actually tagged. A new commit and an existing tag then pass the same test.

## Critics' overall notes

- hooks: The plan applies rulings 33 and 34 consistently in decisions 1, 9, 11, 12, 15, section 4, section 6 and Appendix A. The one exception is the glossary (H2). The review found eight defects: two major, five minor and one nitpick.

**What I tested.** I built a toy channel with conda 25.11.1, using a private HOME, CONDARC and pkgs directory, and a small local forge channel copied from the round-4 cache.
- The hook fragment and the pre-unlink are copied verbatim from plan:487-492 and :515-517.
- The isabelle builds 1 and 2 depend on python. Their post-link is the existing hint, then a re-run of the direct dependents only, then exit 0, with no fragment.
- The toy tool follows rev 5's message rules.
- There is a direct component package and an indirect-only package whose post-link counts its runs.
- The three feature packages carry exact pins: feat_a, feat_b and dev_patches, whose package name is qiyuan-dev-patches. dev_patches creates a file and has a component payload.

**What holds (measured, run1.out):**
- The re-run finds exactly the installed packages that are not in the current command.
- `--force-reinstall isabelle` restores the patches and all component registrations, and the indirect package's run count stays at 1 (lines 16-27).
- Exactly one full diagnosis appears when isabelle or the chain-top package is relinked and the CONFLICT survives (lines 42 and 53). Relinking only a lower feature gives one-line notices only (line 64).
- One applied line and one heap paragraph appear per install.
- The verbatim .bat texts behave correctly under wine (bat/run.out):
  - exit codes 0, 1, 0xC0000135, 0xC0000005 and a missing python.exe;
  - prefixes with spaces and with ')';
  - tool absent, with and without a features.d directory;
  - the component lines run on every path, and the hook always exits 0.
- Decision 12 point 10 and the citations I checked are accurate: recipe.yaml:208, build.yml:1012/1203/1217/1286, release.yml:115, ci.yml:19-23, Semantic_Embedding recipe.yaml:318/:338, semantics.py:1567-1607, link.py:938-999, path_actions.py:1209-1219. All published component packages depend on isabelle directly.

**What does not hold:**
- **H1 (major).** In a replacement, which includes the README's own `conda update --all`, the residue block and the frozen `||` texts tell users to remove the feature packages they are keeping. This silently deviates from the round-4 judge's C11 action.
- **H2 (major).** The authoritative glossary still says the pristine build copies the hook fragment, contradicting ruling 33. Both the C3 and the C12 judge actions targeted that line.
- **H3 (minor).** Every update prints a false 'back at the shipped sources, delete heaps/' line just before the reapply paragraph. Decision 15's own transcript check cannot pass against this specified text.
- **H4 (minor).** The decision 12.7 contract, as worded, is violated by the very packages the re-run exists for.
- **H5 (minor).** The full-diagnosis rule does not say which kind of hook writes it, and the invariant says 换了 where it means 'links'.
- **H6 (minor).** Two parts of the C8 judge action are missing from the in-place-edit remedy texts.
- **H7 (minor).** Two user-facing conda commands still lack the channel flags that C17 required, one of them in frozen text.
- **H8 (nitpick).** Decision 12 point 5 keeps a stale '§5 第 6 步' that the C9 judge asked to change to step 8.

Experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-hooks/: the scripts mkchan5.py, toytool5.py, rerun5.py and mkforge.py under src/, the extracted hook texts under texts/, run1.out, run2.out and bat/run.out. No repository, Isabelle tree or owner environment was modified.

- release: Rev 5 carries out the round-4 judge actions in my lens (decisions 10, 11, 16, 17, §5, §6) closely, and the three new rulings are implemented consistently in decisions 11, 16, §5, §6 and Appendix A:
- the noarch-only feature-packages artifact with an assertion;
- the run-mode artifact merged only into the roundtrip and accept channels;
- an immediate failure when publish=true is combined with run mode;
- a roundtrip test on an installed environment, with --features-dir as the only feature input;
- the always-on linux-64 session build;
- one call to publish-conda.yml;
- a concurrency group;
- the documented behaviour of re-running failed jobs;
- the Isabelle release tag written last, with by-name staging;
- the strong gate made mandatory;
- §5 step 7's cross-repository rehearsal.
The line numbers I checked hold, in publish-conda.yml, build.yml, release.yml, Isabelle_RPC's release-conda.yml, RELEASE_CHECKLIST.md, sweep-old-versions.py, pack.sh, make-patches and the reference-transaction hook.

New defects, measured with toy channels and repositories in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/:
- One major. The HEAD probe the C2 judge required covers only feature packages. A new tool version stranded by a publish that uploaded but never indexed makes every later dispatch fail at the guard. That dispatch is exactly the recovery decision 11 prescribes for a publish-conda.yml bug, and §5 step 8's first batch is that case. A single 'download and reuse a served file that matches' rule for all packages fixes it, and is simpler.
- Minor ones:
  - Write step (d) of point 8 lets the tagged commit differ from what gates 7 and (e) checked: a stale existing tag, or another agent's staged changes swept in.
  - §6 (f) needs a cache-corrupting in-place edit, and (h) has no defined starting state.
  - The smoke job is not the README's command.
  - The strong gate's levels() inputs are unavailable to make-patches.
  - The migration plan's authoritative glossary was not amended for ruling 35.
  - Ruling 35 voids records on any change during the build, contrary to the plan's parenthetical.
  - Four §10.1 rows are silent about judge actions that were not done.
None of these requires reversing a ruling. One optional owner question remains (ruling 35's comparison during the build). After these targeted fixes, decisions 10, 11 and 16 look ready.

- consistency: Lens: §10 truthfulness and cross-section consistency in rev 5 (plan = contrib/my_better_isabelle_prover/ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md). I checked every round-4 'Judge:' paragraph (REVIEW4.md, C1-C24) against the rev-5 text, the 【订正】 rows of §10.2 against the archived rev 4 and REVIEW3, rulings 33-35 across all the places the task lists, and the newly cited lines (in the CI recipe, build.yml, release.yml, publish-conda.yml, RELEASE_CHECKLIST, PACKAGING_DESIGN, the Semantic_Embedding and semantic-data recipes, isabelle_semantics.py and semantics.py, the Performant_Isabelle_ML, auto_sledgehammer and Isabelle_RPC workflows and recipe, getfunctions:262, conda's link.py and path_actions.py, and make-patches and run-tree). I also checked the §8 round-4 evidence paths. All of those line citations and evidence files exist and say what the plan claims, except the 'minilang' package name (CONS-17e).

What holds:
- Rulings 33 and 34 are carried out correctly in decisions 1, 9, 11, 12.2 and 12.7, decision 15, §4, §6 (c) and (e), §7 row (1) and Appendix A. The one exception is the glossary entry 钩子片段 (hook fragment), which still says the isabelle package copies the fragment (CONS-1, major).
- Ruling 35 appears in decision 16.7, §5 step 2, the HOL-only example and migration §0 item 32. Its text, however, compares a light-repository commit with an Isabelle-repository commit without naming the light one, and the migration plan's glossary and gate (e) were never amended (CONS-11).
- These judge actions were carried out as asked: the C2 plan_builds function, the C6 noarch-only artifact and first-step failure, the C7 .bat texts, the C13 write order, the C14 check-roundtrip interface, the C15 check_bytes inputs, the C18 rule that the lock mode picks the replay directory, the C19 refusals, and C16, C20-C22.

What does not hold:
- §10 is untrue again in about ten places, against the header's promise (CONS-2, major). Silent or misstated partial fixes:
  - C8: the residue block still promises that reinstalling isabelle restores the package's files (CONS-3), and §9 contradicts decision 15 (CONS-9).
  - C9: a stale step number remains, and the row names the wrong location for the fix (CONS-5).
  - C11: the frozen pre-unlink text tells users who are replacing a feature to remove it again (CONS-7).
  - C12: four of the judge's spot edits were skipped, so ruling 28's record and §7 now misuse 链顶 (CONS-6).
  - C17: the smoke job does not run the README's command, and the release note lacks the channel flags (CONS-10).
  - C24: the §6 bound cited twice does not exist (CONS-4).
  - C5: the owner notification was replaced by the author's own reading (CONS-13).
  - Several smaller items (CONS-17).
- Defects newly introduced in decisions 9 and 16:
  - Residue blocks are not interchangeable on the CONFLICT branch (CONS-8).
  - The mandatory gate does not say where its inputs come from (CONS-14).
  - The release commit is not limited to patches/<R>/, measured on toy repositories (CONS-15).
  - Appendix A and decision 9 over-credit the isabelle re-run after a build upgrade (CONS-12).
- The archived rev-4 copy is not the text that was reviewed (CONS-16).

Every finding can be fixed in the text without changing any ruling or design decision. One owner question should be asked (CONS-13). After the fixes, one more check of each §10 row against its 'Judge:' paragraph is enough; no further critic round is needed. Experiments: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-consistency/commit and …/commit2. No repository or environment was modified.

## Dropped by the merge editor

- hooks-H2 (C12 attribution part): Wrong line. In the reviewed rev 4, the C12 judge's 'plan:37' is the batch release workflow entry of the glossary, not the hook fragment entry, which is rev 4's line 35 (…PLAN.rev4.md:35-37). The rest of hooks-H2 is merged into C3.

- consistency-CONS-6 (decision 11 roundtrip and decision 17 uses of 链顶): The C12 judge explicitly listed these uses (rev 4 :531, :685, :689) as correct unchanged (REVIEW4:1592). In both places 链顶 is the top of the chain of the environment or features.d under test, which fits the new definition.

- consistency-CONS-17 (c): The substance is already in the plan. §2.3 (plan:250-253) states that the .messages.txt redirect is this plan's own addition and that the .bat line is silent. The two Isabelle_RPC ranges, 165-176 and 168-174, each quote correctly what they cite.

- consistency-CONS-17 (e): Nitpick: 'minilang' at plan:260 should read isabelle-minilang (Isa-Mini/conda/recipe.yaml:51). This is a one-word fix the author can make in passing; it is mentioned in C4's rebuttal.

- consistency-CONS-17 (f): Nitpicks of wording: the C4 row's '记在 §9 外不展开' and the C1 row naming decision 12 point 10 for edits that are in point 4.

- hooks-H7 (plan:558-559 part): Decision 9's remedy list is design prose, not text the user sees. The user-facing residue block in §4 (plan:898) carries the channel flags under the convention at plan:856.

## Challenges

### C1 [major] Pre-unlink texts assume the package is being removed. In a replacement, including the README's `conda update --all`, the residue block, the frozen `||` texts and the 'back at the shipped sources' heap line all give wrong advice, and the `||` texts can never be corrected after the first release

Section: Decision 9 (pre-unlink texts plan:513-529; residue rule plan:547-551; heap line plan:561-563); §4 (heap line plan:865-867; residue block plan:889-899); decision 15 (plan:776-778, :783); §10.1 rows C11 (plan:1058) and C20 (plan:1067)  ·  merged from: hooks-H1, consistency-CONS-7, consistency-CONS-8, hooks-H3

**Statement.** The core problem: conda runs a package's pre-unlink script both when the package is being removed and when it is being replaced, and the script cannot tell which of the two is happening. Replacement is the common case:
- `conda update --all`, the README's update command, replaces every feature package whenever a new isabelle build arrives (§2.3, plan:239-241);
- the README itself recommends `--force-reinstall <feature>` as the way to mark a package explicitly requested (plan:714-715).
conda runs every pre-unlink before any unlink and before any post-link (core/link.py:938-967). So a pre-unlink never knows whether, a moment later, a new package will be linked and re-apply the chain.

The round-4 judge's C11 action (REVIEW4:1472-1476) therefore required two things: 'If you are removing <feature>' in front of every recovery step, and the sentence 'status will not see them' only in the removal case. Rev 5 does this only in part, and the §10.1 C11 row (plan:1058) does not say so. There are five places:
1. §4's residue block (plan:895-898) makes only the sentence 'status will not see them' conditional. The next sentence ('To clean up: … --force-reinstall isabelle …; then delete the created files listed above') is unconditional. So is the line 'If the cause was "lock busy" or the tool could not run: conda install -c … <最高的包名>; then conda remove <最高的包名>'.
2. The two frozen `||` texts of the feature pre-unlink (.sh at plan:516, .bat at plan:524) say 'If you are removing or replacing <feature>: … then install <包名> together with every other feature package this command removed; then remove them again'. These texts are copied into every published feature package and are frozen for all of 1.x (decision 1, plan:334-336). They cannot be fixed after the first publish.
3. Decision 9 (plan:547-548) attaches '这些改动在包卸掉后 status 就看不见了' to '若你是在卸掉或替换它'. For a replacement this is false: the new package's features.d lists the same files.
4. Decision 9 and §4 (plan:549-551, :889) say every block of one conda command gives the same command, so it does not matter which block the user follows. That holds for the lock-busy branch, whose recovery names the same highest package in every block. It does not hold for the CONFLICT branch. There, each block's 'delete the created files listed above' lists only its own feature's created files (plan:548). A user who follows one block of a removal that printed several blocks leaves the other features' created files in isa/, and status stops seeing them once those packages are gone.
5. Rev 5 adds a heap line for the case where a reversal leaves the tree at the chain bottom: 'The tree is back at the shipped sources. Delete heaps/ … and the shipped heaps are used again' (plan:561-563, :865-867).
   - This line prints in every replacement whose last pre-unlink reaches the chain bottom: `conda update --all` to a new build, a new version of the bottom feature, and `--force-reinstall` of the bottom feature.
   - Right after it, the new post-links re-apply the chain and print the 'changed (applied: …) … rebuilds' paragraph.
   - In the reinstall-the-bottom-feature case, the heaps in the user directory still match the final tree. A user who obeys the line forces a rebuild of HOL and of every other heap for nothing.
   - Decision 15's transcript check of `update --all` (plan:783) cannot pass against these specified texts.

The hooks critic measured this on a toy channel with conda 25.11.1, using the plan's hook texts verbatim (review-ipc5/critic-hooks/run2.out and run1.out):
- `conda update --all` to isabelle build 2 while another process holds the lock on the old etc/ISABELLE_ID. Three residue blocks each recommend 'conda install qiyuan-dev-patches; then conda remove qiyuan-dev-patches' (run2.out:6-14), although the update itself ends with every feature applied (run2.out:26-31). Following that advice leaves features.d empty, and status says 'no feature packages installed' (run2.out:52-68).
- `conda update --all` with a tool that crashes at import, where the update brings in a working tool. Each pre-unlink prints the frozen 'If you are removing or replacing … then remove them again' (run2.out:75-77), and the new post-links apply everything (run2.out:86).
- `conda update --all`, and separately `--force-reinstall isabelle-feat-a`. Each prints the 'back at the shipped sources, delete heaps/' line followed by the 'applied … rebuilds' paragraph (run1.out:75 and :111-118).

Required:
- §4's residue block gets two labelled branches:
  - 'If this command replaces light_locale (an update or a reinstall): its new package re-applies the chain when the command finishes; afterwards run isabelle-patch-control status.'
  - 'If this command removes light_locale: status will not see these files once the package is gone. To clean up: …; then delete the created files listed in every block this command printed. If the cause was "lock busy" or the tool could not run: conda install -c … <最高的包名>; then conda remove <最高的包名>.'
- The frozen `||` texts (.sh and .bat) become: 'If this command removes <feature>: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then conda install -c https://conda.qiyuan.me -c conda-forge <包名> and every other feature package this command removed; then conda remove them again. If it replaces <feature>: when it finishes, run isabelle-patch-control status.' This also spells the reinstall step as a command with both channel flags (see C8).
- The heap line appears only in the removal branch ('If this command removes the last feature package: the tree is back at the shipped sources; delete heaps/ …'). Alternatively, print it only for command-line unapply and add one README sentence about conda remove.
- Decision 9 at plan:548 says '若你是在卸掉它'. Plan:549-551 and §4 at plan:889 say 'the named package is the same in every block' instead of 'it does not matter which block'.
- Decision 15's residue and transcript cases (plan:776-778, :783) gain the two `update --all` shapes above, the heap texts of `--force-reinstall` of the bottom feature, and a removal with a CONFLICT that prints two blocks, each feature having a created file.
- The §10.1 C11 and C20 rows name all of this.

**Editor.** I checked this and it holds.
- The texts are quoted correctly (plan:516, :524, :547-551, :561-563, :865-867, :889-899).
- core/link.py:938-947 runs every pre-unlink of the unlink group before any unlink action. I read this myself; the round-4 judge also verified it.
- The toy tool that produced the transcripts is the critic's own implementation of rev 5's message rules. So the transcripts show what a literal implementation prints, not what the real tool will print. But the printed texts are the plan's, and the harm follows from the texts alone.

One overstatement: in a replacement with a CONFLICT, following 'delete the created files' damages a feature, but `isabelle-patch-control apply` can repair that. The harm that needs more than one command to repair is the install-then-remove advice, which strips the environment.

Severity stays major for two reasons: the `||` texts are frozen for 1.x, and the judge's explicit action was left undone without §10 saying so.

**Relaxation proposed by the editor.** Use one rule instead of five separate fixes. A pre-unlink cannot know whether a link follows, so every pre-unlink text has exactly two labelled branches:
- 'If this command removes <feature>: …', and
- 'If it replaces <feature>: its new package re-applies the chain; then run isabelle-patch-control status'.
Every recovery step, the 'status will not see them' sentence and the 'back at the shipped sources' heap line live only in the removal branch. The residue block, both frozen `||` texts and the heap line then follow the same rule, and for a replacement the question of which block to follow never comes up.

**Defender: confirmed** (needs owner: False).

Bottom line: a pre-unlink is the script conda runs just before it unlinks a package. It runs both when the package is being removed and when it is being replaced, and it cannot tell which. Rev 5 still writes several pre-unlink texts as if removal were certain. All five text defects survived my attempts to refute them. The round-4 judge's C11 action was only partly carried out, and §10 does not say so. Two of the challenge's supporting claims are overstated (corrected below), but the required fix stands.

Premise: confirmed from the conda source.
- conda runs the pre-unlink of every package in the unlink group before any unlink action (core/link.py:938-947, then :950). Post-links run later (:964-967).
- The script's environment is a copy of os.environ (:1566) plus ROOT_PREFIX, PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM (:1630-1634). Nothing in it describes the transaction.
- A `--force-reinstall`ed package is put in both the unlink set and the link set (core/solve.py:1417-1423).
- Replacement is the routine case: ruling 22 (plan:88-92, :239-241), and the README's own advice to `--force-reinstall` a feature to mark it explicitly requested (plan:714-715).

1. §4 residue block (plan:891-898): CONFIRMED.
- Only the sentence 'status will not see them' carries the removal condition (plan:895). The 'To clean up' sentence and the lock-busy line (plan:898) carry none.
- The round-4 judge required 'If you are removing <feature>' before every recovery step (REVIEW4:1474). The §10.1 C11 row (plan:1058) does not record that this was not done.
- Harm, measured on the critic's toy: in a lock-busy `update --all`, three blocks each say 'install qiyuan-dev-patches; then remove qiyuan-dev-patches', yet the update ends with every feature applied (critic-hooks/run2.out:6-17). Following that advice empties features.d, and status prints 'no feature packages installed' (:52-68).
- 'To clean up' is also harmful in a replacement where isabelle is not part of the command. It runs `--force-reinstall isabelle`, which deletes the user directory with the user's settings, own component registrations and heaps (recipe.yaml:223-231), for nothing. Deleting the listed created files then leaves a still-installed feature half-applied; `apply` repairs that, as the editor says.

2. The `||` texts (plan:516, :524): CONFIRMED as a silent deviation.
- They say 'If you are removing or replacing <feature>: … then remove them again', which contradicts REVIEW4:1474. §10 is silent about it.
- The advice is wrong in every replacement:
  - When the version stays the same, the new post-link re-applies everything (run2.out:75-80), and the advice strips the environment.
  - When the version changes, reinstalling the already-installed new version and removing it meets the old version's changes as a CONFLICT, so the advice does not even clean up.
- OVERSTATED: 'frozen for all of 1.x, can never be fixed after the first publish'.
  - Decision 1's freeze (plan:334-336) covers the command lines, the invocation, exit 0 and the .messages.txt channel, not the echo wording.
  - The renderer writes the hooks for each build (plan:589-592), and ruling 22 rebuilds every feature package for every isabelle build.
  - What is true: each published build's text is permanent, and the text that runs is the outgoing build's. So the first batch's text runs in every environment when its packages first leave it, most often at an `update --all`, which is a replacement. It must still be right before the first release.

3. Decision 9 (plan:547-548): CONFIRMED.
- It ties 'status 就看不见' to '若你是在卸掉或替换它'. That contradicts §4 (plan:895) and the judge, and it is false for a replacement.
- Appendix A (plan:1142-1143) states the same thing without any condition.

4. 'It does not matter which block' (plan:549-551, :889): CONFIRMED, low harm.
- The sentence is true only of the package that the lock-busy recovery names. Each block's 'delete the created files listed above' lists only its own feature's files (plan:548).
- Precondition: decision 7 moves every file that can be moved (plan:463-464). So a created file is listed only when it cannot move: when the lock was busy, or when the user edited the created file. In the lock-busy case the block prints both recovery recipes, so the user can pick the wrong one.
- What is left behind is untracked orphan files, harmless to builds but invisible to status.

5. The heap line (plan:561-563, :865-867): CONFIRMED as a new defect in the judge's own text.
- The line is the round-4 judge's C20 wording (REVIEW4:2430), carried out faithfully, so it is not a silent deviation.
- In `update --all` to a new isabelle build the line is moot. The feature pre-unlinks run first (solve.py:1450-1451), and isabelle's pre-unlink then deletes the user directory anyway. So the line is false by the end of the command but harmless.
- It does harm in `--force-reinstall` of the bottom feature (run1.out:110-113). There isabelle is not part of the command, the user directory survives, and the final tree equals the old one. Obeying the line deletes the still-valid heaps of every session the user built.
- Decision 15's check that the heap wording of `update --all` is correct (plan:783) would have to accept the false line.

Caveat on the evidence: the transcripts come from the critic's toy tool (critic-hooks/common.sh, src/toytool5.py). The printed texts are the plan's, and the harm follows from the texts alone.

Adjacent defect, measured at solver level only: the recovery's `conda install <包名>` gives no version. A dry-run solve picks the newest version compatible with the pinned isabelle build (defender-C1/dryrun.out: feat-a 2 chosen over 1). If that newer version has different patches, its post-link reads the old version's leftovers as a CONFLICT, and the recovery fails.

The editor's relaxation: I agree; it is the better shape. One rule, 'no pre-unlink text presumes removal', replaces five separate patches and prevents new ones. Two refinements:
- (a) The heap line needs only the removal label, not a replacement branch. In a replacement the post-link's paragraph already covers the outcome, and a replacement branch would add a useless line to every routine update.
- (b) The replacement branch must not promise 'its new package re-applies the chain'. That is false when the lock is still busy at post-link time or a CONFLICT remains. It should only point to status.

No ruling is reversed; this is wording under ruling 17.

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C1/.

(1) Read the conda 25.11.1 source:
- core/link.py:925-1000: pre-unlinks of the whole unlink group run, then the unlink actions, then post-unlinks; the link group follows with pre-link, link and post-link.
- core/link.py:1566 and :1630-1634: the script environment.
- core/solve.py:1417-1423 (force-reinstall goes into both sets) and :1450-1453 (unlink order: dependents first).
- isabelle-packaging-ci/conda/recipe.yaml:223-231: the isabelle pre-unlink runs `rm -rf` on the user directory.

(2) Re-read the critic's toy-channel transcripts (real conda 25.11.1, the critic's tool implementing rev 5's rules, setup in review-ipc5/critic-hooks/common.sh):
- run2.out:6-17: `update --all` with the lock busy prints three residue blocks, each naming qiyuan-dev-patches, then 'applied: feat_a feat_b dev_patches'.
- run2.out:52-68: following the lock-busy line literally leaves features.d empty, and status prints 'no feature packages installed'.
- run2.out:75-80: with a crashing tool, the `||` text 'If you are removing or replacing' is printed, then the new post-links apply everything.
- run1.out:72-78 and :110-113: 'The tree is back at the shipped sources. Delete heaps/' is printed before the 'applied … rebuilds' paragraph, both in `update --all` and in `--force-reinstall isabelle-feat-a`; in the second case isabelle is not part of the command.

(3) Own measurement: chan/noarch/repodata.json is a channel holding only an index (repodata), with isabelle 2025.2 build 1 and isabelle-feat-a versions 1 and 2, both pinning that build.
- Command: `conda create --dry-run --json --override-channels -c file://chan isabelle=2025.2=1 isabelle-feat-a`, with a private HOME, CONDARC and CONDA_PKGS_DIRS.
- Result (dryrun.out): it links isabelle-feat-a 2. An unpinned install picks the newer version.

(4) No new conda transactions were run: /tmp is 98% full (593 MB free), and round 4's defender-C11 ran out of space (ENOSPC). Nothing outside my scratch directory was modified.

Recommended fix: Smallest fix: wording and tests only, under ruling 17.

1. Decision 9: state the rule once, after plan:551. 'A pre-unlink cannot tell removal from replacement (link.py:938-947, :1630-1634). Every claim or step that is right only for a removal stands under "If this command removes <feature>:". A residue text also carries "If it replaces <feature>: when this command finishes, run isabelle-patch-control status."'

2. Decision 9 wording:
- plan:548: say '若你是在卸掉它'.
- plan:549-551 and §4 plan:889: replace '用户按哪一块做都一样' with 'every block names the same package'.

3. §4 residue block (plan:895-898):
- 'If this command removes light_locale: status will not see these files once the package is gone. To clean up: [only the recipe for this block's own cause; the tool knows it]. For a CONFLICT or a write failure: save your edits under $PREFIX/isa and in the user directory; conda install -c … --force-reinstall isabelle; then delete the created files listed in every block this command printed. For "lock busy": conda install -c … <最高的包名>=<版本>; then conda remove <最高的包名>.'
- 'If this command replaces light_locale (an update or a reinstall): when it finishes, run isabelle-patch-control status.'
- Drop 'or the tool could not run' from the block: that case is handled by the `||` text, never by this block.

4. Both frozen `||` texts (plan:516 .sh, plan:524 .bat):
- 'If this command removes <feature>: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then conda install -c https://conda.qiyuan.me -c conda-forge <包名>=<版本> and every other feature package this command removed, at the versions it removed; then conda remove them again.'
- 'If it replaces <feature>: when it finishes, run isabelle-patch-control status.'
- The renderer fills in <版本> from provenance.txt.
- Fix plan:529 to match.

5. Heap line (plan:561-563, :865-867): 'If this command removes <feature>: the tree is back at the shipped sources; delete heaps/ in the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER) and the shipped heaps are used again.' No replacement branch. Command-line unapply keeps the line without the condition.

6. Appendix A (plan:1142-1143): 'status 在包被卸掉（而不是被替换）后看不见它们'.

7. Decision 15 (plan:776-778, :783): add four cases.
- `update --all` with the lock busy: no step that removes a package is offered without the removal label; the command ends applied.
- `update --all` from a crashing tool to a working one.
- `--force-reinstall` of the bottom feature: the heap line carries the removal label, and the heaps in the user directory survive.
- A removal with a CONFLICT that prints two blocks, each feature having a created file: following only the last block leaves no created file.

8. §10.1: the C11 row (plan:1058) states that rev 5's `||` texts had deviated from REVIEW4:1474 and how this is fixed. The C20 row (plan:1067) states that the chain-bottom heap line now carries the removal label.

9. Correct the challenge's claim: the `||` wording is fixed per build, not for all of 1.x. Each published build's text stays permanent and runs when that build leaves an environment, so it must be right in the first batch.

**Judge: confirmed → author_fixes_no_rereview.** Apply one rule instead of five separate patches (relaxation 1). A pre-unlink cannot tell a removal from a replacement (link.py:938-947, :1630-1634). So every claim or step that is right only for a removal stands under 'If this command removes <feature>:', and every pre-unlink text also carries 'If it replaces <feature>: when it finishes, run isabelle-patch-control status'. Do not promise that the chain is re-applied: the lock may still be busy, or a CONFLICT may remain.

(1) Decision 9:
- state the rule once, after plan:551;
- plan:548 becomes '若你是在卸掉它';
- plan:549-551 and §4 plan:889 say 'every block names the same package' instead of '按哪一块做都一样'.

(2) §4 residue block (plan:891-898) gets the two labelled branches.
- The removal branch keeps 'status will not see them once the package is gone'.
- For a CONFLICT or write failure: save your edits; then conda install -c … --force-reinstall isabelle, with the wording chosen by C7; then delete the created files listed in every block this command printed.
- For lock busy: conda install -c … <highest package>=<version>; then conda remove <highest package>.
- Drop 'or the tool could not run' from the block, since the || text handles that case.

(3) Both || texts (.sh plan:516, .bat plan:524):
- Removal branch, spelled as commands with both channel flags: reinstall the tool; then `conda install -c https://conda.qiyuan.me -c conda-forge <包名>=<版本>` together with every other feature package this command removed, at the versions it removed; then `conda remove` them.
- Replacement branch: run status when the command finishes.
- The renderer fills in the name and version. The rendered .bat echo must contain none of cmd's metacharacters (< > | & ^ %), so write the 'other packages' part in words.
- Fix plan:529 to match.

(4) Heap line (plan:561-563, :865-867): in a pre-unlink it appears only under the removal label. Command-line unapply keeps it unconditionally.

(5) Appendix A (plan:1142-1143): say 'after the package is removed (not replaced)'.

(6) Decision 15 (plan:776-778, :783) adds four cases:
- update --all with the lock busy: no step that removes a package appears outside the removal branch, and the command ends with every feature applied;
- update --all from a crashing tool to a working one;
- --force-reinstall of the bottom feature: the heap line is labelled, and the heaps in the user directory survive;
- a removal with a CONFLICT that prints two blocks, each listing a created file: following the last block leaves no created file.

(7) The §10.1 rows C11 and C20 say that rev 5 left REVIEW4:1474 undone in the || texts and in the residue block, and how it is now fixed.

Correction to the challenge: the || wording is fixed per published build, not for all of 1.x. Decision 1 freezes the command lines, not the echo text. It must still be right in the first batch, because that text runs when those builds leave an environment, most often during update --all.

### C2 [major] plan_builds probes HEAD only for feature packages. A new tool version stranded by a publish that uploaded but never indexed then makes every later dispatch fail at the guard, and a new dispatch is exactly the recovery decision 11 prescribes

Section: Decision 10 plan_builds (plan:577-582); decision 11 rerun text (plan:634-636); decision 15 pytest (plan:748)  ·  merged from: release-R5-REL-1

**Statement.** The core problem: decision 10 handles a file that was uploaded but not yet indexed when the file is a feature package, but not when it is the tool package, and a stranded tool file blocks the whole batch.

How plan_builds works (plan:577-582). For each feature package (F, v):
- it reuses a live build whose depends pin the wanted isabelle build;
- otherwise it builds a new one with build number n = (highest existing build number) + 1;
- it then skips any n whose filename https://conda.qiyuan.me/noarch/<file> answers HEAD 200, that is, a file an earlier run uploaded but whose index push never happened.
The tool package is 'reused by version', and that lookup reads only the live repodata.json. Nothing derives the tool's build number, so a rebuild of the same tool version gets the same filename. Every noarch python package on the channel is named pyh4616a5c_<n> (review-ipc4/defender-C2/noarch-repodata.json).

How publish-conda.yml behaves:
- it uploads the .conda files first (:193-203), and only later pulls the channel and re-indexes it (:205-221);
- its guard compares every file of the batch with the bucket, not with the index, and refuses the whole batch when a file of the same name has different bytes (:147-191);
- a rebuilt .conda never has the same bytes (RELEASE_CHECKLIST.md:564-567).

Now consider a batch that ships a new tool version and fails after the upload but before the index push.
- The first batch, at §5 step 8, always ships a new tool version.
- §2.3 (plan:278-280) describes exactly this kind of failure for today's banner step.
- Decision 11 (plan:636) says a fix to publish-conda.yml can only be picked up by a new dispatch.
- In that new dispatch, the HEAD probe makes the features build with n = 1. The tool, however, is rebuilt as isabelle-patch-control-1.0.0-pyh4616a5c_0.conda with new bytes, and the guard refuses the whole batch.
- Every further dispatch fails the same way. This lasts until some other repository's publish happens to re-index the channel (:205-221). At that point the stranded batch becomes visible, and this batch's smoke job never runs.
The release critic simulated rev 5's rule against round 4's live repodata (review-ipc5/critic-release/plan_builds/sim.py and sim.out): dispatches D2 and D3 are refused on the tool file, and D4 succeeds only after an unrelated re-index.

The plan also contradicts itself:
- plan:634 says a failed publish can be resumed only by re-running the failed job and 'cannot be re-dispatched';
- plan:636 says a fix to publish-conda.yml needs a new dispatch;
- the HEAD probe exists only to make a new dispatch work.
Decision 15's pytest list (plan:748) has an 'uploaded but not indexed' case but does not say that it covers the tool.

When a feature file is stranded and the tool is already published, the current rule works. It leaves two builds of the same (F, v), pinned to the same isabelle build, with different bytes (sim.out, scenario B). That is harmless, but it shows that skipping a file the channel already serves is the wrong shape.

Required:
- One rule for every package the batch would publish, the tool included: if a candidate filename already answers HEAD 200, download that file and reuse it when it is what the batch wants.
  - For the tool, 'what the batch wants' means the same version.
  - For a feature, it means the depends in its info/index.json pin `isabelle 2025.2 <isabelle_build>`.
  - Only a served file that does not match is skipped, by n+1, and only for features.
- plan_builds takes the HEAD-and-fetch step as an injected parameter, so the pytest case can run, and that case covers a stranded tool.
- Reword plan:634-636: a new dispatch with the same inputs resumes byte for byte; re-running the failed job remains possible while the artifact exists.

**Editor.** I checked publish-conda.yml:147-203 myself. The guard lists the bucket with rclone and compares the sha256 of the https copy, and the upload comes before the index push. So a stranded file is served, and it blocks any rebuild with the same name.

The harm is narrower than the critic says. If the failure is transient and the artifact still exists, re-running the failed job still works (plan:634-635). The dead end needs one of two things: a failure that only a new dispatch can fix (a publish-conda.yml bug, which plan:636 itself anticipates), or an expired artifact. Also, the critic's simulation models the rule; it does not run the real workflows.

Severity stays major: this is the plan's own prescribed recovery for its own first release, and it sits in decision 11, which the round-4 judge asked to re-review.

**Relaxation proposed by the editor.** A single rule, 'a file the channel already serves is reused if it is what we want, and skipped only if it is not', replaces both the tool's repodata-only reuse and the features' skip-past-HEAD rule. A new dispatch then always resumes byte for byte. Decision 11 no longer needs to distinguish re-running a failed job from dispatching again, and the artifact retention stops limiting recovery.

**Defender: partially_confirmed** (needs owner: False).

The core mechanism is real. Two of the claims around it are overstated.

CONFIRMED, core.
- Decision 10 handles a file that was uploaded but never indexed only for feature packages. plan:580 skips any feature n whose file answers HEAD 200; for the tool it says only "工具包按版本复用" (reuse the tool by version), and that lookup reads repodata alone.
- Nothing gives the tool a build number. Decision 11 removed the `build_number` input (plan:605), decision 10 derives numbers only for features, and the channel convention is a fixed recipe number (`Isabelle_RPC/conda/recipe.yaml:46` `number: 0`). So a rebuild of the same tool version gets the same filename.
- Measured with rattler-build 0.69.1, using a toy noarch-python recipe with the tool's run deps (`python >=3.12, git >=2.43`, plan:323-324):
  - two builds both produce `toy-tool-py-1.0.0-pyh4616a5c_0.conda`, with different sha256;
  - the difference is the `info/index.json` timestamp (1792841060959 vs 1792841067684).
- The real guard text, publish-conda.yml:147-191, run against a stub bucket (guard.out):
  - rev 5's rule (features skipped to n=1, tool rebuilt): "::error:: ... toy-tool-py-1.0.0-pyh4616a5c_0.conda is ALREADY on the channel with DIFFERENT content", exit 1. The whole batch is refused, the new feature file included.
  - Upload comes before the index push (:193-203 vs :205-236), so the stranding state can happen.
- This is not a silent deviation from the round-4 judge. The judge prescribed "reuse the tool package by version" (REVIEW4:432-447), and rev 5 follows that literally. It is a gap in that prescribed design. It is in scope because rev 5 rewrote decision 10 and decision 11 cites it.

CONFIRMED, text.
- plan:634-636 contradicts itself. It says a failed publish can only be resumed by re-running the failed job, "不能重新 dispatch" (cannot be re-dispatched), because rebuilt bytes differ. Yet rev 5's HEAD probe exists only to make a new dispatch work for features, and plan:636 says a publish-conda.yml fix needs a new dispatch.
- The reason given at plan:635, "build 号是推出来的" (the build number is derived), is false for the tool.
- The re-run escape is also narrower than stated. GitHub allows re-runs only "up to 30 days after its initial run" (docs.github.com, re-run workflows and jobs), whatever the artifact retention.
- The pytest list at plan:748 does not cover a stranded tool.

OVERSTATED.
1. "Every further dispatch fails ... until some other repository's publish happens to re-index" is too strong. Two escapes exist, though the plan documents neither:
   - Bump the tool version. This passes the guard (guard.out case 3), and it is what the guard's own message advises (publish-conda.yml:185-186).
   - Re-run any earlier publish job, which re-pulls and re-indexes the whole bucket (:205-221).
   Users are never harmed; the release is stalled.
2. The cited trigger is already headed off. The banner failure (plan:278-280) is prevented by §5 step 7 and by the prerequisite at plan:640 (round-4 defender C2 noted this). Real triggers that remain:
   - a second publish-conda.yml bug that strikes after the upload (plan:636 itself expects this class);
   - an expired artifact, or a run older than 30 days;
   - an operator who dispatches again instead of re-running.
3. Decision 11 prescribes re-running, not a new dispatch. The title overstates this, but the inconsistency stands.

Scenario B (a stranded feature file while the tool is already published): the current rule works. The duplicate builds it leaves (_1 and _2, both pinned to the same isabelle build, both accepted) are harmless, because the solver takes the highest build. That point is about elegance only.

THE EDITOR'S RELAXATION, on its merits: sound, and more elegant.
- It reuses a served file when it is what the batch wants, and skips only a non-matching feature file.
- A served file was uploaded only by a `publish` job, which has `needs: [build, roundtrip, accept]` (plan:628). The new dispatch puts the reused file into the same local channel and runs roundtrip and accept on it again.
- It matches the guard's own design ("allow a re-run to resume ... the test is on CONTENT", publish-conda.yml:132-142). With the relaxed rule, case 2 of guard.out passes as "resume" for both files, exit 0.
- The tool's filename is known before any build: `rattler-build build --render-only` prints `"string": "pyh4616a5c_0"` (measured, 0.69.1). Every noarch-python package on the channel is pyh4616a5c_<n> (review-ipc4/defender-C2/noarch-repodata.json).
- For features, the pin test on a downloaded file is the same test already applied to repodata records. One test then serves indexed and not-yet-indexed files alike. The duplicates go away, and "a new dispatch with the same inputs resumes byte for byte" becomes true. That removes the artifact-retention and 30-day caveats from the recovery story.
- "Same version" as the tool's criterion is the existing reuse-by-version rule, so it adds nothing new.

Severity: the defect is real and sits on the plan's own first-release path, but its effect is a stalled release with undocumented escapes. Major is defensible only for the self-contradictory recovery text; the user-facing harm is nil. No owner ruling is touched.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C2/. Nothing outside it was modified, and no network write was made.

1. `rb/`: the round-3 toy noarch-python recipe (`run: [python >=3.12, git >=2.43]`), built twice with `/var/tmp/claude-reverify-pkg/rattler-build` 0.69.1.
   - Same filename `toy-tool-py-1.0.0-pyh4616a5c_0.conda`; sha256 40765bf8… vs 3467001d….
   - Extracted `info/index.json`: only the timestamp differs.
   - `--render-only` prints `"string": "pyh4616a5c_0"` and `"hash": "4616a5c"` before any build.
2. `guard/`: publish-conda.yml:147-191 copied verbatim into guard.sh and run under `set -euo pipefail` with `R2_BUCKET=conda`, against stub `rclone lsf` and `curl` backed by a fake bucket. The bucket holds the D1 tool bytes plus a stranded feature `_0`. Results in guard.out:
   - (1) rev 5 rule, rebuilt tool plus feature `_1`: refused on the tool, exit 1.
   - (2) relaxation, served files reused: both "resume", exit 0.
   - (3) tool bumped to 1.0.1: both "new", exit 0. This is an escape the plan does not name.
3. Read:
   - plan:270-280, :321-338, :570-648, :726-790, :909-933, :1049;
   - REVIEW4:346-447;
   - publish-conda.yml:1-345;
   - RELEASE_CHECKLIST.md:555-575;
   - Isabelle_RPC conda/recipe.yaml:46 and release-conda.yml:22,39,110;
   - review-ipc4/defender-C2/noarch-repodata.json (every noarch-python package is pyh4616a5c_<n>);
   - review-ipc5/critic-release/plan_builds/sim.py, sim.out, fixed.py, fixed.out (the critic's model agrees with the real-guard run).
4. GitHub docs (re-run workflows and jobs): re-runs are allowed "up to 30 days after its initial run" and use the original GITHUB_SHA.

Recommended fix: Smallest fix, adopting the editor's relaxation:

1. Decision 10 (plan:577-582). Replace "再跳过任何 … HEAD 200 的 n …。工具包按版本复用" with one rule for every package the batch would publish:
   - A candidate is a repodata record, or a filename the channel serves (HEAD 200) at the next build number. Starting at n = 1 + the highest indexed build number, probe upward.
   - A candidate is reused (downloaded unchanged into the local channel) when it is what the batch wants:
     - tool: the same version. Its filename comes from `rattler-build build --render-only`.
     - feature: its info/index.json depends contain exactly `isabelle 2025.2 <isabelle_build>`.
   - Only a served feature file that does not match is skipped (n+1).
   - `plan_builds(repodata, isabelle_build, wanted, fetch)` takes the HEAD-and-fetch step as an injected parameter.
2. Decision 15 (plan:748). The uploaded-but-not-indexed case covers three inputs: a stranded tool, a stranded feature whose pin matches (reused), and one whose pin does not (skipped).
3. Decision 11 (plan:634-636). Reword the recovery:
   - A new dispatch with the same inputs resumes byte for byte: it downloads the stranded files, and the guard reads them as a resume. This is also how a publish-conda.yml fix gets picked up.
   - Re-running the failed job also works, while the artifact exists and within GitHub's 30-day re-run limit.
   - Delete "build 号是推出来的" as the reason.
4. §10.1, C2 row: state that the tool's stranded-file case extends the round-4 judge's "reuse the tool package by version".

If the author prefers the narrowest change instead: in step 1, apply the HEAD-and-reuse rule to the tool only, and keep the features' skip rule, accepting the harmless duplicate builds. Steps 2-4 are needed either way.

**Judge: partially_confirmed → author_fixes_no_rereview.** The core holds.
- Nothing derives a build number for the tool, so a rebuild of the same tool version reuses its filename with new bytes, and publish-conda.yml:147-191 refuses the whole batch (measured: defender-C2/guard.out).
- Overstated: 'every later dispatch fails' is too strong. Bumping the tool version, or re-running an earlier publish job, escapes. The cited banner trigger is already prevented by §5 step 7.

Adopt relaxation 2.

(1) Decision 10 (plan:577-582): replace the HEAD skip and '工具包按版本复用' with one rule for every package the batch would publish, the tool included.
- Candidates are the live repodata records, plus each filename the channel serves (HEAD 200), probing upward from n = 1 + the highest indexed build number.
- A candidate is reused, downloaded unchanged, when it is what the batch wants:
  - for the tool, the same version, with the filename taken from `rattler-build build --render-only`;
  - for a feature, info/index.json's depends contain exactly `isabelle 2025.2 <isabelle_build>`.
- Only a served feature file that does not match is skipped (n+1).
- The signature is plan_builds(repodata, isabelle_build, wanted, fetch), with the HEAD-and-fetch step injected.

(2) Decision 15 (plan:748): the 'uploaded but not indexed' case covers a stranded tool, a stranded feature that matches (reused) and one that does not (skipped).

(3) Decision 11 (plan:634-636):
- a new dispatch with the same inputs resumes byte for byte, and this is also how a publish-conda.yml fix gets picked up;
- re-running the failed job works only while the artifact exists and within GitHub's 30-day re-run window;
- state the artifact retention in days;
- delete 'build 号是推出来的' as the reason.

(4) The §10.1 C2 row says this extends the round-4 judge's 'reuse the tool package by version'.

### C3 [major] The authoritative glossary still says the pristine isabelle build copies the hook fragment, which ruling 33 forbids. Four of the edits that rev 5's redefinition of 链顶 needs were also skipped, and §10 mentions neither

Section: Glossary (plan:37, :39); §0 item 28 (plan:128); decision 14 (plan:713); §7 (plan:989); §10.1 rows C3 (plan:1050) and C12 (plan:1059)  ·  merged from: hooks-H2, consistency-CONS-1, consistency-CONS-6

**Statement.** The core problem: the owner's rules make a document's glossary authoritative over the rest of it. This glossary still describes the design that ruling 33 removed, and the new meaning of 链顶 makes four lines that were left unchanged false.

1. The hook fragment entry.
- The glossary entry 钩子片段 (plan:37) reads '工具仓库拥有、所有 feature 包和原版构建的 post-link 逐字复制的那段文本'.
- Ruling 33 (plan:141-145) removed the copy from the isabelle package. Decision 9 (plan:483-484) and decision 12 point 2 (plan:658-659) both say the isabelle package carries none.
- Item (7) of the round-4 C3 judge action named exactly this line: 'Reword plan:35 (glossary: 钩子片段 is copied only by feature packages)' (REVIEW4:530, :544). The line was rev 4's line 35.
- Rev 5 made the other rewordings in that action and left this one. The §10.1 C3 row (plan:1050) does not mention it.

2. The new meaning of 链顶.
Rev 5 took the 'fewer edits' option of the C12 judge (REVIEW4:1593-1597). Now:
- 链顶 means the last feature of the chain the tool builds from an environment's feature directories (plan:16-17);
- 链序最末 means dev_patches;
- tip means the commit make-patches releases.
That option came with a set of small edits, and four were not made:
- §0 item 28's record (plan:128) still says '被改文件在链顶的内容'. It describes a release-time gate, where no environment exists. The judge asked for 'tip（待发布的 commit）的内容'.
- §7's row (plan:989) still says 'dev_patches 在链顶'. That is now false for every user who does not install qiyuan-dev-patches. The judge asked for 链序最末.
- The glossary entry 批量发布 workflow (plan:39; rev 4's line 37) still says '把整条链一次构建'. The judge asked for '链序上的全部 feature 包'.
- Decision 14's README text (plan:713) still says 'libmamba 卸顶层包', which uses 顶层, a fourth term the glossary never defines. The judge asked for 链顶.
The §10.1 C12 row (plan:1059) lists only the glossary definitions and decision 9.

Required:
- plan:37 becomes '工具仓库拥有、每个 feature 包的 post-link 逐字复制的那段文本（决定 9）；isabelle 包里没有它的副本（第 33 条）'.
- plan:128 becomes 'tip（待发布的 commit）'. This line is the author's paraphrase of the ruling, not the owner's words, so the author may change it.
- plan:989 becomes '链序最末'.
- plan:39 becomes '链序上的全部 feature 包'.
- plan:713 becomes '卸链顶的包'.
- The §10.1 C3 and C12 rows name all five edits.

**Editor.** Two corrections to the critics.
(a) hooks-H2 says the C12 judge's 'write 链序上的全部 feature 包 at plan:37' was aimed at the hook fragment line. It was not. In the reviewed rev 4, line 35 is the hook fragment entry and line 37 is the batch release workflow entry ('把整条链一次构建'), which is plan:39 in rev 5. I checked …PLAN.rev4.md:35-37; the §0 additions do not shift glossary line numbers. Only the C3 action is aimed at the hook fragment line.
(b) consistency-CONS-6 also asks to rewrite 链顶 in decision 11's roundtrip job (plan:620) and in decision 17's '<链顶 feature>' (plan:824). The C12 judge listed those uses (rev 4 :531, :685, :689) among the ones that 'are correct unchanged' (REVIEW4:1592). In both places 链顶 means the chain top of the environment or features.d under test, which fits the new definition. I dropped that part.
I verified everything else line by line.

**Defender: confirmed** (needs owner: False).

I tried to refute the challenge and could not. Every factual claim in it holds. Two of its supporting remarks go further than the evidence, but the required fix does not depend on them.

How the line numbers line up. The judges' line numbers in REVIEW4 match the saved copy ISABELLE_PATCH_CONTROL_PLAN.rev4.md exactly up to the end of section 0. After that they are 15 lower, because the saved copy already contains section 0 items 33-35 (rev4.md:144 holds ruling 33's text). With that offset every target is unambiguous:
- C12 :830 is rev4:845;
- C12 :603 is rev4:618;
- C3 :731 is rev4:746;
- C3 :811 is rev4:826;
- C3 :923-924 is rev4:938-939.

1. The glossary entry 钩子片段 (hook fragment) contradicts ruling 33. Confirmed.
- plan:37 still says the post-links of 所有 feature 包和原版构建 (all feature packages and the pristine build) copy the fragment verbatim. It is byte-identical to rev4:35.
- Ruling 33 (plan:141-145), decision 9 (plan:483-484, :564-565), decision 12 point 2 (plan:659), decision 15 (plan:762) and §5 step 7 (plan:927) all say the isabelle package carries no copy.
- grep finds no other place in rev 5 that still says the pristine build copies the fragment. So the authoritative glossary is the only place that tells a reader, for example the author of the CI plan, to do the thing ruling 33 forbids.
- The C3 judge's paragraph (REVIEW4:544) lists 'Reword plan:35'. Every other target in that list was reworded:
  - rev4:746 became plan:873;
  - rev4:791-792 became plan:927-928;
  - rev4:826 became plan:970;
  - rev4:938-939 became Appendix A at plan:1124-1125.
- Only the glossary line was skipped, and the §10.1 C3 row (plan:1050) does not mention any rewording. That is a silent deviation.

2. Four edits from the C12 judge's 'fewer edits' option (REVIEW4:1593-1597) are missing, and the §10.1 C12 row (plan:1059) is silent about them. Confirmed. The 顶层 (top-level) replacements in decision 15 were made (plan:769-782), but that row does not mention them either.
- (a) plan:128, §0 item 28, still says 被改文件在链顶的内容 (the content of the changed file at 链顶). Under the new definition at plan:16-17, 链顶 is the last feature of the chain built from an environment's feature directories, and no environment exists at release time. Decision 16 point 5 (plan:802) and point 7 (plan:809) say 'tip' for the same thing, and REVIEW3's C7 text (REVIEW3 C7 block, line 35 of that section) says 'content at the tip'. The record is the author's paraphrase: the owner's only words were 赞同 (agreed). So rewording it restores the reviewed meaning and is not a reinterpretation of the ruling.
- (b) plan:989 still says dev_patches 在链顶 (dev_patches is at 链顶). The resolution the row describes is by chain order: the migration plan glossary :26 defines 链序 (chain order), and :158 says 链序即依赖序 (chain order is dependency order). So the canonical term is 链序最末 (last in chain order), defined at plan:16. The challenge also says the row is 'false for every user who does not install qiyuan-dev-patches'. That goes too far: the overlap only exists when dev_patches is installed, and then it is 链顶. This is a terminology defect plus a skipped judge edit, not a false statement.
- (c) plan:39 still says 把整条链一次构建 (builds the whole chain at once). The challenge says the new 链顶 makes this false. It does not, because plan:15 still defines 链 as the full sequence pristine→…→dev_patches. Two things still stand. First, the judge named this edit. Second, plan:16 now also uses 链 for the chain built from features.d, so 链 has two senses inside the glossary itself. The judge's wording is also more precise: the workflow does not build pristine, and per ruling 25 (plan:110) it handles 全部 feature 包 (all feature packages).
- (d) plan:713, decision 14's README content, still says 卸顶层包 (remove the top-level package). Decision 15 names the same act 卸链顶的包 (remove the 链顶 package) at plan:774-775, and 顶层 is otherwise used only for a repository's top-level directory (plan:52, :152). So one concept carries two names. The judge's list (:603, which is rev4:618) included this line. Rev 5 edited this sentence for C17 (it added 以及没被显式要求过的 isabelle, 'and isabelle when it was never explicitly requested') but left 顶层.

The editor's rebuttals. I accept both.
- (a) rev4:35 is the hook fragment entry and rev4:37 is the batch release workflow entry. The C12 critic's '整条链 -> …' only makes sense against line 37.
- (b) The judge listed rev4:546, :700 and :704 (judge numbers :531, :685, :689) as correct unchanged under the new definition. plan:620 is a sentence new in rev 5 (the C14 change). Its 链顶 feature 包 is the package that becomes the test environment's 链顶 once installed, so it fits the new definition.

There is no relaxation to weigh. Severity: the glossary contradiction is real and a reader would act on it, because the owner made the glossary authoritative. The four terminology items are minor.

Experiment: Text-only checks. The scratch directory is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C3/, and the grep output is saved there as evidence.txt.
- Compared the glossary of rev4.md with the glossary of rev 5 (lines 12-40). The only changes are the 链底/链序最末/链顶/tip definitions and the 暂存目录 (staging directory) and 临时目录 (temporary directory) entries. The 钩子片段 and 批量发布 workflow entries are unchanged.
- grep over rev 5 found:
  - 片段 (fragment): only plan:37 still says the pristine build copies it;
  - 顶层: plan:52, :152, :713;
  - 整条链 (the whole chain): plan:39, :620;
  - 链序最末: plan:16 and plan:1059 only;
  - tip: plan:17, :802, :809, :922.
- Mapped every judge line number in REVIEW4:530-544 and :1593-1597 onto rev4.md (+15 after §0 item 32; confirmed through rev4:618, :661, :665-666, :670, :746, :791, :826, :845, :938). Then located each target in rev 5:
  - done: :873, :927, :970, :1124, :769-782;
  - not done: :37, :128, :713, :989, :39.
- Read the §10.1 rows C3 (plan:1050) and C12 (plan:1059), decision 9 (plan:481-569), decision 11 (plan:598-649), decision 12 point 2 (plan:658-662), decision 14 (plan:706-725) and decision 16 (plan:792-821).
- Read the migration plan :20-32 and :150-160, and REVIEW3 C7 for the 'tip' wording.
No conda experiment was needed: every claim in this challenge is about the plan's text.

Recommended fix: The author can make all of these edits by hand; ruling 17 covers the wording, and §0 item 28 is the author's own paraphrase.

1. plan:37: '工具仓库拥有、每个 feature 包的 post-link 逐字复制的那段文本（决定 9；`isabelle` 包里没有它的副本，第 33 条），`.sh` 与 `.bat` 各一份。' (The text the tool repository owns and every feature package's post-link copies verbatim; the isabelle package holds no copy.)
2. plan:128: replace 在链顶的内容 with 在 tip（待发布的 commit）上的内容 (the content at the tip, the commit being released). This matches decision 16 point 5 at plan:802.
3. plan:989: replace dev_patches 在链顶 with dev_patches 在链序最末 (dev_patches is last in chain order).
4. plan:39: replace 把整条链一次构建 with 把链序上的全部 feature 包一次构建 (builds every feature package in chain order at once).
5. plan:713: replace 卸顶层包 with 卸链顶的包 (remove the 链顶 package), the same words decision 15 uses at plan:774.
6. §10.1:
   - The C3 row adds: '术语表 钩子片段、§5 第 7 步、§7 第 (1) 行、§4 CONFLICT 标题、附录 A 改写' (glossary 钩子片段, §5 step 7, §7 row (1), the §4 CONFLICT heading and Appendix A reworded).
   - The C12 row adds: '§0 第 28 条记录用 tip、§7 发现 1 用链序最末、术语表 批量发布 workflow 用"链序上的全部 feature 包"、决定 14 与决定 15 的 顶层 换成 链顶' (§0 item 28's record uses tip, §7 finding 1 uses 链序最末, the batch release workflow entry uses 链序上的全部 feature 包, and 顶层 becomes 链顶 in decisions 14 and 15).

Drop the parts of CONS-6 that the editor rejected: plan:620 and plan:824 stay as they are.

**Judge: confirmed → author_fixes_no_rereview.** Make the five hand edits.
- plan:37: '工具仓库拥有、每个 feature 包的 post-link 逐字复制的那段文本（决定 9；isabelle 包里没有它的副本，第 33 条），.sh 与 .bat 各一份'.
- plan:128: '在 tip（待发布的 commit）上的内容'. This is the author's paraphrase; the owner said only 赞同.
- plan:989: 'dev_patches 在链序最末'.
- plan:39: '把链序上的全部 feature 包一次构建'.
- plan:713: '卸链顶的包', as at plan:774.

The §10.1 C3 and C12 rows name these edits and the 顶层 replacements already made in decision 15.

Keep plan:620 and plan:824 unchanged: the editor's rebuttal is right, both fit the new definition of 链顶.

### C4 [major] §10 is untrue again, although the header promises that every row was checked against the judge's text, and several small judge actions are left undone without any row saying so

Section: Header (plan:5-6); §10.1 rows C1, C2, C5, C6, C9, C24 (plan:1048-1071); §10.2 intro (plan:1075); decision 12 point 5 (plan:674); §6 (plan:936-962); decision 14 (plan:722-724); §4 (plan:881); archive …PLAN.rev4.md  ·  merged from: consistency-CONS-2, release-R5-REL-8, consistency-CONS-4, consistency-CONS-5, hooks-H8, consistency-CONS-13, consistency-CONS-16, consistency-CONS-17

**Statement.** The core problem: the plan header says that every row of §10 was checked against the ruling text (plan:5-6). For the third round in a row this is not true. The round-4 judge named an untrue §10 as one of the four things that kept rev 4 from being ready (REVIEW4:22-30).

Some untrue rows come from defects that have their own challenge in this review: C3 and C12 (see challenge C3), C8 (challenge C7), C11 and C20 (challenge C1), and C17 (challenge C8). The remaining items are listed below. Each is either a judge action that was not carried out or a row that misstates what was done.

1. C9 row (plan:1056).
- The C9 judge asked for two stale references to be fixed (REVIEW4:1245).
- Decision 12 point 5 still calls the banner fix '§5 第 6 步发布原版构建的前提' (plan:674). Step 6 writes and lands the CI plan (plan:927); the pristine build is published at step 8 (plan:932).
- The row says the other reference was fixed in '§0 第 25 条'. §0 item 25 (plan:108-113) has no such reference; the fix is in §2.3 (plan:280).

2. C24 row (plan:1071), which says '§6 的界'.
- The C24 judge asked §6 to state the bound that decision 5's argument relies on: one run holds the lock far below the 60 s wait. The judge left the number to the author (REVIEW4:2763).
- Decisions 5 (plan:419) and 15 (plan:789) both cite '§6 要求…远低于 60 秒'. §6 (plan:936-962) has no such item and no number.
- Decision 15 says to merge the listing step into one batched --numstat call only if the bound is exceeded. Without a written bound, that switch can never trigger.

3. C6 row (plan:1053).
- The C6 judge asked for §6's list of channel sources to be corrected (REVIEW4:903): in run mode, the run's isabelle packages are merged into the local channel.
- §6 still reads '本地渠道加线上/artifact 的原版构建加 conda-forge' (plan:939), unchanged from rev 4, and the row does not mention §6.

4. C2 row (plan:1049).
- The row lists 'retention' as done. The judge asked for the artifact retention to be stated (REVIEW4:440).
- Decision 11 says only '保留期写进 workflow' (plan:635), with no number.

5. C5 row (plan:1052).
- The C5 judge asked the author to 'tell the owner this strictly extends ruling 28's gate' (REVIEW4:779).
- The row instead records the author's view that the change is within the spirit of ruling 28, and §0 records no owner answer.
- Ruling 28 (plan:127-129) refuses a change whose content equals the content at a lower state. Decision 16 point 5 (plan:803-805) adds a second kind of refusal: a change that undoes nothing but whose context fits several levels ('上下文有歧义、要改写').
- The row does name the deviation. But the owner's rule 'never act on assumptions — ask' (CLAUDE.md) leaves this call to the owner.

6. The C1 action 'reconsider the reason given at :420-422' (REVIEW4:340).
- Performant_Isabelle_ML release-conda.yml:420-422 and auto_sledgehammer release-conda.yml:191-194 both say that --override-channels keeps conda-forge out of 'a proxy that breaks TLS here'.
- Decision 14 (plan:722-724) tells both maintainers to add -c conda-forge and does not mention that reason.

7. The C20 action (6), 'mark created files'.
- The CONFLICT text points to files 'marked "created" in status -v' (plan:881).
- Decision 6's -v format (plan:449) defines no such marker.

8. §10.2's introduction says eight rows carry the 【订正】 mark (plan:1075). Ten rows carry it (plan:1081, :1089, :1093, :1098, :1102, :1105-1108, :1115).

9. The archive …PLAN.rev4.md is not the text round 4 reviewed.
- It contains §0 items 33-35 (…PLAN.rev4.md:140-155), which record owner answers given after round 4.
- Its modification time (16:30) is later than REVIEW4.md's (16:14).
- As a result, every REVIEW4 'plan:N' reference after §0 points 15 lines too early in the archive. For example, REVIEW4's plan:603 is …PLAN.rev4.md:618.

Required:
- Fix items 1-7:
  - plan:674 becomes '§5 第 8 步', and the C9 row names §2.3 (plan:280) as the place of the other fix;
  - add a §6 item such as '(l) on win-64 a whole-chain status and a --force-reinstall isabelle each hold the lock at most N s', and have decisions 5 and 15 cite it by its letter;
  - §6's list of channel sources says that in run mode the run's isabelle packages sit in the local channel;
  - state the retention in days next to plan:635;
  - ask the owner the one-line question about the strong gate, and record the answer in §0;
  - add one clause to decision 14 about the TLS-proxy reason;
  - define the 'created' marker in decision 6's -v format.
- Correct the count in §10.2's introduction.
- Either restore the rev 4 archive to the reviewed text, or say in the header that it has §0 items 33-35 added.
- Then re-check every §10.1 row against its Judge paragraph, one action at a time, and keep the header sentence only if it is then true.

**Editor.** Notes on the merged findings:
- consistency-CONS-2 counts about ten untrue rows. Four of them are counted here only by reference, because their substance is a separate challenge.
- hooks-H8 duplicates item 1 and is merged into it.
- consistency-CONS-13 does not describe a silent deviation, since the row names it. What remains is that the plan answers a question the judge sent to the owner.
- consistency-CONS-16 is about keeping the archive accurate, not about the design. The glossary and §0 lines in the archive are not shifted.

Dropped from consistency-CONS-17:
- (c) The two Isabelle_RPC line ranges are both accurate. 165-176 is the whole printf block; 168-174 is the same block without @echo off and exit /b 0. Each quotes what it cites. §2.3 (plan:250-253) already says that the .messages.txt redirect is this plan's own addition and that the .bat line is silent.
- (e) 'minilang' at plan:260 should read isabelle-minilang (Isa-Mini/conda/recipe.yaml:51). This is a one-word fix the author can make in passing.
- (f) The C4 row's '记在 §9 外不展开' and the point number in the C1 row are wording nits.

**Defender: partially_confirmed** (needs owner: False).

The main claim holds. The header says every §10 row was checked against the judge's text (plan:5-6), and that is false again. I could refute only one of the nine items, item 5, and only in part. I checked each item against the plan, REVIEW4 and the sources.

Item 1, CONFIRMED.
- The C9 judge said to change plan:572 '§5 第 6 步' to 第 8 步 (REVIEW4:1245).
- rev4.md:587 and rev5 plan:674 both still say '这是 §5 第 6 步发布原版构建的前提'.
- §5 step 6 only writes and lands the CI plan and does a non-publish dispatch (plan:927). The pristine build is published at step 8 (plan:932).
- The C9 row (plan:1056) puts the other fix in '§0 第 25 条'. §0 item 25 (plan:108-113) has no reference to decision 12. The fix is really in §2.3 (plan:280; rev4.md:260).

Item 2, CONFIRMED.
- Decision 5 (plan:419) and decision 15 (plan:789) both say '§6 要求…远低于 60 秒'.
- §6 (plan:936-962) has no lock or time item at all; a grep of the section for 锁/秒/60 finds only the general 'pytest 覆盖' line.
- The judge asked for exactly this, with a number (REVIEW4:2763).
- Decision 15's switch, '超了才…', therefore has no threshold to compare against.

Item 3, CONFIRMED.
- The C6 judge said 'Fix §6's source list (plan:785)' (REVIEW4:903).
- rev5 plan:939 is byte-identical to rev4.md:800.
- The C6 row (plan:1053) does not mention §6. (The C10 row in §10.2 was fixed.)

Item 4, CONFIRMED, minor. The judge said 'state the artifact retention' (REVIEW4:440). plan:635 says only '保留期写进 workflow' and gives no number. The CI's own artifacts state 7 days (build.yml:1106,1114).

Item 5, PARTLY REFUTED.
- C5's verdict was author_decides_then_rereview. The owner questions were only C3, C4 and C10 (REVIEW4:12-15). So the judge sent no question to the owner; it asked the author to tell the owner (REVIEW4:779).
- The editor's 'answers a question the judge sent to the owner' therefore misreads REVIEW4, and requiring an owner answer recorded in §0 goes too far.
- The row does name the extension (plan:1052).
- The author's report after rev 5 did tell the owner 'make-patches：强门禁改必做' (transcript record 8593, 0-based). It did not say that this refuses more than ruling 28 does (plan:127-129 against plan:803-805).
- What remains: one sentence to the owner, and a row that records it was said.

Item 6, CONFIRMED.
- Performant release-conda.yml:421-422 and auto_sledgehammer :193-194 give the reason '(which this stack needs nothing from) out of a proxy that breaks TLS here'.
- Decision 14 (plan:722-724) adds -c conda-forge and says nothing about that reason.
- Evidence that the reason is stale: Isabelle_RPC's identical step already uses conda-forge on ubuntu-latest with a rewritten comment (release-conda.yml:188, :206, :223-229).

Item 7, CONFIRMED.
- plan:881 points to files 'marked "created" in status -v'.
- Decision 6's -v format (plan:449) defines no such marker; it only says 新建文件显示 +++ b/ 那边的路径.
- The judge's action (6) was to mark created files in the CONFLICT text itself (REVIEW4:2436 and the defender's (6) at REVIEW4 C20). Yet the C20 row says '新建文件标出' (plan:1067).

Item 8, CONFIRMED, as an undercount.
- Eleven lines contain the mark: the intro (plan:1075) and ten rows (plan:1081, 1089, 1093, 1098, 1102, 1105-1108, 1115).
- The literal sentence ('the eight rows are marked') is true. But it hides two more corrections:
  - C3: round 4 found this one too, through C2 (REVIEW4:445).
  - C15: the author found this one; REVIEW4 never mentions the private cache.

Item 9, CONFIRMED.
- rev4.md:140-155 holds §0 items 33-35.
- rev4.md's modification time is 16:30, after REVIEW4.md at 16:14. The transcript also says that rulings 33-35 were recorded before 'rev 4 副本已存' (record 8078).
- Every REVIEW4 plan:N after §0 is shifted by +15 in the archive: REVIEW4's plan:572 is rev4.md:587, and plan:785 is rev4.md:800.

Elegance point: four rounds in a row show that free-text §10 rows drift from the judge's actions. A row shape of one line per judge action, each marked 'done at plan:N' or '偏离：reason', would make a silent omission visible. It would have caught items 1-4, 6 and 7.

Experiment: All checks were read-only, with grep, sed and diff over the plan, rev4.md, REVIEW4.md, the component workflows and the session transcript. The outputs are saved under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C4/ (textchecks.out, msgs.txt, extract.py).

1. I counted the 【订正】 marks: 11 lines, which is the intro plus 10 rows.
2. I grepped '第 6 步发布原版构建' and found it at rev4.md:587 and plan:674, unchanged.
3. I counted occurrences of '60' in §6 (plan:936-962): zero.
4. I diffed rev4.md:800 against plan:939: identical.
5. I grepped '^3[345]\.' in rev4.md and found lines 140, 145 and 150. I compared file times: rev4.md 16:30:11, REVIEW4.md 16:14:24. I confirmed the +15 offset at REVIEW4 plan:572, which is rev4.md:587.
6. I read Performant :420-425 and auto_sledgehammer :191-197 (the TLS-proxy comment), and Isabelle_RPC :188, :206 and :223-229 (the same step, already using conda-forge on ubuntu-latest).
7. I extracted the transcript messages after 08:00Z, including queued ones (extract.py, writing to msgs.txt). Record 8593 is the post-rev-5 report saying '强门禁改必做' without mentioning ruling 28. Record 8078 is 'rev 4 副本已存', written after rulings 33-35 were recorded.

Recommended fix: These are text edits only; no owner ruling is needed.

1. Step reference and C9 row:
   - plan:674: change '§5 第 6 步发布原版构建的前提' to '§5 第 8 步发布原版构建的前提'.
   - C9 row: replace '§0 第 25 条引用改' with '§2.3（plan:280）的引用改"决定 12 第 5 点"；决定 12 第 5 点的步号改第 8 步'.
2. Lock bound:
   - Add a §6 item: '(l) win-64 上整链 status 一次、--force-reinstall isabelle 一次，各自持锁不超过 N 秒'. N is the author's call, for example 10.
   - Have decision 5 (plan:419) and decision 15 (plan:789) cite '§6 (l)', with '超了' meaning above N.
3. §6 source list: change plan:939 to '本地渠道（run 模式下含那次运行的 isabelle 包）加线上渠道加 conda-forge（决定 11）'. Add '§6 来源句' to the C6 row.
4. Retention: at plan:635, give feature-packages' retention-days as a number, and note the CI artifact's 7 days (decision 12 point 3).
5. Strong gate:
   - Tell the owner in one sentence that decision 16 point 5 also refuses context-ambiguous multi-level changes, which ruling 28 does not name.
   - Change the C5 row to record that the owner was told, and drop the '已在精神内' framing.
   - Add §0 text only if the owner rules.
6. Decision 14 (plan:722-724): add a clause saying that both comments' reason ('needs nothing from conda-forge; a proxy that breaks TLS here') no longer holds and the comment must be rewritten, as Isabelle_RPC release-conda.yml:223-229 already did.
7. Created files: in decision 6's -v format (plan:449), mark created files '(created by the feature)', the same marker as the residue block (plan:894). Make plan:881 match it, and mark the file named on the CONFLICT line in the same way.
8. §10.2 intro (plan:1075): say ten rows are marked, namely the round-4 judge's eight plus C3 (from round-4 C2) and C15 (found by the author).
9. Header: add that …PLAN.rev4.md had §0 items 33-35 added after the review, so REVIEW4 references to plan:N for N ≥ 140 sit at N+15 in the archive.
10. Re-check every §10.1 row one judge action at a time. Restating the rows as one line per action, marked done at plan:N or 偏离 with a reason, is the more robust shape. Keep the header sentence only if it is then true.

**Judge: partially_confirmed → author_fixes_no_rereview.** Items 1-4 and 6-9 hold. Item 5 is partly refuted: the round-4 judge asked the author to tell the owner, not to obtain a ruling. The fixes:

(1) Decision 12 point 5 and the C9 row:
- plan:674 becomes '§5 第 8 步';
- the C9 row names §2.3 (plan:280) as the place of the other fix.

(2) Lock bound:
- add a §6 item such as '(l) on win-64 a whole-chain status and a --force-reinstall isabelle each hold the lock at most N s'; N is the author's call;
- decisions 5 (plan:419) and 15 (plan:789) cite it by its letter, and 超了 means above N.

(3) plan:939: in run mode the local channel holds that run's isabelle packages. Add this to the C6 row.

(4) plan:635: give the retention of feature-packages in days.

(5) Tell the owner in one sentence that decision 16 point 5 also refuses context-ambiguous releases that undo nothing (owner question 2). The C5 row records that the owner was told, and drops '已在精神内'.

(6) Decision 14 (plan:722-724): one clause saying the reason those workflows give ('needs nothing from conda-forge; a proxy that breaks TLS here', Performant release-conda.yml:421-422, auto_sledgehammer :193-194) no longer holds, so the comment must be rewritten, as Isabelle_RPC release-conda.yml:222-229 already did.

(7) Decision 6's -v format (plan:449) defines the marker '(created by the feature)', the one the residue block uses at plan:894, and plan:881 uses it.

(8) The §10.2 intro (plan:1075) says ten rows are marked: the round-4 judge's eight, plus C3 and C15.

(9) The header says that …PLAN.rev4.md had §0 items 33-35 added after the review, so a REVIEW4 reference plan:N with N≥140 sits at N+15 in the archive.

(10) Restructure §10.1 as one line per judge action, each marked 'done at plan:N' or '偏离：reason' (relaxation 4). Keep the header sentence only if it is then true.

Also fix in passing: plan:260 'minilang' → isabelle-minilang (Isa-Mini/conda/recipe.yaml:52).

### C5 [minor] Decision 16 point 8 never says which feature-repository commit is released. On a rerun it accepts an existing tag after checking only the patch files, so the tag can ship component files that no tested build built; and the release commit is not limited to patches/<R>/

Section: §0 ruling 35 (plan:151-155); decision 16 points 7-8 (plan:808-817)  ·  merged from: release-R5-REL-2, consistency-CONS-15, consistency-CONS-11

**Statement.** The core problem: ruling 35 ties light's shipped HOL-side files to a tested build by comparing them between 'the recorded HEAD' and 'the commit to be released' (plan:151-155). The recorded HEAD is a commit of the light repository. The plan, though, never says which light commit is the one released:
- in this plan's glossary, tip is the Isabelle commit that make-patches releases (plan:17);
- decision 16 point 7 (plan:808-810) says only '核 tested 记录里 light 仓库的状态';
- the natural candidate is the feature-repository commit that write step (e) tags, but the plan never says so.
Two concrete gaps follow.

(1) An existing tag is accepted on a rerun.
- Write step (e) (plan:815-816) accepts an existing feature-repository tag whose tree passes the check in (d).
- Step (d) checks only patches/<R>/*.patch and provenance.txt. It never looks at tools/component_files.txt or the files that list names.
- The release critic ran point 8 and gate (e), implemented literally, on a toy light repository (review-ipc5/critic-release/resume/stale_tag.out):
  - run 1 tags commit C1 in the light repository, then fails at the Isabelle tag;
  - the maintainer commits a fixed Light_Locale.thy and makes tested record 2;
  - the rerun passes gate (e) on record 2, accepts the old tag, and ships Light_Locale.thy b163d608, the bytes record 1 built, while HEAD has 8572e0ba.
- provenance.txt does not record the feature-repository commit (plan:810-811), so nothing downstream notices.

(2) The release commit takes in other staged changes.
- Write step (c) (plan:813-814) says to commit when patches/<R>/ differs, but gives no pathspec.
- In the shared feature repository, a plain git commit records every staged change into the release commit.
- I measured the path-limited form (review-ipc5/merge/c1). After the by-name `git add`, the `git rm --cached` and the deletion of the old file, `git commit -m … -- patches/R/` commits exactly the new file, the deletion and provenance.txt, and leaves another staged file staged.
- Point 7 already refuses staged changes to the listed files ('已提交且无改动'), so a change taken in this way cannot become shipped bytes. The harm is that an immutable, tagged release commit carries another agent's unrelated work.

Required:
- Point 7 defines ruling 35's 'commit to be released' as the feature-repository commit that write step (e) tags.
- Write step (d) runs on that commit, whether it is new or an existing tag. It checks patches/<R>/*.patch, provenance.txt, tools/component_files.txt and every file that list names against what gates 7 and (e) checked at HEAD.
  - For an existing tag, the check is `git diff --quiet <tag> HEAD -- patches/<R>/ tools/component_files.txt <entries>`.
  - If an existing tag differs, refuse, and say that the version number is used up.
- Write step (c) commits with `-- patches/<R>/` after the by-name add.

**Editor.** Points of fact:
- The round-4 judge's own C13 recipe (REVIEW4:1714) has no pathspec either. So (2) is a gap in the judge's action, not a silent deviation.
- The owner's CLAUDE.md does accept other agents' changes being swept into a commit. That rule covers an agent's own commit, whose message then describes the swept-in work. It does not fit an immutable, tagged release commit that a script writes.
- The fact that point 7 refuses staged changes to the listed files limits (2) to keeping the repository tidy.
- Part (i) of consistency-CONS-11 (which light commit is compared) is folded in here. Its other parts are in C10.

Severity is minor: (1) needs a component edit between a failed run and its rerun.

**Defender: confirmed** (needs owner: False).

I tried to refute each part and could not. I also found that the editor's argument on part (2) fails, and that the challenge's fix needs two corrections.

Core claim: the plan never says which feature-repository commit is released. CONFIRMED.
- Ruling 35 compares the shipped files "between the recorded HEAD and 要发布的 commit" (the commit to be released) (plan:153). The migration plan's §0 item 32 says the same (ISABELLE_GIT_MIGRATION_PLAN.md:137).
- The glossary gives that exact phrase to tip (plan:17). In make-patches, tip is the commit of the Isabelle branch (make-patches:89), and the migration plan's gate (e) reads tested records of the "待发布 commit", which is also the Isabelle commit (migration:400).
- Read by the glossary, then, the ruling asks for a diff across two repositories, which cannot run.
- Point 7 says only "核 tested 记录里 light 仓库的状态" (check the light repository's state in the tested record) (plan:810).
- The round-4 judge's action had used `HEAD` (REVIEW4 C10 Judge). The owner's question 3(a) said "the commit being released" (REVIEW4, owner questions). The plan defines neither.

Part (1), the stale existing tag. CONFIRMED, with one correction to the critic's example.
- Write step (e) accepts an existing feature tag whose tree passes (d) (plan:815-816), and (d) compares only patches/<R>/*.patch and provenance.txt.
- Provenance pins the Isabelle tip (make-patches:197), so only light-side files can drift without (d) noticing.
- Experiment release.out, scenario S1, reading A (the judge's HEAD): the rerun admits record 2 and ships the record-1 bytes b163d608, while HEAD has c3db37fc. This reproduces the critic's run.
- The correction: in that example the shipped bytes were built by record 1, so S1 alone does not show the title's "no tested build built". Under reading B (the commit to be released is the existing tag), S1 is internally consistent; the maintainer's fix is just silently left out.
- The title's claim is still true, through a different path. Point 7 checks the listed files only "运行前" (before the run starts) (plan:808-809). The light repository is shared (plan:809). Nothing re-checks the shipped files after the gates.
  - S2: another agent stages an edit to Light_Locale.thy while the gates run. The plain commit sweeps it in.
  - S3: another agent commits that edit while the gates run.
  - In both, under both readings, the tag ships bytes 74506dee that no record built. (d) passes.
- The batch workflow checks out the feature tag (plan:110, :612). It compares only the release_tag string (plan:591-592). Its linux-64 build passes on any file that compiles. So nothing downstream notices.

Part (2), the commit takes in other staged changes. CONFIRMED, and the harm is larger than the editor says.
- Rev 4 said "按路径提交 patches/<R>/" (commit by path) (rev4.md:691). Rev 5 says only "有差别才 commit" (commit if something differs) (plan:814). The plan's own example cites C13 as "`git commit -- 路径` 对新文件返回 0 却不提交" (a commit with a path returns 0 for new files without committing them) (plan:812).
- That failure happens only when nothing was staged first (commit_forms.out case 4). After the by-name add, a path-limited commit does include the new files (cases 2 and 3). So the citation does not justify dropping the path limit.
- §10.1's C13 row does not mention the drop (plan:1060). The judge's action had no pathspec either, so this is a regression from rev 4, not a silent deviation from the judge.
- Case 1 measures the plain commit: it commits another agent's staged README.md.
- The editor says the harm is only tidiness. That is refuted twice:
  - S2: point 7's start-of-run check does not stop a staged shipped file from being swept in.
  - The feature's own README is shipped in share/doc (plan:588), and for features without a component payload it is in no list that point 7 checks (plan:808-809).

The challenge's fix needs two corrections.
(a) `git commit -- patches/<R>/` is not exact. With a pathspec, git commits the working-tree content of every tracked file under that directory. Case 2 committed another agent's unstaged edit to a tracked patches/R/NOTES.md. Only a per-file list is exact (case 3). That list must also decide whether to commit: in rerun_cond.out the directory-wide condition said "differs" but the per-file commit had nothing to commit and returned rc 1.
(b) "`git diff --quiet <tag> HEAD`" uses the current HEAD. In S3 the current HEAD has moved, and for a new commit the comparison is with itself. The check must use the light HEAD that the gates checked, or the admitted record's HEAD.

With the corrected fix, S1 and S3 are refused, S2 ships the built bytes, and the positive control S4 (an unrelated light commit after the build) passes.

Severity minor and needs-owner false are right. Defining the commit as the one that is tagged is the plain reading of the owner's "the commit being released".

Experiment: All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C5/. They use git 2.43.0 with no global or system git configuration, and toy repositories only.

(1) commit_forms.sh, output in commit_forms.out. It runs rev 5's (b) and (c) steps: delete the old *.patch files, write new files, stage them by name, and `git rm --cached` the old ones. Another agent has a staged README.md and an unstaged edit to a tracked patches/R/NOTES.md.
- Case 1, plain commit: commits README.md.
- Case 2, `-- patches/R/`: commits NOTES.md v2 and leaves README.md staged.
- Case 3, per-file pathspec: commits exactly a.patch, b.patch, provenance.txt and the deletion of gone.patch, and leaves README.md staged.
- Case 4, the C13 shape (no add first, then `-- patches/R/`): rc 0, and provenance.txt stays untracked.

(2) rerun_cond.sh, output in rerun_cond.out. A rerun regenerates byte-identical files while another agent has staged NOTES.md under patches/R/. The directory-wide condition says "differs", the per-file condition says "same", and the per-file commit then returns rc 1.

(3) release.py, output in release.out. It runs point 7, ruling 35's gate (e), and write steps (b) to (f) on a toy light repository. A gate-time hook simulates another agent.
- Reading A (the current HEAD):
  - S1, stale tag: admits record 2 and ships the record-1 bytes.
  - S2, staged edit during the gates: ships 74506dee, which no record built.
  - S3, committed edit during the gates: ships 74506dee, which no record built.
  - S4, positive control: passes.
- Reading B (the existing tag): S1 is consistent but leaves out the fix; S2 and S3 still ship unbuilt bytes.
- Reading A plus the fix (per-file pathspec, and (d) comparing the component files of the tagged commit with the gate-time HEAD): S1 is refused, with "version 2 is used up"; S2 ships the built bytes; S3 is refused at (d); S4 passes.

(4) Read-only checks:
- plan:17, :151-155, :588, :591-592, :612, :808-817, :1057, :1060;
- rev4.md:690-693;
- make-patches:86-89, :159, :194-211, :255-258 (pristine already refuses an existing tag on a different commit);
- ISABELLE_GIT_MIGRATION_PLAN.md:33-36, :134-138, :400;
- REVIEW4 C10 and C13 (defender and Judge paragraphs), and owner question 3;
- `git -C contrib/light_locale ls-files patches` lists only *.patch files.

Recommended fix: Decision 16, the smallest fix.

(1) Point 7: add one sentence. In ruling 35, "要发布的 commit" means the feature-repository commit that write step (e) tags, whether it is new or an existing tag. make-patches records the feature-repository HEAD H at which point 7 and gate (e) run.

(2) Write step (c): use one path list L, the generated files plus the old *.patch files that were not regenerated.
- Stage L by name: `git add` and `git rm --cached`, as now.
- Decide with `git diff --cached --quiet -- L`.
- Commit with `git commit -m … -- L`.
- Correct plan:812's parenthesis. A path-limited commit loses new files only when they were not staged first. Do not use `-- patches/<R>/`: it commits the working-tree content of every tracked file under that directory.

(3) Write step (d) checks the commit to be tagged, the new commit or an existing tag:
- the blob ids of patches/<R>/*.patch and provenance.txt equal the generated ones;
- `git diff --quiet H <that commit> -- tools/component_files.txt <its entries>` holds.

(4) Write step (e): an existing tag that fails (d) is refused. The message names the tag, its commit and the files that differ, and says the version is used up and to release v+1 (migration §7 rule 14 forbids moving the tag).

(5) Point 9: add three toy cases: a rerun after (f) failed with a component edit committed in between (refused); a commit to a component file between the gates and (c) (refused); a staged unrelated file (left out of the release commit).

(6) §10.1's C13 row: name the dropped path limit (rev4:691) and the restored per-file form.

**Judge: confirmed → author_fixes_no_rereview.** Decision 16, points 7-9.

(1) Point 7:
- in ruling 35, 'the commit to be released' means the feature-repository commit that write step (e) tags, whether it is new or an existing tag;
- make-patches records the feature-repository HEAD H at which point 7 and gate (e) run.

(2) Write step (c) uses one path list L: the generated files plus the old *.patch files that were not regenerated.
- Stage L by name.
- Decide whether to commit with `git diff --cached --quiet -- L`.
- Commit with `git commit -m … -- L`.
- Never use `-- patches/<R>/`: it also commits unstaged edits to tracked files under that directory (judge/c5, defender-C5/commit_forms.out).
- Correct plan:812's parenthesis: a path-limited commit loses new files only when they were not staged first.

(3) Write step (d) checks the commit to be tagged, new or existing:
- the blob ids of patches/<R>/*.patch and provenance.txt equal the generated ones;
- for a package with a component payload, `git diff --quiet H <that commit> -- tools/component_files.txt <its entries>` holds.

(4) Write step (e): an existing tag that fails (d) is refused. The message names the tag, its commit and the differing files, and says the version is used up; release v+1.

(5) Point 9 adds three toys:
- a rerun after a failure at (f), with a component edit committed in between: refused;
- a commit to a component file between the gates and (c): refused;
- an unrelated staged file: left out of the release commit.

(6) The §10.1 C13 row names the restored per-file path limit, which rev 4 had (rev4:691).

### C6 [minor] The mandatory strong gate calls levels(tree, features_dir), but make-patches has neither a tree the chain logic accepts nor the lower features' patch files and provenance

Section: Decision 16 point 5 (plan:800-805); decision 8 levels (plan:475-477); decision 3 chain linking (plan:363-370)  ·  merged from: release-R5-REL-5, consistency-CONS-14

**Statement.** The core problem: rev 5 makes the gate 'every state fits exactly one level' mandatory, and tells make-patches to answer it with decision 8's levels(tree, features_dir). Nothing make-patches holds can be passed to that function.

What decision 16 point 5 asks (plan:800-805): for each file the new feature changes, take its content (or its absence) with git show at the chain bottom, at every lower release tag and at the tip. Then require 'the tool's level function (decision 8's levels, imported like apply_to)' to give each of these states exactly its own level.

Decision 8 defines that function as levels(tree, features_dir) (plan:476), and it builds the chain the way status does (decision 3, plan:363-370). That needs two inputs make-patches does not have:
- A tree with etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID. The Isabelle repository does not track etc/ISABELLE_IDENTIFIER: in contrib/Isabelle2025-2, `git ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists ISABELLE_ID but not ISABELLE_IDENTIFIER (I checked this). Decision 17 says the same of a git archive (plan:834-835).
- A features_dir that holds every lower feature's *.patch and provenance.txt, plus the new feature's. make-patches receives only the new feature's --package directory (make-patches:2, :267). The lower features' released patch files live in other repositories. The new feature's provenance.txt is written only at point 8 (b) (plan:813), after the gates have run.
As specified, the gate cannot be implemented without guessing where its inputs come from.

Required, if the relaxation below is not taken: state in point 5 how the inputs are assembled.
- For each lower chain tag: the generator's blocks between its base_tag and that tag. git diff-tree is plumbing and ignores diff.* configuration (review-ipc5/critic-release/cfg). Its provenance.txt comes from the tag annotation, which already embeds the provenance lines (make-patches:210).
- For the new feature: its blocks, plus a provisional provenance, from the temporary directory of point 8 (a).
- For each state: a temporary tree holding that state's content, etc/ISABELLE_ID, and a synthesized etc/ISABELLE_IDENTIFIER = <R>.
- A toy test that the regenerated lower blocks equal the released ones byte for byte.

**Editor.** This holds. Gate (c) does not have the same problem: apply_to and unapply_from (decision 8) take a single feature directory and read neither provenance nor the chain. That is why they work on a git archive today.

**Relaxation proposed by the editor.** Expose a per-file level function instead. It takes one file's content (or its absence) and the patch blocks that touch that file, in chain order, and returns the set of levels the file fits.
- status builds the chain from features.d and calls this function for each file.
- The gate already knows the chain order from its base_tag walk. It regenerates each lower feature's block for that file with the same generator make-patches releases with.
No synthesized tree, features.d or provenance is then needed. The gate and status share exactly the code that decision 6 defines, and decision 8 no longer needs levels(tree, features_dir) as a public function.

**Defender: confirmed** (needs owner: False).

I tried to refute C6 and could not. Its core claim holds, and in a slightly worse form than stated. Two of the critic's supporting details are wrong, and both affect only how the fix is worded.

What is confirmed
1. The function and what it needs.
   - Rev 5 tells the gate to use "decision 8's levels" (plan:802). Decision 8 defines that function as levels(tree, features_dir), returning the set of levels each file fits (plan:476).
   - Building the chain needs etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID in the tree (plan:350, plan:364). It also needs one subdirectory per chain feature, each holding provenance.txt and its *.patch files (plan:348-349, 365).
2. make-patches has neither input.
   - It is given only the new feature's package directory (make-patches:2, :267). Its blocks go into gate (c)'s temporary directory and have no provenance.txt until step 8 (b) (plan:813).
   - The Isabelle repository does not track etc/ISABELLE_IDENTIFIER. It is git-ignored (contrib/Isabelle2025-2 .gitignore:10), and `git ls-tree` of the pristine tag's etc/ lists ISABELLE_ID but no ISABELLE_IDENTIFIER. The plan itself says a git archive lacks the file (plan:834-835).
3. Gate (c) does not have this problem. apply_to does not read provenance (plan:474), which is why it works on a git archive. The editor's rebuttal is right.
4. Neither the plan nor section 10 says how the gate's inputs are assembled.
   - Point 5 specifies only the base_tag walk and the `git show` states (plan:800-805).
   - Section 10's C5 row says only "决定 8 公开 levels" (plan:1052).
   - Round 4's two prototypes of this gate both had to make the inputs up. review-ipc4/critic-engine/real/gen.py writes etc/ISABELLE_IDENTIFIER and provenance files by hand. review-ipc4/defender-C5/harness.py writes provenance files (prov() at :90-91, used at :107), and its toy repository tracks ISABELLE_IDENTIFIER (:97), which the real repository does not.

Stronger than stated
If the function is wired literally, the gate does not fail; it passes without checking anything (gate.out, line A0').
- With only a git archive, levels raises FileNotFoundError on etc/ISABELLE_IDENTIFIER.
- If an implementer adds that file and passes gate (c)'s temporary directory, there is no provenance.txt. By plan:348-349 the tool then reads "no feature packages installed" and returns no files at all. "Every state fits exactly its own level", checked over an empty result, passes.

What is overstated or wrong
1. "Nothing make-patches holds can be passed" is true only as stated. The inputs can be derived from the repository: the tag annotations carry the provenance lines (make-patches:194-210), and each lower feature's blocks can be regenerated with make-patches' own command (make-patches:154-169). My assembled version (route A1 in gate.py) works. So this is a gap in the specification, not an impossibility. Under the owner's never-guess rule it is still a real defect.
2. The critic says `git diff-tree` is plumbing and ignores diff.* configuration. Measured with git 2.43.0, that is false (cfg.out):
   - `-c diff.indentHeuristic=false`, `-c diff.suppressBlankEmpty=true` and `-c core.abbrev=12` all change diff-tree's output.
   - make-patches runs git with the user's own environment (tools/common.py:30-32).
3. "Regenerated lower blocks equal the released ones byte for byte" will stop holding in the real repository over time.
   - After 20,000 objects were added, the abbreviated ids on the `index` line grew from 7 to 8 hex digits (cfg.out). The real repository has about 5,400 objects today and grows with every daily advance.
   - This is harmless to the level computation: git apply ignores the `index` line. A garbage index line applied forward and in reverse identically.
   - So the invariant to test is "equal apart from the `index` line, with the generator's configuration pinned", not byte equality. A toy repository would pass the byte test while the real one later fails it.

The editor's relaxation is the better design, and I recommend it
- Decision 6 defines a level per file (plan:426-429). A per-file function is therefore exactly "the tool's own level function" that the round-4 judge asked for.
- status keeps decision 3's chain building and calls that function for each file. The gate calls it on `git show` contents and on the blocks for that file.
- Nothing has to be synthesized: no tree, no features.d, no provenance. The empty-result trap described above cannot happen.
- On the benign, xf3 (both of its releases) and revert toys, it gives the same verdicts as the assembled levels(tree, features_dir) route. The A1 and B lines in gate.out agree in every case.
- It needs fewer inputs and keeps decision 3 private to status and apply.
- The checks that the per-file function skips are already covered elsewhere in make-patches: one target per patch file (make-patches:164-166), the header checks in point 2-4, and gate (c), which goes through apply_to.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C6/.

gate.py and gate.out:
- ipc4.py is round 4's literal prototype of decisions 3-8, copied unchanged.
- The toy repository is shaped like the real one: etc/ISABELLE_IDENTIFIER is git-ignored, etc/ISABELLE_ID is tracked, and each release tag is annotated with the provenance lines, as make-patches:210 writes them.
- At each release, with the tip not yet tagged, the gate is run three ways:
  - A0: literal levels(tree, features_dir) on what make-patches holds, that is a git archive plus gate (c)'s temporary directory. The archive alone gives FileNotFoundError on etc/ISABELLE_IDENTIFIER. After adding that file, read_chain returns (None, None), meaning "no feature packages installed", so the gate would pass with nothing checked.
  - A1: assembled inputs, namely lower blocks regenerated with diff-tree, provenance taken from the tag annotations, a provisional provenance for the new feature, and a synthesized ISABELLE_IDENTIFIER.
  - B: the per-file function (ipc4.replay) on `git cat-file` contents.
- Results:
  - benign passes.
  - xf3 is refused at F2's release (tip fits [0,2]) and at F3's release (the F2 state fits [0,2]).
  - revert is refused.
  - A1 and B agree in every case.
  - In the toy, the regenerated lower blocks equal the released ones byte for byte.

cfg/, cfg2/ and cfg.out:
- git diff-tree output changes under `-c diff.indentHeuristic=false`, `-c diff.suppressBlankEmpty=true` and `-c core.abbrev=12`. It does not change under noprefix, mnemonicPrefix, context, interHunkContext or color.
- After a fast-import of 20,000 blobs, the regenerated diff's `index` abbreviations grew from 7 to 8 hex digits.
- git apply, run in the tool's environment forward and in reverse, gives identical results for the base, grown, suppressBlankEmpty and garbage-index variants.

Read-only checks:
- In contrib/Isabelle2025-2, `git ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists only ISABELLE_ID; .gitignore:10 ignores /etc/ISABELLE_IDENTIFIER; `git count-objects -v` shows about 5,400 objects; there is no diff.* or core.abbrev setting in local, global or system config.
- Read make-patches:2, 154-169, 194-210 and 267; tools/common.py:30-32; and round 4's real/gen.py and defender-C5/harness.py.

Nothing was modified outside the scratch directory.

Recommended fix: Take the editor's relaxation:
1. Decision 8 (plan:475-477): replace levels(tree, features_dir) with a per-file level function, for example file_levels(path, content, patches).
   - content is the file's bytes, or None when the file is absent.
   - patches lists, in chain order, the (feature number, patch file) pairs that change that path.
   - It returns the set of levels the file fits, by decision 6's definition, run in a fresh temporary directory.
   - status, apply and unapply call it for each file after decision 3 has built the chain. levels(tree, features_dir) is no longer public.
2. Decision 16 point 5 (plan:800-805): state the gate's inputs.
   - The chain order and each lower release's base_tag and commit come from the annotated tags' provenance lines (make-patches:194-210).
   - Each lower feature's block for the file is regenerated by the same generator function that point 8 releases with: `git diff-tree -r -p --no-renames <base_tag> <commit>`, split per file (make-patches:154-169).
   - The new feature's block comes from gate (c)'s temporary directory (point 8 (a)).
   - Each state's content comes from `git show <rev>:<path>`; a missing path means the file is absent.
   - Say explicitly that no tree, features.d or provenance file is synthesized.
3. Pin the generator. Measured: diff-tree honours diff.indentHeuristic, diff.suppressBlankEmpty and core.abbrev, and its index abbreviations lengthen once the repository passes 2^14 objects.
   - Release and regeneration share one function with fixed settings: `-c diff.indentHeuristic=true -c diff.suppressBlankEmpty=false`, or system and global config switched off.
   - Point 9's toy test compares the regenerated blocks with the released ones ignoring the `index` line (git apply ignores that line), not byte for byte.
4. Section 10's C5 row (plan:1052): change "决定 8 公开 levels" to name the per-file function, and say why: make-patches has no tree with etc/ISABELLE_IDENTIFIER and no features.d.

**Judge: confirmed → author_fixes_no_rereview.** Adopt relaxation 3.

(1) Decision 8 (plan:475-477) replaces the public levels(tree, features_dir) with a per-file function, for example file_levels(path, content, patches).
- content is the file's bytes, or None when the file is absent.
- patches lists, in chain order, the (feature number, patch block) pairs that touch the path.
- It returns the set of levels the file fits, by decision 6.
- status, apply and unapply call it for each file after decision 3 builds the chain.

(2) Decision 16 point 5 (plan:800-805) states the gate's inputs:
- chain order, and each lower release's base_tag and commit, come from the annotated tags' provenance lines (make-patches:194-210);
- each lower feature's block for the file is regenerated by the same generator function make-patches releases with (`git diff-tree -r -p --no-renames`, split per file, make-patches:154-169);
- the new feature's block comes from the temporary directory of point 8 (a);
- each state's content comes from `git show`.
No tree, features.d or provenance file is synthesized.

(3) Pin the generator: run it with system and global git config disabled, or with diff.indentHeuristic, diff.suppressBlankEmpty and core.abbrev fixed. Measured: diff-tree honours all three (defender-C6/cfg.out), which refutes the critic's claim that plumbing ignores them. The point 9 toy compares regenerated blocks with released ones ignoring the `index` line.

(4) The §10.1 C5 row names the per-file function, and why: make-patches has no tree with etc/ISABELLE_IDENTIFIER (the file is git-ignored) and no features.d.

### C7 [minor] The fix for edits written in place is only half done: the residue block still promises that reinstalling isabelle restores the package's files, §9 contradicts decision 15 about conda-meta, and the remedy text misses environments that share the edited file but report nothing

Section: §4 residue block (plan:896-897) and CONFLICT text (plan:884-887); decision 9 (plan:552-557); §9 (plan:1031-1032); decision 15 (plan:751-752, :756-757); §10.1 row C8 (plan:1055)  ·  merged from: consistency-CONS-3, hooks-H6, consistency-CONS-9

**Statement.** The core problem: an edit written in place through conda's hard link also changes conda's package cache, so `--force-reinstall isabelle` brings the edit back (§2.3, plan:247-249). Rev 5 fixed the CONFLICT text for this case, but not the other places the round-4 C8 judge named.

1. The residue block.
- The C8 judge required the unconditional '(restores the package's files' to be dropped from both the CONFLICT text and the residue block (REVIEW4:1150).
- Rev 5 added the detection and a second wording to the CONFLICT text only (plan:884-887).
- The residue block still says 'conda install -c … --force-reinstall isabelle (restores the package's files, deletes this environment's Isabelle user directory; …)' (plan:896-897).
- For an edit written in place this is false. Once the package is removed, status says 'no feature packages installed', so the edited source stays in isa/ with nothing pointing to it.

2. §9 versus decision 15.
- §9 (plan:1031-1032) says conda-meta's paths_data is read in two places, the second being decision 15's check_bytes.
- Rev 5's decision 15 (plan:751-752) takes check_bytes's reference data from the archives' info/paths.json and says check_bytes never reads conda-meta.
- The C8 judge said conda-meta is read only to choose the remedy text (REVIEW4:1157).
- check_bytes is test code and does not belong in a list of the tool's state sources.
- The C8 row (plan:1055) repeats the error ('§9 说明 conda-meta 的两处读').

3. Environments that report nothing.
- The remedy text says to reinstall 'here and in every other environment that reports this conflict' (plan:886-887; decision 9, plan:557).
- An environment created from the same cached isabelle build, but with no feature package touching that file (a plain isabelle environment, for example), shares the edited inode and never reports a CONFLICT.
- After the user deletes the extracted directory and reinstalls in the environments that do report it, that environment keeps the edit (review-ipc4/defender-C8/run.out, steps 2 and 7).

4. The detection reads 'conda-meta/isabelle-*.json' (plan:555). That pattern matches the record of every package whose name starts with isabelle- (isabelle-light-locale, isabelle-patch-control, …).

Required:
- Give the residue block the same two wordings as the CONFLICT text, chosen by the same test (samefile plus sha256). The single static line the judge also allowed would do as well.
- §9 says: the tool reads conda-meta's paths_data only to choose the remedy text for edits written in place; check_bytes uses the archives' info/paths.json.
- Widen the remedy to 'every environment on this machine that uses isabelle-2025.2-<b>, whether or not it reports this conflict'.
- Name the record as 'the conda-meta record of the package named isabelle'.
- Name all of this in the C8 row.

**Editor.** Items 1 and 2 are judge actions left undone without §10 saying so, and they stand. Items 3 and 4 criticise wording the judge itself proposed (REVIEW4:1150), so they are improvements to the text under ruling 17, not deviations. consistency-CONS-3 also asks decision 15 for a residue case with a hard-linked edit. That is optional: the judge asked only that the residue case's edit be written as a new inode, and plan:757 does that.

**Defender: partially_confirmed** (needs owner: False).

The core problem: when a file under $PREFIX/isa is still the same inode as conda's package-cache copy, an edit written in place changes the cache too. `--force-reinstall isabelle` then links the edited copy back and restores nothing (plan:247-249). Items 1, 2 and 4 hold, item 1 only in a narrower form. Item 3 is factually true, but it is an optional wording improvement, not a deviation.

ITEM 1: CONFIRMED, NARROWED
- What the judge required: the C8 judge said to drop the unconditional "(restores the package's files" from both the CONFLICT text and the residue block (REVIEW4:1150).
- What rev 5 did: it added the second wording to the CONFLICT text only (plan:884-887). The residue block still makes the promise (plan:896-897). Decision 9's residue bullet (plan:547-551) has no in-place-edit case.
- Why it is silent: §10.1 row C8 says only "§4 两种文案" (plan:1055) and never says the residue block was left out. That is a silent deviation from an author_fixes action.
- Where the challenge overreaches: "for an edit written in place this is false" is too broad. Every file the tool installs is a fresh inode (os.replace, decision 5, plan:400-401). An in-place edit made after the feature was applied therefore stays private, and the plain reinstall does restore it. My run.out S1 shows this: A's file got inode 10069775 with nlink 1, the cache was untouched, and the reinstall brought back the pristine file.
- Where the promise is false: a residue file that is still the cache inode. This shape is reachable. The user edits a pristine file in place. Installing F then gives a CONFLICT. Decision 7's cap (plan:454-455) leaves F's files untouched, so the file stays the cache inode. Removing or replacing F then writes a residue block that lists the file: plan:547 says "不论原因是 CONFLICT", the example is at plan:891-893, and the test at plan:776. My run.out S2 shows the plain reinstall leaving the edit in place with rc 0.
- Worse, on replacement: if F is replaced, one conda output prints the old F's residue block ("the reinstall restores the files") and then the new top F's CONFLICT text ("a plain reinstall keeps it"). The two remedies contradict each other.
- Side note on wording: plan:547's literal trigger "层级 ≥ k" would exclude a CONFLICT file that matches no level at all. The C11 judge's wording, "the feature's own files that did not return below k" (REVIEW4:1480), includes it, and so do the plan's own example and test.

ITEM 2: CONFIRMED
- §9 (plan:1032) says conda-meta's paths_data is read in two places, the second being check_bytes.
- Decision 15 (plan:751-752) and §6 (k) (plan:960) say check_bytes takes the archives' info/paths.json and never reads conda-meta. That was the round-4 C15 judge's own action (REVIEW4:1925).
- The C8 judge said conda-meta is read only to choose the remedy text (REVIEW4:1157).
- §10.1 row C8 repeats the false "两处读" (plan:1055).
- §9 also leaves out extracted_package_dir, which the detection test reads as well (REVIEW4:1135, :1151).

ITEM 3: FACT TRUE, BUT NOT A DEVIATION
- The text uses the judge's own wording (REVIEW4:1151).
- My run.out S2' confirms the fact. After the extracted directory is deleted and A (the only environment reporting the CONFLICT) is reinstalled, a plain isabelle environment still has the edit (inode 10069692, nlink 1) and reports nothing.
- The same leak happens under the ordinary wording: in review-ipc4/defender-C8/run.out step 7, Y kept the edit after X was repaired. So a fix confined to the cache wording is incomplete.
- The proposed widening, "every environment that uses isabelle-2025.2-<b>", takes in too many environments. Some do not share the inode: those whose file the tool has already replaced, and those linked from an earlier extraction (the owner's machine today, REVIEW4:1087). A needless reinstall deletes that environment's user directory (plan:877-879). Under ruling 17 the author picks the wording; this is optional.

ITEM 4: CONFIRMED AS A PRECISION DEFECT (the judge wrote the same glob, REVIEW4:1151)
- On the owner's machine, /home/qiyuan/miniconda3/envs/isabelle/conda-meta has 8 files matching isabelle-*.json: isabelle-2025.2-0 plus isabelle-ai, -mcp, -minilang, -performant-ml, -rpc, -semantic-data and -semantic-embedding.
- Only the record whose name is "isabelle" holds isa/ paths (24535 of them) and extracted_package_dir=/home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0.
- Decision 9 never says where "<缓存里解开的包目录>" comes from, and §4 hard-codes <pkgs>/isabelle-2025.2-<b>/.

ON THE EDITOR'S REBUTTAL
- I agree that items 1-2 stand and that items 3-4 are ruling-17 wording improvements.
- I agree that a decision 15 residue case with an edit through the hard link is optional, because plan:757 does what the judge asked. If the residue block gets the second wording, though, the S2 shape is the natural test for it.

Severity: minor. No data is lost. These are text and record defects.

Experiment: I ran everything in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C7/.
- Files: run.sh; tool_sim.py, which simulates decision 5's os.replace install and decision 9's samefile+sha256 test; mkchan.py, copied from review-ipc4/defender-C8.
- Output: run.out.
- Setup: conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and a toy noarch package `isa`.

Steps:
- (0) Created environment A and a plain environment (no feature) from one cache. b.ML has one inode in both environments and in the cache: 10069692, nlink 3.
- (S1) Simulated the tool applying F in A (os.replace), then made a same-size in-place edit. A got a new inode, 10069775 with nlink 1. The cache and the plain environment were untouched. The test chose "ordinary", and a plain --force-reinstall restored A. So the residue block's claim is TRUE in this shape.
- (S2) Made an in-place edit of the still-pristine file (the CONFLICT-at-install shape; the capped apply never touches it). A, the plain environment and the cache all changed. The test chose the cache remedy. The residue block's plain --force-reinstall left A edited, rc 0. So the claim is FALSE in this shape.
- (S2') Followed the CONFLICT text's remedy in A only: deleted the extracted directory and reinstalled. A was restored (new inode 10071530). The plain environment kept the edit (inode 10069692, nlink 1) with nothing reporting it. A plain reinstall there fixed it.

Read-only checks on the owner's machine:
- python/json over /home/qiyuan/miniconda3/envs/isabelle/conda-meta: 8 isabelle-*.json records; only name=="isabelle" has isa/ paths and the right extracted_package_dir.

Plan and review lines checked:
- plan:247-249, 400-401, 454-455, 547-557, 751-757, 776, 877-899, 960, 1031-1032, 1055, 1148-1149
- REVIEW4:1087, 1135, 1150-1161, 1480, 1925
- review-ipc4/defender-C8/run.out, steps 2, 5 and 7

Recommended fix: These are author edits under ruling 17. No owner question is needed.

1. §4 residue block (plan:896-897). Drop the unconditional "(restores the package's files". Choose between two wordings with decision 9's test (samefile plus sha256), applied to the listed files:
   - If any listed file passes the test, the reinstall step becomes the in-place-edit line of plan:885-887.
   - Otherwise write "(replaces every file of the isabelle package, deletes …)".
   In decision 9's residue bullet (plan:547-551), add that the remedy is chosen by the same test. The judge's single static line would also do. Optionally, align plan:547's trigger with REVIEW4:1480 ("自己 feature 的文件中没有回到 k 以下的"), so that CONFLICT files are listed by definition.

2. §9 (plan:1032). Replace the sentence with: "`conda-meta` 只在一处读：决定 9 从名为 `isabelle` 的那条记录取 `extracted_package_dir` 与 `paths_data`，只为选经硬链接原地编辑的修复文案，从不作状态来源；决定 15 的 `check_bytes` 用包归档的 `info/paths.json`，不读 `conda-meta`。"

3. Decision 9 (plan:555) and §4 (plan:886).
   - Replace `conda-meta/isabelle-*.json` with "conda-meta 里 `name` 为 `isabelle` 的那条记录（`conda-meta/isabelle-2025.2-<b>.json`）".
   - Say that "<缓存里解开的包目录>" is that record's `extracted_package_dir`.
   - Print that path in place of `<pkgs>/isabelle-2025.2-<b>/`.

4. Optional (item 3). Add one sentence to both CONFLICT wordings and to the residue block: "Other conda environments created from the same package cache may share this file and carry your edit without reporting anything; reinstall isabelle there too." An exact variant: print it only when st_nlink - 1 - [samefile with the cache] > 0. Here st_nlink counts the paths that share the file, so this is a count of sharers, not the cache test the judge rejected.

5. §10.1 row C8 (plan:1055). Name the residue-block change, the §9 correction (one read, check_bytes from the archives) and the record naming. Drop "§9 说明 conda-meta 的两处读".

**Judge: partially_confirmed → author_fixes_no_rereview.** Items 1 and 2 are silent deviations from the C8 judge. Items 3 and 4 are optional improvements to text the judge itself wrote.

(1) §4 residue block (plan:896-897): drop the unconditional '(restores the package's files'. Choose between the CONFLICT text's two wordings with decision 9's test (samefile plus sha256) applied to the listed files: the in-place line from plan:885-887, or '(replaces every file of the isabelle package, deletes …)'. The judge's single static line would also do. Say the same in decision 9's residue bullet.

Optionally, align plan:547's trigger with REVIEW4:1480: 'the feature's own files that did not return below k'. That wording includes CONFLICT files that fit no level.

(2) §9 (plan:1032): conda-meta is read in one place only. Decision 9 reads extracted_package_dir and paths_data from the record of the package named isabelle, only to choose the remedy text for edits written in place. check_bytes uses the archives' info/paths.json.

(3) Decision 9 (plan:555) and §4 (plan:886):
- name 'the conda-meta record whose name is isabelle', not isabelle-*.json, which matches eight records on the owner's machine;
- print that record's extracted_package_dir in place of <pkgs>/isabelle-2025.2-<b>/.

(4) Optional: one sentence saying that other environments made from the same package cache may share the edited file without reporting anything, so the reinstall is needed there too.

(5) The C8 row names all of this and drops '两处读'.

### C8 [minor] Two C17 actions are not done: the release note's conda command still lacks the channel flags, and the smoke job, said to run the README's install command verbatim, installs a different package

Section: Decision 12 point 8 (plan:679); decision 9 frozen `||` texts (plan:516, :524); decision 11 smoke (plan:631-633); decision 14 (plan:711); §10.1 row C17 (plan:1064)  ·  merged from: hooks-H7, release-R5-REL-4, consistency-CONS-10

**Statement.** The core problem: before the first publish, every user-facing conda command must carry both channel flags, -c https://conda.qiyuan.me -c conda-forge. The round-4 C17 judge required this because a user who installed the way the README says has the channels only on the command line; an environment-level .condarc is not honoured with -n (review-ipc4/defender-C17/run4.out). The judge named the pre-unlink line and the release note in particular. The judge also asked, as an option, that the smoke job run the README's install command verbatim (REVIEW4:2103-2106).

1. The release note.
- Decision 12 point 8 (plan:679) still says '由 conda install isabelle-expose-foreign 提供'.
- §4's convention of abbreviating the flags as '-c …' (plan:856) covers only the texts that follow it in §4. The release note is text for the isabelle package description and for two documents.
- Without the channels, this command fails with PackagesNotFoundError (REVIEW4 C17, critic-user/run1.out case 4b).

2. The frozen `||` pre-unlink texts (plan:516, :524).
- They carry both flags for reinstalling the tool, but give the next step as prose: 'then install <包名> together with …'. A user types that as a conda install without flags.
- These texts are frozen for 1.x (plan:334-336). The rewrite in challenge C1 spells the step out as a command.

3. The smoke job.
- It 'runs the README install command verbatim' as `conda create -n t -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches` (plan:631-633).
- The README's install command in decision 14 is `… isabelle isabelle-light-locale` (plan:711).
- So the documented command is still not the tested one, and making them the same was the point of the optional action (REVIEW4:2093, :2106).

4. The §10.1 C17 row (plan:1064) says '钩子片段与残留块同' and '决定 11 冒烟原样跑 README 的命令', and does not mention the release note.

Required:
- The release note writes `conda install -c https://conda.qiyuan.me -c conda-forge isabelle-expose-foreign`.
- The `||` texts spell the step as a command (see C1).
- The smoke job takes the install command from the unified README text and runs it unchanged. If coverage of the whole chain after publication is wanted, it also runs `… qiyuan-dev-patches` as a second command, named as such.
- Correct the C17 row.

**Editor.** hooks-H7 also counts decision 9's remedy list, 'conda install <残留块点名的包>' (plan:558-559), as a user-facing command without flags. It is design prose that describes the remedy. The user-facing residue block in §4 (plan:898) carries the flags under the convention at plan:856. I dropped that sub-point.

**Defender: confirmed** (needs owner: False).

I could not refute any of the four parts. Each claim is visible in the plan text, and my own toy-channel run reproduces the failures.

Background. The round-4 C17 judge (REVIEW4:2104) required the two channel flags, `-c https://conda.qiyuan.me -c conda-forge`, on every other user-facing conda command before the first publish. The judge named the pre-unlink line and the release note in particular. Optionally, the smoke job was to run the README's install command verbatim (REVIEW4:2106; the defender's elegance item at REVIEW4:2093). Rev 5 even states the rule itself in decision 9: every conda command the user is to type carries both flags (plan:511-512). Each place below breaks that rule.

1. Release note: confirmed, and not mentioned anywhere in section 10.
- Decision 12 point 8 still says `Foreign`... are provided by `conda install isabelle-expose-foreign` (plan:679), with no flags.
- The abbreviation convention at plan:856 covers only the texts after it in section 4 ("下文"). Decision 12 comes before it.
- Unlike decision 9's remedy list, the release note has no separate user-facing text anywhere else in the plan. Decision 12 point 8 is the only place its sentence is specified, so the editor's "design prose" argument does not reach it.
- Measured (run.out cases 1b and 1c): in an environment created the way the README says, the flagless command fails with PackagesNotFoundError, both with `-n` and when the environment is activated. With the flags it installs (case 1d).
- The command is a silent no-op only when the package is already installed as a dependency (case 1).

2. The frozen `||` pre-unlink texts: confirmed.
- plan:516 and :524 put the flags on the first command, the tool reinstall. The second step is prose: "then install <包名> together with every other feature package this command removed; then remove them again".
- Rev 4's line (rev4.md:475) had a literal `conda install <包名>`. The C17 judge asked for flags on it. Rev 5 followed the C11 judge's paraphrase (REVIEW4:1477) and turned the step into prose without flags. The author had already turned the C11 judge's "make the tool runnable" into a command with flags, so the install step should have been treated the same way.
- Measured (case 2b): after the removal, a flagless `conda install isabelle-light-locale` gives PackagesNotFoundError. With the flags it works (2c). `conda remove` needs no flags (2d, exit 0), so only the install step needs fixing.
- No section 10 row names this. The C17 row says "钩子片段与残留块同", but by the glossary (plan:37) 钩子片段 means the post-link fragment, and 残留块 means the residue block in section 4. The pre-unlink `||` text is neither.
- One correction to the challenge's framing. plan:334-336 freezes the interface the hook text calls, and says that published copies cannot change. Every new `isabelle` build re-renders and republishes every feature package (ruling 22, plan:91-95), so later builds can carry corrected wording. Only the builds already published keep the old text. This lowers the cost of fixing it later, but the judge's "before the first publish" still stands.

3. Smoke job: confirmed.
- plan:631-633 says it "原样跑 README 的安装命令" (runs the README's install command verbatim), then gives `… isabelle qiyuan-dev-patches`.
- The README's install command in decision 14 is `… isabelle isabelle-light-locale` (plan:711). Every feature README starts with the same unified text (plan:588), and decision 13's README contents (plan:695-699) contain no `qiyuan-dev-patches` install command. So no README contains the smoke's command.
- Measured (case 3): the two commands produce different environments (one adds qiyuan-dev-patches) and different explicitly requested specs in history. That means pruning on removal also differs. The documented command is still not the tested one.
- I checked one possible new defect and rejected it. Rev 5 dropped `--override-channels` from the smoke (rev4.md:552 had it). On GitHub runners this does not cause a CondaToSNonInteractiveError: the conda Terms-of-Service plugin auto-accepts when CI is set (conda_anaconda_tos/console/render.py:327-336). Dropping the flag also matches what users do.

4. The section 10.1 C17 row (plan:1064): confirmed.
- It claims "决定 11 冒烟原样跑 README 的命令" (decision 11's smoke runs the README's command verbatim), which is false (point 3).
- It omits both the release note and the pre-unlink `||` step.
- Its other claims are true: section 4's commands carry the flags (plan:872, 880, 886, 896, 898, 905-906), and so does the post-link fragment (plan:489, 491, 501, 505).

Editor's rebuttal (dropping the decision-9 remedy list, plan:558-559): I agree. Decision 9 says "诊断按原因给修法（§4）" (plan:552), which points to section 4 as the source of the actual texts, and the user-facing block at plan:898 carries `-c …` under plan:856. Adding the flags to plan:559 as well would be a cosmetic consistency edit, not a requirement.

Line checks: all citations in the challenge match rev 5 (plan:334-336, 516, 524, 558-559, 631-633, 679, 711, 856, 898, 1064; REVIEW4:2093, 2103-2106). review-ipc4/defender-C17/run4.out does show that an environment-level .condarc is not honoured with `-n`.

Severity: minor is right. The release-note and `||` failures are loud (PackagesNotFoundError), and the smoke mismatch is a false claim in the plan about itself plus a coverage gap. These are wording and test edits under ruling 17, so the owner is not needed.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C8/.

Setup:
- src/mkchan.py, my own generator, builds a toy noarch channel: isabelle 2025.2 build 1, isabelle-patch-control 1.0.0, isabelle-expose-foreign 1, isabelle-light-locale 1 (depends on expose-foreign) and qiyuan-dev-patches 1 (depends on light). Every feature package is pinned to `isabelle 2025.2 1`.
- src/run.sh runs conda 25.11.1 (libmamba) with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS. The condarc lists only an empty stand-in channel for conda-forge, as for a user who never ran `conda config --add channels`. Environment and package directories are deleted at the end. Output is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C8/run.out.

Results:
- Case 0: the README-style `conda create -n u -c CH -c forge isabelle isabelle-light-locale` succeeds.
- Release note (plan:679) as written:
  - Case 1: it is a no-op with exit 0 when expose-foreign is already installed as a dependency.
  - Cases 1b and 1c: in a plain isabelle environment it gives PackagesNotFoundError, exit 1, both with `-n` and activated.
  - Case 1d: with the flags it installs.
- The `||` text after light was removed:
  - Case 2a: step 1, which carries the flags, works.
  - Case 2b: step 2 typed without flags gives PackagesNotFoundError.
  - Case 2c: step 2 with the flags works.
  - Case 2d: step 3, `conda remove` without flags, works.
- Case 3: the smoke command (plan:632) and the README command (plan:711) give different environments (one adds qiyuan-dev-patches) and different history specs: ['qiyuan-dev-patches','isabelle'] vs ['isabelle','isabelle-light-locale'].

Sources read:
- The plan in full, focused on 37, 91-95, 334-336, 481-568, 588, 598-648, 650-687, 706-724, 837-907, 1042-1071.
- rev4.md:475, 552, 591.
- REVIEW4 C11 judge (:1472-1486) and C17 (:2027-2106).
- review-ipc4/defender-C17/src/run1.sh, run1.out cases 4-5, run4.out.
- channel-banner.html:6, :10.
- Isabelle_RPC release-conda.yml:367-376.
- conda_anaconda_tos console/render.py:320-336.

Recommended fix: Wording and test edits only (ruling 17):
1. plan:679, the release note: write `conda install -c https://conda.qiyuan.me -c conda-forge isabelle-expose-foreign`.
2. plan:516 (.sh) and plan:524 (.bat): replace the prose step with commands, for example: "…; then: conda install -c https://conda.qiyuan.me -c conda-forge <包名> <every other feature package this command removed>; then: conda remove <the same packages>". `conda remove` needs no flags (measured).
3. plan:631-633, the smoke: run the README's command with `<env>` = t, `conda create -n t -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale`. A more elegant version takes the line from the unified-text file the renderer copies, so the documented command and the tested command cannot drift apart. If whole-chain coverage after publication is wanted, add a second command named as such: `conda create -n t2 -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches`.
4. plan:1064, the section 10.1 C17 row: list the release note and the pre-unlink `||` texts, and describe the smoke exactly as it now runs.
Optional: add `-c …` to `conda install <残留块点名的包>` at plan:559 for consistency. The editor's drop of this sub-point is otherwise sound.

**Judge: confirmed → author_fixes_no_rereview.** (1) plan:679, the release note: `conda install -c https://conda.qiyuan.me -c conda-forge isabelle-expose-foreign`.

(2) The || texts spell the step as commands, as in C1.

(3) The smoke job (plan:631-633) runs the README's install command unchanged (plan:711, isabelle isabelle-light-locale). Preferably it reads that line from the unified-text file the renderer copies, so the documented and the tested command cannot drift apart (relaxation 5). If whole-chain coverage after publication is wanted, it also runs `… isabelle qiyuan-dev-patches` as a second command, named as such.

(4) Correct the §10.1 C17 row: list the release note and the pre-unlink || texts, and describe the smoke exactly as it now runs.

The editor's drop of plan:558-559 stands; adding the flags there is optional.

### C9 [minor] §6 (f) asks for a CONFLICT that survives `--force-reinstall isabelle` after a tracked file is broken; only an edit written in place gives that, and it corrupts the leg's package cache. §6 (h) has no defined starting state

Section: §6 (f), (h) (plan:950-956); decision 11 build output (plan:615-616)  ·  merged from: release-R5-REL-3

**Statement.** The core problem: two acceptance scenarios cannot be run as written.

(f) (plan:950-951) has two halves: first 'break a tracked file, then install', then '--force-reinstall isabelle while the CONFLICT is still there → still exactly one full diagnosis'. The second half comes from the C3 judge (REVIEW4:544-546). There are two ways to break a tracked file:
- An edit that writes a new file (a new inode). The reinstall undoes it, so the second half cannot hold (review-ipc3/defender-C27/run.out, environment a).
- An edit written in place. It survives only because it goes through the hard link into the package cache (environment b). That changes `<pkgs>/isabelle-2025.2-<b>/isa/<file>`, so every later scenario on that leg that creates an environment from the same build starts in CONFLICT.
§6 runs every scenario on one runner and says each starts from a new environment (plan:939). But environments share the leg's package cache (§2.3, plan:247-249), and only the hook-layer test uses a private CONDA_PKGS_DIRS (plan:758). The C12 judge already suggested the right shape for the case where only isabelle is reinstalled: a file created by a feature, holding other content (REVIEW4:1589).

(h) (plan:955-956) runs `conda update --all` from an environment on an older isabelle build. The build job outputs only a boolean, isabelle_rebuild (plan:616). §6 says neither how that starting environment is made nor which older build it uses.

Required:
- (f): make the CONFLICT that survives a file created by a feature, holding other content. conda does not track that file, the reinstall leaves it alone, and the cache stays clean. Alternatively, run the in-place variant inside a private CONDA_PKGS_DIRS and end it with decision 9's repair.
- (h): let the build job output the old isabelle build string, empty meaning 'skip'. The leg then creates `isabelle=2025.2=<old>` plus the installed chain from the live channel and conda-forge, and runs `conda update --all` with accept's three channels.

**Editor.** This holds. For (h), a leg could also build the starting state without a new output: create the environment from the live channel alone, and the solver picks the features pinned to the old build. The plan states neither approach, and an explicit build-string output is the more deterministic of the two.

**Defender: confirmed** (needs owner: False).

I tried to refute both halves and could not. Both hold. Three of the challenge's citations are slightly off, but the substance does not depend on them.

What §6 (f) asks for. Scenario (f) (plan:950-951) has two halves. First, break a tracked file and then install a feature package. Second, run `--force-reinstall isabelle` "而 CONFLICT 仍在" (with the CONFLICT still there) and expect exactly one full diagnosis.

Why the second half cannot hold for an ordinary edit. The plan itself names `--force-reinstall isabelle` as the repair for exactly this CONFLICT: a user-edited tracked file (decision 9, plan:552-553). It keeps that remedy from failing only in one case, the edit written in place through the hard link, where it gives a separate repair (plan:553-557). That edit is the one that changes the package cache (§2.3, plan:247-249). This is already measured with real conda 25.11.1, using the rev-5 hook shape (re-run only; only the top feature writes the full diagnosis):
- review-ipc4/defender-C3/run-relaxed.out:116-137 (B8 then B9). A tracked-file CONFLICT followed by `--force-reinstall isabelle` is repaired: all files applied, FULL=0. So the second half as written observes zero full diagnoses, not one.
- run-relaxed.out:42-56 (B3). A file created by a feature, holding other content, survives `--force-reinstall isabelle` with FULL=1. That is exactly the shape the challenge proposes.

A file written in place survives only by going through the cache. I measured that the damage spreads (review-ipc5/defender-C9/run.out):
- The plainest shell idiom, `echo ... >> file`, writes through the hard link into `pkgs/<isabelle>/isa/...`.
- Every later new environment created from that build (B, X and Y in run.out) starts with the broken file. conda prints only a SafetyError warning and exits rc 0.
- `sed -i` (which writes a new inode) is undone by the reinstall and leaves the cache clean.

So the risk reaches the FIRST half of (f) as well. The plan never says how to break the file. Done with `>` or `>>`, the first half corrupts the leg's cache, and it also makes the second half "pass" for the wrong reason. Why this matters on the legs:
- §6 runs all scenarios of a leg on one runner, each from a new environment (plan:939, decision 11 plan:621-625).
- The only private CONDA_PKGS_DIRS anywhere is in the hook-layer test (plan:758). The accept legs share the runner's cache.
- No workflow caches pkgs across runs (build.yml:149-191 caches only the hg clone), so the damage stays within one leg.
- Scenarios (g), (j) and the end state of (h) would hit the corrupted build.

The proposed fix can be run with the real packages. Light creates three files: src/Pure/exported_premises.ML, src/Pure/more_exported_premises.ML and src/Pure/Isar/light_locale_axiom_facts.ML (their patches in contrib/light_locale/patches/Isabelle2025-2 start from an empty file). conda does not track these paths, so the reinstall leaves them alone.

§6 (h). The build job's only output for it is the boolean `isabelle_rebuild` (plan:615-616). Decision 11 requires every environment to use the three channels local, live and conda-forge (plan:624-625). Under that list a fresh create resolves to the new build. So the starting state, an environment on an older build, needs the old build string, and no job outputs it.

The proposed shape works. pintest/envs/e3/conda-meta/history shows `create isa=1.0=1 featb` followed by `update --all` moving to isa 1.0-2 with the re-released features, with the explicit pin neutered to `isa==1.0`.

The editor's alternative (create from the live channel alone, no pin) has two problems:
- It needs a written exception to decision 11's rule for all environments.
- It fails under the definition of `isabelle_rebuild` the plan actually adopted (the C15 judge's, REVIEW4:1930; plan:616). That definition is true whenever live still holds an older build of some listed (F, v). Sweeps are manual and chosen by the owner (sweep-old-versions.py:1-30), so this is the normal state after any earlier isabelle bump; the plan's own HOL-only light example is one case. There, a live-only create lands on `isabelle_build` itself, `update --all` leaves isabelle where it is, and (h)'s assertion "isabelle upgrades" fails. An explicit old-build output avoids this and replaces the boolean rather than adding a second output.

Citation slips in the challenge (they do not change the finding):
- The C3 judge's action is at REVIEW4:543, not :544-546.
- REVIEW4:1589 is the C12 defender's "recommended alongside" text, not the judge's paragraph (:1591-1600).
- In review-ipc3/defender-C27/run.out, "environment a" is actually file a.ML inside one environment.

§10.1 does not mention either issue. Both are defects rev 5 introduced by adding the C3 judge's shape and the C15 output; neither is a silent deviation from a judge action.

Experiment: New: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C9/run.sh writes run.out next to it. It uses real conda 25.11.1 with a private HOME, CONDARC and pkgs directory, and a toy noarch `isa` package (the generator is copied from review-ipc3/defender-C27/mkchan.py).
- (1) In env A, `echo '(* broken *)' >> isa/src/b.ML`: the cache copy changes too (same inode, nlink 2).
- (2) A NEW env B created afterwards from the same cache gets the broken b.ML, with only a SafetyError warning, rc 0.
- (3) In env X, `sed -i` on a.ML makes a new inode. `--force-reinstall isa` restores it; the cache is untouched.
- (4) A later env Y has a clean a.ML but still inherits the broken b.ML.

Reused measurements:
- review-ipc4/defender-C3/run-relaxed.out (rev-5 hook shape). B8 then B9 (:116-137): a tracked-file CONFLICT is repaired by `--force-reinstall isabelle`, FULL=0. B3 (:42-56): a created file holding other content survives the reinstall, FULL=1.
- review-ipc4/defender-C8/run.out: an in-place edit spreads to a second environment and needs the extracted cache directory deleted.
- pintest/envs/e3/conda-meta/history: `create isa=1.0=1 featb` then `update --all` gives isa-1.0-2 plus feata/featb T_1, with "neutered specs: ['isa==1.0']".

Read: plan:203-285 (§2.3), :481-568 (decision 9), :598-648 (decision 11), :726-790 (decision 15), :936-962 (§6), :1042-1116 (§10); REVIEW4:448-546 (C3), :1488-1600 (C12), :1846-1931 (C15); light_locale patch headers; sweep-old-versions.py:1-30; build.yml:140-195; Isabelle_RPC release-conda.yml:195-215.

Recommended fix: Ruling 17 lets the author make these changes; no ruling is touched.

(1) §6 (f) (plan:950-951): split it into two scenarios.

(f1) Fresh environment with isabelle and the tool. Replace a tracked file that light patches with a NEW file holding other content, using `sed -i` or a temp file plus `mv`. Never use `>`, `>>` or an editor that writes in place: they write through the hard link into the leg's package cache, and every later environment of that build inherits the edit (§2.3; review-ipc5/defender-C9/run.out). Then `conda install isabelle-light-locale`. Expect: exactly one full diagnosis with the tracked-file wording, `status` shows CONFLICT with the features below it applied, the environment stays usable. Then run `--force-reinstall isabelle`, the repair decision 9 documents (plan:552). Expect: `status` all applied, no diagnosis.

(f2) Fresh environment. Put other content at a path light creates, for example `isa/src/Pure/exported_premises.ML`. Install light. Expect one full diagnosis with the created-file wording. Then `--force-reinstall isabelle`. Expect the CONFLICT to survive (conda does not track that path) and still exactly one full diagnosis.

Use the same phrase, "a file created by a feature, holding other content", for the shape "--force-reinstall isabelle 而 CONFLICT 仍在" in decision 15 (plan:770). The hook-layer test shares one private pkgs directory across all its scenarios, so the same risk applies there.

If the owner wants the in-place diagnosis exercised on the real legs: give that one scenario its own CONDA_PKGS_DIRS and end it with decision 9's repair (delete the extracted directory, then reinstall).

(2) Decision 11 (plan:615-616) and §6 (h) (plan:955-956): replace the boolean `isabelle_rebuild` with an output `isabelle_old_build`. It is the highest isabelle build string other than `isabelle_build` that a live record of a listed (F, v) pins; this is the lookup `plan_builds` already does. Empty means skip (h).

(h) then:
- `conda create --override-channels -c https://conda.qiyuan.me -c conda-forge isabelle=2025.2=<old> <the batch's top feature package> isabelle-patch-control`. Use the live channel plus conda-forge only, because the local channel's features pin the new build. State this as the one exception to decision 11's rule for all environments.
- Then `conda update --all` with accept's three channels.
- Assert that isabelle is now `isabelle_build`, every feature's `depends` pins it, and `status` is all applied.

Update §10.1's C15 row to name the changed output.

**Judge: confirmed → author_fixes_no_rereview.** (1) Split §6 (f) (plan:950-951) into two scenarios.
- (f1): replace a tracked file that light patches with a NEW file holding other content (sed -i, or a temp file plus mv). Never use > or >> or an editor that writes in place: that writes through the hard link into the leg's package cache (defender-C9/run.out). Install light. Expect one full diagnosis, CONFLICT with the features below it applied, and a usable environment. Then --force-reinstall isabelle repairs it: all applied, no diagnosis.
- (f2): put other content at a path light creates, for example isa/src/Pure/exported_premises.ML. Install light. Then --force-reinstall isabelle: the CONFLICT survives, because conda does not track that path, and there is still exactly one full diagnosis.
- Use the (f2) shape for '--force-reinstall isabelle 而 CONFLICT 仍在' in decision 15 (plan:770).
- If the owner wants the in-place diagnosis tested on the real legs, that one scenario gets its own CONDA_PKGS_DIRS and ends with decision 9's repair.

(2) Decision 11 (plan:615-616) and §6 (h): replace the boolean isabelle_rebuild with an output isabelle_old_build, the highest isabelle build string other than isabelle_build that a live record of a listed (F, v) pins. Empty means skip (h) (relaxation 6).
- (h) creates `isabelle=2025.2=<old>`, the batch's top feature package and the tool from the live channel plus conda-forge. Name this as the one exception to decision 11's channel rule.
- It then runs `conda update --all` with accept's three channels.
- It asserts that isabelle is now isabelle_build, every feature pins it, and status shows everything applied.

(3) Update the §10.1 C15 row.

### C10 [minor] Ruling 35 exists only as a new §0 item. The migration plan's glossary, run-tree's description and gate (e) still define the old tested record; §1's scope does not allow the run-tree change; nothing tests the cases ruling 35 must accept; and the maintainer is never told that any change in a -d repository during the build voids the record

Section: §0 item 35 (plan:151-155); §1 (plan:178); §5 steps 2-3 (plan:916-922); decision 16 point 9 (plan:818-820); ISABELLE_GIT_MIGRATION_PLAN.md (:33-36, :134-138, :295, :400-401)  ·  merged from: release-R5-REL-6, consistency-CONS-11, release-R5-REL-7

**Statement.** The core problem: the owner approved a change to what a tested record is (ruling 35). Rev 5 wrote the change down only as a new §0 item, so the texts that define the record still give the old definition.

1. The migration plan's definitions were not amended.
- Migration plan item 32 says it revises 'glossary 的 tested 记录与 run-tree 的说明' (ISABELLE_GIT_MIGRATION_PLAN.md:134-138).
- The glossary entry (:33-36) still lists the old conditions (exit 0, empty status before and after, HEAD unchanged) and no line for the -d repositories.
- run-tree's description (:295) still says 'tested 记录按 glossary 的条件写'.
- Gate (e) (:400-401) still checks only that the sessions are covered.
- The owner's rules make a document's glossary authoritative, and the C10 judge asked for exactly these amendments (REVIEW4:1351). The §10.1 C10 row (plan:1057) presents migration item 32 as the amendment.

2. §1's scope. §1 (plan:178) puts the design of the migration plan's five scripts out of scope, yet §5 step 2 (plan:916) lands the run-tree change. The round-4 owner question itself called this fix 'outside this plan's scope' (REVIEW4:86). §1 needs to name the exception.

3. Tests.
- Decision 16 point 9 (plan:818-820) adds only refusal cases for point 7.
- Nothing tests what ruling 35 must accept: an unrelated light commit made after the tested build must still pass, because the comparison is by content.
- Nothing tests run-tree writing the new line for each -d repository, or run-tree withholding the record when such a line changes during the build. Today run-tree records only tested, command and sessions (tools/common.py:174-186).

4. No operating rule for the build.
- Ruling 35 writes no record when a -d repository's lines (its top-level directory, HEAD and uncommitted files) change during the build.
- The natural implementation of run-tree reuses Repo.status, which passes --untracked-files=all (tools/common.py:146-147). So a commit, an edit or a new untracked file anywhere in the light repository during a build that takes hours (five light sessions plus FOL and ZF, §5 step 3, plan:919-920) silently costs the whole build. run-tree then prints only that no record was written.
- The light repository is shared (decision 16 point 7, plan:809). It received five commits between 10-17 and 10-24 (`git -C contrib/light_locale log`).
- The procedure texts give the maintainer no rule about this: ruling 21's procedure for HOL-side releases (plan:87-89), decision 11's example (plan:641) and §5 step 3.

Required:
- Edit by hand the migration plan's glossary entry, run-tree's description and the gate (e) text to state the new definition.
- Extend §1's scope to include the run-tree tested record (ruling 35).
- Add the acceptance test and the two run-tree toy tests.
- Add one sentence to the three procedure texts: 'no commit, edit or new file in the -d repositories while the tested build runs'. Have run-tree name the -d line that changed.
- Optionally, ask the owner whether the check during the build should cover only the shipped files.

**Editor.** release-R5-REL-7 says the parenthetical in §0 item 35 ('按内容比较，light 仓库里无关的 commit 不逼重跑构建') is true only for commits made after the build. Read where it stands, it belongs to the gate (e) clause and describes that comparison, exactly as the owner question framed it (REVIEW4:88). So it is not a misreading of the ruling. The real gap is the missing operating rule, which I kept as item 4.
release-R5-REL-7 also cites tools/common.py:156-158 for Repo.status; the method is at common.py:146-147.
Part (i) of consistency-CONS-11, which light commit 'the commit to be released' refers to, is handled in challenge C5.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the four parts. Part 3 (tests) holds in full. Parts 1, 2 and 4 hold only in a narrower form.

Part 1, the migration plan's definitions. The facts are right, but "not amended" overstates it.
- The three body passages still state the old record:
  - the glossary entry (ISABELLE_GIT_MIGRATION_PLAN.md:33-36);
  - run-tree's description, "tested 记录按 glossary 的条件写" followed by the old list (:295);
  - gate (e) (:400-401).
- But the amendment exists. Migration item 32 (:134-138) says outright that it revises "glossary 的 tested 记录与 run-tree 的说明", and it states gate (e)'s new rule. Plan §0 item 35 says the change is recorded there ("记为迁移方案 §0 第 32 条", plan:154-155). So the route is disclosed, and the "silent deviation" claim is refuted.
- That route follows the approved migration plan's own convention for rulings made after its approval:
  - item 30 says "glossary 的 k 条目保留作历史解释", and the stale k entry still stands at :47;
  - item 31 revises "第 21 条后半句" without editing item 21.
- The challenge says the owner's rules make a glossary authoritative. That CLAUDE.md rule is about which canonical term to use, not about which definition wins, so it is misapplied here.
- What remains: the judge asked to amend the entry itself (REVIEW4:1351). Today a reader of the glossary or of :295 sees an incomplete definition with no pointer, and the §10.1 C10 row (plan:1057) does not say that the body text was left unchanged. Judged on elegance, that is a real but small defect.

Part 2, §1's scope. Mostly refuted.
- The design of the run-tree change lives in the migration plan (item 32). That is exactly how the round-4 owner question framed it: "it amends the migration plan's definition" (REVIEW4:86). So §1's out-of-scope clause, "五个脚本的设计（迁移方案）" (plan:178), is not contradicted.
- The only gap is a list. §1's in-scope list already names "make-patches 与 (b2) 的配套改动" (plan:176), and make-patches is one of the five scripts (migration :308). It does not name run-tree, although §5 step 2 (plan:916) lands the run-tree change. This is a one-phrase nit.

Part 3, tests. Confirmed, and measured.
- Decision 16 point 9 (plan:818-820) lists only refusal cases for point 7.
- No test is listed for run-tree, although test_trees.sh has a case for each record condition that exists today (tools/tests/test_trees.sh:93-103). Today run-tree writes only the tested, command and sessions lines (run-tree:116-119; common.py:174-186).
- I ran the round-4 prototype of the fix against two mutants:
  - mut_head: gate (e) requires HEAD equality instead of comparing contents;
  - mut_rt: run-tree never withholds the record.
- The refusal cases A (built while the component file was dirty) and B (component file changed after the build) refuse under all three toolsets, so they cannot tell the mutants from the fix.
- Only the acceptance case catches mut_head: C, an unrelated light commit after the build, is accepted by the fix and refused by mut_head.
- Case C2 catches it too: a rerun after make-patches' own commit of patches/ to the light repository is accepted by the fix and refused by mut_head. So comparing contents is also what lets decision 16 point 8's "每一步可重跑" (every step can be re-run) work for light.
- Only a during-build case catches mut_rt. In case D, Light_Locale.thy is edited during the build and reverted after it. The fix writes no record. mut_rt writes one, and R/light/1 is released, although the build compiled the edited file.
- Point 9's failure injections would catch mut_head only if they ran on a package that has tools/component_files.txt, and the plan does not say they do.

Part 4, the operating rule. Narrowed.
- The condition is stated, in ruling 35 itself ("构建期间这些行变了就不写记录", plan:152) and in migration item 32. That is parallel to how the private-tree condition is stated.
- "Silently" is wrong, and "prints only that no record was written" is speculation: today run-tree prints a specific reason (run-tree:105-114). Under ruling 17, the wording of messages is the author's call.
- "Hours" is not borne out. The heap logs of the record on 577e67d show the exact required set (Pure through ZF) built in about 25 minutes on this machine: Pure.db at 15:03:58, ZF.db at 15:26:54.
- The light repository holds no plan documents. Its .gitignore hides what the build writes (tests/golden/*.actual and private_build_logs/), and golden.ML writes tracked files only on the stock tree, where run-tree writes no record anyway.
- The facts that do hold:
  - Repo.status uses --untracked-files=all (common.py:146-147).
  - There were five light commits between 10-17 and 10-24.
  - The plan calls the light repository shared (plan:809).
  - In my cases E and F, an unrelated commit or a new untracked file during the build cost the record.
- The places that state the rule to other agents mention only the private tree: migration rule 11 (:560) and the AGENTS.md text in the migration plan (:745-746). The challenge did not cite these; that is the real gap. I would not add the sentence to §0 item 21, which is a record of an owner ruling.

The editor's rebuttal of release-R5-REL-7 is right: the parenthetical in item 35 describes gate (e)'s comparison after the build. The challenge's optional idea, asking the owner to limit the during-build check to shipped files, would reopen ruling 35 and should be dropped.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C10/. Nothing was installed, and no repository outside the scratch directory was modified.

Toolsets:
- fix/ is the round-4 defender's prototype of ruling 35, copied from review-ipc4/defender-C10/fixtools: a 'dir:' line per -d repository, withholding on change, and the content-comparing gate (e).
- mut_head/ changes one line: gate (e) compares HEAD equality.
- mut_rt/ changes one line: run-tree never withholds.
- fake_isabelle.sh is round 4's stub plus a $HOME/during hook that runs inside 'build' before it logs the Light_Locale.thy it compiled.

e.sh runs seven cases, each on a fresh toy chain with the real hook. Results are in e.out:

| Case | fix | mut_head | mut_rt |
|---|---|---|---|
| A: built while the component file was dirty | refused | refused | refused |
| B: component change committed after the build | refused | refused | refused |
| C: unrelated light commit after the build | accepted | refused | accepted |
| C2: rerun after make-patches' own patches/ commit | accepted | refused | accepted |
| D: component file edited during the build, reverted after it | record withheld | record withheld | record written, R/light/1 released |
| E: unrelated light commit during the build | record withheld | record withheld | record written |
| F: new untracked file during the build | record withheld | record withheld | record written |

In D under mut_rt, the build compiled the edited "vX" file.

Read-only checks:
- `git --no-optional-locks log/status` in contrib/light_locale: five commits from 10-17 to 10-24; status clean; .gitignore lists private_build_logs/ and tests/golden/*.actual. tests/Golden/golden.ML:23-58 writes tracked files only on the stock tree.
- `git notes --ref=tested show HEAD` in contrib/Isabelle2025-2-light_locale, plus the timestamps of ~/.isabelle/Isabelle2025-2-light_locale/heaps/*/log: a full build of the required set in about 25 minutes.
- Diff of ISABELLE_GIT_MIGRATION_PLAN.rev3.md against the current file: the glossary was edited in place before approval; items 30-32 after approval are append-only (:47, :125-138).
- tools/run-tree:98-120, tools/common.py:146-147, :174-186, tools/tests/test_trees.sh:93-103, migration plan :33-36, :295, :308, :400-401, :560, :745-746, REVIEW4:86, :1351.

Recommended fix: These are the smallest fixes, all in text the author may change without asking the owner.

1. Migration plan. By hand, either rewrite the three passages, or append a pointer to each: the glossary entry (:33-36), run-tree's description (:295) and gate (e) (:400-401). The pointer would read: "另记每个 -d 目录所在仓库的顶层、HEAD、未提交的文件，构建期间变了不写；门禁 (e) 对带组件载荷的包的条件见 §0 第 32 条". In the §10.1 C10 row, say which was done. If the append-only convention is kept, the row should read: "正文按迁移方案 §0 的惯例未改，修订记为第 32 条，三处加了指引".

2. §1, in-scope list. Change "`make-patches` 与 (b2) 的配套改动" to "`make-patches`、`run-tree` 的 tested 记录（第 35 条）与 (b2) 的配套改动".

3. Decision 16 point 9 and §5 step 2. Add:
   - (i) an acceptance case: a clean build, then an unrelated light commit, then make-patches must pass;
   - (ii) point 8's three failure injections, run on a package that has tools/component_files.txt;
   - (iii) two test_trees.sh cases: run-tree writes one 'dir:' line per -d repository; and it writes no record when a component file is edited during the build and reverted after it.

   With only the refusal cases, both measured mutants pass.

4. Migration rule 11 (:560) and its AGENTS.md text (:745-746). Add one clause: no commit, edit or new file in a -d repository while a tested build runs, or no record is written. run-tree's reason names the -d top-level directory whose line changed.

Drop from the challenge: "hours", "silently", and the optional owner question, which would reopen ruling 35.

**Judge: partially_confirmed → author_fixes_no_rereview.** The migration plan's convention is that rulings made after approval are appended (items 30-32), and §0 item 35 discloses the route. So the 'silent deviation' claim and most of the §1 scope claim are refuted. 'Hours' and 'silently' are also refuted: a full build takes about 25 minutes, and run-tree prints a reason. What remains:

(1) Add by hand, at the migration plan's glossary entry (:33-36), run-tree's description (:295) and gate (e) (:400-401), a pointer to §0 item 32 that states the new -d line and the gate (e) condition. The §10.1 C10 row says this was done.

(2) §1's in-scope list (plan:176) adds 'run-tree 的 tested 记录（第 35 条）'.

(3) Decision 16 point 9 and §5 step 2 add:
- (i) an acceptance case: a clean build, then an unrelated light commit, then make-patches passes;
- (ii) point 8's failure injections run on a package that has tools/component_files.txt;
- (iii) two test_trees.sh cases: run-tree writes one 'dir:' line per -d repository, and it writes no record when a component file is edited during the build and reverted after it.
Without these, both measured mutants pass (defender-C10/e.out).

(4) Migration rule 11 (:560) and its AGENTS.md text (:745-746) add one clause: no commit, edit or new file in a -d repository while a tested build runs, or no record is written. run-tree's reason names the -d directory whose line changed.

Drop the optional owner question: it would reopen ruling 35.

### C11 [minor] Three descriptions written for the isabelle re-run are inexact: read literally, the re-run contract is broken by the very packages the re-run exists for; the diagnosis rule does not say which kind of hook writes the full diagnosis; and decision 9 and Appendix A credit the re-run with work that, after a build upgrade, the feature packages' own post-links do

Section: Decision 12 point 7 (plan:676-677); §0 item 34 (plan:149-150); §2.3 (plan:260-261); decision 9 (plan:542-546); decision 15 (plan:769-771); Appendix A (plan:1125-1128, :1150-1152)  ·  merged from: hooks-H4, hooks-H5, consistency-CONS-12

**Statement.** The core problem: three descriptions written for rulings 26, 33 and 34 say something different from what the design does.

1. The re-run contract.
- Decision 12 point 7 (plan:676-677), Appendix A (plan:1150-1152) and §0 item 34 (plan:149-150) say that a direct dependent's post-link must have no effect when re-run while its own files are unchanged.
- But the re-run exists precisely to have an effect while those files are unchanged:
  - after isabelle's pre-unlink deletes the user directory, the component hooks re-register (review-ipc5/critic-hooks/run1.out:16-27);
  - after isabelle's files are replaced, the feature hooks re-apply the chain.
- Read literally, every component package and every feature package breaks the contract.
- Read as plain idempotence, the one hook ruling 34 excludes passes it. `isabelle-semantics post-install-system-db` calls itself 'Idempotent: a second run finds nothing left to delete' (Semantic_Embedding/Isabelle_Semantic_Embedding/semantics.py:1606). Yet a later re-run deletes the stand-in vectors the user created since the first run (semantics.py:1567-1607).
- So neither reading separates the packages that should be re-run from the one that must not be.
- §2.3 (plan:261) says the other dependents' post-links only run components -u, '重跑无效果'. That contradicts the reason the re-run exists.
- This text goes into RELEASE_CHECKLIST.md §4, the document future package authors follow.

2. Which hook writes the full diagnosis.
- Decision 9 gives the full diagnosis to '链顶 feature 的钩子' (plan:542-543). The glossary's 钩子 covers both the post-link and the pre-unlink (plan:35-36).
- So a literal implementation lets the chain top's pre-unlink write it too. Then `--force-reinstall <chain-top package>`, or `conda update --all` with a CONFLICT that survives, prints two full diagnoses: one from the old top's pre-unlink and one from the new top's post-link. The plan's invariant says exactly one.
- The diagnosis text itself ('… were not applied', plan:876) only makes sense after an apply.
- The invariant is worded '事务里只要换了 isabelle 或链顶 feature 包' (plan:544-545, :769). The judge's relaxation said 'links' (REVIEW4:96), and a plain `conda remove <top>` runs no post-link at all.

3. What the re-run does in a build upgrade.
- Decision 9 says ruling 26's re-run reaches the chain top's hook in every transaction that changes isabelle (plan:544).
- In `conda update --all` to a new build, the feature packages are part of the transaction (§2.3, plan:239-241). Their records are removed before the re-run scans (plan:565-566), so the re-run does not run them; their own post-links do. The critic's toy shows the re-run finding only the component packages (run1.out, scenario S6).
- Appendix A (plan:1126-1128) likewise says that after '--force-reinstall isabelle 或升构建' only the isabelle post-link can restore features and registrations. After a build upgrade, only the component registrations depend on it.
- The invariant still holds, but for a different reason than the one written.

Required:
- (1) In decision 12 point 7, RELEASE_CHECKLIST §4 and Appendix A, word the contract as: 'a direct dependent's post-link may be re-run at any time; a re-run only re-establishes what the package's own first run established (component registrations, patches), and must not delete or change state created since by the user or by other packages'. The old sentence sits inside ruling 34's record, so show the new wording to the owner. Change plan:261 to 'their post-links only run components -u, which re-establishes the registration and changes nothing else'.
- (2) Decision 9 says: 'only the chain-top feature's post-link writes the full diagnosis, including when the re-run runs it; a pre-unlink writes residue blocks only'. The invariant reads 'a command that links (installs or reinstalls) isabelle or the chain-top package'. Add `--force-reinstall <top>` and `conda update --all` with a CONFLICT that survives to decision 15's invariant cases (plan:769-771).
- (3) Decision 9 says: 'the chain-top hook runs in every transaction that changes isabelle — through the re-run when the top package stays, through its own post-link when it is replaced too'. Appendix A says: 'after --force-reinstall isabelle only isabelle's post-link can restore features and registrations; after a build upgrade the feature packages are replaced too and re-apply themselves, but component registrations come back only through isabelle's post-link'.

**Editor.** Notes on each item:
- Item 1 criticises wording that the C4 judge proposed and the owner adopted with option (a) of question 2 (REVIEW4:70, :647). Clarifying it under ruling 17 is acceptable only if the owner sees the new wording, as stated above.
- Item 3's Appendix A sentence comes from the C22 judge's wording (REVIEW4:2597). The correction is factual and does not conflict with that action.
- Item 2 has a consequence the author should state. If only post-links write the full diagnosis, a plain removal with a broken chain gets no full diagnosis, only its residue block. That block's reason must then name the broken chain.

**Defender: confirmed** (needs owner: True).

I tried to refute each of the three parts against the plan text, the conda source, and a toy conda channel of my own. All three parts survive. Two of the challenge's proposed replacement texts need small corrections, given at the end.

Part 1. The re-run contract, as worded, describes neither the packages that should be re-run nor the one that must not be.
- Where the contract appears: plan:149-150 (inside ruling 34's record), decision 12 point 7 (plan:676-677) and Appendix A (plan:1150-1152). All three say: "直接依赖者的 post-link 在自己的文件没变时重跑必须无效果" (a direct dependent's post-link, re-run while its own files are unchanged, must have no effect).
- Why the re-run exists: plan:221-223 says the isabelle pre-unlink deletes the user directory together with every component registration, and that ruling 26's re-run brings them back. So the re-run must have an effect at exactly the moment the contract forbids one.
- Measured. I built a toy package `markcomp` whose post-link follows the literal contract: it skips when a marker holding the hash of its own files matches. After `--force-reinstall isabelle` its registration was gone, while the ordinary `components -u` package `comp` was restored (run1.out, S2: "markcomp: own files unchanged -> no effect", registrations [comp]).
- So the literal wording permits, even invites, a hook that defeats ruling 26.
- The other reading, plain idempotence (run twice in a row, the second run changes nothing), does not exclude the destructive kind of hook:
  - semantics.py:1606 describes the semantic-data purge as "Idempotent: a second run finds nothing left to delete";
  - my toy `purgecomp`, shaped like it, deleted 1 and then 0 stand-in vectors on two consecutive runs (S1b);
  - yet on the `--force-reinstall isabelle` re-run it deleted the 2 stand-ins the user had created since (S2).
- So neither reading separates the two kinds of package. This text is meant for RELEASE_CHECKLIST §4, where future package authors will read it.
- §2.3 (plan:261, "重跑无效果", the re-run has no effect) contradicts plan:221-223 in the same way.
- Mitigation, not a refutation: the wording is the C4 judge's own (REVIEW4:647-650), and the owner adopted it with option (a) of question 2 (REVIEW4:70). Rev 5 implemented it faithfully. Changing it therefore needs the owner, as the editor says.

Part 2. The plan does not say which kind of hook writes the full diagnosis, and the invariant is worded loosely.
- The rule says "链顶 feature 的钩子" (the chain-top feature's hook; plan:542), and the glossary's 钩子 covers both post-link and pre-unlink (plan:35-36).
- In a pre-unlink, PKG_NAME is set (plan:234), so a literal implementation treats the old top's pre-unlink as the chain top.
- The pre-unlink does see the CONFLICT: unapply lists every file it cannot move, including lower features' files (plan:463).
- The rule for a broken chain also explicitly covers every hook (plan:545-546).
- The diagnosis text ("…were not applied", plan:876) only fits after an apply.
- Measured: `--force-reinstall <top>` runs both the old top's pre-unlink and the new top's post-link (my S5; critic S4). A literal implementation therefore prints two full diagnoses.
- The invariant says "换了" (changed). The plan's own usage of 换了的包 (plan:239) means unlink_precs or link_precs, so a plain removal counts. But a plain `conda remove <top>` runs no post-link at all (my S4).
- Under either reading, therefore, one of these shapes breaks "恰有一段完整诊断" (exactly one full diagnosis).
- The judge wrote "links" (REVIEW4:96, :543). §10.1's C3 and C12 rows (plan:1050, :1059) do not mention the change of word.
- Decision 15 (plan:769-770) lacks the `--force-reinstall <top>` shape. The update-with-CONFLICT shape is there only as a residue-block case (plan:777).

Part 3. Decision 9 and Appendix A credit the re-run with work that the feature packages' own post-links do after a build upgrade.
- Plan:544 says ruling 26's re-run reaches the chain-top hook in every transaction that changes isabelle.
- Appendix A (plan:1126-1128), copying the C22 judge's wording (REVIEW4:2597), says that after a build upgrade only isabelle's post-link can restore features.
- Conda removes the records of packages it unlinks before linking, and writes the new records only after all post-links (link.py:925-1000; path_actions.py:1209-1219).
- Measured on `conda update --all` to a new build: RERUN-SCAN found only comp, markcomp and purgecomp; feat-a and feat-top ran through conda's own post-link calls, after isabelle's (my S3; critic S6).
- On a fresh create the scan found nothing (records=0, S1).
- Plan:565-567 in the same decision states the mechanism correctly, so plan:544 contradicts it. The invariant still holds, but for a different reason than the one written.

On the editor's relaxation: I accept it. If only post-links write the full diagnosis, plain removals get no full diagnosis. A pre-unlink cannot reverse anything when the chain is broken, because decision 3 exits with code 3. So the residue block's reason list (plan:547, :891) must include "feature chain broken", and plan:545-546 must be limited to post-links.

Unrelated, noticed while checking: the glossary at plan:37 still says the pristine build's post-link copies the hook fragment verbatim, which contradicts ruling 33 (plan:142, :484). That is outside C11.

Experiment: All files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/defender-C11/: the generator src/mkchan.py, the re-run src/rerun.py, the driver run1.sh, and the results in run1.out.

Setup:
- The owner's conda 25.11.1, with a private HOME, CONDARC and CONDA_PKGS_DIRS, and only a file:// channel. No python is installed into the environment; the toy re-run uses the base python read-only.
- Toy isabelle builds 1 and 2:
  - pre-unlink: the user-directory deletion from recipe.yaml:223-231;
  - post-link: the hint, then decision 12 point 2's direct-only re-run, which sets VIA=rerun; no hook fragment.
- feat-a and feat-top are pinned to `isabelle 2025.2 <b>` and their hooks only log.
- Three component-style packages:
  - comp: the Isabelle_RPC idiom, `components -u` every time;
  - markcomp: follows the literal contract, skipping when a hash of its own files matches a marker;
  - purgecomp: a direct dependent shaped like semantic-data, deleting the stand-ins in a shared cache.

Results:
- S1, create: the re-run scan found nothing (records=0).
- S1b, purgecomp run twice by hand: it deleted 1 stand-in, then 0. So plain idempotence holds.
- S2, the user creates 2 new stand-ins, then `--force-reinstall isabelle`:
  - the scan found comp, feat-a, feat-top, markcomp and purgecomp;
  - markcomp logged "own files unchanged -> no effect" and its registration was lost (registrations: [comp]);
  - purgecomp deleted 2 stand-ins.
- S3, `conda update --all` to build 2:
  - pre-unlinks ran for feat-top and feat-a, then isabelle;
  - the scan found only comp, markcomp and purgecomp;
  - feat-a and feat-top post-links ran with VIA=conda, after isabelle's.
- S4, `conda remove feat-top`: only the pre-unlinks of feat-top and feat-a ran; no post-link ran at all.
- S5, `--force-reinstall feat-top`: feat-top's pre-unlink and its post-link both ran.

Source reads:
- conda core/link.py:916-1000 (order of pre-unlink, unlink actions, link, post-link, then record actions) and core/path_actions.py:1209-1219;
- Semantic_Embedding semantics.py:1567-1607 and isabelle_semantics.py:1030-1034;
- REVIEW4:43-115, :536-545, :600-656, :1593-1603, :2593-2604;
- plan:33-37, :142-150, :221-261, :463, :481-568, :650-687, :758-785, :855-899, :1042-1071, :1118-1154.

Recommended fix: Part 1. Needs the owner, because the sentence sits in ruling 34's record and in option (a), which the owner approved.
- Show the owner this replacement for plan:149-150, decision 12 point 7, the RELEASE_CHECKLIST §4 addition and Appendix A plan:1150-1152: "直接依赖 isabelle 的包的 post-link 必须能在任何时候重跑：重跑只把它自己装包时建立的东西（组件登记、补丁）恢复回来，除此之外什么都不改" (a direct dependent's post-link may be re-run at any time; a re-run only re-establishes what the package's own first run established, and changes nothing else).
- Prefer "changes nothing else" over the challenge's "must not delete or change state created since by the user". The challenge's clause collides with re-registering a component the user unregistered by hand.
- Change plan:261 to "post-link 都只是 components -u：重跑只把登记恢复回来，不改别的" (their post-links only run components -u; a re-run re-establishes the registration and changes nothing else).

Part 2. An author fix under ruling 17.
- Decision 9 (plan:542-546): "完整诊断只由链顶 feature 的 post-link 写（经第 26 条的重跑跑到时也一样）；pre-unlink 从不写完整诊断" (only the chain-top feature's post-link writes the full diagnosis, also when ruling 26's re-run runs it; a pre-unlink never writes it). A pre-unlink writes its reversed line, and when needed a residue block or the one-line notice. Do not say "residue blocks only": pre-unlinks also write the reversed line and the back-at-shipped line (plan:561-562).
- Limit the broken-chain sentence (plan:545-546) to post-links. Add "feature chain broken" to the residue block's reason list (plan:547, :891), as the editor notes.
- In plan:544-545 and :769, the invariant reads "一条命令链接（安装或重装）了 isabelle 或链顶 feature 包" (a command that links, that is installs or reinstalls, isabelle or the chain-top package).
- Add `--force-reinstall <top>` and `conda update --all` with a CONFLICT that survives to decision 15's invariant shapes (plan:769-770).
- Name the "links" wording in §10.1's C3 row.

Part 3. Wording only.
- Plan:544: "链顶的钩子在每个换 isabelle 的事务里都会跑：链顶包不在事务里时经第 26 条的重跑，在事务里时经它自己的 post-link" (the chain-top hook runs in every transaction that changes isabelle: through ruling 26's re-run when the top package stays, through its own post-link when it is replaced too).
- Appendix A plan:1127-1128: "--force-reinstall isabelle 之后只有 isabelle 自己的 post-link 能把 feature 和登记恢复回来；升构建时 feature 包随之换掉、由自己的 post-link 重打，组件包的登记仍只能经 isabelle 的 post-link 回来" (after `--force-reinstall isabelle` only isabelle's own post-link can restore features and registrations; after a build upgrade the feature packages are replaced too and re-apply themselves through their own post-links, but component registrations come back only through isabelle's post-link).
- Note in §10.1's C22 row that this corrects the judge's sentence.

Outside C11: the glossary at plan:37 still says the pristine build's post-link copies the hook fragment, which contradicts ruling 33. Drop "和原版构建".

**Judge: confirmed → owner_decides.** (1) Owner question 1.
- The contract sentence in ruling 34's record, decision 12 point 7, the RELEASE_CHECKLIST §4 addition and Appendix A plan:1150-1152 ('在自己的文件没变时重跑必须无效果') describes neither the packages that should be re-run nor the one that must not be (defender-C11/run1.out S1b and S2).
- Show the owner the replacement '直接依赖 isabelle 的包的 post-link 必须能在任何时候重跑：重跑只把它自己装包时建立的东西（组件登记、补丁）恢复回来，除此之外什么都不改'.
- Independent of the answer, change §2.3 plan:261 to 'post-link 都只是 components -u：重跑只把登记恢复回来，不改别的'.

(2) Author, under ruling 17:
- Decision 9 (plan:542-546) says that only the chain-top feature's post-link writes the full diagnosis, including when ruling 26's re-run runs it. A pre-unlink writes its reversed line, the residue block, or the one-line notice, never the full diagnosis. This clarifies §0 item 33's 钩子 without editing that record.
- Limit the broken-chain sentence to post-links, and add 'feature chain broken' to the residue block's reasons (plan:547, :891).
- The invariant (plan:544-545, :769) reads 'a command that links (installs or reinstalls) isabelle or the chain-top package'.
- Add --force-reinstall <top> and update --all with a CONFLICT that survives to decision 15's invariant cases.

(3) Wording:
- plan:544: 'the chain-top hook runs in every transaction that changes isabelle — through ruling 26's re-run when the top package stays, through its own post-link when it is replaced too'.
- Appendix A plan:1126-1128: after --force-reinstall isabelle only isabelle's post-link restores features and registrations; after a build upgrade the feature packages are replaced and re-apply themselves, and only the component registrations depend on isabelle's post-link.
- The C22 row notes that this corrects the judge's sentence (REVIEW4:2597).

## All critic findings

### hooks-H1 [major] The residue block and the frozen `||` texts give their recovery steps for replacements too; on `conda update --all` they tell the user to remove the feature packages being kept and to delete files the new package now owns

Lens: hooks  ·  Section: Decision 9 (pre-unlink texts plan:515-529, residue rule plan:547-552); §4 residue block plan:889-899; §10.1 row C11 plan:1058

**Claim.** A replacement is a command that swaps a package for a new or reinstalled build: `conda update --all` (the README's update command), a new isabelle build, a new feature version, or `--force-reinstall` of a feature. In a replacement:
- every pre-unlink runs;
- conda then relinks the packages; when isabelle itself is replaced, that also overwrites every tracked file;
- the new packages' post-links re-apply the chain.

The pre-unlink cannot tell a removal from a replacement. That is why the round-4 judge (REVIEW4:1472-1478) required 'If you are removing <feature>' before EVERY recovery step.

Rev 5 does not do this. §4's block conditions only the sentence 'status will not see them'. Its two recovery lines are unconditional:
- 'To clean up: … --force-reinstall isabelle …; then delete the created files listed above';
- 'If the cause was "lock busy" or the tool could not run: conda install -c … <最高的包名>; then conda remove <最高的包名>'.

The frozen `||` texts (plan:516, :524) go further and say 'If you are removing or replacing <feature>: … then install <包名> together with every other feature package this command removed; then remove them again'. Decision 9 (plan:548) also attaches 'status will not see them after the package is gone' to '卸掉或替换', which is false for a replacement.

One more claim is false. 'Every block of one command is the same, so it does not matter which one the user follows' (plan:550-551, :889) holds only for the package that blocks name. Each block's 'delete the created files listed above' lists only its own feature's files. Following one block of a multi-block removal therefore leaves the other features' created files in isa/ for good.

§10.1's C11 row (plan:1058) does not mention any of these deviations. The `||` texts are frozen into every published feature package for all of 1.x (decision 1), so this cannot be fixed after the first release.

**Evidence.** Toy channel with the verbatim hook texts (critic-hooks/run2.out):
- S8: another process holds the lock on the old isa/etc/ISABELLE_ID during `conda update --all` to isabelle build 2.
  - Three residue blocks appear, each naming qiyuan-dev-patches and each recommending install-then-remove (run2.out:6-14).
  - The update itself ends with every file at its level (run2.out:26-31): the isabelle files were replaced and the new post-links locked the new inode.
- S8b: the user follows the block literally, `conda install qiyuan-dev-patches; conda remove qiyuan-dev-patches`. The result is features.d=[], components=[] and 'no feature packages installed' (run2.out:52-68). Every feature the user was updating is gone.
- S9: the old tool crashes at import while `conda update --all` brings in a working tool.
  - Each pre-unlink prints the frozen 'If you are removing or replacing … then remove them again' (run2.out:75-77).
  - The new post-links apply everything (run2.out:86).
  - Following the frozen text would again strip the environment.
- conda runs every pre-unlink before any unlink (link.py:938-947), which is why the blocks cannot know about the relink.

**Proposed change.** Make every recovery step conditional on removal, as the judge asked, and give the replacement case its own line.

For §4's block:
'If this command removes light_locale: status will not see these files once the package is gone. To clean up: …; then delete the created files listed in every block above.'
'If this command replaces it (an update or a reinstall): its new package's post-link re-applies the chain; afterwards run isabelle-patch-control status.'

For the frozen `||` texts:
'If this command removes <feature>: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then conda install -c https://conda.qiyuan.me -c conda-forge <包名> and every other feature package this command removed; then conda remove them again. If it replaces <feature>: after it finishes, run isabelle-patch-control status.'

Also:
- Fix plan:548 to read '若你是在卸掉它'.
- Narrow plan:550-551 and :889 to 'the named package is the same in every block'.
- Add the S8 and S9 shapes to decision 15's residue cases (plan:776-778).
- Name the change in §10.1's C11 row.

### hooks-H2 [major] The authoritative glossary still says the pristine isabelle build copies the hook fragment, against binding ruling 33; the C3 and C12 judge actions both named this line and §10 is silent

Lens: hooks  ·  Section: Glossary plan:37; §0 item 28 plan:128; §7 plan:989; decision 14 plan:713; §10.1 rows C3 plan:1050 and C12 plan:1059

**Claim.** The glossary entry for 钩子片段 (plan:37) still reads '工具仓库拥有、所有 feature 包和原版构建的 post-link 逐字复制的那段文本'. Ruling 33 (plan:141-145) and decisions 9 and 12 (plan:484, :565, :659) say the isabelle package carries NO copy.

The owner's CLAUDE.md makes a document's glossary authoritative. Read by its own glossary, the plan therefore specifies the duplicate-diagnosis design that ruling 33 removed.

Two judge actions targeted this exact line:
- C3: 'Reword plan:35 (glossary)' (REVIEW4:544).
- C12: 'write 链序上的全部 feature 包 at plan:37' (REVIEW4:1595).
Neither §10.1 row C3 (plan:1050) nor row C12 (plan:1059) names the omission.

Rev 5 chose C12's 'fewer edits' option (redefining 链顶 as the last feature of the chain built from features.d). Three of the companion edits that option needs were also left, and under the new definition they read wrongly:
- ruling 28's paraphrase (plan:128) says '被改文件在链顶的内容' where the judge asked for 'tip（待发布的 commit）';
- §7 (plan:989) says 'dev_patches 在链顶' where the judge asked for 链序最末;
- decision 14 (plan:713) still says '卸顶层包'.

**Evidence.** - plan:37 is byte-identical to rev 4's line 35 (ISABELLE_PATCH_CONTROL_PLAN.rev4.md:35), which both judge actions cite.
- REVIEW4:544 is C3's action: 'Reword plan:35, :731 …'.
- REVIEW4:1595 is C12's action: 'write 链序上的全部 feature 包 at plan:37, 链序最末 at plan:830, and tip（待发布的 commit） at plan:126. Replace 顶层 with 链顶 at plan:603 …'.
- rev4:126 and rev5:128 read the same, as do rev4:845 and rev5:989, and rev4:618 and rev5:713 ('卸顶层包').

**Proposed change.** - Glossary: '钩子片段：工具仓库拥有、链序上的全部 feature 包的 post-link 逐字复制的那段文本（决定 9）；isabelle 包里没有它的副本（第 33 条）'.
- plan:128: write 'tip（待发布的 commit）' (the paraphrase, not the owner's quote).
- plan:989: write '链序最末'.
- plan:713: write '卸链顶的包'.
- Name all four in §10.1's C3 and C12 rows.

### hooks-H3 [minor] The pre-unlink's 'back at the shipped sources, delete heaps/' line prints in every replacement, including every `conda update --all` to a new isabelle build; it is false there, and decision 15's own transcript check cannot pass

Lens: hooks  ·  Section: Decision 9 heap notices plan:561-563; §4 plan:865-867; decision 15 plan:783

**Claim.** Rev 5 makes a pre-unlink add 'The tree is back at the shipped sources. Delete heaps/ … and the shipped heaps are used again.' whenever its reversal leaves the tree at the chain bottom (plan:561-563, :865-867).

In a replacement, the last pre-unlink always leaves the tree at the chain bottom, and the new post-links re-apply the chain right after. Affected shapes:
- `conda update --all` to a new isabelle build: every feature is re-released, so every one is replaced;
- a new version of the bottom feature;
- `--force-reinstall` of the bottom feature.

The same output then shows the line followed by 'Isabelle sources … changed (applied: …) … rebuilds …'. The line's claim that the shipped heaps are used again is false.

In a feature-only replacement with identical patch content (S7), the heaps in the user directory still match the final tree. A user who obeys the line forces a full rebuild for nothing. HOL alone takes several minutes, and light's sessions take far longer.

Decision 15 requires that the update --all transcript's heap wording is correct (plan:783). Against the specified texts it cannot be.

**Evidence.** critic-hooks/run1.out:
- S6, `conda update --all` to build 2 with re-released features: three 'reversed' lines, then BACK-AT-SHIPPED (run1.out:75), then 'applied: feat_a feat_b dev_patches' and the heap paragraph. COUNTS shows back-at-shipped=1 and heap-para=1 (run1.out:88). The final tree is fully applied.
- S7, `--force-reinstall isabelle-feat-a`: the same contradictory pair (run1.out:111-118).
- The rule's source is judge C20 (1) (REVIEW4:2430). Rev 5 introduced it into decision 9 and §4, so this re-review is the first time it is checked against decision 15's update-transcript assertion.

**Proposed change.** Make the line conditional, because a pre-unlink cannot know that a relink follows: 'If this command leaves no feature package installed: the tree is back at the shipped sources; delete heaps/ …'.

Alternatively, drop it from pre-unlink and keep it for command-line `unapply`, and tell `conda remove` users once in the README.

Add S6 and S7 to the hook-layer transcript checks (plan:783).

### hooks-H4 [minor] Decision 12.7's re-run contract, as worded, is violated by the very packages the re-run exists for, and §2.3 calls the components' re-run 'no effect'

Lens: hooks  ·  Section: Decision 12 point 7 plan:676-677; §0 item 34 plan:149-150; §2.3 plan:261; Appendix A plan:1150-1152

**Claim.** The contract reads: 直接依赖 isabelle 的包的 post-link 在自己的文件没变时重跑必须无效果. That is, re-running a direct dependent's post-link while its own files are unchanged must have no effect.

The re-run exists precisely to have an effect while the dependents' own files are unchanged:
- after isabelle's pre-unlink deletes the user directory, component hooks re-register;
- after isabelle's files are replaced, feature hooks re-apply the chain.

Read literally, every component package and every feature package violates the contract, and the semdata package does too. Read as plain idempotence, the semdata hook passes: its docstring says 'Idempotent: a second run finds nothing left to delete' (semantics.py:1606). Yet that hook is exactly what ruling 34 excludes. Neither reading separates the packages that should be re-run from the one that must not be.

§2.3 (plan:261) says the other dependents' post-links '只是 components -u，重跑无效果', which contradicts the reason the re-run exists. This text goes into RELEASE_CHECKLIST.md §4 and PACKAGING_DESIGN.md (Appendix A), the documents future package authors follow.

**Evidence.** - critic-hooks/run1.out S2 (lines 16-27): `--force-reinstall isabelle`. The re-run's 'applied: feat_a feat_b dev_patches' and the restored components=[isabelle-comp isabelle-sememb qiyuan-dev-patches] are effects of re-running packages whose files did not change.
- semantics.py:1567-1606: the purge deletes stand-in vectors created after the previous run, and calls itself idempotent.
- The wording comes from the C4 judge text (REVIEW4:648), which option (a) of owner question 2 adopted.

**Proposed change.** Clarify the wording under ruling 17 (wording delegated to the author), keeping ruling 34's substance, and show it to the owner because the sentence sits inside ruling 34's record:

'直接依赖 isabelle 的包的 post-link 必须可以在任何时候重跑：重跑只重新建立它自己首次运行建立的状态（组件登记、补丁），不得删除或改动此后由用户或其他包建立的状态。'

That is: re-running may only re-create what the package's own first run created, and must not delete or change anything created since.

Fix plan:261 to say 'the components' post-links only run components -u, which re-establishes the registration and changes nothing else'.

### hooks-H5 [minor] The full-diagnosis rule does not say which kind of hook writes it; read with the glossary, the chain top's pre-unlink also writes one, and the invariant's 换了 covers removals

Lens: hooks  ·  Section: Decision 9 plan:542-546; glossary 钩子 plan:35-36; decision 15 plan:769-777

**Claim.** Decision 9 gives the full diagnosis to '链顶 feature 的钩子' (the chain-top feature's hook), and other hooks write one line. The glossary defines 钩子 as both the post-link and the pre-unlink.

A literal implementation therefore lets the chain top's pre-unlink write the full diagnosis too. Two shapes then show two full diagnoses:
- `--force-reinstall <chain-top package>` with a surviving CONFLICT;
- `conda update --all` with a CONFLICT, which decision 15 tests (plan:777).
In both, the old top's pre-unlink and the new top's post-link each write one. This breaks the plan's own invariant of exactly one. The diagnosis text itself ('… were not applied', plan:874-875) only makes sense after an apply.

Conversely, the invariant reads '事务里只要换了 isabelle 或链顶 feature 包，就恰有一段完整诊断' (plan:544-545, :769). 换了 includes removing the top. A pure `conda remove <top>` runs no post-link and, under the residue-only reading, produces zero full diagnoses.

The judge's relaxation said 'links' (REVIEW4:96).

**Evidence.** - critic-hooks/run1.out S4 (lines 43-53). In my toy, pre-unlinks write only residue blocks. `--force-reinstall qiyuan-dev-patches` with an edited created file gives one residue block plus FULL=1. Letting the top's pre-unlink also write the full diagnosis, as the rule literally allows, adds a second one.
- The decision 15 shapes (plan:769-771) are all link shapes, and the residue case 'conda update --all 时存在 CONFLICT' (plan:777) is not counted.

**Proposed change.** Decision 9:
'完整诊断只由链顶 feature 的 post-link 写（含第 26 条重跑里的那次）；pre-unlink 只写残留块，见到别的 feature 的 CONFLICT 时什么都不写或只写一行。'
That is: only the chain-top feature's post-link writes the full diagnosis, including when the re-run runs it; a pre-unlink writes only residue blocks.

Invariant: '链接（装上或重装）了 isabelle 或链顶 feature 包的事务'. That is: a command that links (installs or reinstalls) isabelle or the chain-top package.

Add `--force-reinstall <top>` and `conda update --all` with a surviving CONFLICT to decision 15's invariant shapes.

### hooks-H6 [minor] The in-place-edit remedy is incomplete: the residue block keeps the unconditional '(restores the package's files', and the fix text misses environments that share the inode but report nothing

Lens: hooks  ·  Section: Decision 9 plan:555-557; §4 plan:883-887 and residue block plan:896-897; §10.1 row C8 plan:1055

**Claim.** (a) The C8 judge action says: 'drop the unconditional (restores the package's files' from BOTH the CONFLICT text and the residue block (REVIEW4:1150, citing both places), using the two forms.
Rev 5 changed only the CONFLICT text (plan:883-887). The residue block still promises '--force-reinstall isabelle (restores the package's files, …)' (plan:896-897), which is false for an edit written through the hard link. Row C8 (plan:1055) does not say the residue block was left.

(b) The remedy says to reinstall 'here and in every other environment that reports this conflict' (plan:886-887, :557).
An environment that uses the same isabelle build but has no feature package touching that file never reports a CONFLICT. That includes a plain `isabelle` environment. Such an environment silently keeps the user's edit in its Isabelle sources, because the edited inode is shared through the package cache.

(c) The detection reads 'conda-meta/isabelle-*.json'. In a real environment that pattern matches every package whose name starts with isabelle-.

**Evidence.** - review-ipc4/defender-C8/run.out steps 2 and 7: an in-place edit in A or X appears in B or Y through the shared inode. In step 7 a plain reinstall in X leaves Y edited.
- critic-hooks run1 environment: the glob matched 7 records: isabelle, isabelle-comp, isabelle-feat-a, isabelle-feat-b, isabelle-patch-control, isabelle-semdata, isabelle-sememb.
- rev4:751 and :763 carried '(restores the package's files' in both places; rev5:896 keeps the second.

**Proposed change.** - Give the residue block the same two forms as the CONFLICT text, chosen by the same samefile plus sha256 test.
- Write 'in every environment on this machine that uses isabelle-2025.2-<b> (they share these files through the package cache), whether or not it reports a conflict'.
- Specify the record as 'the conda-meta record whose name is isabelle'.
- Name the residue-block change in row C8.

### hooks-H7 [minor] Two user-facing conda commands still lack the channel flags C17 required, one of them in frozen hook text

Lens: hooks  ·  Section: Decision 12 point 8 plan:679; pre-unlink `||` texts plan:516 and :524; decision 9 plan:558; §10.1 row C17 plan:1064

**Claim.** The C17 judge action (REVIEW4:2103-2104) requires the channel flags on every other user-facing conda command, and names the pre-unlink line and the release note in particular.

- The release note in decision 12 point 8 still says '由 `conda install isabelle-expose-foreign` 提供' (plan:679). A user who installed the way the README says has the channels only on the command line, so this command fails with PackagesNotFoundError.
- The frozen `||` texts give their reinstall step as prose, 'then install <包名> together with …' (plan:516, :524). A user turns that into a flagless `conda install`. This text cannot be changed after the first publish.
- Decision 9's remedy list also writes a flagless 'conda install <残留块点名的包>' (plan:558).

Row C17 (plan:1064) claims 钩子片段与残留块同 (the hook fragment and residue block are done too) and does not mention the release note.

**Evidence.** - REVIEW4:2104: '… the pre-unlink line (plan:460), the residue block (plan:750) and the release note (plan:576)'. The rev4:591 release note is unchanged at rev5:679.
- Without the channel, `conda install isabelle-patch-control` gave PackagesNotFoundError (REVIEW4:2027 section, critic-user/run1.out case 4b).

**Proposed change.** - Release note: 'conda install -c https://conda.qiyuan.me -c conda-forge isabelle-expose-foreign'.
- The `||` texts: spell the step as a command with both -c flags (see H1's proposed text).
- plan:558: add 'conda install -c …'.
- Correct row C17.

### hooks-H8 [nitpick] Decision 12 point 5 still calls the banner fix 'the precondition of §5 step 6 publishing the pristine build'; the pristine build is published at step 8

Lens: hooks  ·  Section: Decision 12 point 5 plan:674; §10.1 row C9 plan:1056

**Claim.** plan:674 says '这是 §5 第 6 步发布原版构建的前提' (this is the precondition of §5 step 6, which publishes the pristine build).

In §5:
- step 6 (plan:926) is writing and landing the CI plan;
- step 8 (plan:932) is where release.yml publishes the pristine build.

The C9 judge action named this exact stale reference: 'plan:572 §5 第 6 步 should be 第 8 步' (REVIEW4:1246). Rev 5 left it, and row C9 (plan:1056) is silent.

**Evidence.** - REVIEW4:1246 asks for the change.
- plan:924-932 gives §5's step list.

**Proposed change.** Write 'this is the precondition of §5 step 8' (这是 §5 第 8 步发布原版构建的前提) and correct row C9.

### release-R5-REL-1 [major] plan_builds probes HEAD only for feature packages. A new tool version stranded by a failed publish blocks every new dispatch, which is the recovery path decision 11 itself prescribes

Lens: release  ·  Section: Decision 10 (plan_builds), decision 11 (rerun semantics), decision 15 (plan_builds pytest)

**Claim.** Decision 10 handles an uploaded-but-unindexed file only for feature packages: it skips any n whose filename answers HEAD 200. The tool package is 'reused by version' from repodata alone, and nothing derives its build number (plan:577-582). Decision 11 forbids bumping a build number (plan:634-635). It also says a fix to publish-conda.yml can only be picked up by a new dispatch (plan:636). Now suppose a batch that ships a new tool version, such as the first batch at §5 step 8, uploads and then fails before the index push. Every later dispatch rebuilds isabelle-patch-control-<v>-pyh4616a5c_0.conda under the same filename with new bytes, and the guard refuses the whole batch. The feature HEAD probe the C2 judge asked for therefore never gets a chance to help. The plan also contradicts itself: plan:634 says no new dispatch is possible, while plan:636 and the HEAD probe exist only to make one possible.

**Evidence.** Simulation of rev 5's rule read literally, using the live noarch repodata from round 4: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/plan_builds/sim.py and sim.out.
- Scenario A, step D1: the first batch uploads and the index is not pushed.
- D2 and D3, new dispatches: the features get n=1 through the HEAD probe, but 'guard refused the whole batch: isabelle-patch-control-1.0.0-pyh4616a5c_0.conda'.
- D4: only after an unrelated publish has re-indexed the bucket (publish-conda.yml:205-221) does the dispatch reuse everything.
- Scenario B: when the tool is already published, the same failure ends with two builds of each (F, v) pinned to the same isabelle build, with different bytes (n=1 stranded and later indexed, n=2 published). This is harmless, but it shows that skipping a served file is the wrong shape.

Facts behind the model:
- The guard lists the bucket, not the index, and compares sha256 (publish-conda.yml:147-191).
- Every noarch python package on the channel is named pyh4616a5c_<n>, so a rebuild keeps the filename (review-ipc4/defender-C2/noarch-repodata.json).
- The round-4 C9 defender predicted this dead end for any re-dispatch (REVIEW4:1193). Rev 5 fixed it for the features only.
- Decision 15's four pytest cases include no stranded tool (plan:748).

**Proposed change.** Apply one rule to every package the batch would publish, the tool included. If a candidate filename answers HEAD 200, download that file and reuse it when it matches:
- for the tool: same version;
- for a feature: the depends in its info/index.json pin `isabelle 2025.2 <isabelle_build>`.
Only a served file that does not match is skipped (for features, by n+1). A new dispatch after a stranded upload then rebuilds nothing, and the guard treats the whole batch as a resume (prototype: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/plan_builds/fixed.py and fixed.out, where D2 reuses all eight files and publishes).

Also:
- Give plan_builds an injected head/fetch parameter, so that the 'uploaded but not indexed' pytest can actually run and covers the tool.
- Reword plan:634-636: a new dispatch is the recovery path, and it resumes byte for byte.

### release-R5-REL-2 [minor] Write step (d) of decision 16 point 8 checks only patches/ and provenance.txt, so the commit that gets tagged can carry component files or staged changes that gates 7 and (e) never checked

Lens: release  ·  Section: Decision 16 points 7-8; §0 ruling 35 ('要发布的 commit')

**Claim.** Ruling 35 binds the component payload to a tested record: the files must be unchanged between the recorded HEAD and 'the commit to be released' (plan:151-155). Decision 16 point 8 never pins down which commit that is.
(1) On a rerun, write step (e) accepts an existing feature-repository tag when its patches/<R>/*.patch and provenance.txt pass write step (d) (plan:815-816). Write step (d) does not look at tools/component_files.txt or the files it lists. Gate (e) checked the feature repository's HEAD, but the commit that ships is the older tag.
(2) Write step (c) says only 'commit if patches/<R>/ differs' (plan:813-814), not `git commit -- patches/<R>/`. In the shared feature repository, a plain commit records every other staged change into the tagged release commit.

**Evidence.** (1) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/resume/stale_tag.py and stale_tag.out implement point 8 and ruling 35's gate (e) literally on a toy light repository.
- Run 1 passes and creates the feature tag; the Isabelle tag (write step f) fails.
- The maintainer then commits a fixed Light_Locale.thy and makes a new tested build (record 2).
- The rerun completes: gate (e) admits record 2, write step (e) accepts the old tag, and the tag ships Light_Locale.thy b163d608, the file record 1 built, while HEAD has 8572e0ba. The fix silently does not ship, and the record that admitted the release did not build the shipped bytes.
- Provenance does not record the feature-repository commit (plan:810-811), so nothing downstream notices.
(2) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/resume/sweep.out: after the by-name add, a plain `git commit` puts another agent's staged tests.thy into the release commit. The round-4 defender's verified recipe was path-limited and left that staged edit alone (review-ipc4/defender-C13/commit_semantics.out case 4).

**Proposed change.** Write step (d) should check everything the renderer reads at the tag: patches/<R>/*.patch, provenance.txt, tools/component_files.txt and every file it lists. It checks them on the commit that write step (e) will tag (new or existing) against what gates 7 and (e) checked at HEAD; for an existing tag that is `git diff --quiet <tag> HEAD -- patches/<R>/ tools/component_files.txt <entries>`. If the existing tag differs, refuse and say the version is used up.

Also:
- Write step (c) commits with a pathspec (`git commit -- patches/<R>/` after the by-name add).
- Point 7 defines ruling 35's 'commit to be released' as the feature-repository commit that write step (e) tags.

### release-R5-REL-3 [minor] §6 (f) and (h) do not say how their starting state is built; for (f), the only way that can work corrupts the leg's package cache

Lens: release  ·  Section: §6 (f), (h); decision 11 isabelle_rebuild output

**Claim.** (f) now requires a 'tracked file' CONFLICT that still exists after `--force-reinstall isabelle` (plan:950-951, from the C3 judge). There are two ways to break a tracked file. An edit that replaces the file is undone by the reinstall, so the second half of (f) cannot hold. An edit written in place survives only because it is written through the hard link into the pkgs cache. That corrupts `<pkgs>/isabelle-2025.2-<b>/isa/<file>`, so every later scenario on that leg that creates an environment from the same build starts in CONFLICT. §6 runs all scenarios on one runner, and nothing isolates CONDA_PKGS_DIRS for (f).
(h) must start from an environment on the older isabelle build M, but the build job outputs only a boolean, isabelle_rebuild (plan:616, :955-956). Neither the start state nor M is defined.

**Evidence.** review-ipc3/defender-C27/run.out:4-26:
- env a, an edit that replaced the file (new inode, links 1): restored by `--force-reinstall`;
- env b, an in-place edit (same inode, links 2): survives two reinstalls.
The hook-layer variant of this case uses a private CONDA_PKGS_DIRS (plan:756, :758); §6 does not. §6 says every scenario starts from a new environment (plan:939), but environments share the leg's pkgs cache, which conda hard-links from (§2.3, plan:247-249).

**Proposed change.** (f): make the surviving CONFLICT one of these:
- a feature-created file with other content (conda does not track it, the reinstall leaves it, and the cache stays clean); or
- an in-place edit inside a private CONDA_PKGS_DIRS, ending with decision 9's documented repair (delete the extracted directory, then reinstall). This option also exercises the in-place diagnosis text on all five platforms.
(h): have the build job output the old build string (empty means skip) instead of a boolean. (h) then creates `isabelle=2025.2=<old>` plus the installed chain from the live channel, and runs `conda update --all` with accept's three channels.

### release-R5-REL-4 [minor] The smoke job is said to run the README's install command verbatim, but it installs a different package than that command

Lens: release  ·  Section: Decision 11 smoke job; decision 14 unified text; §10.1 row C17

**Claim.** Decision 11's smoke 'runs the README install command verbatim' as `conda create -n t -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches` (plan:631-633). The README's install command in decision 14's unified text is `… isabelle isabelle-light-locale` (plan:711). §10.1 row C17 claims the smoke runs the README's command (plan:1064). As written, the documented command is still not the tested one, which is the point of the C17 judge's optional action (REVIEW4:2106).

**Evidence.** plan:631-633 against plan:711; REVIEW4:2093 and :2106 (the critic's purpose: 'so the documented command is the tested one'); §10.1 row C17 at plan:1064.

**Proposed change.** Keep the install command once, in the unified text file, and have the smoke job extract it from the README and run it unchanged. If post-publish coverage of the whole chain is wanted, add qiyuan-dev-patches as a separate, named second command rather than calling it the README command. Correct the §10.1 C17 row to match.

### release-R5-REL-5 [minor] The mandatory strong gate calls levels(tree, features_dir), but make-patches has neither a tree for each state nor the lower features' patch directories

Lens: release  ·  Section: Decision 16 point 5; decision 8 (levels API); decision 3 (chain linking)

**Claim.** Point 5 takes each file's content at each chain state with `git show` and asks the tool's levels function, imported like apply_to, to give each state exactly its own level (plan:800-805). Decision 8 defines that function as levels(tree, features_dir), which builds the chain the way status does (plan:475-477). That requires:
- a tree with etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID (decision 3, plan:364-369);
- a features_dir that holds every lower feature's patch files and provenance.txt, plus the new feature's, which point 8 writes only after the gates (plan:812-813).
make-patches receives only the new feature's --package directory (make-patches:2, :271-272). The lower features' released patch files live in other repositories, and git trees have no etc/ISABELLE_IDENTIFIER. The gate is now mandatory, but its inputs are unspecified.

**Evidence.** `git -C contrib/Isabelle2025-2 ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists ISABELLE_ID but no ISABELLE_IDENTIFIER. Decision 17 states the same (plan:834-835).

The lower directories can be regenerated exactly. `git diff-tree` is plumbing and ignores diff.context, diff.algorithm, diff.noprefix and diff.mnemonicPrefix: the same md5 under each, while porcelain `git diff` changes (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-release/cfg). Every tag annotation embeds the provenance lines (make-patches:210).

**Proposed change.** Preferred, because it is simpler: expose a per-file level function, file_levels(content or absent, [patch files touching p in chain order]). Both status and the gate call it. The gate already knows the chain order from its base_tag walk, so it needs no synthesized tree or provenance.

Alternatively, state the assembly in point 5:
- for each chain tag, the generator's blocks between its base_tag and the tag, plus a provenance.txt taken from the tag annotation;
- the new feature's blocks and provenance in the temporary directory;
- a per-state mini tree with etc/ISABELLE_ID from the state and a synthesized etc/ISABELLE_IDENTIFIER = <R>.

### release-R5-REL-6 [minor] Ruling 35 says it amends the migration plan's tested-record glossary entry, but only a new §0 item was added; the glossary, run-tree's description and gate (e) still state the old definition

Lens: release  ·  Section: §0 ruling 35; §10.1 row C10; ISABELLE_GIT_MIGRATION_PLAN glossary, §5.1, gate (e)

**Claim.** §0 item 35 says the ruling 'revises the migration plan's definition of the tested record (glossary and run-tree's description), recorded as migration §0 item 32' (plan:151-155). The C10 judge asked to 'amend the migration plan's tested-record glossary entry, run-tree's docstring, decision 16 and §10'. Only migration §0 item 32 was added. The glossary entry, which the owner's rules make authoritative, still lists the old conditions and no -d lines. So do the run-tree description and the gate (e) text. §10.1 row C10 presents 'migration item 32' as the amendment and does not say the glossary was left unchanged.

**Evidence.** ISABELLE_GIT_MIGRATION_PLAN.md:
- :33-36, the tested-record glossary entry: conditions are exit 0, empty status before and after, HEAD unchanged; no -d line;
- :295, run-tree: 'tested 记录按 glossary 的条件写：…';
- :400, gate (e): session coverage only;
- :134-138, the new item 32, which declares the amendment.
Plan §10.1 row C10 is at plan:1057.

**Proposed change.** Edit by hand, as CLAUDE.md requires for plan documents:
- the migration glossary entry: add the -d line (toplevel, HEAD, uncommitted files) and the rule that no record is written if those lines change;
- the run-tree description at :295;
- gate (e) at :400: for packages with tools/component_files.txt, only records whose shipped files are clean and unchanged since the recorded HEAD count.
Then make §10.1 row C10 name these edits.

### release-R5-REL-7 [minor] Under ruling 35, any commit or new file in a -d repository during the multi-hour tested build silently voids the record; the plan claims unrelated commits never force a rebuild and gives the maintainer no rule

Lens: release  ·  Section: §0 ruling 35 (parenthetical); §0 ruling 21 (end) and decision 11's HOL-side example; §5 steps 2-3

**Claim.** Ruling 35 writes no record if a -d repository's lines (toplevel, HEAD, uncommitted files) change during the build. That covers the whole repository, not only the shipped files. §0 item 35 adds: 'compared by content, unrelated commits in the light repository do not force a rebuild' (plan:154). That is true only for commits made after the build. An unrelated commit, edit or new untracked file in the shared light repository while the build runs (five light sessions plus FOL and ZF, §5 step 3, plan:920) discards hours of work, and run-tree prints only 'no tested record'. The light repository is not exclusive to the release (decision 16 point 7 calls it shared, plan:809). It received five commits from 10-17 to 10-24 (`git -C contrib/light_locale log`). The same applies to any feature whose build passes -d.

**Evidence.** plan:151-155 (the ruling and its parenthetical); plan:808-809. common.py:156-158: Repo.status uses `--untracked-files=all`, so reusing it for -d repositories, as CLAUDE.md's reuse rule implies, also counts new untracked files. The current light record's command line: `isabelle build -d contrib/light_locale -d contrib/light_locale/tests Light_Locale_Golden … FOL ZF` (git notes --ref=tested on 577e67d).

**Proposed change.** Without reversing the ruling:
- correct the parenthetical to 'commits after the build do not force a rebuild; any change to the repository during the build voids the record';
- add to ruling 21's HOL-side procedure, decision 11's example and §5 step 3: no commit, edit or new file in the -d repositories while the tested build runs;
- have run-tree print which -d line changed.
Optionally, ask the owner whether the during-build comparison should cover only the files the package ships.

### release-R5-REL-8 [minor] §10.1 rows C2, C5, C6 and C9 again leave judge actions undone without saying so

Lens: release  ·  Section: §10.1 rows C2, C5, C6, C9; §6 source list; decision 12 point 5; decision 11 rerun text

**Claim.** Four round-4 judge actions are missing, and their §10.1 rows do not say so:
(1) C6: 'Fix §6's source list (plan:785)'. §6 still reads 本地渠道加线上/artifact 的原版构建加 conda-forge (plan:939), which treats the artifact as a separate channel, while decision 11 now merges the run's packages into the local channel. Row C6 (plan:1053) does not mention §6.
(2) C9: 'plan:572 §5 第 6 步 should be 第 8 步'. Decision 12 point 5 still says the banner fix is a prerequisite of 'publishing the pristine build at §5 step 6' (plan:674). Step 6 publishes nothing; the publication is step 8 (plan:927, :932). Row C9 (plan:1056) is silent.
(3) C2: 'state the artifact retention'. Decision 11 says only that the retention is 'written into the workflow' (plan:635), yet row C2 (plan:1049) lists 'retention' as done.
(4) C5: 'Tell the owner this strictly extends ruling 28's gate'. Row C5 (plan:1052) instead records the author's judgement that the change is 'within the spirit of ruling 28'. Nothing in §0 shows the owner was told, and CLAUDE.md reserves such calls for the owner.

**Evidence.** REVIEW4:898-907 (C6 judge: 'Fix §6's source list (plan:785) and §10 row C10'); REVIEW4:1240-1245 (C9 judge: the two stale references); REVIEW4:441-445 (C2 judge: 'state the artifact retention'); REVIEW4:780 (C5 judge: 'Tell the owner this strictly extends ruling 28's gate'). Plan:939, :674, :635, :1049, :1052, :1053, :1056.

**Proposed change.** - §6 should list three channels: the local channel (holding, in run mode, the run's isabelle packages), the live channel and conda-forge.
- Change plan:674 to '§5 第 8 步'.
- State the feature-packages retention in days next to plan:635.
- Put a one-line note to the owner on the strong gate, as an extension of ruling 28, into the next owner message, and record the answer in §0.
- Make rows C2, C5, C6 and C9 say exactly what was done.

### consistency-CONS-1 [major] The glossary still says the pristine isabelle build copies the hook fragment, which contradicts ruling 33

Lens: consistency  ·  Section: 术语 (glossary) 钩子片段; ruling 33; decisions 9 and 12.2

**Claim.** The glossary entry 钩子片段 still defines the hook fragment as the text that 'all feature packages AND the pristine build's post-link copy verbatim'. Ruling 33 removed that copy. Decision 9 and decision 12 point 2 say the isabelle package carries no copy. The round-4 judge named this exact line for rewording. §10.1's C3 row lists the other rewordings but not this one, so the line was left unchanged without saying so. Under the project's rule the glossary is authoritative, so as written it brings back the copy the owner ordered deleted, in the one place a CI-plan author would look up what the term means.

**Evidence.** plan:37 '工具仓库拥有、所有 feature 包和原版构建的 post-link 逐字复制的那段文本（决定 9）'. Contradicted by plan:141-145 (ruling 33), plan:483-484 ('isabelle 包里没有它的副本（第 33 条）'), plan:658-659 ('不带工具的钩子片段') and plan:762. The judge action is at REVIEW4.md:530 ('(7) Reword plan:35 (glossary: 钩子片段 is copied only by feature packages)') and REVIEW4.md:544. The §10.1 C3 row at plan:1050 does not mention the glossary.

**Proposed change.** Change plan:37 to '工具仓库拥有、每个 feature 包的 post-link 逐字复制的那段文本（决定 9）；isabelle 包里没有它的副本（第 33 条）'. Add '术语表' to the C3 row.

### consistency-CONS-2 [major] §10 is untrue again in about ten places, although the header says every row was checked against the judge text

Lens: consistency  ·  Section: header (plan:3-6); §10.1; §10.2 intro

**Claim.** The plan header promises that every §10 row was checked against the judge's text. Nine §10.1 rows instead claim actions that were not done, state them wrongly, or leave a judge action out without naming it: C3 (CONS-1); C8 (CONS-3, CONS-9); C9 (CONS-5); C11 (CONS-7); C12 (CONS-6); C17 (CONS-10); C23 and C1/C4 (CONS-17); C24 (CONS-4). Two more judge actions are undone with no row naming the gap: C5's owner notification (CONS-13) and C10's migration-glossary amendment (CONS-11). The §10.2 introduction says eight rows carry the 【订正】 mark, but ten rows do (C3 and C15 are extra). The round-4 judge listed exactly this, an untrue §10 against the header's promise, as one of the four things that kept rev 4 from being ready.

**Evidence.** plan:5-6 '本版 §10 的每一行都对着裁决原文核过'. REVIEW4.md:22-30 (round-4 readiness blocker (3)). plan:1075 '第四轮查出 rev 4 §10 不实的八行在本表相应行标【订正】'; grep counts 【订正】 marks in the rows at plan:1081, 1089, 1093, 1098, 1102, 1105, 1106, 1107, 1108 and 1115, which is ten rows. The individual defects and their citations are in CONS-1, CONS-3 to CONS-7, CONS-9, CONS-10, CONS-11, CONS-13 and CONS-17.

**Proposed change.** Fix the items below. Then re-check every §10.1 row against its 'Judge:' paragraph, one action per bullet. Correct the §10.2 introduction to the true number of rows. Do not keep the header's 'every row checked' sentence unless it has been made true.

### consistency-CONS-3 [minor] The residue block still promises that reinstalling isabelle restores the package's files; C8's half of the judge action covering the residue block was dropped without saying so

Lens: consistency  ·  Section: §4 residue block; decision 9; decision 15; §10.1 C8 row

**Claim.** The C8 judge required the unconditional '(restores the package's files' to come out of BOTH the CONFLICT text and the residue block. Rev 5 changed only the CONFLICT text: it added the hard-link detection and a second wording. The residue block is the message a pre-unlink writes when it cannot fully reverse its feature. It still says '--force-reinstall isabelle (restores the package's files, …)'. For an edit written in place through the hard link this is false: the reinstall links the edited cache copy back in. Once the package is removed, status says 'no feature packages installed', so the edited Isabelle source stays invisible. Decision 15 builds the residue test case with an edit that makes a new inode, so no test exercises the hard-link case. The C8 row says '§4 两种文案' and does not mention that the residue block was skipped.

**Evidence.** REVIEW4.md:1150 ('§4 CONFLICT text and residue block (plan:736-737, :748-749): drop the unconditional (restores the package's files'); REVIEW4.md:1127. The rev-5 residue block at plan:896-897 still reads 'conda install -c … --force-reinstall isabelle (restores the package's files, deletes this environment's Isabelle user directory; …)'. The hard-link test exists only for the CONFLICT text (plan:554-557, plan:884-887). Decision 15 at plan:757 has '残留块那例的编辑写成新 inode'. The C8 row is at plan:1055.

**Proposed change.** Apply decision 9's samefile-plus-sha256 test (plan:555-556) to the residue files as well, and print the hard-link remedy in the residue block. Or make the line static: 'restores the package's files, unless an edit was written through the package cache; see status -v / README'. Add a residue case with a hard-linked edit to decision 15. Name the change in the C8 row.

### consistency-CONS-4 [minor] Decisions 5 and 15 and the C24 row cite a lock-hold bound in §6 that does not exist

Lens: consistency  ·  Section: §6; decision 5; decision 15; §10.1 C24 row

**Claim.** The C24 judge asked §6 to state the bound that decision 5's argument relies on: one run holds the lock far below the 60-second wait, with the number left to the author. Decisions 5 and 15 both say '§6 要求…远低于 60 秒', and the C24 row says '§6 的界'. §6 contains no such item and no number. Decision 15 says to switch to batched listing only 'if the bound is exceeded', but with no bound written down that switch can never be triggered.

**Evidence.** REVIEW4.md:2763. plan:419 '§6 要求它远低于 60 秒的等待上限'. plan:789 '§6 要求持锁时间远低于 60 秒的等待上限；超了才按评审四 C24 的办法…'. plan:1071 (the C24 row: '决定 15 Windows 测量与 §6 的界'). §6 is plan:936-962; grep finds neither '60' nor any lock-time item in it.

**Proposed change.** Add a §6 item, for example '(l) on win-64 a whole-chain status and a --force-reinstall isabelle each hold the lock at most N s (N chosen, e.g. 10)'. Cite that item by its letter in decisions 5 and 15.

### consistency-CONS-5 [minor] Decision 12 point 5 still says the pristine build is published at §5 step 6 (it is step 8), and the C9 row puts the reference fix in §0 item 25, where it was not made

Lens: consistency  ·  Section: decision 12 point 5; §5; §10.1 C9 row

**Claim.** The C9 judge asked for two stale references to be fixed. Rev 5 fixed one, '决定 12 第 9 点 → 第 5 点' in §2.3. It left the other: decision 12 point 5 still calls the banner fix 'the precondition for publishing the pristine build at §5 step 6'. §5 step 6 only writes the CI plan and produces an artifact; the pristine build is published at step 8. The C9 row says the first fix was made in '§0 第 25 条'. That item contains no such reference; the fix is at §2.3.

**Evidence.** REVIEW4.md:1245 ("plan:572 '§5 第 6 步' should be 第 8 步"). plan:674 '这是 §5 第 6 步发布原版构建的前提'. plan:927 (step 6: CI 计划落地、产出 artifact). plan:932 (step 8: 'release.yml 以同一个 N 发布原版构建'). plan:1056 (C9 row: '§0 第 25 条引用改…'). plan:107-114 (§0 item 25; it has no 决定 12 reference). The actual fix is at plan:280.

**Proposed change.** Change plan:674 to '§5 第 8 步'. Change the C9 row to '§2.3（plan:280）的引用改为决定 12 第 5 点；决定 12 第 5 点的步号改为第 8 步'.

### consistency-CONS-6 [minor] 链顶 was redefined, but four of the C12 judge's spot edits were skipped, so several lines now say something false

Lens: consistency  ·  Section: glossary; §0 item 28; §7; decision 14 README text; decisions 11 and 17

**Claim.** Rev 5 redefines 链顶 (top of the chain) as the last feature of the chain the tool builds from an environment's feature directories, and adds the separate terms 链序最末 (last in chain order, i.e. dev_patches) and tip (the commit make-patches releases). The judge's 'fewer edits' option came with spot edits, and four were skipped. (1) Ruling 28's record still says '被改文件在链顶的内容'. It describes a release-time gate, where no environment exists, so it should say tip. (2) The §7 row says 'dev_patches 在链顶', which is now false for any user without qiyuan-dev-patches; it should say 链序最末. (3) The glossary's batch-workflow entry still says '整条链'. (4) The README text still uses 顶层包, a fourth, undefined term. In addition, decision 11's roundtrip job ('装链顶 feature 包') and decision 17's '<链顶 feature>' argument use 链顶 for the highest feature of a batch before anything is installed, which the new definition does not cover. The C12 row lists only the glossary and decision 9.

**Evidence.** REVIEW4.md:1595 and :1578 ('plan:126: 在链顶的内容 -> 在 tip（待发布的 commit）的内容'). plan:16-17 (new definitions). plan:128 ('被改文件在链顶的内容'). plan:989 ('dev_patches 在链顶'). plan:39 ('把整条链一次构建'). plan:713 ('libmamba 卸顶层包会…'). plan:620 ('再往同一环境装链顶 feature 包'). plan:824. The C12 row is at plan:1059.

**Proposed change.** Make the judge's edits: plan:128 → 'tip（待发布的 commit）', plan:989 → '链序最末', plan:39 → '链序上的全部 feature 包', plan:713 → '链顶的包'. In decisions 11 and 17 write '批次里链序最高的 feature（包）'. Name all of this in the C12 row.

### consistency-CONS-7 [minor] The frozen pre-unlink text tells users who are replacing a feature to remove it again, and the residue block's lock-busy step is not limited to removals

Lens: consistency  ·  Section: decision 9 (pre-unlink || text, residue rule); §4 residue block; §10.1 C11 row

**Claim.** The C11 judge asked for 'If you are removing <feature>' before every recovery step, and for 'status will not see them' to apply only to removals. Rev 5 deviates in three places. (i) The frozen || text in the .sh and the .bat says 'If you are removing or replacing <feature>: … then install <包名> together with every other feature package this command removed; then remove them again'. Frozen means it is copied into every published feature package and cannot change in 1.x. For a replacement, for example the documented conda update --all, this tells the user to remove the upgraded feature packages. (ii) In the §4 residue block, the lock-busy and tool-cannot-run recovery ('conda install <最高的包名>; then conda remove <最高的包名>') sits outside the 'If you are removing' sentence. (iii) Decision 9 makes 'status 就看不见了' apply when the package is removed OR replaced. §4 applies it to removal only, and §4 is right: in a replacement, the new package's features.d still lists the files. The C11 row names none of these.

**Evidence.** REVIEW4.md:1472-1476. plan:516 and plan:524 (the frozen || texts). plan:334-336 (1.x freezes the hook texts). plan:547-548 ('若你是在卸掉或替换它这些改动在包卸掉后 status 就看不见了'). plan:895 ('If you are removing light_locale, status will not see them once the package is gone'). plan:898 (the lock-busy step stands on its own). The C11 row is at plan:1058.

**Proposed change.** || text: 'If you are removing <feature>: …; then remove them again. If <feature> was being replaced: after the command, run isabelle-patch-control status and follow its advice.' Put the lock-busy step in §4 under the removal condition. Align decision 9's wording with §4. Name the change in the C11 row.

### consistency-CONS-8 [minor] New in rev 5: following any one residue block is not always equivalent, because each block lists only its own feature's created files

Lens: consistency  ·  Section: decision 9 residue rule; §4 residue block; decision 15

**Claim.** Decision 9 now concludes that, because every block of one conda command names the same highest package, it does not matter which block the user follows. That holds only for the lock-busy and tool-cannot-run branch, where the tool itself removes the created files. The CONFLICT branch ends 'then delete the created files listed above', and each block lists only its own feature's files. Example: a pruning removal, a user-edited file touched by a lower and an upper feature, and an edited file the upper feature created. The pre-unlinks run top-down and print two blocks. If the user follows only the last block, which belongs to the lower feature, the upper feature's created file stays in isa/. conda does not track it, and status no longer sees it once the packages are gone. A later §6 (g)-style 'conda remove isabelle' would then leave isa/ behind. Decision 15's 'follow only the last block' case covers only the lock-busy shape.

**Evidence.** plan:549-550 ('同一条 conda 命令里每个残留块给出的命令相同，用户按哪一块做都一样'). plan:548 ('只列自己 feature 的'). plan:897 ('then delete the created files listed above'). plan:775 (pre-unlinks run top-down). plan:776-777 (the decision 15 case is lock-busy only). plan:952 (§6 (g) asserts that isa/ is absent).

**Proposed change.** Either have each block list every created file the command left behind (features.d is still complete when the pre-unlinks run, plan:549), or limit the equivalence claim to the lock-busy branch and tell the user to follow every block's file list. Add a two-block CONFLICT case with a created file to decision 15.

### consistency-CONS-9 [minor] §9 still says check_bytes reads conda-meta paths_data, which contradicts rev 5's decision 15; the C8 row repeats the error

Lens: consistency  ·  Section: §9; decision 15; §10.1 C8 row

**Claim.** §9 says the paths_data in conda-meta is read in exactly two places, and the second is decision 15's check_bytes after removal. Following the C15 judge, rev 5 changed check_bytes to take its reference data from info/paths.json in the package archives, and decision 15 now says it never reads conda-meta. §9 is about the tool's state sources, and check_bytes is test code, so it does not belong on that list at all. The C8 row repeats the claim ('§9 说明 conda-meta 的两处读').

**Evidence.** plan:1031-1032 ('conda-meta 的 paths_data 只在两处读：决定 9 …，决定 15 的 check_bytes 作卸载后的校验'). plan:751-752 ('isabelle 包的 info/paths.json——从包缓存或本地渠道的 artifact 取，不从环境的 features.d 或 conda-meta 取'). REVIEW4.md:1925. The C8 row is at plan:1055.

**Proposed change.** §9: 'the tool reads conda-meta paths_data only in decision 9's hard-link test; decision 15's check_bytes uses the archives' info/paths.json'. Fix the C8 row.

### consistency-CONS-10 [minor] The smoke job does not run the README's install command, although decision 11 and the C17 row say it does, and the release note's conda command still lacks the channel flags

Lens: consistency  ·  Section: decision 11 smoke; decision 14; decision 12 point 8; §10.1 C17 row

**Claim.** (i) Decision 11 says the smoke job runs the README's install command verbatim, but its command installs qiyuan-dev-patches. The README command in decision 14 installs isabelle-light-locale. The C17 row repeats 'runs the README's command verbatim'. (ii) The C17 judge listed the release note among the user-facing commands that must carry -c https://conda.qiyuan.me -c conda-forge. Decision 12 point 8 still has a bare 'conda install isabelle-expose-foreign'. §4's note that it omits the flags for brevity covers only the text below it.

**Evidence.** plan:631-632 ('原样跑 README 的安装命令 conda create -n t … isabelle qiyuan-dev-patches'). plan:711 ('conda create -n <env> … isabelle isabelle-light-locale'). The C17 row is at plan:1064. REVIEW4.md:2104 ('… and the release note (plan:576)') and REVIEW4.md:2106. plan:679 ('由 conda install isabelle-expose-foreign 提供'). plan:856 ('下文凡出现 …').

**Proposed change.** Make the smoke command literally the README's command, or make the README name the package the smoke job installs. Add the two -c flags at plan:679. Correct the C17 row.

### consistency-CONS-11 [minor] Ruling 35 is written down inconsistently: one comparison spans two repositories without naming the light commit, the migration-plan glossary is not amended, and the scope and tests miss it

Lens: consistency  ·  Section: §0 item 35; decision 16 point 7; §1; §5 step 2; decision 16 point 9; migration plan glossary and gate (e)

**Claim.** (i) Ruling 35 and migration ruling 32 compare 'the recorded HEAD' with 'the commit being released'. The recorded HEAD is a commit of the light repository. Under the glossary, the commit being released is tip, an Isabelle-repository commit. The judge's form named the light repository's own HEAD (git diff --quiet <recorded head> HEAD -- <entries>). Decision 16 point 7 only says 'check the light repository's state in the tested record', and nowhere names the light-side commit. That commit is the HEAD that point 8 (c) commits on and (e) tags. (ii) The judge asked for the migration plan's tested-record glossary entry to be amended. Migration ruling 32 says it amends that entry, but the glossary and gate (e) still give the old definition. (iii) §1 puts the design of the migration plan's five scripts out of scope, yet §5 step 2 lands the run-tree change, and the scope line does not name this exception. (iv) Decision 16 point 9 adds refusal tests only. It has no test of the ruling's acceptance side (an unrelated light commit after the build still passes), none of run-tree writing the new line, and none of run-tree withholding the record when the lines change during the build.

**Evidence.** plan:151-155. plan:17 ('tip 指 make-patches 要发布的那个 commit'). plan:808-810. REVIEW4.md:1349-1351 ('git diff --quiet <recorded head> HEAD -- <entries>'; 'amend the migration plan's tested-record glossary entry, run-tree's docstring'). ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md:134-138 (ruling 32 says '修订 glossary 的 tested 记录') against :33-36 (glossary unchanged) and :400-401 (gate (e) unchanged). plan:174-179 (scope). plan:916 (§5 step 2). plan:818-820. Today's code: tools/run-tree:98-120 and tools/common.py:174-186 record only tested/command/sessions.

**Proposed change.** Write: 'run git diff --quiet <recorded light HEAD> <light HEAD at make-patches time> -- <component_files> in the light repository; that HEAD is the commit point 8 (c) builds on and (e) tags'. Amend the migration glossary entry and gate (e) text. Extend §1's scope with 'run-tree 的 tested 记录（第 35 条）'. Add the acceptance and run-tree toy tests.

### consistency-CONS-12 [minor] Appendix A and decision 9 credit the isabelle re-run with things that, after a build upgrade, the feature packages' own post-links do

Lens: consistency  ·  Section: Appendix A; decision 9 diagnosis rule; §2.3

**Claim.** Appendix A, the argued exception the owner asked for in ruling 14, says that after '--force-reinstall isabelle or a build upgrade', only the isabelle post-link can restore the features and the registrations. Under ruling 22, a build upgrade (conda update --all) also swaps every feature package and runs their own post-links; §2.3 says so after the C23 correction. Only the component registrations depend on the re-run. Decision 9 likewise says the re-run reaches the top feature's hook in every transaction that changes isabelle. In update --all the top feature package is part of the transaction: its record has been removed, so the re-run skips it, and its own post-link runs instead. The invariant still holds, but for a different reason than the one written. Two judge actions, C22's wording and C23's fact, now disagree inside the plan.

**Evidence.** plan:1126-1128 ('所以 --force-reinstall isabelle 或升构建之后，只有 isabelle 自己的 post-link 有机会把 feature 和登记恢复回来'). plan:239-241 ('conda update --all 升到新 isabelle 构建时按第 22 条连带换掉并跑全部 feature 包的钩子，但不跑组件包的'). plan:544 ('第 26 条的重跑在每个换 isabelle 的事务里都会跑到链顶的钩子'). plan:565-566 (the re-run sees only packages outside the transaction).

**Proposed change.** Appendix A: '… after --force-reinstall isabelle only the isabelle post-link can restore the features and registrations; after a build upgrade the feature packages are replaced too and re-apply themselves, but component registrations come back only through the isabelle post-link'. Decision 9: 'the top feature's hook runs in every transaction that changes isabelle: through the re-run when the top package stays, through its own post-link when it is replaced'.

### consistency-CONS-13 [minor] C5: the owner was not told that the mandatory strong gate goes beyond ruling 28; the author's own reading took its place

Lens: consistency  ·  Section: §10.1 C5 row; §0 item 28; decision 16 point 5

**Claim.** The C5 judge's action included 'Tell the owner this strictly extends ruling 28's gate'. Instead, the C5 row records the author's view that the strong gate is already within the spirit of ruling 28, and §0 records no owner answer. Ruling 28 as recorded refuses only a change whose blob equals the blob at a lower state. Decision 16 point 5 adds a second refusal class: a change whose context is ambiguous even though no lower change is undone, with the message 'the change's context is ambiguous and must be reworked'. The owner never ruled on that class. The deviation is named, so it is not silent, but the plan decides the question on the owner's behalf, against the project rule to ask under uncertainty.

**Evidence.** REVIEW4.md:779. plan:1052 ('judge 说这扩展第 28 条的门禁，已在第 28 条的精神内'). plan:127-129 (ruling 28: blob equality only). plan:803-805 ('否则说这个改动的上下文有歧义、要改写'). CLAUDE.md 'Never Act on Assumptions — ALWAYS Ask'.

**Proposed change.** Ask the owner one question, with the background explained: 'the release gate will also refuse a change whose hunks fit more than one level although it undoes nothing below; agree?'. Record the answer as §0 item 36 and fix the C5 row.

### consistency-CONS-14 [minor] New in rev 5: the mandatory 'exactly one level' gate does not say where its inputs come from, and what it needs is not available to make-patches

Lens: consistency  ·  Section: decision 16 point 5; decision 8 levels(); decision 3

**Claim.** Decision 16 point 5 makes make-patches call the tool's levels(tree, features_dir) on each state of each changed file. levels builds the chain by exact tag. To do that it needs etc/ISABELLE_IDENTIFIER and etc/ISABELLE_ID in the tree, and provenance.txt plus *.patch for every feature of the chain. The plan never says where make-patches gets these. (i) It knows only the new feature's --package directory; the lower features' patch files live in other repositories. (ii) etc/ISABELLE_IDENTIFIER is not tracked in the Isabelle repository (new-tree writes it), so a tree assembled from git show contents cannot be linked to the chain. (iii) The new feature's provenance.txt is written only at point 8 (b), after the gate has run. As specified, the gate cannot be implemented without guessing.

**Evidence.** plan:800-805. plan:475-477 (levels). plan:363-370 (chain linking from ISABELLE_IDENTIFIER, ISABELLE_ID and provenance). make-patches:2 and :267 (only --package). In contrib/Isabelle2025-2-light_locale, 'git ls-files --error-unmatch etc/ISABELLE_IDENTIFIER' finds no match, while etc/ISABELLE_ID is tracked; tools/common.py:197-201 writes ISABELLE_IDENTIFIER. plan:813 (provenance written at 8 (b)). make-patches:210 (the provenance is in the annotated tag message).

**Proposed change.** Specify the inputs. The gate assembles a temporary features.d: the new feature's blocks and a provisional provenance from point 8 (a)'s temporary directory, plus each lower feature's blocks regenerated with the same generator from git diff-tree <its base_tag> <its release tag>, with provenance taken from the annotated tag message. For each state it builds a temporary tree holding etc/ISABELLE_IDENTIFIER=<R>, etc/ISABELLE_ID=<pristine id> and that state's content. Add a toy test that the regenerated lower blocks are byte-identical to the released ones.

### consistency-CONS-15 [minor] New in rev 5: make-patches' release commit is not limited to patches/<R>/, so in the shared feature repository it would take in other agents' staged files (toy-measured)

Lens: consistency  ·  Section: decision 16 point 8 (c)/(d)

**Claim.** Point 8 (c) stages the generated files by name and commits only when there is a difference. It does not say the commit itself is limited to patches/<R>/, and point 7 states that the feature repository's work tree is shared. In a toy repository with another file already staged, a plain 'git commit' after the named adds also committed that other file. 'git commit -- patches/R/' after the same adds committed exactly the patch-directory changes (one new file, one removed file, provenance.txt) and left the other file staged. The check in (d) compares only the patch files' blobs, so a change swept in this way would ship unnoticed in the tagged release commit.

**Evidence.** plan:813-815. plan:809 ('不要求整个工作树干净——它是共享的'). Toy runs: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc5/critic-consistency/commit2 (plain commit: 'other/f | 2 +-' inside the release commit) and …/critic-consistency/commit ('git commit -qm rel -- patches/R/' gives new.patch, old.patch deletion and provenance.txt; 'M  other/f' stays staged).

**Proposed change.** Write: 'git commit -m … -- patches/<R>/ after the named git add / git rm --cached (measured to include the new and the removed files and nothing else)'.

### consistency-CONS-16 [minor] The archived …PLAN.rev4.md is not the text round 4 reviewed: it contains rulings 33-35, and every REVIEW4 line reference after §0 is off by 15 in it

Lens: consistency  ·  Section: header (copies); §10.2

**Claim.** The header presents …PLAN.rev4.md as the copy of rev 4, and this re-review was asked to check §10.2 against it. The copy contains §0 items 33-35, which record owner answers given after round 4. Its modification time is after REVIEW4.md was written. Every REVIEW4 'plan:N' reference past §0 points 15 lines too early in the copy, so the archived rev 4 is not the text round 4 reviewed, and §10.2's 【订正】 rows cannot be checked against it by line number.

**Evidence.** PLAN.rev4.md:141-155 (items 33-35 present). Modification times: PLAN.rev4.md 2026-10-24 16:30:11, REVIEW4.md 16:14:24. Offset examples: REVIEW4.md:1245 cites plan:245, which is PLAN.rev4.md:260; REVIEW4.md:1595 cites plan:603 (顶层), which is PLAN.rev4.md:618; REVIEW4.md:544 cites plan:731, which is PLAN.rev4.md:746. plan:4-5 ('副本 …PLAN.rev1.md … …PLAN.rev4.md').

**Proposed change.** Restore the copy to the reviewed text by removing items 33-35. Alternatively, state in the header that the copy has §0 items 33-35 added and that line numbers after §0 are shifted by 15.

### consistency-CONS-17 [minor] Smaller judge actions dropped without saying so, and small new inaccuracies

Lens: consistency  ·  Section: decisions 6, 9, 11 and 14; §2.3; §10.1 rows C1 and C4

**Claim.** (a) C1: decision 14 leaves out the judge's 'reconsider the reason given at :420-422'. That comment says --override-channels was kept so conda-forge stays out of a proxy that breaks TLS, so adding -c conda-forge brings that problem back. (b) C2: the judge asked for the artifact retention to be stated; the plan only says the retention 'is written into the workflow'. (c) C23 (1): decision 9's component lines neither present the .sh line's .messages.txt redirect as this plan's own change, nor say that light's .bat registration line, copied from Isabelle_RPC, is silent when it fails. Also, the post-link cites Isabelle_RPC recipe lines 165-176, which include the template's @echo off and exit /b 0, while the pre-unlink cites 168-174 for the same lines. (d) C20 (6): the CONFLICT text points to files marked 'created' in status -v, but decision 6's -v format defines no such marker. (e) §2.3's new list of direct dependents names 'minilang'; the published package is isabelle-minilang. (f) The C4 row says option (b) is '记在 §9 外不展开' (recorded outside §9), but it is recorded nowhere. The C1 row puts the rewrite-list additions under decision 12 point 10, but they are in point 4.

**Evidence.** (a) REVIEW4.md:340; plan:722-724; Performant_Isabelle_ML/.github/workflows/release-conda.yml:420-422 and auto_sledgehammer/.github/workflows/release-conda.yml:191-194 (the TLS-proxy comment). (b) REVIEW4.md:440; plan:635. (c) REVIEW4.md:2671; plan:530-533 versus plan:528; Isabelle_RPC/conda/recipe.yaml:166-176 (line 174 ends '>nul 2>&1'). (d) plan:881 versus plan:449. (e) plan:260; Isa-Mini/conda/recipe.yaml:52 ('name: isabelle-minilang'); live snapshot review-ipc4/critic-conda/live/noarch.json lists isabelle-minilang-0.6.0/0.7.0. (f) plan:1051; plan:1048 versus plan:667-669.

**Proposed change.** (a) Add 'and decide how to reach conda-forge despite the TLS proxy noted at :420-422'. (b) State the retention in days. (c) In decision 9, add one sentence each: the .sh line's redirect is this plan's own choice, and the .bat line is silent on failure; cite the same Isabelle_RPC line range in both places. (d) Define the marker in decision 6's -v format. (e) Write isabelle-minilang. (f) Fix both rows.
