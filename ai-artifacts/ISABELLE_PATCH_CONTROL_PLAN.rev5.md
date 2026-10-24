# 补丁工具改造计划：`my_better_isabelle_prover` → `isabelle_patch_control` —— rev 5（2026-10-24）

> 状态：**rev 5，待定向重评**（第四轮 judge 的建议：只重评决定 9、11、12、16 与 §10 各行，不必整轮）。四轮评审在
> `ISABELLE_PATCH_CONTROL_REVIEW1.md`（29 条）、`…REVIEW2.md`（26 条）、`…REVIEW3.md`（32 条）、`…REVIEW4.md`（24 条，judge 判"未就绪但接近"）；
> 副本 `…PLAN.rev1.md` … `…PLAN.rev4.md`。rev 5 按第四轮的 24 条裁决、用户 2026-10-24 的三条新裁定（§0 第 33–35 条）改写；§10 逐条对照，
> **凡与评审裁决不同之处都在 §10 明说**（rev 3、rev 4 的 §10 各有八处写得不实，评审查出；本版 §10 的每一行都对着裁决原文核过）。
> 这是迁移方案 `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`（下称"迁移方案"）§0 第 19 条划出的两份计划之一；§5.3 定了本工具对外的接口，
> 本计划定内部怎么改。另一份（`isabelle-packaging-ci`）晚些写，决定 12 列出它必须提供的东西。
> 行号针对 `contrib/my_better_isabelle_prover`（工具仓库）、`contrib/isabelle-packaging-ci`（CI 仓库）、本机 conda 25.11.1
> （`~/miniconda3/lib/python3.13/site-packages/conda`），除非另注。事实出处见 §8。

## 术语

沿用迁移方案 glossary 的 **feature**、**链序**、**基 tag**、**发布 tag**、**来历文件**、**patch 文件**；"前 k 节"只剩历史含义（§0 第 11、22 条）。
链：`pristine → expose_foreign → future_assign_interrupt → light_locale → local_type_abbrev → localized_record → local_datatype → dev_patches`。
**链底**是 `pristine`；**链序最末**是 `dev_patches`。**链顶**指工具从环境里的 feature 目录建出的那条链的最后一个 feature——装了什么就到哪，
不一定是 `dev_patches`。**tip** 指 `make-patches` 要发布的那个 commit。

- **工具**：本仓库的 Python 程序。今天叫 `my-better-isabelle-prover`（命令 `my-better-isabelle`），改造后叫 `isabelle_patch_control`
  （命令 `isabelle-patch-control`）。
- **原版构建**：以后的 conda `isabelle` 包：Isabelle 源码一字不动、`etc/ISABELLE_ID` 等于官方 changeset `89701cf1768e`，另有打包改动（第 20 条）。
  已发布的 `isabelle-2025.2-0`（`ISABELLE_ID` `5533cd83156e`，带 `expose_foreign`）不是原版构建；第 22 条后没有任何 feature 包能装到它上面。
- **build 号**：conda 包的 build number。说到某个包的 build 号时都点明是哪个包的。`isabelle` 包的 build string 就是它的 build 号（§2.3）；
  feature 包的 build string 是 `Isabelle2025_2_<该 feature 包的 build 号>`（第 30 条）。
- **树**：工具作用的那棵 Isabelle 目录。conda 环境里是 `$PREFIX/isa`（CI `recipe.yaml:75-87`）。
- **feature 包**：一个 feature 的 conda 包：patch 文件加来历文件（`make-patches` 的产物），加两个钩子；light 另带**组件载荷**（第 21 条）。
- **feature 目录**：feature 包装进 conda 环境后的目录 `$PREFIX/share/isabelle_patch_control/features.d/<feature>/`。
- **组件载荷**：feature 包里可选的 Isabelle 组件（`share/<包名>/` 下的 `ROOT` 与 theory），按渠道组件包的规矩用 `isabelle components` 登记。
- **组件登记**：`isabelle components -u <目录>` 写进 Isabelle 用户目录里 `etc/components` 文件的那一行（`components.scala:294-302`）。
- **层级**：一个文件相对于链的位置：文件内容等于"链底以上编号 ≤ L 的、改过该文件的 feature 都打过"的样子，就说它在层级 L（决定 6）。
- **目标层级**：`apply`/`unapply` 要把一个文件移到的层级，每个文件自己一个（决定 7）。
- **暂存目录**：树旁边、同一文件系统上的目录 `<树的 realpath>.staging`，**只有持排他锁的那次运行**在这里重放并装入（决定 5）。
- **临时目录**：工具用 `tempfile.mkdtemp()` 建的目录；其他一切 `git` 调用都在这里跑——读目标、`status`、任何 `--dry-run`、锁超时后 pre-unlink
  的层级计算、目录接口（它建在 `realpath(<目录>)` 旁边）。`git` 只在暂存目录或临时目录里运行。
- **钩子**：conda 在装包后运行的 post-link 脚本和卸包前运行的 pre-unlink 脚本（`$PREFIX/bin/.<包名>-post-link.sh`，Windows 是
  `%PREFIX%\Scripts\.<包名>-post-link.bat`）。
- **钩子片段**：工具仓库拥有、所有 feature 包和原版构建的 post-link 逐字复制的那段文本（决定 9），`.sh` 与 `.bat` 各一份。
- **目录接口**：对一个指定目录打或反打一个 feature 目录的 patch 文件、不读 conda 环境的子命令（迁移方案 §5.3，决定 8）。
- **批量发布 workflow**：工具仓库里把整条链一次构建、验收、发布的 GitHub Actions workflow（第 25 条，决定 11）。

## 0. 用户已裁定的事（不再重议）

出自迁移方案 §0 与 light 计划的：
1. 发布方式不变：patch 文件经工具打到用户装好的 Isabelle 上；git 仓库只用于开发（迁移方案第 5 条）。
2. 工具"逐步改成不带任何预置补丁的纯框架"（light 计划 D1 第 3 句，迁移方案 §0 D1 引文第 3 条与 §5.3）；`isabelle-packaging-ci` 变成纯框架
   （迁移方案第 8 条）。
3. 基补丁各自成 feature 包（迁移方案第 21 条）。该条第 (1) 点"构建预先打好前几节"已被第 11 条修订，后半句"不钉 `isabelle` 的 build 号"已被
   第 22 条修订（迁移方案第 31 条）。
4. 新建文件的 patch 头部用 git 原生的 `--- /dev/null`（迁移方案第 13 条）；包精确钉死所对的基包版本（第 14 条）；feature 包的 build string 是
   **`<发行版名把 - 换成 _>_<build 号>`**，即 `Isabelle2025_2_<build 号>`（第 27 条原文；rev 3 曾擅改，第 30 条撤回）；包的版本号是发布 tag
   里的版本号（迁移方案决定 3）。
5. 共用脚本放工具仓库顶层 `tools/`（迁移方案第 20 条、决定 6）——已写好、**尚未提交**（`?? tools/`，§5 第 0 步）。
6. 不发空的 0 版包；`qiyuan_dev_patches` 等三个 feature 发布后再发（迁移方案第 25 条）。
7. **feature 补丁由 conda 包的 post-link 打、pre-unlink 反打，heap 全部失效按需重建，用户接受**（用户 2026-09-14 与 2026-10-11；
   light 计划 `LIGHT_LOCALE_PLAN_REV37.md:5805`、`:7796` 第 (1) 条；(44) 只替换了开发侧）。本计划不重议安装方式。
8. light 计划 D4：工具层的十九条推迟到动手改工具时逐条请用户定；清单在 `ai-artifacts/LIGHT_LOCALE_HANDOFF.md:1979`（(1)–(19)），细节在
   `ai-artifacts/readers_impl0/reader2_patch_scheme.md`（发现 1–16、决定 D1–D12）。本计划 §7 逐条对应。
9. 迁移方案 §5.3 对工具的接口要求：输入是 `features.d/<feature>/`；按链序打、逆序卸、`status` 逐 feature 列出；目录接口；
   `_read_patch_target` 认 `/dev/null`、`status` 对新建文件显示真实目标路径。"前 k 节识别"按第 11、22 条不再存在。
10. 迁移方案 §0 第 15 条 Q4 把 `skip_nitpick_examples` 登记为 `dev_patches` 里的补丁目录；§6 第 1.6 步把它做成 commit 30aab6e。包的布局由本
    计划定（第 17 条）。

用户 2026-10-23（rev 1 评审之后）：
11. **conda `isabelle` 包是原版，不带任何补丁**。原话："我建议 isabelle 就是原版，原汁原味。我建议再发布一个 isabelle 新版本，是原版，不带有
    expose_foreign；然后 expose_foreign 按我们之前讨论的，是单独一个 patch package"。在 CI 改成不打补丁之前不再发布任何 `isabelle` 构建。
    （迁移方案 §0 第 30 条。rev 2 据此设的"`2025.2-0` 的固定记录"已由第 22 条取消。）
12. **钩子失败一律 exit 0**，结果经 `$PREFIX/.messages.txt` 报告（"赞同你的建议"）。用户答的是 rev 1 问题 1，覆盖两个钩子。
13. **新的 `isabelle` 构建的 post-link 在装了工具时把已装的 feature 重打一遍**（"赞同 (a)"）。（同条"对 `2025.2-0` 手动 `apply`"已由第 22 条
    取消：它上面装不了 feature 包。）
14. **`PACKAGING_DESIGN.md` 记一条例外并详细论证**：用包管理系统管补丁，用户自行决定装哪些补丁，`isabelle` 包保持原样（附录 A）。
15. Isabelle2024 的补丁集留在旧工具 `my-better-isabelle-prover` 里，不再考虑；不切新版本。
16. 三个 feature 本周就绪；所有包等全部就绪后按用户命令一次发布，D1 的"逐步"不再构成顺序问题；旧工具 0.3.0 留在 PyPI 上不动。
17. 文案与测试相关的决定，在不改设计的前提下授权作者自决（"你可以自决"）。据此定：状态词 `applied | half-applied | not-applied | CONFLICT`
    （rev 2 的 `pre-applied` 随第 22 条消失）；`skip_nitpick_examples` 在包里以 commit 与 README 一节存在；工具运行时对树加锁；只支持 conda。
18. **引擎用 `git apply`**（"好，就定了 git apply"；此前"我反对自己写引擎。这种事情应该走已有的库"）。**必须支持全平台**。
19. 用户自装、不在 conda 里的 Isabelle2025-2 不支持（"赞同 (a)"，答的是 rev 1 问题 8）。rev 2 同条写的"feature 包声明
    `isabelle >=2025.2,<2025.3`"是作者宣布的、不是用户裁定，且已被第 22 条的精确钉死取代。
20. （2026-10-23，第二轮评审 C9 的问题 1）**"原汁原味"指 Isabelle 源码一字不动、`etc/ISABELLE_ID` 是官方 changeset；
    `scripts/pack.sh` 对 `etc/settings`（`ISABELLE_HOME_USER` 加 `-conda-<环境名>` 后缀）、`etc/options`（`ML_system_64` 默认 true）、
    `etc/components`（删 nunchaku 行）三个文件的打包改动保留**（"应当保留 scripts/pack.sh 所改动的那三个文件"）；CI 编的 heap 与
    Windows 的 `bin/isabelle.bat` 随之保留。附录 A 与决定 12 按此改写，删"逐字节一致"。（第 31 条修订了其中用户目录后缀的写法。）
21. （2026-10-23，第二轮评审 C11 的问题 2）**light 的 Pure 补丁与 HOL 侧 session（`contrib/light_locale/ROOT`、`Light_Locale.thy`）
    做成同一个包 `isabelle-light-locale`**，不拆 session 包（"这两部分本就是同一个项目内的啊，本来版本就是耦合的啊"）。据此：
    feature 包模板加一个可选的组件载荷（`share/<包名>/` 下的 ROOT 与 theory，按渠道 `RELEASE_CHECKLIST.md` §4 的组件包规范用
    `isabelle components -u/-x` 登记）；钩子 = 钩子片段 + 组件包规范的登记行，只有带组件的包才有后者；版本仍是补丁发布
    tag 的版本号，HOL 侧单独改动也走一次新的 light 发布并连带重发其上的 feature 包，这是用户接受的既有耦合。
    作者 2026-10-24 对用户说"HOL 侧改了就重跑 `make-patches` 得到新 tag、补丁内容可以不变"，不完整：`make-patches` 拒绝在同一个 commit 上打
    第二个发布 tag（决定 16），所以 HOL 侧单独改动的发布流程是：在 `<R>/light_locale` 分支上一个 commit（空 commit 即可）、一次 tested 构建、
    `make-patches light_locale <v+1>`，然后对其上每一层依次 merge、tested 构建、`make-patches`（决定 11 的例子）。
22. （2026-10-23，第二轮评审 C22 的问题 3）**每个 feature 包精确钉死它所对的 `isabelle` 构建**（用户提议"各个 Feature 包把 build number
    直接固定死"，作者赞成并实测，用户"确认"）。写法 `isabelle 2025.2 <isabelle 的 build string>`；版本和 build string 都定死。后果：没有任何
    feature 包能装到 `2025.2-0` 上，`LEGACY_BUILDS` 记录、rev 2 决定 10、"2025.2-0 上手动 `apply`"全部删除；每发一个 `isabelle` 构建就把
    全部 feature 包重发一遍（版本不变、各包 build 号加一、钉死换新，批量发布 workflow 接 **`isabelle` 包的 build 号**输入）；README 的更新命令是
    `conda update --all`（libmamba 下单独 `conda update isabelle` 不动，实测）；CI 五个平台腿同一个 build 号；批量发布先发原版 `isabelle`
    再发 feature 包。记录里"别的 ID 一律 exit 3"那句已由第 29 条修订为"有 feature 目录才 exit 3"。
    这修订迁移方案 §0 第 21 条的后半句（"不是 `isabelle` 的版本或 build 号"），基 feature 包之间的精确钉死（迁移 §0 第 14 条）照旧。
    实测：scratchpad `pintest/`——在旧构建上装 feature 会自动升 `isabelle`；新构建未配套重发 feature 时 update 原地不动、显式装报冲突、
    feature 从不被悄悄卸掉。
23. （2026-10-24，第二轮评审 C24 的问题 4）**工具 1.0.0 只发 conda，不发 PyPI**（"赞同 (a)"）。旧的 `my-better-isabelle-prover` 0.3.0
    留在 PyPI 上不动；`pyproject.toml` 的名字保留，只用于 conda recipe 内部的 `pip install . --no-deps` 与开发者的 editable 安装
    （含义见第 32 条）。
24. （2026-10-24，第二轮评审 C2 的问题 5）**暂存目录加原子改名是唯一的写树路径，与第 18 条"引擎用 `git apply`"一致**（"赞同 (a)"）。
    补丁内容只由 `git apply` 在树外、同一文件系统的暂存目录里对每个文件的副本重放产生（一个补丁文件一次调用）；工具只做复制、
    设权限位、`os.replace`/`os.unlink`，一次一个文件；每个文件任何时刻非旧即新，中断后下一次 `apply`/`unapply` 接着做完；
    `status`、`--dry-run`、`apply`、`unapply`、目录接口共用"先重放、再决定装不装"一条路径；`git` 永远只在工具自己建的目录里跑。
    实测依据：`git apply` 改多文件时先 `unlink` 全部旧文件再逐个创建（strace，scratchpad `verify2/t3.strace`），rev 2 的
    "每次调用原子"只在 hunk 不匹配、什么都不写时成立。
25. （2026-10-24，第二轮评审 C12/C13 的问题 6）**一个批量发布 workflow，住在工具仓库**（`xqyww123/my_better_isabelle_prover`，改名后
    `isabelle_patch_control`）**的 `.github/workflows/` 下**（用户"赞同你的建议"一个批量 workflow，仓库"建议 (2)"）。它接 `isabelle`
    包的 build 号与各 feature 发布 tag 两组输入，按 tag 检出各 feature 仓库、现场渲染 recipe、把工具包与全部 feature 包构建进一个本地渠道、
    五个平台腿上跑 §6 验收，通过后上传（上传方式由第 27 条修订为只调一次 `publish-conda.yml`）。后果：工具仓库要 `gh secret set` 两个
    R2 密钥、加进 `PUBLISH_REPOS`；GitHub 改名在 workflow 存在之前；feature 仓库自己不需要任何 workflow。作者曾改推荐
    `isabelle-packaging-ci`（密钥已在、`isabelle` 包的 build 号同处产生），用户仍选工具仓库。
26. （2026-10-24，第三轮评审 C1 的问题 1）**原版构建的 post-link 重新执行依赖 `isabelle` 的已装包的 post-link**（用户："本质上我们是要重新
    执行后续依赖的 post link 脚本"、"赞同 (d)"），由 CI 计划在 `isabelle` 包里实现；**`isabelle` 包可以依赖 Python**（用户原话），所以这段
    扫描可以用 Python 写。扫描 `conda-meta/*.json` 的 `depends` 找出（含间接）依赖 `isabelle` 的已装包，按依赖拓扑序对每个仍有
    `bin/.<包名>-post-link.sh`（Windows `Scripts\.<包名>-post-link.bat`）的包重跑其 post-link，照 conda 的样子给 `PREFIX`、`PKG_NAME`、
    `PKG_VERSION`、`PKG_BUILDNUM`。这也修好从 `2025.2-0` 第一次升级时丢组件登记那一回（旧构建的 pre-unlink 改不了，新构建的 post-link
    重建）。**不加标记**：依赖 `isabelle` 且环境里有 post-link 脚本的包都重跑（用户曾提议给 feature 包加标记决定是否重跑，作者指出需要重跑的
    是组件包、它们已发布且无标记，用户"很好"）；"依赖 `isabelle` 的包的 post-link 必须可重复执行"写进对 CI 计划的要求与
    `RELEASE_CHECKLIST.md` §4（措辞见第 34 条）。**组件包不精确钉死 `isabelle` 构建**，维持 `isabelle >=2025.2,<2025.3`（用户曾提议所有包都
    钉死构建，作者指出它盖不住 `--force-reinstall isabelle`、要六个组件仓库每次重发、保证的内容又少，用户"好的，赞同你的建议"）；feature 包的
    精确钉死（第 22 条）不变。"含间接依赖"已由第 34 条修订为只限直接依赖。
27. （2026-10-24，第三轮评审 C6 的问题 2）**整批验收过的产物只调一次 `publish-conda.yml`**（"赞同你的建议"）。修订第 25 条的"按依赖顺序逐个调"：
    `publish-conda.yml` 对产物里全部 `.conda` 一起查重、一起上传、一次重建索引（`:148-203`），所有包是 noarch、共用一个 `repodata.json`，
    一次索引推送整批同时可见，门禁对整批全有或全无。
28. （2026-10-24，第三轮评审 C7 的问题 3）**上层 feature 不得删掉、改名或完全撤销下层 feature 的改动**（"赞同"）：`make-patches` 加门禁——
    被改文件在链顶的内容（或不存在）若与它在链底或任何下层发布 tag 上的内容相同，拒绝发布并点名文件与 tag；这类改动放进下层 feature 的
    新版本。工具端：同时匹配几个层级的文件一律 CONFLICT，rev 3 决定 7 的"取相同结果"规则删除。今天的真实链 0 例（评审实测）。
29. （2026-10-24，第三轮评审 C9 的问题 4）**没装任何 feature 包时，不论树是哪个构建，`status` 打印 "no feature packages installed"、exit 0**
    （"赞同你的建议"）；树上出现任何 feature 目录而其 `base_tag` 的 pristine changeset 不等于树的 `ISABELLE_ID` 时才 exit 3 并提示
    `conda update --all`。这修订第 22 条记录里"别的 ID 一律 exit 3"那一句；工具不内置官方 changeset 表。
30. （2026-10-24，第三轮评审 C14 的问题 5）**feature 包的 build string 保持迁移方案第 27 条的 `Isabelle2025_2_<build 号>`**（"按你建议来"）；
    rev 3 决定 10 的 `Isabelle2025_2_<isabelle 构建号>_<build 号>` 撤回。build 号怎么推出见决定 10。
31. （2026-10-24，第三轮评审 C25 的问题 6）**CI 计划在 Isabelle 用户目录的后缀 `-conda-<环境路径最后一段>` 后面加一段环境完整路径的短 hash**
    （"赞同你的建议"），每个环境各有各的用户目录；这是对第 20 条保留的 `etc/settings` 打包改动的一处修订。现有用户升到原版构建时目录换名，
    旧构建的 pre-unlink 本来就删旧目录，无额外损失。
