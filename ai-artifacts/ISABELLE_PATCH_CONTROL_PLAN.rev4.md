# 补丁工具改造计划：`my_better_isabelle_prover` → `isabelle_patch_control` —— rev 4（2026-10-24）

> 状态：**rev 4，待第四轮 agent team 评审**（重点：决定 4–7、9、11、12、16；其余是文案与测试）。三轮评审在 `ISABELLE_PATCH_CONTROL_REVIEW1.md`
> （29 条）、`…REVIEW2.md`（26 条）、`…REVIEW3.md`（32 条，judge 判未就绪）；副本 `…PLAN.rev1.md`、`…PLAN.rev2.md`、`…PLAN.rev3.md`。
> rev 4 按第三轮的 32 条裁决、judge 另加的两条发现、用户 2026-10-24 的七条新裁定（§0 第 26–32 条）重写；§10 逐条对照，**凡与评审裁决不同之处
> 都在 §10 明说**（rev 3 的 §10 有八处把替换写成了"已做"，评审查出，本版不再如此）。
> 这是迁移方案 `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md`（下称"迁移方案"）§0 第 19 条划出的两份计划之一；§5.3 定了本工具对外的接口，
> 本计划定内部怎么改。另一份（`isabelle-packaging-ci`）晚些写，决定 12 列出它必须提供的东西。
> 行号针对 `contrib/my_better_isabelle_prover`（工具仓库）、`contrib/isabelle-packaging-ci`（CI 仓库）、本机 conda 25.11.1
> （`~/miniconda3/lib/python3.13/site-packages/conda`），除非另注。事实出处见 §8。

## 术语

沿用迁移方案 glossary 的 **feature**、**链序**、**基 tag**、**发布 tag**、**来历文件**、**patch 文件**；"前 k 节"只剩历史含义（§0 第 11、22 条）。
链：`pristine → expose_foreign → future_assign_interrupt → light_locale → local_type_abbrev → localized_record → local_datatype → dev_patches`。
链的两端叫**链底**（`pristine`）和**链顶**（`dev_patches`）。

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
- **暂存目录**：树旁边、同一文件系统上的目录 `<树的 realpath>.staging`，写树的命令在这里重放（决定 5）。
- **临时目录**：`status` 和 `--dry-run` 重放用的 `tempfile.mkdtemp()` 目录（决定 5）。`git` 只在暂存目录或临时目录里运行。
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
    全部 feature 包重发一遍（版本不变、各包 build 号加一、钉死换新，批量发布 workflow 接 **`isabelle` 构建号**输入）；README 的更新命令是
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
    构建号与各 feature 发布 tag 两组输入，按 tag 检出各 feature 仓库、现场渲染 recipe、把工具包与全部 feature 包构建进一个本地渠道、
    五个平台腿上跑 §6 验收，通过后上传（上传方式由第 27 条修订为只调一次 `publish-conda.yml`）。后果：工具仓库要 `gh secret set` 两个
    R2 密钥、加进 `PUBLISH_REPOS`；GitHub 改名在 workflow 存在之前；feature 仓库自己不需要任何 workflow。作者曾改推荐
    `isabelle-packaging-ci`（密钥已在、构建号同处产生），用户仍选工具仓库。
26. （2026-10-24，第三轮评审 C1 的问题 1）**原版构建的 post-link 重新执行依赖 `isabelle` 的已装包的 post-link**（用户："本质上我们是要重新
    执行后续依赖的 post link 脚本"、"赞同 (d)"），由 CI 计划在 `isabelle` 包里实现；**`isabelle` 包可以依赖 Python**（用户原话），所以这段
    扫描可以用 Python 写。扫描 `conda-meta/*.json` 的 `depends` 找出（含间接）依赖 `isabelle` 的已装包，按依赖拓扑序对每个仍有
    `bin/.<包名>-post-link.sh`（Windows `Scripts\.<包名>-post-link.bat`）的包重跑其 post-link，照 conda 的样子给 `PREFIX`、`PKG_NAME`、
    `PKG_VERSION`、`PKG_BUILDNUM`。这也修好从 `2025.2-0` 第一次升级时丢组件登记那一回（旧构建的 pre-unlink 改不了，新构建的 post-link
    重建）。**不加标记**：依赖 `isabelle` 且环境里有 post-link 脚本的包都重跑（用户曾提议给 feature 包加标记决定是否重跑，作者指出需要重跑的
    是组件包、它们已发布且无标记，用户"赞同你的建议"）；"依赖 `isabelle` 的包的 post-link 必须可重复执行"写进对 CI 计划的要求与
    `RELEASE_CHECKLIST.md` §4。**组件包不精确钉死 `isabelle` 构建**，维持 `isabelle >=2025.2,<2025.3`（用户曾提议所有包都钉死构建，作者
    指出它盖不住 `--force-reinstall isabelle`、要六个组件仓库每次重发、保证的内容又少，用户"好的，赞同你的建议"）；feature 包的精确钉死
    （第 22 条）不变。
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
    rev 3 决定 10 的 `Isabelle2025_2_<isabelle 构建号>_<build 号>` 撤回。build 号从渠道上该包该版本已有的最高号加一推出，跨 `isabelle` 构建
    严格递增（评审 C3）。
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
  标记（`:284-324`）；包里没有官方 tarball 的 `lib/browser_info.db`、`src/Tools/Find_Facts/lib/isabelle.db`（评审核实）。包内自带 Pure/HOL/Main
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
  pre-unlink 非零只记警告，包照样卸（`link.py:1676-1683`）。钩子的 stdin/stdout/stderr 都是管道（`gateways/subprocess.py:83-117`）；
  **conda 在每个脚本跑完后立刻打印并删掉 `$PREFIX/.messages.txt`**（`link.py:1685,1697-1708`），所以钩子之间不能通过它传递任何信息。
  钩子的工作目录是 `$PREFIX/bin`（`link.py:1644-1646`）；每个脚本都拿到 `PREFIX`、`PKG_NAME`、`PKG_VERSION`、`PKG_BUILDNUM`（`:1630-1634`）。
  post-link 在激活的环境里跑，pre-unlink 只把 `$PREFIX/bin`（Windows `Scripts`）加到 PATH 前面（`:1109-1114,1635`）。conda 在跑 post-link
  之前就建好入口点（`:956-959`；Windows 是 `Scripts\<命令>.exe`，`path_actions.py:811-838`）。`conda-meta/history` 与包记录在 post-link
  之后才写（`:969-999`）。**被卸载的文件在 post-link 期间还在**：conda 先把它们改名成 `<路径>.c~`（`path_actions.py:1152-1164`，
  `constants.py:180`），所有 post-link 跑完才删（`link.py:1057-1060`），所以 post-link 看到的 feature 目录里可能有 `*.patch.c~`、
  `provenance.txt.c~`。
