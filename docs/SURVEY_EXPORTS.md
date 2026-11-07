# 问卷平台导出对照

本表用于把问卷星、腾讯问卷、Credamo 的常见导出形态映射到 `templates/data-preflight-schema.json`。平台版本和导出选项会变化，使用前先看实际表头与编码说明。

## 常见形态

| 平台/形态 | 典型表头 | schema 写法 | 预检行为 |
| --- | --- | --- | --- |
| 单选/量表 | `Q1`、`3` | `{"type":"integer","likert_points":5}` | 1..5 之外的值为 `disallowed` |
| 反向题 | `Q5`、`2` | `{"type":"integer","likert_points":5,"reverse_coding":true}` | 只报告 `reverse_coding_declared`，不改原值 |
| 多选一列多值 | `Q5`、`A|B|C` | `{"type":"string","multi_select_separator":"|","allowed_values":["A","B","C"]}` | 逐个 token 校验；空 token 记 `disallowed` |
| 多选拆列 | `Q5_1`、`Q5_2`、`Q5_3` | 每列 `{"type":"integer","item_group":"q5","allowed_values":[0,1]}` | 组内全空记一次 `group_missing`；不重复报每列缺失 |
| 排序/矩阵 | `Q6_1`..`Q6_5` | 按变量字典拆成独立变量，必要时设 `min/max` | 只做结构与范围检查，不推断矩阵一致性 |
| 开放题 | `Q7` | `{"type":"string","required":false}` | 不输出原文，只统计缺失与列映射 |
| 平台元数据 | `提交时间`、`IP`、`用时` | 不放进 `variables` | 会出现在 `unmapped_columns`，人工决定是否删除或脱敏 |

## 问卷星

- 导出 CSV 时优先选择“按选项编号”而不是“按选项文本”，否则 `allowed_values` 要跟着改。
- 多选常见为一列 `A|B|C`，也可能按选项拆列；以实际表头为准。
- 矩阵题通常拆成 `Q6_1`..`Q6_n`，建议只把用于分析的子列放进 schema。
- 不要收集学号、手机号；如果平台默认收集，导出后先删除或哈希化。

## 腾讯问卷

- 多选常见为 `A,B,C` 或 `A|B|C`；把 `multi_select_separator` 设成实际分隔符。
- “其他”选项常写成开放文本，建议单独建变量并标注 `string`，不要混进数值量表。
- 导出编码常为 UTF-8 with BOM；预检默认 `utf-8-sig` 可读。

## Credamo

- 常见宽表导出，量表题多为 1–7；`likert_points` 要按实际点数设置，不能套用 5 点。
- 平台可能带 `Duration`、`IP`、`Longitude` 等字段；这些不进入分析变量，先脱敏。
- 反向题与注意力检测题要在变量字典中单独标注；预检只报告，不自动改分或删卷。

## 共同规则

1. 先保留原始导出只读副本，再写 schema；不要在原始 CSV 上手工改数。
2. 多选组只在 schema 中声明一次 `item_group`；每列都要出现。
3. `reverse_coding` 是提示，不是自动转换；清洗脚本中显式执行并记录。
4. 平台导出的“无效样本”标记不能直接当作删除依据；先定义规则并留痕。
5. 预检 `READY_FOR_REVIEW` 只代表结构与取值没触发阻断，不代表样本代表性或量表效度。
