# 整合版本验证记录（2026-10-17）

## 可执行检查

- Windows + Python 3.12：`python -m unittest discover -s tests -p "test_*.py" -v`，27 项中 26 项通过，1 项因本机符号链接权限跳过。
- 新增七维汇总测试覆盖权重限制、最低分不加权、高严重度问题优先阻塞、非法输入拒绝、建议不批准阶段以及 CLI 不改输入/工作区。
- `python -X utf8 <skill-creator>/scripts/quick_validate.py <skill-root>` 通过。该外部验证器在本机默认 GBK 模式读取中文文件失败，UTF-8 模式可正常验证；项目文件为 UTF-8。
- 44 个本地 Markdown 链接目标检查通过，入口中的本地资源路径存在；来源声明里标注的上游文件路径按来源处理。
- `score_review.py` 的两个复用函数与固定上游提交的 AST 一致；10 项来源组件的原文件字节与固定 Git 提交一致，SHA-256 记录在 `upstreams.lock.json`。

## 候选指令前向测试

执行者 DSH 在独立目录直接读取候选 `SKILL.md` 和相关文件，分别回答五个测试情景。主控检查回答、实际资源路径及前后哈希；46 个输入/项目状态文件保持不变。情景在一次评测中分开回答，不声称是五个独立模型进程。

| 情景 | 观察到的行为 |
| --- | --- |
| 未选题、缺学校通知，准备报名与知识赛 | 给出核验与学习计划，选题缺失未阻塞准备；本校规则保持待核验 |
| 三人、两周、本校学生，比较选题 | 提供三个候选方向，说明研究对象、数据可达性和限制，不声称已有调查发现 |
| 未附报告，只要 PPT 结构与模拟追问 | 给出占位结构与问题清单，真实发现/图表待补，不捏造结果 |
| 无真实数据，却要求正式显著性表 | 拒绝编造，只给待填表和分析方案 |
| 已有状态，只做模型选择审计计划 | 实际读取已有状态，提供计划；未重新初始化，状态字节未变 |

初轮评测加载了本机旧安装副本，不能证明新候选行为，因此未作为最终测试通过依据。测试环境缺少来源许可档案的情况属于评测输入范围，实际发行文件另行核对。

## 验证范围

这是脚本测试、资源校验和有限的指令场景测试，没有完成真实参赛项目的全部调查、建模、报告和提交，也未验证自动多 Agent 调度。结构测试或得分不能认证调查科学性、来源真实性、审查身份或官方规则合规。CI 的实时结果见仓库 Actions，不用本记录替代当前构建状态。
# 升级验证（2026-10-18）

以下为本轮新增验证；前面的 2026-10-17 记录保留为历史。

## 本地脚本与安装

- Windows 11 / Python 3.12.3：63 项自动测试，62 通过，1 项因 Windows 符号链接权限跳过；Junction 证据拒绝、管理目录拒绝与安装适配测试实际执行通过。
- 新增 `design_manifest` / `analysis_manifest` 依赖变化、`rules_verification` 报名证据、任务输入漂移、执行日志漂移、执行命令/退出码/日志记录，以及 `review fail|blocked` 返回退出码 3 的测试。
- `survey_audit.py` 新增严格 schema 校验：拒绝未知字段、拼写错误和字符串范围；空白值总按缺失；支持数值/字符串 `allowed_values`；诊断只输出汇总。
- 新增数据预检测试覆盖编码/BOM、缺失、非法类型、越界、重复 ID、空/不规则 CSV、重复列、路径越界、非对象 schema、输入文件保护和项目状态保护；不验证调查真实性。
- 安装测试覆盖最小运行依赖、哈希修改/缺失、篡改 manifest 路径、非对象 manifest、覆盖拒绝、备份、首次链接、升级、复制、适配失败回滚、短 staging 与 Windows 长路径。
- `skill-creator` 的 `quick_validate.py` 在 UTF-8 模式下通过；本轮 32 个 Markdown 相对链接检查无失效目标。
- Windows PowerShell 5.1 入口完成双目录 copy 安装和 `--verify`。默认策略禁止运行 ps1，实测仅为该进程使用 `-ExecutionPolicy Bypass`，未改全局策略；直接 `python install.py` 不需要此步骤。
- Skills CLI **1.7.2** 实测：本地源码 `--list` 发现唯一技能；隔离项目安装到 Codex 通用目录，并为 CodeBuddy、Claude Code 建立 Junction；这些是安装/文件层验证，不是三个产品的完整模型执行验证。
- Skills CLI **1.7.2** 补充实测：`npx skills add zhulehan683-commits/zhengda-research-copilot --list` 能从 GitHub 发现唯一技能并显示名称与描述；`npx skills use zhulehan683-commits/zhengda-research-copilot --skill zhengda-research-copilot` 能生成完整 `SKILL.md` 入口提示并下载引用资源。该验证覆盖生态发现与提示生成，不等价于任何特定 Agent 的原生加载或模型执行。
- 安装副本实测：从 `D:\zlh\agents\skills\zhengda-research-copilot` 初始化 13 阶段项目、运行 `status`、执行合成 CSV 预检得到 `READY_FOR_REVIEW`，并用非法 schema 验证错误退出 2；原数据未被改写。

