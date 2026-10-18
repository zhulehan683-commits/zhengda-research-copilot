# 正大杯研策 · Zhengda Research Copilot

**把选题、问卷、统计和报告连成一条可复核的研究链。**

[![Tests](https://github.com/zhulehan683-commits/zhengda-research-copilot/actions/workflows/tests.yml/badge.svg)](https://github.com/zhulehan683-commits/zhengda-research-copilot/actions/workflows/tests.yml)
![Status](https://img.shields.io/badge/status-preview-f59e0b)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab)

面向「正大杯」全国大学生市场调查与分析大赛的 Agent Skill。支持从报名、知识赛、选题到调查、建模、报告与答辩的 13 阶段流程，也可以只用一个阶段。内置第十七届（2026—2027）规则基线；当届主办方及本人适用的学校/赛区通知优先。本项目非主办方官方产品。

同一套 `SKILL.md + references + scripts + templates` 可供不同 Agent 使用。它提供研究指引和可执行的本地审核工具，团队仍需完成真实调查、科学判断和正式提交。

## 这次升级了什么

| 能力 | 实际作用 | 边界 |
| --- | --- | --- |
| 问卷与分析合同 | 逐题审核构念、时间窗、选项、跳题、编码，提前约定主要分析与排除规则 | 不能代替预测试和调查实施 |
| CSV 数据预检 | 检查必填缺失、类型、取值范围、重复编号、CSV 列结构；输出汇总诊断和哈希 | 不修改原数据，不自动剔除，不计算信效度或显著性 |
| 研究合同冻结 | `design_manifest` 把问卷、变量字典和分析合同纳入哈希链；改动任一依赖会撤销旧验收 | 只证明依赖文件未变，不证明问卷或方法本身正确 |
| 计算依赖追踪 | `analysis_manifest` 记录输入、代码、配置、结果和复现命令；辅助文件变化会使分析失效 | 需要用户显式列全依赖，不做自动依赖扫描 |
| 测量与推断指引 | 反向计分、缺失机制、EFA/CFA、效应量、多重比较、非概率样本和复杂抽样边界 | 按研究设计判断，不能靠阈值认证科学性 |
| 统一安装 | 共用主副本，可为不同 Agent 建链接；提供离线安装、备份、回滚和哈希校验 | 原生加载和模型调用需各自验证 |
| 证据链与状态 | 文件 SHA-256、前序门禁、独立复核记录、上游变化使下游验收失效 | 身份、来源真实性和复核质量仍需人工核实 |
| 多 Agent 任务交接 | 创建任务时绑定输入快照，提交时可记录实际命令、退出码和日志；输入漂移会标为失效 | 本地队列不是后台调度器，不自动调用其他 Agent |
| 报告与答辩 | 方法路由、图表审核、正文证据绑定、篇幅预算、答辩问题 | 没有真实结果时只给计划、模板或占位结构 |

运行资源仅依赖 Python 3.10+ 标准库；Python/R/SPSS/AMOS/MATLAB 等统计软件由实际分析任务另行选用，不随 skill 安装。

## 安装：不同 Agent 用同一份技能

### 联网安装（Skills CLI）

需要 Node.js/npm 和 Git，按 [Skills CLI 官方说明](https://github.com/vercel-labs/skills)选择你正在使用的 Agent：

```sh
npx skills add zhulehan683-commits/zhengda-research-copilot --skill zhengda-research-copilot -g -a codex -a claude-code -a codebuddy -a hermes-agent -y
```

可删去不用的 `-a`，如只保留 `-a codex`。去掉 `-g` 则安装到当前项目。先查看可发现的技能：`npx skills add zhulehan683-commits/zhengda-research-copilot --list`。联网安装与更新由 Skills CLI 管理，未承诺其支持所有产品的所有版本。

### 离线 / D 盘统一安装

clone 或完整 ZIP 解压后进入仓库根目录：

```sh
git clone https://github.com/zhulehan683-commits/zhengda-research-copilot.git
cd zhengda-research-copilot
python install.py --dry-run
python install.py
python install.py --verify
```

默认主副本在 `~/.agents/skills/zhengda-research-copilot/`。Windows 可把主副本放到 D 盘，再让实际 Agent 技能目录链接到它：

```powershell
python install.py --target-root D:\zlh\agents\skills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.claude\skills" --agent-root "$HOME\.codebuddy\skills" --agent-root "$HOME\.hermes\skills"
python install.py --target-root D:\zlh\agents\skills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.claude\skills" --agent-root "$HOME\.codebuddy\skills" --agent-root "$HOME\.hermes\skills" --verify
```

`--agent-root` 是实际的 skills 根目录，可重复指定；只保留真实存在的 Agent 目录，不要为了“统一”创建没有产品使用的路径。Windows 使用 Junction，POSIX 使用符号链接；无法链接时用 `--mode copy`，升级时重新同步副本。已有目标默认拒绝覆盖；确认后加 `--force`，旧版备份到技能扫描根之外。Windows 的 `install.ps1` 委托同一 Python 安装器，不再整仓复制 `.git` 和测试缓存。文件安装成功不等于原生发现或模型执行成功，验证分层见安装指南。

**Agent 路径、ZIP、更新、恢复和旧名迁移见 [安装指南](docs/INSTALLATION.md)。** 同一安装副本选择一种安装方式维护。旧标识 `market-survey-competition` 的研究状态可继续使用；归档旧技能后再启用新名，避免重复触发。

## 先选一个入口

不必一次跑完 13 个阶段。第一次使用先选最接近当前材料的一项：

1. **还没有选题或数据**：让 Agent 读取 `templates/research-brief.md` 和 `templates/topic-scorecard.csv`，输出 3 个候选选题、研究对象、数据可达性、成本和淘汰理由；不要生成调查结果。
2. **已有问卷草稿**：让 Agent 读取 `templates/questionnaire-review.csv`、`templates/analysis-contract.csv` 和 `references/measurement-and-inference.md`，逐题检查构念、选项、跳题、编码、主要分析和排除规则，输出待修改清单。
3. **已有 CSV 和变量字典**：先按 `templates/data-preflight-schema.json` 写真实 schema，再运行 `survey_audit.py`；从 `READY_FOR_REVIEW` 进入人工复核，不要把它当成统计显著性通过。

首轮草稿不需要先补造前序 `passed` 记录，也不会重置已有项目。只有正式阶段放行才需要完整证据和独立复核。

## 开始使用

新开已加载技能的 Agent 会话，例如在 Codex 中输入：

```text
使用 $zhengda-research-copilot。
我准备第十七届正大杯本科组，只有初步方向，还没有真实调查数据。
本轮目标：比较可执行选题，给出问卷与采样计划。
项目目录：<填写实际研究目录>。
读取已有材料和状态；缺少学校通知时标记待核验。
不要生成调查结果；每个建议说明依据、限制和下一步。
```

其他 Agent 可直接说“使用正大杯研策 skill”，或按其技能调用语法指定 `zhengda-research-copilot`。启动模板见 [CODEX_START.md](CODEX_START.md)，其流程也适用于其他执行端，不要求固定的模型供应商。

按本轮阶段补充赛事/组别、已有材料、研究对象和交付目标即可；报名与复习不要求先确定选题，PPT 草稿也不要求先补全全部前序状态。正式阶段放行仍需要完整证据。

### 用真实数据做预检

1. 把获准的原始 CSV 放到独立研究工作区 `raw_private/`。
2. 按真实变量字典修改 [预检合同模板](templates/data-preflight-schema.json)，保存为工作区 `plans/data-schema.json`。
3. 从 skill 根目录运行（路径为示例，换成实际研究目录）：

```powershell
$project = 'D:\Competitions\MySurvey'
python scripts/survey_audit.py --project $project --data raw_private/survey.csv --schema plans/data-schema.json --output analysis/data-preflight.json
```

退出码 0 为 `READY_FOR_REVIEW`，3 为 `BLOCKED`（需处理的数据合同问题），2 为输入/执行错误。输出只含汇总计数和哈希，原数据保持不变。重复编号可能来自追访或多波次，需解释；预检通过不代表样本有效、量表有效或代表总体。Excel/SPSS 等文件先在获准环境导出 CSV 并保留编码信息。

Schema 只接受已实现的约束：`schema_version`、`description`/`note`、`id_column`、`missing_values`、`variables`；变量规则支持 `type`、`required`、数值 `min`/`max`、`allowed_values`、`description` 和 `label`。拼错字段或写入脚本尚不执行的规则会返回输入错误，而不是静默通过。空白格始终按缺失处理。

诊断文件只允许新建在 `analysis/` 内；重复运行时换一个输出文件名，已有文件及项目状态不会被覆盖。

### 初始化或恢复项目

以下命令从 skill 根目录执行；研究工作区与安装目录分开：

```powershell
python scripts/workflow.py init --project $project
python scripts/workflow.py status --project $project
```

`init` 拒绝覆盖已有状态；已初始化时直接 `status`。脚本不会自动报名或生成实证数据。

进入设计阶段时，用 `templates/design-manifest.json` 冻结问卷、变量字典和分析合同；进入分析阶段时，用 `templates/analysis-manifest.json` 列出输入、代码、配置和结果。两者都必须在项目内保存并由 `evidence add` 绑定。修改清单中的任一依赖后，旧阶段会机械失效，必须重新复核。

## 按阶段找工具

```text
报名 → 知识赛 → 组队 → 选题 → 文献与二手研究
                              ↓
调查设计 → 预调查 → 正式调查 → 清洗 → 统计分析
                              ↓
                   研究报告 → 答辩 → 提交
```

| 本轮目标 | 入口 / 产物 |
| --- | --- |
| 核对阶段与材料 | [阶段地图](references/stages.md)、[质量门禁](references/gates.md) |
| 选题、行业与竞品研究 | [研究设计](references/research-design.md)、[市场研究](references/market-research.md) |
| 审核问卷、抽样与分析计划 | [问卷与抽样](references/survey-quality.md)、[测量与推断](references/measurement-and-inference.md)、[逐题审核表](templates/questionnaire-review.csv)、[分析合同](templates/analysis-contract.csv) |
| 清洗、测量和建模 | `scripts/survey_audit.py`、[统计复现](references/analysis.md)、[方法路由](references/method-routing.md) |
| 有真实文本时做内容分析 | [文本分析](references/text-analysis.md)；词云仅为入口图 |
| 图表、报告与答辩 | [可视化](references/visualization-guide.md)、[报告生产](references/report-production.md)、[报告与答辩](references/report-defense.md) |
| 交接、复核与评分 | [Agent 协作](references/agents.md)、[角色与复核](references/roles-and-review.md)、`task_queue.py`、`score_review.py` |

## 命令速查

| 需求 | 从 skill 根目录执行 |
| --- | --- |
| 查看项目状态 | `python scripts/workflow.py status --project <项目目录>` |
| 登记真实证据 | `python scripts/workflow.py evidence add --project <目录> --stage <阶段> --key <键> --file <项目内文件> --author <作者>` |
| 检查阶段 | `python scripts/workflow.py gate --project <目录> --stage <阶段>` |
| 记录实际复核 | `python scripts/workflow.py review --project <目录> --stage <阶段> --reviewer <复核者> --decision pass --note <核验说明>` |
| CSV 预检参数 | `python scripts/survey_audit.py --help` |
| 本地任务交接参数 | `python scripts/task_queue.py --help` |
| 七维评分汇总 | `python scripts/score_review.py <已填写的复核JSON>` |

`gate` 通过只表示机械检查通过；`review` 是留痕，不能证明 reviewer 的身份与独立性。`gate` / `review` 退出码 3 表示阻断或复核不通过，2 表示输入/执行错误；调用脚本时不要只判断“进程有没有启动”。`task_queue.py` 记录创建、认领、提交和复核，不会自动启动其他 Agent。创建任务时用 `--input` 绑定输入；提交时可记录 `--command`、`--exit-code` 和 `--log`。外部执行端必须实际调用、产生文件、运行验收，才算交付。

## 借鉴了哪些 Skill

| 来源 | 已整合的内容 | 本项目适配 |
| --- | --- | --- |
| [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) | 方法路由、文本、图表、报告生产契约与模板 | 映射到本项目 13 阶段与证据链 |
| [mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill) | 三角色交付边界、权重与评分函数 | 七维输入校验，评分不代替阶段批准 |
| [questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill) | 清洗、测量诊断与结果报告框架 | 修正机械阈值、缺失机制与共同方法偏差断言，加入非概率抽样限制 |

以上适配内容随本项目安装，无需再安装上游；不是自动调用那些技能。固定提交、文件哈希、适配差异和完整许可见 [第三方声明](THIRD_PARTY_NOTICES.md) 与 [来源锁文件](docs/upstreams.lock.json)。其余可选参考见 [集成说明](references/integrations.md)。

## 验证与已知限制

在**源码仓库**根目录运行：

```sh
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/workflow.py --help
python scripts/task_queue.py --help
python scripts/survey_audit.py --help
python scripts/score_review.py --help
```

覆盖项目状态、证据失效、原始数据私有路径、符号链接与 Windows Junction、任务交接、评分、安装哈希/备份和 CSV 预检。CI 在 Windows/Linux 与 Python 3.10—3.13 上运行；平台特定用例可能跳过，当前结果以 Actions 为准。具体本地实测、外部执行端回执与限制见 [验证记录](docs/VALIDATION.md)。离线最小安装包不含单元测试，贡献者应在 clone 的源码副本运行测试。

- 没有真实数据时只交付研究方案、问卷、代码框架或待填结果表。
- 没有验证真实参赛项目全流程的无人值守执行，文件哈希不能证明调查真实或统计正确。
- 便利样本不能因大样本、信效度或 bootstrap 自动获得总体代表性；高级模型必须满足测量、设计和诊断条件。
- 赛事规则快照不是实时公告，校赛日期、报名代码与提交要求必须核对本人适用通知。
- 受访者标识与敏感数据留在私有工作区，分享/外部处理前完成授权与脱敏。

## 目录

```text
SKILL.md                         Agent 入口
agents/openai.yaml               展示名称与默认启动提示词
install.py / install.ps1         统一离线安装与哈希核验
scripts/                        状态、交接、评分、CSV 预检
references/                     阶段、研究方法与交付指南
templates/                      研究、问卷、分析与报告合同
competitions/zhengda-17/         第十七届规则基线
licenses/                       上游完整许可
docs/                           安装、验证、来源与发布记录
tests/                          源码回归测试
```

## 许可与贡献

本项目目前没有 `LICENSE` 文件，原创部分许可证尚未决定，不能默认将整个仓库视为 MIT。已合并上游内容各自保留原许可；详见 [许可决定记录](LICENSE-DECISION.md)。贡献前阅读 [贡献规范](CONTRIBUTING.md) 与 [隐私说明](SECURITY.md)，不要提交真实受访者数据或密钥。
