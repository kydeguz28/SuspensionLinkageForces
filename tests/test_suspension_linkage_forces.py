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
