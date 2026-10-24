# 补丁工具改造计划：`my_better_isabelle_prover` → `isabelle_patch_control` —— rev 1（2026-10-22）

> 状态：**草稿，待 agent team 评审与用户批准**。这是迁移方案 `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`（下称"迁移方案"）§0 第 19 条划出的
> 两份计划之一（另一份是 `isabelle-packaging-ci` 的，晚些写）。迁移方案 §5.3 定了本工具对外的接口，本计划定内部怎么改。
> 行号针对 `contrib/my_better_isabelle_prover`（工具仓库）、`contrib/isabelle-packaging-ci`（CI 仓库）、`contrib/Isabelle2025-2`（共享树），除非另注。
> 事实出处见 §8。术语沿用迁移方案的 glossary；本文新增的词在下面定义。

## 术语

- **feature**、**链序**、**基 tag**、**发布 tag**、**来历文件**、**patch 文件**、**k**：同迁移方案 glossary。链：
  `pristine → expose_foreign → future_assign_interrupt → light_locale → local_type_abbrev → localized_record → local_datatype → dev_patches`。
- **feature 包**：一个 feature 的 conda 包，装到用户机器上，内容是该 feature 的 patch 文件加来历文件（`make-patches` 的产物）。
- **feature 目录**：feature 包装进用户环境后的目录 `<features.d>/<feature>/`，里面是 patch 文件和来历文件。`<features.d>` 的位置见决定 2。
- **内置 feature**：conda `isabelle` 包构建时已经打进去的链的前 k 节（今天 k=1：`expose_foreign`）。它们是构建的一部分：工具不打、不反打。
- **内置清单**：`isabelle` 包内记录内置 feature 的文件，位置与格式见决定 4。
- **目录接口**：对一个指定目录打或反打一个 feature 目录的 patch 文件、不调 `isabelle` 的子命令与函数（迁移方案 §5.3）。
- **工具**：本仓库的 Python 程序，今天叫 `my-better-isabelle-prover`（命令 `my-better-isabelle`），改名后叫 `isabelle_patch_control`
  （命令 `isabelle-patch-control`）。
- **用户的 Isabelle**：工具作用的那棵 Isabelle 树，由 `isabelle getenv -b ISABELLE_HOME` 定位（`isabelle.py:42-55`）。conda 安装时是
  `$PREFIX/isa`（`recipe.yaml:75-87`）。

## 0. 用户已裁定的事（不再重议；出处是迁移方案 §0 与 light 计划）

1. 发布方式不变：patch 文件经工具打到用户装好的 Isabelle 上；git 仓库只用于开发（迁移方案 §0 第 5 条）。
2. 工具变成**不带任何补丁的纯框架**；`isabelle-packaging-ci` 也变成纯框架、不带补丁（第 8 条）。
3. 基补丁各自成 feature 包；conda `isabelle` 构建预先打好链的前 k 节；工具装到这种构建上时把前 k 节当"已打上"跳过（第 21 条）。
4. 新建文件的 patch 头部用 git 原生的 `--- /dev/null`，工具的 `_read_patch_target` 改一行认它（第 13 条）。
5. 包精确钉死所对的基包版本（第 14 条）；feature 包的 build string 是 `Isabelle2025_2_<n>`（第 27 条）；包的版本号是发布 tag 里的版本号，与
   conda build 号无关（迁移方案决定 3）。
6. 共用脚本放工具仓库顶层 `tools/`，Python 包之外（第 20 条、迁移方案决定 6）——已落地。
7. 不发空的 0 版包；`qiyuan_dev_patches` 等 `local_type_abbrev`、`localized_record`、`local_datatype` 都发布后再发（第 25 条）。
   留给本计划的只有一问：工具里 Isabelle2024 的三个补丁集怎么办（judge 建议留在工具里直到不再支持 Isabelle2024）。
8. light 计划 2026-10-11 定案（迁移方案 §0 D1 引文）：dev 补丁搬出、自成仓库与 conda 包 `qiyuan_dev_patches`（conda 名 `qiyuan-dev-patches`）；
   工具改名 `isabelle_patch_control`，加外部 feature 目录 `features.d/<feature>/`；"顺序由 conda 依赖决定、纯框架不设 `after`"；
   工具去掉 Isabelle2025-2 dev 补丁的那次发版在 `qiyuan_dev_patches` 首次发布之后（"逐步"）。
9. light 计划 D4（转述）：工具层十余条（`.orig`/`.rej`、`after` 与 `order.txt` 的拓扑序、版本键校验、钉死等）推迟到动手改工具时逐条请用户定。
   本计划把它们逐条摆出来（§7）。
10. 迁移方案 §5.3 对工具的接口要求（本计划必须满足）：Isabelle2025-2 这条线上不再带补丁；输入是 `features.d/<feature>/`；按链序打、逆序
    unpatch、`status` 逐 feature 列出；前 k 节算构建的一部分，k 从 `isabelle` 包内文件读、旧构建按 `etc/ISABELLE_ID` 识别、识别不出按 k=0；
    目录接口不调 `isabelle`；`_read_patch_target` 认 `/dev/null`、`status` 对新建文件显示真实目标路径。

