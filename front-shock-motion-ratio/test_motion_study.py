from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "front_shock_motion_study", PROJECT / "generate_study.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MotionStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((PROJECT / "study_config.json").read_text())
        cls.study = MODULE.build_study(cls.config)

    def test_sweep_is_complete_and_contains_ride_height(self):
        samples = self.study["samples"]
        self.assertEqual(len(samples), 61)
        self.assertAlmostEqual(samples[0]["wheel_travel_in"], -1.5)
        self.assertAlmostEqual(samples[-1]["wheel_travel_in"], 1.5)
        ride = next(item for item in samples if abs(item["wheel_travel_in"]) < 1e-12)
        self.assertAlmostEqual(ride["shock_compression_in"], 0.0, places=10)
        self.assertAlmostEqual(ride["rocker_rotation_deg"], 0.0, places=8)

    def test_links_remain_constant_and_chassis_shock_pickup_is_fixed(self):
        assembly = self.study["assembly"]
        reference_lengths = MODULE._member_lengths(assembly)
        fixed_shock = assembly["rocker"]["shock_chassis_pickup"]
        for sample in self.study["samples"]:
            self.assertLess(sample["max_constraint_residual_in"], 1e-8)
            self.assertEqual(
                sample["geometry"]["rocker"]["shock_chassis_pickup"], fixed_shock
            )
            for index, member in enumerate(sample["geometry"]["members"]):
                current = MODULE.magnitude(
                    MODULE.subtract(member["anchor"], member["application"])
                )
                self.assertAlmostEqual(current, reference_lengths[index], places=8)

    def test_pullrod_pickup_follows_lower_arm_and_travel_uses_wheel_center(self):
        assembly = self.study["assembly"]
        lower = [
            member
            for member in assembly["members"]
            if member["name"].startswith("lower_")
        ]
        pullrod = next(
            member for member in assembly["members"] if member.get("role") == "pushrod"
        )
        reference_radii = [
            MODULE.magnitude(MODULE.subtract(pullrod["application"], leg["anchor"]))
            for leg in lower
        ]
        base_wheel_z = assembly["wheel_center"][2]
        for sample in self.study["samples"]:
            moved_pullrod = next(
                member
                for member in sample["geometry"]["members"]
                if member.get("role") == "pushrod"
            )
            for radius, leg in zip(reference_radii, lower):
                current = MODULE.magnitude(
                    MODULE.subtract(moved_pullrod["application"], leg["anchor"])
                )
                self.assertAlmostEqual(current, radius, places=8)
            actual_travel = base_wheel_z - sample["geometry"]["wheel_center"][2]
            self.assertAlmostEqual(actual_travel, sample["wheel_travel_in"], places=8)

    def test_shock_compression_is_monotonic_and_motion_ratio_positive(self):
        samples = self.study["samples"]
        compression = [item["shock_compression_in"] for item in samples]
        self.assertTrue(
            all(right > left for left, right in zip(compression, compression[1:]))
        )

    def test_physical_shock_length_and_stroke_limits(self):
        spec = self.study["shock_spec"]
        self.assertAlmostEqual(spec["extended_length_mm"], 200.0)
        self.assertAlmostEqual(spec["travel_mm"], 47.5)
        self.assertAlmostEqual(spec["collapsed_length_mm"], 152.5)
        self.assertAlmostEqual(
            spec["ride_height_stroke_used_mm"]
            + spec["ride_height_stroke_remaining_mm"],
            spec["travel_mm"],
            places=9,
        )
        self.assertAlmostEqual(
            spec["extension_limit_wheel_travel_in"], -0.7040631663, places=6
        )
        self.assertIsNone(spec["compression_limit_wheel_travel_in"])
        samples = self.study["samples"]
        self.assertEqual(samples[0]["shock_travel_status"], "over_extended")
        ride = next(item for item in samples if abs(item["wheel_travel_in"]) < 1e-12)
        self.assertEqual(ride["shock_travel_status"], "within_travel")
        self.assertAlmostEqual(ride["shock_length_mm"], 188.3195089694, places=6)
        self.assertGreater(samples[-1]["shock_stroke_remaining_mm"], 0.0)
        self.assertTrue(
            all(item["instantaneous_motion_ratio"] > 0.0 for item in samples)
        )
        self.assertTrue(
            all(
                abs(
                    item["wheel_rate_factor"]
                    - 1.0 / item["instantaneous_motion_ratio"] ** 2
                )
                < 1e-12
                for item in samples
            )
        )
        ride = next(item for item in samples if abs(item["wheel_travel_in"]) < 1e-12)
        self.assertAlmostEqual(ride["instantaneous_motion_ratio"], 1.5543557931, places=8)

    def test_generated_page_embeds_study_and_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "index.html"
            MODULE.write_study_html(self.study, output)
            html = output.read_text(encoding="utf-8")
        self.assertNotIn("__MOTION_STUDY_DATA__", html)
        self.assertIn("Front shock motion ratio study", html)
        self.assertIn('id="scene"', html)
        self.assertIn('id="trace"', html)
        self.assertIn('id="travel"', html)
        self.assertIn('id="strokeMeter"', html)
        self.assertIn("instantaneous_motion_ratio", html)
        self.assertIn("shock_travel_status", html)


if __name__ == "__main__":
    unittest.main()
