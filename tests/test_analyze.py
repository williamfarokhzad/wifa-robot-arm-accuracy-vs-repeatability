from pathlib import Path
import math
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from analyze import read_points, summarize

ROOT = Path(__file__).resolve().parents[1]


class PoseSampleTests(unittest.TestCase):
    def sample(self, name):
        return summarize((100, 50), read_points(ROOT / "examples" / f"{name}.csv"))

    def test_tight_offset_has_small_spread_and_large_bias(self):
        r = self.sample("tight_offset")
        self.assertEqual(r.offset, (2.0, 0.0))
        self.assertAlmostEqual(r.rms_spread_mm, .2)
        self.assertAlmostEqual(r.max_target_error_mm, 2.2)

    def test_centered_wide_has_zero_mean_error_but_no_exact_hits(self):
        r = self.sample("centered_wide")
        self.assertEqual(r.center_error_mm, 0)
        self.assertEqual(r.rms_spread_mm, 1.5)
        self.assertEqual(r.max_target_error_mm, 1.5)

    def test_two_approaches_can_cancel_the_mean_error(self):
        r = self.sample("approach_mixed")
        self.assertEqual(r.center_error_mm, 0)
        self.assertAlmostEqual(r.rms_spread_mm, math.sqrt(1.01))
        self.assertAlmostEqual(self.sample("approach_positive").offset[0], 1.0)
        self.assertAlmostEqual(self.sample("approach_negative").offset[0], -1.0)
        self.assertAlmostEqual(self.sample("approach_positive").rms_spread_mm, .1)
        self.assertAlmostEqual(self.sample("approach_negative").rms_spread_mm, .1)

    def test_two_axis_offset_and_translation(self):
        a = summarize((0, 0), [(3, 3), (3, 5)])
        b = summarize((10, -10), [(13, -7), (13, -5)])
        self.assertEqual(a.center_error_mm, 5)
        self.assertEqual(a.rms_spread_mm, 1)
        self.assertEqual(a.offset, b.offset)
        self.assertEqual(a.max_target_error_mm, b.max_target_error_mm)

    def test_refuses_nonfinite_and_single_reading(self):
        for target, points in [
            ((0, 0), [(0, 0)]),
            ((0, 0), [(0, 0), (math.nan, 0)]),
            ((math.inf, 0), [(0, 0), (0, 0)]),
        ]:
            with self.subTest(target=target, points=points), self.assertRaises(ValueError):
                summarize(target, points)

    def test_bad_csv_width_and_header(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            for contents, pattern in [
                ("x,y\n3,4\n", "header"),
                ("x_mm,y_mm\n3,4,5\n", "line 2"),
            ]:
                with self.subTest(contents=contents), self.assertRaisesRegex(ValueError, pattern):
                    p.write_text(contents, encoding="utf-8")
                    read_points(p)

    def test_cli_success_and_invalid_target(self):
        args = [sys.executable, "analyze.py", "examples/tight_offset.csv", "--target"]
        good = subprocess.run(args + ["100", "50"], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertIn("Mean endpoint error: 2.000 mm", good.stdout)
        self.assertIn("RMS spread around mean: 0.200 mm", good.stdout)
        bad = subprocess.run(args + ["nan", "50"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("finite millimetre coordinates", bad.stderr)


if __name__ == "__main__":
    unittest.main()
