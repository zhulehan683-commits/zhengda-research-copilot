# Find Skills：发现并接入外部能力

本指南适配 [vercel-labs/skills 的 find-skills](https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/skills/find-skills/SKILL.md)。原文位于 `references/upstream-skills/find-skills/SKILL.md`，MIT 许可见 `licenses/vercel-labs-skills/LICENSE`；`.agents/skills/find-skills/SKILL.md` 为研究适配入口，默认项目级安装并支持离线降级。

## 从实际缺口出发

用户要求找 skill 或当前任务确实缺少专门能力时启用。先识别要补的产物，例如：核验文献引用、执行统计诊断、导出 DOCX、制作答辩 PPT。已有内置参考和工具能完成时直接使用；普通研究步骤不强制联网搜索。

支持原生调用时使用本项目 find-skills；否则读取 `<SKILL_ROOT>/.agents/skills/find-skills/SKILL.md` 并执行本指南。适配入口包含安装范围、热度信号与离线行为约束，上游原文仅作来源对照。标准库研究脚本可离线运行，发现或安装外部 skill 才需要网络与相应工具。

## 发现、核验、选择

1. 看当前会话真实可发现的技能和工具；必要时只读检查用户指定的技能目录。名称相似不代表同一技能已加载。
2. 查 [skills.sh](https://skills.sh) 和 `npx skills find "<具体任务>"`；使用中英文同义词缩小候选。没有 npm 时使用 GitHub/网页检索；离线时报告暂不能查远端，继续能完成的本地工作。
3. 打开候选 GitHub 仓库的 SKILL.md、依赖、脚本和许可，记录固定提交。安装数、stars 和维护日期可作发现线索，不能替代内容审查或作为低热度专业技能的淘汰阈值。
4. 推荐最少必要的候选，并列出用途、真实输入输出、依赖、数据去向、来源/提交/许可、匹配理由、安装命令和未验证点。尚未执行就写“候选”，不写“已可用”。
5. 用户已授权安装时按指定范围安装；没有授权则给出建议。默认项目级安装，只有明确需要跨项目使用才加 `-g`；不要升级全部全局技能或覆盖现有副本来完成单个任务。

```sh
npx skills find "survey analysis"
npx skills add <owner/repo> --skill <实际技能名> -a <实际Agent> -y
```

## 与研究主流程交接

- 输入：本轮研究问题、允许访问的材料、已有工具、指定输出和验收条件。分享受访者数据前先获得授权并脱敏。
- 执行：仅调用当前确实可用的 skill/工具。需要隔离交接时使用 `task_queue.py`，记录输入快照、实际命令、退出码、日志与输出哈希。纯提示词任务没有命令时如实记录，不编造执行日志。
- 验收：文件安装、客户端发现、脚本运行、模型任务分别核验；发现失败可直接读取技能文件继续，不把手工读取声称为原生加载。
- 冲突：子技能不能自动修改研究总体、排除规则、原始数据或权威状态。采用其中与研究设计相符的部分，核心结论仍要从真实数据复现。
- 并入仓库：固定 commit，保存完整许可，更新 `THIRD_PARTY_NOTICES.md` 与 `docs/upstreams.lock.json`。许可证不明时可报告链接与用途，暂不复制分发。

## 选择示例

| 当前缺口 | 搜索方向 | 先检查 |
| --- | --- | --- |
| 文献表引用不全 | citation / literature verification | 能否验证原文，是否需要数据库权限 |
| 模型诊断不足 | statistical analysis / survey analysis | 方法前提、实际代码依赖、便利样本推断边界 |
| 报告交付为 Word | docx / document workflow | 是否真的能导出和检查版面 |
| 答辩材料 | presentation / pptx | 输出是 PPTX 还是网页，图表能否追溯 |
| 维护项目首页 | readme / documentation | 是否从仓库证据写作，是否保留来源和有效链接 |

查不到合适候选就明确记录查过的关键词与限制，回到本技能可执行的本地步骤。
