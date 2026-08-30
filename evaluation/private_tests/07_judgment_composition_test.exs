defmodule GroupStay.Private.JudgmentCompositionSevenTest do
  use GroupStayWeb.ConnCase, async: false

  @credit_fields ~w(issued_cents expired_cents consumed_cents revoked_cents absorbed_cents)

  test "a late chargeback follows transferred refunded cash to its settlement property", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("late-cross-start", "2027-06-01"),
      open_group("late-cross-source-open", "late-cross-source", "late-cross-guest", "ams-canal"),
      open_group(
        "late-cross-destination-open",
        "late-cross-destination",
        "late-cross-guest",
        "rome-centro"
      ),
      payment("late-cross-pay", "late-cross-source", 1_000, "2027-06-01"),
      transfer(
        "late-cross-transfer",
        "late-cross-source",
        "late-cross-destination",
        1_000,
        "2027-06-01"
      ),
      cancel_group("late-cross-refund", "late-cross-destination", "2027-06-02", nil),
      close_period("late-cross-close", "2027-06-30")
    ])

    published = report(conn, "2027-06-02")
    assert cash(published, "rome-centro")["movements"]["refunded_cents"] == 1_000

    [charged_back] =
      submit(conn, [chargeback("late-cross-chargeback", "late-cross-pay", "2027-06-03")])

    assert charged_back["charged_back_cents"] == 1_000
    assert report(conn, "2027-06-02") == published

    first_open = report(conn, "2027-07-01")
    destination = late_cash(first_open, "rome-centro")["movements"]
    assert destination["refunded_cents"] == -1_000
    assert destination["charged_back_cents"] == 1_000
    refute Enum.any?(first_open["late_adjustments"]["cash"], fn entry ->
             entry["property_id"] == "ams-canal"
           end)
  end

  test "revived expired credit can be consumed without rewriting or netting its history", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("double-start", "2027-06-01"),
      open_group("double-origin-open", "double-origin", "double-guest", "ams-canal"),
      open_group(
        "double-target-open",
        "double-target",
        "double-guest",
        "rome-centro",
        arrival_on: "2028-07-02"
      ),
      payment("double-origin-pay", "double-origin", 1_000, "2027-06-01"),
      cancel_group("double-issue", "double-origin", "2027-06-02", "hotel_credit"),
      close_period("double-close", "2028-06-30")
    ])

    published = report(conn, "2028-06-02")
    assert published["status"] == "closed"
    assert published["credit"]["movements"]["expired_cents"] == 1_100

    application = apply_credit("double-apply", "double-target", 600, "2027-06-03")
    [applied] = submit(conn, [application])
    assert applied["status"] == "applied"

    [settled] =
      submit(conn, [cancel_group("double-consume", "double-target", "2028-07-01", nil)])

    assert settled["retained_cents"] == 0
    assert report(conn, "2028-06-02") == published

    first_open = report(conn, "2028-07-01")
    assert first_open["credit"]["opening_liability_cents"] == 0
    assert first_open["credit"]["movements"] == Map.put(zero_credit(), "consumed_cents", 600)
    assert first_open["late_adjustments"]["credit"] ==
             Map.put(zero_credit(), "expired_cents", -600)
    assert first_open["credit"]["closing_liability_cents"] == 0

    ledger = get_data(conn, "/api/v1/ledger?on=2028-07-01")
    assert ledger["credit_liability_cents"] == 0
    assert get_data(conn, "/api/v1/guests/double-guest/credit?on=2028-07-01")["available_cents"] ==
             0
    assert get_data(conn, "/api/v1/groups/double-target")["status"] == "cancelled"
    assert get_data(conn, "/api/v1/operations/double-apply") == applied
  end

  defp cash(report, property_id) do
    Enum.find(report["cash"], &(&1["property_id"] == property_id))
  end

  defp late_cash(report, property_id) do
    Enum.find(report["late_adjustments"]["cash"], &(&1["property_id"] == property_id))
  end

  defp zero_credit, do: Map.new(@credit_fields, &{&1, 0})
  defp report(conn, date), do: get_data(conn, "/api/v1/finance/daily-report?date=#{date}")

  defp start_reporting(operation_id, starts_on) do
    %{
      "operation_id" => operation_id,
      "type" => "start_finance_reporting",
      "occurred_on" => starts_on,
      "starts_on" => starts_on
    }
  end

  defp close_period(operation_id, period_end_on) do
    %{
      "operation_id" => operation_id,
      "type" => "close_finance_period",
      "occurred_on" => period_end_on,
      "period_end_on" => period_end_on
    }
  end

  defp open_group(operation_id, group_id, guest_id, property_id, options \\ []) do
    arrival_on = Keyword.get(options, :arrival_on, "2027-12-01")

    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => property_id,
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
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

  defp cancel_group(operation_id, group_id, occurred_on, refund_method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id
    }
    |> maybe_put("refund_method", refund_method)
  end

  defp chargeback(operation_id, payment_operation_id, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => occurred_on,
      "payment_operation_id" => payment_operation_id
    }
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
