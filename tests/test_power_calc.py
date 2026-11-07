import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import power_calc


class PowerCalcTests(unittest.TestCase):
    def test_proportion_sample_size_matches_standard_approximation(self):
        result = power_calc.sample_size_proportion(p=0.5, margin=0.05)
        self.assertEqual(result["n_before_dropout"], 385)
        self.assertEqual(result["n"], 385)
        inflated = power_calc.sample_size_proportion(p=0.5, margin=0.05, dropout=0.2)
        self.assertEqual(inflated["n"], 482)

    def test_finite_population_correction_reduces_n(self):
        result = power_calc.sample_size_proportion(p=0.5, margin=0.05, population=500)
        self.assertLess(result["n_before_dropout"], 385)
        self.assertGreater(result["n_before_dropout"], 200)

    def test_two_proportion_design_reaches_target(self):
        result = power_calc.sample_size_two_proportions(0.4, 0.6, power=0.8)
        self.assertGreaterEqual(result["achieved_power_before_dropout"], 0.8)
        self.assertEqual(result["n1"], result["n2"])

    def test_mean_design_and_power(self):
        result = power_calc.sample_size_means(delta=0.5, sd=1.0, power=0.8)
        self.assertGreater(result["n1"], 50)
        self.assertLess(result["n1"], 100)
        achieved = power_calc.power_means(0.5, 1.0, result["n1"], result["n2"])
        self.assertGreaterEqual(achieved["power"], 0.79)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            power_calc.sample_size_proportion(p=1.2)
        with self.assertRaises(ValueError):
            power_calc.sample_size_two_proportions(0.4, 0.4)
        with self.assertRaises(ValueError):
            power_calc.sample_size_means(delta=0, sd=1)


if __name__ == "__main__":
    unittest.main()
