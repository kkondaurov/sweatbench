defmodule GroupStay.Private.ComposedDurabilityTest do
  use GroupStayWeb.ConnCase, async: false

  test "retries preserve cancellation and credit side effects", %{conn: conn} do
    submit(conn, [
      open_group("open-source", "source", "2027-02-01", "2027-06-01", 20_000),
      payment("pay-source", "source", "2027-02-02", 4_000),
      cancel("cancel-source", "source", "2027-04-01", "hotel_credit"),
      open_group("open-idem", "idem", "2027-02-01", "2027-07-01", 20_000),
      payment("pay-idem", "idem", "2027-02-02", 4_000)
    ])

    rejected_apply = apply_credit("apply-rejected", "idem", "2027-04-02", 500)
    [first_rejection] = submit(conn, [rejected_apply])
    assert first_rejection["code"] == "payment_exceeds_outstanding"

    cancellation = cancel("cancel-idem", "idem", "2027-04-03", "hotel_credit")
    [first_cancellation] = submit(conn, [cancellation])
    [retried_cancellation] = submit(conn, [cancellation])
    assert retried_cancellation == first_cancellation

    credit = get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-04-03")
    assert credit["available_cents"] == 8_800

    assert Enum.map(credit["lots"], &Map.take(&1, ["source_operation_id", "remaining_cents"])) ==
             [
               %{"source_operation_id" => "cancel-source", "remaining_cents" => 4_400},
               %{"source_operation_id" => "cancel-idem", "remaining_cents" => 4_400}
             ]

    [retried_rejection] = submit(conn, [rejected_apply])
    assert retried_rejection == first_rejection

    submit(conn, [open_group("open-next", "next", "2027-04-04", "2027-09-01", 50_000)])
    application = apply_credit("apply-next", "next", "2027-04-04", 6_000)
    [first_application] = submit(conn, [application])
    [retried_application] = submit(conn, [application])
    assert retried_application == first_application

    next_group = get_data(conn, "/api/v1/groups/next")
    assert next_group["credit_paid_cents"] == 6_000
    assert next_group["outstanding_deposit_cents"] == 4_000

    remaining = get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-04-04")
    assert remaining["available_cents"] == 2_800

    assert Enum.map(remaining["lots"], &Map.take(&1, ["source_operation_id", "remaining_cents"])) ==
             [
               %{"source_operation_id" => "cancel-idem", "remaining_cents" => 2_800}
             ]

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-04")
    assert ledger["cash_converted_to_credit_cents"] == 8_000
    assert ledger["credit_liability_cents"] == 8_800
  end

  defp open_group(operation_id, group_id, booked_on, arrival_on, rate) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => booked_on,
      "group_id" => group_id,
      "guest_id" => "guest-1",
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

  defp apply_credit(operation_id, group_id, occurred_on, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp cancel(operation_id, group_id, occurred_on, method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => method
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
