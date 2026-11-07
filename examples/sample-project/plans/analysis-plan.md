# 分析计划（演示）

1. 描述样本结构与各题分布；
2. 对 Q1 用配对 t 检验比较 2 元与 5 元情境下的重复购买意愿，同时报告均值差与 95% 置信区间；
3. 用 OLS 检查价格敏感度与折扣情境的交互，交互项作为探索性结果；
4. 报告缺失、排除和样本量变化；
5. 不做事后改主假设、不因显著性删样本。

运行示例：

```sh
python -X utf8 scripts/stats_basic.py describe --data data/sample_survey.csv --columns q3,q4,q5
python -X utf8 scripts/stats_basic.py alpha --data data/sample_survey.csv --columns q3,q4,q5,q6
python -X utf8 scripts/stats_basic.py ols --data data/sample_survey.csv --y repeat_intent --x discount_5,price_sensitivity
```
