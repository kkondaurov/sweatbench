defmodule GroupStay.Private.DailyFinanceReportTest do
  use GroupStayWeb.ConnCase, async: false

  @cash_fields ~w(received_cents transferred_in_cents transferred_out_cents refunded_cents retained_cents converted_to_credit_cents reduced_cents charged_back_cents)
  @credit_fields ~w(issued_cents expired_cents consumed_cents revoked_cents absorbed_cents)

  test "cash movements bridge properties and reconcile to current held balances", %{conn: conn} do
    submit(conn, [
      start_reporting("cash-start", "2027-06-01"),
      open_group("cash-source-open", "cash-source", "guest-1", "ams-canal", [10_000]),
      open_group("cash-destination-open", "cash-destination", "guest-1", "berlin-mitte", [10_000]),
      payment("cash-pay", "cash-source", 2_000, "2027-06-01"),
      transfer("cash-transfer", "cash-source", "cash-destination", 500, "2027-06-01"),
      reduction("cash-reduce", "cash-pay", 300, "2027-06-01")
    ])

    report = report(conn, "2027-06-01")
    source = cash(report, "ams-canal")
    destination = cash(report, "berlin-mitte")

    assert source["opening_held_cents"] == 0
    assert source["movements"]["received_cents"] == 2_000
    assert source["movements"]["transferred_out_cents"] == 500
    assert source["closing_held_cents"] == 1_500

    assert destination["movements"]["transferred_in_cents"] == 500
    assert destination["movements"]["reduced_cents"] == 300
    assert destination["closing_held_cents"] == 200

    assert Enum.sum_by(report["cash"], & &1["movements"]["transferred_in_cents"]) ==
             Enum.sum_by(report["cash"], & &1["movements"]["transferred_out_cents"])

    ledger = get_data(conn, "/api/v1/ledger?on=2027-06-01")
    assert Enum.sum_by(report["cash"], & &1["closing_held_cents"]) == ledger["cash_held_cents"]
  end

  test "credit issuance and consumption reconcile the company liability", %{conn: conn} do
    submit(conn, [
      start_reporting("credit-start", "2027-06-01"),
      open_group("credit-source-open", "credit-source", "credit-guest", "ams-canal", [10_000]),
      payment("credit-pay", "credit-source", 1_000, "2027-06-01"),
      cancel_group("credit-issue", "credit-source", "2027-06-01", "hotel_credit"),
      open_group("credit-use-open", "credit-use", "credit-guest", "rome-centro", [10_000],
        rate_plan: "advance_purchase"
      ),
      apply_credit("credit-apply", "credit-use", 400, "2027-06-02"),
      cancel_group("credit-consume", "credit-use", "2027-06-02", nil)
    ])

    first = report(conn, "2027-06-01")
    assert first["credit"]["opening_liability_cents"] == 0
    assert first["credit"]["movements"]["issued_cents"] == 1_100
    assert first["credit"]["closing_liability_cents"] == 1_100

    second = report(conn, "2027-06-02")
    assert second["credit"]["opening_liability_cents"] == 1_100
    assert second["credit"]["movements"]["consumed_cents"] == 400
    assert second["credit"]["closing_liability_cents"] == 700

    assert second["credit"]["closing_liability_cents"] ==
             get_data(conn, "/api/v1/ledger?on=2027-06-02")["credit_liability_cents"]
  end

  test "cash properties are isolated, complete, and ordered", %{conn: conn} do
    submit(conn, [
      start_reporting("order-start", "2027-06-01"),
      open_group("order-z-open", "order-z", "order-guest", "zurich-lake", [10_000]),
      open_group("order-a-open", "order-a", "order-guest", "ams-canal", [10_000]),
      payment("order-z-pay", "order-z", 300, "2027-06-01"),
      payment("order-a-pay", "order-a", 200, "2027-06-01")
    ])

    report = report(conn, "2027-06-01")
    assert Enum.map(report["cash"], & &1["property_id"]) == ["ams-canal", "zurich-lake"]

    Enum.each(report["cash"], fn entry ->
      assert Map.keys(entry["movements"]) |> Enum.sort() == Enum.sort(@cash_fields)
    end)

    assert Map.keys(report["credit"]["movements"]) |> Enum.sort() == Enum.sort(@credit_fields)
  end

  test "reporting inception uses current state as opening and rejects unavailable dates", %{
    conn: conn
  } do
    submit(conn, [
      open_group("opening-open", "opening-group", "opening-guest", "ams-canal", [10_000]),
      payment("opening-pay", "opening-group", 1_200, "2027-08-01"),
      start_reporting("opening-start", "2027-06-10")
    ])

    inception = report(conn, "2027-06-10")
    assert cash(inception, "ams-canal")["opening_held_cents"] == 1_200
    assert cash(inception, "ams-canal")["closing_held_cents"] == 1_200
    assert cash(inception, "ams-canal")["movements"] == zero_cash()

    assert_error(
      conn,
      "/api/v1/finance/daily-report?date=2027-06-09",
      404,
      "report_not_available"
    )

    [again] = submit(conn, [start_reporting("opening-start-again", "2027-06-10")])
    assert again["status"] == "rejected"
    assert again["code"] == "reporting_already_started"
  end

  test "same-batch operations on opposite sides of inception are classified differently", %{
    conn: conn
  } do
    [_, _, started, _, _] =
      submit(conn, [
        open_group("batch-before-open", "batch-before", "batch-guest", "ams-canal", [10_000]),
        payment("batch-before-pay", "batch-before", 600, "2027-06-01"),
        start_reporting("batch-start", "2027-06-01"),
        open_group("batch-after-open", "batch-after", "batch-guest", "ams-canal", [10_000]),
        payment("batch-after-pay", "batch-after", 400, "2027-06-01")
      ])

    assert started == %{
             "operation_id" => "batch-start",
             "status" => "applied",
             "starts_on" => "2027-06-01"
           }

    entry = cash(report(conn, "2027-06-01"), "ams-canal")
    assert entry["opening_held_cents"] == 600
    assert entry["movements"]["received_cents"] == 400
    assert entry["closing_held_cents"] == 1_000
  end

  test "backdated operations use the reporting inception floor", %{conn: conn} do
    submit(conn, [
      start_reporting("floor-start", "2027-06-10"),
      open_group("floor-open", "floor-group", "floor-guest", "ams-canal", [10_000]),
      payment("floor-pay", "floor-group", 700, "2027-05-01")
    ])

    assert cash(report(conn, "2027-06-10"), "ams-canal")["movements"]["received_cents"] == 700
    assert report(conn, "2027-06-09") == :not_available
  end

  test "a chargeback reports signed reversal classifications without inventing held cash", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("reclass-start", "2027-06-01"),
      open_group("reclass-open", "reclass-group", "reclass-guest", "ams-canal", [10_000]),
      payment("reclass-pay", "reclass-group", 1_000, "2027-06-01"),
      cancel_group("reclass-refund", "reclass-group", "2027-06-02", "cash"),
      chargeback("reclass-chargeback", "reclass-pay", "2027-06-03")
    ])

    refund_day = cash(report(conn, "2027-06-02"), "ams-canal")
    assert refund_day["movements"]["refunded_cents"] == 1_000

    correction_day = cash(report(conn, "2027-06-03"), "ams-canal")
    assert correction_day["movements"]["refunded_cents"] == -1_000
    assert correction_day["movements"]["charged_back_cents"] == 1_000
    assert correction_day["opening_held_cents"] == 0
    assert correction_day["closing_held_cents"] == 0
  end

  test "unused credit expiry appears on the first day after its expiry without an operation", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("expiry-start", "2027-06-01"),
      open_group("expiry-open", "expiry-group", "expiry-guest", "ams-canal", [10_000]),
      payment("expiry-pay", "expiry-group", 1_000, "2027-06-01"),
      cancel_group("expiry-credit", "expiry-group", "2027-06-01", "hotel_credit")
    ])

    expiry_day = report(conn, "2028-05-31")
    assert expiry_day["credit"]["closing_liability_cents"] == 1_100

    first_expired_day = report(conn, "2028-06-01")
    assert first_expired_day["credit"]["opening_liability_cents"] == 1_100
    assert first_expired_day["credit"]["movements"]["expired_cents"] == 1_100
    assert first_expired_day["credit"]["closing_liability_cents"] == 0
  end

  test "equivalent batched and sequential histories produce equivalent reports", %{conn: conn} do
    submit(conn, [start_reporting("equivalent-start", "2027-06-01")])

    batched = history("batched", "batched-property")
    submit(conn, batched)
    Enum.each(history("sequential", "sequential-property"), &submit(conn, [&1]))

    report = report(conn, "2027-06-02")
    batched_cash = cash(report, "batched-property") |> Map.put("property_id", "property")
    sequential_cash = cash(report, "sequential-property") |> Map.put("property_id", "property")
    assert batched_cash == sequential_cash
    assert report == report(conn, "2027-06-02")
  end

  test "rejections and durable retries neither erase nor duplicate reporting movements", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("atomic-start", "2027-06-01"),
      open_group("atomic-open", "atomic-group", "atomic-guest", "ams-canal", [10_000])
    ])

    valid = payment("atomic-pay", "atomic-group", 1_000, "2027-06-01")
    invalid = payment("atomic-too-large", "atomic-group", 9_000, "2027-06-01")
    [applied, rejected] = submit(conn, [valid, invalid])
    assert applied["status"] == "applied"
    assert rejected["status"] == "rejected"
    assert submit(conn, [valid]) == [applied]

    entry = cash(report(conn, "2027-06-01"), "ams-canal")
    assert entry["movements"]["received_cents"] == 1_000
    assert entry["closing_held_cents"] == 1_000
  end

  defp history(prefix, property) do
    [
      open_group("#{prefix}-open", "#{prefix}-group", "#{prefix}-guest", property, [10_000]),
      payment("#{prefix}-pay", "#{prefix}-group", 1_000, "2027-06-01"),
      reduction("#{prefix}-reduce", "#{prefix}-pay", 200, "2027-06-02")
    ]
  end

  defp zero_cash, do: Map.new(@cash_fields, &{&1, 0})

  defp cash(report, property_id) do
    Enum.find(report["cash"], &(&1["property_id"] == property_id))
  end

  defp report(conn, date) do
    response = conn |> recycle() |> get("/api/v1/finance/daily-report?date=#{date}")

    case response.status do
      200 -> json_response(response, 200) |> Map.fetch!("data")
      404 -> :not_available
    end
  end

  defp assert_error(conn, path, status, code) do
    assert conn |> recycle() |> get(path) |> json_response(status) == %{
             "error" => %{"code" => code}
           }
  end

  defp start_reporting(operation_id, starts_on) do
    %{
      "operation_id" => operation_id,
      "type" => "start_finance_reporting",
      "occurred_on" => starts_on,
      "starts_on" => starts_on
    }
  end

  defp open_group(operation_id, group_id, guest_id, property_id, room_rates, options \\ []) do
    arrival_on = Keyword.get(options, :arrival_on, "2027-10-01")
    rate_plan = Keyword.get(options, :rate_plan, "flexible")

    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => property_id,
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => rate_plan,
      "rooms" =>
        room_rates
        |> Enum.with_index(1)
        |> Enum.map(fn {rate, index} ->
          %{"room_id" => "#{group_id}-room-#{index}", "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, amount, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp transfer(operation_id, source, destination, amount, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "transfer_deposit",
      "occurred_on" => occurred_on,
      "source_group_id" => source,
      "destination_group_id" => destination,
      "amount_cents" => amount
    }
  end

  defp reduction(operation_id, payment_operation_id, amount, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "reduce_cash_payment",
      "occurred_on" => occurred_on,
      "payment_operation_id" => payment_operation_id,
      "amount_cents" => amount
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

  defp apply_credit(operation_id, group_id, amount, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
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
