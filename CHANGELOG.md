# Changelog

本项目仍处于 Preview 阶段。此文件记录有意发布的变更；未记录的工作不能视为已经发布。

## Unreleased

### Added
- 整合 MIT 许可上游 [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) 的核心参考文档：方法路由（`references/method-routing.md`）、条件化文本分析（`references/text-analysis.md`）、可视化审计（`references/visualization-guide.md`）、长篇报告生产契约（`references/report-production.md`）。
- 新增启动 Intake、建模方案比较、结果矩阵与图表登记表模板；新增 `tests/pressure-scenarios.md` 压力场景清单。
- `SKILL.md` 增加 Intake 字段分级（阻塞/设计/优化）、建模方案固定格式与结论/建议句式规范；`references/gates.md` 增加七维评分自查。
- 新增项目规格文档，统一项目目标、13 阶段范围、协作协议、真实性边界和验收标准。
- 新增贡献指南、安全报告说明、第三方来源说明、许可证决策记录与发布检查清单。
- 新增 GitHub Actions 测试工作流和 GitHub About 文案。
- 新增选题、问卷、抽样、预测试、清洗、分析、AI 使用、答辩和提交模板。

### Changed
- 完善 Windows 安装脚本：先复制到 staging 目录并验证必要文件，再替换旧安装；保留备份与失败恢复。
- 将路径校验改为在解析路径前检查符号链接，避免 `resolve()` 掩盖链接路径。
- 扩展任务队列验收条款和负责人校验的回归测试。
- 更新第三方 Skill 路由：只作为可选参考，不假定已安装或自动调用。

### Known limitations
- 未实现后台自动调度或真实 Hermes/Codex/DSH/Workbud 连接。
- 当前只有第十七届正大杯规则基线；学校/赛区规则需要参赛者重新核验。
- 尚未完成真实参赛项目端到端验证。
- 项目许可证待所有者确认；未添加 `LICENSE` 文件，不应宣称已经正式开源授权。
