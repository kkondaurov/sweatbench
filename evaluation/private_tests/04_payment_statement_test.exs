defmodule GroupStay.Private.PaymentStatementTest do
  use GroupStayWeb.ConnCase, async: false

  test "a payment statement reconciles every cash disposition with group and ledger views", %{
    conn: conn
  } do
    submit(conn, [
      open_group("statement-open", "statement-group"),
      payment("statement-pay", "statement-group", 5_000),
      cancel_rooms("statement-refund", "statement-group", ["room-1"], "2027-04-01", "cash"),
      cancel_rooms(
        "statement-convert",
        "statement-group",
        ["room-2"],
        "2027-04-01",
        "hotel_credit"
      ),
      cancel_rooms("statement-retain", "statement-group", ["room-3"], "2027-05-15", "cash"),
      reduction("statement-reduce", "statement-pay", 500)
    ])

    assert get_data(conn, "/api/v1/payments/statement-pay") == %{
             "payment_operation_id" => "statement-pay",
             "original_group_id" => "statement-group",
             "recorded_cents" => 5_000,
             "held_cents" => 1_500,
             "refunded_cents" => 1_000,
             "retained_cents" => 1_000,
             "converted_to_credit_cents" => 1_000,
             "reduced_cents" => 500,
             "charged_back_cents" => 0
           }

    group = get_data(conn, "/api/v1/groups/statement-group")
    assert group["cash_paid_cents"] == 1_500
    assert group["outstanding_deposit_cents"] == 500

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-15")
    assert ledger["cash_held_cents"] == 1_500
    assert ledger["cash_refunded_cents"] == 1_000
    assert ledger["cash_retained_cents"] == 1_000
    assert ledger["cash_converted_to_credit_cents"] == 1_000
    assert ledger["cash_reduced_cents"] == 500

    [charged_back] = submit(conn, [chargeback("statement-charge", "statement-pay")])
    assert charged_back["charged_back_cents"] == 4_500

    assert get_data(conn, "/api/v1/payments/statement-pay") == %{
             "payment_operation_id" => "statement-pay",
             "original_group_id" => "statement-group",
             "recorded_cents" => 5_000,
             "held_cents" => 0,
             "refunded_cents" => 0,
             "retained_cents" => 0,
             "converted_to_credit_cents" => 0,
             "reduced_cents" => 500,
             "charged_back_cents" => 4_500
           }

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-15")
    assert ledger["cash_charged_back_cents"] == 4_500
    assert ledger["cash_reduced_cents"] == 500
    assert ledger["credit_liability_cents"] == 0
  end

  test "payment statements distinguish missing and non-payment operations", %{conn: conn} do
    submit(conn, [open_group("not-a-payment", "other-group")])

    rejected_payment = payment("rejected-payment", "missing-group", 1_000)
    [rejected] = submit(conn, [rejected_payment])
    assert rejected["code"] == "group_not_found"

    conn = conn |> recycle() |> get("/api/v1/payments/missing-operation")
    assert json_response(conn, 404) == %{"error" => %{"code" => "operation_not_found"}}

    for operation_id <- ["not-a-payment", "rejected-payment"] do
      conn = conn |> recycle() |> get("/api/v1/payments/#{operation_id}")
      assert json_response(conn, 422) == %{"error" => %{"code" => "payment_not_reconcilable"}}
    end
  end

  defp open_group(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-02-01",
      "group_id" => group_id,
      "guest_id" => "statement-guest",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-06-01",
      "departure_on" => "2027-06-02",
      "rate_plan" => "flexible",
      "rooms" =>
        Enum.map(1..5, fn index ->
          %{"room_id" => "room-#{index}", "nightly_rate_cents" => 5_000}
        end)
    }
  end

  defp payment(operation_id, group_id, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-02-02",
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp cancel_rooms(operation_id, group_id, room_ids, occurred_on, method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_rooms",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "room_ids" => room_ids,
      "refund_method" => method
    }
  end

  defp reduction(operation_id, payment_operation_id, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "reduce_cash_payment",
      "occurred_on" => "2027-05-16",
      "payment_operation_id" => payment_operation_id,
      "amount_cents" => amount
    }
  end

  defp chargeback(operation_id, payment_operation_id) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => "2027-05-17",
      "payment_operation_id" => payment_operation_id
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
