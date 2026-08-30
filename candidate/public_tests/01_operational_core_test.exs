defmodule GroupStay.Acceptance.OperationalCoreTest do
  use GroupStayWeb.ConnCase, async: false

  test "a group can be opened, funded, moved, and cancelled", %{conn: conn} do
    operations = [
      %{
        "operation_id" => "open-81",
        "type" => "open_group",
        "occurred_on" => "2026-10-03",
        "group_id" => "group-81",
        "guest_id" => "guest-22",
        "property_id" => "ams-canal",
        "arrival_on" => "2026-12-10",
        "departure_on" => "2026-12-13",
        "rate_plan" => "flexible",
        "rooms" => [
          %{"room_id" => "room-a", "nightly_rate_cents" => 15_000},
          %{"room_id" => "room-b", "nightly_rate_cents" => 17_500}
        ]
      },
      %{
        "operation_id" => "pay-81",
        "type" => "record_cash_payment",
        "occurred_on" => "2026-10-04",
        "group_id" => "group-81",
        "expected_revision" => 1,
        "amount_cents" => 10_000
      },
      %{
        "operation_id" => "move-81",
        "type" => "reschedule_group",
        "occurred_on" => "2026-10-05",
        "group_id" => "group-81",
        "expected_revision" => 2,
        "new_arrival_on" => "2027-01-10"
      }
    ]

    [opened, paid, moved] = submit(conn, operations)
    assert opened["deposit_due_cents"] == 19_500
    assert opened["revision"] == 1
    assert paid["outstanding_deposit_cents"] == 9_500
    assert paid["revision"] == 2
    assert moved["new_arrival_on"] == "2027-01-10"
    assert moved["new_departure_on"] == "2027-01-13"
    assert moved["revision"] == 3

    active = get_data(conn, "/api/v1/groups/group-81")
    assert active["status"] == "active"
    assert active["revision"] == 3
    assert active["lodging_total_cents"] == 97_500
    assert active["arrival_on"] == "2027-01-10"

    [cancelled] =
      submit(conn, [
        %{
          "operation_id" => "cancel-81",
          "type" => "cancel_group",
          "occurred_on" => "2027-01-01",
          "group_id" => "group-81",
          "expected_revision" => 3
        }
      ])

    assert cancelled["refunded_cents"] == 0
    assert cancelled["retained_cents"] == 10_000
    assert cancelled["revision"] == 4
    assert get_data(conn, "/api/v1/groups/group-81")["status"] == "cancelled"

    ledger = get_data(conn, "/api/v1/ledger")
    assert ledger["cash_held_cents"] == 0
    assert ledger["cash_retained_cents"] == 10_000
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
