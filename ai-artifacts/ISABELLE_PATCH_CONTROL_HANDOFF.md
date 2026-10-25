# 交接：补丁工具改造计划（2026-10-24 更新；首版 2026-10-23 compact 前写）

## 现状（2026-10-24，深夜）
- 计划 `ISABELLE_PATCH_CONTROL_PLAN.md` **rev 5**（同目录），副本 `…PLAN.rev1/2/3/4.md`；评审报告 `…REVIEW1–4.md`（29/26/32/24 条），明细
  `…REVIEW{1,2,3,4}_detail.json`。用户 2026-10-24 答了第四轮的三问，记在计划 §0 第 33–35 条（`isabelle` 包不带钩子片段副本；重跑只限直接依赖
  `isabelle` 的包；tested 记录绑 `-d` 目录的仓库状态，迁移方案第 32 条）。rev 5 按第四轮 24 条裁决逐节手改（§10.1 对照、§10.2 订正 rev 4 的八行）。
  **定向重评已完成**（run `wf_573a4702-2df`，16 个 agent；3 个评审员 hooks、release、consistency 共 33 条；合并成 11 条挑战、弃 6 条；judge
  **判就绪**："作者做完下列修改后即可请用户批准，不必再评一轮"）。报告 `…REVIEW5.md`、明细 `…REVIEW5_detail.json`（同目录），judge 逐条指令的
  摘录在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/review5-actions.txt`。11 条里 10 条
  "作者改、不再评"，1 条（C11）要用户定；两个用户问题：问题 1（C11）重跑契约那句话的措辞；问题 2（C4 第 5 项）决定 16 第 5 点的"不撤销下层、每个状态恰一个层级"门禁是否可以比第 28 条多拒一种发布（上下文有歧义的）。
  中文汇报已发给用户（2026-10-24 深夜）。用户答：C11 选 (a) 并允许要求被重跑的 post-link idempotent（§0 第 36 条）；问题 2 的讨论里用户裁定
  **所有 feature 包可信，对 feature 内容的检查只写 release checklist、不写代码，"不要过度设计"**（§0 第 37 条，含原话），并确认迁移方案已有的
  门禁 (a)–(k)、决定 16 第 1、7、8 点、第 35 条保留（"如果已经实现了，而且是没有问题的就不用了"）。**rev 6 已写完**（`…PLAN.md`；`…PLAN.rev5.md`
  是第五轮评审读到的原文，第 36、37 条已从副本里去掉）：按第五轮 11 条裁决逐条改，C6 按第 37 条不做；决定 2、3 删四种针对 feature 内容的拒绝，
  决定 16 第 2–6 点改为第 10 点的 checklist（写进工具仓库 `RELEASE.md`）；§10.1 改为每条 judge 指令一行；迁移方案 glossary、`run-tree` 说明、
  门禁 (e)、规则 11、AGENTS.md 文本加了第 32 条的指针与"构建期间 `-d` 仓库不得动"。用户 2026-10-24 又要求把改过的用户可见文案交给独立 Opus
  reader（medium effort）校读第一印象："一定要考虑这些信息是否是读者需要知道的，读者是否能够理解……别过度复杂，要尽可能简单"——三位 reader 的
  共同意见与改写都已落进计划（决定 9 "文案的写法"一条、§4 五段文案、决定 12 第 8 点、§8、§10.1 末段）。checklist 放工具仓库 `RELEASE.md`
  （用户"可以"）；memory 不写（用户"你写到方案里就好"，已在 §0 第 37 条）。**用户 2026-10-24 最后说："这些文案我没看，也不需要我看，可以继续"；
  "我没看 rev 6 也没法批准，但评审通过后我们就可以开工了"；"建议先 compact 之后开工，请准备"。** 所以 rev 6 没有逐字批准，但评审通过即开工，
  rev 6 就是施工依据。

## §5 第 1 步的进展（2026-10-25 凌晨；用户 2026-10-24 "开工"）
- **新包已写好、未提交、未删任何旧东西**：工具仓库 `isabelle_patch_control/`（`names.py` 决定 10 的包名映射与反函数；`errors.py` 四类异常与
  退出码；`engine.py` 决定 4 的唯一 `git` 原语 `Git.run`（白名单环境、固定 `-c`、`GIT_CEILING_DIRECTORIES`、umask 022）、决定 5 的锁
  `locked()`（`flock` 共享/排他，Windows `msvcrt.locking` 偏移 `0x40000000`，上限 60 s）、暂存目录/临时目录、决定 6 的 `Replayer.levels()`
  （每个候选层级两条顺序重放，副本上真打，`tables[L]` 记下每个层级的内容字节，装入的就是这份快照）、`Replayer.install()`（逐文件
  `os.replace`/`os.unlink`，权限位沿用原文件或取 create/delete 行）；`features.py` 决定 2、3（树、来历文件、按精确 tag 链接、三种链接不上的报文）；
  `model.py` 决定 6、7 的纯逻辑（四种显示状态、hole、`plan()` 的封顶与 T_p）；`api.py` 决定 8 的公开函数 `status/apply/unapply/apply_to/unapply_from`
  （从不 `sys.exit`）；`texts.py` §4 与决定 9 的全部文案逐字；`cli.py` §4 的命令行与退出码；`conda_hook.py` 决定 9 的 post-link/pre-unlink
  （只经 `.messages.txt` 说话、链顶才写完整诊断、残留块四种原因、锁超时后不持锁算层级、链接不上时按该 feature 单独重放算残留、
  决定 9 判"经硬链接原地改写"的唯一一处 `conda-meta` 读取）；`hooks/post-link.sh|.bat`、`hooks/pre-unlink.sh|.bat` 决定 9 的钩子文本逐字
  （pre-unlink 里 `<feature>`、`<package>`、`<version>` 是渲染器要填的占位符；`.bat` 已是 CRLF 字节）；`AGENTS.md -> ../AGENTS.md` 符号链接
  （`help` 打印它，内容等决定 14 的重写）。`pyproject.toml` 只加：第二个入口 `isabelle-patch-control`、新包进 `packages.find` 与 `package-data`、
  `[tool.pytest.ini_options]`（`pythonpath = ["."]`）；**名字与版本没改**（随决定 14 的重写一起，第 32 条）。
- **测试** `tests/`（pytest，87 例，约 2 分 10 秒，其中 14 例是杀进程子进程）：`conftest.py` 的 `Toy` 用一个玩具 git 仓库按 make-patches 的方式
  （`git diff-tree -r -p --no-renames` 按文件切块、扁平名、provenance.txt）造 feature 目录，`git -c tar.umask=022 archive` 造树（否则 git archive
  给 0664/0775，与补丁头部的 0644/0755 不符——第一轮 30 例失败的主因）；夹具自己的 git 不吃敌对环境（去掉 `GIT_*`、`core.attributesFile=/dev/null`）。
  覆盖决定 15 工具层的全部条目：链接规则与各种 exit 3、`--isabelle-home`/`--features-dir` 推导、四种状态、第一轮 C3 五个场景、两例多层级 CONFLICT、
  堆叠上下文在三种树上的 status/apply/unapply/两个 dry-run、两个新建文件加模拟重链接、杀进程后非旧即新并收敛（apply/unapply 各 k=1..7）、
  工具目录写失败树不变、`os.replace` 失败后打印 status、共享 inode 不变、umask 002/077 的权限位、五种敌对环境、锁（只读树、忙、共享、串行、
  不持锁不碰暂存目录）、目录接口、钩子层不用 conda 的部分（假 `$PREFIX`：post-link 幂等只说一次、CONFLICT 链顶整段/其他一行、锁忙、旧构建、
  pre-unlink 成功两种文案、残留块三种原因、硬链接原地改写选包缓存文案）。**真 conda 的钩子层测试、`plan_builds`、`check_bytes` 是第 2、5 步的。**
- **真实链核对**（scratchpad `realchain/`，只读地用源码仓库 `git diff-tree`，分支 expose_foreign f8d760a → future_assign_interrupt 6d8be01 →
  light_locale 577e67d 生成三个 feature 目录；树是官方 tarball 里被碰到的 31 个文件加 `etc/` 两文件，3 个新建文件不在 tarball 里）：fresh 树
  `status` 三条 not-applied 0.18 s；`apply` 后 34 个路径全部等于 light tip 的 blob（`git hash-object` 对 `rev-parse tip:path`）0.19 s；
  `unapply` 后全部回到 pristine blob、新建文件消失、无 `.staging` 残留。
- **作者在方案之外自己定的（都可改）**：(1) `-v`/`-q` 在子命令之后也接受（§4 文案写的是 `isabelle-patch-control status -v`）；(2) `apply-to`/
  `unapply-from` 不查目录里的 `.git`（目录是调用方的）；(3) `apply --feature F` 的 exit 1 只看"挡在 F 以下的 CONFLICT 文件"，`unapply` 只看
  "T 以上的"；(4) 报文里 "applied: X"/"reversed: X" 列的是"自己的文件在本次运行中跨过了 X 的编号"的 feature；(5) 方案没给逐字文案的地方作者按
  "文案的写法"写了：链接不上时"installed: none"、两目录同一 base_tag、发行版不配、patch 文件读不出/目标数不是一、符号链接目标、git 写失败、
  只读树上 `apply`、`--dry-run` 与 `-v` 的逐文件行 `  <path>  level a -> b`、`CONFLICT  <path>  no level|levels 0, 2`、§4 "conda install 被 Ctrl-C
  中断后"那段 `status` 在 `conda-meta` 存在而 `history` 不存在时打印的话（`texts.interrupted`）——这些没经 reader 校读。
- **下一步**：§5 第 2 步（决定 16：门禁 (c) 改 `import` `apply_to/unapply_from`、第 7–8 点写入顺序、第 9 点玩具测试、第 10 点 checklist 进
  `RELEASE.md`；`tools/common.py` 从 `isabelle_patch_control.names` 导入 `package_name`、加 `plan_builds`；`run-tree` 的 `-d` 行；决定 17 `check-roundtrip`）。
  旧包、`patches/`、五份 `.md` 的删除与 README/reference/develop/AGENTS/RELEASE 重写、pyproject 改名仍等之后（第 0 步 commit 已存在，可以开始）。
  提交只在用户说"提交"时做：新增 `isabelle_patch_control/`（15 个文件）与 `tests/`（9 个文件），改动 `pyproject.toml` 与本交接。

## compact 之后怎么开工（2026-10-24 深夜写）
1. **§5 第 0 步已完成**（用户 2026-10-24 "批准提交"）：工具仓库 `main` 上 7336934（`tools/` 与 README 一节，README 的 tested 一条补了第 35 条
   的一句）、113a28f（`ai-artifacts/`：计划、副本、五轮评审、交接）；CI 仓库 `main` 上 2c5901d（`RELEASE.md` 发布冻结）。**未 push**（push 只按
   用户命令）；主仓库里两个 submodule 指针变了、**未 bump**（用户没说）。
2. **§5 第 1 步（工具改造）可以立刻动手**，不等第 0 步，但**先只加不删**：在工具仓库里新建 Python 包 `isabelle_patch_control/`（决定 1：`names.py`
   放包名映射；决定 4：`_git` 唯一原语与白名单环境；决定 2、3：定位树、读来历文件、按精确 tag 链接、`git apply --numstat --summary` 读目标；
   决定 5：暂存目录/临时目录按锁模式、`flock` 锁 `etc/ISABELLE_ID`、逐文件 `os.replace`；决定 6、7：层级与 `apply`/`unapply`/`--dry-run`；
   决定 8：`apply_to`/`unapply_from` 与 CLI；决定 9：`conda-hook post-link`/`pre-unlink` 与 `hooks/post-link.sh`、`post-link.bat` 文本——
   文本逐字取计划决定 9 与 §4；§4 的退出码表）和 `tests/`（决定 15 的 pytest：玩具树、玩具 features.d，不需要 Isabelle，**不跑 `isabelle build`**）。
   旧包 `my_better_isabelle_prover/`、`patches/`、`categories.toml`、五份 `.md` 的删除与 README/reference/develop/AGENTS/RELEASE 的重写
   （决定 14；RELEASE.md 含决定 16 第 10 点的 checklist）要等第 0 步的 commit 存在之后再做（§5 第 3 步要从那个 commit 复制 `.md`）。
   pyproject 改名 `isabelle-patch-control`（第 32 条）随重写一起。
3. 需要用户下令的外部动作：GitHub 仓库改名与主仓库 `.gitmodules:41`（决定 1）；卸掉 base 与 `.venv` 里旧的 editable 安装（base 是共享环境）；
   §5 第 3 步建三个 GitHub 仓库；`make-patches`（light 的请求仍按 `expose_foreign 1 → future_assign_interrupt 1 → light_locale <v>` 等用户命令）。
4. 之后：§5 第 2 步（决定 16 第 1、7–10 点、`run-tree` 的 `-d` 行、决定 17、`test_trees.sh` 两例、迁移方案五处已改）、第 3 步起每步等用户下令。
5. 代码写法：复用已有代码（`tools/common.py`、`make-patches`、`run-tree`）、不复制粘贴；注释短；优雅与正确同权重；每个改动跑 pytest 看结果再说做完了。
6. 开工时的现场（2026-10-24 深夜核实）：工具仓库 `main` 在 113a28f，工作树只有 `ai-artifacts/…HANDOFF.md` 一处未提交改动。旧代码：
   `my_better_isabelle_prover/{cli.py 181 行, patcher.py 169 行, isabelle.py 68 行, patches/}`，`pyproject.toml` `[project] name = "my-better-isabelle-prover"`
   `version = "0.3.0"`，`[project.scripts]` 在 :33。新代码放新包 `isabelle_patch_control/`，旧包先不动。可直接复用的已有东西：`tools/common.py`（244 行：
   仓库/tag/来历相关的辅助函数，`make-patches`、`run-tree` 都用它——决定 10 的 `plan_builds`、`package_name` 要放进去或从 `isabelle_patch_control.names`
   导入）。`_git` 原语的隔离要点与实测都在计划决定 4 与 §2.4（`GIT_CEILING_DIRECTORIES`、`GIT_CONFIG_NOSYSTEM`、`GIT_CONFIG_GLOBAL=/dev/null`、
   `GIT_ATTR_NOSYSTEM`、`-c core.autocrlf=false -c core.attributesFile=/dev/null`、`LC_ALL=C`、umask 022），复现脚本在 scratchpad `verify2/`、`gittest/`。
   用户可见文案逐字取计划 §4 与决定 9（已经 reader 校读，不再自己改措辞）。先读计划 §3 决定 1–9 与决定 15 再动手；§4 是 CLI 与退出码的权威。
  注意：`…PLAN.rev4.md` 是在加了 §0 第 33–35 条之后才复制的，不是第四轮评审看到的原文（judge C4 第 9 项要在 rev 6 头部注明：REVIEW4 引用的
  plan:N 在 N≥140 时对应副本的 N+15 行）。
- light 会话 2026-10-24 请求跑 `make-patches light_locale`：作者核对三道前提——基 tag 不存在（先要 `isabelle-base-features` 仓库与
  `make-patches expose_foreign 1`、`future_assign_interrupt 1`）、577e67d 的 tested 记录（light 随后补齐）、计划未批——已回复 light 并向用户请示，
  建议等计划批准、按 §5 第 1–3 步做完工具改造再跑；**用户 2026-10-24 定："好的，继续等"**——`make-patches` 等计划批准后按
  `expose_foreign 1 → future_assign_interrupt 1 → light_locale <v>` 的顺序、按用户命令跑；light 的 tested 记录（577e67d）已就位，不受阻。
  下一步概要：等 `w3heqfdog` 完成 → 渲染 REVIEW5、中文汇报 → judge 判就绪则请用户批准计划 → §5 第 0 步（提交 `tools/`、在
  `isabelle-packaging-ci/RELEASE.md` 记发布冻结，都要用户下令）→ 第 1 步工具改造（决定 1–9、14、15 的 pytest）。所有会话规则不变（不跑
  `isabelle build`、不 commit 除非用户说"提交"、计划文档只手改、不写 memory、评审用 Workflow+Opus+xhigh）。
- 以下是 2026-10-24 晚的记录。
- 计划 rev 4 时的状态：副本 `…PLAN.rev1/2/3.md`；评审报告 `…REVIEW1.md`（29 条）、`…REVIEW2.md`（26 条）、
  `…REVIEW3.md`（32 条，judge 判未就绪），明细 `…REVIEW{1,2,3}_detail.json`。
- 用户 2026-10-24 答了第三轮的七个问题，记在计划 §0 第 26–32 条：原版构建的 post-link 重跑依赖 `isabelle` 的包的 post-link、不加标记、组件包不钉死
  构建、`isabelle` 包可依赖 Python（26）；只调一次 `publish-conda.yml`（27）；上层不得撤销下层、make-patches 门禁（28）；无 feature 时 exit 0（29）；
  build string 恢复 `Isabelle2025_2_<n>`（30）；用户目录后缀加 hash（31）；pyproject 名 `isabelle-patch-control`（32）。
- **第四轮评审已完成（2026-10-24 晚）**：judge 判 rev 4 未就绪但"接近"（24 条：11 major、13 minor；3 条要用户定——C3 `isabelle` 包里的钩子片段副本
  是否删掉、C4 重跑范围只限直接依赖、C10 tested 记录要不要绑 light 仓库状态；3 条作者改后重评——C2 复用键、C5 强门禁、C6 artifact 只含 noarch；
  18 条作者改不重评）。judge 建议改完后做**针对决定 9、11、12、16 与 §10 各行的定向重评**，不必整轮。报告 `…REVIEW4.md`、明细 `…REVIEW4_detail.json`。
  作者又说错两处（评审查出）：对用户说"重跑集合今天恰好是组件包和 feature 包"（漏了间接依赖 `isabelle-semantic-data`，其 post-link 会清用户向量缓存）；
  §0 第 26 条把 "很好" 与 "好的，赞同你的建议" 两句归错了问题。**等用户答三问后出 rev 5、定向重评。**
- rev 4 按三轮 32 条裁决与 judge 两条额外发现重写；§10 对照表明说每处偏离。第四轮评审 workflow：任务 `wnflmh4ej`，
  run `wf_9531e1ef-1d3`，脚本 `~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/workflows/scripts/patch-tool-plan-review-4-wf_9531e1ef-1d3.js`，
  结果在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/wnflmh4ej.output`（JSON 包装同前）。处理方式同前三轮：
  存 `…REVIEW4_detail.json`、渲染 `…REVIEW4.md`（渲染脚本写法见本会话第二/三轮）、中文汇报、用户同意前不改代码；judge 判就绪则请用户批准、
  然后按 §5 落地（第 0 步按用户命令提交 `tools/` 并在 `isabelle-packaging-ci/RELEASE.md` 记发布冻结）；未就绪则 rev 5。
  中途暂停：`Workflow({scriptPath: <脚本>, resumeFromRunId: 'wf_9531e1ef-1d3'})`。
