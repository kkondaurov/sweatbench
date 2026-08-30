#!/usr/bin/env python3
"""Materialize and inspect Sweat Bench milestones without invoking a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from run_candidate import CONTINUE_PROMPT, INITIAL_PROMPT


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "benchmark.json"
MARKER = ".group-stay-work.json"
RESULTS_DIR = ROOT / ".results"
CANDIDATE_TEST_POLICIES = ("canonical", "endogenous")
EXAMPLE_TEST_POLICIES = {"canonical": "included", "endogenous": "none"}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def get_stage(stage_id: int) -> dict:
    for stage in load_manifest()["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise ValueError(f"unknown milestone: {stage_id}")


def stage_private_tests(stage: dict) -> list[Path]:
    return [ROOT / path for path in stage["private_tests"]]


def private_case_ids(path: Path) -> set[str]:
    source = path.read_text()
    module_match = re.search(r"^defmodule\s+(\S+)\s+do$", source, re.MULTILINE)
    if module_match is None:
        raise ValueError(f"private test has no module: {path.relative_to(ROOT)}")

    module = module_match.group(1)
    return {
        f'{module}::test {name}'
        for name in re.findall(r'^\s+test "([^"]+)"', source, re.MULTILINE)
    }


def stage_case_ids(stage: dict) -> set[str]:
    return set().union(*(private_case_ids(path) for path in stage_private_tests(stage)))


def stage_families(stage_id: int) -> list[dict]:
    return [family for family in load_manifest()["families"] if family["stage"] == stage_id]


def family_track(family: dict) -> str:
    return family.get("track", "core")


def family_results(stage_id: int, tests: list[dict], system_checks: list[dict]) -> list[dict]:
    statuses = {test["id"]: test["status"] for test in tests}
    system_statuses = {check["name"]: check["status"] for check in system_checks}
    results = []

    for family in stage_families(stage_id):
        failing = [
            member for member in family["members"] if statuses.get(member) != "passed"
        ]
        failing.extend(
            f"system:{name}"
            for name in family["system_checks"]
            if system_statuses.get(name) != "passed"
        )

        results.append(
            {
                "id": family["id"],
                "track": family_track(family),
                "status": "passed" if not failing else "failed",
                "failing_members": failing,
            }
        )

    return results


def candidate_packet(stage_id: int, candidate_tests: str = "canonical") -> list[Path]:
    manifest = load_manifest()
    get_stage(stage_id)
    if candidate_tests not in CANDIDATE_TEST_POLICIES:
        raise ValueError(f"unknown candidate test policy: {candidate_tests}")

    files = [ROOT / path for path in manifest["shared_candidate_files"]]

    for stage in manifest["stages"]:
        if stage["id"] > stage_id:
            break
        files.append(ROOT / stage["request"])
        if candidate_tests == "canonical":
            files.append(ROOT / stage["public_test"])

    return files


def write_task(workspace: Path, stage: dict, candidate_tests: str) -> None:
    testing_expectation = ""
    if candidate_tests == "endogenous":
        testing_expectation = """

Changes to this service ship with appropriate automated tests. Decide what needs verification,
add those tests as part of the change, and leave the suite strong enough for the next engineer to
rely on.
"""

    task = f"""# Current work

Implement `docs/requests/{Path(stage['request']).name}` in this application.

