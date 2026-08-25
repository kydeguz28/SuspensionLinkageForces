"""3D suspension linkage and rocker force calculator.

The model treats each listed suspension member as a two-force member.  Positive
member force is tension; negative member force is compression.  Coordinates may
use any consistent length unit.  Forces and moments must use matching units.
"""

from __future__ import annotations

import argparse
import copy
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


def rotate_about_axis(point: Vector, axis_a: Vector, axis_b: Vector, angle: float) -> Vector:
    """Rotate a point about an arbitrary fixed axis using Rodrigues' formula."""
    axis = unit(subtract(axis_b, axis_a), "rotation axis")
    relative = subtract(point, axis_a)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    rotated = add(
        add(scale(cosine, relative), scale(sine, cross(axis, relative))),
        scale((1.0 - cosine) * dot(axis, relative), axis),
    )
    return add(axis_a, rotated)


def rotate_by_vector(point: Vector, rotation: Vector) -> Vector:
    """Apply a rotation-vector (axis times radians) about the origin."""
    angle = magnitude(rotation)
    if angle <= 1e-14:
        return point[:]
    axis = scale(1.0 / angle, rotation)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return add(
        add(scale(cosine, point), scale(sine, cross(axis, point))),
        scale((1.0 - cosine) * dot(axis, point), axis),
    )


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


def external_wrench(
    load_case: dict[str, Any],
    default_point: Vector,
    reference: Vector,
    tire_force_to_coordinate_signs: Iterable[float] = (1.0, 1.0, 1.0),
) -> Vector:
    input_force = _vec(load_case["force"], f"{load_case['name']}.force")
    if load_case.get("force_in_coordinate_axes"):
        force = input_force
    else:
        signs = _vec(tire_force_to_coordinate_signs, "tire_force_to_coordinate_signs")
        force = [input_force[index] * signs[index] for index in range(3)]
    additional_force = _vec(
        load_case.get("additional_force_coordinate", [0.0, 0.0, 0.0]),
        f"{load_case['name']}.additional_force_coordinate",
    )
    force = add(force, additional_force)
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


