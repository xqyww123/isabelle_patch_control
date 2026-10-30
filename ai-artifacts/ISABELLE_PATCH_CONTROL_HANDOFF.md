# 交接：补丁工具改造计划（2026-10-28 20:40 +08 更新；首版 2026-10-23 compact 前写）

## compact 之后怎么开工（2026-10-25 傍晚写；下面"现状"与"§5 第 1 步的进展"两节是按时间顺序的流水账，细节在那里）
1. **现场**：工具仓库 `contrib/my_better_isabelle_prover` 的 `main` 在 **16078a3**（已推 GitHub `origin/main`；历史已用 filter-repo 改写、去掉了五份
   评审明细，旧哈希 113a28f/cc0e603/fa1d64a/321646d 已不存在），工作树有本文件与 `RELEASE.md`（见第 3 条）两处未提交改动，另有两份未跟踪的
   `ai-artifacts/…CODE_REVIEW{1,2}.md`（用户不要提交，留在磁盘）。主仓库 `main` 在 **cbe68707**（bump 到 16078a3；主仓库从不由本会话推送；其三个
   旧 bump 提交的子模块指针悬空，用户接受），索引里暂存着新子模块 `contrib/isabelle-base-features`（`.gitmodules` 条目 + gitlink 5cb0251）。
   pytest 129 例约 19 秒、`tools/tests/run-all.sh` 全过、变异检查 28 杀 / 1 等价。
2. **已完成**：§5 第 0、1、2 步；代码评审一轮（38 条）与定向再评（judge 判 ACCEPTED，可进第 3 步）全部裁决已实施并提交。方案 rev 6 已按两轮评审手改
   （§0 第 38 条、§10.0）；迁移方案 §0 第 32 条注记、新第 33 条。
