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


def create(root: Path, stage: str, title: str, assignee: str, acceptance_file: str):
    root = root.resolve()
    ensure_project(root)
    if not assignee.strip() or not title.strip(): raise ValueError("Title and assignee required")
    contract = within(root, acceptance_file)
    with local_lock(state_file(root, '.tasks.lock')):
        tid = str(uuid.uuid4())
        task = {"task_id": tid, "stage": stage, "title": title.strip(), "assignee": assignee.strip(), "acceptance_file": str(contract.relative_to(root)), "acceptance_sha256": sha(contract), "status": "queued", "output": None, "review": None, "created_at": now(), "updated_at": now(), "revision": 0, "history": []}
        task["history"].append({"at": now(), "event": "created", "actor": "coordinator"})
        persist(root, task, {"event": "created", "actor": "coordinator", "stage": stage})
    return {"ok": True, "task_id": tid, "status": "queued"}


def change(root: Path, task_id: str, command: str, actor: str, **kwargs):
    root = root.resolve()
    ensure_project(root)
    if not actor.strip(): raise ValueError("Actor required")
    with local_lock(state_file(root, '.tasks.lock')):
        t = load(root, task_id)
        if sha(within(root, t["acceptance_file"])) != t["acceptance_sha256"]:
            raise ValueError("Acceptance criteria changed; create a new task")
        current = t["status"]
        if command == "claim":
            if current not in {"queued", "rework"}: raise ValueError("Task not claimable: " + current)
            if actor != t["assignee"]: raise ValueError("Actor does not match assignee")
            t["status"] = "claimed"
        elif command == "submit":
            if current != "claimed": raise ValueError("Task not claimed")
            if actor != t["assignee"]: raise ValueError("Actor does not match assignee")
            output = within(root, kwargs["output"])
            t["output"] = {"path": str(output.relative_to(root)), "sha256": sha(output), "at": now(), "note": kwargs.get("note", "")}
            t["review"] = None
            t["status"] = "needs_review"
        elif command == "review":
            if current != "needs_review": raise ValueError("Task is not pending review")
            if actor == t["assignee"]: raise ValueError("Self-review is not an independent review")
            if sha(within(root, t["output"]["path"])) != t["output"]["sha256"]:
                raise ValueError("Submitted output changed since delivery")
            decision = kwargs["decision"]
            if not kwargs.get("note", "").strip(): raise ValueError("Review note required")
            t["review"] = {"actor": actor, "decision": decision, "note": kwargs["note"].strip(), "at": now(), "independence_not_technically_verified": True}
            t["status"] = "accepted" if decision == "pass" else "rework"
        else: raise ValueError("Invalid transition")
        t["history"].append({"at": now(), "event": command, "actor": actor, "from": current, "to": t["status"]})
        persist(root, t, {"event": command, "actor": actor, "from": current, "to": t["status"], "output_sha256": t["output"]["sha256"] if t["output"] else None})
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
            if sha(within(root, t["acceptance_file"])) != t["acceptance_sha256"]:
                effective = "STALE_ACCEPTANCE"
            elif t.get("output") and sha(within(root, t["output"]["path"])) != t["output"]["sha256"]:
                effective = "STALE_OUTPUT"
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
        if cmd in ["claim", "submit", "review"]:
            sp.add_argument("--id", required=True); sp.add_argument("--actor", required=True)
        if cmd == "submit": sp.add_argument("--output", required=True); sp.add_argument("--note", default="")
        if cmd == "review": sp.add_argument("--decision", choices=["pass", "fail"], required=True); sp.add_argument("--note", required=True)
    a = p.parse_args()
    root = project_root(a.project)
    try:
        if a.cmd == "create": x = create(root, a.stage, a.title, a.assignee, a.acceptance_file)
        elif a.cmd == "list": x = list_tasks(root)
        else: x = change(root, a.id, a.cmd, a.actor, **({"output": a.output, "note": a.note} if a.cmd == "submit" else {"decision": a.decision, "note": a.note} if a.cmd == "review" else {}))
        print(json.dumps(x, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        return fail(exc)


if __name__ == "__main__": sys.exit(main())
