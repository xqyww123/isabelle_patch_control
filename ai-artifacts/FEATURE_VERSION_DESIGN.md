# Feature package versions `<Y>.<k>.<m>` (design, draft 3, 2026-11-02)

Draft 1 was reviewed (wf_231c8b2e-96b); draft 2 applied its rulings and the owner's answers; draft 2's focused
re-review (wf_e82b58ea-dc1) left only author fixes, applied here, and ruled that no further design review is needed.

## 1. What the owner decided

- 2026-11-02 (relayed by session mlml-71): "我对这个版本设计不满意。我建议 2026.1 这样的版本号，大版本号与 isabelle 的
  major version 统一".
- 2026-11-02: "我建议进一步改进为 Isabelle2026 这条线为 2026.0.1, 2026.0.2... 这样未来出现 2026-2 的时候就可以说
  2026.2.1 ... 采纳这个建议，tag 可以不变。Isabelle2025-2 线写成 2025.2.1".
- 2026-11-02, on the review's proposals: the pin on the base package loses its `<prefix>_*` part ("1. 按你建议来");
  make-patches stops writing the provenance fields `base_package_version` and `base_pin` ("2. 按你建议来"); no new term
  for the number at the end of a tag ("3. 这么小的事情需要制造新术语吗？").

## 2. The rule

A release tag stays `<R>/<feature>/<m>`, `m` = 1, 2, 3, … (`make-patches <feature> <m>` as today). The conda package
built from it has the version

    Isabelle<Y>/<feature>/<m>     ->  <Y>.0.<m>     (Isabelle2026/light_locale/1   -> 2026.0.1)
    Isabelle<Y>-<k>/<feature>/<m> ->  <Y>.<k>.<m>   (Isabelle2025-2/light_locale/1 -> 2025.2.1)

computed as a plain string transform from the existing helpers: `isabelle_version(build_string_prefix(<R>))`, then
`.0` appended when that has one part, then `.<m>`. It refuses nothing; a toy line `R` gives `R.0.<m>`.

Words: "version" alone means the package version (what conda shows). The number at the end of a tag is written `<m>`
and described as 1, 2, 3, …; no new term. `<n>` stays the conda build number (build strings `<prefix>_<n>`).

## 3. Where it applies

One function in `isabelle_patch_control/dev.py`, `package_version(release_tag)`, next to `build_string_prefix` and
`isabelle_version`; every place below calls it, none re-derives it.

1. The renderer (`tools/render-feature-recipe`): the recipe's `version`; `<version>` in the hook texts (the pre-unlink
   hook prints `conda install … <package>=<version>`); the pin on the base package, written there directly as
   `<base package> ==<package_version(base_tag)>`, for example `isabelle-fast-abbrev-printing ==2026.0.1`.
   `dev.feature_pin`, its re-export in `tools/common.py` and its import in `tools/tests/toy-channel.sh` go.
2. `make-patches` stops writing `base_package_version` and `base_pin` (make_patches.py:193-194 and its `feature_pin`
   import go). Its docstring (:1, :29, :31), usage and metavar (cli.py:19, :271) say `<m>`; its messages:
   - :123: "the number at the end of the release tag is a positive integer (1, 2, 3, …), not '…'";
   - :146: "… to release this commit's content again under a new number";
   - :265: "this number is spent: release {m + 1}" (tools/tests/test_make_patches.sh:214 expects it).
3. `tools/release-plan`: `Wanted.version` of each feature is `package_version(tag)`, hence its file names; its
   refusal at :73 says `<R>/<feature>/<m>`.
4. The tool at run time: `features.FeatureDir.version` returns `package_version(release_tag)` (the messages of
   `link_chain`, `texts.chain_broken`, the residue block's `conda install … <package>=<version>`); and in
   `link_chain`'s refusal the needed base's version is `package_version(fd.base_tag)`, only the name still split from
   the tag. On that path `base_tag` is always a release tag: a pristine base of another build is refused first by
   `not_pristine`, and the tree's own pristine tag is used at the first step of the chain. The comment at
   features.py:55 says `<m>`.
5. Tests and the toy channel, whose expected strings follow the rule: `tests/test_render.py`,
   `tests/test_release_tools.py`, `tests/test_chain.py`, `tests/test_hooks.py`, `tests/conftest.py` and
   `test_render.py`'s provenance fixtures (the two dropped fields go); `tools/tests/test_conda_hooks.sh` (the `bytes`
   helper's package-cache paths, the conda-meta file name, the residue lines); `tools/tests/toy-channel.sh` (the two
   provenance lines go; the file-name assertion at :260); `tools/tests/test_make_patches.sh` (the two `base_pin`
   checks become checks of `base_tag: R/base/1` and `base_tag: R/base/2`; the message at :214).

Unchanged: tags and make-patches' argument, build strings `<prefix>_<n>`, `check-packages`, `tools/accept`, the
release workflow's inputs.

The three Isabelle2025-2 tags keep the fields in their provenance files (expose_foreign/1: `base_pin: none`;
future_assign_interrupt/1: `==1=Isabelle2025_2_*`; fast_abbrev_printing/1: `==1 Isabelle2025_2_*`). Nothing reads
them: the renderer computes the pin from `base_tag`, and the tool reads only `release_tag` and `base_tag`.

## 4. Documents

- RELEASE.md: :25 (tags `<R>/<feature>/<m>`; the package version `<Y>.<k>.<m>`, with the rule); :62-64 (the clone
  line takes `<m>`, the last number of the package version); :68-71 (the pin `==<the base's package version>`, a new
  example, no `base_pin`); :107-108 (the Windows path estimate: `<package>-<Y>.<k>.99-<prefix>_99/...`, `<Y>.<k>`
  being the package version's first two numbers); :126 (take the highest package version among the builds of
  `<R>`; its tag ends in that version's last number); :159-162 (the version is computed from the release tag, :25);
  other places where `<version>` means the tag's number say `<m>` (:76, :112 "release m+1", :152).
- SKILL: 3.4 step 2's path check (SKILL.md:191): `<package name>-<Y>.<k>.99-<prefix>_99/...`, with `<Y>.<k>` defined
  as above; steps 5-6 write the tag's number `<m>` (today `<v>`).
- develop.md:73 drops `feature_pin` from its list; develop.md:199 cites the renderer for the base pin; dev.py's module
  docstring (:3-4) and section header (:123) say "build strings and package versions" instead of "pins".
- Patch tool plan: a new §0 item 44 (the owner's decisions); marks "revised by item 44" on item 4's last clause,
  item 21's version clause, decision 3 ("版本取第三段" and the two fields), decision 10's version line, its base-pin
  line and the 2026-10-28 note (:990-995), its path formula (example `isabelle-future-assign-interrupt-2025.2.1-
  Isabelle2025_2_0/…`, longest 158), decision 16 point 10; §8 :1632 follows decision 10 (158).
- The feature READMEs' clone lines (contrib/light_locale/README.md, contrib/bicompose_rename_fix/README.md) belong to
  their sessions: told through the session "git 2026".

## 5. Costs for the owner

Users see `2026.0.1` instead of `1`. Windows path headroom shrinks by 7 characters (worst case today about 160 of
198). No feature package is on the channel yet.

## 6. Testing

pytest; `tools/tests/run-all.sh`; the toy channel and the hook-layer test on GitHub (`tests.yml`) after the owner's
approval to commit and push.
