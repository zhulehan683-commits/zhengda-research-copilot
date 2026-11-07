import hashlib
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
        decision = (ROOT / "LICENSE-DECISION.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("未决定", decision)
        license_file = ROOT / "LICENSE"
        if license_file.exists():
            self.assertTrue(license_file.read_text(encoding="utf-8").strip())
        else:
            self.assertIn("没有 `LICENSE` 文件", readme)

    def test_award_snapshot_is_not_redistributed(self):
        self.assertFalse((ROOT / "references/award-topics/data.js").exists())
        baseline = (ROOT / "references/award-topics/baseline.json").read_text(encoding="utf-8")
        self.assertIn("no raw title rows are bundled", baseline)

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
            "templates/topic-density-report.md",
            "templates/questionnaire-blueprint.csv",
            "templates/questionnaire-review.csv",
            "templates/analysis-contract.csv",
            "templates/design-manifest.json",
            "templates/sampling-plan.md",
            "templates/pilot-log.md",
            "templates/fieldwork-log.csv",
            "templates/data-dictionary.csv",
            "templates/cleaning-report.md",
            "templates/analysis-plan.md",
            "templates/analysis-manifest.json",
            "templates/ai-usage-log.csv",
            "templates/rules-checklist.md",
            "templates/defense-question-bank.md",
            "templates/report-qa-checklist.md",
            "templates/submission-manifest.csv",
        ]:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_integrated_upstream_references_exist_and_are_attributed(self):
        merged = [
            "references/method-routing.md",
            "references/text-analysis.md",
            "references/visualization-guide.md",
            "references/report-production.md",
            "templates/intake.md",
            "templates/model-option-comparison.md",
            "templates/result-matrix.csv",
            "templates/figure-register.csv",
            "tests/pressure-scenarios.md",
        ]
        for rel in merged:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("zhengdabei-survey-report-skill", notices)
        self.assertIn("MIT", notices)
        self.assertIn("DDXYY189", notices)

    def test_install_script_uses_staging_validation(self):
        script = (ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("install.py", script)
        self.assertIn("$LASTEXITCODE", script)
        installer = (ROOT / 'install.py').read_text(encoding='utf-8')
        self.assertIn('Staging validation failed', installer)
        self.assertIn('scripts/workflow.py', installer)

    def test_skill_name_and_new_routes(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('name: zhengda-research-copilot', skill)
        self.assertIn('references/measurement-and-inference.md', skill)
        self.assertIn('references/grill-me.md', skill)
        self.assertIn('references/find-skills.md', skill)
        self.assertIn('scripts/survey_audit.py', skill)
        self.assertIn('scripts/stats_basic.py', skill)
        self.assertIn('scripts/power_calc.py', skill)
        self.assertIn('scripts/advisor.py', skill)
        self.assertIn('scripts/topic_radar.py', skill)
        self.assertIn('references/award-topics.md', skill)
        self.assertIn('evidence list', skill)
        self.assertIn('rules_verification', skill)

    def test_execution_layer_examples_and_fast_lanes_exist(self):
        required = [
            'scripts/stats_basic.py',
            'scripts/power_calc.py',
            'scripts/advisor.py',
            'scripts/topic_radar.py',
            'references/award-topics.md',
            'references/award-topics/baseline.json',
            'templates/rules-verification.json',
            'templates/grill-log.md',
            'templates/topic-density-report.md',
            'examples/sample-project/README.md',
            'examples/sample-project/data/sample_survey.csv',
            'examples/sample-project/plans/design-manifest.json',
        ]
        for rel in required:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)
        readme = (ROOT / 'examples/sample-project/README.md').read_text(encoding='utf-8')
        self.assertIn('不得用于参赛', readme)

    def test_text_templates_and_examples_use_lf(self):
        for base in [ROOT / 'templates', ROOT / 'examples']:
            for path in base.rglob('*'):
                if path.is_file() and path.suffix.lower() in {'.md', '.csv', '.json', '.txt'}:
                    with self.subTest(path=str(path.relative_to(ROOT))):
                        self.assertNotIn(b'\r\n', path.read_bytes())

    def test_bundled_skill_snapshots_match_pinned_sources(self):
        lock = json.loads((ROOT / 'docs/upstreams.lock.json').read_text(encoding='utf-8'))
        sources = {entry['repository']: entry for entry in lock['sources']}
        for repo in ['mattpocock/skills', 'vercel-labs/skills']:
            source = sources[repo]
            self.assertRegex(source['commit'], r'^[0-9a-f]{40}$')
            license_bytes = (ROOT / source['license_file']).read_bytes()
            self.assertEqual(hashlib.sha256(license_bytes).hexdigest(), source['license_sha256'])
            for component in source['components']:
                path = component['original_copy']
                with self.subTest(path=path):
                    original = (ROOT / path).read_bytes()
                    self.assertEqual(hashlib.sha256(original).hexdigest(),
                                     component['source_sha256'])
        self.assertTrue((ROOT / '.agents/skills/grilling/SKILL.md').is_file())
        self.assertTrue((ROOT / 'docs/INSTALLATION.md').is_file())

    def test_recorded_license_hashes_match_checkout_bytes(self):
        lock = json.loads((ROOT / 'docs/upstreams.lock.json').read_text(encoding='utf-8'))
        for source in lock['sources']:
            if 'license_sha256' in source:
                with self.subTest(repository=source['repository']):
                    actual = hashlib.sha256((ROOT / source['license_file']).read_bytes()).hexdigest()
                    self.assertEqual(actual, source['license_sha256'])


if __name__ == "__main__":
    unittest.main()
