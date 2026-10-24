# 补丁工具改造计划：`my_better_isabelle_prover` → `isabelle_patch_control` —— rev 2（2026-10-23）

> 状态：**rev 2，待第二轮 agent team 评审**。rev 1 的评审报告在 `ISABELLE_PATCH_CONTROL_REVIEW1.md`（29 条 challenge，judge 判未就绪）；
> rev 1 的副本在 `ISABELLE_PATCH_CONTROL_PLAN.rev1.md`。rev 2 吸收了评审的全部确认项，并按用户 2026-10-23 的裁定（§0 第 11–19 条）重写了
> 核心机制：`isabelle` 包是原版、引擎换成 `git apply`、钩子一律 exit 0、全平台。
> 这是迁移方案 `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`（下称"迁移方案"）§0 第 19 条划出的两份计划之一；§5.3 定了本工具对外的接口，
> 本计划定内部怎么改。另一份（`isabelle-packaging-ci`）晚些写，本计划 §3 决定 11 列出它必须提供的东西。
> 行号针对 `contrib/my_better_isabelle_prover`（工具仓库）、`contrib/isabelle-packaging-ci`（CI 仓库）、本机 conda 25.11.1
> （`~/miniconda3/lib/python3.13/site-packages/conda`），除非另注。事实出处见 §8。

## 术语

沿用迁移方案 glossary 的 **feature**、**链序**、**基 tag**、**发布 tag**、**来历文件**、**patch 文件**；"前 k 节"只剩历史含义（§0 第 11 条）。
链：`pristine → expose_foreign → future_assign_interrupt → light_locale → local_type_abbrev → localized_record → local_datatype → dev_patches`。

- **工具**：本仓库的 Python 程序。今天叫 `my-better-isabelle-prover`（命令 `my-better-isabelle`），改造后叫 `isabelle_patch_control`
  （命令 `isabelle-patch-control`）。
- **feature 包**：一个 feature 的 conda 包，内容是该 feature 的 patch 文件加来历文件（`make-patches` 的产物）。
- **feature 目录**：feature 包装进 conda 环境后的目录 `$PREFIX/share/isabelle_patch_control/features.d/<feature>/`。
- **用户的 Isabelle**：工具作用的那棵 Isabelle 树。conda 环境里是 `$PREFIX/isa`（CI `recipe.yaml:75-87`）。
- **预先打好的 feature**：已发布的 `isabelle-2025.2-0` 构建里带着的 `expose_foreign/1`。以后的构建不再有（§0 第 11 条）。
- **目录接口**：对一个指定目录打或反打一个 feature 目录的 patch 文件、不读 conda 环境的子命令与函数（迁移方案 §5.3）。
- **钩子**：conda 在装包后运行的 `post-link` 脚本和卸包前运行的 `pre-unlink` 脚本（`$PREFIX/bin/.<包名>-post-link.sh`，Windows 是
  `%PREFIX%\Scripts\.<包名>-post-link.bat`）。

## 0. 用户已裁定的事（不再重议）

出自迁移方案 §0 与 light 计划的：
1. 发布方式不变：patch 文件经工具打到用户装好的 Isabelle 上；git 仓库只用于开发（迁移方案第 5 条）。
2. 工具"逐步改成不带任何预置补丁的纯框架"（light 计划 D1 第 3 句，迁移方案 §0 D1 引文第 3 条与 §5.3）；`isabelle-packaging-ci` 变成纯框架
   （迁移方案第 8 条）。
3. 基补丁各自成 feature 包（迁移方案第 21 条）。该条第 (1) 点"构建预先打好前几节"已被第 11 条修订。
4. 新建文件的 patch 头部用 git 原生的 `--- /dev/null`（第 13 条）；包精确钉死所对的基包版本（第 14 条）；build string 是 `Isabelle2025_2_<n>`
   （第 27 条）；包的版本号是发布 tag 里的版本号（迁移方案决定 3）。
5. 共用脚本放工具仓库顶层 `tools/`（第 20 条、决定 6）——已落地。
6. 不发空的 0 版包；`qiyuan_dev_patches` 等三个 feature 发布后再发（第 25 条）。
7. **feature 补丁由 conda 包的 post-link 打、pre-unlink 反打，heap 全部失效按需重建，用户接受**（用户 2026-09-14 与 2026-10-11；
   light 计划 `LIGHT_LOCALE_PLAN_REV37.md:5805`、`:7796` 第 (1) 条；(44) 只替换了开发侧）。本计划不重议安装方式。
8. light 计划 D4：工具层的十余条推迟到动手改工具时逐条请用户定；清单是 `ai-artifacts/readers_impl0/reader2_patch_scheme.md` 的发现 1–16
   与决定 D1–D11。本计划 §7 逐条对应。
9. 迁移方案 §5.3 对工具的接口要求：输入是 `features.d/<feature>/`；按链序打、逆序 unpatch、`status` 逐 feature 列出；目录接口；
   `_read_patch_target` 认 `/dev/null`、`status` 对新建文件显示真实目标路径。"前 k 节识别"按第 11 条只剩 `2025.2-0` 一条记录。
10. 迁移方案 §0 第 15 条 Q4 把 `skip_nitpick_examples` 登记为 `dev_patches` 里的补丁目录；§6 第 1.6 步把它做成 commit 30aab6e。包的布局由本
    计划定（第 17 条）。

用户 2026-10-23（rev 1 评审之后）：
11. **conda `isabelle` 包是原版，不带任何补丁**。原话："我建议 isabelle 就是原版，原汁原味。我建议再发布一个 isabelle 新版本，是原版，不带有
    expose_foreign；然后 expose_foreign 按我们之前讨论的，是单独一个 patch package"。已发布的 `isabelle-2025.2-0` 带 `expose_foreign/1`
    是历史事实，由工具的一条固定记录承载（决定 10）。在 CI 改成不打补丁之前不再发布任何 `isabelle` 构建。（迁移方案 §0 第 30 条。）
12. **钩子失败一律 exit 0**，结果经 `$PREFIX/.messages.txt` 报告（"赞同你的建议"）。
13. **新的 `isabelle` 构建的 post-link 在装了工具时把已装的 feature 重打一遍**（"赞同 (a)"）；对改不了的 `2025.2-0`，用户换包后手动
    `apply` 一次，README 写明。
14. **`PACKAGING_DESIGN.md` 记一条例外并详细论证**：用包管理系统管补丁，用户自行决定装哪些补丁，`isabelle` 包保持原样（附录 A）。
15. Isabelle2024 的补丁集留在旧工具 `my-better-isabelle-prover` 里，不再考虑；不切新版本。
16. 三个 feature 本周就绪；所有包等全部就绪后按用户命令一次发布，D1 的"逐步"不再构成顺序问题；旧工具 0.3.0 留在 PyPI 上不动。
17. 文案与测试相关的决定，在不改设计的前提下授权作者自决（"你可以自决"）。据此定：状态词 `pre-applied | applied | half-applied |
    not-applied | CONFLICT`；`skip_nitpick_examples` 在包里以 commit 与 README 一节存在；工具运行时对树加锁；只支持 conda（pixi、micromamba
    不跑 link 脚本，不支持）。
