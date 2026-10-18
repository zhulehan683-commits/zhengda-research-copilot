#!/usr/bin/env python3
"""A fail-closed local project-state and evidence register for survey competitions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import project_root, within, sha, read_json, atomic_json, local_lock, append_event, fail, now

STAGES = {
    "registration": ["official_notice", "registration_confirmation"],
    "knowledge": ["exam_result"],
    "team": ["team_roster"],
    "topic": ["topic_brief", "feasibility_check"],
    "desk_research": ["source_register", "research_gap"],
    "design": ["survey_instrument", "sampling_plan", "research_ethics"],
    "pilot": ["pilot_log", "pilot_revision"],
    "fieldwork": ["collection_log", "raw_dataset", "provenance"],
    "cleaning": ["cleaning_script", "clean_dataset", "cleaning_report"],
    "analysis": ["analysis_code", "result_tables", "diagnostic_report", "claim_map_draft"],
    "report": ["report_doc", "claim_evidence_matrix", "ai_usage_log", "rules_checklist"],
    "defense": ["slides", "defense_notes", "mock_defense_log"],
    "submission": ["submission_package_manifest", "receipt"],
}
ORDER = tuple(STAGES)
SCHEMA = "1.0"


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


def evidence_problems(root: Path, data: dict, stage: str) -> list[str]:
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
        except (ValueError, OSError, KeyError) as exc:
            reasons.append(f"invalid evidence {key}: {exc}")
    return reasons


def check(root: Path, data: dict, stage: str) -> dict:
    reasons = []
    idx = ORDER.index(stage)
    for prior in ORDER[:idx]:
        if data["stages"][prior]["status"] != "passed":
            reasons.append("prior stage not passed: " + prior)
            continue
        if evidence_problems(root, data, prior):
            reasons.append("prior stage evidence stale: " + prior)
    reasons.extend(evidence_problems(root, data, stage))
    return {"stage": stage, "status": "PASS_MECHANICAL_ONLY" if not reasons else "BLOCKED", "reasons": reasons, "review_required": True}


def evidence_add(root: Path, stage: str, key: str, file: str, author: str) -> dict:
    if key not in STAGES[stage]:
        raise ValueError(f"Unknown evidence key {key}; allowed: {STAGES[stage]}")
    if not author.strip():
        raise ValueError("--author required and must be nonblank")
    f = within(root, file)
    relative = f.relative_to(root)
    if stage == "fieldwork" and key == "raw_dataset" and (not relative.parts or relative.parts[0] != "raw_private"):
        raise ValueError("raw_dataset must be stored under the project's raw_private/ directory; do not place identifiable survey data in tracked folders")
    new = {"path": str(relative), "sha256": sha(f), "author": author.strip(), "recorded_at": now()}
    with local_lock(state_file(root, '.project.lock')):
        data = get_state(root)
        before = data["stages"][stage]["evidence"].get(key)
        if before and before["path"] == new["path"] and before["sha256"] == new["sha256"] and before["author"] == new["author"]:
            return {"ok": True, "unchanged": True, "stage": stage, "key": key}
        data["stages"][stage]["evidence"][key] = new
        for s in ORDER[ORDER.index(stage):]:
            data["stages"][s]["status"] = "pending"
            data["stages"][s]["review"] = None
        persist(root, data, {"type": "evidence_changed", "stage": stage, "key": key, "path": new["path"], "sha256": new["sha256"], "downstream_invalidated": True})
    return {"ok": True, "stage": stage, "key": key, "sha256": new["sha256"], "downstream_invalidated": True}


def review_stage(root: Path, stage: str, reviewer: str, decision: str, note: str):
    if not reviewer.strip() or not note.strip():
        raise ValueError("Both reviewer identity and review note are required")
    with local_lock(state_file(root, '.project.lock')):
        data = get_state(root)
        gate = check(root, data, stage)
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


def status(root: Path) -> dict:
    d = get_state(root)
    stale_upstream = False
    stages = []
    for name in ORDER:
        item = d["stages"][name]
        own_stale = item["status"] == "passed" and bool(evidence_problems(root, d, name))
        effective = "STALE" if own_stale else ("STALE_UPSTREAM" if stale_upstream and item["status"] == "passed" else item["status"])
        stale_upstream = stale_upstream or own_stale
        stages.append({"stage": name, "status": item["status"], "effective_status": effective, "evidence_present": list(item["evidence"]), "required": STAGES[name]})
    return {"project": str(root), "competition": d["competition"], "season": d["season"], "revision": d["revision"], "rules_status": d["rules_status"], "stages": stages, "next_pending": next((s["stage"] for s in stages if s["effective_status"] != "passed"), None)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    initp = subs.add_parser("init"); initp.add_argument("--project", required=True); initp.add_argument("--competition", default="zhengda-17"); initp.add_argument("--season", default="2026-2027")
    sp = subs.add_parser("status"); sp.add_argument("--project", required=True)
    gp = subs.add_parser("gate"); gp.add_argument("--project", required=True); gp.add_argument("--stage", choices=ORDER, required=True)
    ep = subs.add_parser("evidence"); eps = ep.add_subparsers(dest="subcommand", required=True)
    ea = eps.add_parser("add"); ea.add_argument("--project", required=True); ea.add_argument("--stage", choices=ORDER, required=True); ea.add_argument("--key", required=True); ea.add_argument("--file", required=True); ea.add_argument("--author", default="team")
    rp = subs.add_parser("review"); rp.add_argument("--project", required=True); rp.add_argument("--stage", choices=ORDER, required=True); rp.add_argument("--reviewer", required=True); rp.add_argument("--decision", choices=["pass", "fail", "blocked"], required=True); rp.add_argument("--note", required=True)
    args = p.parse_args()
    try:
        root = project_root(args.project)
        if args.command == "init": result = init(root, args.competition, args.season)
        elif args.command == "status": result = status(root)
        elif args.command == "gate": result = check(root, get_state(root), args.stage)
        elif args.command == "evidence": result = evidence_add(root, args.stage, args.key, args.file, args.author)
        elif args.command == "review": result = review_stage(root, args.stage, args.reviewer, args.decision, args.note)
        else: raise ValueError("Unknown command")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") != "BLOCKED" else 3
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        return fail(exc)


if __name__ == "__main__": sys.exit(main())
