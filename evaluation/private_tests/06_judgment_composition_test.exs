defmodule GroupStay.Private.JudgmentCompositionSixTest do
  use GroupStayWeb.ConnCase, async: false

  test "restored transferred credit absorbs its original lot shortfall before availability", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("absorb-start", "2027-06-01"),
      open_group("absorb-origin-open", "absorb-origin", "absorb-guest", "ams-canal"),
      payment("absorb-origin-pay", "absorb-origin", 1_000, "2027-06-01"),
      cancel_group(
        "absorb-origin-credit",
        "absorb-origin",
        "2027-06-01",
        "hotel_credit"
      ),
      open_group("absorb-source-open", "absorb-source", "absorb-guest", "ams-canal"),
      open_group(
        "absorb-destination-open",
        "absorb-destination",
        "absorb-guest",
        "rome-centro"
      ),
      apply_credit("absorb-apply", "absorb-source", 700, "2027-06-02"),
      chargeback("absorb-chargeback", "absorb-origin-pay", "2027-06-03"),
      transfer(
        "absorb-transfer",
        "absorb-source",
        "absorb-destination",
        500,
        "2027-06-04"
      ),
      cancel_group("absorb-restore", "absorb-destination", "2027-06-05", nil)
    ])

    source = get_data(conn, "/api/v1/groups/absorb-source")
    destination = get_data(conn, "/api/v1/groups/absorb-destination")
    assert source["credit_paid_cents"] == 200
    assert destination["status"] == "cancelled"
    assert destination["credit_paid_cents"] == 0

    credit = get_data(conn, "/api/v1/guests/absorb-guest/credit?on=2027-06-05")
    assert credit["available_cents"] == 0
    assert credit["lots"] == []

    ledger = get_data(conn, "/api/v1/ledger?on=2027-06-05")
    assert ledger["credit_liability_cents"] == 200
    assert ledger["credit_shortfall_cents"] == 200

    report = report(conn, "2027-06-05")
    assert report["credit"]["movements"]["absorbed_cents"] == 500
    assert report["credit"]["opening_liability_cents"] == 700
    assert report["credit"]["closing_liability_cents"] == 200
  end

  test "a pre-reporting durable payment retry leaves the opening and movements unchanged", %{
    conn: conn
  } do
    original_payment = payment("replay-pay", "replay-group", 1_000, "2027-07-01")

    [_opened, first_result] =
      submit(conn, [
        open_group("replay-open", "replay-group", "replay-guest", "ams-canal"),
        original_payment
      ])

    submit(conn, [start_reporting("replay-start", "2027-06-01")])

    report_before = report(conn, "2027-06-01")
    group_before = get_data(conn, "/api/v1/groups/replay-group")
    ledger_before = get_data(conn, "/api/v1/ledger?on=2027-06-01")

    assert cash(report_before, "ams-canal")["opening_held_cents"] == 1_000
    assert cash(report_before, "ams-canal")["closing_held_cents"] == 1_000
    assert Enum.all?(cash(report_before, "ams-canal")["movements"], fn {_key, value} ->
             value == 0
           end)

    assert submit(conn, [original_payment]) == [first_result]
    assert report(conn, "2027-06-01") == report_before
    assert get_data(conn, "/api/v1/groups/replay-group") == group_before
    assert get_data(conn, "/api/v1/ledger?on=2027-06-01") == ledger_before
    assert get_data(conn, "/api/v1/operations/replay-pay") == first_result
  end

  defp cash(report, property_id) do
    Enum.find(report["cash"], &(&1["property_id"] == property_id))
  end

  defp report(conn, date) do
    get_data(conn, "/api/v1/finance/daily-report?date=#{date}")
  end

  defp start_reporting(operation_id, starts_on) do
    %{
      "operation_id" => operation_id,
      "type" => "start_finance_reporting",
      "occurred_on" => starts_on,
      "starts_on" => starts_on
    }
  end

  defp open_group(operation_id, group_id, guest_id, property_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => property_id,
      "arrival_on" => "2027-12-01",
      "departure_on" => "2027-12-02",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "#{group_id}-room", "nightly_rate_cents" => 5_000}]
    }
  end

  defp payment(operation_id, group_id, amount_cents, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount_cents
    }
  end

  defp cancel_group(operation_id, group_id, occurred_on, refund_method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id
    }
    |> maybe_put("refund_method", refund_method)
  end

  defp apply_credit(operation_id, group_id, amount_cents, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount_cents
    }
  end

  defp chargeback(operation_id, payment_operation_id, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => occurred_on,
      "payment_operation_id" => payment_operation_id
    }
  end

  defp transfer(operation_id, source, destination, amount_cents, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "transfer_deposit",
      "occurred_on" => occurred_on,
      "source_group_id" => source,
      "destination_group_id" => destination,
      "amount_cents" => amount_cents
    }
  end

  defp maybe_put(map, _key, nil), do: map
  defp maybe_put(map, key, value), do: Map.put(map, key, value)

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