## 1. 目标与范围

**目标。** 工具不再是"自带一堆补丁、按类别打"的程序，而是"认得用户环境里装了哪些 feature 包、按链序把它们打到用户的 Isabelle 上、逆序卸掉、
随时能报告每个 feature 的状态"的框架。补丁的权威是 Isabelle 源码的 git 仓库和由它发布的 feature 包；工具里一行 Isabelle2025-2 的补丁都没有。

**范围内。** 工具的改名、输入形式（feature 目录与来历文件）、链序、内置 feature 的识别、目录接口、patch 头部与状态显示的两处改动、硬链接的处理、
feature 包的 conda 配方模板与安装时机、三个新包（`expose_foreign`、`future_assign_interrupt`、`qiyuan_dev_patches`）的仓库布局、Isabelle2024
补丁集的去留、工具自身的发布、落地顺序与验收。

**范围外。** `isabelle-packaging-ci` 的改造（另一份计划；本文 §3 决定 11 只写它必须提供的两样东西）；Isabelle 源码仓库与五个脚本（迁移方案已定并落地）；
各 feature 项目自己的清单与计划。

## 2. 现状（2026-10-22 核实）

### 2.1 工具今天的样子

- 补丁在 Python 包内：`my_better_isabelle_prover/patches/<版本>/<feature>/*.patch`，`patches/__init__.py:8` 把 `PATCHES_DIR` 定成包目录，
  `:106-121` 只从那里发现补丁；`categories.toml` 把 feature 分 user/dev（`:11,47-75`），没登记的 feature 目录是硬错误（exit 3）。
  Isabelle2025-2 有五个 feature 目录（`expose_foreign`、`future_assign_interrupt`、`register_thy`、`show_types_nv`、`expose_map_syn`），
  Isabelle2024 有三个（`future_assign_interrupt`、`show_types_nv`、`expose_map_syn`）。
- 顺序：可选的 `patches/<版本>/order.txt`（`:82-103`），没有时按字母序；两个版本目录今天都没有 `order.txt`。
- 状态只靠 `patch -R --dry-run` / `patch --dry-run`（`patcher.py:28-42`）：反打能过 = applied，正打能过 = not-applied，否则 CONFLICT。
  打之前先 `chmod u+w`、打完恢复 mode（`:45-56,89-100`）。反打时只跳过 NOT_APPLIED（`:73-75`）。`apply_all` 正序打、逆序卸（`:119-120`）。
- 目标路径只认 `--- a/<path>` 头（`patches/__init__.py:124-130`），新建文件的 patch 会退回文件名做目标。
- 定位 Isabelle：`shutil.which("isabelle")` 或 `--isabelle-bin`（`isabelle.py:12-27`），版本 `isabelle version`（`:30-39`），树根
  `isabelle getenv -b ISABELLE_HOME`（`:42-55`）。每个命令都要 `isabelle`（`cli.py:18-45`）。
- `patch`/`unpatch` 之后若碰了 `.scala` 就 `scala_build -f`（`cli.py:71-80`）；今天没有 feature 碰 Scala。
- 没有测试目录。文档四份：`README.md`、`reference.md`、`develop.md`、`RELEASE.md`，加 `AGENTS.md`（`help` 子命令打印它）。
- PyPI 名 `my-better-isabelle-prover` 0.3.0（`pyproject.toml:5-6`）；`package-data` 只带 `patches/**/*.patch`、`categories.toml`、`AGENTS.md`（`:44-46`）。

### 2.2 谁在用它

- CI（`build.yml:218-246`）：`pip install my-better-isabelle-prover==0.3.0`，用一个 5 行 shim 冒充 `isabelle`，`patch --category user --no-build`，
  再 `status --category all` 做交叉核对（`:248-282`），然后 `hg commit`（`:284-293`）。`check_patch_sync.sh:50-52` 对包内 `*.patch`、
  `categories.toml`、`*.py` 做 sha256 比对 PyPI 与本地检出。
- 共享树上的开发（迁移前）：`my-better-isabelle status` 被 light 的 `check_stock_diff.sh:18` 调用。迁移后 light 的脚本退役。
- Isabelle-MCP 不再依赖它（`contrib/Isabelle-MCP/docs/COMPONENT_INSTALL_PLAN.md:22,359`）。Isa-Mini 的配方只在注释里提它（`recipe.yaml:32,142`）。
  Semantic_Embedding 的配方不依赖它（`expose_foreign` 已在 `isabelle` 构建里）。

### 2.3 conda 侧的事实（本计划要适应的）