- **哪些包跑钩子**：只有本次事务里换了的包（`core/solve.py:1417-1418` 的 `unlink_precs`/`link_precs`）。所以 `conda update isabelle`、
  `conda update --all`、`--force-reinstall isabelle` 都只跑 `isabelle` 自己的钩子；`conda create --clone` 先把未跟踪的文件复制过去、再链接包并跑
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
  `exit 0`/`exit /b 0`。它们失败时的 `echo` 走 stdout、被 conda 丢掉，`.bat` 则不出声——**不经 `.messages.txt`**；经 `.messages.txt` 说话是
  `RELEASE_CHECKLIST.md:259` 的要求和本计划的做法，不是它们今天的行为。渠道的组件包测试清单在 `RELEASE_CHECKLIST.md:630-642`。
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
  10-09 早上的 `release-isabelle-ai`，在该 commit 之前）。按现在的文本，下一次发布会在 `.conda` 上传之后、索引推送之前失败（决定 12 第 9 点）。
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
  `$GIT_DIR/config`，所以 `GIT_DIR=/nonexistent` 不是隔离办法。CRLF 的 patch 文件本身会被 `git apply` 拒绝（rc 1）。
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
  报告。每个 1.x 版本都必须继续接受它们；`isabelle` 包对工具没有版本上界。
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
  `--feature` 给的名字不在 feature 目录里。
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
     `conda update --all`（§4）。工具不内置官方 changeset 表（第 29 条）。`feature` 字段的 `<R>` 必须等于树的发行版名。
  3. 没装任何 feature 包时链只有链底，`status` 打印 `no feature packages installed`、exit 0，不论树是哪个构建（第 29 条）。
- 工具不读 `order.txt`、不读 `categories.toml`、没有 `after`。
- 每个 patch 文件改哪个路径，用决定 4 的原语在一个临时目录里跑 `git apply --numstat --summary <patch 文件>` 读出（新建/删除/权限在 `--summary`
  里），不自己解析头部。**每个 patch 文件必须恰好一个目标**，零个或多个 exit 3 并点名文件；没有任何 `*.patch` 的 feature 目录 exit 3；这一步
  的任何非零退出码都是"patch 文件解析不了"，exit 3 并点名文件。目标等于 `isabelle_patch_control.engine.LOCK_FILE`（`etc/ISABELLE_ID`）的
  feature 一律 exit 3（决定 5 锁的是这个文件；决定 16 在发布时就拒绝）。

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
- 写树的命令（`apply`、`unapply`、`conda-hook`）在**暂存目录** `<realpath(树)>.staging`（`$PREFIX/isa.staging`）里重放：与树同一文件系统
  （`os.replace` 才是原子的；树是符号链接时取 realpath，否则 EXDEV），**不在树里**（残留不会让 `isa/` 留下来），在锁内开始时清空、结束时删掉。
  `status` 和 `--dry-run` 不写前缀下任何东西，在**临时目录**（`tempfile.mkdtemp()`）里重放。目录接口（决定 8）在 `realpath(<目录>)` 旁边的
  一个 per-run `mkdtemp` 里重放、不加锁——这是"工具对树加锁"的一处有意例外，因为目录接口的调用方（门禁、(b2)）自己拥有那个目录。
- 保证：每个文件任何时刻要么整个是旧的、要么整个是新的；工具的一条命令被中断（Ctrl-C 直接发给工具、被杀、磁盘满）后树是"部分文件已到目标
  层级"的状态，下一次 `apply` 或 `unapply` 重算层级后接着做完（决定 7 的逐文件移动天然收敛；评审 C2 的原型在 32 个杀进程位置全部收敛）。
  **这条保证只对工具自己的命令成立**：`conda install` 被 Ctrl-C 中断时，conda 回滚整个事务、可能把工具一起卸掉、删 `conda-meta/history`，而
  post-link 已写进树的改动留着（§2.3）；恢复步骤见 §4（评审 C11 实测收敛）。写失败只会发生在工具自己的目录里（exit 1，树不变）；`os.replace`
  本身失败时重算并打印 `status`。Windows 上 `os.replace`/`os.unlink` 对"被占用"做有限重试（约 7 次、共约 6 秒，和 conda 一样）。
- 锁：对 `树/etc/ISABELLE_ID` 这个**已有**文件加锁，不新建任何文件；路径常量 `isabelle_patch_control.engine.LOCK_FILE`，决定 3 的运行时拒绝和
  决定 16 的发布门禁都用它。POSIX `fcntl.flock`（不是 `lockf`）：`status` 只读打开、`LOCK_SH`；`apply`、`unapply`、`conda-hook` 读写打开、
  `LOCK_EX`（NFS 要可写描述符）。Windows `msvcrt.locking` 锁**固定偏移 `0x40000000` 处的 1 字节**（先 seek 再锁；`flock` 不看偏移）：这个
  偏移任何读到文件末尾的程序都碰不到（rev 3 锁"末尾之后 1 字节"是错的——`cat` 和 Python 的读都会碰到它，`isabelle version -i` 用 `cat`），
  在 Windows 腿上核。不锁目录（NFS 上排他锁坏、Windows 锁不了目录句柄）。等待上限 60 秒，超时 exit 1 报忙；`conda-hook post-link` 把忙和重试
  命令写进 `.messages.txt`、exit 0，`conda-hook pre-unlink` 的处理见决定 9。这个文件的 inode 经包缓存与同机其他环境共享，所以锁也跨环境串行
  ——接受（一次运行持锁 0.2–0.3 秒，评审实测），忙的报文点名被锁的文件并说明可能是别的环境在用。
- `status`、`--dry-run`、`apply`、`unapply`、`apply-to`、`unapply-from` 共用这一条路径：先重放，`status`/`--dry-run` 到此为止，其余接着装。
  所以 `status` 预测的字节就是会装进去的字节，权限位对每个调用者相同。

### 决定 6：状态模型——每个文件的层级

- 链底以上的 feature 按链序编号 1…n。文件 `p` 被其中编号为 `t1 < … < tm` 的 feature 改过（决定 3 末点读出）。`p` **处于层级 L**
  （L ∈ {0, t1, …, tm}）的定义：在 `p` 的一份副本上，把编号 ≤ L 的那些补丁按编号**降序**逐个 `git apply -R`——每成功一个就真的反打到副本上
  再做下一个——全部成功；且在另一份副本上，把编号 > L 的那些补丁按编号**升序**逐个 `git apply`——同样每成功一个就真的打到副本上——全部成功。
  两半都是顺序重放。副本放在暂存目录或临时目录里、保持 `p` 的相对路径。不存在的 `p` 也是一种内容。（rev 3 用 feature 编号去索引"改过 `p` 的
  feature 列表"，两种编号混用，评审 C18 查出；本版层级只用 feature 编号。）
- **同时处于几个层级的文件一律 CONFLICT**（第 28 条），`status`、`apply`、`unapply` 都如此；`status -v` 列出它匹配的层级。按第 28 条的发布门禁，
  正常发布的链上不会出现这种文件；出现就是有人改了树。没有任何层级匹配的文件同样是 CONFLICT。
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
- **每个文件自己的目标层级** T_p = {0, t1, …, tm} 中 ≤ T 的最大者。于是目标 feature 没碰过的文件，T_p 就等于它现在的层级，永不移动
  （rev 3 的"层级 < T 就移"会让全打好的树上 32 个没被碰的文件被白白重写、`--dry-run` 全列出来、heap 提示误发；评审 C18 查出）。
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
  `apply_to(dir, feature_dir)`、`unapply_from(dir, feature_dir)`——返回结果对象或抛异常，从不 `sys.exit`。`_git`、重放、装入都是私有的。
  `make-patches` 的门禁 (c) 调 `apply_to` 再 `unapply_from`（`sys.path.insert(0, TOOLS_DIR.parent)` 从 checkout 导入，不经 PATH、不需要安装，
  决定 16）；(b2) 脚本用命令行（决定 17）。rev 3 写的 `install_files` 不存在，删除。

### 决定 9：conda 钩子

