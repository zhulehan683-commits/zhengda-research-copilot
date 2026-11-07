import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import survey_audit
import workflow


class ExampleProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        shutil.copytree(ROOT / "examples" / "sample-project", self.root)
        workflow.init(self.root, "zhengda-17", "2026-2027")
        self.today = date(2026, 11, 7)

    def bind(self, stage, key, relative):
        return workflow.evidence_add(self.root, stage, key, relative, "demo")

    def pass_stage(self, stage):
        workflow.review_stage(self.root, stage, "DemoReviewer", "pass",
                              "演示状态，不是真实人工复核", today=self.today)

    def test_example_reaches_design_gate_without_real_data(self):
        for key, relative in [
            ("official_notice", "sources/rules-verification.json"),
            ("rules_verification", "sources/rules-verification.json"),
            ("registration_confirmation", "intake.md"),
        ]:
            self.bind("registration", key, relative)
        self.pass_stage("registration")
        self.bind("knowledge", "exam_result", "sources/demo-exam.txt")
        self.pass_stage("knowledge")
        self.bind("team", "team_roster", "sources/demo-team.csv")
        self.pass_stage("team")
        self.bind("topic", "topic_brief", "plans/topic-brief.md")
        self.bind("topic", "feasibility_check", "plans/feasibility-check.md")
        self.pass_stage("topic")
        self.bind("desk_research", "source_register", "sources/source_register.csv")
        self.bind("desk_research", "research_gap", "sources/research-gap.md")
        self.pass_stage("desk_research")
        for key, relative in [
            ("survey_instrument", "plans/survey-instrument.md"),
            ("sampling_plan", "plans/sampling-plan.md"),
            ("research_ethics", "plans/research-ethics.md"),
            ("design_manifest", "plans/design-manifest.json"),
        ]:
            self.bind("design", key, relative)
        result = workflow.check(self.root, workflow.get_state(self.root), "design",
                                today=self.today)
        self.assertEqual(result["status"], "PASS_MECHANICAL_ONLY", result["reasons"])

    def test_example_data_passes_preflight_as_demo_only(self):
        result = survey_audit.audit(self.root, "data/sample_survey.csv",
                                    "plans/data-preflight-schema.json")
        self.assertEqual(result["status"], "READY_FOR_REVIEW")
        self.assertEqual(result["row_count"], 50)
        self.assertFalse(result["scientific_validity_verified"])


if __name__ == "__main__":
    unittest.main()
