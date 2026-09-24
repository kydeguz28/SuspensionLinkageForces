import json
import math
import unittest
from pathlib import Path

from suspension_linkage_forces import expand_config, solve_config
from linkage_viewer import write_viewer_html
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class RearPackagingTests(unittest.TestCase):
    def test_axis_is_centered_on_packaging_pivot_and_mirrored(self):
        config = expand_config(json.loads((ROOT / "examples/mk12_front.json").read_text()))
        right, left = config["assemblies"][2:]
        axis = right["rocker"]["pivot_axis"]
        center = [(a + b) / 2 for a, b in zip(*axis)]
        for actual, expected in zip(center, [-61 + 66.0972/25.4, 309.3145/25.4, -283.5143/25.4]):
            self.assertAlmostEqual(actual, expected, places=10)
        for a, b in zip(axis, left["rocker"]["pivot_axis"]):
            self.assertEqual(b, [a[0], -a[1], a[2]])
        direction = [b - a for a, b in zip(*axis)]
        for key in ("pushrod_pickup", "shock_pickup"):
            arm = [b - a for a, b in zip(center, right["rocker"][key])]
            self.assertAlmostEqual(sum(a * b for a, b in zip(direction, arm)), 0.0, places=9)

    def test_selected_tie_rod_and_all_motion_cases_converge(self):
        config = json.loads((ROOT / "examples/mk12_front.json").read_text())
        rear = config["assemblies"][2]
        rod = next(m for m in rear["members"] if m["name"] == "rear_tie_rod")
        self.assertEqual(rod["application"], [-64.17, 20.74, -9.26])
        result = solve_config(config)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "viewer.html"
            write_viewer_html(config, result, output)
            self.assertNotIn("Motion solution incomplete.", output.read_text(encoding="utf-8"))

        for assembly in result["assemblies"]:
            for case in assembly["load_cases"]:
                self.assertNotIn("solution_status", case)
                self.assertLess(case["kinematics"]["max_constraint_residual"], 1e-8)

    def test_upper_arm_matches_packaging_ride_height(self):
        config = json.loads((ROOT / "examples/mk12_front.json").read_text())
        rear = config["assemblies"][2]
        members = {m["name"]: m for m in rear["members"]}
        self.assertEqual(rear["contact_patch"], [-61.0, 22.5, 0.0])
        for name, x in [("upper_fore", -53.0), ("upper_aft", -59.0)]:
            for actual, expected in zip(members[name]["anchor"], [x, 12.25, -10.26 if name == "upper_fore" else -9.79]):
                self.assertAlmostEqual(actual, expected, places=10)
        self.assertEqual(members["pushrod"]["anchor"], rear["rocker"]["pushrod_pickup"])
        self.assertEqual(members["pushrod"]["anchor"], [-58.46, 16.39, -12.01])
        self.assertEqual(members["pushrod"]["application"], [-58.4, 19.48, -11.21])
        self.assertLess(math.dist(members["pushrod"]["anchor"], members["pushrod"]["application"]), 3.3)


if __name__ == "__main__":
    unittest.main()
