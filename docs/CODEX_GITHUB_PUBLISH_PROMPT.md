# 给 Codex 的 GitHub 发布提示词

> 只有在项目所有者明确决定创建 GitHub 仓库并说明是否公开后，才执行远程创建或推送。本文件本身不会创建仓库。

```text
请将当前 zhengda-research-copilot 项目整理为可维护的 GitHub 仓库。

目标：为正大杯等大学生市场调查与分析竞赛提供中文优先的 Agent Skill；当前首个配置是第十七届正大杯 2026–2027。项目包含 13 阶段研究流程、本地状态/证据检查、任务交接脚本、研究模板、测试和 GitHub 发布文档。

发布前必须：
1. 读取 README.md、docs/PROJECT_SPEC.md、CHANGELOG.md、THIRD_PARTY_NOTICES.md、LICENSE-DECISION.md 和 docs/RELEASE_CHECKLIST.md。
2. 检查工作区与 Git 历史，确认没有真实受访者数据、报名代码、账号凭证、API Key、Token、.env、私有日志或无关文件。
3. 运行 `python -m unittest discover -s tests -p 'test_*.py' -v`、`python scripts/workflow.py --help`、`python scripts/task_queue.py --help`。
4. 检查所有内部文档链接、安装命令、阶段名和实际代码一致。
5. 检查第三方来源与许可。当前 LICENSE-DECISION.md 标记许可证待确认；不要自行添加许可证，也不要把项目描述为已获开源授权。
6. 不要添加虚假的 CI 状态、覆盖率、下载量或功能徽章。
7. 说明 Windows PowerShell 安装脚本是否已在真实 Windows 环境测试；不能实测就标为未验证。
8. 汇报所有测试、缺陷、文件变更和剩余风险。

远程发布边界：
- 未经我明确确认，不创建远程仓库、不推送、不改为公开、不创建 Release。
- 如果我已经指定仓库 URL 和可见性，则先展示拟提交文件清单与 `git diff --check` 结果，再按授权操作。
- 优先建议先创建私有仓库；许可证确认后再考虑公开。
- 不修改 Hermes、DSH、Workbud 或其他现有 Agent 配置。

最后提供仓库 URL（仅在真实创建成功后）、commit hash、测试结果和仍待确认事项。
```
