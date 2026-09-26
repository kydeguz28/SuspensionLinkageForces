import copy
import json
import unittest
from pathlib import Path
from auto_spec import auto_spec


class AutoSpecTests(unittest.TestCase):
    def test_all_corners_all_member_checks_pass_without_changing_loads(self):
        config = json.loads((Path(__file__).resolve().parents[1] / 'examples/mk12_front.json').read_text())
        original = copy.deepcopy(config)
        selected, result = auto_spec(config)
        self.assertEqual(config, original)
        self.assertEqual(selected['assemblies'], original['assemblies'])
        self.assertEqual(selected['sizing']['material'], original['sizing']['material'])
        self.assertEqual(selected['sizing']['hardware'], original['sizing']['hardware'])
        self.assertEqual(len(result['assemblies']), 4)
        # A larger thin-wall tube must beat a smaller heavy-wall tube by weight.
        rear = selected['sizing']['rear']['lower_fore']
        self.assertEqual(rear['tube_od_in'], 0.5)
        self.assertEqual(rear['tube_id_in'], 0.444)
        self.assertLess(rear['tube_od_in']**2 - rear['tube_id_in']**2,
                        0.4375**2 - 0.34**2)

        for assembly in result['assemblies']:
            self.assertEqual(len(assembly['load_cases']), 7)
            for row in assembly['sizing_summary']:
                if row['member'] == 'shock':
                    self.assertIsNone(row['governing_margin'])
                    continue
                self.assertGreaterEqual(row['tube_od_in'], 0.375)
                for kind in ('tube_checks', 'jmx_checks', 'hardware_checks'):
                    self.assertTrue(row[kind])
                    for check in row[kind]:
                        self.assertGreaterEqual(check['margin'], 0.1)

    def test_impossible_catalog_target_fails(self):
        config = json.loads((Path(__file__).resolve().parents[1] / 'examples/mk12_front.json').read_text())
        with self.assertRaises(ValueError):
            auto_spec(config, target=1e6)