18. **引擎用 `git apply`**（"好，就定了 git apply"；此前"我反对自己写引擎。这种事情应该走已有的库"）。**必须支持全平台**。
19. 用户自装、不在 conda 里的 Isabelle2025-2 不支持（"赞同 (a)"）；feature 包声明 `isabelle >=2025.2,<2025.3`。
20. （2026-10-23，第二轮评审 C9 的问题 1）**"原汁原味"指 Isabelle 源码一字不动、`etc/ISABELLE_ID` 是官方 changeset；
    `scripts/pack.sh` 对 `etc/settings`（`ISABELLE_HOME_USER` 加 `-conda-<环境名>` 后缀）、`etc/options`（`ML_system_64` 默认 true）、
    `etc/components`（删 nunchaku 行）三个文件的打包改动保留**（"应当保留 scripts/pack.sh 所改动的那三个文件"）；CI 编的 heap 与
    Windows 的 `bin/isabelle.bat` 随之保留。附录 A 与决定 11 按此改写，删"逐字节一致"。
21. （2026-10-23，第二轮评审 C11 的问题 2）**light 的 Pure 补丁与 HOL 侧 session（`contrib/light_locale/ROOT`、`Light_Locale.thy`）
    做成同一个包 `isabelle-light-locale`**，不拆 session 包（"这两部分本就是同一个项目内的啊，本来版本就是耦合的啊"）。据此：
    feature 包模板加一个可选的组件载荷（`share/<包名>/` 下的 ROOT 与 theory，按渠道 `RELEASE_CHECKLIST.md` §4 的组件包规范用
    `isabelle components -u/-x` 登记）；钩子 = 冻结的工具调用片段 + 组件包规范的登记行，只有带组件的包才有后者；版本仍是补丁发布
    tag 的版本号，HOL 侧单独改动也走一次新的 light 发布并连带重发其上的 feature 包，这是用户接受的既有耦合。
22. （2026-10-23，第二轮评审 C22 的问题 3）**每个 feature 包精确钉死它所对的 `isabelle` 构建**（用户提议"各个 Feature 包把 build number
    直接固定死"，作者赞成并实测，用户"确认"）。写法 `isabelle 2025.2 <build string>`；版本和 build string 都定死。后果：没有任何 feature 包
    能装到 `2025.2-0` 上，`LEGACY_BUILDS` 记录、决定 10、"2025.2-0 上手动 `apply`"全部删除；工具只认 `etc/ISABELLE_ID` 等于官方
    changeset 的原版构建，别的 ID 一律 exit 3 并提示 `conda update --all`；每发一个 `isabelle` 构建就把全部 feature 包重发一遍
    （版本不变、build 号加一、钉死换新，批量发布 workflow 接 build 号输入）；README 的更新命令是 `conda update --all`（libmamba 下
    单独 `conda update isabelle` 不动，实测）；CI 五个平台腿同一个 build 号；批量发布先发原版 `isabelle` 再发 feature 包。
    这修订迁移方案 §0 第 21 条的后半句（"不是 `isabelle` 的版本或 build 号"），基 feature 包之间的精确钉死（迁移 §0 第 14 条）照旧。
    实测：scratchpad `pintest/`——在旧构建上装 feature 会自动升 `isabelle`；新构建未配套重发 feature 时 update 原地不动、显式装报冲突、
    feature 从不被悄悄卸掉。
23. （2026-10-24，第二轮评审 C24 的问题 4）**工具 1.0.0 只发 conda，不发 PyPI**（"赞同 (a)"）。旧的 `my-better-isabelle-prover` 0.3.0
    留在 PyPI 上不动；`pyproject.toml` 的名字保留，只用于 conda recipe 内部的 `pip install . --no-deps` 与开发者的 editable 安装；
    决定 1、13、14 与 0.x 迁移一节删去 PyPI 的半边与"先 conda 后 PyPI"一句。
24. （2026-10-24，第二轮评审 C2 的问题 5）**暂存目录加原子改名是唯一的写树路径，与第 18 条"引擎用 `git apply`"一致**（"赞同 (a)"）。
    补丁内容只由 `git apply` 在树外、同一文件系统的暂存目录里对每个文件的副本重放产生（一个补丁文件一次调用）；工具只做复制、
    设权限位、`os.replace`/`os.unlink`，一次一个文件；每个文件任何时刻非旧即新，中断后下一次 `apply`/`unapply` 接着做完；
    `status`、`--dry-run`、`apply`、`unapply`、目录接口共用"先重放、再决定装不装"一条路径；`git` 永远只在暂存目录里跑。
    实测依据：`git apply` 改多文件时先 `unlink` 全部旧文件再逐个创建（strace，scratchpad `verify2/t3.strace`），rev 2 的
    "每次调用原子"只在 hunk 不匹配、什么都不写时成立。
25. （2026-10-24，第二轮评审 C12/C13 的问题 6）**一个批量发布 workflow，住在工具仓库**（`xqyww123/my_better_isabelle_prover`，改名后
    `isabelle_patch_control`）**的 `.github/workflows/` 下**（用户"赞同你的建议"一个批量 workflow，仓库"建议 (2)"）。它接 `isabelle`
    构建号与各 feature 发布 tag 两组输入，按 tag 检出各 feature 仓库、现场渲染 recipe、把工具包与全部 feature 包构建进一个本地渠道、
    五个平台腿上跑 §6 验收，通过后把同一批文件按依赖顺序逐个调 `isabelle-packaging-ci` 的 `publish-conda.yml` 上传。后果：工具仓库
    要 `gh secret set` 两个 R2 密钥、加进 `PUBLISH_REPOS`；GitHub 改名在 workflow 存在之前；feature 仓库自己不需要任何 workflow。
    作者曾改推荐 `isabelle-packaging-ci`（密钥已在、构建号同处产生），用户仍选工具仓库。

## 1. 目标与范围

**目标。** 工具不再带补丁，而是"认得 conda 环境里装了哪些 feature 包、按链序把它们打到 `$PREFIX/isa` 上、逆序卸掉、随时报告每个 feature
的状态"的框架。打补丁的引擎是 `git apply`；工具自己不含任何补丁逻辑，只有调用、状态判定与链的核对。

**范围内。** 改名与发布形态；定位树；feature 目录与来历文件；按精确 tag 的链；`git apply` 的调用方式；状态模型；`apply`/`unapply`；目录接口；
conda 钩子；feature 包的配方模板、渲染器与发布流程；`2025.2-0` 的固定记录；对 CI 计划的要求；三个新包的仓库布局；测试与发布；
`make-patches` 的配套改动；D4 清单逐条；用户可见文案。

**范围外。** `isabelle-packaging-ci` 的改造细节（另一份计划）；Isabelle 源码仓库与五个脚本的设计（迁移方案）；各 feature 项目自己的清单与
计划；Isabelle2024。

