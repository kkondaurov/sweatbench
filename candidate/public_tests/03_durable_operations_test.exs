defmodule GroupStay.Acceptance.DurableOperationsTest do
  use GroupStayWeb.ConnCase, async: false

  test "a retry returns its original result without applying payment twice", %{conn: conn} do
    open = %{
      "operation_id" => "open-retry",
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => "retry-group",
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-03",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }

    payment = %{
      "operation_id" => "pay-retry",
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
      "group_id" => "retry-group",
      "expected_revision" => 1,
      "amount_cents" => 1_000
    }

    submit_one(conn, open)
    first = submit_one(conn, payment)
    assert first["revision"] == 2

    moved =
      submit_one(conn, %{
        "operation_id" => "move-after-payment",
        "type" => "reschedule_group",
        "occurred_on" => "2027-05-03",
        "group_id" => "retry-group",
        "expected_revision" => 2,
        "new_arrival_on" => "2027-08-01"
      })

    assert moved["revision"] == 3
    assert submit_one(conn, payment) == first
    assert get_data(conn, "/api/v1/groups/retry-group")["deposit_paid_cents"] == 1_000

    conflict = submit_one(conn, Map.put(payment, "amount_cents", 2_000))
    assert conflict["code"] == "operation_id_conflict"
    assert get_data(conn, "/api/v1/operations/pay-retry") == first
  end

  defp submit_one(conn, operation) do
    conn
    |> recycle()
    |> post("/api/v1/partner-batches", %{"operations" => [operation]})
    |> json_response(200)
    |> Map.fetch!("results")
    |> List.first()
  end

  defp get_data(conn, path) do
    conn |> recycle() |> get(path) |> json_response(200) |> Map.fetch!("data")
  end
end
