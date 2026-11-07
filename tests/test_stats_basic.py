import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stats_basic


class StatsBasicTests(unittest.TestCase):
    def test_descriptive_statistics(self):
        values = [1, 2, 3, 4, 5]
        self.assertEqual(stats_basic.mean(values), 3)
        self.assertEqual(stats_basic.median(values), 3)
        self.assertAlmostEqual(stats_basic.stdev(values), math.sqrt(2.5))
        self.assertEqual(stats_basic.quantile(values, 0.5), 3)

    def test_t_critical_and_one_sample_test(self):
        self.assertAlmostEqual(stats_basic.t_critical(4, 0.95), 2.776445, places=5)
        result = stats_basic.t_test_one([1, 2, 3, 4, 5])
        self.assertAlmostEqual(result["t"], 4.242640687, places=5)
        self.assertAlmostEqual(result["p_value"], 0.013235, places=5)
        self.assertEqual(result["df"], 4)

    def test_welch_and_paired_tests(self):
        result = stats_basic.t_test_two([1, 2, 3], [4, 5, 6])
        self.assertAlmostEqual(result["difference"], -3)
        self.assertAlmostEqual(result["t"], -3.6742346, places=5)
        self.assertEqual(result["n1"], 3)
        paired = stats_basic.t_test_paired([1, 2, 3], [0, 1, 2])
        self.assertEqual(paired["test"], "paired t")
        self.assertAlmostEqual(paired["mean"], 1.0)

    def test_chi_square_and_fisher(self):
        result = stats_basic.chi_square([[10, 20], [30, 15]])
        self.assertAlmostEqual(result["statistic"], 8.0357142857, places=6)
        self.assertEqual(result["df"], 1)
        self.assertLess(result["p_value"], 0.01)
        fisher = stats_basic.fisher_exact([[3, 1], [1, 3]])
        self.assertAlmostEqual(fisher["p_value"], 34 / 70, places=6)

    def test_cronbach_alpha(self):
        result = stats_basic.cronbach_alpha([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        self.assertAlmostEqual(result["alpha"], 1.0, places=10)
        with self.assertRaises(ValueError):
            stats_basic.cronbach_alpha([[1, 2]])

    def test_ols_recovers_exact_line(self):
        result = stats_basic.ols([3, 5, 7, 9], {"x": [1, 2, 3, 4]})
        self.assertAlmostEqual(result["coefficients"]["intercept"], 1.0, places=8)
        self.assertAlmostEqual(result["coefficients"]["x"], 2.0, places=8)
        self.assertAlmostEqual(result["r_squared"], 1.0, places=10)
        self.assertEqual(result["n_dropped"], 0)
        with self.assertRaises(ValueError):
            stats_basic.ols([1, 2, 3], {"x": [1, 1, 1]})

    def test_logit_converges_on_nonseparable_data(self):
        result = stats_basic.logit([0, 0, 1, 0, 1, 1], {"x": [0, 1, 1, 2, 2, 3]})
        self.assertEqual(result["n"], 6)
        self.assertTrue(math.isfinite(result["coefficients"]["x"]))
        self.assertIn("odds_ratios", result)

    def test_complete_case_handling_reports_dropped_rows(self):
        result = stats_basic.ols([1, 2, None, 4, 5], {"x": [1, 2, 3, 4, None]})
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["n_dropped"], 2)


if __name__ == "__main__":
    unittest.main()
