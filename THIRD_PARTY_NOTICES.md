# Third-party sources and notices

## 分发范围与固定版本

本项目合并以下明确标注许可的部分文档、提示词、模板与代码。每一项都固定来源提交；原文件 SHA-256、来源路径和目标清单见 [upstreams.lock.json](docs/upstreams.lock.json)。下表的 MIT 仅适用于对应上游内容，不代表本项目所有者已为整个仓库选择许可证。

| 上游 | 固定提交 | 实际并入的内容 | 完整许可 |
| --- | --- | --- | --- |
| [DDXYY189/zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill/tree/449a58e64d15d263fcd9763df27d16f9ffc88ac9) | `449a58e64d15d263fcd9763df27d16f9ffc88ac9` | 方法、文本、可视化、报告生产文档；模板；部分入口指令、七维自查与压力场景 | [MIT 全文](licenses/zhengdabei-survey-report-skill/LICENSE)，Copyright (c) 2026 DDXYY189 |
| [rootkiller6788/mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill/tree/a5f4d60c7db2a98e1284b1995a1aaaaa008facd5) | `a5f4d60c7db2a98e1284b1995a1aaaaa008facd5` | 三角色/边界复核提示词；`score_artifact.py` 中 `apply_dim_weights`、`summarize_scores` 两个函数 | [MIT 全文](licenses/mathmodel-skill/LICENSE)，Copyright (c) 2026 rootkiller6788；评分代码的上游声明 [handsomeZR-netizen MIT](licenses/handsomeZR-netizen-mathmodel-skill/LICENSE) |

mathmodel-skill 的 [来源说明](licenses/mathmodel-skill/SOURCES.md) 和 [子工具许可说明](licenses/mathmodel-skill/THIRD_PARTY_NOTICES.md) 保留为来源链档案，里面的路径属于上游仓库，不代表本项目分发了全部上游文件。未合并该仓库的 Office/PDF 子工具、字体、模板或数据。其 LaTeX 引用检查工具进一步上游未见独立许可，本次不分发该代码；只在隔离研究目录评估过候选。

## 文件映射与适配

### 正大杯报告 Skill

- `references/method-routing.md`、`text-analysis.md`、`visualization-guide.md`、`report-production.md` 对应上游 `skills/zhengdabei-survey-report/references/` 同名文件；去除将上游本地论文当成本项目已核验证据的表述，报告阶段改为本项目 `report`。
- `templates/intake.md`、`model-option-comparison.md`、`result-matrix.csv`、`figure-register.csv` 从上游 `references/report-templates.md` 拆分适配；保留本项目原有报名、知识赛、预算与规则字段，并增加项目自定义要求。
- `SKILL.md` 借鉴字段分级、方案比较、结论与建议表达；按竞赛阶段调整，未选题可继续报名/知识赛和选题工作。
- `references/gates.md` 的七维自查改编自上游 `references/quality-gates.md`；专业判断不改变本项目脚本状态枚举。
- `tests/pressure-scenarios.md` 改编自上游同名文件，调整答辩范围并补充未选题的情景；它是测试方案，不是声称所有场景已通过。

### 数学建模 Skill

- `references/roles-and-review.md` 根据上游 `references/角色-阶段映射.md` 适配研究设计、分析实现、报告/答辩及交付物检查点。沿用本项目 13 阶段，不引入其他数学建模赛事规则、强制图数或第二套权威状态。
- `scripts/score_review.py` 从上游 `scripts/score_artifact.py` 复用上述两个函数，其余七维输入校验、只读 CLI、建议状态与测试由本项目补充。分数只用于整理复核意见，不能认证研究质量、来源真实性或批准阶段。

## 仅参考的项目

下列项目仍仅保留链接，不分发它们的文件，也不声称已安装或已调用。

| 项目 | 参考方向 |
| --- | --- |
| [MAS-32/conduct-market-research](https://github.com/MAS-32/conduct-market-research/tree/b932488e6e48e268d9eaf99b33359b787943d4e1) | 商业研究与证据核验；该快照未见 LICENSE，不复制代码或提示词；本项目 `references/market-research.md` 独立编写 |
| [maydengximin-sketch/questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill) | 量表与问卷统计 |
| [2811jh/survey-research](https://github.com/2811jh/survey-research) | 问卷处理 |
| [scdenney/open-science-skills](https://github.com/scdenney/open-science-skills/tree/main/codex/survey-design) | 问卷设计 |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills/tree/main/research-ops/skills/market-research) | 市场规模与抽样 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 统计推断 |
| [anthropics/skills](https://github.com/anthropics/skills) | Skill 信息结构 |

## 核验记录

核验日期：2026-10-17。实际源文件来自上述固定提交；完整版权与许可文本随包保留。合并上游内容不转移其作者身份、不表示主办方或上游背书，也不代表已取得赛事通知、论文、受访者数据或其他第三方素材的再分发权。本项目自己的许可证仍按 [LICENSE-DECISION.md](LICENSE-DECISION.md) 待所有者决定。
