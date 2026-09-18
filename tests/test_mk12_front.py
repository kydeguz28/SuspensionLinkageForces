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

    def test_contact_patch_uses_tire_center_not_steering_axis_intercept(self):
        config = json.loads((ROOT / "examples/mk12_front.json").read_text())
        front = config["assemblies"][0]
        self.assertEqual(front["contact_patch"], [0.0, 22.5, 0.0])
        upper = next(m for m in front["members"] if m["name"] == "upper_fore")
        # Native part +Z is forward; +Y is upward. Preserve this orientation.
        self.assertAlmostEqual(upper["anchor"][0], 7.0)
        self.assertAlmostEqual(upper["anchor"][2], -9.12498387190005)


if __name__ == "__main__":
    unittest.main()
