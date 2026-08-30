#!/usr/bin/env python3
"""Cross-process checks that cannot run inside Ecto's SQL sandbox."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path


def mix(workspace: Path, database: Path, *arguments: str) -> None:
    env = os.environ | {
        "MIX_ENV": "test",
        "GROUP_STAY_DATABASE_PATH": str(database),
    }
    subprocess.run(["mix", *arguments], cwd=workspace, env=env, check=True)


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


class Server:
    def __init__(self, workspace: Path, database: Path):
        self.workspace = workspace
        self.database = database
        self.port = available_port()
        self.process: subprocess.Popen[str] | None = None
        self.log = tempfile.TemporaryFile(mode="w+")

    def __enter__(self) -> "Server":
        env = os.environ | {
            "MIX_ENV": "test",
            "GROUP_STAY_DATABASE_PATH": str(self.database),
            "PORT": str(self.port),
        }
        self.process = subprocess.Popen(
            ["mix", "phx.server"],
            cwd=self.workspace,
            env=env,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            self._wait_until_ready()
        except Exception:
            details = self._log_contents()
            self._stop()
            self.log.close()
            raise RuntimeError(f"Phoenix did not become ready:\n{details}") from None
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop()
        self.log.close()

    def _stop(self) -> None:
        assert self.process is not None
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

    def _log_contents(self) -> str:
        self.log.flush()
        self.log.seek(0)
        return self.log.read()

    def _wait_until_ready(self) -> None:
        assert self.process is not None
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("Phoenix exited during startup")
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("Phoenix did not accept connections within 60 seconds")

    def request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"content-type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def submit(self, operations: list[dict]) -> list[dict]:
        status, body = self.request("POST", "/api/v1/partner-batches", {"operations": operations})
        if status != 200:
            raise AssertionError(f"batch returned {status}: {body}")
        return body["results"]

    def data(self, path: str) -> dict:
        status, body = self.request("GET", path)
        if status != 200:
            raise AssertionError(f"GET {path} returned {status}: {body}")
        return body["data"]


def open_group(operation_id: str, group_id: str, booked_on: str) -> dict:
    return {
        "operation_id": operation_id,
        "type": "open_group",
        "occurred_on": booked_on,
        "group_id": group_id,
        "guest_id": "upgrade-guest",
        "property_id": "ams-canal",
        "arrival_on": "2027-03-01",
        "departure_on": "2027-03-02",
        "rate_plan": "flexible",
        "rooms": [{"room_id": "room-1", "nightly_rate_cents": 10_000}],
    }


def payment(
    operation_id: str,
    group_id: str,
    occurred_on: str = "2027-01-02",
    amount_cents: int = 2_000,
    expected_revision: int | None = None,
) -> dict:
    operation = {
        "operation_id": operation_id,
        "type": "record_cash_payment",
        "occurred_on": occurred_on,
        "group_id": group_id,
        "amount_cents": amount_cents,
    }
    if expected_revision is not None:
        operation["expected_revision"] = expected_revision
    return operation


def policy_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "policy-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        with Server(previous, database) as server:
            results = server.submit(
                [
                    open_group("open-old", "old", "2026-12-31"),
                    payment("pay-old", "old", "2026-12-31"),
                    open_group("open-new", "new", "2027-01-01"),
                    payment("pay-new", "new"),
                ]
            )
            assert all(result["status"] == "applied" for result in results)

        mix(current, database, "ecto.migrate", "--quiet")

        with Server(current, database) as server:
            assert server.data("/api/v1/groups/old")["policy_version"] == "flex-14"
            assert server.data("/api/v1/groups/new")["policy_version"] == "flex-30"
            old, new = server.submit(
                [
                    {
                        "operation_id": "cancel-old",
                        "type": "cancel_group",
                        "occurred_on": "2027-02-01",
                        "group_id": "old",
                        "expected_revision": 2,
                    },
                    {
                        "operation_id": "cancel-new",
                        "type": "cancel_group",
                        "occurred_on": "2027-02-01",
                        "group_id": "new",
                        "expected_revision": 2,
                    },
                ]
            )
            assert old["refunded_cents"] == 2_000
            assert new["retained_cents"] == 2_000


def policy_history_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "policy-history-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        def group(operation_id: str, group_id: str, booked_on: str) -> dict:
            return {
                "operation_id": operation_id,
                "type": "open_group",
                "occurred_on": booked_on,
                "group_id": group_id,
                "guest_id": "policy-history-guest",
                "property_id": "ams-canal",
                "arrival_on": "2027-04-01",
                "departure_on": "2027-04-02",
                "rate_plan": "flexible",
                "rooms": [{"room_id": f"{group_id}-room", "nightly_rate_cents": 5_000}],
            }

        settled = group("history-settled-open", "history-settled", "2027-01-05")
        settled["arrival_on"] = "2027-02-01"
        settled["departure_on"] = "2027-02-02"

        with Server(previous, database) as server:
            results = server.submit(
                [
                    group("history-old-open", "history-old", "2026-12-20"),
                    payment("history-old-pay", "history-old", "2026-12-21", 1_000),
                    group("history-new-open", "history-new", "2027-01-10"),
                    payment("history-new-pay", "history-new", "2027-01-11", 1_000),
                    settled,
                    payment("history-settled-pay", "history-settled", "2027-01-06", 1_000),
                    {
                        "operation_id": "history-settled-cancel",
                        "type": "cancel_group",
                        "occurred_on": "2027-01-18",
                        "group_id": "history-settled",
                    },
                ]
            )
            assert all(result["status"] == "applied" for result in results)
            ledger_before = server.data("/api/v1/ledger?on=2027-01-18")
            assert ledger_before["cash_refunded_cents"] == 1_000

        mix(current, database, "ecto.migrate", "--quiet")

        with Server(current, database) as server:
            old = server.data("/api/v1/groups/history-old")
            new = server.data("/api/v1/groups/history-new")
            settled_after = server.data("/api/v1/groups/history-settled")
            assert old["policy_version"] == "flex-14"
            assert new["policy_version"] == "flex-30"
            assert new["refundable_until"] == "2027-03-02"
            assert settled_after["policy_version"] == "flex-30"
            assert settled_after["status"] == "cancelled"
            ledger_after_upgrade = server.data("/api/v1/ledger?on=2027-01-18")
            for field in (
                "cash_held_cents",
                "cash_refunded_cents",
                "cash_retained_cents",
            ):
                assert ledger_after_upgrade[field] == ledger_before[field]

            [moved, old_cancel, new_cancel] = server.submit(
                [
                    {
                        "operation_id": "history-old-move",
                        "type": "reschedule_group",
                        "occurred_on": "2027-02-01",
                        "group_id": "history-old",
                        "new_arrival_on": "2027-05-01",
                    },
                    {
                        "operation_id": "history-old-cancel",
                        "type": "cancel_group",
                        "occurred_on": "2027-04-17",
                        "group_id": "history-old",
                    },
                    {
                        "operation_id": "history-new-cancel",
                        "type": "cancel_group",
                        "occurred_on": "2027-03-03",
                        "group_id": "history-new",
                    },
                ]
            )
            assert moved["policy_version"] == "flex-14"
            assert moved["refundable_until"] == "2027-04-17"
            assert old_cancel["refunded_cents"] == 1_000
            assert new_cancel["retained_cents"] == 1_000
            ledger = server.data("/api/v1/ledger?on=2027-04-17")
            assert ledger["cash_refunded_cents"] == 2_000
            assert ledger["cash_retained_cents"] == 1_000


def idempotency_restart(workspace: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "idempotency-restart.db"
        mix(workspace, database, "ecto.create", "--quiet")
        mix(workspace, database, "ecto.migrate", "--quiet")

        open_operation = {
            "operation_id": "restart-open",
            "type": "open_group",
            "occurred_on": "2027-05-01",
            "group_id": "restart-group",
            "guest_id": "restart-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-07-01",
            "departure_on": "2027-07-03",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "room-1", "nightly_rate_cents": 10_000}],
        }
        pay_operation = payment(
            "restart-payment",
            "restart-group",
            "2027-05-02",
            amount_cents=1_000,
            expected_revision=1,
        )

        with Server(workspace, database) as server:
            server.submit([open_operation])
            [first] = server.submit([pay_operation])
            group_before = server.data("/api/v1/groups/restart-group")
            ledger_before = server.data("/api/v1/ledger?on=2027-05-02")

        with Server(workspace, database) as server:
            [retry] = server.submit([pay_operation])
            assert retry == first
            assert server.data("/api/v1/groups/restart-group") == group_before
            assert server.data("/api/v1/ledger?on=2027-05-02") == ledger_before
            assert server.data("/api/v1/operations/restart-payment") == first


def payment_reduction_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "payment-reduction-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        source_open = {
            "operation_id": "upgrade-source-open",
            "type": "open_group",
            "occurred_on": "2027-04-01",
            "group_id": "upgrade-source",
            "guest_id": "upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-07-01",
            "departure_on": "2027-07-02",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "source-room", "nightly_rate_cents": 10_000}],
        }
        source_payment = payment(
            "upgrade-source-pay",
            "upgrade-source",
            "2027-04-02",
            amount_cents=2_000,
            expected_revision=1,
        )
        source_cancel = {
            "operation_id": "upgrade-source-cancel",
            "type": "cancel_group",
            "occurred_on": "2027-04-03",
            "group_id": "upgrade-source",
            "refund_method": "hotel_credit",
            "expected_revision": 2,
        }
        target_open = {
            "operation_id": "upgrade-open",
            "type": "open_group",
            "occurred_on": "2027-05-01",
            "group_id": "upgrade-group",
            "guest_id": "upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-07-01",
            "departure_on": "2027-07-02",
            "rate_plan": "flexible",
            "rooms": [
                {"room_id": "room-a", "nightly_rate_cents": 10_000},
                {"room_id": "room-b", "nightly_rate_cents": 10_000},
                {"room_id": "room-c", "nightly_rate_cents": 10_000},
            ],
        }
        first_payment = payment(
            "upgrade-pay-first",
            "upgrade-group",
            "2027-05-03",
            amount_cents=3_000,
            expected_revision=1,
        )
        credit_application = {
            "operation_id": "upgrade-credit",
            "type": "apply_hotel_credit",
            "occurred_on": "2027-05-04",
            "group_id": "upgrade-group",
            "amount_cents": 1_000,
            "expected_revision": 2,
        }
        second_payment = payment(
            "upgrade-pay-second",
            "upgrade-group",
            "2027-05-02",
            amount_cents=2_000,
            expected_revision=3,
        )

        split_open = {
            "operation_id": "upgrade-split-open",
            "type": "open_group",
            "occurred_on": "2027-04-01",
            "group_id": "upgrade-split",
            "guest_id": "upgrade-split-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-10-01",
            "departure_on": "2027-10-02",
            "rate_plan": "flexible",
            "rooms": [
                {"room_id": "split-a", "nightly_rate_cents": 5_000},
                {"room_id": "split-b", "nightly_rate_cents": 5_000},
            ],
        }
        split_payment = payment(
            "upgrade-split-pay",
            "upgrade-split",
            "2027-04-02",
            amount_cents=2_000,
            expected_revision=1,
        )
        spent_open = {
            "operation_id": "upgrade-spent-open",
            "type": "open_group",
            "occurred_on": "2027-04-01",
            "group_id": "upgrade-spent",
            "guest_id": "upgrade-split-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-11-01",
            "departure_on": "2027-11-02",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "spent-room", "nightly_rate_cents": 10_000}],
        }

        with Server(previous, database) as server:
            source_results = server.submit([source_open, source_payment, source_cancel])
            assert all(result["status"] == "applied" for result in source_results)

            results = server.submit(
                [target_open, first_payment, credit_application, second_payment]
            )
            assert all(result["status"] == "applied" for result in results)
            original_second_result = results[3]

            split_results = server.submit([split_open, split_payment, spent_open])
            assert all(result["status"] == "applied" for result in split_results)
            original_split_payment_result = split_results[1]

        mix(current, database, "ecto.migrate", "--quiet")

        with Server(current, database) as server:
            group = server.data("/api/v1/groups/upgrade-group")
            rooms = {room["room_id"]: room for room in group["rooms"]}
            assert rooms["room-a"]["cash_paid_cents"] == 2_000
            assert rooms["room-a"]["credit_paid_cents"] == 0
            assert rooms["room-b"]["cash_paid_cents"] == 1_000
            assert rooms["room-b"]["credit_paid_cents"] == 1_000
            assert rooms["room-c"]["cash_paid_cents"] == 2_000
            assert rooms["room-c"]["credit_paid_cents"] == 0

            second_statement = server.data("/api/v1/payments/upgrade-pay-second")
            assert second_statement == {
                "payment_operation_id": "upgrade-pay-second",
                "original_group_id": "upgrade-group",
                "recorded_cents": 2_000,
                "held_cents": 2_000,
                "refunded_cents": 0,
                "retained_cents": 0,
                "converted_to_credit_cents": 0,
                "reduced_cents": 0,
                "charged_back_cents": 0,
            }

            [wrong_type] = server.submit(
                [
                    {
                        "operation_id": "upgrade-reduce-credit",
                        "type": "reduce_cash_payment",
                        "occurred_on": "2027-05-14",
                        "payment_operation_id": "upgrade-credit",
                        "amount_cents": 1_000,
                    }
                ]
            )
            assert wrong_type["code"] == "payment_not_reducible"

            [cancelled] = server.submit(
                [
                    {
                        "operation_id": "upgrade-cancel-b",
                        "type": "cancel_rooms",
                        "occurred_on": "2027-05-15",
                        "group_id": "upgrade-group",
                        "room_ids": ["room-b"],
                        "expected_revision": 4,
                    }
                ]
            )
            assert cancelled["refunded_cents"] == 1_000

            reduction = {
                "operation_id": "upgrade-reduction",
                "type": "reduce_cash_payment",
                "occurred_on": "2027-05-16",
                "payment_operation_id": "upgrade-pay-second",
                "amount_cents": 1_000,
                "expected_revision": 5,
            }
            [first_reduction] = server.submit([reduction])
            assert first_reduction["outstanding_deposit_cents"] == 1_000
            group_before_restart = server.data("/api/v1/groups/upgrade-group")
            rooms = {room["room_id"]: room for room in group_before_restart["rooms"]}
            assert rooms["room-a"]["cash_paid_cents"] == 2_000
            assert rooms["room-c"]["cash_paid_cents"] == 1_000
            ledger_before_restart = server.data("/api/v1/ledger?on=2027-05-16")
            assert ledger_before_restart["cash_held_cents"] == 5_000
            assert ledger_before_restart["cash_refunded_cents"] == 1_000
            assert ledger_before_restart["cash_reduced_cents"] == 1_000
            statement_before_restart = server.data("/api/v1/payments/upgrade-pay-second")
            assert statement_before_restart["held_cents"] == 1_000
            assert statement_before_restart["reduced_cents"] == 1_000

            split_refund, split_credit = server.submit(
                [
                    {
                        "operation_id": "upgrade-split-refund",
                        "type": "cancel_rooms",
                        "occurred_on": "2027-05-17",
                        "group_id": "upgrade-split",
                        "room_ids": ["split-a"],
                        "refund_method": "cash",
                        "expected_revision": 2,
                    },
                    {
                        "operation_id": "upgrade-split-credit",
                        "type": "cancel_rooms",
                        "occurred_on": "2027-05-17",
                        "group_id": "upgrade-split",
                        "room_ids": ["split-b"],
                        "refund_method": "hotel_credit",
                        "expected_revision": 3,
                    },
                ]
            )
            assert split_refund["refunded_cents"] == 1_000
            assert split_credit["credit_issued_cents"] == 1_100

            [spent] = server.submit(
                [
                    {
                        "operation_id": "upgrade-spend-credit",
                        "type": "apply_hotel_credit",
                        "occurred_on": "2027-05-18",
                        "group_id": "upgrade-spent",
                        "amount_cents": 600,
                        "expected_revision": 1,
                    }
                ]
            )
            assert spent["revision"] == 2

            chargeback = {
                "operation_id": "upgrade-split-chargeback",
                "type": "charge_back_payment",
                "occurred_on": "2027-05-19",
                "payment_operation_id": "upgrade-split-pay",
                "expected_revision": 4,
            }
            [first_chargeback] = server.submit([chargeback])
            assert first_chargeback["charged_back_cents"] == 2_000
            assert first_chargeback["revision"] == 5

            split_group_before_restart = server.data("/api/v1/groups/upgrade-split")
            spent_group_before_restart = server.data("/api/v1/groups/upgrade-spent")
            assert spent_group_before_restart["revision"] == 2
            assert spent_group_before_restart["credit_paid_cents"] == 600

            chargeback_ledger_before_restart = server.data("/api/v1/ledger?on=2027-05-19")
            assert chargeback_ledger_before_restart["cash_charged_back_cents"] == 2_000
            assert chargeback_ledger_before_restart["credit_shortfall_cents"] == 600

        with Server(current, database) as server:
            reduction_retry, payment_retry = server.submit([reduction, second_payment])
            assert reduction_retry == first_reduction
            assert payment_retry == original_second_result
            assert server.data("/api/v1/groups/upgrade-group") == group_before_restart
            assert server.data("/api/v1/operations/upgrade-reduction") == first_reduction
            assert (
                server.data("/api/v1/payments/upgrade-pay-second")
                == statement_before_restart
            )

            chargeback_retry, split_payment_retry = server.submit(
                [chargeback, split_payment]
            )
            assert chargeback_retry == first_chargeback
            assert split_payment_retry == original_split_payment_result
            assert server.data("/api/v1/groups/upgrade-split") == split_group_before_restart
            assert server.data("/api/v1/groups/upgrade-spent") == spent_group_before_restart
            assert (
                server.data("/api/v1/ledger?on=2027-05-19")
                == chargeback_ledger_before_restart
            )
            assert server.data("/api/v1/operations/upgrade-split-chargeback") == first_chargeback


def room_history_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "room-history-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        def group(operation_id: str, group_id: str, rates: list[int]) -> dict:
            return {
                "operation_id": operation_id,
                "type": "open_group",
                "occurred_on": "2027-03-01",
                "group_id": group_id,
                "guest_id": "room-history-guest",
                "property_id": "ams-canal",
                "arrival_on": "2027-09-01",
                "departure_on": "2027-09-02",
                "rate_plan": "flexible",
                "rooms": [
                    {"room_id": f"{group_id}-room-{index}", "nightly_rate_cents": rate}
                    for index, rate in enumerate(rates, start=1)
                ],
            }

        source_cancel = {
            "operation_id": "room-history-credit",
            "type": "cancel_group",
            "occurred_on": "2027-04-01",
            "group_id": "room-history-origin",
            "refund_method": "hotel_credit",
        }
        credit_application = {
            "operation_id": "room-history-apply",
            "type": "apply_hotel_credit",
            "occurred_on": "2027-05-10",
            "group_id": "room-history-target",
            "amount_cents": 1_000,
        }

        with Server(previous, database) as server:
            results = server.submit(
                [
                    group("room-history-origin-open", "room-history-origin", [10_000]),
                    payment("room-history-origin-pay", "room-history-origin", "2027-03-02", 2_000),
                    source_cancel,
                    group("room-history-target-open", "room-history-target", [5_000, 5_000, 5_000]),
                    payment("room-history-pay-a", "room-history-target", "2027-05-20", 1_500),
                    credit_application,
                    payment("room-history-pay-b", "room-history-target", "2027-05-01", 500),
                ]
            )
            assert all(result["status"] == "applied" for result in results)
            original_credit_result = results[5]
            original_payment_result = results[6]

        mix(current, database, "ecto.migrate", "--quiet")

        cancel_room = {
            "operation_id": "room-history-cancel-room",
            "type": "cancel_rooms",
            "occurred_on": "2027-06-01",
            "group_id": "room-history-target",
            "room_ids": ["room-history-target-room-2"],
        }
        reduction = {
            "operation_id": "room-history-reduce",
            "type": "reduce_cash_payment",
            "occurred_on": "2027-06-02",
            "payment_operation_id": "room-history-pay-b",
            "amount_cents": 500,
        }

        with Server(current, database) as server:
            rooms = {
                room["room_id"]: room
                for room in server.data("/api/v1/groups/room-history-target")["rooms"]
            }
            assert rooms["room-history-target-room-1"]["cash_paid_cents"] == 1_000
            assert rooms["room-history-target-room-2"]["cash_paid_cents"] == 500
            assert rooms["room-history-target-room-2"]["credit_paid_cents"] == 500
            assert rooms["room-history-target-room-3"]["credit_paid_cents"] == 500
            assert rooms["room-history-target-room-3"]["cash_paid_cents"] == 500

            [cancelled, reduced] = server.submit([cancel_room, reduction])
            assert cancelled["refunded_cents"] == 500
            assert reduced["outstanding_deposit_cents"] == 500
            group_after = server.data("/api/v1/groups/room-history-target")
            assert group_after["cash_paid_cents"] == 1_000
            assert group_after["credit_paid_cents"] == 500
            assert group_after["outstanding_deposit_cents"] == 500

            statement_a = server.data("/api/v1/payments/room-history-pay-a")
            statement_b = server.data("/api/v1/payments/room-history-pay-b")
            assert statement_a["held_cents"] == 1_000
            assert statement_a["refunded_cents"] == 500
            assert statement_b["held_cents"] == 0
            assert statement_b["reduced_cents"] == 500
            ledger_after = server.data("/api/v1/ledger?on=2027-06-02")

        with Server(current, database) as server:
            assert server.submit([cancel_room, reduction]) == [cancelled, reduced]
            assert server.submit(
                [
                    credit_application,
                    payment("room-history-pay-b", "room-history-target", "2027-05-01", 500),
                ]
            ) == [original_credit_result, original_payment_result]
            assert server.data("/api/v1/ledger?on=2027-06-02") == ledger_after


def transfer_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "transfer-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        source_open = {
            "operation_id": "transfer-upgrade-source-open",
            "type": "open_group",
            "occurred_on": "2027-04-01",
            "group_id": "transfer-upgrade-source",
            "guest_id": "transfer-upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-08-01",
            "departure_on": "2027-08-02",
            "rate_plan": "flexible",
            "rooms": [
                {"room_id": f"source-room-{index}", "nightly_rate_cents": 5_000}
                for index in range(1, 4)
            ],
        }
        source_payment = payment(
            "transfer-upgrade-source-pay",
            "transfer-upgrade-source",
            "2027-04-02",
            amount_cents=3_000,
            expected_revision=1,
        )
        destination_open = {
            "operation_id": "transfer-upgrade-destination-open",
            "type": "open_group",
            "occurred_on": "2027-04-01",
            "group_id": "transfer-upgrade-destination",
            "guest_id": "transfer-upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-08-01",
            "departure_on": "2027-08-02",
            "rate_plan": "flexible",
            "rooms": [
                {"room_id": f"destination-room-{index}", "nightly_rate_cents": 5_000}
                for index in range(1, 4)
            ],
        }
        destination_payment = payment(
            "transfer-upgrade-destination-pay",
            "transfer-upgrade-destination",
            "2027-04-02",
            amount_cents=500,
            expected_revision=1,
        )

        with Server(previous, database) as server:
            results = server.submit(
                [source_open, source_payment, destination_open, destination_payment]
            )
            assert all(result["status"] == "applied" for result in results)
            original_source_payment_result = results[1]
            statement_before = server.data(
                "/api/v1/payments/transfer-upgrade-source-pay"
            )
            assert statement_before["held_cents"] == 3_000

        mix(current, database, "ecto.migrate", "--quiet")

        transfer = {
            "operation_id": "transfer-upgrade-move",
            "type": "transfer_deposit",
            "occurred_on": "2027-05-01",
            "source_group_id": "transfer-upgrade-source",
            "destination_group_id": "transfer-upgrade-destination",
            "amount_cents": 2_000,
            "expected_revision": 2,
            "destination_expected_revision": 2,
        }
        reduction = {
            "operation_id": "transfer-upgrade-reduce",
            "type": "reduce_cash_payment",
            "occurred_on": "2027-05-02",
            "payment_operation_id": "transfer-upgrade-source-pay",
            "amount_cents": 500,
            "expected_revision": 3,
        }
        chargeback = {
            "operation_id": "transfer-upgrade-chargeback",
            "type": "charge_back_payment",
            "occurred_on": "2027-05-03",
            "payment_operation_id": "transfer-upgrade-source-pay",
            "expected_revision": 4,
        }

        with Server(current, database) as server:
            statement_after = server.data(
                "/api/v1/payments/transfer-upgrade-source-pay"
            )
            assert statement_after == statement_before

            first_transfer, first_reduction, first_chargeback = server.submit(
                [transfer, reduction, chargeback]
            )
            assert first_transfer["source_revision"] == 3
            assert first_transfer["destination_revision"] == 3
            assert first_reduction["revision"] == 4
            assert first_chargeback["revision"] == 5
            assert first_chargeback["charged_back_cents"] == 2_500

            source_before_restart = server.data("/api/v1/groups/transfer-upgrade-source")
            destination_before_restart = server.data(
                "/api/v1/groups/transfer-upgrade-destination"
            )
            assert source_before_restart["cash_paid_cents"] == 0
            assert source_before_restart["revision"] == 5
            assert destination_before_restart["cash_paid_cents"] == 500
            assert destination_before_restart["revision"] == 5

            statement_before_restart = server.data(
                "/api/v1/payments/transfer-upgrade-source-pay"
            )
            assert statement_before_restart["held_cents"] == 0
            assert statement_before_restart["held_by_group"] == []
            assert statement_before_restart["reduced_cents"] == 500
            assert statement_before_restart["charged_back_cents"] == 2_500

            ledger_before_restart = server.data("/api/v1/ledger?on=2027-05-03")
            assert ledger_before_restart["cash_held_cents"] == 500
            assert ledger_before_restart["cash_reduced_cents"] == 500
            assert ledger_before_restart["cash_charged_back_cents"] == 2_500

        with Server(current, database) as server:
            transfer_retry, reduction_retry, chargeback_retry, payment_retry = server.submit(
                [transfer, reduction, chargeback, source_payment]
            )
            assert transfer_retry == first_transfer
            assert reduction_retry == first_reduction
            assert chargeback_retry == first_chargeback
            assert payment_retry == original_source_payment_result
            assert server.data("/api/v1/groups/transfer-upgrade-source") == source_before_restart
            assert (
                server.data("/api/v1/groups/transfer-upgrade-destination")
                == destination_before_restart
            )
            assert (
                server.data("/api/v1/payments/transfer-upgrade-source-pay")
                == statement_before_restart
            )
            assert server.data("/api/v1/ledger?on=2027-05-03") == ledger_before_restart


def payment_history_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "payment-history-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        def group(operation_id: str, group_id: str, property_id: str, room_count: int) -> dict:
            return {
                "operation_id": operation_id,
                "type": "open_group",
                "occurred_on": "2027-03-01",
                "group_id": group_id,
                "guest_id": "payment-history-guest",
                "property_id": property_id,
                "arrival_on": "2027-09-01",
                "departure_on": "2027-09-02",
                "rate_plan": "flexible",
                "rooms": [
                    {"room_id": f"{group_id}-room-{index}", "nightly_rate_cents": 5_000}
                    for index in range(1, room_count + 1)
                ],
            }

        with Server(previous, database) as server:
            results = server.submit(
                [
                    group("payment-history-source-open", "payment-history-source", "ams-canal", 3),
                    payment("payment-history-p1", "payment-history-source", "2027-03-02", 2_500),
                    payment("payment-history-p2", "payment-history-source", "2027-03-03", 500),
                    {
                        "operation_id": "payment-history-refund",
                        "type": "cancel_rooms",
                        "occurred_on": "2027-04-01",
                        "group_id": "payment-history-source",
                        "room_ids": ["payment-history-source-room-1"],
                    },
                    {
                        "operation_id": "payment-history-pre-reduce",
                        "type": "reduce_cash_payment",
                        "occurred_on": "2027-04-02",
                        "payment_operation_id": "payment-history-p2",
                        "amount_cents": 200,
                    },
                    group(
                        "payment-history-destination-open",
                        "payment-history-destination",
                        "rome-centro",
                        2,
                    ),
                    payment(
                        "payment-history-destination-pay",
                        "payment-history-destination",
                        "2027-03-02",
                        500,
                    ),
                ]
            )
            assert all(result["status"] == "applied" for result in results)

        mix(current, database, "ecto.migrate", "--quiet")

        transfer = {
            "operation_id": "payment-history-transfer",
            "type": "transfer_deposit",
            "occurred_on": "2027-05-01",
            "source_group_id": "payment-history-source",
            "destination_group_id": "payment-history-destination",
            "amount_cents": 800,
        }
        p2_chargeback = {
            "operation_id": "payment-history-p2-chargeback",
            "type": "charge_back_payment",
            "occurred_on": "2027-05-02",
            "payment_operation_id": "payment-history-p2",
        }
        p1_reduction = {
            "operation_id": "payment-history-p1-reduction",
            "type": "reduce_cash_payment",
            "occurred_on": "2027-05-03",
            "payment_operation_id": "payment-history-p1",
            "amount_cents": 500,
        }

        with Server(current, database) as server:
            first_transfer, first_chargeback, first_reduction = server.submit(
                [transfer, p2_chargeback, p1_reduction]
            )
            assert first_chargeback["charged_back_cents"] == 300

            p1 = server.data("/api/v1/payments/payment-history-p1")
            p2 = server.data("/api/v1/payments/payment-history-p2")
            destination_payment = server.data(
                "/api/v1/payments/payment-history-destination-pay"
            )
            assert p1["held_cents"] == 1_000
            assert p1["refunded_cents"] == 1_000
            assert p1["reduced_cents"] == 500
            assert p1["held_by_group"] == [
                {"group_id": "payment-history-source", "amount_cents": 1_000}
            ]
            assert p2["held_cents"] == 0
            assert p2["reduced_cents"] == 200
            assert p2["charged_back_cents"] == 300
            assert destination_payment["held_cents"] == 500

            source_after = server.data("/api/v1/groups/payment-history-source")
            destination_after = server.data("/api/v1/groups/payment-history-destination")
            assert source_after["cash_paid_cents"] == 1_000
            assert destination_after["cash_paid_cents"] == 500
            ledger_after = server.data("/api/v1/ledger?on=2027-05-03")
            assert ledger_after["cash_held_cents"] == 1_500
            assert ledger_after["cash_refunded_cents"] == 1_000
            assert ledger_after["cash_reduced_cents"] == 700
            assert ledger_after["cash_charged_back_cents"] == 300

        with Server(current, database) as server:
            assert server.submit([transfer, p2_chargeback, p1_reduction]) == [
                first_transfer,
                first_chargeback,
                first_reduction,
            ]
            assert server.data("/api/v1/groups/payment-history-source") == source_after
            assert server.data("/api/v1/groups/payment-history-destination") == destination_after
            assert server.data("/api/v1/ledger?on=2027-05-03") == ledger_after


def finance_reporting_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "finance-reporting-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        source_open = {
            "operation_id": "finance-upgrade-source-open",
            "type": "open_group",
            "occurred_on": "2027-05-01",
            "group_id": "finance-upgrade-source",
            "guest_id": "finance-upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-10-01",
            "departure_on": "2027-10-02",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "source-room", "nightly_rate_cents": 10_000}],
        }
        destination_open = {
            "operation_id": "finance-upgrade-destination-open",
            "type": "open_group",
            "occurred_on": "2027-05-01",
            "group_id": "finance-upgrade-destination",
            "guest_id": "finance-upgrade-guest",
            "property_id": "berlin-mitte",
            "arrival_on": "2027-10-01",
            "departure_on": "2027-10-02",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "destination-room", "nightly_rate_cents": 10_000}],
        }
        source_payment = payment(
            "finance-upgrade-source-pay",
            "finance-upgrade-source",
            "2027-05-02",
            amount_cents=2_000,
        )
        destination_payment = payment(
            "finance-upgrade-destination-pay",
            "finance-upgrade-destination",
            "2027-05-02",
            amount_cents=500,
        )
        original_transfer = {
            "operation_id": "finance-upgrade-original-transfer",
            "type": "transfer_deposit",
            "occurred_on": "2027-05-03",
            "source_group_id": "finance-upgrade-source",
            "destination_group_id": "finance-upgrade-destination",
            "amount_cents": 600,
        }

        with Server(previous, database) as server:
            results = server.submit(
                [
                    source_open,
                    source_payment,
                    destination_open,
                    destination_payment,
                    original_transfer,
                ]
            )
            assert all(result["status"] == "applied" for result in results)

        mix(current, database, "ecto.migrate", "--quiet")

        start = {
            "operation_id": "finance-upgrade-start",
            "type": "start_finance_reporting",
            "occurred_on": "2027-06-01",
            "starts_on": "2027-06-01",
        }
        transfer = {
            "operation_id": "finance-upgrade-transfer",
            "type": "transfer_deposit",
            "occurred_on": "2027-06-01",
            "source_group_id": "finance-upgrade-source",
            "destination_group_id": "finance-upgrade-destination",
            "amount_cents": 300,
        }
        reduction = {
            "operation_id": "finance-upgrade-reduction",
            "type": "reduce_cash_payment",
            "occurred_on": "2027-06-01",
            "payment_operation_id": "finance-upgrade-source-pay",
            "amount_cents": 200,
        }

        with Server(current, database) as server:
            [start_result] = server.submit([start])
            opening = server.data("/api/v1/finance/daily-report?date=2027-06-01")
            opening_cash = {entry["property_id"]: entry for entry in opening["cash"]}
            assert opening_cash["ams-canal"]["opening_held_cents"] == 1_400
            assert opening_cash["berlin-mitte"]["opening_held_cents"] == 1_100
            assert all(
                value == 0
                for entry in opening_cash.values()
                for value in entry["movements"].values()
            )

            first_transfer, first_reduction = server.submit([transfer, reduction])
            report_before_restart = server.data(
                "/api/v1/finance/daily-report?date=2027-06-01"
            )
            cash = {entry["property_id"]: entry for entry in report_before_restart["cash"]}
            assert cash["ams-canal"]["movements"]["transferred_out_cents"] == 300
            assert cash["ams-canal"]["closing_held_cents"] == 1_100
            assert cash["berlin-mitte"]["movements"]["transferred_in_cents"] == 300
            assert cash["berlin-mitte"]["movements"]["reduced_cents"] == 200
            assert cash["berlin-mitte"]["closing_held_cents"] == 1_200

        with Server(current, database) as server:
            assert server.data("/api/v1/finance/daily-report?date=2027-06-01") == report_before_restart
            assert server.submit([start]) == [start_result]
            assert server.submit([transfer, reduction]) == [first_transfer, first_reduction]
            assert server.data("/api/v1/finance/daily-report?date=2027-06-01") == report_before_restart


def projection_history_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "projection-history-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        def group(
            operation_id: str,
            group_id: str,
            guest_id: str,
            property_id: str,
            booked_on: str = "2027-01-01",
            arrival_on: str = "2027-12-01",
            rate_plan: str = "flexible",
            rate: int = 5_000,
        ) -> dict:
            return {
                "operation_id": operation_id,
                "type": "open_group",
                "occurred_on": booked_on,
                "group_id": group_id,
                "guest_id": guest_id,
                "property_id": property_id,
                "arrival_on": arrival_on,
                "departure_on": str(date.fromisoformat(arrival_on) + timedelta(days=1)),
                "rate_plan": rate_plan,
                "rooms": [{"room_id": f"{group_id}-room", "nightly_rate_cents": rate}],
            }

        def cancel(operation_id: str, group_id: str, occurred_on: str, method: str | None = None) -> dict:
            operation = {
                "operation_id": operation_id,
                "type": "cancel_group",
                "occurred_on": occurred_on,
                "group_id": group_id,
            }
            if method is not None:
                operation["refund_method"] = method
            return operation

        def reduce(operation_id: str, payment_id: str, amount: int) -> dict:
            return {
                "operation_id": operation_id,
                "type": "reduce_cash_payment",
                "occurred_on": "2027-05-03",
                "payment_operation_id": payment_id,
                "amount_cents": amount,
            }

        with Server(previous, database) as server:
            operations = [
                group("projection-held-source-open", "projection-held-source", "projection-held-guest", "ams-canal"),
                group("projection-held-destination-open", "projection-held-destination", "projection-held-guest", "rome-centro"),
                payment("projection-held-pay", "projection-held-source", "2027-05-01", 1_000),
                {
                    "operation_id": "projection-held-transfer",
                    "type": "transfer_deposit",
                    "occurred_on": "2027-05-02",
                    "source_group_id": "projection-held-source",
                    "destination_group_id": "projection-held-destination",
                    "amount_cents": 300,
                },
                group("projection-refund-open", "projection-refund", "projection-refund-guest", "ams-canal"),
                payment("projection-refund-pay", "projection-refund", "2027-05-01", 400),
                cancel("projection-refund-cancel", "projection-refund", "2027-05-02"),
                group(
                    "projection-retained-open",
                    "projection-retained",
                    "projection-retained-guest",
                    "rome-centro",
                    rate_plan="advance_purchase",
                    rate=500,
                ),
                payment("projection-retained-pay", "projection-retained", "2027-05-01", 500),
                cancel("projection-retained-cancel", "projection-retained", "2027-05-02"),
                group("projection-reduced-open", "projection-reduced", "projection-reduced-guest", "ams-canal"),
                payment("projection-reduced-pay", "projection-reduced", "2027-05-01", 500),
                reduce("projection-reduced-op", "projection-reduced-pay", 200),
                group("projection-charged-open", "projection-charged", "projection-charged-guest", "rome-centro"),
                payment("projection-charged-pay", "projection-charged", "2027-05-01", 400),
                {
                    "operation_id": "projection-charged-op",
                    "type": "charge_back_payment",
                    "occurred_on": "2027-05-02",
                    "payment_operation_id": "projection-charged-pay",
                },
                group("projection-future-open", "projection-future", "projection-future-guest", "ams-canal"),
                payment("projection-future-pay", "projection-future", "2027-08-01", 250),
                group(
                    "projection-expired-open",
                    "projection-expired",
                    "projection-expired-guest",
                    "berlin-mitte",
                    booked_on="2025-01-01",
                    arrival_on="2025-12-01",
                ),
                payment("projection-expired-pay", "projection-expired", "2025-01-02", 1_000),
                cancel("projection-expired-credit", "projection-expired", "2025-06-01", "hotel_credit"),
                group("projection-live-open", "projection-live", "projection-live-guest", "berlin-mitte"),
                payment("projection-live-pay", "projection-live", "2027-05-01", 1_000),
                cancel("projection-live-credit", "projection-live", "2027-06-01", "hotel_credit"),
                group("projection-short-open", "projection-short", "projection-short-guest", "ams-canal"),
                payment("projection-short-pay", "projection-short", "2027-05-01", 1_000),
                cancel("projection-short-credit", "projection-short", "2027-06-02", "hotel_credit"),
                group("projection-short-target-open", "projection-short-target", "projection-short-guest", "rome-centro"),
                {
                    "operation_id": "projection-short-apply",
                    "type": "apply_hotel_credit",
                    "occurred_on": "2027-06-03",
                    "group_id": "projection-short-target",
                    "amount_cents": 600,
                },
                {
                    "operation_id": "projection-short-chargeback",
                    "type": "charge_back_payment",
                    "occurred_on": "2027-06-04",
                    "payment_operation_id": "projection-short-pay",
                },
            ]
            results = server.submit(operations)
            assert all(result["status"] == "applied" for result in results)

        mix(current, database, "ecto.migrate", "--quiet")

        start = {
            "operation_id": "projection-start",
            "type": "start_finance_reporting",
            "occurred_on": "2027-06-10",
            "starts_on": "2027-06-10",
        }

        with Server(current, database) as server:
            [start_result] = server.submit([start])
            opening = server.data("/api/v1/finance/daily-report?date=2027-06-10")
            cash = {entry["property_id"]: entry for entry in opening["cash"]}
            assert cash["ams-canal"]["opening_held_cents"] == 1_250
            assert cash["rome-centro"]["opening_held_cents"] == 300
            assert all(
                value == 0
                for entry in cash.values()
                for value in entry["movements"].values()
            )
            assert opening["credit"]["opening_liability_cents"] == 1_700
            assert opening["credit"]["closing_liability_cents"] == 1_700
            assert all(value == 0 for value in opening["credit"]["movements"].values())

            expiry = server.data("/api/v1/finance/daily-report?date=2028-06-01")
            assert expiry["credit"]["movements"]["expired_cents"] == 1_100
            assert expiry["credit"]["closing_liability_cents"] == 600
            ledger = server.data("/api/v1/ledger?on=2027-06-10")
            assert ledger["credit_liability_cents"] == 1_700
            assert ledger["credit_shortfall_cents"] == 600

        with Server(current, database) as server:
            assert server.submit([start]) == [start_result]
            assert server.data("/api/v1/finance/daily-report?date=2027-06-10") == opening
            assert server.data("/api/v1/finance/daily-report?date=2028-06-01") == expiry


def finance_close_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "finance-close-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        start = {
            "operation_id": "close-upgrade-start",
            "type": "start_finance_reporting",
            "occurred_on": "2027-06-01",
            "starts_on": "2027-06-01",
        }
        group_open = {
            "operation_id": "close-upgrade-open",
            "type": "open_group",
            "occurred_on": "2027-05-01",
            "group_id": "close-upgrade-group",
            "guest_id": "close-upgrade-guest",
            "property_id": "ams-canal",
            "arrival_on": "2027-10-01",
            "departure_on": "2027-10-02",
            "rate_plan": "flexible",
            "rooms": [{"room_id": "close-upgrade-room", "nightly_rate_cents": 10_000}],
        }
        cash_payment = payment(
            "close-upgrade-pay",
            "close-upgrade-group",
            "2027-06-01",
            amount_cents=1_000,
        )
        refund = {
            "operation_id": "close-upgrade-refund",
            "type": "cancel_group",
            "occurred_on": "2027-06-02",
            "group_id": "close-upgrade-group",
            "refund_method": "cash",
        }

        with Server(previous, database) as server:
            results = server.submit([start, group_open, cash_payment, refund])
            assert all(result["status"] == "applied" for result in results)

        mix(current, database, "ecto.migrate", "--quiet")

        close = {
            "operation_id": "close-upgrade-close",
            "type": "close_finance_period",
            "occurred_on": "2027-06-30",
            "period_end_on": "2027-06-30",
        }
        chargeback = {
            "operation_id": "close-upgrade-chargeback",
            "type": "charge_back_payment",
            "occurred_on": "2027-06-03",
            "payment_operation_id": "close-upgrade-pay",
        }

        with Server(current, database) as server:
            [close_result] = server.submit([close])
            published = server.data("/api/v1/finance/daily-report?date=2027-06-02")
            assert published["status"] == "closed"
            [chargeback_result] = server.submit([chargeback])
            assert server.data("/api/v1/finance/daily-report?date=2027-06-02") == published

            adjustment = server.data("/api/v1/finance/daily-report?date=2027-07-01")
            late = {entry["property_id"]: entry for entry in adjustment["late_adjustments"]["cash"]}
            assert late["ams-canal"]["movements"]["refunded_cents"] == -1_000
            assert late["ams-canal"]["movements"]["charged_back_cents"] == 1_000

        with Server(current, database) as server:
            assert server.data("/api/v1/finance/daily-report?date=2027-06-02") == published
            assert server.data("/api/v1/finance/daily-report?date=2027-07-01") == adjustment
            assert server.submit([close, chargeback]) == [close_result, chargeback_result]
            assert server.data("/api/v1/finance/daily-report?date=2027-07-01") == adjustment


def close_history_upgrade(previous: Path, current: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "close-history-upgrade.db"
        mix(previous, database, "ecto.create", "--quiet")
        mix(previous, database, "ecto.migrate", "--quiet")

        def group(operation_id: str, group_id: str, property_id: str) -> dict:
            return {
                "operation_id": operation_id,
                "type": "open_group",
                "occurred_on": "2027-05-01",
                "group_id": group_id,
                "guest_id": "close-history-guest",
                "property_id": property_id,
                "arrival_on": "2027-12-01",
                "departure_on": "2027-12-02",
                "rate_plan": "flexible",
                "rooms": [{"room_id": f"{group_id}-room", "nightly_rate_cents": 5_000}],
            }

        start = {
            "operation_id": "close-history-start",
            "type": "start_finance_reporting",
            "occurred_on": "2027-06-10",
            "starts_on": "2027-06-10",
        }
        future_payment = payment(
            "close-history-future-pay",
            "close-history-future",
            "2027-08-01",
            600,
        )

        with Server(previous, database) as server:
            before_start = server.submit(
                [
                    group("close-history-future-open", "close-history-future", "ams-canal"),
                    future_payment,
                    start,
                ]
            )
            assert all(result["status"] == "applied" for result in before_start)

            after_start = server.submit(
                [
                    group("close-history-floor-open", "close-history-floor", "rome-centro"),
                    payment(
                        "close-history-floor-pay",
                        "close-history-floor",
                        "2027-05-20",
                        400,
                    ),
                    group("close-history-dated-open", "close-history-dated", "berlin-mitte"),
                    payment(
                        "close-history-dated-pay",
                        "close-history-dated",
                        "2027-06-15",
                        300,
                    ),
                ]
            )
            assert all(result["status"] == "applied" for result in after_start)
            inception_before = server.data("/api/v1/finance/daily-report?date=2027-06-10")
            dated_before = server.data("/api/v1/finance/daily-report?date=2027-06-15")
            inception_cash = {
                entry["property_id"]: entry for entry in inception_before["cash"]
            }
            assert inception_cash["ams-canal"]["opening_held_cents"] == 600
            assert inception_cash["rome-centro"]["movements"]["received_cents"] == 400
            assert {
                entry["property_id"]: entry for entry in dated_before["cash"]
            }["berlin-mitte"]["movements"]["received_cents"] == 300

        mix(current, database, "ecto.migrate", "--quiet")

        close = {
            "operation_id": "close-history-close",
            "type": "close_finance_period",
            "occurred_on": "2027-06-30",
            "period_end_on": "2027-06-30",
        }
        reduction = {
            "operation_id": "close-history-reduction",
            "type": "reduce_cash_payment",
            "occurred_on": "2027-05-01",
            "payment_operation_id": "close-history-future-pay",
            "amount_cents": 200,
        }

        with Server(current, database) as server:
            [close_result] = server.submit([close])
            inception_closed = server.data("/api/v1/finance/daily-report?date=2027-06-10")
            dated_closed = server.data("/api/v1/finance/daily-report?date=2027-06-15")
            assert inception_closed == {**inception_before, "status": "closed", "late_adjustments": {"cash": [], "credit": {"issued_cents": 0, "expired_cents": 0, "consumed_cents": 0, "revoked_cents": 0, "absorbed_cents": 0}}}
            assert dated_closed == {**dated_before, "status": "closed", "late_adjustments": {"cash": [], "credit": {"issued_cents": 0, "expired_cents": 0, "consumed_cents": 0, "revoked_cents": 0, "absorbed_cents": 0}}}

            [reduction_result] = server.submit([reduction])
            assert reduction_result["status"] == "applied"
            first_open = server.data("/api/v1/finance/daily-report?date=2027-07-01")
            late = {
                entry["property_id"]: entry
                for entry in first_open["late_adjustments"]["cash"]
            }
            assert late["ams-canal"]["movements"]["reduced_cents"] == 200
            assert server.data("/api/v1/finance/daily-report?date=2027-06-10") == inception_closed
            assert server.data("/api/v1/finance/daily-report?date=2027-06-15") == dated_closed

        with Server(current, database) as server:
            assert server.submit([close, reduction, future_payment]) == [
                close_result,
                reduction_result,
                before_start[1],
            ]
            assert server.data("/api/v1/finance/daily-report?date=2027-06-10") == inception_closed
            assert server.data("/api/v1/finance/daily-report?date=2027-06-15") == dated_closed
            assert server.data("/api/v1/finance/daily-report?date=2027-07-01") == first_open


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    policy = subparsers.add_parser("policy-upgrade")
    policy.add_argument("previous", type=Path)
    policy.add_argument("current", type=Path)

    policy_history = subparsers.add_parser("policy-history-upgrade")
    policy_history.add_argument("previous", type=Path)
    policy_history.add_argument("current", type=Path)

    restart = subparsers.add_parser("idempotency-restart")
    restart.add_argument("workspace", type=Path)

    reduction = subparsers.add_parser("payment-reduction-upgrade")
    reduction.add_argument("previous", type=Path)
    reduction.add_argument("current", type=Path)

    room_history = subparsers.add_parser("room-history-upgrade")
    room_history.add_argument("previous", type=Path)
    room_history.add_argument("current", type=Path)

    transfer = subparsers.add_parser("transfer-upgrade")
    transfer.add_argument("previous", type=Path)
    transfer.add_argument("current", type=Path)

    payment_history = subparsers.add_parser("payment-history-upgrade")
    payment_history.add_argument("previous", type=Path)
    payment_history.add_argument("current", type=Path)

    reporting = subparsers.add_parser("finance-reporting-upgrade")
    reporting.add_argument("previous", type=Path)
    reporting.add_argument("current", type=Path)

    projection_history = subparsers.add_parser("projection-history-upgrade")
    projection_history.add_argument("previous", type=Path)
    projection_history.add_argument("current", type=Path)

    close = subparsers.add_parser("finance-close-upgrade")
    close.add_argument("previous", type=Path)
    close.add_argument("current", type=Path)

    close_history = subparsers.add_parser("close-history-upgrade")
    close_history.add_argument("previous", type=Path)
    close_history.add_argument("current", type=Path)

    args = parser.parse_args()
    if args.command == "policy-upgrade":
        policy_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "policy-history-upgrade":
        policy_history_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "idempotency-restart":
        idempotency_restart(args.workspace.resolve())
    elif args.command == "payment-reduction-upgrade":
        payment_reduction_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "room-history-upgrade":
        room_history_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "transfer-upgrade":
        transfer_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "payment-history-upgrade":
        payment_history_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "finance-reporting-upgrade":
        finance_reporting_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "projection-history-upgrade":
        projection_history_upgrade(args.previous.resolve(), args.current.resolve())
    elif args.command == "finance-close-upgrade":
        finance_close_upgrade(args.previous.resolve(), args.current.resolve())
    else:
        close_history_upgrade(args.previous.resolve(), args.current.resolve())


if __name__ == "__main__":
    main()
