defmodule GroupStay.Acceptance.DepositTransferTest do
  use GroupStayWeb.ConnCase, async: false

  test "deposit funding can move between groups without changing finance totals", %{conn: conn} do
    [_source, _destination, _first, _second, transferred] =
      submit(conn, [
        open_group("open-source", "source", [10_000, 10_000]),
        open_group("open-destination", "destination", [10_000]),
        payment("pay-first", "source", 2_000, 1),
        payment("pay-second", "source", 1_000, 2),
        %{
          "operation_id" => "transfer-1",
          "type" => "transfer_deposit",
          "occurred_on" => "2027-05-03",
          "source_group_id" => "source",
          "destination_group_id" => "destination",
          "amount_cents" => 1_500,
          "expected_revision" => 3,
          "destination_expected_revision" => 1
        }
      ])

    assert transferred == %{
             "operation_id" => "transfer-1",
             "status" => "applied",
             "source_group_id" => "source",
             "destination_group_id" => "destination",
             "amount_cents" => 1_500,
             "source_outstanding_deposit_cents" => 2_500,
             "destination_outstanding_deposit_cents" => 500,
             "source_revision" => 4,
             "destination_revision" => 2
           }

    source = get_data(conn, "/api/v1/groups/source")
    destination = get_data(conn, "/api/v1/groups/destination")
    assert source["cash_paid_cents"] == 1_500
    assert destination["cash_paid_cents"] == 1_500

    assert get_data(conn, "/api/v1/payments/pay-second")["held_by_group"] == [
             %{"group_id" => "destination", "amount_cents" => 1_000}
           ]

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-03")
    assert ledger["cash_held_cents"] == 3_000
  end

  defp open_group(operation_id, group_id, rates) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-02",
      "rate_plan" => "flexible",
      "rooms" =>
        rates
        |> Enum.with_index(1)
        |> Enum.map(fn {rate, index} ->
          %{"room_id" => "#{group_id}-room-#{index}", "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
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
