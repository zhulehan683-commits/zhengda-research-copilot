# Market Survey Competition

**从选题到答辩，让每一步研究都有证据。**

*An Agent Skill for evidence-driven market research competitions.*

![Project status](https://img.shields.io/badge/status-preview-f59e0b)
[![Tests](https://github.com/zhulehan683-commits/market-survey-competition/actions/workflows/tests.yml/badge.svg)](https://github.com/zhulehan683-commits/market-survey-competition/actions/workflows/tests.yml)
![Skill](https://img.shields.io/badge/Agent-Skill-334155)
![Competition](https://img.shields.io/badge/first%20preset-Zhengda%20Cup-0f766e)

`market-survey-competition` 是面向大学生市场调查与分析竞赛的 **Agent 工作流 Skill**。它以**第十七届正大杯（2026—2027）**为首个赛事配置，将知识赛准备、选题、问卷与抽样、真实调查、统计建模、研究报告和答辩串成一条可记录、可复核、可交接的工作链。

它不是"一键生成获奖论文"的工具。我们希望解决的是一个更实际的问题：**当研究跨越多周、多名队员与多个 AI Agent 时，如何确保问题、数据、结论和交付物始终对应？**

> **项目状态：Preview（可安装初版）**
>
> 当前版本已整合 13 阶段规范、SHA-256 证据登记、本地任务交接、方法路由、文本/图表审计、报告生产契约、角色复核与七维评分，并通过 27 项自动化测试中的 26 项（1 项因 Windows symlink 权限跳过）。**尚未实现自动调用其他 Agent 的运行时调度器**，也没有验证完整真实参赛项目的端到端无人值守执行。项目非正大杯主办方官方产品。

## 为什么需要它？

一次市场调查竞赛不只是写一份报告。中途可能发生问卷改版、样本剔除、模型重算、图表过期、团队交接、赛事规则变动，甚至答辩 PPT 仍在引用旧数据。

普通聊天式 AI 可以完成某个局部任务，但很容易丢失跨阶段的决策依据。这个 Skill 采用 **「阶段 → 证据 → 检查 → 独立复核 → 状态更新」** 的方式组织研究：

- **不丢上下文**：将阶段进度和证据索引写入项目目录，而非只放在聊天记录里。
- **不让数字凭空出现**：结论必须关联真实来源、数据、代码或可核验的文献。
- **不把"生成了"当"完成了"**：文件检查、科学性审查和竞赛合规各司其职。
- **不怕中途返工**：上游证据变化后，阻止沿用失效的下游验收结果。
- **不把多 Agent 说成魔法**：只有实际执行、提交、验收和更新都留下证据，才称得上协作闭环。

## 核心能力

| 模块 | 当前可做的事 |
| --- | --- |
| **13 阶段竞赛路线** | 从报名与知识赛到团队实践、调查分析、报告、答辩和提交核验 |
| **项目状态持久化** | `state/project.json` 记录各阶段状态，支持跨会话继续 |
| **证据与变更跟踪** | 登记本地文件及 SHA-256；检测证据过期和上游变更 |
| **阶段质量门禁** | 检查必需证据、前序阶段状态，记录人工复核决定 |
| **方法路由与降级** | 按研究问题选择描述、比较、回归、测量、聚类、文本、IPA 等方法，并定义失败条件 |
| **文本分析与可视化** | 条件化文本分析、词云审计、图表选择与可视化质量门禁 |
| **报告生产与答辩** | 篇幅预算、图表交付契约、正文证据绑定、答辩问题库 |
| **任务交接协议** | 任务创建、认领、提交、复核和本地事件记录 |
| **角色复核与评分** | 三角色交付边界、五类检查点、七维评分汇总 CLI |
| **赛制配置** | 内置第十七届正大杯规则基线；当届官方及本校通知始终优先 |

### 十三阶段地图

```text
报名核验 → 知识赛准备 → 组队 → 选题 → 文献与二手研究
    ↓
调查设计 → 预调查 → 正式调查 → 数据清洗 → 统计分析
    ↓
研究报告 → PPT 与答辩 → 提交审计
```

阶段明细、必需证据和验收条件见 [阶段地图](references/stages.md)。只想完成某一阶段时，可以单独使用对应方法模块，无须立刻完成全部阶段。

## 快速开始

### 1. 安装 Skill

在 Windows 上，将仓库克隆或打包 ZIP 解压后，进入其中的 `market-survey-competition` 文件夹，先查看 `install.ps1`，再运行：

```powershell
git clone https://github.com/zhulehan683-commits/market-survey-competition.git
cd market-survey-competition
.\install.ps1
```

默认安装至：

```text
%USERPROFILE%\.agents\skills\market-survey-competition\
```

该脚本在目标目录已存在时默认拒绝覆盖；需要替换旧版本时，检查变更后使用 `-Force`，安装脚本会先备份旧目录。其他支持 `SKILL.md` 的 Agent 环境可按自身文档，将整个文件夹放进对应的 Skills 目录。**不要只复制 `SKILL.md`**。

从 Git 仓库安装时会按完整目录复制，包括 `.git`、文档和测试文件。对大多数 Agent 环境这不影响启动；如果你希望安装包保持最小化，请使用经检查的 ZIP 副本或自行清理安装副本。当前安装脚本会保留这些文件，以避免误删发布或审计材料。

### 2. 在 Codex 中启动

重新打开 Codex 会话，输入：

```text
使用 $market-survey-competition。

我要准备第十七届正大杯本科组比赛。
当前只有初步研究方向，还没有真实问卷数据。
请先核验当届与学校通知，检查目前所处阶段，
建立项目计划和待收集证据清单。
不要生成虚构的调查结果，也不要修改我的其他 Agent 配置。
```

首次使用时，建议至少提供以下信息，便于 Skill 判断当前阶段和缺失材料：

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| 赛事与组别 | 当届名称、组别、赛区 | 第十七届正大杯本科组 |
| 当前阶段 | 13 阶段中的位置 | 只确定了方向，尚未问卷 |
| 选题/研究对象 | 具体人群、地域、时间范围 | 武汉在校大学生消费习惯 |
| 已有材料 | 已有的通知、文献、问卷或数据 | 学院报名通知 PDF |
| 本轮目标 | 你希望本次会话交付什么 | 选题评分与研究计划 |

字段缺失不影响启动，但 Skill 会先列出还需要哪些证据，而不是跳过检查直接生成内容。

### 3. 初始化独立的竞赛工作区（可选手动操作）

本地脚本使用 Python 标准库，无需先安装额外 Python 包；建议使用 Python 3.10 或更新版本。进入 **Skill 根目录** 后，建议把研究工作区放在文档/竞赛目录中，而不是嵌套在 Skill 安装目录里：

```powershell
$project = Join-Path $HOME 'Documents\my-survey-project'
python scripts/workflow.py init --project $project --competition zhengda-17 --season 2026-2027
python scripts/workflow.py status --project $project
```

程序会创建独立的研究工作区，不会自动报名、访问问卷平台或生成实证结论。后续按真实材料逐项登记证据，例如：

```powershell
python scripts/workflow.py evidence add --project $project --stage registration --key official_notice --file "sources\official-notice.pdf" --author "参赛者"
python scripts/workflow.py evidence add --project $project --stage registration --key registration_confirmation --file "sources\registration-confirmation.pdf" --author "参赛者"
python scripts/workflow.py gate --project $project --stage registration
# 只有在独立人工复核后，才记录通过；这条命令不会验证审查者的真实身份。
python scripts/workflow.py review --project $project --stage registration --reviewer "独立复核者" --decision pass --note "已核对本人适用的官方与学校通知"
```

上例假定你**已经自行放入**真实的通知 PDF；它不是随项目提供的文件。`gate` 仅执行机械检查，正式放行还需要合格证据和独立复核记录。

## 常用命令速查

以下命令都在 Skill 根目录运行，假设 `$project` 已按上面初始化：

| 需求 | 命令 |
| --- | --- |
| 查看阶段状态 | `python scripts/workflow.py status --project $project` |
| 登记证据 | `python scripts/workflow.py evidence add --project $project --stage <阶段> --key <键名> --file <文件> --author <作者>` |
| 机械检查阶段 | `python scripts/workflow.py gate --project $project --stage <阶段>` |
| 记录人工复核结果 | `python scripts/workflow.py review --project $project --stage <阶段> --reviewer <人> --decision pass\|fail --note <说明>` |
| 查看可选集成 | 阅读 `references/integrations.md`（本地文件） |
| 看阶段定义 | 阅读 `references/stages.md`（本地文件） |

详细参数见 `python scripts/workflow.py --help`。

## 已整合的能力

| 来源 | 已整合进本项目 | 使用入口 |
| --- | --- | --- |
| 正大杯报告 Skill | 方法路由、条件化文本分析、图表审计、完整报告交付契约与模板 | 按任务加载下方参考资料 |
| mathmodel-skill | 三角色分工、交付物边界复核、权重与分数汇总函数 | [角色与复核](references/roles-and-review.md)、`scripts/score_review.py` |
| 本项目补充 | 13 阶段竞赛流程、证据失效、任务交接、项目自定义要求及市场研究模块 | [Skill 入口](SKILL.md)、[市场研究](references/market-research.md) |

这些模块随项目安装提供，共用 `state/project.json`；无需另外安装前两个上游 Skill。完整许可和固定版本见 [第三方说明](THIRD_PARTY_NOTICES.md)。

## 参考文件导航

按需阅读，不必全部读完再用 Skill：

| 想解决什么问题 | 先看哪份资料 |
| --- | --- |
| 各阶段定义、必需证据与退出条件 | [references/stages.md](references/stages.md) |
| 阶段门禁规则与 BLOCKED 原因 | [references/gates.md](references/gates.md) |
| 研究设计、文献综述与二手材料 | [references/research-design.md](references/research-design.md) 与 [references/market-research.md](references/market-research.md) |
| 问卷、抽样与测量质量 | [references/survey-quality.md](references/survey-quality.md) |
| 统计分析与结果解释 | [references/analysis.md](references/analysis.md) 与 [references/method-routing.md](references/method-routing.md)（方法路由与失败降级） |
| 文本分析与词云（条件能力） | [references/text-analysis.md](references/text-analysis.md) |
| 图表选择与可视化审计 | [references/visualization-guide.md](references/visualization-guide.md) |
| 报告篇幅预算与图表交付契约 | [references/report-production.md](references/report-production.md) |
| 报告写作与答辩准备 | [references/report-defense.md](references/report-defense.md) |
| 角色分工、交付物复核与 Agent 协作 | [references/roles-and-review.md](references/roles-and-review.md) 与 [references/agents.md](references/agents.md) |
| 第三方 Skill 集成与已合并上游说明 | [references/integrations.md](references/integrations.md) |

其中方法路由、文本分析、可视化审计、报告生产、Intake/方案模板与压力场景整合自 MIT 许可的 [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill)，署名与文件清单见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 失败恢复与常见陷阱

### 证据丢失或哈希失效

`workflow.py status` 显示 `STALE` / `STALE_UPSTREAM`，或 `gate` 的 `reasons` 提示证据缺失、文件被改动时：

1. 打开 `state/project.json`，看缺失或失效的证据键。
2. 重新提供原始文件并用 `evidence add` 重登记；新哈希会覆盖旧记录。
3. 重新运行 `gate`；通过后走独立复核。

### 阶段被 BLOCKED

- 运行 `python scripts/workflow.py gate --project $project --stage <阶段>`，查看 JSON 的 `reasons`；该命令阻塞时退出码为 3。`status` 成功读取状态时退出码为 0，不能据此判断阶段已通过。
- 补齐必需证据后重新 `gate`。
- `review` 只在真实人工核对后使用；如果不清楚缺什么，回到 `references/stages.md`。

### Agent 生成了虚构数据或未经验证的数字

- 在会话中明确要求："当前没有真实数据，不要生成参赛结论；给出数据收集计划和模板。"
- 检查它是否用了 `state/project.json` 里登记过的证据；未登记引用的数字不能作为结论。
- 如果它声称"文件检查通过"，亲自核对对应文件是否存在、内容是否与 `evidence` 登记一致。

### 下载的赛程与仓库不一致

仓库中的赛制是基线快照，不是实时来源。当届正式通知、校赛安排、提交模板永远优先。发现差异时，以官方/学校通知为准更新自己的工作区文件，并在 `source_register` 里登记来源和核对日期。

## 工作方式

```text
你 / 参赛团队
     │ 规则、材料、真实调查数据
     ▼
主控 Skill（阶段规划与证据管理）
     ├── 研究设计 / 文献 / 问卷方法
     ├── 数据清洗 / 统计分析 / 图表
     ├── 报告写作 / 答辩准备
     └── 本地任务交接协议（可选外部 Agent）
                  │
                  ▼
       证据文件 + 哈希 + 审核记录
                  │
                  ▼
       通过则更新状态；问题则返工
```

**边界说明：** `scripts/task_queue.py` 是本地交接记录工具，不会主动唤起 Codex、Hermes、DSH 或 Workbud。接入真实多 Agent 系统还需要外部编排器、执行日志与身份验证；仅凭任务记录不能证明自动协作已跑通。详见 [Agent 协作协议](references/agents.md)。

## 目录结构

```text
market-survey-competition/
├── SKILL.md                     # Agent 入口与行为边界
├── competitions/zhengda-17/     # 第十七届正大杯赛制基线
├── references/                 # 阶段、门禁、方法和协作参考
├── scripts/
│   ├── workflow.py             # 项目状态、证据及阶段审核
│   ├── task_queue.py           # 本地任务交接
│   ├── score_review.py         # 七维复核输入汇总
│   └── common.py               # 共用工具
├── templates/                  # 知识赛、组队、选题、问卷、抽样、数据、分析、报告、答辩模板
├── tests/                      # 自动化测试
├── docs/                       # 项目规格、发布清单、验证记录、GitHub About 与发布提示词
├── licenses/                   # 上游许可档案
├── .github/workflows/          # GitHub Actions 测试工作流
├── install.ps1                 # Windows 安装脚本
├── CODEX_START.md              # Codex 启动提示词
├── CHANGELOG.md                # 变更记录
├── CONTRIBUTING.md             # 贡献规范
├── SECURITY.md                 # 安全与隐私说明
├── THIRD_PARTY_NOTICES.md      # 第三方来源与许可注意事项
└── LICENSE-DECISION.md         # 许可证待确认记录（不是许可证）
```

初始化后的 **参赛工作区与 Skill 安装目录分离**，包含 `sources/`、`raw_private/`、`data/`、`analysis/`、`report/`、`defense/`、`state/` 和 `tasks/` 等目录。原始受访者信息应留在私有工作区，不要上传到公共仓库。

## 自检与测试

当前自动化测试包含状态初始化、证据哈希失效、前序门禁、路径穿越/符号链接拒绝、原始数据私有目录约束、任务队列的认领/提交/复核/变更检测，以及发布文档与竞赛配置契约检查。在 Skill 根目录运行：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/workflow.py --help
python scripts/task_queue.py --help
python scripts/score_review.py --help
```

七维复核可填写 `templates/review-rubric.json` 后运行 `python scripts/score_review.py <review.json>`；空模板不能作为有效复核输入。该工具只输出摘要与建议，不批准阶段。

自动测试覆盖状态管理、证据变更、阶段门禁及任务交接的若干情景，**不是对调查方法科学性、真实赛事合规或外部 Agent 实际运行的认证**。

2026-10-17 本地实测：Windows 11 + Python 3.12.3 下，27 项测试中 26 项通过、1 项 symlink 用例因本机权限跳过。`workflow.py init/status/evidence/gate/review`、`task_queue.py` 和 `score_review.py` 在真实独立工作区完成冒烟验证，证据 SHA-256 与实际文件哈希一致。首次 GitHub Actions `Tests` 验证已通过（历史记录，当前状态以顶部动态徽章为准），Python 3.10—3.13 矩阵见 [.github/workflows/tests.yml](.github/workflows/tests.yml)。

## 设计原则与限制

1. **真实性优先**：不伪造问卷、访谈、回收率、显著性、引用或获奖结果。模拟数据必须明确标注，不进入参赛报告作为真实证据。
2. **当届规则优先**：仓库中的赛程仅为基线，个人报名、组队、校赛及提交要求必须以当届官方与本校通知为准。
3. **最小必要权限**：不代考、不代报名、不代替团队收集问卷；外部 AI 工具仅处理获准使用且已脱敏的数据。
4. **审查不能由脚本冒充**：本地审核记录只是留痕，无法技术性证明 reviewer 的真实身份、独立性和研究质量。
5. **有来源的整合**：合并模块保留来源、固定提交与完整许可，按本项目阶段适配；其余外部 Skill 按需使用，见 [集成参考](references/integrations.md)。

## 后续路线

- [ ] 由项目所有者确认许可证并添加标准 `LICENSE` 文件。
- [x] 在真实 Windows PowerShell 环境中验证安装脚本（2026-10-17）。
- [x] 在本地 Windows + Python 3.12 环境运行测试与 CLI（2026-10-17，19 项测试中 18 项通过、1 项 symlink 用例因权限跳过）。
- [x] 通过 GitHub Actions `Tests` 工作流验证 Python 3.10—3.13（最新 main 分支）。
- [x] 完成进入 Skill 根目录的 ZIP 解压验证（2026-10-17）。
- [ ] 扩展新的竞赛年份与其他市场调查赛事配置。
- [ ] 在 Codex / Claude Code 中做端到端回归测试。
- [ ] 接入真实多 Agent 编排器，验证派发—认领—执行—复核—状态更新的完整日志链。
- [ ] 补充经过匿名化处理的示例研究项目与可复现数据分析演示。
- [ ] 增强报告与答辩交付的自动化检查。

## 参考、开源发布与贡献

本项目的工作流思路参考了 [mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill)、[正大杯调查报告 Skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill)、[Conduct Market Research](https://github.com/MAS-32/conduct-market-research)、问卷设计与统计分析相关 Skill。本次已合并前两个 MIT 来源的部分文档、提示词、模板和评分代码；`conduct-market-research` 的核验快照未见 LICENSE，保留链接，本项目市场研究模块独立编写。完整来源列表与复用规则见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 和 [集成参考](references/integrations.md)。

- [项目规格与验收标准](docs/PROJECT_SPEC.md)
- [GitHub About 简介与 Topics](docs/GITHUB_ABOUT.md)
- [给 Codex 的 GitHub 发布提示词](docs/CODEX_GITHUB_PUBLISH_PROMPT.md)
- [发布前检查清单](docs/RELEASE_CHECKLIST.md)
- [贡献指南](CONTRIBUTING.md)
- [安全与隐私](SECURITY.md)
- [许可证决策（待所有者确认）](LICENSE-DECISION.md)

**许可证尚未决定，当前没有 `LICENSE` 文件。** 公开发布前必须由项目所有者确认许可证并完成第三方许可、代码与隐私检查。不要把当前 Preview 包宣传为已正式授权的开源发行版。

---

**让 AI 帮助研究，而不是替研究制造证据。**