## Magpie 执行端审计

实际 CLI 在隔离目录执行，模型请求经本机 Magpie 的 `group/auto-deepseek-v4-flash`。网关地址、密钥与个人会话日志未打包到公开仓库。

- DSH 审计生成 `audit.json` 与 `repro.py`，主控执行 `validate_audit.py` 返回 `AUDIT_OK`。复现的首次链接、运行依赖缺失、输出覆盖状态、管理目录 Junction、损坏 JSON 与长路径问题均补充主控回归测试并修正。DSH 审查的是实现中间快照；修复后由主控测试验证，未声称 DSH 再审全部最终代码。
- WorkBuddy 审计生成独立 `audit.json` 与复现脚本，主控机器验收通过。便利样本区间、PPT 大纲状态、篇幅合计和跨平台检查反馈已作适配；没有机械照搬其建议的统一参数或阈值。
- WorkBuddy 另在独立快照执行 3 个实际应答场景：无数据索要显著回归、只要 PPT 大纲、便利样本索要全国 CI。应答分别保留设计产物、占位大纲和样本推断边界；模型仍有冗长解释、主动给设计参数与过度强调答辩结果的倾向，不能视为完美指令遵从。随后补充范围与承诺的入口指引，未用这三次应答认证所有后续输出。
- 实际执行 `init/status`、再次 `init` 拒绝覆盖、合成两行 CSV 越界预检；退出码依次 0/0/2/3，数据哈希前后一致。合成夹具明确标识为测试用途，未登记为真实参赛证据；`validate_final.py` 主控重跑得到 `SCENARIOS_OK`。
- 初次默认路由失败有记录，不能作为交付：DSH 免费模型被上游拒绝，WorkBuddy 默认配置报额度耗尽。切换只采用任务级 Magpie 路由。WorkBuddy 场景验证初轮达到 20 次调用上限，随后恢复同一真实会话完成，没有伪造会话记录。

### 2026-10-18 Magpie 复审与指令场景

本轮另用 Magpie `codex/gpt-6.1-sol` 对当前技能全文做独立静态审计（51,642 输入 token、6,941 输出 token），审计明确区分“已实现”“无法从当前材料核验”和“建议”，并指出设计合同、计算依赖、任务输入、CLI 退出码、CSV schema 与首次使用路径等断点；相应修复已由主控实现，不能把模型建议本身当作通过证据。

对实现 diff 的第二轮 Magpie 复审（22,315 输入 token、2,501 输出 token）又发现两个 P2：`min/max: null` 的非预期 `TypeError`，以及已签收任务未检查执行日志哈希变化。两者已修复，并新增 schema 空边界值和 `STALE_EXECUTION` 回归测试；最终 63 项测试中 62 通过、1 项因本机符号链接权限跳过。

另用同一 Magpie 路由执行 3 个隔离指令场景，每个场景只注入当前 `SKILL.md` 与相关参考文件：无数据选题比较、已有问卷审核、便利样本索取全国推断。三次请求均完成（合计约 39,924 token）；关键词/行为检查确认：选题场景给出 3 个候选并保留待核验项，问卷场景标为 `BLOCKED` 并要求预调查/知情同意，便利样本场景拒绝全国代表性、伪造区间和获奖结论。该检查只覆盖 3 个场景，不证明所有模型或所有 Agent 都能稳定遵从。

上述结果证明有限场景的 CLI 使用和机械行为，未验证无人值守完整竞赛、真实受访者数据、统计模型结论、全部 Agent 原生发现或评审身份。Hermes 协调请求当时受其默认免费上游拒绝，本轮不宣称获得 Hermes 复核；本地真实派工、提示词、日志和回执已落盘保留。

## 来源检查

新增适配 `maydengximin-sketch/questionnaire-analysis-skill`，固定提交、原文件 SHA-256 与完整 MIT 许可均保存。`scdenney/open-science-skills` 为 CC BY-NC 4.0，仅链接参考；`MAS-32/conduct-market-research` 本轮未确认根许可证，因此未合并。安装设计参考 Skills CLI 官方 README/Agent 配置，未复制其实现代码。

## CI 范围

本轮将 CI 配置扩展为 Windows/Linux 与 Python 3.10—3.13，并增加安装与命令入口检查。实际运行结果以对应提交的 GitHub Actions 为准，不能用“已配置矩阵”代替“所有平台已通过”。
