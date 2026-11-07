#!/usr/bin/env python3
"""Low-friction entry points for find-skills and grill-me.

`find` scans locally installed skills and prints reproducible ecosystem search
commands. `grill` turns the current project stage into a dependency-ordered
decision frontier with recommended answers. Neither command changes project
state or pretends that a remote search happened.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import enable_utf8, fail


GRILL_BANK = {
    "topic": [
        ("研究对象", "这项研究具体观察谁在什么情境下的什么行为或判断？谁能回答这个问题？",
         "把对象收窄到一个可接触群体和一个可观测行为，暂不扩展到多个行业。"),
        ("研究问题", "哪一个可被数据推翻的陈述是本次调查的核心？什么结果会让你放弃这个方向？",
         "先写一个带方向的主假设和一个明确的淘汰条件，再比较备选题。"),
        ("备选与撞题", "另外两个备选方向是什么？公开获奖名单中同题出现过几次、最高奖项是什么？",
         "至少比较三个方向，并把同题数量、最高奖项、年份分布写进选题评分表。"),
        ("证据缺口", "支撑痛点的是原始数据、访谈还是二手报道？哪一条最关键但尚未核实？",
         "把最关键的一条标为待核验，先查官方统计或一手材料，不用宣传稿替代。"),
        ("可执行性", "两周内能接触到多少符合条件的受访者？谁负责渠道授权？",
         "按已获准渠道估算可达人数，低于分析所需样本就缩小总体或改题。"),
        ("行动价值", "如果结论成立，哪个主体会据此改变什么动作？",
         "写出证据 → 责任主体 → 具体动作 → 前提 → 衡量指标；写不出就换题。"),
    ],
    "design": [
        ("总体与抽样框", "目标总体、抽样框和实际可联系名单分别是什么？名单遗漏了谁？",
         "先固定总体和抽样框，再谈样本量；便利样本只能推断到本渠道。"),
        ("招募渠道", "哪些渠道已获准使用？每个渠道预计回收多少、是否存在自选择？",
         "列出渠道、授权人、预计份数和偏差方向，不把社群转发当作随机抽样。"),
        ("样本量", "主分析需要多少有效样本？依据是什么效应量、把握度和脱落率？",
         "用 power_calc.py 记录参数与来源，再按预计有效率上浮。"),
        ("测量", "每个构念用哪些题项？时间窗、反向题、缺失码和跳题逻辑是什么？",
         "先做变量字典和逐题审核，再冻结问卷；反向计分在清洗阶段显式执行。"),
        ("分析合同", "主估计量、排除规则、缺失处理和失败降级分别是什么？",
         "在收数前填写 analysis-contract.csv，避免看到显著性后改规则。"),
        ("伦理与规则", "知情同意、最小必要数据和当届 AI/数据规则如何落实？",
         "保存同意文本、脱敏规则和规则核验日期；原始数据留在 raw_private/。"),
    ],
    "analysis": [
        ("主问题与估计量", "每个研究问题对应的主表/主图、估计量和单位是什么？",
         "一个主问题只指定一个主估计量，其余放稳健性或探索性分析。"),
        ("方法前提", "当前方法的关键前提哪些已检查、哪些只能标注为假设？",
         "先跑诊断再解释系数；前提不满足就降级方法，不硬上 SEM/黑箱。"),
        ("缺失与排除", "缺失机制、排除标准和样本量变化如何记录？",
         "预先写规则并报告每步剩余 n；不得为显著性删样本。"),
        ("多重比较", "本轮检验了几个假设？是否需要校正或预先指定主结果？",
         "明确主结果与探索性结果；多重检验时报告校正方法或降低结论强度。"),
        ("稳健性", "换一种合理编码、子样本或模型设定，结论会反转吗？",
         "至少做一项可解释的敏感性分析，并报告方向和幅度。"),
        ("复现", "独立 reviewer 在干净环境运行哪条命令能复现主结果？",
         "绑定数据哈希、代码、命令、退出码和输出；跑不通就是阻塞。"),
    ],
    "report": [
        ("主张与证据", "每条核心结论对应哪张表/图、哪个样本量和哪条限制？",
         "先填 claim-evidence-matrix，再写正文；没有证据的句子删除或降级。"),
        ("因果边界", "哪些句子是描述、哪些是相关、哪些声称因果？",
         "因果句必须有设计或识别策略；否则改成关联并写明替代解释。"),
        ("规则符合", "当届页数、匿名、引用、AI 披露和附件要求核验到哪一天？",
         "把核验日期和全国/本校公告 URL 写进 rules_verification。"),
        ("行动建议", "建议是否写明责任主体、动作、前提、时间和指标？",
         "把“加强宣传”改成可执行动作和可衡量指标。"),
    ],
    "defense": [
        ("最弱证据", "评审最可能攻击哪条证据？你的替代解释是什么？",
         "主动列出 weakest link、替代解释和补充证据计划。"),
        ("样本偏差", "样本如何产生？哪些群体被系统性遗漏？",
         "用一页说明抽样框、渠道、回收结构和推断边界。"),
        ("数字一致性", "PPT、报告、代码中的主数字是否逐项一致？",
         "建立数字对照表，答辩前由非作者逐项核对。"),
        ("规则与角色", "答辩人是否清楚当届规则和本人承担的工作？",
         "每人准备一段本人贡献和证据链说明，不背稿冒充全员经历。"),
    ],
}

NEED_ALIASES = {
    "问卷": ["survey", "questionnaire"],
    "统计": ["statistical analysis", "statistics"],
    "回归": ["regression", "statistical analysis"],
    "文献": ["citation", "literature review"],
    "引用": ["citation", "reference verification"],
    "查重": ["plagiarism", "similarity check"],
    "图表": ["visualization", "chart"],
    "可视化": ["visualization", "chart"],
    "报告": ["report", "document"],
    "论文": ["academic writing", "paper"],
    "word": ["docx", "document"],
    "docx": ["docx", "document"],
    "ppt": ["pptx", "presentation"],
    "幻灯": ["pptx", "presentation"],
    "答辩": ["presentation", "defense"],
    "爬虫": ["scraping", "browser automation"],
    "文本": ["text analysis", "nlp"],
    "数据清洗": ["data cleaning", "spreadsheet"],
    "excel": ["xlsx", "spreadsheet"],
}

TERM_ALIASES = {
    "citation": ["citation", "citations", "reference", "literature review"],
    "citations": ["citation", "citations", "reference", "literature review"],
    "reference": ["reference", "citation"],
    "statistic": ["statistic", "statistics", "statistical"],
    "statistics": ["statistic", "statistics", "statistical"],
    "statistical": ["statistic", "statistics", "statistical"],
    "survey": ["survey", "questionnaire"],
    "questionnaire": ["survey", "questionnaire"],
    "presentation": ["presentation", "slides", "pptx"],
    "document": ["document", "docx", "word"],
    "visualization": ["visualization", "chart", "figure"],
}

STOPWORDS = {
    "a", "an", "the", "for", "to", "of", "and", "or", "find", "skill", "skills",
    "can", "you", "help", "with", "i", "need", "want", "is", "there", "how", "do",
    "my", "our", "we", "please", "using", "use",
}


def _default_skill_roots(repo_root: Path):
    roots = [repo_root / ".agents" / "skills",
             Path.home() / ".agents" / "skills",
             Path.home() / ".codex" / "skills"]
    extra = os.environ.get("CODEX_SKILL_ROOTS", "")
    roots.extend(Path(part).expanduser() for part in extra.split(os.pathsep) if part.strip())
    unique = []
    for root in roots:
        resolved = root.expanduser()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _frontmatter(path: Path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    block = match.group(1) if match else ""
    data = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() in {"name", "description"}:
            data[key.strip()] = value.strip().strip('"\'')
    return data or None


def _terms(need: str):
    lowered = need.lower()
    primary = []
    aliases = []
    for token in re.split(r"[\s,，、/;；]+", lowered):
        if not token or token in STOPWORDS:
            continue
        if token not in primary:
            primary.append(token)
        aliases.extend(TERM_ALIASES.get(token, []))
    for chinese, mapped in NEED_ALIASES.items():
        if chinese in lowered:
            for alias in mapped:
                if alias.lower() not in primary:
                    aliases.append(alias.lower())
    aliases = [alias for alias in dict.fromkeys(aliases) if alias not in primary]
    return primary or [lowered], aliases


def find_skills(need: str, roots=None):
    repo_root = Path(__file__).resolve().parents[1]
    roots = roots or _default_skill_roots(repo_root)
    primary, aliases = _terms(need)
    lowered_need = need.lower()
    allow_meta = any(token in lowered_need for token in ("skill", "find", "grill", "拷问", "技能"))
    meta_names = {"find-skills", "grill-me", "grilling"}
    matches = []
    scanned = []
    for root in roots:
        if not root.is_dir():
            continue
        scanned.append(str(root))
        for skill_file in root.rglob("SKILL.md"):
            meta = _frontmatter(skill_file)
            if not meta:
                continue
            name = meta.get("name") or skill_file.parent.name
            if name in meta_names and not allow_meta:
                continue
            haystack = (meta.get("name", "") + " " + meta.get("description", "")).lower()
            score = 3 * sum(1 for term in primary if term and term in haystack)
            score += sum(1 for term in aliases if term and term in haystack)
            if score >= 2:
                matches.append({"name": name,
                                "description": meta.get("description", ""),
                                "path": str(skill_file), "score": score})
    matches.sort(key=lambda item: (-item["score"], item["name"]))
    deduped = []
    seen_names = set()
    for item in matches:
        if item["name"] not in seen_names:
            seen_names.add(item["name"])
            deduped.append(item)
    matches = deduped
    mapped = list(dict.fromkeys(
        alias for chinese, mapped_aliases in NEED_ALIASES.items()
        if chinese in lowered_need for alias in mapped_aliases))
    search_terms = " ".join(mapped) if mapped else " ".join((primary + aliases)[:4])
    return {"need": need, "terms": primary + aliases, "scanned_roots": scanned,
            "local_matches": matches[:8],
            "mode": "local-index-only",
            "remote_search_performed": False,
            "search_commands": [f'npx skills find "{search_terms}"'],
            "browse_url": "https://skills.sh/",
            "caveat": ("Local matches are discovery hints. Verify SKILL.md, dependencies, "
                       "license and pinned commit before installing; nothing was installed.")}


def _project_gaps(project: Path, stage: str):
    try:
        state = json.loads((project / "state" / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    stages = state.get("stages", {})
    if stage not in stages:
        return None
    return {"status": stages[stage].get("status"),
            "bound": sorted(stages[stage].get("evidence", {})),
            "review": stages[stage].get("review")}


def grill(stage: str, project=None, quick=False):
    questions = GRILL_BANK[stage]
    if quick:
        questions = questions[:3]
    lines = [f"# Grill Me · {stage}", "",
             "规则：每轮只问前置条件已定的问题；每题先给建议答案；等答复后再展开依赖问题。", ""]
    for index, (title, question, recommendation) in enumerate(questions, 1):
        lines.extend([f"## Q{index} · {title}", "", question, "",
                      f"**建议**：{recommendation}", ""])
    if project:
        gaps = _project_gaps(project, stage)
        if gaps:
            lines.extend(["## 当前项目状态", "",
                          f"- 阶段状态：`{gaps['status']}`",
                          f"- 已绑定证据：{', '.join(gaps['bound']) or '无'}",
                          f"- 独立复核：{gaps['review'] or '未记录'}", ""])
        else:
            lines.extend(["## 当前项目状态", "", "- 未找到可读的项目状态；以下问题仅基于阶段模板。", ""])
    lines.extend(["## 结束条件", "",
                  "问题问完后，用一段新人能读懂的话解释研究如何完成，再列已决定事项、"
                  "待核验事实和剩余风险。达成共识前不修改项目状态。", ""])
    return "\n".join(lines)


def _write_unique(project: Path, stage: str, text: str, suffix=".md"):
    plans = project / "plans"
    plans.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = plans / f"grill-{stage}-{stamp}{suffix}"
    counter = 1
    while target.exists():
        target = plans / f"grill-{stage}-{stamp}-{counter}{suffix}"
        counter += 1
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("find")
    find.add_argument("--need", required=True)
    find.add_argument("--root", action="append", default=[])
    find.add_argument("--json", action="store_true")
    ask = sub.add_parser("grill")
    ask.add_argument("--stage", choices=sorted(GRILL_BANK), required=True)
    ask.add_argument("--project")
    ask.add_argument("--quick", action="store_true")
    ask.add_argument("--json", action="store_true")
    ask.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "find":
            roots = [Path(value).expanduser() for value in args.root] if args.root else None
            result = find_skills(args.need, roots)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"# Find Skills · {args.need}\n")
                print("已扫描：" + (", ".join(result["scanned_roots"]) or "无可用技能目录"))
                if result["local_matches"]:
                    print("\n## 本地候选")
                    for item in result["local_matches"]:
                        print(f"- `{item['name']}` — {item['description']}\n  `{item['path']}`")
                else:
                    print("\n本地没有匹配项；这不代表生态里不存在。")
                print("\n## 远端检索（尚未执行）")
                for command in result["search_commands"]:
                    print(f"- `{command}`")
                print(f"- 浏览：{result['browse_url']}")
                print(f"\n> {result['caveat']}")
            return 0
        text = grill(args.stage, Path(args.project).expanduser() if args.project else None,
                     args.quick)
        if args.json:
            payload = {"stage": args.stage, "quick": args.quick, "markdown": text,
                       "project": args.project}
            if args.write:
                if not args.project:
                    raise ValueError("--write requires --project")
                target = _write_unique(Path(args.project).expanduser(), args.stage,
                                       json.dumps(payload, ensure_ascii=False, indent=2),
                                       ".json")
                payload["written_to"] = str(target)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(text)
            if args.write:
                if not args.project:
                    raise ValueError("--write requires --project")
                target = _write_unique(Path(args.project).expanduser(), args.stage, text)
                print(f"\n已写入 `{target}`")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return fail(exc)


if __name__ == "__main__":
    sys.exit(main())
