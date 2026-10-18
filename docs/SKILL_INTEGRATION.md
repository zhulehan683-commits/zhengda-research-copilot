# Grill Me / Find Skills 整合记录

保留主技能和原有 13 阶段；压力测试研究决策、发现缺少的外部能力均按需使用，不要求每次研究都先访谈或联网。

## 上游原文与研究适配

| 上游原文 | 本项目路由 | 适配点 |
| --- | --- | --- |
| [grill-me](../references/upstream-skills/grill-me/SKILL.md) | [研究压力测试](../references/grill-me.md) | 原文依赖 grilling，实际入口直接包含完整行为 |
| [grilling](../references/upstream-skills/grilling/SKILL.md) | 同上 | 研究决策树、当前范围、待验证事实、结束时解释完整研究 |
| [find-skills](../references/upstream-skills/find-skills/SKILL.md) | [能力发现](../references/find-skills.md) | 先本地再生态，审查方法与数据去向，按授权范围安装 |

固定提交和源文件哈希见 [upstreams.lock.json](upstreams.lock.json)，署名与完整 MIT 许可见[第三方声明](../THIRD_PARTY_NOTICES.md)。原文保留，不混入定制指令。新组件的 `original_copy` 是字节一致副本，`targets` 同时列出改编文件，不要求其哈希等于源哈希。

## 发现与安装

- clone 后，支持 `.agents/skills` 项目目录的客户端可在新会话发现子技能；其他客户端以自身配置为准。
- `.agents/skills/` 内的 [grill-me](../.agents/skills/grill-me/SKILL.md)、[grilling](../.agents/skills/grilling/SKILL.md)、[find-skills](../.agents/skills/find-skills/SKILL.md) 是自含的研究适配入口；即使客户端跳过主技能直接加载，也包含项目范围、无原生工具和离线降级的行为。
- 主技能读取研究指南或适配入口执行；`references/upstream-skills/` 仅供来源对照，不作为另一套运行指令覆盖适配约束。
- 离线安装器保留适配入口、三份原文与两份许可，均为必需文件并纳入安装哈希；不额外注册全局子技能。
- Skills CLI 默认发现根主技能，不表示子技能也独立安装。需查看主包实际文件；缺失时用完整 ZIP/离线安装器，或单独安装上游。

如需在**另一个研究项目**独立使用上游技能，可在该项目根目录执行（需要 npm、Git、网络）：

```sh
npx skills add mattpocock/skills --skill grill-me --skill grilling -a codex -y
npx skills add vercel-labs/skills --skill find-skills -a codex -y
```

替换 `-a codex` 为实际 Agent；这些命令跟随上游当前版本，与本仓库固定快照可能不同。已安装则检查现有副本，避免重复覆盖。用于本项目研究时仍采用研究适配指南。

## 冲突处理

| 问题 | 本项目处理 |
| --- | --- |
| 纯访谈被自动初始化项目 | 先识别模式，仅讨论时只读，需要保存研究产物时再初始化 |
| grill-me 只有转调指令 | 保存原文依赖，研究入口直接包含完整行为，无原生工具仍可运行 |
| 提问过广或一直不结束 | 限定本轮范围，复用已有决定，待预测试问题列为待验证，用完整研究说明结束 |
| 按热度挑选专业技能 | 安装数和 stars 仅作线索，判断任务适配、依赖与方法质量 |
| 原文示例全局安装 | 项目级为研究适配默认值，明确需要全局时才加 `-g` |
| 文件可读被声称为已加载 | 分别核验文件、原生发现、脚本、模型任务 |

## README 重写依据

参考 [README Skills](https://github.com/Shiaoming123/readme-skills/tree/d504414579dedbc5e7a86dd720ea2204a1bb9e08) 的 `restructure` 方法：本仓库是研究工作流 Skill，附带本地 CLI，当前为 Preview。写作技能不随研究包安装。

- 保留名称、13 阶段、CSV/证据链工具、原有署名和安装/模板/复核入口。
- 将安装与首个可用请求前置，详细方法与命令继续链接到现有文档。
- 增加新技能使用示例、原文与适配关系、原生工具缺失时的读取路径。
- 更正早期草稿“找不到来源、完全原创”的结论，登记实际 MIT 来源链。
- 不推断全部客户端加载、完整赛事无人值守、统计软件自带或原创许可证已决定。

验证以 [VALIDATION.md](VALIDATION.md) 本轮记录为准。