32. （2026-10-24，第三轮评审 C31 的问题 7）第 23 条"`pyproject.toml` 的名字保留"的含义确认为：**`[project].name` 字段保留、值改成
    `isabelle-patch-control`**，不发 PyPI，只供 conda recipe 的 `pip install . --no-deps` 与 editable 安装用（"按你建议来"）。
    旧值会让 `pip uninstall my-better-isabelle-prover` 卸掉新工具（评审实测）。
33. （2026-10-24，第四轮评审 C3 的问题 1）**原版构建的 post-link 不再自带钩子片段的副本**（"赞同删除"）：它只做自己现有的提示、第 26 条的
    重跑依赖者的 post-link、`exit 0`。第 13 条的"重打已装 feature"由重跑里第一个 feature 钩子（就是钩子片段）完成——conda 在所有 post-link
    之后才写包记录、先删被卸包的记录（`link.py:938-999`，`path_actions.py:1209-1219`），所以重跑扫到的恰是不在本次事务里的已装包，事务里的
    包自己跑 post-link，每个 feature 钩子每次换 `isabelle` 恰跑一次。随之删除：决定 11 对 `isabelle` 包 post-link 的逐字节核对及其下载，
    决定 1 里 `isabelle` 包对工具命令行的绑定；完整诊断只由链顶 feature 的钩子写。
34. （2026-10-24，第四轮评审 C4 的问题 2）**重跑只限 `depends` 里直接写了 `isabelle` 的已装包**（"赞同你的建议"），修订第 26 条的"含间接"。
    理由：间接依赖者 `isabelle-semantic-data` 的 post-link（`isabelle-semantics post-install-system-db`）设计上只在数据载荷换了时触发，
    重跑会清用户本地的向量缓存（`semantics.py:1567-1607`）；所有组件包与 feature 包都直接依赖 `isabelle`，已发布的包一个不用重发。
    配套契约写进 `RELEASE_CHECKLIST.md` §4：post-link 会动 Isabelle 树或用户目录的包必须直接依赖 `isabelle`；直接依赖者的 post-link
    在自己的文件没变时重跑必须无效果。作者对用户说过"重跑集合今天恰好是组件包和 feature 包"，不实，见下方更正。
35. （2026-10-24，第四轮评审 C10 的问题 3）**tested 记录绑住 `-d` 目录的仓库状态**（"这个按你建议来吧"）：`run-tree` 对每个位于 git 工作树里的
    `-d` 目录多记一行（该仓库顶层、HEAD、未提交的文件），构建期间这些行变了就不写记录；`make-patches` 的门禁 (e) 对带 `tools/component_files.txt`
    的包只接受"随包发出的文件在记录里无未提交改动、且在记录的 HEAD 与要发布的 commit 之间 `git diff --quiet -- <这些文件>` 为真"的记录
    （按内容比较，light 仓库里无关的 commit 不逼重跑构建）。这修订迁移方案对 tested 记录的定义（glossary 与 `run-tree` 的说明），记为
    迁移方案 §0 第 32 条。另外不论此条，批量发布 workflow 在 linux-64 上总是构建装好的带组件载荷的 session（评审 C10）。
作者 2026-10-24 对用户的更正（第二轮评审 C16、C22 与第三轮 C4 查出）：
- 作者 2026-10-23 04:46 对用户说"问题 10 后半（内置 feature 出新版）消失了"是错的；该问题以问题 3 重新提出，由第 22 条解决。
- 作者同一条消息说"Semantic_Embedding 的 conda 包要改成依赖 `isabelle-expose-foreign`"，**不需要**：Performant_Isabelle_ML 0.2.0 起的
  `library/rescue_foreign.ML`（`Performant_Isabelle_ML.thy:7` 加载）在原版 Pure 上把 `Foreign` 重新绑回全局 ML 名字空间，
  Semantic_Embedding 已依赖 `isabelle-performant-ml >=0.2.0,<0.3.0`（`Semantic_Embedding/conda/recipe.yaml:338`）。生态外自己调
  `Foreign` 的用户才需要 `isabelle-expose-foreign`（决定 12 第 8 点的发布说明）。同条消息答应"记进计划"的另一件事——`isabelle-ai`
  元包要不要依赖 `isabelle-future-assign-interrupt`——记在 §9。
- HOL 侧单独改动的发布流程，见第 21 条末。
- 作者 2026-10-24 对用户说"依赖 `isabelle` 且有 post-link 的包，今天恰好就是组件包和 feature 包，它们的钩子都幂等"，**不实**：`isabelle-semantic-data`
  经 `isabelle-semantic-embedding` 间接依赖 `isabelle`，它的 post-link `isabelle-semantics post-install-system-db` 重跑会清掉用户本地的向量缓存
  （§2.3）。第 34 条据此把重跑限于直接依赖者。

## 1. 目标与范围

**目标。** 工具不再带补丁，而是"认得 conda 环境里装了哪些 feature 包、按链序把它们打到 `$PREFIX/isa` 上、逆序卸掉、随时报告每个 feature
的状态"的框架。打补丁的引擎是 `git apply`，只在工具自己建的目录里对单个文件的副本运行；工具自己只做复制、改名、删除，不含任何补丁逻辑。

**范围内。** 改名与发布形态；定位树；feature 目录与来历文件；按精确 tag 的链；`git` 的调用方式与隔离；写树的路径；状态模型；
`apply`/`unapply`；目录接口；conda 钩子；feature 包的配方模板与渲染器；批量发布 workflow 与发布程序；对 CI 计划的要求；三个新包的仓库布局；
测试；`make-patches` 与 (b2) 的配套改动；D4 清单逐条；用户可见文案。

**范围外。** `isabelle-packaging-ci` 的改造细节（另一份计划）；Isabelle 源码仓库与五个脚本的设计（迁移方案）；各 feature 项目自己的清单与
计划；Isabelle2024。

## 2. 现状（2026-10-22/24 核实；前三版的错误已订正）

### 2.1 工具今天的样子

- 补丁在 Python 包内：`my_better_isabelle_prover/patches/<版本>/<feature>/*.patch`（`patches/__init__.py:8,106-121`）；`categories.toml` 把
  feature 分 user/dev（`:11,47-75`）。Isabelle2025-2 五个 feature 目录，Isabelle2024 三个。顺序靠可选的 `order.txt`（`:82-103`）。
- 状态只靠 GNU patch 的 `-R --dry-run` / `--dry-run`（`patcher.py:28-42`）；打前 `chmod u+w`、打后恢复（`:45-56,89-100`）；
  `apply_all` 正序打、逆序卸、逐文件、无回滚（`:108-128`）。目标路径只认 `--- a/` 头（`patches/__init__.py:124-130`）。
- 定位 Isabelle：`shutil.which("isabelle")` 或 `--isabelle-bin`，再跑 `isabelle version` 与 `isabelle getenv -b ISABELLE_HOME`
  （`isabelle.py:12-55`、`cli.py:18-45`）。没有测试目录；没有 `conda/` 目录。`pyproject.toml:6-7` 名 `my-better-isabelle-prover` 0.3.0，
  `:36-37` 只打包 Python 包本体（`tools/` 不在包里）。
- 本机有两处 editable 安装（0.1.x，base 环境与 `.venv`）；改名后它们会 `ModuleNotFoundError`（评审 C23 实测）。

### 2.2 谁在用它

- CI（`build.yml:204-256`）：`pip install my-better-isabelle-prover==0.3.0`（`:219`），shim 冒充 `isabelle`，`patch --category user --no-build`，
  然后 `hg commit`（`:292-300`，commit 在 `:297`）；`scripts/check_patch_sync.sh:50-52` 比对 PyPI 与本地。按第 11 条这一整段退役。
- light 迁移前的 `check_stock_diff.sh:18` 调它，已退役。Isabelle-MCP、Isa-Mini、Semantic_Embedding 的配方都不依赖它。Isa-Mini 的注释提到它
  （`conda/recipe.yaml:32,142,152`、`Agent/Injector/ROOT:8-24`：`expose_map_syn` 是 dev 类补丁，`Minilang_Agent_Injector` 在没打它的树上
  编不过），决定 14 要求改写。
- pip 用户：任何 `pip install my-better-isabelle-prover` 的人。他们继续用 0.3.0；新工具不发 PyPI（第 23 条），README 的 0.x 一节说明。

### 2.3 conda 侧的事实（本计划要适应的）

- `isabelle` 包：整棵树在 `$PREFIX/isa`，`$PREFIX/bin/isabelle` 是相对符号链接（`recipe.yaml:75-87,176-177`）；没有 `requirements`
  （`:235-237`）；build string 只是 build 号（`:30-43`）；pkgs 缓存只有 linux-64 的 `isabelle-2025.2-0`。`etc/ISABELLE_ID` 今天是 CI 那次
  `hg commit` 的 changeset（`:20`，`pack.sh:386-391`）：`2025.2-0` 是 `5533cd83156e`，树里带 `expose_foreign`。本机 pkgs 缓存里另有一个
  `isabelle-2025.2-89701cf1768e_0`：树在 `opt/Isabelle2025-2/`（没有 `isa/`），`ISABELLE_ID` 是**官方** changeset `89701cf1768e`，却也带
  `expose_foreign`（`ml_name_space.ML:67` 是 `["Signal"]`），只来自本地文件渠道、没装在任何环境里——它说明 **`ISABELLE_ID` 等于官方
  changeset 不能证明树是原版**；决定 12 第 1 点要求 CI 用断言保证，决定 17 的 (b2) 能抓到预先打好的 feature。
- `scripts/pack.sh` 的打包改动（第 20 条，保留）：Windows 加 `bin/isabelle.bat`（`:159-165`）；`etc/settings` 把 `ISABELLE_HOME_USER` 改成
  `~/.isabelle/<R>-conda-$(basename <prefix>)`（`:184-189`）；`etc/options` 把 `ML_system_64` 默认改成 true，与包内 64 位 heap 配套
  （`:206-211`，`:200-204` 说明两者必须同步）；`etc/components` 删 nunchaku 行（`:226-231`）；另有 `obj/` 清理（`:122-139`）、`.conda-keep`
  标记（`:284-324`）；包里没有官方 tarball 的 `lib/browser_info.db`、`src/Tools/Find_Facts/lib/isabelle.db`（评审核实），也没有
  `contrib/polyml-5.9.2-2/*/libpoly{ml,main}.la` 四个文件（rattler-build 0.69.1 丢掉 `*.la`，评审四实测）。包内自带 Pure/HOL/Main
  的 heap（`recipe.yaml:3-4,246-247`）。缓存里 `isa/src` 的文件权限是 3522 个 0644、26 个 0755，**没有 0444**（评审 C19）。
- **用户目录共用**（第 31 条要修的）：后缀是 prefix 路径的最后一段，`-p ~/a/env` 与 `-p ~/b/env` 共用 `~/.isabelle/Isabelle2025-2-conda-env`：
  heap 与组件登记共用，今天就会 "Duplicate session"（`sessions.scala:869-872`）；有 feature 包后一个环境会静默加载另一个环境用打过补丁的源码
  编的 heap（`isabelle process` 不核对源码，`store.scala:357-360`）；任一环境重装 `isabelle` 都删掉对方的状态。这个问题早于本计划。
- **`isabelle` 包的 pre-unlink 删整个用户目录**（`recipe.yaml:223-231`：`getenv -b ISABELLE_HOME_USER`、`rm -rf`；Windows `:154-160` 先调
  `isabelle.bat version`），用户目录里有 `etc/components`——所有组件登记随之消失。重链接 `isabelle`（`--force-reinstall`、升构建）时只有
  `isabelle` 自己的钩子跑，组件包的 post-link 不跑（下一点），登记不会回来。第 26 条由新构建的 post-link 重跑它们修复。Windows 上
  `isabelle.bat` 的 cygwin 初始化会往 `isa/` 写未跟踪文件，conda 只删跟踪的路径，所以 `conda remove isabelle` 后 `isa/contrib/cygwin/` 下有残留
  （评审 C21 实测；`recipe.yaml:106` 的"no untracked files"不对）。
- **钩子的执行与失败语义（conda 25.11.1，评审实测）**：conda 先链接事务里的全部包，再依次跑 post-link（`core/link.py:938-967`）；一个
  post-link 失败后其余的照跑，最后回滚（`:1006-1007,1038-1045`）；**回滚只撤文件链接、不跑任何脚本**（`:1129-1160`，入口 `:1042`），所以前面的
  post-link 已经写进 `isa/` 的改动留在树里、而包没了；回滚还删 `conda-meta/history`（`core/path_actions.py:1075-1080`），之后 conda 不再认
  这个目录是环境。**Ctrl-C** 走同一条回滚路（`link.py:916`，`conda/__init__.py:153-163`）：整个事务撤销、history 被删、钩子里 `exit 0` 也无济于事。
  回滚把工具一起撤掉时，`status` 也没了，只有 README 还在说明怎么恢复；恢复之前每条 `isabelle` 命令都可能打印
  `### Missing Isabelle component`（`lib/scripts/getfunctions:262`，组件登记指向已不存在的目录）。
  pre-unlink 非零只记警告，包照样卸（`link.py:1676-1683`）。钩子的 stdin/stdout/stderr 都是管道（`gateways/subprocess.py:83-117`）；
  **conda 在每个脚本跑完后立刻打印并删掉 `$PREFIX/.messages.txt`**（`link.py:1685,1697-1708`），所以钩子之间不能通过它传递任何信息。
  钩子的工作目录是 `$PREFIX/bin`（`link.py:1644-1646`）；每个脚本都拿到 `PREFIX`、`PKG_NAME`、`PKG_VERSION`、`PKG_BUILDNUM`（`:1630-1634`）。
  post-link 在激活的环境里跑，pre-unlink 只把 `$PREFIX/bin`（Windows `Scripts`）加到 PATH 前面（`:1109-1114,1635`）。conda 在跑 post-link
  之前就建好入口点（`:956-959`；Windows 是 `Scripts\<命令>.exe`，`path_actions.py:811-838`）。`conda-meta/history` 与包记录在 post-link
  之后才写（`:969-999`）。**被卸载的文件在 post-link 期间还在**：conda 先把它们改名成 `<路径>.c~`（`path_actions.py:1152-1164`，
  `constants.py:180`），所有 post-link 跑完才删（`link.py:1057-1060`），所以 post-link 看到的 feature 目录里可能有 `*.patch.c~`、
  `provenance.txt.c~`。
- **哪些包跑钩子**：只有本次事务里换了的包（`core/solve.py:1417-1418` 的 `unlink_precs`/`link_precs`）。所以 `--force-reinstall isabelle` 只跑
  `isabelle` 自己的钩子；`conda update --all` 升到新 `isabelle` 构建时按第 22 条连带换掉并跑全部 feature 包的钩子，但不跑组件包的（它们钉的是
  版本范围，评审四 C23 实测）；`conda create --clone` 先把未跟踪的文件复制过去、再链接包并跑
  **每个**包的 post-link（`misc.py:274-357`）。卸载顺序 `solve.py:1450-1452`，链接顺序 `:1453`（依赖拓扑序）。libmamba 的 `conda remove X` 会把
  只作为依赖、不在 history 里的包一并卸掉（`conda_libmamba_solver/solver.py:558-582`）；`conda remove --force X` 只卸 X；再 `conda install` 一个
  已装的包不会把它记成显式要求的，`--force-reinstall` 会。
- 精确钉死 `isabelle` 构建的 solver 行为（第 22 条，§8）：在旧构建上装 feature 自动升 `isabelle`；新构建未配套重发 feature 时 `update` 原地不动、
  显式装报冲突；配套重发后 `conda update --all` 一起升，libmamba 下单独 `conda update isabelle` 不动。
- 硬链接：conda 把 pkgs 缓存里的文件硬链接进环境，同机的两个环境也共享 inode（评审 C19：inode 55605093）。`os.replace` 换进新文件后，环境里的
  路径指向新 inode，其他路径的内容与权限位不变。反过来，**经硬链接原地写入的编辑**（vim 的 `backupcopy=auto` 就这样）会把包缓存里那份一起改掉，
  之后 `--force-reinstall isabelle` 恢复不了它（大小不变时静默，变了只有 SafetyError 警告、rc 0；评审 C27 实测）。
- 已发布组件包的钩子（`RELEASE_CHECKLIST.md` §4，`contrib/Isabelle_RPC/conda/recipe.yaml:148-179`）：`.sh` 与 `.bat` 各一份无条件写出，
  `isabelle components -u/-x "$PREFIX/share/<包名>"`，Windows 先 `isabelle.bat getenv -b ISABELLE_HOME` 热身、路径转 `/cygdrive/`，一律
  `exit 0`/`exit /b 0`。它们失败时的 `echo` 走 stdout、被 conda 丢掉，`.bat` 则不出声——**不经 `.messages.txt`**。`RELEASE_CHECKLIST.md:259`
  只要求 exit 0，整份清单没提 `.messages.txt`；经 `.messages.txt` 说话是**本计划自己的做法**（决定 9）。渠道的组件包测试清单在
  `RELEASE_CHECKLIST.md:630-642`。
- **`isabelle-semantic-data`**（第 34 条的由来）：9.6 GB 的语义数据库包，`isabelle-ai` 拉进来，依赖 `isabelle-semantic-embedding >=0.3.0`，后者依赖
  `isabelle >=2025.2,<2025.3`（`Semantic_Embedding/conda/recipe.yaml:318`；数据包的配方在 CI 仓库 `conda/data/isabelle-semantic-data/recipe.yaml:16-23,80-96`）。
  它的 post-link 只有一行 `"$PREFIX/bin/isabelle-semantics" post-install-system-db; exit 0`；这个命令的设计前提是"恰在数据载荷换了的时候触发"
  （`Isabelle_Semantic_Embedding/isabelle_semantics.py:1033-1034`），它删掉用户层里没有用户记录的向量（`semantics.py:1567-1607`），那些是用户本机
  从旧系统文本算出来的替身向量，删了要重新花钱嵌入。所以它的 post-link **不能**在载荷没变时重跑——这是第 26 条"含间接依赖"被第 34 条收窄的原因。
  其余已发布的依赖者（`isabelle-rpc`、`isabelle-nunchaku`、`isabelle-performant-ml`、`auto-sledgehammer`、`minilang`、`isabelle-semantic-embedding`）
  的 post-link 都只是 `components -u`，重跑无效果。
- **`isabelle` 包依赖 python 的后果**（第 26 条）：线上渠道没有 python 和 git；CI 自己的 `build.yml:1012,1203,1217,1286` 和 `release.yml:115`
  都是 `--override-channels` 只带本地或线上渠道装 `isabelle`，加了 python 依赖后这些安装解不出来（显式钉构建时报 "nothing provides python"；
  不钉时会退回线上的 `2025.2-0`）；Performant_Isabelle_ML（`release-conda.yml:423-425,527-529`）与 auto_sledgehammer（`:195-197,273-274`）
  的 release workflow 同形。决定 12 第 10 点列出要改的地方。
- 其他前端：micromamba 2.8.1 跑 post-link、不跑 pre-unlink；mamba 2.x 同类；pixi 的 rattler 默认不跑 link 脚本（评审实测/核查）。只支持 conda
  （第 17 条）。
