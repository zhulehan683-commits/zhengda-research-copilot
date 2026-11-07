#!/usr/bin/env python3
"""Award-topic density radar for Zhengda Cup topic screening.

The raw award-title snapshot is fetched only when the user explicitly asks.
This repository ships aggregate baselines, not the 2,920-row third-party
database. Searches are title/tag/keyword matches, not judgments that a topic is
novel, feasible, or likely to win.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import enable_utf8, fail


SOURCE_COMMIT = "b37a6dc2338500f69244d2046886c66e7d317d55"
SOURCE_PAGE = "https://bi-cmy.github.io/zhengda-cup-topic-dashboard/"
SOURCE_REPOSITORY = "https://github.com/Bi-cmy/zhengda-cup-topic-dashboard"
SOURCE_URL = (
    "https://raw.githubusercontent.com/Bi-cmy/zhengda-cup-topic-dashboard/"
    f"{SOURCE_COMMIT}/data.js"
)
SOURCE_SHA256 = "a1fb550d102e2a4076c44351c826eb7cebaa2624cd8b06b742c14d39b9e2cc1c"
MAX_SNAPSHOT_BYTES = 5 * 1024 * 1024
AWARD_RANK = {"一等奖": 2, "二等奖": 1}
CONFIDENCE_RANK = {"高": 3, "中": 2, "低": 1}
GROUP_ORDER = ("本科组", "研究生组", "专科组", "在华留学生组")


class RadarError(ValueError):
    """A user-correctable radar input or snapshot error."""


def _text(value, label: str, *, required=True) -> str:
    if isinstance(value, str):
        value = value.strip()
    elif required:
        raise RadarError(f"{label} must be a string")
    else:
        return ""
    if required and not value:
        raise RadarError(f"{label} must not be blank")
    return value


def _string_list(value, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RadarError(f"{label} must be an array of strings")
    return [item.strip() for item in value if item.strip()]


def _year(value) -> int:
    if isinstance(value, bool):
        raise RadarError("year must be a four-digit integer")
    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise RadarError("year must be a four-digit integer") from exc
    if not 2000 <= year <= 2100:
        raise RadarError("year must be between 2000 and 2100")
    return year


def _normalize_record(item, index: int) -> dict:
    if not isinstance(item, dict):
        raise RadarError(f"record {index} must be an object")
    return {
        "year": _year(item.get("y")),
        "group": _text(item.get("g"), f"record {index} group"),
        "award": _text(item.get("a"), f"record {index} award"),
        "title": _text(item.get("t"), f"record {index} title"),
        "school": _text(item.get("s"), f"record {index} school", required=False),
        "category": _text(item.get("p"), f"record {index} category", required=False),
        "detail": _text(item.get("d"), f"record {index} detail", required=False),
        "tags": _string_list(item.get("tags"), f"record {index} tags"),
        "keywords": _string_list(item.get("kw"), f"record {index} keywords"),
        "confidence": _text(item.get("c"), f"record {index} confidence", required=False),
        "review_required": bool(item.get("r", False)),
        "notice_url": _text(item.get("u"), f"record {index} notice_url", required=False),
    }


def parse_snapshot(text: str) -> list[dict]:
    stripped = text.lstrip("\ufeff").strip()
    if not stripped:
        raise RadarError("snapshot is empty")
    if stripped.startswith("window.AWARD_DATA"):
        match = re.search(r"=\s*(\[.*\])\s*;?\s*$", stripped, re.S)
        if not match:
            raise RadarError("snapshot does not contain a JSON array assigned to window.AWARD_DATA")
        payload = match.group(1)
    else:
        payload = stripped
    try:
        data = json.loads(payload)
    except ValueError as exc:
        raise RadarError(f"snapshot is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise RadarError("snapshot must contain a nonempty JSON array")
    return [_normalize_record(item, index) for index, item in enumerate(data)]


def load_snapshot(path: Path) -> tuple[list[dict], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RadarError(f"cannot read snapshot: {path}: {exc}") from exc
    digest = hashlib.sha256(raw).hexdigest()
    try:
        records = parse_snapshot(raw.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise RadarError("snapshot must be UTF-8") from exc
    return records, digest


def _award_best(values) -> str | None:
    values = list(values)
    if not values:
        return None
    return max(values, key=lambda value: AWARD_RANK.get(value, 0))


def _counter_dict(values, order=None) -> dict[str, int]:
    counts = Counter(str(value) for value in values)
    if order:
        keys = [key for key in order if key in counts]
        keys.extend(sorted(key for key in counts if key not in order))
    else:
        keys = sorted(counts)
    return {key: counts[key] for key in keys}


def coverage(records: list[dict]) -> dict:
    years = sorted({record["year"] for record in records})
    present_groups = {record["group"] for record in records}
    groups = [group for group in GROUP_ORDER if group in present_groups]
    groups.extend(sorted(present_groups - set(groups)))
    matrix = {
        str(year): {
            group: sum(1 for record in records
                       if record["year"] == year and record["group"] == group)
            for group in groups
            if any(record["year"] == year and record["group"] == group
                   for record in records)
        }
        for year in years
    }
    comparable = [
        group for group in groups
        if all(matrix[str(year)].get(group, 0) > 0 for year in years)
    ]
    return {
        "total": len(records),
        "years": years,
        "groups": groups,
        "awards": _counter_dict(record["award"] for record in records),
        "confidence": _counter_dict(record["confidence"] for record in records),
        "year_group_counts": matrix,
        "comparable_across_all_years": comparable,
        "missing_cells": [
            {"year": year, "group": group}
            for year in years for group in groups
            if matrix[str(year)].get(group, 0) == 0
        ],
    }


def _haystack(record: dict) -> str:
    return " ".join([
        record["title"],
        record["category"],
        record["detail"],
        " ".join(record["tags"]),
        " ".join(record["keywords"]),
    ]).casefold()


def _query_terms(query: str, extra_terms) -> list[str]:
    values = [query, *(extra_terms or [])]
    terms = []
    for value in values:
        if not value:
            continue
        for term in re.split(r"[\s,，、;；/|]+", value.casefold()):
            term = term.strip()
            if term and term not in terms:
                terms.append(term)
    if not terms:
        raise RadarError("--query must contain at least one nonblank term")
    return terms


def _filtered(records: list[dict], years, groups, awards, include_low_confidence):
    selected = records
    if years:
        wanted = {_year(value) for value in years}
        selected = [record for record in selected if record["year"] in wanted]
    if groups:
        wanted = {str(value).strip() for value in groups if str(value).strip()}
        selected = [record for record in selected if record["group"] in wanted]
    if awards:
        wanted = {str(value).strip() for value in awards if str(value).strip()}
        selected = [record for record in selected if record["award"] in wanted]
    if not include_low_confidence:
        selected = [record for record in selected if record.get("confidence") != "低"]
    return selected


def search(records: list[dict], query: str, *, extra_terms=(), years=(),
           groups=(), awards=(), include_low_confidence=True, limit=20) -> dict:
    terms = _query_terms(query, extra_terms)
    filters = {
        "years": sorted({_year(value) for value in years}),
        "groups": list(_counter_dict(
            (str(value).strip() for value in groups if str(value).strip()),
            GROUP_ORDER,
        ).keys()),
        "awards": sorted({str(value).strip() for value in awards if str(value).strip()}),
        "include_low_confidence": include_low_confidence,
    }
    selected = _filtered(records, years, groups, awards, include_low_confidence)
    if not selected:
        raise RadarError("filters leave no records to search")
    hits_by_title = {}
    term_stats = {}
    for term in terms:
        matches = [record for record in selected if term in _haystack(record)]
        term_stats[term] = {
            "count": len(matches),
            "by_year": _counter_dict(record["year"] for record in matches),
            "by_group": _counter_dict((record["group"] for record in matches), GROUP_ORDER),
            "by_award": _counter_dict(record["award"] for record in matches),
            "by_confidence": _counter_dict(record["confidence"] for record in matches),
            "best_award": _award_best(record["award"] for record in matches),
        }
        for record in matches:
            key = record["title"]
            if key not in hits_by_title:
                hits_by_title[key] = {"record": record, "terms": set()}
            hits_by_title[key]["terms"].add(term)

    hits = []
    for entry in hits_by_title.values():
        record = dict(entry["record"])
        record["matched_terms"] = sorted(entry["terms"])
        hits.append(record)
    hits.sort(key=lambda record: (
        -len(record["matched_terms"]),
        -AWARD_RANK.get(record["award"], 0),
        -record["year"],
        -CONFIDENCE_RANK.get(record["confidence"], 0),
        record["title"],
    ))
    best_award = _award_best(record["award"] for record in hits)
    result = {
        "mode": "snapshot-search",
        "query": query,
        "terms": terms,
        "filters": filters,
        "unmatched_terms": [term for term in terms if term_stats[term]["count"] == 0],
        "corpus_size": len(selected),
        "hit_count": len(hits),
        "share_of_filtered_corpus": round(len(hits) / len(selected), 6) if selected else 0,
        "best_award": best_award,
        "low_confidence_hits": sum(
            1 for record in hits if record.get("confidence") == "低"
            or record.get("review_required")
        ),
        "by_year": _counter_dict(record["year"] for record in hits),
        "by_group": _counter_dict((record["group"] for record in hits), GROUP_ORDER),
        "by_award": _counter_dict(record["award"] for record in hits),
        "by_confidence": _counter_dict(record["confidence"] for record in hits),
        "term_stats": term_stats,
        "hits": hits[:max(0, int(limit))],
        "hits_truncated": len(hits) > max(0, int(limit)),
    }
    return result


def _markdown_cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def render_search(result: dict, records: list[dict], snapshot_sha256: str) -> str:
    cov = coverage(records)
    lines = [
        f"# 获奖题目密度雷达 · {result['query']}",
        "",
        "> 这是题目级去重线索，不是创新性评分、可行性判断或获奖预测。",
        "",
        "## 本次匹配",
        "",
        f"- 查询词：{'、'.join(f'`{term}`' for term in result['terms'])}",
        "- 筛选范围："
        + (
            "、".join([
                "年份=" + (",".join(map(str, result["filters"]["years"])) or "全部"),
                "组别=" + ("、".join(result["filters"]["groups"]) or "全部"),
                "奖项=" + ("、".join(result["filters"]["awards"]) or "全部"),
                "低置信度=" + ("包含" if result["filters"]["include_low_confidence"] else "排除"),
            ])
        ),
        f"- 匹配记录：**{result['hit_count']}** / 筛选语料 {result['corpus_size']} 条"
        f"（{result['share_of_filtered_corpus']:.2%}）",
        f"- 最高奖项：{result['best_award'] or '未观察到'}",
        f"- 低置信度或待复核命中：{result['low_confidence_hits']} 条",
        "",
        "## 查询词分布",
        "",
        "| 查询词 | 命中 | 最高奖 | 年份 | 组别 |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for term in result["terms"]:
        stat = result["term_stats"][term]
        years = "、".join(f"{year}:{count}" for year, count in stat["by_year"].items()) or "—"
        groups = "、".join(f"{group}:{count}" for group, count in stat["by_group"].items()) or "—"
        lines.append(
            f"| `{_markdown_cell(term)}` | {stat['count']} | {stat['best_award'] or '—'} "
            f"| {years} | {groups} |"
        )
    lines.extend([
        "",
        "## 命中记录分布",
        "",
        f"- 年份：{_compact_counts(result['by_year'])}",
        f"- 组别：{_compact_counts(result['by_group'])}",
        f"- 奖项：{_compact_counts(result['by_award'])}",
        f"- 分类置信度：{_compact_counts(result['by_confidence'])}",
        "",
        "## 最接近题目",
        "",
    ])
    if result["hits"]:
        lines.extend([
            "| 年份 | 组别 | 奖项 | 学校 | 题目 | 命中词 | 置信度 |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ])
        for record in result["hits"]:
            lines.append(
                f"| {record['year']} | {_markdown_cell(record['group'])} "
                f"| {_markdown_cell(record['award'])} | {_markdown_cell(record['school'])} "
                f"| {_markdown_cell(record['title'])} "
                f"| {_markdown_cell('、'.join(record['matched_terms']))} "
                f"| {_markdown_cell(record['confidence'] or '—')} |"
            )
        if result["hits_truncated"]:
            lines.extend(["", f"> 仅显示前 {len(result['hits'])} 条；可增大 `--limit`。"])
    else:
        lines.append("在本次筛选范围内没有命中记录。**零命中不等于无人研究**，仍要换同义词、检查数据缺口并做人工检索。")
    lines.extend([
        "",
        "## 数据覆盖",
        "",
        "| 年份 | " + " | ".join(cov["groups"]) + " |",
        "| ---: | " + " | ".join("---:" for _ in cov["groups"]) + " |",
    ])
    for year in cov["years"]:
        row = cov["year_group_counts"][str(year)]
        lines.append(
            f"| {year} | " + " | ".join(str(row.get(group, "—")) for group in cov["groups"]) + " |"
        )
    lines.extend([
        "",
        f"- 共有 {cov['total']} 条记录；分类置信度：{_compact_counts(cov['confidence'])}。",
        "- 只有全部年份均有记录的组别才适合做跨年比较："
        + ("、".join(cov["comparable_across_all_years"]) or "无"),
        "- 空缺格表示当前快照没有记录，不能直接解释为该组别当年没有作品。",
        "",
        "## 解释边界",
        "",
        "- 数据范围是 2022—2026 年全国一、二等奖题目；不含省赛、校赛、三等奖或未获奖作品。",
        "- 分类和标签由标题自动生成；低置信度记录必须人工复核，不能把标签数量当作事实总量。",
        "- 同题或近题数量只反映公开获奖题目中的可见度；没有观察到，不等于赛道空白或更容易获奖。",
        "- 零命中不等于无人研究：换同义词、年份、组别并回到官方名单人工核对后，才能描述检索结果。",
        "- 已有同题一等奖只能证明评委接受过该方向，不能证明同一题目会再次获奖。",
        "- 搜索是关键词子串匹配；同义词、隐晦标题和分类错误都可能漏检。",
        "",
        "## 写回选题评分表",
        "",
        f"- `topic_density_count`：`{result['hit_count']}`",
        f"- `topic_density_best_award`：`{result['best_award'] or '未观察到'}`",
        "- `topic_density_years`：填写命中记录的年份分布",
        "- `topic_density_notes`：写同义词、最接近题目、低置信度记录和“未找到不等于空白”的限制",
        "",
        "## 来源",
        "",
        f"- 在线页面：{SOURCE_PAGE}",
        f"- 源码仓库：{SOURCE_REPOSITORY}",
        f"- 固定提交：`{SOURCE_COMMIT}`",
        f"- 本次快照 SHA-256：`{snapshot_sha256}`",
        f"- 生成日期：{datetime.now(timezone.utc).date().isoformat()}",
        "",
    ])
    return "\n".join(lines)


def _compact_counts(values: dict) -> str:
    return "、".join(f"{key}:{value}" for key, value in values.items()) or "—"


def default_data_path(project: Path) -> Path:
    return project.expanduser().resolve() / "raw_private" / "award-topics" / "data.js"


def resolve_data_path(data: str | None, project: str | None) -> Path:
    if data:
        return Path(data).expanduser()
    if project:
        path = default_data_path(Path(project))
        if path.is_file():
            return path
        raise RadarError(
            "No award-topic snapshot found. Fetch it explicitly with: "
            f'python -X utf8 "<SKILL_ROOT>/scripts/topic_radar.py" fetch --project "{project}"'
        )
    raise RadarError(
        "A snapshot is required for exact title search. Use --data <data.js> or --project <dir>; "
        "run the bundled baseline command for aggregate signals without a snapshot."
    )


def fetch_snapshot(output: Path, *, url=SOURCE_URL, force=False) -> dict:
    if output.exists() and not force:
        raise RadarError(f"Output already exists; use --force to replace: {output}")
    request = urllib.request.Request(url, headers={"User-Agent": "zhengda-research-copilot"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(MAX_SNAPSHOT_BYTES + 1)
    except OSError as exc:
        raise RadarError(f"download failed: {exc}") from exc
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise RadarError("snapshot exceeds the 5 MB safety limit")
    records = parse_snapshot(raw.decode("utf-8-sig"))
    digest = hashlib.sha256(raw).hexdigest()
    expected_verified = False
    if url == SOURCE_URL:
        if digest != SOURCE_SHA256:
            raise RadarError(
                "pinned snapshot hash mismatch: "
                f"expected {SOURCE_SHA256}, got {digest}"
            )
        expected_verified = True
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.tmp")
    try:
        temporary.write_bytes(raw)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "ok": True,
        "output": str(output),
        "records": len(records),
        "sha256": digest,
        "source_url": url,
        "pinned_hash_verified": expected_verified,
        "raw_snapshot_bundled": False,
    }


def load_baseline() -> dict:
    path = Path(__file__).resolve().parents[1] / "references" / "award-topics" / "baseline.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RadarError(f"bundled baseline is unavailable: {exc}") from exc
    if not isinstance(data, dict):
        raise RadarError("bundled baseline must be a JSON object")
    return data


def render_baseline(baseline: dict) -> str:
    source = baseline.get("source", {})
    cov = baseline.get("coverage", {})
    lines = [
        "# 正大杯获奖题目聚合基线",
        "",
        "> 离线聚合摘要；不含 2,920 条原始题目，不能替代针对具体选题的快照检索。",
        "",
        "## 覆盖",
        "",
        "| 年份 | " + " | ".join(cov.get("groups", [])) + " |",
        "| ---: | " + " | ".join("---:" for _ in cov.get("groups", [])) + " |",
    ]
    for year in cov.get("years", []):
        row = cov.get("year_group_counts", {}).get(str(year), {})
        lines.append(
            f"| {year} | " + " | ".join(str(row.get(group, "—")) for group in cov.get("groups", [])) + " |"
        )
    lines.extend([
        "",
        f"- 总计：{cov.get('total', '—')} 条",
        f"- 分类置信度：{_compact_counts(cov.get('confidence', {}))}",
        "- 可跨年比较的组别："
        + ("、".join(cov.get("comparable_across_all_years", [])) or "无"),
        "",
        "## 本科组主题累计",
        "",
        "| 主题 | 条数 |",
        "| --- | ---: |",
    ])
    for item in baseline.get("undergraduate_category_totals", []):
        lines.append(f"| {_markdown_cell(item['category'])} | {item['count']} |")
    lines.extend([
        "",
        "## 2026 本科组一等奖主题",
        "",
        "| 主题 | 条数 |",
        "| --- | ---: |",
    ])
    for item in baseline.get("undergraduate_first_prizes_2026", []):
        lines.append(f"| {_markdown_cell(item['category'])} | {item['count']} |")
    lines.extend([
        "",
        "## 关键词信号",
        "",
        "| 词 | 条数 | 年份 | 组别 |",
        "| --- | ---: | --- | --- |",
    ])
    for item in baseline.get("keyword_signals", []):
        lines.append(
            f"| `{_markdown_cell(item['term'])}` | {item['count']} "
            f"| {_compact_counts(item.get('by_year', {}))} "
            f"| {_compact_counts(item.get('by_group', {}))} |"
        )
    lines.extend([
        "",
        "## 边界",
        "",
        "- 关键词为标题、主题、标签和关键词字段的子串匹配，不是完整语义检索。",
        "- 这批数据只统计全国一、二等奖题目，未覆盖省赛、校赛、三等奖和未获奖作品。",
        "- 低置信度分类与缺失组别会改变计数；做具体选题判断时，先抓取快照并人工复核。",
        "",
        "## 来源",
        "",
        f"- 页面：{source.get('page', SOURCE_PAGE)}",
        f"- 仓库：{source.get('repository', SOURCE_REPOSITORY)}",
        f"- 固定提交：`{source.get('commit', SOURCE_COMMIT)}`",
        f"- 原始 data.js SHA-256：`{source.get('data_sha256', SOURCE_SHA256)}`",
        f"- 核验日期：{source.get('checked_on', '—')}",
        f"- 再分发边界：{source.get('redistribution_note', '—')}",
        "",
    ])
    return "\n".join(lines)


def render_coverage(cov: dict, digest: str) -> str:
    lines = [
        "# 获奖题目快照覆盖",
        "",
        f"- 总记录：{cov['total']} 条",
        f"- 快照 SHA-256：`{digest}`",
        f"- 分类置信度：{_compact_counts(cov.get('confidence', {}))}",
        "- 可跨年比较的组别："
        + ("、".join(cov.get("comparable_across_all_years", [])) or "无"),
        "",
        "| 年份 | " + " | ".join(cov.get("groups", [])) + " |",
        "| ---: | " + " | ".join("---:" for _ in cov.get("groups", [])) + " |",
    ]
    for year in cov.get("years", []):
        row = cov.get("year_group_counts", {}).get(str(year), {})
        lines.append(
            f"| {year} | " + " | ".join(str(row.get(group, "—")) for group in cov.get("groups", [])) + " |"
        )
    lines.extend([
        "",
        "空缺格表示当前快照没有记录，不能直接解释为该组别当年没有作品。",
        "",
        f"- 来源：{SOURCE_PAGE}",
        f"- 固定提交：`{SOURCE_COMMIT}`",
        "",
    ])
    return "\n".join(lines)


def _write(path: Path, text: str, force=False) -> Path:
    if path.exists() and not force:
        raise RadarError(f"Output already exists; use --force to replace: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    baseline_parser = sub.add_parser("baseline", help="show bundled aggregate signals")
    baseline_parser.add_argument("--json", action="store_true")

    coverage_parser = sub.add_parser("coverage", help="show snapshot coverage")
    coverage_parser.add_argument("--data")
    coverage_parser.add_argument("--project")
    coverage_parser.add_argument("--json", action="store_true")

    search_parser = sub.add_parser("search", help="search award titles and tags")
    search_parser.add_argument("--data")
    search_parser.add_argument("--project")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--term", action="append", default=[],
                               help="additional exact term; repeatable")
    search_parser.add_argument("--year", action="append", default=[])
    search_parser.add_argument("--group", action="append", default=[])
    search_parser.add_argument("--award", action="append", default=[])
    search_parser.add_argument("--exclude-low-confidence", action="store_true")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--json", action="store_true")
    search_parser.add_argument("--write", help="write Markdown or JSON report")
    search_parser.add_argument("--force", action="store_true")

    fetch_parser = sub.add_parser("fetch", help="download a pinned raw snapshot explicitly")
    fetch_parser.add_argument("--output")
    fetch_parser.add_argument("--project")
    fetch_parser.add_argument("--url", default=SOURCE_URL)
    fetch_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "baseline":
            data = load_baseline()
            print(json.dumps(data, ensure_ascii=False, indent=2) if args.json
                  else render_baseline(data))
            return 0
        if args.command == "fetch":
            if args.output:
                output = Path(args.output).expanduser()
            elif args.project:
                output = default_data_path(Path(args.project))
            else:
                raise RadarError("fetch requires --output or --project")
            print(json.dumps(fetch_snapshot(output, url=args.url, force=args.force),
                             ensure_ascii=False, indent=2))
            return 0
        if args.command == "coverage":
            path = resolve_data_path(args.data, args.project)
            records, digest = load_snapshot(path)
            result = {"ok": True, "data": str(path), "sha256": digest,
                      "coverage": coverage(records),
                      "source": {"page": SOURCE_PAGE, "repository": SOURCE_REPOSITORY,
                                 "commit": SOURCE_COMMIT}}
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
                  else render_coverage(result["coverage"], digest))
            return 0
        path = resolve_data_path(args.data, args.project)
        records, digest = load_snapshot(path)
        result = search(
            records,
            args.query,
            extra_terms=args.term,
            years=args.year,
            groups=args.group,
            awards=args.award,
            include_low_confidence=not args.exclude_low_confidence,
            limit=args.limit,
        )
        payload = {
            "ok": True,
            "data": str(path),
            "snapshot_sha256": digest,
            "source": {"page": SOURCE_PAGE, "repository": SOURCE_REPOSITORY,
                       "commit": SOURCE_COMMIT},
            "coverage": coverage(records),
            "result": result,
        }
        output_text = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_search(
            result, records, digest
        )
        written = None
        if args.write:
            written = _write(Path(args.write).expanduser(), output_text, force=args.force)
            payload["written_to"] = str(written)
            if args.json:
                output_text = json.dumps(payload, ensure_ascii=False, indent=2)
        print(output_text)
        if written and not args.json:
            print(f"\n已写入 `{written}`")
        return 0
    except (RadarError, OSError, ValueError, TypeError) as exc:
        return fail(exc)


if __name__ == "__main__":
    sys.exit(main())
