defmodule GroupStay.Acceptance.PeriodCloseTest do
  use GroupStayWeb.ConnCase, async: false

  test "an old-dated payment after close is visible on the first open day", %{conn: conn} do
    submit(conn, [
      start_reporting("start", "2027-06-01"),
      open_group("open", "group-1"),
      close_period("close", "2027-06-30"),
      payment("late-pay", "group-1", 500, "2027-06-15")
    ])

    closed = get_data(conn, "/api/v1/finance/daily-report?date=2027-06-30")
    assert closed["status"] == "closed"

    open = get_data(conn, "/api/v1/finance/daily-report?date=2027-07-01")
    [cash] = open["cash"]
    assert cash["movements"]["received_cents"] == 0

    assert open["late_adjustments"]["cash"] == [
             %{
               "property_id" => "ams-canal",
               "movements" => %{
                 "received_cents" => 500,
                 "transferred_in_cents" => 0,
                 "transferred_out_cents" => 0,
                 "refunded_cents" => 0,
                 "retained_cents" => 0,
                 "converted_to_credit_cents" => 0,
                 "reduced_cents" => 0,
                 "charged_back_cents" => 0
               }
             }
           ]
  end

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

  defp open_group(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-06-01",
      "group_id" => group_id,
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-10-01",
      "departure_on" => "2027-10-02",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
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
