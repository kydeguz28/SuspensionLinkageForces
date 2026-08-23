# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Vehicle-dynamics and suspension-design engineers working from CAD pickup points and tire load cases. They need to inspect a linkage model, catch geometry mistakes, and understand the load path before sizing parts.

## Product Purpose

Convert 3D suspension geometry and tire forces into auditable axial linkage, shock, and rocker reactions. Success means the geometry, sign convention, assumptions, and force path remain visible and technically reviewable.

## Positioning

The calculator keeps numerical equilibrium results and a navigable 3D representation driven from the same JSON source of truth.

## Operating Context

Inputs come from CAD coordinates and tire load cases. Outputs are reviewed in a terminal, CSV/JSON reports, and an interactive local HTML viewer.

## Capabilities and Constraints

- Dependency-free Python 3.10+ solver and viewer generator.
- Six ideal two-force suspension members per assembly.
- Rigid-rocker moment equilibrium about a defined pivot axis.
- Static, small-deflection model; local wishbone bending requires beam analysis or FEA.
- The supplied workbook does not contain production rocker/shock packaging coordinates.

## Evidence on Hand

- `examples/mk11_reference.json` contains translated Mk11 geometry and load cases.
- `tests/test_suspension_linkage_forces.py` verifies equilibrium and sign consistency.
- Rocker and shock coordinates in the example are explicitly illustrative.

## Product Principles

- One geometry source drives calculation and visualization.
- Engineering meaning takes priority over decoration.
- Never hide illustrative or weakly conditioned data.
- Make force direction, units, and assumptions explicit.