- `isabelle` 包：整棵树在 `$PREFIX/isa`，`$PREFIX/bin/isabelle` 是相对符号链接（`recipe.yaml:75-87,176-177`）；没有 `requirements`（`:235-237`）；
  build string 只是 build 号，因为 Windows MAX_PATH（`:30-43`）；`isa/etc/ISABELLE_ID` 是 CI 自己那次 `hg commit` 的 changeset
  （`:20`，`pack.sh:386-391`）。本机两个构建：`isabelle-2025.2-0` 的 ISABELLE_ID 是 `5533cd83156e`、`etc/settings` 带 conda 后缀；
  更早的 `isabelle-2025.2-89701cf1768e_0`（旧 build string 形式）ISABELLE_ID 为空、没有 conda 后缀。两个 conda 环境 `isabelle`、`isabelle-2`
  装的都是 `isabelle-2025.2-0`。
- 用户目录：`pack.sh:168-189` 把 `ISABELLE_HOME_USER` 改成 `~/.isabelle/Isabelle2025-2-conda-<env>`，按需建的 heap 落在那里。包内自带
  Pure/HOL/Main 的 heap（`recipe.yaml:3-4,246-247`）。
- post-link / pre-unlink：conda 跑 `$PREFIX/bin/.<包名>-post-link.sh`、`.pre-unlink.sh`（Windows 是 `Scripts/.<包名>-post-link.bat`），只给
  `PREFIX`/`PKG_*`；非零退出让 conda 回滚整次安装（`recipe.yaml:117-121,179-182`；`CONDA_ISABELLE_BRIDGE.md:188`）。已发布的消费者包
  （`isabelle-rpc`、`isabelle-semantic-embedding`）都用这对钩子调 `"$PREFIX/isa/bin/isabelle" components -u/-x "$PREFIX/share/<包名>"`，
  钩子永远 exit 0（`contrib/Semantic_Embedding/conda/recipe.yaml:264-299`）。`PACKAGING_DESIGN.md:5-9` 的立场是"一切随包装、post-link 不生成
  conda 不跟踪的文件"。
- 硬链接：conda 把 pkgs 缓存里的文件硬链接进环境。实测（§8）：GNU `patch` 写新文件再改名，环境里的副本换了 inode、缓存那份内容不变；但
  `chmod u+w` 作用在共享的 inode 上，打完后恢复 mode 的 `chmod` 作用在新 inode 上，于是**缓存那份的 mode 被留在 644**。
- 工具自己不在 conda 渠道上（`ROLLOUT_STATUS.md`、`CONDA_CHANNEL_SWEEP_PLAN.md` 都没有它）；渠道的包都叫 `isabelle-<名字>`。

### 2.4 迁移方案已落地的、与本工具相接的东西

- `tools/make-patches`：从基 tag 到 feature tag 按文件生成 `patches/<R>/<path 的 / 换成 ->.patch`（`git diff-tree -p` 的原样块，新建文件
  `--- /dev/null`、删除 `+++ /dev/null`，带 `index` 行），加 `patches/<R>/provenance.txt`（字段见决定 3）。门禁 (c) 的往返今天用裸
  `patch -p1 -F0` 顶替目录接口（`make-patches:78-84`）。
- `tools/new-tree`、`run-tree`、`check-signatures`、`advance-daily` 与 hook；玩具测试 `tools/tests/run-all.sh`。
- README 已有 "Working in the Isabelle source repository" 一节（附录 A）。

## 3. 决定

### 决定 1：名字与发布形态

- Python 包目录与 import 名 `isabelle_patch_control`，命令 `isabelle-patch-control`，PyPI 名 `isabelle-patch-control`，conda 包名
  `isabelle-patch-control`（noarch，python），版本从 **1.0.0** 起（行为全变，RELEASE.md 的"0.x 破坏性改动 bump MINOR"规则不再适用）。
  GitHub 仓库改名 `isabelle_patch_control`（GitHub 会给旧名做跳转）。
- 旧 PyPI 包 `my-better-isabelle-prover` 不再发版；0.3.0 留着给今天的 CI 用到 CI 计划落地为止。
- 子命令改名：`patch` → `apply`，`unpatch` → `unapply`，`status` 不变，`build` 删除（没有 feature 碰 Scala；若将来有，由 feature 包自己的
  文档说明），`help` 不变。`--category` 与 `--feature` 里的分类消失；`--feature <名>` 保留，意思是"只处理这个 feature 及（打时）它链上的前置、
  （卸时）它链上的后继"（决定 3）。

### 决定 2：输入——feature 目录与它的位置

- 工具的输入是 `<features.d>/<feature>/`，内容恰好是 `make-patches` 写出的东西：`*.patch`（扁平命名）和 `provenance.txt`。工具不改这些文件。
- `<features.d>` 的默认位置：**`$ISABELLE_HOME/../share/isabelle_patch_control/features.d`**，即 conda 布局下的
  `$PREFIX/share/isabelle_patch_control/features.d`——与已发布包放组件的 `$PREFIX/share/<包名>` 惯例一致，而且从 `ISABELLE_HOME` 推出来、
  不依赖 `CONDA_PREFIX`（`CONDA_ISABELLE_BRIDGE.md:121-127` 的约束：用户可能没激活 conda）。`--features-dir <目录>` 覆盖默认，给非 conda
  安装的 Isabelle 和测试用。目录不存在时视为没有任何 feature 包（`status` 打印"no feature packages"并退出 0）。
