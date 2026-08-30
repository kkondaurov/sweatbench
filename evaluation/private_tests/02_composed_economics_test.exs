defmodule GroupStay.Private.ComposedEconomicsTest do
  use GroupStayWeb.ConnCase, async: false

  test "rescheduling can move groups into and out of refundable territory", %{conn: conn} do
    submit(conn, [
      open_group("open-late", "late", "guest-a", "2026-12-15", "2027-03-01", 20_000),
      payment("pay-late", "late", "2026-12-16", 4_000)
    ])

    [moved_later] = submit(conn, [reschedule("move-late", "late", "2027-02-20", "2027-04-01")])
    assert moved_later["policy_version"] == "flex-14"
    assert moved_later["refundable_until"] == "2027-03-18"

    [credited] = submit(conn, [cancel("cancel-late", "late", "2027-02-21", "hotel_credit")])
    assert credited["credit_issued_cents"] == 4_400

    submit(conn, [
      open_group("open-early", "early", "guest-b", "2027-01-05", "2027-06-01", 10_000),
      payment("pay-early", "early", "2027-01-06", 2_000)
    ])

    [moved_earlier] =
      submit(conn, [reschedule("move-early", "early", "2027-04-01", "2027-04-20")])

    assert moved_earlier["policy_version"] == "flex-30"
    assert moved_earlier["refundable_until"] == "2027-03-21"

    [retained] = submit(conn, [cancel("cancel-early", "early", "2027-04-02")])
    assert retained["retained_cents"] == 2_000

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-02")
    assert ledger["cash_converted_to_credit_cents"] == 4_000
    assert ledger["cash_retained_cents"] == 2_000
    assert ledger["credit_liability_cents"] == 4_400
  end

  defp open_group(operation_id, group_id, guest_id, booked_on, arrival_on, rate) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => booked_on,
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => rate}]
    }
  end

  defp payment(operation_id, group_id, occurred_on, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp reschedule(operation_id, group_id, occurred_on, arrival_on) do
    %{
      "operation_id" => operation_id,
      "type" => "reschedule_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "new_arrival_on" => arrival_on
    }
  end

  defp cancel(operation_id, group_id, occurred_on, method \\ nil) do
    operation = %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id
    }

    if method, do: Map.put(operation, "refund_method", method), else: operation
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
