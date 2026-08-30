import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

import run_candidate


class CandidateRunnerTest(unittest.TestCase):
    @mock.patch(
        "run_candidate.git_commit", side_effect=["restore-commit", "request-commit"]
    )
    @mock.patch("run_candidate.checked")
    @mock.patch(
        "run_candidate.subprocess.check_output",
        side_effect=["benchmark-commit\n", "runner-commit\n"],
    )
    def test_resume_restores_last_snapshot_and_archives_interrupted_stage(
        self, _check_output, checked, _git_commit
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_root = root / "runs" / "candidate-01"
            snapshot = run_root / "snapshots" / "milestone-1"
            snapshot.mkdir(parents=True)
            (snapshot / "kept.txt").write_text("accepted\n")
            (snapshot / ".group-stay-work.json").write_text(
                json.dumps({"request": 1, "example_tests": "none"})
            )
            logs = run_root / "logs"
            logs.mkdir()
            interrupted = logs / "agent-2.jsonl"
            interrupted.write_text('{"type":"error"}\n')
            original_workspace = root / "candidate" / "groupstay"
            catalogue = (
                original_workspace.parent
                / "container-state"
                / "xdg"
                / "cache"
                / "opencode"
                / "models.json"
            )
            catalogue.parent.mkdir(parents=True)
            catalogue.write_text("frozen catalogue\n")
            state = {
                "label": "candidate-01",
                "model": "openrouter/example/model",
                "reasoning_effort": "high",
                "protocol": "handoff",
                "candidate_tests": "endogenous",
                "benchmark_commit": "benchmark-commit",
                "harness": {"name": "opencode", "version": "test"},
                "workspace": str(original_workspace),
                "thread_id": None,
                "milestones": [{"milestone": 1, "report": "report.json"}],
                "failed_at": {"milestone": 2},
            }
            (run_root / "state.json").write_text(json.dumps(state))
            args = Namespace(
                label="candidate-01",
                model="openrouter/example/model",
                effort="high",
                protocol="handoff",
                candidate_tests="endogenous",
                harness="opencode",
                benchmark_ref="sweat-bench-v6",
                workspace_parent=root / "candidate",
                container_image="sweat-bench-opencode:test",
                opencode_auth_file=None,
            )

            resumed, start_stage, thread_id = run_candidate.prepare_resumed_run(
                run_root, args
            )

            workspace = (root / "candidate").resolve() / "resume-01" / "groupstay"
            self.assertEqual(2, start_stage)
            self.assertIsNone(thread_id)
            self.assertEqual("accepted\n", (workspace / "kept.txt").read_text())
            self.assertEqual(str(workspace), resumed["workspace"])
            self.assertNotIn("failed_at", resumed)
            self.assertEqual(
                "frozen catalogue\n",
                (
                    workspace.parent
                    / "container-state"
                    / "xdg"
                    / "cache"
                    / "opencode"
                    / "models.json"
                ).read_text(),
            )
            self.assertFalse(interrupted.exists())
            self.assertTrue(
                (
                    run_root
                    / "interrupted-attempts"
                    / "resume-01"
                    / interrupted.name
                ).is_file()
            )
            self.assertTrue(
                any(
                    "advance" in call.args[0] and "2" in call.args[0]
                    for call in checked.call_args_list
                )
            )

    @mock.patch(
        "run_candidate.subprocess.check_output",
        side_effect=["benchmark-commit\n", "runner-commit\n"],
    )
    def test_resume_continues_interrupted_first_milestone_session(self, _check_output):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_root = root / "runs" / "candidate-01"
            workspace = root / "candidate" / "groupstay"
            workspace.mkdir(parents=True)
            (workspace / ".group-stay-work.json").write_text(
                json.dumps({"request": 1, "example_tests": "none"})
            )
            state = {
                "label": "candidate-01",
                "model": "openrouter/example/model",
                "reasoning_effort": "high",
                "protocol": "handoff",
                "candidate_tests": "endogenous",
                "benchmark_commit": "benchmark-commit",
                "harness": {"name": "opencode", "version": "test"},
                "workspace": str(workspace),
                "thread_id": None,
                "milestones": [],
                "failed_at": {"milestone": 1, "thread_id": "session-123"},
            }
            run_root.mkdir(parents=True)
            (run_root / "state.json").write_text(json.dumps(state))
            args = Namespace(
                label="candidate-01",
                model="openrouter/example/model",
                effort="high",
                protocol="handoff",
                candidate_tests="endogenous",
                harness="opencode",
                benchmark_ref="sweat-bench-v6",
                workspace_parent=root / "candidate",
                container_image="sweat-bench-opencode:test",
                opencode_auth_file=None,
            )

            resumed, start_stage, thread_id = run_candidate.prepare_resumed_run(
                run_root, args
            )

            self.assertEqual(1, start_stage)
            self.assertEqual("session-123", thread_id)
            self.assertEqual(str(workspace), resumed["workspace"])
            self.assertNotIn("failed_at", resumed)
            self.assertEqual("interrupted_stage", resumed["resumptions"][0]["mode"])

    @mock.patch(
        "run_candidate.git_commit", side_effect=["restore-commit", "request-commit"]
    )
    @mock.patch("run_candidate.checked")
    @mock.patch(
        "run_candidate.subprocess.check_output",
        side_effect=["benchmark-commit\n", "runner-commit\n"],
    )
    def test_resume_uses_stable_workspace_parent_for_legacy_nested_state(
        self, _check_output, _checked, _git_commit
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_root = root / "runs" / "candidate-01"
            snapshot = run_root / "snapshots" / "milestone-2"
            snapshot.mkdir(parents=True)
            (snapshot / "kept.txt").write_text("accepted\n")
            initial_workspace = root / "candidate" / "groupstay"
            nested_workspace = root / "candidate" / "resume-01" / "groupstay"
            state = {
                "label": "candidate-01",
                "model": "gpt-5.6-luna",
                "reasoning_effort": "xhigh",
                "protocol": "handoff",
                "candidate_tests": "endogenous",
                "benchmark_commit": "benchmark-commit",
                "harness": {"name": "codex", "version": "test"},
                "workspace": str(nested_workspace),
                "milestones": [{"milestone": 1}, {"milestone": 2}],
                "resumptions": [
                    {
                        "previous_workspace": str(initial_workspace),
                        "workspace": str(nested_workspace),
                    }
                ],
            }
            (run_root / "state.json").write_text(json.dumps(state))
            args = Namespace(
                label="candidate-01",
                model="gpt-5.6-luna",
                effort="xhigh",
                protocol="handoff",
                candidate_tests="endogenous",
                harness="codex",
                benchmark_ref="sweat-bench-v6",
                workspace_parent=None,
                container_image=None,
                opencode_auth_file=None,
            )

            resumed, start_stage, _thread_id = run_candidate.prepare_resumed_run(
                run_root, args
            )

            expected_parent = (root / "candidate").resolve()
            expected_workspace = expected_parent / "resume-02" / "groupstay"
            self.assertEqual(3, start_stage)
            self.assertEqual(str(expected_parent), resumed["workspace_parent"])
            self.assertEqual(str(expected_workspace), resumed["workspace"])
            self.assertFalse(
                str(expected_workspace).startswith(str(nested_workspace.parent))
            )

    def test_codex_command_uses_clean_config_workspace_sandbox_and_network(self):
        command = run_candidate.codex_command(
            Path("/opt/codex"),
            Path("/private/tmp/northstar/abc/groupstay"),
            "gpt-5.6-luna",
            "xhigh",
            None,
        )

        self.assertIn("--approve-for-me", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertIn("sandbox_workspace_write.network_access=true", command)
        self.assertNotIn("--sandbox", command)
        self.assertNotIn(str(run_candidate.ROOT), command)

    @mock.patch("run_candidate.terminate_workspace_beams", return_value=[])
    def test_agent_phase_does_not_revoke_repository_access(self, _terminate):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output = workspace / "agent.log"
            command = [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "raise SystemExit(0 if "
                    f"Path({str(run_candidate.ROOT / 'benchmark.json')!r}).is_file() else 1)"
                ),
            ]

            exit_code, terminated = run_candidate.run_agent(
                command, workspace=workspace, output=output
            )

            self.assertEqual(0, exit_code)
            self.assertEqual([], terminated)

    @mock.patch("run_candidate.terminate_workspace_beams", return_value=[])
    def test_agent_retry_appends_to_the_existing_log(self, _terminate):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output = workspace / "agent.log"

            run_candidate.run_agent(
                [sys.executable, "-c", "print('first')"],
                workspace=workspace,
                output=output,
            )
            run_candidate.run_agent(
                [sys.executable, "-c", "print('second')"],
                workspace=workspace,
                output=output,
                append=True,
            )

            self.assertEqual(["first", "second"], output.read_text().splitlines())

    @mock.patch("run_candidate.terminate_workspace_beams", return_value=[])
    def test_agent_receives_a_workspace_private_temporary_directory(self, _terminate):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate" / "groupstay"
            workspace.mkdir(parents=True)
            output = workspace / "agent.log"

            exit_code, _terminated = run_candidate.run_agent(
                [
                    sys.executable,
                    "-c",
                    "import os; print(os.environ['TMPDIR'])",
                ],
                workspace=workspace,
                output=output,
            )

            self.assertEqual(0, exit_code)
            self.assertEqual(str(workspace.parent / "tmp"), output.read_text().strip())

    @mock.patch("run_candidate.terminate_workspace_beams", return_value=[])
    def test_agent_receives_workspace_private_opencode_state_directories(self, _terminate):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate" / "groupstay"
            workspace.mkdir(parents=True)
            output = workspace / "agent.log"

            exit_code, _terminated = run_candidate.run_agent(
                [
                    sys.executable,
                    "-c",
                    (
                        "import os; "
                        "print(os.environ['XDG_DATA_HOME']); "
                        "print(os.environ['XDG_CACHE_HOME'])"
                    ),
                ],
                workspace=workspace,
                output=output,
                private_xdg=True,
            )

            self.assertEqual(0, exit_code)
            self.assertEqual(
                [
                    str(workspace.parent / "xdg" / "data"),
                    str(workspace.parent / "xdg" / "cache"),
                ],
                output.read_text().splitlines(),
            )

    @mock.patch("run_candidate.subprocess.run")
    def test_containerized_agent_mounts_only_workspace_and_private_state(self, run):
        run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate" / "groupstay"
            workspace.mkdir(parents=True)
            output = workspace.parent / "agent.log"

            exit_code, terminated = run_candidate.run_agent(
                ["/usr/local/bin/opencode", "run"],
                workspace=workspace,
                output=output,
                docker=Path("/usr/local/bin/docker"),
                container_image="sweat-bench-opencode:test",
            )

            command = run.call_args.args[0]
            self.assertEqual(0, exit_code)
            self.assertEqual([], terminated)
            self.assertEqual("/usr/local/bin/docker", command[0])
            self.assertEqual(2, command.count("--mount"))
            self.assertIn(f"type=bind,src={workspace},dst=/workspace", command)
            self.assertIn(
                f"type=bind,src={workspace.parent / 'container-state'},dst=/state",
                command,
            )
            self.assertIn("MIX_BUILD_PATH=/state/build", command)
            self.assertNotIn(str(run_candidate.ROOT), command)
            self.assertNotIn("/var/run/docker.sock", command)
            self.assertNotIn("OPENROUTER_API_KEY", command)

    def test_seed_opencode_auth_copies_only_requested_oauth_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            target = root / "private" / "auth.json"
            source.write_text(
                json.dumps(
                    {
                        "openai": {"type": "oauth", "access": "secret"},
                        "openrouter": {"type": "api", "key": "other-secret"},
                    }
                )
            )

            run_candidate.seed_opencode_auth(source, target, "openai")

            self.assertEqual(
                {"openai": {"type": "oauth", "access": "secret"}},
                json.loads(target.read_text()),
            )
            self.assertEqual(0o600, target.stat().st_mode & 0o777)

    def test_seed_opencode_auth_rejects_api_key_for_openai_subscription(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps({"openai": {"type": "api", "key": "x"}}))

            with self.assertRaisesRegex(ValueError, "require an OAuth credential"):
                run_candidate.seed_opencode_auth(
                    source, root / "target.json", "openai"
                )

    @mock.patch("run_candidate.subprocess.run")
    def test_containerized_agent_passes_only_requested_environment(self, run):
        run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate" / "groupstay"
            workspace.mkdir(parents=True)

            run_candidate.run_agent(
                ["/usr/local/bin/opencode", "run"],
                workspace=workspace,
                output=workspace.parent / "agent.log",
                docker=Path("/usr/local/bin/docker"),
                container_image="sweat-bench-opencode:test",
                container_environment=("OPENROUTER_API_KEY",),
            )

            self.assertIn("OPENROUTER_API_KEY", run.call_args.args[0])

    def test_parallel_audit_rejects_process_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "tool_use",
                        "part": {
                            "type": "tool",
                            "tool": "bash",
                            "state": {
                                "input": {
                                    "command": "ps aux; ls /private/tmp/northstar/peer/groupstay"
                                }
                            },
                        },
                    }
                )
                + "\n"
            )

            audit = run_candidate.audit_agent_log(
                log,
                parallel=True,
            )

            self.assertEqual("failed", audit["status"])
            self.assertIn("host process inspection", audit["hits"][0]["fragments"])

    def test_parallel_audit_does_not_treat_top_level_label_as_process_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "type": "command_execution",
                            "command": (
                                "/bin/zsh -lc \"pwd && printf "
                                "'\\\\n--- top-level ---\\\\n' && ls -la\""
                            ),
                        },
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "passed",
                run_candidate.audit_agent_log(log, parallel=True)["status"],
            )

    def test_log_readers_ignore_json_scalars(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                '"stream preamble"\n'
                + json.dumps(
                    {"type": "thread.started", "thread_id": "thread-123"}
                )
                + "\n"
            )

            self.assertEqual("thread-123", run_candidate.find_thread_id(log))
            self.assertEqual(
                "passed",
                run_candidate.audit_agent_log(log, parallel=True)["status"],
            )

    def test_parallel_audit_rejects_wrapped_process_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "type": "command_execution",
                            "command": '/bin/zsh -lc "pwd && ps aux"',
                        },
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "failed",
                run_candidate.audit_agent_log(log, parallel=True)["status"],
            )

    def test_parallel_audit_flag_is_independent_from_barriers(self):
        args = run_candidate.build_parser().parse_args(
            [
                "--label",
                "candidate-01",
                "--model",
                "gpt-5.6-sol",
                "--effort",
                "high",
                "--parallel-audit",
            ]
        )

        self.assertTrue(args.parallel_audit)
        self.assertIsNone(args.barrier_dir)

    def test_container_pid_namespace_disables_host_process_audit(self):
        self.assertFalse(
            run_candidate.host_process_audit_required(
                parallel_audit=True,
                barrier_dir=None,
                container_image="sweat-bench-opencode:test",
            )
        )
        self.assertTrue(
            run_candidate.host_process_audit_required(
                parallel_audit=True,
                barrier_dir=None,
                container_image=None,
            )
        )
        self.assertTrue(
            run_candidate.host_process_audit_required(
                parallel_audit=False,
                barrier_dir=Path("/tmp/cohort"),
                container_image=None,
            )
        )

    def test_max_milestones_parses_for_handoff_runs(self):
        args = run_candidate.build_parser().parse_args(
            [
                "--label",
                "candidate-01",
                "--model",
                "claude-opus-5",
                "--effort",
                "high",
                "--harness",
                "claude",
                "--max-milestones",
                "1",
            ]
        )

        self.assertEqual(1, args.max_milestones)
        self.assertEqual("handoff", args.protocol)

    def test_parallel_audit_allows_own_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            workspace = Path("/private/tmp/northstar/own/groupstay")
            log.write_text(
                json.dumps(
                    {
                        "type": "tool_use",
                        "part": {
                            "type": "tool",
                            "tool": "bash",
                            "state": {
                                "input": {"command": f"find {workspace} -type f"}
                            },
                        },
                    }
                )
                + "\n"
            )

            audit = run_candidate.audit_agent_log(
                log,
                parallel=True,
            )

            self.assertEqual("passed", audit["status"])

    def test_single_member_barrier_releases_immediately(self):
        with tempfile.TemporaryDirectory() as directory:
            barrier = Path(directory)

            run_candidate.await_cohort_barrier(
                barrier,
                1,
                label="candidate-01",
                milestone=2,
                phase="agent-finished",
            )

            self.assertTrue(
                (barrier / "milestone-2" / "agent-finished" / "candidate-01.ready").is_file()
            )

    def test_barrier_aborts_when_a_peer_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            barrier = Path(directory)
            run_candidate.signal_barrier_abort(barrier, "candidate-02", "failed")

            with self.assertRaisesRegex(RuntimeError, "parallel cohort aborted"):
                run_candidate.await_cohort_barrier(
                    barrier,
                    2,
                    label="candidate-01",
                    milestone=2,
                    phase="agent-finished",
                )

    def test_resume_command_keeps_the_same_thread(self):
        command = run_candidate.codex_command(
            Path("/opt/codex"),
            Path("/private/tmp/northstar/abc/groupstay"),
            "gpt-5.6-sol",
            "high",
            "thread-123",
        )

        self.assertEqual(command[command.index("exec") + 1 : command.index("--json")], ["resume", "thread-123"])

    def test_thread_id_is_read_from_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps({"type": "thread.started", "thread_id": "thread-123"}) + "\n"
            )

            self.assertEqual(run_candidate.find_thread_id(log), "thread-123")

    def test_claude_command_uses_clean_mode_and_requested_effort(self):
        command = run_candidate.claude_command(
            Path("/opt/claude"),
            "claude-opus-5",
            "high",
            None,
        )

        self.assertIn("--safe-mode", command)
        self.assertIn("--dangerously-skip-permissions", command)
        self.assertIn("--no-chrome", command)
        self.assertEqual(command[command.index("--effort") + 1], "high")
        self.assertEqual(command[command.index("--model") + 1], "claude-opus-5")
        self.assertNotIn(str(run_candidate.ROOT), command)

    def test_claude_session_id_is_read_from_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps({"type": "system", "session_id": "claude-session-123"})
                + "\n"
            )

            self.assertEqual(run_candidate.find_thread_id(log), "claude-session-123")

    def test_opencode_command_uses_pure_auto_mode_and_requested_variant(self):
        workspace = Path("/private/tmp/northstar/abc/groupstay")
        command = run_candidate.opencode_command(
            Path("/opt/opencode"),
            workspace,
            "openrouter/moonshotai/kimi-k3",
            "max",
            None,
        )

        self.assertIn("--pure", command)
        self.assertIn("--auto", command)
        self.assertIn("--thinking", command)
        self.assertEqual(command[command.index("--variant") + 1], "max")
        self.assertEqual(
            command[command.index("--model") + 1],
            "openrouter/moonshotai/kimi-k3",
        )
        self.assertEqual(command[command.index("--dir") + 1], str(workspace))
        self.assertNotIn(str(run_candidate.ROOT), command)

    def test_opencode_session_id_is_read_from_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps({"type": "step_start", "sessionID": "opencode-session-123"})
                + "\n"
            )

            self.assertEqual(run_candidate.find_thread_id(log), "opencode-session-123")

    def test_opencode_resume_uses_the_same_session(self):
        command = run_candidate.opencode_command(
            Path("/opt/opencode"),
            Path("/private/tmp/northstar/abc/groupstay"),
            "openrouter/z-ai/glm-5.3",
            "max",
            "opencode-session-123",
        )

        self.assertEqual(
            command[command.index("--session") + 1], "opencode-session-123"
        )

    def test_opencode_provider_unavailable_is_transient(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            message = json.dumps(
                {
                    "code": 502,
                    "message": "upstream provider returned an error",
                    "metadata": {"error_type": "provider_unavailable"},
                }
            )
            log.write_text(
                json.dumps(
                    {
                        "type": "error",
                        "error": {"data": {"message": message}},
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "provider_unavailable (502)",
                run_candidate.opencode_retry_reason(log),
            )

    def test_opencode_database_lock_is_retryable_without_a_session(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text("Error: Unexpected error\n\ndatabase is locked\n")

            self.assertEqual(
                "local_database_locked",
                run_candidate.opencode_retry_reason(log),
            )

    def test_opencode_structured_database_lock_is_retryable(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "error",
                        "error": {"message": "database is locked"},
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "local_database_locked",
                run_candidate.opencode_retry_reason(log),
            )

    def test_opencode_candidate_database_lock_discussion_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "reasoning",
                        "part": {
                            "text": "The candidate database is locked while a test exits."
                        },
                    }
                )
                + "\n"
                + json.dumps(
                    {"type": "step_finish", "part": {"reason": "stop"}}
                )
                + "\n"
            )

            self.assertIsNone(run_candidate.opencode_retry_reason(log))

    def test_opencode_unexpected_server_error_is_retryable(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "data": {
                                "message": "Unexpected server error. Check server logs for details.",
                                "ref": "err_example",
                            }
                        },
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "provider_server_error",
                run_candidate.opencode_retry_reason(log),
            )

    def test_opencode_length_limit_resumes_the_same_session(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "step_finish",
                        "sessionID": "opencode-session-123",
                        "part": {"reason": "length"},
                    }
                )
                + "\n"
            )

            self.assertEqual(
                "turn_length_limit",
                run_candidate.opencode_retry_reason(log),
            )

    def test_opencode_normal_stop_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "step_finish",
                        "part": {"reason": "stop"},
                    }
                )
                + "\n"
            )

            self.assertIsNone(run_candidate.opencode_retry_reason(log))

    def test_opencode_nontransient_or_recovered_log_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "agent.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "data": {
                                "message": json.dumps(
                                    {
                                        "code": 400,
                                        "metadata": {"error_type": "invalid_request"},
                                    }
                                )
                            }
                        },
                    }
                )
                + "\n"
            )
            self.assertIsNone(run_candidate.opencode_retry_reason(log))

            with log.open("a") as stream:
                stream.write(
                    json.dumps(
                        {"type": "step_finish", "part": {"reason": "stop"}}
                    )
                    + "\n"
                )
            self.assertIsNone(run_candidate.opencode_retry_reason(log))

    def test_continuous_protocol_resumes_after_the_first_milestone(self):
        self.assertEqual(
            run_candidate.INITIAL_PROMPT,
            run_candidate.agent_prompt("continuous", 1),
        )
        self.assertEqual(
            run_candidate.CONTINUE_PROMPT,
            run_candidate.agent_prompt("continuous", 2),
        )
        self.assertEqual("thread-123", run_candidate.resume_thread_id("continuous", "thread-123"))

    def test_handoff_protocol_starts_every_milestone_fresh(self):
        self.assertEqual(
            run_candidate.INITIAL_PROMPT,
            run_candidate.agent_prompt("handoff", 1),
        )
        self.assertEqual(
            run_candidate.INITIAL_PROMPT,
            run_candidate.agent_prompt("handoff", 7),
        )
        self.assertIsNone(run_candidate.resume_thread_id("handoff", "thread-123"))

    def test_agent_prompt_appends_experimental_suffix(self):
        suffix = "Use one focused subagent."

        self.assertEqual(
            run_candidate.INITIAL_PROMPT.rstrip() + "\n\n" + suffix + "\n",
            run_candidate.agent_prompt("handoff", 1, suffix),
        )

    def test_test_inventory_records_files_hashes_and_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            test = workspace / "test/example_test.exs"
            test.parent.mkdir()
            test.write_text('defmodule ExampleTest do\n  test "works" do\n  end\nend\n')

            inventory = run_candidate.test_inventory(workspace)

            self.assertEqual(1, inventory["file_count"])
            self.assertEqual(1, inventory["test_declarations"])
            self.assertEqual("test/example_test.exs", inventory["files"][0]["path"])
            self.assertEqual(64, len(inventory["files"][0]["sha256"]))

    def test_integrity_audit_rejects_referee_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory) / "clean.jsonl"
            clean.write_text('{"path":"/private/tmp/northstar/abc/groupstay/lib/x.ex"}\n')
            leaked = Path(directory) / "leaked.jsonl"
            leaked.write_text(json.dumps({"path": str(run_candidate.ROOT / "benchmark.json")}) + "\n")

            self.assertEqual(run_candidate.audit_agent_log(clean)["status"], "passed")
            self.assertEqual(run_candidate.audit_agent_log(leaked)["status"], "failed")

    def test_trajectory_scores_unique_ship_and_final_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            milestones = []
            cumulative = set()

            for milestone in range(1, 8):
                introduced = run_candidate.introduced_case_ids(milestone)
                cumulative |= introduced
                statuses = {identifier: "passed" for identifier in cumulative}
                if milestone == 2:
                    statuses[next(iter(introduced))] = "failed"
                if milestone == 4:
                    statuses[next(iter(run_candidate.introduced_case_ids(1)))] = "failed"

                system_names = {
                    2: ["policy-upgrade", "policy-history-upgrade"],
                    3: ["idempotency-restart"],
                    4: ["payment-reduction-upgrade", "room-history-upgrade"],
                    5: ["transfer-upgrade", "payment-history-upgrade"],
                    6: ["finance-reporting-upgrade", "projection-history-upgrade"],
                    7: ["finance-close-upgrade", "close-history-upgrade"],
                }
                report = {
                    "status": "failed" if "failed" in statuses.values() else "passed",
                    "tests": [
                        {"id": identifier, "status": status}
                        for identifier, status in sorted(statuses.items())
                    ],
                    "system_checks": [
                        {"name": name, "status": "passed"}
                        for name in system_names.get(milestone, [])
                    ],
                }
                path = root / f"milestone-{milestone}.json"
                path.write_text(json.dumps(report))
                milestones.append({"milestone": milestone, "report": str(path)})

            scores = run_candidate.trajectory_scores(milestones)
            self.assertEqual(1, scores["prefix_depth"])
            self.assertEqual({"passed": 48, "total": 49}, scores["ship_time"])
            self.assertEqual({"passed": 49, "total": 49}, scores["final_state"])
            self.assertEqual(
                {"passed": 38, "total": 39}, scores["tracks"]["core"]["ship_time"]
            )
            self.assertEqual(
                {"passed": 10, "total": 10},
                scores["tracks"]["judgment"]["final_state"],
            )
            self.assertEqual(
                {"passed": 93, "total": 94}, scores["scenarios"]["ship_time"]
            )
            self.assertEqual(
                {"passed": 94, "total": 94}, scores["scenarios"]["final_state"]
            )
            self.assertEqual(1, scores["regression_episodes"]["count"])
            [episode] = scores["regression_episodes"]["episodes"]
            self.assertEqual(4, episode["opened_at"])
            self.assertEqual(5, episode["recovered_at"])

    def test_prefix_depth_uses_core_families_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            milestones = []
            cumulative = set()

            for milestone in range(1, 8):
                cumulative |= run_candidate.introduced_case_ids(milestone)
                statuses = {identifier: "passed" for identifier in cumulative}
                if milestone == 6:
                    judgment_family = next(
                        family
                        for family in run_candidate.family_definitions(6)
                        if family.get("track") == "judgment" and family["members"]
                    )
                    statuses[judgment_family["members"][0]] = "failed"

                report = {
                    "status": "failed" if "failed" in statuses.values() else "passed",
                    "tests": [
                        {"id": identifier, "status": status}
                        for identifier, status in sorted(statuses.items())
                    ],
                    "system_checks": [
                        {"name": name, "status": "passed"}
                        for name in {
                            2: ["policy-upgrade", "policy-history-upgrade"],
                            3: ["idempotency-restart"],
                            4: ["payment-reduction-upgrade", "room-history-upgrade"],
                            5: ["transfer-upgrade", "payment-history-upgrade"],
                            6: ["finance-reporting-upgrade", "projection-history-upgrade"],
                            7: ["finance-close-upgrade", "close-history-upgrade"],
                        }.get(milestone, [])
                    ],
                }
                path = root / f"milestone-{milestone}.json"
                path.write_text(json.dumps(report))
                milestones.append({"milestone": milestone, "report": str(path)})

            scores = run_candidate.trajectory_scores(milestones)
            self.assertEqual(7, scores["prefix_depth"])
            self.assertEqual(
                {"passed": 9, "total": 10},
                scores["tracks"]["judgment"]["ship_time"],
            )


if __name__ == "__main__":
    unittest.main()
