# Design System

## Direction

Extend the BFR optical inspection bench into a dedicated motion rig: the moving linkage and the measured trace share one continuous working surface, with no dashboard-card grid.

## Color and Type

- Canvas `#edf0f1`, paper `#f7f8f8`, chrome `#dfe4e6`, ink `#172026`, muted `#52616a`.
- Safety orange `#e56a2f` marks the active travel pose; engineering blue `#266d93` is shock compression; vermilion `#c84d35` is instantaneous motion ratio.
- Bahnschrift/DIN-like system type for controls and headings; Consolas only for coordinates and measured values.

## Composition

The first viewport is a motion bench: compact travel controls at the top, exact 3D packaging at left, the compression trace at right, and one shared full-width travel scrubber joining both. On narrow screens these stack in the same order.

A linear physical-stroke gauge sits between calculated pose readouts and the motion bench. It maps the real extended and bottom-out node-to-node lengths without turning the surface into a dashboard, and uses vermilion only when a solved pose exceeds the shock envelope.

## Interaction

Dragging or arrow keys orbits the mechanism. The shared travel control updates the mechanism, plot cursor, and numerical readout together. Reduced-motion users receive immediate state changes without interpolation.
