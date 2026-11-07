# Changelog

本项目仍处于 Preview 阶段。此文件记录有意发布的变更；未记录的工作不能视为已经发布。

## 0.3.0 - 2026-11-07

### Added

- 新增纯标准库 `scripts/stats_basic.py`：描述统计、均值置信区间、单/双样本与配对 t 检验、卡方/Fisher、频数表、Cronbach's α、OLS 与二元 Logit；只做成对完整案例分析，不插补、不加权。
- 新增 `scripts/power_calc.py`：比例精度、两比例、两均值与卡方设计的样本量/功效近似，支持脱落率上浮与有限总体校正。
- 新增 `scripts/advisor.py`：`grill` 按阶段生成决策前沿与建议答案，`find` 扫描本地技能并打印生态检索命令；两者都不修改项目状态、不自动联网或安装。
- 新增 `examples/sample-project/`：一份 50 行模拟数据与已填写的选题、来源、抽样、伦理、变量字典、分析合同和设计清单，可直接跑通 `topic → desk_research → design` 机械门禁。
- 新增 `templates/rules-verification.json`、`templates/grill-log.md` 与 `docs/SURVEY_EXPORTS.md`。
- 新增 `workflow.py template` 模板复制与 `workflow.py evidence list` 证据查看子命令。

### Changed

- `workflow.py evidence add` 默认拒绝覆盖已存在的证据键；`--force` 替换时返回 `replaced` 块（旧路径、SHA-256、作者、时间），并继续使下游阶段失效。
- `rules_verification` 现在必须包含实际核验日期与全国/本校公告 URL；`gate` 拒绝未来日期和超过 60 天的记录。
- CSV 预检 schema 支持 `item_group`、`reverse_coding`、`likert_points` 与 `multi_select_separator`；多选组内全空只记一次缺失，反向计分只提示不自动改数。
- `SKILL.md` 增加两个高频入口：选题/设计/分析/报告/答辩冻结点默认先跑 3 问 grill；缺少能力时默认先扫本地技能。
- `grill-me`、`grilling`、`find-skills` 适配入口扩大触发描述，加入冻结前默认动作与 `advisor.py` 快速通道。
- `research-design.md` 增加历届获奖题目密度检索；`topic-scorecard.csv` 增加 `topic_density` 与 `topic_density_notes`。
- 所有 CLI 入口统一 UTF-8 输出；模板与示例文本统一 LF，`.gitattributes` 覆盖模板、示例、脚本和文档。
- 安装清单新增统计脚本、顾问脚本、规则模板与示例项目；README 命令细节移入 `docs/COMMANDS.md`。

### Fixed

- 修复证据键静默覆盖导致旧绑定丢失的问题。
- 修复模板 CRLF/LF 不一致导致安装副本与仓库副本哈希不一致的问题。
- 修复旧 Windows 代码页下中文诊断可能崩溃或乱码的问题。

### Known limitations

- 联合分析、KANO、IPA、SEM、复杂抽样、机器学习和因果识别仍只有方法路由与合同，没有实现；不得声称本仓库已运行。
- `stats_basic.py` 的 t、卡方、Logit 与样本量计算使用经典近似，不处理复杂抽样设计或加权数据。
- 示例数据是模拟数据，不得用于参赛、报告或推断。
- 项目许可证仍待所有者确认；在添加 `LICENSE` 前不应宣称已正式开源授权。

## 0.2.0 - 2026-10-18

### Grill Me / Find Skills 整合

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

### 早期整合

- 整合 mathmodel-skill 的三角色交付/独立复核提示词，并从 `score_artifact.py` 复用 `apply_dim_weights` 与 `summarize_scores`；新增只读七维汇总 CLI、字段校验和行为测试。
- 保存上游固定提交、来源文件哈希和完整 MIT 声明；合并内容与外部引用分别登记。
- 整合 MIT 许可上游 [zhengdabei-survey-report-skill](https://github.com/DDXYY189/zhengdabei-survey-report-skill) 的核心参考文档：方法路由（`references/method-routing.md`）、条件化文本分析（`references/text-analysis.md`）、可视化审计（`references/visualization-guide.md`）、长篇报告生产契约（`references/report-production.md`）。
- 新增启动 Intake、建模方案比较、结果矩阵与图表登记表模板；新增 `tests/pressure-scenarios.md` 压力场景清单。
- `SKILL.md` 增加 Intake 字段分级（阻塞/设计/优化）、建模方案固定格式与结论/建议句式规范；`references/gates.md` 增加七维评分自查。
- 新增项目规格文档，统一项目目标、13 阶段范围、协作协议、真实性边界和验收标准。
- 新增贡献指南、安全报告说明、第三方来源说明、许可证决策记录与发布检查清单。
- 新增 GitHub Actions 测试工作流和 GitHub About 文案。
- 新增选题、问卷、抽样、预测试、清洗、分析、AI 使用、答辩和提交模板。

### 早期变更

- 完善 Windows 安装脚本：先复制到 staging 目录并验证必要文件，再替换旧安装；保留备份与失败恢复。
- 将路径校验改为在解析路径前检查符号链接，避免 `resolve()` 掩盖链接路径。
- 扩展任务队列验收条款和负责人校验的回归测试。
- 更新第三方 Skill 路由：许可明确的部分直接整合，其他项目保持可选参考，不假定已安装或自动调用。
- 修正报告上游与竞赛总控的范围冲突：报名/知识赛/选题按阶段收集字段；PPT 与答辩纳入本项目范围；专业状态与脚本阶段状态明确区分。
