"""Preliminary AN bolt shear screening using the linkage-sheet allowables."""
import math
from html import escape


def select_bolt(load, planes, strength=70000.0, safety_factor=1.5):
    for number in range(3, 9):
        diameter = number / 16.0  # Workbook nominal shank areas, including AN3.
        allowable = planes * math.pi * diameter**2 / 4 * strength / safety_factor
        if allowable >= load:
            return {'series': f'AN{number}', 'diameter_in': diameter,
                    'allowable_lbf': allowable, 'margin': allowable / load - 1 if load else None}
    return {'series': 'Above AN8', 'diameter_in': None, 'allowable_lbf': None, 'margin': None}


def build_bolt_schedule(config, result):
    hardware = config.get('sizing', {}).get('hardware', {})
    strength = float(hardware.get('bolt_shear_strength_ksi', 70)) * 1000
    fs = float(hardware.get('bolt_shear_safety_factor', 1.5))
    maxima = {}
    configs = {a['name']: a for a in config['assemblies']}
    for solved in result['assemblies']:
        assembly = configs[solved['name']]
        axle = assembly.get('axle', assembly['name'].split('_')[0])
        specs = config.get('sizing', {}).get(axle, {})
        roles = {m['name']: m.get('role') for m in assembly['members']}
        def bore(name, end):
            size = specs.get(name, {}).get(end + '_jmx')
            return hardware.get('bolt_diameter_in', {}).get(size)
        for case in solved['load_cases']:
            geometry = case.get('kinematics', {}).get('geometry', assembly)
            geom = {m['name']: m for m in geometry['members']}
            forces = {m['name']: m['force'] for m in case['members']}
            joints = []
            for name, force in forces.items():
                if roles[name] == 'pushrod':
                    joints += [('Pushrod to bellcrank', abs(force), bore(name, 'chassis'), 'Full rod axial force; confirm bearing bore and tab stack.'),
                               ('A-arm to pushrod', abs(force), bore(name, 'wheel'), 'Full rod force; arm bracket bending and attachment welds require separate checks.')]
                elif name.startswith(('upper_', 'lower_')):
                    joints.append((name.replace('_', ' ').title() + ' to chassis', abs(force), bore(name, 'chassis'), 'Configured inboard rod-end bore.'))
                else:
                    joints += [('Tie rod to chassis', abs(force), bore(name, 'chassis'), 'Configured inboard rod-end bore.'),
                               ('Tie rod to upright', abs(force), bore(name, 'wheel'), 'Configured outboard rod-end bore.')]
            for arm in ('upper', 'lower'):
                names = [n for n in forces if n.startswith(arm + '_')]
                if len(names) != 2:
                    continue
                points = [geom[n]['application'] for n in names]
                if math.dist(*points) > 1e-6:
                    continue
                vectors = []
                for name in names:
                    m = geom[name]; length = math.dist(m['anchor'], m['application'])
                    vectors.append([forces[name] * (b-a)/length for a,b in zip(m['application'],m['anchor'])])
                load = math.sqrt(sum(sum(v[i] for v in vectors)**2 for i in range(3)))
                joints.append((arm.title() + ' arm to upright (shared)', load, None,
                               'Vector sum of both legs in each case; assumes one shared bolt. Bore and physical joint topology unconfirmed.'))
            shock = abs(case['rocker']['shock_force'])
            joints += [('Shock to bellcrank', shock, None, 'Shock-eye bore and mounting stack required.'),
                       ('Shock to chassis', shock, None, 'Shock-eye bore and mounting stack required.'),
                       ('Bellcrank pivot', case['rocker']['pivot_reaction_magnitude'], None,
                        'Force-only lower bound; pivot moment, axial load, bearing spacing and bolt bending must be resolved before selection.')]
            for joint, load, diameter, note in joints:
                key = (axle, joint)
                if key not in maxima or load > maxima[key]['load_lbf']:
                    maxima[key] = {'axle': axle, 'joint': joint, 'load_lbf': load,
                                   'governing_corner': assembly['name'], 'governing_case': case['name'],
                                   'configured_bore_in': diameter, 'note': note,
                                   'provisional_load': case.get('solution_status') == 'fixed_geometry_estimate'}
    rows = []
    for key, row in sorted(maxima.items()):
        for planes, name in ((1, 'single'), (2, 'double')):
            row[name] = select_bolt(row['load_lbf'], planes, strength, fs)
            diameter = row['configured_bore_in']
            row[name + '_existing_bore_margin'] = (planes*math.pi*diameter**2/4*strength/fs/row['load_lbf']-1
                                                      if diameter and row['load_lbf'] else None)
        rows.append(row)
    return {'strength_psi': strength, 'safety_factor': fs, 'rows': rows}


