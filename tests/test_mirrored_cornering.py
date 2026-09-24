"""Both turn directions must give matching left/right sizing envelopes."""
import json
from pathlib import Path
import unittest
from suspension_linkage_forces import solve_config

class MirroredCorneringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((Path(__file__).resolve().parents[1] / 'examples/mk12_front.json').read_text())
        cls.inputs = {a['name']: a for a in cls.config['assemblies']}
        cls.solved = {a['name']: a for a in solve_config(cls.config)['assemblies']}

    def test_mirrored_cases_swap_wheels_and_reverse_lateral(self):
        for axle in ('front', 'rear'):
            for side, other in (('left', 'right'), ('right', 'left')):
                cases = {c['name']: c for c in self.inputs[axle+'_'+side]['load_cases']}
                opposite = {c['name']: c for c in self.inputs[axle+'_'+other]['load_cases']}
                self.assertEqual(len(cases), 7)
                for name in ('case_3_accel_corner', 'case_4_brake_corner'):
                    x,y,z = opposite[name]['force']
                    self.assertEqual(cases[name+'_mirrored']['force'], [x,-y,z])

    def test_solved_forces_and_sizing_are_symmetric(self):
        for axle in ('front', 'rear'):
            right, left = [self.solved[axle+'_'+s] for s in ('right', 'left')]
            lc = {c['name']: c for c in left['load_cases']}
            for c in right['load_cases']:
                name = c['name']
                mirror = name.removesuffix('_mirrored') if name.endswith('_mirrored') else name+'_mirrored' if '_corner' in name else name
                other = lc[mirror]
                for a,b in zip(c['members'],other['members']):
                    self.assertEqual(a['name'],b['name'])
                    self.assertAlmostEqual(a['force'],b['force'],delta=1e-5)
                self.assertAlmostEqual(c['rocker']['shock_force'],other['rocker']['shock_force'],delta=1e-5)
            for a,b in zip(right['sizing_summary'],left['sizing_summary']):
                self.assertEqual(a['member'],b['member'])
                for key in ('peak_force','max_tension_force','max_compression_force'):
                    if key not in a: continue
                    if a[key] is None: self.assertIsNone(b[key])
                    else: self.assertAlmostEqual(a[key],b[key],delta=1e-5)
                for key in ('tube_checks','hardware_checks'):
                    if key in a:
                        self.assertAlmostEqual(min(x['margin'] for x in a[key]),min(x['margin'] for x in b[key]),places=6)
