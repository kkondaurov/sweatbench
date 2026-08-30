#!/usr/bin/env python3
"""Run one isolated, sequential Sweat Bench candidate trajectory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BENCH = ROOT / "bench.py"


def discover_executable(name: str, *fallbacks: str) -> Path:
    if executable := shutil.which(name):
        return Path(executable)
    for fallback in fallbacks:
        path = Path(fallback).expanduser()
        if path.is_file():
            return path
    return Path(name)


def resolve_executable(path: Path) -> Path:
    path = path.expanduser()
    if path.parent == Path("."):
        if executable := shutil.which(str(path)):
            return Path(executable)
        return path
    return path.resolve()


DEFAULT_CODEX = discover_executable(
    "codex", "/Applications/ChatGPT.app/Contents/Resources/codex"
)
DEFAULT_CLAUDE = discover_executable("claude")
DEFAULT_OPENCODE = discover_executable("opencode")
DEFAULT_DOCKER = discover_executable("docker")
DEFAULT_RUNS = ROOT / ".runs"
WORKSPACE_ROOT = Path(tempfile.gettempdir()) / "sweat-bench"
MILESTONES = range(1, len(json.loads((ROOT / "benchmark.json").read_text())["stages"]) + 1)
CANDIDATE_TEST_POLICIES = ("canonical", "endogenous")
OPENCODE_MAX_ATTEMPTS = 20
OPENCODE_RETRY_DELAY_SECONDS = 2
OPENCODE_LOCK_RETRY_DELAY_SECONDS = 15

INITIAL_PROMPT = """Work on the current product request in this repository.

Read TASK.md and the product, API, and runbook documents before changing code. Implement the
request completely and preserve all behavior described by earlier requests. Use the normal
engineering loop: inspect, implement, run the project's full test suite, and repair failures.

Before finishing, review the full implementation and diff against all current requirements, fix
anything you would not ship, and rerun the relevant tests. Keep all work inside this repository.
Do the work rather than only describing it.
"""

CONTINUE_PROMPT = """A new product request is now available in TASK.md.

Implement it completely while preserving the behavior from every earlier request. Inspect the
existing implementation before editing, run the project's full test suite, and repair failures.
Before finishing, review the full implementation and diff against all current requirements, fix
anything you would not ship, and rerun the relevant tests. Keep all work inside this repository.
Do the work rather than only describing it.
"""

RETRY_PROMPT = """Your previous turn ended before the current request was complete.

