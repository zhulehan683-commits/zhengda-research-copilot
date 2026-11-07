import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import topic_radar


FIXTURE = """window.AWARD_DATA=[
  {"y":2022,"g":"本科组","a":"一等奖","s":"甲大学","t":"食品零添加与购买意愿研究","p":"食品饮料","d":"食品","tags":["食品"],"kw":["零添加"],"c":"高","r":false,"u":"http://example.test/1"},
  {"y":2025,"g":"本科组","a":"二等奖","s":"乙大学","t":"食品添加剂公众认知研究","p":"食品饮料","d":"食品","tags":["食品安全"],"kw":["添加剂"],"c":"中","r":false,"u":"http://example.test/2"},
  {"y":2026,"g":"本科组","a":"一等奖","s":"丙大学","t":"AI陪伴机器人适老化研究","p":"健康医疗与养老","d":"养老","tags":["养老"],"kw":["AI陪伴","机器人"],"c":"高","r":false,"u":"http://example.test/3"},
  {"y":2022,"g":"研究生组","a":"二等奖","s":"丁大学","t":"宠物医疗保险研究","p":"金融保险与支付","d":"保险","tags":["宠物"],"kw":["保险"],"c":"低","r":true,"u":"http://example.test/4"}
];
"""


class TopicRadarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data.js"
        self.data.write_text(FIXTURE, encoding="utf-8")
        self.records, self.digest = topic_radar.load_snapshot(self.data)

    def test_parses_js_assignment_and_builds_coverage(self):
        self.assertEqual(len(self.records), 4)
        self.assertEqual(len(self.digest), 64)
        cov = topic_radar.coverage(self.records)
        self.assertEqual(cov["total"], 4)
        self.assertEqual(cov["years"], [2022, 2025, 2026])
        self.assertEqual(cov["comparable_across_all_years"], ["本科组"])
        self.assertEqual(cov["year_group_counts"]["2026"]["本科组"], 1)
        self.assertIn({"year": 2026, "group": "研究生组"}, cov["missing_cells"])

    def test_search_deduplicates_titles_and_reports_best_award(self):
        result = topic_radar.search(self.records, "零添加 添加剂")
        self.assertEqual(result["hit_count"], 2)
        self.assertEqual(result["best_award"], "一等奖")
        self.assertEqual(result["unmatched_terms"], [])
        titles = [item["title"] for item in result["hits"]]
        self.assertIn("食品零添加与购买意愿研究", titles)
        self.assertIn("食品添加剂公众认知研究", titles)

    def test_search_filters_and_low_confidence_flag(self):
        result = topic_radar.search(self.records, "宠物", groups=["本科组"])
        self.assertEqual(result["hit_count"], 0)
        self.assertEqual(result["filters"]["groups"], ["本科组"])
        json.dumps(result, ensure_ascii=False)
        result = topic_radar.search(self.records, "宠物")
        self.assertEqual(result["hit_count"], 1)
        self.assertEqual(result["low_confidence_hits"], 1)
        result = topic_radar.search(self.records, "宠物", include_low_confidence=False)
        self.assertEqual(result["hit_count"], 0)

    def test_search_limit_marks_truncation(self):
        result = topic_radar.search(self.records, "研究", limit=1)
        self.assertEqual(len(result["hits"]), 1)
        self.assertTrue(result["hits_truncated"])

    def test_render_contains_coverage_and_explicit_boundaries(self):
        result = topic_radar.search(self.records, "宠物")
        text = topic_radar.render_search(result, self.records, self.digest)
        self.assertIn("2022—2026 年全国一、二等奖", text)
        self.assertIn("零命中不等于无人研究", text)
        self.assertIn("宠物医疗保险研究", text)
        self.assertIn("数据覆盖", text)

    def test_empty_or_invalid_snapshot_is_rejected(self):
        with self.assertRaises(topic_radar.RadarError):
            topic_radar.parse_snapshot("")
        with self.assertRaises(topic_radar.RadarError):
            topic_radar.parse_snapshot("window.AWARD_DATA={};")
        with self.assertRaises(topic_radar.RadarError):
            topic_radar.parse_snapshot('[{"y":2026,"g":"本科组"}]')

    def test_project_cache_resolution_and_no_implicit_download(self):
        project = self.root / "project"
        cached = topic_radar.default_data_path(project)
        cached.parent.mkdir(parents=True)
        cached.write_text(FIXTURE, encoding="utf-8")
        self.assertEqual(topic_radar.resolve_data_path(None, str(project)), cached)
        other = self.root / "other"
        with self.assertRaisesRegex(topic_radar.RadarError, "fetch"):
            topic_radar.resolve_data_path(None, str(other))

    def test_explicit_fetch_from_local_source_and_refuses_overwrite(self):
        source = self.root / "source.js"
        source.write_text(FIXTURE, encoding="utf-8")
        output = self.root / "downloaded.js"
        result = topic_radar.fetch_snapshot(output, url=source.as_uri())
        self.assertEqual(result["records"], 4)
        self.assertFalse(result["pinned_hash_verified"])
        with self.assertRaisesRegex(topic_radar.RadarError, "already exists"):
            topic_radar.fetch_snapshot(output, url=source.as_uri())

    def test_write_refuses_silent_overwrite(self):
        target = self.root / "report.md"
        topic_radar._write(target, "first")
        with self.assertRaisesRegex(topic_radar.RadarError, "already exists"):
            topic_radar._write(target, "second")
        self.assertEqual(target.read_text(encoding="utf-8"), "first")

    def test_bundled_baseline_is_aggregate_only(self):
        baseline = topic_radar.load_baseline()
        self.assertEqual(baseline["coverage"]["total"], 2920)
        self.assertIn("本科组", baseline["coverage"]["comparable_across_all_years"])
        terms = {item["term"] for item in baseline["keyword_signals"]}
        self.assertIn("清洁标签", terms)
        serialized = json.dumps(baseline, ensure_ascii=False)
        self.assertNotIn("深圳大学", serialized)
        self.assertNotIn("崇“零”风向", serialized)


if __name__ == "__main__":
    unittest.main()
