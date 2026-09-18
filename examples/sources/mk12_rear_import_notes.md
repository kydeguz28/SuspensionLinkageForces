# Current rear coordinates

Rear wishbones use 3D HARDPOINTS INBOARD BRAKES from the kinematics part.
The rearward tie rod uses ANTI + INBOARD BRAKES as explicitly selected by the user.
The pushrod arm pickup is source (-19.477494,11.209784,-2.598527), confirmed
by the user assembly screenshots. The rocker-side joint is the later source
(-16.654995,12.099762,-2.529146). These supersede the packaging-part rod points.

The newer user screenshots supersede the packaging part's rocker pivot,
shock chassis mount, shock-to-rocker joint and rocker-to-pushrod joint.
Their mapping is (model X,Y,Z)=(-61-source Z,-source X,-source Y), in inches,
using the user-supplied axis orientation and 61-inch axle offset. This makes
negative source X point outward on model right, source Y upward and negative
source Z forward. Other source files retain their separately established
conversions: kinematics (z-61,x,-y), old packaging (x-61,-y,z).

The new rocker axis is inferred perpendicular to the plane through its pivot
and two attachment joints. This assumes a planar bellcrank; it is not a newly
measured axis. The solver endpoints lie one inch each side of the pivot along
that normal. The previous packaging-axis reference has been removed from the
active coordinate table. The CSV lists all current source and model points;
the TSV exports preserve the original CAD geometry for traceability.

All 20 spring-loaded cases converge with these corrected points. No case uses
a fixed-geometry fallback and the prior incomplete-motion banner is absent.
The earlier candidate JSON is historical, not the active configuration.
The active input remains ../mk12_front.json, containing both front and rear.

The force solver retains its rigid-upright treatment of the rod application
point. Updating the coordinates does not change that modeling assumption.

The corrected pushrod length is 2.9602998444 in and the rocker rod-arm radius
is 4.5749993346 in. All 20 motion cases still converge after the joint correction.