def bolt_schedule_html(schedule):
    rows = []
    for row in schedule['rows']:
        def sizing(kind):
            item = row[kind]
            margin = item['margin']
            return escape(item['series']) + (f' / MS {margin:.2f}' if margin is not None else '')
        diameter = row['configured_bore_in']
        fit = f'AN{round(diameter * 16)} bore / {diameter:.4f} in' if diameter else 'Unconfirmed'
        if diameter:
            margins = [row[k+'_existing_bore_margin'] for k in ('single', 'double')]
            fit += '<br>' + ' / '.join(('passes' if m is not None and m >= 0 else 'fails') for m in margins) + ' (1 / 2 shear)'
        labels = ('Axle', 'Joint', 'Peak load, lbf', 'Single shear', 'Double shear', 'Configured bore', 'Governing case', 'Fit / load-path check')
        rows.append('<tr>' + ''.join('<td data-label="'+label+'">'+v+'</td>' for label,v in zip(labels, (
            escape(row['axle'].title()), escape(row['joint']), f"{row['load_lbf']:.1f}",
            sizing('single'), sizing('double'), fit,
            escape(row['governing_corner'] + ' / ' + row['governing_case']), escape(row['note'])))) + '</tr>')
    html = '''<section aria-labelledby="jointBoltsHeading" id="joint-bolts">
<h2 id="jointBoltsHeading">Joint bolt schedule</h2>
<p>Preliminary shear sizing across all four corners and all load cases. Each axle row covers both sides using the governing side. Diameters are load-only minima, not released part numbers.</p>
<p>Linkage-sheet basis: 70 ksi shear strength, safety factor 1.5, MS = n * pi * d^2 * 70,000 / (4 * 1.5 * load) - 1. One shear plane reproduces the sheet; two assumes a symmetric double-shear joint. AN3 uses the conservative 0.1875-inch area from the sheet. Confirm actual shank tolerance and bore fit.</p>
<div class="sizing-table-wrap"><table class="sizing-table"><caption>AN diameter screening: lengths and joint details pending</caption><thead><tr>
<th>Axle</th><th>Joint</th><th>Peak load, lbf</th><th>Single shear</th><th>Double shear</th><th>Configured bore</th><th>Governing case</th><th>Fit / load-path check</th>
</tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div>
<p><strong>Before ordering:</strong> confirm tab arrangement, bearing/rod-end bore, grip stack and locking method. A larger bolt requires compatible bearings and tabs; do not simply enlarge a rod-end bore. Shared arm pickups assume one common bolt. The ideal two-force linkage model does not resolve arm bending from its pushrod bracket. Pivot force-only sizing does not cover its reaction moment. All rows exclude bolt bending, combined tension, fatigue, tab bearing/tear-out and weld checks.</p>
<p>The old sheet lists AN3-12A, AN4-13A and AN5-14A for its tab stacks; these lengths are not transferred to the new geometry. Use a smooth shank through the shear planes and select the dash length after measuring the full stack. The suffix and locking method remain to be specified.</p>
</section>'''
    return html.replace("70 ksi shear strength, safety factor 1.5", f"{schedule['strength_psi']/1000:g} ksi shear strength, safety factor {schedule['safety_factor']:g}").replace("70,000 / (4 * 1.5", f"{schedule['strength_psi']:,.0f} / (4 * {schedule['safety_factor']:g}")
