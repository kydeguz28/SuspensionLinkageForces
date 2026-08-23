import json
import unittest
import tempfile
from pathlib import Path

from suspension_linkage_forces import solve_config
from linkage_viewer import write_viewer_html


ROOT = Path(__file__).resolve().parents[1]


class SuspensionForceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        cls.result = solve_config(config)

    def test_all_load_cases_satisfy_six_equilibrium_equations(self):
        for assembly in self.result["assemblies"]:
            for case in assembly["load_cases"]:
                self.assertLess(case["max_equilibrium_residual"], 1e-8)

    def test_reference_contains_front_and_rear_tie_rods(self):
        front_names = {
            member["name"]
            for member in self.result["assemblies"][0]["load_cases"][0]["members"]
        }
        rear_names = {
            member["name"]
            for member in self.result["assemblies"][1]["load_cases"][0]["members"]
        }
        self.assertIn("steering_tie_rod", front_names)
        self.assertIn("rear_tie_rod", rear_names)

    def test_rocker_axis_moment_is_balanced(self):
        for assembly in self.result["assemblies"]:
            for case in assembly["load_cases"]:
                rocker = case["rocker"]
                balanced = (
                    rocker["pushrod_axis_moment"]
                    + rocker["shock_force"]
                    * rocker["shock_axis_moment_per_unit_force"]
                )
                self.assertAlmostEqual(balanced, 0.0, places=8)

    def test_ride_height_baseline_uses_vehicle_weight_and_unsprung_weight(self):
        ride = self.result["ride_height"]
        self.assertAlmostEqual(ride["front_tire_load_per_corner_lbf"], 159.012)
        self.assertAlmostEqual(ride["rear_tire_load_per_corner_lbf"], 156.488)
        self.assertAlmostEqual(ride["unsprung_weight_per_corner_lbf"], 21.625)
        self.assertAlmostEqual(ride["front_spring_supported_wheel_load_lbf"], 137.387)
        self.assertAlmostEqual(ride["rear_spring_supported_wheel_load_lbf"], 134.863)

    def test_moving_geometry_preserves_links_and_fixed_shock_chassis_pickup(self):
        config = json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        config_by_name = {item["name"]: item for item in config["assemblies"]}
        for assembly in self.result["assemblies"]:
            fixed = config_by_name[assembly["name"]]["rocker"]["shock_chassis_pickup"]
            for case in assembly["load_cases"]:
                motion = case["kinematics"]
                self.assertLess(motion["max_constraint_residual"], 1e-7)
                self.assertEqual(motion["geometry"]["rocker"]["shock_chassis_pickup"], fixed)
                expected = (
                    assembly["ride_height_reference"]["shock_compression_force"]
                    + assembly["ride_height_reference"]["spring_rate"]
                    * motion["shock_travel_from_ride_height"]
                )
                self.assertAlmostEqual(expected, motion["spring_force"], places=7)
                self.assertAlmostEqual(-case["rocker"]["shock_force"], expected, places=5)

    def test_force_sign_state_is_consistent(self):
        for assembly in self.result["assemblies"]:
            for case in assembly["load_cases"]:
                for member in case["members"]:
                    expected = "tension" if member["force"] >= 0.0 else "compression"
                    self.assertEqual(member["state"], expected)

    def test_standalone_viewer_embeds_geometry_and_results(self):
        config = json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "viewer.html"
            write_viewer_html(config, self.result, output)
            html = output.read_text(encoding="utf-8")
        self.assertIn("front_left", html)
        self.assertIn("rear_left", html)
        self.assertIn("steering_tie_rod", html)
        self.assertIn("FIXED CHASSIS", html)
        self.assertNotIn("__SUSPENSION_DATA__", html)
        self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
