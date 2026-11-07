# 统计分析与复现

## 本 Skill 的代码边界

本技能自带可离线运行的 `scripts/stats_basic.py` 与 `scripts/power_calc.py`，覆盖：

- 描述统计、均值置信区间、单/双样本与配对 t 检验；
- 卡方独立性检验、Fisher 精确检验、频数表；
- Cronbach's α、简单 OLS、二元 Logit（IRLS）；
- 比例/均值/卡方的样本量与功效近似计算。

**不覆盖**：复杂抽样权重与设计效应、SEM/CFA、多层模型、潜类别、机器学习、因果识别、缺失数据多重插补。需要这些方法时，使用用户自备的 R、Stata、SPSS、AMOS、Mplus 或 Python 第三方环境；本技能只提供分析合同、变量字典、结果登记与复现门禁。不要因为脚本能跑就声称方法前提已经满足。

## 数据合同

问卷分析先读 `references/measurement-and-inference.md`；填写 `templates/analysis-contract.csv`，对真实 CSV 按变量合同执行 `scripts/survey_audit.py`。预检不等同信效度、抽样代表性或模型诊断通过。

保留源数据只读副本、SHA-256、变量字典、问卷版本、清洗脚本、执行命令和日志。分析仅使用脱敏数据。建立`变量 → 测量尺度 → 缺失逻辑 → 研究问题 → 分析方法`映射。

最小闭环示例（60 人、5 个 Likert 题、一个 0/1 结果）：

```sh
python -X utf8 "<SKILL_ROOT>/scripts/stats_basic.py" alpha --data data/clean.csv --columns q1,q2,q3,q4,q5
python -X utf8 "<SKILL_ROOT>/scripts/stats_basic.py" describe --data data/clean.csv --columns q1,q2,q3,q4,q5
python -X utf8 "<SKILL_ROOT>/scripts/stats_basic.py" logit --data data/clean.csv --y purchase --x q1,q2,q3
python -X utf8 "<SKILL_ROOT>/scripts/power_calc.py" proportion --p 0.5 --margin 0.05 --dropout 0.1
```

脚本只做成对完整案例分析，不插补、不加权、不自动反向计分；必须在 `cleaning-report.md` 记录这些决定。

## 方法选择

| 目的 | 可选方法 | 关键检查 |
|---|---|---|
| 总体描述 | 频数、比例、置信区间、交叉表 | 抽样方法与设计权重；分母与缺失 |
| 组间差异 | t 检验/ANOVA/非参数检验 | 组样本量、分布、方差、效应量 |
| 相关与解释 | 线性/Logit/有序回归 | 编码、共线性、拟合、混杂、相关≠因果 |
| 测量模型 | α、EFA/CFA、SEM | 理论结构、样本量、估计方法、模型可识别性 |
| 消费者细分 | 聚类、潜类别 | 标准化、稳定性、分群可解释性 |
| 改善优先级 | IPA、KANO、联合分析 | 题项和实验设计是否满足前提 |
| 文本分析 | 人工编码、TF-IDF、主题、情感 | 语料合法性、代表性、文本重复、模型误差 |
| 预测 | 逻辑回归、树/森林等 | 泄露、交叉验证、外部/时间验证和解释 |

先使用能够回答问题的最简基线；高级模型必须通过增量价值检验。没有适用数据不要为凑模型而跑 SEM/随机森林/词云。

## 独立复现门禁

最终报告的每项关键数值必须映射到脚本产物：`claim_id, question_id, dataset_sha256, command, output_path, figure_or_table, value, unit, sample_n, limit`。独立 reviewer 应在干净环境运行同一命令并核对退出码、主结果与参数范围；跑不通就是阻塞。图表应有来源、单位、有效样本数与对应研究问题。
