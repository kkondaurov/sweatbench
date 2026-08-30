defmodule GroupStay.Private.PolicyChangeTest do
  use GroupStayWeb.ConnCase, async: false

  test "the 30-day policy starts on its effective booking date", %{conn: conn} do
    first = open_group("open-exact", "exact", "2027-01-01", "2027-03-02")
    second = open_group("open-late", "late", "2027-01-01", "2027-03-02")

    cancellations = [
      %{
        "operation_id" => "cancel-exact",
        "type" => "cancel_group",
        "occurred_on" => "2027-01-31",
        "group_id" => "exact"
      },
      %{
        "operation_id" => "cancel-late",
        "type" => "cancel_group",
        "occurred_on" => "2027-02-01",
        "group_id" => "late"
      }
    ]

    submit(conn, [first, payment("pay-exact", "exact"), second, payment("pay-late", "late")])
    [exact, late] = submit(conn, cancellations)

    assert exact["refunded_cents"] == 2_000
    assert late["retained_cents"] == 2_000
    assert get_data(conn, "/api/v1/groups/exact")["policy_version"] == "flex-30"
  end

  test "a grandfathered policy survives a move while its deadline follows arrival", %{conn: conn} do
    operations = [
      open_group("open-old", "old", "2026-12-31", "2027-03-01"),
      %{
        "operation_id" => "move-old",
        "type" => "reschedule_group",
        "occurred_on" => "2027-01-10",
        "group_id" => "old",
        "new_arrival_on" => "2027-04-01"
      }
    ]

    [_opened, moved] = submit(conn, operations)
    assert moved["policy_version"] == "flex-14"
    assert moved["new_departure_on"] == "2027-04-02"
    assert moved["refundable_until"] == "2027-03-18"

    group = get_data(conn, "/api/v1/groups/old")
    assert group["booked_on"] == "2026-12-31"
    assert group["arrival_on"] == "2027-04-01"
  end

  defp open_group(operation_id, group_id, booked_on, arrival_on) do
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
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp payment(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-01-02",
      "group_id" => group_id,
      "amount_cents" => 2_000
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
