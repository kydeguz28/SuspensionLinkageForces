# AN joint-bolt schedule — preliminary

Current geometry and all seven load cases, including mirrored acceleration/cornering and braking/cornering (28 corner solutions). Both sides use the larger demand per axle/joint.

70 ksi sheet shear strength; FS 1.5. Single/double shear conditions shown separately. Exact lengths, bore fit, and joint construction remain pending.

| Axle | Joint | Peak lbf | Single shear minimum | Double shear minimum | Configured bore in | Governing case |
|---|---|---:|---|---|---:|---|
| front | A-arm to pushrod | 366.0 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Bellcrank pivot | 301.0 | AN3 | AN3 | TBD | front_left / case_4_brake_corner_mirrored |
| front | Lower Aft to chassis | 737.9 | AN3 | AN3 | 0.1875 | front_right / case_2_braking |
| front | Lower Fore to chassis | 814.9 | AN3 | AN3 | 0.25 | front_left / case_2_braking |
| front | Lower arm to upright (shared) | 852.2 | AN3 | AN3 | TBD | front_left / case_3_accel_corner_mirrored |
| front | Pushrod to bellcrank | 366.0 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Shock to bellcrank | 340.2 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| front | Shock to chassis | 340.2 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| front | Tie rod to chassis | 143.8 | AN3 | AN3 | 0.25 | front_right / case_2_braking |
| front | Tie rod to upright | 143.8 | AN3 | AN3 | 0.1875 | front_right / case_2_braking |
| front | Upper Aft to chassis | 307.5 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Upper Fore to chassis | 294.3 | AN3 | AN3 | 0.1875 | front_left / case_2_braking |
| front | Upper arm to upright (shared) | 294.2 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| rear | A-arm to pushrod | 1123.6 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Bellcrank pivot | 536.4 | AN3 | AN3 | TBD | rear_right / case_3_accel_corner |
| rear | Lower Aft to chassis | 1523.4 | AN4 | AN3 | 0.3125 | rear_right / case_4_brake_corner |
| rear | Lower Fore to chassis | 1291.7 | AN4 | AN3 | 0.25 | rear_right / case_1_linear_accel |
| rear | Lower arm to upright (shared) | 1067.0 | AN3 | AN3 | TBD | rear_left / case_3_accel_corner_mirrored |
| rear | Pushrod to bellcrank | 1123.6 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Shock to bellcrank | 595.7 | AN3 | AN3 | TBD | rear_left / case_3_accel_corner_mirrored |
| rear | Shock to chassis | 595.7 | AN3 | AN3 | TBD | rear_left / case_3_accel_corner_mirrored |
| rear | Tie rod to chassis | 134.2 | AN3 | AN3 | 0.1875 | rear_right / case_1_linear_accel |
| rear | Tie rod to upright | 134.2 | AN3 | AN3 | 0.1875 | rear_right / case_1_linear_accel |
| rear | Upper Aft to chassis | 1553.1 | AN4 | AN3 | 0.1875 | rear_right / case_4_brake_corner |
| rear | Upper Fore to chassis | 410.3 | AN3 | AN3 | 0.1875 | rear_left / case_2_braking |
| rear | Upper arm to upright (shared) | 1262.4 | AN3 | AN3 | TBD | rear_right / case_4_brake_corner |

## Limits and fit

These are shear-only diameter screens, not purchase-ready bolt callouts. Keep the existing bore size if it is larger and passes; if it fails, redesign the bearing/tab interface rather than drilling a rod end. Shared outboard arm bolts use the simultaneous vector sum of both legs; physical single-bolt topology must be confirmed. Arm/bracket bending and load redistribution are not resolved by the six two-force-member model. Bellcrank pivot diameter is only a force-based lower bound: its reaction moment and bearing span need separate assessment. Bolt bending, combined axial load, fatigue, tab bearing/tear-out and welds remain unchecked.

The workbook lists AN3-12A, AN4-13A and AN5-14A for the old tab stacks. Do not reuse those dash lengths without measurements. For each joint provide both tab thicknesses (or single-tab detail), spacers, bearing inner-race width/bore, washer stack and locking arrangement.

## Sources

- Project linkage-sheet extract: `tmp_sheet_read/sizing_ranges.json`, Manufacturing Summary and Rod end and plugs. Nominal shear diameter AN3 = 0.1875 in is retained for parity.
- [Airfasco AN3 dimensional table](https://www.airfasco.com/products/AN/AN3-AN20/AN3.php): actual AN3 thread designation and grip/length examples; AN3-12A grip 0.875 in, overall length 1.281 in.
- [FAA AC 43.13-1B, Chapter 7](https://www.faa.gov/sites/faa.gov/files/2023-08/AC_43.13-1B_Ch7.pdf): general bolt installation and grip guidance. This is installation reference material, not vehicle-joint design approval.
