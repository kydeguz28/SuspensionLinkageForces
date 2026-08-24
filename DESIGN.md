# Design System

## Direction

The viewer behaves like a clean optical inspection bench: cool aluminum surfaces, precise dark linework, and restrained safety colors. The 3D mechanism owns the viewport; controls remain compact and subordinate.

## Color

- Canvas: `#edf0f1`; chrome: `#dfe4e6`; ink: `#172026`; muted ink: `#52616a`.
- Selection: safety orange `#e56a2f`.
- Tension: vermilion `#c84d35`; compression: engineering blue `#266d93`.
- Component colors are categorical and must remain distinguishable without relying on labels alone.

## Typography

Use Bahnschrift or the closest native DIN-like UI face for controls and headings. Monospace is reserved for coordinates, forces, and units.

## Components

Controls are squared, tactile instruments with small radii and clear focus rings. Avoid dashboard-card repetition. Panels use one border or one offset shadow, never both.

## Visualization

- Links are cylinders/lines with visible joint nodes and depth sorting.
- A ground datum, axes, and `−Z up` note make the coordinate convention explicit.
- Hover and click reveal endpoints, length, force, and state.
- Shock chassis pickups use a clean pickup node and do not influence camera reframing between load cases.
- Chassis force vectors are an optional, off-by-default overlay in the 3D geometry view.
- Mirrored geometry is visibly translucent and labeled illustrative.
- Force color and thickness encode state and magnitude; component mode provides structural identification.

## Motion and Interaction

Drag or arrow keys orbit, wheel or `+`/`−` zoom, Shift-drag pans, and `R` resets. Motion must respect reduced-motion preferences. Geometry stays visible before interaction.

## Responsive Behavior

Desktop uses a narrow control rail and inspection rail around the viewport. Small screens place controls above the viewport and condense inspection details below it without covering the mechanism.
