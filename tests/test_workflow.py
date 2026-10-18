import sys
import os
import subprocess
import tempfile
import unittest
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

    def bind(self, stage: str, key: str, path: Path, author="team"):
        return workflow.evidence_add(self.root, stage, key, str(path), author)

    def bind_registration(self):
        notice = self.write("sources/notice.txt")
        receipt = self.write("sources/receipt.txt")
        self.bind("registration", "official_notice", notice)
        self.bind("registration", "registration_confirmation", receipt)
        return notice, receipt

    def pass_stage(self, stage: str):
        return workflow.review_stage(self.root, stage, "IndependentReviewer", "pass", "仅记录测试中的人工复核操作")

    def test_missing_files_do_not_pass(self):
        result = workflow.check(self.root, workflow.get_state(self.root), "registration")
        self.assertEqual(result["status"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "Cannot pass stage"):
            workflow.review_stage(self.root, "registration", "QA", "pass", "not enough")

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
        self.bind("registration", "registration_confirmation", receipt)
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
        self.bind("registration", "official_notice", notice)
        status = workflow.status(self.root)
        self.assertEqual([s["status"] for s in status["stages"][:2]], ["pending", "pending"])

    def test_reviewer_cannot_be_author(self):
        notice = self.write("sources/notice.txt")
        receipt = self.write("sources/receipt.txt")
        self.bind("registration", "official_notice", notice, "same")
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

    def test_raw_dataset_must_live_in_private_directory(self):
        raw = self.write("data/raw_responses.csv", "id,answer\n1,x\n")
        with self.assertRaisesRegex(ValueError, "raw_private"):
            self.bind("fieldwork", "raw_dataset", raw)
        private_raw = self.write("raw_private/raw_responses.csv", "id,answer\n1,x\n")
        self.bind("fieldwork", "raw_dataset", private_raw)

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