## 2. 现状（2026-10-22/23 核实；rev 1 的错误已订正）

### 2.1 工具今天的样子

- 补丁在 Python 包内：`my_better_isabelle_prover/patches/<版本>/<feature>/*.patch`（`patches/__init__.py:8,106-121`）；`categories.toml` 把
  feature 分 user/dev（`:11,47-75`）。Isabelle2025-2 五个 feature 目录，Isabelle2024 三个。顺序靠可选的 `order.txt`（`:82-103`）。
- 状态只靠 GNU patch 的 `-R --dry-run` / `--dry-run`（`patcher.py:28-42`）；打前 `chmod u+w`、打后恢复（`:45-56,89-100`）；
  `apply_all` 正序打、逆序卸、逐文件、无回滚（`:108-128`）。目标路径只认 `--- a/` 头（`patches/__init__.py:124-130`）。
- 定位 Isabelle：`shutil.which("isabelle")` 或 `--isabelle-bin`，再跑 `isabelle version` 与 `isabelle getenv -b ISABELLE_HOME`
  （`isabelle.py:12-55`、`cli.py:18-45`）。没有测试目录。PyPI 名 `my-better-isabelle-prover` 0.3.0。

### 2.2 谁在用它

- CI（`build.yml:218-246`）：`pip install my-better-isabelle-prover==0.3.0`，shim 冒充 `isabelle`，`patch --category user --no-build`，
  `hg commit`（`:284-293`）；`check_patch_sync.sh:50-52` 比对 PyPI 与本地。按第 11 条这一整段退役。
- light 迁移前的 `check_stock_diff.sh:18` 调它，已退役。Isabelle-MCP、Isa-Mini、Semantic_Embedding 的配方都不依赖它。

### 2.3 conda 侧的事实（本计划要适应的）

- `isabelle` 包：整棵树在 `$PREFIX/isa`，`$PREFIX/bin/isabelle` 是相对符号链接（`recipe.yaml:75-87,176-177`）；没有 `requirements`
  （`:235-237`）；build string 只是 build 号（`:30-43`）。`etc/ISABELLE_ID` 是 CI 那次 `hg commit` 的 changeset（`:20`，`pack.sh:386-391`）：
  已发布的 `isabelle-2025.2-0` 是 `5533cd83156e`，树里带 `expose_foreign`，`etc/settings` 带 conda 后缀。本机 pkgs 缓存里另有一个
  `isabelle-2025.2-89701cf1768e_0`：树在 `opt/Isabelle2025-2/`（没有 `isa/`），`ISABELLE_ID` 是原版 changeset `89701cf1768e`，也带
  `expose_foreign`，只来自本地文件渠道、没有装在任何环境里——**不支持，它的 ID 永不进决定 10 的记录**。
- 用户目录：`pack.sh:168-189` 把 `ISABELLE_HOME_USER` 改成 `~/.isabelle/<R>-conda-$(basename <prefix>)`——键是 prefix 的 basename，不是
  环境；两个 prefix basename 相同的环境（`-p ~/a/env` 与 `-p ~/b/env`）共用一个 heap 目录，装了不同 feature 时会互相重建对方的 Pure/HOL，
  任一环境卸 `isabelle` 会删掉共用目录（`recipe.yaml:223-231`）。包内自带 Pure/HOL/Main 的 heap（`recipe.yaml:3-4,246-247`）。
- **钩子的执行与失败语义（conda 25.11.1，评审实测）**：conda 先链接事务里的全部包，再依次跑 post-link（`core/link.py:938-967`）；一个
  post-link 失败后其余的照跑，最后回滚（`:1006-1007,1038-1045`）；**回滚只撤文件链接、不跑任何脚本**（`:1129-1160`），所以前面的
  post-link 已经写进 `isa/` 的改动留在树里、而包没了；回滚还删 `conda-meta/history`（`core/path_actions.py:1075-1080`），之后 conda 不再认
  这个目录是环境。pre-unlink 非零只记警告，包照样卸（`link.py:1676-1683`）。钩子的 stdin/stdout/stderr 都是管道（`gateways/subprocess.py:83-117`）；
  成功时用户只看到 `$PREFIX/.messages.txt` 的内容（`link.py:1684-1708`）。
- **哪些包跑钩子**：只有本次事务里换了的包（`core/solve.py:1417-1418` 的 `unlink_precs`/`link_precs`）。所以 `conda update isabelle`、
  `conda update --all`、求解器顺带换 `isabelle` 的 build、`--force-reinstall isabelle` 都只跑 `isabelle` 自己的钩子；`conda create --clone`
  先把未跟踪的文件复制过去、再链接包并跑 post-link（`misc.py:276-357`）。链接顺序按依赖拓扑排序（`core/solve.py` 的 `PrefixGraph(...).graph`，
  `models/prefix_graph.py`），卸载逆序（`core/link.py` 的 `reversed(...)`）。
- 硬链接：conda 把 pkgs 缓存里的文件硬链接进环境。`git apply` 写新文件再替换：环境里的副本换了 inode，缓存那份的内容与权限位都不变
  （§8 实测）；新 inode 的权限按 umask。
- 已发布消费者包的钩子惯例（`contrib/Semantic_Embedding/conda/recipe.yaml:255-299`、`contrib/Isabelle_RPC/conda/recipe.yaml:148-179`）：
  `.sh` 与 `.bat` 各一份，永远 exit 0，经 `.messages.txt` 说话；`RELEASE_CHECKLIST.md:259` 要求所有钩子 exit 0。
- conda-forge 的 `git`：linux-64 11.9 MB、linux-aarch64 16.5 MB、osx-64/osx-arm64 13.5 MB、win-64 120.8 MB（整包是 Git for Windows 的
  PortableGit，自带 MSYS2 运行时，不依赖 `m2-*` 包；feedstock `meta.yaml:20-27,76-77`）。

### 2.4 `git apply` 的实测（§8）

在普通目录里（不是 git 仓库）对 light 的 32 个文件的 git 格式 diff：`--check` 在基上通过、`-R --check` 在基上失败；正打后树哈希等于
light 的树；此后 `--check` 失败、`-R --check` 通过；`-R` 反打后树哈希等于基。玩具：新建可执行文件（可执行位对）、删除、末尾无换行（保持）、
反打时删掉它建的文件；**一个文件对不上时整次调用什么都不改**；对 0444、与缓存硬链接的文件，缓存那份内容与权限不变；非贴着文件头尾的 hunk
允许偏移（和 GNU patch `-F0` 一样）。对新增行的行尾空白只有 warning（`--whitespace=nowarn` 关掉）。
对照测过的 Python 库都不够：`patch-ng` 反打不删新建文件、不认末尾无换行、不原子；`whatthepatch` 只做文本层；`pygit2`（libgit2）正打对、但没有
反向应用，且要借一个 bare 仓库。

### 2.5 迁移方案已落地的、与本工具相接的东西

