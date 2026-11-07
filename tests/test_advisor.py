import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import advisor


class AdvisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_skill(self, name, description):
        folder = self.root / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8")

    def test_find_scans_frontmatter_and_reports_only_local(self):
        self.write_skill("survey-helper", "Statistical analysis and questionnaire diagnostics")
        self.write_skill("deck-helper", "Create presentation slides")
        result = advisor.find_skills("问卷 统计分析", roots=[self.root])
        self.assertEqual(result["local_matches"][0]["name"], "survey-helper")
        self.assertFalse(result["remote_search_performed"])
        self.assertIn('npx skills find "survey questionnaire statistical analysis statistics"',
                      result["search_commands"])

    def test_find_skips_meta_skills_unless_requested(self):
        self.write_skill("find-skills", "Find survey statistics skills")
        result = advisor.find_skills("统计分析", roots=[self.root])
        self.assertEqual(result["local_matches"], [])
        result = advisor.find_skills("find a skill for statistics", roots=[self.root])
        self.assertEqual(result["local_matches"][0]["name"], "find-skills")

    def test_grill_produces_frontier_and_recommendation(self):
        text = advisor.grill("design", quick=True)
        self.assertIn("Q1", text)
        self.assertIn("建议", text)
        self.assertNotIn("Q4", text)
        full = advisor.grill("design")
        self.assertIn("Q6", full)

    def test_grill_write_is_unique_and_does_not_touch_state(self):
        project = self.root / "project"
        (project / "state").mkdir(parents=True)
        state = {"stages": {"design": {"status": "pending", "evidence": {}, "review": None}}}
        (project / "state" / "project.json").write_text(json.dumps(state), encoding="utf-8")
        before = (project / "state" / "project.json").read_bytes()
        first = advisor._write_unique(project, "design", "one")
        second = advisor._write_unique(project, "design", "two")
        self.assertNotEqual(first, second)
        self.assertIn("当前项目状态", advisor.grill("design", project))
        self.assertEqual(before, (project / "state" / "project.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
