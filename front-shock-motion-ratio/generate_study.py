"""Generate a static front suspension motion-ratio study.

The sweep prescribes vertical wheel travel while preserving all six suspension
link lengths. The upright is a six-degree-of-freedom rigid body and the rocker
adds one rotational degree of freedom, giving seven unknowns for seven
constraints.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from suspension_linkage_forces import (  # noqa: E402
    add,
    cross,
    displaced_assembly,
    dot,
    magnitude,
    rotate_about_axis,
    rotate_by_vector,
    scale,
    solve_square,
    subtract,
)


Vector = list[float]


def _move_upright_point(assembly: dict[str, Any], point: Vector, state: Vector) -> Vector:
    """Apply the solved rigid-upright pose to an attached point."""
    contact_reference = assembly["contact_patch"]
    relative = subtract(point, contact_reference)
    return add(
        contact_reference,
        add(rotate_by_vector(relative, state[3:6]), state[:3]),
    )


def _lower_arm_pullrod_pickup(
    assembly: dict[str, Any], moved: dict[str, Any]
) -> Vector:
    """Move the pullrod pickup with the rigid lower A-arm about its chassis axis."""
    lower_indices = [
        index
        for index, member in enumerate(assembly["members"])
        if str(member.get("name", "")).startswith("lower_")
    ]
    if len(lower_indices) != 2:
        raise ValueError("Motion study requires exactly two lower wishbone legs")
    first, second = (assembly["members"][index] for index in lower_indices)
    outer_reference = first["application"]
    outer_moved = moved["members"][lower_indices[0]]["application"]
    axis_a, axis_b = first["anchor"], second["anchor"]
    axis = subtract(axis_b, axis_a)
    axis_length = magnitude(axis)
    if axis_length < 1e-12:
        raise ValueError("Lower wishbone pivot axis has zero length")
    unit_axis = scale(1.0 / axis_length, axis)

    def radial(point: Vector) -> Vector:
        offset = subtract(point, axis_a)
        return subtract(offset, scale(dot(offset, unit_axis), unit_axis))

    reference_radial = radial(outer_reference)
    moved_radial = radial(outer_moved)
    angle = math.atan2(
        dot(unit_axis, cross(reference_radial, moved_radial)),
        dot(reference_radial, moved_radial),
    )
    pullrod = next(
        member for member in assembly["members"] if member.get("role") == "pushrod"
    )
    return rotate_about_axis(pullrod["application"], axis_a, axis_b, angle)


def _displaced_motion_assembly(
    assembly: dict[str, Any], state: Vector
) -> dict[str, Any]:
    """Move upright, lower-arm pickup, rocker, and configured wheel center."""
    moved = displaced_assembly(assembly, state)
    moved_pullrod_pickup = _lower_arm_pullrod_pickup(assembly, moved)
    for member in moved["members"]:
        if member.get("role") == "pushrod":
            member["application"] = moved_pullrod_pickup
            break
    moved["wheel_center"] = _move_upright_point(
        assembly, assembly["wheel_center"], state
    )
    return moved


def _member_lengths(assembly: dict[str, Any]) -> list[float]:
    return [
        magnitude(subtract(member["anchor"], member["application"]))
        for member in assembly["members"]
    ]


def _shock_length(assembly: dict[str, Any]) -> float:
    rocker = assembly["rocker"]
    return magnitude(
        subtract(rocker["shock_chassis_pickup"], rocker["shock_pickup"])
    )


def _evaluate_pose(
    assembly: dict[str, Any],
    reference_lengths: list[float],
    target_wheel_travel: float,
    state: Vector,
) -> tuple[Vector, dict[str, Any]]:
    moved = _displaced_motion_assembly(assembly, state)
    link_residuals = [
        magnitude(subtract(member["anchor"], member["application"]))
        - reference_lengths[index]
        for index, member in enumerate(moved["members"])
    ]
    base_z = float(assembly["wheel_center"][2])
    moved_z = float(moved["wheel_center"][2])
    # CAD uses -Z upward, so bump travel is base Z minus moved Z.
    travel_residual = (base_z - moved_z) - target_wheel_travel
    return link_residuals + [travel_residual], moved


def solve_wheel_travel_pose(
    assembly: dict[str, Any],
    target_wheel_travel: float,
    initial_state: Vector | None = None,
) -> tuple[Vector, dict[str, Any], int, float]:
    """Solve one prescribed wheel-travel pose with damped Newton iteration."""
    reference_lengths = _member_lengths(assembly)
    state = list(initial_state or [0.0] * 7)
    for iteration in range(50):
        residual, moved = _evaluate_pose(
            assembly, reference_lengths, target_wheel_travel, state
        )
        norm = max(abs(value) for value in residual)
        if norm < 1e-9:
            return state, moved, iteration, norm

        jacobian = [[0.0] * 7 for _ in range(7)]
        for column in range(7):
            step = 1e-6
            trial = state[:]
            trial[column] += step
            trial_residual, _ = _evaluate_pose(
                assembly, reference_lengths, target_wheel_travel, trial
            )
            for row in range(7):
                jacobian[row][column] = (
                    trial_residual[row] - residual[row]
                ) / step

        delta = solve_square(jacobian, scale(-1.0, residual))
        accepted = False
        factor = 1.0
        for _ in range(14):
            trial = add(state, scale(factor, delta))
            trial_residual, _ = _evaluate_pose(
                assembly, reference_lengths, target_wheel_travel, trial
            )
            if max(abs(value) for value in trial_residual) < norm:
                state = trial
                accepted = True
                break
            factor *= 0.5
        if not accepted:
            raise ValueError(
                f"Wheel-travel pose did not converge at {target_wheel_travel:.4f} in"
            )
    raise ValueError(
        f"Wheel-travel pose exceeded 50 iterations at {target_wheel_travel:.4f} in"
    )


def _travel_values(minimum: float, maximum: float, step: float) -> list[float]:
    count = int(round((maximum - minimum) / step))
    values = [minimum + index * step for index in range(count + 1)]
    if not math.isclose(values[-1], maximum, abs_tol=1e-9):
        values.append(maximum)
    return [round(value, 10) for value in values]


def _crossing_travel(samples: list[dict[str, Any]], target_length_mm: float) -> float | None:
    """Linearly interpolate wheel travel where shock length crosses a limit."""
    for left, right in zip(samples, samples[1:]):
        left_delta = left["shock_length_mm"] - target_length_mm
        right_delta = right["shock_length_mm"] - target_length_mm
        if abs(left_delta) < 1e-12:
            return float(left["wheel_travel_in"])
        if left_delta * right_delta <= 0.0:
            fraction = left_delta / (left_delta - right_delta)
            return float(
                left["wheel_travel_in"]
                + fraction * (right["wheel_travel_in"] - left["wheel_travel_in"])
            )
    if samples and abs(samples[-1]["shock_length_mm"] - target_length_mm) < 1e-12:
        return float(samples[-1]["wheel_travel_in"])
    return None


def build_study(config: dict[str, Any]) -> dict[str, Any]:
    assembly = deepcopy(config["assembly"])
    sweep = config["sweep"]
    minimum = float(sweep["minimum_wheel_travel_in"])
    maximum = float(sweep["maximum_wheel_travel_in"])
    step = float(sweep["step_in"])
    if not minimum < 0.0 < maximum or step <= 0.0:
        raise ValueError("Sweep must cross zero and use a positive step")

    values = _travel_values(minimum, maximum, step)
    reference_shock_length = _shock_length(assembly)
    shock_spec_input = config["shock_spec"]
    extended_length_mm = float(shock_spec_input["extended_length_mm"])
    shock_travel_mm = float(shock_spec_input["travel_mm"])
    if extended_length_mm <= 0.0 or shock_travel_mm <= 0.0:
        raise ValueError("Shock extended length and travel must be positive")
    collapsed_length_mm = extended_length_mm - shock_travel_mm
    if collapsed_length_mm <= 0.0:
        raise ValueError("Shock travel must be shorter than its extended length")
    solved: dict[float, dict[str, Any]] = {}

    def solve_branch(branch: list[float]) -> None:
        state = [0.0] * 7
        for travel in branch:
            state, moved, iterations, residual = solve_wheel_travel_pose(
                assembly, travel, state
            )
            shock_length = _shock_length(moved)
            shock_length_mm = shock_length * 25.4
            stroke_used_mm = extended_length_mm - shock_length_mm
            stroke_remaining_mm = shock_length_mm - collapsed_length_mm
            if stroke_used_mm < -1e-6:
                shock_travel_status = "over_extended"
            elif stroke_remaining_mm < -1e-6:
                shock_travel_status = "bottomed_out"
            else:
                shock_travel_status = "within_travel"
            shock_axis = subtract(
                moved["rocker"]["shock_chassis_pickup"],
                moved["rocker"]["shock_pickup"],
            )
            shock_angle = math.degrees(
                math.acos(
                    min(1.0, abs(shock_axis[2]) / max(shock_length, 1e-12))
                )
            )
            solved[travel] = {
                "wheel_travel_in": travel,
                "shock_compression_in": reference_shock_length - shock_length,
                "shock_length_in": shock_length,
                "shock_length_mm": shock_length_mm,
                "shock_stroke_used_mm": stroke_used_mm,
                "shock_stroke_remaining_mm": stroke_remaining_mm,
                "shock_travel_status": shock_travel_status,
                "shock_angle_from_vertical_deg": shock_angle,
                "rocker_rotation_deg": math.degrees(state[6]),
                "upright_translation_in": state[:3],
                "upright_rotation_vector_rad": state[3:6],
                "iterations": iterations,
                "max_constraint_residual_in": residual,
                "geometry": {
                    "contact_patch": moved["contact_patch"],
                    "wheel_center": moved["wheel_center"],
                    "members": moved["members"],
                    "rocker": moved["rocker"],
                },
            }

    positive = sorted((value for value in values if value >= 0.0))
    negative = sorted((value for value in values if value <= 0.0), reverse=True)
    solve_branch(positive)
    solve_branch(negative)
    samples = [solved[value] for value in values]

    for index, sample in enumerate(samples):
        if index == 0:
            left, right = samples[index], samples[index + 1]
        elif index == len(samples) - 1:
            left, right = samples[index - 1], samples[index]
        else:
            left, right = samples[index - 1], samples[index + 1]
        wheel_delta = right["wheel_travel_in"] - left["wheel_travel_in"]
        shock_delta = (
            right["shock_compression_in"] - left["shock_compression_in"]
        )
        instantaneous = wheel_delta / shock_delta
        travel = sample["wheel_travel_in"]
        average = (
            travel / sample["shock_compression_in"]
            if abs(travel) > 1e-12
            else instantaneous
        )
        sample["instantaneous_motion_ratio"] = instantaneous
        sample["average_motion_ratio"] = average
        sample["wheel_rate_factor"] = 1.0 / (instantaneous * instantaneous)

    extension_limit = _crossing_travel(samples, extended_length_mm)
    compression_limit = _crossing_travel(samples, collapsed_length_mm)
    safe_samples = [
        sample for sample in samples if sample["shock_travel_status"] == "within_travel"
    ]
    if not safe_samples:
        raise ValueError("Configured shock has no usable stroke within this sweep")
    shock_spec = {
        "extended_length_mm": extended_length_mm,
        "travel_mm": shock_travel_mm,
        "collapsed_length_mm": collapsed_length_mm,
        "ride_height_length_mm": reference_shock_length * 25.4,
        "ride_height_stroke_used_mm": extended_length_mm - reference_shock_length * 25.4,
        "ride_height_stroke_remaining_mm": reference_shock_length * 25.4 - collapsed_length_mm,
        "extension_limit_wheel_travel_in": extension_limit,
        "compression_limit_wheel_travel_in": compression_limit,
        "safe_sample_min_wheel_travel_in": safe_samples[0]["wheel_travel_in"],
        "safe_sample_max_wheel_travel_in": safe_samples[-1]["wheel_travel_in"],
    }

    return {
        "title": config["title"],
        "coordinate_units": config.get("coordinate_units", "in"),
        "travel_convention": config["travel_convention"],
        "motion_ratio_convention": config["motion_ratio_convention"],
        "assembly": assembly,
        "sweep": sweep,
        "shock_spec": shock_spec,
        "reference_shock_length_in": reference_shock_length,
        "samples": samples,
    }


def write_study_html(study: dict[str, Any], output: Path) -> None:
    template = (PROJECT_DIR / "app_template.html").read_text(encoding="utf-8")
    placeholder = "__MOTION_STUDY_DATA__"
    if template.count(placeholder) != 1:
        raise ValueError("App template must contain exactly one data placeholder")
    payload = json.dumps(study, separators=(",", ":"), ensure_ascii=False).replace(
        "</", "<\\/"
    )
    output.write_text(template.replace(placeholder, payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=PROJECT_DIR / "study_config.json"
    )
    parser.add_argument("--output", type=Path, default=PROJECT_DIR / "index.html")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    study = build_study(config)
    write_study_html(study, args.output)
    data_output = args.output.with_name("motion-study-data.json")
    data_output.write_text(json.dumps(study, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.output} and {data_output} with {len(study['samples'])} poses"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