`tools/make-patches` 生成 `patches/<R>/<path 的 / 换成 ->.patch`（`git diff-tree -r -p --no-renames` 的原样块：`diff --git`、可选的
`new file mode`/`deleted file mode`、`index`、`---`/`+++`、hunk）和 `patches/<R>/provenance.txt`；拒绝改名、二进制、mode 变化
（`make-patches:167-168`）。门禁 (c) 今天用裸 `patch -p1 -F0`（`:63-69,179-183`）。`new-tree`、`run-tree`、`check-signatures`、
`advance-daily`、hook，玩具测试 `tools/tests/run-all.sh`。README 已有 "Working in the Isabelle source repository" 一节。

## 3. 决定

### 决定 1：名字与发布形态

- Python 包 `isabelle_patch_control`，命令 `isabelle-patch-control`，PyPI 与 conda 包名都是 `isabelle-patch-control`（conda：noarch python），
  版本从 **1.0.0** 起。GitHub 仓库改名 `isabelle_patch_control`（旧名自动跳转）。
- 1.0.0 不带任何补丁：`patches/` 整个目录、`categories.toml`、`order.txt` 机制、user/dev 分类全部删除（Isabelle2024 按第 15 条留在旧工具里，
  不搬）。旧 PyPI 包 `my-better-isabelle-prover` 停在 0.3.0，不下架。
- 子命令：`status`、`apply`、`unapply`、`apply-to`、`unapply-from`、`conda-hook`、`help`；删除 `patch`、`unpatch`、`build`、
  `--category`、`--force`。

### 决定 2：定位树与 feature 目录

- `--isabelle-home DIR` 取代 `--isabelle-bin`。默认值：`sys.prefix/isa`，且只在 `sys.prefix/conda-meta` 存在（工具跑在 conda 环境里）时
  使用；否则拒绝（exit 2）并提示该参数。工具**永不运行 `isabelle`**，不用 `shutil.which`，不读环境变量 `ISABELLE_HOME`：发行版名从
  `DIR/etc/ISABELLE_IDENTIFIER` 读（conda 树是 `Isabelle2025-2`），构建身份从 `DIR/etc/ISABELLE_ID` 读。钩子把 `$PREFIX/isa` 传给它。
- feature 目录的根：`--features-dir DIR` 显式给出时必须存在，否则 exit 3；不给时只在 conda 环境里用默认 `sys.prefix/share/isabelle_patch_control/features.d`
  ——目录不存在是正常的"没装任何 feature 包"（conda 随最后一个包删掉它），`status` 打印 `no feature packages installed` 并退出 0；
  不在 conda 环境里又没给 `--features-dir` 是 exit 3（第 19 条：不支持自装的 Isabelle）。
- 每个 feature 包把 `patches/<R>/*.patch` 与 `provenance.txt` 原样装到 `share/isabelle_patch_control/features.d/<feature>/`。工具不改这些文件。

### 决定 3：来历文件与按精确 tag 的链

- 来历文件 `provenance.txt` 的字段就是 `make-patches` 今天写的：`feature`（`<R>/<feature>`）、`release_tag`、`commit`、`base_tag`、
  `base_commit`、`base_package_version`、`base_pin`、`build_string_prefix`、`tree_hash`、`tree_hash_excludes`。工具读 `feature`、
  `release_tag`、`base_tag`，其余给配方渲染器与人看。
- **链按精确 tag 链接**，不按名字：
  1. 链底是树自己的记录：`etc/ISABELLE_ID` 在决定 10 的记录里 → 底是记录给出的发布 tag（`2025.2-0`：`Isabelle2025-2/expose_foreign/1`）；
     否则底是 `<R>/pristine/<ISABELLE_ID>`，`<R>` 来自 `etc/ISABELLE_IDENTIFIER`。
  2. 从底开始，每一级恰好一个 feature 目录的 `base_tag` 等于当前的 tag，它的 `release_tag` 成为下一级；两个目录的 `base_tag` 相同、或某个
     目录的 `base_tag` 谁都不等于（基没装、版本不配、发行版不配、树的 `ISABELLE_ID` 不是原版 changeset）都是 exit 3，报文点名是哪一个目录、
     它要的 tag、链上实际有的 tag。`feature` 字段的 `<R>` 必须等于树的发行版名。
  3. 这一条规则同时覆盖了 rev 1 的"版本不匹配检查"和"名字链接"：原版构建的 `ISABELLE_ID` 必须等于 `expose_foreign` 包所基的 pristine tag 里的
     changeset，否则链接不上——工具不需要知道哪个 changeset 是原版，CI 也不需要再写 k 文件。
- 工具不读 `order.txt`、不读 `categories.toml`、没有 `after`。

### 决定 4：引擎——`git apply`

- 全部补丁操作经 **一个函数** `git_apply(tree, patch_files, *, reverse=False, check=False)`：在 `tree` 目录下运行
  `git apply [--check] [-R] --whitespace=nowarn <patch 文件…>`，捕获 stdout/stderr，返回成功与否及输出。不传 `--directory`、不传
  `--unsafe-paths`（patch 文件里的路径都在树内）。`git` 的位置：先 `sys.prefix/bin/git`（Windows `sys.prefix/Library/bin/git.exe`），
  再 PATH；要求 `git --version` ≥ 2.43（本机实测版本），否则 exit 2。
- 一次调用交给 `git apply` 的 patch 文件集合是**一次原子操作**：任一文件对不上，整次什么都不改（§2.4）。`apply`/`unapply` 以 feature 为单位
  调用（一个 feature 的全部 patch 文件一次交），所以不会出现"同一次调用里半打"。
- 工具不 `chmod`、不复制、不写任何文件内容；唯一的写者是 `git apply`。打完后对被改写的文件把原来的权限位恢复到新 inode 上
  （Isabelle 的源码是 0444，`git apply` 按 umask 写出 0644/0664；恢复只碰新 inode，不影响缓存）。符号链接目标拒绝（exit 3）。
- 运行期间对树持有一把文件锁（`fcntl.flock` / Windows `msvcrt.locking`，锁文件 `DIR/etc/.isabelle_patch_control.lock`，由 `.gitignore`
  之外的 conda 树承载，不进 git 树），第二个进程等待或报忙。

### 决定 5：状态模型

每个 feature 的状态由它的文件各自的层级得出，不再有 rev 1 的"按 feature 合取 + covered"。

- 设文件 `p` 被链上（底以上的）feature `t1 < … < tm` 改过，`j` 是 `p` 的**层级**：在 `p` 的临时副本上按 `t_j, t_{j-1}, …, t_1` 的顺序
  逐个 `git apply -R --check`（每成功一个就真的反打到副本上再查下一个）全部通过，且在另一份副本上按 `t_{j+1}, …, t_m` 逐个
  `git apply --check` 全部通过。没有这样的 `j` 就是该文件 CONFLICT。临时副本放在一个临时目录里、保持 `p` 的相对路径，`git apply`
  在那里运行。