- **钩子片段**，工具仓库 `isabelle_patch_control/hooks/post-link.sh` 与 `post-link.bat` 拥有，渲染器和 CI 计划**逐字复制**，没有 feature 参数。
  `.sh`：
  ```sh
  if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then
    "$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook post-link \
      || echo "isabelle-patch-control: the hook could not run. Run: conda install --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
  elif [ -d "$PREFIX/share/isabelle_patch_control/features.d" ]; then
    echo "isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
  fi
  ```
  `.bat`（CRLF；没有带括号的块、每个 `%PREFIX%` 都在引号里、用 `goto` 标签；`exit /b 0` 结尾）：
  ```bat
  @echo off
  if not exist "%PREFIX%\Scripts\isabelle-patch-control.exe" goto :notool
  "%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook post-link
  if errorlevel 1 echo isabelle-patch-control: the hook could not run. Run: conda install --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
  goto :end
  :notool
  if not exist "%PREFIX%\share\isabelle_patch_control\features.d\" goto :end
  echo isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
  :end
  ```
  每个钩子文件以 `exit 0`/`exit /b 0` 结尾（`.bat` 在 `:end` 之后）。exit 0 于是写在钩子文本里，工具没装、python 坏了、启动即崩都不会让 conda
  回滚（§2.3）。用 `python -I -X utf8 -m` 而不是入口点脚本：`-I` 让调用方的 `PYTHONPATH` 遮不住工具，`-X utf8` 配 `-I` 是 Windows 上必需的；
  `-x` 的存在性检查仍看入口点文件。工具的 conda 包依赖 python，所以 `$PREFIX/bin/python`（`%PREFIX%\python.exe`）一定在。
- feature 包的 pre-unlink（`.sh`；`.bat` 同义，同样无括号块）：
  ```sh
  "$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature> \
    || echo "isabelle-patch-control: could not run the pre-unlink hook of <feature>; files under $PREFIX/isa may still carry its changes. Recovery: conda install --force-reinstall isabelle-patch-control; conda install <包名>; conda remove <包名>" >> "$PREFIX/.messages.txt"
  exit 0
  ```
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
  - 完整诊断（CONFLICT、链接不上、树不是原版构建）**按 `$PKG_NAME` 分配**：只有 `isabelle` 包的钩子（`PKG_NAME=isabelle`）和链顶 feature 的钩子
    写完整诊断；其他钩子见到同样的问题只写一行，点名 feature、文件和 `isabelle-patch-control status -v`。`PKG_NAME` 没设或不认识时按 `isabelle`
    的钩子处理。链还不存在时（例如第一个 feature 包就链接不上）每个钩子都会写一次诊断，接受。
  - pre-unlink 只列**自己这个 feature** 的文件；凡它结束时 F 或其上 feature 的文件还有层级 ≥ k 的——不论原因是 CONFLICT、锁超时、`os.replace`
    失败、工具起不来（后者由钩子文本的 `||` 分支兜住）——都写**残留块**（§4）：文件清单（新建的标出）、这些改动在包卸掉后 `status` 就看不见了、
    恢复步骤。锁超时时层级在不持锁的情况下算（每次写树都是单个 `os.replace`/`os.unlink`，不持锁读是安全的）。pre-unlink **永不写** "Retry later"。
  - 诊断按原因给修法（§4）：用户改过的跟踪文件 → 先保存自己的改动，再 `conda install --force-reinstall isabelle`（替换包的每个文件、删掉该环境
    的用户目录；原版构建的 post-link 随后自动重打 feature、重跑组件登记，第 26 条）——若改动是经硬链接原地写入的，包缓存那份也被改了、重装
    恢复不了，README 写明并给出恢复法（决定 15 实测后定稿）；新建文件内容不同 → 挪开后 `isabelle-patch-control apply`；链接不上 → 更新点名的
    包；锁超时或工具起不来留下的残留 → 让工具能跑（`conda install --force-reinstall isabelle-patch-control`），`conda install <包名>`，再
    `conda remove <包名>`（评审 C23 实测能把残留连新建文件一起反打干净）。
- 原版构建的 post-link（第 13、26 条，CI 计划实现，决定 12 第 2 点）：**同一段钩子片段**，放在它现有的最后一行 `exit 0`/`exit /b 0` 之前
  （`recipe.yaml:208` 处）；之后再重跑依赖 `isabelle` 的已装包的 post-link（第 26 条）。它的 pre-unlink 继续删用户目录。于是 `conda update --all`、
  `--force-reinstall isabelle`、`conda create --clone` 之后补丁和组件登记都自动恢复；留下的新建文件按决定 6 就在它创建者的层级上，不碍事。

### 决定 10：feature 包的配方与渲染器

- 包名由 `isabelle_patch_control.names.package_name(feature)` 给出（`tools/common.py` 导入它；渲染器与 `make-patches` 的路径长度门禁都用它）：
  `isabelle-<feature 名把 _ 换成 ->`（`isabelle-expose-foreign`、`isabelle-future-assign-interrupt`、`isabelle-light-locale`、
  `isabelle-local-type-abbrev`、`isabelle-localized-record`、`isabelle-local-datatype`），唯一的例外条目 `dev_patches → qiyuan-dev-patches`
  （light 计划 D1）。
- 版本 = 发布 tag 里的版本号。build string **`Isabelle2025_2_<该 feature 包的 build 号>`**（第 30 条）；build 号由批量发布 workflow 从渠道上
  该包该版本已有的最高 build 号加一推出（没有就是 0），跨 `isabelle` 构建严格递增。noarch generic。
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

- 工具仓库 `.github/workflows/release-features.yml`，手动触发。输入：`isabelle_build`（原版构建的 build string，必填）；`isabelle_from` =
  `channel` 或 `run:<isabelle-packaging-ci 的 run id>`（后者下载那次运行的 `conda-packages` artifact，断言其 build string 等于 `isabelle_build`
  且不为 0——build 0 的 artifact 会遮住线上的 `2025.2-0`、让 §6 (e) 失真；需要一个对 `isabelle-packaging-ci` 有 `actions:read` 的 token，run
  token 的权限不能放宽，`publish-conda.yml:69-74`）；`tool_ref`（工具仓库的 tag，默认触发的 ref）；`features`（**显式**的发布 tag 列表，
  没有默认值）；`session_build_legs`（允许跑 session 构建的腿，默认空）；`publish`（默认 false）。**没有** `build_number` 输入（由渠道推出）、
  **没有** `roundtrip_checked`（(b2) 是 workflow 里的门禁 job）。
