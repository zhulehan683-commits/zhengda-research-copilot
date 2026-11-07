# 命令参考

以下命令从主技能根目录执行；从其他目录运行时使用脚本绝对路径。研究工作区与技能安装目录分开。

## 项目状态与证据

| 场景 | 命令 | 结果判断 |
| --- | --- | --- |
| 新建研究项目 | `python -X utf8 scripts/workflow.py init --project $project --competition zhengda-17 --season 2026-2027` | 创建 13 阶段状态；已有项目会被拒绝覆盖 |
| 查看阶段状态 | `python -X utf8 scripts/workflow.py status --project $project` | 输出各阶段状态、证据与待办门禁 |
| 登记证据文件 | `python -X utf8 scripts/workflow.py evidence add --project $project --stage <阶段> --key <证据键> --file <项目内文件> --author <作者>` | 记录路径与哈希；默认拒绝覆盖已存在的键 |
| 强制替换证据 | 在上一行加 `--force` | 返回 `replaced` 块，含旧路径、SHA-256、作者和时间 |
| 查看证据绑定 | `python -X utf8 scripts/workflow.py evidence list --project $project --stage <阶段>` | 列出路径、哈希、作者与是否漂移 |
| 检查阶段门禁 | `python -X utf8 scripts/workflow.py gate --project $project --stage <阶段>` | `0` 表示机械检查通过，`3` 表示阻断，`2` 表示输入错误 |
| 记录独立复核 | `python -X utf8 scripts/workflow.py review --project $project --stage <阶段> --reviewer <复核者> --decision pass --note <意见>` | 复核记录用于留痕；通过与放行仍需协调者核实 |
| 复制模板 | `python -X utf8 scripts/workflow.py template --project $project --name analysis-contract.csv` | 默认写入 `plans/`；已存在时拒绝，需 `--dest` 或 `--force` |

`rules_verification` 必须是 JSON（推荐）或含 `verified_at` 与两个公告 URL 的 Markdown；日期超过 60 天会被 `gate` 阻断。证据路径使用 `/` 分隔符保存，Windows 与 POSIX 可互读。

## CSV 预检

```powershell
python -X utf8 scripts/survey_audit.py --project $project --data raw_private/survey.csv --schema plans/data-schema.json --output analysis/data-preflight-01.json
```

| 退出码 | 含义 | 后续动作 |
| --- | --- | --- |
| `0` | `READY_FOR_REVIEW` | 进入人工复核，继续检查样本、测量和分析条件 |
| `3` | `BLOCKED` | 处理数据合同问题，解释或修正后重新预检 |
| `2` | 输入或执行错误 | 核对路径、schema、编码和输出文件是否已存在 |

schema 支持 `item_group`（同题多列，组内全空记一次缺失）、`reverse_coding`（只报告，不改数）、`likert_points`（展开 1..N）、`multi_select_separator`（一格多值，如 `A|B`）。导出格式对照见 [SURVEY_EXPORTS.md](SURVEY_EXPORTS.md)。

## 基础统计与样本量

```powershell
# 描述统计与置信区间
python -X utf8 scripts/stats_basic.py describe --data data/clean.csv --columns q1,q2,q3

# 单样本 / 两组 t 检验
python -X utf8 scripts/stats_basic.py ttest --data data/clean.csv --value score --popmean 3
python -X utf8 scripts/stats_basic.py ttest --data data/clean.csv --value score --group group

# 卡方 / Fisher / 信度
python -X utf8 scripts/stats_basic.py chisq --data data/clean.csv --row gender --col purchase
python -X utf8 scripts/stats_basic.py fisher --data data/clean.csv --row gender --col purchase
python -X utf8 scripts/stats_basic.py alpha --data data/clean.csv --columns q1,q2,q3,q4,q5

# OLS / 二元 Logit
python -X utf8 scripts/stats_basic.py ols --data data/clean.csv --y score --x q1,q2
python -X utf8 scripts/stats_basic.py logit --data data/clean.csv --y purchase --x q1,q2

# 样本量与功效
python -X utf8 scripts/power_calc.py proportion --p 0.5 --margin 0.05 --dropout 0.1
python -X utf8 scripts/power_calc.py two-proportions --p1 0.4 --p2 0.6 --dropout 0.1
python -X utf8 scripts/power_calc.py mean --delta 0.5 --sd 1.0 --power 0.8
python -X utf8 scripts/power_calc.py chisq --effect-size 0.3 --df 1
```

这些脚本只做成对完整案例分析，不插补、不加权、不自动反向计分。SEM、复杂抽样、机器学习等不在覆盖范围，见 [analysis.md](../references/analysis.md)。

## 两个高频入口

```powershell
# 选题/设计/分析/报告/答辩前，生成当前决策前沿，3 问快速版
python -X utf8 scripts/advisor.py grill --stage topic --project $project --quick

# 需要外部能力时，先扫本地技能；只打印检索命令，不联网、不安装
python -X utf8 scripts/advisor.py find --need "问卷 统计分析"
```

`grill --write` 会把本轮问题写入 `plans/grill-<stage>-<timestamp>.md`，不修改项目状态。`find` 的本地候选只是发现线索，安装前必须核验 SKILL.md、依赖、许可证与固定提交。

## 协作与复核

| 需求 | 入口 |
| --- | --- |
| 输入快照、执行回执与任务签收 | `python -X utf8 scripts/task_queue.py --help`、[协作协议](../references/agents.md) |
| 七维评分汇总 | `python -X utf8 scripts/score_review.py --help`、[角色与复核](../references/roles-and-review.md) |
| 选择研究模板 | [模板索引](../templates/README.md) |

`workflow.py gate` / `review` 的阻断或复核不通过返回 `3`，输入错误返回 `2`。签收任务时检查真实文件和验收记录，而不仅是进程是否启动或退出。
