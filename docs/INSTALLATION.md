# 统一安装与迁移

本项目使用标准 `SKILL.md`，同一入口、参考资料和脚本供不同 Agent 使用。安装只提供技能文件，不提供模型额度、统计软件或跨 Agent 调度服务。原生发现目录与执行模型路由分别配置。

## 方式一：Skills CLI（联网，适合常见 Agent）

先安装 Node.js/npm 与 Git，再按 [vercel-labs/skills 官方说明](https://github.com/vercel-labs/skills)选择 Agent。查看内容：

```sh
npx skills add zhulehan683-commits/zhengda-research-copilot --list
```

全局安装到指定 Agent，共用同一份技能：

```sh
npx skills add zhulehan683-commits/zhengda-research-copilot --skill zhengda-research-copilot -g -a codex -a claude-code -a codebuddy -a hermes-agent -y
```

只列出你实际使用的 Agent；`--all` 会覆盖更广的目标，不作为默认命令。项目级安装移除 `-g`，在研究项目目录运行。Skills CLI 自己管理安装布局和更新记录；使用 `npx skills list -g`、`npx skills update zhengda-research-copilot -g`，不要再用下面的离线安装器覆盖同一副本。上游 CLI 的 `--copy` 是独立副本模式，更新后需检查各副本。

## 方式二：仓库内离线安装器（Python 3.10+）

Git clone 或完整 ZIP 解压后，在仓库根目录运行。Python 标准库即可，安装阶段不联网。

```sh
python install.py --dry-run
python install.py
python install.py --verify
```

默认唯一主副本：`~/.agents/skills/zhengda-research-copilot/`。只复制运行资源、许可和文档，排除 `.git`、Python 缓存和单元测试；不复制原始研究数据。哈希清单为 `.skill-install.json`，只验证安装完整性，不能证明来源可信或 Agent 已成功执行。

Windows 放在 D 盘、再把需要的发现目录指向主副本：

```powershell
python install.py --target-root D:\zlh\agents\skills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.codebuddy\skills" --dry-run
python install.py --target-root D:\zlh\agents\skills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.codebuddy\skills"
python install.py --target-root D:\zlh\agents\skills --agent-root "$HOME\.agents\skills" --agent-root "$HOME\.codebuddy\skills" --verify
```

Windows 的 `link` 使用目录联接（Junction），POSIX 使用目录符号链接。可重复添加 `--agent-root`，参数是**skills 根目录**，不要再加技能名；不改 Agent 配置、密钥或模型。目标根目录允许已有目录联接；安装器会使用其真实目标，并拒绝源目录与目标目录相互包含。

Windows 兼容入口：`./install.ps1 -TargetRoot D:\zlh\agents\skills -AgentRoot "$HOME\.agents\skills","$HOME\.codebuddy\skills"`；支持 `-Force`、`-Verify`、`-DryRun`、`-Mode copy`、`-Python <Python可执行文件>`。

若本机 PowerShell 策略阻止脚本，直接使用上述 `python install.py`；不必改全局执行策略。审查过脚本后也可仅为本次进程指定 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun`。

如环境无法建立链接，加 `--mode copy`。此时是相同内容的多个副本，**不是持续同步**；升级时用相同的根目录列表重新安装。安装不启动 Agent、不声称运行验证通过。

## Agent 发现目录

下表按 [Skills CLI 的 Agent 配置](https://github.com/vercel-labs/skills/blob/main/src/agents.ts)核对（2026-10-18）；具体版本可能支持额外目录。仅在实际配置与应用文档相符时使用。

| Agent | 常见全局技能根目录 | 本项目接入方式 |
| --- | --- | --- |
| Codex | `~/.agents/skills` | 默认共享目录；自定义安装可显式链接到这里 |
| Claude Code | `$CLAUDE_CONFIG_DIR/skills` 或 `~/.claude/skills` | 作为 `--agent-root` |
| CodeBuddy | `~/.codebuddy/skills` | 作为 `--agent-root`；定制配置目录需按实际发现路径核验 |
| Hermes Agent | `$HERMES_HOME/skills` 或 `~/.hermes/skills` | 作为 `--agent-root`；技能加载/审批行为以实际版本为准 |
| OpenCode | `$XDG_CONFIG_HOME/opencode/skills` 或 `~/.config/opencode/skills` | 作为 `--agent-root` |
| Cursor | `~/.cursor/skills` | 作为 `--agent-root` |
| DSH/其他 Harness | 取决于 profile、技能插件与启动器 | 核实发现根后显式适配；否则由主控提供 `SKILL.md` 和本次需要的资料 |

CodeBuddy、WorkBuddy 桌面版与其 CLI 的配置目录可能不同；文件可读、技能被列出和模型完成任务是三个不同检查。不要仅凭写入目录就宣称所有产品都支持该技能。

## 升级、冲突与恢复

- 默认拒绝覆盖已有目标；核对来源后加 `--force`。先在临时 staging 校验，再替换目标；替换旧版前备份到各 skills 根目录的同级 `.skill-backups/` 下，位于技能扫描目录之外。
- 多目标安装失败时回滚本次替换。安装期间停止其它安装器对相同目录的并发写入；安装器不是分布式事务或多进程锁服务。
- 旧标识为 `market-survey-competition`。新旧名不会自动互相覆盖；先安装新版本并验收，再把旧技能目录移到扫描根之外归档，避免同时触发。旧研究工作区的 `state/project.json` 无需重新初始化。
- 恢复某个备份前，先把当前候选移到扫描根之外，再将日志中的备份目录移回目标。链接只删除/移动链接本身，保留主副本。
- 退出码：安装/验证成功 0，冲突或错误 2；`--verify` 只核对哈希，不做原生加载或联网测试。

## 安装后的验收

1. `python install.py --verify` 核对主副本；有 adapter 时带同一组 `--agent-root`。
2. 新开 Agent 会话，在技能列表确认 `zhengda-research-copilot`；未列出则核对该版本技能根，不复制到猜测的路径。
3. 让它在临时研究工作区执行 `workflow.py init/status`，确认输出 13 阶段、已有状态不被覆盖。
4. 让它在没有真实数据时给分析计划，再用测试 CSV 执行 `survey_audit.py`。测试输入需标明合成验收夹具，不能作为参赛调查证据。

代理/网关（例如 Magpie）属于执行环境：检查正在使用的模型确实走指定网关、请求成功且有真实文件与验收日志。本网关配置、模型和密钥不写入公开技能包；文件安装成功与模型有额度分开报告。