Read the product and API documents first. Preserve behavior delivered in earlier requests unless
the current request explicitly changes it. Run the complete test suite, inspect the implementation
as a whole, and keep working until you consider the change ready to ship.{testing_expectation}
"""
    (workspace / "TASK.md").write_text(task)


def install_stage_files(
    workspace: Path, stage_id: int, candidate_tests: str = "canonical"
) -> None:
    manifest = load_manifest()
    stage = get_stage(stage_id)
    if candidate_tests not in CANDIDATE_TEST_POLICIES:
        raise ValueError(f"unknown candidate test policy: {candidate_tests}")
    docs = workspace / "docs"
    requests = docs / "requests"
    acceptance = workspace / "test" / "acceptance"
    requests.mkdir(parents=True, exist_ok=True)
    acceptance.mkdir(parents=True, exist_ok=True)

    for shared in manifest["shared_candidate_files"]:
        source = ROOT / shared
        shutil.copy2(source, docs / source.name)

    request = ROOT / stage["request"]
    shutil.copy2(request, requests / request.name)
    provided_tests = []
    if candidate_tests == "canonical":
        public_test = ROOT / stage["public_test"]
        shutil.copy2(public_test, acceptance / public_test.name)
        provided_tests.append(str(Path("test/acceptance") / public_test.name))
    write_task(workspace, stage, candidate_tests)
    (workspace / MARKER).write_text(
        json.dumps(
            {
                "request": stage_id,
                "example_tests": EXAMPLE_TEST_POLICIES[candidate_tests],
                "installed_examples": provided_tests,
            },
            indent=2,
        )
        + "\n"
    )


def materialize(
    stage_id: int, destination: Path, candidate_tests: str = "canonical"
) -> None:
    if stage_id != 1:
        raise ValueError("only milestone 1 starts from the scaffold; use advance for later work")
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")

    starter = ROOT / load_manifest()["starter"]
    shutil.copytree(starter, destination, ignore=shutil.ignore_patterns("_build", "deps", "*.db*"))
    shutil.copy2(ROOT / ".tool-versions", destination / ".tool-versions")
    install_stage_files(destination, stage_id, candidate_tests)


def advance(
    stage_id: int, workspace: Path, candidate_tests: str | None = None
) -> None:
    marker_path = workspace / MARKER
    if not marker_path.exists():
        raise ValueError(f"not a materialized Sweat Bench workspace: {workspace}")

    marker = json.loads(marker_path.read_text())
    current = marker["request"]
    if stage_id != current + 1:
        raise ValueError(f"milestone {stage_id} cannot follow milestone {current}")

    example_tests = marker.get("example_tests", "included")
    try:
        existing_policy = next(
            policy
            for policy, marker_value in EXAMPLE_TEST_POLICIES.items()
            if marker_value == example_tests
        )
    except StopIteration as error:
        raise ValueError(f"unknown example test policy: {example_tests}") from error
    if candidate_tests is not None and candidate_tests != existing_policy:
        raise ValueError(
            f"candidate test policy cannot change from {existing_policy} to {candidate_tests}"
        )
    install_stage_files(workspace, stage_id, existing_policy)


def snapshot(workspace: Path, destination: Path) -> None:
    marker_path = workspace / MARKER
    if not marker_path.exists():
        raise ValueError(f"not a materialized Sweat Bench workspace: {workspace}")
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    if destination == workspace or workspace in destination.parents:
        raise ValueError("snapshot destination cannot be inside the workspace")

    ignored = shutil.ignore_patterns("_build", "*.db*", ".git", ".elixir_ls")
    shutil.copytree(workspace, destination, ignore=ignored)


def validate() -> None:
    manifest = load_manifest()
    stages = manifest["stages"]
    ids = [stage["id"] for stage in stages]
    if ids != list(range(1, len(stages) + 1)):
        raise ValueError("milestone identifiers must be consecutive and start at 1")

    case_count = 0
    case_stages: dict[str, int] = {}
    for stage in stages:
        case_count += sum(path.read_text().count('\n  test "') for path in stage_private_tests(stage))
        if stage["expected_private_cases"] != case_count:
            raise ValueError(
                f"milestone {stage['id']} expects {stage['expected_private_cases']} private cases "
                f"but its cumulative files define {case_count}"
            )

        for case_id in stage_case_ids(stage):
            if case_id in case_stages:
                raise ValueError(f"duplicate private scenario id: {case_id}")
            case_stages[case_id] = stage["id"]

    system_stages = {
        check["command"]: check["after_stage"] for check in manifest["system_checks"]
    }
    family_ids = set()
    case_memberships: dict[str, dict[str, list[str]]] = {
        case_id: {} for case_id in case_stages
    }
    system_memberships: dict[str, dict[str, list[str]]] = {
        name: {} for name in system_stages
    }

    for family in manifest["families"]:
        family_id = family["id"]
        if family_id in family_ids:
            raise ValueError(f"duplicate family id: {family_id}")
        family_ids.add(family_id)

        track = family_track(family)
        if track not in {"core", "judgment"}:
            raise ValueError(f"family {family_id} has unknown track: {track}")
        if track == "judgment":
            definition = ROOT / family.get("definition", "")
            if not definition.is_file():
                raise ValueError(f"judgment family {family_id} has no definition")
            digest = hashlib.sha256(definition.read_bytes()).hexdigest()
            if digest != family.get("definition_sha256"):
                raise ValueError(f"judgment family {family_id} definition hash drifted")

        if family["stage"] not in ids:
            raise ValueError(f"family {family_id} has unknown milestone {family['stage']}")
        if not family["members"] and not family["system_checks"]:
            raise ValueError(f"family {family_id} has no members")

        for case_id in family["members"]:
            if case_id not in case_stages:
                raise ValueError(f"family {family_id} references unknown scenario: {case_id}")
            if case_stages[case_id] != family["stage"]:
                raise ValueError(
                    f"family {family_id} milestone does not match scenario: {case_id}"
                )
            case_memberships[case_id].setdefault(track, []).append(family_id)

        for command in family["system_checks"]:
            if command not in system_stages:
                raise ValueError(f"family {family_id} references unknown system check: {command}")
            if system_stages[command] != family["stage"]:
                raise ValueError(
                    f"family {family_id} milestone does not match system check: {command}"
                )
            system_memberships[command].setdefault(track, []).append(family_id)

    invalid_cases = {
        case_id: memberships
        for case_id, memberships in case_memberships.items()
        if not memberships or any(len(families) != 1 for families in memberships.values())
    }
    if invalid_cases:
        raise ValueError(f"private scenarios must belong to exactly one family: {invalid_cases}")

    invalid_checks = {
        command: memberships
        for command, memberships in system_memberships.items()
        if not memberships or any(len(families) != 1 for families in memberships.values())
    }
    if invalid_checks:
        raise ValueError(f"system checks must belong to exactly one family: {invalid_checks}")

    required = [
        ROOT / manifest["starter"],
        ROOT / "evaluation/score_formatter.exs",
        ROOT / "evaluation/system_checks.py",
        *candidate_packet(ids[-1]),
    ]
    required.extend(path for stage in stages for path in stage_private_tests(stage))
    required.extend(ROOT / check["scenario"] for check in manifest["system_checks"])
    required.extend(
        ROOT / family["definition"]
        for family in manifest["families"]
        if family_track(family) == "judgment"
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise ValueError(f"missing benchmark files: {', '.join(missing)}")

    model_text = "\n".join(path.read_text() for path in candidate_packet(ids[-1]))
    model_text += "\n" + INITIAL_PROMPT + "\n" + CONTINUE_PROMPT
    forbidden = ["public test", "hidden test", "withheld", "evaluator", "benchmark score"]
    leaked = [term for term in forbidden if term in model_text.lower()]
    if leaked:
        raise ValueError(f"model packet contains evaluation language: {', '.join(leaked)}")

    migrations = list((ROOT / manifest["starter"] / "priv/repo/migrations").glob("[0-9]*.exs"))
    if migrations:
        raise ValueError("starter must not contain product migrations")

    router = (ROOT / manifest["starter"] / "lib/group_stay_web/router.ex").read_text()
    if any(route in router for route in ("get ", "post ", "put ", "patch ", "delete ")):
        raise ValueError("starter must not contain product routes")

    print(f"validated {len(stages)} milestones")


def system_commands(stage_id: int, workspace: Path, previous: Path | None) -> list[list[str]]:
    checks = [
        item
        for item in load_manifest()["system_checks"]
        if item["after_stage"] == stage_id
    ]
    runner = str((ROOT / "evaluation/system_checks.py").resolve())
    commands = []
    for check in checks:
        command = check["command"]
        if command == "idempotency-restart":
            commands.append([sys.executable, runner, command, str(workspace)])
            continue
        if previous is None:
            raise ValueError(f"milestone {stage_id} evaluation requires --previous")
        commands.append(
            [sys.executable, runner, command, str(previous), str(workspace)]
        )
    return commands


def default_report_path(stage_id: int, workspace: Path) -> Path:
    workspace_id = hashlib.sha256(str(workspace).encode()).hexdigest()[:12]
    return RESULTS_DIR / f"{workspace.name}-{workspace_id}-milestone-{stage_id}.json"


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def evaluate(
    stage_id: int,
    workspace: Path,
    previous: Path | None = None,
    report_path: Path | None = None,
) -> int:
    marker_path = workspace / MARKER
    if not marker_path.exists():
        raise ValueError(f"not a materialized Sweat Bench workspace: {workspace}")

    completed = json.loads(marker_path.read_text())["request"]
    if completed != stage_id:
        raise ValueError(f"workspace is at milestone {completed}, not {stage_id}")

    manifest = load_manifest()
    stage = get_stage(stage_id)
    expected_private_cases = stage["expected_private_cases"]
    private_tests = [
        str(path.resolve())
        for candidate_stage in manifest["stages"]
        if candidate_stage["id"] <= stage_id
        for path in stage_private_tests(candidate_stage)
    ]
    cross_processes = system_commands(stage_id, workspace, previous)
    destination = report_path or default_report_path(stage_id, workspace)

    with tempfile.TemporaryDirectory(prefix=f"sweat-bench-{stage_id}-") as directory:
        database = Path(directory) / "private-tests.db"
        raw_results = Path(directory) / "exunit-results.json"
        env = os.environ | {
            "MIX_ENV": "test",
            "GROUP_STAY_DATABASE_PATH": str(database),
            "GROUP_STAY_TEST_RESULT_PATH": str(raw_results),
        }

        setup_commands = [
            ["mix", "ecto.create", "--quiet"],
            ["mix", "ecto.migrate", "--quiet"],
        ]
        setup_result = 0
        for command in setup_commands:
            setup_result = subprocess.run(command, cwd=workspace, env=env, check=False).returncode
            if setup_result != 0:
                break

        test_result = setup_result
        if setup_result == 0:
            formatter_source = ROOT / "evaluation/score_formatter.exs"
            formatter_target = workspace / "test/support/group_stay_test_report_formatter.ex"
            formatter_bytes = formatter_source.read_bytes()
            original_formatter = formatter_target.read_bytes() if formatter_target.exists() else None
            if original_formatter == formatter_bytes:
                original_formatter = None

            conn_case_source = ROOT / manifest["starter"] / "test/support/conn_case.ex"
            conn_case_target = workspace / "test/support/conn_case.ex"
            original_conn_case = conn_case_target.read_bytes()

            formatter_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(formatter_source, formatter_target)
            shutil.copy2(conn_case_source, conn_case_target)

            try:
                command = [
                    "mix",
                    "test",
                    "--formatter",
                    "ExUnit.CLIFormatter",
                    "--formatter",
                    "GroupStay.TestReportFormatter",
                    "--seed",
                    "0",
                    *private_tests,
                ]
                test_result = subprocess.run(command, cwd=workspace, env=env, check=False).returncode
            finally:
                conn_case_target.write_bytes(original_conn_case)

                if original_formatter is None:
                    formatter_target.unlink(missing_ok=True)
                else:
                    formatter_target.write_bytes(original_formatter)

                for pattern in (
                    "_build/**/Elixir.GroupStay.TestReportFormatter.beam",
                    "_build/**/Elixir.GroupStayWeb.ConnCase.beam",
                ):
                    for beam in workspace.glob(pattern):
                        beam.unlink(missing_ok=True)

        tests = []
        if raw_results.exists():
            tests = json.loads(raw_results.read_text()).get("tests", [])

    system_results = [
        subprocess.run(command, cwd=ROOT, check=False).returncode
        for command in cross_processes
    ]
    system_checks = [
        {
            "name": command[2],
            "status": "passed" if result == 0 else "failed",
        }
        for command, result in zip(cross_processes, system_results, strict=True)
    ]

    families = family_results(stage_id, tests, system_checks)

    private_complete = len(tests) == expected_private_cases and all(
        test["status"] == "passed" for test in tests
    )
    system_complete = all(check["status"] == "passed" for check in system_checks)
    passed = setup_result == 0 and test_result == 0 and private_complete and system_complete

    family_tracks = {}
    for track in ("core", "judgment"):
        tracked = [family for family in families if family["track"] == track]
        family_tracks[track] = {
            "passed": sum(family["status"] == "passed" for family in tracked),
            "total": len(tracked),
        }

    report = {
        "milestone": stage_id,
        "status": "passed" if passed else "failed",
        "expected_private_cases": expected_private_cases,
        "tests": tests,
        "system_checks": system_checks,
        "system_check": system_checks[0] if len(system_checks) == 1 else None,
        "families": families,
        "family_summary": {
            "passed": sum(family["status"] == "passed" for family in families),
            "total": len(families),
        },
        "family_tracks": family_tracks,
        "summary": {
            "passed": sum(test["status"] == "passed" for test in tests)
            + sum(check["status"] == "passed" for check in system_checks),
            "total": expected_private_cases + len(system_checks),
        },
    }
    if setup_result != 0:
        report["setup_error"] = "fresh test database preparation failed"
    elif len(tests) != expected_private_cases:
        report["test_error"] = (
            f"private test report contains {len(tests)} of {expected_private_cases} expected scenarios"
        )

    write_report(destination, report)
    print(f"evaluation report: {destination}")

    if passed:
        return 0
    return test_result or next((result for result in system_results if result), 0) or 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")

    packet = subparsers.add_parser("packet")
    packet.add_argument("stage", type=int)
    packet.add_argument(
        "--candidate-tests", choices=CANDIDATE_TEST_POLICIES, default="canonical"
    )

    create = subparsers.add_parser("materialize")
    create.add_argument("stage", type=int)
    create.add_argument("destination", type=Path)
    create.add_argument(
        "--candidate-tests", choices=CANDIDATE_TEST_POLICIES, default="canonical"
    )

    next_stage = subparsers.add_parser("advance")
    next_stage.add_argument("stage", type=int)
    next_stage.add_argument("workspace", type=Path)
    next_stage.add_argument("--candidate-tests", choices=CANDIDATE_TEST_POLICIES)

    save = subparsers.add_parser("snapshot")
    save.add_argument("workspace", type=Path)
    save.add_argument("destination", type=Path)

    judge = subparsers.add_parser("evaluate")
    judge.add_argument("stage", type=int)
    judge.add_argument("workspace", type=Path)
    judge.add_argument("--previous", type=Path)
    judge.add_argument("--report", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "validate":
            validate()
        elif args.command == "packet":
            for path in candidate_packet(args.stage, args.candidate_tests):
                print(path.relative_to(ROOT))
        elif args.command == "materialize":
            materialize(
                args.stage, args.destination.resolve(), args.candidate_tests
            )
        elif args.command == "advance":
            advance(args.stage, args.workspace.resolve(), args.candidate_tests)
        elif args.command == "snapshot":
            snapshot(args.workspace.resolve(), args.destination.resolve())
        elif args.command == "evaluate":
            previous = args.previous.resolve() if args.previous else None
            report = args.report.resolve() if args.report else None
            return evaluate(args.stage, args.workspace.resolve(), previous, report)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