- conda-forge 的 `git`：linux-64 11.9 MB、linux-aarch64 16.5 MB、osx-64/osx-arm64 13.5 MB、win-64 120.8 MB（整包是 Git for Windows 的
  PortableGit，自带 MSYS2 运行时，不依赖 `m2-*` 包；feedstock `meta.yaml:20-27,76-77`；`bld.bat` 原样解到 `Library\`，conda-forge 自己测
  `%LIBRARY_PREFIX%\bin\git.exe`）。PortableGit 带 Git for Windows 的系统配置 `core.autocrlf=true`。今天解析到 2.56。GitHub 的 Windows runner
  上 `actions/checkout` 也默认 `core.autocrlf=true`。
- 渠道的发布：`isabelle-packaging-ci/.github/workflows/publish-conda.yml` 是可复用 workflow，对产物里**全部** `.conda` 查重（`:148-191`，
  已发布且字节不同就整批拒绝，字节相同视为续传）、全部上传（`:193-203`）、拉整个渠道重建索引、推回；`package_name` 输入只给 job 起名（`:54-57`）。
  调用方必须显式传两个 R2 密钥（`:8-26`；未设密钥的仓库在解析期就报错，`RELEASE_CHECKLIST.md:299-301`）。发包仓库登记在
  `scripts/sweep-old-versions.py:61-69` 的 `PUBLISH_REPOS`（`RELEASE_CHECKLIST.md:172`），**只有清扫脚本**用它查其他仓库有没有正在跑的发布
  （`:211-237`）；发布 workflow 之间互不检查。发布失败后用"重跑失败的 job"续，不能重新 dispatch（重建的 `.conda` 带时间戳、字节不同、门禁拒绝；
  `RELEASE_CHECKLIST.md:564-567`）。可复用 workflow 必须直接放在 `.github/workflows/` 下才能被调用；它的 job 不能要求调用方没有的权限
  （`publish-conda.yml:69-74`）。**`publish-conda.yml` 现在是坏的**：10-09 的 commit 85dc11b 加的 banner 步骤（`:223-227`）在没有 checkout 的
  job 里调 `scripts/banner-index.py`，再 `grep` 一个 `channel-banner.html` 和脚本里都没有的字串；此后没有任何发布跑过（最后一次成功发布是
  10-09 早上的 `release-isabelle-ai`，在该 commit 之前）。按现在的文本，下一次发布会在 `.conda` 上传之后、索引推送之前失败（决定 12 第 5 点）。
- `isabelle-packaging-ci` 自己的构建：`build.yml` Job F 在 linux-64 构建全部五个平台的包并上传一个 `conda-packages` artifact（`:1108-1114`，
  保留 7 天），Job G（`macos-14`：osx-arm64 原生、osx-64 经 Rosetta）和 Job H（`ubuntu-24.04-arm`）下载**同一份** artifact 安装运行
  （`:1116-1130`："what is installed here is the EXACT byte-for-byte package that would be published"）；heap job 的超时见 `:498,:583,:677`。
  `ci.yml` 调 `build.yml` 时不传 build 号（`:19-23`）。

### 2.4 `git` 的实测（§8）

在**普通目录、作者自己的 git 配置**下对 light 的 32 个文件的 git 格式 diff：`--check` 在基上通过、`-R --check` 在基上失败；正打后树哈希等于
light 的树；此后 `--check` 失败、`-R --check` 通过；`-R` 反打后树哈希等于基。玩具：新建可执行文件（可执行位对）、删除、末尾无换行（保持）、
反打时删掉它建的文件；一个文件对不上时整次调用什么都不写；非贴着文件头尾的 hunk 允许偏移（和 GNU patch `-F0` 一样）；新增行的行尾空白只有
warning（`--whitespace=nowarn` 关掉）。

第二、三轮评审补测，作者复现其中两项（§8）：
- `git` 会向上找仓库。工作目录在某个 git 工作树之下时（`conda create -p <仓库>/env`、被 git 管着的 home、`TMPDIR` 在仓库里、conda 跑钩子时的
  `$PREFIX/bin`），`git apply` 对每个文件打印"跳过补丁"、`--check`/`-R --check`/`apply` 全部返回 0、树不变；**`git apply --numstat --summary`
  同样什么都不打印、返回 0**，于是每个 feature 都读成 applied（评审 C2，judge 复现）。设 `GIT_CEILING_DIRECTORIES=<工作目录的父目录>` 后正确。
- `git apply` 在仓库外也读系统与全局配置、attributes：`core.autocrlf=true` 时写出 CRLF，反打后字节与原版不同；`GIT_DIR` 指向一个目录时读
  `$GIT_DIR/config`，所以 `GIT_DIR=/nonexistent` 不是隔离办法。**patch 文件本身被转成 CRLF 时**（Windows 上 checkout 的默认行为）：改文件的
  补丁 `--numstat --summary` 照常列出目标、重放 rc 1、读成 CONFLICT；**新建文件的补丁却以 rc 0 应用、写出带 CR 的文件**（评审四 C19 实测），
  所以决定 3 按头部行末尾的 CR 拒绝这种文件。
- 性能（真链、Linux）：一次 `status` 启动 `git` 126–128 次，耗时 0.16–0.25 秒（评审三）、0.17–0.32 秒（评审三 C22）、0.17–0.19 秒
  （评审四 engine）、负载下 0.32–0.43 秒（评审四 C24）；rev 3 §8 写的 1.3–2.3 秒是第二轮原型每步 `--check` 加 `apply` 的数字。Windows 上
  `Library\bin\git.exe` 是转接器、再起 `ucrt64\bin\git.exe`，不加载 `msys-2.0.dll`，每次调用是两个原生进程；Windows 的耗时在决定 15 实测后写进 §8。
- 多文件 diff 的写入不原子：先 `unlink` 全部旧文件，再逐个 `O_CREAT|O_EXCL` 创建（strace）。分开传多个 patch 文件时逐个应用，中途失败半打。
- 退出码：不匹配是 1；patch 文件解析不了是 128；**写模式下 128 也可能是写失败**（磁盘满、目录只读、EFBIG 都给 128；RLIMIT_FSIZE 给信号码
  −25 并留下截断的文件；评审 C17 实测）——所以只有在"工具自己建的副本上重放"这个前提下，1 才能可靠地解读为"不匹配"，其他值一律当写失败。
对照测过的 Python 库都不够：`patch-ng` 反打不删新建文件、不认末尾无换行、不原子；`whatthepatch` 只做文本层；`pygit2`（libgit2）正打对、但没有
反向应用，且要借一个 bare 仓库。

### 2.5 迁移方案已落地的、与本工具相接的东西

`tools/make-patches` 生成 `patches/<R>/<path 的 / 换成 ->.patch`（`git diff-tree -r -p --no-renames` 的原样块：`diff --git`、可选的
`new file mode`/`deleted file mode`、`index`、`---`/`+++`、hunk）和 `patches/<R>/provenance.txt`；拒绝 `old mode`/`new mode`、
`similarity index`、`GIT binary patch`（`make-patches:167-168`）——改名因 `--no-renames` 表现为删除加新建，二进制块今天被 (c) 门禁的 `patch` 拦住、
决定 16 后被头部检查拦住。门禁 (c) 今天用裸 `patch -p1 -F0`（`:63-69,179-183`）。**它只在 Isabelle 仓库打发布 tag**（`:209-211`），不碰 feature
仓库（light 仓库今天没有任何 tag）。`new-tree`、`run-tree`、`check-signatures`、`advance-daily`、hook，玩具测试 `tools/tests/run-all.sh`。
README 已有 "Working in the Isabelle source repository" 一节。都未提交（§5 第 0 步）。

## 3. 决定

### 决定 1：名字与发布形态

- Python 包 `isabelle_patch_control`，命令 `isabelle-patch-control`，conda 包名 `isabelle-patch-control`（noarch python，`run: [python >=3.12,
  git >=2.43]`，配方在工具仓库 `conda/recipe.yaml`，由批量发布 workflow 构建），版本从 **1.0.0** 起。**只发 conda**（第 23 条）。
  `pyproject.toml` 的 `[project].name = "isabelle-patch-control"`（第 32 条）：不发布，只供 recipe 的 `pip install . --no-deps` 与 editable
  安装用；与旧名不同，所以 0.x 一节教的 `pip uninstall my-better-isabelle-prover` 永远只碰 0.x。
- 本地目录仍是 `contrib/my_better_isabelle_prover`（先例：`contrib/Semantic_Embedding` 的目录名与包名也不同）。GitHub 仓库改名
  `isabelle_patch_control`，**在任何 workflow、任何 `PUBLISH_REPOS` 条目存在之前**做，同一步改主仓库 `.gitmodules:41` 的 url。
  改名的自动跳转只对 `git` 远程有效，对 `uses:` 引用的 workflow 无效，所以顺序不能反。
- 1.0.0 不带任何补丁：`patches/` 整个目录、`categories.toml`、`order.txt` 机制、user/dev 分类全部删除（Isabelle2024 按第 15 条留在旧工具里，
  不搬）。旧 PyPI 包 `my-better-isabelle-prover` 停在 0.3.0，不下架。
- 子命令：`status`、`apply`、`unapply`、`apply-to`、`unapply-from`、`conda-hook`、`help`；删除 `patch`、`unpatch`、`build`、
  `--category`、`--force`。`conda-hook` 读环境变量 `PREFIX` 和 `PKG_NAME`（决定 9）。
- **1.x 冻结的接口**（钩子文本一旦随 feature 包发布就改不了）：`conda-hook post-link`（无参数）与 `conda-hook pre-unlink <feature>` 两条命令行、
  钩子里的调用方式 `"$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control …`、树在 `$PREFIX/isa`、钩子里 exit 0、经 `$PREFIX/.messages.txt`
  报告。每个 1.x 版本都必须继续接受它们（已发布的 feature 包里冻着这些文本）。`isabelle` 包自己**不调工具**（第 33 条），不受这条约束。
- `package_name(feature)`（决定 10）放在 Python 包里（`isabelle_patch_control/names.py`），`tools/common.py` 从它导入：`pyproject.toml:36-37`
  只打包 Python 包，工具运行时也要用它。

### 决定 2：定位树与 feature 目录

- 一个前缀 `P` 推出两样东西。`P` 的来源按优先级：`conda-hook` 子命令里是环境变量 `$PREFIX`；否则显式 `--isabelle-home DIR` 的父目录；
  否则 `sys.prefix`。树 = 显式 `--isabelle-home`，否则 `P/isa`。默认 feature 目录根 = `P/share/isabelle_patch_control/features.d`，**只在
  `P/conda-meta` 是目录时使用**（判据是这个目录而不是 `conda-meta/history`：history 与包记录在 post-link 之后才写，§2.3）；它不存在是正常的
  "没装任何 feature 包"——`status` 打印 `no feature packages installed`、退出 0（第 29 条），`apply`/`unapply` 无事可做。`P/conda-meta` 不是
  目录又没给 `--features-dir` 是 exit 3（第 19 条：不支持自装的 Isabelle），报文让用户传 `--features-dir`。显式 `--features-dir DIR` 必须存在，
  否则 exit 3。树和 feature 目录于是不可能来自两个环境。
- **工具只读每个 feature 目录里的 `provenance.txt` 和 `*.patch`**，别的文件（conda 卸载过程中的 `*.c~`、编辑器残片）一概不看；没有
  `provenance.txt` 的子目录视为不存在（不是错误）。
- 工具**永不运行 `isabelle`**，不用 `shutil.which`，不读环境变量 `ISABELLE_HOME`、`CONDA_PREFIX`：发行版名从 `树/etc/ISABELLE_IDENTIFIER` 读
  （conda 树是 `Isabelle2025-2`），构建身份从 `树/etc/ISABELLE_ID` 读。
- 每个命令开始时的拒绝（exit 3）：`树/.git` 存在（目录或文件）——工具不碰 git 管着的树，共享树与私有树都算；某个 patch 文件的目标是符号链接
  （`realpath(树/p) != realpath(树)/p`，在读 feature 目录时检查、重放之前）——报文点名 conda 的 `always_softlink`/`allow_softlinks` 设置；
  目标存在但不是普通文件（`os.lstat` 非 `S_ISREG`：目录、FIFO 等，同一遍检查）——发布门禁 (c) 经 `apply_to`/`unapply_from` 往返，所以
  "文件变目录"这类补丁在发布时就被拦住，正确打好的树上这条拒绝永不触发；`--feature` 给的名字不在 feature 目录里。
- `status` 的第一行永远打印它读的树和 feature 目录根；`apply`、`unapply` 在 `-v` 下打印。

### 决定 3：来历文件与按精确 tag 的链

- 来历文件 `provenance.txt` 的字段就是 `make-patches` 今天写的：`feature`（`<R>/<feature>`）、`release_tag`、`commit`、`base_tag`、
  `base_commit`、`base_package_version`、`base_pin`、`build_string_prefix`、`tree_hash`、`tree_hash_excludes`。工具读 `feature`、
  `release_tag`、`base_tag`，其余给渲染器与人看。
- **链按精确 tag 链接**，不按名字：
  1. 链底永远是 `<R>/pristine/<ISABELLE_ID>`，`<R>` 来自 `etc/ISABELLE_IDENTIFIER`、`<ISABELLE_ID>` 来自 `etc/ISABELLE_ID`。
  2. 从链底开始，每一级恰好一个 feature 目录的 `base_tag` 等于当前的 tag，它的 `release_tag` 成为下一级；两个目录的 `base_tag` 相同、或某个
     目录的 `base_tag` 谁都不等于，都是 exit 3，报文点名是哪一个目录、它要的 tag、链上实际有的 tag。**"树不是原版构建"的判据**：某个目录的
     `base_tag` 是 `<R>/pristine/<X>` 而 `X` 不等于树的 `ISABELLE_ID`——这时报文另加一句：这棵树的 `isabelle` 构建装不了 feature 包，
     `conda update --all -c https://conda.qiyuan.me -c conda-forge`（§4）。工具不内置官方 changeset 表（第 29 条）。`feature` 字段的 `<R>`
     必须等于树的发行版名。链接不上的报文经 `names.package_name` 把 feature 名换成包名、说"安装匹配的版本"（§4）。
  3. 没装任何 feature 包时链只有链底，`status` 打印 `no feature packages installed`、exit 0，不论树是哪个构建（第 29 条）。
- 工具不读 `order.txt`、不读 `categories.toml`、没有 `after`。
- 每个 patch 文件改哪个路径，用决定 4 的原语在一个临时目录里跑 `git apply --numstat --summary <patch 文件>` 读出（新建/删除/权限在 `--summary`
  里），不自己解析头部。**每个 patch 文件必须恰好一个目标**，零个或多个 exit 3 并点名文件；同一 feature 目录里两个 patch 文件目标相同 exit 3；
  patch 文件第一行（`diff --git` 头）以 CR 结尾 exit 3（被 CRLF 转换过的文件，§2.4；内容行里的 CR 是合法的，autocrlf 不会碰这种文件）；
  没有任何 `*.patch` 的 feature 目录 exit 3；这一步的任何非零退出码都是"patch 文件解析不了"，exit 3 并点名文件。目标等于
  `isabelle_patch_control.engine.LOCK_FILE`（`etc/ISABELLE_ID`）的 feature 一律 exit 3（决定 5 锁的是这个文件；决定 16 在发布时就拒绝）。

### 决定 4：引擎——启动 `git` 的唯一原语

- Python 包里只有**一个私有函数**能启动 `git`，叫它 `_git(workdir, args)`：它构造子进程环境、固定参数、在 `workdir` 运行、返回退出码与输出。
  `workdir` 永远是工具自己建的目录——暂存目录或临时目录（决定 5）——从不是树、也从不是调用方的当前目录。重放（`git apply [-R] --whitespace=nowarn
  <一个 patch 文件>`）、读目标（`git apply --numstat --summary`）、探版本（`git --version`）都是它的薄封装。
- 子进程的环境**从白名单构造**，不继承调用方的：只带 `PATH`（Windows 另加 `SystemRoot`、`TEMP`、`TMP`），再加 `GIT_CONFIG_NOSYSTEM=1`、
  `GIT_CONFIG_GLOBAL=<os.devnull>`、`GIT_ATTR_NOSYSTEM=1`、`LC_ALL=C`、`GIT_CEILING_DIRECTORIES=<workdir 的父目录（已 realpath）>`。命令行
  固定前缀 `git -c core.autocrlf=false -c core.attributesFile=<os.devnull>`。于是任何现在或将来的 `GIT_*` 变量、XDG 路径、系统/全局配置、
  attributes 文件都进不来，工作目录之上的仓库也找不到（§2.4）。POSIX 上子进程 umask 022。`HOME` 不需要（实测无 `HOME` 也能正确往返）。
  Windows 另试 `-c core.longpaths=true`，在 Windows 腿上核。
- 不传 `--directory`、不传 `--unsafe-paths`。没有 `--check`：层级计算（决定 6）是在副本上真的打，不需要预检。
- 退出码的解读按阶段：读目标那一步非零 = patch 文件解析不了（exit 3，决定 3）；重放时 1 = 这个补丁对这份副本不匹配（喂给层级计算）；重放时
  其他任何值（含负的信号码）= `git` 没能在副本上完成写入（磁盘满、只读、超限）——**不装任何东西**，原样打印 `git` 的输出、副本路径、正在重放的
  patch 文件，**不说补丁文件坏了**，exit 1。这个解读之所以成立，是因为每份副本都是工具自己在自己的目录里建的。
- `git` 的位置：先 `sys.prefix/bin/git`（Windows `sys.prefix/Library/bin/git.exe`，pre-unlink 时 PATH 不完整，§2.3），再 PATH；
  要求 `git --version` ≥ 2.43，否则 exit 2。
- 工具不 `chmod` 树里的文件、不在树里运行 `git`；树里的每一次改动都是决定 5 的 `os.replace`/`os.unlink`。

### 决定 5：写树——暂存目录与原子改名（第 24 条）

- **唯一写树的路径**：先按决定 6 对每个文件在工具自己的目录里重放一次、算出层级并得到"移到目标层级后的样子"（决定 7），然后对每个要动的
  文件 `p`：(1) 设权限位——被改的文件沿用 `树/p` 原来的权限位，新建的文件按 patch 头部的 `100644`/`100755`；(2) `os.replace(重放结果, 树/p)`
  （需要时先建父目录），或者结果是"文件不存在"时 `os.unlink(树/p)` 并删掉变空的父目录。**一次一个文件；重放只做一次**，装进树的就是重放时
  算出的那份快照（rev 3 先算层级再重放一遍、多出 42 次 `git` 调用，删掉）。
- 在哪里重放**由锁的模式决定**，不由命令名决定：**只有持排他锁的那次运行**用暂存目录 `<realpath(树)>.staging`（`$PREFIX/isa.staging`）——与树
  同一文件系统（`os.replace` 才是原子的；树是符号链接时取 realpath，否则 EXDEV），**不在树里**（残留不会让 `isa/` 留下来），持锁后先清空、
  结束时删掉（`finally` 里也删）。其他一切 `git` 调用都在新建的临时目录（`tempfile.mkdtemp()`）里：读目标、`status`、任何 `--dry-run`、
  锁超时后 pre-unlink 的层级计算，前缀下不写任何东西。目录接口（决定 8）在 `realpath(<目录>)` 旁边的一个 per-run `mkdtemp` 里重放、不加锁
  ——这是"工具对树加锁"的一处有意例外，因为目录接口的调用方（门禁、(b2)）自己拥有那个目录。于是"只有锁的持有者碰暂存目录"由构造保证，
  超时后不持锁算层级的 pre-unlink 不会碰到持锁者正在用的暂存目录（评审四 C18 实测）。
- 保证：每个文件任何时刻要么整个是旧的、要么整个是新的；工具的一条命令被中断（Ctrl-C 直接发给工具、被杀、磁盘满）后树是"部分文件已到目标
  层级"的状态，下一次 `apply` 或 `unapply` 重算层级后接着做完（决定 7 的逐文件移动天然收敛；评审 C2 的原型在 32 个杀进程位置全部收敛）。
  **这条保证只对工具自己的命令成立**：`conda install` 被 Ctrl-C 中断时，conda 回滚整个事务、可能把工具一起卸掉、删 `conda-meta/history`，而
  post-link 已写进树的改动留着（§2.3）；恢复步骤见 §4（评审 C11 实测收敛）。写失败只会发生在工具自己的目录里（exit 1，树不变）；`os.replace`
  本身失败时重算并打印 `status`。Windows 上 `os.replace`/`os.unlink` 对"被占用"做有限重试（约 7 次、共约 6 秒，和 conda 一样）。
- 锁：对 `树/etc/ISABELLE_ID` 这个**已有**文件加锁，不新建任何文件；路径常量 `isabelle_patch_control.engine.LOCK_FILE`，决定 3 的运行时拒绝和
  决定 16 的发布门禁都用它。POSIX `fcntl.flock`（不是 `lockf`）：`status` 与任何带 `--dry-run` 的命令只读打开、`LOCK_SH`（所以
  `apply --dry-run` 在只读树上也能跑）；不带 `--dry-run` 的 `apply`、`unapply` 与 `conda-hook` 读写打开、`LOCK_EX`（NFS 要可写描述符）。Windows `msvcrt.locking` 锁**固定偏移 `0x40000000` 处的 1 字节**（先 seek 再锁；`flock` 不看偏移）：这个
  偏移任何读到文件末尾的程序都碰不到（rev 3 锁"末尾之后 1 字节"是错的——`cat` 和 Python 的读都会碰到它，`isabelle version -i` 用 `cat`），
  在 Windows 腿上核。不锁目录（NFS 上排他锁坏、Windows 锁不了目录句柄）。等待上限 60 秒，超时 exit 1 报忙；`conda-hook post-link` 把忙和重试
  命令写进 `.messages.txt`、exit 0，`conda-hook pre-unlink` 的处理见决定 9。这个文件的 inode 经包缓存与同机其他环境共享，所以锁也跨环境串行
  ——接受（Linux 上一次运行持锁 0.17–0.43 秒，§2.4；Windows 的数字由决定 15 实测后写进 §8，§6 要求它远低于 60 秒的等待上限），忙的报文点名
  被锁的文件并说明可能是别的环境在用。
