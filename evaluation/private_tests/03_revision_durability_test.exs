defmodule GroupStay.Private.RevisionDurabilityTest do
  use GroupStayWeb.ConnCase, async: false

  test "a remembered stale rejection wins over a corrected revision under the same id", %{
    conn: conn
  } do
    submit_one(conn, open_group("stale-open", "stale-group"))

    stale = payment("stale-payment", "stale-group", 1_000, 9)
    first_rejection = submit_one(conn, stale)

    assert first_rejection["code"] == "stale_revision"
    assert first_rejection["actual_revision"] == 1

    applied = submit_one(conn, payment("other-payment", "stale-group", 1_000, 1))
    assert applied["revision"] == 2
    assert submit_one(conn, stale) == first_rejection

    conflict = submit_one(conn, Map.put(stale, "expected_revision", 2))
    assert conflict["code"] == "operation_id_conflict"
    assert get_data(conn, "/api/v1/operations/stale-payment") == first_rejection
    assert get_data(conn, "/api/v1/groups/stale-group")["revision"] == 2
  end

  test "an applied retry preserves its old revision after later changes", %{conn: conn} do
    submit_one(conn, open_group("echo-open", "echo-group"))
    payment = payment("echo-payment", "echo-group", 1_000, 1)
    original = submit_one(conn, payment)

    moved =
      submit_one(conn, %{
        "operation_id" => "echo-move",
        "type" => "reschedule_group",
        "occurred_on" => "2027-05-03",
        "group_id" => "echo-group",
        "new_arrival_on" => "2027-08-01",
        "expected_revision" => 2
      })

    assert original["revision"] == 2
    assert moved["revision"] == 3
    assert submit_one(conn, payment) == original
    assert get_data(conn, "/api/v1/operations/echo-payment") == original
    assert get_data(conn, "/api/v1/groups/echo-group")["revision"] == 3
  end

  defp open_group(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => "durable-revision-guest",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-07-01",
      "departure_on" => "2027-07-03",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => 10_000}]
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