def solve_case(assembly: dict[str, Any], load_case: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    """Solve one load case at the geometry currently stored in assembly."""
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

    wrench = external_wrench(
        load_case,
        contact_patch,
        reference,
        assembly.get("tire_force_to_coordinate_signs", [1.0, 1.0, 1.0]),
    )
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
    result = {
        "name": str(load_case["name"]),
        "external_wrench": wrench,
        "members": member_results,
        "rocker": rocker_result,
        "max_equilibrium_residual": max(abs(value) for value in residual),
    }
    return result, geometry, condition


def displaced_assembly(assembly: dict[str, Any], state: Vector) -> dict[str, Any]:
    """Move the rigid upright/wheel and rotate the rocker about its fixed axis."""
    translation = state[:3]
    rotation = state[3:6]
    rocker_angle = state[6]
    contact_reference = _vec(assembly["contact_patch"], "contact_patch")

    def move_upright(point: Iterable[float]) -> Vector:
        relative = subtract(_vec(point, "upright point"), contact_reference)
        return add(contact_reference, add(rotate_by_vector(relative, rotation), translation))

    moved = copy.deepcopy(assembly)
    moved["contact_patch"] = move_upright(assembly["contact_patch"])
    axis_a = _vec(assembly["rocker"]["pivot_axis"][0], "rocker.pivot_axis[0]")
    axis_b = _vec(assembly["rocker"]["pivot_axis"][1], "rocker.pivot_axis[1]")
    moved_pushrod = rotate_about_axis(
        _vec(assembly["rocker"]["pushrod_pickup"], "rocker.pushrod_pickup"),
        axis_a,
        axis_b,
        rocker_angle,
    )
    moved_shock = rotate_about_axis(
        _vec(assembly["rocker"]["shock_pickup"], "rocker.shock_pickup"),
        axis_a,
        axis_b,
        rocker_angle,
    )
    moved["rocker"]["pushrod_pickup"] = moved_pushrod
    moved["rocker"]["shock_pickup"] = moved_shock
    for original, member in zip(assembly["members"], moved["members"]):
        member["application"] = move_upright(original["application"])
        if original.get("role") == "pushrod":
            member["anchor"] = moved_pushrod
    return moved


def solve_moving_case(
    assembly: dict[str, Any],
    load_case: dict[str, Any],
    spring_rate: float,
    ride_shock_compression: float,
) -> dict[str, Any]:
    """Find the rigid suspension pose compatible with link lengths and spring force."""
    reference_lengths = [
        magnitude(subtract(_vec(item["anchor"], "anchor"), _vec(item["application"], "application")))
        for item in assembly["members"]
    ]
    shock_chassis = _vec(assembly["rocker"]["shock_chassis_pickup"], "shock chassis")
    reference_shock_length = magnitude(
        subtract(shock_chassis, _vec(assembly["rocker"]["shock_pickup"], "shock pickup"))
    )

    def evaluate(state: Vector) -> tuple[Vector, dict[str, Any], dict[str, Any]]:
        moved = displaced_assembly(assembly, state)
        moved_case = copy.deepcopy(load_case)
        if "application" in load_case:
            # Explicit tire-force application points are attached to the upright.
            base_cp = _vec(assembly["contact_patch"], "contact patch")
            relative = subtract(_vec(load_case["application"], "load application"), base_cp)
            moved_case["application"] = add(
                _vec(moved["contact_patch"], "moved contact patch"),
                rotate_by_vector(relative, state[3:6]),
            )
        solved, geometry, _ = solve_case(moved, moved_case)
        link_residuals = [
            item["length"] - reference_lengths[index]
            for index, item in enumerate(geometry)
        ]
        current_shock_length = solved["rocker"]["shock_length"]
        shock_compression = reference_shock_length - current_shock_length
        spring_compression_force = ride_shock_compression + spring_rate * shock_compression
        # Negative solver force denotes compression. Divide by rate so all seven
        # residuals are expressed as equivalent inches.
        spring_residual = (
            -solved["rocker"]["shock_force"] - spring_compression_force
        ) / spring_rate
        solved["kinematics"] = {
            "upright_translation": state[:3],
            "upright_rotation_vector_rad": state[3:6],
            "rocker_rotation_rad": state[6],
            "shock_travel_from_ride_height": shock_compression,
            "spring_force": spring_compression_force,
            "geometry": {
                "contact_patch": moved["contact_patch"],
                "members": moved["members"],
                "rocker": moved["rocker"],
            },
        }
        return link_residuals + [spring_residual], solved, moved

    state = [0.0] * 7
    solved: dict[str, Any] | None = None
    for iteration in range(40):
        residual, solved, _ = evaluate(state)
        norm = max(abs(value) for value in residual)
        if norm < 1e-8:
            solved["kinematics"]["iterations"] = iteration
            solved["kinematics"]["max_constraint_residual"] = norm
            return solved
        jacobian = [[0.0] * 7 for _ in range(7)]
        for column in range(7):
            step = 1e-5
            trial = state[:]
            trial[column] += step
            trial_residual, _, _ = evaluate(trial)
            for row in range(7):
                jacobian[row][column] = (trial_residual[row] - residual[row]) / step
        delta = solve_square(jacobian, scale(-1.0, residual))
        accepted = False
        factor = 1.0
        for _ in range(12):
            trial = add(state, scale(factor, delta))
            try:
                trial_residual, _, _ = evaluate(trial)
            except ValueError:
                factor *= 0.5
                continue
            if max(abs(value) for value in trial_residual) < norm:
                state = trial
                accepted = True
                break
            factor *= 0.5
        if not accepted:
            raise ValueError(f"{assembly['name']} {load_case['name']} kinematics did not converge")
    raise ValueError(f"{assembly['name']} {load_case['name']} kinematics exceeded 40 iterations")


def solve_assembly(
    assembly: dict[str, Any], ride_height_wheel_load: float | None = None
) -> dict[str, Any]:
    name = str(assembly["name"])
    initial_case_results = [solve_case(assembly, case)[0] for case in assembly["load_cases"]]
    _, geometry, condition = solve_case(assembly, assembly["load_cases"][0])
    case_results = initial_case_results
    ride_height_result = None
    spring_rate = assembly.get("spring_rate_lbf_per_in")
    if ride_height_wheel_load is not None and spring_rate is not None:
        spring_rate = float(spring_rate)
        if spring_rate <= 0.0:
            raise ValueError(f"{name}.spring_rate_lbf_per_in must be positive")
        ride_case = {
            "name": "ride_height_reference",
            "force": [0.0, 0.0, -float(ride_height_wheel_load)],
            "force_in_coordinate_axes": True,
        }
        ride_height_result, _, _ = solve_case(assembly, ride_case)
        ride_compression = -ride_height_result["rocker"]["shock_force"]
        if ride_compression <= 0.0:
            raise ValueError(f"{name} ride-height load does not compress the shock")
        case_results = [
            solve_moving_case(assembly, case, spring_rate, ride_compression)
            for case in assembly["load_cases"]
        ]

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
        "ride_height_reference": (
            {
                "wheel_load_supported_by_spring": ride_height_wheel_load,
                "shock_force": ride_height_result["rocker"]["shock_force"],
                "shock_compression_force": -ride_height_result["rocker"]["shock_force"],
                "spring_rate": spring_rate,
                "spring_compression_from_free_length": -ride_height_result["rocker"]["shock_force"] / spring_rate,
            }
            if ride_height_result is not None
            else None
        ),
        "load_cases": case_results,
    }


