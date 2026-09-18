# AN joint-bolt schedule — preliminary

Current geometry and all supplied load cases. Both sides use the larger demand per axle/joint.

70 ksi sheet shear strength; FS 1.5. Single/double shear conditions shown separately. Exact lengths, bore fit, and joint construction remain pending.

| Axle | Joint | Peak lbf | Single shear minimum | Double shear minimum | Configured bore in | Governing case |
|---|---|---:|---|---|---:|---|
| front | A-arm to pushrod / pullrod | 367.2 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Bellcrank pivot | 311.8 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| front | Lower Aft to chassis | 974.2 | AN3 | AN3 | 0.1875 | front_right / case_2_braking |
| front | Lower Fore to chassis | 1040.0 | AN3 | AN3 | 0.25 | front_right / case_2_braking |
| front | Lower arm to upright (shared) | 846.4 | AN3 | AN3 | TBD | front_right / case_3_accel_corner |
| front | Pushrod / pullrod to bellcrank | 367.2 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Shock to bellcrank | 368.2 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| front | Shock to chassis | 368.2 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| front | Tie rod to chassis | 140.1 | AN3 | AN3 | 0.25 | front_right / case_2_braking |
| front | Tie rod to upright | 140.1 | AN3 | AN3 | 0.1875 | front_right / case_2_braking |
| front | Upper Aft to chassis | 345.0 | AN3 | AN3 | 0.1875 | front_right / case_4_brake_corner |
| front | Upper Fore to chassis | 357.2 | AN3 | AN3 | 0.1875 | front_right / case_2_braking |
| front | Upper arm to upright (shared) | 303.3 | AN3 | AN3 | TBD | front_right / case_4_brake_corner |
| rear | A-arm to pushrod / pullrod | 366.7 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Bellcrank pivot | 150.7 | AN3 | AN3 | TBD | rear_right / case_3_accel_corner |
| rear | Lower Aft to chassis | 2185.7 | AN4 | AN3 | 0.3125 | rear_right / case_3_accel_corner |
| rear | Lower Fore to chassis | 1761.7 | AN4 | AN3 | 0.25 | rear_left / case_1_linear_accel |
| rear | Lower arm to upright (shared) | 1381.1 | AN4 | AN3 | TBD | rear_right / case_3_accel_corner |
| rear | Pushrod / pullrod to bellcrank | 366.7 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Shock to bellcrank | 252.4 | AN3 | AN3 | TBD | rear_right / case_3_accel_corner |
| rear | Shock to chassis | 252.4 | AN3 | AN3 | TBD | rear_right / case_3_accel_corner |
| rear | Tie rod to chassis | 1061.4 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Tie rod to upright | 1061.4 | AN3 | AN3 | 0.1875 | rear_right / case_3_accel_corner |
| rear | Upper Aft to chassis | 1009.5 | AN3 | AN3 | 0.1875 | rear_right / case_4_brake_corner |
| rear | Upper Fore to chassis | 635.9 | AN3 | AN3 | 0.1875 | rear_left / case_1_linear_accel |
| rear | Upper arm to upright (shared) | 733.1 | AN3 | AN3 | TBD | rear_left / case_1_linear_accel |

## Limits and fit

These are shear-only diameter screens, not purchase-ready bolt callouts. Keep the existing bore size if it is larger and passes; if it fails, redesign the bearing/tab interface rather than drilling a rod end. Shared outboard arm bolts use the simultaneous vector sum of both legs; physical single-bolt topology must be confirmed. Arm/bracket bending and load redistribution are not resolved by the six two-force-member model. Bellcrank pivot diameter is only a force-based lower bound: its reaction moment and bearing span need separate assessment. Bolt bending, combined axial load, fatigue, tab bearing/tear-out and welds remain unchecked.

The workbook lists AN3-12A, AN4-13A and AN5-14A for the old tab stacks. Do not reuse those dash lengths without measurements. For each joint provide both tab thicknesses (or single-tab detail), spacers, bearing inner-race width/bore, washer stack and locking arrangement.

## Sources

- Project linkage-sheet extract: `tmp_sheet_read/sizing_ranges.json`, Manufacturing Summary and Rod end and plugs. Nominal shear diameter AN3 = 0.1875 in is retained for parity.
- [Airfasco AN3 dimensional table](https://www.airfasco.com/products/AN/AN3-AN20/AN3.php): actual AN3 thread designation and grip/length examples; AN3-12A grip 0.875 in, overall length 1.281 in.
- [FAA AC 43.13-1B, Chapter 7](https://www.faa.gov/sites/faa.gov/files/2023-08/AC_43.13-1B_Ch7.pdf): general bolt installation and grip guidance. This is installation reference material, not vehicle-joint design approval.
