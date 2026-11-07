# 示例项目运行手册

以下命令假设当前目录是仓库根目录，示例已复制到 `<PROJECT_ROOT>`。

```sh
# 1. 建项目
python -X utf8 scripts/workflow.py init --project "<PROJECT_ROOT>" --competition zhengda-17 --season 2026-2027

# 2. 绑定报名演示证据（规则文件需替换成本人真实核验）
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key official_notice --file sources/rules-verification.json --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key rules_verification --file sources/rules-verification.json --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage registration --key registration_confirmation --file intake.md --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage registration --reviewer DemoReviewer --decision pass --note "演示状态，不是真实报名"

# 3. 知识与团队演示证据
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage knowledge --key exam_result --file sources/demo-exam.txt --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage knowledge --reviewer DemoReviewer --decision pass --note "演示状态，不是真实成绩"
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage team --key team_roster --file sources/demo-team.csv --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage team --reviewer DemoReviewer --decision pass --note "演示状态，不是真实组队"

# 4. 选题与二手研究
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage topic --key topic_brief --file plans/topic-brief.md --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage topic --key feasibility_check --file plans/feasibility-check.md --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage topic --reviewer DemoReviewer --decision pass --note "演示状态，不是真实选题"
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage desk_research --key source_register --file sources/source_register.csv --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage desk_research --key research_gap --file sources/research-gap.md --author demo
python -X utf8 scripts/workflow.py review --project "<PROJECT_ROOT>" --stage desk_research --reviewer DemoReviewer --decision pass --note "演示状态，不是真实文献综述"

# 5. 设计冻结
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage design --key survey_instrument --file plans/survey-instrument.md --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage design --key sampling_plan --file plans/sampling-plan.md --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage design --key research_ethics --file plans/research-ethics.md --author demo
python -X utf8 scripts/workflow.py evidence add --project "<PROJECT_ROOT>" --stage design --key design_manifest --file plans/design-manifest.json --author demo

# 6. 机械门禁
python -X utf8 scripts/workflow.py gate --project "<PROJECT_ROOT>" --stage design
```

预期最后一条输出 `"status": "PASS_MECHANICAL_ONLY"`。这仍需要人工复核，且示例数据不能用于参赛。
