# 示例项目：校园咖啡自带杯折扣

这是一个**演示项目**，用于展示从选题到设计冻结的最小结构。所有受访者数据都是程序生成的模拟数据，**不得用于参赛、报告或任何真实推断**。

## 包含什么

- 已填写的 Intake、研究简报、选题评分表（含撞题密度）；
- 三个二手来源与一份研究缺口说明；
- 问卷说明、抽样计划、伦理说明、变量字典、分析合同；
- 50 行模拟数据与预检 schema；
- 可直接绑定到 `topic`、`desk_research`、`design` 的证据文件。

## 跑一遍

在仓库根目录执行（把 `<PROJECT_ROOT>` 换成一个新目录）：

```sh
python -X utf8 scripts/workflow.py init --project "<PROJECT_ROOT>" --competition zhengda-17 --season 2026-2027
python -X utf8 scripts/workflow.py template --project "<PROJECT_ROOT>" --name rules-verification.json
```

然后把本目录的 `intake.md`、`plans/`、`sources/`、`data/` 复制进项目，按下面顺序绑定：

```sh
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key official_notice --file sources/rules-verification.json --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key rules_verification --file sources/rules-verification.json --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key registration_confirmation --file intake.md --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage registration --reviewer DemoReviewer --decision pass --note "演示状态，不是真实报名"
```

`knowledge`、`team` 也用演示文件绑定后，再依次绑定 `topic`、`desk_research`、`design`。完整命令见本目录 `RUNBOOK.md`。`gate` 的输出是 `PASS_MECHANICAL_ONLY`，只代表文件与哈希结构完整，不代表研究科学有效。

## 不要做什么

- 不要把模拟数据改成“真实回收数据”；
- 不要把示例里的规则核验日期当作本人核验；
- 不要把 `PASS_MECHANICAL_ONLY` 当成阶段科学通过。
