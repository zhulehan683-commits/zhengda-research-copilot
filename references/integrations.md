# 外部开源 Skill 集成与合并说明

## 已合并进本项目的上游内容

以下 MIT 许可项目的部分参考文档已直接合并进本仓库（保留署名，见 `THIRD_PARTY_NOTICES.md`），安装本项目即可获得，无需另行安装：

| 上游项目 | 已合并内容 | 本项目位置 |
|---|---|---|
| [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill)（MIT） | 方法路由、文本分析、可视化审计、报告生产契约、Intake/方案比较模板、压力场景 | `references/method-routing.md`、`references/text-analysis.md`、`references/visualization-guide.md`、`references/report-production.md`、`templates/intake.md`、`templates/model-option-comparison.md`、`templates/result-matrix.csv`、`templates/figure-register.csv`、`tests/pressure-scenarios.md` |
| [mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill)（MIT） | 三角色与交付物边界复核提示词；复用权重限制与分数汇总代码，补充七维校验 | `references/roles-and-review.md`、`scripts/score_review.py` |
| [questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill)（MIT） | 清洗、信效度与结果报告框架；修正机械阈值和推断边界 | `references/measurement-and-inference.md`；无需另装上游 |

## 可选外部 Skill（不随本项目打包）

本表用于按任务路由到可选参考项目。它们**不是本 Skill 的内置依赖**：安装本项目不会自动安装、调用或验证任何上游 Skill。开始使用前，应查看目标仓库当前版本、入口文件、依赖、许可证和数据权限要求。

| 任务阶段 | 参考项目 | 适合补充的能力 | 当前关系 |
|---|---|---|---|
| 正大杯报告 | [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) | 调查报告结构、证据绑定、报告质量门禁 | **核心参考文档已合并**；其最新完整版可单独安装 |
| 市场研究 | [conduct-market-research](https://github.com/MAS-32/conduct-market-research) | 行业与竞品研究、证据分级、市场规模双路径核验 | 仅参考；需单独安装/验证 |
| 问卷设计 | [open-science-skills / survey-design](https://github.com/scdenney/open-science-skills/tree/main/codex/survey-design) | 题项措辞、问卷顺序、预测试与调查偏差 | 仅参考；需单独安装/验证 |
| 市场规模/抽样 | [claude-skills / market-research](https://github.com/alirezarezvani/claude-skills/tree/main/research-ops/skills/market-research) | 市场规模估算、样本量规划、市场细分 | 仅参考；需单独安装/验证 |
| 量表统计 | [questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill) | 信度、效度、EFA/CFA、回归、SEM 等方法参考 | 清洗/测量/报告框架已适配合并；完整版需单独审查 |
| 问卷数据处理 | [survey-research](https://github.com/2811jh/survey-research) | 问卷数据导入、基础统计、交叉分析与报告处理 | 仅参考；执行前审查脚本和数据权限 |
| 科学统计 | [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 统计检验、假设检查、效应量与推断参考 | 仅参考；需单独安装/验证 |
| 工作流与质量门禁 | [mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill) | 其他建模赛事、专用排版和算法参考 | 本项目已整合部分角色与评分逻辑；完整上游可按任务另行使用 |

## 路由规则

1. 先识别当前阶段和需要的产物，再选择最少必要的子 Skill；不要因为可安装就全部安装。
2. 只使用当前环境中确实可发现、可执行且获准访问所需数据的工具。不可用时回退到本项目的参考文档与人工步骤，并如实报告。
3. 选题与二手资料优先使用 `conduct-market-research`；问卷和抽样优先参考 `survey-design` 与 `market-research`；问卷统计可参考 `questionnaire-analysis` 和 `survey-research`；统计结论需独立复现。方法选择细节优先使用本项目内置的 `references/method-routing.md`。
4. 子 Skill 不得自行改变研究总体、关键变量定义、原始数据或权威项目状态；交付隔离产物、来源、执行命令和 SHA-256，由主控协调者审查。
5. 已合并内容及完整版权/许可见 `THIRD_PARTY_NOTICES.md` 与 `licenses/`，来源固定版本见 `docs/upstreams.lock.json`。未列入合并清单的项目仅作外部参考；不能将一个仓库的根许可证自动套到所有子工具。
6. 当届官方规则优先于学校/赛区通知，学校/赛区通知只适用于对应参赛单位，经验类 Skill 不能替代规则。

## 冲突解决

优先级：当届主办方规则与正式补充通知 → 用户所在学校/赛区有效通知 → 本项目真实性、隐私和安全底线 → 子 Skill 方法建议。若两条有效规则存在冲突，停止相关操作并请求人工确认，不自行选择对参赛者最方便的版本。