- 每个 feature 包把自己的 feature 目录装到 `$PREFIX/share/isabelle_patch_control/features.d/<feature>/`（决定 8 的配方模板）。

### 决定 3：来历文件、链序与状态

- 来历文件 `provenance.txt`（`make-patches` 今天写的字段，本计划把它定下来；键值对一行一个）：
  `feature`（`<R>/<feature>`）、`release_tag`、`commit`、`base_tag`、`base_commit`、`base_package_version`（基是 `pristine` 时
  `none (the base is pristine)`）、`base_pin`、`build_string_prefix`、`tree_hash`、`tree_hash_excludes`。工具读 `feature`、`release_tag`、
  `base_tag`；其余给 CI 与人看。`base_tag` 的第二段是基 feature 的名字（`pristine` 表示链头）。
- **链序由来历文件推出**：每个 feature 目录的 `base_tag` 指向它的基 feature；工具从 `pristine` 出发沿"谁以我为基"走，得到一条线。
  两个 feature 以同一个基为基、或某个 feature 的基不在环境里（也不是内置 feature、也不是 `pristine`），都是错误（exit 3，列出断点）。
  没有 `order.txt`、没有 `categories.toml`、没有 `after`。
- 每个 feature 的状态，按链序逐个算：
  - **built-in**：在内置清单里（决定 4）。
  - **applied / not-applied / CONFLICT**：沿用 `patcher.py:28-42` 的判定，对该 feature 的每个 patch 文件算，feature 的状态是它们的合取：
    全 applied = applied，全 not-applied = not-applied，否则 CONFLICT（混合状态也是 CONFLICT：半打的 feature 不是一个合法状态）。
  - `status` 一行一个 feature：`[built-in | applied | not-applied | CONFLICT]  <feature>  <release_tag>  (<n> files)`，再列每个文件的
    目标路径（新建文件显示 `+++ b/` 那边的真实路径，§0 第 10 条）。退出码：选中的 feature（`--feature` 或全部）都是 built-in/applied 为 0，否则 1。
- **堆叠固有的限制**（迁移方案 §7 第 15 条）：上层 feature 打上后，下层 feature 的 patch 读作 CONFLICT——因为同一文件被改了两次，
  `patch -R --dry-run` 对下层的 patch 不再通过。所以 `status` 的判定要**按链序、带记忆**：一个 feature 若其后继已 applied，它自己的 patch
  读作 CONFLICT 是预期的，此时报 **applied (covered)**，不算错误。实现：从链尾向链头判定；一旦某个 feature 判为 applied，它之前的所有
  feature 中读作 CONFLICT 的都标 applied (covered)，读作 not-applied 的仍是 not-applied（这是真错：链有洞）。
- `apply`：按链序，对每个 not-applied 的 feature 正打；built-in 和 applied 跳过；遇到 CONFLICT 停下、退出 1（没有 `--force`：强行打一个
  冲突的 patch 从来不是用户要的，今天 `--force` 的"继续过失败"语义（`cli.py:152`）删除）。`--feature F` 时只打到 F 为止（F 的前置也打）。
  `--dry-run` 保留。
- `unapply`：逆链序，对每个 applied 的 feature 反打；built-in 不反打；`--feature F` 时从链尾反打到 F 为止（F 的后继也卸，否则卸不掉）。
  不带 `--feature` 时卸掉全部非内置 feature。
- 打或卸任何碰 `src/Pure` 的 feature 之后，工具打印一行："Pure 变了，这棵 Isabelle 的 heap 会在下次使用时按需重建到
  `<ISABELLE_HOME_USER>/heaps`；现在手动重建用 `isabelle build -b HOL`"。工具自己**不**构建任何东西（用户的规则）。

### 决定 4：内置 feature 的识别（前 k 节）

- 内置清单文件：**`$ISABELLE_HOME/etc/ISABELLE_BUILT_IN_FEATURES`**，一行一个内置 feature，按链序：`<feature> <release_tag> <commit>`，
  例如 `expose_foreign Isabelle2025-2/expose_foreign/1 f8d760a3d944…`。由 CI 在打完前 k 节、`hg commit` 之前写进树（CI 计划的事；它不在
  git 的任何分支上，CI 计算树哈希时要把它排除——写进来历文件的 `tree_hash_excludes` 或 CI 在哈希之后再写，由 CI 计划定）。
- 工具读它：列出的 feature 是 built-in。若环境里也装了该 feature 的 feature 包（例如 `isabelle-expose-foreign`），要求包的
  `release_tag` 等于清单里的 tag；不等就是 **版本不匹配** 错误（exit 3）：这棵 Isabelle 内置的是版本 1，而包是版本 2——这种组合不该出现，
  因为 `isabelle` 配方的 `run_constrained` 会让求解器避开（决定 11），工具的检查是最后一道。