- 一个 feature 建的文件（`--- /dev/null`）若存在且内容恰好等于补丁给出的内容，视为与 applied、not-applied **都相容**；不存在视为
  not-applied；存在而内容不同视为 CONFLICT。
- feature `F` 的状态：全部文件层级 ≥ F 的位置 → **applied**；全部 < → **not-applied**；有的 ≥ 有的 < → **half-applied**；任一文件
  CONFLICT → **CONFLICT**。底以下的记录项显示 **pre-applied**。
- 全树的合法形状：applied 的 feature 是链（底以上）的一个前缀，前缀之上至多一个 half-applied。不合法（链中有洞）时 `status` 仍逐个打印，
  但退出 3 并说明哪一级是洞。
- `status` 的输出（第 17 条授权定稿）：
  ```
  pre-applied  expose_foreign           Isabelle2025-2/expose_foreign/1       (build isabelle-2025.2-0)
  applied      future_assign_interrupt  Isabelle2025-2/future_assign_interrupt/1   1 file
  half-applied light_locale             Isabelle2025-2/light_locale/1        32 files, 3 not applied
  not-applied  local_type_abbrev        Isabelle2025-2/local_type_abbrev/1    4 files
  CONFLICT     localized_record         Isabelle2025-2/localized_record/1     src/Pure/Isar/locale.ML
  ```
  每行后可加 `-v` 列出文件与各自层级；新建文件显示 `+++ b/` 那边的路径。退出码：选中的 feature 都是 pre-applied/applied 为 0，否则 1；
  链不合法为 3。

### 决定 6：`apply`、`unapply`、`--feature`

- `apply [--feature F] [--dry-run]`：按链序，对每个 not-applied 或 half-applied 的 feature，把它尚未到位的文件的 patch 文件一次交给
  `git apply`（half-applied 只补缺的那些）；applied 与 pre-applied 跳过；遇到 CONFLICT 停下、exit 1、打印 `git apply` 的输出。
  `--feature F` 打到 F 为止（F 的前置一并打）。
- `unapply [--feature F] [--dry-run]`：逆链序，对每个 applied 或 half-applied 的 feature 反打它已到位的文件；pre-applied 不反打；
  `--feature F` 从链尾反打到 F 为止（F 的后继一并卸）；不带 `--feature` 卸掉底以上全部。
- 两者在改了 `src/` 下任何文件之后都打印 heap 提示（文案见 §4）。工具自己不构建任何东西。
- 没有 `--force`。

### 决定 7：目录接口

`apply-to <目录> <feature 目录>` 与 `unapply-from <目录> <feature 目录>`：对 `<目录>` 一次交该 feature 目录的全部 patch 文件给
`git_apply`，不读来历文件、不看 conda 环境、不加锁、不恢复权限位；失败 exit 1 并原样打印输出。Python 函数
`isabelle_patch_control.engine.git_apply(...)` 是它们和 `apply`/`unapply` 的共同底层。`make-patches` 的门禁 (c) 与迁移方案的 (b2)
直接 `import` 这个函数（`sys.path.insert(0, TOOLS_DIR.parent)`），不经 PATH、不需要安装（决定 15）。

### 决定 8：conda 钩子

- 每个 feature 包的两个钩子各只有一行，调工具自己拥有的入口：
  `"$PREFIX/bin/isabelle-patch-control" conda-hook post-link <feature>` 与 `… conda-hook pre-unlink <feature>`；Windows 的 `.bat` 调
  `"%PREFIX%\Scripts\isabelle-patch-control.exe"`，不经 Cygwin（工具不再运行 `isabelle`）。钩子文本由配方渲染器生成（决定 9），所有包相同。
- `conda-hook post-link <F>`：对 `$PREFIX/isa` 做**整链幂等 `apply`**（不带 `--feature`）。理由：conda 先链接全部包再跑 post-link
  （§2.3），所以本次事务里所有 feature 的目录都已在；整链 apply 让"重链接一个下层包"也把上层补回去，而不是 rev 1 的单向 `--feature F`
  （评审 C4）。
- `conda-hook pre-unlink <F>`：`unapply --feature F`（反打 F 及其上面的），**只反打、永不打**。
- **退出码一律 0**（第 12 条）。结果写进 `$PREFIX/.messages.txt`：成功时列出本次打/卸的 feature 与 heap 提示；失败时写 `status` 的输出、
  `git apply` 的报错、以及修复命令（`isabelle-patch-control status` / `apply`）。失败的 post-link 留下的状态是"包装着、feature 未打"，
  `status` 看得见、`apply` 修得了。
- 新的 `isabelle` 构建的 post-link（第 13 条，CI 计划实现）：`[ -x "$PREFIX/bin/isabelle-patch-control" ] && "$PREFIX/bin/isabelle-patch-control" conda-hook post-link isabelle`
  ——同一个入口，整链 apply；它的 pre-unlink 不调工具。于是换 `isabelle` 包、`--force-reinstall`、clone 之后补丁自动恢复。对改不了的
  `2025.2-0`：`--force-reinstall isabelle` 或 clone 之后用户手动 `isabelle-patch-control apply` 一次，README 写明。
- 换 `isabelle` 包后 light 新建的三个文件会留在树里（conda 不跟踪它们）：按决定 5 它们与 not-applied 相容，所以 `apply` 能修，
  `conda create --clone` 不会因此失败（评审 C1、C3）。

### 决定 9：feature 包的配方、渲染器与发布

- 包名 `isabelle-<feature 名把 _ 换成 ->`：`isabelle-expose-foreign`、`isabelle-future-assign-interrupt`、`isabelle-light-locale`、
  `isabelle-local-type-abbrev`、`isabelle-localized-record`、`isabelle-local-datatype`；dev 补丁按 light 计划叫 `qiyuan-dev-patches`。
  版本 = 发布 tag 里的版本号；build string `Isabelle2025_2_<build 号>`；noarch generic。
- 依赖：`isabelle-patch-control >=1.0,<2`；`isabelle >=2025.2,<2025.3`（发行版范围，从 `build_string_prefix` 推出，写法同
  `contrib/Isabelle_RPC/conda/recipe.yaml:192`）；基包 `isabelle-<基> ==<版本>=Isabelle2025_2_*`（`base_pin`；基是 `pristine` 时没有）。
- 文件：`share/isabelle_patch_control/features.d/<feature>/`（patch 文件与来历文件原样），`share/doc/<包名>/README.md`（feature 说明），
  两个钩子（`bin/.<包名>-post-link.sh`、`.pre-unlink.sh`、`Scripts/.<包名>-post-link.bat`、`.pre-unlink.bat`）。
- **一个模板、一个渲染器**，放工具仓库 `tools/`：`tools/render-feature-recipe <包目录>` 从 `patches/<R>/provenance.txt` 算出版本、基包名、
  钉死、发行版范围、build string 前缀和钩子行，写出 `conda/recipe.yaml`——没有任何钉死是手抄的。`tools/release-feature.yml` 是一个可复用的
  GitHub Actions workflow（`workflow_call`），各 feature 仓库的 workflow 只是调它；它跑渲染器、rattler-build、本地渠道验收，发布只在
  `dry_run=false` 且用户下令时。各 feature 仓库要进 `sweep-old-versions.py` 的 `PUBLISH_REPOS`（`RELEASE_CHECKLIST.md:171-174`）。
