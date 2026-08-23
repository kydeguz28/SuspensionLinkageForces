# Suspension Linkage Forces

This is a dependency-free Python version of the core calculation in the supplied
Mk11 suspension-force spreadsheet. It accepts multiple tire load cases and 3D
pickup coordinates, then calculates:

- axial force in the front steering tie rod or rear toe/tie rod;
- axial force in the fore and aft legs of both wishbones;
- pushrod or pullrod force at an A-arm/rocker pickup;
- shock force from the rocker geometry;
- rocker pivot force reaction and reaction moment; and
- a numerical conditioning warning for weak or nearly singular geometry.

Positive axial force means **tension**. Negative axial force means
**compression**.

## Run it

Python 3.10 or newer is sufficient; there are no third-party dependencies.

```powershell
python suspension_linkage_forces.py examples/mk11_reference.json --output-dir outputs
```

The command prints a summary and writes `suspension_forces.json`,
`suspension_forces.csv`, and a self-contained interactive
`suspension_linkages_3d.html` viewer. Open the HTML file in any modern browser;
it does not require a server or internet connection.

The viewer supports drag-to-orbit, Shift-drag panning, wheel zoom, assembly and
load-case selection, component or force coloring, joint/member labels, hover and
click inspection, and an optional translucent mirror of the opposite side.

Run the verification suite with:

```powershell
python -m unittest discover -s tests -v
```

## Input model

Each assembly contains exactly six two-force members:

1. front steering tie rod or rear toe/tie rod;
2. lower wishbone fore leg;
3. lower wishbone aft leg;
4. upper wishbone fore leg;
5. upper wishbone aft leg; and
6. pushrod or pullrod.

For each member:

- `application` is the point where the member acts on the moving suspension;
- `anchor` is its chassis or rocker pickup; and
- the push/pull rod must have `"role": "pushrod"`.

The pushrod `application` can be the actual A-arm vertex. Its `anchor` must equal
`rocker.pushrod_pickup`. The rocker also needs two points defining its pivot axis,
the shock pickup on the rocker, and the shock pickup on the chassis.

Each load case supplies `force`, the force applied by the tire/ground **to the
suspension**. It acts at `contact_patch` unless that case provides a different
`application`. An optional free `moment` may also be supplied. Coordinates can be
in inches or millimetres, but every coordinate in one assembly must use the same
unit. Moments must use force × coordinate units (for example lbf-in).

The Mk11 coordinate convention uses negative Z upward. Consequently, an upward
vertical tire force must be entered as a negative Z force component.

The example uses wishbone coordinates and translated load cases from the Mk11
workbook. Its rocker axis and shock points are deliberately illustrative because
those packaging coordinates were not present in the workbook; replace them with
CAD coordinates before using the shock results.

## Engineering assumptions

This is a static, small-deflection, rigid-body model. All six links are ideal
pin-jointed two-force members; friction, joint offsets, member bending, compliance,
inertial loads, and brake torque are omitted unless added as an external moment.
The rocker is treated as rigid and its shock force is found by moment equilibrium
about the pivot axis. The reported pivot reaction moment is the couple that the
pivot/bearings must react perpendicular to that axis.

If a pushrod mounts partway along a flexible wishbone, this global model gives the
load-path estimate but not local wishbone bending stress. Use a beam/FEA model for
that local detail and validate critical results against CAD, hand calculations,
and measured load cases before sizing safety-critical parts.
