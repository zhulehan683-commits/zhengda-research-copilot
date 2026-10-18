# Changelog

本项目仍处于 Preview 阶段。此文件记录有意发布的变更；未记录的工作不能视为已经发布。

## Unreleased

### Grill Me / Find Skills 整合（2026-10-18）
- 固定 MIT 上游 `mattpocock/skills` 与 `vercel-labs/skills` 的三份原文，保留 `grill-me` 对 `grilling` 的依赖；完整许可和 SHA-256 纳入来源锁文件。
- 加入研究决策压力测试与外部能力发现的适配指南，支持没有原生 Skill 调用工具时直接读取；纯讨论不初始化项目。
- 可发现入口改为自含的研究适配版，完整上游原文移至 `references/upstream-skills/`；避免独立调用时绕过安装范围、离线降级和访谈范围规则。
- 离线安装器携带子技能与许可，增加安装完整性回归测试；README 按项目事实与首次使用路径全面重写。
- 修正既有问卷来源许可的换行/哈希一致性和“仅参考”重复分类，补充所有已记录许可哈希的回归校验。

### 2026-10-18 升级
- 增加 `design_manifest` / `analysis_manifest` 依赖清单，问卷、变量字典、分析合同、输入、代码和配置变化会使旧阶段失效；`rules_verification` 纳入报名门禁。
- 任务队列创建时保存输入哈希，提交时可记录实际命令、退出码与日志哈希；列表新增 `STALE_INPUT` / `STALE_EXECUTION`。`gate`/`review` 的阻断与不通过统一返回退出码 3。
- CSV schema 改为 fail-closed：拒绝未实现字段、拼写错误和不适用的范围规则，支持离散 `allowed_values`，空白始终识别为缺失。
- 增加 CSV 数据合同预检 CLI：必填缺失、类型、范围、重复标识、行结构、输入哈希和汇总诊断；只读原数据，仅在 analysis/ 新建输出。
- 适配 MIT 许可 questionnaire-analysis-skill 的清洗/测量/报告框架，补充分析合同、逐题审核、便利样本推断边界、缺失机制和模型诊断。
- 统一 Python 离线安装器与 PowerShell 入口，支持 D 盘主副本、显式 Agent 适配目录、Junction/符号链接或复制、哈希校验、备份与失败回滚；Skills CLI 安装另有独立说明。
- 修复 Windows 证据/项目状态/任务目录的 Junction 绕过、长路径 staging、运行依赖缺失和非对象 JSON 输入错误。
- 重写 README 与跨 Agent 启动提示词，名称更新为“正大杯研策 / zhengda-research-copilot”；原研究状态无需重置。
- 扩展 Windows/Linux CI、安装和数据预检回归测试；外部执行端经 Magpie 调用，实测范围见 docs/VALIDATION.md。

### Added
- 整合 mathmodel-skill 的三角色交付/独立复核提示词，并从 `score_artifact.py` 复用 `apply_dim_weights` 与 `summarize_scores`；新增只读七维汇总 CLI、字段校验和行为测试。
- 保存上游固定提交、来源文件哈希和完整 MIT 声明；合并内容与外部引用分别登记。
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
- 更新第三方 Skill 路由：许可明确的部分直接整合，其他项目保持可选参考，不假定已安装或自动调用。
- 修正报告上游与竞赛总控的范围冲突：报名/知识赛/选题按阶段收集字段；PPT 与答辩纳入本项目范围；专业状态与脚本阶段状态明确区分。

### Known limitations
- 未实现后台自动调度或真实 Hermes/Codex/DSH/Workbud 连接。
- 当前只有第十七届正大杯规则基线；学校/赛区规则需要参赛者重新核验。
- 尚未完成真实参赛项目端到端验证。
- 项目许可证待所有者确认；未添加 `LICENSE` 文件，不应宣称已经正式开源授权。
