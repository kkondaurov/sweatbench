import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import bench


class BenchmarkStructureTest(unittest.TestCase):
    def test_manifest_is_consecutive_and_complete(self):
        manifest = bench.load_manifest()
        self.assertEqual([1, 2, 3, 4, 5, 6, 7], [stage["id"] for stage in manifest["stages"]])
        self.assertEqual(
            [12, 22, 29, 50, 61, 73, 83],
            [stage["expected_private_cases"] for stage in manifest["stages"]],
        )

        for stage in manifest["stages"]:
            self.assertTrue((bench.ROOT / stage["request"]).is_file())
            self.assertTrue((bench.ROOT / stage["public_test"]).is_file())
            for private_test in stage["private_tests"]:
                self.assertTrue((bench.ROOT / private_test).is_file())

        self.assertEqual(
            [2, 2, 3, 4, 4, 5, 5, 6, 6, 7, 7],
            [check["after_stage"] for check in manifest["system_checks"]],
        )
        for check in manifest["system_checks"]:
            self.assertTrue((bench.ROOT / check["scenario"]).is_file())

    def test_milestone_one_packet_does_not_leak_future_work(self):
        names = {path.name for path in bench.candidate_packet(1)}
        self.assertIn("01-operational-core.md", names)
        self.assertIn("01_operational_core_test.exs", names)
        self.assertNotIn("02-cancellation-economics.md", names)
        self.assertNotIn("04_room_accounting_test.exs", names)

    def test_model_packet_avoids_evaluation_language(self):
        text = "\n".join(path.read_text().lower() for path in bench.candidate_packet(7))
        for term in ("hidden test", "withheld", "evaluator", "benchmark score"):
            self.assertNotIn(term, text)

    def test_starter_has_no_product_implementation(self):
        starter = bench.ROOT / "candidate/starter"
        self.assertEqual([], list((starter / "priv/repo/migrations").glob("[0-9]*.exs")))

        router = (starter / "lib/group_stay_web/router.ex").read_text()
        for route in ("get ", "post ", "put ", "patch ", "delete "):
            self.assertNotIn(route, router)

        test_config = (starter / "config/test.exs").read_text()
        self.assertNotIn("server: false", test_config)

    def test_materialize_then_advance_preserves_milestone_history(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            bench.materialize(1, workspace)

            self.assertTrue((workspace / "docs/requests/01-operational-core.md").is_file())
            self.assertFalse(
                (workspace / "docs/requests/02-cancellation-economics.md").exists()
            )
            self.assertFalse((workspace / "evaluation").exists())

            bench.advance(2, workspace)

            self.assertTrue((workspace / "docs/requests/01-operational-core.md").is_file())
            self.assertTrue(
                (workspace / "docs/requests/02-cancellation-economics.md").is_file()
            )
            self.assertEqual(2, json.loads((workspace / bench.MARKER).read_text())["request"])

    def test_endogenous_packet_never_installs_canonical_milestone_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            bench.materialize(1, workspace, "endogenous")

            marker = json.loads((workspace / bench.MARKER).read_text())
            self.assertEqual("none", marker["example_tests"])
            self.assertEqual([], marker["installed_examples"])
            self.assertNotIn("candidate", marker)
            self.assertNotIn("provided", marker)
            self.assertEqual([], list((workspace / "test/acceptance").glob("*.exs")))
            self.assertIn(
                "Decide what needs verification", (workspace / "TASK.md").read_text()
            )

            for milestone in range(2, 8):
                bench.advance(milestone, workspace)

                marker = json.loads((workspace / bench.MARKER).read_text())
                self.assertEqual("none", marker["example_tests"])
                self.assertEqual([], marker["installed_examples"])
                self.assertEqual(
                    [], list((workspace / "test/acceptance").glob("*.exs"))
                )

    def test_candidate_test_policy_cannot_change_mid_trajectory(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            bench.materialize(1, workspace, "endogenous")

            with self.assertRaisesRegex(ValueError, "cannot change"):
                bench.advance(2, workspace, "canonical")

    def test_later_milestone_cannot_start_from_the_scaffold(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "only milestone 1"):
                bench.materialize(2, Path(directory) / "candidate")

    def test_upgrade_check_requires_the_previous_milestone(self):
        with self.assertRaisesRegex(ValueError, "requires --previous"):
            bench.system_commands(2, Path("current"), None)

        commands = bench.system_commands(2, Path("current"), Path("previous"))
        self.assertEqual(
            ["policy-upgrade", "policy-history-upgrade"],
            [item[2] for item in commands],
        )
        self.assertTrue(all(item[-2:] == ["previous", "current"] for item in commands))

    def test_family_results_matches_system_checks_by_name(self):
        family = {
            "id": "migration",
            "members": [],
            "system_checks": ["expected-upgrade"],
        }

        with mock.patch("bench.stage_families", return_value=[family]):
            [wrong_check] = bench.family_results(
                1, [], [{"name": "other-upgrade", "status": "passed"}]
            )
            [right_check] = bench.family_results(
                1, [], [{"name": "expected-upgrade", "status": "passed"}]
            )

        self.assertEqual("failed", wrong_check["status"])
        self.assertEqual(["system:expected-upgrade"], wrong_check["failing_members"])
        self.assertEqual("passed", right_check["status"])

    def test_snapshot_preserves_source_and_dependencies_without_build_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            saved = Path(directory) / "milestone-1"
            bench.materialize(1, workspace)
            (workspace / "_build").mkdir()
            (workspace / "_build/generated").write_text("ignore me")
            (workspace / "deps/example").mkdir(parents=True)
            (workspace / "deps/example/mix.exs").write_text("dependency source")

            bench.snapshot(workspace, saved)

            self.assertTrue((saved / bench.MARKER).is_file())
            self.assertTrue((saved / "lib/group_stay.ex").is_file())
            self.assertTrue((saved / "deps/example/mix.exs").is_file())
            self.assertFalse((saved / "_build").exists())

    def test_evaluate_uses_a_fresh_database_and_writes_scenario_results(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            report_path = Path(directory) / "milestone-1.json"
            bench.materialize(1, workspace)
            conn_case = workspace / "test/support/conn_case.ex"
            candidate_conn_case = conn_case.read_text() + "\n# candidate customization\n"
            conn_case.write_text(candidate_conn_case)
            conn_case_beam = (
                workspace
                / "_build/test/lib/group_stay/test/Elixir.GroupStayWeb.ConnCase.beam"
            )
            conn_case_beam.parent.mkdir(parents=True)
            conn_case_beam.write_bytes(b"compiled evaluator case")
            commands = []

            def fake_run(command, cwd, env=None, check=False):
                commands.append((command, cwd, env, check))
                if command[:2] == ["mix", "test"]:
                    self.assertEqual(
                        (
                            bench.ROOT
                            / bench.load_manifest()["starter"]
                            / "test/support/conn_case.ex"
                        ).read_text(),
                        conn_case.read_text(),
                    )
                    Path(env["GROUP_STAY_TEST_RESULT_PATH"]).write_text(
                        json.dumps(
                            {
                                "tests": [
                                    {
                                        "id": "Example::works",
                                        "name": "works",
                                        "module": "Example",
                                        "status": "passed",
                                        "time_us": 10,
                                    }
                                ]
                            }
                        )
                    )
                return mock.Mock(returncode=0)

            with mock.patch("bench.subprocess.run", side_effect=fake_run):
                result = bench.evaluate(1, workspace, report_path=report_path)

            self.assertEqual(1, result)
            self.assertEqual(["mix", "ecto.create", "--quiet"], commands[0][0])
            self.assertEqual(["mix", "ecto.migrate", "--quiet"], commands[1][0])
            self.assertEqual(["mix", "test"], commands[2][0][:2])
            self.assertIn("ExUnit.CLIFormatter", commands[2][0])
            self.assertIn("GroupStay.TestReportFormatter", commands[2][0])
            self.assertEqual("0", commands[2][0][commands[2][0].index("--seed") + 1])
            self.assertIn("GROUP_STAY_DATABASE_PATH", commands[0][2])
            self.assertFalse(
                (workspace / "test/support/group_stay_test_report_formatter.ex").exists()
            )
            self.assertEqual(candidate_conn_case, conn_case.read_text())
            self.assertFalse(conn_case_beam.exists())

            report = json.loads(report_path.read_text())
            self.assertEqual({"passed": 1, "total": 12}, report["summary"])
            self.assertEqual({"passed": 0, "total": 6}, report["family_summary"])
            self.assertEqual("failed", report["status"])
            self.assertEqual("passed", report["tests"][0]["status"])

    def test_setup_failure_reports_zero_of_the_expected_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "candidate"
            report_path = Path(directory) / "milestone-1.json"
            bench.materialize(1, workspace)

            with mock.patch("bench.subprocess.run", return_value=mock.Mock(returncode=1)):
                result = bench.evaluate(1, workspace, report_path=report_path)

            self.assertEqual(1, result)
            report = json.loads(report_path.read_text())
            self.assertEqual("failed", report["status"])
            self.assertEqual([], report["tests"])
            self.assertEqual({"passed": 0, "total": 12}, report["summary"])
            self.assertEqual("fresh test database preparation failed", report["setup_error"])


if __name__ == "__main__":
    unittest.main()
