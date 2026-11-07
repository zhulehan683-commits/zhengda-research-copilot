import sys
import os
import json
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import task_queue
import workflow


class WorkflowTests(unittest.TestCase):
    def test_nonobject_project_and_task_states_rejected(self):
        import json
        state_file = self.root / 'state/project.json'
        before = state_file.read_bytes()
        state_file.write_text('[]')
        with self.assertRaises(ValueError):
            workflow.get_state(self.root)
        state_file.write_bytes(before)
        task_file = self.root / 'tasks/broken.json'
        task_file.write_text('[]')
        with self.assertRaises(ValueError):
            task_queue.list_tasks(self.root)

    @unittest.skipUnless(os.name == 'nt', 'Windows managed-path regression')
    def test_managed_state_and_tasks_junctions_rejected(self):
        for name in ['state', 'tasks']:
            root = self.root / ('fixture-' + name)
            outside = self.root / ('outside-' + name)
            root.mkdir()
            outside.mkdir()
            link = root / name
            env = {**os.environ, 'SURVEY_TEST_LINK': str(link), 'SURVEY_TEST_TARGET': str(outside)}
            subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                            "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                            '-Path $env:SURVEY_TEST_LINK -Target $env:SURVEY_TEST_TARGET | Out-Null'],
                           env=env, check=True, capture_output=True)
            try:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    workflow.init(root, 'zhengda-17', '2026-2027')
                self.assertEqual(list(outside.iterdir()), [])
            finally:
                link.rmdir()

    def test_path_check_without_windows_stat_constants(self):
        import common
        file = self.write('sources/portable.txt')
        with mock.patch.object(common.stat, 'FILE_ATTRIBUTE_REPARSE_POINT', create=True):
            delattr(common.stat, 'FILE_ATTRIBUTE_REPARSE_POINT')
            self.assertEqual(workflow.within(self.root, 'sources/portable.txt'), file)

    @unittest.skipUnless(os.name == 'nt', 'Windows junction regression')
    def test_internal_junction_evidence_is_rejected(self):
        directory = self.root / 'sources' / 'real'
        directory.mkdir()
        (directory / 'notice.txt').write_text('test fixture')
        link = self.root / 'sources' / 'junction'
        env = {**os.environ, 'SURVEY_TEST_LINK': str(link), 'SURVEY_TEST_TARGET': str(directory)}
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                        "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                        '-Path $env:SURVEY_TEST_LINK -Target $env:SURVEY_TEST_TARGET | Out-Null'],
                       env=env, check=True, capture_output=True)
        self.addCleanup(lambda: link.rmdir() if link.exists() else None)
        with self.assertRaisesRegex(ValueError, 'link|reparse'):
            workflow.within(self.root, 'sources/junction/notice.txt')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "competition"
        workflow.init(self.root, "zhengda-17", "2026-2027")

    def write(self, rel: str, text: str = "genuine-local-placeholder-for-structural-test"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def bind(self, stage: str, key: str, path: Path, author="team", force=False):
        return workflow.evidence_add(self.root, stage, key, str(path), author, force=force)

    def bind_registration(self):
        notice = self.write("sources/notice.txt")
        rules = self.write("sources/rules.json", json.dumps({
            "verified_at": date.today().isoformat(),
            "national_notice_url": "https://example.org/national",
            "school_notice_url": "https://example.org/school",
        }))
        receipt = self.write("sources/receipt.txt")
        self.bind("registration", "official_notice", notice)
        self.bind("registration", "rules_verification", rules)
        self.bind("registration", "registration_confirmation", receipt)
        return notice, receipt

    def pass_stage(self, stage: str):
        return workflow.review_stage(self.root, stage, "IndependentReviewer", "pass", "仅记录测试中的人工复核操作")

    def test_missing_files_do_not_pass(self):
        result = workflow.check(self.root, workflow.get_state(self.root), "registration")
        self.assertEqual(result["status"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "Cannot pass stage"):
            workflow.review_stage(self.root, "registration", "QA", "pass", "not enough")

    def test_status_suggests_grill_and_find_without_changing_state(self):
        status = workflow.status(self.root)
        self.assertEqual(status["next_pending"], "registration")
        commands = " ".join(status["suggested_actions"])
        self.assertIn("advisor.py", commands)
        self.assertIn("find", commands)
        self.assertNotIn("--stage registration", commands)

    def test_gate_and_hash_invalidation(self):
        notice, receipt = self.bind_registration()
        result = workflow.check(self.root, workflow.get_state(self.root), "registration")
        self.assertEqual(result["status"], "PASS_MECHANICAL_ONLY")
        self.pass_stage("registration")
        receipt.write_text("NEW-EVIDENCE", encoding="utf-8")
        result = workflow.check(self.root, workflow.get_state(self.root), "registration")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("SHA" in x for x in result["reasons"]))
        status = workflow.status(self.root)
        self.assertEqual(status["stages"][0]["effective_status"], "STALE")
        self.bind("registration", "registration_confirmation", receipt, force=True)
        status = workflow.status(self.root)
        self.assertEqual(status["stages"][0]["status"], "pending")

    def test_predecessor_stale_blocks_next_stage(self):
        _, receipt = self.bind_registration()
        self.pass_stage("registration")
        exam = self.write("sources/exam.txt")
        self.bind("knowledge", "exam_result", exam)
        receipt.write_text("changed after approval", encoding="utf-8")
        result = workflow.check(self.root, workflow.get_state(self.root), "knowledge")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("prior" in x.lower() for x in result["reasons"]))

    def test_previous_stage_change_revokes_downstream(self):
        notice, _ = self.bind_registration()
        self.pass_stage("registration")
        exam = self.write("sources/exam.txt")
        self.bind("knowledge", "exam_result", exam)
        self.pass_stage("knowledge")
        notice.write_text("updated notice", encoding="utf-8")
        self.bind("registration", "official_notice", notice, force=True)
        status = workflow.status(self.root)
        self.assertEqual([s["status"] for s in status["stages"][:2]], ["pending", "pending"])

    def test_reviewer_cannot_be_author(self):
        notice = self.write("sources/notice.txt")
        rules = self.write("sources/rules.json", json.dumps({
            "verified_at": date.today().isoformat(),
            "national_notice_url": "https://example.org/national",
            "school_notice_url": "https://example.org/school",
        }))
        receipt = self.write("sources/receipt.txt")
        self.bind("registration", "official_notice", notice, "same")
        self.bind("registration", "rules_verification", rules, "same")
        self.bind("registration", "registration_confirmation", receipt, "same")
        with self.assertRaisesRegex(ValueError, "Reviewer cannot"):
            workflow.review_stage(self.root, "registration", "same", "pass", "self")

    def test_path_escape_is_rejected(self):
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("data", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "escapes project"):
            self.bind("registration", "official_notice", outside)

    def test_init_never_overwrites(self):
        with self.assertRaisesRegex(ValueError, "refusal to overwrite"):
            workflow.init(self.root, "zhengda-17", "2026-2027")

    def test_existing_evidence_key_is_not_silently_overwritten(self):
        notice = self.write("sources/notice.txt", "first")
        self.bind("registration", "official_notice", notice)
        notice.write_text("second", encoding="utf-8")
        with self.assertRaisesRegex(workflow.BlockedError, "already bound"):
            self.bind("registration", "official_notice", notice)
        unchanged = workflow.get_state(self.root)["stages"]["registration"]["evidence"]["official_notice"]
        self.assertNotEqual(unchanged["sha256"], workflow.sha(notice))

    def test_force_overwrite_returns_replaced_block_and_invalidates_downstream(self):
        notice = self.write("sources/notice.txt", "first")
        self.bind("registration", "official_notice", notice, "first-author")
        notice.write_text("second", encoding="utf-8")
        result = workflow.evidence_add(self.root, "registration", "official_notice",
                                       str(notice), "second-author", force=True)
        self.assertEqual(result["replaced"]["author"], "first-author")
        self.assertNotEqual(result["replaced"]["sha256"], result["sha256"])
        self.assertEqual(result["downstream_invalidated"], True)

    def test_evidence_list_reports_path_hash_and_drift(self):
        notice = self.write("sources/notice.txt", "first")
        self.bind("registration", "official_notice", notice)
        listing = workflow.evidence_list(self.root, "registration")
        item = next(i for i in listing["items"] if i["key"] == "official_notice")
        self.assertEqual(item["path"], "sources/notice.txt")
        self.assertTrue(item["sha256_matches"])
        notice.write_text("changed", encoding="utf-8")
        listing = workflow.evidence_list(self.root, "registration")
        item = next(i for i in listing["items"] if i["key"] == "official_notice")
        self.assertFalse(item["sha256_matches"])
        self.assertTrue(any(m["key"] == "rules_verification" for m in listing["missing"]))

    def test_stale_or_incomplete_rules_verification_blocks(self):
        notice = self.write("sources/notice.txt")
        self.bind("registration", "official_notice", notice)
        for label, payload, expected in [
            ("stale", {"verified_at": (date.today() - timedelta(days=61)).isoformat(),
                       "national_notice_url": "https://example.org/n",
                       "school_notice_url": "https://example.org/s"}, "stale"),
            ("future", {"verified_at": (date.today() + timedelta(days=1)).isoformat(),
                        "national_notice_url": "https://example.org/n",
                        "school_notice_url": "https://example.org/s"}, "future"),
            ("missing-url", {"verified_at": date.today().isoformat()}, "national_notice_url"),
        ]:
            with self.subTest(label=label):
                rules = self.write("sources/rules-" + label + ".json", json.dumps(payload))
                if label == "stale":
                    self.bind("registration", "rules_verification", rules)
                else:
                    workflow.evidence_add(self.root, "registration", "rules_verification",
                                          str(rules), "team", force=True)
                problems = workflow.evidence_problems(
                    self.root, workflow.get_state(self.root), "registration", date.today())
                self.assertTrue(any(expected in problem for problem in problems), problems)

    def test_rules_verification_accepts_fresh_markdown_record(self):
        notice = self.write("sources/notice.txt")
        self.bind("registration", "official_notice", notice)
        rules = self.write("sources/rules.md",
                           f"verified_at: {date.today().isoformat()}\n"
                           "https://example.org/national\nhttps://example.org/school\n")
        self.bind("registration", "rules_verification", rules)
        problems = workflow.evidence_problems(
            self.root, workflow.get_state(self.root), "registration", date.today())
        self.assertFalse(any("rules_verification" in problem for problem in problems), problems)

    def test_template_pull_copies_and_refuses_overwrite(self):
        result = workflow.template_pull(self.root, "analysis-contract.csv")
        self.assertEqual(result["path"], "plans/analysis-contract.csv")
        self.assertTrue((self.root / "plans/analysis-contract.csv").is_file())
        with self.assertRaisesRegex(workflow.BlockedError, "already exists"):
            workflow.template_pull(self.root, "analysis-contract.csv")
        result = workflow.template_pull(self.root, "analysis-contract.csv", force=True)
        self.assertTrue(result["overwritten"])

    def test_evidence_overwrite_cli_returns_three(self):
        notice = self.write("sources/notice.txt", "first")
        self.bind("registration", "official_notice", notice)
        notice.write_text("second", encoding="utf-8")
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/workflow.py"), "evidence", "add",
            "--project", str(self.root), "--stage", "registration",
            "--key", "official_notice", "--file", str(notice), "--author", "team",
        ], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 3, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertIn("already bound", payload["error"])

    def test_raw_dataset_must_live_in_private_directory(self):
        raw = self.write("data/raw_responses.csv", "id,answer\n1,x\n")
        with self.assertRaisesRegex(ValueError, "raw_private"):
            self.bind("fieldwork", "raw_dataset", raw)
        private_raw = self.write("raw_private/raw_responses.csv", "id,answer\n1,x\n")
        self.bind("fieldwork", "raw_dataset", private_raw)

    def test_dependency_manifest_detects_changed_dependency(self):
        instrument = self.write("plans/questionnaire.md", "version 1")
        sampling = self.write("plans/sampling.md", "sampling plan")
        ethics = self.write("plans/ethics.md", "consent")
        contract = self.write("plans/analysis-contract.csv", "item,rule\nq1,total\n")
        import hashlib
        manifest = self.write("plans/design-manifest.json", "")
        manifest.write_text(__import__("json").dumps({
            "description": "frozen design contract",
            "files": [
                {"path": "plans/questionnaire.md", "sha256": hashlib.sha256(instrument.read_bytes()).hexdigest(), "role": "instrument"},
                {"path": "plans/analysis-contract.csv", "sha256": hashlib.sha256(contract.read_bytes()).hexdigest(), "role": "analysis contract"},
            ],
            "command": "",
            "environment": "local",
        }), encoding="utf-8")
        self.bind("design", "survey_instrument", instrument)
        self.bind("design", "sampling_plan", sampling)
        self.bind("design", "research_ethics", ethics)
        self.bind("design", "design_manifest", manifest)
        self.assertEqual(workflow.evidence_problems(self.root, workflow.get_state(self.root), "design"), [])
        contract.write_text("item,rule\nq1,complete-case\n", encoding="utf-8")
        problems = workflow.evidence_problems(self.root, workflow.get_state(self.root), "design")
        self.assertTrue(any("manifest dependency" in x for x in problems), problems)

    def test_review_fail_and_blocked_cli_return_three(self):
        self.bind_registration()
        for decision in ["fail", "blocked"]:
            with self.subTest(decision=decision):
                result = subprocess.run([
                    sys.executable, str(ROOT / "scripts/workflow.py"), "review",
                    "--project", str(self.root), "--stage", "registration",
                    "--reviewer", "IndependentQA", "--decision", decision,
                    "--note", "test terminal outcome",
                ], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 3, result.stderr or result.stdout)
                self.assertEqual(__import__("json").loads(result.stdout)["status"], "blocked")

    def test_symlink_evidence_is_rejected(self):
        target = self.write("sources/real_notice.txt")
        link = self.root / "sources" / "notice_link.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable in this environment: {exc}")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.bind("registration", "official_notice", link)

    def create_task(self, title="Run analysis", acceptance_text="Check numerical results"):
        contract = self.write("plans/acceptance.md", acceptance_text)
        return task_queue.create(self.root, "analysis", title, "DSH", str(contract))

    def test_queue_does_not_treat_submit_as_accept(self):
        task = self.create_task()
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        output = self.write("analysis/result.csv", "x,y\n1,2\n")
        result = task_queue.change(self.root, tid, "submit", "DSH", output=str(output))
        self.assertEqual(result["status"], "needs_review")
        with self.assertRaisesRegex(ValueError, "Self-review"):
            task_queue.change(self.root, tid, "review", "DSH", decision="pass", note="same actor")
        result = task_queue.change(self.root, tid, "review", "IndependentQA", decision="pass", note="复核运行")
        self.assertEqual(result["status"], "accepted")

    def test_queue_detects_changed_output_before_review(self):
        task = self.create_task()
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        output = self.write("analysis/result.csv", "value,1")
        task_queue.change(self.root, tid, "submit", "DSH", output=str(output))
        output.write_text("value,9", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed"):
            task_queue.change(self.root, tid, "review", "QA", decision="pass", note="reviewed")

    def test_queue_detects_changed_inputs_before_submit_and_review(self):
        contract = self.write("plans/acceptance.md", "Check numerical results")
        source = self.write("analysis/source.csv", "x\n1\n")
        task = task_queue.create(self.root, "analysis", "Run analysis", "DSH", str(contract), inputs=[str(source)])
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        source.write_text("x\n2\n", encoding="utf-8")
        output = self.write("analysis/result.csv", "x\n2\n")
        with self.assertRaisesRegex(ValueError, "Task evidence changed"):
            task_queue.change(self.root, tid, "submit", "DSH", output=str(output))
        listing = task_queue.list_tasks(self.root)
        self.assertEqual(listing["tasks"][0]["effective_status"], "STALE_INPUT")

    def test_queue_records_execution_metadata(self):
        task = self.create_task()
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        output = self.write("analysis/result.csv", "x\n1\n")
        log = self.write("analysis/run.log", "exit=0\n")
        task_queue.change(self.root, tid, "submit", "DSH", output=str(output), command="python analysis.py", exit_code=0, log=str(log))
        stored = task_queue.load(self.root, tid)
        self.assertEqual(stored["execution"]["command"], "python analysis.py")
        self.assertEqual(stored["execution"]["exit_code"], 0)
        self.assertEqual(stored["execution"]["log"]["path"], "analysis/run.log")

    def test_queue_detects_changed_execution_log(self):
        task = self.create_task()
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        output = self.write("analysis/result.csv", "x\n1\n")
        log = self.write("analysis/run.log", "exit=0\n")
        task_queue.change(self.root, tid, "submit", "DSH", output=str(output), command="python analysis.py", exit_code=0, log=str(log))
        log.write_text("exit=1\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "execution log SHA-256 differs"):
            task_queue.change(self.root, tid, "review", "IndependentQA", decision="pass", note="reviewed")
        listing = task_queue.list_tasks(self.root)
        self.assertEqual(listing["tasks"][0]["effective_status"], "STALE_EXECUTION")

    def test_queue_list_marks_accepted_output_stale(self):
        task = self.create_task()
        tid = task["task_id"]
        task_queue.change(self.root, tid, "claim", "DSH")
        output = self.write("analysis/result.csv", "x,y\n1,2\n")
        task_queue.change(self.root, tid, "submit", "DSH", output=str(output))
        task_queue.change(self.root, tid, "review", "IndependentQA", decision="pass", note="复核通过")
        output.write_text("x,y\n1,999\n", encoding="utf-8")
        listing = task_queue.list_tasks(self.root)
        self.assertEqual(listing["tasks"][0]["status"], "accepted")
        self.assertEqual(listing["tasks"][0]["effective_status"], "STALE_OUTPUT")

    def test_queue_rejects_changed_acceptance_contract(self):
        task = self.create_task()
        contract = self.root / "plans" / "acceptance.md"
        contract.write_text("Changed acceptance criteria", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Acceptance criteria changed"):
            task_queue.change(self.root, task["task_id"], "claim", "DSH")

    def test_queue_rejects_wrong_assignee(self):
        task = self.create_task()
        with self.assertRaisesRegex(ValueError, "Actor does not match assignee"):
            task_queue.change(self.root, task["task_id"], "claim", "Workbud")


if __name__ == "__main__":
    unittest.main()
