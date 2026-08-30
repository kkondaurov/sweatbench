defmodule GroupStay.Acceptance.RoomAccountingTest do
  use GroupStayWeb.ConnCase, async: false

  test "reductions and chargebacks preserve payment provenance", %{conn: conn} do
    operations = [
      %{
        "operation_id" => "open-block",
        "type" => "open_group",
        "occurred_on" => "2027-05-01",
        "group_id" => "block",
        "guest_id" => "guest-1",
        "property_id" => "ams-canal",
        "arrival_on" => "2027-07-01",
        "departure_on" => "2027-07-02",
        "rate_plan" => "flexible",
        "rooms" => [
          %{"room_id" => "room-a", "nightly_rate_cents" => 10_000},
          %{"room_id" => "room-b", "nightly_rate_cents" => 10_000}
        ]
      },
      payment("pay-first", 2_500),
      payment("pay-second", 1_500),
      %{
        "operation_id" => "reduce-second",
        "type" => "reduce_cash_payment",
        "occurred_on" => "2027-05-03",
        "payment_operation_id" => "pay-second",
        "expected_revision" => 3,
        "amount_cents" => 1_000
      },
      %{
        "operation_id" => "chargeback-second",
        "type" => "charge_back_payment",
        "occurred_on" => "2027-05-04",
        "payment_operation_id" => "pay-second",
        "expected_revision" => 4
      }
    ]

    [_opened, _first, _second, reduced, charged_back] = submit(conn, operations)
    assert reduced["payment_operation_id"] == "pay-second"
    assert reduced["group_id"] == "block"
    assert reduced["outstanding_deposit_cents"] == 1_000
    assert reduced["revision"] == 4
    assert charged_back["charged_back_cents"] == 500
    assert charged_back["outstanding_deposit_cents"] == 1_500
    assert charged_back["revision"] == 5

    group = get_data(conn, "/api/v1/groups/block")
    rooms = Map.new(group["rooms"], &{&1["room_id"], &1})
    assert rooms["room-a"]["cash_paid_cents"] == 2_000
    assert rooms["room-b"]["cash_paid_cents"] == 500

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-03")
    assert ledger["cash_held_cents"] == 2_500
    assert ledger["cash_reduced_cents"] == 1_000
    assert ledger["cash_charged_back_cents"] == 500

    statement = get_data(conn, "/api/v1/payments/pay-second")

    assert statement == %{
             "payment_operation_id" => "pay-second",
             "original_group_id" => "block",
             "recorded_cents" => 1_500,
             "held_cents" => 0,
             "refunded_cents" => 0,
             "retained_cents" => 0,
             "converted_to_credit_cents" => 0,
             "reduced_cents" => 1_000,
             "charged_back_cents" => 500
           }
  end

  defp payment(operation_id, amount_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
      "group_id" => "block",
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
