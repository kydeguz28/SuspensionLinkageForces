import unittest
from bolt_schedule import build_bolt_schedule, select_bolt


class BoltScheduleTests(unittest.TestCase):
    def test_shear_plane_count_and_safety_factor(self):
        self.assertEqual(select_bolt(1300, 1)['series'], 'AN4')
        self.assertEqual(select_bolt(1300, 2)['series'], 'AN3')
        self.assertAlmostEqual(select_bolt(1000, 1)['allowable_lbf'], 1288.543861824, places=6)

    def schedule(self, loads):
        members = [{'name': n, 'application': [0,0,0], 'anchor': [1,0,0]} for n in ['upper_fore','upper_aft']]
        config = {'assemblies': [{'name':'front_right','axle':'front','members':members}]}
        cases = [{'name':str(i), 'members':[{'name':m['name'],'force':v} for m,v in zip(members,pair)],
                  'rocker':{'shock_force':0,'pivot_reaction_magnitude':0}} for i,pair in enumerate(loads)]
        return build_bolt_schedule(config, {'assemblies':[{'name':'front_right','load_cases':cases}]})

    def test_shared_joint_cancels_opposing_forces(self):
        row = next(r for r in self.schedule([(100,-100)])['rows'] if r['joint']=='Upper arm to upright (shared)')
        self.assertEqual(row['load_lbf'], 0)

    def test_shared_joint_uses_simultaneous_case_not_independent_peaks(self):
        row = next(r for r in self.schedule([(100,1),(1,100)])['rows'] if r['joint']=='Upper arm to upright (shared)')
        self.assertEqual(row['load_lbf'], 101)


if __name__ == '__main__':
    unittest.main()