- 没有内置清单的旧构建：工具内一张表 `LEGACY_BUILDS = {"5533cd83156e": ["expose_foreign Isabelle2025-2/expose_foreign/1"]}`，按
  `etc/ISABELLE_ID` 查；查不到按 k=0。表只会增不会改，它是对已经发出去、不可改的构建的事实记录。
- 内置 feature 不打、不反打、`status` 显示 built-in；它们的 patch 文件如果在环境里（装了它的包），工具不读它们的 patch 内容，只读来历文件。

### 决定 5：目录接口

- 子命令 `isabelle-patch-control apply-to <目录> <feature 目录>` 与 `unapply-from <目录> <feature 目录>`：对 `<目录>` 用
  `patch -p1 -F0 --no-backup-if-mismatch` 按文件名顺序打（或 `-R` 反打）该 feature 目录的全部 patch 文件；不调 `isabelle`、不看内置清单、
  不看别的 feature；任何一个文件失败就退出 1 并打印 `patch` 的输出（已打上的文件不回滚：这是给可丢弃的临时目录用的接口，调用者自己管副本）。
- Python 函数 `isabelle_patch_control.patcher.patch_tree(tree: Path, feature_dir: Path, *, reverse=False) -> None`，CLI 只是它的壳。
  `make-patches` 的门禁 (c) 和迁移方案的 (b2) 改调这个 CLI（`make-patches:78-84` 的 `apply_patches` 换成调用
  `isabelle-patch-control apply-to`；工具不在 PATH 时退回今天的裸 `patch`——不，退回会让门禁悄悄变弱；**要求工具在 PATH**，否则拒绝）。

### 决定 6：patch 头部与新建文件

- `_read_patch_target`（`patches/__init__.py:124-130`）改成：找第一行 `--- ` 与紧随的 `+++ `；`--- a/<p>` → 目标 `<p>`；`--- /dev/null` 配
  `+++ b/<p>` → 目标 `<p>`（新建）；`--- a/<p>` 配 `+++ /dev/null` → 目标 `<p>`（删除）。找不到成对头部是错误（exit 3），不再退回文件名。
- 新建文件的状态判定：`patch -R --dry-run` 对新建文件的 patch，在文件存在且内容相同时通过（= applied），文件不存在时正打的 dry-run 通过
  （= not-applied）。GNU patch 2.7.6 对 `/dev/null` 头的正反打已在迁移方案 §10 T5 实测。
- `make-patches` 写出的块带 `index <sha>..<sha> <mode>` 行和 `new file mode` / `deleted file mode` 行，GNU patch 认得（`make-patches` 的
  玩具测试 28 项含新建可执行文件的往返）。工具不做任何头部改写。

### 决定 7：硬链接与只读文件

- 打一个文件之前，若它的 `st_nlink > 1`（conda 从 pkgs 缓存硬链接进来），先 `cp -p` 成临时文件再 `mv -f` 盖回去，让它有自己的 inode；
  然后再 `chmod u+w`、`patch`、恢复 mode。这样 pkgs 缓存那份的内容和 mode 都不动（§2.3 实测的 mode 泄漏就此消失）。反打同理。
- 反打把文件恢复成原内容后不尝试重新硬链接回缓存（conda 不要求，`conda remove isabelle` 会整体删环境里的副本）。
- 新建文件的删除（反打）由 `patch` 完成；它所在的目录若因此变空，不删目录。

### 决定 8：feature 包的 conda 配方与安装时机

- 包名：`isabelle-<feature 名把 _ 换成 ->`：`isabelle-expose-foreign`、`isabelle-future-assign-interrupt`、`isabelle-light-locale`、
  `isabelle-local-type-abbrev`、`isabelle-localized-record`、`isabelle-local-datatype`；dev 补丁按 light 计划叫 `qiyuan-dev-patches`。
  版本 = 发布 tag 里的版本号；build string `Isabelle2025_2_<build 号>`（§0 第 5 条）；noarch generic。
- 依赖（由来历文件生成，`make-patches` 已写 `base_pin`）：`isabelle-patch-control >=1.0`，`isabelle`（任意版本；内置清单与
  `run_constrained` 管匹配），基包 `isabelle-<基> ==<版本>=Isabelle2025_2_*`（基是 `pristine` 时没有这一项）。
- 文件：`share/isabelle_patch_control/features.d/<feature>/` 里放 `patches/<R>/*.patch` 与 `provenance.txt` 的原样副本；再带该 feature
  的说明文档（从工具仓库 `patches/*.md` 搬过去，见决定 10）。
