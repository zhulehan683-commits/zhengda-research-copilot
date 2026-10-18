#!/usr/bin/env python3
"""Local auditable task handoff; NOT an automatic Agent execution engine."""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from common import project_root, within, sha, read_json, atomic_json, local_lock, append_event, fail, now
from workflow import STAGES, get_state, state_file


def filename(root: Path, task_id: str) -> Path:
    try:
        clean = str(uuid.UUID(task_id))
        if clean != task_id: raise ValueError()
    except ValueError as exc:
        raise ValueError("Invalid task id (must be canonical UUID)") from exc
    return within(root, 'tasks/' + clean + '.json', must_exist=False)


def load(root: Path, task_id: str) -> dict:
    path = filename(root, task_id)
    if not path.is_file(): raise ValueError("Task not found: " + task_id)
    task = read_json(path)
    if not isinstance(task, dict):
        raise ValueError('Unsupported or damaged task schema')
    return task


def persist(root: Path, task: dict, event: dict):
    task["updated_at"] = now()
    task["revision"] += 1
    atomic_json(filename(root, task["task_id"]), task)
    append_event(state_file(root, 'task_events.jsonl'), {"task_id": task["task_id"], "task_revision": task["revision"], **event})


def ensure_project(root: Path):
    get_state(root)
    within(root, 'tasks/.path-check', must_exist=False)


def input_problems(root: Path, task: dict) -> list[str]:
    reasons = []
    for item in task.get("inputs", []):
        try:
            path = within(root, item["path"])
            if sha(path) != item["sha256"]:
                reasons.append("input SHA-256 differs: " + item["path"])
        except (ValueError, OSError, KeyError) as exc:
            reasons.append(f"invalid task input: {exc}")
    return reasons


def execution_problems(root: Path, task: dict) -> list[str]:
    log = (task.get("execution") or {}).get("log")
    if not log:
        return []
    try:
        path = within(root, log["path"])
        if sha(path) != log["sha256"]:
            return ["execution log SHA-256 differs: " + log["path"]]
    except (ValueError, OSError, KeyError) as exc:
        return [f"invalid execution log: {exc}"]
    return []


def create(root: Path, stage: str, title: str, assignee: str, acceptance_file: str, inputs=None):
    root = root.resolve()
    ensure_project(root)
    if not assignee.strip() or not title.strip(): raise ValueError("Title and assignee required")
    contract = within(root, acceptance_file)
    input_files = []
    seen = set()
    for value in inputs or []:
        path = within(root, value)
        relative = path.relative_to(root).as_posix()
        if relative in seen:
            raise ValueError("Duplicate task input: " + relative)
        seen.add(relative)
        input_files.append({"path": relative, "sha256": sha(path), "at": now()})
    with local_lock(state_file(root, '.tasks.lock')):
        tid = str(uuid.uuid4())
        task = {"task_id": tid, "stage": stage, "title": title.strip(), "assignee": assignee.strip(), "acceptance_file": contract.relative_to(root).as_posix(), "acceptance_sha256": sha(contract), "inputs": input_files, "status": "queued", "output": None, "execution": None, "review": None, "created_at": now(), "updated_at": now(), "revision": 0, "history": []}
        task["history"].append({"at": now(), "event": "created", "actor": "coordinator"})
        persist(root, task, {"event": "created", "actor": "coordinator", "stage": stage})
    return {"ok": True, "task_id": tid, "status": "queued", "input_count": len(input_files)}


