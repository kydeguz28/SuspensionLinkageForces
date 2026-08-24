import json
import unittest
import tempfile
from pathlib import Path

from suspension_linkage_forces import expand_config, solve_config
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
        by_name = {assembly["name"]: assembly for assembly in self.result["assemblies"]}
        front_names = {
            member["name"]
            for member in by_name["front_right"]["load_cases"][0]["members"]
        }
        rear_names = {
            member["name"]
            for member in by_name["rear_right"]["load_cases"][0]["members"]
        }
        self.assertIn("steering_tie_rod", front_names)
        self.assertIn("rear_tie_rod", rear_names)

    def test_reference_solves_all_four_corners(self):
        self.assertEqual(
            {assembly["name"] for assembly in self.result["assemblies"]},
            {"front_left", "front_right", "rear_left", "rear_right"},
        )

    def test_full_tire_force_vector_uses_reaction_signs(self):
        config = expand_config(
            json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        )
        assemblies = {item["name"]: item for item in config["assemblies"]}
        cases = {
            item["name"]: item["force"]
            for item in assemblies["front_right"]["load_cases"]
        }
        # Tire inputs use vehicle axes: +X front, +Y left, +Z upward.
        self.assertEqual(
            cases["case_3_accel_corner"], [48.7544, -406.0447, 281.8825]
        )
        result_by_name = {item["name"]: item for item in self.result["assemblies"]}
        coordinate_force = next(
            item
            for item in result_by_name["front_right"]["load_cases"]
            if item["name"] == "case_3_accel_corner"
        )["external_wrench"][:3]
        self.assertEqual(coordinate_force, [48.7544, 406.0447, -281.8825])

    def test_static_ride_height_case_uses_weight_distribution_and_zero_travel(self):
        expected = {
            "front_right": (159.012, -137.387),
            "front_left": (159.012, -137.387),
            "rear_right": (156.488, -134.863),
            "rear_left": (156.488, -134.863),
        }
        config = expand_config(
            json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        )
        config_by_name = {item["name"]: item for item in config["assemblies"]}
        for assembly in self.result["assemblies"]:
            input_load, coordinate_load = expected[assembly["name"]]
            configured = next(
                item
                for item in config_by_name[assembly["name"]]["load_cases"]
                if item["name"] == "ride_height_static"
            )
            solved = next(
                item
                for item in assembly["load_cases"]
                if item["name"] == "ride_height_static"
            )
            self.assertAlmostEqual(configured["force"][2], input_load)
            self.assertEqual(configured["additional_force_coordinate"], [0.0, 0.0, 21.625])
            self.assertAlmostEqual(solved["external_wrench"][2], coordinate_load)
            self.assertAlmostEqual(
                solved["kinematics"]["shock_travel_from_ride_height"], 0.0, places=7
            )

    def test_sizing_summary_finds_peak_case_and_margin(self):
        by_name = {assembly["name"]: assembly for assembly in self.result["assemblies"]}
        front = by_name["front_right"]
        sizing = {row["member"]: row for row in front["sizing_summary"]}
        self.assertEqual(len(sizing), 7)
        lower_aft = sizing["lower_aft"]
        self.assertEqual(lower_aft["peak_case"], "case_2_braking")
        self.assertAlmostEqual(lower_aft["peak_force"], 1731.76, places=1)
        self.assertEqual(lower_aft["chassis_jmx"], "JMX3")
        self.assertLess(lower_aft["governing_margin"], 0.0)

    def test_chassis_interface_loads_reconstruct_external_wrench(self):
        for assembly in self.result["assemblies"]:
            for chassis, case in zip(assembly["chassis_loads"], assembly["load_cases"]):
                reconstructed = chassis["resultant_force"] + chassis["resultant_moment"]
                for actual, expected in zip(reconstructed, case["external_wrench"]):
                    self.assertAlmostEqual(actual, expected, places=8)
                names = {item["name"] for item in chassis["interfaces"]}
                self.assertIn("rocker_pivot_axis", names)
                self.assertIn("shock_chassis_pickup", names)
                self.assertNotIn("pullrod", names)
                self.assertNotIn("pushrod", names)
                pivot = next(
                    item for item in chassis["interfaces"] if item["name"] == "rocker_pivot_axis"
                )
                axis = case["kinematics"]["geometry"]["rocker"]["pivot_axis"]
                midpoint = [(axis[0][i] + axis[1][i]) / 2.0 for i in range(3)]
                self.assertEqual(pivot["point"], midpoint)

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
        config = expand_config(
            json.loads((ROOT / "examples" / "mk11_reference.json").read_text())
        )
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
        self.assertNotIn("FIXED CHASSIS", html)
        self.assertIn("Member Sizing", html)
        self.assertIn("Governing member loads", html)
        self.assertIn("Chassis Loads", html)
        self.assertIn("ride_height_static", html)
        self.assertNotIn("Maximum resultant envelope", html)
        self.assertNotIn("Interactive chassis hardpoint resultant visualizer", html)
        self.assertNotIn("Corner resultant into chassis", html)
        self.assertNotIn("All listed coordinates are the ride-height reference geometry", html)
        self.assertNotIn("Mirror opposite side", html)
        self.assertNotIn("chassisCanvasHost", html)
        self.assertIn("Chassis force vectors", html)
        self.assertIn('id="chassisForces" type="checkbox"', html)
        self.assertNotIn("drawFixedAnchors", html)
        self.assertNotIn("state.projected.length>120", html)
        self.assertNotIn("__SUSPENSION_DATA__", html)
        self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
