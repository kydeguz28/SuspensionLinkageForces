"""3D suspension linkage and rocker force calculator.

The model treats each listed suspension member as a two-force member.  Positive
member force is tension; negative member force is compression.  Coordinates may
use any consistent length unit.  Forces and moments must use matching units.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable


Vector = list[float]
Matrix = list[list[float]]


def _vec(value: Iterable[float], label: str) -> Vector:
    result = [float(x) for x in value]
    if len(result) != 3:
        raise ValueError(f"{label} must contain exactly three coordinates")
    return result


def add(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("Cannot add vectors of different lengths")
    return [a[i] + b[i] for i in range(len(a))]


def subtract(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("Cannot subtract vectors of different lengths")
    return [a[i] - b[i] for i in range(len(a))]


def scale(value: float, vector: Vector) -> Vector:
    return [value * component for component in vector]


def dot(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError("Cannot dot vectors of different lengths")
    return sum(a[i] * b[i] for i in range(len(a)))


def cross(a: Vector, b: Vector) -> Vector:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def magnitude(vector: Vector) -> float:
    return math.sqrt(dot(vector, vector))


def unit(vector: Vector, label: str) -> Vector:
    length = magnitude(vector)
    if length <= 1e-12:
        raise ValueError(f"{label} has zero length")
    return scale(1.0 / length, vector)


def solve_square(matrix: Matrix, rhs: Vector) -> Vector:
    """Solve a square linear system with scaled partial pivoting."""
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix) or len(rhs) != n:
        raise ValueError("Linear system must be non-empty and square")

    augmented = [matrix[i][:] + [rhs[i]] for i in range(n)]
    row_scale = [max(abs(value) for value in row[:n]) for row in augmented]
    if any(value <= 1e-15 for value in row_scale):
        raise ValueError("Equilibrium matrix is singular (zero equation row)")

    for pivot_col in range(n):
        pivot_row = max(
            range(pivot_col, n),
            key=lambda row: abs(augmented[row][pivot_col]) / row_scale[row],
        )
        if abs(augmented[pivot_row][pivot_col]) <= 1e-12 * row_scale[pivot_row]:
            raise ValueError(
                "Equilibrium matrix is singular or nearly singular; check member geometry"
            )
        augmented[pivot_col], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[pivot_col],
        )
        row_scale[pivot_col], row_scale[pivot_row] = (
            row_scale[pivot_row],
            row_scale[pivot_col],
        )

        pivot = augmented[pivot_col][pivot_col]
        for row in range(pivot_col + 1, n):
            factor = augmented[row][pivot_col] / pivot
            for col in range(pivot_col, n + 1):
                augmented[row][col] -= factor * augmented[pivot_col][col]

    solution = [0.0] * n
    for row in range(n - 1, -1, -1):
        remainder = augmented[row][n] - sum(
            augmented[row][col] * solution[col] for col in range(row + 1, n)
        )
        solution[row] = remainder / augmented[row][row]
    return solution


def matrix_inf_norm(matrix: Matrix) -> float:
    return max(sum(abs(value) for value in row) for row in matrix)


def condition_number_inf(matrix: Matrix) -> float:
    n = len(matrix)
    inverse_columns = [
        solve_square(matrix, [1.0 if row == col else 0.0 for row in range(n)])
        for col in range(n)
    ]
    inverse = [[inverse_columns[col][row] for col in range(n)] for row in range(n)]
    return matrix_inf_norm(matrix) * matrix_inf_norm(inverse)


def mat_vec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum(row[col] * vector[col] for col in range(len(vector))) for row in matrix]


def build_equilibrium_matrix(members: list[dict[str, Any]], reference: Vector) -> tuple[Matrix, list[dict[str, Any]]]:
    if len(members) != 6:
        raise ValueError(
            f"Exactly six two-force members are required for a determinate 3D solve; got {len(members)}"
        )

    columns: list[Vector] = []
    member_geometry: list[dict[str, Any]] = []
    for member in members:
        name = str(member["name"])
        application = _vec(member["application"], f"{name}.application")
        anchor = _vec(member["anchor"], f"{name}.anchor")
        direction = unit(subtract(anchor, application), name)
        moment_arm = subtract(application, reference)
        columns.append(direction + cross(moment_arm, direction))
        member_geometry.append(
            {
                "name": name,
                "application": application,
                "anchor": anchor,
                "direction_application_to_anchor": direction,
                "length": magnitude(subtract(anchor, application)),
                "role": member.get("role", "link"),
            }
        )

    matrix = [[columns[col][row] for col in range(6)] for row in range(6)]
    return matrix, member_geometry


def external_wrench(load_case: dict[str, Any], default_point: Vector, reference: Vector) -> Vector:
    force = _vec(load_case["force"], f"{load_case['name']}.force")
    application = _vec(load_case.get("application", default_point), f"{load_case['name']}.application")
    applied_moment = _vec(load_case.get("moment", [0.0, 0.0, 0.0]), f"{load_case['name']}.moment")
    moment = add(cross(subtract(application, reference), force), applied_moment)
    return force + moment


def solve_rocker(
    rocker: dict[str, Any], pushrod_force: float, arm_pickup: Vector
) -> dict[str, Any]:
    pushrod_pickup = _vec(rocker["pushrod_pickup"], "rocker.pushrod_pickup")
    shock_pickup = _vec(rocker["shock_pickup"], "rocker.shock_pickup")
    shock_chassis = _vec(rocker["shock_chassis_pickup"], "rocker.shock_chassis_pickup")
    axis_points = rocker["pivot_axis"]
    if len(axis_points) != 2:
        raise ValueError("rocker.pivot_axis must contain two points")
    pivot_a = _vec(axis_points[0], "rocker.pivot_axis[0]")
    pivot_b = _vec(axis_points[1], "rocker.pivot_axis[1]")
    axis = unit(subtract(pivot_b, pivot_a), "rocker pivot axis")

    force_on_rocker_from_pushrod = scale(
        pushrod_force,
        unit(subtract(arm_pickup, pushrod_pickup), "rocker-to-arm pushrod"),
    )
    shock_direction = unit(subtract(shock_chassis, shock_pickup), "shock")
    pushrod_axis_moment = dot(
        axis,
        cross(subtract(pushrod_pickup, pivot_a), force_on_rocker_from_pushrod),
    )
    shock_axis_moment_per_force = dot(
        axis, cross(subtract(shock_pickup, pivot_a), shock_direction)
    )
    if abs(shock_axis_moment_per_force) <= 1e-10:
        raise ValueError(
            "Shock line of action has effectively zero moment arm about the rocker axis"
        )
    shock_force = -pushrod_axis_moment / shock_axis_moment_per_force
    force_on_rocker_from_shock = scale(shock_force, shock_direction)
    pivot_reaction = scale(
        -1.0, add(force_on_rocker_from_pushrod, force_on_rocker_from_shock)
    )
    pivot_reaction_moment = scale(
        -1.0,
        add(
            cross(subtract(pushrod_pickup, pivot_a), force_on_rocker_from_pushrod),
            cross(subtract(shock_pickup, pivot_a), force_on_rocker_from_shock),
        ),
    )

    return {
        "shock_force": shock_force,
        "shock_state": "tension" if shock_force >= 0.0 else "compression",
        "shock_length": magnitude(subtract(shock_chassis, shock_pickup)),
        "shock_direction_rocker_to_chassis": shock_direction,
        "pushrod_force_on_rocker": force_on_rocker_from_pushrod,
        "pivot_reaction": pivot_reaction,
        "pivot_reaction_magnitude": magnitude(pivot_reaction),
        "pivot_reaction_moment": pivot_reaction_moment,
        "pushrod_axis_moment": pushrod_axis_moment,
        "shock_axis_moment_per_unit_force": shock_axis_moment_per_force,
    }


def solve_assembly(assembly: dict[str, Any]) -> dict[str, Any]:
    name = str(assembly["name"])
    contact_patch = _vec(assembly["contact_patch"], f"{name}.contact_patch")
    reference = _vec(assembly.get("moment_reference", contact_patch), f"{name}.moment_reference")
    matrix, geometry = build_equilibrium_matrix(assembly["members"], reference)
    condition = condition_number_inf(matrix)
    pushrod_indexes = [
        index for index, item in enumerate(geometry) if item["role"] == "pushrod"
    ]
    if len(pushrod_indexes) != 1:
        raise ValueError(f"{name} must contain exactly one member with role='pushrod'")
    pushrod_index = pushrod_indexes[0]
    configured_rocker_pickup = _vec(
        assembly["rocker"]["pushrod_pickup"], f"{name}.rocker.pushrod_pickup"
    )
    if magnitude(subtract(geometry[pushrod_index]["anchor"], configured_rocker_pickup)) > 1e-6:
        raise ValueError(
            f"{name} pushrod member anchor and rocker pushrod_pickup must be the same point"
        )

    case_results = []
    for load_case in assembly["load_cases"]:
        wrench = external_wrench(load_case, contact_patch, reference)
        rhs = scale(-1.0, wrench)
        forces = solve_square(matrix, rhs)
        residual = subtract(mat_vec(matrix, forces), rhs)
        member_results = []
        for item, force in zip(geometry, forces):
            member_results.append(
                {
                    "name": item["name"],
                    "force": force,
                    "state": "tension" if force >= 0.0 else "compression",
                    "length": item["length"],
                }
            )
        rocker_result = solve_rocker(
            assembly["rocker"],
            forces[pushrod_index],
            geometry[pushrod_index]["application"],
        )
        case_results.append(
            {
                "name": str(load_case["name"]),
                "external_wrench": wrench,
                "members": member_results,
                "rocker": rocker_result,
                "max_equilibrium_residual": max(abs(value) for value in residual),
            }
        )

    return {
        "name": name,
        "coordinate_units": assembly.get("coordinate_units", "in"),
        "force_units": assembly.get("force_units", "lbf"),
        "condition_number_inf": condition,
        "geometry_warning": (
            "Poorly conditioned geometry; small coordinate changes may strongly change forces."
            if condition > 1.0e4
            else None
        ),
        "member_geometry": geometry,
        "load_cases": case_results,
    }


def solve_config(config: dict[str, Any]) -> dict[str, Any]:
    assemblies = config.get("assemblies")
    if not isinstance(assemblies, list) or not assemblies:
        raise ValueError("Configuration must contain a non-empty 'assemblies' list")
    return {
        "model": "3D rigid-body equilibrium with axial two-force members",
        "sign_convention": "positive = tension; negative = compression",
        "assemblies": [solve_assembly(assembly) for assembly in assemblies],
    }


def write_csv(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "assembly",
                "load_case",
                "component",
                "force",
                "state",
                "length",
                "reaction_x",
                "reaction_y",
                "reaction_z",
                "reaction_magnitude",
            ]
        )
        for assembly in result["assemblies"]:
            for case in assembly["load_cases"]:
                for member in case["members"]:
                    writer.writerow(
                        [
                            assembly["name"],
                            case["name"],
                            member["name"],
                            member["force"],
                            member["state"],
                            member["length"],
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                rocker = case["rocker"]
                writer.writerow(
                    [
                        assembly["name"],
                        case["name"],
                        "shock",
                        rocker["shock_force"],
                        rocker["shock_state"],
                        rocker["shock_length"],
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                reaction = rocker["pivot_reaction"]
                writer.writerow(
                    [
                        assembly["name"],
                        case["name"],
                        "rocker_pivot_reaction",
                        "",
                        "reaction",
                        "",
                        reaction[0],
                        reaction[1],
                        reaction[2],
                        rocker["pivot_reaction_magnitude"],
                    ]
                )


def print_summary(result: dict[str, Any]) -> None:
    for assembly in result["assemblies"]:
        units = assembly["force_units"]
        print(f"\n{assembly['name']}  (condition number {assembly['condition_number_inf']:.1f})")
        if assembly["geometry_warning"]:
            print(f"WARNING: {assembly['geometry_warning']}")
        for case in assembly["load_cases"]:
            print(f"  {case['name']}")
            for member in case["members"]:
                print(
                    f"    {member['name']:<22} {member['force']:>11.2f} {units}  {member['state']}"
                )
            rocker = case["rocker"]
            print(
                f"    {'shock':<22} {rocker['shock_force']:>11.2f} {units}  {rocker['shock_state']}"
            )
            print(
                f"    {'rocker pivot reaction':<22} {rocker['pivot_reaction_magnitude']:>11.2f} {units}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate 3D suspension-link and rocker/shock forces from JSON inputs."
    )
    parser.add_argument("config", type=Path, help="Input JSON configuration")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs"), help="Report directory"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.config.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    result = solve_config(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "suspension_forces.json"
    csv_path = args.output_dir / "suspension_forces.csv"
    viewer_path = args.output_dir / "suspension_linkages_3d.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_csv(result, csv_path)
    from linkage_viewer import write_viewer_html

    write_viewer_html(config, result, viewer_path)
    print_summary(result)
    print(f"\nWrote {json_path}, {csv_path}, and {viewer_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