- 以下是 2026-10-24 白天的记录。
- 用户 2026-10-23/24 答了第二轮的六个问题，全部记在计划 §0 第 20–25 条（pack.sh 三处打包改动保留；light 补丁与 HOL session 同一个包、模板加
  可选组件载荷；**feature 包精确钉死 `isabelle` 构建**，`LEGACY_BUILDS`/决定 10 删除；只发 conda；暂存目录加原子改名；批量发布 workflow 放工具
  仓库 `.github/workflows/`）。迁移方案 §0 加了第 31 条、第 30 条"post-link"改成两个钩子。
- **第三轮评审已完成（2026-10-24）**：judge 判 rev 3 未就绪（32 条 challenge：13 major、18 minor、C1 由 blocking 降为 major；5 条要用户定、
  10 条作者改后重评、17 条作者改不重评；7 个用户问题 Q1–Q7；judge 另加两条发现：`publish-conda.yml` 的 banner 步骤无 checkout 且 grep 的字串
  不存在、会让下一次发布在上传之后失败——作者核实 banner commit 85dc11b 晚于最后一次成功发布；conda 在 post-link 期间把被卸文件留成 `*.c~`）。
  报告 `ISABELLE_PATCH_CONTROL_REVIEW3.md`、明细 `…REVIEW3_detail.json`。已用中文汇报，**等用户答 Q1–Q7 后出 rev 4、第四轮重评决定 4–7、9、11、12、16**。
  作者在 rev 3 里自己犯的错（评审查出）：`.messages.txt` 去重不可能（conda 每个脚本后打印并删文件）；`--numstat --summary` 没走隔离；
  五条腿各自构建 noarch 包；八次 `publish-conda.yml` 调用其实一次全发；"多层级取相同结果"规则不成立；`install_files` 没定义；`.bat` 片段没写；
  build string 改动没有裁定；§10 若干"已做"不实。
