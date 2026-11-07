# 选题、证据与调研方案

## 选题比较（至少 3 个备选）

各项 1–5 分，仅为研究**决策工具**，不属于官方评分标准：可调研人群与样本可达性、公共/行业数据可得性、痛点可验证性、结论可行动性、团队方法匹配、伦理与时间风险。保留淘汰原因。市场规模测算要分清总体、时间、币种、测算模型、数据来源。

### 第四步：查历届获奖题目，避免撞题

在给候选题打分前，必须做一次公开获奖题目的密度检索：

1. 先看离线聚合基线，判断是否值得继续查具体题目：
   `python -X utf8 "<SKILL_ROOT>/scripts/topic_radar.py" baseline`
2. 需要精确题目时，由用户显式抓取固定快照到项目私有目录，再按核心对象词、行为词、行业词和中英文同义词检索：
   `python -X utf8 "<SKILL_ROOT>/scripts/topic_radar.py" fetch --project "<PROJECT_ROOT>"`
   `python -X utf8 "<SKILL_ROOT>/scripts/topic_radar.py" search --project "<PROJECT_ROOT>" --query "<词1 词2>" --write "<PROJECT_ROOT>/plans/topic-density.md"`
3. 在中国商业统计学会官网、赛区/本校公告和公开获奖名单中补充检索，不能把第三方聚合数据当成唯一来源。
4. 记录每个候选题的**同题数量、筛选范围、最高奖项、年份分布、最接近的题目**。同题已有一等奖是重复度的直接证据；多年空白是差异化的线索，但也要检查是否因为不可做。
5. 把结果写进 `templates/topic-scorecard.csv` 的结构化密度列，并把公告链接放进 `problem_evidence` 或来源登记表。
6. 不下载、不分发未授权的获奖全文；公开公告只用于题目去重和赛道判断，不能替代自己的调查证据。

检索示例（按实际届次替换年份）：

```text
site:china-cssc.org 正大杯 获奖 名单 <对象词>
正大杯 第 <届> 届 获奖 题目 <对象词> <行为词>
<学校> 市场调查与分析大赛 获奖 名单 <对象词>
```

如果查不到公开名单，记录检索词、检索日期和“未找到”，不要据此声称赛道空白。

零命中、低置信度和缺失组别的解释边界见 `references/award-topics.md`。雷达是撞题线索，不是创新性评分或获奖预测。

## 研究问题

每个问题填：目标主体、可观测概念、变量或访谈主题、数据来源、可检验假设、结论可能作用于谁。研究框架不能因后续显著性结果随意改变。定量+定性组合必须说明各自弥补的缺陷。

## 文献/市场来源登记

建议 `sources/source_register.csv` 列：`id,title,publisher,publication_date,url,retrieved_at,source_type,method,scope,metric_definition,reliability,used_for,limitations`。

- 不把二手报道伪装为原始数据；官方标准与政策优先到发布机构核验。
- 来源较旧时注明年份；竞争分析不得混合不同年度口径。
- 统计显著不代表市场重要；建议还需考虑执行成本和主体职责。
