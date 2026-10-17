import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    def test_release_documents_exist(self):
        required = [
            "docs/PROJECT_SPEC.md",
            "docs/RELEASE_CHECKLIST.md",
            "docs/GITHUB_ABOUT.md",
            "docs/CODEX_GITHUB_PUBLISH_PROMPT.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "THIRD_PARTY_NOTICES.md",
            "LICENSE-DECISION.md",
        ]
        for rel in required:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_license_is_explicitly_pending_not_falsely_declared(self):
        self.assertFalse((ROOT / "LICENSE").exists())
        decision = (ROOT / "LICENSE-DECISION.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("未决定", decision)
        self.assertIn("没有 `LICENSE` 文件", readme)

    def test_competition_pack_warns_against_copying_school_specific_rules(self):
        data = json.loads((ROOT / "competitions/zhengda-17/rules.json").read_text(encoding="utf-8"))
        self.assertEqual(data["season"], "2026-2027")
        self.assertIn("secondary-institutional-notices-only", data["verification_status"])
        self.assertIn("不得复制其他学校", data["scope_warning"])
        serialized = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("202609240807339196", serialized)
        self.assertNotIn("202609212122019710", serialized)

    def test_templates_cover_major_research_stages(self):
        for rel in [
            "templates/knowledge-exam-study-plan.md",
            "templates/team-roster.csv",
            "templates/research-brief.md",
            "templates/topic-scorecard.csv",
            "templates/questionnaire-blueprint.csv",
            "templates/sampling-plan.md",
            "templates/pilot-log.md",
            "templates/fieldwork-log.csv",
            "templates/data-dictionary.csv",
            "templates/cleaning-report.md",
            "templates/analysis-plan.md",
            "templates/ai-usage-log.csv",
            "templates/rules-checklist.md",
            "templates/defense-question-bank.md",
            "templates/report-qa-checklist.md",
            "templates/submission-manifest.csv",
        ]:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_install_script_uses_staging_validation(self):
        script = (ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("staging", script)
        self.assertIn("scripts\\workflow.py", script)
        self.assertIn("Previous version backed up", script)


if __name__ == "__main__":
    unittest.main()