- `status`、`--dry-run`、`apply`、`unapply`、`apply-to`、`unapply-from` 共用这一条路径：先重放，`status`/`--dry-run` 到此为止，其余接着装。
  所以 `status` 预测的字节就是会装进去的字节，权限位对每个调用者相同。

### 决定 6：状态模型——每个文件的层级

- 链底以上的 feature 按链序编号 1…n。文件 `p` 被其中编号为 `t1 < … < tm` 的 feature 改过（决定 3 末点读出）。`p` **处于层级 L**
  （L ∈ {0, t1, …, tm}）的定义：在 `p` 的一份副本上，把编号 ≤ L 的那些补丁按编号**降序**逐个 `git apply -R`——每成功一个就真的反打到副本上
  再做下一个——全部成功；且在另一份副本上，把编号 > L 的那些补丁按编号**升序**逐个 `git apply`——同样每成功一个就真的打到副本上——全部成功。
  两半都是顺序重放。副本放在暂存目录或临时目录里、保持 `p` 的相对路径。不存在的 `p` 也是一种内容。（rev 3 用 feature 编号去索引"改过 `p` 的
  feature 列表"，两种编号混用，评审 C18 查出；本版层级只用 feature 编号。）
- **同时处于几个层级的文件一律 CONFLICT**（第 28 条），`status`、`apply`、`unapply` 都如此；`status -v` 列出它匹配的层级。这条保证靠决定 16
  第 5 点的发布门禁撑着：它用工具自己的层级函数核过"链上每种状态下每个被改文件恰好一个层级"，所以正常发布的链上不会出现这种文件；出现就是
  有人改了树（只比 blob 相同的弱门禁拦不住上下文歧义的情形，评审四 C5 造出了反例）。没有任何层级匹配的文件同样是 CONFLICT。
- rev 2 "新建文件存在且内容相同就与两态都相容"的特殊规则**删除**：一个 feature 新建、内容恰好等于补丁内容的文件就处于该 feature 的层级，
  不存在就处于其下一级，内容不同就无层级。换 `isabelle` 包后留下的新建文件因此只是"一个已经在它的创建者层级上的文件"：`apply` 不碰它，
  `unapply` 删掉它。
- feature `F`（编号 k）的**显示**状态：它改的文件层级都 ≥ k → `applied`；都 < k → `not-applied`；有的 ≥ 有的 < → `half-applied`；任一文件
  CONFLICT → `CONFLICT`。某个 `applied` 的 feature 下面有 `not-applied` 的，`status` 在那一行后面标 `(hole below)`。这些词**只是显示**，
  `apply`/`unapply` 不读它们，只按文件层级移动（决定 7）。
- `status` 的输出（第 17 条授权定稿）：
  ```
  tree /home/u/miniconda3/envs/e/isa   features.d /home/u/miniconda3/envs/e/share/isabelle_patch_control/features.d
  applied      expose_foreign           Isabelle2025-2/expose_foreign/1           1 file
  applied      future_assign_interrupt  Isabelle2025-2/future_assign_interrupt/1  1 file
  half-applied light_locale             Isabelle2025-2/light_locale/1             32 files, 3 below
  not-applied  local_type_abbrev        Isabelle2025-2/local_type_abbrev/1        4 files
  CONFLICT     localized_record         Isabelle2025-2/localized_record/1         src/Pure/Isar/locale.ML
  ```
  `-v` 列出每个文件与它的层级（新建文件显示 `+++ b/` 那边的路径；多层级的列出全部）。退出码：选中的 feature（默认全部）都 `applied`
  且没有 hole 为 0；有 `not-applied`、`half-applied`、`CONFLICT` 或 hole 为 1；链接不上（决定 3）或拒绝（决定 2）为 3；没装 feature 包为 0。

### 决定 7：`apply`、`unapply`、`--feature`、`--dry-run`——逐文件移到各自的目标层级

- 命令的目标 T：`apply` 是 n（给了 `--feature F` 则是 F 的编号），再**封顶**在"最低的含 CONFLICT 文件的 feature"之下（那个 feature 及其上面
  的全不碰）；`unapply` 是 0（给了 `--feature F` 则是 F 的编号减一，即反打 F 及其上面的全部）。
- **每个文件自己的目标层级** T_p = {0, t1, …, tm} 中 ≤ T 的最大者。层级已经等于 T_p 的文件不动；特别地，全打好的树上 `apply --dry-run`
  一个文件都不列（rev 3 的"层级 < T 就移"会让全打好的树上 32 个没被目标 feature 碰过的文件被白白重写、`--dry-run` 全列出来、heap 提示误发；
  评审三 C18 查出）。
- 封顶的一个后果要写给用户（决定 14 的 README）：重链接一个位于 CONFLICT 之下的 feature 包时，它的 pre-unlink 反打它和它之上的全部，它的
  post-link 再整链 apply 时被封顶在 CONFLICT 之下——于是 CONFLICT 之上的 feature 变成 not-applied，直到 CONFLICT 修好。
- `apply`：对每个层级 L < T_p 的文件，在副本上按升序正打编号在 (L, T_p] 内的补丁，装进树；L = T_p 的不碰；`apply` 只往上移。
- `unapply`：对每个层级 L > T_p 的文件，在副本上按降序反打编号在 (T_p, L] 内的补丁，装进树；L = T_p 的不碰；`unapply` 只往下移。
  CONFLICT 的文件移不了：**能移的都移，移不了的列出来**，exit 1。这取代 rev 1 评审 C3 的"下面还有 feature 就拒绝"规则，并让 pre-unlink 失败时
  留下的残留最少。
- `apply` 有 CONFLICT 时 exit 1，打印 CONFLICT 的文件和 `git apply` 的输出；否则 exit 0。
- `--dry-run`：同一次重放，跳过决定 5 的装入，打印将要移动的文件（从哪一层到哪一层），退出码与真跑相同。在全打好的树上 `apply --dry-run`
  一个文件都不列。
- 两者在真的改了 `src/` 下任何文件之后才打印 heap 提示（§4）。工具自己不构建任何东西。没有 `--force`。
- 中断后的状态：部分文件已在 T_p、其余还在原层级，`status` 把受影响的 feature 显示为 `half-applied`；再跑同一条命令就完成。

### 决定 8：目录接口与 Python API

- `apply-to <目录> <feature 目录>` 与 `unapply-from <目录> <feature 目录>`：把 `<目录>` 当树、`<feature 目录>` 当唯一的 feature，走决定 5
  同一条路径（在 `realpath(<目录>)` 旁的 per-run 临时目录里重放，不加锁），不读来历文件、不看 conda 环境；失败 exit 1 并原样打印输出。
- **公开的 Python API 就是命令行跑的那几个函数**：`isabelle_patch_control.api.status(tree, features_dir, ...)`、`apply(...)`、`unapply(...)`、
  `apply_to(dir, feature_dir)`、`unapply_from(dir, feature_dir)`，再加一个 `levels(tree, features_dir)`（返回每个文件匹配的层级集合，
  决定 16 第 5 点的门禁用它）——返回结果对象或抛异常，从不 `sys.exit`。`_git`、重放、装入都是私有的。
  `make-patches` 的门禁 (c) 调 `apply_to` 再 `unapply_from`（`sys.path.insert(0, TOOLS_DIR.parent)` 从 checkout 导入，不经 PATH、不需要安装，
  决定 16）；(b2) 脚本用命令行（决定 17）。rev 3 写的 `install_files` 不存在，删除。

### 决定 9：conda 钩子

- **钩子片段**，工具仓库 `isabelle_patch_control/hooks/post-link.sh` 与 `post-link.bat` 拥有，渲染器**逐字复制**进每个 feature 包的 post-link，
  没有 feature 参数；`isabelle` 包里**没有**它的副本（第 33 条）。片段到 `fi`（`.bat` 到 `:end`）为止，`exit 0`/`exit /b 0` 由钩子文件供给。
  `.sh`：
  ```sh
  if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then
    "$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook post-link \
      || echo "isabelle-patch-control: the hook could not run. Run: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
  elif [ -d "$PREFIX/share/isabelle_patch_control/features.d" ]; then
    echo "isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install -c https://conda.qiyuan.me -c conda-forge isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
  fi
  ```
  `.bat`（CRLF；没有带括号的块、每个 `%PREFIX%` 都在引号里、用 `goto` 标签。退出码用两行 `if` 判"等于 0"：`if errorlevel 1` 对负的
  NTSTATUS 退出码为假，评审四 C7 在 wine 下测过、与 cmd 文档的有符号比较一致）：
  ```bat
  @echo off
  if not exist "%PREFIX%\Scripts\isabelle-patch-control.exe" goto :notool
  "%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook post-link
  if not errorlevel 1 if errorlevel 0 goto :end
  echo isabelle-patch-control: the hook could not run. Run: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
  goto :end
  :notool
  if not exist "%PREFIX%\share\isabelle_patch_control\features.d\" goto :end
  echo isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install -c https://conda.qiyuan.me -c conda-forge isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
  :end
  ```
  每个钩子文件以 `exit 0`/`exit /b 0` 结尾（`.bat` 在 `:end` 之后、组件登记行之后）。exit 0 于是写在钩子文本里，工具没装、python 坏了、启动即崩
  都不会让 conda 回滚（§2.3）。用 `python -I -X utf8 -m` 而不是入口点脚本：`-I` 让调用方的 `PYTHONPATH` 遮不住工具，`-X utf8` 配 `-I` 是
  Windows 上必需的；存在性检查仍看入口点文件。工具的 conda 包依赖 python，所以 `$PREFIX/bin/python`（`%PREFIX%\python.exe`）一定在。
  用户要敲的每条 conda 命令都带 `-c https://conda.qiyuan.me -c conda-forge`（线上渠道没有 python 和 git，§2.3；`-n` 的环境级 `.condarc` 不生效，
  评审四 C17 实测）。
- feature 包的 pre-unlink。`.sh`：
  ```sh
  "$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature> \
    || echo "isabelle-patch-control: could not run the pre-unlink hook of <feature>; files under $PREFIX/isa may still carry its changes. If you are removing or replacing <feature>: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then install <包名> together with every other feature package this command removed; then remove them again" >> "$PREFIX/.messages.txt"
  exit 0
  ```
  `.bat`（CRLF）：
  ```bat
  @echo off
  "%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature>
  if not errorlevel 1 if errorlevel 0 goto :end
  echo isabelle-patch-control: could not run the pre-unlink hook of <feature>; files under "%PREFIX%\isa" may still carry its changes. If you are removing or replacing <feature>: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then install <包名> together with every other feature package this command removed; then remove them again>> "%PREFIX%\.messages.txt"
  :end
  exit /b 0
  ```
  带组件载荷的包的 `.bat` 把 `components -x` 的几行（照 `Isabelle_RPC/conda/recipe.yaml:168-174`，去掉它的 `@echo off`）放在 `:end` 与 `exit /b 0`
  之间。这两段 `||` 文本算不出"最高的 feature 包是谁"，所以让用户把本次命令卸掉的 feature 包一起装回再卸（决定 9 的残留块规则）。
- 带组件载荷的包（今天只有 light，第 21 条）：post-link 在钩子片段的 `fi`（`.bat` 的 `:end` 标签）之后、`exit 0` 之前加 `RELEASE_CHECKLIST.md`
  §4 的登记行（`"$PREFIX/isa/bin/isabelle" components -u "$PREFIX/share/<包名>" 2>/dev/null || echo "warning: …" >> "$PREFIX/.messages.txt"`；
  Windows 先 `getenv -b ISABELLE_HOME` 热身、路径转 `/cygdrive/`，照 `Isabelle_RPC/conda/recipe.yaml:165-176`）；pre-unlink 在工具行之后加
  `components -x`。先打补丁再登记组件，两步互不依赖。
- `conda-hook post-link`：对 `$PREFIX/isa` 做**整链幂等 `apply`**（决定 7，不带 `--feature`）。理由：conda 先链接全部包再跑 post-link
  （§2.3），所以本次事务里所有 feature 的目录都已在；整链 apply 让"重链接一个下层包"也把上层补回去。
- `conda-hook pre-unlink <F>`：`unapply --feature F`（反打 F 及其上面的），**只反打、永不打**。此时 features.d 还列着本次事务里所有要走的包
  （§2.3），所以不能做成"对齐 features.d"。
- **退出码一律 0**（第 12 条）。写 `.messages.txt` 的规矩（conda 每个脚本后就打印并删掉它，所以钩子之间不能互相看，§2.3）：
  - 每次钩子运行只报告**它自己这次改了什么**：打了/反打了哪些 feature（按 feature 列），`src/` 下有改动就附 heap 提示（§4）。什么都没改、链又
    正常的运行**一个字都不写**。于是一个事务里装三个 feature 包，只有第一个跑的 post-link 说话；卸载时每个 pre-unlink 自上而下各报自己反打的
    那一个。
  - 完整诊断（CONFLICT、链接不上、树不是原版构建）**只由链顶 feature 的钩子写**：`conda-hook` 用 `names.package_name` 的反函数把 `$PKG_NAME`
    换回 feature 名，等于链顶才写完整诊断；其他钩子见到同样的问题只写一行，点名 feature、文件和 `isabelle-patch-control status -v`；`PKG_NAME`
    没设或不认识时按链顶处理。第 26 条的重跑在每个换 `isabelle` 的事务里都会跑到链顶的钩子，所以**不变式**是：事务里只要换了 `isabelle` 或
    链顶 feature 包，就恰有一段完整诊断，否则只有一行提示（评审四 C3/C12 实测）。链还不存在时（例如第一个 feature 包就链接不上）每个钩子都会
    写一次诊断，接受。
  - pre-unlink 的残留块（§4）：凡它结束时**自己这个 feature** 的文件还有层级 ≥ k 的——不论原因是 CONFLICT、锁超时、`os.replace` 失败、工具
    起不来（后者由钩子文本的 `||` 分支兜住）——都写：文件清单（新建的标出，只列自己 feature 的）、"若你是在卸掉或替换它"这些改动在包卸掉后
    `status` 就看不见了、恢复步骤。恢复步骤点名的包是**此刻 features.d 里最高的那个 feature 包**：所有 pre-unlink 都在任何 unlink 之前跑
    （§2.3），所以同一条 conda 命令里每个残留块给出的命令相同，用户按哪一块做都一样。锁超时时层级在不持锁的情况下、在临时目录里算（每次写树
    都是单个 `os.replace`/`os.unlink`，不持锁读是安全的）。pre-unlink **永不写** "Retry later"。
  - 诊断按原因给修法（§4）。用户改过的跟踪文件 → 先保存自己在 `isa/` 和用户目录里的改动，再 `conda install -c … --force-reinstall isabelle`
    （替换包的每个文件、删掉该环境的用户目录；原版构建的 post-link 随后重跑依赖者的 post-link，feature 和已装包的组件登记自动恢复，用户自己
    的设置和手工 `components -u` 的登记不恢复，第 26、33 条）。**经硬链接原地写入的编辑**（vim 的 `backupcopy=auto` 就这样）连包缓存那份一起
    改了，重装恢复不了——工具这样判断：`os.path.samefile(树/p, <缓存里解开的包目录>/isa/p)` 为真且 `p` 的 sha256 不等于 `conda-meta/isabelle-*.json`
    `paths_data` 里记的（**不用** `st_nlink`：缓存干净时它会误判，评审四 C8 实测），这时报文改成：保存改动；删掉缓存里解开的那个包目录
    （conda 会从 `.conda` 归档重新解开）；在本环境和每个报同样 CONFLICT 的环境里各 `--force-reinstall isabelle`（评审四 C8 实测可恢复）。
    新建文件内容不同 → 挪开后 `isabelle-patch-control apply`。链接不上 → 装点名的包的匹配版本。锁超时或工具起不来留下的残留 → 让工具能跑
    （`conda install -c … --force-reinstall isabelle-patch-control`），`conda install <残留块点名的包>`，再 `conda remove` 它（评审三 C23 实测能把
    残留连新建文件一起反打干净）。
  - heap 提示（§4）：post-link 与命令行 `apply` 写整段；pre-unlink 与命令行 `unapply` 只写 "changed (reversed: X)" 一行；若反打后树回到链底，
    另加一行"删掉用户目录里的 `heaps/`，包内自带的 heap 就又对上了"（`store.scala:334-336,488-492`）。"重建"那句写成"Isabelle 在首次使用时
    重建每个不是由这些源码编出来的 heap"——同一棵树上重复发布内容相同的补丁时它仍然成立（评审四 C20 实测三次提示都对）。
- 原版构建的 post-link（第 13、26、33、34 条，CI 计划实现，决定 12 第 2 点）：它现有的提示 → 重跑**直接**依赖 `isabelle` 的已装包的 post-link →
  `exit 0`，**不带钩子片段的副本**。第 13 条的"重打已装 feature"由重跑里第一个 feature 钩子完成：conda 在所有 post-link 之后才写包记录、先删
  被卸包的记录（`link.py:938-999`，`path_actions.py:1209-1219`），所以重跑扫到的恰是不在本次事务里的已装包，事务里的包自己跑 post-link，每个
  feature 钩子每次换 `isabelle` 恰跑一次。它的 pre-unlink 继续删用户目录。于是 `conda update --all`、`--force-reinstall isabelle`、
  `conda create --clone` 之后补丁和已装包的组件登记都自动恢复；留下的新建文件按决定 6 就在它创建者的层级上，不碍事。

### 决定 10：feature 包的配方与渲染器

- 包名由 `isabelle_patch_control.names.package_name(feature)` 给出（`tools/common.py` 导入它；渲染器与 `make-patches` 的路径长度门禁都用它）：
  `isabelle-<feature 名把 _ 换成 ->`（`isabelle-expose-foreign`、`isabelle-future-assign-interrupt`、`isabelle-light-locale`、
  `isabelle-local-type-abbrev`、`isabelle-localized-record`、`isabelle-local-datatype`），唯一的例外条目 `dev_patches → qiyuan-dev-patches`
  （light 计划 D1）。
- 版本 = 发布 tag 里的版本号。build string **`Isabelle2025_2_<该 feature 包的 build 号>`**（第 30 条）。noarch generic。
- **复用与 build 号由一个函数决定**（`tools/common.py` 的 `plan_builds(repodata, isabelle_build, wanted)`，pytest 覆盖；评审四 C2）：对每个
  要发的 (feature 包 F, 版本 v)，若线上 `noarch/repodata.json` 里有 (F, v) 的记录、其 `depends` 恰含 `isabelle 2025.2 <isabelle 的 build string>`，
  就**复用**——把其中 build 号最高的那个原样下载进本地渠道，不重建；否则**新建**，build 号 n = 该 (F, v) 已有记录的最高 build 号加一（没有就是 0），
  再跳过任何 `https://conda.qiyuan.me/noarch/<文件名>` 对 HEAD 答 200 的 n（已上传、索引还没重建的文件）。工具包按版本复用。复用键不在 build
  string 里而在 `depends` 的钉死里，所以第 30 条的 build string 不需要带 `isabelle` 的 build 号。同一 (F, v, `isabelle` 构建) 下只改 README 或
  模板不重发——要改就发新版本。
- 依赖：`isabelle-patch-control >=1.0,<2`；**`isabelle 2025.2 <isabelle 的 build string>`**（第 22 条；`2025.2` 从 `build_string_prefix` 推出）；
  基包 `isabelle-<基> ==<版本>=Isabelle2025_2_*`（来历文件的 `base_pin`；基是 `pristine` 时没有）。