Continue the current product request from the existing workspace and session. Inspect the work
already completed, finish the implementation, run the full test suite, repair failures, and do the
same final review you were originally asked to perform. Do not merely describe what remains.
"""

def run(command: list[str], *, cwd: Path, output: Path | None = None) -> int:
    if output is None:
        return subprocess.run(command, cwd=cwd, check=False).returncode

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as stream:
        return subprocess.run(
            command,
            cwd=cwd,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        ).returncode


def workspace_beam_pids(workspace: Path) -> list[int]:
    result = subprocess.run(
        ["lsof", "-a", "-c", "beam.smp", "-d", "cwd", "-Fn"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError("could not inspect candidate BEAM processes")

    matches = []
    pid = None
    for line in result.stdout.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid is not None:
            if Path(line[1:]).resolve() == workspace.resolve():
                matches.append(pid)
            pid = None
    return matches


def terminate_workspace_beams(workspace: Path) -> list[int]:
    pids = workspace_beam_pids(workspace)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    if pids:
        time.sleep(1)
    for pid in pids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        os.kill(pid, signal.SIGKILL)
    return pids


def run_agent(
    command: list[str],
    *,
    workspace: Path,
    output: Path,
    append: bool = False,
    private_xdg: bool = False,
    container_image: str | None = None,
    docker: Path | None = None,
    container_environment: tuple[str, ...] = (),
) -> tuple[int, list[int]]:
    temporary_directory = workspace.parent / "tmp"
    xdg_root = workspace.parent / "xdg"
    temporary_directory.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(
        {
            "TMPDIR": str(temporary_directory),
            "TMP": str(temporary_directory),
            "TEMP": str(temporary_directory),
        }
    )
    if private_xdg:
        for directory in ("cache", "config", "data", "state"):
            (xdg_root / directory).mkdir(parents=True, exist_ok=True)
        environment.update(
            {
                "XDG_CACHE_HOME": str(xdg_root / "cache"),
                "XDG_CONFIG_HOME": str(xdg_root / "config"),
                "XDG_DATA_HOME": str(xdg_root / "data"),
                "XDG_STATE_HOME": str(xdg_root / "state"),
            }
        )
    if container_image is not None:
        if docker is None:
            raise ValueError("Docker executable is required for a containerized agent")
        state_root = workspace.parent / "container-state"
        state_root.mkdir(parents=True, exist_ok=True)
        container_command = [
            str(docker),
            "run",
            "--rm",
            "--init",
            "--workdir",
            "/workspace",
            "--mount",
            f"type=bind,src={workspace},dst=/workspace",
            "--mount",
            f"type=bind,src={state_root},dst=/state",
            "--env",
            "HOME=/state/home",
            "--env",
            "XDG_CACHE_HOME=/state/xdg/cache",
            "--env",
            "XDG_CONFIG_HOME=/state/xdg/config",
            "--env",
            "XDG_DATA_HOME=/state/xdg/data",
            "--env",
            "XDG_STATE_HOME=/state/xdg/state",
            "--env",
            "MIX_BUILD_PATH=/state/build",
        ]
        for name in container_environment:
            container_command.extend(["--env", name])
        command = [*container_command, container_image, *command]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a" if append else "w") as stream:
        exit_code = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        ).returncode
        terminated = [] if container_image is not None else terminate_workspace_beams(workspace)
    return exit_code, terminated


def opencode_auth_path(workspace: Path, *, containerized: bool) -> Path:
    xdg_data = (
        workspace.parent / "container-state" / "xdg" / "data"
        if containerized
        else workspace.parent / "xdg" / "data"
    )
    return xdg_data / "opencode" / "auth.json"


def seed_opencode_auth(source: Path, target: Path, provider: str) -> None:
    try:
        credentials = json.loads(source.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read OpenCode auth file: {error}") from error

    credential = credentials.get(provider)
    if not isinstance(credential, dict):
        raise ValueError(f"OpenCode auth file has no {provider!r} credential")
    if provider == "openai" and credential.get("type") != "oauth":
        raise ValueError("OpenAI subscription runs require an OAuth credential")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({provider: credential}, indent=2) + "\n")
    target.chmod(0o600)


def opencode_retry_reason(log_path: Path) -> str | None:
    lines = log_path.read_text().splitlines()
    for line in lines[-5:]:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            if "database is locked" in line:
                return "local_database_locked"
            continue

        if event.get("type") != "error":
            continue
        error = event.get("error", {})
        message = error.get("data", {}).get("message") or error.get("message") or ""
        if "database is locked" in message:
            return "local_database_locked"

    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "step_finish":
            part = event.get("part") or {}
            return (
                "turn_length_limit"
                if part.get("reason") == "length"
                else None
            )
        if event.get("type") != "error":
            return None

        error = event.get("error", {})
        message = error.get("data", {}).get("message") or error.get("message") or ""
        try:
            detail = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            detail = {}

        code = detail.get("code")
        error_type = detail.get("metadata", {}).get("error_type")
        if error_type in {"provider_unavailable", "rate_limited", "timeout"}:
            return f"{error_type} ({code})" if code is not None else error_type
        if code in {429, 502, 503, 504}:
            return f"provider HTTP {code}"
        if message.startswith("Unexpected server error"):
            return "provider_server_error"
        return None
    return None


def checked(command: list[str], *, cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")


def git_commit(workspace: Path, message: str) -> str:
    checked(["git", "add", "-A"], cwd=workspace)
    dirty = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=workspace, check=False
    ).returncode
    if dirty == 1:
        checked(["git", "commit", "-m", message], cwd=workspace)
    elif dirty != 0:
        raise RuntimeError("could not inspect the candidate Git index")

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=workspace, text=True
    ).strip()


def find_thread_id(log_path: Path) -> str | None:
    for line in log_path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        if event.get("type") == "thread.started":
            return event.get("thread_id") or event.get("session_id")
        if event.get("sessionID"):
            return event["sessionID"]
        if event.get("session_id"):
            return event["session_id"]
    return None


def command_from_event(event: object) -> str | None:
    if not isinstance(event, dict):
        return None

    item = event.get("item")
    if not isinstance(item, dict):
        item = {}
    if item.get("type") == "command_execution":
        return item.get("command")

    part = event.get("part")
    if not isinstance(part, dict):
        return None
    if part.get("tool") == "bash":
        state = part.get("state")
        if not isinstance(state, dict):
            return None
        input_data = state.get("input")
        if not isinstance(input_data, dict):
            return None
        return input_data.get("command")
    return None


def inspects_host_processes(command: str) -> bool:
    body = command
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []
    if tokens and Path(tokens[0]).name in {"sh", "bash", "zsh"}:
        for flag in ("-c", "-lc"):
            if flag in tokens and tokens.index(flag) + 1 < len(tokens):
                body = tokens[tokens.index(flag) + 1]
                break

    return bool(
        re.search(
            r"(?:^|(?:&&|\|\||[;|&(\n])\s*)"
            r"(?:(?:sudo|command|exec)\s+)*"
            r"(?:/[^\s;&|()]+/)?"
            r"(?:ps|pgrep|top|lsof)"
            r"(?=$|\s|[;&|)])",
            body,
        )
    )


def audit_agent_log(
    log_path: Path, *, parallel: bool = False
) -> dict:
    forbidden = [
        str(ROOT),
        "evaluation/private_tests",
        "evaluation/system_checks.py",
        "benchmark.json",
    ]
    hits = []
    for number, line in enumerate(log_path.read_text().splitlines(), start=1):
        matched = [fragment for fragment in forbidden if fragment in line]
        if parallel:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                event = {}
            command = command_from_event(event) or ""
            if inspects_host_processes(command):
                matched.append("host process inspection")
        if matched:
            hits.append({"line": number, "fragments": matched})
    return {"status": "passed" if not hits else "failed", "hits": hits}


def host_process_audit_required(
    *,
    parallel_audit: bool,
    barrier_dir: Path | None,
    container_image: str | None,
) -> bool:
    return (
        (parallel_audit or barrier_dir is not None)
        and container_image is None
    )


def signal_barrier_abort(barrier_dir: Path | None, label: str, reason: str) -> None:
    if barrier_dir is None:
        return
    abort_dir = barrier_dir / "aborted"
    abort_dir.mkdir(parents=True, exist_ok=True)
    (abort_dir / f"{label}.json").write_text(
        json.dumps({"label": label, "reason": reason}, indent=2) + "\n"
    )


def await_cohort_barrier(
    barrier_dir: Path | None,
    barrier_size: int | None,
    *,
    label: str,
    milestone: int,
    phase: str,
) -> None:
    if barrier_dir is None:
        return
    if barrier_size is None or barrier_size < 1:
        raise ValueError("parallel barrier size must be positive")

    ready_dir = barrier_dir / f"milestone-{milestone}" / phase
    ready_dir.mkdir(parents=True, exist_ok=True)
    (ready_dir / f"{label}.ready").write_text("ready\n")
    while True:
        aborts = sorted((barrier_dir / "aborted").glob("*.json"))
        if aborts:
            raise RuntimeError(f"parallel cohort aborted: {aborts[0].read_text().strip()}")
        if len(list(ready_dir.glob("*.ready"))) >= barrier_size:
            return
        time.sleep(0.25)


def test_inventory(workspace: Path) -> dict:
    test_root = workspace / "test"
    files = []
    if test_root.exists():
        for path in sorted(test_root.rglob("*")):
            if not path.is_file():
                continue
            source = path.read_bytes()
            files.append(
                {
                    "path": str(path.relative_to(workspace)),
                    "sha256": hashlib.sha256(source).hexdigest(),
                }
            )

    declarations = 0
    for item in files:
        source = (workspace / item["path"]).read_text(errors="replace")
        declarations += len(re.findall(r'^\s*test\s+"', source, re.MULTILINE))

    return {
        "file_count": len(files),
        "test_declarations": declarations,
        "files": files,
    }


def codex_command(
    codex: Path,
    workspace: Path,
    model: str,
    effort: str,
    thread_id: str | None,
) -> list[str]:
    command = [
        str(codex),
        "--approve-for-me",
        "--cd",
        str(workspace),
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{effort}"',
        "--config",
        "sandbox_workspace_write.network_access=true",
        "exec",
    ]
    if thread_id is not None:
        command.extend(["resume", thread_id])

    command.extend(
        [
            "--json",
            "--ignore-user-config",
            "--ignore-rules",
        ]
    )
    return command


def claude_command(
    claude: Path,
    model: str,
    effort: str,
    thread_id: str | None,
) -> list[str]:
    command = [
        str(claude),
        "-p",
        "--model",
        model,
        "--effort",
        effort,
        "--output-format",
        "stream-json",
        "--verbose",
        "--safe-mode",
        "--no-chrome",
        "--dangerously-skip-permissions",
    ]
    if thread_id is not None:
        command.extend(["--resume", thread_id])
    return command


def opencode_command(
    opencode: Path,
    workspace: Path,
    model: str,
    effort: str,
    thread_id: str | None,
) -> list[str]:
    command = [
        str(opencode),
        "run",
        "--format",
        "json",
        "--pure",
        "--auto",
        "--thinking",
        "--model",
        model,
        "--variant",
        effort,
        "--dir",
        str(workspace),
    ]
    if thread_id is not None:
        command.extend(["--session", thread_id])
    return command


def prepare_run(
    run_root: Path,
    model: str,
    effort: str,
    label: str,
    harness: str,
    executable: Path,
    protocol: str,
    candidate_tests: str,
    benchmark_ref: str,
    workspace_parent: Path | None = None,
    container_image: str | None = None,
    docker: Path | None = None,
    opencode_auth_provider: str | None = None,
    prompt_suffix: str | None = None,
) -> dict:
    if run_root.exists():
        raise ValueError(f"run already exists: {run_root}")

    if container_image is None:
        harness_version = subprocess.check_output(
            [str(executable), "--version"], text=True
        ).strip()
    else:
        if docker is None:
            raise ValueError("Docker executable is required with --container-image")
        harness_version = subprocess.check_output(
            [str(docker), "run", "--rm", container_image, str(executable), "--version"],
            text=True,
        ).strip()
    workspace = (
        WORKSPACE_ROOT / secrets.token_hex(6)
        if workspace_parent is None
        else workspace_parent.resolve()
    ) / "groupstay"
    run_root.mkdir(parents=True)
    checked(
        [
            sys.executable,
            str(BENCH),
            "materialize",
            "1",
            str(workspace),
            "--candidate-tests",
            candidate_tests,
        ],
        cwd=ROOT,
    )
    checked(["mix", "deps.get"], cwd=workspace)
    checked(["git", "init", "-b", "main"], cwd=workspace)
    checked(["git", "config", "user.name", "Northstar Engineering"], cwd=workspace)
    checked(["git", "config", "user.email", "platform@northstar.example"], cwd=workspace)
    initial_commit = git_commit(workspace, "Initialize Group Stay service")
    benchmark_commit = subprocess.check_output(
        ["git", "rev-parse", f"{benchmark_ref}^{{}}"], cwd=ROOT, text=True
    ).strip()
    runner_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()

    if harness == "codex":
        sandbox_contract = {
            "flag": "--approve-for-me",
            "candidate_workspace": str(workspace),
            "effective_mode": "workspace-write [workdir, /tmp, $TMPDIR]",
            "network_access": True,
            "source_repository_mode": "unchanged",
            "version_policy": "record the exact CLI version in every run state",
        }
    elif harness == "claude":
        sandbox_contract = {
            "flag": "--dangerously-skip-permissions",
            "candidate_workspace": str(workspace),
            "effective_mode": "Claude Code permissions bypass in isolated candidate workspace",
            "network_access": True,
            "source_repository_mode": "unchanged and audited from the agent log",
            "customizations": "disabled with --safe-mode",
        }
    else:
        credential_source = (
            f"private {opencode_auth_provider} OAuth credential file"
            if opencode_auth_provider is not None
            else "OPENROUTER_API_KEY environment variable"
        )
        sandbox_contract = {
            "flag": "--auto",
            "candidate_workspace": str(workspace),
            "effective_mode": "OpenCode auto-approved tools in isolated candidate workspace",
            "temporary_directory": str(workspace.parent / "tmp"),
            "xdg_directory": str(workspace.parent / "xdg"),
            "network_access": True,
            "source_repository_mode": "unchanged and audited from the agent log",
            "customizations": "external plugins disabled with --pure",
            "credential_source": credential_source,
        }

    state = {
        "label": label,
        "model": model,
        "reasoning_effort": effort,
        "protocol": protocol,
        "candidate_tests": candidate_tests,
        "prompt_suffix": prompt_suffix,
        "canonical_milestone_tests_provided": candidate_tests == "canonical",
        "created_at": datetime.now(UTC).isoformat(),
        "benchmark_ref": benchmark_ref,
        "benchmark_commit": benchmark_commit,
        "runner_commit": runner_commit,
        "harness": {"name": harness, "version": harness_version},
        "codex_version": harness_version if harness == "codex" else None,
        "sandbox_contract": sandbox_contract,
        "workspace": str(workspace),
        "workspace_parent": str(workspace.parent),
        "initial_commit": initial_commit,
        "thread_id": None,
        "milestones": [],
    }
    save_state(run_root, state)
    return state


def prepare_resumed_run(
    run_root: Path,
    args: argparse.Namespace,
) -> tuple[dict, int, str | None]:
    state_path = run_root / "state.json"
    if not state_path.is_file():
        raise ValueError(f"run has no state to resume: {run_root}")

    state = json.loads(state_path.read_text())
    if state.get("completed_at"):
        raise ValueError(f"run is already complete: {run_root}")
    if args.protocol != "handoff" or state.get("protocol") != "handoff":
        raise ValueError("checkpoint resume currently requires the handoff protocol")

    expected = {
        "label": args.label,
        "model": args.model,
        "reasoning_effort": args.effort,
        "candidate_tests": args.candidate_tests,
        "prompt_suffix": getattr(args, "prompt_suffix", None),
    }
    for field, value in expected.items():
        if state.get(field) != value:
            raise ValueError(
                f"resume argument {field}={value!r} does not match stored {state.get(field)!r}"
            )
    if state.get("harness", {}).get("name") != args.harness:
        raise ValueError("resume harness does not match the stored run")
    benchmark_commit = subprocess.check_output(
        ["git", "rev-parse", f"{args.benchmark_ref}^{{}}"], cwd=ROOT, text=True
    ).strip()
    if state.get("benchmark_commit") != benchmark_commit:
        raise ValueError("resume benchmark ref does not match the stored benchmark commit")

    completed = [item["milestone"] for item in state.get("milestones", [])]
    if completed != list(range(1, len(completed) + 1)):
        raise ValueError("stored milestones are not a complete prefix")

    prior_resumptions = state.get("resumptions", [])
    historical_workspace = next(
        (
            item.get("previous_workspace")
            for item in prior_resumptions
            if item.get("previous_workspace")
        ),
        None,
    )
    original_workspace = Path(state["workspace"])
    workspace_base = (
        args.workspace_parent.resolve()
        if args.workspace_parent is not None
        else Path(
            state.get("workspace_parent")
            or (
                Path(historical_workspace).parent
                if historical_workspace is not None
                else original_workspace.parent
            )
        ).resolve()
    )
    state["workspace_parent"] = str(workspace_base)

    if not completed:
        failure = state.get("failed_at") or {}
        stage = failure.get("milestone")
        thread_id = failure.get("thread_id")
        workspace = Path(state["workspace"])
        marker = workspace / ".group-stay-work.json"
        if (
            stage not in MILESTONES
            or thread_id is None
            or not marker.is_file()
            or json.loads(marker.read_text()).get("request") != stage
        ):
            raise ValueError(
                "run has neither an accepted snapshot nor a resumable interrupted stage"
            )

        current_runner_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        state.setdefault("resumptions", []).append(
            {
                "resumed_at": datetime.now(UTC).isoformat(),
                "mode": "interrupted_stage",
                "milestone": stage,
                "workspace": str(workspace),
                "thread_id": thread_id,
                "runner_commit": current_runner_commit,
            }
        )
        state["thread_id"] = None
        state["runner_commit"] = current_runner_commit
        state.pop("failed_at", None)
        state.pop("invalid_at", None)
        state.pop("scores", None)
        state.pop("aggregate", None)
        save_state(run_root, state)
        return state, stage, thread_id

    last_completed = completed[-1]
    next_stage = last_completed + 1
    if next_stage not in MILESTONES:
        raise ValueError("run has no remaining milestone to resume")
    snapshot = run_root / "snapshots" / f"milestone-{last_completed}"
    if not snapshot.is_dir():
        raise ValueError(f"resume snapshot is missing: {snapshot}")

    resumptions = state.setdefault("resumptions", [])
    resume_number = len(resumptions) + 1
    resume_parent = workspace_base / f"resume-{resume_number:02d}"
    workspace = resume_parent / "groupstay"
    if resume_parent.exists():
        raise ValueError(f"resume workspace already exists: {resume_parent}")

    shutil.copytree(snapshot, workspace)
    checked(["mix", "deps.get"], cwd=workspace)
    checked(["git", "init", "-b", "main"], cwd=workspace)
    checked(["git", "config", "user.name", "Northstar Engineering"], cwd=workspace)
    checked(["git", "config", "user.email", "platform@northstar.example"], cwd=workspace)
    restored_commit = git_commit(
        workspace, f"Restore accepted milestone {last_completed:02d}"
    )
    checked(
        [
            sys.executable,
            str(BENCH),
            "advance",
            str(next_stage),
            str(workspace),
            "--candidate-tests",
            args.candidate_tests,
        ],
        cwd=ROOT,
    )
    request_commit = git_commit(workspace, f"Add product request {next_stage:02d}")

    source_catalogue = (
        original_workspace.parent
        / "container-state"
        / "xdg"
        / "cache"
        / "opencode"
        / "models.json"
    )
    if args.container_image and source_catalogue.is_file():
        resumed_catalogue = (
            workspace.parent
            / "container-state"
            / "xdg"
            / "cache"
            / "opencode"
            / "models.json"
        )
        resumed_catalogue.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_catalogue, resumed_catalogue)

    source_auth = opencode_auth_path(
        original_workspace, containerized=bool(args.container_image)
    )
    if args.opencode_auth_file is not None and source_auth.is_file():
        resumed_auth = opencode_auth_path(
            workspace, containerized=bool(args.container_image)
        )
        resumed_auth.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_auth, resumed_auth)

    interrupted_log = run_root / "logs" / f"agent-{next_stage}.jsonl"
    archived_log = None
    if interrupted_log.exists():
        archive_dir = run_root / "interrupted-attempts" / f"resume-{resume_number:02d}"
        archive_dir.mkdir(parents=True, exist_ok=False)
        archived_log = archive_dir / interrupted_log.name
        interrupted_log.replace(archived_log)

    current_runner_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    resumptions.append(
        {
            "resumed_at": datetime.now(UTC).isoformat(),
            "from_milestone": last_completed,
            "previous_workspace": str(original_workspace),
            "workspace": str(workspace),
            "archived_agent_log": None if archived_log is None else str(archived_log),
            "restored_commit": restored_commit,
            "request_commit": request_commit,
            "runner_commit": current_runner_commit,
        }
    )
    state["workspace"] = str(workspace)
    state["thread_id"] = None
    state["runner_commit"] = current_runner_commit
    state.pop("failed_at", None)
    state.pop("invalid_at", None)
    state.pop("scores", None)
    state.pop("aggregate", None)
    save_state(run_root, state)
    return state, next_stage, None


def append_prompt_suffix(prompt: str, prompt_suffix: str | None) -> str:
    if not prompt_suffix or not prompt_suffix.strip():
        return prompt
    return f"{prompt.rstrip()}\n\n{prompt_suffix.strip()}\n"


def agent_prompt(protocol: str, milestone: int, prompt_suffix: str | None = None) -> str:
    prompt = (
        INITIAL_PROMPT
        if protocol == "handoff" or milestone == 1
        else CONTINUE_PROMPT
    )
    return append_prompt_suffix(prompt, prompt_suffix)


def resume_thread_id(protocol: str, thread_id: str | None) -> str | None:
    return thread_id if protocol == "continuous" else None


def save_state(run_root: Path, state: dict) -> None:
    (run_root / "state.json").write_text(json.dumps(state, indent=2) + "\n")


def score_report(report_path: Path) -> dict:
    report = json.loads(report_path.read_text())
    return {
        "status": report["status"],
        "passed": report["summary"]["passed"],
        "total": report["summary"]["total"],
        "family_passed": report["family_summary"]["passed"],
        "family_total": report["family_summary"]["total"],
        "family_tracks": report.get("family_tracks", {}),
    }


def introduced_case_ids(milestone: int) -> set[str]:
    manifest = json.loads((ROOT / "benchmark.json").read_text())
    stage = next(item for item in manifest["stages"] if item["id"] == milestone)
    identifiers = set()

    for relative_path in stage["private_tests"]:
        source = (ROOT / relative_path).read_text()
        module_match = re.search(r"^defmodule\s+(\S+)\s+do$", source, re.MULTILINE)
        if module_match is None:
            raise ValueError(f"private test has no module: {relative_path}")
        module = module_match.group(1)
        for name in re.findall(r'^\s+test "([^"]+)"', source, re.MULTILINE):
            identifiers.add(f"{module}::test {name}")

    return identifiers


def family_definitions(milestone: int | None = None) -> list[dict]:
    manifest = json.loads((ROOT / "benchmark.json").read_text())
    families = manifest["families"]
    if milestone is None:
        return families
    return [family for family in families if family["stage"] == milestone]


def family_outcome(
    family: dict, test_statuses: dict[str, str], system_statuses: dict[str, str]
) -> dict:
    failing = [
        member for member in family["members"] if test_statuses.get(member) != "passed"
    ]
    failing.extend(
        f"system:{command}"
        for command in family["system_checks"]
        if system_statuses.get(command) != "passed"
    )
    return {
        "id": family["id"],
        "stage": family["stage"],
        "track": family.get("track", "core"),
        "status": "passed" if not failing else "failed",
        "failing_members": failing,
    }


def trajectory_scores(milestones: list[dict]) -> dict:
    scenario_ship_passed = 0
    scenario_ship_total = 0
    family_ship_results = []
    system_outcomes: dict[str, str] = {}
    prefix_depth = 0
    prefix_intact = True
    final_report = None
    family_timeline = []
    ever_passed = set()
    open_episodes: dict[str, dict] = {}
    regression_episodes = []

    for milestone in milestones:
        report = json.loads(Path(milestone["report"]).read_text())
        statuses = {test["id"]: test["status"] for test in report["tests"]}
        milestone_id = milestone.get("milestone", milestone.get("checkpoint"))
        introduced = introduced_case_ids(milestone_id)
        scenario_ship_total += len(introduced)
        scenario_ship_passed += sum(
            statuses.get(identifier) == "passed" for identifier in introduced
        )

        system_checks = report.get("system_checks")
        if system_checks is None:
            legacy_check = report.get("system_check")
            system_checks = [] if legacy_check is None else [legacy_check]
        for system_check in system_checks:
            system_outcomes[system_check["name"]] = system_check["status"]
            scenario_ship_total += 1
            scenario_ship_passed += system_check["status"] == "passed"

        family_ship_results.extend(
            family_outcome(family, statuses, system_outcomes)
            for family in family_definitions(milestone_id)
        )

        cumulative_families = [
            family_outcome(family, statuses, system_outcomes)
            for family in family_definitions()
            if family["stage"] <= milestone_id and family.get("track", "core") == "core"
        ]
        family_timeline.append(
            {
                "milestone": milestone_id,
                "families": cumulative_families,
            }
        )
        for result in cumulative_families:
            family_id = result["id"]
            if result["status"] == "passed":
                ever_passed.add(family_id)
                episode = open_episodes.pop(family_id, None)
                if episode is not None:
                    episode["recovered_at"] = milestone_id
            elif family_id in ever_passed and family_id not in open_episodes:
                episode = {
                    "family": family_id,
                    "opened_at": milestone_id,
                    "recovered_at": None,
                }
                regression_episodes.append(episode)
                open_episodes[family_id] = episode

        core_milestone_passed = all(
            result["status"] == "passed" for result in cumulative_families
        )
        if prefix_intact and core_milestone_passed:
            prefix_depth = milestone_id
        else:
            prefix_intact = False
        final_report = report

    if final_report is None:
        raise ValueError("cannot score an empty trajectory")

    final_statuses = {test["id"]: test["status"] for test in final_report["tests"]}
    expected_final = set().union(
        *(
            introduced_case_ids(milestone.get("milestone", milestone.get("checkpoint")))
            for milestone in milestones
        )
    )
    scenario_final_passed = sum(
        final_statuses.get(identifier) == "passed" for identifier in expected_final
    )
    scenario_final_passed += sum(status == "passed" for status in system_outcomes.values())
    scenario_final_total = len(expected_final) + len(system_outcomes)

    completed_milestone = max(
        milestone.get("milestone", milestone.get("checkpoint"))
        for milestone in milestones
    )
    family_final_results = [
        family_outcome(family, final_statuses, system_outcomes)
        for family in family_definitions()
        if family["stage"] <= completed_milestone
    ]

    family_ship_passed = sum(
        result["status"] == "passed" for result in family_ship_results
    )
    family_final_passed = sum(
        result["status"] == "passed" for result in family_final_results
    )

    track_scores = {}
    for track in ("core", "judgment"):
        ship = [result for result in family_ship_results if result["track"] == track]
        final = [result for result in family_final_results if result["track"] == track]
        track_scores[track] = {
            "ship_time": {
                "passed": sum(result["status"] == "passed" for result in ship),
                "total": len(ship),
            },
            "final_state": {
                "passed": sum(result["status"] == "passed" for result in final),
                "total": len(final),
            },
        }

    return {
        "prefix_depth": prefix_depth,
        "ship_time": {"passed": family_ship_passed, "total": len(family_ship_results)},
        "final_state": {"passed": family_final_passed, "total": len(family_final_results)},
        "tracks": track_scores,
        "families": {
            "ship_time": family_ship_results,
            "final_state": family_final_results,
            "timeline": family_timeline,
        },
        "regression_episodes": {
            "count": len(regression_episodes),
            "episodes": regression_episodes,
        },
        "scenarios": {
            "ship_time": {
                "passed": scenario_ship_passed,
                "total": scenario_ship_total,
            },
            "final_state": {
                "passed": scenario_final_passed,
                "total": scenario_final_total,
            },
        },
    }


def evaluate_stage(run_root: Path, workspace: Path, stage: int) -> tuple[Path, dict]:
    report = run_root / "reports" / f"milestone-{stage}.json"
    command = [
        sys.executable,
        str(BENCH),
        "evaluate",
        str(stage),
        str(workspace),
        "--report",
        str(report),
    ]
    if stage in {2, 4, 5, 6, 7}:
        command.extend(["--previous", str(run_root / "snapshots" / f"milestone-{stage - 1}")])

    exit_code = run(command, cwd=ROOT, output=run_root / "logs" / f"evaluate-{stage}.log")
    score = score_report(report)
    score["exit_code"] = exit_code
    return report, score


def execute(args: argparse.Namespace) -> int:
    if (args.barrier_dir is None) != (args.barrier_size is None):
        raise ValueError("--barrier-dir and --barrier-size must be provided together")
    if args.opencode_provider_failure_limit < 1:
        raise ValueError("--opencode-provider-failure-limit must be positive")
    if args.max_milestones is not None and args.max_milestones < 1:
        raise ValueError("--max-milestones must be positive")
    if args.max_milestones is not None and args.protocol != "handoff":
        raise ValueError("--max-milestones requires the handoff protocol")
    if args.opencode_auth_file is not None and args.harness != "opencode":
        raise ValueError("--opencode-auth-file requires the OpenCode harness")

    run_root = args.runs_dir.resolve() / args.label
    executables = {
        "codex": args.codex,
        "claude": args.claude,
        "opencode": args.opencode,
    }
    executable = resolve_executable(executables[args.harness])
    if args.resume_existing:
        state, start_stage, resumed_stage_thread_id = prepare_resumed_run(run_root, args)
    else:
        state = prepare_run(
            run_root,
            args.model,
            args.effort,
            args.label,
            args.harness,
            executable,
            args.protocol,
            args.candidate_tests,
            args.benchmark_ref,
            args.workspace_parent,
            args.container_image,
            args.docker,
            args.opencode_auth_provider if args.opencode_auth_file is not None else None,
            args.prompt_suffix,
        )
        start_stage = min(MILESTONES)
        resumed_stage_thread_id = None
    workspace = Path(state["workspace"])
    if args.opencode_auth_file is not None:
        auth_target = opencode_auth_path(
            workspace, containerized=bool(args.container_image)
        )
        if not auth_target.is_file():
            seed_opencode_auth(
                args.opencode_auth_file.resolve(),
                auth_target,
                args.opencode_auth_provider,
            )
    barrier_dir = None if args.barrier_dir is None else args.barrier_dir.resolve()
    audit_host_processes = host_process_audit_required(
        parallel_audit=args.parallel_audit,
        barrier_dir=barrier_dir,
        container_image=args.container_image,
    )
    if args.container_image:
        state["container_isolation"] = {
            "image": args.container_image,
            "mounts": {
                "/workspace": str(workspace),
                "/state": str(workspace.parent / "container-state"),
            },
            "network": "default Docker bridge",
            "docker_socket_mounted": False,
            "container_build_path": "/state/build",
        }
        save_state(run_root, state)
    if barrier_dir is not None:
        state["parallel_cohort"] = {
            "barrier_directory": str(barrier_dir),
            "size": args.barrier_size,
            "policy": "candidate and private-evaluation phases never overlap",
        }
        save_state(run_root, state)
    if args.parallel_audit:
        state["parallel_audit"] = {
            "host_process_inspection": (
                "isolated by container PID namespace"
                if args.container_image
                else "forbidden"
            ),
            "barrier_required": False,
        }
        save_state(run_root, state)

    milestones_run = 0
    for stage in MILESTONES:
        if stage < start_stage:
            continue
        packet = json.loads((workspace / ".group-stay-work.json").read_text())
        expected_examples = (
            "included" if args.candidate_tests == "canonical" else "none"
        )
        if packet.get("example_tests", "included") != expected_examples:
            raise RuntimeError("candidate test policy drifted during materialization")
        inventory_before = test_inventory(workspace)
        print(f"[{args.label}] milestone {stage}: model work", flush=True)
        agent_log = run_root / "logs" / f"agent-{stage}.jsonl"
        continuing_interrupted_stage = (
            stage == start_stage and resumed_stage_thread_id is not None
        )
        thread_id = (
            resumed_stage_thread_id
            if continuing_interrupted_stage
            else resume_thread_id(args.protocol, state["thread_id"])
        )
        if args.harness == "codex":
            command = codex_command(
                executable,
                workspace,
                args.model,
                args.effort,
                thread_id,
            )
        elif args.harness == "claude":
            command = claude_command(
                executable,
                args.model,
                args.effort,
                thread_id,
            )
        else:
            command = opencode_command(
                executable,
                Path("/workspace") if args.container_image else workspace,
                args.model,
                args.effort,
                thread_id,
            )
        prompt = append_prompt_suffix(
            RETRY_PROMPT
            if continuing_interrupted_stage
            else agent_prompt(args.protocol, stage),
            args.prompt_suffix,
        )
        agent_attempts = []
        terminated = []
        provider_failures = 0
        for attempt in range(1, OPENCODE_MAX_ATTEMPTS + 1):
            agent_exit, attempt_terminated = run_agent(
                [*command, prompt],
                workspace=workspace,
                output=agent_log,
                append=continuing_interrupted_stage or attempt > 1,
                private_xdg=args.harness == "opencode" and not args.container_image,
                container_image=args.container_image,
                docker=args.docker,
                container_environment=(
                    ("OPENROUTER_API_KEY",)
                    if args.harness == "opencode" and args.opencode_auth_file is None
                    else ()
                ),
            )
            terminated.extend(attempt_terminated)
            milestone_thread_id = find_thread_id(agent_log)
            retry_reason = (
                opencode_retry_reason(agent_log)
                if args.harness == "opencode"
                else None
            )
            agent_attempts.append(
                {
                    "attempt": attempt,
                    "exit_code": agent_exit,
                    "retry_reason": retry_reason,
                }
            )
            if retry_reason not in {
                None,
                "turn_length_limit",
                "local_database_locked",
            }:
                provider_failures += 1
            retry_without_session = retry_reason == "local_database_locked"
            if retry_reason is None or attempt == OPENCODE_MAX_ATTEMPTS or (
                milestone_thread_id is None and not retry_without_session
            ) or provider_failures >= args.opencode_provider_failure_limit:
                break

            print(
                f"[{args.label}] milestone {stage}: interrupted ({retry_reason}); "
                f"resuming attempt {attempt + 1}/{OPENCODE_MAX_ATTEMPTS}",
                flush=True,
            )
            retry_delay = (
                OPENCODE_LOCK_RETRY_DELAY_SECONDS
                if retry_reason == "local_database_locked"
                else OPENCODE_RETRY_DELAY_SECONDS
            )
            time.sleep(retry_delay)
            if milestone_thread_id is not None:
                command = opencode_command(
                    executable,
                    Path("/workspace") if args.container_image else workspace,
                    args.model,
                    args.effort,
                    milestone_thread_id,
                )
                prompt = RETRY_PROMPT

        integrity = audit_agent_log(
            agent_log,
            parallel=audit_host_processes,
        )
        milestone_thread_id = find_thread_id(agent_log)
        if args.protocol == "continuous" and state["thread_id"] is None:
            state["thread_id"] = milestone_thread_id
        if integrity["status"] != "passed":
            state["invalid_at"] = {"milestone": stage, "integrity_audit": integrity}
            save_state(run_root, state)
            print(f"[{args.label}] invalid trajectory: integrity policy violation detected")
            return 1
        if agent_exit != 0 or milestone_thread_id is None or retry_reason is not None:
            changed = bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=workspace, text=True
                ).strip()
            )
            state["failed_at"] = {
                "milestone": stage,
                "thread_id": milestone_thread_id,
                "agent_exit_code": agent_exit,
                "retry_reason": retry_reason,
                "agent_attempts": agent_attempts,
                "workspace_changed": changed,
                "policy": "candidate_failure" if changed else "discard_and_rerun_fresh_label",
            }
            save_state(run_root, state)
            print(f"[{args.label}] agent failed at milestone {stage}; see {agent_log}")
            return 1

        inventory_after = test_inventory(workspace)
        commit = git_commit(workspace, f"Deliver product request {stage:02d}")
        if barrier_dir is not None:
            print(f"[{args.label}] milestone {stage}: waiting at agent barrier", flush=True)
        await_cohort_barrier(
            barrier_dir,
            args.barrier_size,
            label=args.label,
            milestone=stage,
            phase="agent-finished",
        )
        print(f"[{args.label}] milestone {stage}: private evaluation", flush=True)
        report, score = evaluate_stage(run_root, workspace, stage)

        snapshot = run_root / "snapshots" / f"milestone-{stage}"
        checked([sys.executable, str(BENCH), "snapshot", str(workspace), str(snapshot)], cwd=ROOT)
        state["milestones"].append(
            {
                "milestone": stage,
                "thread_id": milestone_thread_id,
                "agent_exit_code": agent_exit,
                "agent_attempts": agent_attempts,
                "integrity_audit": integrity,
                "terminated_beam_processes": terminated,
                "candidate_packet": packet,
                "test_inventory_before": inventory_before,
                "test_inventory_after": inventory_after,
                "commit": commit,
                "report": str(report),
                **score,
            }
        )
        save_state(run_root, state)
        print(
            f"[{args.label}] milestone {stage}: {score['passed']}/{score['total']} "
            f"scenarios, {score['family_passed']}/{score['family_total']} families "
            f"(Core {score['family_tracks'].get('core', {}).get('passed', 0)}/"
            f"{score['family_tracks'].get('core', {}).get('total', 0)}, Judgment "
            f"{score['family_tracks'].get('judgment', {}).get('passed', 0)}/"
            f"{score['family_tracks'].get('judgment', {}).get('total', 0)}) "
            f"({score['status']})",
            flush=True,
        )

        if stage < max(MILESTONES):
            checked(
                [
                    sys.executable,
                    str(BENCH),
                    "advance",
                    str(stage + 1),
                    str(workspace),
                    "--candidate-tests",
                    args.candidate_tests,
                ],
                cwd=ROOT,
            )
            git_commit(workspace, f"Add product request {stage + 1:02d}")

        if barrier_dir is not None:
            print(
                f"[{args.label}] milestone {stage}: waiting at evaluation barrier",
                flush=True,
            )
        await_cohort_barrier(
            barrier_dir,
            args.barrier_size,
            label=args.label,
            milestone=stage,
            phase="evaluation-finished",
        )

        milestones_run += 1
        if args.max_milestones is not None and milestones_run >= args.max_milestones:
            break

    if state["milestones"][-1]["milestone"] < max(MILESTONES):
        state["scores"] = trajectory_scores(state["milestones"])
        state["aggregate"] = state["scores"]["final_state"]
        state["paused_at"] = datetime.now(UTC).isoformat()
        save_state(run_root, state)
        print(
            f"[{args.label}] paused after milestone "
            f"{state['milestones'][-1]['milestone']}; resume with --resume-existing",
            flush=True,
        )
        return 0

    state["completed_at"] = datetime.now(UTC).isoformat()
    state.pop("paused_at", None)
    state["scores"] = trajectory_scores(state["milestones"])
    state["aggregate"] = state["scores"]["final_state"]
    save_state(run_root, state)
    print(
        f"[{args.label}] complete: Core final-state "
        f"{state['scores']['tracks']['core']['final_state']['passed']}/"
        f"{state['scores']['tracks']['core']['final_state']['total']}, Judgment final-state "
        f"{state['scores']['tracks']['judgment']['final_state']['passed']}/"
        f"{state['scores']['tracks']['judgment']['final_state']['total']}, "
        f"scenario final-state {state['scores']['scenarios']['final_state']['passed']}/"
        f"{state['scores']['scenarios']['final_state']['total']}, "
        f"prefix depth {state['scores']['prefix_depth']}/{max(MILESTONES)}",
        flush=True,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--harness", choices=["codex", "claude", "opencode"], default="codex"
    )
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--effort", choices=["low", "medium", "high", "xhigh", "max"], required=True
    )
    parser.add_argument(
        "--protocol",
        choices=["continuous", "handoff"],
        default="handoff",
        help="reuse one model thread or start a fresh thread for every milestone",
    )
    parser.add_argument(
        "--candidate-tests",
        choices=CANDIDATE_TEST_POLICIES,
        default="endogenous",
        help="provide canonical milestone tests or rely on the candidate-authored suite",
    )
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--codex", type=Path, default=DEFAULT_CODEX)
    parser.add_argument("--claude", type=Path, default=DEFAULT_CLAUDE)
    parser.add_argument("--opencode", type=Path, default=DEFAULT_OPENCODE)
    parser.add_argument(
        "--workspace-parent",
        type=Path,
        help="preassigned private parent for the candidate workspace, temp, and XDG state",
    )
    parser.add_argument("--docker", type=Path, default=DEFAULT_DOCKER)
    parser.add_argument(
        "--container-image",
        help="run the candidate harness inside this Docker image",
    )
    parser.add_argument(
        "--opencode-auth-file",
        type=Path,
        help="seed a private OpenCode credential from this auth.json file",
    )
    parser.add_argument(
        "--opencode-auth-provider",
        default="openai",
        help="copy only this provider from --opencode-auth-file",
    )
    parser.add_argument(
        "--barrier-dir",
        type=Path,
        help="coordinate parallel candidates so agent and private-evaluation phases never overlap",
    )
    parser.add_argument(
        "--barrier-size",
        type=int,
        help="number of candidates participating in the parallel milestone barrier",
    )
    parser.add_argument(
        "--parallel-audit",
        action="store_true",
        help="reject host process inspection without coupling candidates at a barrier",
    )
    parser.add_argument(
        "--benchmark-ref",
        default="HEAD",
        help="benchmark tag or commit recorded independently from the runner commit",
    )
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help="continue an incomplete handoff run from its last accepted milestone snapshot",
    )
    parser.add_argument(
        "--max-milestones",
        type=int,
        help="run at most this many milestones, then pause for a later handoff resume",
    )
    parser.add_argument(
        "--opencode-provider-failure-limit",
        type=int,
        default=OPENCODE_MAX_ATTEMPTS,
        help="stop an OpenCode milestone after this many provider failures",
    )
    parser.add_argument(
        "--prompt-suffix",
        help="append a recorded experimental instruction to every candidate milestone prompt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = execute(args)
    except (OSError, RuntimeError, ValueError) as error:
        signal_barrier_abort(args.barrier_dir, args.label, str(error))
        print(f"error: {error}", file=sys.stderr)
        return 2
    if result != 0:
        signal_barrier_abort(args.barrier_dir, args.label, "candidate trajectory failed")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