- **安装时机（本计划的主要提案，待用户定）**：post-link 钩子 `bin/.<包名>-post-link.sh` 跑
  `"$PREFIX/bin/isabelle-patch-control" --isabelle-bin "$PREFIX/isa/bin/isabelle" apply --feature <feature>`，pre-unlink 跑
  `unapply --feature <feature>`；Windows 是 `Scripts/.<包名>-post-link.bat` 经 `isa\contrib\cygwin\bin\bash` 调同一命令（与
  `isabelle-rpc` 等包的 `.bat` 写法一致）。conda 按依赖顺序链接包，所以 post-link 的执行顺序就是链序（`qiyuan-dev-patches` 依赖
  `isabelle-local-datatype`，后者依赖……），卸载时相反。
  - post-link 的退出码：**apply 失败（CONFLICT）时非零**，让 conda 回滚这次安装——用户的 Isabelle 有不相容的改动，装上一个打不上的包比
    回滚更糟。这与已发布包"钩子永远 exit 0"的写法不同，理由写进配方注释。
  - 与 `PACKAGING_DESIGN.md:5-9` 的立场（post-link 不该产生 conda 不跟踪的东西）的关系：这里 post-link 不产生新文件，而是改 `isabelle` 包的
    文件——这正是用户裁定的发布方式（§0 第 1 条）本身的性质，conda 不会知道 `isa/src/Pure/…` 变了。后果与对策：(a) `conda remove isabelle`
    会先卸依赖它的 feature 包（pre-unlink 反打），再删树，没有残留；(b) `conda install --force-reinstall isabelle` 会用缓存覆盖已打补丁的文件
    而 feature 包仍"装着"——工具的 `status` 能看出（not-applied），`apply` 能修；文档写明；(c) 包内自带的 Pure/HOL/Main heap 在打了碰 `src/Pure`
    的 feature 之后过期，Isabelle 在首次使用时按需重建到 `~/.isabelle/<R>-conda-<env>/heaps`（HOL 在 14 核机器上约 6 分钟，见迁移记录），
    post-link 打印这一句，不自己构建。
  - 备选（若用户否决 post-link）：包只放文件，用户装完手动 `isabelle-patch-control apply`；文档与 post-link 的消息都写清楚。

### 决定 9：Isabelle2024 的三个补丁集

- 留在工具里作为**随包附带的 feature 目录**：包目录 `isabelle_patch_control/bundled/Isabelle2024/<feature>/`，每个目录补一个
  `provenance.txt`（`feature: Isabelle2024/<f>`、`release_tag: none (bundled)`、`base_tag: Isabelle2024/pristine/none`，链序按今天
  `patches/Isabelle2024` 的字母序：`expose_map_syn → future_assign_interrupt → show_types_nv`——它们互不相干，任何顺序都行）。工具在
  `isabelle version` 是 Isabelle2024 时把它们当作 `<features.d>` 里的内容；Isabelle2025-2 什么都不附带。
- 这是 judge 的建议（§0 第 7 条）的落实；去掉的时机是"不再支持 Isabelle2024"，由用户以后定。附带目录不参与 `check_patch_sync.sh`
  （那个脚本随 CI 计划退役）。

### 决定 10：三个新包的仓库与工具仓库里要搬走的东西

- `contrib/isabelle-base-features/`（新仓库，一个仓库两个包）：`expose_foreign/` 与 `future_assign_interrupt/` 两个子目录，每个按 light 的
  布局：`tools/patched_files.txt`（各一行）、`tools/signature_additions.txt`（`expose_foreign` 不加 signature 条目，空；
  `future_assign_interrupt` 同，空）、`tools/required_sessions.txt`（`Pure`；迁移第 3 步已在两棵私有树各建过 Pure 并有 tested 记录）、
  `patches/Isabelle2025-2/`（`make-patches` 写）、`conda/recipe.yaml`（决定 8 的模板）、`README.md`（从工具仓库搬来
  `patches/expose_foreign.md`、`patches/future_assign_interrupt.md` 的内容）。`make-patches --package contrib/isabelle-base-features/expose_foreign …`。
- `contrib/qiyuan_dev_patches/`（新仓库，一个包）：`tools/patched_files.txt`（八个文件：`thy_info.ML`、`attrib.ML`、`etc/options`、
  `printer.ML`、`syntax_phases.ML`、`sign.ML`、`Abs_Int3.thy`、`Sudoku.thy`）、`tools/signature_additions.txt`（用 `check-signatures`
  对 `future_assign_interrupt → ab6006e` 算出，恰好三条：`src/Pure/Syntax/printer.ML BASIC_PRINTER val show_types_nv`、
  `src/Pure/Thy/thy_info.ML THY_INFO val register_thy`、`src/Pure/sign.ML SIGN val map_syn`）、`tools/required_sessions.txt`（`HOL`，加
  `HOL-IMP`、`HOL-ex` 因为 nitpick 置空碰它们）、`patches/Isabelle2025-2/`、`conda/recipe.yaml`、`README.md`（搬来 `register_thy.md`、
  `show_types_nv.md`、`expose_map_syn.md`，加一节 `skip_nitpick_examples`）。四个补丁目录在包里不再区分：一个 feature、一份清单。
  （`expose_foreign`、`future_assign_interrupt` 的 signature 清单为空也是用 `check-signatures` 核过的，§8。）
