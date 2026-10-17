# 多 Agent 交接协议（Hermes/Codex/DSH/Workbud 为可选映射）

## 明确边界

本 Skill 可以在一个 Codex 实例运行；不要求存在 Hermes/DSH/Workbud。若接入：Hermes = 全局统筹；Codex = 研究任务拆分和模型/代码协调；DSH = 数据/实验执行；Workbud = 报告/演示素材；独立 reviewer = 其他未参与该工件作者。角色映射是**建议**，不是连接成功的证据。

## 交付契约

任务字段：`task_id, stage, title, assignee, acceptance_file, inputs, status, history, output_path, sha256, reviewed_by`。

执行端：
1. `create` 任务时提供验收条款文件和承接角色。
2. 执行端用 `claim --actor <assignee>` 认领，隔离目录完成文件；不得直接写 `state/project.json`。
3. 执行端运行实际计算/生成，提交文件+ SHA-256；“完成”只表示已提交候选输出，状态为 `needs_review`。
4. 独立审查者必须不同于 `assignee`，`review pass` 才将队列项标记 `accepted`。实际身份隔离仍由调用环境确认。
5. `task_queue.py list` 同时显示存储状态和 `effective_status`；若验收条款或已提交输出文件在审核后变化，任务应显示 `STALE_ACCEPTANCE` / `STALE_OUTPUT`，不可继续把旧结果当作有效签收。
6. 协调者将接受的成果与权威状态绑定，再执行阶段门禁；**任务 accepted != 阶段 passed**。

## 严格证据

不能以“发送了请求”代替“执行者实际收到并执行”；不能以“报告成功”代替独立复现。要证明自动协作闭环，必须记录**同一 task_id**：派发时间、认领时间、执行日志、提交时间/产物 SHA、审查意见、权威项目状态更新时间。外部适配器需要记录真实命令/退出码；当前项目只包含本地队列/状态记录，并无后台自动轮询、SDK、远程 Agent 调用。

## 避免冲突

- 同一权威结果只允许一个主写者；并行仅用独立输入/输出目录。
- 上游模型变更必须使下游审核失效；不让报告 Agent 单独“优化”模型数据。
- 原始 `raw_dataset` 必须放在工作区 `raw_private/` 下；不在多个 Agent 的上下文传播受访者 PII，脱敏分析表优先。
- 同时改写 `state/project.json` 要串行或由唯一协调者更新；脚本使用本地排他锁，跨机器协作需可靠的集中状态存储。

## CLI 样例

```powershell
python scripts/task_queue.py create --project "D:\Competitions\Zhengda2027" --stage analysis --assignee DSH --title "回归模型独立运行" --acceptance-file "D:\Competitions\Zhengda2027\plans\analysis_acceptance.md"
python scripts/task_queue.py list --project "D:\Competitions\Zhengda2027"
python scripts/task_queue.py claim --project "D:\Competitions\Zhengda2027" --id <task_id> --actor DSH
python scripts/task_queue.py submit --project "D:\Competitions\Zhengda2027" --id <task_id> --actor DSH --output "D:\Competitions\Zhengda2027\analysis\results.csv"
python scripts/task_queue.py review --project "D:\Competitions\Zhengda2027" --id <task_id> --actor IndependentQA --decision pass --note "复现数值一致"
```
