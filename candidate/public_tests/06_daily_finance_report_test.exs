defmodule GroupStay.Acceptance.DailyFinanceReportTest do
  use GroupStayWeb.ConnCase, async: false

  test "a reporting start separates opening position from daily movements", %{conn: conn} do
    submit(conn, [
      open_group("opening-group", "opening", "ams-canal"),
      payment("opening-pay", "opening", 1_000, "2027-06-01"),
      start_reporting("reporting-start", "2027-06-01"),
      open_group("movement-group", "movement", "ams-canal"),
      payment("movement-pay", "movement", 500, "2027-06-01")
    ])

    report = get_data(conn, "/api/v1/finance/daily-report?date=2027-06-01")
    assert report["status"] == "open"

    assert report["cash"] == [
             %{
               "property_id" => "ams-canal",
               "opening_held_cents" => 1_000,
               "movements" => %{
                 "received_cents" => 500,
                 "transferred_in_cents" => 0,
                 "transferred_out_cents" => 0,
                 "refunded_cents" => 0,
                 "retained_cents" => 0,
                 "converted_to_credit_cents" => 0,
                 "reduced_cents" => 0,
                 "charged_back_cents" => 0
               },
               "closing_held_cents" => 1_500
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

  defp open_group(operation_id, group_id, property_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => "guest-1",
      "property_id" => property_id,
      "arrival_on" => "2027-10-01",
      "departure_on" => "2027-10-02",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "#{group_id}-room", "nightly_rate_cents" => 10_000}]
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
