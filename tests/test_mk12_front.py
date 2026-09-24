import json
import unittest
from pathlib import Path

from suspension_linkage_forces import expand_config, solve_config


ROOT = Path(__file__).resolve().parents[1]


class Mk12FrontTests(unittest.TestCase):
    def test_native_front_solves_and_mirrors(self):
        config = expand_config(json.loads((ROOT / "examples/mk12_front.json").read_text()))
        right, left = config["assemblies"][:2]
        for original, mirrored in zip(right["members"], left["members"]):
            for key in ("application", "anchor"):
                x, y, z = original[key]
                self.assertEqual(mirrored[key], [x, -y, z])
        for assembly in solve_config(config)["assemblies"]:
            for case in assembly["load_cases"]:
                self.assertLess(case["max_equilibrium_residual"], 1e-8)
                self.assertLess(case["kinematics"]["max_constraint_residual"], 1e-7)

    def test_latest_rocker_coordinates_and_axis(self):
        config = expand_config(json.loads((ROOT / "examples/mk12_front.json").read_text()))
        source = json.loads((ROOT / "examples/sources/mk12_rocker_updates_2026-09-23.json").read_text())
        for assembly in (config["assemblies"][0], config["assemblies"][2]):
            axle = assembly["name"].split("_")[0]
            offset = 0 if axle == "front" else -61
            rocker = assembly["rocker"]
            rod = next(m for m in assembly["members"] if m.get("role") == "pushrod")
            center = [(a+b)/2 for a,b in zip(*rocker["pivot_axis"])]
            actual = {**rocker, "pivot": center, "rod_lower": rod["application"]}
            for key, (x,y,z) in source["points"][axle].items():
                if key in ("pushrod_pickup", "rod_lower"): continue
                for measured, expected in zip(actual[key], [offset-z/25.4,-x/25.4,-y/25.4]):
                    self.assertAlmostEqual(measured, expected, places=10)
            self.assertEqual(rod["anchor"], rocker["pushrod_pickup"])
            axis = [b-a for a,b in zip(*rocker["pivot_axis"])]
            for key in ("pushrod_pickup", "shock_pickup"):
                arm = [v-p for v,p in zip(rocker[key], center)]
                self.assertAlmostEqual(sum(a*b for a,b in zip(axis, arm)), 0, places=9)

    def test_latest_linkage_tables(self):
        config = expand_config(json.loads((ROOT / "examples/mk12_front.json").read_text()))
        tables = json.loads((ROOT / "examples/sources/mk12_linkage_table_updates_2026-09-23.json").read_text())["points"]
        for assembly in config["assemblies"]:
            axle, side = assembly["name"].split("_")
            for member in assembly["members"]:
                for key, (x,y,z) in zip(("application", "anchor"), tables[axle][member["name"]]):
                    self.assertEqual(member[key], [x, y if side == "right" else -y, -z])

    def test_contact_patch_uses_tire_center_not_steering_axis_intercept(self):
        config = json.loads((ROOT / "examples/mk12_front.json").read_text())
        front = config["assemblies"][0]
        self.assertEqual(front["contact_patch"], [0.0, 22.5, 0.0])
        upper = next(m for m in front["members"] if m["name"] == "upper_fore")
        # Native part +Z is forward; +Y is upward. Preserve this orientation.
        self.assertAlmostEqual(upper["anchor"][0], 7.0)
        self.assertAlmostEqual(upper["anchor"][2], -10.08)


if __name__ == "__main__":
    unittest.main()