- 固定表 `feature → (GitHub 仓库, 子目录)` 写在 workflow 里；`isabelle-base-features` 的两个 feature 共用一个仓库、不同子目录。
- 作业：
  1. **`build`**（`ubuntu-latest`，唯一取 `rattler-build` 的 job，asset `rattler-build-x86_64-unknown-linux-musl` 0.69.1）：读线上
     `noarch/repodata.json`；已发布的 (名, 版本, build string) **直接下载**进本地渠道、不重建（`publish-conda.yml:179-180` 对字节相同的文件续传）；
     工具包只在 `tool_ref` 的版本未发布时构建；各 feature 的 build 号按决定 10 推出；按 tag 检出各 feature 仓库（私有仓库用一个只读的
     `Contents:read` token）；渲染器生成 recipe；构建进**一个**本地渠道；解开每个 `.conda` 检查钩子齐全、`.bat` 是 CRLF、`.sh` 是 LF、
     `share/<包名>` 字面路径对（`RELEASE_CHECKLIST.md:630-642`，`Isabelle_RPC/release-conda.yml:115-171`）；断言 `isabelle_from` 取到的 `isabelle`
     包的 post-link `.sh` 与 `.bat` **逐字节包含** `hooks/post-link.sh`、`hooks/post-link.bat`；上传**一个** artifact。理由：验收过的字节就是发布的
     字节，和 `build.yml` Job F/G/H 一样（§2.3）。rev 3 把构建放进五条腿是错的：五份不同的字节，Windows 腿的 checkout 还会把 `.patch` 变成 CRLF。
  2. **`roundtrip`**（linux-64，`needs: build`）：装一个环境，对其 `isa/` 的副本跑决定 17 的 (b2)，features.d 由刚构建的包拼出，`git diff-tree` 的
     两个 tag 从树的 `etc/ISABELLE_ID` 与链顶来历文件推出，`isabelle-patched` 用同一个只读 token 做深度 1 的两 tag fetch。
  3. **`accept`**（matrix 五条腿，各自下载同一份 artifact 跑 §6：`ubuntu-latest` linux-64、`ubuntu-24.04-arm` linux-aarch64、`macos-14` osx-arm64
     原生加 osx-64 经 Rosetta、`windows-latest` win-64）。所有环境用 `--override-channels -c file://<本地渠道> -c https://conda.qiyuan.me -c conda-forge`
     （线上渠道没有 python 和 git）。`session_build_legs` 里的腿才跑 §6 (a) 的 session 构建，超时照 `build.yml` 对应 heap job 的（`:498,:583,:677`）。
  4. **`publish`**（`needs: [build, roundtrip, accept]`，仅 `publish=true`）：对那份 artifact **调一次** `xqyww123/isabelle-packaging-ci/.github/workflows/publish-conda.yml@main`
     （第 27 条），显式传 `CONDA_R2_ACCESS_KEY_ID`、`CONDA_R2_SECRET_ACCESS_KEY`，不用 `secrets: inherit`。
  5. **`smoke`**（`needs: publish`；linux-64 与 win-64）：`conda create -n t --override-channels -c https://conda.qiyuan.me -c conda-forge isabelle qiyuan-dev-patches`
     （线上渠道在前，照 `Isabelle_RPC/release-conda.yml:375`），`status` 全 applied、conda 输出里恰一次 heap 提示；runner 是新的，不需要私有包缓存。
- 发布失败只能**重跑同一次运行里失败的 job**，不能重新 dispatch（重建的 `.conda` 带时间戳、字节不同，门禁拒绝；`RELEASE_CHECKLIST.md:564-567`；
  那里的"或 bump build_number"在本 workflow 里不适用，build 号是推出来的）。
- 发布前的手续（§5 第 5 步，按用户命令）：工具仓库进 `PUBLISH_REPOS` 与 `RELEASE_CHECKLIST.md:172` 的清单；设两个 R2 密钥、只读 token、
  `actions:read` token；工具仓库加 `.gitattributes`（`*.sh text eol=lf`、`*.bat -text`、`*.patch -text`，照 `isabelle-packaging-ci/.gitattributes`）。
  `publish=true` 的前提：`release.yml` 已把原版构建发到线上且绿（含审计行）；`PUBLISH_REPOS` 里没有正在跑的发布（用清扫脚本的查询，
  `sweep-old-versions.py:211-229`）。
- 例子，light 的 HOL 侧单独改动（第 21 条末）：light 分支一个 commit → `run-tree … build …`（tested 记录）→ `make-patches light_locale 2` →
  local_type_abbrev 分支 merge light、构建、`make-patches local_type_abbrev 2` → localized_record、local_datatype、dev_patches 同样 → 工作树里
  `git push` 各 feature 仓库与 `isabelle-patched` 的 tag → dispatch `release-features.yml`，`features` 列出七个新 tag（expose_foreign、
  future_assign_interrupt 的 tag 不变，它们已发布、`build` 直接下载），`publish=false` 看五腿，再 `publish=true`。
- 例子，新的 `isabelle` 构建 N+1：CI 发布它之后，dispatch 同一个 workflow，`isabelle_build=N+1`、`features` 不变：工具包已发布、直接下载；八个
  feature 包各自 build 号加一、钉死换成 N+1、重新构建发布。
- feature 仓库自己不需要任何 workflow。rev 2/3 的 `tools/release-feature.yml` 不存在。

### 决定 12：对 `isabelle-packaging-ci` 计划的要求

1. `isabelle` 包是原版构建：CI 不再 `pip install` 工具、不打补丁、不 `hg commit`；`etc/ISABELLE_ID` 等于官方 changeset `89701cf1768e`，并加一道
   断言：打包的树除第 20 条的打包改动、heap 与 §2.3 列的差别外与官方 tarball 相同（`ISABELLE_ID` 等于官方 changeset 本身不能证明原版，§2.3）。
   保留的打包改动：`etc/settings` 的用户目录后缀（按第 31 条加 prefix 完整路径的短 hash）、`etc/options` 的 `ML_system_64=true`、`etc/components`
   删 nunchaku、Windows 的 `bin/isabelle.bat`、CI 编的 Pure/HOL/Main heap。`check_patch_sync.sh`、`MBI_VERSION` 退役。不需要 `run_constraints`、
   不需要 k 文件、不需要树哈希断言。
2. `isabelle` 包的 post-link（`.sh` 与 `.bat`）在现有最后一行 `exit 0`（`recipe.yaml:208`）/`exit /b 0` 之前插入决定 9 的钩子片段（逐字复制，
   批量发布 workflow 会逐字节核对），然后按第 26 条**重跑依赖 `isabelle` 的已装包的 post-link**：`isabelle` 包依赖 python；扫描 `conda-meta/*.json`
   的 `depends`，取（含间接）依赖 `isabelle` 的包，按依赖拓扑序，对每个 `bin/.<包名>-post-link.sh`（Windows `Scripts\.<包名>-post-link.bat`）
   存在的包，在 `$PREFIX/bin` 下以 `PREFIX`、`PKG_NAME`、`PKG_VERSION`、`PKG_BUILDNUM` 环境运行它，忽略其退出码；跳过 `isabelle` 自己。
   pre-unlink 不变（仍删用户目录）。
3. 一次 CI 运行的五个平台腿用同一个 build 号（`build.yml` 今天已是如此），build string 就是 build 号——feature 包按它钉死（第 22 条）。
   `ci.yml` 的非发布 dispatch 接受 `build_number`（今天 `:19-23` 不传），`release.yml` 之后用同一个号发布：批量发布 workflow 要先对那次运行的
   artifact 排练（决定 11 的 `isabelle_from=run:<id>`）。artifact 只保留 7 天，过期重跑。
4. `PACKAGING_DESIGN.md` 加附录 A 的一节，并改写与之矛盾的段落：`PACKAGING_DESIGN.md:20-30`、§7.9（`:876-`）、§7.11（`:940-`）、`:1027`；
   `recipe.yaml:3,6-9,20,253-264`；`recipe.yaml:106` 的 "no untracked files"（Windows 上 cygwin 初始化会写）；`pack.sh` 里把 Pure 称作
   "patched" 的注释；`publish-conda.yml:55` 过时的 `package_name` 说明。
5. **先修 `publish-conda.yml` 的 banner 步骤**（`:223-227`；§2.3）：给它 checkout，或把脚本与 banner 放进 artifact；`grep` 的字串改成 banner
   里真有的。这是 §5 第 6 步发布原版构建的前提。