def expand_config(config: dict[str, Any]) -> dict[str, Any]:
    """Expand compact mirror_geometry_of assembly definitions."""
    expanded = copy.deepcopy(config)
    source_assemblies = config.get("assemblies", [])
    full_by_name = {
        str(item["name"]): copy.deepcopy(item)
        for item in source_assemblies
        if "mirror_geometry_of" not in item
    }
    resolved: list[dict[str, Any]] = []
    for specification in source_assemblies:
        source_name = specification.get("mirror_geometry_of")
        if source_name is None:
            resolved.append(copy.deepcopy(specification))
            continue
        if str(source_name) not in full_by_name:
            raise ValueError(
                f"{specification.get('name', 'assembly')} mirrors unknown assembly {source_name}"
            )
        mirrored = copy.deepcopy(full_by_name[str(source_name)])
        for key, value in specification.items():
            if key != "mirror_geometry_of":
                mirrored[key] = copy.deepcopy(value)

        def mirror_y(point: Iterable[float]) -> Vector:
            vector = _vec(point, "mirrored coordinate")
            return [vector[0], -vector[1], vector[2]]

        mirrored["contact_patch"] = mirror_y(mirrored["contact_patch"])
        if "moment_reference" in mirrored:
            mirrored["moment_reference"] = mirror_y(mirrored["moment_reference"])
        for member in mirrored["members"]:
            member["application"] = mirror_y(member["application"])
            member["anchor"] = mirror_y(member["anchor"])
        rocker = mirrored["rocker"]
        rocker["pivot_axis"] = [mirror_y(point) for point in rocker["pivot_axis"]]
        rocker["pushrod_pickup"] = mirror_y(rocker["pushrod_pickup"])
        rocker["shock_pickup"] = mirror_y(rocker["shock_pickup"])
        rocker["shock_chassis_pickup"] = mirror_y(rocker["shock_chassis_pickup"])
        resolved.append(mirrored)
    expanded["assemblies"] = resolved
    return expanded


