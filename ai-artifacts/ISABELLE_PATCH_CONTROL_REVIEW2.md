# isabelle_patch_control plan rev 2 — review 2 (workflow wf_53ea674b-1cc, 2026-10-23)

Critics: 72 findings (5 lenses). Merge editor: 26 challenges, 1 dropped. One fresh defender per challenge. Judge: ready = False.

## Judge summary

Verdict: rev 2 is not ready for the owner's approval. The owner's rulings set its direction: the conda isabelle package is pristine, git apply is the engine, hooks always exit 0, new builds re-apply the installed features, non-conda trees are unsupported, Isabelle2024 stays in the old tool, and everything ships in one batch. Rev 2 follows that direction, and its outer shape is good: packages, provenance files, a chain linked by exact tags, one tool-owned hook entry point, and a renderer. But its central claims about the engine are false.

Two blocking defects, both re-measured:
- C1: git apply runs with the caller's environment. Inside an enclosing git work tree it silently does nothing and reports success. A user's git config or attributes file rewrites the bytes it writes. My own run reproduced the silent no-op (a reverse check on an unpatched file passed, rc=0). It also showed that the challenge's GIT_DIR=/nonexistent fix is a hack: git reads $GIT_DIR/config, and a planted config there turned on CRLF. A whitelist environment with GIT_CEILING_DIRECTORIES gave correct verdicts and an exact round trip. Runs are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/judge/c1/.
- C2: decision 4's atomicity claim is false. With separate patch-file arguments, a feature half-applies. Even a single stream deletes every target before writing any, so a Ctrl-C, a kill or a full disk leaves Isabelle source files missing, and no command can repair them.

Several rev-1 directives did not survive:
- the .git refusal (C1);
- interrupt tests (C2);
- the record-entry rule and the check of the built-in feature (C3);
- the 1.x freeze of the hook contract (C4);
- the created-file action rules (C5);
- the rule for a file that fits several levels, and the definition of --dry-run (C6);
- the pre-unlink residue message (C8);
- running (b2) before every publication (C10);
- the per-repository release list (C12);
- the live smoke install (C13);
- the pruning expectation in the tests (C14);
- the build-bump test (C16);
- the getenv heap path (C17);
- the tree-derived features.d (C18);
- no committed derived recipe (C21);
- step 0 and the 0.x section (C23);
- the C29 citation fixes (C26).
So plan:4's claim that every confirmed item was absorbed is false.

Several rulings are misread or overstretched:
- Ruling 12's exit 0 is guaranteed only by the tool's code, not by the hook text (C4).
- Appendix A, which ruling 14 asked for, states false facts, and decision 11 quietly reads '原汁原味' as keeping pack.sh's packaging edits (C9).
- Ruling 18 ('all platforms') is tested on only three of the five conda subdirs (C15).
- Ruling 19 merges an announcement by the author with the owner's 'agree (a)', which answered rev 1's question 8 (C22).
- The second half of rev 1's question 10 was withdrawn from the owner on a false premise (transcript line 5373: 'it disappeared'), and rev 2 then settled it silently (C22).
- PyPI publication was never ruled (C24).
- One more, unrecorded: at 04:46 the author promised the owner two follow-ups 'recorded in the plan': a Semantic_Embedding dependency on isabelle-expose-foreign, and the isabelle-ai / future_assign_interrupt question. Neither appears. The dependency is in fact unnecessary, because Performant_Isabelle_ML >=0.2.0 re-binds Foreign (C16).

What rev 3 should do:
- One write path: replay each file on a staging copy with git apply, then install it into the tree with an atomic rename (C2). status, --dry-run, apply, unapply and apply-to then share one code path, and modes, write failures and dry-run divergence are correct by construction (C6, C19, C20).
- git's environment built from a whitelist inside git_apply, plus a .git refusal for every tree (C1).
- Per-file target levels: apply only moves files up, unapply only down. The created-file rule and the shape rule are deleted as inputs (C5, C6).
- Every chain walk starts from the pristine tag, and the LEGACY_BUILDS entry marks a verified pre-applied level (C3).
- One byte-identical post-link fragment, frozen for 1.x (C4).
- The lock taken on etc/ISABELLE_ID, so no file is created (C7).
- One prefix P from which the tree and features.d both derive (C18).

Owner questions: pack.sh's packaging edits (C9), how light's HOL session ships (C11), later feature versions on 2025.2-0 (C22), conda-only release (C24), and a confirmation that install-by-rename fits ruling 18 (C2). Re-review is needed for the engine, the state model, the hooks, (b2) and the release infrastructure. The rest is text and test work the author can do under ruling 17.

## Questions for the owner

Q1 (C9). Ruling 11 says the conda `isabelle` package is '原版，原汁原味' (pristine, untouched). Besides the feature patches, the packaging script pack.sh changes three files:
- It appends a conda suffix to ISABELLE_HOME_USER in etc/settings, so each environment gets its own Isabelle user directory (pack.sh:184-189).
- It sets ML_system_64=true in etc/options, so the default word size matches the 64-bit Pure/HOL/Main heaps the package ships (pack.sh:206-211). pack.sh:200-204 says this flip must move together with the heap jobs, otherwise HOL is rebuilt on first use.
- It removes the nunchaku line from etc/components (pack.sh:226-231).
On Windows it also adds bin/isabelle.bat (pack.sh:159-165).
Which reading do you mean?
(a) Recommended: Isabelle's sources are untouched and etc/ISABELLE_ID is the release changeset 89701cf1768e; these packaging edits, the CI-built heaps and isabelle.bat stay.
(b) The packaging edits go too. The shipped heaps then no longer match the default word size, so HOL is rebuilt on first use, and environments share one user directory unless the CI plan finds another way.

Q2 (C11). light_locale is two things: the Pure patches (32 files), and an Isabelle session, `session Light_Locale = HOL` (contrib/light_locale/ROOT). That session's theory declares the commands users install light for: light_locale, implicit_structure, set_implicit_structure, with_implicit_structure (Light_Locale.thy:4-11). The planned feature-package template carries only patch files, so `isabelle-light-locale` as planned would install the patches without the commands. How should the session ship?
(a) Recommended: a separate session package, built the way the channel's other component packages are (files under share/<package>/, registered with `isabelle components -u/-x` in its own hooks, RELEASE_CHECKLIST.md §4), which depends exactly on the light patch package. The feature packages' hooks stay identical one-line calls. You would also choose the names, for example keep `isabelle-light-locale` for the patches and call the session package `isabelle-light-locale-session`, or give the plain name to the session package that users install.
(b) The feature-package template gains an optional component payload, so isabelle-light-locale also ships the session and its hooks also call `isabelle components`. The hooks then differ per package and again call isabelle, with the Windows warm-up that needs.
Either way the batch release gains this step.

Q3 (C22). Rev 1's question 10 had two halves. On 2026-10-23 you were told that the second half had 'disappeared' once future isabelle builds are pristine. That was wrong. The published isabelle-2025.2-0 still carries expose_foreign version 1 built in, and its package declares no constraints and can never get any. So when a later version, for example isabelle-expose-foreign 2 and a light built on it, is published, conda will install it onto 2025.2-0. A toy channel shows this: `conda update isabelle-light-locale` keeps isabelle 2025.2-0 and swaps in the whole version-2 chain. Choose:
(a) Later versions carry a constraint that keeps them off 2025.2-0, so the solver moves the user to the new pristine isabelle build by itself. Under conda's default solver the natural spelling `isabelle[build_number=">=1"]` makes every solve fail (measured). It would need either an exact build-string match on isabelle, which ruling 21 excluded, or a build-string prefix that the CI plan gives every new pristine build and that later feature packages match on.
(b) Accept it; rev 2 does this provisionally. The update succeeds; the old version-1 features are reversed by their removal hooks; the tool refuses the version-2 chain on 2025.2-0 (exit 3), so no feature is applied. conda prints a message telling the user to run `conda update isabelle`, which then repairs everything.

Q4 (C24). The plan publishes isabelle-patch-control 1.0.0 to both PyPI and conda. Your 2026-10-11 decision was to rename the tool and publish it to conda (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1958). Nobody would install the new tool from PyPI: every feature package pulls in the conda package, and make-patches imports the tool from the checkout. A PyPI release would add the rule that the conda package must never fall behind PyPI (RELEASE_CHECKLIST.md:243-245), for every future release. Choose:
(a) Recommended: conda only. The old my-better-isabelle-prover 0.3.0 stays on PyPI untouched.
(b) Both PyPI and conda.

Q5 (C2), confirmation. The plan says git apply is the only program that writes Isabelle's files. Measured: when git apply writes several files, it first deletes all the old files and then creates the new ones. So a Ctrl-C during `conda install`, a full disk or a killed process can leave Isabelle source files missing, and no command of the tool can repair that. The proposed fix keeps git apply as the only program that produces patched content, but runs it on a copy of each file in a staging directory next to the tree. The tool then moves each finished file into place with an atomic rename, so every file is always either fully old or fully new. Is this consistent with your ruling 'the engine is git apply; no self-written engine'?
(a) Yes. Recommended: moving a finished file into place is not patch logic.
(b) No. Then the plan must accept the window and document how to recover from it.

## Relaxations recommended

1. Install by rename as the single write path (C2, C6, C19, C20):
- replay each file's own patches on a staging copy with git_apply;
- set the staging file's mode;
- os.replace or os.unlink it into the tree, one file at a time, from a staging directory on the tree's filesystem but outside the tree.
status, --dry-run, apply, unapply, apply-to and unapply-from share one path: replay, then install or not. So what status predicts is exactly what is installed. Every file is always old or new, modes are identical for every caller, and a git write failure can only happen in staging.

2. git's environment built inside git_apply from a whitelist (C1):
- PATH, plus SystemRoot/TEMP/TMP on Windows;
- GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=devnull, GIT_ATTR_NOSYSTEM=1, LC_ALL=C;
- GIT_CEILING_DIRECTORIES set to the parent of git's working directory;
- `-c core.autocrlf=false -c core.attributesFile=devnull`;
- umask 022.
Plus an exit-3 refusal of any tree containing .git, for every command. Measured: correct verdicts and an exact round trip inside an enclosing repository with no HOME (judge/c1/whitelist.out). Do not use GIT_DIR=/nonexistent: git reads $GIT_DIR/config.

3. Per-file target levels instead of per-feature calls (C5, C6):
- apply moves files only up, to the top or F, capped just below the lowest feature that has a CONFLICT file;
- unapply moves files only down;
- a file that fits several levels is CONFLICT unless moving it from each gives the same content.
The created-file rule and the prefix/hole shape rule are deleted as inputs; applied, half-applied, not-applied and hole become words status displays. A left-behind created file is then simply a file already at its creator's level: apply leaves it alone and unapply deletes it.

4. Every chain walk starts at <R>/pristine/<c> (C3). The LEGACY_BUILDS entry becomes 5533cd83156e -> (89701cf1768e, Isabelle2025-2/expose_foreign/1): a pre-applied level that counts on the chain, links by base_tag like any other level, is verified by the per-file level computation when its directory is present, and is never applied or reversed. One walk rule for every tree, and decision 10's 'naturally' becomes true.

5. One byte-identical post-link fragment with no feature argument, owned by the tool repository and copied verbatim by the renderer and by the CI plan for the isabelle package (C4):
- `if [ -x tool ]; then tool conda-hook post-link || echo ... >> .messages.txt; elif [ -d features.d ]; then echo ... >> .messages.txt; fi`, then `exit 0`;
- only pre-unlink names its feature.
The conda-hook command lines, PREFIX, exit 0 and .messages.txt are frozen for 1.x.

6. Lock the tree's existing etc/ISABELLE_ID instead of creating a lock file (C7): flock, shared for status and exclusive for writers; on Windows a 1-byte msvcrt lock past the end of the file; a bounded wait. Nothing is created, so §6 (g), clones and the (b2) comparison are correct by construction.

7. Derive the tree and features.d from one prefix P (C18): $PREFIX in conda-hook, else the parent of --isabelle-home, else sys.prefix. The default features.d is used only when P/conda-meta is a directory. A tree and features.d from different environments can then no longer be combined.

8. Optional, author's choice (C8, C3): status compares tracked isa/ files against the isabelle package's per-file sha256 in conda-meta (24538 paths; about 0.34 s to hash isa/src) and walks for untracked files. It reports changes that no installed feature explains. Leftovers of a failed pre-unlink, a built-in expose_foreign reversed by 0.x, and user edits then become visible to status by construction, with no new ledger.

9. One batch release workflow in the tool repository's .github/workflows/ (C12, C13, C15, C21):
- it checks out each feature repository at its release tag;
- it renders the recipes at build time;
- it builds every package into one local channel per leg and runs §6;
- it publishes that same artifact through one publish-conda.yml call.
The accepted bytes are then the published bytes, one repository holds secrets and a PUBLISH_REPOS entry, and the batch cannot race with itself on repodata.json. The pristine isabelle build is published last, in a separate serial run.

10. Publish isabelle-patch-control 1.0.0 to conda only (C24): one release path and no lockstep rule (pending Q4).

11. One package_name(feature) function in tools/common.py, imported by the renderer and by make-patches' path-length gate, and parsing of patch targets with `git apply --numstat --summary` instead of a hand-written header parser (C20, C21).

## Critics' overall notes

- conda: I re-checked rev 2 through the conda lens against conda 25.11.1's source and toy channels. Rev 2 carries out the owner's rulings 11-19 faithfully: the isabelle package has no feature patches (k=0), the engine is git apply, hooks always exit 0 and report through .messages.txt, new isabelle builds re-apply installed features, all five platforms, non-conda trees unsupported, Isabelle2024 left in the old tool, one-batch publication.

The core hook design also holds up in the toys:
- post-link applies the whole chain;
- pre-unlink only reverses;
- clone and relinks recover.

It rests on correct facts:
- conda creates entry points before post-links (core/link.py:956-959), and on Windows as `Scripts\<cmd>.exe` (core/path_actions.py:811-838);
- the post-link runs inside an activated environment, while the pre-unlink only gets $PREFIX/bin (Scripts on Windows) prepended to PATH (core/link.py:1109-1114, :1635). So looking git up explicitly at sys.prefix/Library/bin/git.exe is needed, and conda-forge's own test of git.exe confirms that path;
- `isabelle >=2025.2,<2025.3` and `==<v>=Isabelle2025_2_*` parse and match correctly;
- the path-length answer stands.

The remaining defects:
- **Blocking: git apply is not isolated (conda-1).** When a prefix sits inside a git work tree, git apply silently does nothing, while the hooks and `status` report the features as applied (measured in a real conda install). Git for Windows' default `core.autocrlf=true` makes git apply write CRLF, and an unapply no longer restores the pristine file.
- **Major: the chain rule contradicts decision 10 (conda-2).** On the only published build, isabelle-2025.2-0, the rule makes every hook exit 3.
- **Major: exit 0 is not built into the hook text (conda-3).** Rev 2's own isabelle line exits 1, and a rollback follows, when the tool is absent.
- **Major: three rev-1 items survive.**
  - C1's action rules: apply must skip a feature's leftover created files, and unapply must delete them (conda-4).
  - C2's pre-unlink policy: a failed pre-unlink leaves changes that `status` cannot see, while Appendix A claims they are visible (conda-5).
  - C22's single-source default (conda-8, minor).
- **Major: two new mechanisms are unsound.**
  - The lock file inside isa/etc defeats acceptance (g) (conda-6).
  - git apply's write phase is not atomic, and a truncated file reads as applied (conda-7).

Smaller items: repeated or false .messages.txt notices, test assertions that contradict measured pruning, and three wrong facts.

Almost all of the fixes are local: isolation inside the one `git_apply`, a hook text that ends in exit 0, one dedupe sentence, staged writes. The design does not need restructuring.

Evidence (scripts and outputs) is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/critic-conda/: git1.out, git2.out and git3.out for the git experiments; run.out, run2.out and run3.out for the conda toy channels, with their scripts mkchan.py, run.sh, run2.sh, run3.sh, git1.sh, git2.sh and git3.sh.

- engine: Rev 2 follows the owner's rulings in its outer shape:
- `git apply` is the engine;
- hooks are one generated line that exits 0, with whole-chain apply in post-link and pure reverse in pre-unlink;
- the new `isabelle` build's post-link re-applies the installed features;
- 2025.2-0 is handled by a fixed record;
- the tool never runs `isabelle`.

The per-file level replay is sound on today's chain. I re-ran it on every prefix of the real chain (pristine plus 0 to 4 features): each of the 40 files had exactly one level, at 126 to 128 `git` calls and 1.3 to 2.3 s per status. Several rev-1 items are resolved or moot:
- C8: `git apply` never prompts;
- C16's copy step and C17's gate (c) import;
- C24's empty-file refusal and C27's write-after-gates;
- C4: whole-chain post-link;
- C6's exact-tag linking, except as noted in E4.

The engine itself, however, is specified as a bare `git` call, and the claims about it were measured on other inputs than the plan uses.
- E1 (blocking): `git` discovers repositories on its own. Inside any git work tree it silently does nothing, with `--check` passing both ways and apply exiting 0. This happens for a `conda create -p ./env` inside a project repository, for (b2) copies placed in `ai-artifacts/` as CLAUDE.md instructs (so the release gate passes vacuously), and when TMPDIR lies inside a repository. At a work-tree root it edits the shared and private Isabelle trees, and rev 1's `.git` guard was dropped.
- E2 (major): the user's git configuration and attribute files change the written bytes (CRLF; the round trip is no longer byte-exact) and the verdicts.
- E3 (blocking): the atomicity claim is false. Separate patch-file arguments are applied one by one (24 of 32 light files written before a mismatch). A single stream unlinks every modified file before writing any, so a write failure or a Ctrl-C forwarded by conda deletes 28 of light's 29 modified sources, and no command of the tool can repair that. Rev 1's rollback directive and its interruption tests were dropped on the strength of this claim.

The state model has three structural problems:
- E4 (major): decision 3 as written gives exit 3 on every 2025.2-0 environment. The required sentence "a directory whose release_tag is a manifest entry is that built-in entry" from rev 1's C6 judge is missing, so decision 10's "naturally" does not hold.
- E5 (major): the special created-file rule and the shape rule misread reachable states. When an upper feature renames a lower feature's created file, a correct tree never reads applied, and repeated hook runs re-create and delete the file in turn. When an upper feature edits a created file and conda then relinks `isabelle`, the result is CONFLICT and ruling 13's automatic repair fails. A relinked light leaves its created files behind on unapply, which rev 1's C1 judge had already flagged.
- E6 (major): the level definition leaves open the reading that reproduces rev 1's false CONFLICT. It does not say the forward half is sequential, it does not define several fitting levels, and it does not define --dry-run.

The remaining findings are smaller:
- E7 (major): the lock file leaves residue in `isa/` by construction, and deleting it after use is racy.
- E8 (minor): mode restoration rests on a false fact (no 0444 sources exist in the package).
- E9 (minor): failures are not classified, so symlinked targets and corrupt patch files read as CONFLICT.

Most fixes converge on one shape, which makes these invariants impossible to violate instead of something people must remember:
- one isolated `git` invocation, with GIT_DIR=/nonexistent, no system or global configuration, no attributes file, a fixed umask and a `.git` refusal;
- run only on scratch copies;
- apply and unapply defined as per-file moves to a target level, installed by `os.replace`;
- status, --dry-run, apply and the directory interface as one code path.

I prototyped this shape. It repairs all toy cases in both directions, and it repairs a relinked real chain to exactly the dev_patches tip in 2.2 s. All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/critic-engine/.

- consistency: Rev 2 is not ready. It gets the outline of the 2026-10-23 rulings right:
- the conda isabelle package is pristine, and a fixed LEGACY_BUILDS record carries the published 2025.2-0;
- a single `git_apply` function is the only engine;
- hooks exit 0 and report through .messages.txt;
- new isabelle builds' post-link re-applies installed features;
- the PACKAGING_DESIGN exception, Isabelle2024 left in the old tool, one-batch publication and conda-only support are all present.

Most of rev 1's structural fixes also landed: the per-file levels, the half-applied state, the created-file rule, linking by exact tag, the whole-chain post-link with a pre-unlink that only reverses, the renderer, the hook-layer tests, the local channel before publishing, and the make-patches changes. The conda source citations hold, except the unlink-order one.

Checked against the sources, however, several of rev 2's claims are false, and ruling 11 has a consequence the plan misses:
- **The batch breaks the AoA stack.** Publishing the pristine isabelle without making Semantic_Embedding depend on isabelle-expose-foreign breaks Semantic_Embedding and everything built on it (F1, blocking).
- **The 2025.2-0 path fails.** Decision 3's linking rule refuses the expose_foreign directory on 2025.2-0, so every feature install on the only published build exits 3 (F2).
- **The engine is specified unsafely.**
  - git apply's behaviour depends on the caller's git environment: inside any git work tree it silently skips every patch (F3).
  - git apply is not atomic against write failures: it unlinks every target before creating them (F9).
  - The forward half of the level test, as written, gives a false CONFLICT on the real light/dev_patches pair (F10).
  - Restoring permission bits rests on a false premise (conda files are 0644, not 0444) and makes the tool and raw git apply disagree on modes, so (b2) cannot compare modes (F5).
- **The exit-0 guarantee is not in the hook text.** The planned isabelle post-link line returns 1 when the tool is absent (F4).
- **Appendix A states false facts.** It claims the package is byte-identical to the official distribution, and it contradicts decision 11.2 (F6).
- **§6 (g) cannot pass.** The lock file and orphaned created files leave isa/ behind after `conda remove isabelle` (F7).
- **(b2) has drifted from migration §5.1.** It changed engine without saying so and no longer runs before each publication (F8).

A dozen rev-1 judge items were also dropped, although the header says every confirmed item was absorbed (F11-F17).

- landing: Rev 2 does not misread any of the rulings. It aims at all of them: the conda `isabelle` package stays pristine, with a fixed record for 2025.2-0; the engine is `git apply`; hooks exit 0 and report through `.messages.txt`; the `isabelle` post-link re-applies installed features; and non-conda trees are refused. Several rev-1 defects in my lens are genuinely fixed: gate (c) now imports the engine by path, empty-file blocks are refused, there is a Windows path-length gate, `make-patches` writes nothing before its gates pass, packages are verified from a local channel before publication, and there is a migration section for 0.x users.

From the landing, operations and acceptance angle, the plan is not ready. The findings fall into four groups.

1. The engine call that every operation, test and acceptance step rests on has three measured defects:
   - `git apply` is atomic only within one patch file, not across the several patch-file arguments the plan passes (L1).
   - Inside any enclosing git work tree it silently skips every patch and exits 0 (L2).
   - It picks up the user's or the system's `core.autocrlf` and rewrites files to CRLF, and the planned tests isolate git config, so they cannot see this (L10).
2. The schedule and ownership do not hold:
   - The §6 acceptance is due at step 5, but it needs the pristine `isabelle` build that only step 6's CI plan produces, and the CI plan in turn needs step 5's packages (L3).
   - The cross-repo local channel, the release workflows, the GitHub repos, the per-repo secrets and the PUBLISH_REPOS entries are unowned. The reusable workflow is placed where GitHub cannot call it (L4).
   - The one-batch release names no order and ignores the documented race on the channel's index between repos (L12).
3. Several items the rev-1 judges confirmed survive:
   - C20: the expectations on removal and on a failed post-link are still wrong (L5).
   - C17/C21: (b2) is still not a per-release script, still runs contradictory code, and its pristine leg cannot run on a git archive (L6).
   - C21: derived recipes are committed (L13).
   - C17/C21: the step-0 and rename housekeeping is still missing (L14).
4. New defects:
   - light's HOL-side session has no package (L7).
   - The hook text does not guarantee exit 0, and the `isabelle` line as given breaks `conda install isabelle` when the tool is absent (L8).
   - The lock file leaves an untracked residue in `isa/` (L9).
   - Appendix A's claim that the package is byte-identical to the official release is false, given pack.sh's three edits (L11).

Most fixes are small and make the invariants hold by construction:
- one stdin stream per `git apply` call;
- one isolated git environment, with a ceiling directory and no global or system config;
- generated hooks that end in `exit 0`;
- a lock on a file conda tracks;
- a (b2) script that every release must pass;
- one joint acceptance after the CI's pristine build exists, on all five subdirs;
- a serial publish in dependency order, ending with a smoke install from the live channel.

All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/critic-landing/ (subdirectories stack, enclosing, crlf, toy2, legacy and newdir), using conda 25.11.1 with a private HOME, CONDARC and package cache, and git 2.43.0. No repository or Isabelle tree was modified.

- user: Rev 2 carries out the owner's rulings 11-19 faithfully in outline. The `isabelle` package is pristine; 2025.2-0 is handled by one fixed record; the engine is `git apply`; hooks are meant to exit 0; new `isabelle` builds re-apply features in post-link; every platform is in scope; only conda is supported; Isabelle2024 stays in the old tool; everything is published in one batch. Most rev-1 challenges are resolved or made moot: C1, C3, C4, C5, C10, C19, C22-C25, C27 and C28 are resolved, and C8, C11, C12, C13's main hazard and C15 are moot. Judged from the user's and the maintainer's side, though, rev 2 is not ready.

I walked the eight scenarios on a toy file:// channel shaped exactly like rev 2: one-line hooks, a whole-chain apply on every post-link, exit 0, reports through `.messages.txt`, and a lock file under `isa/etc`. Scripts and output are in `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/critic-user/` (mkchan2.py, run2.sh, run2.out, e1.sh-e3.sh).

(a) Fresh `conda install isabelle isabelle-light-locale` on the new pristine build: the `isabelle` post-link applies all three features and prints one applied line plus the heap notice. The other hooks do nothing, and the plan never says they must print nothing.

(b) The same on isabelle-2025.2-0: as written, decision 3's chain rule rejects the `isabelle-expose-foreign` directory that conda always installs as a dependency, so the walk ends with exit 3 (F2).

(c) `conda update isabelle` from 2025.2-0 with light installed: it works by design, but §6 never tests it. Users without the tool silently lose expose_foreign, and no release note tells them (F11).

(d) `conda remove isabelle-light-locale`: it also removes future_assign_interrupt, expose_foreign and the tool, and prints three heap notices (F12).

(e) A conflict caused by a user edit: the same error block is printed once per feature hook (three times), and it ends with a repair command that cannot repair it (F4).

(f) Light releases version 2: the update prints two heap notices. If the pre-unlink fails, the residue becomes invisible to `status`, and light 2's created files end in a CONFLICT that `--force-reinstall isabelle` does not clear (F4).

(g) The maintainer cutting a feature package: the reusable workflow sits where GitHub cannot call it, it bypasses the channel's existing publish workflow, and nothing runs the (b2) check for any release after the first (F8, F9, F10).

(h) A Windows user: Git for Windows ships `core.autocrlf=true`, and `git apply` honours it outside a repository. Every patched file is rewritten with CRLF line endings, and unapply does not restore the original bytes (F1).

The most serious defect is F1: `git apply` is run without isolation from its environment. Inside an enclosing git work tree it skips every file, exits 0, and `--check` and `-R --check` both pass; a personal or system git config rewrites line endings. A few environment variables inside the single `git_apply` function fix both; I measured this. Two of the plan's claims about `git apply` are false. Its write phase is not atomic: an I/O failure half-applies a feature, and SIGKILL left 2,982 of 3,000 target files missing. And a crash of the tool escapes the exit-0 policy, because that policy lives in the tool rather than in the hook text.

Several rev-1 instructions were dropped without comment:
- C6: the clause that recognises the pre-applied directory.
- C7: rollback and interrupt tests.
- C13: checking that a pre-applied feature is really present.
- C14: the `.git` guard.
- C16: the 0444 premise, which is still repeated.
- C17: the old editable installs.
- C18: naming `isabelle getenv ISABELLE_HOME_USER` in the heap notice.
- C20: the pruning expectations.
- C21: the per-release (b2) script, the per-repo secrets, and not committing the derived recipe.
- C2: the pre-unlink message policy.

Appendix A, the justified exception the owner asked for, contains several false statements (F7).

## Dropped by the merge editor

- consistency-F1: Refuted. The claim is that publishing the pristine isabelle takes expose_foreign away from Semantic_Embedding and breaks the AoA stack. The sources say otherwise.
- Semantic_Embedding.thy:2 imports Isabelle_RPC.Remote_Procedure_Calling.
- Isabelle_RPC/Remote_Procedure_Calling.thy:2 imports Performant_Isabelle_ML.Performant_Isabelle_ML.
- Performant_Isabelle_ML.thy:7 loads library/rescue_foreign.ML, which binds Foreign again in the global ML name space on a pristine Pure. Its plan reports 'PRISTINE/after: Foreign=YES' (Semantic_Embedding/archive/plans/FOREIGN_RESCUE.md:114).
- That file is in the released v0.2.0 (`git show v0.2.0:library/rescue_foreign.ML`), and Semantic_Embedding/conda/recipe.yaml:338 requires isabelle-performant-ml >=0.2.0,<0.3.0.
- Every non-comment FFI use in Tools/simd_vector.ML is Foreign. Its RunCall uses sit inside the comment block :100-115 and the comments at :129, :137 and :182.
- The only other FFI user in the stack, Performant_Isabelle_ML/library/thread_cpu.ML, loads after the rescue.
The pristine build therefore does not break Semantic_Embedding. user-F11 reaches the same conclusion. The remaining real point, users outside the ecosystem who call Foreign themselves, is kept in C16.

## Challenges

### C1 [blocking] git apply runs with the caller's environment: inside any git work tree it silently does nothing, at a work-tree root it edits git-managed trees, and git config or attribute files rewrite the bytes it writes

Section: Decision 4 (plan:171-174); decision 2 (plan:146-151); decision 7 (plan:219-222); §2.4 (plan:119); §8 (plan:405); decision 14 (plan:300-307)  ·  merged from: conda-conda-1, engine-E1, engine-E2, consistency-F3, landing-L2, landing-L10, user-F1, user-F15

**Statement.** What the plan says. Every patch operation goes through one function, git_apply, which runs plain `git apply [--check] [-R] --whitespace=nowarn <patch files>` with the tree as working directory and the inherited environment (plan:171-174). All of the plan's git evidence was gathered "in a plain directory, not a git repository" (plan:119, :405), under the owner's own git configuration.

What git actually does. Before applying anything, git looks for a repository by walking up the parent directories, and it reads the system config, ~/.gitconfig and the attributes file ~/.config/git/attributes, even when no repository is found. conda hooks inherit the user's environment, HOME included (conda/core/link.py:1564, env = os.environ.copy()). Three measured consequences, git 2.43.0 (scratch root /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/):

(a) A tree inside an enclosing work tree. git reads the `diff --git` paths as relative to that repository's top and skips every file. `--check` gives rc=0, `-R --check` on the UNPATCHED file also gives rc=0, apply gives rc=0, and the file is unchanged. Only `-v` prints "Skipped patch" (merge/g/evidence.out case 1; critic-engine/e1/noop.sh with light's 32 real patches: the created file never appears). Realistic placements: `conda create -p ./env` inside a project checkout; a $HOME kept in git; scratch or (b2) copies under ai-artifacts/, which CLAUDE.md:41-43 prescribes and which lies inside the MLML repo. In a real conda install the hooks logged `applied` and status printed `applied` while the tree was untouched (critic-conda/run.out scenario D). (b2) then passes vacuously: copies A and B both stay equal to the original.

(b) A tree that is itself a work-tree root. This covers the shared tree contrib/Isabelle2025-2, which has a .git directory, and the private and stock trees, which have a .git file. git applies normally there and edits a tree that may change only through git (migration plan §7 rule 1, :529). GIT_CEILING_DIRECTORIES does not prevent this (merge/g/evidence.out case 7: rc=0, `git status` shows ` M src/Pure/a.ML`). Decision 2 accepts any tree given with explicit flags (plan:146-151). Rev 1's judge required the single writer to refuse any tree where `.git` exists (REVIEW1:1356); rev 2 dropped that guard.

(c) Line endings and verdicts.
- core.autocrlf=true, Git for Windows' system default and a common personal setting, rewrites every patched and created file with CRLF.
- `-R --check` still passes, so status reads applied, and reversing leaves the file in CRLF, so unapply no longer restores the package's bytes (merge/g/evidence.out case 5; critic-conda/git2.out; critic-engine/e3/run.sh).
- An attributes line `* text eol=crlf` does the same even with GIT_CONFIG_GLOBAL=/dev/null (merge/g/evidence.out case 6).
- apply.ignoreWhitespace=change makes a forward check pass on a hand-edited file (critic-engine/e3/run.sh (c)).
Ruling 18 makes Windows mandatory (plan:59), and RELEASE_CHECKLIST.md:178 records a CRLF etc/settings that already broke a win-64 release.

The tests cannot see any of this, because the existing toy tests export GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1 (tools/tests/test_make_patches.sh:9-10). Rev 1 had already learned the analogous lesson for GNU patch (scrub POSIXLY_CORRECT, REVIEW1:800-806), and rev 2 applies no environment control at all.

Required. Decision 4 must fix the child environment and flags inside git_apply itself, so that every caller gets them by construction: status replay, apply, unapply, apply-to and unapply-from, make-patches gate (c) and (b2).
- Environment built from a short whitelist (PATH; SystemRoot and TEMP on Windows), so no GIT_* or XDG_* variable is inherited.
- GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=<null device>, HOME=<empty scratch directory>.
- GIT_DIR=/nonexistent, measured to force non-repository mode on 2.43 (merge/g/evidence.out case 1, last line: the reverse check correctly fails); alternatively GIT_CEILING_DIRECTORIES set to the tree's parent.
- LC_ALL=C, so that the messages copied into .messages.txt are stable.
- `-c core.autocrlf=false -c core.eol=lf -c core.attributesFile=<null device>`.
- Refuse with exit 3 any tree where `<tree>/.git` exists, for every command.
§2.4 must record what git apply consults. Add pytest cases, each of which must give the clean case's bytes and verdicts:
- a tree inside a gitignored subdirectory of a repository;
- a tree at a work-tree root;
- a hostile HOME (autocrlf, an attributes file, apply.ignoreWhitespace, apply.whitespace=error);
- GIT_DIR and GIT_WORK_TREE exported by the caller.
The Windows acceptance leg compares file bytes after apply and after unapply, not only status.

**Editor.** The core claim is confirmed by my own runs (merge/g/evidence.sh and evidence.out) and by four critics independently. Points where the critics overreach:
- user-F1's remark about MSYS2 tools under Library\usr\bin sitting on PATH next to Isabelle's Cygwin is unmeasured and is not part of this challenge.
- The claim that PortableGit's system config sets autocrlf=true is taken from Git for Windows' build-extra sources; nobody measured it on a Windows machine, and consistency-F3 says so itself. The fix does not depend on it, because personal configs set it anyway.
- landing-L2's extra idea of treating any "Skipped patch" line in the `-v` output as a failure only patches the symptom; isolation makes the skip impossible.
- user-F15 would refuse `.git` trees only for apply and unapply, not for --check. That is weaker than needed: a status that replays inside a repository also gives wrong verdicts. Refusing the tree up front, for every command, is simpler.
- GIT_CEILING_DIRECTORIES alone (conda-conda-1, consistency-F3, landing-L2) does not stop git at a tree that is itself a work-tree root (my case 7). The `.git` refusal is therefore needed in addition, not as an alternative.

**Relaxation proposed by the editor.** Build git's environment from a whitelist instead of inheriting the caller's and removing known variables. Then no present or future GIT_* variable, XDG path or config file can leak into the engine. Together with the fixed `-c` flags and the `.git` refusal, the result of every call depends only on the tree and the patch files, and one hostile-environment test case covers all of it.

**Defender: partially_confirmed** (needs owner: False).

CORE DEFECT CONFIRMED; severity stays blocking.

What the plan says.
- Decision 4 runs plain `git apply [--check] [-R] --whitespace=nowarn` with the tree as working directory. It says nothing about the child's environment or config (plan:171-174).
- The plan's evidence was gathered only "in a plain directory, not a git repository" (plan:119, :405).
- conda hooks inherit the caller's environment: `env = os.environ.copy()` (conda/core/link.py:1566; the challenge cites :1564).
- `grep` finds no GIT_*, autocrlf or `.git` handling anywhere in the plan.

My own runs (git 2.43.0; defender-C1/exp.py, results in exp.out). Each case compares plan rev 2's call against an isolated call.
(a) Tree inside a gitignored subdirectory of a repository.
- Plan's call: `--check` rc=0, `-R --check` on the UNPATCHED tree rc=0, apply rc=0, tree unchanged.
- Isolated call: correct verdicts, and the tree is patched.
- Real placements exist on this machine. The owner's conda root and home are not inside a work tree. But both ai-artifacts/ directories are (git rev-parse shows MLML and my_better_isabelle_prover), and migration rule 1 (ISABELLE_GIT_MIGRATION_PLAN.md:529) and CLAUDE.md send scratch work there.
- Rev 2 switched (b2) copy B from `patch -p1 -F0` (migration :399) to git apply (plan:354-355). Migration :399-402 has no "A differs from the original" check. So (b2) placed there passes vacuously: copies A and B both stay equal to the original.
(b) Tree at a work-tree root.
- git applies normally but reads the repository's own config: with core.autocrlf=true in that repository, apply wrote CRLF and unapply did not restore the original bytes.
- The real danger is a policy breach, not a git malfunction. Rev 1's judge, on C14, ordered the single writer to refuse any tree where `.git` exists (REVIEW1:1346, :1356). Rev 2 has no such guard, although plan:4 claims every confirmed item was absorbed. This is a rev-1 defect that survived.
(c) Hostile environment. Each of these gave CRLF, a reverse check that still passes (so status reads applied), and an unapply that does not restore the bytes:
- ~/.gitconfig with autocrlf=true;
- ~/.config/git/attributes with `* text eol=crlf` (even with GIT_CONFIG_GLOBAL=/dev/null);
- an exported GIT_DIR, or GIT_DIR plus GIT_WORK_TREE, naming another repository;
- GIT_CONFIG_COUNT/KEY/VALUE, which a parent `git -c` exports.
- Separately, apply.ignoreWhitespace=change made `--check` pass on a hand-edited file (ceiling.sh).
- Windows is mandatory (plan:59). The CRLF hazard is real: RELEASE_CHECKLIST.md:178 records a win-64 package pulled because of a CRLF etc/settings.
- The tests cannot see any of this: the toy tests export GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1 (tools/tests/test_make_patches.sh:9-10), the hook tests use a private HOME (plan:304), and decision 14 (plan:300-303) has no hostile-environment case.

REFUTED OR CORRECTED.
1. The supporting example "status printed applied while the tree was untouched" (critic-conda run.out scenario D) comes from the critic's prototype. Its state() replays in the tree (`cd "$T" && git apply -R --check`, critic-conda/mkchan.py). Plan decision 5 replays on copies in a temporary directory instead (plan:186-189). Under the plan, status after the no-op therefore says not-applied, unless the temporary directory is itself inside a work tree. What survives is that apply, unapply, apply-to, unapply-from and the hooks silently do nothing and report success, and that (b2) can pass vacuously.
2. The required fix's `GIT_DIR=/nonexistent` is a hack.
- When GIT_DIR names a directory that is not a repository, git still reads `$GIT_DIR/config`. strace shows the probe of /nonexistent-ipc/config.
- I planted a config at that path. It turned CRLF on (5 CR bytes), and with the challenge's own `-c core.autocrlf=false -c core.attributesFile` flags in place, a planted apply.ignoreWhitespace still flipped a conflict verdict to rc=0.
- On Windows, /nonexistent resolves to C:\nonexistent, which any user can create.
- The documented alternative works: GIT_CEILING_DIRECTORIES=<the resolved parent of the working directory> gave correct verdicts and a byte-exact round trip in an enclosing repository, including through a symlinked path. It needs the `.git` refusal alongside it, and that refusal is required anyway (rev-1 C14).
3. The fix list misses GIT_ATTR_NOSYSTEM=1. GIT_CONFIG_NOSYSTEM does not stop git from opening the system attributes file /etc/gitattributes (strace).
4. Three items in the fix list are unnecessary:
- HOME=<empty dir>: once GIT_CONFIG_GLOBAL and core.attributesFile point to the null device, nothing is read from HOME.
- core.eol=lf: it acts only on files that have a text attribute.
- In-tree .gitattributes are ignored outside a repository (t2 and t3: 0 CR bytes). LC_ALL=C already follows from the whitelist.

THE EDITOR'S RELAXATION. It is sound. My GIT_CONFIG_COUNT case shows that removing known variables one by one misses things. The repository already builds a child environment from a whitelist (tools/run-tree:31, PASS_THROUGH), so the relaxation reuses an existing shape. Caveat: which variables Windows needs in the whitelist (SystemRoot, TEMP, TMP) is unmeasured, so the Windows leg must exercise it.

Experiment: All experiments are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C1/.
- setup.sh builds a toy tree and a real `git diff-tree -r -p` patch that modifies src/Pure/a.ML and creates src/Pure/new.ML.
- exp.py (results in exp.out) runs plan rev 2's call (inherited environment, working directory = tree) against an isolated call (whitelist environment, GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=null, GIT_ATTR_NOSYSTEM, GIT_DIR=<fresh path>, -c core.autocrlf=false, -c core.attributesFile=null) over eight scenarios: plain directory; tree in a gitignored subdirectory of a repository; tree at a work-tree root whose repository has autocrlf; ~/.gitconfig with autocrlf; XDG attributes file; exported GIT_DIR; exported GIT_DIR plus GIT_WORK_TREE; GIT_CONFIG_COUNT. For each it reports --check, the reverse check on the unpatched tree, apply, CRLF, the reverse check after apply, unapply, and whether the base bytes are restored.
- ceiling.sh: GIT_CEILING_DIRECTORIES=<parent> in an enclosing repository (rc=1 on the unpatched reverse check; byte-exact round trip; also through a symlinked path), and apply.ignoreWhitespace=change turning a hand-edited file into rc=0.
- st/: strace of the files git apply opens in the plan form and the isolated form (it opens /etc/gitconfig, ~/.gitconfig, the XDG config and attributes files, /etc/gitattributes, and walks every parent directory for .git); a planted config in a non-repository GIT_DIR is read (t1: 5 CR bytes; ignoreWhitespace flips the verdict even with the -c flags); in-tree .gitattributes are ignored outside a repository (t2, t3).
- Read-only checks: git rev-parse on the conda root, the home directory and both ai-artifacts/ directories; grep of the plan; REVIEW1:1237-1360 and :790-806; migration plan :376-438 and :521-560; make-patches :63-69 and :174; common.py :155-167; run-tree :31; conda link.py:1566; RELEASE_CHECKLIST.md:178.

Recommended fix: Smallest fix, all inside the one function every caller already uses (decision 7), so every caller gets it by construction.

1. Decision 4: git_apply builds the child process itself.
- Environment: copied from a whitelist in the shape of tools/run-tree:31 (PATH; on Windows also SystemRoot, TEMP, TMP), plus:
  - GIT_CONFIG_NOSYSTEM=1
  - GIT_CONFIG_GLOBAL=os.devnull
  - GIT_ATTR_NOSYSTEM=1
  - LC_ALL=C
  - GIT_CEILING_DIRECTORIES=<resolved parent of the working directory>
- Command line: `git -c core.autocrlf=false -c core.attributesFile=<os.devnull> apply ...`.
- Do NOT use a fixed GIT_DIR=/nonexistent, because git reads $GIT_DIR/config. If GIT_DIR is preferred over the ceiling, it must name a path inside a fresh temporary directory the tool creates.
- HOME and core.eol are unnecessary.

2. Restore rev-1 C14's guard.
- Refuse with exit 3 any tree for which `<tree>/.git` exists, as a directory or a file, when the tree is resolved, for every command that names a tree.
- git_apply asserts the same for its own working directory. That covers gate (c), (b2) and status's temporary copies by construction.
- Record this in §0 or decision 2 as the absorbed C14 item.

3. §2.4 and §8: state that the evidence holds only outside a repository and with no config. List what git apply otherwise consults: system, global and XDG config; the XDG and system attributes files; the .git directory of every parent; inside a repository, also that repository's config and in-tree .gitattributes.

4. Decision 14: one parametrized pytest hostile-environment case. Each variant must reproduce the clean case's bytes and verdicts:
- a tree in a gitignored subdirectory of a repository;
- a HOME with autocrlf, an attributes file and apply.ignoreWhitespace=change;
- GIT_DIR, GIT_WORK_TREE and GIT_CONFIG_COUNT exported by the caller;
- plus a case where a `.git` tree is refused.

5. §6: the Windows acceptance leg compares file bytes after apply and after unapply, not only status.

Optional: (b2) also asserts that copy A differs from the original after apply.

**Judge: partially_confirmed → author_decides_then_rereview.** Core confirmed, severity stays blocking. My run (judge/c1/, whitelist.out) reproduced the silent no-op in an enclosing repository: `-R --check` on the unpatched file gave rc=0. It also showed that git reads $GIT_DIR/config when GIT_DIR names a directory, so the GIT_DIR=/nonexistent fix is rejected (it is also creatable as C:\nonexistent on Windows). Refuted: the 'status printed applied' evidence (critic-conda scenario D) came from a prototype that replays in the tree; the plan replays on copies (plan:186-189).

Changes:
(1) Decision 4 (plan:171-174): git_apply builds the child process itself, so every caller gets this by construction.
- Environment from a whitelist: PATH, plus SystemRoot, TEMP and TMP on Windows. Added to it: GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM=1, LC_ALL=C, and GIT_CEILING_DIRECTORIES=<resolved parent of git's working directory>.
- Arguments: `git -c core.autocrlf=false -c core.attributesFile=<devnull> apply ...`. On Windows also try `-c core.longpaths=true` (unmeasured; verify on the Windows leg).
- HOME and core.eol are not needed (measured: the whitelist environment without HOME applied and round-tripped exactly).
(2) Under C2's install by rename, git only ever runs in a staging directory the tool creates, so its working directory never contains .git.
(3) Restore rev-1 C14 (REVIEW1:1356): refuse with exit 3 any tree where <tree>/.git exists, as a directory or a file. This applies to every command: status, apply, unapply, the directory interface and conda-hook.
(4) §2.4 and §8 (plan:119, :405): say the evidence holds only outside a repository with no config, and list what git otherwise reads.
(5) Decision 14: one parametrized hostile-environment pytest case, which must reproduce the clean case's bytes and verdicts:
- a tree in a gitignored subdirectory of a repository;
- a HOME with autocrlf, an XDG attributes file and apply.ignoreWhitespace=change;
- GIT_DIR, GIT_WORK_TREE and GIT_CONFIG_COUNT exported by the caller;
- a tree containing .git, which must be refused.
The Windows leg compares file bytes after apply and after unapply.

### C2 [blocking] Decision 4's atomicity claim is false: separate patch-file arguments half-apply a feature, and even a single stream unlinks every target before writing any, so a failure or a kill leaves Isabelle source files missing

Section: Decision 4 (plan:175-177); §2.3 (plan:110-111); §2.4 (plan:121); §8 (plan:406); decision 6 (plan:209-215); decision 8 (plan:234-235); §7 rows 发现 5 and 发现 7 (plan:379, :381); decision 14 (plan:300-306)  ·  merged from: engine-E3, conda-conda-7, consistency-F9, landing-L1, user-F3

**Statement.** What the plan says. The set of patch files given to one git apply call is one atomic operation: if any file does not fit, nothing changes, so one call never half-applies a feature (plan:175-176). git apply "writes a new file and then replaces" (plan:110). It is "atomic" (§7, plan:379) and "writes no file on failure" (plan:381). Rev 1's judge directive on C7 asked for patch texts held in memory, a dry-run before any write, rollback on BaseException and SIGTERM, and tests in which an interrupt at file k still converges (REVIEW1:732-739). Rev 2 dropped that directive on the strength of this claim. Measured with git 2.43.0, the claim is false in two independent ways (scratch root /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

(a) Separate arguments. Decision 4 passes one patch file per target as a separate argument, which is make-patches' layout (make-patches:162-171). git checks and writes each argument in turn. With two arguments where the second conflicts, rc=1 and the first file is already patched (merge/g/evidence.out case 2). On light's 32 real files with drule.ML hand-edited, 24 of 32 were written (critic-engine/e4/multi.sh). The same patches fed as one stream on stdin change nothing (merge/g/evidence.out case 3). The author's evidence measured the stream shape (scratchpad pylib/light.diff is one file with 32 blocks), not the shape the plan specifies.

(b) Even one stream is atomic only in its checking stage. Its write stage opens every target for reading, unlinks every target, and then creates each new file at its final path with O_CREAT|O_EXCL. There is no temporary file and no rename (strace, merge/g/evidence.out case 4; critic-engine/e4/strace5.out). A write error between the unlinks and the creates, or a kill in that window, leaves targets missing or truncated:
- a full disk right after conda has linked a multi-GB package, or a quota: critic-engine/e4/write_err.sh gives rc=128 with 28 of light's 29 modified sources missing;
- a kill: critic-engine/e4/write_fail.sh leaves the same 28 missing and one truncated; critic-user/e3.sh shows 2982 of 3000 files missing after SIGKILL at 0.21 s;
- a truncated file can still pass `-R --check` and read applied (critic-conda/git3.out).
conda forwards SIGINT and SIGTERM to hook processes (conda/gateways/subprocess.py:118, called from core/link.py:1644), so a Ctrl-C during `conda install` lands in exactly this window.

Consequences. Under decision 5 a missing target of a modification patch has no level, so it reads CONFLICT. apply then stops, unapply refuses (plan:209-213), and there is no --force (plan:215). No command of the tool repairs the tree; only relinking isabelle does, plus a manual apply on 2025.2-0. Decision 8's "a failed post-link leaves the package installed and the feature not applied; status sees it and apply repairs it" (plan:234-235) is therefore false. Decision 14 has no interruption or write-failure test.

A second gap. status replays each file on copies in a temporary directory (plan:188-189), while apply runs git in the tree. Whatever differs between the two places makes the real call fail, or do nothing, after status predicted success: a symlinked target becomes a regular file in the copy, and C1's enclosing-repository trap can hold in one place and not the other.

Required. Every write must leave each file either old or new, by construction. Correct plan:110, :121, :175-176, :379, :381 and §8:406. Add tests that kill the tool at each file during apply and during unapply, and that inject a write failure; afterwards apply and unapply must both converge.

**Editor.** Confirmed by my own strace and argument tests (merge/g/evidence.out cases 2-4) and by four critics independently. The proposed fixes are partly wrong:
- landing-L1's fix, one stdin stream per call, is necessary but not sufficient. It makes the checking stage all-or-nothing, but the write stage still unlinks every target first (case 4).
- consistency-F9's first alternative, keep the old contents and restore them on failure, cannot survive SIGKILL or a power loss, which is exactly when files go missing. It would also make the tool a second writer with its own rollback logic.
- conda-conda-7's "a truncated file reads as applied" holds only when every hunk lies before the truncation point. It is real but secondary; the missing files are the main harm.

**Relaxation proposed by the editor.** Install by rename. For each file, produce its target content on its scratch copy with git_apply, by the same sequential replay status already performs. Then move the result into the tree with os.replace, or delete it with os.unlink when the patch deletes the file, one file at a time. The scratch directory sits on the tree's filesystem (for example under $PREFIX) and is cleared at the start of every run. Before the rename, set the scratch file's mode: the original mode for a modified file, 0644 or 0755 from the patch for a created one.
What this gives by construction:
- A file is never missing or truncated, because each rename is atomic.
- An interrupted run leaves a half-applied state, which the next apply or unapply completes.
- The new inode keeps the pkgs cache and sibling environments untouched, as today.
- status, --dry-run, apply, unapply and apply-to become one code path (replay, then install or not), so what status predicted is exactly what gets installed.
- The separate chmod step disappears (C19).
git apply remains the only producer of patched content, so ruling 18 holds; moving a finished file into place is not patch logic.

**Defender: partially_confirmed** (needs owner: True).

I tried to refute C2 and could not refute its core. Every main claim reproduced in my own scratch runs with git 2.43.0. A few side claims are narrower than stated, or wrong.

CONFIRMED
1. Separate patch-file arguments half-apply a feature (e1/run.out). Decision 4 passes `<patch 文件…>`, one argument per patch file (plan:171-172). git checks and writes each argument before it reads the next one:
- b conflicts → a written, rc=1;
- c conflicts → a and b written;
- the same patches as one stream → nothing changes.
So plan:175-176 is false for the form the plan specifies.

2. One stream is all-or-nothing only while git is checking. When it writes, it unlinks every target, then creates each new file with O_CREAT|O_EXCL. There is no rename. On light's 32 files (e2/strace.out): 29 unlinks at trace lines 80-108, all creates at lines 109-202, 0 renames. So plan:110 describes the mechanism wrongly: git deletes the old file and then writes a new one; it does not write a new file and then swap it in. The consequence plan:110 states (new inode, pkgs cache untouched) is still correct.

3. A failure after the check passes leaves Isabelle source files missing (e3/run.out):
- an injected write error (file-size limit, standing in for a full disk, a quota or an I/O error): 28 of 29 modified files missing, 1 truncated;
- one unwritable directory: `--check` passes, then 8 files are missing.
A kill does the same. SIGKILL 6-8 ms into a run of about 8 ms left files missing in up to 11 of 15 trials (e3/kill2.out).

4. The tool cannot repair this. It has no copy of the base content. Under decision 5 a missing modified file has no consistent level, so it reads CONFLICT (plan:186-193). Three plan sentences are therefore false for failures during writing:
- decision 8's "status sees it and apply repairs it" (plan:234-235);
- appendix A's "不会损坏环境" (does not damage the environment, plan:446);
- the §7 rows for 发现 5 and 发现 7 (plan:379, :381).
Decision 14 has no interrupt test and no write-failure test (plan:300-306).

5. The rev-1 C7 directive was dropped. It asked for rollback and for interrupt tests (REVIEW1:732-739). Rev 2 kept half-applied as a named state but replaced the rest with the false atomicity claim. That is a rev-1 defect that survived.

REFUTED OR NARROWED
- plan:121 and plan:406 are accurate as written. Both describe one multi-file diff in which a hunk does not match, and that case changes nothing. They need a note on their scope, not a correction.
- The symlink example in the second gap does not apply: plan:178 already refuses symlink targets (exit 3). The enclosing-repository trap is C1's issue.
- One stdin stream is not "necessary"; on its own it makes writing more dangerous. With one argument per file, at most one file is damaged (e3/perarg.out):
  - write error: 0 missing, 1 truncated (stream: 28 missing);
  - unwritable directory: 0 missing, 20 applied (stream: 8 missing).
  Neither form is safe by construction.
- conda forwards signals only to the hook's shell (conda/__init__.py:153-159). A forwarded SIGTERM kills that shell but not its child (e5). The kills that really reach git are:
  - a Ctrl-C or hang-up from the terminal, which reaches the whole foreground process group because the hook is not started in a new session (gateways/subprocess.py:108-117);
  - SIGKILL;
  - power loss.
- The window is short: about 1-2 ms per feature.
- Decision 8's sentence stays true when status detects the conflict before anything is written.

THE EDITOR'S RELAXATION
It holds up on the merits. I prototyped it as e4/proto.py and drove it with e4/drive.sh. For each file the prototype copies the file to a scratch directory, runs git apply on the copy, sets the mode, and then moves it into the tree with os.replace (or deletes it with os.unlink).
- Killed after each file k = 1..32 during apply, and after file 13 during unapply: 0 targets were anything but byte-equal to old or new. apply then unapply converged in 32 of 32 runs (e4/drive.out).
- An injected write error left the tree untouched (old=32), and apply then converged.
- Modified files keep 0444. The hard-linked cache copy kept its content and mode 444.
- git's own work-tree writes always delete and recreate a file, never rename, so no git option gives this guarantee. A rename step outside git is the minimum.
- git apply still produces every patched byte, so ruling 18 holds.

Caveats:
- the scratch directory must be on the tree's filesystem;
- Windows (not measured): os.replace onto a read-only or open file may need the read-only attribute cleared first, or fail cleanly;
- fsync before the rename if power loss matters;
- remove empty directories after a deletion, as git does;
- not fixed by this: conda's rollback after an interrupted post-link (plan:102-103) removes the feature directory while its file changes stay. Reinstalling the feature completes it.

Experiment: All scripts and outputs are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C2/. They use git 2.43.0 with GIT_DIR=/nonexistent and an empty git config, on a copy of critic-engine/real (light's 32 real per-file patches and their base).
- e1/run.sh → e1/run.out: three toy patches, each one made to conflict in turn, given as separate arguments and as one stream. Separate arguments write every argument before the conflicting one; one stream writes nothing.
- e2/run.sh → e2/run.out and e2/strace.out: strace of one stream over light. 29 unlinks come before all creates (O_CREAT|O_EXCL) and there are no renames. Total run time is 5-8 ms.
- e3/run.sh → e3/run.out (one stream):
  - file-size limit (stands for a write error): 28 files missing, 1 neither old nor new;
  - unwritable src/Pure/Syntax: `--check` rc=0, then 8 files missing.
- e3/perarg.sh → e3/perarg.out (one argument per file):
  - write error: 0 missing, 1 truncated;
  - unwritable directory: 0 missing, 20 applied, 12 not applied.
- e3/kill2.sh → e3/kill2.out: SIGKILL by `timeout` at 3-9 ms, 15 trials per delay. Files were missing only for kills at 6-8 ms (up to 11 of 15 trials).
- e4/proto.py and e4/drive.sh → e4/drive.out: prototype of the install-by-rename relaxation.
  - killed after each file k = 1..32 during apply, and after file 13 during unapply: 0 files neither old nor new; 32 of 32 runs converged;
  - a write error left the tree unchanged, and apply then converged;
  - modified files keep mode 444; the hard-linked cache inode is unchanged.
- e5: SIGTERM sent to a `bash -x` hook shell kills the shell but not its child.
- Source reads: conda/__init__.py:153-159 (signal forwarding), core/link.py:916 (handler registered), core/link.py:1628 (hook command), gateways/subprocess.py:108-118 (Popen without a new session).

Recommended fix: Smallest fix:
1. Decision 4 (plan:171-178): adopt install by rename. git_apply never runs in the user's tree. For each file to change:
   - copy it into a scratch directory next to the tree (`mkdtemp(dir=<parent of DIR>)`); remove leftover scratch directories at the start of every run, under the lock;
   - run git_apply on that file's patch there, the same per-file replay status already does;
   - set the mode: the original mode for a modified file, or the mode from `new file mode` for a created one;
   - then os.replace it into the tree (creating parent directories as needed), or os.unlink it when the result is absent, removing directories left empty.
   Delete the separate chmod step and the phrases "工具不复制、不写任何文件内容；唯一的写者是 git apply" (the tool copies nothing and writes no file content; git apply is the only writer). State the guarantee as: every file is always either old or new; an interrupted run leaves a half-applied feature, which apply or unapply completes. status, --dry-run, apply, unapply, apply-to and unapply-from share this one path.
2. Rewrite these lines:
   - plan:110: git unlinks the target and creates a new file; the rename keeps the new-inode property;
   - plan:175-176: per-file atomic; no promise of all-or-nothing per feature;
   - §7 plan:379 and :381.
   Add scope wording ("one multi-file diff, a hunk that does not match") to plan:121 and :406. Add the new measurements to §8.
3. Decision 14 (plan:300-306): add tests:
   - kill after file k, during apply and during unapply; afterwards every target is byte-equal to old or new, and both commands converge;
   - a write error in the scratch copy (file-size limit on the git child) leaves the tree file unchanged;
   - the hard-linked cache copy keeps its content and mode;
   - on the Windows leg, replacing a read-only file and a file that another process has open.
4. Optional: fsync the scratch file before the rename. Note in decision 8 that a conda rollback after an interrupted post-link leaves the feature's files changed (plan:102-103), and that reinstalling the feature completes it.

**Judge: confirmed → author_decides_then_rereview.** Confirmed by two independent stracing defenders and kill tests. plan:121 and :406 are true only for 'one multi-file diff with a non-matching hunk'; add that scope instead of deleting them.

Adopt install by rename as the only path that writes the tree.
- For each file to change: copy it into a staging directory, replay that file's own patches there with git_apply (one patch file per call, C1's environment), then set the mode: the original mode for a modified file, 0644/0755 from the header for a created one. Then os.replace it into the tree, or os.unlink it and remove directories left empty. One file at a time.
- Staging must be on the tree's filesystem but outside the tree, so a leftover can never keep isa/ alive. Example: a fixed-name sibling of DIR. Clear it under the lock at the start of every writing run.
- status writes nothing under the prefix; its replay may use the system temp directory.
- State the guarantee: every file is always either old or new, and an interrupted run leaves a state the next apply or unapply completes (C5's per-file moves).
- status, --dry-run, apply, unapply, apply-to and unapply-from become one path: replay, then install or not.

Rewrite:
- plan:110 (git unlinks and recreates; the rename gives the new inode);
- plan:175-178 (delete 'atomic per call', '不复制', '唯一的写者是 git apply');
- §7 rows for findings 5, 7 and 13 (:379, :381, :387);
- decision 8 :234-235 and Appendix A :446, for interrupted writes;
- decision 8 also says that conda's rollback after an interrupted post-link removes the feature directory while the file changes stay, and that reinstalling the feature completes it.

Add tests:
- kill after file k during apply and during unapply; afterwards every target is old or new, and both commands converge;
- a write failure in staging leaves the tree untouched;
- the inode shared with a sibling environment or the cache keeps its content and mode;
- Windows leg: replacing a read-only target, and a target another process has open.

The defender's prototype (defender-C2/e4/drive.out) converged in 32 of 32 kill points. Put Q5 to the owner as a confirmation.

### C3 [major] On isabelle-2025.2-0 the chain rule rejects the isabelle-expose-foreign directory that is always installed there, so every command and every hook exits 3; and the LEGACY_BUILDS entry is never checked against the tree

Section: Decision 3 points 1-2 (plan:159-166); decision 10 (plan:263-266); decision 5 (plan:193); decision 2 (plan:150); §6 (e) (plan:367-368)  ·  merged from: conda-conda-2, engine-E4, consistency-F2, user-F2, consistency-F15, user-F14

**Statement.** The defect. On a tree whose etc/ISABELLE_ID is 5533cd83156e, the only published build (pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_ID), decision 3 sets the bottom of the chain to Isabelle2025-2/expose_foreign/1 (plan:160-161). Every feature package above expose_foreign pins isabelle-expose-foreign exactly: base_pin is a package dependency (plan:248), and make-patches writes one for every base that is not pristine (make-patches:192-201). So on that build features.d always contains expose_foreign/. That directory's base_tag is the pristine tag, Isabelle2025-2/pristine/89701cf1768e (make-patches:197-201 with base_name pristine). Rule 2 says a directory whose base_tag equals no tag on the chain is exit 3 (plan:162-164). As written, therefore:
- status, apply, every post-link, and ruling 13's one-time manual apply exit 3 on 2025.2-0;
- because the hooks exit 0, nothing is applied and the user only gets a "feature chain broken" message;
- §6 (e) fails.
Prototypes that implement rule 2 literally confirm this (critic-engine/e7/chain.py and critic-consistency/chain_rule.py under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/). Decision 10 claims that "decision 3's linking rule does this naturally" (plan:264-265); it does not. The sentence that would make it true was in rev 1's C6 ruling and was dropped: "A directory whose release_tag is a manifest entry is that built-in entry" (REVIEW1:684).

Second part: rev 1's C13 directive survived unaddressed. The LEGACY_BUILDS entry is trusted without checking. 0.3.0's default `unpatch` reverses the built-in expose_foreign on conda trees (my_better_isabelle_prover/cli.py:157 defaults to 'all'; migration plan :610-611 says the tool reads that expose_foreign as APPLIED). After that, rev 2 still prints `pre-applied expose_foreign` (plan:193), and code that uses Foreign fails with no diagnosis. Rev 1's judge asked for exactly this check: if a built-in feature's directory is present and its files do not read applied, exit 3 with a reinstall hint (REVIEW1:1235). Also, on 2025.2-0 with no feature package installed, status prints only `no feature packages installed` (plan:150) and hides that the tree carries expose_foreign.

Required.
- Add the record-entry rule to decision 3 point 2.
- A directory of the same feature with another release_tag (for example expose_foreign/2 on 2025.2-0) is exit 3, naming both tags and saying "update isabelle".
- When the record's directory is present, reverse-check its files. A failure is CONFLICT, with "run conda install --force-reinstall isabelle".
- status prints the LEGACY_BUILDS line even when features.d is absent.
- Drop "naturally" from decision 10.
- pytest cases for a legacy ID with the expose_foreign/1 directory (accepted), with expose_foreign/2 (exit 3), and with expose_foreign reversed (CONFLICT).

**Editor.** Confirmed by reading make-patches:192-201 and plan:160-164 against each other; the only tag in contrib/Isabelle2025-2 today is Isabelle2025-2/pristine/89701cf1768e. Two parts of the critics' findings are dropped or moved:
- engine-E4's demand to "refuse a name that is not a release name" is dropped. A tree whose etc/ISABELLE_IDENTIFIER is not a release name already fails rule 2's equality check on `<R>` (plan:164), so it fails safely.
- E4's point that git archives lack etc/ISABELLE_IDENTIFIER is real, but it is a (b2) problem and is carried in C10.

**Relaxation proposed by the editor.** Let every walk start from the pristine tag. Give each LEGACY_BUILDS entry the shape `ID -> (pristine changeset, pre-applied release tags)`, for example 5533cd83156e -> (89701cf1768e, {Isabelle2025-2/expose_foreign/1}). The pre-applied tags count as chain levels whether or not their directory is installed. Then the expose_foreign/1 directory links by its own base_tag, exactly as on any other tree, and decision 10's "naturally" becomes true. The record only marks that level pre-applied: it is shown, verified by a reverse check, and never applied or reversed. A pre-applied level whose installed directory has a different release_tag is exit 3. The result is one walk rule for every tree, with no special bottom.

**Defender: confirmed** (needs owner: False).

I tried to refute the challenge and could not. Both parts stand. The overstatements are cosmetic.

PART 1: the chain rule rejects the expose_foreign directory on 2025.2-0. Confirmed.
- The facts behind it:
  - The only published build has etc/ISABELLE_ID 5533cd83156e and etc/ISABELLE_IDENTIFIER Isabelle2025-2 (pkgs/isabelle-2025.2-0/isa/etc).
  - Rule 1 makes the bottom of the chain Isabelle2025-2/expose_foreign/1 (plan:160-161).
  - make-patches writes base_tag as the single release tag at the merge-base (make-patches:97-102, 198). The only pristine tag in contrib/Isabelle2025-2 is Isabelle2025-2/pristine/89701cf1768e (git tag -l). So expose_foreign/1's provenance will say base_tag Isabelle2025-2/pristine/89701cf1768e.
  - Every package above expose_foreign pins its base package exactly (plan:248; make-patches:201). So once any feature package is installed on 2025.2-0, features.d/expose_foreign/ is present.
- Rule 2 makes that directory exit 3 (plan:162-164). Its own list of causes even names this exact case: "树的 ISABELLE_ID 不是原版 changeset" ("the tree's ISABELLE_ID is not the release changeset").
- Decision 10 says "决定 3 的链接规则自然做到" ("decision 3's linking rule does this naturally", plan:264-265). That is false.
- The plan's intent is clear elsewhere, but no rule implements it:
  - decision 5 shows a pre-applied line (plan:193, :198);
  - decision 6 skips pre-applied features (plan:209, :212);
  - §5 step 4 (plan:353) and §6 (e) (plan:367-368) expect expose_foreign to read pre-applied.
- Rev 1's C6 judge ruling had the missing sentence: "A directory whose release_tag is a manifest entry is that built-in entry" (REVIEW1:684, :673). Rev 2 dropped it.
- My prototype confirms the consequence. It applies rule 2 literally to the real git diff-tree blocks (ef.diff, fai.diff) and copies of the 2025.2-0 files. It prints "exit 3: feature chain broken at Isabelle2025-2/expose_foreign/1: its base Isabelle2025-2/pristine/89701cf1768e is not installed".
  - So status, apply, unapply, the tool call inside every post-link and pre-unlink, and the one-time manual apply of ruling 13 all fail on 2025.2-0.
  - §6 (e) fails.

PART 2: rev 1's C13 directive survived unaddressed. Confirmed.
- What the rev-1 judge asked for: if a built-in feature's directory is present and its files do not read applied, refuse with a reinstall hint (REVIEW1:1235).
- What rev 2 does instead:
  - it shows the record entry as pre-applied by fiat ("底以下的记录项显示 pre-applied", plan:193; plan:263-264);
  - its level model covers only features above the bottom ("链上（底以上的）", plan:186);
  - the only related line in §7 drops the optional paths_data evidence ("未采用", "not adopted", plan:394) and adds no check.
- Rev 2's only defence is a README instruction never to run a bare unpatch (plan:293-295). That asks people to remember the rule.
- The danger is real:
  - 0.3.0's unpatch defaults to category all (cli.py:157), and expose_foreign is in category user (categories.toml), so a bare unpatch reverses it.
  - The tool reads the built-in expose_foreign as APPLIED (migration plan:610-611).
  - expose_foreign touches only src/Pure/ML/ml_name_space.ML, and no other branch touches that file (git diff-tree --name-only).
  - Scenario S4 in my prototype: after reversing expose_foreign, future_assign_interrupt still reads not-applied and applies cleanly, while expose_foreign is still shown as pre-applied. Code that uses Foreign then breaks with no diagnosis.
- No owner ruling makes this moot:
  - ruling 16 keeps 0.3.0 on PyPI;
  - existing 2025.2-0 environments stay on 2025.2-0, which satisfies isabelle >=2025.2,<2025.3 (plan:247);
  - §6 (e) tests exactly that tree.
- The smaller point also holds: with features.d absent, plan:150 prints only `no feature packages installed`, while the record says the tree carries expose_foreign/1.

WHAT IS OVERSTATED.
- The directory is not "always installed". It is present whenever any feature package is installed, because of the pins; with none installed the literal rule gives an empty chain and exit 0 (scenario S2).
- The hooks themselves exit 0 (ruling 12). It is the tool run inside them that hits the exit-3 condition.
- The challenge requires that expose_foreign/2 on 2025.2-0 exit 3 with "update isabelle". Decision 10 already demands that (plan:264-265). Only the mechanism is missing.
- Which pytest cases to add is the author's decision (ruling 17). Decision 14 already lists LEGACY_BUILDS (plan:302).

THE EDITOR'S RELAXATION, ON ITS MERITS. Adopt it, with three precisions.
- What it changes:
  - every walk starts at <R>/pristine/<c>;
  - the single record entry becomes 5533cd83156e -> (89701cf1768e, Isabelle2025-2/expose_foreign/1);
  - the record's tag is a chain level whether or not its directory is installed.
- Why it is better than adding back the rev-1 sentence:
  - there is one walk rule and no special bottom;
  - the expose_foreign/1 directory links by its own base_tag, which also cross-checks the record's changeset;
  - a different directory at that level is caught as a fork, for example expose_foreign/2 (S3) or another feature built on pristine (S6);
  - the record line prints even with no directory (S2);
  - "naturally" in decision 10 becomes true;
  - the reverse check falls out of decision 5's level model, not a separate rule (S4 gives CONFLICT).
- Precisions:
  1. Store the pre-applied tag as an ordered value, not a set. Ruling 11 keeps it to one entry with one tag.
  2. The check must be the pre-applied level taking part in the level computation. A naive `git apply -R --check` of the record directory would fail wrongly if a later feature ever patches the same file.
  3. Report a failed check as CONFLICT (status exit 1). Exit 3 is for invalid directory sets (plan:334-335), and CONFLICT keeps every status line printed. The hint must name both steps, because 2025.2-0's post-link does not call the tool (plan:237-238): `conda install --force-reinstall isabelle`, then `isabelle-patch-control apply`.

No owner ruling is touched: the record stays one fixed entry (ruling 11), and the wording is delegated (ruling 17).

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C3/. The scripts are proto.py and proto.out.

Inputs:
- Real diffs from read-only `git diff-tree -r -p --no-renames` in contrib/Isabelle2025-2:
  - pristine/89701cf1768e to expose_foreign gives ef.diff: one file, ml_name_space.ML, where hidden_structures loses Foreign;
  - expose_foreign to future_assign_interrupt gives fai.diff: one file, future.ML.
- The legacy build's ml_name_space.ML and future.ML are byte-identical (cmp) to the expose_foreign branch tip's.
- Toy trees are copies of pkgs/isabelle-2025.2-0/isa files with etc/ISABELLE_ID and ISABELLE_IDENTIFIER, plus features.d directories with make-patches-style provenance. git apply is git 2.43.0, run in a non-repo directory.

Results:
- S1 (2025.2-0 with expose_foreign/1 and future_assign_interrupt/1):
  - the literal rev-2 rule gives "exit 3: feature chain broken at Isabelle2025-2/expose_foreign/1: its base Isabelle2025-2/pristine/89701cf1768e is not installed";
  - with the REVIEW1:684 sentence: expose_foreign is pre-applied and the chain is [future_assign_interrupt/1];
  - the editor's relaxation gives the levels [expose_foreign/1 (pre-applied), future_assign_interrupt/1], and status reads pre-applied, then not-applied.
- S2 (features.d empty):
  - literal rule: empty chain, so the record line is not shown;
  - relaxation: shows "pre-applied expose_foreign/1 (unverified)".
- S3 (expose_foreign/2 and future_assign_interrupt/2 on 2025.2-0): exit 3 in every variant; only the patched variants can say "update isabelle".
- S4 (expose_foreign reversed with git apply -R, as 0.3.0's bare unpatch would):
  - rev 2 with the sentence but no check still shows pre-applied, and future_assign_interrupt reads not-applied, so apply would proceed;
  - relaxation with the level check gives "CONFLICT expose_foreign/1 (pre-applied in this build but reads not-applied; run conda install --force-reinstall isabelle)".
- S5 (pristine ID): all variants link pristine, expose_foreign, future_assign_interrupt.
- S6 (a feature X based directly on pristine, on 2025.2-0): the relaxation reports a fork against the record level, exit 3.

Source checks:
- make-patches:97-102, 192-201 (base_tag and base_pin);
- cli.py:157 (unpatch defaults to all);
- categories.toml (expose_foreign is category user);
- no other branch touches ml_name_space.ML;
- REVIEW1:673, :684, :1235;
- rev1 plan:160-165.

Recommended fix: Adopt the editor's relaxation, written into the plan by hand.

(1) Decision 3, point 1 (plan:160-161):
- The bottom is always <R>/pristine/<c>. Here <c> is etc/ISABELLE_ID, unless that ID is in decision 10's record; then <c> is the record's release changeset.
- The record's release tag is the first chain level, marked pre-applied, whether or not its directory is installed.

(2) Decision 3, point 2 (plan:162-164), for a pre-applied level:
- The only directory allowed to have base_tag equal to the current tag is the one whose release_tag is the record's tag. That directory is the level.
- Any other directory there is exit 3, naming both tags. If it is the same feature, add "update isabelle". This covers expose_foreign/2 on 2025.2-0.

(3) Decision 5 (plan:186-193):
- A pre-applied level whose directory is present takes part in the per-file level computation like any other level, and its required state is applied.
- Anything else is CONFLICT with "run `conda install --force-reinstall isabelle`, then `isabelle-patch-control apply`".
- With the directory absent, the level is shown as pre-applied and is not verified.
- apply and unapply never touch a pre-applied level (as plan:209 and :212 already say).

(4) Decision 10 (plan:263-266):
- Make the record LEGACY_BUILDS = {"5533cd83156e": ("89701cf1768e", "Isabelle2025-2/expose_foreign/1")}.
- Delete "（决定 3 的链接规则自然做到）" ("decision 3's linking rule does this naturally") and point to the new decision 3 rule.

(5) Decision 2 (plan:150): on a tree in the record, status prints the pre-applied record line before "no feature packages installed".

(6) Decision 14 (plan:302), author's choice under ruling 17. Suggested pytest cases on the legacy ID:
- the expose_foreign/1 directory: pre-applied, and the chain continues;
- expose_foreign/2: exit 3 with "update isabelle";
- expose_foreign reversed: CONFLICT, and apply refuses;
- features.d absent: the record line is printed.

Smaller alternative: restore REVIEW1:684's sentence in point 2 and add the level check in (3). This works too, but it keeps a special bottom, and it needs the same verification clause.

**Judge: confirmed → author_decides_then_rereview.** Confirmed: plan:160-164 rejects expose_foreign/1, whose base_tag is pristine/89701cf1768e (make-patches:192-201), and decision 10's 'naturally' (plan:264-265) is false. Correction: the directory is present whenever any feature package is installed, not 'always'.

Adopt the editor's relaxation with the defender's precisions:
- The record becomes LEGACY_BUILDS = {"5533cd83156e": ("89701cf1768e", "Isabelle2025-2/expose_foreign/1")}, an ordered value.
- Every walk starts at <R>/pristine/<c>.
- The record's tag is the first level, marked pre-applied, whether or not its directory is installed. The directory, if present, links by its own base_tag, and any other directory claiming that level is exit 3, naming both tags; when it is the same feature (e.g. expose_foreign/2), add 'update isabelle'.
- When the directory is present, the pre-applied level takes part in decision 5's per-file level computation, and its files must read applied. Otherwise the result is CONFLICT, with the hint 'conda install --force-reinstall isabelle, then isabelle-patch-control apply'. Do not use a naive standalone -R --check.
- When the directory is absent, status still prints the pre-applied line, including when features.d is missing (plan:150).
- apply and unapply never touch a pre-applied level.
- Delete '自然做到' (naturally).

Test cases (author's choice under ruling 17): expose_foreign/1 directory accepted; expose_foreign/2 gives exit 3; expose_foreign reversed gives CONFLICT; features.d absent still prints the record line.

Optional: C8's paths_data relaxation would also verify the pre-applied files when no directory is present.

### C4 [major] Exit 0 is promised by the tool's code, not by the hook text; the isabelle line handed to the CI plan exits 1 whenever the tool is absent, and the hook interface is inconsistent and not frozen for 1.x

Section: Decision 8 (plan:226-238); decision 11 item 2 (plan:272); §4 (plan:330, :335); decision 1 (plan:137-142); decision 2 (plan:148)  ·  merged from: conda-conda-3, consistency-F4, landing-L8, user-F5

**Statement.** The defect. Ruling 12 says that hooks always exit 0 (plan:50). Decision 8 makes each feature hook a single line that calls the tool (plan:226-228), and puts the exit policy inside the tool ("conda-hook is always 0", plan:335). A one-line hook returns whatever the tool process returns. conda runs a .sh hook as `bash -x path`, or sources it inside an activation wrapper, and raises LinkError on any non-zero status (conda/core/link.py:1606-1647). So anything that fails before the tool's own handler runs fails the post-link:
- the entry point is missing after `conda remove --force isabelle-patch-control`;
- python is broken;
- a later 1.x release raises ImportError at start-up;
- the user presses Ctrl-C (KeyboardInterrupt).
conda then rolls back without running scripts and deletes conda-meta/history (plan:101-104). RELEASE_CHECKLIST.md:259 says "Every hook ends `exit 0`", and every existing hook in the channel ends in an unconditional exit (isabelle-packaging-ci/conda/recipe.yaml:208; Isabelle_RPC/conda/recipe.yaml:154-157).

The isabelle line. The line given to the CI plan for the isabelle package, `[ -x "$PREFIX/bin/isabelle-patch-control" ] && …` (plan:236), evaluates to 1 when the tool is not installed, which is the normal case for a plain isabelle user. Decision 11.2 says only "add the line" (plan:272), not "before the final exit 0". Measured: a package whose post-link ends with that line, installed without the tool, gives `LinkError: post-link script failed … return code: 1` and installs nothing (critic-conda/run.out scenario F, critic-landing/toy2/T3-create.log and critic-consistency/hook1.sh, all under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

The interface around the line is inconsistent:
- `conda-hook post-link <feature>` ignores `<feature>`, because post-link applies the whole chain (plan:229).
- The isabelle package passes `isabelle`, which is not a feature (plan:236). So "the hook text is the same for all packages" (plan:228) is not true.
- Decision 2 says the hooks pass $PREFIX/isa (plan:148), but the line passes nothing.
- The isabelle package's copy of the line is hand-written in another repository.
- Rev 1's judge required the conda-hook contract to be part of the 1.x compatibility promise (REVIEW1:494). Rev 2 never states one, although hook text in published packages can never change.

Required.
- The renderer emits `if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then "$PREFIX/bin/isabelle-patch-control" conda-hook post-link || echo "isabelle-patch-control could not run; run: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"; fi`, followed by `exit 0`. The .bat equivalent uses `if exist … call …` followed by `exit /b 0`.
- Decision 11.2 gives the exact isabelle lines and says they go before the recipe's existing final `exit 0` / `exit /b 0`.
- Decision 1 freezes the `conda-hook` command line and its use of PREFIX for all of 1.x.
- A hook-layer test installs with a tool entry point that raises at import, and asserts that the install succeeds and that conda-meta/history survives.

**Editor.** Confirmed against conda/core/link.py:1606-1647 and three independent toy runs. consistency-F4's remark that "if the CI plan places the line after the existing exit 0, it never runs" is true but trivial; the point is that the plan must say where the line goes.

**Relaxation proposed by the editor.** Drop the ignored `<feature>` argument from post-link. One byte-identical post-link text then serves every package, the isabelle package included. It can be generated from one source in the tool repo, used by both the CI recipe and the hook-layer test, and a single test can check every rendered package. Only the feature packages' pre-unlink needs to name its feature.

**Defender: partially_confirmed** (needs owner: False).

I tried to refute C4 and could not refute its core. One headline claim is overstated, and one trigger is weak.

CONFIRMED 1: exit 0 rests on the tool process, not on the hook text.
- Decision 8 makes each feature hook a single line that calls the tool (plan:226-228). The exit policy lives only in the tool ("conda-hook 总是 0", plan:335).
- conda runs post-link with activate=True (conda/core/link.py:1109-1114). On POSIX it sources the script inside a wrapper (link.py:1619-1625; utils.py:300-310). On Windows it runs `@CALL path` followed by `IF %ERRORLEVEL% NEQ 0 EXIT /b %ERRORLEVEL%` (link.py:1606-1613; utils.py:268-269). Any non-zero status raises LinkError (link.py:1647-1675).
- So a tool that dies before its own handler fails the install. Examples: an import-time bug in a later 1.x release, which the hook text cannot defend against because published hooks never change while the tool moves within `<2` (plan:247); a missing entry point; a python that cannot start.
- Measured (S1): a one-line hook calling a tool that exits 1 before its handler, installed into an existing env, gives LinkError and rollback. conda-meta/history is deleted, and `conda list -p` then exits 2.
- The plan cites the rule it breaks (plan:112-113; RELEASE_CHECKLIST.md:259 "Every hook ends `exit 0`"). The isabelle recipe records a real incident of exactly this class: a trailing findstr status "broke every Windows `conda install`" (isabelle-packaging-ci/conda/recipe.yaml:118-122).
- Ctrl-C is a weak trigger, because conda itself receives the signal. I discount it.

OVERSTATED: "the isabelle line exits 1 whenever the tool is absent".
- The line `[ -x … ] && …` (plan:236) does evaluate to 1. But decision 11.2 says to ADD it (plan:272) to a post-link that already ends with `exit 0` (recipe.yaml:188-209, exit at :208). Anything after `exit 0` never runs, so the only working placement is before it.
- Measured (S3): the line inserted before the final `exit 0`, isabelle installed without the tool, installs cleanly. The critics' LinkError (S4 here; critic-conda scenario F) puts the line last, which the plan does not prescribe.
- What remains true:
  - The plan gives neither placement nor the `.bat` text ("同理", plan:272).
  - The `&&` form reports nothing when the tool fails. Measured (S7): silent, which contradicts plan:233's promise that failures go to `.messages.txt`.
  - The plan's tests never install isabelle without the tool (plan:304-306, 364-369).

CONFIRMED 2: the interface is inconsistent.
- post-link ignores `<feature>`, since it always applies the whole chain (plan:229).
- The isabelle package passes `isabelle`, which is not a feature (plan:236). "所有包相同" (plan:228) is false even among the feature packages, because each names its own feature.
- Decision 2 says "钩子把 `$PREFIX/isa` 传给它" (plan:148), but the hook line passes nothing (plan:227). This is harmless in practice, since sys.prefix equals $PREFIX for the entry point (link.py:1631). The text is still inconsistent.
- The isabelle copy of the line is written by hand in another repository (plan:236, 272).

CONFIRMED 3: a rev-1 defect survives. Rev 1's judge required "make the conda-hook contract part of the 1.x compatibility promise" (REVIEW1:494). Rev 2 adopted `<2` (plan:247) but states no such promise; a search of the plan finds none. It is worse than rev 1 knew: the isabelle package has no requirements (recipe.yaml:235-237) and no run_constraints (plan:271). So its line will call any future tool version, 2.x included.

THE EDITOR'S RELAXATION is sound, with three refinements.
- Dropping `<feature>` from post-link makes the text say what it does: post-link reconciles the installed set, whichever package triggered it. One post-link fragment then serves every package.
- (a) For feature packages, the tool is a hard dependency, so a silent skip when it is absent loses information. An `elif [ -d …/features.d ]` branch reports a missing tool and stays silent for a plain isabelle install. This is still one byte-identical fragment (measured S2, S5, S6).
- (b) In the isabelle package, it is the fragment that is byte-identical, embedded in its larger message script, not the whole file. The CI cannot consume the fragment at build time, so the canonical copy lives in the tool repo and the CI copies it verbatim.
- (c) pre-unlink keeps `<feature>`. Deriving the feature from $PKG_NAME breaks for `qiyuan-dev-patches` (plan:245).

Severity major is fair: the failure leaves the env unusable, and published hook text can never be fixed.

Experiment: Files:
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C4/mkchan.py builds a toy noarch channel.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C4/run.sh runs the scenarios.
- /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C4/run.out holds the output.

Setup: local conda 25.11.1, fully isolated (HOME, CONDA_PKGS_DIRS, CONDA_ENVS_DIRS and TMPDIR redirected; CONDA_REGISTER_ENVS=false). Packages:
- `isa` build 0: no hooks.
- `isa` build 2: a CI-style message post-link with rev 2's line placed before the final `exit 0`.
- `isa` build 3: rev 2's line as the last line.
- `isa` build 4: the safe fragment, then `exit 0`.
- `ipc` build 0: a working toy tool.
- `ipc` build 1: a toy tool that dies before its handler, printing an ImportError traceback and exiting 1. This simulates a start-up failure.
- `feata`: rev 2's one-line hooks.
- `featsafe`: the safe fragment plus `exit 0`.

Results:
- S1: create an env with isa 0 and the broken ipc, then `conda install feata`. LinkError, return code 1. conda-meta/history is ABSENT afterwards, and `conda list -p` exits 2.
- S2: the same env, then `conda install featsafe`. exit 0; the message "isabelle-patch-control could not run; run: isabelle-patch-control apply" is printed; history is present.
- S3: isa build 2 alone, no tool. exit 0. The line is safe when placed before `exit 0`.
- S4: isa build 3 alone, no tool. LinkError, return code 1, history ABSENT. This reproduces the critics' scenario.
- S5: isa build 4 alone. exit 0, silent.
- S6: isa build 4, the working tool and featsafe. Both post-links call the tool; exit 0.
- S7: isa build 2 with the broken tool. exit 0, but nothing is reported to the user.

Windows was not run. I relied on conda/utils.py:268-269 and link.py:1606-1613.

Recommended fix: 1. Decision 8 (plan:226-236): one canonical post-link fragment, owned by the tool repo (e.g. tools/conda-hooks/post-link.sh and .bat), with no feature argument:

   if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then "$PREFIX/bin/isabelle-patch-control" conda-hook post-link || echo "isabelle-patch-control could not run; run: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"; elif [ -d "$PREFIX/share/isabelle_patch_control/features.d" ]; then echo "isabelle-patch-control is not installed; feature patches were not applied" >> "$PREFIX/.messages.txt"; fi

   The .bat uses `if exist "%PREFIX%\Scripts\isabelle-patch-control.exe" (call … conda-hook post-link || >>"%PREFIX%\.messages.txt" echo …) else if exist … echo …`.
   - Every rendered hook ends with `exit 0` / `exit /b 0`.
   - pre-unlink is `conda-hook pre-unlink <feature> || echo … >> .messages.txt`, then `exit 0`.
   - Reword plan:228 to say that every post-link fragment is byte-identical and that pre-unlink differs only in the feature name.
   - Add one sentence citing RELEASE_CHECKLIST.md:259 and recipe.yaml:118-122.
2. Decision 11.2 (plan:272): give the exact .sh and .bat fragment, copied verbatim from the tool repo, and require that it go before the recipe's existing final `exit 0` / `exit /b 0`.
3. Decision 1 or 8: state that the `conda-hook post-link` and `conda-hook pre-unlink <feature>` command lines, the tree being sys.prefix/isa (= $PREFIX/isa), the exit status 0 and the .messages.txt channel are frozen for all of 1.x. Because the isabelle package has no tool dependency (plan:271), also state that `conda-hook post-link` must stay accepted by every later tool version. Fix plan:148 to say that conda-hook takes the tree from sys.prefix rather than from an argument.
4. Decision 14's hook-layer test (plan:304-306): add (a) a tool that exits non-zero before its handler: the install must succeed, conda-meta/history must survive and the message must appear; and (b) an isabelle-style package that carries the fragment, installed with no tool: the install must succeed silently. Both use the canonical fragment file.

**Judge: partially_confirmed → author_decides_then_rereview.** Confirmed: exit 0 lives only in the tool's code (plan:226-228, :335), so a tool that dies before its handler fails the transaction and deletes conda-meta/history (defender-C4 S1). The interface is also inconsistent (plan:148, :228-229, :236), and rev-1's freeze of the 1.x contract (REVIEW1:494) is missing.

Refuted: rev 2's isabelle line does not exit 1 when it is placed before the recipe's existing `exit 0` (recipe.yaml:208; S3). The plan's real gap is that it never states where the line goes. Ctrl-C is a weak trigger.

Changes:
- One canonical post-link fragment, with no feature argument, owned by the tool repository (.sh and .bat):
  `if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then "$PREFIX/bin/isabelle-patch-control" conda-hook post-link || echo "<could not run; run apply>" >> "$PREFIX/.messages.txt"; elif [ -d "$PREFIX/share/isabelle_patch_control/features.d" ]; then echo "<tool not installed; features not applied>" >> "$PREFIX/.messages.txt"; fi`
  followed by `exit 0`.
- pre-unlink: `conda-hook pre-unlink <feature> || echo ...`, then `exit 0`.
- The renderer copies the fragment; reword plan:228 to say so.
- Decision 11.2 gives the exact .sh and .bat text and requires it before the existing final `exit 0` / `exit /b 0`.
- Decision 1 freezes for all of 1.x: the `conda-hook post-link` and `conda-hook pre-unlink <feature>` command lines, tree = $PREFIX/isa, exit 0, and the .messages.txt channel. Every later version must keep accepting `post-link`, because the isabelle package has no bound on the tool.
- Fix plan:148.

Hook-layer tests:
- a tool that fails at start-up: the install succeeds, history survives, and the message is shown;
- an isabelle-style package carrying the fragment, installed with no tool: silent success.

### C5 [major] Rev 1's C1 survives in part: nothing makes apply skip a feature's created file that is already present, or unapply delete it, so ruling 13's automatic re-apply fails for light and `conda remove` leaves files behind

Section: Decision 5 (plan:190-195); decision 6 (plan:209-213); decision 8 (plan:239-240); decision 14 (plan:300-306); §6 (g) (plan:369)  ·  merged from: conda-conda-4, engine-E5, consistency-F7

**Statement.** What was required. Rev 2 adopted the status half of rev 1's C1 rule: a created file that is present with exactly the patch's content is consistent with both applied and not-applied (plan:190-191). It left out the two action rules the judge required with it (REVIEW1:259-260): "`apply` skips such a file, and `unapply` of a not-applied feature deletes it, so `conda remove isabelle` leaves nothing behind".

(1) apply. Decision 6 hands "the files not yet in place" of a not-applied feature to git apply (plan:209-210), and never says whether a present, identical created file counts as in place. git apply refuses a creation patch whose target exists ("already exists in working directory"). Since decision 4 passes all of a feature's files in one call, the whole call fails (critic-conda/git1.out case 6, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/). This state is not rare: every isabelle relink (ruling 13's re-apply, every update, every clone) produces it, because light creates three files conda does not track. `git diff-tree -r --no-renames --name-status Isabelle2025-2/future_assign_interrupt Isabelle2025-2/light_locale` lists A src/Pure/Isar/light_locale_axiom_facts.ML, src/Pure/exported_premises.ML and src/Pure/more_exported_premises.ML (also RECORD.md:19-20). In critic-conda/run.out scenario G, the feature above then reads CONFLICT.

(2) unapply. Decision 6 reverses only applied and half-applied features (plan:212). Ruling 13 itself creates a relinked tree that was not repaired: `--force-reinstall isabelle` on 2025.2-0 without the manual apply. There light reads not-applied, so its three files survive `conda remove isabelle-light-locale` and `conda remove isabelle`, and §6 (g) fails (critic-engine/e6/caseD.py).

(3) Decision 8's claim that these leftover files are harmless because "apply can repair" (plan:239-240) holds only once (1) is in place.

(4) Why the special rule exists at all. The shape rule says the applied features form a prefix of the chain with at most one half-applied feature above it (plan:194-195). Without the special created-file rule, a relinked light reads half-applied above not-applied features, which is a hole and exit 3. Decision 6 also never says what apply and unapply do when the shape is illegal; rev 1 asked that they refuse (REVIEW1:402).

(5) Rev 1's judge required tests for C3's five reproduced scenarios, including "an upper feature that moves or renames a lower feature's addition" (REVIEW1:395). Decision 14's list (plan:300-303) does not name them.

Required.
- Add both action rules to decision 6, for apply and unapply with or without --feature.
- Specify what apply and unapply do on an illegal shape.
- Add the five C3 scenarios to pytest.
- Add a relink-then-remove case to the hook-layer test: (i) the new build's post-link re-applies the whole chain over left-behind created files; (ii) `conda remove isabelle`, with no repair in between, leaves no isa/.

**Editor.** Parts (1) and (2) are confirmed. Where the critics overreach:
- engine-E5's cases A, B and C are not reachable on today's chain. Case A is an upper feature that edits a lower feature's created file, case B one that deletes or renames it, case C a feature made only of created files. `git diff-tree --name-status` from Isabelle2025-2/light_locale to each of local_type_abbrev, localized_record, local_datatype and dev_patches lists none of light's three created files. They deserve tests, because rev 1 required the rename case, but they are not current defects.
- E5's claim that under per-file moves "any fitting level gives the same result" is false in general. Suppose a file fits levels j1 < j2. Moving from j1 replays t_{j1+1}..t_{j2} on content that already fits j2, which gives different bytes unless those patches leave this content unchanged. The claim does hold for an absent file, because a creation followed by a deletion leaves nothing, and that is E5's case B. The relaxation below therefore keeps an ambiguity check.
- consistency-F7 contributes only its second half here; its lock half is in C7.

**Relaxation proposed by the editor.** With C2's install by rename, define apply and unapply as moves of each file to a target level, not as calls per feature.
- apply computes the target as the highest chain level at or below which no touched file is CONFLICT. It then moves every file from its fitting level to that target, by replaying the file's own patches on a scratch copy.
- `unapply --feature F` moves every file to the level just below F.
- A file whose several fitting levels lead to different target contents is CONFLICT.
A left-behind created file is then simply a file already at its creator's level: apply leaves it alone, and unapply deletes it. Neither the special created-file rule nor the shape rule is needed as an input to apply and unapply; applied, half-applied, not-applied and "hole" become words that status displays. critic-engine prototyped this shape: e6/perfile.py handles all toy cases in both directions, and e5/relink_real.py brings a relinked real chain to exactly the dev_patches tip 30aab6e in 2.2 s.

**Defender: partially_confirmed** (needs owner: False).

Verdict in short: the core of the challenge holds. The created-file rule rev 2 kept from C1 is itself the cause of the unapply defect. The smallest fix is to delete that rule, not to add two more special action rules beside it.

Part (2), unapply: confirmed. Decision 5 says a present created file with the patch's exact content is compatible with both applied and not-applied (plan:190-191). So a relinked light reads not-applied (plan:192-193). Decision 6's unapply only acts on applied or half-applied features (plan:212). On the real chain (39 files; light adds 3 and modifies 29, confirmed by `git diff-tree --name-status 6d8be01 7983d8a` and RECORD.md:19-20), `unapply --feature light_locale` on the unrepaired relinked 2025.2-0 tree leaves all three created files (real_relink.out, M2). Conda also leaves untracked files under isa/ after a remove (critic-conda/run.out scenario B: isa/etc/.isabelle_patch_control.lock survives). So §6 (g) (plan:369) fails on this path. The rev-1 judge required "unapply of a not-applied feature deletes it" (REVIEW1:259-260), and rev 2 has no such rule. The key point: without the rule, the plain level replay of decision 5's first bullet (plan:186-189) gives each present identical created file exactly one level, light's own (levels [1] for all three files). Light then reads half-applied, and decision 6's existing half-applied branch deletes the files (M3: "created files left: []").

Part (1), apply: confirmed as a contradiction in the spec. That apply always fails is refuted.
- Decision 4 says each call hands over "一个 feature 的全部 patch 文件" ("all of a feature's patch files", plan:175-176).
- Decision 6 says only "尚未到位的文件" ("the files not yet in place", plan:209-210).
- Neither says whether a file that is compatible with both states counts as in place.
- With decision 4's wording, real-chain apply fails: "light_locale_axiom_facts.ML: already exists in working directory" (M1).
- With decision 6's wording, where "in place" means the replay level, apply reaches the dev_patches tip exactly: 0 differing files (M2).
So ruling 13's re-apply works or not depending on which sentence an implementer follows.

Part (3) follows from (1).

Refuted evidence: run.out scenario G does not model decision 5. Its toy `state()` runs one whole-feature `--check` (mkchan.py:24-26), so its CONFLICT is an artifact of the toy. Under decision 5 the feature reads not-applied.

Part (4), partly refuted. Under the literal shape rule (plan:194-195: an applied prefix with at most one half-applied feature above it), the relinked real tree [fai not-applied, light half-applied, dev not-applied] is legal, not a hole. The text never says "directly above". But it becomes illegal as soon as two features create files: two_creators.out shows both F1 and F2 half-applied and the shape illegal, while file-driven apply and unapply still reach tip and base. That matters because the three new features are being written now (ruling 16). Decision 6 never says whether apply and unapply consult the shape (REVIEW1:402); §4 only lists hole under exit 3 (plan:334-335). That gap is confirmed.

A further rev-1 item was also dropped. Decision 5 defines only "no level means CONFLICT" (plan:188) and drops the rev-1 judge's rule that a file with several levels is an error (REVIEW1:399-400). And under the created-file rule, a feature made only of created files is undefined (toy case C: "UNDEFINED").

Part (5): partly confirmed, minor. Decision 14 (plan:300-306) covers levels and "created files left on the tree", but it names neither the C3 rename/move case (REVIEW1:395) nor relink-then-remove. Ruling 17 delegates test choices to the author, so this is a request, not a defect of a ruling.

The editor's relaxation is right in substance: act per file, treat status words and shape as display only, keep the ambiguity check. It needs two corrections.
(a) As written, apply "moves every file ... to that target". Files above the target would then move down. Example: one hand-edited dev_patches file would make a post-link apply reverse dev's other seven files. Apply must only move files up and unapply only down, mirroring plan:232.
(b) It does not need C2's install-by-rename. One git apply call per feature, restricted to the files the replay selects, already moves files per file on the real tree. That keeps decision 4's "git apply is the only writer" and its per-call atomicity; M3 and two_creators do exactly this.

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C5/, using git 2.43.0. On contrib/Isabelle2025-2 I ran only read-only git commands (diff-tree, show, rev-parse).

1. Real chain. `git diff-tree -r --no-renames --name-status` for each step:
   - expose_foreign f8d760a to future_assign_interrupt 6d8be01: 1 M.
   - 6d8be01 to light_locale 7983d8a: 3 A and 29 M.
   - local_type_abbrev, localized_record and local_datatype are each equal to 7983d8a.
   - 7983d8a to dev_patches 30aab6e: 8 M.
   - From light to dev, none of light's three created files is touched.

2. real_relink.py, output in real_relink.out (7 s). I generated patch files the way make-patches does (make-patches:153-171). The base is the expose_foreign tree (2025.2-0). I applied fai, light and dev, then simulated the relink: every tracked file went back to base and the three created files stayed. Replay levels of the three created files: [1] each, i.e. light. Results:
   - Status with the created-file rule: all three features not-applied. Without it: light half-applied (29 files not applied), the others not-applied.
   - M1: apply handing every file of a not-applied feature (decision 4's wording) fails at light with "already exists in working directory".
   - M2: apply handing only files whose replay level is below the feature (decision 6's wording) gives 0 files different from 30aab6e.
   - M3: no created-file rule, decision 6 as written: 0 different.
   - Then `unapply --feature light_locale` on the unrepaired relinked tree. M2: all three created files left. M3: none left; only future.ML differs, as expected, because fai was never re-applied.

3. two_creators.py, output in two_creators.out (a toy built on critic-engine's e6/toy.py). F1 and F2 each edit a file and create one; then the relink.
   - With the created-file rule: both not-applied, shape legal.
   - Without it: both half-applied, shape illegal under plan:194-195.
   - File-driven apply (per feature, files chosen by replay level, status word ignored) gives the tip. File-driven unapply gives the base, with no created files left.

4. Re-ran critic-engine e6 (toy.py, caseD.py, perfile.py) in my own directory and reproduced its output. caseD: decision 5 as written gives F1 not-applied; plain levels give half-applied.

5. Read critic-conda/git1.out case 6, which shows the creation patch refused because the file exists. Read mkchan.py:24-26: the toy tool's state is one whole-feature check, not decision 5. Read run.out scenario B: untracked files under isa/ survive `conda remove isa`.

Recommended fix: Smallest fix. Remove the special case rather than adding more special cases.
1. Delete the created-file rule (plan:190-191). Decision 5's replay alone already gives a present, identical created file its creator's level, an absent one the level below, and a different one no level, which is CONFLICT.
2. Reconcile decisions 4 and 6 and make decision 6 file-driven:
   - apply: for each feature F in chain order up to the target, one git_apply call with exactly those of F's patch files whose file's replay level is below F. Stop at the first CONFLICT file and never move a file down.
   - unapply: in reverse chain order down to F, one reverse call per feature with exactly those patch files whose level is at or above that feature.
   - The status word of a feature is not consulted.
   - Change plan:175-176 from "全部 patch 文件" (all patch files) to the files not in place.
3. Restore the rev-1 rule: a file that fits several levels is CONFLICT (plan:188).
4. The shape rule (plan:194-195) only affects status. Apply and unapply do not consult it. Under per-file levels, a not-applied feature below an applied one cannot share a file with it, so the double application that motivated "refuse" cannot happen. Report the shape with exit 1, not 3; exit 3 stays for directory and chain-link errors (plan:334-335).
5. Rewrite plan:239-240. After a relink, light reads half-applied (3 files in place, 29 not). The post-link's apply completes it, and light's pre-unlink deletes the three files even if the tree was never repaired.
6. Tests (the author's call under ruling 17):
   - pytest: a relinked tree with two features that each create a file. Apply reaches the tip; unapply reaches the base with no created files left.
   - Hook layer: a 2025.2-0-like build, `--force-reinstall` without repair, then `conda remove isabelle` leaves no created files (the lock file belongs to C7).
   - Name C3's move/rename case.
If the editor's per-file-move relaxation is adopted instead, apply must only move files up and unapply only down, and it can keep per-feature git apply calls without C2's rename.

**Judge: partially_confirmed → author_decides_then_rereview.** Confirmed: decision 6 never says how a present, identical created file is treated, and decision 4's 'all patch files' wording makes apply fail with 'already exists'. unapply of a not-applied light leaves its three created files (defender-C5 M1/M2), and REVIEW1:259-260's action rules are missing.

Refuted:
- scenario G's evidence: the toy ran a whole-feature check (mkchan.py:24-26);
- that apply always fails: it depends on which sentence an implementer follows;
- the defender's claim that C2's rename is unnecessary: per-feature calls in the tree are unsafe (C2).

Smallest elegant fix:
(1) Delete the created-file rule (plan:190-191). Plain replay already gives a present, identical created file its creator's level, an absent one the level below, and a different one no level.
(2) Redefine apply and unapply as per-file moves to a target level:
- apply's target is the top, or F, capped just below the lowest feature that has a CONFLICT file. It only moves files up.
- `unapply --feature F` only moves files down, to the level below F.
- A file that fits several levels is CONFLICT, unless moving it from each of them gives the same content. That covers an absent file that one feature creates and a later one deletes.
(3) applied, half-applied, not-applied and the shape rule (plan:194-195) become words status displays; apply and unapply never consult them. A 'hole' is exit 1, not 3.
(4) State what unapply does at a CONFLICT file. Recommended: move every file that can be moved and list the rest. Say that this supersedes REVIEW1:315's refuse-beneath rule, whose only reason was the prefix shape, and that it minimises the residue a pre-unlink leaves (C8).
(5) Rewrite plan:239-240.
(6) Tests:
- rev-1's five C3 scenarios (REVIEW1:395), including the move/rename case;
- two features that each create a file, then a relink: apply reaches the tip, and unapply reaches the base with no created files left;
- hook layer: relink, then `conda remove isabelle` with no repair in between, leaves no isa/.

### C6 [major] The level definition leaves open the reading that reproduces rev 1's false CONFLICT: the forward half is not stated as sequential, several fitting levels are undefined, and --dry-run is never defined

Section: Decision 5 (plan:186-189); decision 6 (plan:209, :212); §4 (plan:326-327)  ·  merged from: engine-E6, consistency-F10

**Statement.** The ambiguity. Decision 5 defines a file's level j by two checks. For the reverse half it says each patch is really reversed on the copy before the next one is checked (plan:186-187). For the forward half it says only "on another copy, git apply --check t_{j+1}, …, t_m one by one, all pass" (plan:187-188). Read literally, every forward check runs against the unchanged copy.

Why that matters on the real chain. src/Pure/Syntax/syntax_phases.ML is patched by light and then by dev_patches, and dev's hunk context comes from light. Checking dev's patch on a copy where light is not yet applied gives "patch failed: src/Pure/Syntax/syntax_phases.ML:739", rc=1; it passes once light's patch has really been applied (critic-engine/e5/literal.sh; critic-consistency/sp/, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/). Under the literal reading, therefore, this file has no level on a fresh tree, so it reads CONFLICT and apply stops. That is rev 1's blocking false CONFLICT (C3) again. A single multi-patch `git apply --check light.patch dev.patch` also gives rc=1, while applying both succeeds, so --check never chains, within one call or across calls. The sequential reading works: on every prefix of the real chain, each of the 40 files has exactly one level, at 126-128 git calls and 1.3-2.3 s per status (critic-engine/e5/levels.py).

Two more gaps:
- Several fitting levels. The definition does not say what a file that fits several levels means. Rev 1's judge ruled it an error, except under the created-file rule (REVIEW1:401).
- --dry-run. It is listed for apply and unapply (plan:209, :212, :326-327) but never defined. Its natural implementation, one `git apply --check` per feature against the unchanged tree, fails on dev's syntax_phases.ML on a fresh tree for the same reason (REVIEW1:154). The judge required apply, unapply and --dry-run to run the same per-file sequences on scratch copies (REVIEW1:403).

Required.
- Phrase both halves the same way: each patch is applied to the copy before the next one is checked.
- State the rule for several fitting levels.
- Define --dry-run as the same replay without the final write.
- Add the light and dev_patches syntax_phases.ML pair to pytest.

**Editor.** Confirmed. engine-E6 claims that under per-file moves "any fitting level gives the same result"; that is false in general (see C5's rebuttal), so the rule for several fitting levels must be stated, not assumed.

**Relaxation proposed by the editor.** Under C2's install by rename, --dry-run is simply apply or unapply with the install step skipped, so it cannot diverge from the real run, and no separate definition is needed.

**Defender: confirmed** (needs owner: False).

I tried to refute all three parts of C6 and could not. Two side claims are overstated, and I correct them below.

1. The forward half of the level definition is ambiguous, and its literal reading brings back rev 1's false CONFLICT.
- The reverse half says each patch that passes is really reversed on the copy before the next one is checked (plan:186-187). The forward half only says "on another copy, `git apply --check` t_{j+1}..t_m one by one, all pass" (plan:187-188). `--check` never writes, so read literally every forward check runs against the unchanged copy.
- Rev 2 also moved away from the rev-1 judge's wording. The judge wrote "forward-applying t_{j+1}..t_m" (REVIEW1:399); rev 2 turned that into "--check". The only hint that the forward half is sequential is the word "replay" in the D4 row of §7 (plan:394).
- I ran both readings on the real patches (git 2.43.0).
  - Sequential reading (defender-C6/levels_seq.py): all 40 files have exactly one level on every one of the 5 chain prefixes, at 126-128 git calls per status.
  - Literal reading (defender-C6/levels_literal.py, the same script without the forward write): src/Pure/Syntax/syntax_phases.ML has no level on the pristine tree, on +expose_foreign and on +future_assign_interrupt. That last state is exactly what a 2025.2-0 tree is once future_assign_interrupt is applied.
- With no level, light reads CONFLICT (plan:192-193) and `apply` stops (plan:209-210). That is rev 1's C3 again.
- Directly: `git apply --check` of dev's syntax_phases.ML patch on the base copy fails with "patch failed: src/Pure/Syntax/syntax_phases.ML:739" (defender-C6/t1). After light's patch has really been applied, the same check passes (defender-C6/t2).

2. The plan gives no rule for a file that fits several levels.
- plan:186 says "j is the level" as if it were unique. The only multi-level rule is the one for created files (plan:190-191).
- The rev-1 judge's ruling was dropped: "A file with more than one level is an error, except under C1's rule for created files" (REVIEW1:401).
- Several fitting levels really happen with git apply. When a hunk's lines also appear elsewhere in the file, git apply finds them at an offset. In a toy (defender-C6/multi), a 7-line hunk is repeated 11 lines further down. On the applied file both `-R --check` and `--check` pass, so levels 0 and 1 both fit.
- If the tool picks the lower level, `apply` patches the duplicate block at line 19 and returns rc=0, silently corrupting the file. The mirror case makes picking the higher level unsafe too. So "any fitting level gives the same result" is false, and the only safe rule is the judge's: report the file as an error.
- On the real chain this never happens (levels_seq.py), so the safe rule costs nothing in practice.

3. `--dry-run` is listed but never defined (plan:209, :212, :326-327).
- The rev-1 defect is REVIEW1:338: today's dry-run tests each patch against the unchanged tree (patcher.py:86-87). The judge's fix was "apply, unapply and --dry-run run the same per-file sequences" (REVIEW1:403). Rev 2 dropped it.
- The natural rev-2 implementation is decision 6's loop with `git_apply(check=True)` (plan:171), one call per feature. It fails both ways with git apply:
  - `apply --dry-run` on a fresh tree fails at dev's syntax_phases.ML, at line 739.
  - `unapply --dry-run` on a fully applied file fails at light's `-R --check`, at line 729 (defender-C6/un).

Corrections to the challenge:
- (a) "--check never chains, within one call" is overstated. `git apply --check L.patch D.patch` (two arguments) does fail, rc=1. But the same two patches concatenated into one input pass `--check` (rc=0), and `-R` with the concatenation in chain order passes as well (defender-C6/t2, t3). The reason is that git apply treats each file argument as its own read, check and write step. A real two-argument `git apply L D` chains only because it writes L to disk before reading D.
- (b) Adding "the real pair to pytest" aims slightly wrong. pytest runs on toy trees (plan:300-301). The real pair is already covered by (b2), which applies the real chain up to its top (plan:353-355). What is missing is a toy of the same shape. More broadly, the test list (plan:300-303) still lacks rev-1's five required scenarios, including "fresh stacked tree" (REVIEW1:395, :404).

The editor's relaxation is right on its merits, but only if C2's install by rename is adopted. Then `--dry-run` is apply or unapply with the install step skipped, and it cannot diverge from the real run by construction. It still needs one sentence in the plan, so "no separate definition is needed" goes too far. And while rev 2 keeps git apply as the only writer (plan:177), the relaxation does not apply. In that case the same guarantee comes from making `--dry-run` the status computation itself. The forward replay already proves that every per-feature call will succeed, because each file's content at each step is identical.

Adjacent finding, outside C6, for whoever handles the engine: decision 4 claims that one call is atomic (plan:175-176), but it passes the patch files as separate arguments (plan:172). With git 2.43.0 that is not atomic. In defender-C6/atom2, passing light's attrib.ML and syntax_phases.ML patches as two arguments, with the second target corrupted, modified attrib.ML and returned rc=1. The same two patches as one concatenated input left attrib.ML untouched. §8's evidence ("a four-file diff, nothing changes") covers only the single-input case.

Experiment: Everything is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C6/. The real per-file patches were copied read-only from critic-engine/real (git diff-tree of 1113ce6..30aab6e). The git environment was isolated: GIT_DIR=/nonexistent, no global or system config.

1. levels_seq.py (critic's levels.py, sequential reading): on all 5 prefixes, 0 of 40 files have no level or several levels.
   levels_literal.py (forward half not written to the copy): syntax_phases.ML has no level on prefixes 0, 1 and 2.
2. t1/: `git apply --check` of dev's syntax_phases.ML patch on base: rc=1, "patch failed: ...:739". The attrib.ML pair passes either way.
3. t2/:
   - `--check L D` as two arguments: rc=1.
   - `cat L D | git apply --check`: rc=0.
   - real `git apply L D`: rc=0, giving the sequential result (sha 910c046e...).
   - Sequential: L applied, then `--check D`: rc=0.
4. t3/: on the fully applied file, `cat L D | git apply -R --check`: rc=0. The order D,L fails at 729.
5. un/: naive `unapply --dry-run` on the fully applied file: dev's `-R --check` gives rc=0, light's `-R --check` gives rc=1 at 729.
6. multi/: toy with a repeated 7-line block. On the applied file both `-R --check` and `--check` pass, so two levels fit. Treating the file as not-applied and applying writes the second block (line 19) with rc=0.
7. atom/ and atom2/: `git apply good.patch bad.patch` as two arguments modifies the good target and returns rc=1. The same pair concatenated into one input changes nothing.

Recommended fix: Smallest fix. The wording and test choices fall under the author's delegation (§0 item 17); none of it changes the design.

1. plan:187-188: give the forward half the same parenthetical as the reverse half: "on another copy, `git apply --check` t_{j+1}, ..., t_m one by one (each patch that passes is really applied to the copy before the next one is checked), all pass".

2. After plan:188, add: "If more than one j satisfies this, the file is reported as CONFLICT, marked ambiguous, with each j listed; created files follow the next rule instead." This is the rev-1 judge's rule (REVIEW1:401). Add a one-line reason: because of offset matching, a file with a repeated block fits two levels, and either choice can write the wrong block.

3. Decision 6 (plan:209-213) and §4 (plan:326-327), add: "--dry-run does only decision 5's per-file replay (the same computation as status), prints the features and files that apply/unapply would hand to git apply, and writes nothing; its exit code is the same as the real run's. It never runs one `--check` per feature against the unchanged tree."
   If C2's install by rename is adopted, replace this with "--dry-run skips the install step". Either way it is one sentence, and either way it cannot diverge from the real run.

4. pytest list (plan:300-303):
   - Add a toy stacked-context pair: an upper feature whose hunk context contains lines a lower feature added. Run status, apply, unapply and both --dry-runs on the fresh, half-applied and fully applied trees.
   - Add the repeated-block toy for the several-levels rule.
   - Restore rev-1's five scenarios (REVIEW1:395).
   The real light and dev syntax_phases.ML pair is already covered by (b2) (plan:353-355).

Adjacent, to route to the engine reviewer: plan:172/:175 should pass a feature's patch files to git apply as one concatenated input on stdin. With separate arguments the call is not atomic in git 2.43.0.

**Judge: confirmed → author_decides_then_rereview.** Confirmed. The literal forward half of plan:187-188 leaves syntax_phases.ML with no level on a fresh tree (defender-C6 levels_literal.py). Several fitting levels do occur: in the repeated-block toy, picking either level can write the wrong block. --dry-run is undefined. Correction: a concatenated single stream does chain within one --check; two separate arguments do not.

Changes:
- Give plan:187-188 the same parenthetical as the reverse half: each patch that passes is really applied to the copy before the next one is checked.
- Add the several-fitting-levels rule from C5, with a one-line reason (offset matching).
- Define --dry-run in one sentence: the same replay with the install step skipped (C2), the same exit code, and printing what would move.
- pytest:
  - a toy stacked-context pair (an upper feature's hunk context contains lines the lower feature added), run with status, apply, unapply and both --dry-runs on fresh, half-applied and fully applied trees;
  - the repeated-block toy.
  The real light/dev pair stays covered by (b2).

### C7 [major] The lock file the tool creates in isa/etc survives `conda remove isabelle`, so acceptance item (g) cannot pass; it also breaks the (b2) comparison and makes status need write access

Section: Decision 4 (plan:179-180); §6 (g) (plan:369); §5 step 4 (b2) (plan:353-355); Appendix A (plan:443-446); decision 14 (plan:303)  ·  merged from: conda-conda-6, engine-E7, consistency-F7, landing-L9, user-F6

**Statement.** The defect. Every run of the tool, status included, holds a lock on `DIR/etc/.isabelle_patch_control.lock`, a file the tool creates (plan:179-180). conda does not track that file. `conda remove isabelle` deletes the package's own files, but this file keeps isa/etc and isa/ alive. The isabelle package's pre-unlink removes only the user directory (isabelle-packaging-ci/conda/recipe.yaml:223-231). So §6 (g), "no isa/ left in the environment" (plan:369), fails by construction. Three toy channels show it (critic-conda/run.out scenario B; critic-landing/toy2/T2-remove.log; critic-user/run2.out walk g; all under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

Further consequences:
- `conda create --clone` copies the file (critic-conda/run3.out).
- In (b2), copy A, patched by the tool, carries the file and copy B does not, so "the whole trees are equal" (plan:355) fails.
- Because even status must create the file, status fails for a user who cannot write isa/etc in a shared, root-owned environment, although status changes nothing.
- It adds a second kind of untracked file, which Appendix A does not admit (plan:443-446).

Deleting the file after use is no fix. Unlinking a flock'ed file lets two processes hold "the lock" at the same time (critic-engine/e8/race.py). "The second process waits or reports busy" (plan:180) also leaves open whether a hook waits for ever inside conda. Rev 1's owner question 11 had proposed a lock that creates no file (REVIEW1:111).

Required.
- Take the lock without creating anything under the prefix.
- status takes a shared lock, or none.
- conda-hook waits a bounded time, then reports "busy" through .messages.txt.
- Make §6 (g) a concrete check: `find $PREFIX/isa` prints nothing.

**Editor.** Confirmed by construction and by three toy runs. Two of the proposed lock targets are weaker than the one in the relaxation:
- consistency-F7's "flock a file descriptor of the isa/ directory" works only on POSIX; msvcrt.locking cannot lock a directory handle.
- conda-conda-6's lock file in the system temp directory, named by a hash of the tree's path, works, but it creates a file outside the prefix that nothing ever removes.

**Relaxation proposed by the editor.** Lock a file that conda already tracks and no feature patches, opened read-only: for example DIR/etc/ISABELLE_ID, or a zero-byte file shipped in the tool's own conda package. Use fcntl.flock (shared for status, exclusive for apply and unapply), and msvcrt.locking on Windows, to be checked on the Windows leg. Nothing is created and nothing is left behind, status needs no write access, and the (b2) trees stay comparable. Two environments that share the hard-linked inode merely serialise, which is harmless.

**Defender: confirmed** (needs owner: False).

I tried to refute C7 and could not. Its core is a defect by construction. One sub-claim depends on how the lock is implemented. The editor's relaxation is right, but it needs three platform details.

What the plan says. Decision 4 has the tool hold a lock on DIR/etc/.isabelle_patch_control.lock "运行期间" (while it runs), and the second process "等待或报忙" (waits or reports busy) (plan:179-180; §0 item 17, plan:57). Only the directory interface is exempt ("不加锁", plan:220). So status, apply, unapply and conda-hook all lock. The plan's phrase "由 .gitignore 之外的 conda 树承载，不进 git 树" (plan:179-180) shows the author thought only about keeping the file out of git, not about conda leaving it behind. Nothing ever removes the file. The isabelle package's pre-unlink deletes only the user directory (isabelle-packaging-ci/conda/recipe.yaml:212-231 for .sh, :153-169 for .bat), and the plan keeps that pre-unlink as it is (plan:237, plan:272).

What is confirmed:
1. §6 (g) (plan:369) fails. In my toy channel (a copy of the critic's mkchan.py with real git apply and private HOME, CONDARC and pkgs), `conda remove isa` removes every package, yet `isa isa/etc isa/etc/.isabelle_patch_control.lock` stays (defender-C7/run_orig.out, scenario B). It also fails with no feature package at all. The new isabelle build's own post-link runs the tool whenever the tool is installed (plan:236), and that creates the file (scenario B1, if the tool locks before it looks at features.d; the plan does not fix that order).
2. `conda create --clone` copies the file (scenario I; the plan itself says so at plan:107-108).
3. (b2) fails twice. The migration plan requires copy A to equal copy B as a whole tree, mode bits included, with no exclusion list, and the unapplied A to equal the original build (ISABELLE_GIT_MIGRATION_PLAN.md:403-406). The comparison helper counts every file (tools/common.py:155-162, `git add -f -A`). Copy A goes through the tool, so it gets the lock file (plan:354). In scenario U, after removing all features the tree's file set differs from the package's by exactly this file.
4. Appendix A breaks. It keeps "post-link 不生成 conda 不跟踪的东西" (post-link creates nothing conda does not track) as the isabelle package's own principle (plan:433). Yet that package's own post-link, through the tool, now creates such a file. The list of costs (plan:442-447) does not mention it.
5. Deleting the file after use is no fix. Re-running race.py: B acquired inode 8357174 and C acquired inode 8357175, so both held "the lock" at once.
6. "等待或报忙" leaves the wait unbounded. A hook could hang conda forever, for example behind a suspended `apply`. On POSIX a blocking flock waits for ever, while msvcrt LK_LOCK gives up after about 10 s, so the two platforms would differ.

The part that depends on implementation. "Status fails without write access" holds when the file does not exist yet, or when the implementation opens it for writing, the usual O_CREAT|O_RDWR. In toy scenario S, with a read-only isa/etc, it fails with "权限不够" (permission denied). An existing file opened read-only can be flock'ed locally. The plan does not say which, so status ends up needing write access only because the plan never decided how the file is opened.

The relaxation, judged on its merits. Lock DIR/etc/ISABELLE_ID. Conda tracks that file, decisions 2-3 already require it in every tree the tool accepts (plan:147-148, 160-161), and no feature changes it.
- It works. Every scenario passes (defender-C7/run_relax.out): after removal isa/ is gone (B and B1), the clone has no extra file (I), the file set equals the package's (U), and status works with a read-only etc (S).
- lockprobe.py: an exclusive and a shared flock on a read-only fd of a 0444 file both work. A hard link to the same inode (the pkgs cache) blocks as expected. No file is created, and content and mode stay unchanged. Two toy environments that share the inode only serialise.
- I prefer it to a zero-byte file in the tool's package. That file would lock per tool install, not per tree, and it does not exist for the --isabelle-home copies used by (b2), so a second mechanism would be needed.

Three details the relaxation still needs:
(a) It must be fcntl.flock. fcntl.lockf LOCK_EX on a read-only fd gives EBADF (lockprobe). On NFS, flock is emulated as a byte-range lock and an exclusive lock requires opening for writing (man 2 flock, "NFS details"). So apply, unapply and conda-hook should open the file read-write. ISABELLE_ID is 0644 in every tree here (pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_ID), and those commands need write access anyway. Status opens it read-only with LOCK_SH.
(b) Windows locks are mandatory, and msvcrt.locking has no shared mode. Isabelle itself reads etc/ISABELLE_ID (src/Pure/System/isabelle_system.scala:85-105, used at server.scala:548 and build_schedule.scala:1112). Locking from byte 0 would make those reads fail during the lock window, in this environment and in every environment sharing the inode. So the tool must seek past the end of the file and lock 1 byte there. The CPython docs say the locked region may extend beyond the end of the file.
(c) No feature may change the lock file, and this should be enforced, not remembered. A feature that patches etc/ISABELLE_ID would already break decision 3, so the tool should refuse it (exit 3).
CIFS mounts have the same mandatory semantics (man 2 flock, "CIFS details"); that is an edge case.

Elegance. Locking ISABELLE_ID ties the lock to the tree's identity file, which the tool already requires. Nothing is created, so §6 (g), the (b2) comparison, clone and Appendix A become correct without any exclusion list.

Experiment: Everything is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C7/.
(1) run.sh runs the local conda 25.11.1 against a toy file:// channel. It uses a private HOME, CONDARC, CONDA_PKGS_DIRS, CONDA_ENVS_DIRS and TMPDIR, and registers nothing. The channel comes from mkchan_orig.py, a copy of the critic's generator: a toy tool that runs real git apply, takes the plan's lock file, has the plan's hook lines, and includes an isa build 1 whose post-link calls the tool. mkchan_relax.py is the same except for one line: flock -s or -x, with -w 10, on a read-only fd of isa/etc/ISABELLE_ID.
Scenarios: B (create, then remove isa), B1 (isa build 1 plus the tool, no feature, then remove isa), I (clone), U (install, then remove every feature, then compare the file set with the package), S (status with isa/etc made read-only).
run_orig.out: B and B1 leave isa/etc/.isabelle_patch_control.lock; the clone copies it; U differs by exactly that file; S fails with permission denied on the lock.
run_relax.out: isa/ is absent after B and B1; the clone has no extra file; U's file set equals the package's; S works.
(2) lockprobe.py, on a 0444 file with a hard link: LOCK_EX and LOCK_SH on a read-only fd work, a second process gets busy through the same path and through the link, shared plus shared works, shared plus exclusive is busy. fcntl.lockf LOCK_EX on a read-only fd gives EBADF. No file was created; content, mode and link count are unchanged.
(3) Holding a flock on one toy environment's ISABELLE_ID blocks another environment that shares the inode. It is acquired as soon as the first one releases.
(4) Re-running the critic's race.py: after an unlink-and-recreate, B (inode 8357174) and C (inode 8357175) both hold the lock.
(5) Sources: man 2 flock ("NFS details", "CIFS details"); Isabelle2025-2 src/Pure/System/isabelle_system.scala:85-105 (Isabelle reads etc/ISABELLE_ID at runtime); file modes are 0644 in the pkgs/isabelle-2025.2-0, contrib/Isabelle2025-2 and 89701cf1768e trees. Windows was not tested.

Recommended fix: The smallest fix:
1. Decision 4 (plan:179-180): replace the lock file with "lock DIR/etc/ISABELLE_ID itself; create nothing."
   - POSIX: use fcntl.flock, never lockf. status opens the file read-only and takes LOCK_SH. apply, unapply and conda-hook open it read-write and take LOCK_EX; an exclusive flock on NFS needs a writable descriptor, and these commands need write access to the tree anyway.
   - Windows: use msvcrt.locking on 1 byte at an offset past the end of the file, exclusive for every command. Windows locks are mandatory, and locking byte 0 would block Isabelle's own reads of ISABELLE_ID.
   - Wait a bounded time: poll the non-blocking lock for about 60 s, then report "busy" (exit 1). conda-hook writes "busy" and the fix command to .messages.txt and exits 0.
   - Refuse, with exit 3, any feature directory whose patches touch etc/ISABELLE_ID.
2. §6 (g) (plan:369): make it a check, `test ! -e "$PREFIX/isa"` after `conda remove isabelle`, both with and without feature packages installed.
3. Decision 14 (plan:303): replace the bare "锁" with tests that apply and unapply leave the tree's file set equal to the package's, that status works on a read-only tree, that two exclusive runs serialise, and that a held lock gives "busy" within the time bound.
4. With these, (b2) (plan:353-355) and Appendix A (plan:433, 445-446) stay correct as written, and no exclusion list is needed.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed by construction and by toy channels (defender-C7 run_orig.out):
- the lock file survives `conda remove isabelle`;
- a clone copies it;
- it breaks (b2)'s comparison;
- status needs write access to create it.
Deleting the file after use is racy (race.py).

Changes:
- Decision 4 (plan:179-180): lock DIR/etc/ISABELLE_ID itself and create nothing.
  - POSIX: use fcntl.flock, never lockf. status opens the file read-only and takes LOCK_SH. apply, unapply and conda-hook open it read-write and take LOCK_EX; NFS needs a writable descriptor for an exclusive lock.
  - Windows: msvcrt.locking on 1 byte past the end of the file, so Isabelle's own reads of ISABELLE_ID are not blocked (isabelle_system.scala:85-105). Verify on the Windows leg.
  - Wait a bounded time (about 60 s), then report busy with exit 1; conda-hook writes busy plus the command to .messages.txt and exits 0.
  - Refuse with exit 3 any feature whose patches touch etc/ISABELLE_ID.
- §6 (g): `test ! -e "$PREFIX/isa"` after `conda remove isabelle`, with and without feature packages.
- Decision 14 tests:
  - after apply then unapply, the tree's file set equals the package's;
  - status works on a read-only tree;
  - two exclusive runs serialise;
  - a held lock gives busy within the bound.

### C8 [major] Rev 1's C2 survives: a failed pre-unlink leaves changes that status can no longer see, decision 8 offers a repair that cannot help, and Appendix A promises the opposite

Section: Decision 8 (plan:233-235); §7 row 发现 3 (plan:377); Appendix A (plan:445-446); decision 14 (plan:304-306); §6 (g) (plan:369)  ·  merged from: conda-conda-5, user-F4

**Statement.** The defect. conda removes a package whatever its pre-unlink returns (conda/core/link.py:1676-1683; plan:104). Suppose unapply cannot reverse feature F, because the user edited a patched file under $PREFIX/isa, or because an upper feature is CONFLICT and the prefix rule forbids reversing F. F's patch files are then deleted with the package. Afterwards no installed feature covers those files, so status reports a clean chain while F's changes and created files stay in the tree. Measured: an environment with feata and featb, a user edit to b.ML, then `conda remove featb`. The pre-unlink reports CONFLICT and the package is removed anyway. Afterwards features.d holds only feata, b.ML still has B2, new.ML is still present, and status prints only `applied a` (critic-conda/run2.out, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

What the plan says about this case:
- Decision 8 offers `status` and `apply` as the repair (plan:233-235); neither can help here.
- Appendix A promises that a failed cleanup leaves only "a hint in .messages.txt and a state status can see" (plan:446); that is false for a pre-unlink.
- §7 claims that the message lists the files that stay changed (plan:377), but decision 8 does not specify it.
Rev 1's judge required three things (REVIEW1:305-315): the pre-unlink message lists the files under isa/ that stay modified or created; "no residue" is stated only for the case where every hook succeeds; and a pre-unlink failure-path test exists. Decision 14 tests only a failing post-link (plan:305-306), and §6 (g) is unqualified.

Required.
- A failed pre-unlink writes every file F leaves modified or created. The tool knows them, because F's patch files are still present during pre-unlink.
- The message says that status will not see these files once the package is gone.
- It gives the restore steps. `conda install --force-reinstall isabelle` restores the tracked files, and on a new build its post-link re-applies the remaining chain. The listed created files must be deleted by hand, because conda never tracked them.
- Appendix A says this instead of "a state status can see".
- §6 (g) is qualified with "when every pre-unlink succeeded".
- Decision 14 adds the pre-unlink-failure case.
- Optionally, adopt the judge's check of the isa/ files against the isabelle package's per-file sha256 in conda-meta paths_data (REVIEW1:313), which plan:394 leaves 未采用 (not adopted), so that status can see such leftovers without a new ledger.

**Editor.** Confirmed. conda-conda-5 gives `--force-reinstall isabelle` as the whole remedy; that does not remove the created files, which conda never tracked, so the message must name them for deletion. user-F4 makes this point; its other parts are in C17.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute C8 and could not. Every part of it holds, in the plan text, in the conda source and in my own toy-channel runs. I also found one more fact that makes it stronger.

1. conda removes the package whatever the pre-unlink returns. In run_script, a non-zero exit raises LinkError only for pre-link and post-link (conda/core/link.py:1647-1675). For pre-unlink it only logs a warning and returns False (:1676-1683), and the caller ignores that value (:938-947). The plan states this itself (plan:104).

2. After the package is gone, status can no longer see the leftover changes. status only looks at the feature directories under features.d. Its per-file level model only covers files that installed features touch (plan:186-193). The leaving feature's patch files go away with the package. In my run, the user had edited b.ML, so the pre-unlink of featb found CONFLICT and reversed nothing. conda removed featb anyway. Afterwards the tree still had b.ML=[b1 B2 b3x] and new.ML, features.d held only `a`, and status printed only `applied a`. That is identical to a clean tree. I ran this on both toy isabelle builds (run.out, sections "isa build 1" and "isa build 0").
   - `conda doctor` cannot stand in for status. It printed "isa-1.0-1: 2 altered files" both with no leftovers and after the failed pre-unlink, because it cannot tell a change made by an installed feature from a leftover. It also never sees created files (doctor.out).
   - One nuance does not refute the point. If a remaining feature also patches a leftover file, status shows that remaining feature as CONFLICT, which blames the wrong feature. The rest of the leftovers stay invisible.

3. Decision 8's repair cannot help after a failed pre-unlink. Its failure text applies to both hooks and offers `isabelle-patch-control status` and `apply` as the fix (plan:233-235). The sentence saying the state is visible to status and repairable is about the post-link only (plan:234-235). After a failed pre-unlink, status reports a clean chain and apply does nothing.

4. Appendix A is wrong in two ways (plan:445-446). It says a failed cleanup "only leaves a hint in .messages.txt and a state status can see".
   - status cannot see the state (point 2).
   - Nothing is left in .messages.txt either. conda prints that file after each hook that exits 0 and then deletes it (link.py:1685, 1697-1708). I checked: no .messages.txt remained in any env that conda had processed. So the hint exists only once, in the terminal output.

5. §7 and decision 8 do not match. The §7 row for finding 3 claims the message lists the files that stay modified (plan:377). Decision 8 specifies only the status output, git apply's error and the repair commands. The status line format names at most the conflicting file of a CONFLICT feature (plan:202). It names neither created files nor the files of applied features underneath. That row also cites ruling 12 as its basis, but ruling 12 only fixes exit 0 and the .messages.txt channel (plan:50). It says nothing about what the message must contain.

6. The rev-1 judge's requirements for this case survived without being addressed:
   - The pre-unlink message must list the files under isa/ that stay modified or created (REVIEW1:313).
   - "No residue" must be stated only for the case where every hook succeeds, and there must be failure-path tests (REVIEW1:314). Decision 14 tests only a failing post-link (plan:305-306), and §6 (g) is unqualified (plan:369).
   - unapply must keep refusing to reverse a feature that sits beneath one it cannot reverse (REVIEW1:315). Decision 6 says nothing about what unapply does at CONFLICT (plan:212-213).

   No ruling makes these moot. Ruling 12 sets the exit code and the message channel, not the message content (plan:50). Ruling 17 hands this content to the author to decide, but it still has to be decided.

7. The facts behind C8's required fix all check out:
   - The tool can list the leftover files during pre-unlink. conda runs every pre-unlink before it unlinks any package (link.py:938-953). My hook log shows "features.d: a b" during the pre-unlink of featb, and again during the pre-unlink of feata when everything was removed together.
   - `conda install --force-reinstall` of the isabelle stand-in restored the tracked b.ML as a hardlink to the package cache again (link count 2). On the new build, the stand-in's post-link (rev 2's line verbatim) re-applied `a`. On the legacy build a manual apply was needed.
   - new.ML survived both restore paths, so created files really must be deleted by hand.
   - The force-reinstall also threw away the user's own edit (b3x). The message must warn about that, which C8 does not say.

8. One more fact, which strengthens the §6 (g) item. Decision 4 puts the lock file at isa/etc/.isabelle_patch_control.lock (plan:179-180), and conda does not track it. Even when every hook succeeded, `conda remove isa feata featb ipc` left isa/etc/.isabelle_patch_control.lock behind. When the pre-unlink failed, isa/src/new.ML was left too. So §6 (g) "no isa/ residue" (plan:369) fails even in the success case. Adding "when every pre-unlink succeeded" is not enough on its own.

9. The optional sha256 check is cheap but not required. The installed isabelle-2025.2-0 record has sha256 and sha256_in_prefix for all 24538 paths, 3548 of them under isa/src. Hashing the cached isa/src took 0.34 s. It would change how status works, though, and ruling 17 delegates only wording and test decisions (plan:56-58), so adopting it needs the owner. The plan just marks it "not adopted" without giving a reason (plan:394).

The editor's relaxation is empty, so there is nothing to weigh. The editor's rebuttal is right: force-reinstall alone does not remove the created files (measured above).

Experiment: All files are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C8/.

The setup:
- mkchan.py is a copy of critic-conda's channel generator. It builds a noarch channel with real `git apply`.
- isa build 0 has no hook. isa build 1's post-link is rev 2's line verbatim.
- ipc is the toy tool. Its post-link applies the whole chain, its pre-unlink reverses F and everything above it, it takes a lock at isa/etc/.isabelle_patch_control.lock, and it always exits 0.
- feata modifies src/a.ML. featb is based on a, modifies src/b.ML and creates src/new.ML.
- run.sh uses conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and CONDA_REGISTER_ENVS=false. The output is run.out, and the run directory is run.vBW7/.

Results:
(1) For each isa build: create the env with isa, feata, featb and ipc; edit b.ML (b3 to b3x); `conda remove featb`. The pre-unlink logs "features.d: a b" and "b: CONFLICT", and conda removes the package anyway. The tree keeps B2, b3x and new.ML, and status prints only "applied a".
(2) `conda install --force-reinstall isa`:
   - b.ML goes back to b1 b2 b3 (link count 2, a hardlink to the cache again), and the user's b3x edit is lost.
   - On build 1 the post-link re-applies a. On build 0 a manual apply is needed.
   - new.ML survives in both cases.
(3) `conda remove isa feata featb ipc` with every hook succeeding leaves isa/etc/.isabelle_patch_control.lock. With featb's pre-unlink failing, it also leaves isa/src/new.ML.
(4) No .messages.txt remains in any env that conda processed (conda deletes it after printing, link.py:1697-1708).
(5) doctor.sh and doctor.out: `conda doctor` reports "isa-1.0-1: 2" altered files both before and after the leftover, and status still prints "applied a".
(6) Read-only checks:
   - the installed isabelle-2025.2-0.json has 24538 paths with sha256 and sha256_in_prefix, 3548 of them under isa/src;
   - hashing the cached isa/src takes 0.34 s;
   - conda source read: link.py:938-953 and 1647-1708.

Recommended fix: These are text and test changes inside the author's delegated authority (ruling 17), so the owner is not needed.

1. Decision 8 (plan:233-235): split the failure sentence by hook.
   - Post-link: keep it as it is (status and apply repair it).
   - Pre-unlink, when F or a feature above it cannot be reversed: the message contains `status -v` for F and every feature above it. It is computed during the pre-unlink, while features.d is still complete (link.py:938-953), and lists only the files not back at their pre-feature level, with created files marked.
   - The message then says: once conda has removed <package>, `isabelle-patch-control status` can no longer see these files.
   - Then the restore steps:
     (i) save any of your own edits under isa/;
     (ii) run `conda install --force-reinstall isabelle`. It restores every file conda tracks and discards local edits. On new builds its post-link re-applies the remaining chain; on isabelle-2025.2-0, run `isabelle-patch-control apply` afterwards;
     (iii) delete the listed created files by hand.
   - In decision 6 (plan:212-213), state that unapply stops at the first feature it cannot reverse and never reverses a feature beneath it (REVIEW1:315).

2. Appendix A (plan:445-446): replace the "失败只会留下…status 可见的状态" clause with this: a failed post-link leaves the feature installed but not applied, which status sees and apply repairs. A failed pre-unlink leaves its changes in the tree after the package is gone. status cannot see them. conda's output shows them once, together with the restore steps.

3. §7 row for finding 3 (plan:377): point it to that new bullet. Do not cite ruling 12 as covering the message content.

4. §6 (g) (plan:369): add "when every pre-unlink succeeded". Also move the lock out of isa/, or lock a file conda tracks instead of creating a new one (plan:179-180). The lock file measurably survives `conda remove isabelle` even when every hook succeeds.

5. Decision 14 (plan:304-306): add a hook-layer case. Edit a patched file, then `conda remove` the top feature. Assert that the package is removed and the message lists the modified and created files and the restore steps. Assert that force-reinstall restores the tracked files and that the created file stays until it is deleted by hand.

Optional, and only with the owner's approval because it changes how status works: status compares isa/src with the isabelle package's sha256 records in conda-meta (3548 files, 0.34 s measured) and reports changes that no installed feature explains. Either way, give a reason for "未采用" (not adopted) at plan:394.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed (defender-C8 run.out):
- conda removes the package whatever the pre-unlink returns (link.py:1676-1683);
- afterwards status prints a clean chain while F's edits and created files remain;
- decision 8's remedy (plan:233-235), Appendix A (plan:445-446) and §7 :377 are wrong for this case;
- REVIEW1:305-315 survived unaddressed.

Changes:
- Decision 8: split the failure text by hook. A pre-unlink that leaves files changed writes, computed while features.d is still complete (link.py:938-953):
  - the files not back at their pre-feature level, with created files marked;
  - that status cannot see them once the package is gone;
  - the restore steps: (i) save your own edits under isa/; (ii) `conda install --force-reinstall isabelle`, which restores tracked files, discards local edits and deletes the environment's Isabelle user directory (recipe.yaml:223-231); on 2025.2-0, then run `isabelle-patch-control apply`; (iii) delete the listed created files by hand.
- Appendix A :446 and §7 :377 say this, and stop citing ruling 12 for the message content.
- §6 (g) gets 'when every pre-unlink succeeded', together with C7's lock fix.
- Decision 14: a hook-layer pre-unlink-failure case (user edit, then remove the top feature). Assert the message, that force-reinstall restores the tracked files, and that the created file stays until deleted by hand.
- What unapply does at a CONFLICT file is settled in C5.
- Either adopt the optional paths_data relaxation or give a reason for '未采用' (not adopted) at plan:394.

### C9 [major] Appendix A, the argued exception the owner asked for, states false facts and contradicts decision 11.2; decision 11.1 silently decides whether pack.sh's packaging edits stay, which is a reading of ruling 11

Section: Appendix A (plan:428-448); decision 11 items 1-3 (plan:270-273); §2.3 (plan:95)  ·  merged from: consistency-F6, user-F7, landing-L11, conda-conda-11

**Statement.** Background. Appendix A is the text the owner asked to be written in detail and argued (ruling 14, plan:53). It states several things that are false.
(1) The isabelle package is "byte-identical with the official release; anyone can check this" (plan:439). It is not. pack.sh rewrites etc/settings (the ISABELLE_HOME_USER suffix, pack.sh:184-189), sets ML_system_64 to true in etc/options (:206-211), and drops nunchaku from etc/components (:226-231). The package also ships CI-built heaps (isabelle-packaging-ci/conda/recipe.yaml:3-4, :246-247) and, on Windows, isabelle.bat. The plan itself notes the conda suffix in etc/settings (plan:95).
(2) The principle "post-link creates nothing conda does not track and patches nothing in place" "remains the isabelle package's own principle" (plan:433). But decision 11.2 makes that package's own post-link re-apply features in place (plan:272, :236).
(3) The list of costs omits that feature post-links create files conda does not track, namely light's three created files. That is exactly the objection PACKAGING_DESIGN §3.1 names (PACKAGING_DESIGN.md:48), and rev 1's judge asked for it to be stated (REVIEW1:985-986).
(4) "The tool refuses to run outside conda" (plan:443). Decisions 2 and 7 let it run on any tree, with explicit flags or through the directory interface (plan:146-151, :219-222).
(5) "A failure leaves only a state status can see" (plan:446). That is false for a pre-unlink (C8).
(6) The heading "## 10." collides with PACKAGING_DESIGN.md:1024, "## 10. 相关文档". "§4 的规矩" (the rule of §4, plan:447), read inside PACKAGING_DESIGN, points to its §4, the release pipeline (:518), while the exit-0 rule is RELEASE_CHECKLIST.md §4 (:250, :259).
(7) Decision 11.3 asks only for this section to be added (plan:273). It leaves in place other passages that contradict ruling 11:
- PACKAGING_DESIGN.md:22-30 (§2: apply our patches and hg commit);
- §7.9 at :876 (only user-category patches);
- §7.11 at :940 (the patch tool must be pinned);
- :1027 (the tool repository as the authoritative source of patches);
- the isabelle recipe's own description of a patched Isabelle (isabelle-packaging-ci/conda/recipe.yaml:3, :253-258).

The design gap underneath. Decision 11.1 tells the CI plan what to stop doing (pip install, patches, hg commit; plan:270-271), but not whether pack.sh's three packaging edits stay. That is a reading of the owner's "原版，原汁原味" (pristine, untouched; plan:47), which the plan must not make silently.
- If the edits stay, Appendix A's justification is false as written.
- If they go, the shipped 64-bit heaps no longer match the default word size. pack.sh:200-204 says the ML_system_64 flip "must move IN LOCKSTEP with the heap jobs", otherwise HOL is rebuilt on first use.
Also, feature patches are generated against the git pristine tag but applied to "pristine plus pack.sh's edits". dev_patches' etc/options hunk (@@ -55) is far from line 191 today, but nothing before release checks a feature against the real conda tree (C10).

Required.
- Ask the owner whether "原汁原味" includes dropping the three packaging edits. Recommend keeping them, because the heaps depend on ML_system_64.
- Decision 11.1 lists the edits that stay.
- Rewrite Appendix A: the sources equal the release and etc/ISABELLE_ID is the release changeset; the only differences are the listed packaging edits and the heaps; the isabelle package's own post-link takes part in the exception; the untracked-file cost; non-conda trees are unsupported, not refused; the pre-unlink residue; a correct section number and the RELEASE_CHECKLIST citation.
- Decision 11 lists the other PACKAGING_DESIGN and recipe passages that the CI plan must revise.

**Editor.** Confirmed against pack.sh:184-231 and the section headings of PACKAGING_DESIGN.md and RELEASE_CHECKLIST.md. conda-conda-11's other two items are carried elsewhere: the 0444 fact in C19, and the unnecessary manual apply after a clone in C26.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: True).

I tried to refute each part and could not. All seven factual items hold. The one claim that needs softening is that decision 11 is "silent": it is not silent, it makes an unstated reading of the ruling. That is still the defect.

(1) Byte-identical is false. pack.sh makes three packaging edits:
- it appends the ISABELLE_HOME_USER conda suffix to etc/settings (pack.sh:184-189);
- it flips ML_system_64 to true in etc/options (:206-211);
- it drops the nunchaku-0.5 line from etc/components (:226-231).
On win-64 it also adds bin/isabelle.bat (:159-165). pack.sh's own log lines call these edits "patched etc/settings/options/components" (:189, :211, :231). The heaps are built by CI. The cached isabelle-2025.2-0 ships heaps/polyml-5.9.2_x86_64-linux/{Pure,HOL,Main}. The official bundle has x86_64_32 heaps (PACKAGING_DESIGN.md:212-216) and no Main heap (:246). I diffed the git pristine tree against pkgs/isabelle-2025.2-0/isa and confirmed etc/settings:98 and etc/options:191. The migration plan also records this (ISABELLE_GIT_MIGRATION_PLAN.md:612). Nothing in decision 11 asks the CI plan to remove any of this. Decision 11.1 only drops pip install, patching and hg commit (plan:270-271). So plan:439 is false as written. The parenthetical "(etc/ISABELLE_ID 等于发行版 changeset)" cannot rescue the words "逐字节一致…任何人都能核对".

(2) Self-contradiction. plan:433 says the isabelle package keeps the principle "post-link does not patch in place". But plan:236 and plan:272 make that package's own post-link run a whole-chain apply in place, and plan:445 in the same appendix says so.

(3) The untracked-file cost is missing. Light adds three files: git diff-tree 6d8be01 7983d8a shows 3 A and 29 M (light_locale_axiom_facts.ML, exported_premises.ML, more_exported_premises.ML). Creating files conda does not track is exactly the §3.1 objection (PACKAGING_DESIGN.md:48). The rev-1 judge asked for it to be stated (REVIEW1:985-986). The appendix's cost list (plan:442-447) mentions only modified files. That is a surviving rev-1 defect. The appendix also does not cite the §7.9 precedent the judge listed (PACKAGING_DESIGN.md:881-882).

(4) "工具在非 conda 环境里拒绝运行" (plan:443) is false. Only the defaults are refused (plan:146-151). With --isabelle-home and --features-dir given, the tool runs anywhere. apply-to and unapply-from never look at conda (plan:219-220). Ruling 19 (plan:60) says such trees are unsupported, not refused. What actually keeps a self-installed Isabelle safe is that the hooks pass $PREFIX/isa (plan:148).

(5) plan:446 is false for a failed pre-unlink. conda removes the package anyway (link.py:1676-1683), so features.d/<F> disappears. status only knows the features found in features.d (plan:149-152, :186-193), so F's leftover edits are invisible to it. The rev-1 C10 defender showed this by experiment (REVIEW1:961-965). .messages.txt is still printed, because the hook exits 0 and messages() runs on success (link.py:1684-1708). That part of the sentence is true. "status 可见" is not.

(6) The new section's heading "## 10." collides with PACKAGING_DESIGN.md:1024 "## 10. 相关文档". "§4 的规矩" (plan:447), read inside PACKAGING_DESIGN, points to the release pipeline (:518). The exit-0 rule is RELEASE_CHECKLIST.md §4 (:250, :259).

(7) Decision 11.3 only asks for the appendix to be added (plan:273). Several passages that contradict ruling 11 stay in place:
- PACKAGING_DESIGN.md:22-30;
- §7.9 at :876-878;
- §7.11 at :940-946;
- :1027, which names the old tool as "补丁的权威来源" and directly contradicts appendix item 3 (plan:440);
- recipe.yaml:3, :20 and :253-264;
- recipe.yaml:6-9 ("Nothing … generated by a post-link"), which I found in addition to the challenge's list.
My strongest defense here was plan:71, which puts the CI plan's details out of scope. But decision 11 is the list of what the CI plan must provide (plan:7), and the appendix text is finalized by this plan. So this item survives, though it is the least severe.

The design gap underneath. The plan is not wholly silent. §2.3 (plan:95) records the suffix, and decision 11.4 (plan:274) assumes the etc/settings edit stays. So the plan has quietly read "原汁原味" as "packaging edits stay". It never says this, and it says nothing about ML_system_64 or nunchaku. Ruling 11 says "不带任何补丁", and pack.sh calls these edits patches, so the reading is genuinely ambiguous. Dropping the ML_system_64 flip without changing the heap jobs would leave the shipped heaps at the wrong word size and rebuild HOL on first use (pack.sh:200-204). Under the "ask, don't assume" rule this needs the owner.

The challenge's side point does not bite today. The dev_patches etc/options hunk (@@ -55, commit ab6006e) passes git apply --check, and applies, on the package's real etc/options, which has the flip at line 191/193. The editor gave no relaxation to consider.

Experiment: All work is under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C9/. I modified nothing in any repository.
1. I diffed etc/settings, etc/options and etc/components between /home/qiyuan/Current/MLML/contrib/Isabelle2025-2-pristine and ~/miniconda3/pkgs/isabelle-2025.2-0/isa. Result: the settings line 98 is added (the conda suffix), and options line 191 is false→true. Components are equal, because the nunchaku drop came after 2025.2-0. The package's heaps directory is polyml-5.9.2_x86_64-linux/{Pure,HOL,Main,log}, and its ISABELLE_ID is 5533cd83156e. Saved in pristine_vs_pkg.txt.
2. Read-only `git diff-tree -r --name-status 6d8be01 7983d8a` in the light_locale worktree gives 3 added files and 29 modified files.
3. `git show ab6006e -- etc/options` produced options.patch, whose hunk is @@ -55,6 +55,8. On a copy of the package's etc/options, git apply --check printed CHECK_OK and the apply succeeded. show_types_nv is now at line 58 and ML_system_64 true at line 193.
4. I read conda core/link.py:1665-1708. A failed pre-unlink only logs a warning and returns False, so removal continues. messages() prints .messages.txt after every successful script, pre-unlink included.
5. I checked the section headings of PACKAGING_DESIGN.md (§4 = :518, §10 = :1024) and RELEASE_CHECKLIST.md (§4 = :250, exit-0 rule at :259).

Recommended fix: Smallest fix, in three parts.

(A) Owner question, added to decision 11.1. Ask whether "原汁原味" keeps pack.sh's three packaging edits:
- the etc/settings ISABELLE_HOME_USER suffix (pack.sh:184-189);
- etc/options ML_system_64=true (:206-211);
- the dropped etc/components nunchaku line (:226-231).
Also say that the Windows bin/isabelle.bat and the CI-built Pure/HOL/Main heaps stay. The author should recommend keeping all three edits, for two reasons: ML_system_64 must move in lockstep with the 64-bit heap jobs (pack.sh:200-204), and decision 11.4 builds on the suffix. Once the owner answers, decision 11.1 lists the edits that stay.

(B) Rewrite Appendix A (plan:430-448) by hand:
- plan:439: the sources equal the release and etc/ISABELLE_ID is the release changeset 89701cf1768e. The only differences from the official bundle are the listed packaging edits and the CI-built heaps. Drop "逐字节一致".
- plan:433: the isabelle package still ships everything inside the package. Its own post-link takes part in the exception: when the tool is installed, it calls the tool to re-apply the installed features in place.
- Add a cost: files a feature creates (light creates three) are not tracked by conda; a successful pre-unlink removes them. Cite the §7.9 precedent (PACKAGING_DESIGN.md:881-882).
- plan:443: the hooks hand the tool only $PREFIX/isa. A self-installed Isabelle is unsupported (ruling 19), not refused.
- plan:446: when a pre-unlink fails, the package is still removed and its feature directory goes with it. The edits left in the tree then show only as the .messages.txt notice, not in status. Use whatever repair C8 settles on.
- Number the new section 11, or put it before §10 and renumber. Cite RELEASE_CHECKLIST.md §4 instead of "§4".

(C) Decision 11.3 lists the passages the CI plan must revise:
- PACKAGING_DESIGN.md:20-30 (§2), §7.9 (:876-), §7.11 (:940-), :1027 (§10's tool-as-authority line);
- isabelle-packaging-ci/conda/recipe.yaml:3, :6-9, :20, :212-216, :253-264;
- the pack.sh comments that call Pure "patched" (:172, :386).

**Judge: confirmed → owner_decides.** Confirmed against pack.sh:159-165, :184-189, :206-211 and :226-231, the cached package (etc/settings:98, etc/options:191, the heaps) and PACKAGING_DESIGN.md's headings. Decision 11 reads '原汁原味' as keeping the packaging edits without saying so (plan:95, :274). That reading needs the owner (Q1).

After the answer:
- Decision 11.1 lists the edits that stay, plus the CI-built heaps and the Windows isabelle.bat.
- Rewrite Appendix A by hand:
  - plan:439: the sources equal the release and etc/ISABELLE_ID is 89701cf1768e; the only differences are the listed packaging edits, the heaps and isabelle.bat; drop '逐字节一致' (byte-identical);
  - plan:433: the isabelle package's own post-link takes part in the exception;
  - add the cost: feature-created files are not tracked by conda (light creates three) and are removed by a successful pre-unlink; cite the §7.9 precedent (PACKAGING_DESIGN.md:876-882);
  - plan:443: non-conda trees are unsupported, not refused;
  - plan:446: per C8;
  - use a section number that does not collide with PACKAGING_DESIGN.md:1024, and cite RELEASE_CHECKLIST.md §4 (:250, :259).
- Decision 11.3 lists the passages the CI plan must revise: PACKAGING_DESIGN.md:20-30, §7.9 (:876-), §7.11 (:940-) and :1027; isabelle-packaging-ci/conda/recipe.yaml:3, :6-9, :20 and :253-264; the pack.sh comments that call Pure 'patched'.

### C10 [major] (b2) has drifted from migration §5.1: it runs once instead of before each publication, silently changes copy B's engine, imports the wrong function, cannot run on its pristine base, and names no comparison method

Section: §5 step 4 (plan:353-355); decision 7 (plan:221-222); decision 15.1 (plan:314); decision 9 workflow (plan:253); §6 (plan:363); decision 2 (plan:147-148)  ·  merged from: consistency-F8, landing-L6, user-F9

**Statement.** What the migration plan requires. (b2) runs "before publishing each package" (ISABELLE_GIT_MIGRATION_PLAN.md:403). It takes two copies of the published conda isabelle build:
- copy A gets the make-patches output in features.d and is patched by the tool, in chain order, up to this feature;
- copy B gets `patch -p1 -F0` of `git diff-tree <k-th tag> <feature tag>`.
A must equal B, including mode bits; the tool's unpatch of A must equal the build; and on the first run status must show the real target paths of created files (:403-407).

Rev 2 departs from this in five ways.
(1) Once, not per publication. §5 step 4 runs it once, for the whole chain up to its top (plan:353-355). The reusable release workflow runs "renderer, rattler-build, local-channel acceptance" with no (b2) (plan:253). Rev 1's judge asked for a (b2) script in tools/, required before every feature-package publication (REVIEW1:1915-1933). A maintainer who cuts light 2 has no defined (b2) step.
(2) Copy B silently switches from `patch -p1 -F0` to git apply (plan:354-355). Both copies then share git_apply's failure modes. With C1's enclosing-repository trap, both stay unchanged and (b2) passes without testing anything.
(3) Contradictory code. Decision 7 and decision 15.1 say (b2) imports the low-level git_apply (plan:221-222, :314). But step 4's copy A needs the chain-aware apply that knows LEGACY_BUILDS (plan:353-354). Rev 1's judge ruled for the latter (REVIEW1:1356, :1585).
(4) The pristine leg's base. It runs on "原版 archive" (the git archive of the pristine tag; plan:354). That archive has no etc/ISABELLE_IDENTIFIER: `git ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists 8 files without it, the tag's .gitignore:10 ignores it, and the migration glossary (:16) calls it untracked. The tool reads `<R>` only from that file (plan:147-148, :161), so it refuses copy A. The archive also lacks pack.sh's edits, so it is not the tree (b2) exists to test (C9).
(5) No comparison method and no created-file path check. The migration plan's "including mode bits" needs a method; rev 1's judge named `diff -r` plus sorted `find -printf '%M %p'` listings (REVIEW1:1847). With the lock file (C7) and the mode restoration (C19), the comparison would fail anyway. Also unsaid: how the package directories become a features.d, and how CI reads the private isabelle-patched repository for the diff-tree (RECORD.md:144).

Required. A script in tools/ (named by the author) that:
- assembles a temporary features.d from the package directories;
- runs the chain-aware `python -m isabelle_patch_control --isabelle-home <copy A> --features-dir <dir> apply`, then unapply;
- builds copy B with `patch -p1 -F0`;
- compares content and full modes, and checks the created-file paths that status prints.
It must pass before any feature package is published. It runs on real conda trees, not on git archives: 2025.2-0 from the cache or the channel, and the CI's pristine build from the local channel. Say where it runs and which credential reads the private repository, or that it runs locally on the owner's order.

**Editor.** Confirmed. user-F9 proposes comparing the trees by git tree hash. A tree hash records only the executable bit, which is weaker than the migration plan's "including mode bits" (:405), so keep a comparison of content plus full mode.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

Most of C10 holds. Four of its five parts are confirmed. Part (3), the claimed contradiction about which function (b2) imports, is refuted.

(1) It runs once, not before each publication. CONFIRMED, and it is a rev-1 defect that survived.
- Migration §5.1 requires (b2) "发布包之前" (before a package is published) (ISABELLE_GIT_MIGRATION_PLAN.md:403).
- The rev-1 judge ruled: "Add a (b2) script to tools/ and require it before every feature-package publication" (REVIEW1:1923).
- Rev 2 runs (b2) only in §5 step 4 and in §6 (plan:353-355, :363). It names no script; tools/ has none (`ls tools`, and grep finds no b2). The reusable release workflow runs only "渲染器、rattler-build、本地渠道验收" (renderer, rattler-build, local-channel acceptance) (plan:251-254).
- Ruling 16 (one batch, plan:55) covers only the first batch, and a single run up to the chain top is enough for that batch. Later releases (light 2 and so on) go through that workflow with no (b2). Yet plan:4 claims every confirmed item was absorbed.

(2) Copy B quietly switches from `patch -p1 -F0` to git apply. CONFIRMED.
- Migration :405 says copy B uses `patch -p1 -F0`. Rev 1 kept "裸 patch -p1 -F0" (bare patch -p1 -F0) and "整树（含 mode）相同" (whole tree equal, including mode) (PLAN.rev1.md:294-295).
- Rev 2 changes copy B to git apply (plan:354-355; decision 15.1 "(b2) 同" at plan:314), and no ruling covers this. Ruling 18 is about the tool's engine.
- A fair counterpoint: in the migration plan, copies A and B also shared one engine (the old tool was GNU patch, migration :23-24). So engine independence was not the original goal.
- It matters now because git apply has a silent failure that GNU patch lacks. Measured with git 2.43.0: run inside a subdirectory of an enclosing repository, git apply prints "跳过补丁" (skipping patch), exits 0 and changes nothing. GNU patch 2.7.6 applies the patch in the same place.
- My toy (b2) shows the consequence. With both copies placed in an enclosing repository and both patched by git apply, the result is "A==B yes, A changed no": a pass that tested nothing. With `patch -p1 -F0` for copy B, A and B differ.
- Copy B via git apply also writes rewritten files at the umask: 664 here, because this machine's umask is 002. Copy A restores the original mode, 0644 in pkgs/isabelle-2025.2-0/isa (plan:177-178). So a full-mode comparison fails falsely. GNU patch keeps 644 and 444.

(3) Contradictory code. REFUTED.
- Decisions 7 and 15.1 say (b2) imports git_apply (plan:221-222, :314). That fits copy B's single git apply of the combined diff.
- Copy A goes through the chain-aware tool with LEGACY_BUILDS (plan:353-354). That honours the rev-1 rulings that copy A runs the chain-aware apply and not apply-to (REVIEW1:1355, :1582).
- The two statements complement each other. They become wrong only once copy B returns to GNU patch, and then "(b2) 同" must be reworded.

(4) The pristine leg's base. CONFIRMED.
- `git ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists 8 files, none of them ISABELLE_IDENTIFIER. The tag's .gitignore:10 ignores that file, and migration :16 calls it untracked.
- The tool reads `<R>` only from that file (plan:147-148, :161), so it cannot form the chain bottom on a git archive.
- The obvious workaround also fails. The repository's own writer stores the directory name in that file (tools/common.py:8, :198-199). A copy named A would get "A", which does not match the provenance file's `Isabelle2025-2`, so the tool exits 3.
- The archive is also not the shipped tree. It lacks pack.sh's edits to etc/settings (:188), etc/options (:210) and etc/components (:230). Migration :406 states that (b2) runs on the build itself.
- Step 6 re-runs §6, which includes (b2), but still on "原版 archive" (the pristine git archive) (plan:358, :363). The CI's pristine conda build that will be published never goes through (b2).
- The conda tree does carry etc/ISABELLE_IDENTIFIER, containing Isabelle2025-2.

(5) No comparison method and no created-file check. CONFIRMED, and both were rev-1 judge requirements.
- The rev-1 judge required the method `diff -r` plus sorted `find -printf '%M %p'` listings (REVIEW1:1847). Rev 2 says only "整树相同" (whole tree equal) (plan:355), and it even drops rev 1's "含 mode" (including mode).
- The check that status prints the real target paths of created files on the first run (migration :406-407; REVIEW1:1358) is absent from §6 (plan:363). It is also absent from the pytest list (plan:300-303).
- The lock file breaks "unapply A 回到原状" (unapply A returns it to its original state), plan:355. A flock lock file at DIR/etc/.isabelle_patch_control.lock (plan:179-180) is still there after use; my toy shows "只在 L/etc 中存在：.isabelle_patch_control.lock" (only present in L/etc). Excluding it contradicts migration :406, which says no exclusion list is needed. Deleting it at exit is racy.
- Also unstated:
  - how the repositories' patches/<R>/ become FD/<feature>/ (plan:152, :281);
  - how copy B's `git diff-tree` reads the private isabelle-patched repository (RECORD.md:144-145).

On the editor's rebuttal: I agree to keep content plus full mode rather than the tree hash, but only if the script fixes umask 022.
- Under umask 002, git apply in copy A creates new.sh with mode 775, while GNU patch writes exactly 755 under any umask. So copy A differs from copy B on every created file, whatever engine copy B uses.
- Under umask 022, both give 755 and 644, and rewritten files are 644 on both sides.
- There was no relaxation to weigh.

Experiment: Scratch directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C10/.

(a) trap/: the enclosing-repository case.
- Ran `git apply` (git 2.43.0) inside outer/sub/A, where outer is a git repository. It printed "跳过补丁 'src/f.txt'" (skipping patch), exited 0 and left the file unchanged; `--check` also exited 0.
- Outside any repository the same patch applied.
- With GIT_CEILING_DIRECTORIES set, it applied inside the repository too.
- GNU patch 2.7.6 applied it inside the repository.

(b) e2e/run.sh: a toy two-feature chain and a toy (b2).
- Copies outside a repository, copy B via git apply: A==B yes, A changed yes.
- Copies inside an enclosing repository, copy B via git apply: A==B yes, A changed no. This is a pass that tested nothing.
- Same, but copy B via `patch -p1 -F0`: A==B NO, so the trap is caught.
- `diff -r` reports files that differ only as 444 vs 644 as equal; the sorted `find -printf '%M %p'` listing catches the difference.
- A lock file created with fcntl.flock stays behind: `diff -rq` reports "只在 L/etc 中存在：.isabelle_patch_control.lock" (only present in L/etc).

(c) Mode test (umask here is 002).
- git apply under umask 002 writes rewritten files at 664 and the new file new.sh at 775; under umask 022 it writes 644 and 755.
- GNU patch keeps 644 and 444 and writes 755 under both umasks.

(d) Read-only checks.
- `git ls-tree --name-only Isabelle2025-2/pristine/89701cf1768e etc/` lists 8 files without ISABELLE_IDENTIFIER, and the tag's .gitignore:10 ignores it.
- pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_IDENTIFIER contains "Isabelle2025-2"; the patched files there are 0644 with link count 1.
- pack.sh edits etc/settings, etc/options and etc/components (:188, :210, :230).
- The dev_patches etc/options hunk is at line 55, while pack.sh's edit is at line 193, so today's dev_patches does not collide with it.
- tools/ contains no (b2) script; make-patches:63-66 runs gate (c) with `patch -p1 -F0`.
- The rev-1 plan's lines 294-295 still say "裸 patch -p1 -F0" (bare patch) and "含 mode" (including mode).

Recommended fix: 1. Add one script to tools/ (the author names it).
- Inputs: a conda isabelle tree, the feature package repositories, and the chain top.
- Run under `umask 022`.
- Build features.d: copy each repository's patches/<R>/ to FD/<feature>/.
- Copy A: from the checkout, run `python -m isabelle_patch_control --isabelle-home A --features-dir FD apply`, then `status -v`, and assert that every created file is printed with its `+++ b/` path.
- Copy B: `patch -p1 -F0` of `git diff-tree -r -p --no-renames <chain-bottom tag> <top tag>`, as migration §5.1 says. Because GNU patch does not share git apply's silent skip, a pass that tested nothing becomes impossible.
- Compare A with B: `diff -r` plus sorted `find -printf '%M %p'` listings.
- Then run `unapply` on A and compare it with the original tree the same way.

2. §5 step 4 and §6: run the script on a copy of 2025.2-0, where the chain bottom is the LEGACY tag, and on the CI's pristine build from the local channel, where it is the pristine tag. Delete "原版 archive" (the pristine git archive).

3. Decision 9 and the release checklist: the script must pass, up to the feature being released, before every feature-package publication. It runs locally on the owner's order, because the owner's machine holds the private isabelle-patched repository and the conda cache. Alternatively, the plan names a read-only credential that lets CI read that repository.

4. Decision 7 (plan:221-222) and decision 15.1 (plan:314): replace "(b2) imports git_apply / (b2) 同" with "(b2) runs the tool from the checkout; copy B uses `patch -p1 -F0` (migration §5.1)".

5. Decision 4: the lock file must not stay inside the tree, otherwise "unapply A equals the build" can never hold. This should be coordinated with C7.

**Judge: partially_confirmed → author_decides_then_rereview.** Confirmed parts:
- (1) (b2) runs once, not per publication (migration :403; REVIEW1:1923);
- (2) copy B switches engine silently;
- (4) the git archive lacks etc/ISABELLE_IDENTIFIER and pack.sh's edits;
- (5) no comparison method and no created-file check.
Refuted: (3); decision 7/15.1 and step 4 complement each other.

Add a (b2) script to tools/ (the author names it). It:
- runs under umask 022;
- builds FD/<feature>/ from each repository's patches/<R>/;
- copy A: `python -m isabelle_patch_control --isabelle-home A --features-dir FD apply` from the checkout, then `status -v`, asserting that every created file is shown at its real path;
- copy B: `patch -p1 -F0` of `git diff-tree -r -p --no-renames <chain-bottom tag> <top tag>` (migration §5.1, :405); GNU patch has no silent skip, so a pass that tested nothing is impossible;
- compares with `diff -r` plus sorted `find -printf '%M %p'` listings;
- asserts that A differs from the original;
- runs unapply on A and compares it with the original.

Where and when:
- Run it on a copy of 2025.2-0 and on the CI's pristine conda build. Delete '原版 archive' (the pristine git archive) at plan:354 and §6.
- It must pass, up to the feature being released, before every feature-package publication.
- Say that it runs locally on the owner's order (private isabelle-patched repository, conda cache), or name a read-only credential for CI.
- Fix plan:221-222 and :314 ('(b2) 同').

### C11 [major] isabelle-light-locale cannot be produced by the single template: light also ships a HOL session that declares its commands, and no plan owns how that session is packaged

Section: Decision 9 (plan:242-254); decision 8 (plan:228); decision 14 (plan:309-310); §1 scope (plan:71-72)  ·  merged from: landing-L7

**Statement.** The gap. Decision 9 says a feature package contains only features.d/<feature>/, a README and the two generated hooks, and that the hook text is the same for all packages (plan:228, :249-250). light_locale is also an Isabelle component. contrib/light_locale/ROOT defines `session Light_Locale = HOL` with the theory Light_Locale. That theory declares the commands `light_locale`, `implicit_structure`, `set_implicit_structure` and `with_implicit_structure` (contrib/light_locale/Light_Locale.thy:4-10). A package rendered from the template would carry the Pure patches without the commands users install it for.

Who owns it. The light plan defers distribution to "a separate plan" (LIGHT_LOCALE_PLAN_REV37.md §9: 本期不做，另立计划, not done in this phase). This plan puts the feature projects out of scope (plan:71-72). Yet decision 14 publishes isabelle-light-locale in the batch (plan:309-310). Component packages in this channel ship a session under share/ and register it with `isabelle components -u/-x` hooks (RELEASE_CHECKLIST.md:250-262; Semantic_Embedding/conda/recipe.yaml:261-299). The same question applies to any of the three new features that ships a HOL side.

Required. Decide how a feature's HOL session ships, assign an owner and a step, and drop "all packages are the same" from decision 8 if the template varies. Two shapes:
(a) the template takes an optional component payload: share/<package>/ plus `isabelle components -u/-x` inside the same generated hooks, which then differ per package;
(b) a separate component package that depends on isabelle-light-locale.
Because the choice changes what the owner gets in the batch, put it to the owner.

**Editor.** Confirmed by reading contrib/light_locale/ROOT and Light_Locale.thy.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: True).

I tried to refute C11 on four grounds. None worked.

(1) Maybe the patches themselves carry the commands. They do not. The four user commands are registered only in contrib/light_locale/Light_Locale.thy: keywords at :6-11, Outer_Syntax registrations at :240, :247 and :252. That file belongs to `session Light_Locale = HOL` in contrib/light_locale/ROOT:4-10. No patch file under contrib/light_locale/patches/Isabelle2025-2/ registers any of them; the only hit, src-Pure-Isar-locale.ML.patch:877, is a print label. tools/patched_files.txt lists only src/ files. The light plan says so explicitly: "HOL 侧 contrib/light_locale/ 是新组件、不是补丁" (the HOL side is a new component, not a patch), LIGHT_LOCALE_PLAN_REV37.md:5608 and :7796 item (4). The light private git tree has no Light_Locale theory under src/ (git ls-files), so make-patches cannot produce one either.

(2) Maybe the plan or someone else ships the component. Nothing does. The rev-2 plan never mentions a session, a ROOT, a component or `isabelle components` (I searched the whole plan). Decision 9 limits the payload to features.d/<feature>/, a README and the hooks (plan:249-250). It also requires one template with identical hooks (plan:228) and a rendered, never hand-written recipe (plan:251-252, :282). Light's own plan defers distribution (LIGHT_LOCALE_PLAN_REV37.md:5805). Its recorded direction, "patch files + post-link/pre-unlink" (:7796 item (1)), says nothing about the session. Migration plan §9 lists what is left for this plan, and the component is not on it (ISABELLE_GIT_MIGRATION_PLAN.md:578-584). No conda recipe in isabelle-packaging-ci/conda/{components,metapackage}, Isa-Mini, Semantic_Embedding or Isabelle_RPC references Light_Locale.

(3) Maybe the plan's scope excludes this (plan:71-72). That defence fails. The plan itself renders light's recipe, builds "全部 feature 包" (all feature packages) at §5 step 5 (plan:356), and publishes isabelle-light-locale in the one batch (plan:309-310). Its acceptance scenario (a) installs isabelle-light-locale but checks only `status`, the heap notice and `build -b HOL` (plan:364-365), so it would pass a package without the commands. The plan therefore schedules a defective release and its acceptance cannot detect it.

(4) Experiment. In my scratch directory (/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C11/pkg) I assembled the decision-9 payload for light: 32 patch files plus the README. No file in it registers the light_locale command, and it contains no ROOT or .thy file. The published tree's ROOTS (pkgs/isabelle-2025.2-0/isa/ROOTS) lists only src/* sessions, and its etc/components mentions nothing light-related. The channel's established way to ship a session is a share/<name> payload registered with `isabelle components -u/-x` (RELEASE_CHECKLIST.md:250-267; Semantic_Embedding/conda/recipe.yaml:261-299). Decision 9 has no such slot.

One narrowing, which does not refute the challenge. Its clause "the same question applies to any of the three new features that ships a HOL side" is vacuous today. localized_record declares "不设 session Localized_Record" (no session Localized_Record; LOCALIZED_RECORD_PLAN.md:247-250). local_datatype and local_type_abbrev have only test sessions (LOCAL_DATATYPE_PLAN.md:267-271, :556-559; LOCAL_TYPE_ABBREV_PLAN.md:994-998, :1177-1184). The base features and dev_patches have none (plan:278-287). Only light is affected.

Why it must go to the owner. Ruling 17 delegates only wording and test decisions "在不改设计的前提下" (without changing the design; plan:56-58). The packaging shape changes what the owner gets in the batch, so it is a design decision.

Comparing the two shapes on elegance:
- Shape (a), the template takes an optional component payload, breaks three invariants at once: "hook text identical, one line" (plan:226-228); "tool never runs isabelle / no Cygwin" (plan:147, :228), since `isabelle components` needs the Windows warm-up (RELEASE_CHECKLIST.md:260-266); and the hook would write ISABELLE_HOME_USER/etc/components, which is keyed by the prefix basename (plan:98-100).
- Shape (b), a separate session package that depends on the patch package, reuses the existing session-package convention unchanged and keeps decision 8/9's single template intact.
The editor gave no relaxation to weigh.

Experiment: Everything was read-only except files in my scratch directory.
(1) Read contrib/light_locale/ROOT (lines 4-10) and Light_Locale.thy (lines 6-11, 240-252).
(2) grep over every file in contrib/light_locale/patches/Isabelle2025-2/*.patch for the registration of light_locale, set_implicit_structure or with_implicit_structure: none. The only hit is the print label at src-Pure-Isar-locale.ML.patch:877.
(3) `git ls-files` in contrib/Isabelle2025-2-light_locale (read-only): no Light_Locale theory under src/.
(4) Built the decision-9 payload in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C11/pkg: features.d/light_locale/ holding the 32 patches, plus share/doc/isabelle-light-locale/README.md. grep found no command registration and no ROOT or .thy file.
(5) Read /home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0/isa/ROOTS (src/* only) and etc/components (nothing light-related).
(6) Searched every ROOT, ROOTS and *.yaml under contrib/ (outside the feature repos themselves), and the packaging-ci component and metapackage recipes, for Light_Locale: nothing ships the session.
(7) Read the distribution sections of the light, local_type_abbrev, localized_record and local_datatype plans, and migration plan §9, to see who owns the component: nobody does. Only light has a component session.

Recommended fix: These are the smallest edits that close the gap. None reverses a ruling.

(1) Decision 9, plan:242-254. Add one sentence: "light_locale is also an Isabelle component: session Light_Locale = HOL (contrib/light_locale/ROOT:4-10) declares the commands light_locale, set_implicit_structure and with_implicit_structure (Light_Locale.thy:6-11, :240-252). A package rendered from the template does not carry it. How it ships is the owner's decision, §0 item 20." Record the owner's choice as a new §0 item.

Present the owner two shapes:
- Shape (a): the template takes an optional component payload, share/<package>/ registered with `isabelle components -u/-x` inside the generated hooks. This drops "所有包相同" (all packages the same; plan:228) and the "one line" rule (plan:226). It brings back an `isabelle` call and the Windows warm-up in the hook (RELEASE_CHECKLIST.md:260-266).
- Shape (b), the author's recommendation: a separate session package, built to the existing RELEASE_CHECKLIST §4 convention, that pins the light patch package exactly. Decision 8/9's single template and identical hooks stay true. The owner must also name the package users install, since isabelle-light-locale is already taken by the patch package (plan:244).

(2) §5, plan:356-359. Add the step that builds that package. Add it to the batch list at plan:309-310.

(3) §6, plan:364-365. Extend scenario (a): after `conda install`, a theory importing Light_Locale.Light_Locale that uses `light_locale` checks, on an authorised runner. Otherwise the acceptance passes a package without the commands.

(4) Narrow the challenge's generalisation. State that today only light ships a HOL session; localized_record, local_datatype, local_type_abbrev, the base features and dev_patches have test sessions only. Any later feature with a session follows the same decision.

**Judge: confirmed → owner_decides.** Confirmed:
- contrib/light_locale/ROOT:4-10 and Light_Locale.thy:4-11 carry the commands;
- no patch registers them;
- decision 9's payload (plan:249-250) has no slot for a component;
- no plan owns its packaging, yet plan:309-310 publishes light;
- §6 (a) would pass a package without the commands.
Today only light ships a HOL session.

Put Q2 to the owner. Then:
- record the choice in §0;
- add the build step and the batch entry;
- extend §6 (a): a theory importing Light_Locale.Light_Locale that uses `light_locale` checks, on an authorised runner;
- state that any later feature with a session follows the same decision.

### C12 [major] The release infrastructure for seven publishing repositories is unowned and partly impossible as written: the reusable workflow sits where GitHub cannot call it, and no repo, secret, channel-index entry or shared local channel is assigned

Section: Decision 9 (plan:251-254); decision 12 (plan:276-288); decision 14 (plan:304-310); §5 steps 5 and 7 (plan:356-359)  ·  merged from: landing-L4, consistency-F11, user-F8

**Statement.** What the plan gives. The batch release of ruling 16 needs a working release path for the tool repo and six publishing feature repositories. The plan gives one sentence: tools/release-feature.yml is a reusable GitHub Actions workflow (workflow_call) that each feature repo's workflow calls (plan:252-254).

(1) GitHub can call a reusable workflow only from a repository's .github/workflows/ directory, addressed as `owner/repo/.github/workflows/<file>@ref`. A file under tools/ cannot be called. Every existing caller here addresses .../.github/workflows/publish-conda.yml@main (Isabelle_RPC/.github/workflows/release-conda.yml:320; Semantic_Embedding/.github/workflows/release-conda.yml:464).
(2) The channel already has one shared publish workflow, publish-conda.yml. It keeps the channel-indexing rules "in exactly one place", and both R2 secrets must be set on every calling repo (isabelle-packaging-ci/.github/workflows/publish-conda.yml:1-26). The plan neither says that the new workflow publishes through it nor lists the two `gh secret set CONDA_R2_*` calls per repo. Rev 1's judge asked for exactly that list: per publishing repo, its caller workflow, its secrets, its PUBLISH_REPOS and checklist entries, and who adds light's (REVIEW1:1915-1933).
(3) The repositories do not exist yet:
- local_type_abbrev and local_datatype have no commits, localized_record has one, and none of the three has a remote;
- contrib/isabelle-base-features and contrib/qiyuan_dev_patches do not exist;
- light_locale has a remote but no conda/ and no .github/.
(Checked with `git -C … remote -v`, `git rev-list --count HEAD` and `ls`.)
(4) A per-repo workflow builds only its own package. It cannot assemble the one local channel §6 needs, which holds the tool, seven feature packages and isabelle per platform. No workflow owns that.
(5) rattler-build is not installed on this machine (`which rattler-build` finds nothing), yet step 5 builds the packages locally.

Required.
- A decision modelled on decision 11 that lists, for each publishing repo (tool, isabelle-base-features, light_locale, local_type_abbrev, localized_record, local_datatype, qiyuan_dev_patches): the GitHub repo, created on the owner's order; the caller workflow; the secrets; the PUBLISH_REPOS and checklist entries; and who does each item.
- The reusable workflow lives in the tool repo's .github/workflows/, is called at a tag, and publishes through publish-conda.yml.
- One acceptance workflow, in the tool repo, builds or downloads every package into one local channel per leg.
- rattler-build is listed as a prerequisite of step 5.

**Editor.** user-F8 says the plan "bypasses" publish-conda.yml. The plan is silent rather than contrary. The silence is still a defect, because it leaves the new workflow free to grow a second upload path, against publish-conda.yml's "in exactly one place".

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the five sub-claims. Three hold in full, one holds once restated, and one is not a real defect. The core claim stands, and it is a rev-1 defect that rev 2 did not fix. The rev-1 judge required: "In §5 step 4, list for each publishing repo its caller workflow, its secrets, and its PUBLISH_REPOS entry plus checklist entry (RELEASE_CHECKLIST.md:171-174), and say who adds light's" (REVIEW1:1922). Rev 2 has no such list. No owner ruling (§0 items 11-19, plan:47-60) makes it moot. Ruling 16 (one batch release, plan:55) makes it more urgent.

(1) The workflow's location cannot work. CONFIRMED. Plan:251-253 puts `tools/release-feature.yml` under `tools/` and says the feature repos call it. GitHub's reusable-workflow docs say: "you locate reusable workflows in the `.github/workflows` directory of a repository. Subdirectories of the `workflows` directory are not supported." The only call syntax is `{owner}/{repo}/.github/workflows/{filename}@{ref}`. Every existing caller follows it (Isabelle_RPC/.github/workflows/release-conda.yml:320; Semantic_Embedding/.github/workflows/release-conda.yml:464). The mistake would also slip past review. actionlint 1.7.12, which RELEASE_CHECKLIST.md:323-325 recommends running before every dispatch, accepts `uses: xqyww123/isabelle_patch_control/tools/release-feature.yml@v1.0.0` with exit 0. So the error would surface only when a workflow is dispatched.
A related error, not in the challenge: plan:138 says the GitHub rename keeps working because the old name "自动跳转" (redirects). GitHub's rename docs say: "GitHub will not redirect calls to an action hosted by a renamed repository ... will fail with the error `repository not found`." Reusable workflows are called through the same `uses:` mechanism, so callers must name the final repository. That means the rename has to happen before any caller workflow is written. The rename is in no step of §5 (plan:346-359), and the rev-1 judge asked for it to be scheduled (REVIEW1:1926).

(2) The plan is silent on publish-conda.yml and on the secrets. CONFIRMED, as silence. The plan never mentions publish-conda.yml, a secret, or R2 (grep over the plan: only lines 138, 253-254, 288, 307-309, 356-359 touch release topics). publish-conda.yml:1-26 keeps the channel-indexing rules "in exactly one place". It also needs both CONDA_R2_* secrets set on every calling repo and passed explicitly (also RELEASE_CHECKLIST.md:299-301). The tool's own release (plan:308-309) is covered by reference to RELEASE_CHECKLIST.md. release-feature.yml and its six callers are not covered. I agree with the editor: the plan does not "bypass" publish-conda.yml, but its silence leaves room for a second upload path. There is also a design reason to say it explicitly. publish-conda.yml verifies every .conda in its artifact, not only `package_name` (publish-conda.yml:238-279). So one call can publish several packages, for example isabelle-base-features' two packages, or the whole batch with a single re-index. Seven overlapping per-repo publishes would instead race on repodata.json (publish-conda.yml:31-44).

(3) The repositories do not exist yet. CONFIRMED, once restated. Every fact checks out:
- local_type_abbrev and local_datatype have no commits.
- localized_record has 1 commit; none of the three has a remote.
- contrib/isabelle-base-features and contrib/qiyuan_dev_patches do not exist.
- light_locale has a remote but no conda/ and no .github/.
- `gh repo list xqyww123` (84 repos) has none of isabelle_patch_control, isabelle-base-features, qiyuan_dev_patches, local_type_abbrev, localized_record or local_datatype. Only Light_Locale and the private isabelle-patched match.
Not existing yet is normal before landing; the defect is that nothing assigns their creation. Who owns what:
- The migration plan gives this plan the repos and recipes of expose_foreign, future_assign_interrupt and qiyuan_dev_patches (ISABELLE_GIT_MIGRATION_PLAN.md:166-167). Step 3 creates only local directories (plan:350-352). There is no GitHub repo, remote or secrets step, though creating a repo and setting secrets need the owner's order.
- local_type_abbrev and local_datatype do own their GitHub repos in their own plans (LOCAL_TYPE_ABBREV_PLAN.md:1185; LOCAL_DATATYPE_PLAN.md:561). On that point "unowned" is too strong. But neither plan knows about the caller workflow or the secrets, because both are this plan's invention.
- light and localized_record put distribution off to a plan that does not exist yet ("本期不做，另立计划": LIGHT_LOCALE_PLAN_REV37.md:5805; LOCALIZED_RECORD_PLAN.md:2001). So light's caller still has no producer, which is exactly what the rev-1 judge asked to be named.

(4) Nothing assembles the shared local channel. CONFIRMED, and an experiment strengthens it. Decision 9 gives each repo's workflow its own "本地渠道验收" (local-channel acceptance) (plan:253). §6 needs one channel per runner holding the tool, all seven feature packages and isabelle (plan:363-369), and decision 14 publishes only after all of them pass (plan:309-310). Under ruling 16 nothing is on the channel beforehand. The live conda.qiyuan.me repodata (noarch, linux-64) contains no isabelle-patch-control and no feature package. So a per-repo acceptance cannot even resolve. A toy local channel holding only isabelle-light-locale, plus conda.qiyuan.me and conda-forge, gives `LibMambaUnsatisfiableError: nothing provides isabelle-patch-control >=1.0,<2`. No workflow is named to build or download every package into one channel. One more point: a rebuilt .conda is not byte-identical (RELEASE_CHECKLIST.md:563-565). If the per-repo workflows rebuild at publish time, the bytes that passed acceptance are not the bytes that ship. Where the workflow should live is a design choice. The tool repo works: build.yml is itself callable (build.yml:49) for the new original-release isabelle, and the published 2025.2-0 build is on the channel.

(5) rattler-build is missing. Largely REFUTED as a defect. `which rattler-build` finds nothing. But a 0.68.0 binary sits in ~/miniconda3/pkgs/rattler-build-0.68.0-ha759004_0/bin/. The existing workflows simply curl the static 0.69.1 binary (Isabelle_RPC/.github/workflows/release-conda.yml:92-100), so this is a one-line prerequisite, not a design gap. Step 5 also does not clearly say it builds on this machine. "先用 2025.2-0 的缓存副本" (use the cached 2025.2-0 copy first, plan:357) hints at that, but the acceptance runs on runners (plan:357).

A nearby rev-1 item that also survived: the rev-1 judge said to commit no derived recipe (REVIEW1:1921). Rev 2 commits rendered recipes (plan:282, 288) while also having the workflow run the renderer (plan:253). So it is unclear which recipe gets built, and the committed copy can drift.

Severity stays major: as written, steps 5 and 7 cannot be carried out. On the challenge's "Required" list: "called at a tag" is better than the house convention @main. It only means something if the reusable workflow checks out its own renderer at `job.workflow_sha` (GitHub contexts docs), so that the caller's tag also fixes the renderer version.

Experiment: All in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C12/. I modified no repository and installed nothing.
(a) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C12/repo/.github/workflows/caller.yml has two jobs: one with `uses: xqyww123/isabelle_patch_control/tools/release-feature.yml@v1.0.0`, one with the .github/workflows path. `actionlint` 1.7.12 exits 0 on both, so the plan's path is not caught statically. GitHub docs (docs.github.com, reuse-workflows) say: "you locate reusable workflows in the .github/workflows directory ... Subdirectories ... are not supported". The renaming-a-repository docs say: "GitHub will not redirect calls to an action hosted by a renamed repository". The contexts docs show that job.workflow_repository and job.workflow_sha identify the called workflow.
(b) Read-only state checks:
- `git -C contrib/<repo> remote -v` and `rev-list --count HEAD`: light_locale has 13 commits and an origin; local_type_abbrev and local_datatype have no commits; localized_record has 1 and no remote; isabelle-base-features and qiyuan_dev_patches are missing.
- `gh repo view` / `gh repo list xqyww123 --limit 200` (84 repos): only Light_Locale and the private isabelle-patched exist among the relevant names.
- `ls`: there is no .github/ or conda/ in the tool repo or light_locale.
(c) `curl https://conda.qiyuan.me/{noarch,linux-64}/repodata.json` (saved under .../defender-C12/live/): the isabelle-* names are isabelle-ai, -mcp, -minilang, -performant-ml, -rpc, -semantic-data, isabelle, -nunchaku, -semantic-embedding. There is no isabelle-patch-control and no feature package.
(d) /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C12/mkrepo.py writes a toy noarch channel holding only isabelle-light-locale 1 (depends isabelle-patch-control >=1.0,<2; isabelle >=2025.2,<2025.3; isabelle-future-assign-interrupt ==1=Isabelle2025_2_*). I ran it with private HOME, CONDARC and CONDA_PKGS_DIRS: `conda create --dry-run --override-channels -c file://<toy> -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale` gives LibMambaUnsatisfiableError "nothing provides isabelle-patch-control >=1.0,<2". `find ~/miniconda3/pkgs -newermt '-10 minutes'` is empty, so the owner's cache was not touched.
(e) `which rattler-build`: not found. ~/miniconda3/pkgs/rattler-build-0.68.0-ha759004_0/bin/rattler-build --version prints 0.68.0. Isabelle_RPC/.github/workflows/release-conda.yml:92-100 downloads the static v0.69.1 binary.
(f) Read publish-conda.yml:1-26, 64-80 and 238-279: per-caller secrets, a run-scoped artifact download, and verification of every .conda in the artifact. Read sweep-old-versions.py:61-69 and 212-237: PUBLISH_REPOS is the list of repos whose in-flight runs the sweep checks.

Recommended fix: The smallest fix, as plan edits the author can make:
1. Decision 9, workflow location and publishing:
   - Move the workflow to the tool repo's `.github/workflows/release-feature.yml` and give callers the address `xqyww123/isabelle_patch_control/.github/workflows/release-feature.yml@<tool release tag>`.
   - Have it check out its own tools/ at `job.workflow_sha`, so the caller's tag fixes the renderer version.
   - Say it publishes only by calling `xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml`, with CONDA_R2_ACCESS_KEY_ID and CONDA_R2_SECRET_ACCESS_KEY declared and passed explicitly, never `secrets: inherit` (publish-conda.yml:8-26; RELEASE_CHECKLIST.md:299-301).
   - Decide whether the workflow renders the recipe at build time or uses the committed one, and drop the other (plan:253 vs 282/288; REVIEW1:1921).
2. Add a decision shaped like decision 11 with one row per publishing repo: tool, isabelle-base-features, light_locale, local_type_abbrev, localized_record, local_datatype, qiyuan_dev_patches. Each row gives:
   - the GitHub repo and whether it exists (only the tool's and Light_Locale's do), created on the owner's order;
   - its caller workflow;
   - its two `gh secret set` calls;
   - its PUBLISH_REPOS line plus the checklist's list line (RELEASE_CHECKLIST.md:171-174; sweep-old-versions.py:61-69);
   - who does each item. local_type_abbrev and local_datatype already own their repos (LOCAL_TYPE_ABBREV_PLAN.md:1185; LOCAL_DATATYPE_PLAN.md:561). Name who adds the light_locale and localized_record callers, since both plans defer distribution.
   An alternative the author may prefer for elegance: one batch workflow in the tool repo that checks out each feature repo at its release tag, builds all packages, runs §6, and publishes the same artifact in one publish-conda.yml call. Then only one repo needs secrets and a PUBLISH_REPOS entry, the published bytes are the accepted bytes, and the batch does not race on repodata.json.
3. §5: put the GitHub rename before any caller workflow is written, and delete "旧名自动跳转" (old name redirects) from plan:138 for workflow calls, since GitHub does not redirect such calls.
4. Name one acceptance workflow, in the tool repo, that puts the tool and all seven feature packages into one local channel per runner, with isabelle taken from the published 2025.2-0 build or from a call to build.yml (build.yml:49). State that per-repo acceptance cannot resolve before the batch publish.
5. Step 5: list rattler-build 0.69.1 as a prerequisite, obtained as the existing workflows do (Isabelle_RPC/.github/workflows/release-conda.yml:92-100).

**Judge: partially_confirmed → author_decides_then_rereview.** Confirmed:
- tools/release-feature.yml cannot be called, because reusable workflows must sit directly in .github/workflows/;
- the plan is silent on publish-conda.yml and the R2 secrets;
- repositories, remotes and callers are unassigned (rev-1 REVIEW1:1922 survived);
- nothing assembles the shared local channel; per-repository acceptance cannot resolve before the batch (defender-C12 toy: 'nothing provides isabelle-patch-control').
Also: plan:138's '旧名自动跳转' (old name redirects) does not hold for workflow calls; the rename must come before any caller is written.
Refuted: rattler-build is a one-line prerequisite, not a design gap.

Choose one release shape and specify it fully.
(a) Per-repository callers:
- the reusable workflow lives in the tool repository's .github/workflows/, is called at a tool tag, checks out its own tools/ at job.workflow_sha, and publishes only through publish-conda.yml with both CONDA_R2 secrets passed explicitly (never `secrets: inherit`);
- a decision listing, for each of the seven publishing repositories: the GitHub repository (created on the owner's order), its caller workflow, its two `gh secret set` calls, its PUBLISH_REPOS and checklist lines, and who does each item.
(b) One batch workflow in the tool repository (recommended relaxation): it checks out each feature repository at its tag, builds every package, runs §6 and publishes the same artifact.
In either shape: name the one acceptance workflow that builds or downloads every package into one local channel per leg, schedule the GitHub rename before any caller exists, and list rattler-build 0.69.1 (fetched as the existing workflows do) as a prerequisite.

### C13 [major] The one-batch release names no publication order, ignores the documented race on the channel index between repositories, and ends with no smoke install (rev 1's C19 directive survives)

Section: Decision 14 (plan:308-310); §5 step 7 (plan:359)  ·  merged from: landing-L12

**Statement.** The gap. Ruling 16 asks for one batch, published on the owner's order (plan:55). In practice that batch is about ten publish runs from seven repositories: the tool on conda and on PyPI; expose_foreign; future_assign_interrupt; light; the three new features; dev; and isabelle on five subdirs.

The race. The shared publish workflow documents that publishes from different repositories overlap and race on repodata.json. A losing run pushes a stale index that hides another repo's just-published package until some later publish or a re-run repairs it, and GitHub's `concurrency:` cannot serialise across repositories (isabelle-packaging-ci/.github/workflows/publish-conda.yml:29-43, :288-297).

The ordering hazard. If the runs are dispatched together, the channel can for a while carry light without the future_assign_interrupt it pins, and `conda install isabelle-light-locale` is unsolvable. The plan sets only one ordering rule, the tool's conda package no later than its PyPI upload (plan:310). Rev 1's judge required publication in dependency order and a closing smoke install from the live channel (REVIEW1:1735-1740); rev 2 has neither.

Required. A strictly serial sequence in dependency order:
- the tool on conda (then PyPI, if kept; see C24);
- expose_foreign, future_assign_interrupt, light, local_type_abbrev, localized_record, local_datatype, dev;
- the pristine isabelle last, so that no user can reach it before isabelle-expose-foreign exists.
Each run must be green, including the whole-channel audit, before the next starts. End with a smoke install of isabelle, isabelle-patch-control and isabelle-light-locale from the live channel on every platform, plus `conda update isabelle` in an existing 2025.2-0 environment (C16).

**Editor.** Confirmed against publish-conda.yml:29-43 and :288-297.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute C13 and could not. Every main claim holds. Five details need correcting, and one of them makes the defect worse than the challenge says.

What holds.

1. The plan names no publication order beyond one rule. Decision 14 says only "在本地渠道全部验收通过后，按用户命令一次发布（第 16 条）；工具的 conda 包不晚于 PyPI 上传" (plan:309-310). §5 step 7 says "用户下令一次发布；PUBLISH_REPOS 更新；各仓库的 README 与 AGENTS.md 就位" (plan:359). A search of the plan for 顺序/并发/串行/race/smoke finds nothing else about publishing (the hits are plan:55, 79, 108, 186, 305, 346, 389, 413, none about the release).

2. A dependency order is already an approved rule, so leaving it out goes against more than a reviewer's wish. Migration decision 3 says "发布它的包要求基包已经发布（钉死指向它）" (publishing a package requires its base package to be published already) and "qiyuan_dev_patches 在 local_datatype、localized_record、local_type_abbrev 发布之前不能发布" (ISABELLE_GIT_MIGRATION_PLAN.md:235-238). The owner gave the reason for the straight chain in the same terms: "不然到时候 conda 包 release 的时候依赖顺序都不好协调" (:65). Ruling 16 does not repeal this. It says "D1 的'逐步'不再构成顺序问题" (plan:55; migration :126-127). That clause settles the rev-1 C11 question: whether the tool's patch-removal release had to wait for qiyuan-dev-patches (REVIEW1:994-1066). It also settles the part of the rev-1 judge's C19 ruling that held light back pending the owner (REVIEW1:1740). It says nothing about the mechanical order of the publish runs. A single batch can still go out serially in dependency order, so the rule and the ruling do not conflict.

3. The race is real, and it is silent. The plan never mentions it. publish-conda.yml:29-43 documents the read-modify-write race on repodata.json across repositories, and states that GitHub's `concurrency:` serialises only within one repository. The whole-channel audit (:287-300) claims to turn the interleaving "A uploads, A pulls, B runs to green, A pushes a stale index" into a red run. It cannot, because it walks the run's own pulled snapshot $CH (:301-318), not R2. I replayed the workflow's own step bodies on local directories (experiment below). In exactly that interleaving, both runs' verify and audit steps exited 0, and B's package stayed on R2 while missing from repodata.json. So "each run green" protects nothing when runs overlap. Only serial runs do. A later serial run's audit sees the whole channel and would catch leftover damage. The challenge's "until some later publish or a re-run repairs it" understates this: with both runs green, nobody knows a re-run is needed.

4. Rev 1's directive partly survives. The rev-1 judge required step 4c: publish in dependency order, the tool's conda package first, and "Finish with a smoke install from the live channel" (REVIEW1:1735-1740). Rev 2 adopted 4a and 4b: the local file:// channel and acceptance before publication (plan:307-310, 356-358, 361-369). It dropped both parts of 4c. §6 runs only on the local channel (plan:364).

Corrections.

(a) There are eight repositories, not seven: the tool, isabelle-base-features, light_locale, local_type_abbrev, localized_record, local_datatype, qiyuan_dev_patches and isabelle-packaging-ci. All exist under contrib/. plan:253 says each feature repo has its own workflow.

(b) The statement "No smoke install" is too broad. The `isabelle` package's own release.yml already smoke-installs `isabelle` from https://conda.qiyuan.me on four runners after publishing (release.yml:68-132; matrix :92). Decision 11 does not remove it (plan:270-274). The tool's release goes "按 RELEASE_CHECKLIST.md" (according to the checklist, plan:309), and that file requires a smoke on Linux and Windows (RELEASE_CHECKLIST.md:641-642). What is really missing is a live-channel install of the chain: isabelle plus the tool plus the feature packages. The feature release workflow lists only the renderer, rattler-build, the local-channel acceptance and the publish (plan:253-254). release.yml:71-78 explains why a local-channel pass does not prove that the channel works.

(c) The stated ordering hazard is weak on its own. If light appears before future_assign_interrupt, `conda install isabelle-light-locale` fails at solve time and changes nothing, before anyone has been told the packages exist. The binding reasons for dependency order are the decision-3 rule above and the mechanics of any live-channel check. RELEASE_CHECKLIST.md:400-401: "verify installs from the live channel, so run deps must already be published."

(d) "Isabelle last" is consistent with the plan. Every feature package installs on 2025.2-0 through LEGACY_BUILDS (plan:261-266). Publishing isabelle last therefore needs nothing new, and nobody gets a build without expose_foreign before isabelle-expose-foreign exists. It is necessary but may not be enough. isabelle-semantic-embedding depends only on `isabelle >=2025.2,<2025.3` (Semantic_Embedding/conda/recipe.yaml:318). Its simd_vector.ML uses RunCall (:104, :112), and Performant_Isabelle_ML's rescue_foreign.ML rescues only Foreign (:14-15). Whether that consumer still works on the original build is not established. That question is outside C13 (it is C16's territory) and is unverified here, since I cannot build.

(e) A smoke on "every platform" is more than the minimum. The tool and the feature packages are noarch and share one index. The isabelle-only smoke per subdir already exists. The checklist's minimum is Linux plus Windows, because Windows failures are silent. §6's three runner kinds (plan:307) is the natural choice. The `conda update isabelle` case from 2025.2-0 belongs to C16.

Smaller related point. plan:359 updates PUBLISH_REPOS in the same step as the publication. The sweep's run-listing gate only sees repositories already in that list (sweep-old-versions.py:61-69, 212-237; RELEASE_CHECKLIST.md:152-160). The new repositories should therefore be added before their first publish.

No owner decision is needed. A serial order inside one batch is consistent with ruling 16, and the order itself is migration decision 3. A smoke install is a test detail delegated to the author by ruling 17 (plan:56-58).

Experiment: All work is in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C13/ and is local only: no network, no credentials, nothing installed.

(1) I extracted the step bodies of the real publish-conda.yml with PyYAML into steps/{upload,pull,reindex,push,verify,audit}.sh. The steps are Upload, Pull, Re-index, Push, Verify and Audit. The only change was replacing https://conda.qiyuan.me with file://$R2DIR. shim/rclone is a copy-only `rclone copy` emulator that maps R2:conda to a local directory. Re-indexing uses the real conda_index from ~/miniconda3, run read-only through conda/bin/python.

(2) bz2/ holds toy noarch packages built with mk.py and converted to .conda with conda_package_handling: isabelle-rpc-0.5.1-0 (the seed), isabelle-expose-foreign-1-Isabelle2025_2_0 (run A) and isabelle-future-assign-interrupt-1-Isabelle2025_2_0 (run B).

(3) scenario.sh runs two cases; output is in scenario.out. RACE is the interleaving documented at publish-conda.yml:293-294: A upload and pull, then B's whole run, then A's reindex, push, verify and audit. All twelve steps exited 0. B's audit said "all 3 package(s) indexed" and A's said "all 2 package(s) indexed". The final R2 held 3 .conda files, but repodata.json listed only 2: isabelle-future-assign-interrupt was on the channel but hidden. SERIAL control (A's whole run, then B's) also went all green, and all 3 packages were indexed with none hidden.

(4) Reading only: release.yml:68-132 is the existing live-channel smoke of isabelle alone. RELEASE_CHECKLIST.md:400-401 (dependencies first), :641-642 (Windows smoke) and :152-174 (sweep gate and PUBLISH_REPOS). sweep-old-versions.py:61-69 and :212-237. Migration plan :65, :126-127 and :235-238. REVIEW1:994-1066 (C11) and :1735-1740 (C19 judge). The Semantic_Embedding recipe :318, simd_vector.ML :104 and :112, and rescue_foreign.ML :14-15.

Recommended fix: Rewrite the last bullet of decision 14 (plan:308-310) and §5 step 7 (plan:359) as a release procedure:

1. Before the batch, add every new publishing repository to PUBLISH_REPOS and to the RELEASE_CHECKLIST list. That means the tool's repo, isabelle-base-features, light_locale, local_type_abbrev, localized_record, local_datatype and qiyuan_dev_patches (RELEASE_CHECKLIST.md:171-174).

2. Publish one run at a time. Dispatch the next run only after the previous one is green and its Audit log reads "audited N subdir(s)" (RELEASE_CHECKLIST.md:666). Reason: the cross-repository race on repodata.json (publish-conda.yml:29-43). Under overlap, the audit can be green while a package is hidden (replay above).

3. Publish in dependency order, as migration decision 3 requires (ISABELLE_GIT_MIGRATION_PLAN.md:235-238):
- the tool's conda package, then its PyPI upload;
- isabelle-expose-foreign 1, then isabelle-future-assign-interrupt 1 (one run from isabelle-base-features is fine);
- isabelle-light-locale, isabelle-local-type-abbrev, isabelle-localized-record, isabelle-local-datatype, qiyuan-dev-patches;
- the new original isabelle build last. Every feature package installs on 2025.2-0 through decision 10, so no earlier step needs the new build.

4. After the last run, do one smoke from the live channel (-c https://conda.qiyuan.me -c conda-forge --override-channels, with a private CONDA_PKGS_DIRS). Run it on Linux and Windows at least, or on §6's three runner kinds. Create an env with `isabelle qiyuan-dev-patches`, which pulls the tool and the whole chain. Assert that the post-link hint appears and that `isabelle-patch-control status` shows every feature applied and exits 0. The isabelle-only live smoke already exists in release.yml:84-132 and needs nothing new. Add the `conda update isabelle` case from a 2025.2-0 env only if C16 is accepted.

Optional, in decision 11: ask the CI plan to make publish-conda.yml's whole-channel audit list R2 rather than the run's own snapshot. Today it cannot see the race it was written to catch.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed:
- the plan sets no publication order beyond conda-before-PyPI (plan:310);
- migration decision 3 already requires dependency order (ISABELLE_GIT_MIGRATION_PLAN.md:235-238);
- the cross-repository race is real, and the defender's replay of publish-conda.yml's own steps shows both runs green while one package is hidden. The audit reads the run's own snapshot (publish-conda.yml:301-318), not R2;
- rev-1's live smoke install (REVIEW1:1735-1740) survived unaddressed.
Corrections: there are eight repositories; an isabelle-only live smoke install already exists (release.yml:68-132).

Write a release procedure into decision 14 and §5 step 7:
(1) Add every new publishing repository to PUBLISH_REPOS and the checklist before the batch.
(2) Run one publish at a time; start the next only when the previous one is green, including its audit line.
(3) Order: the tool (conda, then PyPI if Q4 keeps it); expose_foreign; future_assign_interrupt; light; local_type_abbrev; localized_record; local_datatype; qiyuan-dev-patches; the pristine isabelle last.
(4) Then a live-channel smoke install (--override-channels, private CONDA_PKGS_DIRS) on at least Linux and Windows: create an environment with `isabelle qiyuan-dev-patches`; status shows everything applied and the heap notice appears. Add C16's update case.
Optional, in decision 11: ask the CI plan to make the audit list R2.

### C14 [major] The hook-layer test and §6 still expect the wrong conda behaviour on removal and on a failed post-link, and check a .messages.txt that conda has already deleted (rev 1's C20 directive survives)

Section: Decision 14 hook-layer test (plan:304-306); §6 (a)-(c), (f) (plan:364-368)  ·  merged from: conda-conda-10, landing-L5, user-F12, consistency-F14

**Statement.** Four expectations contradict what conda does.
(1) "Removing the top package leaves the rest untouched" (plan:306) is false in the normal case. When only the top package was requested, conda-libmamba's remove also removes the dependency-only feature packages and the tool. It runs their pre-unlinks, which reverse those features (conda_libmamba_solver/solver.py:558-582; RELEASE_CHECKLIST.md:312-313). Measured: critic-conda/run.out scenario C; critic-landing/toy2 envT1; critic-user/run2.out walk d, which also printed three heap notices (all under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).
(2) §6 (a) creates the environment with `conda install isabelle isabelle-light-locale` (plan:364). After (b) removes light, the tool is gone, so (c), "the post-link re-applies and status is unchanged" (plan:366), cannot run in that environment.
(3) "A failing post-link leaves the package installed and the tree unchanged" (plan:305-306) contradicts decisions 6 and 8. The whole-chain apply stops at the first CONFLICT and leaves the lower features applied (plan:209-211; critic-conda/run.out scenario E).
(4) §6 (a), §6 (f) and decision 14 assert on the contents of .messages.txt (plan:305, :365, :368). conda prints and deletes that file after every script (conda/core/link.py:1697-1708), so a check that reads the file sees nothing; it must read conda's output.
Rev 1's judge required the first fix: either request explicitly every package that should stay, or expect the pruning, and document both behaviours and that `--force` removes only the named package (REVIEW1:1845-1846).

Required.
- Create the test and acceptance environments with every package meant to stay requested explicitly, and add one case that asserts the pruning.
- Replace "the tree is unchanged" with the state the design guarantees: the longest applicable prefix of the chain is applied, the failing feature and everything above it are not, and status names the conflict.
- Run each §6 scenario in a fresh environment, or order them so that the tool survives.
- Assert on conda's stdout, not on the file.
- Document the pruning, and `conda remove --force`, in the feature packages' README.

**Editor.** Confirmed against the libmamba source and conda/core/link.py:1697-1708 (messages() prints the file and then deletes it). consistency-F14 contributes only its §6 (b) point here; its other parts are in C18 and C23.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

Four claims are in the challenge. Three of them, and the surviving rev-1 directive, are confirmed. They live in decision 14's hook-layer test and in the missing documentation. The title's claim that "§6 still expects the wrong behaviour on removal and on a failed post-link" is mostly refuted.

(1) Pruning on removal: confirmed for decision 14, refuted for §6 (b).
- Decision 14 asserts "卸顶层包后其余不动" (removing the top package leaves the rest untouched, plan:306). This is false whenever only the top package was requested.
- conda-libmamba keeps only packages named in the env history (conda_libmamba_solver/solver.py:566-571). It removes the requested specs "and their deps" (:573-580). The project's own checklist records the same effect (RELEASE_CHECKLIST.md:312-313).
- Three independent toy runs removed the lower feature packages and the tool, and ran their pre-unlinks in reverse chain order:
  - review-ipc2/critic-conda/run.out, scenario C: INSTALLED afterwards is just isa-1.0-0;
  - critic-landing/toy2/run/T1-remove.log, which lists fe, ff, fl and ipc as REMOVED;
  - critic-user/run2.out:106-126.
- Rev 1's judge required two things (REVIEW1:1845-1846). First, either create the env with every package that should stay requested explicitly, or expect the pruning. Second, document both behaviours and that `--force` removes only the named package. Rev 2 does neither. It never mentions pruning or `conda remove --force` (grep finds `--force` only for the tool's own flag, plan:142, :215). Appendix A point 1 (plan:437-438) presents the solver as an asset and says nothing about it. This rev-1 defect survived.
- However, rev 2 did fix §6 itself. Rev 1 expected "status 剩两行" (two rows remain, rev1:297). Rev 2's (b) expects only "light 反打干净，新建文件消失" (light reversed cleanly, created files gone, plan:365-366). That still holds under pruning: scenario C's tree ends pristine with new.ML absent. So the false expectation moved from §6 into decision 14's test.

(2) The §6 ordering: an ambiguity, not a contradiction.
- (b) clearly runs in (a)'s env. Nothing says (c) runs in (b)'s.
- (e) needs a separate 2025.2-0 env (plan:367-368), so §6 is a list of scenarios, not one script.
- Still, a sequential reading of (c) after (b) is vacuous. Isabelle's post-link is guarded by `[ -x tool ]` (plan:236), and the tool has been pruned. One sentence fixes this.

(3) "post-link 失败时包装着、树不变" (on a failed post-link the package stays installed and the tree is unchanged, plan:305-306): confirmed as a general claim.
- Decision 6 applies in chain order and stops at the first CONFLICT (plan:209-210). So any transaction that also brings lower features leaves those applied.
- Measured in critic-conda/run.out scenario E: the tree is changed, with a.ML applied.
- My own git-apply simulation of decision 6's loop shows both sides (defender-C14/exp):
  - Case 1, a fresh transaction bringing fa and fbad: the tree is CHANGED.
  - Case 2, only the conflicting feature is new: the tree is unchanged.
- "Tree unchanged" holds only in case 2, or for exit-2/exit-3 failures that happen before any apply. It looks like rev 1's defender wording for a rollback design, carried over into rev 2's exit-0 design.
- Decision 8's own wording "包装着、feature 未打" (package installed, feature not applied, plan:234-235) and §6 (f) (plan:368-369) are correct.

(4) Asserting on `.messages.txt`: confirmed, but minor.
- `messages()` prints the file and then deletes it in a finally block (conda/core/link.py:1697-1708). It is called after every script: at :1685 on success and at :1648 on failure.
- The toy hooks append to the file (critic-conda/mkchan.py:30). conda printed those lines, and afterwards no `.messages.txt` exists in envs/e or envs/c.
- The plan itself knows that conda displays the content (plan:104-105). So this is a matter of naming the right thing to assert on, at plan:305, :365 and :368, not a design flaw.

Severity: each fix is a test-setup or wording edit. Calling it "major" is defensible only because a rev-1 directive survived.

Experiment: Scratch dir: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C14/exp

Toy tree: a.ML and b.ML. Patches came from a private git repo: fa changes a2 to A2, fbad changes b2 to B2. A user edit (b2 to USER) makes fbad conflict. I simulated decision 6's apply loop with real git 2.43.0 `git apply --check`, `-R --check` and apply, in chain order, stopping at the first CONFLICT.
- Case 1, a fresh transaction bringing fa and fbad: fa applied, fbad CONFLICT, tree CHANGED (a.ML sha differs).
- Case 2, fa already applied and only fbad new: tree unchanged.

I also re-read existing evidence:
- critic-conda/run.out: scenario C shows pruning, scenario E shows a applied with bad CONFLICT.
- critic-landing/toy2/run/T1-remove.log and hook-T1.txt: fe, ff, fl and ipc REMOVED, pre-unlinks fl, ff, fe.
- critic-user/run2.out:106-126: fa, fb, fc and the tool removed, three heap notices.
- No `.messages.txt` remains in critic-conda/run.K9Am/envs/{c,e} after the transactions.

Sources read:
- conda/core/link.py:1640-1708 (messages() calls rm_rf in finally);
- conda_libmamba_solver/solver.py:558-582;
- RELEASE_CHECKLIST.md:312-313;
- rev 1 plan :297 compared with rev 2 plan :364-369;
- REVIEW1:1742-1850.

Recommended fix: These are the smallest edits, all within the author's delegated authority over wording and tests (plan §0 item 17, :56-58).

1. Decision 14 (plan:304-306): replace "卸顶层包后其余不动" (removing the top package leaves the rest untouched) with three cases:
   - (i) The env is created requesting `isabelle isabelle-patch-control` and every feature package. Removing the top runs only the top's pre-unlink, and the other features stay applied.
   - (ii) The env is created requesting only `isabelle` and the top. Removing the top also removes the dependency-only feature packages and the tool. Their pre-unlinks run in reverse chain order while the tool is still present, and the tree ends at the chain bottom.
   - (iii) `conda remove --force <top>` removes only the top.

2. Replace "post-link 失败时包装着、树不变" (on a failed post-link the package stays installed and the tree is unchanged) with: "post-link 遇到 CONFLICT：包都装着；冲突 feature 之下的按链序打上，冲突的 feature 及其之上不动；status 点名冲突". In English: when a post-link hits a CONFLICT, the packages stay installed; the features below the conflicting one are applied in chain order; the conflicting feature and the ones above it are left untouched; status names the conflict. Optionally keep "树逐字节不变" (tree byte-identical) only for the case where the conflicting feature is the sole unapplied one, as the atomicity check.

3. At plan:305, :365 and :368, say "conda 的输出里有…" (conda's output contains …) instead of "`.messages.txt` 有…" (`.messages.txt` contains …). Note that conda prints the file after each script and then deletes it (conda/core/link.py:1697-1708). The test asserts on the conda command's captured stdout.

4. §6: add one sentence saying that each scenario starts in a fresh env built the way case (i) of fix 1 builds it, or else that (c) runs before (b).

5. Add one paragraph to the feature packages' README (decision 9's share/doc/<包名>/README.md, the README inside each feature package) and to the tool README. It should say three things: removing a feature package also removes and reverses the dependency-only lower features and the tool; `conda remove --force <pkg>` removes only that package; and `conda install` on an already-installed package does not mark it as requested.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- decision 14's 'removing the top package leaves the rest untouched' (plan:306) is false under libmamba pruning (solver.py:558-582);
- 'tree unchanged on a failed post-link' (plan:305-306) contradicts decision 6's stop rule;
- asserting on the .messages.txt file is impossible, because conda deletes it (link.py:1697-1708);
- rev-1's pruning documentation (REVIEW1:1845-1846) is missing.
Refuted: §6 (b) itself (plan:365-366) still holds under pruning.

Changes:
- Hook-layer test cases:
  (i) every package that should stay is requested explicitly; removing the top runs only its own pre-unlink;
  (ii) only isabelle and the top are requested; the dependency-only features and the tool are pruned, their pre-unlinks run top-down while the tool is present, and the tree ends at the bottom;
  (iii) `conda remove --force <top>` removes only the top.
- Replace 'tree unchanged' with: the features below the conflicting one are applied, the conflicting feature and those above it are untouched, and status names the conflict.
- Assert on conda's captured stdout at plan:305, :365 and :368.
- §6: each scenario starts in a fresh environment built as in (i), or (c) runs before (b).
- The feature-package README and the tool README document pruning, --force, and that installing an already-installed package does not mark it as requested.

### C15 [major] The acceptance cannot run as scheduled: step 5 requires a §6 pass that needs the pristine build only step 6 produces, no step owns the joint run with the CI plan, and only three of the five conda platforms are covered

Section: §5 steps 5-6 (plan:356-358); §6 (plan:364-369); decision 14 (plan:307); decision 8 (plan:237-238)  ·  merged from: landing-L3, landing-L16

**Statement.** Ordering. Step 5's exit criterion is that §6 passes on three runners, using the pristine isabelle build "once the CI plan has landed, or the cached copy of 2025.2-0 for now" (plan:356-357). §6 (a) and (c) need the new pristine build (plan:364-366). On 2025.2-0, (c) cannot pass by design, because its post-link never calls the tool (plan:237-238). So step 5 cannot meet its own criterion, and step 6 then reruns §6 (plan:358). In the other direction, the CI plan must verify its new post-link line (decision 11.2) against the tool and feature packages that step 5 builds, and neither step owns that joint run.

Where the packages come from. The only local isabelle package is linux-64 (subdir in pkgs/isabelle-2025.2-0/info/index.json). The macOS and Windows legs must therefore take 2025.2-0 from the live channel, and the pristine build from a CI run's artifacts, because the CI publishes nothing from Job F (build.yml:10-14, :1096-1109). The plan says neither.

Coverage. Ruling 18 requires all five platforms (plan:59), but decision 14 runs three legs (plan:307). packaging-ci already executes all five subdirs: Job G runs osx-arm64 natively and osx-64 through Rosetta on macos-14, and Job H runs linux-aarch64 on ubuntu-24.04-arm (isabelle-packaging-ci/.github/workflows/build.yml:1120-1127; release.yml:92 lists four runners). The git package differs per subdir (plan:114-115), so git_apply's behaviour must be checked per subdir.

Required.
- Step 5 runs only the hook-layer tests and the 2025.2-0 scenarios.
- One joint acceptance runs after step 6. Each leg uses one local channel holding the tool, every feature package, the CI's pristine build for that subdir (named by its workflow run) and 2025.2-0 from the live channel. This run also verifies decision 11.2.
- Say which repository's workflow runs it (C12).
- One leg per conda subdir, with osx-64 through Rosetta as Job G does.

**Editor.** Confirmed against build.yml:1120-1127 and release.yml:92.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each of the challenge's three parts. One clause is refuted, the rest survive in a weaker form, and the severity drops from major to minor. Nothing unverified can ship, because step 7 (publication, plan:359) comes after step 6's full rerun of §6 (plan:358).

1. Ordering: partly confirmed.
- Step 5 offers a fallback: "原版 isabelle 包（需 CI 计划落地，或先用 2025.2-0 的缓存副本）", and requires that "§6 验收在三种 runner 上通过" (plan:356-357). The CI plan only lands in step 6 (plan:358), so step 5 has only 2025.2-0.
- On 2025.2-0, scenario (c) cannot pass. It names "(新原版构建)" explicitly (plan:366), and decision 8 says the 2025.2-0 post-link never calls the tool (plan:237-238).
- Scenario (a)'s "链上各 feature applied" (plan:364-365) is also false on 2025.2-0, where expose_foreign reads pre-applied (plan:193, 263-264).
- So step 5's exit criterion cannot be met as worded. That is a wording defect, not an ordering hazard: "先用" plus step 6's "重跑 §6" already marks step 5 as provisional.
- One side note against the challenge: scenario (d) does run on 2025.2-0. `clone_env` copies the untracked files and then calls `explicit(...)` on every package (conda misc.py:274-357). That runs every feature package's post-link, so the feature post-links re-apply the chain without a manual step, even though plan:238 says a manual apply is needed after a clone.

2. "Neither step owns the joint run": refuted.
- Step 6 says "产出新的原版 isabelle 构建进本地渠道，重跑 §6" (plan:358). That local channel already holds step 5's tool and feature packages.
- §6 (c) (plan:366) is exactly the test of decision 11.2's post-link line with the tool installed.
- The other case, the same line with no tool installed, is already exercised by packaging-ci's own install jobs, which install `isabelle` alone (build.yml:1203, 1216-1217, 1286). The line's `[ -x ]` test fails harmlessly there, because the post-link ends with `exit 0` (recipe.yaml:208).
- Which repository's workflow runs the acceptance is C12's question, not this one's.

3. Where the packages come from: confirmed as a gap in the plan's text.
- The local cache holds only linux-64: pkgs/isabelle-2025.2-0/info/index.json has "subdir": "linux-64".
- The live channel has isabelle-2025.2-0 in all five subdirs (my probe).
- Job F only uploads an artifact, with retention-days: 7, and publishes nothing (build.yml:10-14, 1108-1114).
- So "2025.2-0 的缓存副本" is wrong for the macOS and Windows legs, and the plan does not say where step 6's new pristine build comes from.
- One more fact, not raised by the challenge: release.yml rebuilds everything instead of promoting artifacts (release.yml:9-11). The published pristine build is therefore a rebuild of the one accepted in step 6. That is acceptable, because the ISABELLE_ID (89701cf1768e, decision 11.1) and the post-link text both come deterministically from the recipe.

4. Coverage: partly confirmed.
- What survives: the plan's justification "packaging-ci 已有这三种" (plan:307) is factually incomplete. packaging-ci installs and runs all five subdirs on four runners: Job G runs osx-arm64 natively and osx-64 through Rosetta on macos-14, and Job H runs linux-aarch64 on ubuntu-24.04-arm (build.yml:1121-1127, 1199-1218, 1249-1287). The Windows heaps are built on windows-latest (build.yml:676), and release-nunchaku.yml:82-88 already uses five native runners, including macos-15-intel.
- What is refuted: three legs is not a misreading of ruling 18.
  - Ruling 18 was option (c) of the rev-1 question 7, and that option described its testing cost as "a windows-latest leg" (REVIEW1:90).
  - Ruling 17 hands test decisions to the author (plan:56-58).
  - The claim that git_apply "must be checked per subdir" is overstated. conda-forge git is 2.56.0 in all five subdirs, built from the same source. The tool is noarch python, and the .sh hook is the same file on all four unix subdirs.
- Still, the two extra legs cost almost nothing, since packaging-ci already runs them. Given ruling 18 and the owner's rule to verify rather than assume, adding them is the better choice.

Experiment: All probes were read-only. The script is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C15/probe.sh and its output is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C15/probe.out.
(1) /home/qiyuan/miniconda3/pkgs/isabelle-2025.2-0/info/index.json reads "subdir": "linux-64", "build": "0", so the only local copy is linux-64. pkgs/urls.txt shows it was fetched from https://conda.qiyuan.me/linux-64/.
(2) The live channel's repodata.json for linux-64, linux-aarch64, osx-64, osx-arm64 and win-64 each lists isabelle-2025.2-0.conda; noarch lists none.
(3) The api.anaconda.org listing of conda-forge git gives 2.56.0 as the newest version for all five subdirs.
Source reads:
- build.yml:10-14, 1108-1115 (artifact only, 7-day retention), 1117-1137, 1139-1218 (Job G, including CONDA_SUBDIR=osx-64 with `arch -x86_64`), 1249-1287 (Job H), 676 (windows-latest heaps).
- release.yml:9-11 (rebuild rather than promote) and :92 (smoke runners).
- release-nunchaku.yml:82-88 (five native runners).
- isabelle recipe.yaml:194-209 (the post-link ends with `exit 0`).
- conda misc.py:274-357 (a clone runs `explicit()` over every package, so every post-link runs).
- REVIEW1:84-90 (the options behind ruling 18).
- plan:56-59, 193, 237-238, 263-264, 307, 356-369.

Recommended fix: These are text and test edits only; all are within the author's delegation under ruling 17.
(1) §5 step 5 (plan:356-357): replace "§6 验收在三种 runner 上通过" with "钩子层测试全绿，§6 中不需要新原版构建的场景在 2025.2-0 上通过（(a) 按 expose_foreign 为 pre-applied 读，(b)(d)(e)(f)(g)）；(c) 留到第 6 步".
(2) §5 step 6 (plan:358): name where each package comes from. The new pristine build is the `conda-packages` artifact of a named packaging-ci workflow run (build.yml:1108-1114; it is kept 7 days, so rerun or re-download if it expires). On legs other than linux-64, 2025.2-0 comes from conda.qiyuan.me, because the local cache has only linux-64. Then require that all of §6 passes with both builds in the channel. Optionally add one line saying that release.yml rebuilds rather than promotes (release.yml:9-11), and that this is acceptable because the ISABELLE_ID and the post-link text come deterministically from the recipe.
(3) Decision 14 (plan:307): correct "packaging-ci 已有这三种" to say that packaging-ci runs all five subdirs (build.yml:1121-1127). Run one leg per subdir: linux-64 on ubuntu-latest, linux-aarch64 on ubuntu-24.04-arm, osx-arm64 natively and osx-64 through `CONDA_SUBDIR=osx-64` plus `arch -x86_64` on macos-14 as Job G does, and win-64 on windows-latest.
No change is needed for joint-run ownership, which step 6 already carries. The question of which repository's workflow runs the acceptance belongs to C12.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- step 5's exit criterion cannot be met on 2025.2-0: (c) needs the new build (plan:237-238, :366), and (a) reads expose_foreign as pre-applied;
- the cache holds only linux-64 (pkgs/isabelle-2025.2-0/info/index.json);
- Job F only uploads a 7-day artifact (build.yml:1108-1114);
- plan:307's 'packaging-ci has these three' is incomplete: it runs all five subdirs (build.yml:1121-1127).
Refuted: the joint run is owned by step 6.

Changes:
- Step 5: the hook-layer tests, plus the §6 scenarios that do not need the new build, on 2025.2-0 ((a) with expose_foreign read as pre-applied; (b), (d)-(g)). (c) moves to step 6.
- Step 6: name where each package comes from: the CI artifact of a named run, re-downloaded or re-run if it expires; on legs other than linux-64, 2025.2-0 from the live channel.
- Decision 14: one leg per conda subdir (five), osx-64 through Rosetta as Job G does. Ruling 18 makes this cheap and the right default.
- The legs use the git that the tool's conda package resolves to (conda-forge 2.56 today, not the 2.43 measured here). The Windows leg checks where git.exe lives.

### C16 [major] The transition every existing user makes, `conda update isabelle` from 2025.2-0 to the pristine build with features installed, is never tested, and users who rely on Foreign get no release note

Section: §6 (plan:364-369); decision 14 hook-layer test (plan:306); decision 10 (plan:263-266); decision 13 (plan:293-295)  ·  merged from: user-F11

**Statement.** Why this path is special. After the batch release, every existing user on isabelle-2025.2-0 reaches the new build through `conda update isabelle` or `conda update --all`. It is the only path on which the bottom of the chain switches from the LEGACY_BUILDS entry (expose_foreign pre-applied) to the pristine tag, with expose_foreign now applied by the tool. The steps are:
1. the old build's pre-unlink deletes the user directory (isabelle-packaging-ci/conda/recipe.yaml:223-231) and does not call the tool;
2. conda unlinks the old tree's files and links the new ones, leaving light's created files behind;
3. the new build's post-link applies the whole chain from pristine (plan:236).
This works only once C3's and C5's rules are in place.

What is tested. §6 covers a force-reinstall of the new build (c), a clone (d) and features on 2025.2-0 (e), but never this update. The toy test "the post-link re-applies after the isabelle package changes" (plan:306) does not exercise the switch away from a LEGACY_BUILDS entry.

Users who call Foreign in their own ML. Users on 2025.2-0 without feature packages lose expose_foreign silently on this update, because the new post-link's guard is false. Ruling 11 accepts that consequence, but no release note tells them to install isabelle-expose-foreign. Ruling 13's README note covers only the manual apply, and without the patch "any ML file touching the FFI fails to compile" (my_better_isabelle_prover/patches/expose_foreign.md).

Required.
- A §6 case and a hook-layer case, the latter with a toy legacy ID in LEGACY_BUILDS: start from 2025.2-0 with isabelle-light-locale applied, run `conda update isabelle` to the pristine build, and expect status to show applied (no longer pre-applied) for expose_foreign, applied for future_assign_interrupt and light_locale, and the heap notice in conda's output.
- A release note in the README and in the new isabelle package's description: expose_foreign is now the package isabelle-expose-foreign.

**Editor.** user-F11 also notes that nobody inside this ecosystem still needs expose_foreign, because Performant_Isabelle_ML re-binds Foreign. That is correct, and it is the reason consistency-F1 is dropped.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

Two parts of C16 hold: §6 has no case for the update itself, and no release note exists. The challenge's main argument does not hold: this update is not special for the tool, and it is not a major risk.

CONFIRMED (1): §6 has no case for a build change of `isabelle`.
- §6 (a)-(g) (plan:364-369) cover a fresh install, a remove, a force-reinstall of the new build (c), a clone (d) and features on 2025.2-0 (e). None of them runs `conda update isabelle`.
- The rev-1 judge required this case. C1 item (5) asks for "pytest and §6 cases for a build bump, a force-reinstall and a clone" (ISABELLE_PATCH_CONTROL_REVIEW1.md:264). Rev 2 kept two of the three and dropped the build bump. This is a rev-1 requirement that survived unaddressed.
- After the batch release, the only real build bump is 2025.2-0 to the new pristine build, which is exactly the update C16 names.
- The hook-layer item "换 isabelle 包后 post-link 重打" (plan:306) does not say which two toy builds it uses.

CONFIRMED (2): no release note.
- Ruling 13's README note covers only the manual `apply` after force-reinstall or clone (plan:52, :238).
- Decision 11 (plan:268-274) asks the CI plan for no user-facing note. Decision 13's "Coming from my-better-isabelle 0.x" section (plan:293-295) sits in the tool's README, which a user without the tool never reads.
- Experiment S3: an environment with only 2025.2-0, after `conda update isabelle`. `hidden_structures` goes from ["Signal"] back to all four structures. conda's output says only "Isabelle is installed." and mentions Foreign zero times.

REFUTED OR OVERSTATED (a): the update is not special for the tool.
- The tool keeps no ledger and works out its state fresh on every run (plan:394, :423). During the update only isabelle's own hooks run (plan:106-107). My toy hook log shows exactly "pre-unlink isabelle 5533cd83156e" and then "post-link isabelle-1".
- The old pre-unlink has the same text as the recipe's pre-unlink: pkgs/isabelle-2025.2-0/bin/.isabelle-pre-unlink.sh against isabelle-packaging-ci/conda/recipe.yaml:223-230. Decision 11 keeps it unchanged (plan:272).
- So the new build's post-link sees the same input as in §6 (c). I snapshotted isa/ at that post-link in both runs. Paths and modes are identical. The only difference in content is etc/ISABELLE_ID.c~, a temporary copy conda keeps of each removed file and deletes after the transaction (conda/core/path_actions.py:1152-1164). The tool never reads it.
- The final trees are identical (modes, paths, sha256), and so are the features.d directories.
- No tool run ever sees the chain bottom change from the 2025.2-0 record to the pristine tag. §6 (c) already runs the same computation. The update did work with the plan's rules: status went from "pre-applied, applied, applied" to "applied ×3", and the heap notice appeared in conda's output.
- The required "toy legacy ID in LEGACY_BUILDS" needs no test-only hook. A toy build can simply carry the real ID 5533cd83156e, as mine did.

REFUTED OR OVERSTATED (b): who loses Foreign.
- Every 2025.2-0 user with any feature package already has isabelle-expose-foreign, because each feature package pins its base package (plan:248). In my toy run conda-meta lists it after `create isabelle=2025.2=0 isabelle-light-locale`.
- So only users without any feature package lose Foreign. Ruling 11 accepts that.
- The failure is a compile error ("Structure (Foreign) has not been declared"), not silent damage. It just carries no hint about the fix.

REFUTED OR OVERSTATED (c): the editor's rebuttal holds for every session the ecosystem ships.
- Performant_Isabelle_ML v0.2.0+ puts Foreign back itself (library/rescue_foreign.ML:27-38). Isabelle_RPC imports it (Remote_Procedure_Calling.thy:2). Semantic_Embedding needs isabelle-performant-ml >=0.2.0 (conda/recipe.yaml:338).
- simd_vector.ML's RunCall uses are commented out (Tools/simd_vector.ML:101-114).
- Older isabelle-semantic-embedding 0.1.2-0.3.0 with performant-ml 0.1.0 has no such rescue. The owner's own envs `isabelle` and `isabelle-2` run that combination. Even there, simd_vector.ML is loaded only by Sledgehammer_Embedding.thy, which the shipped ROOT does not list (pkgs/isabelle-semantic-embedding-0.3.0-hb0f4dca_0/info/recipe/recipe.yaml:203-206).
- So only users who load that theory explicitly, or who write their own FFI code, are affected.

Severity: minor. Both gaps fall under wording and test decisions, which ruling 17 delegates to the author.

Experiment: Directory: /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C16/

Files:
- src/ipc.py: a prototype tool that keeps no state. It implements:
  - decision 3: the chain linked by exact tags;
  - decision 5: a level for each file, by replaying its patches with git apply; a created file that is present with the patch's exact content counts as both applied and not-applied;
  - decision 6: whole-chain apply, and unapply;
  - decision 8: conda-hook, always exit 0, reporting through .messages.txt;
  - decision 10: LEGACY_BUILDS = {"5533cd83156e": expose_foreign/1}.
- src/mkchan.py: builds a toy file:// channel.
  - A toy git repository with tags pristine/89701cf1768e, expose_foreign/1, future_assign_interrupt/1 and light_locale/1. light edits ml_name_space.ML too, edits locale.ML and creates a file.
  - Per-file patches from `git diff-tree -r -p --no-renames`.
  - isabelle build 0: the expose_foreign tree with ID 5533cd83156e. isabelle build 1: the pristine tree with ID 89701cf1768e; its post-link takes a snapshot of isa/ and then runs the guarded tool line from plan:236. Both builds have the same pre-unlink.
  - The tool package, and three feature packages with the plan's pins and one-line hooks.
- src/run.sh: runs conda 25.11.1 with a private HOME, CONDARC and CONDA_PKGS_DIRS, envs created with -p. Output is in run.out; logs and snapshots are in run1/.

Results:
- S1, the update C16 names: `create isabelle=2025.2=0 isabelle-light-locale`.
  - status: pre-applied expose_foreign, applied future_assign_interrupt, applied light_locale.
  - `conda update isabelle`: conda printed "isabelle 2025.2-0 --> 2025.2-1".
  - Hooks that ran: only "pre-unlink isabelle 5533cd83156e" and "post-link isabelle-1".
  - status after: all three applied.
  - conda's output contained the heap notice.
- S2, the same as §6 (c): build 1 plus light, then `--force-reinstall isabelle=2025.2=1`. Same hooks, same final status.
- The isa/ snapshot taken at the build-1 post-link has identical paths and modes in S1 and S2. The only content difference is conda's temporary copy etc/ISABELLE_ID.c~. The final trees are identical (modes, paths, sha256), and so are the features.d directories.
- S3: build 0 alone, then `conda update isabelle`. hidden_structures reverts to all four structures. conda's output is only "Isabelle is installed." and mentions Foreign 0 times.

Read-only checks:
- pkgs/isabelle-2025.2-0: the pre-unlink script, etc/ISABELLE_ID 5533cd83156e, ml_name_space.ML:67 = ["Signal"].
- index.json `depends` of the cached semantic-embedding 0.1.2/0.2.0/0.3.0 (performant-ml <0.2.0) and performant-ml 0.1.0 (no rescue_foreign).
- envs isabelle and isabelle-2 contain semantic-embedding 0.3.0 and performant-ml 0.1.0.
- No Foreign use in the cached rpc, minilang, mcp or nunchaku packages.

Recommended fix: Three small text changes, none of which alters the design:

1. §6: add case (h), the build-bump case rev-1 C1 item (5) asked for (REVIEW1:264).
   - Start from (e)'s environment, with isabelle-light-locale installed (which pulls in isabelle-expose-foreign and isabelle-future-assign-interrupt).
   - Run `conda update isabelle` to the new pristine build.
   - Expect: status shows expose_foreign as applied (no longer pre-applied), and future_assign_interrupt and light_locale as applied; conda's output shows the heap notice.

2. Decision 14, hook-layer test: say that "换 isabelle 包" means going from a toy build whose etc/ISABELLE_ID is the real LEGACY_BUILDS key 5533cd83156e (with the toy expose_foreign change built in) to a pristine toy build. No injectable LEGACY table or other test-only hook is needed. Do not add a second legacy-specific mechanism: because the tool keeps no state, this case is the same as (c) by construction.

3. Decision 11: add one requirement on the CI plan. The new `isabelle` build's description or release notes, and the isabelle-packaging-ci README, say that this build no longer exposes Foreign, RunCall and CInterface, and that `conda install isabelle-expose-foreign` brings them back. Put the same sentence in the isabelle-base-features README (decision 12). Note there that the ecosystem's own packages do not need it, because Performant_Isabelle_ML >=0.2.0 puts Foreign back itself. Wording is the author's call under ruling 17.

Lower the severity to minor.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- §6 has no build-bump case, which REVIEW1:264 required;
- no release note tells users that expose_foreign has become a package.
Refuted: the update is not special for the tool. It keeps no state, so it computes the same thing as §6 (c); defender-C16 measured identical trees. The severity is minor.

Changes:
- Add §6 (h): from (e)'s environment with isabelle-light-locale, run `conda update isabelle` to the pristine build. Expect expose_foreign applied (no longer pre-applied), future_assign_interrupt and light applied, and the heap notice in conda's output.
- The hook-layer toy build carries the real key 5533cd83156e; no test-only hook.
- Decision 11 and decision 12: one release-note sentence in the new isabelle package's description, the packaging-ci README and the isabelle-base-features README: Foreign, RunCall and CInterface now come from `conda install isabelle-expose-foreign`, and the ecosystem's own packages do not need it, because Performant_Isabelle_ML >=0.2.0 re-binds Foreign (rescue_foreign.ML; Semantic_Embedding/conda/recipe.yaml:338).
- Correct, to the owner, the author's 2026-10-23 04:46 statement (transcript line 5373, item 4) that Semantic_Embedding must depend on isabelle-expose-foreign.
- Record the promised open item on whether isabelle-ai should pull isabelle-future-assign-interrupt. Neither item is in rev 2.

### C17 [minor] Hook messages are repeated once per hook, end with a repair command that cannot repair a user edit, and the heap notice fires when it is false and names a path the tool cannot compute

Section: Decision 8 (plan:233-235); §4 heap notice (plan:337-342)  ·  merged from: conda-conda-9, user-F4, user-F13

**Statement.** Repetition. conda prints and deletes .messages.txt after every successful script (conda/core/link.py:1685, :1697-1708), and every feature post-link re-runs the whole chain and writes its result. So one conflict is reported once per feature package in the transaction. Measured: three identical blocks for a three-feature install (critic-conda/run.out scenario E; critic-user/run2.out walk e, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/). dev_patches would print up to seven.

Wrong remedy. Each block ends with the remedy `isabelle-patch-control status / apply` (plan:233-234). That cannot fix a CONFLICT caused by a user edit. The real remedy is to restore the file (`conda install --force-reinstall isabelle`, plus `apply` on 2025.2-0), or to delete a created file that is present with other content.

The heap notice is written when it is redundant or false (critic-conda/run.out scenarios B and C):
- twice on an update of a feature, once from the pre-unlink and once from the post-link;
- on `conda remove isabelle-light-locale`, once per pruned package, even when the tree ends at the pristine base, where the shipped heaps are valid again;
- on `conda remove isabelle`, while the tree is being deleted.
The notice also prints `<ISABELLE_HOME_USER>/heaps` (plan:340), which the tool cannot compute, because it never runs isabelle (plan:147). Rev 1's judge asked for the command `isabelle getenv ISABELLE_HOME_USER` instead (REVIEW1:1357, :1662). The plan also does not say whether a hook that changed nothing writes anything.

Required. The wording is the author's under ruling 17, but who writes what is design.
- Each hook reports only on its own package, in one line: applied, or "not applied: X is CONFLICT".
- The full diagnosis comes only from the hook whose own feature failed, or from the isabelle hook.
- A hook that changed nothing writes nothing.
- The CONFLICT text names each file and its real remedy.
- The heap notice comes only from a hook that changed files under src/, and names `isabelle getenv -b ISABELLE_HOME_USER`.
- When the tree returns to the shipped state, the notice says instead that the shipped heaps are valid again.

**Editor.** conda-conda-9 attributes "once per transaction" to rev 1's judge. That phrase was the rev-1 editor's relaxation (REVIEW1:1594, :1654); the judge required the src/ trigger, the getenv command and exact text (REVIEW1:1658-1664). user-F13's claim that stale heaps in the user directory then hide the valid shipped ones rests on store.scala:334-336 and :359. Rev 1's judge marked the heap search order as unmeasured guidance (REVIEW1:1667), so it should go into the notice only after a check. user-F4's pre-unlink part is in C8.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute each part of the challenge. Five parts survive. Three parts are refuted, and so is one of the fixes the challenge requires.

CONFIRMED

(A) One conflict is reported once per feature package.
- Every feature's post-link runs a whole-chain apply (plan:229).
- On failure, every hook writes the `status` output, the `git apply` error and the repair command (plan:233-234).
- So a single CONFLICT produces one identical block per feature package in the transaction.
- Measured in three places:
  - critic-conda/run.out:100-103;
  - critic-user/run2.out:74-96 (three identical blocks);
  - my own run, defender-C17/run.out, rule "plan": three identical "FULL DIAGNOSIS" blocks for a three-package install.
- The chain has seven features above pristine (plan:14), so installing qiyuan-dev-patches can print up to seven blocks.
- The tool cannot remove the duplicates through the file. conda prints `.messages.txt` and deletes it after every successful script (conda/core/link.py:1685, :1697-1708).
- The alternative rule works. Under the "report on your own package" rule in my prototype, the same install prints one diagnosis plus one one-line message (run.out, rule "own").

(B) The plan does not say what a hook that changed nothing writes. Plan:233 says a successful hook lists "the features applied or reversed this time". It does not say that a hook whose list is empty writes nothing. In a seven-package install, six of the seven hooks change nothing.

(C) The repair command cannot repair a conflict.
- Plan:234-235 says the user can see the state with `status` and fix it with `apply` ("status 看得见、apply 修得了"). That is false for CONFLICT, which is the main way a post-link fails:
  - `apply` stops at CONFLICT with exit 1 (plan:209-210);
  - there is no `--force` (plan:215);
  - CONFLICT is computed from the file contents (plan:186-191), so running `apply` again reproduces it.
- §6 (f) tests exactly this case (plan:368) but never tests the remedy.
- The real remedy is to restore the file. `conda install --force-reinstall isabelle` does that on a new build: in my toy, the edited file was restored and the isabelle post-link re-applied the whole chain.
- That remedy has a cost the challenge does not mention:
  - with `--force-reinstall`, conda adds the package to the packages it unlinks (core/solve.py:1423), so the isabelle pre-unlink runs; my toy's hook log shows ISA-PRE-UNLINK;
  - the real isabelle pre-unlink deletes the environment's whole Isabelle user directory, with `rm -rf` (isabelle-packaging-ci/conda/recipe.yaml:223-231). That directory holds the heaps, the preferences and the component registrations.
- For a file that a feature creates and that is present with other content, the remedy is to move the file aside and then run `apply`.

(D) A rev-1 requirement was not carried out.
- Rev 1's judge required the notice to name the command `isabelle getenv ISABELLE_HOME_USER` (REVIEW1:1357 for C14; REVIEW1:1662 for C18).
- Plan:340 still prints `<ISABELLE_HOME_USER>/heaps`.
- The tool cannot compute that path:
  - it never runs `isabelle` (plan:147);
  - computing the path itself would copy the suffix rule of pack.sh:168-189, and decision 11 item 4 proposes to change that rule (plan:274).
- The right command is `isabelle getenv -b ISABELLE_HOME_USER`. The `-b` flag prints only the value (lib/Tools/getenv:19), and the isabelle recipe itself uses that form (recipe.yaml:225).

(E) The notice is partly false when an unapply returns the tree to its shipped state. The plan has one notice text for both apply and unapply (plan:214, :338-342). When an unapply ends with no feature above the chain base applied, its first sentence, "The prebuilt heaps are now stale", is false.

REFUTED

(1) Most of the duplicate heap notices cannot be removed, and the challenge's own rule would not remove them.
- The rule "the notice comes only from a hook that changed files under src/" is already the plan's rule (plan:214, :337). It implements REVIEW1:1658.
- The challenge's examples all come from hooks that did change src/:
  - one notice per pruned package on `conda remove` of a feature (critic-conda/run.out:61-62; critic-user/run2.out:118-122);
  - notices during `conda remove isabelle` (critic-conda/run.out:39-40; critic-user/run2.out:141-145).
- A hook cannot know the rest of the transaction. conda gives a script only ROOT_PREFIX, PREFIX, PKG_NAME, PKG_VERSION and PKG_BUILDNUM (link.py:1630-1634), and it deletes the message file after each script. So a feature's pre-unlink cannot tell that `isabelle` itself is being removed, or that another pruned package's hook will follow.
- The pre-unlink still has to reverse the feature, because §6 (g) requires that no `isa/` files remain (plan:369).
- So this repetition is unavoidable. How long each notice is, is wording, which ruling 17 leaves to the author.
- The "twice on update" case comes from the pre-unlink, which is C8's subject.

(2) "Once per transaction" was not a rev-1 requirement. The editor is right: that phrase is the rev-1 editor's relaxation (REVIEW1:1594). The judge's text (REVIEW1:1658-1664) does not require it.

(3) The required text "the shipped heaps are valid again" should not be adopted.
- Isabelle's sources say it would usually be false:
  - Isabelle looks in the user directory before the system directory (store.scala:334-336);
  - `get_session` takes the first heap or build database it finds (:358-360), and `try_open_database` takes the first match (:489-492);
  - `check_output` compares that database's recorded sources with the current sources (:538-556);
  - rebuilt heaps go into the user directory (:331).
- So if the user started Isabelle while features were applied, the stale Pure and HOL heaps in the user directory are found first and rebuilt, even though the shipped heaps are current.
- The execution record says the same thing for the opposite case: the user directory's heaps are read first (RECORD.md:83).
- This exact case has not been measured; measuring it needs a build, which needs the owner's command.
- On the merits I agree with the editor: until it is checked, the notice should claim neither that the shipped heaps are valid again nor that the user heaps hide them.

Severity stays minor. No ruling is contradicted: ruling 17 delegates the wording to the author, and who writes what is decided inside the author's decision 8.

Experiment: I built my own toy noarch channel in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C17/. The generator is mkchan.py, the driver is run.sh, and the output is run.out. I used conda 25.11.1 with a private HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS, and the real `git apply` 2.43.0.

The channel holds:
- `isa`, which stands in for a new pristine isabelle build. Its post-link is rev 2's line. Its pre-unlink writes one line to a log.
- `ipc`, a toy tool. Every feature's post-link runs a whole-chain apply, as in plan:229.
- Three chained features: feata, featb and featc.

I ran it under two message rules.
- Rule "plan" (plan:233-234): the user edits src/b.ML, then runs `conda install featc`. The output has three identical "FULL DIAGNOSIS: b is CONFLICT" blocks, each ending "Fix with: ipc status / ipc apply".
- Rule "own" (a hook writes only about its own package; the full diagnosis comes only from the hook of the feature that is in CONFLICT, or from the isabelle hook; a hook that changed nothing writes nothing): the same install prints "applied a; HEAP NOTICE", one diagnosis from featb's hook, and "featc: not applied: b is CONFLICT".

Then I ran `conda install --force-reinstall isa`. It restored the edited file, and isa's post-link re-applied a, b and c. The hook log shows that isa's pre-unlink ran. The real isabelle pre-unlink deletes the environment's user directory (recipe.yaml:223-231).

I also re-read the round-2 critics' logs: critic-conda/run.out (scenarios B, C and E) and critic-user/run2.out (walks d, e and g).

Reading only, no builds: conda/core/link.py:1630-1708 and core/solve.py:1413-1432; Isabelle2025-2 src/Pure/Build/store.scala:331-360, 476-492 and 538-556; lib/Tools/getenv:19; RECORD.md:83.

Recommended fix: Make the changes below. The author can do this under ruling 17, with no new design decision.

1. Decision 8 (plan:233-235): replace the "on failure, write…" sentence with a rule for who writes what. When `conda-hook` writes to `.messages.txt`:
   - (i) It lists only the features its own run applied or reversed. It adds the heap notice when that run changed a file under src/.
   - (ii) On failure, it writes the full `status` output and the `git apply` error only if the feature in CONFLICT is the hook's own feature, or the hook is the isabelle one. Any other hook whose own feature is left unapplied writes one line: `<own feature>: not applied, because <X> is CONFLICT at <file>; see isabelle-patch-control status`.
   - (iii) A hook whose run changed nothing, and whose own feature is applied, writes nothing.
2. Same place: delete "apply 修得了" (apply can fix it). Give a remedy for each cause:
   - A file shipped by the isabelle package was edited: restore it, for example with `conda install --force-reinstall isabelle`. Say that this also deletes the environment's Isabelle user directory (heaps, preferences, component registrations), through recipe.yaml:223-231. On 2025.2-0, the user must then run `isabelle-patch-control apply`.
   - A file a feature creates is present with other content: move it aside, then run `apply`.
   - The chain is broken: update the package the error names.
3. §4 heap notice (plan:338-342):
   - Replace `<ISABELLE_HOME_USER>/heaps` with "the heaps/ directory under the path printed by `isabelle getenv -b ISABELLE_HOME_USER`". This carries out REVIEW1:1357 and :1662.
   - When the run leaves no feature above the chain base applied, drop "The prebuilt heaps are now stale". Say only that heaps built from other sources are rebuilt on first use.
   - Do not claim that the shipped heaps are valid again. Make that claim only after it has been measured on a runner the owner authorizes.
4. Decision 14 hook-layer test: assert exactly one full diagnosis per conflict, and that hooks which changed nothing write nothing.

Do not try to remove the one-notice-per-pruned-package repetition, or the notices during `conda remove isabelle`. They are unavoidable, because a hook cannot see the rest of the transaction.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- one diagnosis is printed per feature package (defender-C17 run.out);
- the plan does not say what a hook that changed nothing writes;
- 'apply 修得了' (apply can fix it) is false for a CONFLICT;
- `<ISABELLE_HOME_USER>/heaps` cannot be computed by the tool (REVIEW1:1357, :1662 survived);
- 'heaps are stale' is false when an unapply returns the tree to its shipped state.
Refuted:
- the duplicate notices on removal cannot be avoided: a hook cannot see the rest of the transaction (link.py:1630-1634);
- 'shipped heaps are valid again' must not be claimed, because the user directory is searched first (store.scala:334-360).

Changes:
- Decision 8 says who writes what:
  - each hook lists only what its own run changed, plus the notice if src/ changed;
  - the full diagnosis comes only from the hook whose own feature is in CONFLICT, or from the isabelle hook; others write one line;
  - a hook that changed nothing, and whose feature is applied, writes nothing.
- Remedies per cause:
  - an edited tracked file: restore it with `--force-reinstall isabelle`, and state that this deletes the environment's user directory (solve.py:1423 unlinks isabelle; recipe.yaml:223-231); on 2025.2-0, then run apply;
  - a created file present with other content: move it aside, then apply;
  - a broken chain: update the named package.
- Heap notice: name `isabelle getenv -b ISABELLE_HOME_USER`, and drop the 'stale' sentence when no feature above the bottom stays applied.
- Test: exactly one full diagnosis per conflict, and silence from hooks that changed nothing.

### C18 [minor] The default tree and the default features.d come from different places, so a mismatched pair silently reads as 'no feature packages installed'; rev 1's C22 CLI rules are missing

Section: Decision 2 (plan:146-151); decision 8 (plan:226-229); §4 (plan:323-335)  ·  merged from: conda-conda-8, consistency-F13, consistency-F14

**Statement.** The mismatch. The tree comes from --isabelle-home, but the default features.d always comes from sys.prefix (plan:146-151). Suppose the tool runs from the base environment or another environment, with --isabelle-home pointing into environment X. It then reads the other environment's features.d. If that has none, status prints "no feature packages installed" and exits 0. That is the silent success rev 1's judge prevented by deriving the default from the tree's own prefix (REVIEW1:2001-2006).

Missing rules. The judge's two other requirements are absent: status, apply and unapply print the features.d path they read, and an unknown `--feature` is exit 3.

Inconsistency. Decision 2 says the hooks pass $PREFIX/isa (plan:148), but the hook line passes nothing (plan:227). The plan never says whether conda-hook reads $PREFIX, which conda sets for every hook (conda/core/link.py:1631), or sys.prefix.

One thing rev 2 gets right should be stated with its reason. The conda-environment test is the conda-meta directory, not conda-meta/history, because history and the package records are written only after the post-links have run (conda/core/link.py:969-1003). A probe post-link during a fresh `conda create` sees conda-meta but no history (critic-conda/run.out scenario A, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

Required.
- Derive everything from one prefix P: $PREFIX for conda-hook, the parent of an explicit --isabelle-home, otherwise sys.prefix.
- The tree is P/isa, features.d is P/share/isabelle_patch_control/features.d, and the environment test is "P/conda-meta is a directory", with the reason it is not conda-meta/history.
- Print the paths read.
- An unknown --feature is exit 3.

**Editor.** Confirmed by reading decision 2. consistency-F13 and consistency-F14 contribute only their tree-passing and CLI parts here; their other parts are in C26, C14 and C23.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute each of the four parts of the challenge. All four survive. One part (the hook inconsistency) is only textual.

1. The mismatch is real, and it misreads ruling 19.
- Decision 2 takes the tree from `--isabelle-home` when that flag is given. It takes the default features.d from sys.prefix, and only when sys.prefix/conda-meta exists (plan:146-151). The two values can come from different places.
- `--isabelle-home` matters only when the tool is not running in the tree's own environment. Inside the tree's own environment the default already finds the tree. So whenever the flag is used without `--features-dir`, the default features.d belongs to the wrong prefix, except when the flag names sys.prefix/isa itself.
- The plan's own error path leads users there. Running from an environment without isa/ is refused with exit 2 and a hint to pass `--isabelle-home` (plan:147, §4 plan:334). Following the hint produces the mismatch.
- On this machine the base environment `~/miniconda3` has conda-meta but no isa/ and no share/isabelle_patch_control. A `pip install` into base, which is active by default, therefore gets `no feature packages installed` and exit 0 for any `--isabelle-home envs/X/isa`.
- My prototype shows four more wrong outcomes:
  - With the tool in environment Y, `--isabelle-home X/isa` applies Y's feature packages to X's tree.
  - A tool installed from PyPI (decision 14) is refused for a conda tree, and the refusal wrongly cites ruling 19.
  - From any conda environment, a self-installed `~/Isabelle2025-2` is accepted. The tool either reports "no feature packages" with exit 0, or patches it with that environment's features. This breaks appendix A's promise at plan:443 ("不碰用户自装的 Isabelle", that is, never touch an Isabelle the user installed themselves).
- Ruling 19 (plan:59) is about the tree ("不在 conda 里的 Isabelle", an Isabelle that is not inside conda). Rev 2 tests the tool's prefix instead.
- Rev 1's judge tied the default to the tree's own prefix (REVIEW1:2001-2004). Rev 2 moved it to sys.prefix without saying why, while plan:4 claims every confirmed item was absorbed. No ruling and nothing in the migration plan fixes features.d to sys.prefix: grep of ISABELLE_GIT_MIGRATION_PLAN.md finds features.d only at :23, :396, :404, :421, :507 and :615.

2. Both CLI rules from rev 1 are missing.
- Printing the features.d path: the "no feature packages" message (plan:150) and the status sample (plan:196-205) carry no path.
- Exit 3 for an unknown `--feature`: the exit-code list (plan:334-335) does not include it, and decisions 5 and 6 (plan:204, 209-213) do not define it. Today's tool exits 1 here (cli.py:34-43).
- Under rev 2's text, `status --feature typo` exits 0 vacuously, because "all selected features are applied" holds for an empty selection (plan:204). `unapply --feature typo` ("from the chain top down to F", plan:212-213) has no defined stopping point.
- Ruling 17 lets the author decide wording, but rev 2 made no such decision; it simply left the rules out.
- One nuance for the fix: the `isabelle` package's post-link passes `isabelle`, which is not a feature, as its argument (plan:236). The post-link argument is only a label (plan:229), so the exit-3 rule must not apply to it.

3. The inconsistency exists, but it does no harm in practice.
- plan:148 says the hooks pass $PREFIX/isa. The hook line at plan:227 passes nothing, and plan:378 says "$PREFIX/sys.prefix".
- In a hook the two are equal. run_script puts the script's own directory, $PREFIX/bin, first on PATH (conda/core/link.py:1635), and sets PREFIX (:1631). The entry point's Python is that environment's Python. Even when a prefix is too long for a full shebang, conda writes `#!/usr/bin/env python` instead (core/portability.py:330-332, :367-372), and that still resolves through the same PATH.
- So the plan only needs to pick one and say which. $PREFIX matches plan:229 and plan:233, and it is the prefix conda reads .messages.txt from (link.py:1684-1708).

4. The conda-meta test is right, and the plan should record why.
- conda writes the history file and the package records in the register group after all post-links have run (link.py:580-596, :969-999).
- The round-2 critic's probe saw `conda-meta=yes history=no json=0` during a fresh `conda create` (critic-conda/run.out, scenario A).
- Both conda's own `is_conda_environment` (gateways/disk/test.py:95-96, PREFIX_MAGIC_FILE at base/constants.py:334) and rev 1's judge (REVIEW1:2003) test conda-meta/history instead.
- An implementer who reuses that helper, which the repository's always-reuse-code rule would push them to do, would make every fresh-create post-link refuse to run. The reason must be written down.

The editor's relaxation is empty, so there was nothing to weigh. The severity is minor, and I agree with it.

Experiment: Files are in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C18/: the script resolve_proto.py and its output resolve_proto.out.

The script builds toy layouts:
- conda environment X, with conda-meta, isa/ and features.d/light_locale;
- conda environment Y, with conda-meta and features.d/qiyuan_dev_patches;
- base, with conda-meta only;
- a PyPI virtual environment;
- a self-installed home/Isabelle2025-2.

It runs rev 2's decision-2 rule and the one-prefix rule on each case.

Results, rev 2 rule against one-prefix rule:
- (1) Tool in X, no flags: both give X with light_locale.
- (2) Tool in base with `--isabelle-home X/isa`: rev 2 says "no feature packages installed", exit 0; one prefix gives X's light_locale.
- (3) Tool in the PyPI venv with `--isabelle-home X/isa`: rev 2 refuses with exit 3 citing ruling 19; one prefix works.
- (4) Tool in base with `--isabelle-home ~/Isabelle2025-2`: rev 2 gives exit 0, "no feature packages"; one prefix refuses with exit 3.
- (5) Tool in Y with `--isabelle-home ~/Isabelle2025-2`: rev 2 would patch the self-installed tree with Y's qiyuan_dev_patches; one prefix refuses with exit 3.
- (6) Tool in Y with `--isabelle-home X/isa`: rev 2 reads Y's features.d for X's tree; one prefix reads X's.
- (7) Tool in base, no flags: both give exit 2. Under rev 2 the exit-2 hint then leads straight to case (2).

Read-only checks on the real machine:
- `~/miniconda3/conda-meta` exists; `~/miniconda3/share/isabelle_patch_control` does not.
- `~/miniconda3/bin/python` has sys.prefix `~/miniconda3`; `envs/isabelle/bin/python` has sys.prefix `envs/isabelle`.

Source reads:
- conda/core/link.py:1631-1635 (PREFIX is set; dirname of the script is prepended to PATH);
- link.py:580-596 and :969-999 (history and records are written after the post-links);
- gateways/disk/test.py:95-96 and base/constants.py:334 (conda's own environment test uses history);
- core/portability.py:330-332 and :367-372 (the `/usr/bin/env` shebang for long prefixes);
- the tool's cli.py:34-43 (an unknown feature exits 1 today).

The critic-conda run.out scenario A probe line (`conda-meta=yes history=no json=0` during a fresh create) confirms the conda-meta point.

Recommended fix: Smallest fix, all inside decision 2, decision 14 and §4.

(1) Replace decision 2's two default rules (plan:146-151) with a single rule built on one prefix P:
- P is $PREFIX inside conda-hook (conda sets it for every script, link.py:1631; it equals sys.prefix there).
- Otherwise P is the parent of an explicit `--isabelle-home`.
- Otherwise P is sys.prefix.
- The tree is the explicit `--isabelle-home`, or else P/isa.
- An explicit `--features-dir` must exist, or the run is exit 3. Without it, features.d is P/share/isabelle_patch_control/features.d, used only when P/conda-meta is a directory. A missing features.d there means "no feature packages installed", exit 0.
- Otherwise, exit 3 with the message "<P> is not a conda environment (self-installed Isabelle is not supported); pass --features-dir".
- Add one sentence of reason: the test is the conda-meta directory, not conda-meta/history and not conda's `is_conda_environment`, because conda writes history and the package records only after all post-links have run (link.py:580-596, :969-999). During a fresh `conda create` a post-link sees conda-meta but no history.

(2) Delete "钩子把 `$PREFIX/isa` 传给它" (the hooks pass $PREFIX/isa to the tool) at plan:148 and at plan:378's "/sys.prefix". The hook line at plan:227 stays as it is.

(3) §4: add two things.
- status, apply and unapply print one header line naming the tree and the features.d they read. The "no feature packages installed" message includes that path.
- An unknown `--feature` exits 3. "Known" means F is a feature directory on the chain or the bottom record's feature from LEGACY_BUILDS. The argument to `conda-hook post-link` is a label, not a selector, so the `isabelle` package's `post-link isabelle` stays valid.

(4) Decision 14: add tests for
- a tool in another environment with `--isabelle-home` pointing into X (must read X's features.d);
- a self-installed tree passed from a conda environment (exit 3);
- a typo in `--feature` (exit 3).

**Judge: confirmed → author_fixes_no_rereview.** Confirmed: decision 2 takes the tree from --isabelle-home but features.d from sys.prefix (plan:146-151), which gives silent successes and cross-environment patching (defender-C18 cases 2-6). This misreads ruling 19: it tests the tool's prefix instead of the tree's. REVIEW1:2001-2006 is missing.

Changes:
- Replace decision 2's defaults with one prefix P:
  - P is $PREFIX inside conda-hook; otherwise the parent of an explicit --isabelle-home; otherwise sys.prefix.
  - The tree is the explicit --isabelle-home, or else P/isa.
  - An explicit --features-dir must exist (exit 3 otherwise). The default features.d, P/share/isabelle_patch_control/features.d, is used only when P/conda-meta is a directory; a missing default directory means 'no feature packages installed', exit 0. Otherwise exit 3: 'not a conda environment; pass --features-dir'.
  - Give the reason the test is the conda-meta directory and not conda-meta/history or conda's is_conda_environment: history and the package records are written only after the post-links (link.py:969-999).
- Delete '钩子把 $PREFIX/isa 传给它' (the hooks pass $PREFIX/isa) at plan:148 and the '/sys.prefix' at plan:378.
- §4: status, apply and unapply print the tree and the features.d they read, and an unknown --feature is exit 3 (conda-hook's post-link takes no argument, per C4).
- Tests:
  - a tool in another environment with --isabelle-home pointing into X reads X's features.d;
  - a self-installed tree passed from a conda environment gives exit 3;
  - a typo in --feature gives exit 3.

### C19 [minor] Restoring mode bits rests on a false fact (no conda source file is 0444), contradicts 'the tool does not chmod', misses created files, and makes the tool and plain git apply produce different modes

Section: Decision 4 (plan:177-178); decision 7 (plan:220); §2.3 (plan:110-111); §7 row 发现 13 (plan:387); §8 (plan:407)  ·  merged from: engine-E8, consistency-F5, conda-conda-11, user-F6

**Statement.** The defect. Decision 4 says that the tool does not chmod and, in the same sentence, that it restores the original mode bits after git apply, because "Isabelle's sources are 0444" (plan:177-178). §7 repeats "不 chmod" (no chmod; plan:387). The premise is false for the only supported target: pkgs/isabelle-2025.2-0/isa/src holds 3522 files at 0644, 26 at 0755 and none at 0444 (`find -printf '%m'`). 0444 is the mode in the git work tree. Rev 1's judge had ordered this fact corrected and the post-step deleted (REVIEW1:1495-1499).

Further problems:
- The restoration covers only rewritten files. A created file gets 0666 & ~umask, so under umask 027 or 077, for example a hardened root installing a shared environment, light's created files become 0640 or 0600 and other users cannot read them (critic-engine/e8/umask.sh, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).
- The directory interface skips the step (plan:220). So the tool and plain git apply produce different modes, 0644 versus 0664 under this machine's umask 002, and (b2)'s mode comparison either fails or must be dropped.
- The step has its own window: an interrupt after git apply and before the chmod.
- §2.3 and §8 describe the hard-link sharing as being with the cache copy; the real sharing is between environments (REVIEW1:1499).

Required.
- Delete the restoration and the 0444 premise.
- Run the git child with a fixed umask (`subprocess.run(..., umask=0o022)`, Python 3.9 or later on POSIX), so that a created file's mode comes only from the patch and a modified file keeps its original mode, identically in every caller.
- Correct plan:110-111, :178, :387 and :407.

**Editor.** Confirmed; I counted the modes myself. consistency-F5 rates this major because of the (b2) mode comparison. It is minor, because the fix is one line and C2's relaxation removes the step altogether.

**Relaxation proposed by the editor.** Under C2's install by rename, the mode is set on the scratch file before the rename. There is then no separate chmod step and no window, and every caller produces the same modes.

**Defender: partially_confirmed** (needs owner: False).

C19 is partly right. Its core defect is real: the 0444 premise is false, and keeping the mode-bit restoration out of the directory interface breaks (b2). Two of its supporting arguments do not hold, and its fix promises more than it delivers. Severity minor, as the editor rated it.

CONFIRMED
1. The 0444 premise is false for the only supported target.
   - plan:178 says "Isabelle 的源码是 0444".
   - Measured file modes: pkgs/isabelle-2025.2-0/isa/src has 3522 files at 644 and 26 at 755, none at 444. The whole isa/ tree has 23001 at 644 and 1077 at 755. envs/isabelle/isa and envs/isabelle-2/isa match.
   - 0444 occurs only in the developer's main git work tree contrib/Isabelle2025-2: 2940 files, inherited from the official tarball. The worktrees are 664/775.
   - pack.sh and recipe.yaml never chmod source files (grep: the only chmod lines are recipe.yaml:210 and :231, on the hook scripts). The future plain build comes from the same pipeline, so it will have the same modes.
   - The rev-1 judge ordered this fact corrected: "Every file in the published package is user-writable" (REVIEW1:1499). Rev 2 asserts the opposite, so this is a rev-1 defect that survived.
2. Wording contradiction. plan:177 and plan:387 say the tool does not chmod (不 chmod), but the restoration at plan:177-178 is a chmod of the new inode. What is meant is "never chmod a shared inode", and the plan should say exactly that.
3. The tool and the directory interface produce different modes, and (b2) fails.
   - Decision 7 says the directory interface does not restore mode bits (不恢复权限位, plan:220).
   - (b2) imports git_apply (plan:221-222), and copy B goes through it (plan:353-355).
   - The migration plan requires "A 必须整树（含 mode 位）等于 B", the whole tree equal including mode bits, and "unpatch A 必须等于构建原状", unpatch must return the build's original state (ISABELLE_GIT_MIGRATION_PLAN.md:403-405).
   - My experiment applied the real future_assign_interrupt and light_locale diffs to copies of the cache files (exp/modes.py). Under rev 2's rule, A≠B under this machine's umask 002: the 30 rewritten files are 644 in A and 664 in B. A≠B also under a caller umask of 027.
4. The window between git apply and the chmod is real but cosmetic. An interrupted state differs only in the group-write bit (664 instead of 644 under umask 002).
5. The prose on hard links is half fixed.
   - On this machine envs/isabelle and envs/isabelle-2 share inode 55605093 (links=2) for ml_name_space.ML. The cache copy is a separate inode, 56390733 (links=1).
   - plan:110-111, :121 and :407 speak only of the cache.
   - The hook test at plan:306 does already check sibling environments.

REFUTED OR OVERSTATED
a. "The rev-1 judge ordered the post-step deleted" misreads the ruling.
   - _restore_mode was deleted because GNU patch keeps the mode by itself (REVIEW1:1451, 1486, 1495).
   - git apply does not keep the mode. It writes (0666|0777)&~umask, which the plan itself records as 444→664 (plan:407).
   - The judge's post-condition was "keeps its mode" (REVIEW1:1498). Under ruling 18 (git apply as the engine), some way of setting modes is therefore required. Adding one is not a regression; only its premise is.
b. The bullet about created files under umask 027/077 is moot.
   - conda 25.11 extracts packages through conda_package_handling (gateways/disk/create.py:241-243), and that extraction applies the umask.
   - Measured: the payload of depa and jsoncomment extracts at 640 under umask 027 (cph2/).
   - So in the hardened-root scenario, every file of isa/ is already 640. Light's created files are no less readable than the rest of the environment, and rev 2's created-file modes follow the same rule as conda's own extraction.
c. The fix's claim that "a modified file keeps its original mode" holds only when the original is 644 or 755.
   - If the cache was extracted under umask 027, the fixed umask turns all 30 rewritten files from 640 into 644 (exp/out).
   - A 444 file becomes 644 (toy444/).
   - For the supported target the claim does hold: all 3548 src files' conda modes equal git's recorded mode (100644/100755) under umask 022 (gitmodes.txt; every patch header is 100644).
   - The 444 case of the rev-1 post-condition test (REVIEW1:1498) must therefore be dropped explicitly.

EDITOR'S RELAXATION
The relaxation depends on C2 being accepted. Install-by-rename removes the window, but the tool then becomes a writer, against plan:177 ("唯一的写者是 git apply", git apply is the only writer), and it still needs a rule for the scratch file's mode. A fixed umask on the git child is exactly that rule, so the two combine and the umask line is needed in either case.

Elegance: the fixed umask is one line in the single engine function. It has no window, and every caller, including (b2) copy B, gives the same modes by construction. It beats moving the restoration into git_apply, which keeps a second mechanism and its window. On Windows, subprocess ignores umask (subprocess.py:805 "POSIX only", :1460 unused_umask), and mode bits mean nothing there anyway.

Experiment: All experiments ran in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C19/.

(1) Counted file modes with find -printf %m in four trees:
- pkgs/isabelle-2025.2-0/isa/src: 3522 at 644, 26 at 755.
- The whole isa/ tree: 23001 at 644, 1077 at 755.
- envs/isabelle and envs/isabelle-2: the same as the cache.
- contrib/Isabelle2025-2 (the main git work tree): 2940 at 444, 1737 at 644, 17 at 664, 26 at 755. The -pristine and -light_locale worktrees: 664 and 775.

(2) gitmodes.txt: compared git ls-tree f8d760a -- src with the cache modes. 3547 files compared, 0 mismatches. All 42 index lines in the patches say 100644.

(3) exp/modes.py: used the real diffs f8d760a..6d8be01 and 6d8be01..7983d8a on cache copies whose modes emulate extraction under umask 002 and under 027, with caller umasks 002, 022 and 027. It compares three rules:
- rev 2's rule (apply restores modes, git_apply does not);
- a fixed child umask of 022;
- the restoration moved inside git_apply.

Results:
- Rev 2's rule gives A≠B under caller umask 002 and under 027.
- The fixed umask gives A==B in every case, but under the 027-extracted cache 30 rewritten files change from 640 to 644.
- The engine-level restoration gives A==B in every case and changes no rewritten file's mode.

(4) cph/ and cph2/: ran conda_package_handling.api.extract, the path conda uses (gateways/disk/create.py:241). The payload extracts at 644/664 under umask 002 and at 640 under umask 027.

(5) toy444/: a 444 file with two hard links, patched with subprocess umask=0o022. The target becomes 644 with links=1. The other link keeps 444 and its original content.

(6) stat of ml_name_space.ML: the two environments share inode 55605093 (links=2); the cache has inode 56390733 (links=1).

(7) subprocess.py:805 and :1460: umask is POSIX only and ignored on Windows.

Recommended fix: The smallest fix is plan text only.

(1) Decision 4, plan:177-178. Replace the restoration sentence and its 0444 premise with this:

"git_apply runs git with subprocess umask=0o022 (ignored on Windows). Every file of a conda isa/ tree is 0644 or 0755, equal to git's recorded mode (measured: 3548 of 3548 src files), so a rewritten file keeps its mode, and a created file gets 0644 or 0755 from its new file mode line, whoever calls the function. The tool never chmods or writes any file; git apply replaces a file with a new inode, so no shared inode is touched."

(2) Decision 7, plan:220: delete 不恢复权限位 ("does not restore mode bits"). Nothing is left to differ between the tool and the directory interface, so (b2)'s comparison of the whole tree including mode bits (ISABELLE_GIT_MIGRATION_PLAN.md:405) holds.

(3) Decision 14, plan:303: replace 权限位恢复 ("mode restoration") with a post-condition test.
- Run apply, unapply and apply-to under caller umasks 002 and 077.
- Rewritten files keep 0644/0755, and created files are 0644/0755.
- apply and apply-to give identical modes.
- The target's other hard links keep their inode, mode and bytes.
- Note that the 444 case of REVIEW1:1498 is dropped because no supported tree contains a 444 file.

(4) Correct plan:110-111, :121, :387 and :407.
- The other hard link that matters is a sibling environment. On this machine envs/isabelle and envs/isabelle-2 share inode 55605093, and the cache copy is a separate inode, 56390733.
- The 444 toy in §8 is an experiment on a file mode that does not occur in the supported target.
- In the §7 row for finding 13 (发现 13), say "never chmods; the git child runs with umask 022".

Do not add a created-file safeguard for umask 027/077 beyond this. conda's own extraction already applies that umask to the whole tree.

The relaxation from C2 (install by rename) is compatible but not needed. If C2 is adopted, the same umask line sets the scratch file's mode.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- the 0444 premise is false: the cached isa/src has 3522 files at 0644 and 26 at 0755;
- '不 chmod' (no chmod) contradicts the restoration step;
- the tool and the directory interface give different modes, so (b2) fails;
- the hard-link prose speaks of the cache, while the shared inode is a sibling environment's (two environments share inode 55605093).
Refuted: the created-file umask-027 argument. conda's own extraction already applies the umask to the whole tree.

Changes:
- Delete the restoration and the 0444 premise (plan:177-178).
- Under C2, the staging file gets its mode before the rename, identically for every caller including apply-to: the original mode for a modified file, 0644/0755 from the header for a created one. Also run the git child with umask=0o022 on POSIX.
- Delete '不恢复权限位' (does not restore mode bits) at plan:220.
- Correct plan:110-111, :121, :387 and :407.
- Tests under caller umasks 002 and 077:
  - modes are preserved or taken from the header;
  - apply and apply-to give the same modes;
  - other hard links keep their inode, mode and bytes.
- Note that REVIEW1:1498's 444 test case is dropped.

### C20 [minor] git_apply returns only success or failure, so symlinked targets, corrupt patch files and failed writes all read as CONFLICT, although §4 promises exit 3 for the first two

Section: Decision 4 (plan:171-172, :178); decision 5 (plan:186-189); §4 exit codes (plan:334-335)  ·  merged from: engine-E9

**Statement.** The defect. git's exit 1 lumps together several failures: "patch does not apply"; "wrong type", where the target is a symlink, as under conda's always_softlink setting; "beyond a symbolic link"; "No such file"; and "already exists". Exit 128 means a corrupt patch file, or a failed write after which files may be gone (C2). The level replay treats every failure as "check failed". So a symlinked target, a truncated patch file in features.d and an I/O error all read as CONFLICT, exit 1. Yet §4 promises exit 3 for symlinked targets and for invalid feature directories (plan:334-335), and decision 4 promises to refuse symlinked targets (plan:178) without saying where they are detected. The scratch copy follows a symlink and holds a regular file, so status can predict success where the call in the tree then fails (critic-engine/e6/symlink.sh, under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/).

Required. Classify failures before replaying:
- one lstat pass over every target path and its parent directories; a symlink is exit 3, and the message names conda's always_softlink setting;
- one parse of every patch file when the feature directories are read (for example `git apply --numstat`); a parse error is exit 3, naming the file;
- any other failure of a writing call means the tree may have changed: recompute status and report it.

**Editor.** Plausible and consistent with git's documented error classes; the critic's symlink run shows the messages.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I tried to refute the challenge from the plan text, the conda source and experiments. Its headline scenario for symlinks does not survive. The narrower claim survives: git_apply's success/failure return throws away the distinction git itself makes.

What is confirmed:
1. The interface erases git's own classification. Decision 4 says git_apply "returns success or not, and the output" (plan:171-172). git 2.43.0 has two failure exit codes, which I measured:
   - Exit 1 covers "patch does not apply", "wrong type" (the target file is a symlink), "affected file ... is beyond a symbolic link", "No such file or directory" and "already exists in working directory".
   - Exit 128 covers "corrupt patch at line 8" (a truncated file), "No valid patches in input" (garbage or empty input), "can't open patch" and "unable to write file".
2. A corrupt patch file reads as CONFLICT. With the plan's mechanism, a broken file under features.d leaves its target with no level in the level replay (plan:186-189). It is reported as CONFLICT, exit 1 (plan:192-193, 204-205). No rule in the plan covers this case. However, §4 does not literally promise exit 3 for it. The exit-3 list (plan:334-335) names forks, holes, version or release mismatch, symlinked targets, a missing --features-dir and the not-in-conda case, but not malformed patch files. So this is a missing case, not a broken promise. It is also hard to reach: published patch files pass gate (c) through the same git_apply (plan:221-222, 314). Only a hand edit or a hand-made --features-dir can produce one.
3. A failed write changes the tree. Exit 128 can come after a check that passed. git first removes all old files, then writes the new ones. In my experiment the tree ended either half-applied or with a file deleted, depending on block order. Decision 6 only says "stop at CONFLICT, exit 1, print git's output" (plan:209-211), with no recomputation of status. And plan:234-235 claims that a failed post-link leaves "package installed, feature not applied", which is false in this case. One mitigation is already in the plan: the hook failure path writes the status output into .messages.txt (plan:233-234), so for hooks half of the required "recompute status and report it" exists. The non-atomicity itself belongs to C2.

What is refuted or overstated:
4. Symlinked targets do not read as CONFLICT under the plan as written. plan:178 says symlinked targets are refused with exit 3, and plan:335 lists them under exit 3. A faithful implementation therefore never reports CONFLICT for one, and the challenge's headline scenario contradicts the plan's own text.
   - What survives is only that the plan does not say where the check runs, and in rev 2 that placement matters. The replay works on scratch copies (plan:186-189). A copy made the obvious way, with shutil.copy2 and its default follow_symlinks=True, is a regular file. On it, --check returns rc 0, while the same call in the tree returns rc 1 "wrong type" (measured).
   - This is also a rev-1 residue. Rev 1's C16 judge asked for refusal "instead of reporting a misleading CONFLICT", and its defender's fix put the os.lstat check "before computing status" and added a pytest case with a symlinked target. Rev 2 kept the refusal but dropped both the placement and the test: decision 14's pytest list (plan:300-303) has no symlink case.
5. Checking parent directories is unnecessary on conda trees. conda never creates symlinked directories. Directories are made with mkdir_p (gateways/disk/create.py:360-370). Only files are softlinked, and only under the non-default always_softlink or allow_softlinks settings (base/context.py:220, 450; core/link.py:94-104). The cached isabelle-2025.2-0 has 0 symlinks under isa/src and isa/etc, the only places patches touch (measured).
6. A separate parse pass with --numstat is not needed. Once git_apply passes the exit code through, a corrupt file is caught at its first --check. There is an optional, more elegant variant. The tool must read every patch file anyway to list its targets (§0 item 9, plan:42). `git apply --numstat --summary` does that parse-only, without touching the tree. It lists the real targets, including `create mode` lines for new files, and exits 128 on corrupt input (measured). Using it would also drop the hand-written header parsing, in line with plan:65 and §9, which say the tool implements no patch logic itself.

The editor's relaxation is empty. The severity "minor" is right.

Experiment: All experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C20/. They use git 2.43.0 outside any repository (GIT_DIR=/nonexistent), on the real future_assign_interrupt patch from critic-engine/real.

- e1.sh classifies git apply's failures by exit code:
  - a file symlink gives --check rc=1 "wrong type", and -R --check rc=1 "new mode (100644) ... does not match old mode (120000)";
  - a real apply on that symlink gives rc=1, and the symlink is left as it was;
  - a directory symlink gives rc=1 "affected file ... is beyond a symbolic link";
  - a missing target gives rc=1 "No such file or directory";
  - a content conflict gives rc=1 "patch does not apply";
  - a new file that already exists gives rc=1 "already exists in working directory";
  - a truncated patch gives rc=128 "corrupt patch at line 8";
  - a garbage or empty patch gives rc=128 "No valid patches in input";
  - a missing patch file gives rc=128 "can't open patch";
  - `--numstat` gives rc=128 on truncated and garbage input, and rc=0 with the target paths on a good one. `--numstat --summary` on light's 32 files lists `create mode` for the new files and needs no tree.
- e2.sh fails a write partway through one call. The patch has two blocks; directory b is read-only. --check gives rc=0, and the real apply gives rc=128 "unable to write file 'b/g'". With block order a,b, a/f ends up patched (the tree is half-applied). With order b,a, a/f is deleted.
- e3.py tests the scratch copy. shutil.copy2 with follow_symlinks=True gives a regular file, and --check there gives rc=0. With follow_symlinks=False the symlink is kept, and --check gives rc=1 "wrong type". In the tree itself, --check gives rc=1 "wrong type".
- Read-only checks:
  - conda's softlink settings default to False (base/context.py:220, 450), and determine_link_type uses them (core/link.py:94-104). Directories are always made with mkdir_p (gateways/disk/create.py:360-370).
  - pkgs/isabelle-2025.2-0 has 0 symlinks under isa/src and isa/etc, and 457 elsewhere.
  - Rev-1 C16's judge text and its defender's fix item 4 (ISABELLE_PATCH_CONTROL_REVIEW1.md:1489, 1497) ask for the os.lstat refusal before status, and fix item 5 (:1490) asks for a test with a symlinked target.

Recommended fix: Two small edits, neither of which changes the design.

(1) Decision 4, plan:171-172: git_apply returns git's exit code (0, 1 or 128) together with its output, instead of success or failure.
- In check mode, 1 means "does not apply" and feeds the level replay.
- A 128 from any check means the patch file cannot be parsed. Map it to exit 3, naming the patch file, and add "patch 文件无法解析" (a patch file that cannot be parsed) to §4's exit-3 list at plan:334-335.
- In a writing call, any non-zero exit means the tree may have changed. `apply` and `unapply` then recompute status and print it, the same way the hook failure path already writes the status output (plan:233-234).
- Correct plan:234-235's claim that a failed post-link always leaves "feature not applied". The atomicity fix itself belongs to C2.

(2) plan:178: say where the symlink refusal happens and test it.
- When the feature directories are read, before any status replay or git call, check every target with one os.lstat. Equivalently, refuse when realpath(tree/p) differs from realpath(tree)/p, which also covers a symlinked parent directory at no extra cost. The check has to run first because the replay's scratch copies would otherwise follow the link.
- The message names conda's always_softlink and allow_softlinks settings.
- Add a symlinked target that must be refused with exit 3 to decision 14's pytest list (plan:300-303), as rev-1 C16 required.

Optional, for elegance: list each feature's targets with `git apply --numstat --summary` (parse-only; it shows the real path of new files and exits 128 on corrupt input) instead of a hand-written header parser. Corrupt files are then caught when the feature directories are read, and the tool keeps no patch logic of its own (plan:65, §9). A separate lstat pass over parent directories is not needed for conda trees.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- git_apply's success/failure return throws away git's own distinction between exit 1 and exit 128 (defender-C20 e1.sh);
- a corrupt patch file reads as CONFLICT;
- plan:178's symlink refusal has no stated place, and a copy made with follow_symlinks turns a symlinked target into a regular file (e3.py).
Refuted: symlinked targets read as CONFLICT under the plan as written; parent-directory checks are needed on conda trees.

Changes:
- git_apply returns git's exit code and its output. In check mode, 1 feeds the replay; 128 means the patch file cannot be parsed: exit 3, naming the file. Add this to §4's exit-3 list.
- With C2, a failed write can only happen in staging. A failure while installing into the tree makes apply or unapply recompute and print status. Correct plan:234-235.
- Refuse symlinked targets when the feature directories are read, before any replay: realpath(tree/p) must equal realpath(tree)/p. The message names conda's always_softlink and allow_softlinks settings. Add the pytest case rev-1 C16 required.
- Optional: list each feature's targets with `git apply --numstat --summary` instead of a hand-written header parser.

### C21 [minor] The renderer's inputs and the release gates are incomplete: derived recipes are committed, the build number has no source, the package-name rule is wrong for dev_patches, one repo holds two packages, and make-patches releases symlink and gitlink blocks

Section: Decision 9 (plan:244-254); decision 12 (plan:278-288); decision 15 (plan:312-318); decision 4 (plan:178)  ·  merged from: landing-L13, landing-L15, user-F10, consistency-F11

**Statement.** (1) Committed derived recipes. Decision 12 has the renderer write conda/recipe.yaml and commits it in both new repositories (plan:282, :288), while the release workflow also runs the renderer (plan:253). Rev 1's judge said to remove conda/recipe.yaml from the layouts, so that no repository commits a derived recipe (REVIEW1:1915-1933). A committed copy goes stale after the next make-patches and can be mistaken for the source.
(2) The build number has no source. The build string is `Isabelle2025_2_<build number>` (plan:246), but provenance.txt carries only the prefix (make-patches:194-205). A recipe-only fix needs a bump, and a published file must never be overwritten (isabelle-packaging-ci/conda/recipe.yaml:42).
(3) The package-name rule. `isabelle-<feature, with _ changed to ->` (plan:244) gives isabelle-dev-patches, not the decided qiyuan-dev-patches (plan:245). Decision 15.3's path-length gate needs the package name from "decision 9's formula" (plan:316), but make-patches has no naming logic. The rule and its exception would therefore be duplicated in two tools.
(4) One repository, two packages. isabelle-base-features holds two independently versioned packages (plan:278), against RELEASE_CHECKLIST.md:242, "One repo, one package, one semver". The plan neither records the exception nor says how a release selects one of the two.
(5) Symlink and gitlink blocks. make-patches refuses only blocks matching `old mode|new mode|GIT binary patch|similarity index` (make-patches:167). A block with "new file mode 120000" (a symlink) or "new file mode 160000" (a gitlink) passes. It also has a ---/+++ pair, so decision 15.2 does not catch it either, and it would be released, while the tool refuses symlinked targets at install time (plan:178). The release gate and the tool thus disagree on what can be released. A plain "Binary files … differ" block has no ---/+++ pair and is caught by 15.2; the plan should say so.

Required.
- Render at build time only, or make CI fail when a committed copy differs from a fresh render.
- The build number becomes a workflow input, default 0, that refuses a version-and-build pair the channel already holds.
- Store the package name in the package directory (for example tools/package_name), or in one shared function with an explicit dev_patches entry, read by both the renderer and make-patches.
- Split the two base features into two repositories, or record the exception together with the mechanism that selects the package.
- Refuse 120000 and 160000 blocks in make-patches, with a toy test.

**Editor.** Confirmed against make-patches:167 and :194-205.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I went through the five parts one at a time. Parts 1, 2 and 5 hold up, part 3 holds up only in a narrower form, and part 4 is refuted.

(1) The committed recipe that the renderer generates: CONFIRMED. This is a rev-1 defect that rev 2 did not fix. The rev-1 judge said "Remove conda/recipe.yaml from decision 10's layouts, so no repository commits a derived recipe" (REVIEW1:1915-1920). Rev 2 keeps it anyway: "conda/recipe.yaml（渲染器生成，不手写）" (plan:282) and "由渲染器生成并提交" (generated by the renderer and committed, plan:288). The reusable workflow then runs the renderer again at build time (plan:253). So no release ever reads the committed copy. It only goes stale after the next make-patches, and a hand edit to it is silently overwritten. None of the owner rulings §0 11-19 (plan:47-60) covers this, and the plan gives no reason for departing from the judge.

(2) No source for the build number: CONFIRMED. The plan treats the build number as variable: the build string is `Isabelle2025_2_<build 号>` (plan:246), and the path-length gate assumes "build 99" (plan:316). But provenance.txt carries only `build_string_prefix` (make-patches:202), and the renderer computes only the "build string 前缀" (build string prefix, plan:251-252). Nothing feeds it a number. Bumping the build number is the channel's rule for any content change (isabelle-packaging-ci/conda/recipe.yaml:42; PACKAGING_DESIGN.md:60,181). Releasing a new feature version instead does not work. A second tag on the same commit would make gate 0 refuse every feature above it, because gate 0 needs exactly one tag at the merge-base (make-patches:97-101). One part of the challenge's required fix is already covered, though: a refusal to republish an existing version-and-build pair. publish-conda.yml:132-185 already refuses changed content under an existing filename. So only the input is missing. The precedent is release-isabelle-ai.yml:24-27 and :62 (`build_number` input, default "0", passed as `--build-num`).

(3) The package-name rule: PARTLY REFUTED. The plan states the exception in the same bullet: "dev 补丁按 light 计划叫 qiyuan-dev-patches" (plan:245). That matches the approved migration plan ("conda 名 qiyuan-dev-patches", ISABELLE_GIT_MIGRATION_PLAN.md:131-132). So the rule is not "wrong for dev_patches". Also, a path-length gate that used the plain rule would compute `isabelle-dev-patches` (20 characters) instead of `qiyuan-dev-patches` (18). It would overestimate by 2 characters and could never wrongly pass a path. What survives: both the renderer and make-patches gate 15.3 need the name, and the plan does not say where the rule and its exception live. make-patches already imports tools/common.py (make-patches:37), so one function there is the obvious home. The plan should say so.

(4) One repository holding two packages: REFUTED as a defect. RELEASE_CHECKLIST.md:242 does say "One repo, one package, one semver". But the channel's own repository already breaks that rule six times. isabelle-packaging-ci holds conda/recipe.yaml (isabelle), conda/metapackage/isabelle-ai, conda/data/isabelle-semantic-data, conda/components/isabelle-nunchaku, and conda/third-party/{json-spec,rocksdict}. Each has its own release-*.yml, and the repository is in PUBLISH_REPOS (sweep-old-versions.py:61-69). The rule sits in the "Versions" section, whose concern is two version sources drifting apart (RELEASE_CHECKLIST.md:243-247). Each feature package takes its version from its own provenance.txt, which is one source per package. The package is selected by the renderer's argument, `render-feature-recipe <包目录>` (package directory, plan:251). Only a small gap remains: the plan does not say that release-feature.yml takes the package directory as an input, or that the repository has one caller workflow per package.

(5) Symlink and gitlink blocks: CONFIRMED for symlinks, REFUTED for gitlinks. I tested toy repositories against a copy of make-patches' split logic, its :167 regex, its flat-name writing and gate (c), using both GNU patch 2.7.6 and git apply 2.43.0:
- Adding, retargeting or deleting a symlink (mode 120000) passes everything and would be released. That includes the ---/+++ pair, so decision 15.2 does not catch it either. The tool, meanwhile, refuses symlinked targets (plan:178, :334-335).
- The block for a retargeted symlink has its mode only on the `index … 120000` line. A fix that matches only "new file mode 120000" would miss it.
- A gitlink (mode 160000) passes :167 and 15.2, but gate (c) refuses it with both engines because the tree hash differs. The challenge's claim that "it would be released" is wrong for gitlinks.
- A typechange produces two blocks for one path. make-patches:169-170 writes both to the same file, and the second overwrites the first. Gate (c) stops this today only by accident.
- A plain "Binary files /dev/null and b/x differ" block has no ---/+++ pair. :167 does not catch it (it matches only `GIT binary patch`); 15.2 and gate (c) do. So plan:129-130, which says make-patches:167 refuses binary diffs, needs correcting.

Real exposure is low. Isabelle's pristine tree has only modes 100644 (3572 files) and 100755 (56 files), and /contrib is gitignored. Severity "minor" is right.

The editor's relaxation is empty, so there was nothing to weigh.

Experiment: All work was in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C21/ with a private HOME. The owner's repositories were only read.

1. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C21/cases/gate.sh copies make-patches:154-187: diff-tree -p --no-renames, the split, the :167 regex, flat-name writing, then `git archive base`, forward and backward replay, and a tree-hash comparison through a temporary index (common.py:155-162). I ran it with GNU patch -p1 -F0 and with git apply on seven toy repositories:
   - symlink_add, symlink_modify, symlink_delete: "PASSES … released" with both engines.
   - gitlink_add: gate (c), forward tree differs.
   - typechange: gate (c), does not apply.
   - binary: caught by gate (c); the block is a "Binary files … differ" line with no ---/+++ pair.
   - emptyfile: no ---/+++ pair, so 15.2 catches it.
2. /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C21/proto.py prototypes the fix: refuse any block whose header modes ("new file mode", "deleted file mode", "old/new mode", and the trailing mode on the "index" line) are not 100644 or 100755. It refuses all symlink and gitlink blocks and the typechange. It passes an ordinary modification, a new 100755 file, and a 100644 deletion.
3. Read-only checks:
   - `git ls-tree -r Isabelle2025-2/pristine` shows only modes 100644 (3572 files) and 100755 (56 files).
   - The pristine .gitignore ignores /contrib.
   - isabelle-packaging-ci has six recipe.yaml files with six distinct package names, each released by its own release-*.yml.
   - publish-conda.yml:132-185 refuses changed content under an existing filename.
   - release-isabelle-ai.yml:24-27 and :62 show the build_number input precedent.

Recommended fix: Five small edits, all within the author's delegated authority:

(a) Decision 12 (plan:282, :288): drop conda/recipe.yaml from both repository layouts. The renderer writes the recipe into the build's own temporary directory, and the plan states that no repository commits a rendered recipe. This is the rev-1 judge's instruction (REVIEW1:1915-1920).

(b) Decision 9 (plan:246, :251-253): give render-feature-recipe a `--build-number N` argument, and give release-feature.yml a `build_number` input, default "0", passed through as release-isabelle-ai.yml:24-27 and :62 do. The renderer writes `build.number: N` and `string: Isabelle2025_2_N`. Publishing goes through publish-conda.yml, whose guard (:132-185) already refuses changed bytes under an existing filename, so no new refusal logic is needed.

(c) Decisions 9 and 15.3: name one home for the package name. A function `package_name(feature)` in tools/common.py holds the `isabelle-<feature with _ changed to ->` rule plus the single `dev_patches → qiyuan-dev-patches` entry. The renderer and make-patches' path-length gate both import it.

(d) Decision 9 / 12: say that release-feature.yml takes the package directory as an input, and that isabelle-base-features has one caller workflow per package. The precedent is isabelle-packaging-ci's one release-*.yml per package. Optionally add one sentence noting the departure from RELEASE_CHECKLIST.md:242.

(e) Decision 15: extend make-patches:167 so it refuses any block whose header modes are not 100644 or 100755. That means the "new file mode", "deleted file mode", "old/new mode" lines and the trailing mode on the "index" line, which covers symlink add, retarget and delete and the typechange. Add a toy test next to test_make_patches.sh:104-106 for a symlink add and a symlink retarget. Correct plan:129-130 to say that plain "Binary files … differ" blocks are refused by 15.2 (no ---/+++ pair), not by :167. A gitlink fix is not needed for correctness, because gate (c) already refuses gitlinks, but the same mode check makes the refusal message clear.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed:
- (1) committed derived recipes (plan:282, :288 against REVIEW1:1915-1920);
- (2) the build number has no source (make-patches:202);
- (5) symlink blocks pass make-patches:167, decision 15.2 and gate (c) (defender-C21 gate.sh).
Partly refuted:
- (3) plan:245 states the dev_patches name; only the rule's home is missing;
- (4) isabelle-packaging-ci already holds six packages in one repository;
- gitlinks are caught by gate (c).

Changes:
- Drop conda/recipe.yaml from decision 12's layouts; render into the build's temporary directory only.
- The renderer takes --build-number N, and the release workflow takes a build_number input, default 0, as release-isabelle-ai.yml:24-27 and :62 do. publish-conda.yml:132-185 already refuses changed bytes under an existing filename.
- package_name(feature) lives in tools/common.py, with the single dev_patches entry, and both the renderer and make-patches' path gate import it.
- Say that the workflow takes the package directory as an input, with one caller per package in isabelle-base-features.
- make-patches refuses any block whose header modes are not 100644 or 100755, including the mode on the index line, with toy tests for adding and retargeting a symlink.
- Correct plan:129-130 on binary and rename blocks.

### C22 [minor] The second half of rev 1's owner question 10 (later versions of a feature that 2025.2-0 already carries) is settled by the author without a ruling

Section: Decision 10 (plan:263-266); §0 items 11-19 (plan:46-60)  ·  merged from: consistency-F16, landing-L17, user-F16

**Statement.** The question. Rev 1's owner question 10 had two parts (REVIEW1:104-110). Ruling 19 (plan:60) answers the first: every feature package declares isabelle >=2025.2,<2025.3. No ruling answers the second. It concerns a later version of a feature that isabelle-2025.2-0 already carries, for example expose_foreign 2:
(a) that later package declares a lower bound on the isabelle build number; or
(b) accept the residue: the tool refuses with exit 3, and the exit-0 hook tells the user to update isabelle.

The defect. Decision 10 implements (b) without saying so (plan:264-265). Ruling 17 delegates only wording and test decisions, "without changing the design" (plan:56), and rev 1's judge listed this as owner-only. The user-visible effect of (b): on 2025.2-0, `conda update isabelle-expose-foreign` succeeds, nothing is applied, and a message says to update isabelle. Option (a) would let the solver update isabelle automatically.

Required. Put the second part to the owner, with both options and their user-visible behaviour, or quote the ruling if one exists, and record the answer in §0.

**Editor.** Confirmed: §0 items 11-19 (plan:46-60) contain no answer.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: True).

The core claim survives. No owner ruling answers the second half of rev 1's question 10. Rev 2 adopts option (b) silently. I tried four refutations; three fail and one corrects the history.

1. Was the question ever put to the owner? Yes. This is the history correction, and it does not save the plan. The session transcript (~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl) shows:
- Assistant line 5318 (2026-10-23T04:24:09Z) posed both options of the second half. It added: "如果 k 改成 0，这个问题消失".
- The owner chose a pristine build (user line 5353, 04:45:53Z).
- The author then told the owner: "第 6 问（认不出的构建）和第 10 问后半（内置 feature 出新版）都消失了" (assistant line 5373, 04:46:51Z).
- The owner's next message (user line 5392, 04:56:56Z) asks only "问题 6 还存在吗？" and answers questions 7 and 8. No later user message mentions question 10. The compaction summary (line 5892) does not mention it either.
So the question was not left unasked; it was withdrawn on a false premise. Choosing k=0 changes only future builds. The published isabelle-2025.2-0 still carries expose_foreign/1: ~/miniconda3/pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_ID is 5533cd83156e, and ml_name_space.ML:67 has `hidden_structures = ["Signal"]`. Its info/index.json has `depends: []` and no constrains. The plan itself describes the leftover case (the residue) at plan:264-265 ("否则 exit 3 并提示更新 isabelle"). The owner's silence after a wrong "it has disappeared" is not a ruling. §0 items 11-19 (plan:46-60) record nothing.

2. Does ruling 13 cover it? No. "对改不了的 2025.2-0，用户换包后手动 apply 一次" (plan:51-52, 238) answers question 2, about relinking. It says nothing about a later expose_foreign landing on 2025.2-0.

3. Does ruling 21 force (b) anyway? Ruling 21 (migration plan:87-90) says "不是 isabelle 的版本或 build 号". That makes (b) the default. But rev 1's judge listed this question as owner-only (REVIEW1:41, :617), and the author himself put it to the owner. Ruling 17 delegates only wording and tests, "without changing the design" (plan:56). So rev 2 still needs either the owner's answer or a quoted ruling.

4. Is the leftover case real under rev 2's metadata? Yes, measured. In a toy channel, every feature depends on `isabelle >=2025.2,<2025.3` plus exact base pins, and build 1 is pristine:
- Environment with isabelle-2025.2-0 and expose-foreign 1: `conda update isabelle-expose-foreign` and `conda install isabelle-expose-foreign=2` both link expose-foreign 2 and keep isabelle-2025.2-0 (run3.out).
- Environment that also has light 1: `conda install isabelle-light-locale=2` and `conda update isabelle-light-locale` keep 2025.2-0 and swap in the whole version-2 chain (run2.out, variant b, L3 and L4).
- A fresh `conda create isabelle=2025.2=0 isabelle-expose-foreign` picks expose-foreign 2 (N1).
- In an environment that has the chain above expose_foreign, `conda update isabelle-expose-foreign` alone does nothing (L1), because the upper package's ==1 pin holds it.

The user-visible effect is worse than the challenge says. This follows from the plan's design and was not measured end to end. In L3/L4 the version-1 packages are unlinked, so their pre-unlinks run `unapply --feature F` (plan:232) and reverse light 1 and future_assign_interrupt 1. Then the version-2 post-links hit decision 3's broken-chain exit 3 (plan:162-164), and nothing is applied. A user whose light 1 worked ends up with no light at all, while `conda list` shows light 2.

Two corrections to the challenge's description of option (a):
- "The solver would update isabelle automatically" holds only for some spellings. The bracket form `isabelle[build_number=">=1"]` in depends makes every libmamba solve touching the package fail under conda 25.11.1, even a fresh create (A1-A4). conda then crashes in its error parser (conda_libmamba_solver/solver.py:952). Only `--solver classic` honours it (A5).
- A plain build-string match `isabelle >=2025.2,<2025.3 1` works under libmamba, and the solver moves isabelle to build 1 by itself. But that is an exact build pin, which ruling 21 and REVIEW1:58 excluded. A glob `[1-9]*` did not exclude build 0.
So a usable (a) needs either an exact build pin or a build-string prefix that the CI plan gives new pristine builds. The owner must be told this.

A related misattribution under ruling 19 (plan:60). The first half, "feature 包声明 isabelle >=2025.2,<2025.3", is also not the owner's words. The author announced "这是第 10 问的前半，我按'是'处理" (assistant line 5249, 04:00:56Z). The "赞同 (a)" quoted in ruling 19 answers question 8 (user line 5392).

Experiment: Read-only: plan:46-60, 232, 238, 247-248, 263-266, 300-303, 363-369; REVIEW1:41, 58, 104-108, 565, 609, 617; migration plan:87-90, 119-127; ~/miniconda3/pkgs/isabelle-2025.2-0/info/index.json, isa/etc/ISABELLE_ID and isa/src/Pure/ML/ml_name_space.ML:67; conda_libmamba_solver/solver.py:936-952.

Transcript: I extracted user messages, including queued ones, and assistant text from ~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4.jsonl with /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C22/extract_user.py and extract_asst.py. Output is in user_msgs.txt and asst_msgs.txt in the same directory. The key lines are 5249, 5318, 5353, 5373, 5392 and 5892.

Solver experiments: conda 25.11.1 with libmamba. HOME, CONDARC, CONDA_PKGS_DIRS and CONDA_ENVS_DIRS were private under .../review-ipc2/defender-C22/exp/run.KFLY, with --override-channels and file:// channels. Nothing outside the scratch directory was written. One aside: the first manual zsh call left $O unsplit and conda printed "Upload did not complete" for an error report. After that I set CONDA_REPORT_ERRORS=false and ran every call from bash.
- mkchan.py: isabelle 2025.2 builds 0 and 1, both without constraints, plus the tool. The expose-foreign, future-assign-interrupt and light-locale chain exists in versions 1 and 2. Each feature depends on `isabelle >=2025.2,<2025.3` and pins its base exactly (`==v=Isabelle2025_2_*`). Variant a adds a build-number bound to expose-foreign 2.
- run.sh produced run.out and run2.out. Variant b, legacy env (2025.2-0 + light 1): L1 update expose-foreign gives no change; L2 install expose-foreign=2 is unsatisfiable; L3 and L4 (light-locale=2 or update light-locale) swap in the version-2 chain and keep 2025.2-0; L5 `update --all` moves to build 1; N1 fresh create isabelle=2025.2=0 + expose-foreign gives expose-foreign 2.
- run3.sh produced run3.out. Legacy env with 2025.2-0 + expose-foreign 1: update or install=2 links expose-foreign 2 and keeps 2025.2-0.
- probe2.sh, variant a with bracket build_number: A1-A4 error under libmamba; A5 (classic) moves isabelle to build 1.
- mkchan_c.py: spec `isabelle >=2025.2,<2025.3 1` makes libmamba move the legacy env to build 1; spec `[1-9]*` keeps build 0.

Recommended fix: 1. Add an open item to §0 and put it to the owner. Say plainly that the author withdrew it on 2026-10-23 on a wrong premise ("k=0 makes it disappear"). Present both options with what the user sees:
- (b) On isabelle-2025.2-0, a later expose_foreign, or anything pinned to it, still installs. `conda update isabelle-light-locale` then reverses the working version-1 features in the pre-unlinks and applies nothing. `status` exits 3, and .messages.txt says to update isabelle. `conda update isabelle` repairs everything through ruling 13.
- (a) The solver moves the user off 2025.2-0 by itself. Under libmamba this cannot be spelled as `isabelle[build_number=">=1"]`, which breaks every solve. It needs either an exact build-string match, the exact pin ruling 21 excluded, or a build-string prefix on new pristine isabelle builds that the CI plan would add (decision 11). Record the answer in §0.
2. Until the owner answers, mark plan:264-265 as the provisional (b). Add to §6 one acceptance case: on 2025.2-0 with expose-foreign 1, update to a test expose-foreign 2. The install succeeds, .messages.txt names `conda update isabelle`, `status` exits 3, and the tree is unchanged.
3. In ruling 19 (plan:60), separate who decided what. The series bound was announced by the author (transcript line 5249), and the owner did not object. "赞同 (a)" answers question 8 only.

**Judge: confirmed → owner_decides.** Confirmed, and stronger than stated. The transcript shows the author told the owner that the question 'disappeared' (assistant line 5373, 04:46:51), which was a false premise: 2025.2-0 still carries expose_foreign/1. The owner never answered it; §0 items 11-19 record nothing. Rev 2 adopts option (b) at plan:264-265.

Defender-C22's solver runs show the real effect: `conda update isabelle-light-locale` on 2025.2-0 keeps 2025.2-0 and swaps in the whole version-2 chain. The pre-unlinks reverse the working version-1 features, and nothing is applied.

Changes:
- Put Q3 to the owner, saying plainly that the question was withdrawn on a wrong premise.
- Until the owner answers, mark plan:264-265 as provisional (b), and add an acceptance case: expose_foreign 2 on 2025.2-0 installs, the message names `conda update isabelle`, status exits 3, and the tree is unchanged.
- Separate the attributions in ruling 19 (plan:60): the series bound was announced by the author (transcript line 5249); the owner's 'agree (a)' answered rev 1's question 8 (self-installed trees).

### C23 [minor] The landing steps omit prerequisites that rev 1's judges listed: tools/ is uncommitted, the editable installs break at the rename, the directory move is unscheduled, files move into repositories that do not exist yet, dev_patches lacks tested records, and the 0.x section is incomplete

Section: §5 steps 1-3 (plan:348-352); decision 13 (plan:292-296); decision 12 (plan:283-287); §0 item 5 (plan:35); §2.2 (plan:85-89)  ·  merged from: landing-L14, user-F17, consistency-F14

**Statement.** (a) §0 item 5 says tools/ has already landed (plan:35), but `git -C contrib/my_better_isabelle_prover status --short` shows `?? tools/` and ` M README.md`. Step 1 rewrites README and step 2 edits make-patches, with no committed baseline. Rev 1's judge asked for a step 0 that commits tools/ (REVIEW1:1915-1933).
(b) Step 1 renames the package. That breaks the editable installs in miniconda base (0.1.1) and in .venv (0.1.0): see the `__editable__.my_better_isabelle_prover-*.pth` files, and `which -a my-better-isabelle` lists both. Rev 1's judge asked step 1 to say what replaces them (REVIEW1:1585).
(c) Whether contrib/my_better_isabelle_prover moves, and when the GitHub rename happens (it must precede the first PUBLISH_REPOS entry), is unscheduled. contrib/light_locale/tools/record_golden_metadata.sh:11 and .gitmodules depend on the path.
(d) Decision 13 moves the patches/*.md files into decision 12's repositories at step 1 (plan:292), but those repositories are created at step 3 (plan:350-352).
(e) Step 3's `make-patches dev_patches 1` needs tested records that cover HOL, HOL-IMP and HOL-ex (plan:285; make-patches gate (e), :137-151). `git notes --ref=tested show Isabelle2025-2/dev_patches` reports none, so these are builds that need the owner's order, and the step does not list them.
(f) The "Coming from 0.x" section (plan:293-295) lacks parts rev 1's judge required (REVIEW1:2105-2110):
- the recovery line: on 2025.2-0, `conda install --force-reinstall isabelle` restores an expose_foreign that 0.x reversed;
- the pointer to the section from the CONFLICT message;
- pip-installed end users in §2.2;
- updating Isa-Mini's `--category all` comments (Isa-Mini/conda/recipe.yaml:32, :142).

Required.
- Add step 0.
- Say what replaces the editable installs (with the owner's approval, since base is shared) and which command replaces `my-better-isabelle` for the sessions that call it.
- Decide and schedule the directory move and the GitHub rename.
- Move the .md files once their repositories exist.
- List the dev_patches builds in step 3.
- Complete the 0.x section.

**Editor.** Confirmed by git status and by the editable-install files. consistency-F14 contributes its landing parts here; its §6 (b) part is in C14 and its CLI part in C18.

**Relaxation proposed by the editor.** 

**Defender: confirmed** (needs owner: False).

I tried to refute each of the six parts. All six survive. Two are narrower than the challenge states, and one part leaves out a further gap. The plan says it took in every confirmed item of review 1 ("rev 2 吸收了评审的全部确认项", plan:4). For the landing items below, that is not true.

(a) CONFIRMED. §0 item 5 says tools/ has "已落地" (landed) (plan:35). But `git status --short` in the tool repository shows `?? tools/` and ` M README.md`, and the tip commit is still c7f9eb6. The README section "Working in the Isabelle source repository", which plan:131 cites as already there, is itself uncommitted: `git diff` shows it as 82 added lines. Step 1 rewrites README and step 2 edits make-patches (plan:348-349), with no committed baseline to diff against. Review 1's judge required "a step 0 that commits tools/" (REVIEW1:1911, :1928). Rev 2's §5 has no step 0 (plan:346-359). The author may commit only when the owner says "提交" (commit) (HANDOFF:29), so the step has to be written into the plan for the owner to order it.

(b) CONFIRMED, but narrower. The editable installs exist: `__editable__.my_better_isabelle_prover-0.1.1.pth` is in miniconda base and 0.1.0 is in .venv. Their finder maps the package to `.../my_better_isabelle_prover/my_better_isabelle_prover`, and `which -a my-better-isabelle` lists both. Review 1's C17 judge required step 1 to say what happens to them (REVIEW1:1583; the challenge cites :1585, which is a blank line). Rev 2 never mentions them: grep finds no "editable", ".venv" or "pip uninstall" outside the 0.x line.
- Two things shrink the issue. First, decision 15 makes make-patches import `git_apply` from the checkout (plan:222, :314), so C17's original blocker ("step 2 cannot run") is gone. Second, no script, skill or ROOT file calls `my-better-isabelle`. The only hits are comments in Isa-Mini and CI's pip-installed 0.3.0, which ruling 11 retires (plan:87-88). So the demand to say "which command replaces it for the sessions that call it" is moot.
- My toy test confirms the impact: after the package directory is renamed, the console script fails with ModuleNotFoundError, while interpreter start-up is unaffected.
- What survives is one missing sentence in step 1.

(c) CONFIRMED, as a missing statement rather than a design defect. Decision 1 renames the GitHub repository (plan:138), but no step in §5 schedules it. Nothing says whether contrib/my_better_isabelle_prover moves. These depend on that path: record_golden_metadata.sh:11, .gitmodules:39-41 and check_patch_sync.sh:21.
- A precedent in this repository shows the directory does not need to move. contrib/Semantic_Embedding has origin xqyww123/Isabelle_Semantic_Embedding. Its .gitmodules:26 still says Premise_Embedding.git, and PUBLISH_REPOS lists "xqyww123/Isabelle_Semantic_Embedding" (sweep-old-versions.py:65).
- The rename has to come before anything that writes the repository's name down: decision 9's caller workflows that call the reusable workflow, and the PUBLISH_REPOS entry (plan:252-254, :359).

(d) CONFIRMED. Step 1 carries out decision 13 in full (plan:348). Decision 13 moves the five patches/*.md files "到决定 12 的仓库" (to decision 12's repositories) (plan:292). Those repositories are created only at step 3 (plan:350-352), and decision 12's READMEs "搬来" (take over) those files (plan:281, :286). The files survive in git history, so nothing is lost, but the order as written cannot be carried out.

(e) CONFIRMED. Gate (e) requires tested records on the exact tip that cover required_sessions (make-patches:137-151; common.py:174-186). For dev_patches that is HOL, HOL-IMP and HOL-ex (plan:285).
- `git notes --ref=tested list` in contrib/Isabelle2025-2 shows only two records, for f8d760a and 6d8be01. `show` on dev_patches (30aab6e) prints "no note".
- The record also has to be made on the final tip, after the three new features are merged in, so it cannot be made today anyway.
- Step 3 lists "light 的完整构建" (light's full build) but no dev_patches build (plan:351-352), and it does not mark either build as needing the owner's order. Review 1's C21 judge asked for that marking.

(f) CONFIRMED, all four items. plan:293-295 has the invisibility line, the `unpatch --category dev` then `pip uninstall` sequence, and the ban on a bare `unpatch`. It lacks the following:
- The recovery line (REVIEW1:2108). It still matters: decision 10 shows expose_foreign as pre-applied without reading the files (plan:263-265), so a reversal done by 0.x stays invisible to the new tool.
- The pointer from the failure message. Decision 8's failure text lists only status, the git apply output and status/apply (plan:233-235), and §4 has no such pointer.
- Pip-installed end users in §2.2 (plan:85-89). Evidence they exist: Isa-Mini Agent/Injector/ROOT:24 and conda/recipe.yaml:152 invite users to run `--category all`, and Isabelle-MCP CHANGELOG.md:395-399 left 0.2.x users with patches applied.
- An update of Isa-Mini's comments (conda/recipe.yaml:32, :142, :152; Agent/Injector/ROOT:8-24; ROOT:15).
A further gap the challenge does not list: the judge's fourth bullet (REVIEW1:2109), that the dev patches now come only as qiyuan-dev-patches, is also missing. The challenge's severity, minor, is fair.

Editor's relaxation: none was proposed.

Experiment: My scratch directory is /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C23/. Everything I ran in the repositories was read-only.

(1) `git --no-optional-locks status --short` in contrib/my_better_isabelle_prover gives ` M README.md`, `?? ai-artifacts/`, `?? tools/`. `git ls-files` lists no tools/. `git diff --stat` shows README.md with 82 insertions: the "Working in the Isabelle source repository" section.

(2) In miniconda base, site-packages contains `__editable__.my_better_isabelle_prover-0.1.1.pth` and its finder, which maps `my_better_isabelle_prover` to `/home/qiyuan/Current/MLML/contrib/my_better_isabelle_prover/my_better_isabelle_prover`. Its direct_url.json says editable. .venv has the same for 0.1.0. `which -a my-better-isabelle` lists both.

(3) Toy test, in editable/ under the scratch directory: a venv with --system-site-packages, then `pip install --no-build-isolation --no-index -e` of a toy package `oldpkg` with a console script. The script printed "old ok". After `mv oldpkg newpkg`, the console script failed with "ModuleNotFoundError: No module named 'oldpkg'". `python -c` still printed "startup ok", so interpreter start-up is not affected.

(4) Callers: `/usr/bin/grep -rlI` for `my-better-isabelle` over *.sh, *.py, *.yml, *.yaml, *.toml, *.js and ROOT files, plus .claude/ and CLAUDE.md. Outside the tool itself it finds only Isa-Mini's comments and isabelle-packaging-ci's CI files (build.yml, check_patch_sync.sh, recipe.yaml), which ruling 11 retires. No script, skill or session calls it.

(5) Path dependants: record_golden_metadata.sh:11, check_patch_sync.sh:16-21 and :57-60, and .gitmodules:39-41.

(6) Precedent for keeping the directory: Semantic_Embedding's origin is xqyww123/Isabelle_Semantic_Embedding, .gitmodules:25-26 has path contrib/Semantic_Embedding with url Premise_Embedding.git, and PUBLISH_REPOS (sweep-old-versions.py:61-69) uses the GitHub name.

(7) In contrib/Isabelle2025-2, `git --no-optional-locks notes --ref=tested list` shows two notes, for 6d8be01 and f8d760a. `notes show Isabelle2025-2/dev_patches` (30aab6e) reports that the commit has no note. The private tree contrib/Isabelle2025-2-dev_patches exists.

(8) Plan text: grep for editable, .venv, pip uninstall, step 0 and GitHub finds only plan:138 (the rename) and plan:293-295 (the 0.x line). §5 (plan:346-359) has no step 0, no rename, no move, and no dev_patches build.

Recommended fix: The smallest set of edits, all author work. At execution time, the commit, the uninstall from shared base, the GitHub rename and the builds each still need the owner's word.

1. §5: add a new first step, step 0. On the owner's order, commit tools/ and the README section in the tool repository (today `?? tools/` and ` M README.md`). Every later step diffs against this commit. Change §0 item 5 to say that tools/ exists but is uncommitted, and that step 0 commits it.

2. Step 1: add one sentence. "The editable 0.1.x installs in ~/miniconda3 and .venv point at my_better_isabelle_prover/my_better_isabelle_prover. After the rename their `my-better-isabelle` fails with ModuleNotFoundError. Nothing calls it: CI pip-installs 0.3.0, which ruling 11 retires. With the owner's approval (base is shared), run `pip uninstall my-better-isabelle-prover` in both. During development the new tool runs from the checkout (`python -m isabelle_patch_control`), and make-patches imports it (decision 15)."

3. Decision 1: say that the local directory stays contrib/my_better_isabelle_prover, as contrib/Semantic_Embedding stays while its GitHub repository is xqyww123/Isabelle_Semantic_Embedding. Rename the GitHub repository at step 5, before the caller workflows and the PUBLISH_REPOS entry are written, and update the url at .gitmodules:41 in the same step.

4. Decision 13 and §5: step 1 only deletes the five .md files. Step 3 copies them from the step-0 commit (`git show <step-0 commit>:my_better_isabelle_prover/patches/....md`) into the new repositories' README.md.

5. Step 3: after dev_patches has merged local_datatype, and on the owner's order, run `run-tree contrib/Isabelle2025-2-dev_patches build HOL HOL-IMP HOL-ex`. This writes the tested record that gate (e) needs; none exists today. Only then run `make-patches dev_patches 1`. Also mark light's full build as run on the owner's order.

6. The "Coming from 0.x" section (decision 13), with its knock-on edits:
- Add: if a bare 0.x `unpatch` has already reversed expose_foreign on isabelle-2025.2-0, run `conda install --force-reinstall isabelle`, then `isabelle-patch-control apply` (plan:237-238).
- Add: the dev patches now come as qiyuan-dev-patches.
- End decision 8's failure text in .messages.txt, and §4, with the line "Patched with my-better-isabelle 0.x before? See `isabelle-patch-control help`, section 'Coming from my-better-isabelle 0.x'."
- §2.2: add the pip-installed end users (Isa-Mini Agent/Injector/ROOT:24 and conda/recipe.yaml:152; Isabelle-MCP CHANGELOG.md:395-399).
- Step 7: rewrite Isa-Mini's `--category all` and `dev`-category comments (conda/recipe.yaml:32, :142, :152; Agent/Injector/ROOT:8-24; ROOT:15) to point to qiyuan-dev-patches.

7. Fix the citation in the challenge: REVIEW1:1585 should be :1583.

**Judge: confirmed → author_fixes_no_rereview.** Confirmed:
- tools/ and the README section are uncommitted (`?? tools/`, ` M README.md`), although plan:35 says they have landed;
- the editable 0.1.x installs in base and .venv break at the rename (defender-C23 toy: ModuleNotFoundError);
- the GitHub rename and whether the directory moves are unscheduled;
- the .md files move into repositories that do not exist yet (plan:292 against :350-352);
- no tested record exists for dev_patches;
- the 0.x section lacks REVIEW1:2105-2110's items.

Changes:
- Add step 0: commit tools/ and the README section, on the owner's order. Correct plan:35.
- Step 1 says what happens to the editable installs: uninstall them in base and .venv with the owner's approval, since base is shared; nothing calls `my-better-isabelle`.
- Decision 1: the local directory stays contrib/my_better_isabelle_prover (precedent: contrib/Semantic_Embedding). Rename the GitHub repository before any caller workflow or PUBLISH_REPOS entry, and update .gitmodules:41 in the same step.
- Step 1 only deletes the .md files; step 3 copies them from the step-0 commit.
- Step 3 lists `run-tree contrib/Isabelle2025-2-dev_patches build HOL HOL-IMP HOL-ex` on the final tip, on the owner's order, before `make-patches dev_patches 1`; mark light's full build the same way.
- The 0.x section adds: the recovery line (`--force-reinstall isabelle`, then apply, on 2025.2-0); that the dev patches are now qiyuan-dev-patches; the pointer from the failure message; pip-installed users in §2.2; the update of Isa-Mini's comments (conda/recipe.yaml:32, :142, :152; Agent/Injector/ROOT:8-24).

### C24 [minor] The 1.0.0 PyPI release has no supported user and adds a release obligation

Section: Decision 1 (plan:137); decision 14 (plan:308-310)  ·  merged from: consistency-F18

**Statement.** Why PyPI has no user. Ruling 19 makes non-conda Isabelle trees unsupported (plan:60), and decision 2 uses the default tree only inside a conda environment (plan:146-151). The tool is therefore useful only inside a conda environment, where every feature package pulls in its conda package. make-patches imports it from the checkout (plan:221-222).

What PyPI costs. Publishing 1.0.0 to PyPI as well (plan:137, :308) adds RELEASE_CHECKLIST.md:243-245's obligation that conda never fall behind PyPI, because `pip install -U` would remove conda's .dist-info and orphan the conda half. It also adds one more run to the serial batch (C13), for no user the plan names. The owner's earlier decision said to rename the tool and publish it to conda (LIGHT_LOCALE_HANDOFF.md:1958, item 5).

Required. Publish 1.0.0 to conda only, or state who installs it from PyPI and why.

**Editor.** None. Developers who need the tool outside conda can install the checkout in editable mode.

**Relaxation proposed by the editor.** Publish to conda only. There is then one release path, no lockstep rule, and one fewer run in the batch.

**Defender: confirmed** (needs owner: True).

I tried to refute C24 and could not. Nobody in the plan installs the tool from PyPI, and the old tool's only PyPI consumer is being retired.

1. The plan names no PyPI user. Every PyPI mention in the plan is about the old tool or the CI that is going away (plan:55, :83, :87-88, :140, :270, :295, :348), apart from the release line itself (plan:137, :308-310).
   - The only code that ever pip-installed the tool is the packaging CI: `pip install my-better-isabelle-prover==${MBI_VERSION}` at isabelle-packaging-ci/.github/workflows/build.yml:219, and `pip download` at scripts/check_patch_sync.sh:33. PACKAGING_DESIGN.md:946-963 gives that CI as the reason PyPI mattered. Ruling 11 retires it (plan:87-88, :270-271).
   - Every developer use already runs from the checkout. make-patches gate (c) and (b2) import `git_apply` from the checkout (plan:221-222, :314), and D9 says development does not use the tool (plan:399).
   - Inside conda, every feature package depends on the conda tool package (plan:247).
   - I searched Isa-REPL, Isa-Mini, Isabelle_RPC, Semantic_Embedding, Isabelle-MCP and evaluation/. They contain no code caller of the tool, old or new; they only mention it in comments.

2. The owner never ruled on PyPI.
   - The 2026-10-11 decision says rename the tool and "发布到 conda" (publish to conda), with no PyPI. The right file is /home/qiyuan/Current/MLML/ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1958, item (5), and :1962. The root-level LIGHT_LOCALE_HANDOFF.md has only 3 lines, so the challenge's citation path is ambiguous.
   - Ruling 16 (plan:55) mentions PyPI only to keep the old 0.3.0.
   - Rev 1 asked the owner about the PyPI and conda names (plan.rev1:305). Rulings 11-19 never answer it.

3. The lockstep obligation is real, but only if PyPI exists. RELEASE_CHECKLIST.md:243-245 applies "If the project also ships to PyPI". I measured it in a venv with a toy distribution:
   - When a newer copy was on an index, `pip install -U` reported "Found existing installation ... Successfully uninstalled 1.0.0" and replaced the installed .dist-info with its own.
   - With no copy on any index, `pip install` and `pip install -U` both reported "Requirement already satisfied" and never needed the index.
   - So the checklist's interop check, "pip install NAME saying already satisfied" (RELEASE_CHECKLIST.md:639), still passes with no PyPI release.

4. The owner has done this before. isabelle-rpc stopped PyPI at 0.3.0 and has been conda-only since (Isabelle_RPC/conda/recipe.yaml:33; release-conda.yml:272-273). Isa-Mini shows the two channels drifting apart (Isa-Mini/conda/recipe.yaml:42-43).
   - The two release paths would also be of different kinds. RELEASE.md describes a by-hand twine upload ("There is no CI", RELEASE.md:1-5), and plan:296 keeps that file. Meanwhile plan:309 promises a release workflow that the tool repository does not have: it has no .github/ directory.

5. On elegance, a PyPI listing also invites `pip install isabelle-patch-control`, for example from 0.x users who installed with pip (plan:293-295).
   - Outside conda, that install refuses to run (plan:146-151: exit 2 or 3).
   - Inside conda, it creates the "pip install first, then conda install" stale .dist-info case, which RELEASE_CHECKLIST.md:286-287 says no packaging choice can fix.
   - Publishing to conda only removes the lockstep rule entirely, instead of asking every future release (1.0.1, 1.1, ...) to remember it. Plan:310 orders conda before PyPI for the first batch only.

Corrections to the challenge, none of which change the verdict:
   (i) "Useful only inside a conda environment" is too strong. The directory interface (plan:219-220) and explicit --isabelle-home/--features-dir (plan:146-151) run anywhere. But those uses belong to the owner's development and gates, served by the checkout, and ruling 19 makes non-conda trees unsupported (plan:60). Appendix A's "工具在非 conda 环境里拒绝运行" (the tool refuses to run outside conda, plan:443) overstates decision 2 in the same way.
   (ii) The plan does honour the ordering for the first release (plan:310). The cost is the ongoing obligation, not an unhandled defect.
   (iii) For this tool, pip -U would not orphan an "Isabelle half". It would leave the conda record pointing at pip-owned files, and could run a version outside the feature packages' `<2` bound (plan:247).
   (iv) I did not verify the C13 "serial batch" claim. Plan:310 does add one more ordered release step.

The editor's relaxation is sound: one release path, no lockstep rule, one fewer step in the batch. Its only cost is leaving the PyPI name unclaimed, and the plan makes no argument for claiming it.

Experiment: I worked in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C24/:
- A venv (venv/, pip 24.0, Python 3.12).
- A toy distribution `isabelle-patch-control-toy` 1.0.0 (toy/) and a 1.0.1 copy (toy101/), built to a wheel in wh/.

Steps:
(a) I installed 1.0.0 locally with `pip install --no-deps --no-build-isolation --no-index ./toy`. This is how the conda recipes create the .dist-info (RELEASE_CHECKLIST.md:280-282).
(b) `pip install --index-url http://127.0.0.1:9/simple isabelle-patch-control-toy` (an unreachable index), `pip install --no-index ...` and `pip install -U` against the unreachable index all printed "Requirement already satisfied ... (1.0.0)". So the interop check needs no PyPI copy.
(c) `pip install -U --no-index --find-links wh isabelle-patch-control-toy`, with 1.0.1 available, printed "Found existing installation: 1.0.0 / Successfully uninstalled ... / Successfully installed 1.0.1", and the 1.0.0 .dist-info was gone. This is the takeover that the lockstep rule guards against, and it exists only when a second index holds a newer version.

Source checks:
- grep of the plan for pip and PyPI.
- grep of the migration plan, RECORD.md and the consumer repositories for any tool caller.
- Read LIGHT_LOCALE_HANDOFF.md:1958/:1962, rev 1's owner questions (plan.rev1:305, REVIEW1 question 9), the precedent comments in the Isabelle_RPC, Isa-Mini and Semantic_Embedding recipes, and the tool's RELEASE.md and directory listing (no .github/).

Recommended fix: The smallest fix publishes 1.0.0 to conda only:
- Decision 1 (plan:137): "conda 包名 `isabelle-patch-control`（noarch python）；不发 PyPI。pyproject 的 `project.name` 仍是 `isabelle-patch-control`，只供配方里的 `pip install . --no-deps` 生成 .dist-info（RELEASE_CHECKLIST.md:280-282）与开发者的 editable 安装。" Keep "旧 PyPI 包停在 0.3.0、不下架" (the old PyPI package stays at 0.3.0 and is not yanked).
- Decision 14 (plan:308-310): drop "PyPI `isabelle-patch-control 1.0.0` +" and the clause "工具的 conda 包不晚于 PyPI 上传" (the tool's conda package goes out no later than its PyPI upload).
- Decision 13 (plan:296): RELEASE.md is rewritten for the conda release workflow and drops the twine/PyPI procedure. The checklist's "pip install NAME says already satisfied" check stays; it passes without PyPI.
- The "Coming from my-better-isabelle 0.x" section (plan:293-295) adds one sentence: the new tool comes with conda, pulled in by any feature package, not with pip.

Ask the owner to confirm this in one line ("1.0.0 只发 conda，与你 10-11 说的一致"), because it changes where the tool is published and no ruling settled that.

Optionally, while editing, align Appendix A's "工具在非 conda 环境里拒绝运行" (plan:443) with decision 2. The tool refuses only when the defaults would be used outside conda; explicit --isabelle-home/--features-dir and the directory interface still run there.

**Judge: confirmed → owner_decides.** Confirmed:
- the plan names no PyPI user;
- the only pip consumer, the packaging CI (build.yml:218-253), is retired by ruling 11;
- the owner's 2026-10-11 decision said conda (ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1958);
- the lockstep rule (RELEASE_CHECKLIST.md:243-245) would bind every future release;
- the interop check 'pip says already satisfied' passes without PyPI (defender-C24 venv).

Put Q4 to the owner. If the answer is conda only, edit:
- decision 1 (plan:137): pyproject keeps project.name only for the recipe's `pip install . --no-deps` and editable installs;
- decision 14 (plan:308-310): drop the PyPI half and the conda-before-PyPI clause;
- decision 13: RELEASE.md describes the conda release;
- the 0.x section: the new tool comes with conda.
Optionally align plan:443.

### C25 [minor] The glossary coins second names for concepts the migration glossary already names, and leaves two terms undefined

Section: 术语 (plan:11-24); decisions 3, 5, 10 (plan:160, :186, :261); §5 step 4 (plan:354)  ·  merged from: consistency-F17

**Statement.** The defect. The plan adopts the migration glossary (plan:13) and then coins two second names:
- 工具 (tool, plan:16) for the glossary's 补丁工具 (patch tool; ISABELLE_GIT_MIGRATION_PLAN.md:22);
- 预先打好的 feature (pre-applied feature, plan:21) for the concept the migration glossary keeps as k, the first k chain nodes, 前 k 节 (:47; k=1 for 2025.2-0).
It also uses 链底 (bottom of the chain; plan:160, :354) and 固定记录 (fixed record; plan:49, :261) without defining them. CLAUDE.md's consistent-terminology rule forbids a second name for a concept that already has one, and rev 1's judge (C28) asked for pointers to the migration glossary and for 前 k 节 (REVIEW1:2462).

Required.
- Use 补丁工具, and 前 k 节 (k=1, historical).
- Define the bottom of the chain once, in decision 3.
- Call the record "the LEGACY_BUILDS entry" everywhere.

**Editor.** None.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

C25 makes four claims. Three are refuted. One survives, and it is small.

1. Refuted: "工具 (tool) is a second name for 补丁工具 (patch tool)."
- 工具 is the head noun of the canonical term. The approved migration plan uses this same short form itself. At ISABELLE_GIT_MIGRATION_PLAN.md:99, 111, 126, 148, 301, 303, 362, 405, 406 and 422-427, bare 工具 means the patch tool. That includes the exact compounds the plan uses: 旧工具 (old tool) at :126, inside ruling 30, and 工具仓库 (tool repository) at :301. It also includes §5.3's "只反打工具自己打的" (only reverse what the tool itself applied) at :424.
- The plan defines the short form in its glossary (plan:16) and uses it the same way everywhere. 工具 occurs 53 times and always means this program. The full form 补丁工具 appears once, in the title (plan:1).
- The plan's use is actually less ambiguous than the migration plan's. There, bare 工具 also names other things: "Isabelle_RPC unicode 工具" at :372 and "Scala 工具" at :444 and :590.
- Rev 1 had the identical entry (PLAN.rev1.md:17-18). Neither rev-1 challenge C28 nor its judge objected to it (REVIEW1:2401-2465).
- Replacing 53 occurrences would be churn, not a fix.

2. Refuted: "链底 (bottom of the chain) is undefined."
- Decision 3, item 1 is its definition, given case by case: "链底是…：`etc/ISABELLE_ID` 在决定 10 的记录里 → 底是记录给出的发布 tag；否则底是 `<R>/pristine/<ISABELLE_ID>`" (plan:160-161). In words: if the tree's etc/ISABELLE_ID is in the record of decision 10, the bottom is the release tag that record gives; otherwise it is the pristine tag for that ID.
- That is its first occurrence, and it sits exactly where C25's own fix wants it ("define it once, in decision 3").
- Every later use agrees with that definition: 底以上 (above the bottom) at plan:186, 194 and 213; 底以下 (below the bottom) at :193; 链底 at :263 and :355.
- The citation plan:354 is off by one; the occurrence is at :355.
- One wording wart remains. plan:160 says "链底是树自己的记录" (the bottom is the tree's own record). In that one sentence, 记录 (record) means both the tree's etc/ISABELLE_ID and decision 10's table.

3. Refuted: "固定记录 (fixed record) is undefined, so call it 'the LEGACY_BUILDS entry' everywhere."
- 固定记录 is the approved migration plan's own word. Ruling 30 says "含 expose_foreign/1 这一事实由补丁工具的固定记录承载" (the fact that the build contains expose_foreign/1 is carried by the patch tool's fixed record; ISABELLE_GIT_MIGRATION_PLAN.md:121).
- The plan points ahead to decision 10 at plan:49. Decision 10's heading is "2025.2-0 的固定记录" (the fixed record for 2025.2-0; plan:261), and its first sentence names it as `LEGACY_BUILDS = {...}` (plan:263). That is a term defined and then bound once to its code identifier.
- Renaming it everywhere to a code identifier would move the plan away from the ruling's own word.
- What is true is that several pointer phrases refer to it: 决定 10 的记录 (decision 10's record; plan:97, 160), 一条记录 (one record; :42) and 记录项 (record item; :193). These are references, not new names. Only plan:160, where 记录 carries two senses, and plan:193 could trip a reader.

4. Confirmed: "预先打好的 feature (pre-applied feature) is a second name next to 前 k 节 (the first k chain nodes)."
- The bolded glossary noun at plan:21 occurs nowhere else in the plan. A grep finds 预先打好 only at :21 and at :32, which quotes ruling 21.
- The plan already points to the migration glossary's 前 k 节 (plan:13 and :42; k is defined at migration :47 and kept as historical by :122-123).
- The body describes the same object (expose_foreign/1 inside isabelle-2025.2-0) a third way: "底以下的记录项显示 pre-applied" (record items below the bottom are shown as pre-applied; plan:193).
- So the glossary carries an unused extra noun, which is what rev-1's judge asked to remove. The judge's instruction was to use 前 k 节 and turn glossary entries into pointers (REVIEW1:2462).
- The harm is small because the noun is never used in the body.

Relaxation: there is none to weigh. The owner does not need to rule. Wording decisions were delegated to the author (plan:56; migration :126).

Adjacent, same kind of defect, outside C25: the plan uses two names for the top of the chain. It says 链尾 (end of the chain) at plan:213 and :327, but 链顶 (top of the chain) at :354, :355 and :375. The migration plan's word is 链顶 (:345).

Experiment: All checks were read-only greps with /usr/bin/grep -n -F, because the default ugrep obeys .gitignore and hit complexity errors on this text. They ran over the plan, the plan's rev 1 copy, REVIEW1 and the migration plan. The per-term line numbers are saved in /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C25/term-occurrences.txt.

Results:
- 补丁工具: plan line 1 only; 42 lines in the migration plan.
- Bare 工具: 53 uses in the plan, all meaning this program; 23 lines in the migration plan, most meaning the patch tool.
- 预先打好的 feature: plan :21 only; absent from the migration plan.
- 前 k 节: plan :13 and :42; migration :122, 144, 226, 227, 404, 423, 424, 432, 435, 507.
- 链底: plan :160 (the definition), :263, :355.
- 底以上 (above the bottom): plan :186, 194, 213. 底以下 (below the bottom): plan :193.
- 固定记录: plan :49, 68, 261; migration :121.
- LEGACY_BUILDS: plan :263, 302, 353.
- 链尾: plan :213, 327. 链顶: plan :354, 355, 375; migration :345.

I also read the rev-1 glossary (PLAN.rev1.md:8-19) and C28 in full (REVIEW1:2401-2465).

Recommended fix: These are hand edits, as CLAUDE.md requires for plan documents.

(1) The surviving part. Delete the glossary entry 预先打好的 feature at plan:21. Fold its content into the 前 k 节 pointer at plan:13, along these lines: "前 k 节（迁移方案 glossary 的 k，:47）只剩历史含义：只有已发布的 isabelle-2025.2-0 有，k=1，即 expose_foreign/1，由决定 10 的固定记录承载，status 显示 pre-applied；以后的构建 k=0（§0 第 11 条）。" In English: the first k chain nodes now have only a historical meaning; only the published isabelle-2025.2-0 has them, k=1, namely expose_foreign/1; decision 10's fixed record carries this fact; status shows it as pre-applied; later builds have k=0.

(2) At plan:193, replace "底以下的记录项显示 pre-applied" (record items below the bottom are shown as pre-applied) with "固定记录给出的 feature（链底及以下）显示 pre-applied" (the feature the fixed record names, at or below the bottom, is shown as pre-applied).

(3) Optional. At plan:160, replace "链底是树自己的记录：" (the bottom of the chain is the tree's own record) with "链底由树的 etc/ISABELLE_ID 决定：" (the bottom of the chain is determined by the tree's etc/ISABELLE_ID), so that 记录 in that sentence means only the fixed record. Keep the definition where it is.

(4) Do NOT rename 固定记录 to "the LEGACY_BUILDS entry". 固定记录 is ruling 30's own word (migration :121), and decision 10 already ties it to LEGACY_BUILDS (plan:261-263).

(5) Do NOT replace 工具 with 补丁工具. At most, add "（即迁移方案 glossary 的补丁工具）" (that is, the patch tool of the migration glossary) to the entry at plan:16.

(6) Adjacent fix, outside C25: at plan:213 and :327, write 链顶 (top of the chain) instead of 链尾 (end of the chain), matching plan:354-355, :375 and migration :345.

**Judge: partially_confirmed → author_fixes_no_rereview.** Partly refuted:
- 工具 (tool) is the migration plan's own short form (ISABELLE_GIT_MIGRATION_PLAN.md:126, :301, :424) and is defined at plan:16;
- 链底 (bottom of the chain) is defined at plan:160-161;
- 固定记录 (fixed record) is ruling 30's own word (migration :121) and is tied to LEGACY_BUILDS at plan:261-263.
Confirmed: the glossary entry 预先打好的 feature (pre-applied feature, plan:21) is a second name next to 前 k 节 (the first k chain nodes) and is unused in the body.

Changes:
- Delete plan:21 and fold its content into the 前 k 节 pointer at plan:13 (k=1, historical, carried by the fixed record, shown as pre-applied).
- Reword plan:193 and plan:160 so that 记录 (record) has one meaning. C3's rewrite changes both lines anyway.
- Write 链顶 (top of the chain) instead of 链尾 (end of the chain) at plan:213 and :327, matching :354-355, :375 and migration :345.
- Do not rename 工具 or 固定记录.

### C26 [minor] Stale citations, wrong statements, contradictions between sections, and rev 1's C9 and C29 fixes that did not land

Section: Header (plan:4); §0 (plan:39-40, :50, :57-58); §2 (plan:88, :107-110, :129-130); decisions 8, 10, 13 (plan:238, :266, :292); §7 (plan:371-401)  ·  merged from: consistency-F12, consistency-F13, conda-conda-11

**Statement.** Fix each of these by hand.
(1) plan:109 cites link.py's reversed(...) for the unlink order. link.py:1042 is the rollback; the unlink order comes from solve.py:1450-1452 (rev 1's C29 ruling, REVIEW1:2531-2538).
(2) plan:107 keeps the claim that the solver switches the isabelle build along the way. Rev 1's defender could not reproduce it, because conda tries a frozen solve first (REVIEW1:265).
(3) plan:292 speaks of five patches/*.md files. There are four, plus patches/Isabelle2025-2/register_thy.md.
(4) §0 item 8 and §7 tabulate reader2's findings 1-16 and decisions D1-D11 (plan:39-40, :371). reader2 also has D12 (readers_impl0/reader2_patch_scheme.md:225). Rev 1's judge (C9) asked §7 to use the handoff's 19-item D4 list, in its numbering (LIGHT_LOCALE_HANDOFF.md:1979; REVIEW1:920-921). Most items are now settled by rulings 11-19; the table should say which ruling settles which of the 19.
(5) plan:129-130 says make-patches refuses binary diffs. Its regex (make-patches:167) matches only "GIT binary patch", which `git diff-tree -p` never prints without --binary. Decision 15.2 is what actually catches a binary block (C21).
(6) plan:57-58 states as fact that pixi and micromamba do not run link scripts. reader2 marks this unverified (reader2_patch_scheme.md:202), and libmamba, micromamba's engine, contains run_script and "failed to execute pre/post link script for". Keep the conda-only decision, which ruling 17 delegated, but correct or drop the reason.
(7) Ruling 12 is recorded as "钩子" (hooks) at plan:50 and as "post-link" at ISABELLE_GIT_MIGRATION_PLAN.md:123-124. Align the two.
(8) plan:88 cites build.yml:284-293 for the hg commit, which is at :290-296.
(9) plan:238 tells 2025.2-0 users to run apply by hand after a clone. That is unnecessary: a clone links every package, so the feature packages' post-links re-apply the chain (plan:107-108; conda/misc.py:274-357; critic-conda/run3.out under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/). Only `--force-reinstall isabelle` needs the manual apply. The clone works only with C5's skip rule.
(10) plan:266 justifies the release freeze by saying the tool would otherwise treat a patched tree as pristine. By decision 3.2, an unknown ISABELLE_ID simply fails to link; the real hazard is exit 3 for every feature user. Also ask the CI plan to record the freeze in isabelle-packaging-ci/RELEASE.md, as rev 1's judge asked (REVIEW1:1232-1234).
(11) plan:4 says rev 2 absorbed every confirmed item of review 1. Challenges C1-C5, C8, C10, C12-C14, C17-C19, C21, C23 and C25 of this review list confirmed rev-1 items that did not land. Soften the sentence.

**Editor.** Each item was checked against the cited source. conda-conda-11's other items are in C9 and C19; consistency-F13's tree-passing item is in C18, and its chmod item in C19.

**Relaxation proposed by the editor.** 

**Defender: partially_confirmed** (needs owner: False).

I went through all eleven sub-items against the sources. Nine stand. Item (2) I refute on substance. Two more are confirmed but need a different fix from the one proposed: item (8) gives wrong replacement line numbers, and item (10)'s RELEASE.md request is aimed at the wrong document.

(1) CONFIRMED. plan:109 cites "core/link.py 的 reversed(...)" for the unlink order. link.py has `reversed` only at :1042 and :1154. :1042 is the rollback ("Rolling back transaction") and :1154 is inside _reverse_actions. The unlink order actually comes from solve.py:1450-1452, and the link order from :1453. Rev 1's C29 judge asked for exactly this change (REVIEW1:2531-2538), and it did not land.

(2) REFUTED as a defect; at most a wording tweak. Rev 1 never had this phrase (rev1 has no 顺带), so rev 2 did not "keep" it; it added it. The phrase is also true. `conda install` first tries a frozen solve (conda/cli/install.py:370-371). Only if that fails does it re-solve without freezing (:400-408). My toy channel shows both cases. An unrelated install kept isa 1.0-0. Installing a package that needs `isa 1.0 1` switched isa from 1.0-0 to 1.0-1, and feat's post-link did not run. So "the solver switches the isabelle build along the way, and only isabelle's hooks run" is a real case. What the rev-1 judge said to drop was the claim about an *unrelated* install, which plan:107 does not make.

(3) CONFIRMED, trivial. There are four top-level patches/*.md files plus patches/Isabelle2025-2/register_thy.md (find). Decision 12 names all five, so nothing is lost. This was an explicit item in rev 1's C29 judge list, and it was not fixed.

(4) PARTIALLY CONFIRMED. The light plan's D4 says "清单在交接文件" (LIGHT_LOCALE_PLAN_REV37.md:7796), which is the 19 items at LIGHT_LOCALE_HANDOFF.md:1979. Plan:39 instead calls the list "reader2 发现 1–16 与 D1–D11". That misattributes the ruling's list. It also leaves out D12 (reader2_patch_scheme.md:225). The plan never cites the handoff, and C9's judge asked for the handoff's numbering (REVIEW1:920-921), which rev 2 does not use. But I mapped all 19 handoff items onto rev 2's §7 rows, and every one is answered. Its status column already names the ruling that settles each row, and D12's substance is the row for finding 14. So only the attribution, the D12 row and the numbering need fixing, not the content.

(5) CONFIRMED. The regex at make-patches:167 can never match a binary block. `git diff-tree -r -p --no-renames` prints "Binary files a/x and b/x differ" without --binary (toy: 0 regex hits, the block is ACCEPTED). GNU patch even skips such a block with rc=0. So today only gate (c)'s tree-hash comparison stops it. Under rev 2, git apply fails on it, and decision 15.2 (no ---/+++ pair) is what explicitly rejects it. A related point the challenge missed: in the same sentence, "拒绝改名" is also false. With --no-renames, `similarity index` never appears, and a rename comes out as a deletion block plus a creation block, both released (toy).

(6) CONFIRMED, and stronger than stated. micromamba 2.8.1, run from pkgs/micromamba-2.8.1-0 against a private root prefix, ran the toy package's post-link with PREFIX set. On `micromamba remove` it ran no pre-unlink. libmamba also contains run_script and "failed to execute pre/post link script for". py-rattler 0.25.0, pixi's engine, has execute_link_scripts defaulting to False (installer.py:286, :339). So it is not true that "micromamba does not run link scripts". The real hazard is worse: under micromamba a feature gets applied, and removing the package leaves its patches in the tree with nothing recording them. The conda-only decision (ruling 17) stands; only its reason needs replacing.

(7) CONFIRMED as a mismatch between the two documents, but the plan is the faithful side. plan:50 records ruling 12 as "钩子失败一律 exit 0", and migration :123 records it as "feature 包的 post-link 失败一律 exit 0". The question the owner answered was REVIEW1:50, option (a): "Every feature hook exits 0 … A failed pre-unlink's message lists…". That covers both hooks, which matches the plan. The fix belongs in the migration plan's record, or as a note in the plan. Either way the practical difference is nil, because conda only warns on a failed pre-unlink (link.py:1676-1683).

(8) CONFIRMED, but the proposed replacement is also wrong. Step (4) of build.yml is :292-300: the name is at :292, `hg addremove` at :296 and `hg commit` at :297. So both the plan's :284-293 and the challenge's :290-296 are off. Also, plan:87's :218-246 misses the `patch --category user` call at :253; step (3) runs :204-256.

(9) CONFIRMED. A clone copies the untracked files and then calls explicit(), which links every package and runs every post-link (misc.py:274-357). critic-conda/run3.out shows feature a's post-link running in the clone of an env built on isa build 0 (the toy stand-in for 2025.2-0) and re-applying a. The plan says the same at :107-108 and :239-240, so the manual apply that plan:238 prescribes "after a clone" contradicts the plan itself. Ruling 13 asks for a manual apply only after a package swap. Whether the clone also succeeds when light's created files were already copied in depends on apply skipping a created file that is present with identical content; that is the challenge's cross-reference to C5, which I have not seen.

(10) CONFIRMED in substance, with a correction to the fix.
- On the reason: build.yml:296-300 and :370-373 make every CI run's ISABELLE_ID a fresh hg commit. Under decision 3.1, the chain bottom then becomes pristine/<new ID>, while expose_foreign's base_tag is pristine/89701cf1768e (migration :29). Nothing links, so every feature user gets exit 3 and an error in .messages.txt. The tree is not silently mistaken for a pristine one, so the reason at plan:266 overstates and misnames the hazard.
- On the record: RELEASE.md has no freeze note (grep). Asking the *CI plan* to record it comes too late. The freeze matters only until the CI plan lands, so it must be written into RELEASE.md now.

(11) CONFIRMED on this challenge's evidence alone. Items (1), (3) and (4) are rev-1 judge instructions (C29, C9) that did not land, so "吸收了评审的全部确认项" (plan:4) is false. I did not see the other challenges this item lists.

The relaxation field is empty. The editor's rebuttal holds except for items (2) and (8), and for the RELEASE.md targeting in item (10).

Experiment: All experiments are under /tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review-ipc2/defender-C26/.

(a) bin1/: a toy git repo with one binary file, one text file, and later a rename. `git diff-tree -r -p --no-renames base HEAD` prints "Binary files a/bin.dat and b/bin.dat differ" with no ---/+++ lines. The make-patches:167 regex gives 0 hits, and the block is ACCEPTED by the script's own split-and-match logic. `git apply --check` fails on it ("cannot apply binary patch … without full index line"). `patch -p1 -F0 --dry-run` prints "checking file bin.dat" and returns rc=0. A rename comes out as a "deleted file mode" block plus a "new file mode" block, with 0 "similarity index" lines.

(b) solver/run.sh, output in run.out: conda 25.11.1, private HOME, CONDARC, pkgs cache and envs dir, and a file:// noarch channel with isa 1.0 builds 0 and 1, feat (depends on isa >=1.0,<1.1), other, and needs1 (depends on "isa 1.0 1"). Create with isa=1.0=0 and feat. Installing `other` keeps build 0. Installing `needs1` prints "isa 1.0-0 --> 1.0-1", and the tree's ID becomes id1. feat's post-link did not run.

(c) mamba/run.sh, output in run.out: the micromamba 2.8.1 binary from ~/miniconda3/pkgs/micromamba-2.8.1-0, run read-only with a private HOME and MAMBA_ROOT_PREFIX, --no-rc, and a file:// channel. `create` ran the package's .feat-post-link.sh (the hook log shows "POSTLINK feat PREFIX=<env>"). `remove` unlinked the package and ran no pre-unlink (the hook log is empty).

(d) Source reads:
- link.py `reversed`: :1042 (rollback) and :1154 (_reverse_actions).
- solve.py:1450-1453: unlink and link order.
- cli/install.py:365-408: frozen solve first, unfrozen retry.
- misc.py:274-357: clone copies untracked files, then calls explicit().
- link.py:1676-1683: a failed pre-unlink only gives a warning.
- `strings libmamba.so.4.0.1`: run_script, post-link, .messages.txt, "failed to execute pre/post link script for", "mamba does not support pre-link scripts".
- py-rattler installer.py:286 and :339: execute_link_scripts=False by default.
- build.yml step (4) is :292-300 (hg addremove :296, hg commit :297), the patch call is at :253, and the ISABELLE_ID assertion is at :370-373.
- `find patches -name '*.md'`: 4 at top level plus Isabelle2025-2/register_thy.md.
- reader2_patch_scheme.md: :202 (finding 16, "未核") and :225 (D12).
- The handoff's 19 items are at LIGHT_LOCALE_HANDOFF.md:1979. LIGHT_LOCALE_PLAN_REV37.md:7796 says "清单在交接文件".
- RELEASE.md has no freeze note.

(e) critic-conda/run3.out was re-read: in a clone of an isa-build-0 env, feature a's post-link runs and re-applies a.

Recommended fix: Hand edits to the plan, in order:

(1) plan:109: replace "（core/link.py 的 reversed(...)）" with "（core/solve.py:1450-1452；链接序 :1453；link.py:1042 的 reversed 是回滚）".

(2) Optional: qualify plan:107 as "某个请求需要另一个 isabelle build 时求解器换掉它（conda install 先做冻结求解，cli/install.py:370-371、:400-408；无关的安装不换）".

(3) plan:292: "四份 patches/*.md 与 patches/Isabelle2025-2/register_thy.md".

(4) §0 item 8 (plan:39-40): "清单是交接文件 LIGHT_LOCALE_HANDOFF.md:1979 的 19 条（细节见 reader2_patch_scheme.md 发现 1–16、D1–D12）".
- §7 header: change D1–D11 to D1–D12.
- Add the row "D12 补丁文件命名 | 同发现 14 | 已落地".
- Tag each row with its handoff number, for example "发现 2（交接 (1)）". The answers themselves need no change.

(5) plan:129-130: "拒绝 mode 变化（:167-168）；二进制块（`Binary files … differ`）:167 的正则匹配不到，今天由门禁 (c) 的树哈希拦下，决定 15.2 起由'无 ---/+++'规则明确拒绝；改名在 --no-renames 下拆成删除+新建，照常发布". Optionally have decision 15 replace the dead `GIT binary patch|similarity index` alternatives with `^Binary files `.

(6) Fix the reason at plan:57-58, :390 and :424: "只支持 conda：micromamba（2.8.1 实测）跑 post-link、卸包时不跑 pre-unlink，会留下没人记账的补丁；pixi 的 rattler 默认不执行 link 脚本".

(7) Align ruling 12 in the migration plan (:123: "feature 包的钩子一律 exit 0"), since the plan's "钩子" matches the question the owner answered (REVIEW1:50). Alternatively, note the difference in plan §0.

(8) plan:88: ":284-293" → ":292-300". Note that the challenge's ":290-296" is also wrong. plan:87: ":218-246" → ":204-256", which takes in the patch call at :253.

(9) plan:238: drop "或 clone". Say a clone re-applies the chain through each feature package's own post-link (misc.py:274-357; plan:107-108), and that only `--force-reinstall isabelle` on 2025.2-0 needs the manual apply.

(10) plan:266: give the reason as "否则新构建的 ISABELLE_ID 是 CI 新的 hg commit（build.yml:296-300、:370-373），链底成 pristine/<新 ID>，任何 feature 都接不上：所有装了 feature 的用户 exit 3、钩子只在 .messages.txt 报错". Record the freeze in isabelle-packaging-ci/RELEASE.md now, as a §5 step 0 or a decision-11 item that applies before the CI plan, not only through the later CI plan.

(11) plan:4: soften "吸收了评审的全部确认项" to say rev 2 addresses the confirmed items, with any that did not land listed in review 2.

**Judge: partially_confirmed → author_fixes_no_rereview.** Confirmed items:
- (1) plan:109: replace link.py's reversed with solve.py:1450-1452 for the unlink order, :1453 for the link order; link.py:1042 is the rollback.
- (3) plan:292: four patches/*.md files plus patches/Isabelle2025-2/register_thy.md.
- (4) plan:39 and §7: cite the 19-item list at ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979, add D12 (reader2_patch_scheme.md:225), tag each row with its handoff number, and name the ruling that settles it.
- (5) plan:129-130: binary blocks are caught by gate (c) today and by decision 15.2 from then on; renames come out as a deletion plus a creation.
- (6) plan:57-58, :390, :424: micromamba 2.8.1 does run post-link but no pre-unlink (measured); pixi's rattler runs no link scripts by default. Keep conda-only, but replace the reason.
- (7) Align ruling 12 in the migration plan, where :123 says post-link, with the question the owner actually answered (REVIEW1:50, both hooks).
- (8) plan:88: build.yml :292-300 (hg commit at :297), not :284-293 and not the challenge's :290-296; plan:87: :204-256.
- (9) plan:238: drop '或 clone' (or clone); a clone runs every post-link (misc.py:274-357).
- (10) plan:266: the real hazard is exit 3 for every feature user, not a silently mis-identified tree. Record the release freeze in isabelle-packaging-ci/RELEASE.md now, on the owner's order, not later through the CI plan.
- (11) Soften plan:4.
Refuted: (2). plan:107 is true: the frozen solve first, then the unfrozen retry (cli/install.py:370-408). Optionally qualify it.