6. 用户目录后缀加 prefix 完整路径的短 hash（第 31 条）。CI 计划的包测试对两个同 basename 的 prefix 比较 `getenv -b ISABELLE_HOME_USER`。
7. `RELEASE_CHECKLIST.md` §4 加一条：依赖 `isabelle` 的包的 post-link 必须可以重复执行（第 26 条会重跑它们）。
8. 发布说明（新 `isabelle` 包的描述、`isabelle-packaging-ci` README、`isabelle-base-features` README 各一句）：`Foreign`、`RunCall`、`CInterface`
   从此由 `conda install isabelle-expose-foreign` 提供；生态自己的包不需要它，因为 Performant_Isabelle_ML ≥ 0.2.0 自己重绑 `Foreign`（§0 末的更正）。
   第一次从 `2025.2-0` 升级时组件登记会被旧构建的 pre-unlink 删掉、由新构建的 post-link 重建（第 26 条），用户不需要做什么。
9. 可选：让 `publish-conda.yml` 的审计列 R2 而不是本次运行的快照（`:301-318`）。
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
feature 包的 README 也以它开头），内容：依赖剪枝（libmamba 卸顶层包会连带卸掉只作依赖的下层包与工具）、`conda remove --force`、再装一遍已装的
包不会把它记成显式要求的而 `--force-reinstall` 会（代价是反打再重打）、更新命令是 `conda update --all`、只支持 conda（mamba 2.x、micromamba、
pixi 会让卸掉的 feature 的改动留在树里，用 `conda install --force-reinstall isabelle` 恢复）、`conda install` 被 Ctrl-C 中断后的恢复（§4）、
经硬链接原地编辑的恢复。加 "Coming from my-better-isabelle 0.x" 一节，`help` 打印它：新工具看不见 0.x 打的补丁；在 `--category all` 打过的树上
装 feature 包之前先 `my-better-isabelle unpatch --category dev`、再 `pip uninstall my-better-isabelle-prover`；对 conda 的 `isabelle` 永远
不要跑裸的 `unpatch`；弄坏了的树用 `conda install --force-reinstall isabelle` 恢复，原版构建会自动重打 feature；dev 补丁现在是
`qiyuan-dev-patches` 包；pip 用户继续用 0.3.0，新工具只在 conda 里；CONFLICT 报文的最后一行指向这一节。`RELEASE.md` 改写成 conda 发布流程
（决定 11）。Isa-Mini 的四处注释（§2.2）改成指向 `qiyuan-dev-patches`（由 Isa-Mini 的维护者做，本计划只列出）。

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
  - 损坏的 patch 文件 exit 3 并点名；符号链接目标 exit 3；
  - 锁：`status` 在只读树上能跑；两个排他运行串行；锁被占时在上限内报忙；`apply` 后 `unapply`，树的文件集合等于包的文件集合；
  - 目录接口；`--isabelle-home`/`--features-dir` 的推导与拒绝（别的环境的工具加 `--isabelle-home X/isa` 读 X 的 features.d；conda 环境里传
    自装树 exit 3）；
  - `check_bytes`（也用于 §6 (k)）：打完后每个被碰文件的 git blob id（Python 算）以碰它的最高补丁的 `index` 行后像开头；打之前 blob 与最低补丁
    前像不同的文件（打包也改过的，今天是 `etc/options`）除外；卸完后每个被碰文件等于 `conda-meta/isabelle-*.json` `paths_data` 里记的 sha256、
    新建文件不存在。
- **钩子层测试**（`tools/tests/test_conda_hooks.sh`，真 conda，私有 `HOME`、`CONDARC`、`CONDA_PKGS_DIRS`，渠道 `--override-channels
  -c file://<玩具> -c conda-forge`，否则空 `CONDARC` 会落到 `defaults` 报 CondaToSNonInteractiveError）：**feature 包用真渲染器加
  `rattler-build --no-test` 构建**（不用小生成器），只有玩具 `isabelle` 包和"坏工具"包由小生成器造。玩具 `isabelle` 包带一个桩 `isa/bin/isabelle`
  （答 `getenv -b ISABELLE_HOME_USER`、做 `components -u/-x`）、`recipe.yaml:223-231` 的真实 pre-unlink、决定 9 的钩子片段加第 26 条的重跑；
  `ISABELLE_ID` 用真键（原版 `89701cf1768e`、旧构建 `5533cd83156e`），feature 包按决定 10 钉死玩具 `isabelle` 的构建。断言看 conda 的 stdout
  （`.messages.txt` 被 conda 删掉）：
  - post-link 顺序等于链序且幂等；一个事务里恰一条 applied 行、一次 heap 提示；
  - 组件登记：装完 `etc/components` 列出 `share/<包名>`；显式要求 `isabelle` 时 `conda remove <包>` 后文件仍在、不再列它；`--force-reinstall isabelle`
    与 `conda update --all` 后登记仍在（第 26 条）；
  - CONFLICT 的诊断条数按事务形状：只链接顶层 feature（`isabelle` 不在事务里）恰一段完整诊断；两者都链接至多两段；都不在事务里只有一行提示；
    CONFLICT 之下的 feature applied、它与其上的不动、history 在、安装成功；
  - 换 `isabelle` 构建（配套重发的 feature）`conda update --all` 后重打；未配套重发时 `conda update --all` 原地不动、显式装报冲突（`pintest/`
    的形状）；`--force-reinstall isabelle` 重打；`--clone` 的新环境状态相同；
  - 剪枝三例：(i) 下层包都显式要求过，卸顶层只跑它自己的 pre-unlink；(ii) 只显式要求过 `isabelle` 和顶层，卸顶层把只作依赖的下层与工具一并卸掉，
    pre-unlink 从上到下、工具还在时跑，树回到链底；(iii) `conda remove --force <顶层>` 只卸顶层；
  - pre-unlink 残留三例：用户改过文件后卸顶层；锁被占时卸（剪枝形状）；工具起不来时卸——都出残留块、都没有 "Retry later"；按 §4 的恢复步骤
    （`--force-reinstall isabelle`；或让工具能跑、`conda install <包>`、`conda remove <包>`）之后树干净、新建文件消失；
  - 工具启动即崩（替换成坏脚本）与工具不装：安装成功、history 在、报文出现；**两例也在 win-64 上跑**；
  - `conda install` 的进程组在两次文件移动之间收到 SIGINT：history 没了；按 §4 的恢复步骤之后 `status` 全 applied、`conda remove <顶层> --dry-run`
    保留 `isabelle`；
  - 在旧构建（`5533cd83156e`）的环境里 `conda install <feature>`：solver 把玩具 `isabelle` 升到原版构建，链打好，组件登记由新 post-link 重建；
  - 重链接后不修直接 `conda remove isabelle`：没有 `isa/` 残留；post-link 期间 feature 目录里有 `*.c~`：被忽略。
- 验收（§6）在五个平台腿上跑（决定 11），用工具的 conda 包解析到的 `git`（今天 conda-forge 2.56，不是本机的 2.43）；Windows 腿核 `git.exe` 的位置、
  `GIT_CEILING_DIRECTORIES` 与 `core.longpaths`、锁（一个进程持锁时第二个 `status` 在上限内报忙，同时 `type etc\ISABELLE_ID` 与
  `isabelle version -i` 都成功）、只读与被占用目标文件的 `os.replace`、`.bat` 钩子。

### 决定 16：`make-patches` 的配套改动

1. 门禁 (c) 改为 `import` 决定 8 的 `apply_to`、`unapply_from`（`sys.path.insert(0, …)`），对基 tag 的 archive 先打再反打、比树哈希；不再调
   PATH 上的 `patch`。
