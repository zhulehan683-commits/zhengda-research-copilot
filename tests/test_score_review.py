import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_review.py"
SPEC = importlib.util.spec_from_file_location("score_review", SCRIPT)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class ScoreReviewTests(unittest.TestCase):
    def setUp(self):
        self.data = {"scores": {k: {"score": 8, "evidence": ["report/table-1"]}
                               for k in review.DIMENSIONS}, "issues": []}

    def test_weighted_mean_and_unweighted_minimum(self):
        self.data["scores"]["analysis"]["score"] = 2
        self.data["weights"] = {"analysis": 0.01, "report": 100}
        result = review.evaluate(self.data)
        self.assertEqual(result["raw_min"], 2)
        self.assertAlmostEqual(result["weighted_mean"], (5 * 8 + 1.5 * 8 + 0.7 * 2) / 7.2)
        self.assertEqual(result["suggestion"], "revise")

    def test_high_issue_blocks_despite_perfect_scores(self):
        for item in self.data["scores"].values():
            item["score"] = 10
        self.data["issues"] = [{"severity": "high", "detail": "Untraceable result"}]
        self.assertEqual(review.evaluate(self.data)["suggestion"], "blocked")

    def test_scores_never_grant_stage_approval_or_mutate_input(self):
        before = copy.deepcopy(self.data)
        result = review.evaluate(self.data)
        self.assertEqual(result["suggestion"], "review_ready")
        self.assertFalse(result["stage_approval"])
        self.assertEqual(result["evidence_authenticity"], "NOT_VERIFIED_BY_SCRIPT")
        self.assertEqual(self.data, before)

    def test_rejects_nonfinite_boolean_and_out_of_range_scores(self):
        for value in [True, float("nan"), float("inf"), -1, 11, "8", None]:
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data["scores"]["analysis"]["score"] = value
                with self.assertRaises(ValueError):
                    review.evaluate(data)

    def test_rejects_invalid_weights(self):
        for weights in [{"typo": 1}, {"analysis": 0}, {"analysis": True},
                        {"analysis": float("nan")}, {"analysis": -2}]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                review.evaluate({**self.data, "weights": weights})

    def test_rejects_missing_dimension_evidence_and_issues(self):
        bad = copy.deepcopy(self.data)
        del bad["scores"]["analysis"]
        missing_evidence = copy.deepcopy(self.data)
        missing_evidence["scores"]["report"]["evidence"] = []
        for data in [bad, missing_evidence, {"scores": self.data["scores"]}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                review.evaluate(data)

    def test_cli_blocking_exit_and_read_only_input(self):
        self.data["issues"] = [{"severity": "high", "detail": "Missing source"}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            before = path.read_bytes()
            proc = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3, proc.stderr)
            self.assertFalse(json.loads(proc.stdout)["stage_approval"])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([p.name for p in Path(folder).iterdir()], ["review.json"])


if __name__ == "__main__":
    unittest.main()
