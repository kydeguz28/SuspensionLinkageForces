# Mk12 minimum-weight tube candidates

Minimum tube OD: 0.375 in.

Objective: minimize tube weight at each fixed member length and common material density. Weight is proportional to A = pi/4 * (OD^2 - ID^2). Actual listed OD/ID pairs are used; nominal wall labels may be rounded. Supplier references identify catalog rows, not a selected purchase length.

Target: MS >= +0.10 for every modeled tube, JMX proxy, bolt shear, rod-end shank, and plug check. Existing strengths and safety factors retained. Both sides and all seven cases checked. Dimensions are inches.

| Axle | Member | Tube OD | Wall | ID | McMaster reference | Weight reduction vs previous tube | Both ends | Bolt bore | Minimum MS | Governing mode |
|---|---|---:|---:|---:|---|---:|---|---|---:|---|
| front | steering_tie_rod | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX3 | AN3 | 7.286 | chassis JMX3 rod end tensile |
| front | lower_fore | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX4 | AN4 | 0.380 | tube axial yield |
| front | lower_aft | 0.5000 | 0.028 | 0.4440 | [89955K479](https://www.mcmaster.com/89955K479/) | 30.6% | JMX3 | AN3 | 0.169 | chassis JMX3 rod end tensile |
| front | upper_fore | 0.3750 | 0.035 | 0.3050 | [89955K149](https://www.mcmaster.com/89955K149/) | 37.5% | JMX3 | AN3 | 0.232 | tube Euler buckling |
| front | upper_aft | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX3 | AN3 | 1.151 | tube Euler buckling |
| front | pushrod | 0.5000 | 0.028 | 0.4440 | [89955K479](https://www.mcmaster.com/89955K479/) | 30.6% | JMX3 | AN3 | 0.677 | tube Euler buckling |
| rear | rear_tie_rod | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX3 | AN3 | 8.284 | chassis JMX3 rod end tensile |
| rear | lower_fore | 0.5000 | 0.028 | 0.4440 | [89955K479](https://www.mcmaster.com/89955K479/) | 30.6% | JMX4 | AN4 | 0.439 | tube Euler buckling |
| rear | lower_aft | 0.5000 | 0.028 | 0.4440 | [89955K479](https://www.mcmaster.com/89955K479/) | 30.6% | JMX4 | AN4 | 0.323 | chassis JMX4 rod end tensile |
| rear | upper_fore | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX3 | AN3 | 1.400 | chassis JMX3 rod end tensile |
| rear | upper_aft | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX4 | AN4 | 0.116 | tube axial yield |
| rear | pushrod | 0.3750 | 0.028 | 0.3190 | [89955K469](https://www.mcmaster.com/89955K469/) | 49.0% | JMX4 | AN4 | 0.228 | tube axial yield |

Damper ratings are not supplied. Shared upright joints, shock-eye fit, pivot moment/bending, tab and weld strength, and tube-insert fit are not verified by these member checks. Bolt lengths require measured grip stacks. Browser-saved tube/JMX overrides can supersede these defaults.