2. 拒绝没有 `---`/`+++` 对的块（git 对空文件的新建/删除就这样写）：空文件不发布。
3. 拒绝头部权限不是 `100644`/`100755` 的块，包括 `index` 行上的权限：符号链接（`120000`）、gitlink（`160000`）都拦在这里；玩具测试加"新增符号链接"
   与"把文件改成符号链接"两例。
4. 门禁 (f) 另加：被改文件等于 `isabelle_patch_control.engine.LOCK_FILE`（`etc/ISABELLE_ID`）→ 拒绝（决定 3 的运行时 exit 3 是后盾）。
5. **"不撤销下层"门禁**（第 28 条）：任何被改文件在 tip 的 blob id（或"不存在"），若等于它在链底 `<R>/pristine/<ID>` 或任何下层发布 tag 上的
   blob id（或同样不存在），拒绝，点名文件与那个 tag。更强的可选形式：用工具自己的层级函数对链上每种状态核一遍、每个被改文件恰好一个层级。
6. 路径长度门禁：每个 patch 文件在 pkgs 缓存里的完整路径（决定 10 的公式，`package_name` 从 `isabelle_patch_control.names` 导入，取版本 99、
   build 号 99）不超过 198 字符。
7. **feature 仓库侧**：运行前要求 `tools/component_files.txt` 所列文件、`patched_files.txt`、`signature_additions.txt`、`required_sessions.txt`
   在该 feature 仓库里已提交且无改动（不要求整个工作树干净——它是共享的）；全部门禁通过后，在 feature 仓库里按路径提交 `patches/<R>/`、
   创建 Isabelle 仓库的发布 tag、并在 feature 仓库的这个 commit 上创建**同名**的 annotated tag；tip 上已有同一 feature 的发布 tag 时拒绝
   （"先 commit"）。`provenance.txt` 不记 feature 仓库的 commit（文件不能写出包含它自己的 commit）。
8. 所有门禁通过之前不碰包目录：块先写进 (c) 的临时目录，门禁都过了再删旧 `*.patch`、复制新文件、写 `provenance.txt`、提交、打 tag。
9. 玩具测试相应补齐：第 4、5、7 点各有拒绝用例，拒绝后不存在任何新 tag（`hooks/reference-transaction:28-29` 保证 tag 不可动）。`make-patches` 的
   输出格式不变。

### 决定 17：(b2) 脚本

`tools/check-roundtrip <原版树> <链顶 feature> [-C <isabelle-patched 仓库>] <feature 仓库目录…>`：
- 在 umask 022 下，从各 feature 仓库的 `patches/<R>/` 拼出一个 `features.d`；
- 副本 A：`isabelle-patch-control --isabelle-home A --features-dir FD apply`（从 checkout 以 `python -m isabelle_patch_control` 运行），然后
  `status -v`，断言每个新建文件都以真实路径出现；
- 副本 B：`patch -p1 -F0` 打 `git diff-tree -r -p --no-renames <链底 tag> <链顶 tag>`——两个 tag 从 A 的 `etc/ISABELLE_ID`（链底）和链顶来历文件
  的 `release_tag` 推出；GNU patch 没有静默跳过，不可能"什么都没测就通过"；
- `diff -r` 加排序后的 `find -printf '%M %p'` 清单比对 A 与 B；断言 A 与原版不同；对 A 跑 `unapply`，与原版比对。
它既在批量发布 workflow 里作为门禁 job 运行（决定 11，对 CI 发出的字节；`isabelle-patched` 用只读 token 深度 1 fetch 两个 tag），也在本地
按用户命令运行（§5 第 4 步，用本机的 `isabelle-patched` 克隆）。原版树：CI 的原版构建存在之前用官方 tarball
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
2 找不到树、`git` 缺失或版本太旧；3 拒绝——链接不上、feature 目录的基不是这棵树的构建、树里有 `.git`、符号链接目标、patch 文件解析不了或目标
不是恰好一个、feature 目录没有 patch 文件、`--features-dir` 不存在、不在 conda 环境里又没给目录、`--feature` 名字不存在、feature 碰
`etc/ISABELLE_ID`。`conda-hook` 总是 0。

heap 提示（`apply`/`unapply` 真的改了 `src/` 下文件后打印；钩子写进 `.messages.txt`），一个模板：
```
Isabelle sources under $PREFIX/isa changed (applied: light_locale).  [或 (reversed: light_locale)]
The heaps shipped with the isabelle package no longer match them; Isabelle rebuilds Pure and HOL on first use into   [仅当链底以上仍有 feature 打着]
the environment's Isabelle user directory (isabelle getenv -b ISABELLE_HOME_USER), under heaps/ (HOL takes several minutes).
To do it now: isabelle build -b HOL
```
反打回包的原样时第二行换成：`Heaps built earlier in the environment's Isabelle user directory came from the patched sources; Isabelle rebuilds them on first use.`
（不声称包内 heap 又能用了：用户目录里的 heap 先被找到。）

链接不上：`feature chain broken: Isabelle2025-2/light_locale/1 (features.d/light_locale) needs base Isabelle2025-2/future_assign_interrupt/1;
installed: Isabelle2025-2/future_assign_interrupt/2. Update the named package.`
树不是原版构建（有 feature 目录时）：`$PREFIX/isa has etc/ISABELLE_ID 5533cd83156e, but features.d/expose_foreign was made for Isabelle2025-2 pristine
89701cf1768e. Feature packages exist only for the pristine isabelle build. Run: conda update --all`
CONFLICT（完整诊断，`isabelle` 的钩子或链顶 feature 的钩子写）：
```
isabelle-patch-control: light_locale is in CONFLICT in $PREFIX/isa: src/Pure/Isar/locale.ML matches no level of the feature
chain. Features below light_locale are applied; light_locale and the features above it were left untouched.
  First save any edits of your own under $PREFIX/isa: the repair replaces every file of the isabelle package.
  If you edited that file: conda install --force-reinstall isabelle   (restores the package's files, deletes this
  environment's Isabelle user directory; features and component registrations are restored automatically)
  If a file created by a feature has other content: move it aside, then: isabelle-patch-control apply
Details: isabelle-patch-control status -v.  Coming from my-better-isabelle 0.x? See: isabelle-patch-control help
```
其他钩子的一行提示：`isabelle-patch-control: light_locale is in CONFLICT (src/Pure/Isar/locale.ML); see isabelle-patch-control status -v`
pre-unlink 的残留块（任何原因）：
```
isabelle-patch-control: could not fully reverse light_locale before its package was removed [reason: CONFLICT | lock busy | …].
These files under $PREFIX/isa still carry its changes, and status will not see them once the package is gone:
  src/Pure/Isar/locale.ML
  src/Pure/Isar/light_locale_axiom_facts.ML   (created by the feature)
To restore: save your own edits under $PREFIX/isa; then: conda install --force-reinstall isabelle   (restores the package's
files, deletes this environment's Isabelle user directory; the remaining features are re-applied automatically); then delete
the created files listed above.  If the cause was "lock busy" or the tool could not run: conda install <包名>; conda remove <包名>
```
锁忙（post-link 与命令行）：`another isabelle-patch-control run holds the lock on $PREFIX/isa/etc/ISABELLE_ID (its inode may be shared with another
conda environment on this machine); gave up after 60 s. Retry later.`
`conda install` 被 Ctrl-C 中断后（README 与 `status` 在 `conda-meta` 存在而 `conda-meta/history` 不存在时打印）：conda 回滚了整个事务并删掉了
`conda-meta/history`，post-link 已写进 `isa/` 的改动留着；恢复：`touch $PREFIX/conda-meta/history`，然后 `conda install <要保留的全部包和被中断的
那个包>`（或 `conda create -p $PREFIX <同一批包>`）；若不想要那个 feature：`conda install --force-reinstall isabelle`。