def build_chassis_load_summary(
    assembly: dict[str, Any], solved: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return the suspension-on-chassis load at every physical chassis interface."""
    roles = {str(item["name"]): item.get("role", "link") for item in assembly["members"]}
    summaries: list[dict[str, Any]] = []
    for case in solved["load_cases"]:
        moved = case.get("kinematics", {}).get("geometry", assembly)
        reference = _vec(
            moved.get("moment_reference", moved["contact_patch"]),
            f"{assembly['name']}.moment_reference",
        )
        moved_members = {str(item["name"]): item for item in moved["members"]}
        interfaces: list[dict[str, Any]] = []

        # The push/pull rod terminates at the rocker and is internal to the
        # suspension assembly. Its load reaches the chassis through the rocker
        # pivot and shock mounts, so it must not be counted a second time here.
        for member in case["members"]:
            name = str(member["name"])
            if roles.get(name) == "pushrod":
                continue
            geometry = moved_members[name]
            point = _vec(geometry["anchor"], f"{name}.anchor")
            direction = unit(
                subtract(geometry["anchor"], geometry["application"]), name
            )
            force = scale(-float(member["force"]), direction)
            interfaces.append(
                {
                    "name": name,
                    "type": "two_force_member",
                    "point": point,
                    "force": force,
                    "force_magnitude": magnitude(force),
                    "local_moment": [0.0, 0.0, 0.0],
                }
            )

        rocker_geometry = moved["rocker"]
        pivot_points = [
            _vec(point, "rocker.pivot_axis") for point in rocker_geometry["pivot_axis"]
        ]
        # Report the pivot reaction at the physical middle of the rocker axis.
        # Translate the equivalent reaction moment from solver point A to that
        # midpoint so the wrench remains mechanically identical.
        pivot_point = scale(0.5, add(pivot_points[0], pivot_points[1]))
        rocker = case["rocker"]
        pivot_force = scale(-1.0, rocker["pivot_reaction"])
        pivot_moment_at_a = scale(-1.0, rocker["pivot_reaction_moment"])
        pivot_moment = add(
            pivot_moment_at_a,
            cross(subtract(pivot_points[0], pivot_point), pivot_force),
        )
        interfaces.append(
            {
                "name": "rocker_pivot_axis",
                "type": "rocker_pivot_reaction",
                "point": pivot_point,
                "force": pivot_force,
                "force_magnitude": magnitude(pivot_force),
                "local_moment": pivot_moment,
            }
        )

        shock_point = _vec(
            rocker_geometry["shock_chassis_pickup"], "rocker.shock_chassis_pickup"
        )
        shock_force = scale(
            -float(rocker["shock_force"]), rocker["shock_direction_rocker_to_chassis"]
        )
        interfaces.append(
            {
                "name": "shock_chassis_pickup",
                "type": "shock_mount",
                "point": shock_point,
                "force": shock_force,
                "force_magnitude": magnitude(shock_force),
                "local_moment": [0.0, 0.0, 0.0],
            }
        )

        total_force = [0.0, 0.0, 0.0]
        total_moment = [0.0, 0.0, 0.0]
        for interface in interfaces:
            total_force = add(total_force, interface["force"])
            total_moment = add(
                total_moment,
                add(
                    cross(subtract(interface["point"], reference), interface["force"]),
                    interface["local_moment"],
                ),
            )
        summaries.append(
            {
                "name": case["name"],
                "reference_point": reference,
                "interfaces": interfaces,
                "resultant_force": total_force,
                "resultant_force_magnitude": magnitude(total_force),
                "resultant_moment": total_moment,
            }
        )
    return summaries


def build_sizing_summary(
    assembly: dict[str, Any],
    solved: dict[str, Any],
    sizing: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate governing force, auto-sized tube checks, and JMX margins."""
    axle = str(assembly.get("axle", ""))
    member_sizing = sizing.get(axle, {})
    material = sizing.get("material", {})
    jmx_allowables = sizing.get("jmx_safe_axial_load_lbf", {})
    elastic_modulus = float(material.get("elastic_modulus_psi", 29_000_000.0))
    yield_strength = float(material.get("yield_strength_psi", 70_000.0))
    ultimate_strength = float(material.get("ultimate_strength_psi", 95_000.0))
    yield_factor = float(material.get("yield_safety_factor", 1.3))
    ultimate_factor = float(material.get("ultimate_safety_factor", 1.5))
    effective_length = float(material.get("effective_length_factor", 1.0))
    auto_size_tubes = bool(sizing.get("auto_size_tubes", False))
    minimum_tube_margin = float(sizing.get("minimum_tube_margin", 0.0))
    tube_catalog = sizing.get("tube_catalog", [])
    geometry_by_name = {item["name"]: item for item in solved["member_geometry"]}
    rows: list[dict[str, Any]] = []

    for member_name, specification in member_sizing.items():
        loads = []
        for case in solved["load_cases"]:
            member = next(item for item in case["members"] if item["name"] == member_name)
            loads.append((case["name"], float(member["force"])))
        peak_case, peak_force = max(loads, key=lambda item: abs(item[1]))
        tension = max((item for item in loads if item[1] > 0.0), key=lambda item: item[1], default=None)
        compression = min((item for item in loads if item[1] < 0.0), key=lambda item: item[1], default=None)
        length = float(geometry_by_name[member_name]["length"])
        configured_outside = float(specification["tube_od_in"])
        configured_inside = float(specification["tube_id_in"])

        def evaluate_tube(outside: float, inside: float) -> dict[str, Any]:
            if outside <= 0.0 or inside < 0.0 or inside >= outside:
                raise ValueError(f"Invalid tube dimensions for {axle}.{member_name}")
            area = math.pi * (outside * outside - inside * inside) / 4.0
            inertia = math.pi * (outside**4 - inside**4) / 64.0
            critical_buckling = (
                math.pi**2 * elastic_modulus * inertia / (effective_length * length) ** 2
            )
            checks: list[dict[str, Any]] = []
            peak_applied = abs(peak_force)
            if peak_applied > 1e-12:
                yield_allowable = area * yield_strength / yield_factor
                ultimate_allowable = area * ultimate_strength / ultimate_factor
                checks.extend(
                    [
                        {
                            "mode": "tube axial yield",
                            "case": peak_case,
                            "applied_load_lbf": peak_applied,
                            "allowable_load_lbf": yield_allowable,
                            "margin": yield_allowable / peak_applied - 1.0,
                        },
                        {
                            "mode": "tube axial ultimate",
                            "case": peak_case,
                            "applied_load_lbf": peak_applied,
                            "allowable_load_lbf": ultimate_allowable,
                            "margin": ultimate_allowable / peak_applied - 1.0,
                        },
                    ]
                )
            if compression is not None:
                compression_case, compression_force = compression
                buckling_allowable = critical_buckling / ultimate_factor
                checks.append(
                    {
                        "mode": "tube Euler buckling",
                        "case": compression_case,
                        "applied_load_lbf": abs(compression_force),
                        "allowable_load_lbf": buckling_allowable,
                        "margin": buckling_allowable / abs(compression_force) - 1.0,
                    }
                )
            governing = min(checks, key=lambda item: item["margin"])
            return {
                "tube_od_in": outside,
                "tube_id_in": inside,
                "tube_wall_in": (outside - inside) / 2.0,
                "tube_area_in2": area,
                "tube_inertia_in4": inertia,
                "critical_buckling_load_lbf": critical_buckling,
                "tube_checks": checks,
                "tube_governing_margin": governing["margin"],
                "tube_governing_mode": governing["mode"],
                "tube_governing_case": governing["case"],
            }

        configured_tube = evaluate_tube(configured_outside, configured_inside)
        selected_tube = configured_tube
        catalog_candidates: list[dict[str, Any]] = []
        if auto_size_tubes:
            for item in tube_catalog:
                outside = float(item["tube_od_in"])
                if "tube_id_in" in item:
                    inside = float(item["tube_id_in"])
                else:
                    inside = outside - 2.0 * float(item["wall_thickness_in"])
                candidate = evaluate_tube(outside, inside)
                if candidate["tube_governing_margin"] >= minimum_tube_margin:
                    catalog_candidates.append(candidate)
            if not catalog_candidates:
                raise ValueError(
                    f"No tube in sizing.tube_catalog gives {axle}.{member_name} "
                    f"a tube margin of at least {minimum_tube_margin:.3f}"
                )
            selected_tube = min(
                catalog_candidates,
                key=lambda item: (
                    item["tube_area_in2"],
                    item["tube_od_in"],
                    item["tube_wall_in"],
                ),
            )

        candidates: list[dict[str, Any]] = [dict(item) for item in selected_tube["tube_checks"]]
        jmx_margins: dict[str, float | None] = {}
        jmx_selected_allowables: dict[str, float | None] = {}
        for end_key in ("chassis_jmx", "wheel_jmx"):
            selection = str(specification.get(end_key, "NA"))
            allowable = jmx_allowables.get(selection)
            jmx_selected_allowables[end_key] = float(allowable) if allowable is not None else None
            margin = (
                float(allowable) / abs(peak_force) - 1.0
                if allowable is not None and abs(peak_force) > 1e-12
                else None
            )
            jmx_margins[end_key] = margin
            if margin is not None:
                candidates.append(
                    {
                        "mode": f"{end_key.replace('_jmx', '')} {selection} axial proxy",
                        "case": peak_case,
                        "applied_load_lbf": abs(peak_force),
                        "allowable_load_lbf": float(allowable),
                        "margin": margin,
                    }
                )
        governing = min(candidates, key=lambda item: item["margin"])
        rows.append(
            {
                "member": member_name,
                "peak_force": peak_force,
                "peak_state": "tension" if peak_force >= 0.0 else "compression",
                "peak_case": peak_case,
                "max_tension_force": tension[1] if tension else None,
                "max_tension_case": tension[0] if tension else None,
                "max_compression_force": compression[1] if compression else None,
                "max_compression_case": compression[0] if compression else None,
                "tube_id_in": selected_tube["tube_id_in"],
                "tube_od_in": selected_tube["tube_od_in"],
                "tube_wall_in": selected_tube["tube_wall_in"],
                "tube_area_in2": selected_tube["tube_area_in2"],
                "tube_inertia_in4": selected_tube["tube_inertia_in4"],
                "critical_buckling_load_lbf": selected_tube["critical_buckling_load_lbf"],
                "tube_checks": selected_tube["tube_checks"],
                "tube_governing_margin": selected_tube["tube_governing_margin"],
                "tube_governing_mode": selected_tube["tube_governing_mode"],
                "tube_governing_case": selected_tube["tube_governing_case"],
                "tube_auto_sized": auto_size_tubes,
                "tube_minimum_margin_target": minimum_tube_margin,
                "configured_tube_id_in": configured_inside,
                "configured_tube_od_in": configured_outside,
                "configured_tube_governing_margin": configured_tube["tube_governing_margin"],
                "member_length_in": length,
                "elastic_modulus_psi": elastic_modulus,
                "yield_strength_psi": yield_strength,
                "ultimate_strength_psi": ultimate_strength,
                "yield_safety_factor": yield_factor,
                "ultimate_safety_factor": ultimate_factor,
                "effective_length_factor": effective_length,
                "chassis_jmx": specification.get("chassis_jmx", "NA"),
                "wheel_jmx": specification.get("wheel_jmx", "NA"),
                "chassis_jmx_margin": jmx_margins["chassis_jmx"],
                "wheel_jmx_margin": jmx_margins["wheel_jmx"],
                "chassis_jmx_allowable_lbf": jmx_selected_allowables["chassis_jmx"],
                "wheel_jmx_allowable_lbf": jmx_selected_allowables["wheel_jmx"],
                "governing_margin": governing["margin"],
                "governing_margin_mode": governing["mode"],
                "governing_margin_case": governing["case"],
                "governing_applied_load_lbf": governing.get("applied_load_lbf"),
                "governing_allowable_load_lbf": governing.get("allowable_load_lbf"),
            }
        )

    shock_loads = [
        (case["name"], float(case["rocker"]["shock_force"]))
        for case in solved["load_cases"]
    ]
    shock_case, shock_force = max(shock_loads, key=lambda item: abs(item[1]))
    rows.append(
        {
            "member": "shock",
            "peak_force": shock_force,
            "peak_state": "tension" if shock_force >= 0.0 else "compression",
            "peak_case": shock_case,
            "chassis_jmx": "NA",
            "wheel_jmx": "NA",
            "chassis_jmx_margin": None,
            "wheel_jmx_margin": None,
            "governing_margin": None,
            "governing_margin_mode": "damper rating not supplied",
            "governing_margin_case": shock_case,
        }
    )
    return rows


def solve_config(config: dict[str, Any]) -> dict[str, Any]:
    config = expand_config(config)
    assemblies = config.get("assemblies")
    if not isinstance(assemblies, list) or not assemblies:
        raise ValueError("Configuration must contain a non-empty 'assemblies' list")
    vehicle = config.get("vehicle")
    ride_loads: dict[str, float] = {}
    ride_summary = None
    if vehicle is not None:
        total = float(vehicle["full_car_weight_lbf"])
        unsprung = float(vehicle["total_unsprung_weight_lbf"])
        front_fraction = float(vehicle["front_weight_fraction"])
        rear_fraction = float(vehicle["rear_weight_fraction"])
        if abs(front_fraction + rear_fraction - 1.0) > 1e-6:
            raise ValueError("vehicle front and rear weight fractions must sum to 1.0")
        unsprung_per_corner = unsprung / 4.0
        front_corner = total * front_fraction / 2.0
        rear_corner = total * rear_fraction / 2.0
        ride_loads = {
            "front": front_corner - unsprung_per_corner,
            "rear": rear_corner - unsprung_per_corner,
        }
        if min(ride_loads.values()) <= 0.0:
            raise ValueError("Calculated spring-supported ride-height corner load must be positive")
        ride_summary = {
            "full_car_weight_lbf": total,
            "total_unsprung_weight_lbf": unsprung,
            "unsprung_weight_per_corner_lbf": unsprung_per_corner,
            "front_tire_load_per_corner_lbf": front_corner,
            "rear_tire_load_per_corner_lbf": rear_corner,
            "front_spring_supported_wheel_load_lbf": ride_loads["front"],
            "rear_spring_supported_wheel_load_lbf": ride_loads["rear"],
            "assumption": "symmetric left/right loading and equal unsprung weight at all four corners",
        }
    solved_assemblies = []
    for assembly in assemblies:
        axle = assembly.get("axle")
        ride_load = ride_loads.get(str(axle)) if vehicle is not None else None
        solved = solve_assembly(assembly, ride_load)
        solved["chassis_loads"] = build_chassis_load_summary(assembly, solved)
        if config.get("sizing"):
            solved["sizing_summary"] = build_sizing_summary(
                assembly, solved, config["sizing"]
            )
        solved_assemblies.append(solved)
    return {
        "model": "3D rigid-body equilibrium with axial two-force members and nonlinear rigid-link kinematics",
        "sign_convention": "positive = tension; negative = compression",
        "ride_height": ride_summary,
        "assemblies": solved_assemblies,
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
            if "kinematics" in case:
                travel = case["kinematics"]["shock_travel_from_ride_height"]
                direction = "compression" if travel >= 0.0 else "rebound"
                print(
                    f"    {'shock travel':<22} {abs(travel):>11.4f} {assembly['coordinate_units']}  {direction} from ride height"
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
        config = expand_config(json.load(handle))
    result = solve_config(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "suspension_forces.json"
    csv_path = args.output_dir / "suspension_forces.csv"
    viewer_path = args.output_dir / "suspension_linkages_3d.html"
    current_viewer_path = args.output_dir / "suspension_linkages_3d_current.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_csv(result, csv_path)
    from linkage_viewer import write_viewer_html

    write_viewer_html(config, result, viewer_path)
    write_viewer_html(config, result, current_viewer_path)
    print_summary(result)
    print(f"\nWrote {json_path}, {csv_path}, {viewer_path}, and {current_viewer_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