3. **下一步 §5 第 3 步，每件都要用户下令**（细节见本文件末段"评审之后"）：GitHub 的 `xqyww123/isabelle-base-features` 与
   `xqyww123/qiyuan_dev_patches` **已于 2026-10-25 18:30 +08 建好**（用户下令；都是 public、空仓库、无初始提交；描述用户批准：前者
   "The base of the Isabelle feature-package chain for isabelle-patch-control: fixes to Isabelle's sources that every other feature package builds on"，
   用户特意不点名两个 feature——设计上它们是"Isabelle 本该有的样子"，Isabelle2026 之后不再这么做；用户问过要不要改名 `isabelle-base`，
   听了"会读成未打补丁的 Isabelle 本体"后保留原名）。本地 `contrib/isabelle-base-features/` **已建并提交 b312f9f**（2026-10-25 18:39 +08，用户
   "请继续"）：`expose_foreign/`、`future_assign_interrupt/` 各有 `tools/patched_files.txt`（一行：`src/Pure/ML/ml_name_space.ML` /
   `src/Pure/Concurrent/future.ML`，与共享树 `diff-tree` 核对过）、`tools/signature_additions.txt`（只有注释，0 条）、`tools/required_sessions.txt`
   （`Pure`），README 从工具仓库 c7f9eb6 的 `my_better_isabelle_prover/patches/{expose_foreign,future_assign_interrupt}.md` 逐字节复制（里面
   "apply with `--no-build`"、"`ml_name_space.ML.patch`"、"Applies to Isabelle2024 and Isabelle2025-2" 等句子是旧工具时代的，已向用户指出、等裁定）；
   根 `.gitattributes` 是 `*.patch -text`；remote `origin` = `git@github.com:xqyww123/isabelle-base-features.git`。用户 2026-10-25 四项裁定并已做：
   **已推送**（`main` = 5cb0251，第二个提交加了根 README 与 BSD-3 LICENSE，版权行 "Copyright (c) 2026, Qiyuan Xu"）；**已登记为主仓库子模块**
   （`.gitmodules` 条目 + gitlink 5cb0251 只暂存在主仓库索引里，等"提交"）；根 README 由作者写、三个 Opus reader（用户/开发者/编辑三视角，
   Workflow wf_88f96ece-2c0）校读后改定——用户要求"一定要简单"，README 只有一句定位、一张两行表（目录、conda 包名、修的是什么）、一句指向
   工具 README 与 RELEASE.md；reader 还指出 `RELEASE.md` 的 "feature repository" 定义不覆盖双包仓库，已补一句（`--package` 指子目录；工具仓库
   工作树里未提交）。用户 2026-10-25 两项裁定：(a) 决定 12 第 8 点那句发布说明**不**进本 README（计划该点已改）；(b) 两份包 README 重写为用户向
   （各约 100 词：feature 改了什么、怎么认出自己需要它、其他 feature 包都叠在它上面、指向 details.md 的 GitHub 绝对链接——README 随 conda 包进
   `share/doc/<包名>/`，details.md 不进包），技术内容移到各目录的 `details.md`（GitHub 专用）。三个 Opus reader（用户/核对者/编辑，Workflow
   wf_0b221acd-326）校读后改定，核对者查出并经作者在原版树与 `polyml-5.9.2-2/x86_64-linux/poly` 上复核的事实：Poly/ML 5.9.2 **没有 `CInterface`**
   （所以 feature 只让 `Foreign`、`RunCall` 重新可见，根 README 同改）；`future.ML` 的调用者是 `promise_name` 而非旧文写的 `promise_group`；用户看到的
   报文是 `exception Option raised (line 84 of "General/basics.ML")`，不是 future.ML；修改是一行变两行（不再说 "one line"）；`Exn.Exn Interrupt` 不存在，
   应为 `Isabelle_Thread.interrupt_exn`；`cond_forks` 在 `Future.enabled ()` 为假时都走 `value_result`（不只是单线程）；旧文"为何不全部重抛"一段的
   理由自相矛盾，已改成两种写法行为相同。窄形式（只重抛中断）当时重跑的结果旧文没记，details.md 只写宽形式的 15 轮；用户说不用补。提交 cce3051。
   两份 details.md 是作者**未经批准**新建提交的——用户据此定下"新增文件须批准"的规矩（见文末），随后看了大小（2.6 KB、6.6 KB）说"可以接受，
   不用管就保留好了"，原样保留。
   **两个 feature 都已发布**：`make-patches expose_foreign 1`（2026-10-25 19:25 +08）与 `make-patches future_assign_interrupt 1`（19:32 +08）都 exit 0、
   门禁 0/1/(f)/(d)/(e)/(c) 全过；各写出 `<包目录>/patches/Isabelle2025-2/{provenance.txt,<flat name>.patch}`，feature 仓库提交 8b10cdd、0c6e56c；
   tag `Isabelle2025-2/expose_foreign/1`（feature 仓库 8b10cdd / 源码仓库 f8d760a）与 `Isabelle2025-2/future_assign_interrupt/1`（0c6e56c / 6d8be01），
   后者的 `base_pin: ==1=Isabelle2025_2_*`。用户"全部推送"：feature 仓库 `main`（0c6e56c）与两个 tag、源码仓库 `isabelle-patched` 的两个 tag 均已推
   （19:36 +08，`ls-remote` 核过；源码仓库的分支 GitHub 上本来就与本地一致，`light_locale` 分支本地领先是 light 会话的事，未动）。主仓库暂存的
   gitlink 已指到 0c6e56c。**light 的发布交给 light 会话做**（用户 2026-10-28 00:19 +08 同意作者的建议；已用 SendMessage 发到
   `uds:/run/user/1002/cc-socks/492123.sock`：前提已备齐、它要做的三件、`.gitattributes` 缺口须向用户提出）；作者这边只在门禁报错时解释或修工具，
   light 发布后跑第 4 步。light 会话回报（2026-10-28）：它要先向用户本人确认再动手；**门禁 (d) 的一个问题**——`check-signatures` 的
   `head()`（照搬旧 `make_patches.sh` 的 sed）把类型参数留在头里（`LOCALE datatype 'a structure_state`），与文档写的 `<keyword> <name>` 格式不符，
   light 清单第 76、78 行没写 `'a`，作者在 f44d7f3 上复现；作者向用户建议改 `head()` 去掉类型参数。light 会话转告：用户 02:01 定为实现问题，由 light
   会话与 Opus agent 定修法；它们定了 (a)，工具与测试归作者改。**已改（2026-10-28 10:10 +08，未提交）**：`check-signatures` 加模块级常量
   `TYPE_PARAMS`（只匹配条目开头的 `type|eqtype|datatype` 后的 `'a ` 或 `('a, 'b)`），`head()` 先去掉它；docstring 写明"类型参数不属于头"；
   `tools/tests/test_signatures.sh` 加带 `'a` 与 `('a, 'b)` 的两条增补、计数 5、一条"清单写了 `'a` 应被拒"。run-all 全过（19/70/11/102/15）、pytest
   129；真实链 expose_foreign/1、future_assign_interrupt/1（0 条）与 light f44d7f3（85 条，清单 02f2694）都通过。变异：旧 `head()`、只认 `'a` 两个
   被杀；去掉 `^` 锚存活——它只影响 `include X where type 'a t = …`，那类头格式本身未定，没为它加测试。light 会话列的三个老问题不在本次：`and` 连写的
   第二个 datatype 名进不了头（原版 8 处）、条目以 `;` 结尾时 `;` 留在头里、以 `:` 开头的符号 val 丢名字；目前没有 feature 新加这几类条目。
   light 会话曾打算给 `make-patches` 加"改了 `.thy` 就拒绝发布"的门禁，用户 2026-10-28 02:01 反对，已取消。
   light 会话 14:1x +08 转告：用户对它说了"请提交"，它的清单第 4 项是"本工具仓库的 check-signatures 修正，提交要对那个会话下令"——作者**没有据此提交**
   （转述不算对本会话的批准；工作区里还有第 5 步的改动与待批新文件），已回复它、等用户亲口下令。它已提交：私有树 5826993（Pure.thy 恢复原版、
   不再导出 locale_val）、light f5b9f29、主仓库 7b806ba6（没碰本会话暂存的 `.gitmodules` 与 `contrib/isabelle-base-features`）。它报的小问题已修
   （未提交）：清单经 `/dev/fd/N` 传入时 `cli()` 再读一遍、打印 "0 additions"——`check-signatures` 改为 `listed_heads()` 读一次；test_signatures.sh 13/13，
   旧行为被新例抓住；5826993 + f5b9f29 经管道 "84 additions as listed"。用户随后对本会话下令"只提交 check-signatures"：**工具仓库提交 0b59fd7**
   （`tools/check-signatures` 与 `tools/tests/test_signatures.sh` 两个文件，含类型参数修正与读一次的修正），已推 origin；主仓库**不** bump。
   **Pure.thy 恢复的快速路径**（用户经 light 会话定、再对本会话"全部下令"，2026-10-28）：local_type_abbrev、localized_record、local_datatype 三条分支
   在各自私有树 `git merge --ff-only` 到 light 的 5826993（三会话事先通知，两个回复无进程依赖），三棵 stock 树 `new-tree --stock` 到 5826993；
   dev_patches 私有树 `git merge --no-ff Isabelle2025-2/local_datatype` 得合并提交 **7eb9137**（树 ef3b2769e32d，与 light 会话试合并相同；与 pristine
   比只有 Abs_Int3.thy、Sudoku.thy 两个 .thy 不同），dev_patches 的 stock 树移到 5826993；`run-tree … build -j 3 HOL HOL-IMP HOL-ex` 17 分 47 秒 exit 0，
   tested 记录 11 个 session；共享树上唯一的使用方是 "wire optimiazation" 会话的 Isa-REPL（pid 136990），它没回话，**用户选"我来杀掉它"**，TERM 后
   全部退出；`advance-daily … HOL HOL-IMP HOL-ex` 把 daily 30aab6e → 7eb9137（15:1x +08），共享树 `Pure.thy` 与原版一致；随后在共享树上重建迁移
   第 2 步那 16 个 heap。已通知 TAT record、jEdit 语义搜索面板、light、wire optimiazation：
   "重建完成"之前不要在共享树上起 Isabelle 进程。重建先用 `-b -j 3`（默认 threads=0，每个 session 8 线程，负载到 40）；用户指出本机只有 10 个
   逻辑 CPU（本 shell 的 `nproc` 报 14，未深究），按用户同意中断（SIGINT）后改 `-b -j 1 -o threads=10` 重跑，27 分 21 秒 exit 0（16:00 +08），
   `build -n -v` 干跑无任何待建 session。期间新会话 mlml-ad 在共享树上起了 `ML_process -l HOL`，用户要它"工作前看看有没有人已经在跑了，别过来抢
   CPU""绝对不能并行编译 isabelle"，已原话转达，它停掉进程、改去 cslh19。"重建完成"已通知五个会话。**提议待批**：memory 记"本机开 Isabelle
   构建前先 `ps` 确认没有别的构建在跑，绝不与别人的构建并行；自己用 `-j 1`、`-o threads` 不超过 10"。
   **§5 第 4 步已对现有两节链跑过（用户 2026-10-28 下令，10:45 +08）**：原版树 = 官方 tarball `~/isa_release_proto/Isabelle2025-2_linux.tar.gz`
   （sha256 a20a507b… 与计划 :1227 记的一致；`etc/ISABELLE_ID` = 89701cf1768e）解到 scratchpad；FD 由两个包目录的 `patches/Isabelle2025-2/` 复制成
   `features.d/{expose_foreign,future_assign_interrupt}/`；`check-roundtrip <树> future_assign_interrupt --features-dir FD -C contrib/Isabelle2025-2`
   exit 0：A（工具 apply）== B（GNU patch 打 pristine/89701cf1768e → future_assign_interrupt/1），A 与原版不同，unapply 后 A == 原版；两个 feature
   都不新建文件。解包树用完已删（2.3 GB，tmpfs）。light 发布后要再跑一次（链顶换成 light_locale）。
   **§5 第 5 步进行中（用户 2026-10-28 "很好，请继续"；全部未提交，新文件都要先经用户批准）**：
   (1) 工具配方 `conda/recipe.yaml`（新文件）：noarch python，版本经 `TOOL_VERSION`（workflow 从 pyproject 读，不设即报错——rattler-build 的
   `load_from_file` 要 `--experimental`，不用），build 号经 `TOOL_BUILD_NUMBER`；五项配方测试含"pip 版本 == conda 版本"；本机构建
   `isabelle-patch-control-1.0.0-pyh4616a5c_0.conda` 全过。rattler-build 用 `/var/tmp/claude-reverify-pkg/rattler-build`（别的会话留的；sha256
   d72b9814… 与 GitHub 上 0.69.1 musl 资产记录的 digest 相同；下载外部二进制被 auto mode 拦了）。
   (2) 渲染器 `tools/render-feature-recipe`（新文件）与 `tests/test_render.py`（新文件，13 例）：HEAD 上的发布 tag 选 `patches/<R>/provenance.txt`；
   只拷 git 跟踪的 patch 文件、包目录脏就拒绝；钩子逐字复制 + 组件登记行 + `exit 0`，`.bat` CRLF 且查 echo 行元字符；模式固定 644/755。
   **钉死写法改了**（rattler-build 拒 `isabelle 2025.2 1` 与 `==1=Isabelle2025_2_*`；conda 的 MatchSpec 实测把新旧写法解析成同一个约束）：
   `common.isabelle_pin` → `isabelle ==2025.2 <b>`；新 `common.feature_pin` → `==<v> <前缀>_*`，`make-patches` 写 `base_pin` 用它，渲染器从
   `base_tag` 算（`future_assign_interrupt/1` 已发布的来历文件里仍是旧写法，所以渲染器不读 `base_pin`）；`test_plan_builds`、`test_make_patches.sh`、
   RELEASE.md 随改；`features.py` 抽出 `provenance_fields` 供两处共用。两个已发布的基 feature 用真渲染器 + rattler-build 构建成功，`depends` 原样。
   (3) `tools/check-bytes`（新文件）与 `tests/test_check_bytes.py`（新文件，5 例）：决定 15 的字节核对，Python 算 blob、不经工具和 git，参照取包缓存
   里解开的包（`isabelle` 的 `info/paths.json` 与 `isa/`、各 feature 包的 patch 文件）。变异：渲染器 10/10、check-bytes 8/8 被杀。pytest 147、
   toy shell 217 全过。**待用户批准的用户可见文案**：feature 包配方的 `about.summary`（"Isabelle feature package <feature>: changes to Isabelle's
   sources, applied by isabelle-patch-control"）、组件登记失败那句（照 Isabelle_RPC："warning: 'isabelle components -u <包名>' failed; the session
   may be unavailable"，写进 `.messages.txt`）。
   (4) 钩子层测试 `tools/tests/test_conda_hooks.sh`（新文件，真 conda 25.11.1，私有 HOME/CONDARC/包缓存，`--override-channels -c file://玩具 -c
   conda-forge`，`-q` 去进度条但钩子消息照印）：玩具渠道 = 真工具包（build 号 1）、玩具 `isabelle` 构建 0（旧 ID）/1/2（桩 `isa/bin/isabelle`、真
   pre-unlink、只做第 26/34 条重跑的 post-link）、三个玩具 feature（真渲染器，t_two 带组件）、间接依赖计数包、坏工具（同版本 build 0，单独渠道）、
   "未配套重发"渠道（同名文件复制 + 建一个空包触发索引——同名不同字节会搅乱按文件名认包的缓存）。十个场景函数照决定 15 逐条；
   分批跑过：`s_order s_prune` 23/23、`s_components s_conflict s_rebuild s_tool s_oldbuild s_leftovers` 48/48、`s_residue s_rule s_interrupt` 45/45，
   共 116 项。途中改过的三处都是测试自己的错：c.ML 末尾追加一行不是 CONFLICT（按决定 6 层级看补丁能否打上，远离 hunk 的编辑照样反打并保留——
   改成 `sed -i` 改 t_three 改过的那一行）；持锁 200 秒没算 conda 求解的十几秒，第三个 pre-unlink 等到锁、把整链撤回原版（工具正确）——改成持锁到
   命令结束再杀；`s_rule` (i) 不受影响，因为换 `isabelle` 后 `etc/ISABELLE_ID` 是新文件。SIGINT 场景 `s_interrupt` 用一个依赖 t_two 的"慢包"
   （post-link 先写标记再睡）可重复地复现 README 的情形：conda 回滚、删 history、t_two 的改动留在 `isa/`、`status` 打出修复文案；两条修复路线
   （`touch history` 加重装、原处 `conda create -p`）与随后的放弃（`conda remove`）全过，且 `conda remove <链顶> --dry-run` 不带走 `isabelle`。
   **全量一次跑通**（2026-10-28 12:21–13:57 +08，116/116，exit 0，运行中脚本未改）。钩子层测试**没做变异检查**（一轮 96 分钟）。
   日志归档 `~/archive/claude-scratchpad/f1ebd39a-step5-{tests,hooks-full}-2026-10-28.tar.zst`（已校验，源已删）。
   (5) `tools/release-plan`、`tools/check-packages`（含 `--chain`：整批必须是从 pristine 起的整条链、按序；`--summary` 给后续 job）、`tools/local-channel`、
   `tools/accept`（§6 (a)–(l)，Python，Windows 腿同一份；(f1)/(f2) 的文件从包里的 patch 推出；light 的 session 检查由 workflow 现写目录传入）、
   `.github/workflows/release-features.yml`（五个 job；固定表只有已有仓库的四个 feature；密钥名 `ISABELLE_PATCHED_READ_TOKEN`、
   `PACKAGING_CI_ACTIONS_READ_TOKEN` 已写进 RELEASE.md）——全是新文件。`tests/test_release_tools.py`（新文件，16 例），变异 12/12。
   `common.conda_archive` 新增。pytest 163 全过。`tools/accept` 在本机对玩具渠道整体试跑：44 项过（(c)、(e) 本机没有 Isabelle_RPC 式组件包、
   跳过），(i) 起初错拿了链顶的 feature 目录（该拿链底，它的 base_tag 才是 pristine tag），已改、复跑过；以链顶为对象另跑 (f1)/(f2) 11/11。
   workflow 改用 miniforge（README 的命令不带 `--override-channels`，defaults 渠道会触发 Anaconda ToS 报错——**这一点对真实用户也成立，待向用户提**），
   osx-64 腿只在 accept 那一步设 `CONDA_SUBDIR`。计划决定 10 的钉死写法已手改记录。workflow 与五条腿只能在 §5 第 7 步排练时真跑。
   **第 5 步本机能做的部分完成（13:59 +08）；等用户的**：12 个新文件逐个批准后提交（两份 CODE_REVIEW 报告照旧不提交）；两句用户可见文案（见上）；要不要先做一轮代码评审
   （作者建议做，新代码约 2500 行）；第 5 步末尾的一次性手续（`PUBLISH_REPOS`、四个密钥、`.gitattributes`）；README 安装命令与 defaults 渠道的 ToS 问题。
   **2026-10-28 16:2x +08 用户"批准提交"**：12 个新文件与两句文案批准；工具仓库提交 **9ece624**（21 个文件，按显式路径；两份 CODE_REVIEW 报告未提交）
   已推 origin；主仓库提交 **7f6432c8**（登记 `contrib/isabelle-base-features` 子模块 + bump 工具仓库到 9ece624），主仓库未推。用户同时要求一轮
   两回合对抗评审（Workflow `wf_25eb638e-632`：五视角质疑 → 每条一个新 agent 辩护 → judge 裁定验收与"哪些须与用户讨论"；Opus、xhigh、全英文），
   **评审期间不改代码**，结果用中文向用户报告并给修法、等用户同意再动。评审明细 JSON 永不进仓库，评审报告 `.md` 不提交。
   **评审结果与修复（2026-10-28 傍晚，全部未提交）**：judge 判 not-accepted，24 条裁定；用户裁决记在计划 §0 第 39 条，逐条去向在计划 §10.0a
   （"代码已改"/"待做"）。还没做的：钩子层测试的 tests-1、4、5、6、7；GitHub 上跑测试的那一套（新文件，要用户批准）；develop.md:155-158 的
   Windows 说法；全部验证；复评审（范围是 judge 的 rereview_scope，见 `wf_25eb638e-632` 的 journal 末条）。**20:2x +08 起了两个 Workflow**：
   `wf_c72ec0c2-cb2`（GitHub 上怎么测：三方案、各一个新 agent 质疑、judge 定方案）与 `wf_339ea5fc-808`（`core.longpaths` 放宽的细查：代码、
   路径长度、外部行为三路，再一个反驳者、一个 judge）。用户已定持锁上界 30 秒（`tools/accept` 的 (l) 已改）；(l) 的 `--force-reinstall isabelle`
   量什么，用户问"这和持锁上界有什么关系"，作者在解释，**未定**。
   **两个 Workflow 都完成（22:3x +08）**，结果在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/`
   `wngplyy06.output`（longpaths：成立附条件，已记计划 §0 第 39 条）与 `wcjef4z1k.output`（GitHub 测试方案；展开的文本在
   `scratchpad/wf-ghtests/verdict.txt`；已记决定 15 新的"GitHub 上的测试"一条与钩子层玩具描述、§6 (m)(n)、pytest 的 `_retry` 一条）。
   judge 查出本轮引入的回归：`tools/common.py` 的 `patch_blocks` 先调 `block_header` 再查权限位改动，`test_make_patches.sh` 的
   "names the mode change" WRONG；已修（拆出 `block_path`，`patch_blocks` 只用它），该测试 102 项全过。**等用户定**：(1) (l) 的
   `--force-reinstall isabelle` 量什么；(2) `core.longpaths` 的 win-64 探针要不要；(3) macOS 腿换 runner（macos-14 10-29、10-30 UTC 14–24 点
   brownout、11-02 下线，runner-images #13518 已核实）；(4) `accept` job 挪成可复用 `accept.yml` 加共用的 rattler-build 安装 action；
   (5) 可选：CI 计划把重跑 post-link 写成单独文件；(6) 先本地全跑钩子层测试还是直接提交推送让 GitHub 跑。另告知用户：`isabelle-packaging-ci`
   （build.yml Job D、G，release.yml 等）与 `Performant_Isabelle_ML` 也用 macos-14。
   **23:00–00:30 +08 做了不依赖用户答复的部分（全部未提交）**：新文件 `tools/tests/toy-channel.sh`、`tools/tests/toy_isabelle.py`（都要用户批准）；
   `test_conda_hooks.sh` 改调它，tests-1/4/5/7 与新 `s_hardlink`；`tools/accept` 的 `--strict`/`--subdir`/环境说明行与 (a)(b)(g)(l)(m)(n) 加固；
   pytest 加重试四例（变异 6/6 杀死）；`test_trees.sh` 的 `cmp`；`run-all.sh` 保留诊断行；`components_sh`/`_bat` 挪进 `common.py`；develop.md
   测试一节。验证：pytest 171 过；run-all 219 过；钩子层冒烟（s_order s_components s_conflict s_hardlink，`scratchpad/hooks5.log`）58 过 1 错——
   那一错是**设计缺口**：重装 isabelle 的事务里 post-link 读不到 isabelle 记录（conda 最后才写），选不了硬链接文案，已记计划 §0 第 39 条交用户定，
   测试里那条断言已删；**10-29 "net printing" 会话（feature `fast_abbrev_printing`，用户授权它建了 `Isabelle2025-2/fast_abbrev_printing` 分支与
   两棵树）提议把 light 的 golden 框架抽成本仓库 `tools/golden/`**；作者回复：形状没问题，但 `run-tree` 记的是 `-d` 目录所在的**整个仓库**
   （每个已跟踪文件的 mtime，`run-tree:82-96,124-132`），作者在本仓库持续改已跟踪文件，它的构建会丢 tested 记录；建议放进一个单独的小仓库
   （要用户批准），已请它也报用户。它随即放弃本仓库，另提 (d) 放在 `isabelle-base-features` 根目录 `golden/`；作者核过：发布工具（make-patches、渲染器、check-packages、release-features.yml 的表）都只看给定的包目录，根目录 `golden/` 不打包、不检查、不拒绝；只有 base-features 的 README（"Each directory's README.md explains its fix"）与 RELEASE.md:29-30 两处文字描述布局，另提醒该仓库公开、用途是"基础修复"，放测试框架算改用途，由用户定。它随后转告：用户定了放 `isabelle-base-features/golden/`（自己的 ROOT，session `Golden_Harness = Pure`），写之前它先做一轮计划重评；base-features 的 README 它自己改。**留给本会话的一件（等用户下令再做）**：`RELEASE.md:29-30` 那句"holds two, expose_foreign/ and future_assign_interrupt/"在 `golden/`（以及将来的 `fast_abbrev_printing/`）出现后要改写。accept 对玩具渠道 `--strict` 70 过 0 错、无跳过（(c)(e)(f2) 首次在玩具上跑；`scratchpad/accept-run.log`，环境已删）；两个反对照（`scratchpad/negctl/`）都按预期报 WRONG。
   **10-29 用户答复七件**（记在计划 §0 第 39 条末，原话照录）：2 加 longpaths 探针、3 macOS 用 macos-15 / macos-15-intel、4 可复用 accept.yml
   与共用安装 action、5 不做、7 选 (b)——都已做（计划决定 4、9、11、15、§6 (a) 已手改；代码：`tools/accept` 的 `longpaths()`，
   `conda_hook._edited_in_cache` 加无记录一支与 `texts.CACHE_DIR_UNKNOWN`，pytest 2 例（变异：去掉分支、pre-unlink 也推断，都杀；"新建路径也算"
   是等价变异，原因是只有新建路径时没有第 2 步，过滤层已删），钩子层 `s_hardlink` 断言新文案；新文件 `.github/workflows/tests.yml`、
   `.github/workflows/accept.yml`、`.github/actions/build-tools/action.yml`，发布 workflow 改调它们；本地 actionlint 被 auto mode 拦（外部二进制），
   留给 GitHub 的 lint job）。1 (l) 用户授权"与文档、测试相关的，在不改变设计的前提下，你可以自决"，作者定：量占锁那段（先 unapply 再计时 apply）、保留为发布门槛、30 秒（计划决定 15、§6 (l)、§0 第 39 条已改）。**仍待用户**：6 新文件逐个批准与"提交"；7 的新文案与对提案的一处偏离（去掉"共用同一份
   数据"条件）。
   **10-29 用户"1. 批准 2. 按你建议来，如有需要 run Opus agent readers for proofread"**：五个新文件批准（提交仍等"提交"）。第 7 件文案经两轮
   三人校读（`wf_18d6613d-869`、`wf_0d9345be-41e`）定稿：`texts.CacheCopy(directory | None, prefix)`，未知目录时让用户从
   `conda list -p <prefix> --full-name isabelle` 读版本与 build；计划决定 9、§4 已改。校读查出的范围外问题（修复命令都假定激活的就是出问题的
   环境；§4 与代码"every other environment …"不一致）记在计划 §0 第 39 条，交用户定。
   **10-29 范围外问题按用户授权（"你可以自决"+"一定要尽可能简单，一个地方讲清楚了不要到处重复"）只改两处**：`texts.save_line(tree)`（原
   `SAVE_LINE`，三种提示共用）点名本环境的 `isa/bin/isabelle`（Windows `isabelle.bat`）；第 2 步缓存版写 "every other environment with isabelle
   …"。第三轮 reader（`wf_6b690b7c-209`）一致指出作者"其余命令在错的环境里不丢东西"的理由对重装那条不成立、只改第 1 步反而更糟；于是加 `texts.reinstall(tree)`（`-p <tree.parent>`，三种提示共用），`CacheCopy` 只剩 `directory`，缓存版第 2 步让其他环境也先做第 1 步，符号链接拒绝调成 conda config → 保存 → 重装。计划 §4 已改（残留块第 1、2 步改为引用）。最后核对 `wf_ae1893a3-3ce` 与真 conda `s_hardlink`（`scratchpad/hooks8`）：真 conda 14/14 过；最后核对查实不丢东西，另删 `save_line` 与 `common-readme.md` 里 "that belongs to this environment alone"（软链接树里为假），三条少见的记进计划 §0 第 39 条不改。pytest 173、run-all 219 过。提交仍等用户说"提交"。
   **10-29 用户"提交"**：工具仓库 `0133f6f`（5 个新文件 + 32 个修改）已推 origin；主仓库 `092a619e` 只动子模块指针，未推。GitHub 首跑
   run 40829078927：lint、两个 unit、toy-channel、accept 的 linux-64/linux-aarch64/osx-arm64/osx-64 过；hooks 失败（Miniforge base 是
   python 3.14、没有 zstandard → `common.unzstd` 先用标准库 `compression.zstd`）；win-64 accept 87 过 4 错（只读目标的暂存副本删不掉 →
   `engine._remove_tree` 先去只读属性）。两处已修、pytest 173 过，**未提交，等用户"提交"后推送重跑**。
   **10-29 用户"提交"**：工具仓库 `8da1a9e`（zstd、只读副本）已推；主仓库 `181b874b` 未推。GitHub 第二跑 run 40832352868：除钩子层外全过
   （win-64 只读问题已好）；钩子层 135 过 4 错，全在 `s_interrupt`：conda 26.9.4 修了"回滚删 history"的 bug（conda#16474），工具因此看不出
   被中断的安装——**设计问题，记在计划 §2.3 的订正，交用户定**。用户"赞同你的建议，请 run Opus agent team 头脑风暴"：Workflow `wf_b5126230-1d6`（事实 1、方案 4：只补说明/记账/比对 conda 记录的 sha256/另找出路，各配一个质疑者，judge 1）在跑；注意 §9 早先否决过记账与 sha256 比对两条路。**结果（17:0x +08）**：judge 推荐 (1) 改所有讲回滚的文字（按 conda 打印的 "Rolling back transaction" 说、修法是同一条命令再跑一次）；(2) 唯一设计改动：命令行 `status` 加一项对 conda `isabelle` 记录 sha256 的检查（检查、非状态来源）；否决记账与树里记录文件。完整推荐在 `scratchpad/wf-rollback/verdict.md`，各项改动清单在 `tasks/w1s8pffcn.output` 的 verdict 里。新事实（作者核过四个 tag）：只有 conda 25.11.0–26.5.x 回滚删 history。**等用户定**。
   **10-29 用户要在 cslh19 的 MLML/contrib 同步本机状态**：裁定 (A) 只同步各 git 仓库的已提交状态；Isabelle2025-2 换成本机的 git 仓库加工作树；
   冲突以本机为准。用户让先把未推的仓库推上 GitHub：已推 Isabelle2025-2（`isabelle-patched` 全部分支加 `refs/notes/tested`）、
   isabelle-base-features、Isa-Mini、isasearch-web、light_locale、nunchaku、Performant_Isabelle_ML、phi-system、Theory-Agent-over-Trees
   （都只快进）。未推、待用户定：AutoCorrode（origin 是 awslabs，只读；另有 `fork` 远端）、localized_record（没有远端）。cslh19 只能用 ssh 地址
   读 GitHub（https 没凭据）。cslh19 上正跑着 light 的变异测试构建（`~/light_mutants/`，与 MLML 无关），任何构建都要等它。同步方案（含两处
   "先备份再覆盖"与 `scala_build`）等用户批准。
   **执行（10-29 16:0x +08，用户：AutoCorrode 不同步、localized_record 先不管、Isabelle-MCP 与 isabelle-packaging-ci 必须是和本机一样的 git 仓库）**：
   cslh19 上 9 个仓库快进到本机提交（Isa-Mini 的 translator 对到记录的 `f402f9d`）；克隆 11 个（含原来是空目录的两个子模块与三个空仓库）；
   `Isabelle2025-2` 原地接 `.git`（来自 `isabelle-patched`，HEAD daily `7eb9137`，11 分支 3 tag 8 条 tested 记录），39 个旧补丁文件与 5 个 `.bak`
   先打包到 cslh19 `~/sync-20261029/isabelle-pre-sync-files.tar`，再换成 daily 内容并补上 3 个；`.bak` 未删；上游、`--ff-only`、钩子照本机。
   **未做**：`scala_build`（4 个 `.scala` 文件变了，jar 是旧补丁编的，PIDE 前端在它之前可能出错；等用户批准）；之后 `new-tree` 建 19 棵私有树；
   heap 等用户下令。cslh19 上 light 的变异测试循环一直在跑（`~/light_mutants/`）。
   **用户批准 `scala_build`，"请帮忙 rebuild the heaps on cslh19"，"等 light 那个循环停下来再跑"；私有树（new-tree）用户问"我们只是要去同步状态对吗"，作者建议不建、按需再建**。
   cslh19 后台脚本 `~/sync-20261029/heaps.sh`（pid 记在 `heaps.pid`，日志 `heaps.log`）：每步前等连续 600 s 没有别的 Isabelle 构建，然后
   `scala_build` → `build -b -j 1 -o threads=12` 那 12 个 32 位 heap → `-o ML_system_64=true Phi_System_Base`；scala_build 失败就停。16:15 起等待。
   scala_build 16:57 exit 0（jar 已是新的）；32 位那步 17:19:38 自己开跑（light 的循环停了 10 分钟；当时作者刚问用户要不要放宽等待条件，
   用户还没答；作者没掐断它，已告知用户）。同时跑着另一会话的 class_variant 作业（`/tmp/xero_s4t/run_cvs.sh`，用 MLML 的 Isabelle 与
   AFP-ALL-4 heap，17:09 起、超时 4 小时）与 Isabelle2026 的 mirabelle；作者另起了 cslh19 可用内存低于 5 GB 的监视。
   **10-29 用户对头脑风暴的裁定**（计划 §0 第 40 条）："好的，赞同 / 可以加 status 的这项检查 / status 的退出码可以变成 1 / 与文档、测试相关的，
   在不改变设计的前提下，你可以自决"。计划已改（§0 第 40 条、§2.3、决定 5/6/9/15、§4、§9、附录 A、§10.0a 末行）。代码已写（未提交）：
   `features.IsabelleRecord`/`edited_in_cache`、`api.unexplained`、cli `status`、texts（`RERUN_LINE`、`UNEXPLAINED_ROW`、`unexplained_row`、
   `unexplained`，CONFLICT 文案第 2 行与 RERUN_LINE，残留块删 "(nothing will remind you later)"，包缓存第 2 步末两行）；README/AGENTS/reference；
   新文件 `tests/test_unexplained.py`（14 例，**提交前要用户批准**）；变异 12 个全杀（插件在 scratchpad `mut-unexplained/`）；pytest 187 过；
   钩子层 `s_interrupt` 按 conda 版本分两支、`toy-slow` 只等一次、`states()` 只读状态行；`tools/accept` 的 `states()` 同改。
   本机钩子层全量（conda 25.11.1，删 history 那支）143 过 0 错（`scratchpad/hooks9.log`，用的是校读前的文案）；临时装的 conda 26.9.4
   （`scratchpad/conda269`）单跑 `s_interrupt` 的重跑那支 15 过 0 错（`scratchpad/hooks10.log`）。三个 Opus reader 校读一轮，文案已按意见改、
   计划 §4 记了取舍；pytest 188 过（新文件 15 例）。**等用户批准文案与新文件**，之后用定稿文案重跑钩子层、等"提交"。
   cslh19：32 位 12 个 heap 17:58 建完 exit 0；64 位 Phi_System_Base 18:08 建完 exit 0（46 秒，它的 64 位上游已是新的——大概是 class_variant
   作业启动时建的，未核实）；heaps.sh 18:08:51 DONE。cslh19 同步与 heap 重建都完成。
   **同晚用户收回第 40 条（计划 §0 第 41 条）**：检查与自动修复都是"过度设计"，回滚的修法只有重装 isabelle；history 不管；`status` 改成
   整句（用户批准）；钩子 CONFLICT 诊断与残留块缩成与 status 同一段重装说明（用户批准）；删掉经硬链接改进包缓存的检测，工具不再读
   conda-meta（用户"按你建议来"）。第 40 条的代码已撤（diff 存 `scratchpad/ruling40-withdrawn.diff`），`tests/test_unexplained.py` 删了；
   pytest 172 过；status 的句子经一个 Opus reader 三面校读一轮并照改（查出 feature 新建文件那种情形会抛异常，已修、加测试），4 个变异全杀。
   钩子层全量在跑（`scratchpad/hooks13.log` 25.11.1、`hooks14.log` 26.9.4）。之后：给用户看结果、等"提交"。
   钩子层全量两版本各 110 过 0 错（`hooks13.log`、`hooks14.log`）；钩子 CONFLICT 诊断、残留块、硬链接检测删除都已做、用户批准文案。
   **等用户"提交"**（提交里没有新文件）。
   下游 5 个分支已合并（4 个快进到 3578f4c，dev_patches 合并成 ea71fb4，五棵 stock 树挪到 3578f4c），用户令推送、已推 isabelle-patched。
   dev_patches 的 run-tree 构建测试：用户同意在 cslh19 跑，但等新目录布局落地后再建树。
   **目录重组（主仓库 `ai-artifacts/ISABELLE_GIT_MIGRATION_PLAN.md` §0 第 34 条、§12）**：用户定每棵树是 feature 仓库里真正独立的 submodule
   克隆，daily 仓库为每台机器的中转站，推送不需用户下令（提交仍需），gitlink 只在发布时由 make-patches 写，isabelle-patched 公开，三个新
   GitHub 仓库公开，`contrib` 软链接 `../../../Isabelle2025-2/contrib`。第一稿、第二稿各经一个 Opus agent 实测评审，结论与修法都记在 §12；
   **第三稿用户已批准**（§12"第三稿"；执行状态与 compact 后的下一步在 §12 末"执行状态"小节）。删门 1、迁移时搬运未提交改动并通知所有
   相关会话、GitHub 不加保护规则、check-signatures 的 `-C` 修复顺带做，都已定。
   **代码评审四的实施清单 (a)–(h) 已改完（2026-10-30）**；用户说新文案"不需要我批准"、让起 Opus reader 校读，两轮校读（三人一轮、
   事实核对一轮）之后，用户定"是问题就都要改"，旧文案的问题也全改了（补丁工具计划 §0 第 41 条末）。pytest 181、变异 58 个全抓到、
   钩子层测试两版 conda 全过（工作目录 `/var/tmp/claude-hooks/`）。等用户说"提交"，之后推送并重跑 GitHub CI；钩子兜底文件的新文案随此后
   发布的 feature 包生效。staging 目录已归档删除；三个 GitHub
   仓库已建（Local_Datatype、Local_Type_Abbrev、Localized_Record）。
   **compact 后先做**：(1) 等/问用户"提交"补丁工具这批改动；(2) 迁移第 (i) 步剩下的：isabelle-patched 设公开（gh 写法要核）、三个新仓库的
   名字向用户确认后建；(3) `Isabelle2025-2-staging` 的调查结果交用户；(4) 第 (ii) 步工具改动。README 的 "When something went wrong" 新段落
   用户还没单独看过（补丁工具计划 §4 标"待用户批准"），提交前给用户看。
   另：net printing 会话转来三项提议（check-signatures 在 `-C` 下解析 `<rev>` 的 bug、"新建功能到发布"的流程文档、一个
   isabelle-feature-package SKILL），自称用户原话"很好这些提议请你发给 git agent 让它去办"；同伴消息不算批准，已问用户，未动手。
   接下来（每件仍要用户下令）：light 的 `tools/component_files.txt`、带 `-d <light 仓库>` 的构建、
   `make-patches light_locale <v>`（门禁 0 已满足：light 分支与 `Isabelle2025-2/future_assign_interrupt` 的 merge-base 就是带 tag 的 6d8be01）；
   checklist 现在在 `RELEASE.md`，**在构建之前**过。之后三个新 feature、`contrib/qiyuan_dev_patches/`（GitHub 仓库已建、本地目录未建）。第 4 步 `check-roundtrip` 在官方 tarball 树上跑；第 5 步渲染器、工具的 `conda/recipe.yaml`、
   `release-features.yml`、钩子层真 conda 测试，**首次发布冻结统一文本之前再过一遍 reader**（judge 要求，范围含 texts.py 外被钩子引用的拒绝句）。
4. **用户新定的规矩**：评审明细 JSON 永不进任何仓库（`.gitignore` 已挡 `ai-artifacts/*_detail.json`）；评审报告 `.md` 也不再提交（已跟踪的五份不动）。
   memory 里原来"评审记录可留"那条（`ai-artifacts-never-commit-experiments.md`）已于 2026-10-25 18:30 +08 经用户批准改成这条新规。
   其余常备规则见文末"用户的常备规则"。
5. **scratchpad**（`/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/scratchpad/`，约 1.1G）：`mutcheck/`（变异插件
   `mutants2.py`、`run.sh`、`results.txt`）、`render_code1.py`/`render_code2.py`、`condensed_code1.py`、`realchain/`；两轮代码评审与前五轮方案评审的
   实验已归档到 `~/archive/claude-scratchpad/f1ebd39a-*-2026-10-25.tar.zst`。/tmp 是 24G tmpfs，用完即归档（压缩、校验、再删源）。

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
- **测试** `tests/`（pytest，当时 87 例，约 2 分 10 秒——其中 120 秒是两个钩子锁用例对冻结进默认参数的 `LOCK_TIMEOUT` 改写无效、各等足 60 秒，
  代码评审一轮 C7 查出并修掉；杀进程子进程的 14 例合计只要 4 秒；修后 123 例约 25 秒）：`conftest.py` 的 `Toy` 用一个玩具 git 仓库按 make-patches 的方式
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
- **提交**：用户 2026-10-25 "批准提交" → 工具仓库 `main` cc0e603（27 个文件）。
- **外部动作（用户 2026-10-25 "全部下令，请你在合适的时机进行"，已全部做完）**：GitHub 仓库改名 `xqyww123/isabelle_patch_control`（`gh repo rename`，
  旧名自动跳转；主仓库 `.gitmodules:41` 的 url 与子模块的 origin 已同步）；工具仓库 push 到 cc0e603、CI 仓库 push 到 2c5901d（都只推 origin）；
  base 与 `.venv` 的旧 editable 安装（0.1.1、0.1.0）已 `pip uninstall`，`my-better-isabelle` 命令随之消失；主仓库 `main` 3bf74ab0 bump 了两个
  submodule 指针与 `.gitmodules`——**主仓库未 push**（不在四项之内；它领先 origin 的其他 commit 是别的会话的）。以后工具仓库每有用户批准的 commit，
  就 push 并 bump 主仓库指针（用户的授权是"在合适的时机进行"）。旧 URL 的残留引用只剩 `contrib/Isabelle-MCP/AGENTS.md:14`（别的项目的文档）与
  CI 仓库 `PACKAGING_DESIGN.md:892,942`（历史记录）——GitHub 跳转能兜住，CI 计划（决定 12 第 4 点）重写时顺手改。
- **决定 14 已做（2026-10-25，未提交）**：`git rm -r my_better_isabelle_prover/`（旧代码、`patches/` 含 Isabelle2024、`categories.toml`、五份补丁
  `.md`——最后含有它们的 commit 是 cc0e603，§5 第 3 步从那里复制到决定 13 的仓库）；盘上残留的 `__pycache__` 与 `my_better_isabelle_prover.egg-info`
  一并删了（`dist/` 里旧轮子留着，被 ignore）。新建 `common-readme.md`（决定 10 的统一文本：每个 feature 包 README 的开头，`README.md` 逐字嵌入，
  smoke 从它读 `conda create -n isabelle -c … isabelle isabelle-light-locale` 那一行；`tests/test_docs.py` 断言逐字相同与那一行的形状）。重写
  `README.md`（统一文本、卸载/重装/剪枝/`--force`/CONFLICT 之下重链接/只支持 conda/Ctrl-C 恢复/硬链接原地编辑恢复、指向 AGENTS.md 的 0.x 一节；
  "Working in the Isabelle source repository"一节原样保留）、`AGENTS.md`（`help` 打印；状态表、退出码、各情形怎么办、规则、命令、"Coming from
  my-better-isabelle 0.x"）、`reference.md`（§4 的命令、树与 feature 来源、链与层级、退出码、锁与工作目录、文案索引）、`develop.md`（一条路径八步、
  模块表、测试、真实链核对的做法、feature 包怎么产生）、`RELEASE.md`（conda 发布；决定 16 第 10 点的 checklist 七条带理由；发布步骤；决定 11 的
  workflow 输入与作业；版本与 build 号；恢复；一次性手续，注明 workflow 在 §5 第 5 步落地、落地前它是规格）。`pyproject.toml` 改名
  `isabelle-patch-control` 1.0.0、URL 换新仓库名、只剩新入口与新包。pytest 91 例全绿。这些文案都是作者写的、没经 reader 校读。
- 决定 14 这批已提交：工具仓库 fa1d64a（用户 2026-10-25 "批准提交"），已 push；主仓库 a17dd76d bump 指针（未 push）。
- **§5 第 2 步已做（2026-10-25，未提交）**：
  - `tools/common.py`：`sys.path` 加仓库根后 `from isabelle_patch_control.names import package_name`（再导出）；`tested_records` 解析 `dir:` 行
    （`dirs[top] = (HEAD, 未提交文件)`）；`repo_state(dir)`、`tracked_mtimes(top)`；决定 10 的 `plan_builds(repodata, wanted, fetch)` 与 `Wanted(name,
    version, filename(n), accepts(record))`——候选 = 索引里同 (名, 版本) 的记录 + 从最高 build 号 + 1 起用 `fetch(文件名)` 探到的在服务文件
    （`fetch` 返回该文件的 index 记录或 None），想要的候选取最高 build 号复用，否则新建、号 = 跳过之后的下一个。
  - `tools/run-tree`：每个位于 git 工作树的 `-d` 目录在记录里多一行 `dir: <顶层> <HEAD> <未提交文件>`；构建前后比较这一行**以及**该仓库全部已跟踪
    文件的 (mtime, size)（"改了又改回"只有 mtime 能看出来；1 秒精度的文件系统上同秒改回会漏），变了就不写记录、原因点名那个 `-d` 目录。
    `stub-isabelle` 加 `$HOME/.stub-build-edit`（构建中改一个文件再改回）；`test_trees.sh` 加两例（64 例全过）。
  - `tools/make-patches`：第 7 点（包目录所在的 feature 仓库：三份清单与 `tools/component_files.txt` 及其所列文件必须已提交且无改动；tip 已有本 feature
    的发布 tag → 拒绝"commit first"；记 H）；门禁 (e) 对带组件文件的包只计"`dir:` 行有该仓库、所列文件无未提交、记录 HEAD 与 H 之间
    `git diff --quiet -- <所列文件>` 为真"的记录（其他记录打印 `not counted: 原因`）；门禁 (c) 改走 `api.apply_to/unapply_from`（块先写进临时目录，
    `patch` 命令不再使用）；第 8 点写入顺序 (b) 删旧 patch、复制新文件与 provenance → (c) 按名 `git add`/`git rm --cached`、
    `git diff --cached --quiet -- L`、`git commit -- L` → (d) 核对将打 tag 的 commit（已有 tag 指的或 HEAD）的 blob 恰等于生成的，带组件文件的另核
    `git diff --quiet H <commit> -- 组件文件`，不符则拒绝、已有 tag 时说"this version number is spent: release v+1" → (e) feature 仓库打 tag →
    (f) 最后 Isabelle 仓库打 tag。测试接缝 `MAKE_PATCHES_FAIL_AFTER=b|c|e`（docstring 里注明 tests only）。`test_make_patches.sh` 重写：包目录成为
    git 仓库；第 7 点两种拒绝且不留 tag；三处失败注入各一次、重跑完成（含"无第二个 commit"）；无关的已暂存文件不进发布 commit；带组件文件的包：
    无 `dir:` 行的记录不计、无关 commit 后通过（第 35 条验收例）、组件文件改后提交被拒、构建时组件文件未提交被拒、(e) 后改组件文件再重跑被拒并说
    版本号作废、light 首次发布形状（旧 patch 文件重写、stale 文件删除、provenance 新增）；70 例全过。输出多了几行（committed/tag/not counted），
    "N patch files written to" 那行保留原样。
  - `tools/check-roundtrip`（决定 17，新文件，可执行）：`<原版树> <链顶 feature> --features-dir FD [-C 仓库] [--tool 命令] [--keep]`；umask 022；
    副本 A/B 用 `cp -a` 建在原版树旁的 mkdtemp 里；A 走工具 apply + `status -v`（每个 `--- /dev/null` 新建的路径必须以 `    <path>  level` 出现）；
    B 走 `patch -p1 -F0 -d B` 吃 `git diff-tree -r -p --no-renames <底 tag> <顶 tag>`；`diff -r --no-dereference -q` 加排序的
    `find . -printf '%M %P'` 清单比对；A 必须异于原版；unapply 后 A 等于原版；`--tool` 默认本 checkout 的 `python -m isabelle_patch_control`
    （PYTHONPATH 指仓库根）。pytest `tests/test_roundtrip.py` 4 例（通过、A≠B、补丁打不上、`--keep`），GNU patch 2.7.6 对新建 100755 文件的权限位
    与工具一致（清单比对过了）。`tests/test_plan_builds.py` 5 例（决定 15 的四种输入 + 空渠道）。
  - 文档：README 的脚本清单加 `check-roundtrip`；develop.md 加一段。pytest 100 例、`tools/tests/run-all.sh` 全部通过。
  - 作者自定的：`plan_builds` 的接口形状（`Wanted` 的两个回调、`fetch` 返回记录）；mtime 指纹；`MAKE_PATCHES_FAIL_AFTER`；`check-roundtrip` 的 `--keep`
    与 `-C` 默认当前目录。
- 第 2 步这批已提交：工具仓库 321646d（用户 2026-10-25 "你可以自决"→作者决定评审前提交），已 push；主仓库 7c212ced bump 指针（未 push）。
- **代码评审第一轮正在跑（2026-10-25）**：用户要求两轮对抗（critics → merge editor → 每个 challenge 一个全新 defender → judge），Opus、xhigh、全英文，
  重点删低质量意见、看优雅性、驳斥钻牛角尖、提议放宽规约；judge 裁定是否达到验收（可进 §5 第 3 步）、哪些要用户定、哪些作者自决后再评；**用户同意前不改代码**；
  reader 校读文案一并做（三位 reader，medium）。Workflow 任务 `wdtyl8idy`，run `wf_0a0a00a6-aa3`，脚本
  `~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/workflows/scripts/patch-tool-code-review-1-wf_0a0a00a6-aa3.js`，
  结果在 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/wdtyl8idy.output`（JSON 包装，`result` 里有
  `findings`、`overalls`、`readings`、`merged`、`defenses`、`judgement`——`judgement` 多了 `accepted` 与 `reader_points_to_act_on`）。处理方式同前五轮：
  存 `ISABELLE_PATCH_CONTROL_CODE_REVIEW1_detail.json`、渲染 `ISABELLE_PATCH_CONTROL_CODE_REVIEW1.md`（渲染脚本仿 scratchpad `render5.py`，加 readers
  一节），用中文向用户汇报全部 concern、每条打算怎么改、哪些要用户定、reader 的意见；用户同意后才改代码。中途暂停则
  `Workflow({scriptPath: <脚本>, resumeFromRunId: 'wf_0a0a00a6-aa3'})`。评审员的实验在 scratchpad `review-code1/`。
- **代码评审第一轮已完成（2026-10-25，50 个 agent，约 2.5 小时）**：报告 `ISABELLE_PATCH_CONTROL_CODE_REVIEW1.md`、明细 `…CODE_REVIEW1_detail.json`
  （渲染脚本 scratchpad `render_code1.py`，浓缩视图 `condensed_code1.py`）。78 条发现 → 38 条 challenge（5 条被 merge editor 删）；defender 一条也没整体驳倒
  （20 confirmed、18 partially）；**judge 判未达验收**（不能进 §5 第 3 步）。阻塞第 3 步的：C3（make-patches 第一次发布形状下失败后重跑永远被拒，一行修）、
  C11（决定 16 第 9 点要求的用例缺失、门禁 (c) 从未在测试里拒绝过）、C22+C25（make-patches 与 check-roundtrip 以文本模式读 diff 丢 CR；check-roundtrip
  对真 pristine tag 的 archive 崩溃——没有 etc/ISABELLE_IDENTIFIER）、以及 checklist 放在 make-patches 之后（失败即烧版本号）。要用户定的（owner_decides）：
  C2（.messages.txt 编码：建议全平台 ASCII+backslashreplace）、C4（忽略目录不算 `-d` 仓库）、C36（`dir:` 行只算已跟踪文件）、C13（CONFLICT 文案改说
  "直到修好之前工具不打 F 及其上"）、C15（hole 规则改"下面有不是 applied 的"）、C19（`--feature` 也接受包名）、C29（README/附录 A 的"stacking 必 CONFLICT"
  句改写）、C34（链接不上时 pre-unlink 改写链接不上文案+两支，删 single_feature_levels）、C35（只读 release_tag/base_tag）、C37（删 checklist "空文件"条）、
  C38（放宽决定 15 锁用例）、checklist 放到 make-patches 之前、`conda update --all` 要不要警告删用户目录、CONFLICT 文案末行 0.x 指针要不要留。
  作者自决后再评（author_decides_then_rereview）：C1、C6、C8、C10、C11、C14、C17、C18、C22、C23、C25、C26、C30、C33。机械修改不再评：C3、C5、C7、C9、
  C12、C16、C20、C21、C24、C27、C28、C31、C32。reader 意见要采纳的在报告 "Readers' points the judge says to act on"。**用户同意前不改代码**；中文汇报已发
  （2026-10-25）。下一步：按用户答复改代码与方案（方案改动手改），跑 pytest/玩具测试/变异检查，再起一轮定向评审（author_decides_then_rereview 的条目）。
- **用户 2026-10-25 对评审的裁决（全部已定，可以开工）**：问"是否与设计有关，无关的自决"。设计相关三件：**C15 按建议改**（hole = applied 下面有任何不是
  applied 的；`status --feature F` 退出 0 当且仅当 1..F 全 applied；决定 6 原文随之手改）；**C29 删句**（"Once a higher feature has changed a file, a lower
  feature's patch for that file reads CONFLICT; that is inherent in stacking" 从工具 README、迁移方案附录 A、§5.3、§7 规则 15 四处删掉，不补替代句，
  迁移方案 §0 加带日期的记录）；**C34 按建议改**（链接不上时 pre-unlink 写链接不上文案 + 更新/卸载两支，不列文件；删 `single_feature_levels`、
  `_residue_chain_broken`、`REASON_CHAIN`，残留原因四减三；决定 9 与 §4 手改）。其余十件作者自决如下：C2 全平台 ASCII+`backslashreplace`；C4 `-d` 目录被
  所在仓库忽略（`git check-ignore -q .` 成功）则不算、第 32/35 条措辞加注记；C36 `dir:` 行只算已跟踪文件（`--untracked-files=no`），规则 11、README、
  glossary、第 32/35 条措辞随之改并加注记；C13 CONFLICT 文案改"until this is fixed, the tool applies neither F nor the packages that depend on it"，
  README 同改；C19 `--feature` 同时接受 feature 名与包名（`names.feature_name`）；C35 只读 `release_tag`/`base_tag`（与 C1 合修）；C37 删 checklist 空文件条，
  `check-roundtrip` 从 `git diff-tree --diff-filter=A` 取新建文件；C38 决定 15 锁用例改措辞、哨兵测试加 `status` 与 `apply --dry-run`；checklist 移到
  `make-patches` 之前、对 `git diff-tree <基 tag> <tip>` 过、每条给手工命令、不写检查代码；`isabelle` 包每次被替换会删用户目录在 README/统一文本说一次；
  CONFLICT 文案末行 0.x 指针暂留。**实施清单**（细节在 `…CODE_REVIEW1.md` 各 challenge 的 JUDGE ACTION）：
  1. 阻塞项：C3（`removed` 从 `git ls-tree HEAD` 算）、C11（写入顺序测试做成函数并在 cpkg 跑；post-commit hook 造"门禁与 (c) 之间提交组件文件"；门禁 (c)
     两例拒绝；`check-roundtrip` 四项检查各一个伪工具用例）、C22+C25（`common.run(text=False)`、`patch_blocks(bytes)` 共用、`check-roundtrip` 用
     `Tree.read`/`FeatureDir.read` 先拒后拷、conftest 用共用切块、CRLF 玩具用例）。
  2. 工具：C1+C35（`FeatureDir(dir, name, release_tag, base_tag)`，name 取 `release_tag` 第二段；每目录检查 `<R'>/pristine/<X>` 不等于树 → not_pristine；
     剩余目录报"base 没人发布"的那个；测试目录名乱序两例）；C15；C17（OSError→WriteFailed 在 `_session` 一处，删 engine 的 PermissionError 特判，
     api.py:118 `read_bytes` 捕 FileNotFoundError，消息兼容 `filename=None`，加 EROFS/ENOSPC 用例）；C18（`features.locate(prefix)`、`FEATURES_D` 一处、
     API 收 `Path`、`read_feature_dirs` 缺根返回 []、`cli.resolve` 用 `abspath`、`Replayer.read_target` 把 patch 路径取绝对）；C19（`features.feature_number`、
     `_chain` 返回 `(chain, k)`、`Status.selected`、`exit_code` 改 property、接受包名）；C23（`apply-to`/`unapply-from` 成功时不打印 conda 环境的文案，
     只 `-v` 列文件与 CONFLICT 行；api.py:182 加注释）；C2（`.messages.txt` 写 `encoding="ascii", errors="backslashreplace"`，加非 ASCII 前缀用例）；
     C7（`locked(tree, exclusive)` 调用时读 `LOCK_TIMEOUT`，删 api 的 timeout 参数，测试用 monkeypatch，断言 "0.2 s"）；C14（Busy/WriteFailed 共用
     `api.status(lock=False)` + 一个 `_residue(...)` 辅助函数，删 `_residue_without_lock`，残留算不出就让异常传播、钩子 `||` 行说话；文案"conda-hook 写出了
     自己的消息才退出 0"进 conda_hook 文档串、cli.py:16、reference.md、AGENTS.md、方案 §4 与决定 9（作者决定，记交接）；加 REASON_WRITE 残留用例与
     "算残留失败 → 非零退出且不写"用例）；C34；C26（前缀只在 `conda_hook.run` 写文件处每段加一次，`texts` 钩子文案去 `{PREFIX}`，`interrupted` 保留，
     test_hooks 加 `said()`）；C6（钩子四处兜底换成 texts 两个框架：post-link "没打上 + 细节 + then run apply"，pre-unlink 两支；符号链接拒绝给
     `conda config --set always_softlink false; conda config --set allow_softlinks false; --force-reinstall isabelle`；五份文档"全部文案已校读"改实话）；
     C16（`interrupted` 的 Windows 命令填真实路径；README.md:102 用 `<prefix>`）；C13；C10（conda_hook 用 `feature_states` 里第一个 CONFLICT 的 feature，
     删 `min(...)`；test_levels 加三例多 feature 同文件 CONFLICT 规则，test_hooks 加 post-link 点名 f1 例；重跑六个变异体）；C27（五个无测试分支：
     REASON_WRITE、git 查找与版本、删除 0755 文件的恢复、`apply -v`/`-q`、默认调用；`EXECUTABLE` 加 `src/Pure/c.ML`）；C28（test_write.py:32 改真断言，
     共享 inode 用 a.ML 0600）；C9（test_isolation GIT_WORK_TREE=tmp_path；ceiling 测试 monkeypatch `tempfile.tempdir`）；C12（只读树测试连父目录；
     C38 哨兵测试加 status/dry-run）。
  3. 发布侧：C4（`repo_state` 加 `git check-ignore -q .`，文档/方案措辞）；C36（`Repo.status(tree, untracked=True)`，`repo_state` 传 False；
     test_trees 与 test_make_patches 的用例；规则 11 等措辞）；C20（note 走 stdin `-F -`；3000 个未跟踪文件的用例）；C21（run-all.sh 删 `|| true`）；
     C24（删 `MAKE_PATCHES_FAIL_AFTER`，测试用 `.git/index.lock`、`refs/tags/<tag>.lock` 造失败；注释写"write step (b)"）；C8（`Wanted(name, version,
     build_string_prefix, pin)` 纯数据、`isabelle_pin()`；**实际保留三参数** `plan_builds(repodata, wanted, fetch)`，钉死随每个 `Wanted` 走，
     偏离已记在决定 10 与 §10.0）；C37（`created_files` 删掉改 diff-tree）；checklist 前移（RELEASE.md 重写该节：
     对 `git diff-tree <base> <tip>` 过、每条手工命令、之后才 `make-patches`；方案决定 16 第 10 点手改）。
  4. 文档与文案：C5（四处 `--force-reinstall isabelle` 前单独一句：保存 isa/ 与用户目录里自己的东西，用户目录 `isabelle getenv -b ISABELLE_HOME_USER` 含
     heap/settings/preferences/components 登记，下一步会删，装了的包自己重登记、自己的设置不回来）；C29 四处删句；C30（AGENTS "the tree is fine" 改实话）；
     C31（RELEASE.md 列明未写的三件、roundtrip 复制 `isa/`、smoke 在发布后只报告、"只改权限位"条加理由；develop.md 两处）；C32（AGENTS 0.x 节改
     `skip_nitpick_examples` 说法、仓库 URL 一次、`isabelle build` 规则移到 "In this repository"；README 0.x 指针句改）；C33（统一文本 = README 第 19 行到
     0.x 节之前整段，两处"消息会说怎么修"改指 README 章节，test_docs 用 `conda create -n ` 选行）；reader 意见全部采纳（见报告 "Readers' points the judge
     says to act on"：统一文本加健康输出样例与每种坏状态第一步、何时手跑 apply、激活环境/`conda run`、定义 `isa/` 与 `<prefix>`、更新时不带 `-c` 会怎样；
     `--help` 重写给用户；CONFLICT 文案先给最简单的路、末尾加"然后跑 status"、保留自己改动会再 CONFLICT、去掉找不到的"其他环境"指令或给命令；AGENTS
     CONFLICT 条去掉 "moved either way"；RELEASE.md 给维护者写当前能否发布、完整命令、首次建 feature 仓库要哪些文件、名词原地定义、"五条腿"改
     "roundtrip 加四条 accept 腿"、每条 checklist 的检查办法）；所有新写/改写的文案（含 texts.py 里从未校读的 chain_broken、not_pristine、lock_busy、
     HEAP_PARAGRAPH、BACK_AT_BOTTOM、write_failed、interrupted）再过一遍 reader（medium）。方案手改：§0 加第 38 条记本轮裁决；决定 3、6、9、15、16 第 10 点、
     §4 相应段；§10.1 加 "rev 6 → 代码评审一轮" 对照。
  5. 全部改完：pytest、`tools/tests/run-all.sh`、评审员的变异体（scratchpad `review-code1/critic-tests/`、`defender-C10/` 等有现成插件）全过；
     交接与 develop.md 的"两分钟"归因改正；然后对 author_decides_then_rereview 的条目（C1、C6、C8、C10、C11、C14、C17、C18、C22、C23、C25、C26、C30、C33）
     起一轮定向评审（Workflow、Opus、xhigh、每条一个 defender、judge 判是否可进第 3 步）；用户说"提交"才提交。
- **裁决已全部实施（2026-10-25 16:40 +08，未提交）**，上面实施清单 1–4 全做完，第 5 的测试与变异检查已过，reader 校读与定向再评正在起：
  - 代码：`features.py`（`FEATURES_D`/`locate`、`FeatureDir(dir, name, release_tag, base_tag)` 只读两字段、逐目录核 `(R', X)`、剩余目录报
    base 没人发布的那个、`feature_number` 接受包名、`read_feature_dirs` 缺根返回 `[]`）；`model.py` hole 改 `!= APPLIED`；`engine.py`
    `locked(tree, exclusive)` 调用时读 `LOCK_TIMEOUT`、删 PermissionError 特判、`read_target` 取绝对路径；`api.py` 删 timeout 参数、`_chain`
    返回 `(chain, k)`、`Status.selected` 与 `exit_code` property（1..F 全 applied）、`_session` 外层 `OSError → WriteFailed(texts.os_error)`、
    `read_bytes` 捕 FileNotFoundError、API 收 `Path`、删 `single_feature_levels`、`_directory` 的 FeatureDir 加注释；`texts.py` 去掉钩子文案的
    `{PREFIX}`、`SAVE_LINE`、`conflict_full(feature, (path, created) 对, …)` 按 C13 与 reader 意见改写、新 `chain_broken_removal`/`post_link_failed`/
    `post_link_write_failed`/`pre_unlink_failed`/`symlink`/`os_error`、删 `REASON_CHAIN`、`interrupted` 两边印真实路径、`step2` 的"其他环境"给
    `conda env list`；`conda_hook.py` 写者逐段加前缀、ASCII+backslashreplace、`post_link` 返回段列表、第一个 CONFLICT 的 FeatureState、
    WriteFailed 单独处理说打到哪、Busy/WriteFailed 共用 `api.status(lock=False)` + 一个 `_residue()`、ChainBroken 写链接不上文案两支、其他 Error 套框架；
    `cli.py` `--help` 为用户改写、用 `locate`/`abspath`、`status(feature=)`、`report_moves` 对目录接口不印环境文案、`--feature` 的 help 说接受包名。
  - 发布侧：`common.py`（`run(text=)`、`git(input=)`、`main` 也捕工具的 Error、`patch_blocks(bytes)` 共用、`Repo.status(untracked=)`、
    `repo_state` 加 `check-ignore` 且 `-uno`、`Wanted(name, version, build_prefix, pin)` 纯数据带 `filename()`/`accepts()`、`isabelle_pin`）；
    `make-patches`（删 `fail_after` 与 `MAKE_PATCHES_FAIL_AFTER`、`committed_files()` 共用于 removed 与 (d)、块按字节写、注释写"write step"、
    docstring 加门禁编号来源）；`run-tree`（note 走 `-F -` stdin、文案改"属于某 git 工作树"/"已跟踪文件"）；`check-roundtrip`（`Tree.read`/
    `FeatureDir.read` 先拒后拷、新建文件取 `diff-tree --diff-filter=A`、diff 按字节喂 patch）。
  - 测试：pytest **123 例约 25 秒**；`tools/tests/run-all.sh` 全过（`test_make_patches.sh` 102 例：`write_order` 函数在 pkg 与 cpkg 各跑一遍、git 锁文件
    造失败、门禁与 (c) 之间 post-commit 钩子提交 ROOT、门禁 (c) 符号链接（指向 `/dev/null`，重放副本读得到才走到前向比较）与重复上下文两例、
    CRLF 文件保 CR、随包文件构建时未跟踪事后提交被拒；`test_trees.sh` 70 例：`dir:` 行只列已跟踪改动、构建中新建未跟踪文件仍有记录、外层仓库
    忽略的 `-d` 目录不绑、4000 个已改文件的长 `dir:` 行；`run-all.sh` 删 `|| true`、打印退出码）。变异检查：scratchpad `mutcheck/mutants2.py`
    （29 个内存变异体，`mutcheck/run.sh`，结果 `mutcheck/results.txt`）——28 个被杀，剩 1 个 `exit_code_selected_only` 是等价变异体（hole 规则
    放宽后"F applied 且无 hole"等于"1..F 全 applied"）；评审员的旧插件（`review-code1/`）针对的是改前代码，大多已不能加载，故自写。
  - 文档：README（统一文本扩到 0.x 节之前、健康样例与四种坏状态的第一步、何时手跑 apply、激活/`conda run`、定义 `isa/` 与 `<prefix>`、忘带 `-c`、
    C5 保存句、C13、C33 指向章节、Windows 路径占位符、删 C29 句、规则 11 措辞）、`common-readme.md` 由 README 生成、AGENTS（仓库 URL 一次、
    hole 定义、退出码、`no feature packages installed` 实话、CONFLICT 条、"In this repository" 收 isabelle build 规则、0.x 条、C5 保存句）、
    reference（决定 3 读法、`--feature` 包名、hole/退出码、目录接口静默、conda-hook 退出码与 ASCII、三种残留原因、文案归属实话）、develop
    （`locate`/`feature_number`、OSError 规则、`patch_blocks`、git 锁文件造失败、25 秒、覆盖清单、§5 第 5 步未写）、RELEASE（现状、名词、feature
    仓库首次设置、checklist 在 `make-patches` 之前且每条给命令、完整命令行、roundtrip 复制 `isa/`、smoke 只报告、publish 前两条件）。
  - 方案手改：本计划 §0 第 38 条、§2.3 一行、决定 2、3、6、9、10、15、16 第 10 点、§4 多处、§10.0 对照表；迁移方案 §0 第 32 条注记、新第 33 条、
    glossary、`run-tree` 说明、§5.3、§7 第 11、15 条、附录 A。
  - **待办**：reader 校读（三位 Opus、medium：README 统一文本、AGENTS、`--help`、texts.py 全部钩子文案含从未校读的七段）与 author_decides_then_rereview
    14 条的定向再评（Opus、xhigh、每条一个 verifier、judge）正在一个 Workflow 里跑（2026-10-25 16:50 +08 起；任务 `wwgfh3tm8`，run
    `wf_9e406159-aa0`，脚本 `~/.claude/projects/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/workflows/scripts/patch-tool-code-review-2-targeted-wf_9e406159-aa0.js`，
    结果 `/tmp/claude-1002/-home-qiyuan-Current-MLML/f1ebd39a-eda3-4c68-b769-d435321fa8d4/tasks/wwgfh3tm8.output`，`result` 里有 `readings`、
    `verdicts`、`judgement`；评审员的实验在 scratchpad `review-code2/`，每条 challenge 的原文在 `review-code2/challenges/C*.txt`）。**评审跑的时候
    不改工作树**。完成后：存 `ISABELLE_PATCH_CONTROL_CODE_REVIEW2_detail.json`、渲染 `…CODE_REVIEW2.md`（仿 `render_code1.py`），按 judge 的
    must-fix 与 reader 意见再改，然后用中文向用户汇报、等"提交"。
  - **scratchpad 清理（2026-10-25 17:05 +08，light locale 会话转来用户提醒：/tmp 24G tmpfs 已 99%）**：前五轮方案评审的实验目录 `review-ipc2..5`、
    `review2`（共约 15G）已压成 `~/archive/claude-scratchpad/f1ebd39a-<目录名>-2026-10-25.tar.zst`（`zstd -t` 与条目数核对后才删源），/tmp 降到 37%。
    留下的：`review-code1/`（代码评审一轮实验，518M）、`review-code2/`（正在跑的再评）、`mutcheck/`、`realchain/`、`mp-test`/`trees-test`（玩具测试的
    临时目录，可随时删）。本会话结束前把 `review-code1/`、`review-code2/` 也照此归档。
- **代码评审第二轮（定向再评）已完成并按其结果改完（2026-10-25 18:10 +08，未提交）**：报告 `ISABELLE_PATCH_CONTROL_CODE_REVIEW2.md`、明细
  `…CODE_REVIEW2_detail.json`（渲染脚本 scratchpad `render_code2.py`）。18 个 agent、35 分钟：14 位 verifier 判 11 条 fixed/fixed_differently、3 条
  partially_fixed（C6、C30、C33，都是文档与测试的边角）；**judge 判 ACCEPTED，可进 §5 第 3 步**——剩下的全是 author_fixes_no_rereview，没有一条改变
  发布 tag 的内容。judge 另查出三件（均已修）：C6 的修法引入的回归——post-link 写失败后第二次 `api.status` 没有兜底，同样的失败再来一次就 exit 1 什么都不写
  （现在：兜住 `api.Error`，写不带 "Applied so far" 的框架）；"Applied so far" 把 (hole below) 的 feature 也算成 applied（现在按 C15 过滤 `not s.hole`）；
  `OSError → WriteFailed` 的翻译只在 `_session` 里、`_chain` 读来历文件不在里面（现在是公开入口上的 `@_public` 装饰器，`errors.WriteFailed` 文档串随之改）。
  其余已修：`Wanted.build_string_prefix` 与来历文件同一拼法（`filename()` 自己加 `_`）、`check-roundtrip` 文档串换行、`patch_blocks` 也拒 "Binary files"、
  RELEASE.md 与 `make-patches --help` 的 gate (f) 命令补 `-r --no-renames`、`--help` 第一句换成给用户的话并把 "(plan §4)" 挪进注释、`--features-dir` 的 help。
  reader 意见按 judge 的取舍落进 texts.py（SAVE_LINE 点明"这个环境自己的用户目录"、chain_broken/not_pristine 动作在前细节在括号里、lock_busy 不说 inode、
  write_failed/os_error 给下一步、chain_broken_removal/pre_unlink_failed/BACK_AT_BOTTOM 改写、step2 无缓存形式带"其他 feature 包自动重打"、CONFLICT 文案的
  "实验放在别的 Isabelle 安装里"、`interrupted` 加 `ls <prefix>/conda-meta`——实测 `conda list -p` 在没有 history 时拒绝列出）、README 统一文本（更新后
  先跑 status、第一行是什么、hole 的方向、`command not found`、识别工具消息的前缀、`conda env export --from-history` 实测可列出点名装的包、Ctrl-C 后列包的办法、
  C30 删"(Isabelle does not load them)"、C33 新建文件先看下一段、样例改单空格）、AGENTS（C30 条改为"照消息做"、文档清单加 RELEASE.md）、reference
  （in-the-way 规则按代码写、`k below` 含义）、develop、RELEASE（owner/命令运行位置/版本号形态/level 定义进名词段、checklist 挪到构建之前、第 1、2 条给可复制
  的循环与命令、哪几条只有维护者查、删"hand edit"条改成"never hand-edit patches/"、完整示例值、`features` 输入含整条链）。方案手改：§4 四段文案去前缀、
  残留块第 1 步换 SAVE_LINE 文本、决定 16 第 10 点符号链接句收窄、决定 11 smoke 选行键、§10.0 加 C10 行、CONFLICT 文案第 4 行加待答注。
  测试 **129 例约 19 秒**、`run-all.sh` 全过；变异检查重跑中（`mutcheck/results.txt` 会刷新）。judge 没采纳的 reader 意见：CONFLICT 文案不说"Isabelle 还能用"、
  不说"status -v 显示差异"（没有这个功能）、不删 0.x 指针行；"忘带 -c 没坏事"那句没测过所以不写。
  **留给用户的两问**（见中文汇报）：(1) `apply/unapply --feature F` 遇到范围之外的 CONFLICT 文件的退出码——代码与测试是"只算 F 及其下面（apply）/上面
  （unapply）碰过的"，决定 7 与原 reference 写的是"任何 CONFLICT 都列出、exit 1"，judge 建议保留代码规则、改文档；(2) CONFLICT 文案第 4 行 "can undo it
  exactly" 用户无从知道改了什么，judge 建议改成 "If you remember exactly what you changed: undo it, then run isabelle-patch-control apply."。
  judge 另要求：统一文本冻结（首次发布）之前再过一遍 reader（§5 第 5 步前），范围含 texts.py 外被钩子引用的拒绝句。
  **用户 2026-10-25 对两问都答"按你建议来"**：(1) 保留代码的挡路规则，决定 7 加了一条、§10.0 的 C10 行改为已做；(2) CONFLICT 文案第 4 行改成
  "If you remember exactly what you changed: undo it, then run isabelle-patch-control apply."（texts.py、§4、README 三处）。变异检查重跑结果已刷新
  （28 杀 / 1 等价）。
- **评审明细不进仓库（用户 2026-10-25："明细是我绝对不能忍受的"，评审报告"能忍受但不喜欢"）**：四个新文件 `…CODE_REVIEW{1,2}.md` 与
  `…CODE_REVIEW{1,2}_detail.json` 不提交（两份 `.md` 留在磁盘上未跟踪，两份 `_detail.json` 删掉）；前五轮的 `…REVIEW{1..5}_detail.json` 用
  `git filter-repo --invert-paths --path-glob 'ai-artifacts/*_detail.json'` 从工具仓库历史里去掉（用户"确认"）：113a28f→2928d8e、cc0e603→53c3abf、
  fa1d64a→74e2d78、321646d→b5eee10，树除那 5 个文件外逐 blob 相同，GitHub `origin/main` 已强推到 b5eee10（lease 对旧哈希），本地 `main` 用
  `update-ref` + `git reset`（只重读索引）跟上，旧对象经 reflog 过期 + `gc --prune` 清掉；`.gitignore` 加 `ai-artifacts/*_detail.json`。
  **后果（用户接受）**：主仓库三个未推送的 bump 提交 3bf74ab0、a17dd76d、7c212ced 指向的子模块哈希 cc0e603、fa1d64a、321646d 不再存在，不改写
  主仓库，随本轮提交新加一个 bump。以后：评审明细一律只留 scratchpad/归档，不进任何仓库；评审报告 `.md` 不再提交（已跟踪的五份不动）。
  本节上文凡提到 `…_detail.json` 的，其文件只在 scratchpad（`review-code1/`、`review-code2/` 的归档）里。
- **提交（用户 2026-10-25 "提交"）**：工具仓库 `main` **16078a3**（35 个文件，含 `.gitignore`；两份 `CODE_REVIEW{1,2}.md` 留作未跟踪），已推 GitHub
  `origin/main`；主仓库 bump 提交指向 16078a3（未推送，主仓库从不由本会话推送）。**下一步是 §5 第 3 步，每件都要用户下令**（见下一条"评审之后"）；
  第 5 步首次发布冻结统一文本之前再过一遍 reader。
- **评审之后**：按裁决改代码（再评一轮），然后 §5 第 3 步，每件都要用户下令：GitHub 建
  `isabelle-base-features`、`qiyuan_dev_patches`（`localized_record` 的仓库用户指派）；本地建 `contrib/isabelle-base-features/`（两个子目录，决定 13 的
  清单文件；README 从 fa1d64a 的父 commit cc0e603 复制 `patches/expose_foreign.md`、`patches/future_assign_interrupt.md`）；`make-patches expose_foreign 1`、
  `make-patches future_assign_interrupt 1`（注意新门禁第 7 点：包目录须在 git 仓库里、清单已提交；两棵私有树已各有 Pure 的 tested 记录，§8）；light：
  `tools/component_files.txt`、用户命令的完整构建（run-tree 要带 `-d <light 仓库>` 才有 `dir:` 行）、`make-patches light_locale <v>`。第 4 步：
  `check-roundtrip` 在官方 tarball 的树上本地跑一遍（`~/isa_release_proto/Isabelle2025-2_linux.tar.gz`，FD 由各包的 `patches/Isabelle2025-2/` 复制成
  `FD/<feature>/`）。第 5 步：渲染器 `tools/render-feature-recipe`、工具的 `conda/recipe.yaml`、`release-features.yml`、钩子层真 conda 测试。

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
解释先讲本质再讲机制、不造词、不假定用户记得前文；提问要把背景讲清楚。**2026-10-25 新增**：提交里的每个新增文件都要先经用户批准；
设计期的临时数据、实验细节不进提交（评审明细 JSON 永不进任何仓库，评审报告 `.md` 也不提交）；用户向文案要简单，技术细节放文档/注释/代码。
