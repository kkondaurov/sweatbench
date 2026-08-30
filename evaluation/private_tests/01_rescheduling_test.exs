defmodule GroupStay.Private.ReschedulingTest do
  use GroupStayWeb.ConnCase, async: false

  test "moving a group preserves stay length and moves the refund boundary", %{conn: conn} do
    submit(conn, [
      open_group("open-move", "move", "2027-03-01"),
      payment("pay-move", "move", 4_000)
    ])

    [moved] =
      submit(conn, [
        %{
          "operation_id" => "move-group",
          "type" => "reschedule_group",
          "occurred_on" => "2027-01-10",
          "group_id" => "move",
          "new_arrival_on" => "2027-04-01"
        }
      ])

    assert moved["group_id"] == "move"
    assert moved["new_arrival_on"] == "2027-04-01"
    assert moved["new_departure_on"] == "2027-04-03"

    [cancelled] =
      submit(conn, [
        %{
          "operation_id" => "cancel-move",
          "type" => "cancel_group",
          "occurred_on" => "2027-03-18",
          "group_id" => "move"
        }
      ])

    assert cancelled["refunded_cents"] == 4_000
    assert cancelled["retained_cents"] == 0
  end

  test "invalid, missing, and inactive reschedules leave state coherent", %{conn: conn} do
    submit(conn, [open_group("open-errors", "errors", "2027-03-01")])

    [invalid] =
      submit(conn, [
        %{
          "operation_id" => "move-invalid",
          "type" => "reschedule_group",
          "occurred_on" => "2027-02-01",
          "group_id" => "errors",
          "new_arrival_on" => "2027-02-01"
        }
      ])

    assert invalid["code"] == "invalid_stay"
    assert get_data(conn, "/api/v1/groups/errors")["arrival_on"] == "2027-03-01"

    [cancelled, inactive, missing] =
      submit(conn, [
        %{
          "operation_id" => "cancel-errors",
          "type" => "cancel_group",
          "occurred_on" => "2027-01-01",
          "group_id" => "errors"
        },
        %{
          "operation_id" => "move-inactive",
          "type" => "reschedule_group",
          "occurred_on" => "2027-01-02",
          "group_id" => "errors",
          "new_arrival_on" => "2027-04-01"
        },
        %{
          "operation_id" => "move-missing",
          "type" => "reschedule_group",
          "occurred_on" => "2027-01-02",
          "group_id" => "missing",
          "new_arrival_on" => "2027-04-01"
        }
      ])

    assert cancelled["status"] == "applied"
    assert inactive["code"] == "group_not_active"
    assert missing["code"] == "group_not_found"
  end

  defp open_group(operation_id, group_id, arrival_on) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2026-12-01",
      "group_id" => group_id,
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 2) |> Date.to_iso8601(),
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp payment(operation_id, group_id, amount_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2026-12-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents
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
