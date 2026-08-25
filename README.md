# Bruin Formula Racing Suspension Linkage Calculator

This is a dependency-free Python version of the core calculation in the supplied
Mk11 suspension-force spreadsheet. It accepts multiple tire load cases and 3D
pickup coordinates, then calculates:

- axial force in the front steering tie rod or rear toe/tie rod;
- axial force in the fore and aft legs of both wishbones;
- pushrod or pullrod force at an A-arm/rocker pickup;
- shock force from the rocker geometry;
- rocker pivot force reaction and reaction moment;
- spring compression and moved pickup coordinates for each load case; and
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
click inspection, collision-aware labels, and an optional chassis-force-vector
overlay for the selected load case. Its
**Member Sizing** tab reports the peak axial force and load case for every corner
and member, automatically selects the lightest configured tube that clears the
tube-margin target, reports the inboard/outboard JMX selections, and separates
tube margin from the overall governing margin. Select a member to expand its
area, inertia, Euler load, applied/allowable loads, equations, safety factors,
and individual margins.

The **Methods** tab traces the derivation from tire wrench through the six-member
upright equilibrium matrix, rocker/shock moment balance, spring-loaded kinematic
iteration, and chassis reactions. Its free-body and rocker diagrams are generated
from the active assembly's exact 3D pickup coordinates and load case, alongside
the numerical workbook-parity checks.

The **Chassis Loads** tab reports the suspension-on-chassis force vector at each
wishbone/tie-rod pickup, the shock chassis pickup, and the equivalent rocker-axis
wrench for the selected load case. Push/pull rods are internal to this free body
and are therefore represented through the rocker and shock reactions rather than
double-counted as chassis interfaces. Select a load case to inspect the force,
local moment, and magnitude at each physical mounting interface. The **Maximum
across all load cases** option independently selects the largest force magnitude
at each hardpoint and reports the governing case and matching vector components.

Sizing uses the configured tube catalog and 4130 properties: 29 Msi elastic
modulus, 70 ksi yield, 95 ksi ultimate, FSy 1.3, and FSu 1.5. The example selects
the minimum-area catalog tube with tube MS ≥ 0.10 across axial yield, axial
ultimate, and Euler buckling. The original per-member dimensions remain in the
result as a comparison. JMX selections follow `Manufacturing
Summary`; their displayed margin is a workbook-derived axial tensile proxy, not
a substitute for the rod-end manufacturer's radial/misalignment rating. A margin
is calculated as `allowable / applied - 1`, so a negative value fails.

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

The Mk11 CAD coordinate convention remains unchanged and uses negative Z upward.
Tire-load inputs deliberately use vehicle force axes instead: +X points toward
the front of the car, +Y toward the left side, and +Z toward the sky. The solver
maps those load components into the CAD basis internally; it does not relabel or
sign-flip any geometry coordinates.

The example solves all four physical corners. Positive-Y front-right and
rear-right geometry uses the supplied CAD rocker and shock coordinates; the
front-left and rear-left geometry is mirrored across the vehicle center plane.
Each corner receives its own tire-force vector from the workbook's `MATLAB Loads`
table, so inside and outside cornering loads are not treated as equal. The
front rocker-axis direction is still assumed parallel to model X; replace its two
axis points when a measured front axis is available.

## Ride height and spring movement

The example defines the initial coordinates as ride height and uses:

- 631 lbf full-car weight;
- 50.4% front / 49.6% rear distribution;
- 86.5 lbf total unsprung weight, provisionally split equally among four corners;
- 600 lbf/in front springs and 450 lbf/in rear springs.

This gives tire loads of 159.012 lbf front and 156.488 lbf rear per corner. After
subtracting 21.625 lbf unsprung weight at each corner, the spring-supported wheel
loads are 137.387 lbf front and 134.863 lbf rear. The rocker geometry converts
those into the ride-height shock preload. Load-case shock travel is then measured
relative to ride height, not relative to the spring's free length.

The first viewer option, **Ride Height Static**, applies only these vertical tire
reactions. The simplified free body also applies the per-corner unsprung weight
downward at the contact patch, so the solved net suspension loads are 137.387 lbf
front and 134.863 lbf rear while the displayed tire arrow remains the full ground
reaction. This case has zero calculated shock travel by definition.

For each load case the nonlinear kinematic solve holds all six two-force member
lengths fixed, treats the upright/wheel as one rigid body, rotates the rocker only
about its fixed pivot axis, and enforces `spring force = ride-height preload +
rate × shock travel`. The moved coordinates are stored below
`load_cases[].kinematics.geometry` in the JSON output and are used by the 3D
viewer. The chassis-side shock pickup remains fixed.

## Engineering assumptions

This is a quasi-static, rigid-body model. All six links are ideal
pin-jointed two-force members; friction, joint offsets, member bending, compliance,
inertial loads, and brake torque are omitted unless added as an external moment.
The rocker is treated as rigid and its shock force is found by moment equilibrium
about the pivot axis. The reported pivot reaction moment is the couple that the
pivot/bearings must react perpendicular to that axis.

If a pushrod mounts partway along a flexible wishbone, this global model gives the
load-path estimate but not local wishbone bending stress. Use a beam/FEA model for
that local detail and validate critical results against CAD, hand calculations,
and measured load cases before sizing safety-critical parts.

The equal four-way unsprung-weight split is an explicit assumption. Replace it
with measured front/rear corner unsprung weights when available. Unsprung weight
is currently removed as a scalar per-corner ride-height load; locating unsprung
component centers of gravity would be required to include their exact moments.