- 第三轮评审 workflow：任务 `w020jayvs`，run `wf_130068f2-2bb`，脚本
  `~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/workflows/scripts/patch-tool-plan-review-3-wf_130068f2-2bb.js`，
  结果在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/w020jayvs.output`（JSON 包装同第二轮）。
  处理方式同前：读 `wrapper['result']`，存 `ISABELLE_PATCH_CONTROL_REVIEW3_detail.json`，渲染 `ISABELLE_PATCH_CONTROL_REVIEW3.md`（渲染脚本的
  写法见第二轮：每条 challenge 的 statement、editor、relaxation、defender、judge），用中文向用户汇报全部 concern、改法、要用户定的问题；
  **用户同意前不改代码**。judge 判未就绪则出 rev 4 再评审；就绪则请用户批准，然后按 §5 落地（第 0 步是按用户命令提交 `tools/`）。
  若 workflow 中途暂停：`Workflow({scriptPath: <上面的脚本>, resumeFromRunId: 'wf_130068f2-2bb'})`。
- 作者 2026-10-24 自己复现的实验：scratchpad `verify2/`（嵌套仓库里 `git apply` 静默跳过；strace 先 unlink 后创建）、`pintest/`（精确钉死
  `isabelle` 构建时的 solver 行为）。
- 下面是 2026-10-23 的记录，留作查阅。
- 第二轮评审 workflow：任务 `w3hual9ef`，run `wf_53ea674b-1cc`，脚本
  `~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/workflows/scripts/patch-tool-plan-review-2-wf_53ea674b-1cc.js`。
  完成后结果在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/w3hual9ef.output`：是一个 JSON 包装
  （键 `summary`、`agentCount`、`logs`、`result`、`totalTokens`），`result` 里有 `findings`、`overalls`、`merged`（`challenges`、`dropped`）、
  `defenses`、`judgement`（`ready`、`summary`、`per_challenge`、`questions_for_owner`、`relaxations_recommended`）。
  处理方式与第一轮相同：用 python 读 `wrapper['result']`，存成 `ISABELLE_PATCH_CONTROL_REVIEW2_detail.json`，渲染
  `ISABELLE_PATCH_CONTROL_REVIEW2.md`（每条 challenge：statement、editor_rebuttal、relaxation、defender verdict/reasoning/fix、judge verdict/route），
  然后用中文向用户汇报：所有 concern、我打算怎么改、哪些要用户定；用户同意前不改代码。若 judge 判未就绪则出 rev 3 再评审；若就绪则请用户批准。
