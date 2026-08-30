defmodule GroupStay.Private.LaunchDepositApiTest do
  use GroupStayWeb.ConnCase, async: false

  test "flexible deposits round correctly and the refund boundary is inclusive", %{conn: conn} do
    operations = [
      open_group("open-rounding", "rounding", "2026-11-15", 10_003),
      payment("pay-rounding", "rounding", 2_001),
      %{
        "operation_id" => "cancel-rounding",
        "type" => "cancel_group",
        "occurred_on" => "2026-11-01",
        "group_id" => "rounding"
      }
    ]

    [opened, _paid, cancelled] = submit(conn, operations)

    assert opened["deposit_due_cents"] == 2_001
    assert cancelled["refunded_cents"] == 2_001
    assert cancelled["retained_cents"] == 0

    totals = ledger(conn)
    assert totals["cash_held_cents"] == 0
    assert totals["cash_refunded_cents"] == 2_001
    assert totals["cash_retained_cents"] == 0
  end

  test "a rejected operation has no partial effect and later operations continue", %{conn: conn} do
    operations = [
      open_group("open-atomic", "atomic", "2026-12-01", 10_000),
      payment("overpay-atomic", "atomic", 2_001),
      payment("pay-atomic", "atomic", 1_000),
      open_group("open-atomic-again", "atomic", "2026-12-01", 50_000)
    ]

    [opened, rejected_payment, paid, rejected_open] = submit(conn, operations)

    assert opened["status"] == "applied"
    assert rejected_payment["code"] == "payment_exceeds_outstanding"
    assert paid["status"] == "applied"
    assert rejected_open["code"] == "group_already_exists"

    group = get_data(conn, "/api/v1/groups/atomic")
    assert group["lodging_total_cents"] == 10_000
    assert group["deposit_paid_cents"] == 1_000
    assert group["outstanding_deposit_cents"] == 1_000
  end

  test "a flexible group sums separately rounded room deposits", %{conn: conn} do
    operation =
      open_group("open-room-rounding", "room-rounding", "2026-12-01", 10_002)
      |> Map.put("rooms", [
        %{"room_id" => "room-a", "nightly_rate_cents" => 10_002},
        %{"room_id" => "room-b", "nightly_rate_cents" => 10_002}
      ])

    [opened] = submit(conn, [operation])
    assert opened["deposit_due_cents"] == 4_000
  end

  test "advance purchase requires the full stay amount and is never refundable", %{conn: conn} do
    open =
      open_group("open-advance", "advance", "2026-12-01", 10_003)
      |> Map.put("rate_plan", "advance_purchase")

    [opened, _paid, cancelled] =
      submit(conn, [
        open,
        payment("pay-advance", "advance", 10_003),
        %{
          "operation_id" => "cancel-advance",
          "type" => "cancel_group",
          "occurred_on" => "2026-10-02",
          "group_id" => "advance"
        }
      ])

    assert opened["deposit_due_cents"] == 10_003
    assert cancelled["refunded_cents"] == 0
    assert cancelled["retained_cents"] == 10_003
  end

  test "invalid group fields reject independently without creating records", %{conn: conn} do
    bad_stay =
      open_group("bad-stay", "bad-stay", "2026-12-01", 10_000)
      |> Map.put("departure_on", "2026-12-01")

    bad_plan =
      open_group("bad-plan", "bad-plan", "2026-12-01", 10_000)
      |> Map.put("rate_plan", "breakfast_magic")

    bad_rooms =
      open_group("bad-rooms", "bad-rooms", "2026-12-01", 10_000)
      |> Map.put("rooms", [
        %{"room_id" => "same", "nightly_rate_cents" => 10_000},
        %{"room_id" => "same", "nightly_rate_cents" => 12_000}
      ])

    results = submit(conn, [bad_stay, bad_plan, bad_rooms])

    assert Enum.map(results, & &1["code"]) == [
             "invalid_stay",
             "invalid_rate_plan",
             "invalid_rooms"
           ]

    for group_id <- ["bad-stay", "bad-plan", "bad-rooms"] do
      conn
      |> recycle()
      |> get("/api/v1/groups/#{group_id}")
      |> json_response(404)
    end
  end

  test "non-positive payments are rejected without changing the balance", %{conn: conn} do
    [opened, zero, negative] =
      submit(conn, [
        open_group("open-amount", "amount", "2026-12-01", 10_000),
        payment("pay-zero", "amount", 0),
        payment("pay-negative", "amount", -1)
      ])

    assert opened["status"] == "applied"
    assert zero["code"] == "invalid_amount"
    assert negative["code"] == "invalid_amount"
    assert get_data(conn, "/api/v1/groups/amount")["deposit_paid_cents"] == 0
  end

  test "malformed batches and missing groups use the documented HTTP errors", %{conn: conn} do
    invalid =
      conn
      |> recycle()
      |> post("/api/v1/partner-batches", %{"not_operations" => []})
      |> json_response(422)

    assert invalid == %{"error" => %{"code" => "invalid_batch"}}

    missing =
      conn
      |> recycle()
      |> get("/api/v1/groups/does-not-exist")
      |> json_response(404)

    assert missing == %{"error" => %{"code" => "group_not_found"}}
  end

  test "an unknown operation is rejected and does not stop the batch", %{conn: conn} do
    unknown = %{
      "operation_id" => "unknown-op",
      "type" => "upgrade_everyone",
      "occurred_on" => "2026-10-01",
      "group_id" => "unknown"
    }

    [rejected, opened] =
      submit(conn, [
        unknown,
        open_group("open-after-unknown", "after-unknown", "2026-12-01", 10_000)
      ])

    assert rejected["code"] == "invalid_operation"
    assert opened["status"] == "applied"
  end

  defp open_group(operation_id, group_id, arrival_on, nightly_rate_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2026-10-01",
      "group_id" => group_id,
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => nightly_rate_cents}]
    }
  end

  defp payment(operation_id, group_id, amount_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2026-10-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents
    }
  end

  defp submit(conn, operations) do
    conn
    |> recycle()
    |> post("/api/v1/partner-batches", %{"operations" => operations})
    |> json_response(200)
    |> Map.fetch!("results")
  end

  defp get_data(conn, path) do
    conn |> recycle() |> get(path) |> json_response(200) |> Map.fetch!("data")
  end

  defp ledger(conn), do: get_data(conn, "/api/v1/ledger")
end