def change(root: Path, task_id: str, action: str, actor: str, **kwargs):
    root = root.resolve()
    ensure_project(root)
    if not actor.strip(): raise ValueError("Actor required")
    with local_lock(state_file(root, '.tasks.lock')):
        t = load(root, task_id)
        problems = input_problems(root, t) + execution_problems(root, t)
        if problems:
            raise ValueError("Task evidence changed; create a new task or explicitly refresh dependencies: " + "; ".join(problems))
        if sha(within(root, t["acceptance_file"])) != t["acceptance_sha256"]:
            raise ValueError("Acceptance criteria changed; create a new task")
        current = t["status"]
        if action == "claim":
            if current not in {"queued", "rework"}: raise ValueError("Task not claimable: " + current)
            if actor != t["assignee"]: raise ValueError("Actor does not match assignee")
            t["status"] = "claimed"
        elif action == "submit":
            if current != "claimed": raise ValueError("Task not claimed")
            if actor != t["assignee"]: raise ValueError("Actor does not match assignee")
            output = within(root, kwargs["output"])
            t["output"] = {"path": output.relative_to(root).as_posix(), "sha256": sha(output), "at": now(), "note": kwargs.get("note", "")}
            execution = {"command": str(kwargs.get("command") or "").strip(), "exit_code": kwargs.get("exit_code")}
            log_value = kwargs.get("log")
            if log_value:
                log = within(root, log_value)
                execution["log"] = {"path": log.relative_to(root).as_posix(), "sha256": sha(log)}
            if execution["exit_code"] is not None and not execution["command"]:
                raise ValueError("--exit-code requires --command")
            t["execution"] = execution
            t["review"] = None
            t["status"] = "needs_review"
        elif action == "review":
            if current != "needs_review": raise ValueError("Task is not pending review")
            if actor == t["assignee"]: raise ValueError("Self-review is not an independent review")
            if sha(within(root, t["output"]["path"])) != t["output"]["sha256"]:
                raise ValueError("Submitted output changed since delivery")
            decision = kwargs["decision"]
            if not kwargs.get("note", "").strip(): raise ValueError("Review note required")
            t["review"] = {"actor": actor, "decision": decision, "note": kwargs["note"].strip(), "at": now(), "independence_not_technically_verified": True}
            t["status"] = "accepted" if decision == "pass" else "rework"
        else: raise ValueError("Invalid transition")
        t["history"].append({"at": now(), "event": action, "actor": actor, "from": current, "to": t["status"]})
        persist(root, t, {"event": action, "actor": actor, "from": current, "to": t["status"], "output_sha256": t["output"]["sha256"] if t["output"] else None})
    return {"ok": True, "task_id": task_id, "status": t["status"], "revision": t["revision"]}


def list_tasks(root: Path):
    ensure_project(root)
    tasks = []
    for f in sorted((root / "tasks").glob("*.json")):
        t = read_json(within(root, str(f)))
        if not isinstance(t, dict):
            raise ValueError('Unsupported or damaged task schema: ' + f.name)
        effective = t["status"]
        try:
            if input_problems(root, t):
                effective = "STALE_INPUT"
            elif sha(within(root, t["acceptance_file"])) != t["acceptance_sha256"]:
                effective = "STALE_ACCEPTANCE"
            elif t.get("output") and sha(within(root, t["output"]["path"])) != t["output"]["sha256"]:
                effective = "STALE_OUTPUT"
            elif execution_problems(root, t):
                effective = "STALE_EXECUTION"
        except (ValueError, OSError, KeyError):
            effective = "STALE_EVIDENCE"
        tasks.append({"task_id": t["task_id"], "stage": t["stage"], "title": t["title"], "assignee": t["assignee"], "status": t["status"], "effective_status": effective})
    return {"tasks": tasks}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="cmd", required=True)
    for cmd in ["create", "claim", "submit", "review", "list"]:
        sp = subs.add_parser(cmd); sp.add_argument("--project", required=True)
        if cmd == "create":
            sp.add_argument("--stage", choices=list(STAGES), required=True)
            sp.add_argument("--title", required=True)
            sp.add_argument("--assignee", required=True)
            sp.add_argument("--acceptance-file", required=True)
            sp.add_argument("--input", action="append", default=[], help="Project-local input file; repeat for each dependency")
        if cmd in ["claim", "submit", "review"]:
            sp.add_argument("--id", required=True); sp.add_argument("--actor", required=True)
        if cmd == "submit":
            sp.add_argument("--output", required=True); sp.add_argument("--note", default="")
            sp.add_argument("--command", default="", help="Actual command used to produce the output")
            sp.add_argument("--exit-code", type=int)
            sp.add_argument("--log", help="Optional project-local execution log")
        if cmd == "review": sp.add_argument("--decision", choices=["pass", "fail"], required=True); sp.add_argument("--note", required=True)
    a = p.parse_args()
    root = project_root(a.project)
    try:
        if a.cmd == "create": x = create(root, a.stage, a.title, a.assignee, a.acceptance_file, a.input)
        elif a.cmd == "list": x = list_tasks(root)
        else: x = change(root, a.id, a.cmd, a.actor, **({"output": a.output, "note": a.note, "command": a.command, "exit_code": a.exit_code, "log": a.log} if a.cmd == "submit" else {"decision": a.decision, "note": a.note} if a.cmd == "review" else {}))
        print(json.dumps(x, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        return fail(exc)


if __name__ == "__main__": sys.exit(main())
