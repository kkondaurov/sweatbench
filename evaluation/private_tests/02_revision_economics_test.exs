defmodule GroupStay.Private.RevisionEconomicsTest do
  use GroupStayWeb.ConnCase, async: false

  test "a rejected refund method leaves the cancellation revision available", %{conn: conn} do
    [opened, paid, rejected, moved] =
      submit(conn, [
        open_group("econ-open", "econ-source", "econ-guest", "2027-05-20", "flexible"),
        payment("econ-pay", "econ-source", 2_000, 1),
        cancel("econ-reject", "econ-source", "2027-05-01", "hotel_credit", 2),
        reschedule("econ-move", "econ-source", "2027-06-20", 2)
      ])

    assert opened["revision"] == 1
    assert paid["revision"] == 2
    assert rejected["code"] == "refund_method_not_available"
    assert moved["revision"] == 3
    assert get_data(conn, "/api/v1/groups/econ-source")["revision"] == 3
  end

  test "credit applications use the target revision without advancing it on failure", %{
    conn: conn
  } do
    [_, _, source_cancelled] =
      submit(conn, [
        open_group(
          "credit-source-open",
          "credit-source",
          "credit-guest",
          "2027-09-01",
          "flexible"
        ),
        payment("credit-source-pay", "credit-source", 1_000, 1),
        cancel("credit-source-cancel", "credit-source", "2027-05-01", "hotel_credit", 2)
      ])

    assert source_cancelled["revision"] == 3

    [opened, insufficient, applied, stale] =
      submit(conn, [
        open_group(
          "credit-target-open",
          "credit-target",
          "credit-guest",
          "2027-10-01",
          "flexible"
        ),
        apply_credit("credit-too-much", "credit-target", 1_200, 1),
        apply_credit("credit-good", "credit-target", 1_000, 1),
        apply_credit("credit-stale", "credit-target", 99_000, 1)
      ])

    assert opened["revision"] == 1
    assert insufficient["code"] == "insufficient_credit"
    assert applied["revision"] == 2
    assert stale["code"] == "stale_revision"
    assert stale["actual_revision"] == 2

    target = get_data(conn, "/api/v1/groups/credit-target")
    assert target["revision"] == 2
    assert target["credit_paid_cents"] == 1_000
  end

  defp open_group(operation_id, group_id, guest_id, arrival_on, rate_plan) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-04-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => rate_plan,
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp payment(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-04-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
    }
  end

  defp cancel(operation_id, group_id, occurred_on, refund_method, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => refund_method,
      "expected_revision" => expected_revision
    }
  end

  defp reschedule(operation_id, group_id, arrival_on, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "reschedule_group",
      "occurred_on" => "2027-05-02",
      "group_id" => group_id,
      "new_arrival_on" => arrival_on,
      "expected_revision" => expected_revision
    }
  end

  defp apply_credit(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => "2027-05-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
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