- 工具仓库删掉：`patches/Isabelle2025-2/`、`patches/categories.toml`、五份 `patches/*.md`（搬走）、`reference.md` 与 `README.md` 里的
  feature 表与 category 一节、`check_patch_sync.sh` 对它的依赖（CI 计划）。时机按 §0 第 8 条"逐步"：删除 Isabelle2025-2 dev 补丁的那次
  发版在 `qiyuan-dev-patches` 首次发布之后（§5 顺序）。

### 决定 11：对 `isabelle-packaging-ci` 的两项要求（细节归 CI 计划）

1. `isabelle` 包内写内置清单 `etc/ISABELLE_BUILT_IN_FEATURES`（决定 4 的格式），并在配方里对每个内置 feature 加弱约束
   `isabelle-<feature> ==<版本>`（装了该包就必须是这个版本；conda-build 叫 `run_constrained`，rattler-build 的 recipe.yaml 里叫
   `run_constraints`——本机没装 rattler-build，这个拼写由 CI 计划核实）。
2. 构建时打前 k 节用**本工具的目录接口**（`apply-to`），输入取自已发布的 feature 包（`conda` 下载、解出 `share/isabelle_patch_control/features.d/<feature>/`），
   不再 `pip install` 某个版本的工具来取补丁。

### 决定 12：工具自身的测试与发布

- 新建 `tests/`（pytest，`pyproject.toml` 加 `[tool.pytest]`）：玩具 Isabelle 树（几个文件 + 假 `bin/isabelle` 回答 `version`/`getenv`，
  沿用 `tools/tests/stub-isabelle` 的做法）+ 玩具 features.d（三个 feature 成链，一个新建文件、一个删除文件、一个可执行文件）：
  `status` 的四种状态与 covered；`apply`/`unapply` 的顺序与 `--feature`；内置清单与 `LEGACY_BUILDS`；版本不匹配；链断裂；目录接口；
  硬链接文件的 inode 与 mode；`/dev/null` 头。CI（GitHub Actions）只跑 pytest，不碰真 Isabelle。
- 发布：PyPI `isabelle-patch-control 1.0.0`；conda 包 `isabelle-patch-control`（noarch python，配方在本仓库 `conda/recipe.yaml`，发到自建
  渠道，按 `RELEASE_CHECKLIST.md` 的流程）。`RELEASE.md` 改写：两个版本文件、`package-data` 只剩 `bundled/**`、`AGENTS.md`。

## 4. 新的命令行

```
isabelle-patch-control [--isabelle-bin PATH] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]                 每个 feature 一行：built-in | applied | applied (covered) | not-applied | CONFLICT
  apply    [--feature F] [--dry-run]     按链序打 not-applied 的 feature（F 及其前置）
  unapply  [--feature F] [--dry-run]     逆链序反打 applied 的 feature（F 及其后继）
  apply-to      <dir> <feature dir>      目录接口：对 <dir> 打 <feature dir> 的 patch 文件（不调 isabelle）
  unapply-from  <dir> <feature dir>      目录接口：反打
  help                                   打印 AGENTS.md
```

退出码：0 成功/选中的都 ok；1 CONFLICT 或 apply/unapply 失败；2 `isabelle` 或 `patch` 找不到；3 feature 目录或内置清单不合法（链断、版本不匹配、
头部不成对）。

## 5. 落地顺序

1. 工具改造（本仓库）：决定 1、2、3、4、5、6、7、9、12；pytest 全绿。不碰 `patches/Isabelle2025-2/`（第 7 步才删）。
2. 建 `contrib/isabelle-base-features/`（决定 10）；用户下令 `make-patches expose_foreign 1`、`make-patches future_assign_interrupt 1`
   （迁移第 4 步；门禁 (c) 已改走目录接口）。
3. 迁移第 4 步其余：light 的完整构建与 `make-patches light_locale`；(b2) 在 `isabelle-2025.2-0` 的副本上跑（工具读 `LEGACY_BUILDS`
   认出 `expose_foreign` 内置）。
4. 发布 `isabelle-patch-control` 1.0.0（PyPI + conda）；发布 `isabelle-expose-foreign` 1、`isabelle-future-assign-interrupt` 1、
   `isabelle-light-locale`（版本由 light 定）到渠道；在一个新建的 conda 环境里从渠道装 `isabelle` + `isabelle-light-locale`，验证
   post-link 打上、`status` 正确、heap 按需重建、`conda remove` 反打干净（§6）。
5. CI 计划：写、评审、落地（决定 11）；新构建的 `isabelle` 包带内置清单。
6. 建 `contrib/qiyuan_dev_patches/`；等 `local_type_abbrev`、`localized_record`、`local_datatype` 都发布后发 `qiyuan-dev-patches`（§0 第 7 条）。
7. 工具删掉 `patches/Isabelle2025-2/` 与 `categories.toml`，发版（§0 第 8 条"逐步"的终点）。

