defmodule GroupStay.Private.PartialRoomCancellationTest do
  use GroupStayWeb.ConnCase, async: false

  test "partial settlement returns only the selected rooms' cash and credit", %{conn: conn} do
    operations =
      credit_source() ++
        [
          open_target(),
          payment("pay-target", "target", 2_500),
          %{
            "operation_id" => "credit-target",
            "type" => "apply_hotel_credit",
            "occurred_on" => "2027-05-03",
            "group_id" => "target",
            "amount_cents" => 1_500
          },
          %{
            "operation_id" => "cancel-room-b",
            "type" => "cancel_rooms",
            "occurred_on" => "2027-05-15",
            "group_id" => "target",
            "room_ids" => ["room-b"]
          }
        ]

    results = submit(conn, operations)
    cancelled = List.last(results)

    assert cancelled["refunded_cents"] == 500
    assert cancelled["retained_cents"] == 0
    assert cancelled["credit_issued_cents"] == 0

    group = get_data(conn, "/api/v1/groups/target")
    assert group["deposit_due_cents"] == 2_000
    assert group["cash_paid_cents"] == 2_000
    assert group["credit_paid_cents"] == 0

    rooms = Map.new(group["rooms"], &{&1["room_id"], &1})
    assert rooms["room-a"]["cash_paid_cents"] == 2_000
    assert rooms["room-b"]["status"] == "cancelled"

    assert get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-05-15")["available_cents"] ==
             4_400

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-15")
    assert ledger["cash_held_cents"] == 2_000
    assert ledger["cash_refunded_cents"] == 500
    assert ledger["cash_converted_to_credit_cents"] == 4_000
    assert ledger["credit_liability_cents"] == 4_400
  end

  test "one bad room identifier rejects the entire partial cancellation", %{conn: conn} do
    submit(conn, [open_target(), payment("pay-target", "target", 4_000)])

    [result] =
      submit(conn, [
        %{
          "operation_id" => "bad-selection",
          "type" => "cancel_rooms",
          "occurred_on" => "2027-05-15",
          "group_id" => "target",
          "room_ids" => ["room-a", "missing"]
        }
      ])

    assert result["status"] == "rejected"
    assert result["code"] == "invalid_rooms"

    group = get_data(conn, "/api/v1/groups/target")
    assert Enum.all?(group["rooms"], &(&1["status"] == "active"))
    assert group["deposit_paid_cents"] == 4_000
  end

  test "the same room cannot appear twice in a partial cancellation", %{conn: conn} do
    submit(conn, [open_target(), payment("pay-target", "target", 4_000)])

    [result] =
      submit(conn, [
        %{
          "operation_id" => "duplicate-selection",
          "type" => "cancel_rooms",
          "occurred_on" => "2027-05-15",
          "group_id" => "target",
          "room_ids" => ["room-a", "room-a"]
        }
      ])

    assert result["code"] == "invalid_rooms"
    assert get_data(conn, "/api/v1/groups/target")["deposit_paid_cents"] == 4_000
  end

  defp credit_source do
    [
      %{
        "operation_id" => "open-source",
        "type" => "open_group",
        "occurred_on" => "2027-03-01",
        "group_id" => "source",
        "guest_id" => "guest-1",
        "property_id" => "ams-canal",
        "arrival_on" => "2027-06-15",
        "departure_on" => "2027-06-17",
        "rate_plan" => "flexible",
        "rooms" => [%{"room_id" => "source-room", "nightly_rate_cents" => 10_000}]
      },
      payment("pay-source", "source", 4_000) |> Map.put("occurred_on", "2027-03-02"),
      %{
        "operation_id" => "cancel-source",
        "type" => "cancel_group",
        "occurred_on" => "2027-04-01",
        "group_id" => "source",
        "refund_method" => "hotel_credit"
      }
    ]
  end

  defp open_target do
    %{
      "operation_id" => "open-target",
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => "target",
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-02",
      "rate_plan" => "flexible",
      "rooms" => [
        %{"room_id" => "room-a", "nightly_rate_cents" => 10_000},
        %{"room_id" => "room-b", "nightly_rate_cents" => 10_000}
      ]
    }
  end

  defp payment(operation_id, group_id, amount_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
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
