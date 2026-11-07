#!/usr/bin/env python3
"""A fail-closed local project-state and evidence register for survey competitions."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from common import (project_root, within, sha, read_json, atomic_json, local_lock,
                    append_event, fail, now, enable_utf8)

STAGES = {
    "registration": ["official_notice", "rules_verification", "registration_confirmation"],
    "knowledge": ["exam_result"],
    "team": ["team_roster"],
    "topic": ["topic_brief", "feasibility_check"],
    "desk_research": ["source_register", "research_gap"],
    "design": ["survey_instrument", "sampling_plan", "research_ethics", "design_manifest"],
    "pilot": ["pilot_log", "pilot_revision"],
    "fieldwork": ["collection_log", "raw_dataset", "provenance"],
    "cleaning": ["cleaning_script", "clean_dataset", "cleaning_report"],
    "analysis": ["analysis_code", "result_tables", "diagnostic_report", "claim_map_draft", "analysis_manifest"],
    "report": ["report_doc", "claim_evidence_matrix", "ai_usage_log", "rules_checklist"],
    "defense": ["slides", "defense_notes", "mock_defense_log"],
    "submission": ["submission_package_manifest", "receipt"],
}
ORDER = tuple(STAGES)
SCHEMA = "1.0"
DEPENDENCY_MANIFESTS = {"design_manifest", "analysis_manifest"}
RULES_MAX_AGE_DAYS = 60
GRILL_STAGES = {"topic", "design", "analysis", "report", "defense"}


class BlockedError(ValueError):
    """A fail-closed refusal that must surface as exit code 3, not 2."""


def rules_record_problems(path: Path, today: date | None = None) -> list[str]:
    """Validate the mandatory rules-verification record (P1-3).

    JSON is the preferred format. A Markdown fallback is accepted when it
    contains an explicit verified date and at least two notice URLs.
    """
    today = today or date.today()
    reasons = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [f"rules_verification cannot be read: {exc}"]
    payload = None
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except ValueError as exc:
            return [f"rules_verification is not valid JSON: {exc}"]
        if not isinstance(payload, dict):
            return ["rules_verification JSON must be an object"]
        verified = payload.get("verified_at")
        national = payload.get("national_notice_url")
        school = payload.get("school_notice_url")
        if not isinstance(national, str) or not national.startswith(("http://", "https://")):
            reasons.append("rules_verification needs national_notice_url (http/https)")
        if not isinstance(school, str) or not school.startswith(("http://", "https://")):
            reasons.append("rules_verification needs school_notice_url (http/https)")
        if isinstance(national, str) and isinstance(school, str) and national == school:
            reasons.append("national_notice_url and school_notice_url must be different")
    else:
        match = re.search(r"(?:核验日期|verified_at)\s*[:：]\s*(\d{4}-\d{2}-\d{2})", text)
        verified = match.group(1) if match else None
        urls = re.findall(r"https?://[^\s<>)\]]+", text)
        if len(set(urls)) < 2:
            reasons.append("rules_verification needs at least two notice URLs (national and school)")
    if not isinstance(verified, str):
        reasons.append("rules_verification needs verified_at (YYYY-MM-DD)")
        return reasons
    try:
        verified_date = datetime.strptime(verified, "%Y-%m-%d").date()
    except ValueError:
        reasons.append("rules_verification verified_at must be YYYY-MM-DD")
        return reasons
    if verified_date > today:
        reasons.append("rules_verification date is in the future")
    elif (today - verified_date).days > RULES_MAX_AGE_DAYS:
        reasons.append(
            f"rules_verification is stale ({verified_date.isoformat()}); re-check notices "
            f"within {RULES_MAX_AGE_DAYS} days"
        )
    return reasons


def state_file(root: Path, name: str) -> Path:
    return within(root, 'state/' + name, must_exist=False)


def get_state(root: Path) -> dict:
    path = state_file(root, 'project.json')
    if not path.is_file():
        raise FileNotFoundError("No project state. Run 'init' first: " + str(path))
    data = read_json(path)
    if (not isinstance(data, dict) or data.get("schema_version") != SCHEMA
            or not isinstance(data.get('stages'), dict) or set(data['stages']) != set(STAGES)):
        raise ValueError("Unsupported or damaged project-state schema")
    return data


def persist(root: Path, data: dict, event: dict) -> None:
    # Both files are in same locked local project; if event append fails, operator must inspect.
    data["updated_at"] = now()
    data["revision"] += 1
    atomic_json(state_file(root, 'project.json'), data)
    append_event(state_file(root, 'events.jsonl'), {"revision": data["revision"], **event})


def init(root: Path, competition: str, season: str):
    if state_file(root, 'project.json').exists():
        raise ValueError("Project already exists; refusal to overwrite existing state")
    if competition != "zhengda-17":
        raise ValueError("Only zhengda-17 configuration is bundled; custom competition must be added explicitly")
    if season != "2026-2027":
        raise ValueError("Bundled zhengda-17 rules are for 2026-2027 only; add another verified rule pack for a different season")
    root.mkdir(parents=True, exist_ok=True)
    for directory in ['sources', 'raw_private', 'data', 'analysis', 'report', 'defense', 'plans', 'tasks']:
        within(root, directory + '/.path-check', must_exist=False)
    with local_lock(state_file(root, '.project.lock')):
        if state_file(root, 'project.json').exists():
            raise ValueError("Project state already exists")
        for d in ["sources", "raw_private", "data", "analysis", "report", "defense", "plans", "tasks"]:
            (root / d).mkdir(parents=True, exist_ok=True)
        # `.gitignore` in workspace prevents accidental initial commits of PII.
        ignore = within(root, '.gitignore', must_exist=False)
        must_ignore = ["raw_private/", "private/", "state/", "tasks/", ".env", ".env.*", "*.key", "*.token", "*.pem", "*.p12"]
        old = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
        additions = [v for v in must_ignore if v not in old.splitlines()]
        if additions:
            with ignore.open("a", encoding="utf-8") as f:
                f.write(("\n" if old and not old.endswith("\n") else "") + "\n".join(additions) + "\n")
        state = {
            "schema_version": SCHEMA, "competition": competition, "season": season,
            "created_at": now(), "updated_at": now(), "revision": 0,
            "rules_status": "UNVERIFIED_FOR_USER_SCHOOL",
            "stages": {key: {"status": "pending", "evidence": {}, "review": None} for key in ORDER}
        }
        persist(root, state, {"type": "init", "competition": competition, "season": season})
    return {"ok": True, "project": str(root), "stage_count": len(ORDER), "note": "Not enrolled; attendance and rules must be verified by user"}


def manifest_problems(root: Path, key: str, manifest: Path) -> list[str]:
    reasons = []
    try:
        data = read_json(manifest)
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"invalid manifest {key}: {exc}"]
    if not isinstance(data, dict) or set(data) - {"description", "files", "command", "environment"}:
        return [f"invalid manifest {key}: expected description/files/command/environment fields"]
    files = data.get("files")
    if not isinstance(files, list) or not files:
        return [f"invalid manifest {key}: files must be a nonempty array"]
    seen = set()
    for index, item in enumerate(files):
        if not isinstance(item, dict) or set(item) - {"path", "sha256", "role"}:
            reasons.append(f"invalid manifest {key}: file entry {index} has unsupported fields")
            continue
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str) or not relative.strip():
            reasons.append(f"invalid manifest {key}: file entry {index} needs path")
            continue
        if relative in seen:
            reasons.append(f"duplicate manifest path: {relative}")
            continue
        seen.add(relative)
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            reasons.append(f"invalid SHA-256 in manifest {key}: {relative}")
            continue
        try:
            target = within(root, relative)
            if sha(target) != expected:
                reasons.append(f"manifest dependency SHA-256 differs: {relative}")
        except (ValueError, OSError) as exc:
            reasons.append(f"invalid manifest dependency {relative}: {exc}")
    command = data.get("command")
    if command is not None and not isinstance(command, str):
        reasons.append(f"invalid manifest {key}: command must be a string")
    environment = data.get("environment")
    if environment is not None and not isinstance(environment, str):
        reasons.append(f"invalid manifest {key}: environment must be a string")
    return reasons


def evidence_problems(root: Path, data: dict, stage: str,
                      today: date | None = None) -> list[str]:
    reasons = []
    items = data["stages"][stage]["evidence"]
    for key in STAGES[stage]:
        e = items.get(key)
        if not e:
            reasons.append("missing evidence: " + key)
            continue
        try:
            f = within(root, e["path"])
            if sha(f) != e["sha256"]:
                reasons.append("SHA-256 differs: " + key)
            elif key in DEPENDENCY_MANIFESTS:
                reasons.extend(manifest_problems(root, key, f))
            elif stage == "registration" and key == "rules_verification":
                reasons.extend(rules_record_problems(f, today))
        except (ValueError, OSError, KeyError) as exc:
            reasons.append(f"invalid evidence {key}: {exc}")
    return reasons


def check(root: Path, data: dict, stage: str, today: date | None = None) -> dict:
    reasons = []
    idx = ORDER.index(stage)
    for prior in ORDER[:idx]:
        if data["stages"][prior]["status"] != "passed":
            reasons.append("prior stage not passed: " + prior)
            continue
        if evidence_problems(root, data, prior, today):
            reasons.append("prior stage evidence stale: " + prior)
    reasons.extend(evidence_problems(root, data, stage, today))
    return {"stage": stage, "status": "PASS_MECHANICAL_ONLY" if not reasons else "BLOCKED", "reasons": reasons, "review_required": True}


def evidence_add(root: Path, stage: str, key: str, file: str, author: str,
                 force: bool = False) -> dict:
    root = root.resolve()
    if key not in STAGES[stage]:
        raise ValueError(f"Unknown evidence key {key}; allowed: {STAGES[stage]}")
    if not author.strip():
        raise ValueError("--author required and must be nonblank")
    f = within(root, file)
    relative = f.relative_to(root).as_posix()
    if stage == "fieldwork" and key == "raw_dataset" and (
            not relative.split("/") or relative.split("/")[0] != "raw_private"):
        raise ValueError("raw_dataset must be stored under the project's raw_private/ directory; do not place identifiable survey data in tracked folders")
    new = {"path": relative, "sha256": sha(f), "author": author.strip(), "recorded_at": now()}
    with local_lock(state_file(root, '.project.lock')):
        data = get_state(root)
        before = data["stages"][stage]["evidence"].get(key)
        if before and before["path"] == new["path"] and before["sha256"] == new["sha256"] and before["author"] == new["author"]:
            return {"ok": True, "unchanged": True, "stage": stage, "key": key}
        replaced = None
        if before and not force:
            raise BlockedError(
                "Evidence key already bound: "
                f"{stage}/{key} -> {before['path']} "
                f"(sha256={before['sha256'][:12]}..., author={before.get('author')}, "
                f"recorded_at={before.get('recorded_at')}). "
                "Refusing silent overwrite; use --force and inspect the returned replaced block."
            )
        if before:
            replaced = {name: before.get(name) for name in
                        ("path", "sha256", "author", "recorded_at")}
        data["stages"][stage]["evidence"][key] = new
        for s in ORDER[ORDER.index(stage):]:
            data["stages"][s]["status"] = "pending"
            data["stages"][s]["review"] = None
        event = {"type": "evidence_changed", "stage": stage, "key": key,
                 "path": new["path"], "sha256": new["sha256"],
                 "downstream_invalidated": True}
        if replaced:
            event["replaced"] = replaced
        persist(root, data, event)
    result = {"ok": True, "stage": stage, "key": key, "sha256": new["sha256"],
              "downstream_invalidated": True}
    if replaced:
        result["replaced"] = replaced
    return result


def evidence_list(root: Path, stage: str | None = None) -> dict:
    data = get_state(root)
    stages = [stage] if stage else list(ORDER)
    items = []
    missing = []
    for name in stages:
        bound = data["stages"][name]["evidence"]
        for key in STAGES[name]:
            entry = bound.get(key)
            if not entry:
                missing.append({"stage": name, "key": key})
                continue
            item = {"stage": name, "key": key, **entry,
                    "exists": False, "sha256_matches": False}
            try:
                target = within(root, entry["path"])
                item["exists"] = True
                item["sha256_matches"] = sha(target) == entry["sha256"]
            except (ValueError, OSError, KeyError):
                pass
            if name == "registration" and key == "rules_verification" and item["exists"]:
                item["rules_reasons"] = rules_record_problems(
                    within(root, entry["path"]))
            items.append(item)
    return {"ok": True, "project": str(root), "stage": stage,
            "items": items, "missing": missing}


def template_pull(root: Path, name: str, dest: str | None = None,
                  force: bool = False) -> dict:
    templates = Path(__file__).resolve().parents[1] / "templates"
    source = templates / name
    if not source.is_file() or source.parent != templates:
        raise ValueError("Unknown template: " + name)
    target = within(root, dest or ("plans/" + name), must_exist=False)
    if target.exists() and not force:
        raise BlockedError(
            f"Destination already exists: {target.relative_to(root.resolve())}; "
            "choose another --dest or pass --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    return {"ok": True, "template": name, "path": target.relative_to(root.resolve()).as_posix(),
            "sha256": sha(target), "overwritten": force}


def review_stage(root: Path, stage: str, reviewer: str, decision: str, note: str,
                 today: date | None = None):
    if not reviewer.strip() or not note.strip():
        raise ValueError("Both reviewer identity and review note are required")
    with local_lock(state_file(root, '.project.lock')):
        data = get_state(root)
        gate = check(root, data, stage, today)
        if decision == "pass" and gate["status"] != "PASS_MECHANICAL_ONLY":
            raise ValueError("Cannot pass stage: " + "; ".join(gate["reasons"]))
        authors = {v.get("author") for v in data["stages"][stage]["evidence"].values()}
        if decision == "pass" and reviewer.strip() in authors:
            raise ValueError("Reviewer cannot be a named author of current-stage evidence")
        data["stages"][stage]["review"] = {"reviewer": reviewer.strip(), "decision": decision, "note": note.strip(), "at": now(), "independence_not_technically_verified": True}
        data["stages"][stage]["status"] = "passed" if decision == "pass" else "blocked"
        if decision != "pass":
            for s in ORDER[ORDER.index(stage) + 1:]:
                data["stages"][s]["status"] = "pending"
                data["stages"][s]["review"] = None
        persist(root, data, {"type": "review", "stage": stage, "decision": decision, "reviewer": reviewer.strip(), "mechanical_gate": gate["status"]})
    return {"ok": True, "stage": stage, "status": "passed" if decision == "pass" else "blocked", "human_review_authenticity": "NOT_VERIFIED_BY_SCRIPT"}


def status(root: Path, today: date | None = None) -> dict:
    d = get_state(root)
    stale_upstream = False
    stages = []
    for name in ORDER:
        item = d["stages"][name]
        own_stale = item["status"] == "passed" and bool(
            evidence_problems(root, d, name, today))
        effective = "STALE" if own_stale else ("STALE_UPSTREAM" if stale_upstream and item["status"] == "passed" else item["status"])
        stale_upstream = stale_upstream or own_stale
        stages.append({"stage": name, "status": item["status"], "effective_status": effective, "evidence_present": list(item["evidence"]), "required": STAGES[name]})
    next_pending = next((s["stage"] for s in stages if s["effective_status"] != "passed"), None)
    suggestions = []
    if next_pending in GRILL_STAGES:
        suggestions.append(
            f'python -X utf8 "<SKILL_ROOT>/scripts/advisor.py" grill '
            f'--stage {next_pending} --project "<PROJECT_ROOT>" --quick')
    suggestions.append(
        'python -X utf8 "<SKILL_ROOT>/scripts/advisor.py" find '
        '--need "<具体能力缺口>"  # only when a tool/skill is missing')
    return {"project": str(root), "competition": d["competition"], "season": d["season"],
            "revision": d["revision"], "rules_status": d["rules_status"],
            "stages": stages, "next_pending": next_pending,
            "suggested_actions": suggestions}


def main() -> int:
    enable_utf8()
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    initp = subs.add_parser("init"); initp.add_argument("--project", required=True); initp.add_argument("--competition", default="zhengda-17"); initp.add_argument("--season", default="2026-2027")
    sp = subs.add_parser("status"); sp.add_argument("--project", required=True)
    gp = subs.add_parser("gate"); gp.add_argument("--project", required=True); gp.add_argument("--stage", choices=ORDER, required=True)
    ep = subs.add_parser("evidence"); eps = ep.add_subparsers(dest="subcommand", required=True)
    ea = eps.add_parser("add"); ea.add_argument("--project", required=True); ea.add_argument("--stage", choices=ORDER, required=True); ea.add_argument("--key", required=True); ea.add_argument("--file", required=True); ea.add_argument("--author", default="team"); ea.add_argument("--force", action="store_true")
    el = eps.add_parser("list"); el.add_argument("--project", required=True); el.add_argument("--stage", choices=ORDER)
    tp = subs.add_parser("template"); tp.add_argument("--project", required=True); tp.add_argument("--name", required=True); tp.add_argument("--dest"); tp.add_argument("--force", action="store_true")
    rp = subs.add_parser("review"); rp.add_argument("--project", required=True); rp.add_argument("--stage", choices=ORDER, required=True); rp.add_argument("--reviewer", required=True); rp.add_argument("--decision", choices=["pass", "fail", "blocked"], required=True); rp.add_argument("--note", required=True)
    args = p.parse_args()
    try:
        root = project_root(args.project)
        if args.command == "init": result = init(root, args.competition, args.season)
        elif args.command == "status": result = status(root)
        elif args.command == "gate": result = check(root, get_state(root), args.stage)
        elif args.command == "evidence":
            if args.subcommand == "add":
                result = evidence_add(root, args.stage, args.key, args.file,
                                      args.author, force=args.force)
            else:
                result = evidence_list(root, args.stage)
        elif args.command == "template":
            result = template_pull(root, args.name, args.dest, args.force)
        elif args.command == "review": result = review_stage(root, args.stage, args.reviewer, args.decision, args.note)
        else: raise ValueError("Unknown command")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        outcome = str(result.get("status", "")).lower()
        return 3 if outcome in {"blocked", "fail", "rework"} else 0
    except BlockedError as exc:
        print(json.dumps({"ok": False, "status": "BLOCKED", "error": str(exc)},
                         ensure_ascii=False))
        return 3
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        return fail(exc)


if __name__ == "__main__": sys.exit(main())
