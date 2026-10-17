# Third-party references and notices

## 当前分发策略

当前发行包包含本仓库编写的工作流说明、参考文档、模板和 Python 脚本，**以及经上游 MIT 许可授权合并的参考文档**（见下表）。其余第三方项目仍以链接和方法路由的形式引用，不随本项目打包其 `SKILL.md`、代码、数据或素材。链接不表示官方背书，也不表示本项目已安装或调用该项目。

如果未来继续复用第三方代码、提示词、模板、数据或图片，必须先检查对应仓库当前许可证、版权声明、来源与再分发条件，并在此文件记录具体文件、来源版本/提交、许可和本项目修改。

## 已合并的上游内容（MIT 许可）

### zhengdabei-survey-report-skill

- 上游：<https://github.com/DDXYY189/zhengdabei-survey-report-skill>
- 许可：MIT License，Copyright (c) 2026 DDXYY189
- 核验日期：2026-10-17
- 合并内容（基于上游当前 main 分支，含少量适配性编辑以对接本项目 13 阶段与 `pass/conditional/blocked` 状态约定）：
  - `references/method-routing.md` ← `skills/zhengdabei-survey-report/references/method-routing.md`
  - `references/text-analysis.md` ← `skills/zhengdabei-survey-report/references/text-analysis.md`
  - `references/visualization-guide.md` ← `skills/zhengdabei-survey-report/references/visualization-guide.md`
  - `references/report-production.md` ← `skills/zhengdabei-survey-report/references/report-production.md`
  - `templates/intake.md`、`templates/model-option-comparison.md`、`templates/result-matrix.csv`、`templates/figure-register.csv` ← 基于 `references/report-templates.md` 拆分适配
  - `tests/pressure-scenarios.md` ← `tests/pressure-scenarios.md`
  - `references/gates.md` 中的"七维评分自查"小节 ← `references/quality-gates.md`
  - `SKILL.md` 中的 Intake 字段分级、建模方案固定格式、结论/建议句式 ← `skills/zhengdabei-survey-report/SKILL.md`

上游 MIT 许可原文要点：允许使用、复制、修改、合并、发布、分发，需在副本中包含版权与许可声明。Copyright (c) 2026 DDXYY189.

## 参考项目

| 项目 | 本项目参考用途 | 当前分发关系 |
|---|---|---|
| [DDXYY189/zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) | 正大杯报告阶段、真实数据边界与提交审计 | **MIT 许可内容已合并（见上）** |
| [MAS-32/conduct-market-research](https://github.com/MAS-32/conduct-market-research) | 证据驱动的市场研究、来源评估与市场规模核验 | 仅链接；不打包其文件 |
| [maydengximin-sketch/questionnaire-analysis-skill](https://github.com/maydengximin-sketch/questionnaire-analysis-skill) | 量表、信效度、因子分析和问卷统计参考 | 仅链接；不打包其文件 |
| [2811jh/survey-research](https://github.com/2811jh/survey-research) | 问卷数据处理与报告导出思路 | 仅链接；不打包其文件 |
| [scdenney/open-science-skills — survey-design](https://github.com/scdenney/open-science-skills/tree/main/codex/survey-design) | 问卷措辞、预测试与调查偏差 | 仅链接；不打包其文件 |
| [alirezarezvani/claude-skills — market research](https://github.com/alirezarezvani/claude-skills/tree/main/research-ops/skills/market-research) | 市场规模、样本量与市场细分分析思路 | 仅链接；不打包其文件 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 统计方法选择与学术分析参考 | 仅链接；不打包其文件 |
| [rootkiller6788/mathmodel-skill](https://github.com/rootkiller6788/mathmodel-skill) | 阶段状态、证据门禁和工作流可恢复性设计 | 仅链接；不打包其文件 |
| [anthropics/skills](https://github.com/anthropics/skills) | Skill 入口和 README 信息架构参考 | 仅链接；不打包其文件 |

## 许可证状态

此列表是来源说明，不等同于第三方许可证审计。公开发布前，维护者应重新打开每个上游仓库的许可证文件和当前版本，记录核验日期。当前项目没有声称已取得对上游内容的再分发授权。
