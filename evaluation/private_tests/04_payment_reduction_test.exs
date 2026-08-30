defmodule GroupStay.Private.PaymentReductionTest do
  use GroupStayWeb.ConnCase, async: false

  test "a payment retains reducible provenance after one funded room is settled", %{conn: conn} do
    submit(conn, [
      open_group("p1-open", "p1", "guest-1", "2027-06-01", [
        {"room-a", 10_000},
        {"room-b", 10_000},
        {"room-c", 10_000}
      ]),
      payment("p1-payment", "p1", 3_500)
    ])

    [cancelled] =
      submit(conn, [cancel_rooms("p1-cancel-b", "p1", "2027-04-01", ["room-b"])])

    assert cancelled["refunded_cents"] == 1_500

    [first, second, exhausted] =
      submit(conn, [
        reduction("p1-reduce-1", "p1-payment", 1_000),
        reduction("p1-reduce-2", "p1-payment", 1_000),
        reduction("p1-reduce-3", "p1-payment", 1)
      ])

    assert first["outstanding_deposit_cents"] == 3_000
    assert second["outstanding_deposit_cents"] == 4_000
    assert exhausted["code"] == "payment_not_reducible"

    rooms = get_data(conn, "/api/v1/groups/p1")["rooms"] |> Map.new(&{&1["room_id"], &1})
    assert rooms["room-a"]["cash_paid_cents"] == 0
    assert rooms["room-c"]["cash_paid_cents"] == 0

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-02")
    assert ledger["cash_refunded_cents"] == 1_500
    assert ledger["cash_reduced_cents"] == 2_000
    assert_cash_conservation(ledger, 3_500)
  end

  test "reduction errors distinguish existence, permanence, amount, and capacity", %{conn: conn} do
    rejected_payment = payment("rejected-payment", "later", 1_000)
    [rejected] = submit(conn, [rejected_payment])
    assert rejected["code"] == "group_not_found"

    submit(conn, [
      open_group("open-later", "later", "guest-1", "2027-06-01", [{"room-a", 10_000}]),
      payment("held-payment", "later", 1_000)
    ])

    [missing, rejected_target, wrong_type, zero, negative, too_large] =
      submit(conn, [
        reduction("reduce-missing", "missing-operation", 1),
        reduction("reduce-rejected", "rejected-payment", 1),
        reduction("reduce-open", "open-later", 1),
        reduction("reduce-zero", "held-payment", 0),
        reduction("reduce-negative", "held-payment", -1),
        reduction("reduce-too-large", "held-payment", 1_001)
      ])

    assert missing["code"] == "operation_not_found"
    assert rejected_target["code"] == "payment_not_reducible"
    assert wrong_type["code"] == "payment_not_reducible"
    assert zero["code"] == "invalid_amount"
    assert negative["code"] == "invalid_amount"
    assert too_large["code"] == "reduction_exceeds_held_cash"
    assert get_data(conn, "/api/v1/groups/later")["cash_paid_cents"] == 1_000
  end

  test "a reduction reopens room for credit and later credit issuance uses remaining cash", %{
    conn: conn
  } do
    submit(conn, [
      open_group("open-source", "source", "guest-1", "2027-06-01", [{"room-source", 20_000}]),
      payment("pay-source", "source", 4_000),
      cancel_group("cancel-source", "source", "2027-04-01", "hotel_credit"),
      open_group("open-target", "target", "guest-1", "2027-07-01", [
        {"room-a", 10_000},
        {"room-b", 10_000}
      ]),
      payment("pay-target", "target", 4_000),
      reduction("reduce-target", "pay-target", 1_500),
      apply_credit("credit-target", "target", 1_500)
    ])

    group = get_data(conn, "/api/v1/groups/target")
    assert group["cash_paid_cents"] == 2_500
    assert group["credit_paid_cents"] == 1_500
    assert group["outstanding_deposit_cents"] == 0

    [cancelled] =
      submit(conn, [cancel_group("cancel-target", "target", "2027-04-03", "hotel_credit")])

    assert cancelled["credit_issued_cents"] == 2_750

    credit = get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-04-03")
    assert credit["available_cents"] == 7_150

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-03")
    assert ledger["cash_converted_to_credit_cents"] == 6_500
    assert ledger["cash_reduced_cents"] == 1_500
    assert ledger["credit_liability_cents"] == 7_150
    assert_cash_conservation(ledger, 8_000)
  end

  test "payment and reduction retries preserve their original results", %{conn: conn} do
    submit(conn, [
      open_group("open-idem", "idem", "guest-1", "2027-06-01", [{"room-a", 10_000}])
    ])

    target = payment("pay-idem", "idem", 2_000)
    [original_payment] = submit(conn, [target])
    correction = reduction("reduce-idem", "pay-idem", 500)
    [original_reduction] = submit(conn, [correction])

    [payment_retry, reduction_retry] = submit(conn, [target, correction])
    assert payment_retry == original_payment
    assert reduction_retry == original_reduction

    [conflict] = submit(conn, [Map.put(correction, "amount_cents", 400)])
    assert conflict["code"] == "operation_id_conflict"
    assert get_data(conn, "/api/v1/operations/reduce-idem") == original_reduction

    group = get_data(conn, "/api/v1/groups/idem")
    assert group["cash_paid_cents"] == 1_500
    assert group["outstanding_deposit_cents"] == 500
  end

  test "settled cash is immovable and exhaustion is not a group-state error", %{conn: conn} do
    submit(conn, [
      open_group("open-settled", "settled", "guest-1", "2027-06-01", [
        {"room-a", 10_000},
        {"room-b", 10_000}
      ]),
      payment("pay-settled", "settled", 3_000)
    ])

    [partial] =
      submit(conn, [cancel_rooms("cancel-settled-a", "settled", "2027-05-25", ["room-a"])])

    assert partial["retained_cents"] == 2_000

    [reduced] = submit(conn, [reduction("reduce-settled", "pay-settled", 1_000)])
    assert reduced["outstanding_deposit_cents"] == 2_000

    [cancelled] = submit(conn, [cancel_group("cancel-settled-rest", "settled", "2027-05-27")])
    assert cancelled["retained_cents"] == 0

    [after_cancel] = submit(conn, [reduction("reduce-after-cancel", "pay-settled", 1)])
    assert after_cancel["code"] == "payment_not_reducible"

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-27")
    assert ledger["cash_retained_cents"] == 2_000
    assert ledger["cash_reduced_cents"] == 1_000
    assert_cash_conservation(ledger, 3_000)
  end

  defp open_group(operation_id, group_id, guest_id, arrival_on, rooms) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-02-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => "flexible",
      "rooms" =>
        Enum.map(rooms, fn {room_id, rate} ->
          %{"room_id" => room_id, "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-03-01",
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp reduction(operation_id, payment_operation_id, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "reduce_cash_payment",
      "occurred_on" => "2027-04-02",
      "payment_operation_id" => payment_operation_id,
      "amount_cents" => amount
    }
  end

  defp apply_credit(operation_id, group_id, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => "2027-04-02",
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp cancel_group(operation_id, group_id, occurred_on, method \\ nil) do
    cancellation(operation_id, "cancel_group", group_id, occurred_on, method)
  end

  defp cancel_rooms(operation_id, group_id, occurred_on, room_ids) do
    cancellation(operation_id, "cancel_rooms", group_id, occurred_on, nil)
    |> Map.put("room_ids", room_ids)
  end

  defp cancellation(operation_id, type, group_id, occurred_on, method) do
    operation = %{
      "operation_id" => operation_id,
      "type" => type,
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

  defp assert_cash_conservation(ledger, recorded) do
    assert recorded ==
             Map.get(ledger, "cash_held_cents", 0) +
               Map.get(ledger, "cash_refunded_cents", 0) +
               Map.get(ledger, "cash_retained_cents", 0) +
               Map.get(ledger, "cash_converted_to_credit_cents", 0) +
               Map.get(ledger, "cash_reduced_cents", 0)
  end
end