- 文件：feature 目录（patch 文件与来历文件原样）、`share/doc/<包名>/README.md`、两个钩子（`bin/.<包名>-post-link.sh`、`.pre-unlink.sh`、
  `Scripts/.<包名>-post-link.bat`、`.pre-unlink.bat`，无条件都写）；带组件载荷的包另有 `share/<包名>/`，内容由该仓库的 `tools/component_files.txt`
  列出（light：`ROOT`、`Light_Locale.thy`、`README.md`、`LICENSE`，不含 `patches/`、`tests/`、`tools/`、`private_build_logs/`）。
  `share/doc/<包名>/README.md` 以工具仓库拥有的**一段统一文本**开头（逐字复制，决定 14 的 README 也嵌同一段），后接该 feature 自己的 README。
- **一个模板、一个渲染器**，放工具仓库 `tools/render-feature-recipe`：输入包目录、`--isabelle-build <isabelle 的 build string>`、
  `--build-number <n>`、输出目录；从 `patches/<R>/provenance.txt` 算出版本、基包名、钉死、build string，复制钩子片段与统一 README 文本，有
  `tools/component_files.txt` 就加组件载荷与登记行，写出 `recipe.yaml`——**没有任何钉死是手抄的**；`provenance.txt` 的 `release_tag` 与检出的
  tag 不同时拒绝。**生成的 recipe 只写进构建的临时目录，不提交**到任何仓库。
- Windows 路径长度（迁移方案 §9 的问题）：pkgs 缓存里 feature 文件的路径是
  `<包名>-<版本>-Isabelle2025_2_<n>/share/isabelle_patch_control/features.d/<feature>/<扁平名>.patch`，今天最长 151 字符
  （`isabelle-future-assign-interrupt-1-Isabelle2025_2_0/…/src-Pure-Concurrent-future.ML.patch`），`isabelle` 包自己的预算是 198
  （`pack.sh:335-339,357`），可行。`make-patches` 的路径长度门禁（决定 16）取版本 99、build 号 99。

### 决定 11：批量发布 workflow 与发布程序（第 25、27 条）

- 工具仓库 `.github/workflows/release-features.yml`，手动触发，workflow 级 `concurrency` 组（照 `Isabelle_RPC/release-conda.yml:39-41`）。输入：
  `isabelle_build`（原版构建的 build string，必填）；`isabelle_from` = `channel` 或 `run:<isabelle-packaging-ci 的 run id>`（后者下载那次运行的
  `conda-packages` artifact 作为**第二份** artifact 供 `roundtrip` 与 `accept` 并进本地渠道，断言其 build string 等于 `isabelle_build` 且不为 0
  ——build 0 会遮住线上的 `2025.2-0`、让 §6 (e) 失真；需要一个对 `isabelle-packaging-ci` 有 `actions:read` 的 token，run token 的权限不能放宽，
  `publish-conda.yml:69-74`）；`tool_ref`（工具仓库的 tag，默认触发的 ref）；`features`（**显式**的发布 tag 列表，没有默认值）；
  `session_build_legs`（除 linux-64 之外还要跑 session 构建的腿，默认空）；`publish`（默认 false）。**没有** `build_number` 输入（决定 10 推出）、
  **没有** `roundtrip_checked`（(b2) 是 workflow 里的门禁 job）。**第一步就失败**的组合：`publish=true` 与 `isabelle_from=run:…` 同时给
  （不能只靠 `publish` job 的 `if:`，那会静默跳过发布）。
- 固定表 `feature → (GitHub 仓库, 子目录)` 写在 workflow 里；`isabelle-base-features` 的两个 feature 共用一个仓库、不同子目录。
- 作业：
  1. **`build`**（`ubuntu-latest`，唯一取 `rattler-build` 的 job，asset `rattler-build-x86_64-unknown-linux-musl` 0.69.1）：读线上
     `noarch/repodata.json`，按决定 10 的 `plan_builds` 决定每个包复用还是新建、新建的 build 号；复用的**直接下载**进本地渠道、不重建
     （`publish-conda.yml:179-180` 对字节相同的文件续传）；按 tag 检出要新建的 feature 仓库（私有仓库用一个只读的 `Contents:read` token）；渲染器
     生成 recipe；构建进**一个**本地渠道；解开每个 `.conda` 检查钩子齐全、`.bat` 是 CRLF、`.sh` 是 LF、`share/<包名>` 字面路径对
     （`RELEASE_CHECKLIST.md:630-642`，`Isabelle_RPC/release-conda.yml:115-171`）；上传**一个** artifact `feature-packages`，**只含 `noarch/*.conda`**，
     并断言每个文件都在 `noarch/` 下——这是唯一交给 `publish-conda.yml` 的 artifact，第 27 条"一次发布整批、全是 noarch"由此成立；输出
     `isabelle_rebuild`（线上有某个要发的 (F, v) 钉着别的 `isabelle` 构建时为 true，§6 (h) 据此决定是否跑）。不下载 `isabelle` 包、不核对它的
     post-link（第 33 条后它里面没有工具的东西）。理由：验收过的字节就是发布的字节，和 `build.yml` Job F/G/H 一样（§2.3）。rev 3 把构建放进五条腿
     是错的：五份不同的字节，Windows 腿的 checkout 还会把 `.patch` 变成 CRLF。
  2. **`roundtrip`**（linux-64，`needs: build`）：用 `accept` 的渠道列表建一个环境，装 `isabelle 2025.2 <b>` 与 `isabelle-patch-control`；
     `cp -a` 它的 `isa/` 作原版树；再往同一环境装链顶 feature 包（精确钉死把整条链拉进来）；跑决定 17 的 `check-roundtrip`，
     `--features-dir $ENV/share/isabelle_patch_control/features.d`、`--tool $ENV/bin/isabelle-patch-control`——测的就是发出去的字节和发出去的工具；
     `git diff-tree` 的两个 tag 从树的 `etc/ISABELLE_ID` 与链顶来历文件推出，`isabelle-patched` 用同一个只读 token 做深度 1 的两 tag fetch。
  3. **`accept`**（matrix 五条腿，各自下载同一份 `feature-packages`，run 模式下再加那份 `conda-packages`，并进 `file://` 本地渠道，跑 §6：
     `ubuntu-latest` linux-64、`ubuntu-24.04-arm` linux-aarch64、`macos-14` osx-arm64 原生加 osx-64 经 Rosetta、`windows-latest` win-64）。所有环境用
     `--override-channels -c file://<本地渠道> -c https://conda.qiyuan.me -c conda-forge`（线上渠道没有 python 和 git）。批次里有带组件载荷的
     feature 时，**linux-64 总是**跑 §6 (a) 的 session 构建（超时照 `build.yml:498`），`session_build_legs` 只加别的腿（它们的超时照
     `build.yml:583,677`）。
  4. **`publish`**（`needs: [build, roundtrip, accept]`，仅 `publish=true`）：对 `feature-packages` **调一次**
     `xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main`（第 27 条），显式传 `CONDA_R2_ACCESS_KEY_ID`、
     `CONDA_R2_SECRET_ACCESS_KEY`，不用 `secrets: inherit`。
  5. **`smoke`**（`needs: publish`；linux-64 与 win-64）：原样跑 README 的安装命令
     `conda create -n t -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches`（线上渠道在前，照 `Isabelle_RPC/release-conda.yml:375`），
     `status` 全 applied、conda 输出里恰一次 heap 提示；runner 是新的，不需要私有包缓存。
- 发布失败只能**重跑同一次运行里失败的 job**，不能重新 dispatch（重建的 `.conda` 带时间戳、字节不同，门禁拒绝；`RELEASE_CHECKLIST.md:564-567`；
  那里的"或 bump build_number"在本 workflow 里不适用，build 号是推出来的）。重跑只在 artifact 还在时可行（保留期写进 workflow）；GitHub 重跑
  失败 job 用的是第一次运行时可复用 workflow 的 SHA，所以 `publish-conda.yml` 的修复要靠新的 dispatch 才能用上（评审四 C9 核实）。
- 发布前的手续（§5 第 5 步，按用户命令）：工具仓库进 `PUBLISH_REPOS` 与 `RELEASE_CHECKLIST.md:172` 的清单；设两个 R2 密钥、只读 token、
  `actions:read` token；工具仓库加 `.gitattributes`（`*.sh text eol=lf`、`*.bat -text`、`*.patch -text`，照 `isabelle-packaging-ci/.gitattributes`）。
  `publish=true` 的前提：`release.yml` 已把原版构建发到线上且绿（含审计行）；`PUBLISH_REPOS` 里没有正在跑的发布（用清扫脚本的查询，
  `sweep-old-versions.py:211-229`）；修好的 `publish-conda.yml` 已被跨仓库调用成功过一次（§5 第 7 步）。
- 例子，light 的 HOL 侧单独改动（第 21 条末）：light 分支一个 commit → `run-tree … build …`（tested 记录，按第 35 条带 light 仓库的状态）→
  `make-patches light_locale 2` → local_type_abbrev 分支 merge light、构建、`make-patches local_type_abbrev 2` → localized_record、local_datatype、
  dev_patches 同样 → `git push` 各 feature 仓库与 `isabelle-patched` 的 tag → dispatch `release-features.yml`，`features` 列出七个 feature 的 tag
  （五个新的：light 与其上四个；expose_foreign、future_assign_interrupt 的不变、由 `plan_builds` 判定复用、直接下载），`publish=false` 看五腿，
  再 `publish=true`。
- 例子，新的 `isabelle` 构建 N+1：CI 发布它之后，dispatch 同一个 workflow，`isabelle_build=N+1`、`features` 不变：工具包按版本复用、直接下载；
  七个 feature 包没有钉着 N+1 的记录、各自新建一个 build（build 号加一、钉死换成 N+1）。
- feature 仓库自己不需要任何 workflow。rev 2/3 的 `tools/release-feature.yml` 不存在。

### 决定 12：对 `isabelle-packaging-ci` 计划的要求

1. `isabelle` 包是原版构建：CI 不再 `pip install` 工具、不打补丁、不 `hg commit`；`etc/ISABELLE_ID` 等于官方 changeset `89701cf1768e`，并加一道
   断言：打包后的树与官方 tarball 相同，例外清单按平台写在断言旁边、逐个点名（第 20 条的打包改动、heap、§2.3 列的 `obj/`、`.conda-keep`、
   两个数据库、四个 `*.la`）；多出或少掉清单外的文件就失败（`ISABELLE_ID` 等于官方 changeset 本身不能证明原版，§2.3）。保留的打包改动：
   `etc/settings` 的用户目录后缀（按第 31 条加 prefix 完整路径的短 hash）、`etc/options` 的 `ML_system_64=true`、`etc/components` 删 nunchaku、
   Windows 的 `bin/isabelle.bat`、CI 编的 Pure/HOL/Main heap。`check_patch_sync.sh`、`MBI_VERSION` 退役。不需要 `run_constraints`、不需要 k 文件、
   不需要树哈希断言。
2. `isabelle` 包的 post-link（`.sh` 与 `.bat`）在现有的提示之后、最后一行 `exit 0`（`recipe.yaml:208`）/`exit /b 0` 之前，按第 26、33、34 条
   **重跑直接依赖 `isabelle` 的已装包的 post-link**，不带工具的钩子片段：`isabelle` 包依赖 python（后果见第 10 点）；扫描 `conda-meta/*.json`，
   取 `depends` 里有名为 `isabelle` 的条目的包（`isabelle-semantic-data` 这类间接依赖者不算，§2.3），按依赖拓扑序，对每个
   `bin/.<包名>-post-link.sh`（Windows `Scripts\.<包名>-post-link.bat`）存在的包，在 `$PREFIX/bin` 下以 `PREFIX`、`PKG_NAME`、`PKG_VERSION`、
   `PKG_BUILDNUM` 环境运行它，忽略其退出码；跳过 `isabelle` 自己；`conda-meta` 里没有记录的包（正在被卸的）自然不在集合里；`*.c~` 文件不算
   钩子。pre-unlink 不变（仍删用户目录）。
3. 一次 CI 运行的五个平台腿用同一个 build 号（`build.yml` 今天已是如此），build string 就是 build 号——feature 包按它钉死（第 22 条）。
   `ci.yml` 的非发布 dispatch 接受 `build_number`（今天 `:19-23` 不传），`release.yml` 之后用同一个号发布：批量发布 workflow 要先对那次运行的
   artifact 排练（决定 11 的 `isabelle_from=run:<id>`）。artifact 只保留 7 天，过期重跑。
4. `PACKAGING_DESIGN.md` 加附录 A 的一节，并改写与之矛盾的段落：`PACKAGING_DESIGN.md:20-30`、`:737`、§7.9（`:876-`）、§7.11（`:940-`）、`:1027`；
   `recipe.yaml:3,6-9,20,182-184,235-237,253-264`；`recipe.yaml:106` 的 "no untracked files"（Windows 上 cygwin 初始化会写）；`pack.sh` 里把
   Pure 称作 "patched" 的注释；`publish-conda.yml:55` 过时的 `package_name` 说明。
5. **先修 `publish-conda.yml` 的 banner 步骤**（`:223-227`；§2.3），修法要对同仓库调用（`uses: ./…`）和跨仓库调用（`…@main`，批量发布 workflow
   就是）都成立：用 `actions/checkout` 检出 `repository: ${{ job.workflow_repository }}`、`ref: ${{ job.workflow_sha }}`（GitHub 文档记载的两个
   上下文，评审四核实），**检到一个子目录**（`path:`；默认路径会清空没有 `.git` 的工作区，渠道副本 `$CH` 就在那里），只稀疏检出
   `scripts/banner-index.py` 与 `conda/channel-banner.html`，不用浮动的 `main`；`grep` 的字串改成 banner 里真有的。不要走"把脚本放进 artifact"
   那条路：它还会弄坏 `publish-conda.yml:251-255` 的核验循环。这是 §5 第 6 步发布原版构建的前提；修好之后要被跨仓库调用成功一次（§5 第 7 步）。
6. 用户目录后缀加 prefix 完整路径的短 hash（第 31 条）。CI 计划的包测试对两个同 basename 的 prefix 比较 `getenv -b ISABELLE_HOME_USER`。
7. `RELEASE_CHECKLIST.md` §4 加两条契约（第 26、34 条）：post-link 会动 Isabelle 树或 Isabelle 用户目录的包**必须直接依赖 `isabelle`**；直接依赖
   `isabelle` 的包的 post-link **在自己的文件没变时重跑必须无效果**（`isabelle` 的 post-link 会重跑它们）。发布时检查前者。
8. 发布说明（新 `isabelle` 包的描述、`isabelle-packaging-ci` 的 `RELEASE.md` 或 `PACKAGING_DESIGN.md`——它没有 README——与 `isabelle-base-features`
   README 各一句）：`Foreign`、`RunCall`、`CInterface` 从此由 `conda install isabelle-expose-foreign` 提供；生态自己的包不需要它，因为
   Performant_Isabelle_ML ≥ 0.2.0 自己重绑 `Foreign`（§0 末的更正）。第一次从 `2025.2-0` 升级时组件登记会被旧构建的 pre-unlink 删掉、由新构建的
   post-link 重建（第 26 条），用户不需要做什么。
9. 可选：让 `publish-conda.yml` 的审计列 R2 而不是本次运行的快照（`:301-318`）。
10. `isabelle` 包依赖 python 的后果（§2.3）：`build.yml:1012,1203,1217,1286` 与 `release.yml:115` 的 `--override-channels` 安装加 `-c conda-forge`
    （或把 python、pip 及其依赖镜像进本地渠道——conda 让 python 依赖 pip，只镜像 python 还是解不出）；`release.yml` 的冒烟改成装
    `isabelle=2025.2=<刚发布的 build>` 并断言 `etc/ISABELLE_ID` 是 `89701cf1768e`（否则会静默退回线上的 `2025.2-0`）。`PACKAGING_DESIGN.md:87`
    的用户命令不带 `--override-channels`，不必改。
发布冻结（第 11 条）记在 §5 第 0 步。

### 决定 13：三个新包的仓库

- `contrib/isabelle-base-features/`（一个仓库、两个包）：`expose_foreign/` 与 `future_assign_interrupt/` 各按 light 的布局：
  `tools/patched_files.txt`（各一行）、`tools/signature_additions.txt`（都为空：`check-signatures` 对 `pristine → expose_foreign`、
  `expose_foreign → future_assign_interrupt` 都是 0 additions，§8）、`tools/required_sessions.txt`（`Pure`；两棵私有树已各有 Pure 的
  tested 记录）、`patches/Isabelle2025-2/`（`make-patches` 写并提交）、`README.md`（搬来 `patches/expose_foreign.md`、`patches/future_assign_interrupt.md`）。
- `contrib/qiyuan_dev_patches/`：`tools/patched_files.txt`（八个文件）、`tools/signature_additions.txt`（三条，`check-signatures` 算出：
  `src/Pure/Syntax/printer.ML BASIC_PRINTER val show_types_nv`、`src/Pure/Thy/thy_info.ML THY_INFO val register_thy`、
  `src/Pure/sign.ML SIGN val map_syn`）、`tools/required_sessions.txt`（`HOL`、`HOL-IMP`、`HOL-ex`）、`patches/Isabelle2025-2/`、
  `README.md`（搬来 `patches/Isabelle2025-2/register_thy.md`、`patches/show_types_nv.md`、`patches/expose_map_syn.md`，加一节
  `skip_nitpick_examples`：它在 git 里是 commit 30aab6e，在包里不是目录，第 10 条）。
- `contrib/light_locale/` 加 `tools/component_files.txt`（决定 10）；它的 README 加用户一节：session `Light_Locale`、`imports Light_Locale.Light_Locale`、
  登记在该环境的用户目录里。
- 两个新仓库和 `localized_record` 的仓库要在 GitHub 上建（按用户命令；`localized_record` 的由用户指派）；发布 tag 要 push 到各 feature 仓库和
  `isabelle-patched`（§5 第 3 步）。
- **没有仓库提交 `conda/recipe.yaml`**；recipe 由批量发布 workflow 现场渲染。

### 决定 14：工具仓库里删掉与搬走的东西

删除 `my_better_isabelle_prover/patches/`（整个，含 Isabelle2024；第 15 条）、`categories.toml`；五份 `.md`（`patches/expose_foreign.md`、
`future_assign_interrupt.md`、`show_types_nv.md`、`expose_map_syn.md`、`patches/Isabelle2025-2/register_thy.md`）在 §5 第 1 步只删除、第 3 步从
第 0 步的 commit 复制到决定 13 的仓库。`README.md`、`reference.md`、`develop.md`、`AGENTS.md` 重写。README 嵌入决定 10 的**统一文本**（每个
feature 包的 README 也以它开头），内容：**两条命令**——安装 `conda create -n <env> -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale`
（为什么要点名 `isabelle`：不点名的话以后卸掉 feature 包会连 Isabelle 和它的用户目录一起卸掉）、更新 `conda update --all -c https://conda.qiyuan.me
-c conda-forge`（不带两个 `-c` 时只有两个渠道都在全局 `.condarc` 里才行，环境级 `.condarc` 对 `-n` 不生效）；依赖剪枝（libmamba 卸顶层包会
连带卸掉只作依赖的下层包、工具，以及没被显式要求过的 `isabelle`）；`conda remove --force`；再装一遍已装的包不会把它记成显式要求的而
`--force-reinstall` 会（代价是反打再重打）；重链接一个 CONFLICT 之下的 feature 包会让 CONFLICT 之上的 feature 变成 not-applied、直到修好
（决定 7）；只支持 conda（mamba 2.x、micromamba、pixi 会让卸掉的 feature 的改动留在树里，用 `conda install -c … --force-reinstall isabelle`
恢复）；`conda install` 被 Ctrl-C 中断后的恢复（§4）；经硬链接原地编辑的恢复（决定 9）。"Coming from my-better-isabelle 0.x" 一节写在
`AGENTS.md` 里（`help` 打印的就是它，`cli.py:118-121`），README 指向它：新工具看不见 0.x 打的补丁；在 `--category all` 打过的树上装 feature 包
之前先 `my-better-isabelle unpatch --category dev`、再 `pip uninstall my-better-isabelle-prover`（只碰 0.x，第 32 条）；对 conda 的 `isabelle`
永远不要跑裸的 `unpatch`；弄坏了的树用 `conda install -c … --force-reinstall isabelle` 恢复，原版构建会自动重打 feature；dev 补丁现在是
`qiyuan-dev-patches` 包；pip 用户继续用 0.3.0，新工具只在 conda 里；CONFLICT 报文的最后一行指向这一节。`RELEASE.md` 改写成 conda 发布流程
（决定 11）。要别的维护者改的（本计划只列出，在他们下一次发布前、§5 第 8 步之后）：Isa-Mini 的四处注释（§2.2）改成指向 `qiyuan-dev-patches`；
Performant_Isabelle_ML `release-conda.yml:423-425,527-529` 与 auto_sledgehammer `release-conda.yml:195-197,273-274` 的 `--override-channels` 安装
加 `-c conda-forge` 并断言装到的 `etc/ISABELLE_ID`（§2.3 的 python 依赖后果）。