## 5. 落地顺序

0. 按用户命令：提交工具仓库里已写好的 `tools/` 与 README 一节（§2.5）；在 `isabelle-packaging-ci/RELEASE.md` 记发布冻结——CI 改成原版构建之前
   不发任何 `isabelle` 构建（第 11 条；理由：feature 包会钉到一个带补丁的构建上，每个 feature 用户都 exit 3）。
1. 工具改造（决定 1–9、14；决定 15 的 pytest）；pytest 全绿。GitHub 改名与 `.gitmodules:41`（决定 1）；卸掉 base 与 `.venv` 里旧的 editable 安装
   （base 是共享环境，先得用户批准；没有东西调 `my-better-isabelle`）。此时 `patches/` 已删、五份 `.md` 已删（第 3 步从第 0 步的 commit 复制），
   旧工具 0.3.0 在 PyPI 上照常。
2. `make-patches` 配套改动（决定 16）与 (b2) 脚本（决定 17）；玩具测试全过；`make-patches pristine` 检查 (a) 仍过。
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
7. 批量发布 workflow 以 `isabelle_from=run:<那次 id>`、`publish=false` 排练：五条腿全绿（§6 不含 (h)）——这是 `.bat` 钩子和 CI 复制的钩子片段
   第一次真跑，发生在任何发布之前。(b2) 在该 artifact 的 `isa/` 上也过了（`roundtrip` job）。
8. 用户下令：CI 的 `release.yml` 以同一个 N 发布原版构建；紧接着批量发布 workflow 以 `isabelle_from=channel`、`publish=true` 一次发布
   （第 16、27 条），它先对线上的原版构建重跑 §6、再发布、再冒烟。发布说明（决定 12 第 8 点）同时就位。各仓库的 `README` 与 `AGENTS.md`
   就位；Isa-Mini 的注释（决定 14）由其维护者改。

## 6. 验收

- pytest 与钩子层测试全绿；`make-patches` 玩具测试全过；(b2) 在官方 tarball 的树（本地）与原版构建的树（`roundtrip` job）上都通过。
- 五个平台腿、本地渠道加线上/artifact 的原版构建加 conda-forge（决定 11），每个场景从新环境开始、所有该留下的包都显式要求过：
  (a) `conda create -n t isabelle=2025.2=<b> isabelle-light-locale` → `status` 全 applied；conda 输出恰一条 applied 行、一次 heap 提示；
  `etc/components` 列出 `share/isabelle-light-locale`；`session_build_legs` 里的腿上，一个 `imports Light_Locale.Light_Locale` 并使用
  `light_locale` 命令的 theory 能通过检查；
  (b) `conda remove isabelle-light-locale` → light 反打干净、新建文件消失、下层 feature 不动、`etc/components` 不再列它；剪枝三例（决定 15）；
  (c) `conda install --force-reinstall isabelle` → post-link 重打、重跑组件钩子：`status` 不变，`etc/components` 仍列出 light 与一个
  Isabelle_RPC 式的组件，conda 输出一次重打记录；
  (d) `conda create --clone` → 新环境 `status` 与原环境相同；
  (e) 在装着 `isabelle-2025.2-0`（线上）加一个组件包的环境里 `conda install isabelle-light-locale` → solver 把 `isabelle` 升到原版构建、链打好、
  组件登记由新 post-link 重建（第 22、26 条）；
  (f) 故意改坏一个跟踪文件后装包 → 安装成功、诊断条数按决定 15 的事务形状、`status` 显示 CONFLICT 与其下 applied、环境仍可用；
  (g) 全部 pre-unlink 成功的前提下 `conda remove isabelle` → 四条 POSIX 腿 `test ! -e "$PREFIX/isa"`；win-64 上断言没有任何 feature 补丁的目标
  路径存在、没有 `isa.staging`、`isa/` 下剩下的都在 `contrib/cygwin/` 之下（这是 `isabelle` 包自己的残留，§2.3）；装与不装 feature 包各一次；
  用户目录不存在；
  (h) 只在为新 `isabelle` 构建重跑时执行：`conda update --all` 把 `isabelle` 和全部 feature 一起升（"未配套重发时原地不动"那一半在钩子层测试里）；
  (i) 只装工具的 `2025.2-0` 环境里 `status` → exit 0、"no feature packages installed"；再放进一个 feature 目录 → exit 3，报文含 `conda update --all`；
  (j) 在一个 git 工作树之下建环境（`conda create -p <仓库>/env …`）→ 结果与 (a) 相同；
  (k) `check_bytes`（决定 15）在 (a) 之后、(b) 与 (g) 之后各跑一次，五条腿都跑。
  中断、锁、权限位、敌对环境、`.c~`、SIGINT 在 pytest 与钩子层测试里覆盖（决定 15），不在真实渠道上重复。

## 7. light 计划 D4 清单逐条

交接清单 `LIGHT_LOCALE_HANDOFF.md:1979` 的 (1)–(19)，括号里是 `reader2_patch_scheme.md` 的发现与决定编号。

| 交接项 | 本计划的回答 | 状态 |
|---|---|---|
| (1) 只更新 `isabelle` 包补丁丢失（发现 2、D3） | 决定 9：原版构建的 post-link 整链重打并重跑依赖者的 post-link；第 22 条：feature 钉死构建 | 用户第 13、22、26 条 |
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
  位置全收敛；真链上逐文件层级重放每次 `status` 1.3–2.3 秒。
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
- 不做 conda 不跟踪的"已打补丁账本"；也不采用"拿 `conda-meta` 的逐文件 sha256 比对 `isa/`"作为状态来源（评审二 C8 的可选项）：状态只从重放得出；
  `paths_data` 只在决定 15 的 `check_bytes` 里作卸载后的校验。
- 不支持一个环境里两棵 Isabelle；不支持自装的 Isabelle2025-2；不支持 mamba 2.x、micromamba、pixi。
- 不改 `make-patches` 的输出格式。
- 不自己实现任何补丁逻辑；不在树里运行 `git`；不在调用方的当前目录运行 `git`。
- 不发 PyPI（第 23 条）。
- 组件包不精确钉死 `isabelle` 构建（第 26 条）。

待用户在发布时定：
- `isabelle-ai` 元包要不要依赖 `isabelle-future-assign-interrupt`（它是每个人都该有的修复，原版构建不带它）。

## 10. rev 3 → rev 4 对照（第三轮评审 32 条、judge 另加两条；**与裁决不同之处明说**）

rev 2 → rev 3 的对照见 `ISABELLE_PATCH_CONTROL_PLAN.rev3.md` §10；其中被第三轮查出不实的八行（C8/C17 规则替换、C20 字节比对、C10 的 CI artifact、
C14 的 build string、C27 的 0.x 指向与树的打印、C15 的私有包缓存、C25 的共用目录句子、C19 的 rev 2 行号）在本表相应行订正。