- Windows 路径长度（迁移方案 §9 的问题）：pkgs 缓存里 feature 文件的路径是
  `<包名>-<版本>-Isabelle2025_2_<n>/share/isabelle_patch_control/features.d/<feature>/<扁平名>.patch`，今天最长 151 字符
  （`isabelle-future-assign-interrupt-1-Isabelle2025_2_0/…/src-Pure-Concurrent-future.ML.patch`），`isabelle` 包自己的预算是 198
  （`pack.sh:335-339,357`），可行；`features.d` 前缀占 40 字符，每个目标路径大约还有 76–102 字符余量。`make-patches` 加一道路径长度门禁
  （决定 15）。

### 决定 10：`2025.2-0` 的固定记录

工具内 `LEGACY_BUILDS = {"5533cd83156e": "Isabelle2025-2/expose_foreign/1"}`：`etc/ISABELLE_ID` 等于这个键的树，链底是该 tag，
`expose_foreign` 显示 pre-applied、不打不反打；环境里若装了 `isabelle-expose-foreign` 包，它的 `release_tag` 必须等于这个 tag（决定 3 的
链接规则自然做到），否则 exit 3 并提示更新 `isabelle`。表只会增不会改。以后的 `isabelle` 构建是原版，`ISABELLE_ID` 等于原版 changeset，
走决定 3 第 1 点的第二种情形。**在 CI 改成不打补丁之前不发布任何 `isabelle` 构建**（第 11 条），否则会出现工具当原版、实际带补丁的树。

### 决定 11：对 `isabelle-packaging-ci` 计划的要求

1. `isabelle` 包是原版：CI 不再 `pip install` 工具、不打补丁、不 `hg commit`；`etc/ISABELLE_ID` 等于发行版 changeset（`89701cf1768e`），
   与官方 tarball 相同。`check_patch_sync.sh`、`MBI_VERSION` 退役。不需要 `run_constraints`、不需要 k 文件、不需要树哈希断言。
2. `isabelle` 包的 post-link 加决定 8 的那一行（Windows `.bat` 同理）；pre-unlink 不变。
3. `PACKAGING_DESIGN.md` 加附录 A 的一节。
4. 建议把用户目录的后缀从 prefix 的 basename 改成能区分不同 prefix 的东西（如 prefix 的 hash），解决 §2.3 的共用 heap 问题；由 CI 计划定。

### 决定 12：三个新包的仓库

- `contrib/isabelle-base-features/`（一个仓库、两个包）：`expose_foreign/` 与 `future_assign_interrupt/` 各按 light 的布局：
  `tools/patched_files.txt`（各一行）、`tools/signature_additions.txt`（都为空：`check-signatures` 对 `pristine → expose_foreign`、
  `expose_foreign → future_assign_interrupt` 都是 0 additions，§8）、`tools/required_sessions.txt`（`Pure`；两棵私有树已各有 Pure 的
  tested 记录）、`patches/Isabelle2025-2/`（`make-patches` 写）、`README.md`（搬来 `patches/expose_foreign.md`、
  `patches/future_assign_interrupt.md`）、`conda/recipe.yaml`（渲染器生成，不手写）。
- `contrib/qiyuan_dev_patches/`：`tools/patched_files.txt`（八个文件）、`tools/signature_additions.txt`（三条，`check-signatures` 算出：
  `src/Pure/Syntax/printer.ML BASIC_PRINTER val show_types_nv`、`src/Pure/Thy/thy_info.ML THY_INFO val register_thy`、
  `src/Pure/sign.ML SIGN val map_syn`）、`tools/required_sessions.txt`（`HOL`、`HOL-IMP`、`HOL-ex`）、`patches/Isabelle2025-2/`、
  `README.md`（搬来 `register_thy.md`、`show_types_nv.md`、`expose_map_syn.md`，加一节 `skip_nitpick_examples`：它在 git 里是 commit
  30aab6e，在包里不是目录，第 10 条）。
- 两个仓库的 `conda/recipe.yaml` 由渲染器生成并提交；发布 workflow 调工具仓库的可复用 workflow。

### 决定 13：工具仓库里删掉与搬走的东西

删除 `my_better_isabelle_prover/patches/`（整个，含 Isabelle2024；第 15 条）、`categories.toml`；五份 `patches/*.md` 搬到决定 12 的仓库；
`README.md`、`reference.md`、`develop.md`、`AGENTS.md` 重写（feature 表、category 一节删除；加 "Coming from my-better-isabelle 0.x" 一节，
`help` 打印它：新工具看不见 0.x 打的补丁；在 `--category all` 打过的树上装 feature 包之前先 `my-better-isabelle unpatch --category dev`、
再 `pip uninstall my-better-isabelle-prover`；对 conda 的 `isabelle` 永远不要跑裸的 `unpatch`）。`RELEASE.md` 改写（两个版本文件、
`package-data` 只剩 `AGENTS.md`）。

### 决定 14：测试与发布

- `tests/`（pytest）：玩具 Isabelle 树（几个文件、`etc/ISABELLE_IDENTIFIER`、`etc/ISABELLE_ID`，**不需要假 `bin/isabelle`**）与玩具
  `features.d`（三个 feature 成链，含新建文件、删除文件、可执行文件、末尾无换行）：链接规则（精确 tag、洞、分叉、发行版不配）；状态模型
  的五种状态与层级；`apply`/`unapply` 与 `--feature`；half-applied 的补齐与撤销；新建文件留在树上的情形；`LEGACY_BUILDS`；目录接口；
  锁；权限位恢复；`--isabelle-home` 与 `--features-dir` 的拒绝规则。
- **钩子层测试**（`tools/tests/test_conda_hooks.sh`）：用一个小生成器造本地 `file://` 渠道（私有 `HOME`、`CONDARC`、`CONDA_PKGS_DIRS`），
  包里带决定 8 的真实钩子行、调真实工具、作用于玩具 Isabelle 树；断言：post-link 顺序等于链序且幂等；post-link 失败时包装着、树不变、
  `.messages.txt` 有报错；换 `isabelle` 包后 post-link 重打；重链接下层包后上层仍在；卸顶层包后其余不动；同级环境与 pkgs 缓存前后清单不变。
- 验收在本地渠道上跑（§6），在 Linux、macOS、Windows 三种 runner 上各一腿（packaging-ci 已有这三种）。
- 发布：PyPI `isabelle-patch-control 1.0.0` + conda `isabelle-patch-control`（配方在本仓库 `conda/recipe.yaml`，`run: [python >=3.12, git >=2.43]`），
  经本仓库的 release workflow，按 `RELEASE_CHECKLIST.md`；进 `PUBLISH_REPOS`。所有包（工具、六个 feature 包、dev 包、新的原版 `isabelle`）
  在本地渠道全部验收通过后，按用户命令一次发布（第 16 条）；工具的 conda 包不晚于 PyPI 上传。

