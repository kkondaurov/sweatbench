defmodule GroupStay.Private.DurableIdempotencyTest do
  use GroupStayWeb.ConnCase, async: false

  test "a rejected result remains stable after domain state changes", %{conn: conn} do
    payment = %{
      "operation_id" => "pay-before-open",
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-01",
      "group_id" => "later",
      "amount_cents" => 1_000
    }

    [first_rejection] = submit(conn, [payment])
    assert first_rejection["code"] == "group_not_found"

    submit(conn, [open_group()])
    [retry] = submit(conn, [payment])

    assert retry == first_rejection
    assert get_data(conn, "/api/v1/groups/later")["deposit_paid_cents"] == 0
    assert get_data(conn, "/api/v1/operations/pay-before-open") == first_rejection
  end

  test "a conflict cannot replace the original record or duplicate its effects", %{conn: conn} do
    payment = %{
      "operation_id" => "stable-payment",
      "type" => "record_cash_payment",
      "occurred_on" => "2027-05-02",
      "group_id" => "later",
      "amount_cents" => 1_000
    }

    submit(conn, [open_group()])
    [first, retry] = submit(conn, [payment, payment])
    assert retry == first

    [conflict] = submit(conn, [Map.put(payment, "amount_cents", 1_500)])
    assert conflict["code"] == "operation_id_conflict"

    assert get_data(conn, "/api/v1/operations/stable-payment") == first
    assert get_data(conn, "/api/v1/groups/later")["deposit_paid_cents"] == 1_000
    assert get_data(conn, "/api/v1/ledger")["cash_held_cents"] == 1_000
  end

  test "object key order does not distinguish retries", %{conn: conn} do
    submit(conn, [open_group()])

    first_json =
      ~s({"operations":[{"operation_id":"ordered-payment","type":"record_cash_payment","occurred_on":"2027-05-02","group_id":"later","amount_cents":1000}]})

    retry_json =
      ~s({"operations":[{"amount_cents":1000,"group_id":"later","occurred_on":"2027-05-02","type":"record_cash_payment","operation_id":"ordered-payment"}]})

    first = submit_json(conn, first_json)
    retry = submit_json(conn, retry_json)

    assert retry == first
    assert get_data(conn, "/api/v1/groups/later")["deposit_paid_cents"] == 1_000
  end

  test "an unknown operation identifier has the documented read error", %{conn: conn} do
    response =
      conn
      |> recycle()
      |> get("/api/v1/operations/not-recorded")
      |> json_response(404)

    assert response == %{"error" => %{"code" => "operation_not_found"}}
  end

  defp open_group do
    %{
      "operation_id" => "open-later",
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => "later",
      "guest_id" => "guest-1",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-03",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
    }
  end

  defp submit(conn, operations) do
    conn
    |> recycle()
    |> post("/api/v1/partner-batches", %{"operations" => operations})
    |> json_response(200)
    |> Map.fetch!("results")
  end

  defp submit_json(conn, body) do
    conn
    |> recycle()
    |> put_req_header("content-type", "application/json")
    |> post("/api/v1/partner-batches", body)
    |> json_response(200)
    |> Map.fetch!("results")
    |> List.first()
  end

  defp get_data(conn, path) do
    conn |> recycle() |> get(path) |> json_response(200) |> Map.fetch!("data")
  end
end
