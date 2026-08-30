defmodule GroupStay.Acceptance.CancellationEconomicsTest do
  use GroupStayWeb.ConnCase, async: false

  test "policy remains fixed while a moved refundable group becomes hotel credit", %{conn: conn} do
    submit(conn, [open_group("open-first", "first", "2026-12-31", "2027-05-01")])

    before_move = get_data(conn, "/api/v1/groups/first")
    assert before_move["policy_version"] == "flex-14"
    assert before_move["refundable_until"] == "2027-04-17"

    [_paid, moved, cancelled, _opened_second, credited] =
      submit(conn, [
        cash_payment("pay-first", "first", 4_000),
        %{
          "operation_id" => "move-first",
          "type" => "reschedule_group",
          "occurred_on" => "2027-03-01",
          "group_id" => "first",
          "expected_revision" => 2,
          "new_arrival_on" => "2027-06-01"
        },
        %{
          "operation_id" => "cancel-first",
          "type" => "cancel_group",
          "occurred_on" => "2027-04-01",
          "group_id" => "first",
          "expected_revision" => 3,
          "refund_method" => "hotel_credit"
        },
        open_group("open-second", "second", "2027-03-01", "2027-07-01"),
        %{
          "operation_id" => "credit-second",
          "type" => "apply_hotel_credit",
          "occurred_on" => "2027-04-02",
          "group_id" => "second",
          "expected_revision" => 1,
          "amount_cents" => 3_000
        }
      ])

    assert moved["policy_version"] == "flex-14"
    assert moved["revision"] == 3
    assert moved["refundable_until"] == "2027-05-18"
    assert cancelled["credit_issued_cents"] == 4_400
    assert cancelled["revision"] == 4
    assert credited["outstanding_deposit_cents"] == 1_000
    assert credited["revision"] == 2

    credit = get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-04-02")
    assert credit["available_cents"] == 1_400

    assert [
             %{
               "source_operation_id" => "cancel-first",
               "remaining_cents" => 1_400,
               "expires_on" => "2028-03-31"
             }
           ] =
             credit["lots"]

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-02")
    assert ledger["credit_liability_cents"] == 4_400
    assert ledger["cash_converted_to_credit_cents"] == 4_000
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
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 2) |> Date.to_iso8601(),
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp cash_payment(operation_id, group_id, amount_cents) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-03-02",
      "group_id" => group_id,
      "expected_revision" => 1,
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