### 决定 15：测试

- `tests/`（pytest）：玩具 Isabelle 树（几个文件、`etc/ISABELLE_IDENTIFIER`、`etc/ISABELLE_ID`，不需要假 `bin/isabelle`）与玩具 `features.d`
  （三个 feature 成链，含新建文件、删除文件、可执行文件、末尾无换行）。用例：
  - 链接规则：精确 tag、hole、分叉、发行版不配、树不是原版构建（`ISABELLE_ID` = `5533cd83156e` 的玩具树加一个 feature 目录 → exit 3 且报文含
    `conda update --all`；只装工具 → exit 0 "no feature packages installed"）、`--feature` 名字打错 exit 3、没有 `provenance.txt` 的子目录和
    `*.c~` 文件被忽略、patch 文件零个或多个目标 exit 3、碰 `etc/ISABELLE_ID` 的 feature exit 3；
  - 层级与四种显示状态；多层级的两例（新建后被删；重复文本块）都读 CONFLICT；堆叠上下文的一对（上层 hunk 的上下文含下层新增的行，就是
    `syntax_phases.ML` 的形状），**feature 编号与"改过该文件的次序"不同**，在新树、半打、全打三种树上的 `status`、`apply`、`unapply` 与两个
    `--dry-run`；全打好的树上 `apply --dry-run` 一个文件都不列；
  - rev 1 评审 C3 的五个场景（改名场景改作决定 16 门禁的用例）；两个各新建一个文件的 feature 加一次模拟重链接：`apply` 到链顶、`unapply` 到链底
    不留新建文件；
  - 中断：`apply` 和 `unapply` 在第 k 个文件之后被杀，之后每个目标文件非旧即新、两命令都收敛；工具目录里写失败时树不变、exit 1、报文不说补丁坏；
    与同级环境或缓存共享 inode 的文件保持原内容与权限位；
  - 权限位：调用方 umask 002 与 077 下，改的文件保留原权限、新建文件按头部；`apply` 与 `apply-to` 给出相同权限；
  - 隔离（参数化的敌对环境，结果的字节与结论必须等于干净环境）：树在某仓库的 gitignored 子目录里；**工具自己的当前目录**在某工作树的子目录里、
    或当前目录有一个坏的 `.git` 文件；`HOME` 带 `core.autocrlf=true`、XDG attributes 文件与 `apply.ignoreWhitespace=change`；调用方导出
    `GIT_DIR`、`GIT_WORK_TREE`、`GIT_CONFIG_COUNT`；树里有 `.git` 时 exit 3；
  - 损坏的 patch 文件 exit 3 并点名；符号链接目标、目录目标、FIFO 目标 exit 3；同一 feature 两个 patch 文件同一目标 exit 3；头部行以 CR 结尾
    exit 3；
  - 锁：`status` 与 `apply --dry-run` 在只读树上都能跑；两个排他运行串行；锁被占时在上限内报忙；一个持锁者正在装入时，一个超时后不持锁算层级的
    pre-unlink 不碰它的暂存目录、持锁者装入的文件完好；`apply` 后 `unapply`，树的文件集合等于包的文件集合；
  - 决定 10 的 `plan_builds`：HOL 侧单版本重发、新 `isabelle` 构建、重复 dispatch、已上传未索引的文件四种输入；
  - 目录接口；`--isabelle-home`/`--features-dir` 的推导与拒绝（别的环境的工具加 `--isabelle-home X/isa` 读 X 的 features.d；conda 环境里传
    自装树 exit 3）；
  - `check_bytes`（也用于 §6 (k)、敌对环境用例和钩子层测试）：输入是**包归档**里的参照数据——各 feature 包的 patch 文件、`isabelle` 包的
    `info/paths.json`——从包缓存或本地渠道的 artifact 取，**不从**环境的 `features.d` 或 `conda-meta` 取（卸载会删掉它们）；调用方说明期望
    打着的 feature 有哪些。断言：打完后每个被碰文件的 git blob id（Python 算）以碰它的最高补丁的 `index` 行后像开头，打之前 blob 与最低补丁前像
    不同的文件（打包也改过的，今天是 `etc/options`）除外；卸完后每个被碰文件等于 `paths.json` 里记的 sha256、新建文件不存在；win-64 上目标清单
    同样来自归档的 patch 文件；
  - 经硬链接原地编辑（两个环境共享 inode）：同大小原地改写后普通 `--force-reinstall isabelle` 留下改动、rc 0；`conda clean -p` 不删解开的目录；
    删掉缓存里解开的目录再在两个环境各重装都恢复；缓存已重新解开的形状下选普通文案且有效（决定 9）；残留块那例的编辑写成新 inode。
- **钩子层测试**（`tools/tests/test_conda_hooks.sh`，真 conda，私有 `HOME`、`CONDARC`、`CONDA_PKGS_DIRS`，渠道 `--override-channels
  -c file://<玩具> -c conda-forge`，否则空 `CONDARC` 会落到 `defaults` 报 CondaToSNonInteractiveError）：**feature 包用真渲染器加
  `rattler-build --no-test` 构建**（不用小生成器），只有玩具 `isabelle` 包、一个只间接依赖 `isabelle` 的玩具包和"坏工具"包由小生成器造。
  玩具 `isabelle` 包带一个桩 `isa/bin/isabelle`（答 `getenv -b ISABELLE_HOME_USER`、做 `components -u/-x`）、`recipe.yaml:223-231` 的真实
  pre-unlink、**只有**第 26、34 条的重跑（没有钩子片段，第 33 条）；`ISABELLE_ID` 用真键（原版 `89701cf1768e`、旧构建 `5533cd83156e`），
  feature 包按决定 10 钉死玩具 `isabelle` 的构建。"坏工具"包是一个声明同一入口点、`import` 即抛异常的模块。断言看 conda 的 stdout
  （`.messages.txt` 被 conda 删掉）：
  - post-link 顺序等于链序且幂等；一个事务里恰一条 applied 行、一次 heap 提示；
  - 组件登记：装完 `etc/components` 列出 `share/<包名>`；显式要求 `isabelle` 时 `conda remove <包>` 后文件仍在、不再列它；`--force-reinstall isabelle`
    与 `conda update --all` 后登记仍在（第 26 条）；那个只间接依赖 `isabelle`、post-link 会计数的玩具包，在 `--force-reinstall isabelle` 后计数
    不变（第 34 条）；
  - CONFLICT 的诊断：**不变式**——事务里换了 `isabelle` 或链顶 feature 包时恰一段完整诊断，否则只有一行提示；覆盖的形状：只装链顶 feature、
    装 `isabelle` 加链顶、只装下层、以及 `--force-reinstall isabelle` 而 CONFLICT 仍在；CONFLICT 之下的 feature applied、它与其上的不动、
    history 在、安装成功；
  - 换 `isabelle` 构建（配套重发的 feature）`conda update --all` 后重打；未配套重发时 `conda update --all` 原地不动、显式装报冲突（`pintest/`
    的形状）；`--force-reinstall isabelle` 重打；`--clone` 的新环境状态相同；
  - 剪枝三例：(i) 下层包都显式要求过，卸链顶的包只跑它自己的 pre-unlink；(ii) 只显式要求过 `isabelle` 和链顶的包，卸它把只作依赖的下层与工具
    一并卸掉，pre-unlink 从上到下、工具还在时跑，树回到链底；(iii) `conda remove --force <链顶的包>` 只卸它；
  - pre-unlink 残留：用户改过文件后卸链顶；锁被占时的剪枝卸载，且有一个文件被上下两层 feature 都改过——**只按最后打印的那块残留块做**，之后树干净、
    `features.d` 为空（评审四 C11 实测）；工具起不来时卸——都出残留块、都没有 "Retry later"、恢复步骤点名的是同一个（最高的）包；`conda update --all`
    时存在 CONFLICT；`--force-reinstall` 一个 CONFLICT 之下的 feature 包（决定 7 的封顶后果）；
  - 工具启动即崩（"坏工具"包）与工具不装：安装成功、history 在、报文出现；**两例也在 win-64 上跑**；
  - `conda install` 的进程组在两次文件移动之间收到 SIGINT：history 没了；按 §4 的恢复步骤（保留派：`conda create -p` 或 `touch history` 加重装；
    放弃派：保留派之后 `conda remove <feature 包>`）之后 `status` 全 applied 或该 feature 不在、新建文件不存在、没有 `isa.staging`、
    `etc/components` 不再列它、`conda remove <链顶> --dry-run` 保留 `isabelle`；
  - 文案核对：`update --all` 升到新 `isabelle` 构建、以及重发内容相同的补丁，两种事务的 conda 输出里 heap 提示的措辞正确；
  - 在旧构建（`5533cd83156e`）的环境里 `conda install <feature>`：solver 把玩具 `isabelle` 升到原版构建，链打好，组件登记由新 post-link 重建；
  - 重链接后不修直接 `conda remove isabelle`：没有 `isa/` 残留；post-link 期间 feature 目录里有 `*.c~`：被忽略。
- 验收（§6）在五个平台腿上跑（决定 11），用工具的 conda 包解析到的 `git`（今天 conda-forge 2.56，不是本机的 2.43）；Windows 腿核 `git.exe` 的位置、
  `GIT_CEILING_DIRECTORIES` 与 `core.longpaths`、锁（一个进程持锁时第二个 `status` 在上限内报忙，同时 `type etc\ISABELLE_ID` 与
  `isabelle version -i` 都成功）、只读与被占用目标文件的 `os.replace`、`.bat` 钩子；并**测量**整链 `status` 一次和 `--force-reinstall isabelle`
  一次的墙钟时间，写进 §8（§6 要求持锁时间远低于 60 秒的等待上限；超了才按评审四 C24 的办法把读目标合成一次 `git apply --numstat --summary`
  调用、失败时逐文件回退点名）。

### 决定 16：`make-patches` 的配套改动

1. 门禁 (c) 改为 `import` 决定 8 的 `apply_to`、`unapply_from`（`sys.path.insert(0, …)`），对基 tag 的 archive 先打再反打、比树哈希；不再调
   PATH 上的 `patch`。
2. 拒绝没有 `---`/`+++` 对的块（git 对空文件的新建/删除就这样写）：空文件不发布。
3. 拒绝头部权限不是 `100644`/`100755` 的块，包括 `index` 行上的权限：符号链接（`120000`）、gitlink（`160000`）都拦在这里；玩具测试加"新增符号链接"
   与"把文件改成符号链接"两例。
4. 门禁 (f) 另加：被改文件等于 `isabelle_patch_control.engine.LOCK_FILE`（`etc/ISABELLE_ID`）→ 拒绝（决定 3 的运行时 exit 3 是后盾）。
5. **"不撤销下层、每个状态恰一个层级"门禁**（第 28 条；评审四 C5 把原来可选的强形式改成必做）：在写任何东西、打任何 tag 之前，对以新 tag 为
   顶的链核一遍——对新 feature 改的每个文件，用 `git show` 取它在链底 `<R>/pristine/<ID>`、每个下层发布 tag（沿 `base_tag` 经 annotated tag
   走，`make-patches:194-210`）和 tip 上的内容（或"不存在"），要求工具的层级函数（决定 8 的 `levels`，像门禁 (c) 导入 `apply_to` 那样导入）
   对每个状态都恰好给出它自己那个层级。拒绝时点名文件、那个状态的 tag、它匹配的层级：若另一个匹配的层级上 blob 相同，打第 28 条的话
   （改动该放进下层 feature 的新版本）；否则说这个改动的上下文有歧义、要改写。只比 blob 相同的弱形式拦不住上下文歧义的多层级文件（评审四
   C5 的三 feature 玩具 `xf3` 过了全部弱门禁、用户看到 CONFLICT）。
6. 路径长度门禁：每个 patch 文件在 pkgs 缓存里的完整路径（决定 10 的公式，`package_name` 从 `isabelle_patch_control.names` 导入，取版本 99、
   build 号 99）不超过 198 字符。
7. **feature 仓库侧**：运行前要求 `tools/component_files.txt` 自身与它所列文件、`patched_files.txt`、`signature_additions.txt`、
   `required_sessions.txt` 在该 feature 仓库里已提交且无改动（不要求整个工作树干净——它是共享的）；tip 上已有同一 feature 的发布 tag 时拒绝
   （"先 commit"）；带 `tools/component_files.txt` 的包另按第 35 条核 tested 记录里 light 仓库的状态。`provenance.txt` 不记 feature 仓库的
   commit（文件不能写出包含它自己的 commit）。
8. **写入顺序**，每一步可重跑（评审四 C13：`git commit -- 路径` 对新文件返回 0 却不提交——light 首次发布的 `provenance.txt` 会丢）：
   (a) 全部门禁通过前不碰包目录，块先写进 (c) 的临时目录；(b) 删旧 `*.patch`、复制新文件、写 `provenance.txt`；(c) **按名** `git add` 每个生成的
   文件、`git rm --cached` 每个没有再生成的旧 `*.patch`，`git diff --cached --quiet -- patches/<R>/` 有差别才 commit（没差别不是错误，重跑时常见）；
   (d) 核对该 commit 里 `patches/<R>/*.patch` 与 `provenance.txt` 的 blob id 恰等于生成的；(e) 在 feature 仓库的这个 commit 上创建同名的
   annotated tag（已有同名 tag 且树通过 (d) 的核对就接受）；(f) **最后**创建 Isabelle 仓库的发布 tag——它的存在标志发布完成，任何中途失败后
   重跑都从它缺席这一事实接着做（`make-patches:20-21,209`；迁移方案 §7 第 14 条；`:86-88` 的"tag 已存在就拒绝"照旧正确）。
9. 玩具测试相应补齐：第 4、5（`xf`、`xf3` 两例，重复文本块那例留给门禁 (c)）、7 点各有拒绝用例，拒绝后不存在任何新 tag
   （`hooks/reference-transaction:28-29` 保证 tag 不可动）；第 8 点在三处写入之后各注入一次失败、重跑必须完成；再加 light 首次发布的形状
   （已跟踪的旧格式 patch 文件被重写、加一个新的 `provenance.txt`）。`make-patches` 的输出格式不变。

### 决定 17：(b2) 脚本

`tools/check-roundtrip <原版树> <链顶 feature> [-C <isabelle-patched 仓库>] --features-dir FD [--tool <命令>]`：**`--features-dir` 是唯一的 feature
输入**（CI 里给装好的环境的 `features.d`；本地由一个小装配步骤把各**包目录**——`isabelle-base-features` 是它的两个子目录——的 `patches/<R>/`
复制成 `FD/<feature>/`）；`--tool` 默认是 checkout 里的 `python -m isabelle_patch_control`，CI 里给 `$ENV/bin/isabelle-patch-control`：
- 在 umask 022 下；
- 副本 A：`<tool> --isabelle-home A --features-dir FD apply`，然后 `status -v`，断言每个新建文件都以真实路径出现；
- 副本 B：`patch -p1 -F0` 打 `git diff-tree -r -p --no-renames <链底 tag> <链顶 tag>`——两个 tag 从 A 的 `etc/ISABELLE_ID`（链底）和链顶来历文件
  的 `release_tag` 推出；GNU patch 没有静默跳过，不可能"什么都没测就通过"；
- `diff -r` 加排序后的 `find -printf '%M %p'` 清单比对 A 与 B；断言 A 与原版不同；对 A 跑 `unapply`，与原版比对。
它既在批量发布 workflow 里作为门禁 job 运行（决定 11 的 `roundtrip`：对装好的环境的 `isa/` 副本、它的 `features.d` 和它里面的工具，
`isabelle-patched` 用只读 token 深度 1 fetch 两个 tag），也在本地按用户命令运行（§5 第 4 步，用本机的 `isabelle-patched` 克隆）。原版树：CI 的原版构建存在之前用官方 tarball
（`~/isa_release_proto/Isabelle2025-2_linux.tar.gz`，§8）解出的树，之后用原版构建 `isa/` 的副本。不再用"原版 git archive"（它没有
`etc/ISABELLE_IDENTIFIER`，也没有打包改动），也不再用 `2025.2-0` 的副本（第 22 条后它上面不会有 feature）。

## 4. 命令行与用户可见文案（第 17 条授权）

```
isabelle-patch-control [--isabelle-home DIR] [--features-dir DIR] [-v|-q] <command>

  status   [--feature F]               第一行是树与 feature 目录根；之后每个 feature 一行：applied | half-applied | not-applied | CONFLICT
  apply    [--feature F] [--dry-run]   把每个文件移到链顶（或 F）以下它自己的目标层级，只往上
  unapply  [--feature F] [--dry-run]   把每个文件移到链底（或 F 之下）它自己的目标层级，只往下
  apply-to      <dir> <feature dir>    目录接口：把 <dir> 当树、该 feature 目录当唯一 feature 打上
  unapply-from  <dir> <feature dir>    目录接口：反打
  conda-hook    post-link              供钩子调用：整链 apply；总是 exit 0，写 $PREFIX/.messages.txt
  conda-hook    pre-unlink <feature>   供钩子调用：反打 <feature> 及其上面的；总是 exit 0
  help                                 打印 AGENTS.md
```

退出码：0 成功（含没装 feature 包）；1 有 not-applied/half-applied/CONFLICT/hole、`apply`/`unapply` 有移不动的文件、`git` 在副本上写失败、锁忙；
2 找不到树、`git` 缺失或版本太旧；3 拒绝——链接不上、feature 目录的基不是这棵树的构建、树里有 `.git`、目标是符号链接或不是普通文件、patch 文件
解析不了或目标不是恰好一个、同一 feature 两个 patch 文件同一目标、patch 文件头部行以 CR 结尾、feature 目录没有 patch 文件、`--features-dir`
不存在、不在 conda 环境里又没给目录、`--feature` 名字不存在、feature 碰 `etc/ISABELLE_ID`。`conda-hook` 总是 0。
下文凡出现 `conda install`/`conda update`，都带 `-c https://conda.qiyuan.me -c conda-forge`（决定 14），这里为短省略为 `conda install -c …`。

heap 提示（`apply`/`unapply` 真的改了 `src/` 下文件后打印；钩子写进 `.messages.txt`）。post-link 与命令行 `apply` 写整段：
```
Isabelle sources under $PREFIX/isa changed (applied: light_locale).
The heaps shipped with the isabelle package were built from other sources; Isabelle rebuilds, on first use, every heap not
built from exactly these sources, into the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER),
under heaps/ (HOL takes several minutes). To do it now: isabelle build -b HOL
```
pre-unlink 与命令行 `unapply` 只写第一行（`(reversed: light_locale)`）；若反打后树回到链底，另加一行：
`The tree is back at the shipped sources. Delete heaps/ in the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER)
and the shipped heaps are used again.`（用户目录里的 heap 先被找到，`store.scala:334-336,488-492`，所以不删它们时不声称包内 heap 又能用。）