## 6. 验收

- pytest（决定 12）全绿。
- 迁移方案的门禁 (c) 改走目录接口后，`make-patches` 的玩具测试 28 项仍全过；`make-patches pristine` 检查 (a) 仍过。
- (b2)：在 `isabelle-2025.2-0` 的两份副本上，副本 A 经工具按链序打到 light 为止（`expose_foreign` 认作内置、不打），副本 B 经裸
  `patch -p1 -F0` 打 `git diff-tree <expose_foreign tag> <light tag>`，两者整树（含 mode）相同；再让工具 unapply A，等于构建原状。
- 真环境：第 5 节第 4 步的新 conda 环境；`conda list` 显示三个 feature 包；`isabelle-patch-control status` 三行 built-in/applied/applied；
  `isabelle build -b HOL` 在用户目录重建成功；`conda remove isabelle-light-locale` 后 `status` 剩两行；`conda remove isabelle` 后环境里没有
  `isa/` 残留。

## 7. 待用户定的问题（按重要性）

1. **安装时机**：post-link 自动打（决定 8，我的建议）还是只放文件、用户手动 `apply`？
2. **Isabelle2024**：留作随包附带（决定 9，judge 的建议）还是本次就删？
3. **基补丁两个包放一个仓库**（决定 10 的 `contrib/isabelle-base-features/`）还是各自一个仓库？
4. **名字**：PyPI/conda 都叫 `isabelle-patch-control`、版本 1.0.0、GitHub 仓库改名——可以吗？
5. **文件名**：来历文件 `provenance.txt`、内置清单 `etc/ISABELLE_BUILT_IN_FEATURES`、feature 目录 `share/isabelle_patch_control/features.d/`。
6. light 计划 D4 推迟的那十余条，本计划的回答：`.orig`/`.rej`——`--no-backup-if-mismatch` 且 `-F0` 下失败即停，不留碎片；
   `after`/`order.txt`——废除，链序来自来历文件；版本键校验——内置清单与 `run_constrained`；钉死——`base_pin`；`--force`——删除；
   `scala_build`——删除 `build` 子命令。有异议的请指出。

## 8. 证据（2026-10-22 实测）

- 硬链接：`cache/f` 与 `env/f` 同 inode（links=2，mode 444）；在 `env/` 里 `chmod u+w f && patch -p1 -F0 && chmod 444 f` 之后：
  `cache/f` inode 不变、内容原样、**mode 644**、links=1；`env/f` 新 inode、内容已打补丁、mode 444。
- 本机 conda：`pkgs/isabelle-2025.2-0/isa/etc/ISABELLE_ID` = `5533cd83156e`，`etc/settings` 带 `-conda-$(basename …)` 后缀；
  `pkgs/isabelle-2025.2-89701cf1768e_0` 的 ISABELLE_ID 为空、无后缀；环境 `isabelle`、`isabelle-2` 的 `conda-meta` 都是 `isabelle-2025.2-0`。
- 消费者包的钩子写法：`contrib/Semantic_Embedding/conda/recipe.yaml:255-299`、`contrib/Isabelle_RPC/conda/recipe.yaml:148-179`。
- conda 的链接顺序：本机 conda 25.11 的 `conda/core/solve.py` 把要链接的包集合整理成 `IndexedSet(PrefixGraph(solution).graph)`
  （`models/prefix_graph.py` 按依赖拓扑排序，被依赖者在前），`core/link.py` 对卸载动作用 `reversed(...)`。所以 feature 包的 post-link
  按链序执行、pre-unlink 逆序执行（决定 8 依赖这一点）。
- `check-signatures`（空清单）：`pristine → expose_foreign`、`expose_foreign → future_assign_interrupt` 都是"0 additions"；
  `future_assign_interrupt → ab6006e`（dev 补丁的 commit）恰好三条新增（决定 10）。
- 工具源码行号：§2.1。CI：`build.yml:218-293`、`check_patch_sync.sh:50-52`、`recipe.yaml:20,30-43,75-87,235-237`、`pack.sh:168-189,386-391`。
- 迁移记录 `ai-artifacts/isabelle-git-migration/RECORD.md`：HOL heap 重建 6 分钟（14 核）；`make-patches` 玩具测试 28 项；两棵基补丁私有树的
  Pure 构建各约 15 秒。

## 9. 不做的事

- 不给工具加构建 heap 的功能（用户规则：任何 `isabelle build` 都要用户命令）。
- 不做"把补丁合并进 conda 的文件跟踪"（conda 没有这种机制，`PACKAGING_DESIGN.md:1011-1013`）。
- 不支持一个环境里两棵 Isabelle（`CONDA_ISABELLE_BRIDGE.md:75` 单活跃 env 的约束照旧）。
- 不改 `make-patches` 的输出格式（本计划的来历文件字段就是它今天写的）。
