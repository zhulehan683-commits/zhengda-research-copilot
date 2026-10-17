# 阶段地图（依序通过，但可在当前阶段并行进行不依赖事项）

文件名键名与 `scripts/workflow.py` 的 `STAGES` 对应。`gate` 校验只是本地**文件存在、路径、哈希、前序状态**，科研审查需真实证据与独立审核者。

| 阶段 | 核心工作 | 最少证据键 | 进入下一阶段的独立确认 |
|---|---|---|---|
| registration | 年度/本校通知核验、个人报名 | official_notice, registration_confirmation | 本人完成报名且核实状态 |
| knowledge | 统计基础、调查方法、知识赛练习与本人考试 | exam_result | 真实成绩/资格；不代考 |
| team | 组建合规团队，确认分工和研究能力 | team_roster | 队员本人确认/同校与人数符合当届规则 |
| topic | 多选题评估、需求痛点、可得样本与可行性 | topic_brief, feasibility_check | 问题真实、范围合理、可做调查 |
| desk_research | 官方数据、行业报告、文献及理论框架 | source_register, research_gap | 来源可靠，变量与研究假设有依据 |
| design | 总体、抽样、样本量、问卷、访谈/合规 | survey_instrument, sampling_plan, research_ethics | 问卷可执行，逻辑与保护措施到位 |
| pilot | 预测试，修订问卷及实施计划 | pilot_log, pilot_revision | 真实预调查记录、质量问题可解释 |
| fieldwork | 正式实地/线上调查及质量监控 | collection_log, raw_dataset, provenance | 真实样本、受访同意、范围一致；`raw_dataset` 原始文件必须放在工作区 `raw_private/` 下 |
| cleaning | 定义并执行剔除、缺失、反向编码 | cleaning_script, clean_dataset, cleaning_report | 变动前后数量与原因可复现 |
| analysis | 统计、模型诊断与研究问题对应 | analysis_code, result_tables, diagnostic_report, claim_map_draft | 数值来自代码、方法前提满足、不能偷换因果 |
| report | 正文图表、完整来源、合规与 AI 台账 | report_doc, claim_evidence_matrix, ai_usage_log, rules_checklist | 每个结论有数据/图表/来源，符合当届规则 |
| defense | 数据驱动演示、模拟提问、纠错 | slides, defense_notes, mock_defense_log | 演示论点、证据、数据一致 |
| submission | 当届格式审计、由队伍提交 | submission_package_manifest, receipt | 上传/参赛结果来自本人或官方系统 |

单项阶段任务：可只做该阶段的工作计划或部分产物，但**不得**在前序未通过且证据不足时把整项标成完成。

## 计划

项目可同时维护 `plans/next_actions.md`（负责人、截止日、约束、实际阻塞），不能用状态 JSON 替代真实行动。比赛日期随当届/赛区变更，须记录已核验来源与核验时间。

## 知识赛

优先覆盖统计学与市场调查基础：总体、抽样框、抽样误差、置信区间、抽样方法、问卷设计、数据编码、描述统计、假设检验、相关/回归、市场调查伦理。基于真题或获准公开题库设计自测、错题归因、学习计划。不得自动参加考试、代答、冒充已合格。
