defmodule GroupStay.Private.RevisionTest do
  use GroupStayWeb.ConnCase, async: false

  test "revisions advance once for applied operations and never for rejections", %{conn: conn} do
    [opened, paid, invalid, moved, cancelled] =
      submit(conn, [
        open_group("rev-open", "rev-group"),
        payment("rev-pay", "rev-group", 1_000, 1),
        payment("rev-invalid", "rev-group", 0, 2),
        reschedule("rev-move", "rev-group", "2027-08-01", 2),
        cancel("rev-cancel", "rev-group", 3)
      ])

    assert opened["revision"] == 1
    assert paid["revision"] == 2
    assert invalid["code"] == "invalid_amount"
    assert moved["revision"] == 3
    assert cancelled["revision"] == 4

    group = get_data(conn, "/api/v1/groups/rev-group")
    assert group["revision"] == 4
    assert group["status"] == "cancelled"
  end

  test "same-batch guards see prior writes and staleness precedes domain validation", %{
    conn: conn
  } do
    [opened, paid, stale, invalid, missing, paid_again] =
      submit(conn, [
        open_group("batch-open", "batch-group"),
        payment("batch-pay", "batch-group", 1_000, 1),
        payment("batch-stale", "batch-group", 99_000, 1),
        payment("batch-invalid", "batch-group", 0, 2),
        payment("batch-missing", "missing-group", 1_000, 99),
        payment("batch-pay-again", "batch-group", 1_000, 2)
      ])

    assert opened["revision"] == 1
    assert paid["revision"] == 2

    assert %{
             "operation_id" => "batch-stale",
             "status" => "rejected",
             "code" => "stale_revision",
             "group_id" => "batch-group",
             "expected_revision" => 1,
             "actual_revision" => 2
           } = stale

    assert invalid["code"] == "invalid_amount"
    assert missing["code"] == "group_not_found"
    assert missing["actual_revision"] == nil
    assert paid_again["revision"] == 3

    group = get_data(conn, "/api/v1/groups/batch-group")
    assert group["revision"] == 3
    assert group["deposit_paid_cents"] == 2_000
  end

  defp open_group(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => "revision-guest",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-03",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp payment(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
    }
  end

  defp reschedule(operation_id, group_id, arrival_on, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "reschedule_group",
      "occurred_on" => "2027-05-03",
      "group_id" => group_id,
      "new_arrival_on" => arrival_on,
      "expected_revision" => expected_revision
    }
  end

  defp cancel(operation_id, group_id, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => "2027-07-01",
      "group_id" => group_id,
      "expected_revision" => expected_revision
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
end