| 评审 | 本版 |
|---|---|
| C1 组件登记 | 第 26 条 (d)：决定 12 第 2 点重跑依赖者的 post-link；§2.3；决定 9 的修复文案；§6 (c)(e)；决定 15 登记断言。**与 judge 的推荐 (a) 不同**：用户选 (d)，不改 pre-unlink |
| C2 读目标未隔离 | 决定 4 唯一原语；决定 3 恰好一个目标、无 patch 文件 exit 3；决定 15 当前目录敌对用例 |
| C3 重跑无法发布 | 决定 11：已发布的包直接下载、工具只在未发布时构建、build 号从渠道推出、删 `build_number` 输入、只重跑失败 job；§0 第 22 条改"isabelle 构建号输入" |
| C4 tag 无人创建、仓库不存在 | 决定 16 第 7 点；决定 11 固定表与显式 `features`；§5 第 3 步建仓库、push tag；§0 第 21 条末 HOL 侧发布流程 |
| C5 五腿各自构建 | 决定 11 `build` 一次、五腿下载同一 artifact；`.gitattributes` |
| C6 八次调用 | 第 27 条：一次调用。judge 的 (a)，用户同意 |
| C7 多层级规则 | 第 28 条：发布门禁（决定 16 第 5 点）加一律 CONFLICT（决定 6）。judge 的 (a)，用户同意 |
| C8 去重不可能 | 决定 9 按 `$PKG_NAME` 分配诊断（恢复第二轮 C17 判决的规则）；`names.py` 进 Python 包；决定 15 诊断条数 |
| C9 exit 3 矛盾 | 第 29 条 (b)：无 feature exit 0；决定 3 的判据；§6 (i) |
| C10 五腿验收在发布之后 | 决定 11 `isabelle_from=run:<id>`；决定 12 第 3 点；§5 第 6–8 步 |
| C11 中断的事务 | 决定 5 限定收敛声明；§2.3 信号路径；§4 恢复步骤；决定 15 SIGINT 用例；附录 A |
| C12 (b2) 只靠勾选 | 决定 11 `roundtrip` job；决定 17 两个 tag 推出、CI 与本地都跑；删 `roundtrip_checked` |
| C13 钩子层测试不测渲染器 | 决定 15：真渲染器加 rattler-build、桩 `isabelle`、登记断言；决定 11 `build` 解包检查 |
| C14 build string | 第 30 条：撤回，恢复第 27 条原文；§0 第 4 条逐字引用 |
| C15 冒烟无解 | 决定 11：渠道列表加 conda-forge、线上渠道在前；钩子层测试同 |
| C16 附录 A 事实 | 附录 A 第 2 条列非穷尽差别；引 `RELEASE_CHECKLIST.md` §4 而不是 §7.9 |
| C17 128 的解读 | 决定 4 按阶段解读、无 `--check`；§4 退出码 |
| C18 层级索引 | 决定 6 按 feature 编号；决定 7 每个文件自己的目标层级；决定 15 编号与次序不同的用例、全打树 dry-run 为空 |
| C19 API 碎片 | 决定 8 公开 API、`install_files` 删除、门禁 (c) 用 `apply_to`/`unapply_from`；决定 5 重放一次、目录接口的临时目录 |
| C20 字节检查 | 决定 15 `check_bytes`；§6 (k)。**替换**第二轮"Windows 腿比字节"的指令 |
| C21 §6 不能跑 | §6 (h) 只在重跑时、(a) 的 `session_build_legs`、(g) 的 win-64 写法；决定 12 第 4 点 `recipe.yaml:106` |
| C22 锁 | 决定 5：Windows 固定偏移 `0x40000000`、接受跨环境串行、忙的文案 |
| C23 pre-unlink 残留 | 决定 9：任何原因都写残留块、永不 "Retry later"；§4 恢复法；决定 15 三例 |
| C24 `.bat` 与副本核对 | 决定 9 写出 `.bat` 文本、`python -I -X utf8 -m`；决定 11 逐字节核对 CI 的副本；决定 5 Windows 重试；决定 15 两例在 win-64 跑 |
| C25 共用用户目录 | 第 31 条 (a)：§2.3 恢复后果句；决定 12 第 6 点 |
| C26 README | 决定 10/14 统一文本；§2.3、§9 加 mamba 2.x；决定 13 light README |
| C27 文案 | §4：一个 heap 模板、"has etc/ISABELLE_ID"、先保存改动、`||`/`elif` 的修法、0.x 指向；决定 2 `status` 第一行永远打印树（**不**只在 `-v`） |
| C28 发布手续 | §5 第 5 步设密钥与 token；§2.3 `PUBLISH_REPOS` 的真实作用；决定 11 `publish` 前提；发布冻结移到 §5 第 0 步 |
| C29 事实 | §2.3：组件钩子不经 `.messages.txt`、第二个缓存构建、`ISABELLE_ID` 不证明原版；§7 行 (7)；决定 17 不再用 2025.2-0 副本 |
| C30 术语 | 术语表加 build 号、临时目录；全文"build 号"点明所属包；"原版树" |
| C31 pyproject 名 | 第 32 条；决定 1 |
| C32 `etc/ISABELLE_ID` 门禁 | 决定 16 第 4 点，与决定 3、5 共用常量 |
| judge (a) banner 步骤 | §2.3 核实（commit 晚于最后一次发布）；决定 12 第 5 点；§5 第 6 步 |
| judge (b) `.c~` | 决定 2 只读两种文件、无 `provenance.txt` 视为不存在；决定 15 用例 |
| 第二轮遗留：C17 规则 | 恢复 judge 的规则（见 C8 行） |
| 第二轮遗留：plan:221-222 的 (b2) 句子 | 决定 8 末、决定 17 |
| 第一轮遗留：C26 共用目录的后果句 | §2.3 |

## 附录 A：写进 `isabelle-packaging-ci/PACKAGING_DESIGN.md` 的一节（文案按第 14、17、20 条由作者定稿，CI 计划落地时写入；节号按当时目录定，不与现有 §10 撞）

```
## 例外（用户 2026-10-23 裁定）：feature 包经 post-link 改写 `$PREFIX/isa`

§3.1 和 §9 的原则——一切随包装进去，post-link 不生成 conda 不跟踪的东西，不原地 patch 用户的 Isabelle——仍然是 `isabelle` 包自身的原则：
它从此是原版构建，不带任何补丁。补丁改由 feature 包分发，每个 feature 一个 conda 包（isabelle-expose-foreign、isabelle-light-locale……），
由 isabelle-patch-control 在包的 post-link 里打到 `$PREFIX/isa`、在 pre-unlink 里反打；`isabelle` 包自己的 post-link 也调同一段钩子片段，
在换包之后把已装的 feature 重打回去，并重新执行依赖它的已装包的 post-link（组件登记因此在换包后恢复）。这是对 §9 的一条有意的例外，理由：

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
  被中断（Ctrl-C）则由 conda 整体回滚：包被撤掉、conda-meta/history 被删、post-link 已写的改动留着；恢复是 `touch conda-meta/history` 后重装
  要保留的包，或 `--force-reinstall isabelle` 放弃该 feature。
- `--force-reinstall isabelle` 替换包的每个文件并删掉该环境的用户目录；经硬链接原地写入的编辑连包缓存一起改了，重装恢复不了，README 写明。
- 钩子一律 exit 0（RELEASE_CHECKLIST.md §4 的规矩不变），exit 0 写在钩子文本里而不是依赖工具。依赖 `isabelle` 的包的 post-link 必须可重复执行，
  因为 `isabelle` 的 post-link 会重跑它们。
- 每发一个新的 `isabelle` 构建，全部 feature 包都要以新的钉死重发（批量发布 workflow 一次跑完）；组件包不钉死构建、不需要重发。
```