链接不上：`feature chain broken: isabelle-light-locale 1 (features.d/light_locale) needs isabelle-future-assign-interrupt 1 (Isabelle2025-2/future_assign_interrupt/1);
installed: isabelle-future-assign-interrupt 2. Install matching versions of these packages.`（包名经 `names.package_name`。）
树不是原版构建（有 feature 目录时）：`$PREFIX/isa has etc/ISABELLE_ID 5533cd83156e, but features.d/expose_foreign was made for Isabelle2025-2 pristine
89701cf1768e. Feature packages exist only for the pristine isabelle build. Run: conda update --all -c https://conda.qiyuan.me -c conda-forge`
CONFLICT（完整诊断，链顶 feature 的钩子写）：
```
isabelle-patch-control: light_locale is in CONFLICT in $PREFIX/isa: src/Pure/Isar/locale.ML matches no level, or several levels, of the
feature chain. Features below light_locale are applied; light_locale and the features above it were not applied.
  First save any edits of your own under $PREFIX/isa and in the environment's Isabelle user directory: the repair replaces every
  file of the isabelle package and deletes that directory (registrations made by installed packages come back by themselves;
  your own settings and manual "isabelle components -u" entries do not).
  If you edited that file: conda install -c … --force-reinstall isabelle
  If a file created by a feature (marked "created" in status -v) has other content: move it aside, then: isabelle-patch-control apply
Details: isabelle-patch-control status -v.  Coming from my-better-isabelle 0.x? See: isabelle-patch-control help
```
文件是经硬链接原地改写的（决定 9 的判据）时，"If you edited that file" 一行换成：
`Your edit was written through the package cache, so a plain reinstall keeps it. Save it; delete the extracted package directory
<pkgs>/isabelle-2025.2-<b>/ (conda re-extracts it from the .conda archive); then run conda install -c … --force-reinstall isabelle here and in
every other environment that reports this conflict.`
其他钩子的一行提示：`isabelle-patch-control: light_locale is in CONFLICT (src/Pure/Isar/locale.ML); see isabelle-patch-control status -v`
pre-unlink 的残留块（任何原因；点名的包是此刻 features.d 里最高的 feature 包，同一条命令的每块都相同）：
```
isabelle-patch-control: could not fully reverse light_locale before its package is removed or replaced [reason: CONFLICT | lock busy | …].
These files under $PREFIX/isa still carry its changes:
  src/Pure/Isar/locale.ML
  src/Pure/Isar/light_locale_axiom_facts.ML   (created by the feature)
If you are removing light_locale, status will not see them once the package is gone. To clean up: save your own edits under
$PREFIX/isa; then conda install -c … --force-reinstall isabelle (restores the package's files, deletes this environment's Isabelle
user directory; the remaining features are re-applied automatically); then delete the created files listed above.
If the cause was "lock busy" or the tool could not run: conda install -c … <最高的包名>; then conda remove <最高的包名>
```
锁忙。命令行：`another isabelle-patch-control run holds the lock on $PREFIX/isa/etc/ISABELLE_ID (its inode may be shared with another conda
environment on this machine); gave up after 60 s. Retry later.` post-link 的 `.messages.txt` 里同一句后面加 `Then run: isabelle-patch-control apply`。
pre-unlink 不写这句，写残留块。
`conda install` 被 Ctrl-C 中断后（README；`status` 在 `conda-meta` 存在而 `conda-meta/history` 不存在时也打印——若中断的事务装的正是工具，`status`
也没了，只有 README 还在）：conda 回滚了整个事务并删掉了 `conda-meta/history`，post-link 已写进 `isa/` 的改动留着，恢复之前每条 `isabelle` 命令
都可能打印 `### Missing Isabelle component`；恢复：`conda create -p $PREFIX -c … <要保留的全部包和被中断的那个包>`（不需要先 `touch`），或
`touch $PREFIX/conda-meta/history`（Windows：`type nul > "%PREFIX%\conda-meta\history"`）后 `conda install -c … <同一批包>`；若不想要那个
feature，先这样恢复、再 `conda remove <它的包名>`——由工具反打、删新建文件、删暂存目录，比 `--force-reinstall isabelle` 干净（评审四 C16 实测）。

## 5. 落地顺序

0. 按用户命令：提交工具仓库里已写好的 `tools/` 与 README 一节（§2.5）；在 `isabelle-packaging-ci/RELEASE.md` 记发布冻结——CI 改成原版构建之前
   不发任何 `isabelle` 构建（第 11 条的规定，这是它唯一的理由）。
1. 工具改造（决定 1–9、14；决定 15 的 pytest）；pytest 全绿。GitHub 改名与 `.gitmodules:41`（决定 1）；卸掉 base 与 `.venv` 里旧的 editable 安装
   （base 是共享环境，先得用户批准；没有东西调 `my-better-isabelle`）。此时 `patches/` 已删、五份 `.md` 已删（第 3 步从第 0 步的 commit 复制），
   旧工具 0.3.0 在 PyPI 上照常。
2. `make-patches` 配套改动（决定 16）、`run-tree` 的 tested 记录加 `-d` 目录的仓库状态（第 35 条）、(b2) 脚本（决定 17）；玩具测试全过；
   `make-patches pristine` 检查 (a) 仍过。
3. 按用户命令在 GitHub 建 `isabelle-base-features`、`qiyuan_dev_patches`（`localized_record` 的仓库由用户指派）；建 `contrib/isabelle-base-features/`；
   用户下令 `make-patches expose_foreign 1`、`make-patches future_assign_interrupt 1`（迁移第 4 步）。light：按用户命令在私有树上做完整构建
   （`run-tree contrib/Isabelle2025-2-light_locale build …` 五个 light session 加 FOL、ZF），然后 `make-patches light_locale <版本>`；三个新
   feature 就绪后各自构建、`make-patches`；建 `contrib/qiyuan_dev_patches/`，按用户命令 `run-tree contrib/Isabelle2025-2-dev_patches build HOL
   HOL-IMP HOL-ex`（在最终 tip 上），然后 `make-patches dev_patches 1`。把各 feature 仓库的分支与 tag、`isabelle-patched` 的 tag push 上去。
   之后删 `contrib/Isabelle2025-2-staging`（迁移方案）。
4. (b2)（决定 17）在官方 tarball 的树上对现有的链本地跑一遍。
5. 渲染器与批量发布 workflow（决定 10、11）；钩子层测试（决定 15）在玩具渠道上全过。按用户命令：工具仓库进 `PUBLISH_REPOS` 与清单、设两个 R2
   密钥与两个 token、加 `.gitattributes`。
6. CI 计划：写、评审、落地（决定 12，先修 banner 步骤）；`ci.yml` 以 `build_number=N` 的非发布 dispatch 产出原版构建的 artifact。
7. 批量发布 workflow 以 `isabelle_from=run:<那次 id>`、`publish=false` 排练：五条腿全绿（§6 不含 (h)）——这是 `.bat` 钩子和 `isabelle` 包的重跑
   第一次真跑，发生在任何发布之前。(b2) 在该 artifact 的 `isa/` 上也过了（`roundtrip` job）。同时让修好的 `publish-conda.yml` 被**跨仓库**调用
   成功一次：下一个组件包的发布，或一个最小的调用方、产物里只放一个已发布的 `.conda`（逐字节下载的，门禁当作续传）。不能用批量发布 workflow
   当这个试验：第 8 步之前它的包一个都没发布。
8. 用户下令：CI 的 `release.yml` 以同一个 N 发布原版构建；紧接着批量发布 workflow 以 `isabelle_from=channel`、`publish=true` 一次发布
   （第 16、27 条），它先对线上的原版构建重跑 §6、再发布、再冒烟。发布说明（决定 12 第 8 点）同时就位。各仓库的 `README` 与 `AGENTS.md`
   就位；Isa-Mini 的注释与两个组件仓库的 workflow 改动（决定 14）由各自维护者改。

## 6. 验收

- pytest 与钩子层测试全绿；`make-patches` 玩具测试全过；(b2) 在官方 tarball 的树（本地）与原版构建的树（`roundtrip` job）上都通过。
- 五个平台腿、本地渠道加线上/artifact 的原版构建加 conda-forge（决定 11），每个场景从新环境开始、所有该留下的包都显式要求过：
  (a) `conda create -n t isabelle=2025.2=<b> isabelle-light-locale` → `status` 全 applied；conda 输出恰一条 applied 行、一次 heap 提示；
  `etc/components` 列出 `share/isabelle-light-locale`；linux-64 上（以及 `session_build_legs` 里的腿上）一个 `imports Light_Locale.Light_Locale`
  并使用 `light_locale` 命令的 theory 能通过检查；
  (b) `conda remove isabelle-light-locale` → light 反打干净、新建文件消失、下层 feature 不动、`etc/components` 不再列它；剪枝三例（决定 15）；
  每例之后跑 (k)；
  (c) `conda install --force-reinstall isabelle` → 重跑直接依赖者的 post-link：`status` 不变，`etc/components` 仍列出 light 与一个
  Isabelle_RPC 式的组件，conda 输出一次重打记录；
  (d) `conda create --clone` → 新环境 `status` 与原环境相同；
  (e) 在装着 `isabelle-2025.2-0`（线上）加一个组件包的环境里 `conda install isabelle-light-locale` → solver 把 `isabelle` 升到原版构建、链打好、
  组件登记由新 post-link 重建（第 22、26 条）；
  (f) 故意改坏一个跟踪文件后装包 → 安装成功、诊断按决定 15 的不变式恰一段、`status` 显示 CONFLICT 与其下 applied、环境仍可用；再
  `--force-reinstall isabelle` 而 CONFLICT 仍在 → 仍恰一段完整诊断；
  (g) 全部 pre-unlink 成功的前提下 `conda remove isabelle` → 四条 POSIX 腿 `test ! -e "$PREFIX/isa"`；win-64 上断言没有任何 feature 补丁的目标
  路径存在、没有 `isa.staging`、`isa/` 下剩下的都在 `contrib/cygwin/` 之下（这是 `isabelle` 包自己的残留，§2.3）；装与不装 feature 包各一次；
  用户目录不存在；
  (h) 只在 `build` job 的 `isabelle_rebuild` 为 true 时执行（线上有钉着别的 `isabelle` 构建的 feature 包）：`conda update --all -c …` 把 `isabelle`
  和全部 feature 一起升（"未配套重发时原地不动"那一半在钩子层测试里）；
  (i) 只装工具的 `2025.2-0` 环境里 `status` → exit 0、"no feature packages installed"；再放进一个 feature 目录 → exit 3，报文含
  `conda update --all -c https://conda.qiyuan.me -c conda-forge`；
  (j) 在一个 git 工作树之下建环境（`conda create -p <仓库>/env …`）→ 结果与 (a) 相同；
  (k) `check_bytes`（决定 15，参照数据取自包归档）在 (a) 之后、(b) 的每一例之后各跑一次，五条腿都跑；(g) 不跑它——那里期望的是"不存在"，(g) 自己
  的断言已覆盖（第三轮 C21 判决排除了 `paths_data` 比对；第三轮 C20 判决写的 "(a), (b) and (g)" 在此有意偏离，§10）。
  中断、锁、权限位、敌对环境、`.c~`、SIGINT 在 pytest 与钩子层测试里覆盖（决定 15），不在真实渠道上重复。

## 7. light 计划 D4 清单逐条

交接清单 `LIGHT_LOCALE_HANDOFF.md:1979` 的 (1)–(19)，括号里是 `reader2_patch_scheme.md` 的发现与决定编号。

| 交接项 | 本计划的回答 | 状态 |
|---|---|---|
| (1) 只更新 `isabelle` 包补丁丢失（发现 2、D3） | 决定 9、12：原版构建的 post-link 重跑直接依赖者的 post-link，feature 钩子整链重打；第 22 条：feature 钉死构建 | 用户第 13、22、26、33、34 条 |
| (2) pre-unlink 失败只警告、要不要账本（发现 3、D4） | 决定 9：exit 0，反打不完时在 features.d 还完整的当下写出残留清单与恢复步骤；不建账本 | 用户第 12 条；本计划 |
| (3) `$CONDA_PREFIX` 找错环境（发现 4） | 决定 2：钩子里用 `$PREFIX`，树与 feature 目录从同一个前缀推出 | 本计划 |
| (4) 多个补丁不原子（发现 5） | 决定 5、7：逐文件暂存加原子改名，中断后收敛 | 用户第 24 条 |
| (5) `--no-backup-if-mismatch --reject-file=-`（发现 7） | 消解：`git apply` 不写 `.orig`/`.rej` | 本计划 |
| (6) 新文件 diff 写法、目标已存在且不同时判 CONFLICT（发现 6、D7） | `--- /dev/null`（迁移第 13 条）；决定 6：内容不同就无层级 = CONFLICT | 已裁定；本计划 |
| (7) 往返验证的参照、要不要 pristine 整树构建（发现 8、D6） | 门禁 (c) 用基 tag 的 archive（已裁定）；(b2) 用官方 tarball 与原版构建的树（决定 17，本计划定）；整树构建是 CI 的事 | 已裁定；本计划 |
| (8) `after`/`order.txt`、`unpatch --feature X` 上面有 feature 时怎么办（发现 11） | 决定 3：链由精确 tag 推出；决定 7：`unapply --feature X` 反打 X 及其上面的 | 本计划 |
| (9) 版本键、`--feature` 校验、conda 依赖写法（发现 10） | 决定 3：`<R>` 从 `etc/ISABELLE_IDENTIFIER` 读；决定 2：名字不存在 exit 3；决定 10：`isabelle 2025.2 <build string>` | 本计划；用户第 22 条 |
| (10) 平台（发现 12、D8） | 全平台：`git apply`、conda-forge `git`、`.sh` 与 `.bat`，五个平台腿验收 | 用户第 18 条 |
| (11) 硬链接 inode 上 chmod、目录写权限（发现 13） | 决定 5：不 chmod 树里的文件；权限位在副本上设；`os.replace` 给新 inode | 本计划 |
| (12) 补丁文件命名、`features.d` 布局（发现 14、D12） | `make-patches` 的扁平命名，仓库布局与 `features.d` 相同 | 已落地 |
| (13) 并发锁（发现 15） | 决定 5：`flock` 锁 `etc/ISABELLE_ID` | 本计划（第 17 条授权） |
| (14) pixi/micromamba（发现 16） | 只支持 conda；micromamba、mamba 2.x 不跑 pre-unlink、pixi 不跑 link 脚本（§2.3） | 本计划（第 17 条授权） |
| (15) `PACKAGING_DESIGN.md` 的例外（D5） | 附录 A | 用户第 14、20 条 |
| (16) 钩子 `exit 0` 规矩（D2） | 决定 9：exit 0 写在钩子文本里 | 用户第 12 条 |
| (17) 非 conda 的共享树上怎么找 feature（D9） | 开发不用工具（私有树经 `run-tree`）；需要时 `--features-dir`（单个目录，不可重复，无环境变量） | 本计划 |
| (18) 默认类别对外部 feature 的含义（D10） | 没有类别：装了的包就是要打的 | 本计划 |
| (19) conda 版工具带不带内部 feature（D11） | 不带（第 11、15 条） | 已裁定 |
| 发现 1 / D1 `syntax_phases.ML` 与 dev 补丁重叠 | 链序解决：dev_patches 在链顶（迁移方案第 9、26 条） | 已裁定 |
| 发现 9 备份 diff 收进别人的改动 | 迁移方案门禁 (f)、自有 commit 门禁 | 已裁定 |

## 8. 证据

- 作者 2026-10-22/23（git 2.43.0，普通目录，作者的配置）：§2.4 第一段；`patch-ng` 1.19.1、`whatthepatch` 1.0.7、`pygit2` 1.20.1 的对照（§2.4 末）。
- 第二轮评审（scratchpad `review-ipc2/`）与作者 2026-10-24 的复现（`verify2/`）：嵌套仓库里 `git apply` 对两个文件都"跳过补丁"、
  `--check`/`-R --check`/`apply` 都 rc=0、文件不变，`GIT_CEILING_DIRECTORIES` 后正确；strace 显示 `unlink` 先于 `O_CREAT|O_EXCL`。评审另测：
  `core.autocrlf=true` 下写出 CRLF、往返不复原；`GIT_DIR` 指向目录时读 `$GIT_DIR/config`；白名单环境无 `HOME` 往返逐字节相同；杀进程原型 32 个
  位置全收敛；第二轮原型（每步 `--check` 加 `apply`）每次 `status` 1.3–2.3 秒，现在的设计是 §2.4 的 0.16–0.43 秒。
- 第四轮评审（scratchpad `review-ipc4/`）：`isabelle` 包里的钩子片段副本让 `--force-reinstall isabelle` 的 CONFLICT 诊断出两遍、无工具时提示出 n+1 遍
  （`critic-conda/run2.out`）；`isabelle-semantic-data` 的钩子文本经 HTTP range 读出（`critic-conda/semdata-hooks.out`）；加了 python 依赖后
  `--override-channels` 装 `isabelle` 报 "nothing provides python"（`defender-C1`）；复用键按 build string 永不匹配（`defender-C2/proto/derive.py`）；
  三 feature 玩具 `xf3` 过全部弱门禁后用户读到 CONFLICT（`defender-C5/harness.out`）；`git commit -- 路径` 对新文件返回 0 不提交（judge `c13`）；
  `if errorlevel 1` 对负退出码为假（`defender-C7/bat`，wine）；`st_nlink` 在干净缓存上误判、删解开目录再重装可恢复原地编辑（`defender-C8`）；
  同一条命令里按最后一块残留块做就干净（`defender-C11/x1.out`）；保留派恢复后 `conda remove` 比 `--force-reinstall isabelle` 干净（`defender-C16`）；
  `-n` 下环境级 `.condarc` 不生效（`defender-C17/run4.out`）；超时 pre-unlink 与持锁者并发安全（`defender-C18/race.out`）；`apply --dry-run` 字面读法
  在只读树上失败（`defender-C18/rotree.out`）；CRLF 的新建文件补丁以 rc 0 应用（`defender-C19/e1.out`）；同一棵树上三次 heap 提示的措辞
  （`defender-C20/run1.out`）；rattler-build 丢 `*.la`（`defender-C23/rb/`）；`Library\bin\git.exe` 是转接器（`defender-C24/wrapper.out`）；
  tested 构建之后再提交的 `Light_Locale.thy` 被发布（`defender-C10/e3.out`）。judge 核实：`job.workflow_repository`/`job.workflow_sha` 有文档、
  重跑失败 job 用首次运行的可复用 workflow SHA；conda 的包记录在全部 post-link 之后才写、被卸包的记录先删（`link.py:938-999`、
  `path_actions.py:1209-1219`）。
- 第三轮评审（scratchpad `review-ipc3/`）：`--numstat --summary` 在工作树子目录里静默返回空（judge `ns/`）；写模式 128 = 写失败（`defender-C17/e1.out`）；
  Windows 读到文件末尾的程序会碰到"末尾之后 1 字节"的锁（`defender-C22`）；`isabelle` 的 pre-unlink 删掉全部组件登记、`--force-reinstall isabelle`
  后 `etc/components` 为空（`critic-conda/run3.out`）；经硬链接原地编辑会改包缓存、重装不恢复（`defender-C27/run.out`）；`publish-conda.yml`
  一次上传产物里全部包（`defender-C6`）；重建的 noarch 包字节不同（`defender-C3`）；Windows checkout 的 CRLF patch 被 `git apply` 拒绝
  （`defender-C5`）；SIGINT 下 conda 回滚整个事务并删 history、`touch history` 加重装收敛（`defender-C11`）；锁忙或工具起不来留下的残留用
  `conda install <包>; conda remove <包>` 清干净（`defender-C23`）；线上渠道没有 python/git、要加 conda-forge（`defender-C15`）；真实链上
  "撤销下层"0 例（`revisit_gate.py`）。作者核实：banner commit 85dc11b（10-09 23:26Z）晚于最后一次成功发布（10-09 05:03Z `release-isabelle-ai`）、
  字串不在任何文件里、`publish-conda.yml` 没有 checkout 步骤；`constants.py:180` 的 `.c~`；`components.scala:294-302`。
- 第 22 条的 solver 行为（作者 2026-10-24，scratchpad `pintest/`，conda 25.11.1，libmamba 与 classic）：§2.3。
- conda 25.11.1 的钩子、回滚、顺序、剪枝、入口点、PATH、`.messages.txt`、`.c~`：§2.3 引用的源码行，评审三轮的 defender 在玩具渠道上实测。
- conda-forge `git` 各平台体积、win-64 的 PortableGit 来源与 `autocrlf`：§2.3。
- `check-signatures`：`pristine → expose_foreign`、`expose_foreign → future_assign_interrupt` 各 0 additions；`future_assign_interrupt → ab6006e` 三条。
- 路径长度：决定 10 的公式，最长 151、预算 198。
- `pack.sh` 的改动、缓存里的权限位分布、Performant_Isabelle_ML 的 `rescue_foreign.ML`、`RELEASE_CHECKLIST.md` 与 `build.yml` 的引用行：作者核对文件。
- 官方 tarball `~/isa_release_proto/Isabelle2025-2_linux.tar.gz` sha256 `a20a507bc7c1270d8be96a9f3fbec06345387789d2dc2c4d3df6260d47bfb33c`。

## 9. 不做的事；待用户在发布时定的事

不做：
- 工具不构建 heap。
- 不做 conda 不跟踪的"已打补丁账本"；也不采用"拿 `conda-meta` 的逐文件 sha256 比对 `isa/`"作为状态来源（评审二 C8 的可选项）：状态只从重放得出。
  `conda-meta` 的 `paths_data` 只在两处读：决定 9 判断"经硬链接原地编辑"以选修复文案，决定 15 的 `check_bytes` 作卸载后的校验。