### 决定 15：`make-patches` 的配套改动

1. 门禁 (c) 改为 `import` 决定 7 的 `git_apply`（`sys.path.insert(0, …)`），不再调 PATH 上的 `patch`；(b2) 同。
2. 拒绝没有 `---`/`+++` 对的块（git 对空文件的新建/删除就这样写）：空文件不发布。
3. 加路径长度门禁：每个 patch 文件在 pkgs 缓存里的完整路径（决定 9 的公式，取版本 99、build 99）不超过 198 字符。
4. 所有门禁（含 (c)）通过之前不碰包目录：块先写进 (c) 的临时目录，门禁都过了再删旧 `*.patch`、复制新文件、写 `provenance.txt`，最后打 tag。
5. 玩具测试相应补齐。

## 4. 命令行与用户可见文案（第 17 条授权）

```
isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]               每个 feature 一行：pre-applied | applied | half-applied | not-applied | CONFLICT
  apply    [--feature F] [--dry-run]   按链序打到 F（默认全部）
  unapply  [--feature F] [--dry-run]   逆链序从链尾卸到 F（默认全部，pre-applied 除外）
  apply-to      <dir> <feature dir>    目录接口：对 <dir> 打该 feature 目录的 patch 文件
  unapply-from  <dir> <feature dir>    目录接口：反打
  conda-hook    post-link|pre-unlink <feature>   供 conda 钩子调用（整链 apply / 反打 F 及其上面的；总是 exit 0，写 .messages.txt）
  help                                 打印 AGENTS.md
```

退出码：0 成功；1 CONFLICT 或 apply/unapply 失败；2 找不到树、`git` 缺失或版本太旧；3 feature 目录或链不合法（分叉、洞、版本或发行版不配、
符号链接目标、`--features-dir` 不存在、不在 conda 环境里又没给目录）。`conda-hook` 总是 0。

heap 提示（apply/unapply 改了 `src/` 下任何文件后打印；钩子写进 `.messages.txt`）：
```
Isabelle sources changed (light_locale). The prebuilt heaps are now stale; Isabelle rebuilds Pure and
HOL on first use into <ISABELLE_HOME_USER>/heaps (HOL takes several minutes). For headless tools run
once, when you are ready:  isabelle build -b HOL
```
链不合法的报文形如：`feature chain broken at Isabelle2025-2/light_locale/1: its base Isabelle2025-2/future_assign_interrupt/1 is not installed
(have: Isabelle2025-2/future_assign_interrupt/2)`。

## 5. 落地顺序

1. 工具改造（决定 1–8、10、13、14 的 pytest 部分）；pytest 全绿。此时 `patches/` 已删，旧工具 0.3.0 在 PyPI 上照常。
2. `make-patches` 配套改动（决定 15），其玩具测试仍全过；`make-patches pristine` 检查 (a) 仍过。
3. 建 `contrib/isabelle-base-features/`；用户下令 `make-patches expose_foreign 1`、`make-patches future_assign_interrupt 1`（迁移第 4 步）。
   然后 light 的完整构建与 `make-patches light_locale <版本>`；三个新 feature 就绪后各自 `make-patches`；建 `contrib/qiyuan_dev_patches/`、
   `make-patches dev_patches 1`。
4. (b2)：在 `isabelle-2025.2-0` 的两份副本上（工具按 `LEGACY_BUILDS` 认出 `expose_foreign` 为 pre-applied，从 `future_assign_interrupt` 起打）
   和在原版 archive 的两份副本上（从 `expose_foreign` 起打）各跑一遍：副本 A 经工具按链序打到链顶，副本 B 经 `git apply` 一次打
   `git diff-tree <链底 tag> <链顶 tag>`，整树相同；工具 unapply A 回到原状。
5. 渲染器、可复用 release workflow、钩子层测试（决定 9、14）；本地 `file://` 渠道：构建工具包、全部 feature 包、原版 `isabelle` 包（需 CI 计划
   落地，或先用 `2025.2-0` 的缓存副本）；§6 验收在三种 runner 上通过。
6. CI 计划：写、评审、落地（决定 11）；产出新的原版 `isabelle` 构建进本地渠道，重跑 §6。
7. 用户下令一次发布（第 16 条）；`PUBLISH_REPOS` 更新；各仓库的 `README` 与 `AGENTS.md` 就位。

## 6. 验收

- pytest 与钩子层测试全绿；`make-patches` 玩具测试 28+ 项全过；(b2) 两种基都通过。
- 本地渠道上的真实场景（三种 runner）：(a) 新环境 `conda install isabelle isabelle-light-locale` → `status` 显示链上各 feature applied，
  `.messages.txt` 有 heap 提示，`isabelle build -b HOL` 在用户目录重建成功（在用户授权的 runner 上）；(b) `conda remove isabelle-light-locale`
  → light 反打干净，新建文件消失；(c) `conda install --force-reinstall isabelle`（新原版构建）→ post-link 重打，`status` 不变；
  (d) `conda create --clone` → 新环境 `status` 与原环境相同；(e) 在 `2025.2-0` 上装 `isabelle-future-assign-interrupt` → `status`
  显示 `expose_foreign` pre-applied；(f) 故意制造冲突后装包 → 安装成功、`.messages.txt` 报错、`status` 显示 not-applied/CONFLICT、
  环境仍可用；(g) `conda remove isabelle` → 环境里无 `isa/` 残留。

## 7. light 计划 D4 清单逐条（`reader2_patch_scheme.md` 发现 1–16、决定 D1–D11）

