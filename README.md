# 正大杯研策 · Zhengda Research Copilot

**面向正大杯参赛团队的研究助手：把选题、问卷、数据分析和报告，连成可复核的工作流程。**

[![Tests](https://github.com/zhulehan683-commits/zhengda-research-copilot/actions/workflows/tests.yml/badge.svg)](https://github.com/zhulehan683-commits/zhengda-research-copilot/actions/workflows/tests.yml)
[![Preview](https://img.shields.io/badge/status-preview-f59e0b)](docs/VALIDATION.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab)](docs/INSTALLATION.md)

[快速开始](#快速开始) · [研究能力](#研究能力) · [Grill Me](#grill-me先把研究方案问清楚) · [Find Skills](#find-skills按具体任务补足能力) · [安装与适配](#安装与适配) · [验证](#验证与边界)

正大杯研策是一套 Agent Skill，包含研究指引、交付模板和本地审核脚本。可以从零开始准备比赛，也可以只审核一份问卷、分析计划或答辩提纲。默认提供第十七届（2026—2027）规则基线，具体要求以本人适用的当届主办方、赛区和学校通知为准。

当前为 Preview，非主办方官方产品。真实调查、研究判断和正式提交由参赛团队完成。

## 快速开始

准备支持 `SKILL.md` 的 Agent。联网安装需要 Node.js/npm 和 Git；运行本项目脚本需要 Python 3.10+，仅用标准库。

以 Codex 全局安装为例：

```sh
npx skills add zhulehan683-commits/zhengda-research-copilot --skill zhengda-research-copilot -g -a codex -y
```

使用其他 Agent 时替换 `-a`，常见标识和路径见[安装与适配](#安装与适配)。去掉 `-g` 可安装到当前项目。新开会话或刷新技能列表后输入：

```text
使用 $zhengda-research-copilot。
我准备正大杯，目前只有初步方向，还没有调查数据。
先比较三个可执行选题，说明研究对象、数据渠道、成本和淘汰理由。
已有材料先读取，缺少的事实标注待核验。
```

你应得到候选选题及可行性比较、尚缺的材料和下一步设计工作。没有数据时输出方案和待验证假设；需要建立研究工作区时，再提供实际项目目录。更多会话示例见 [CODEX_START.md](CODEX_START.md)。

想先查看或临时试用：

```sh
npx skills add zhulehan683-commits/zhengda-research-copilot --list
npx skills use zhulehan683-commits/zhengda-research-copilot --skill zhengda-research-copilot
```

`use` 下载资源并打印入口提示词，不启动模型，也不代表客户端已原生加载。

## 研究能力

| 你现在有什么 | 本轮可以得到什么 | 主要入口 |
| --- | --- | --- |
| 一个模糊方向 | 选题比较、研究问题、样本可达性和预算取舍 | [研究简报](templates/research-brief.md)、[选题评分表](templates/topic-scorecard.csv) |
| 一份待定方案 | 分轮压力提问、决定与假设清单 | [Grill Me](references/grill-me.md) |
| 问卷草稿 | 逐题审核、构念与变量映射、抽样和预测试计划 | [逐题审核表](templates/questionnaire-review.csv)、[问卷与抽样](references/survey-quality.md) |
| CSV 和变量字典 | 缺失、类型、范围、重复 ID、列结构的汇总预检 | [预检合同](templates/data-preflight-schema.json)、`survey_audit.py` |
| 真实数据与研究问题 | 方法选择、诊断、可复现代码及结果解释指引 | [测量与推断](references/measurement-and-inference.md)、[方法路由](references/method-routing.md) |
| 已核验的结果 | 图表、报告证据对应、篇幅安排、答辩问答 | [可视化](references/visualization-guide.md)、[报告生产](references/report-production.md)、[报告与答辩](references/report-defense.md) |
| 当前工具无法完成的产物 | 经来源核验的外部 skill 候选与接入方式 | [Find Skills](references/find-skills.md) |

统计模型、Word/PPT 导出等由 Agent 实际可用的工具执行；Python/R/SPSS/AMOS/MATLAB 不随技能安装。只有真实、合规且相关的文本才启用[文本分析](references/text-analysis.md)。

全流程覆盖 13 阶段：

```text
报名 → 知识赛 → 组队 → 选题 → 文献与二手研究 → 调查设计
     → 预调查 → 正式调查 → 清洗 → 统计分析 → 报告 → 答辩 → 提交
```

单阶段咨询可以独立开展。正式阶段放行需要前序证据和实际复核；详见[阶段地图](references/stages.md)与[质量门禁](references/gates.md)。

## Grill Me：先把研究方案问清楚

已整合 [mattpocock/skills](https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity) 的 `grill-me` 与 `grilling`。前者是入口，后者执行分轮提问，因此两者一起保存。

```text
使用正大杯研策，grill me。
我们想研究大学生对校园二手交易平台的使用。
本轮只讨论研究问题与样本可达性，每轮给出建议和理由，
等我回答后再展开依赖这些答案的问题。
```

Agent 先读已有材料，区分事实与待作决定；同轮只问前置条件已确定的问题。例如研究对象未定，就先澄清对象，再讨论抽样配额。能查证的事实自行查询，用户负责预算、渠道和目标等决策。

讨论结束时，用一段完整说明讲清研究如何实施，再列已决定事项、待核验事实和剩余风险。用户确认后接入研究简报、抽样计划或分析合同。纯讨论不自动初始化项目或批准阶段。

研究适配与结束条件见[压力测试指南](references/grill-me.md)。已明确的执行任务直接推进，无需每次先访谈。

## Find Skills：按具体任务补足能力

已整合 [vercel-labs/skills 的 find-skills](https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/skills/find-skills/SKILL.md)。

```text
使用正大杯研策的 Find Skills。
我们的报告需要导出 DOCX 并检查排版。
先看当前已安装技能；不足时再查 GitHub 和 skills.sh。
给出候选用途、依赖、来源提交、许可证和未验证点。
```

发现路径：当前可用技能 → [skills.sh](https://skills.sh) / `npx skills find` → GitHub 原文与依赖核验 → 最少必要候选 → 按已授权范围安装并验证。

安装数和 stars 只作发现线索。统计前提、文件格式、数据去向和实际依赖决定技能是否合适。外部产物接回当前研究流程，项目状态仍由统一门禁管理；详细规则见[技能发现指南](references/find-skills.md)与[集成说明](references/integrations.md)。

## 安装与适配

同一份主技能可供多个 Agent 使用。Skills CLI 可重复指定 `-a`；只选择实际使用的执行端。

| Agent | Skills CLI 标识 | 常见全局技能根目录 |
| --- | --- | --- |
| Codex | `codex` | `~/.agents/skills` |
| Claude Code | `claude-code` | `~/.claude/skills` |
| CodeBuddy / WorkBuddy | `codebuddy` | `~/.codebuddy/skills`，以实际产品配置为准 |
| Hermes Agent | `hermes-agent` | `~/.hermes/skills`，可受 `HERMES_HOME` 影响 |

DSH 等执行端可由主控显式提供技能入口和本轮参考资料。更多 Agent、配置目录差异、ZIP、更新、恢复与旧名迁移见[安装指南](docs/INSTALLATION.md)。

### 离线安装与 D 盘主副本

clone 或完整 ZIP 解压后，在仓库根目录运行：

```sh
git clone https://github.com/zhulehan683-commits/zhengda-research-copilot.git
cd zhengda-research-copilot
python install.py --dry-run
python install.py
python install.py --verify
```

默认安装到 `~/.agents/skills/zhengda-research-copilot`。Windows 可将唯一主副本放在 D 盘，并链接实际技能根目录：

```powershell
python install.py --target-root D:\AgentSkills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.codebuddy\skills"
python install.py --target-root D:\AgentSkills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.codebuddy\skills" --verify
```

已有目标默认拒绝覆盖；升级时核对后加 `--force`，旧版会备份。Windows 使用 Junction，POSIX 使用符号链接；无法建立链接时加 `--mode copy`，更新后重新同步。同一副本选择 Skills CLI 或离线安装器之一维护。

### 子技能如何随包使用

项目级 `.agents/skills/{grill-me,grilling,find-skills}/SKILL.md` 是可直接执行的研究适配入口，包含无 Skill 工具时的行为、研究范围和项目级安装默认值。完整上游原文另存于 `references/upstream-skills/`，固定版本供来源对照；两套文件都随离线主包安装。

子技能能否被客户端单独发现取决于扫描目录和客户端版本；主技能可直接读取适配入口，无需再次联网。独立加载入口时也使用相同研究规则。内嵌文件不会自动注册成三个全局技能，来源、差异和单独安装方式见[整合记录](docs/SKILL_INTEGRATION.md)。

## 用本地工具核对真实材料

以下命令从主技能根目录执行；从其他目录调用时使用脚本绝对路径。研究工作区与技能安装目录分开。

```powershell
$project = 'D:\Competitions\MySurvey'
python scripts/workflow.py init --project $project
python scripts/workflow.py status --project $project
```

`init` 拒绝覆盖已有状态，恢复项目直接用 `status`。设计阶段用[设计清单](templates/design-manifest.json)绑定问卷、变量字典和[分析合同](templates/analysis-contract.csv)；分析阶段用[分析清单](templates/analysis-manifest.json)绑定输入、代码、配置、结果与复现命令。依赖变化会使旧验收失效。

### CSV 预检

将获准的原始 CSV 放在工作区 `raw_private/`，按真实变量字典填写[预检合同模板](templates/data-preflight-schema.json)，保存为 `plans/data-schema.json`，然后运行：

```powershell
python scripts/survey_audit.py --project $project --data raw_private/survey.csv --schema plans/data-schema.json --output analysis/data-preflight.json
```

退出码 `0` 为 `READY_FOR_REVIEW`，`3` 为 `BLOCKED`，`2` 为输入/执行错误。原数据保持不变，输出只含汇总诊断与哈希；预检不计算信效度或显著性，不自动删行。Schema 拒绝未知字段和未实现的约束。输出必须新建在 `analysis/`，重跑时更换文件名。

### 命令导航

| 需求 | 入口 |
| --- | --- |
| 证据登记、阶段门禁和复核记录 | `python scripts/workflow.py --help`；具体流程见[质量门禁](references/gates.md) |
| 输入快照、执行回执与任务签收 | `python scripts/task_queue.py --help`、[Agent 协作](references/agents.md) |
| 七维评分与问题汇总 | `python scripts/score_review.py --help`、[角色与复核](references/roles-and-review.md) |
| 更多研究模板 | [模板索引](templates/README.md) |

`gate` / `review` 的阻断或不通过返回 `3`，输入错误返回 `2`。任务队列登记交接，实际调用执行端由外部编排器完成；签收前需核对真实产物和验收日志。

## 验证与边界

在源码仓库根目录执行回归测试：

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

CI 配置覆盖 Windows/Linux、Python 3.10—3.13。当前运行结果以顶部 Actions 为准；本地测试、安装校验和有限模型场景记录见[验证记录](docs/VALIDATION.md)。文件安装、客户端发现、脚本运行和模型完成任务分别验证。

- 无真实数据时交付设计、代码框架或待填结果表；模拟数据只能用于明确标注的测试。
- 预检、哈希和评分辅助复核，不能证明调查真实、统计正确或评审独立。
- 便利样本的结论先限定于本次受访样本，扩大样本或 bootstrap 不自动赋予总体代表性。
- 学校代码、校赛日期、提交规则与 AI 使用要求须核对适用通知。
- 受访者标识与敏感数据保留在私有工作区，外部处理前完成授权与脱敏。

目前未验证真实参赛项目从调查到正式提交的无人值守全流程。

## 来源、许可与贡献

| 已整合来源 | 本项目用途 |
| --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Grill Me / grilling 原文与研究决策压力测试 |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | find-skills 原文与外部能力发现 |
| [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) | 方法路由、文本、图表、报告契约与模板 |
| [mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill) | 角色边界、复核和评分函数 |
| [questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill) | 清洗、测量与报告框架，补充推断边界 |

固定提交、逐文件 SHA-256、适配差异和完整上游许可见[第三方声明](THIRD_PARTY_NOTICES.md)、[来源锁文件](docs/upstreams.lock.json)与[整合记录](docs/SKILL_INTEGRATION.md)。本次 README 结构参考 [README Skills](https://github.com/Shiaoming123/readme-skills)，按本仓库实际能力重写，未将该写作技能打包为研究依赖。

本项目目前没有 `LICENSE` 文件，原创部分许可证尚未决定；各上游 MIT 许可只适用于对应内容。见[许可决定记录](LICENSE-DECISION.md)。反馈与协作请阅读[贡献规范](CONTRIBUTING.md)和[隐私说明](SECURITY.md)，不要提交真实受访者数据或密钥。