- 不支持一个环境里两棵 Isabelle；不支持自装的 Isabelle2025-2；不支持 mamba 2.x、micromamba、pixi。
- 不改 `make-patches` 的输出格式。
- 不自己实现任何补丁逻辑；不在树里运行 `git`；不在调用方的当前目录运行 `git`。
- 不发 PyPI（第 23 条）。
- 组件包不精确钉死 `isabelle` 构建（第 26 条）。

待用户在发布时定：
- `isabelle-ai` 元包要不要依赖 `isabelle-future-assign-interrupt`（它是每个人都该有的修复，原版构建不带它）。

## 10. 对照表（**与裁决不同之处明说**）

### 10.1 rev 4 → rev 5（第四轮评审 24 条）

| 评审 | 本版 |
|---|---|
| C1 python 依赖的后果 | §2.3 新增一条；决定 12 第 10 点（`build.yml`/`release.yml` 加 conda-forge、冒烟钉构建并断言 ID、改写清单加 `recipe.yaml:182-184,235-237`、`PACKAGING_DESIGN.md:737`）；决定 14 列两个组件仓库的改动；`PACKAGING_DESIGN.md:87` 不改 |
| C2 复用键 | 决定 10 的 `plan_builds`（按 `depends` 里的 `isabelle` 钉死复用、HEAD 探测、工具按版本）；决定 11 的并发组、保留期、例子改为"七个 tag、五个新"；决定 15 的 pytest；§0 第 30 条删推导句。**不改** §0 对 Q5 的记录：judge 判不需要 |
| C3 `isabelle` 包的片段副本 | 第 33 条 (a)：决定 9、12 第 2 点删副本；决定 11 删逐字节核对与 `isabelle` 下载；决定 1 解除绑定；诊断规则只看链顶（下一行） |
| C4 重跑范围 | 第 34 条 (a)：决定 12 第 2 点只限直接依赖；§2.3 写明 `isabelle-semantic-data`；决定 12 第 7 点两条契约；决定 15 间接依赖者计数用例；§0 更正作者的话。judge 的 (b) 属于 Semantic_Embedding，记在 §9 外不展开 |
| C5 强门禁 | 决定 16 第 5 点改为必做；决定 6 的保证指向它；决定 8 公开 `levels`；§4 CONFLICT 文案 "no level, or several levels"；决定 16 第 9 点 `xf`/`xf3` 用例。judge 说这扩展第 28 条的门禁，已在第 28 条的精神内（"同时匹配几个层级一律 CONFLICT"） |
| C6 artifact 与 run 模式 | 决定 11：`feature-packages` 只含 `noarch/` 并断言；run 的 `conda-packages` 作第二份 artifact 只供 roundtrip/accept；`publish=true` 加 `run:` 第一步失败 |
| C7 `.bat` pre-unlink | 决定 9 写出全文；两行 `if` 判退出码；片段到 `fi`/`:end` 为止；§4 Ctrl-C 恢复把 `conda create -p` 放前面、Windows 用 `type nul >` |
| C8 原地编辑 | 决定 9：`samefile` 加 sha256 判据（不用 `st_nlink`）、删解开目录再重装的修法；§4 两种文案；决定 15 两环境用例；§9 说明 `conda-meta` 的两处读 |
| C9 banner 修法 | 决定 12 第 5 点：按 `job.workflow_sha` 检出到子目录、稀疏、不浮动 `main`、删 artifact 方案；§5 第 7 步跨仓库试跑；决定 11 说明重跑不会带上修复；§0 第 25 条引用改"决定 12 第 5 点" |
| C10 tested 记录绑 light 仓库 | 第 35 条 (a)：决定 16 第 7 点、§5 第 2 步、迁移方案第 32 条；决定 11 linux-64 总是构建组件 session；judge 的可选项（tag 注解记 package_commit）未采用 |
| C11 残留块 | 决定 9：only 自己 feature 的文件、"removed or replaced"、恢复点名最高的包、`||` 文本让用户装回整批再卸；§4 文案；决定 7 与决定 14 写封顶后果；决定 15 共享文件加锁忙用例、update --all 带 CONFLICT、重装 CONFLICT 之下的包；§8 更正 C23 的实测描述 |
| C12 链顶 | 术语表：链顶 = 建出的链的最后一个 feature、链序最末 = dev_patches、tip；决定 9 `$PKG_NAME` 经 `package_name` 反查；诊断规则去掉 `isabelle` 钩子那半 |
| C13 两仓库写入 | 决定 16 第 8 点：按名 add、`rm --cached`、有差别才 commit、核 blob、feature 仓库 tag 先、Isabelle tag 最后；第 7 点加 `component_files.txt` 自身；第 9 点失败注入与 light 首发形状 |
| C14 `check-roundtrip` 接口 | 决定 17 `--features-dir` 唯一输入、`--tool`、本地装配；决定 11 `roundtrip` 用装好的环境 |
| C15 验收与测试可跑性 | 决定 15 `check_bytes` 的输入来自归档、"坏工具"包的定义；§6 (b) 每例后跑 (k)、(g) 不跑 (k)（**偏离**第三轮 C20 的 "(a), (b) and (g)"，理由见 §6）、(h) 按 `isabelle_rebuild` |
| C16 Ctrl-C 恢复 | §4：放弃派改为"保留派之后 `conda remove`"、两句新说明；决定 5 `finally` 删暂存目录；决定 15 SIGINT 变体；附录 A 同步。**改了**第三轮 C11 判决给的恢复文本 |
| C17 更新命令 | 决定 14 两条带渠道的命令与理由；§4 全部 conda 命令带渠道；钩子片段与残留块同；剪枝句含 `isabelle`；决定 11 冒烟原样跑 README 的命令。这是在第 22 条之上的补充，不改它 |
| C18 目录由锁模式决定 | 决定 5；术语表；决定 15 只读树 dry-run、并发用例；决定 9 "在临时目录里算" |
| C19 不能表示的输入 | 决定 2 非普通文件拒绝（含门禁 (c) 的说明）；决定 3 重复目标、CR 头部；§2.4 CRLF 事实订正；决定 15 用例。**不采纳**强制目录权限 0755（judge 也否决） |
| C20 文案 | §4：heap 模板一个、pre-unlink 一行、回到链底加一行、"not built from exactly these sources"、busy 后 "Then run"、新建文件标出、登记恢复的边界、链接不上点包名；决定 14 `help` 目标统一为 AGENTS.md |
| C21 记录 | §0 第 26 条两句引语归位；第 30 条删推导句；全文"`isabelle` 包的 build 号"；§5 第 0 步只给第 11 条作理由；§10.2 补 REVIEW2:584 的注 |
| C22 附录 A | 第一句收窄到包的内容；括号改成论证句（pre-unlink 删用户目录、只有 `isabelle` 的 post-link 能恢复、Python、与 `PACKAGING_DESIGN.md:52` 的偏离同组件钩子）；代价一条按第 34 条改 |
| C23 事实 | §2.3：`.messages.txt` 是本计划的做法、`update --all` 的真实行为、四个 `*.la`；决定 12 第 1 点按平台的例外清单；决定 12 第 8 点 `isabelle-packaging-ci` 无 README |
| C24 性能 | §2.4 新数字与 Windows 转接器事实；§8 订正；决定 5 注明 Linux；决定 15 Windows 测量与 §6 的界 |

### 10.2 rev 3 → rev 4（第三轮评审 32 条、judge 另加两条），含第四轮查出不实的八行的订正

rev 2 → rev 3 的对照见 `ISABELLE_PATCH_CONTROL_PLAN.rev3.md` §10。第四轮查出 rev 4 §10 不实的八行在本表相应行标 **【订正】**。

| 评审 | 本版 |
|---|---|
| C1 组件登记 | 第 26 条 (d)：决定 12 第 2 点重跑依赖者的 post-link；§2.3；决定 9 的修复文案；§6 (c)(e)；决定 15 登记断言。**与 judge 的推荐 (a) 不同**：用户选 (d)，不改 pre-unlink |
| C2 读目标未隔离 | 决定 4 唯一原语；决定 3 恰好一个目标、无 patch 文件 exit 3；决定 15 当前目录敌对用例 |
| C3 重跑无法发布 | 决定 11：已发布的包直接下载、工具只在未发布时构建、删 `build_number` 输入、只重跑失败 job；§0 第 22 条改"`isabelle` 包的 build 号输入"。**【订正】**rev 4 的复用键"(名, 版本, build string)"在第 30 条之后永不匹配；rev 5 决定 10 的 `plan_builds` 按 `depends` 里的 `isabelle` 钉死复用，并给出判决要的单元测试函数 |
| C4 tag 无人创建、仓库不存在 | 决定 16 第 7、8 点（rev 5 把写入顺序改为 feature 仓库 tag 先、Isabelle 发布 tag 最后，第四轮 C13）；决定 11 固定表与显式 `features`；§5 第 3 步建仓库、push tag；§0 第 21 条末 HOL 侧发布流程 |
| C5 五腿各自构建 | 决定 11 `build` 一次、五腿下载同一 artifact；`.gitattributes` |
| C6 八次调用 | 第 27 条：一次调用。judge 的 (a)，用户同意 |
| C7 多层级规则 | 第 28 条：发布门禁（决定 16 第 5 点）加一律 CONFLICT（决定 6）。judge 的 (a)，用户同意 |
| C8 去重不可能 | 决定 9 按 `$PKG_NAME` 分配诊断；`names.py` 进 Python 包；决定 15 诊断条数。rev 5 按第 33 条把"`isabelle` 的钩子也写完整诊断"去掉——第三轮 relaxation 5 的那一半被第 26 条的重跑取代 |
| C9 exit 3 矛盾 | 第 29 条 (b)：无 feature exit 0；决定 3 的判据；§6 (i) |
| C10 五腿验收在发布之后 | 决定 11 `isabelle_from=run:<id>`；决定 12 第 3 点；§5 第 6–8 步。rev 5：run 的 artifact 只供 roundtrip/accept，不进发布（第四轮 C6） |
| C11 中断的事务 | 决定 5 限定收敛声明；§2.3 信号路径；§4 恢复步骤；决定 15 SIGINT 用例；附录 A。**【订正】**第二轮 C2 判决（REVIEW2:584）那句"重装该 feature 即补完"被第三轮实测为假，rev 4 漏记 |
| C12 (b2) 只靠勾选 | 决定 11 `roundtrip` job；决定 17 两个 tag 推出、CI 与本地都跑；删 `roundtrip_checked`。rev 5：`roundtrip` 对装好的环境跑、`--features-dir` 是唯一 feature 输入（第四轮 C14） |
| C13 钩子层测试不测渲染器 | 决定 15：真渲染器加 rattler-build、桩 `isabelle`、登记断言；决定 11 `build` 解包检查 |
| C14 build string | 第 30 条：撤回，恢复第 27 条原文；§0 第 4 条逐字引用。rev 5：复用键因此移到 `depends` 的钉死里（决定 10） |
| C15 冒烟无解 | 决定 11：渠道列表加 conda-forge、线上渠道在前；钩子层测试同。**【订正】**rev 4 的 §10 没说"私有包缓存"一项按第三轮判决改成"runner 是新的" |
| C16 附录 A 事实 | 附录 A 第 2 条列非穷尽差别；引 `RELEASE_CHECKLIST.md` §4 而不是 §7.9 |
| C17 128 的解读 | 决定 4 按阶段解读、无 `--check`；§4 退出码 |
| C18 层级索引 | 决定 6 按 feature 编号；决定 7 每个文件自己的目标层级；决定 15 编号与次序不同的用例、全打树 dry-run 为空 |
| C19 API 碎片 | 决定 8 公开 API、`install_files` 删除、门禁 (c) 用 `apply_to`/`unapply_from`；决定 5 重放一次、目录接口的临时目录。rev 5：判决的"暂存目录只在锁内用"（REVIEW3:2577）成为决定 5 的"由锁模式决定目录"规则（第四轮 C18） |
| C20 字节检查 | 决定 15 `check_bytes`；§6 (k)。**替换**第二轮"Windows 腿比字节"的指令。**【订正】**rev 4 没把它放进敌对环境用例和钩子层测试（REVIEW3:2670 要求），rev 5 放了 |
| C21 §6 不能跑 | §6 (h) 只在重跑时、(a) 的 `session_build_legs`、(g) 的 win-64 写法；决定 12 第 4 点 `recipe.yaml:106` |
| C22 锁 | 决定 5：Windows 固定偏移 `0x40000000`、接受跨环境串行、忙的文案 |
| C23 pre-unlink 残留 | 决定 9：任何原因都写残留块、永不 "Retry later"；§4 恢复法；决定 15 三例 |
| C24 `.bat` 与副本核对 | 决定 9 写出 `.bat` 文本、`python -I -X utf8 -m`；决定 5 Windows 重试；决定 15 两例在 win-64 跑。**【订正】**rev 4 只写了 post-link 的 `.bat`，pre-unlink 的 `.bat` 仍是"同义"，rev 5 写出；逐字节核对 CI 副本一项随第 33 条删除 |
| C25 共用用户目录 | 第 31 条 (a)：§2.3 恢复后果句；决定 12 第 6 点 |
| C26 README | 决定 10/14 统一文本；§2.3、§9 加 mamba 2.x；决定 13 light README |
| C27 文案 | §4：一个 heap 模板、"has etc/ISABELLE_ID"、先保存改动、`||`/`elif` 的修法、0.x 指向；决定 2 `status` 第一行永远打印树（**不**只在 `-v`）。**【订正】**判决第 (4) 条"经硬链接原地编辑"那一半 rev 4 只写"实测后定稿"，rev 5 在决定 9 与 §4 写定 |
| C28 发布手续 | §5 第 5 步设密钥与 token；§2.3 `PUBLISH_REPOS` 的真实作用；决定 11 `publish` 前提；发布冻结移到 §5 第 0 步。**【订正】**rev 4 给冻结保留了旧理由，rev 5 只给第 11 条 |
| C29 事实 | §2.3：组件钩子不经 `.messages.txt`、第二个缓存构建、`ISABELLE_ID` 不证明原版；§7 行 (7)；决定 17 不再用 2025.2-0 副本。**【订正】**rev 4 仍把 `.messages.txt` 说成 `RELEASE_CHECKLIST.md:259` 的要求、没把它写成本计划的改进，rev 5 改 |
| C30 术语 | 术语表加 build 号、临时目录；"原版树"。**【订正】**rev 4 在 §0 三处仍写"构建号"，rev 5 改成"`isabelle` 包的 build 号" |
| C31 pyproject 名 | 第 32 条；决定 1 |
| C32 `etc/ISABELLE_ID` 门禁 | 决定 16 第 4 点，与决定 3、5 共用常量 |
| judge (a) banner 步骤 | §2.3 核实（commit 晚于最后一次发布）；决定 12 第 5 点；§5 第 6 步 |
| judge (b) `.c~` | 决定 2 只读两种文件、无 `provenance.txt` 视为不存在；决定 15 用例 |
| 第二轮遗留：C17 规则 | 恢复 judge 的规则（见 C8 行）；rev 5 按第 33 条再改为只看链顶 |
| 第二轮遗留：plan:221-222 的 (b2) 句子 | 决定 8 末、决定 17 |
| 第二轮遗留：C9 (2) 附录 A 的矛盾 | **【订正】**rev 4 附录 A 仍说 `isabelle` 包的 post-link 守着"不生成不跟踪的东西"，与它参与例外矛盾、无对照行；rev 5 附录 A 改写（第四轮 C22） |
| 第一轮遗留：C26 共用目录的后果句 | §2.3 |

## 附录 A：写进 `isabelle-packaging-ci/PACKAGING_DESIGN.md` 的一节（文案按第 14、17、20 条由作者定稿，CI 计划落地时写入；节号按当时目录定，不与现有 §10 撞）

```
## 例外（用户 2026-10-23 裁定）：feature 包经 post-link 改写 `$PREFIX/isa`

§3.1 和 §9 的原则——一切随包装进去，post-link 不生成 conda 不跟踪的东西，不原地 patch 用户的 Isabelle——对 `isabelle` 包的**内容**仍然成立：
它从此是原版构建，不带任何补丁。补丁改由 feature 包分发，每个 feature 一个 conda 包（isabelle-expose-foreign、isabelle-light-locale……），
由 isabelle-patch-control 在包的 post-link 里打到 `$PREFIX/isa`、在 pre-unlink 里反打。`isabelle` 包的 post-link 也参与这条例外：它重新执行
直接依赖它的已装包的 post-link。这一步是必要的，因为 `isabelle` 包的 pre-unlink 删掉整个 Isabelle 用户目录、连组件登记一起（recipe.yaml:223-231），
而 conda 只跑本次事务里换了的包的钩子，所以 `--force-reinstall isabelle` 或升构建之后，只有 `isabelle` 自己的 post-link 有机会把 feature 和登记
恢复回来；它用 Python 写（`isabelle` 包因此依赖 python），这是与本文档 :52 "post-link 不做事"原则的偏离，和组件包的 `components -u` 钩子
属同一类。这是对 §9 的一条有意的例外，理由：

1. 用包管理系统管补丁，用户自行决定装哪些补丁：装 isabelle-light-locale 就有 light locale，不装就没有；依赖关系（light 依赖
   future_assign_interrupt 依赖 expose_foreign）由 conda 求解器保证，版本由精确钉死保证，每个 feature 包还精确钉死它所对的 `isabelle` 构建。
2. `isabelle` 包保持原汁原味：可核对的不变量是 Isabelle 的源码与官方发行版相同、etc/ISABELLE_ID 是官方 changeset（89701cf1768e），CI 用断言
   保证。与官方发行版的差别只有打包：etc/settings 的用户目录后缀、etc/options 的 ML_system_64、etc/components 去掉 nunchaku、Windows 的
   bin/isabelle.bat、obj/ 的清理、.conda-keep 标记、CI 编好的 Pure/HOL/Main heap，以及 CI 自己的 build_release 产出与官方 tarball 的差别
   （没有 browser_info 与 Find_Facts 的数据库）——以上列举不保证穷尽，不变量是前一句。
3. 补丁的权威是 Isabelle 源码的 git 仓库（迁移方案），feature 包是从发布 tag 之间的 diff 自动生成的，往返一致由发布门禁保证。

边界与代价：
- 只改渠道自己发的 `$PREFIX/isa` 那棵树。用户自装的 Isabelle 不支持（工具在非 conda 环境里要显式给 feature 目录才运行）。
- feature 新建的文件（light 有三个）conda 不跟踪；它们随 pre-unlink 成功反打而消失，这与组件包用 `isabelle components -x` 注销自己登记的
  做法同类（RELEASE_CHECKLIST.md §4）。pre-unlink 反打不完时留下的改动由钩子当场写进 .messages.txt（文件清单与恢复步骤），status 在包卸掉后
  看不见它们。
- `$PREFIX/isa` 自带的 heap 在打了改 `src/` 的 feature 之后不再匹配，Isabelle 在首次使用时重建到该环境的用户目录；用户接受。
- 工具的每次写树都是逐文件的原子替换，工具自己的命令被中断只留下"部分文件已到新层级"的状态，再跑一次 apply 或 unapply 即完成。conda 事务
  被中断（Ctrl-C）则由 conda 整体回滚：包被撤掉、conda-meta/history 被删、post-link 已写的改动留着；恢复是 `conda create -p <prefix> <要保留的包>`
  （或 `touch conda-meta/history` 后重装），不想要那个 feature 就再 `conda remove` 它。
- `--force-reinstall isabelle` 替换包的每个文件并删掉该环境的用户目录；经硬链接原地写入的编辑连包缓存一起改了，重装恢复不了，工具识别这种情形
  并指引用户先删掉缓存里解开的包目录。
- 钩子一律 exit 0（RELEASE_CHECKLIST.md §4 的规矩不变），exit 0 写在钩子文本里而不是依赖工具。两条契约：post-link 会动 `$PREFIX/isa` 或 Isabelle
  用户目录的包必须直接依赖 `isabelle`；直接依赖 `isabelle` 的包的 post-link 在自己的文件没变时重跑必须无效果——因为 `isabelle` 的 post-link
  会重跑它们。只间接依赖 `isabelle` 的包（isabelle-semantic-data）不被重跑。
- 每发一个新的 `isabelle` 构建，全部 feature 包都要以新的钉死重发（批量发布 workflow 一次跑完）；组件包不钉死构建、不需要重发。
```
