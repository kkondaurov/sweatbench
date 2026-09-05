#!/usr/bin/env python3
"""Validate and summarize the frozen Sweat Bench v6 accepted-run dataset."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


DATASET = Path(__file__).with_name("accepted-runs.json")
EXPECTED_ACCEPTED = 89
EXPECTED_MODEL_VIEW = 64
EXPECTED_HARNESS_VIEW = 25
NUMERIC_TOLERANCE = 1e-9


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=NUMERIC_TOLERANCE, abs_tol=NUMERIC_TOLERANCE)


def load(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("dataset root must be an object")
    return data


def recompute_group(group: str, runs: list[dict]) -> dict:
    costs = [float(run["cost"]) for run in runs]
    cores = [int(run["core_final"]) for run in runs]
    maintenance = [int(run["maintenance_final"]) for run in runs]
    return {
        "group": group,
        "n": len(runs),
        "mean_core": mean(cores),
        "mean_maintenance": mean(maintenance),
        "sweeps": sum(
            core == 39 and upkeep == 10
            for core, upkeep in zip(cores, maintenance, strict=True)
        ),
        "median_cost": statistics.median(costs),
    }


def validate(data: dict) -> list[dict]:
    runs = data.get("runs")
    groups = data.get("groups")
    if not isinstance(runs, list) or not isinstance(groups, list):
        raise ValueError("dataset must contain run and group arrays")

    errors: list[str] = []
    ids = [run.get("id") for run in runs]
    if len(runs) != EXPECTED_ACCEPTED:
        errors.append(f"accepted population is {len(runs)}, expected {EXPECTED_ACCEPTED}")
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        errors.append("run ids must be non-empty and unique")
    if any("source" in run for run in runs):
        errors.append("machine-local source fields must not be published")

    views = Counter(run.get("view") for run in runs)
    if views != Counter({"models": EXPECTED_MODEL_VIEW, "harness": EXPECTED_HARNESS_VIEW}):
        errors.append(f"unexpected view populations: {dict(views)}")

    for run in runs:
        if not 0 <= run.get("core_final", -1) <= 39:
            errors.append(f"{run.get('id')}: Core is outside 0..39")
        if not 0 <= run.get("maintenance_final", -1) <= 10:
            errors.append(f"{run.get('id')}: Maintenance is outside 0..10")
        if not 0 <= run.get("scenarios_final", -1) <= 94:
            errors.append(f"{run.get('id')}: scenarios are outside 0..94")
        if run.get("cost", -1) < 0:
            errors.append(f"{run.get('id')}: cost is negative")
        if run.get("subagents", -1) < 0:
            errors.append(f"{run.get('id')}: subagent count is negative")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for run in runs:
        grouped[run["group"]].append(run)
    committed = {group["group"]: group for group in groups}
    if set(grouped) != set(committed):
        errors.append("run groups and committed aggregate groups differ")

    recomputed = []
    for group in sorted(grouped):
        actual = recompute_group(group, grouped[group])
        expected = committed.get(group)
        recomputed.append(actual)
        if expected is None:
            continue
        for field in ("n", "sweeps"):
            if actual[field] != expected[field]:
                errors.append(
                    f"{group}: {field} is {actual[field]}, committed value is {expected[field]}"
                )
        for field in ("mean_core", "mean_maintenance", "median_cost"):
            if not close(actual[field], expected[field]):
                errors.append(
                    f"{group}: {field} is {actual[field]}, committed value is {expected[field]}"
                )

    declared = data.get("validation", {}).get("population", {})
    expected_population = {
        "accepted_trajectories": EXPECTED_ACCEPTED,
        "model_view": EXPECTED_MODEL_VIEW,
        "additional_harness_view": EXPECTED_HARNESS_VIEW,
    }
    for field, value in expected_population.items():
        if declared.get(field) != value:
            errors.append(f"declared {field} is {declared.get(field)}, expected {value}")

    if errors:
        raise ValueError("dataset validation failed:\n- " + "\n- ".join(errors))
    return recomputed


def print_table(data: dict, groups: list[dict]) -> None:
    committed = {group["group"]: group for group in data["groups"]}
    print(
        f"Sweat Bench v{data['release']['version']}: "
        f"{len(data['runs'])} accepted trajectories "
        f"({EXPECTED_MODEL_VIEW} model view, {EXPECTED_HARNESS_VIEW} harness view)"
    )
    print()
    print(f"{'Group':<31} {'n':>2} {'Core':>6} {'Maint':>6} {'Sweeps':>7} {'Median cost':>12}")
    print("-" * 70)
    for group in groups:
        display = committed[group["group"]]["display"]
        if len(display) > 31:
            display = display[:28] + "..."
        print(
            f"{display:<31} {group['n']:>2} {group['mean_core']:>6.1f} "
            f"{group['mean_maintenance']:>6.1f} "
            f"{str(group['sweeps']) + '/' + str(group['n']):>7} "
            f"${group['median_cost']:>11.2f}"
        )
    print("\nValidation passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATASET)
    parser.add_argument("--json", action="store_true", help="emit recomputed group metrics as JSON")
    args = parser.parse_args()

    data = load(args.data)
    groups = validate(data)
    if args.json:
        print(json.dumps({"status": "passed", "groups": groups}, indent=2))
    else:
        print_table(data, groups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