| 条目 | 本计划的回答 | 状态 |
|---|---|---|
| 发现 1 syntax_phases.ML 与 dev 补丁重叠 | 链序解决：dev_patches 在链顶、以 light 之上的 feature 为基（迁移方案第 9、26 条） | 已裁定 |
| 发现 2 只更新 `isabelle` 包时补丁丢失 | 决定 8：新构建的 post-link 整链重打；`2025.2-0` 手动 `apply` | 用户第 13 条 |
| 发现 3 pre-unlink 失败只警告 | 决定 8：钩子 exit 0，`.messages.txt` 列出仍被改的文件 | 用户第 12 条 |
| 发现 4 `$CONDA_PREFIX` 找错地方 | 决定 2：从 `$PREFIX`/`sys.prefix` 推，不读 `CONDA_PREFIX` | 本计划 |
| 发现 5 多个补丁不原子 | 决定 4：`git apply` 一次交一个 feature 的全部文件，原子 | 本计划 |
| 发现 6 新文件的 diff 写法 | `--- /dev/null`（迁移方案第 13 条）；`git apply` 原生支持 | 已裁定 |
| 发现 7 `.orig`/`.rej` 残片 | `git apply` 失败不写任何文件，没有残片 | 本计划 |
| 发现 8 往返验证的参照 | 迁移方案门禁 (c)：基 tag 的 `git archive` | 已裁定 |
| 发现 9 备份 diff 收进别人的改动 | 迁移方案门禁 (f)、自有 commit 门禁 | 已裁定 |
| 发现 10 版本键只认内部目录 | 决定 3：发行版名从 `etc/ISABELLE_IDENTIFIER` 读，来历文件的 `<R>` 必须相等；`isabelle >=2025.2,<2025.3` | 本计划 |
| 发现 11 `after` 与 `order.txt` | 决定 3：废除，链由精确 tag 推出；`unapply --feature X` 先卸 X 之上的 | 本计划 |
| 发现 12 平台 | 决定 4、8、9：`git apply`，conda-forge `git`，`.sh` 与 `.bat` 钩子，全平台 | 用户第 18 条 |
| 发现 13 硬链接与 chmod | 决定 4：不 chmod，`git apply` 写新 inode；权限位恢复只碰新 inode | 本计划 |
| 发现 14 补丁文件撞名 | `make-patches` 的扁平命名（完整路径编码），仓库布局与 `features.d` 相同 | 已落地 |
| 发现 15 并发 | 决定 4：文件锁 | 本计划（第 17 条授权） |
| 发现 16 其他前端不跑 link 脚本 | 只支持 conda，文档写明 | 本计划（第 17 条授权） |
| D1 重叠怎么处理 | 同发现 1 | 已裁定 |
| D2 钩子失败 | exit 0 | 用户第 12 条 |
| D3 更新 `isabelle` 时防丢 | 新构建 post-link 重打（不钉 build、不加运行时检查） | 用户第 13 条 |
| D4 已打补丁账本 | 不建；状态由 `git apply --check` 重放得出，conda 的 `paths_data` 可作辅助证据（未采用） | 本计划 |
| D5 与打包设计对上 | `PACKAGING_DESIGN.md` 例外一节（附录 A） | 用户第 14 条 |
| D6 pristine 参照与是否含构建 | 迁移方案 §5.1 (c)、(e) | 已裁定 |
| D7 新文件的 diff 写法 | `/dev/null` | 已裁定 |
| D8 平台范围 | 全平台 | 用户第 18 条 |
| D9 开发时找外部 feature | 开发不用工具（私有树经 `run-tree`）；需要时 `--features-dir` | 本计划 |
| D10 外部 feature 的类别 | 没有类别：装了的包就是要打的 | 本计划 |
| D11 conda 版工具带不带内部 feature | 不带（第 11、15 条） | 已裁定 |

## 8. 证据（2026-10-22/23 实测；评审 agent 的实验在 scratchpad `review-ipc/`）

- `git apply`（git 2.43.0，普通目录）：light 32 文件 diff 正打/反打树哈希分别等于 light 树与基树；`--check` 与 `-R --check` 的通过/失败与
  状态一致；玩具：新建可执行文件可执行位正确、删除、末尾无换行保持（`700a51`）、反打删掉新建文件；损坏一个文件后四文件 diff 一个都不动；
  0444 且 links=2 的文件打后新 inode 664、缓存那份内容与 444 不变；30 行文件中部的 hunk 偏移 2 行成功应用，贴着文件末尾的 hunk 偏移后
  被拒。
- `patch-ng` 1.19.1：正打 light 对；反打不删新建文件（树 ≠ 基）；末尾无换行被补上换行；对不上时已改的文件不回滚。`whatthepatch` 1.0.7：
  文本层严格、支持 reverse，丢末尾无换行信息。`pygit2` 1.20.1（libgit2 1.9.x）：bare 仓库重定向 workdir 后 `applies`/`apply` 对 light 正确，
  无反向应用。
- conda-forge `git` 各平台体积与 win-64 的 PortableGit 来源：§2.3。
- conda 25.11.1 的钩子/回滚/链接顺序：§2.3 引用的源码行（评审 C1、C2、C4 的 defender 在玩具渠道上实测）。
- `check-signatures`：`pristine → expose_foreign`、`expose_foreign → future_assign_interrupt` 各 0 additions；
  `future_assign_interrupt → ab6006e` 三条。
- 旧构建 `isabelle-2025.2-89701cf1768e_0` 的事实：评审 C13 的 defender 核实（`opt/Isabelle2025-2`、ID `89701cf1768e`、含 `expose_foreign`、
  未装在任何环境）。
- 路径长度：评审 C25 的计算（最长 151，预算 198）。

## 9. 不做的事

- 工具不构建 heap。
- 不做 conda 不跟踪的"已打补丁账本"。
- 不支持一个环境里两棵 Isabelle；不支持自装的 Isabelle2025-2；不支持 pixi/micromamba。
- 不改 `make-patches` 的输出格式。
- 不自己实现任何补丁逻辑。

## 附录 A：写进 `isabelle-packaging-ci/PACKAGING_DESIGN.md` 的一节（文案按第 14、17 条由作者定稿，CI 计划落地时写入）

```
## 10. 例外（用户 2026-10-23 裁定）：feature 包经 post-link 改写 `$PREFIX/isa`

§3.1 和 §9 的原则——一切随包装进去，post-link 不生成 conda 不跟踪的东西，不原地 patch 用户的 Isabelle——仍然是 `isabelle` 包自身的原则：
它从此是原版，不带任何补丁。补丁改由 feature 包分发，每个 feature 一个 conda 包（isabelle-expose-foreign、isabelle-light-locale……），
由 isabelle-patch-control 在包的 post-link 里打到 `$PREFIX/isa`、在 pre-unlink 里反打。这是对 §9 的一条有意的例外，理由：

1. 用包管理系统管补丁，用户自行决定装哪些补丁：装 isabelle-light-locale 就有 light locale，不装就没有；依赖关系（light 依赖
   future_assign_interrupt 依赖 expose_foreign）由 conda 求解器保证，版本由精确钉死保证。
2. `isabelle` 包保持原汁原味：与官方发行版逐字节一致（etc/ISABELLE_ID 等于发行版 changeset），任何人都能核对；不再有"我们的补丁版"。
3. 补丁的权威是 Isabelle 源码的 git 仓库（迁移方案），feature 包是从发布 tag 之间的 diff 自动生成的，往返一致由发布门禁保证。

边界与代价：
- 只改渠道自己发的 `$PREFIX/isa` 那棵树，不碰用户自装的 Isabelle（工具在非 conda 环境里拒绝运行）。
- `$PREFIX/isa` 自带的 Pure/HOL/Main heap 在打了改 `src/` 的 feature 之后过期，Isabelle 在首次使用时重建到该环境的用户目录；用户接受。
- conda 不知道 `isa/` 下的文件被改过。换 `isabelle` 包、`--force-reinstall`、clone 之后由 `isabelle` 包自己的 post-link 调工具把已装的
  feature 重打回去；清理依赖 pre-unlink 成功执行，失败只会留下 `.messages.txt` 里的提示和 `status` 可见的状态，不会损坏环境。
- 钩子一律 exit 0（§4 的规矩不变）。
```