- 若 workflow 中途因配额暂停：`Workflow({scriptPath: <上面的脚本>, resumeFromRunId: 'wf_53ea674b-1cc'})`，必须重用已有结果。

## 用户 2026-10-23 的裁定（全部已写进计划 §0 第 11–19 条与迁移方案 §0 第 30 条）
conda `isabelle` 包是原版（k=0），再发一个原版构建，CI 改好之前不发任何 `isabelle` 构建；引擎 `git apply`（用户反对自写引擎，要走已有库；
`patch-ng`、`whatthepatch`、`pygit2` 都实测不够）；钩子一律 exit 0、经 `.messages.txt` 报告；新 `isabelle` 构建的 post-link 在装了工具时
重打已装 feature；`PACKAGING_DESIGN.md` 记例外并详细论证（理由：包管理系统管补丁、用户自选、`isabelle` 原汁原味）；Isabelle2024 留旧工具不考虑；
三个 feature 本周就绪、所有包一次发布；全平台（Windows 的 conda-forge `git` 是自带 MSYS2 的 PortableGit，121 MB）；自装 Isabelle 不支持；
文案与测试在不改设计的前提下作者自决。

## 迁移（另一条线）的状态
迁移方案 §6 第 0–3、5、6 步完成，第 4 步的 `make-patches expose_foreign 1` 等等本计划落地（需要 `isabelle-base-features` 仓库与引擎接入）。
记录在 `ai-artifacts/isabelle-git-migration/RECORD.md`。staging 仓库 `contrib/Isabelle2025-2-staging` 留到第 4 步后删。
light 的第 5 步部分已完成（等提交）；local_type_abbrev、local_datatype 的计划已按 §8 改；record 未回报。

## 用户的常备规则（不变）
不 `git stash/checkout/reset --hard/clean`；只在用户说"提交"时 commit（主仓库 `main`，trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`）；
不开 PR；不写 memory 目录；**不跑 `isabelle build`**（含子 agent）；子 agent 用 Opus、评审 `effort: 'xhigh'`、必须用 Workflow；计划文档只手改；
解释先讲本质再讲机制、不造词、不假定用户记得前文；提问要把背景讲清楚。
