"""Select catalog tubes and JMX ends to meet every modeled member margin."""
import copy
import json
from pathlib import Path

from suspension_linkage_forces import expand_config, solve_config, build_sizing_summary
from linkage_viewer import write_viewer_html

ROOT = Path(__file__).resolve().parent


def auto_spec(config, target=0.1):
    config = copy.deepcopy(config)
    config['sizing']['auto_size_tubes'] = True
    config['sizing']['minimum_tube_margin'] = target
    expanded = expand_config(config)
    solved = solve_config(expanded)
    sizing = config['sizing']
    selections = sorted(sizing['jmx_safe_axial_load_lbf'],
                        key=lambda name: sizing['hardware']['bolt_diameter_in'][name])
    for axle in ('front', 'rear'):
        pairs = [(a, s) for a, s in zip(expanded['assemblies'], solved['assemblies'])
                 if a['axle'] == axle]
        for member, spec in sizing[axle].items():
            candidates = []
            for assembly, result in pairs:
                row = next(r for r in build_sizing_summary(assembly, result, sizing)
                           if r['member'] == member)
                candidates.append(row)
            tube = max(candidates, key=lambda r: r['tube_area_in2'])
            spec['tube_od_in'] = tube['tube_od_in']
            spec['tube_id_in'] = round(tube['tube_id_in'], 6)
            for selection in selections:
                spec['chassis_jmx'] = spec['wheel_jmx'] = selection
                rows = [next(r for r in build_sizing_summary(a, s, sizing)
                             if r['member'] == member) for a, s in pairs]
                if all(r['governing_margin'] >= target for r in rows):
                    break
            else:
                raise ValueError(f'No catalog rod end passes {axle}.{member}')
    # Persist selected dimensions rather than relying on display-time sizing.
    sizing['auto_size_tubes'] = False
    sizing['source_note'] = (
        f'Catalog auto-selection with minimum modeled margin {target:g} across both '
        'sides and every load case. Minimum-area catalog tubes and smallest passing '
        'JMX size at both ends. Original material strengths and safety factors retained. '
        'Rod-end checks remain workbook proxies; physical fit and damper ratings unverified.'
    )
    result = solve_config(config)
    for assembly in result['assemblies']:
        for row in assembly['sizing_summary']:
            if row['member'] != 'shock':
                if row['governing_margin'] < target:
                    raise ValueError(f"Final specification fails: {assembly['name']} {row['member']}")
    return config, result


def main():
    path = ROOT / 'examples/mk12_front.json'
    config, result = auto_spec(json.loads(path.read_text()))
    path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    write_viewer_html(expand_config(config), result, ROOT / 'index.html')
    lines = ['# Mk12 automatically selected member specifications', '',
             'Target: MS >= +0.10 for every modeled tube, JMX proxy, bolt shear, rod-end shank, and plug check. Existing strengths and safety factors retained. Both sides and all seven cases checked. Dimensions are inches.', '',
             '| Axle | Member | Tube OD | Wall | Both ends | Bolt bore | Minimum MS | Governing mode |',
             '|---|---|---:|---:|---|---|---:|---|']
    for assembly in result['assemblies']:
        if not assembly['name'].endswith('_right'):
            continue
        for row in assembly['sizing_summary']:
            if row['member'] == 'shock':
                continue
            bore = config['sizing']['hardware']['bolt_diameter_in'][row['chassis_jmx']]
            lines.append(f"| {assembly['name'].split('_')[0]} | {row['member']} | {row['tube_od_in']:.4f} | {row['tube_wall_in']:.3f} | {row['chassis_jmx']} | AN{round(16*bore)} | {row['governing_margin']:.3f} | {row['governing_margin_mode']} |")
    lines += ['', 'Damper ratings are not supplied. Shared upright joints, shock-eye fit, pivot moment/bending, tab and weld strength, and tube-insert fit are not verified by these member checks. Bolt lengths require measured grip stacks. Browser-saved tube/JMX overrides can supersede these defaults.', '']
    (ROOT / 'reports/auto_spec.md').write_text('\n'.join(lines), encoding='utf-8')
    bolt_lines = ['# AN joint-bolt schedule - preliminary', '',
                  'All corners and load cases. Load-only minima use MS >= 0, 70 ksi shear strength and FS 1.5; selected member hardware is checked to MS >= +0.10. Bore/stack confirmation and pivot moment checks remain required.', '',
                  '| Axle | Joint | Peak lbf | Single shear minimum | Double shear minimum | Configured bore in | Governing case |',
                  '|---|---|---:|---|---|---:|---|']
    for row in result['joint_bolt_schedule']['rows']:
        bolt_lines.append(f"| {row['axle']} | {row['joint']} | {row['load_lbf']:.1f} | {row['single']['series']} | {row['double']['series']} | {row['configured_bore_in'] or 'TBD'} | {row['governing_corner']} / {row['governing_case']} |")
    (ROOT / 'reports/joint_bolt_schedule.md').write_text('\n'.join(bolt_lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
