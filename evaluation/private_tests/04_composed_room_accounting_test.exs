defmodule GroupStay.Private.ComposedRoomAccountingTest do
  use GroupStayWeb.ConnCase, async: false

  test "partial cancellation reallocates around cancelled rooms and can exhaust a group", %{
    conn: conn
  } do
    submit(conn, [
      open_group("p1-open", "p1", "p1-guest", "2027-02-01", "2027-06-01", "flexible", [
        {"room-a", 10_000},
        {"room-b", 20_000},
        {"room-c", 10_000}
      ]),
      payment("p1-pay-1", "p1", "2027-02-02", 3_000)
    ])

    [first] = submit(conn, [cancel_rooms("p1-cancel-b", "p1", "2027-03-01", ["room-b"])])
    assert first["refunded_cents"] == 1_000

    group = get_data(conn, "/api/v1/groups/p1")
    assert group["deposit_due_cents"] == 4_000
    assert group["outstanding_deposit_cents"] == 2_000

    submit(conn, [payment("p1-pay-2", "p1", "2027-03-02", 2_000)])
    rooms = get_data(conn, "/api/v1/groups/p1")["rooms"] |> Map.new(&{&1["room_id"], &1})
    assert rooms["room-a"]["cash_paid_cents"] == 2_000
    assert rooms["room-c"]["cash_paid_cents"] == 2_000

    [last] =
      submit(conn, [cancel_rooms("p1-cancel-rest", "p1", "2027-03-03", ["room-c", "room-a"])])

    assert last["cancelled_room_ids"] == ["room-a", "room-c"]
    assert last["refunded_cents"] == 4_000
    assert get_data(conn, "/api/v1/groups/p1")["status"] == "cancelled"

    [late_payment, late_cancel] =
      submit(conn, [
        payment("p1-pay-late", "p1", "2027-03-04", 1),
        cancel_group("p1-cancel-late", "p1", "2027-03-04")
      ])

    assert late_payment["code"] == "group_not_active"
    assert late_cancel["code"] == "group_not_active"

    ledger = get_data(conn, "/api/v1/ledger?on=2027-03-04")
    assert ledger["cash_refunded_cents"] == 5_000
    assert_cash_conservation(ledger, 5_000)
  end

  test "partial settlements combine bonus rounding and preserve advance-purchase rules", %{
    conn: conn
  } do
    submit(conn, [
      open_group(
        "p3-open-bonus",
        "p3-bonus",
        "p3-guest",
        "2027-02-01",
        "2027-06-01",
        "flexible",
        [
          {"room-a", 2_025},
          {"room-b", 2_025},
          {"room-c", 10_000}
        ]
      ),
      payment("p3-pay-bonus", "p3-bonus", "2027-02-02", 810)
    ])

    [bonus] =
      submit(conn, [
        cancel_rooms(
          "p3-cancel-bonus",
          "p3-bonus",
          "2027-03-01",
          ["room-a", "room-b"],
          "hotel_credit"
        )
      ])

    assert bonus["credit_issued_cents"] == 891

    submit(conn, [
      open_group(
        "p3-open-advance",
        "p3-advance",
        "p3-advance-guest",
        "2027-02-01",
        "2027-06-01",
        "advance_purchase",
        [{"room-d", 3_000}, {"room-e", 5_000}]
      ),
      payment("p3-pay-advance", "p3-advance", "2027-02-02", 4_000)
    ])

    advance = get_data(conn, "/api/v1/groups/p3-advance")
    assert advance["policy_version"] == "advance-nonrefundable"
    assert advance["refundable_until"] == nil

    [cancelled_d] =
      submit(conn, [cancel_rooms("p3-cancel-d", "p3-advance", "2027-03-01", ["room-d"])])

    assert cancelled_d["retained_cents"] == 3_000

    [rejected_e] =
      submit(conn, [
        cancel_rooms(
          "p3-cancel-e-credit",
          "p3-advance",
          "2027-03-02",
          ["room-e"],
          "hotel_credit"
        )
      ])

    assert rejected_e["code"] == "refund_method_not_available"
    [cancelled_e] = submit(conn, [cancel_group("p3-cancel-e", "p3-advance", "2027-03-03")])
    assert cancelled_e["retained_cents"] == 1_000

    ledger = get_data(conn, "/api/v1/ledger?on=2027-03-03")
    assert ledger["cash_converted_to_credit_cents"] == 810
    assert ledger["cash_retained_cents"] == 4_000
    assert ledger["credit_liability_cents"] == 891
    assert_cash_conservation(ledger, 4_810)
  end

  test "applied credit survives lot expiry but expires when restored", %{conn: conn} do
    submit(conn, [
      open_group(
        "p4-open-source",
        "p4-source",
        "p4-guest",
        "2027-01-10",
        "2027-06-01",
        "flexible",
        [{"room-source", 20_000}]
      ),
      payment("p4-pay-source", "p4-source", "2027-01-11", 4_000),
      cancel_group("p4-cancel-source", "p4-source", "2027-02-01", "hotel_credit"),
      open_group(
        "p4-open-other",
        "p4-other",
        "other-guest",
        "2027-02-10",
        "2028-05-01",
        "flexible",
        [{"room-other", 10_000}]
      ),
      apply_credit("p4-other-apply", "p4-other", "2027-02-15", 1_000),
      open_group(
        "p4-open-target",
        "p4-target",
        "p4-guest",
        "2027-02-10",
        "2028-05-01",
        "flexible",
        [{"room-a", 10_000}, {"room-b", 10_000}]
      ),
      apply_credit("p4-apply", "p4-target", "2027-02-15", 3_000),
      payment("p4-pay-target", "p4-target", "2027-02-16", 1_000)
    ])

    assert get_data(conn, "/api/v1/operations/p4-other-apply")["code"] == "insufficient_credit"
    assert_credit(conn, "p4-guest", "2028-01-31", 1_400, 4_400)
    assert_credit(conn, "p4-guest", "2028-02-05", 0, 3_000)

    [room_cancelled] =
      submit(conn, [cancel_rooms("p4-cancel-a", "p4-target", "2028-02-15", ["room-a"])])

    assert room_cancelled["refunded_cents"] == 0
    assert_credit(conn, "p4-guest", "2028-02-15", 0, 1_000)

    [group_cancelled] =
      submit(conn, [cancel_group("p4-cancel-target", "p4-target", "2028-02-20")])

    assert group_cancelled["refunded_cents"] == 1_000
    assert_credit(conn, "p4-guest", "2028-02-20", 0, 0)

    ledger = get_data(conn, "/api/v1/ledger?on=2028-02-20")
    assert ledger["cash_converted_to_credit_cents"] == 4_000
    assert ledger["cash_refunded_cents"] == 1_000
    assert_cash_conservation(ledger, 5_000)
  end

  defp open_group(operation_id, group_id, guest_id, booked_on, arrival_on, rate_plan, rooms) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => booked_on,
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => "ams-canal",
      "arrival_on" => arrival_on,
      "departure_on" => Date.add(Date.from_iso8601!(arrival_on), 1) |> Date.to_iso8601(),
      "rate_plan" => rate_plan,
      "rooms" =>
        Enum.map(rooms, fn {room_id, rate} ->
          %{"room_id" => room_id, "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, occurred_on, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp apply_credit(operation_id, group_id, occurred_on, amount) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp cancel_group(operation_id, group_id, occurred_on, method \\ nil) do
    cancellation(operation_id, "cancel_group", group_id, occurred_on, method)
  end

  defp cancel_rooms(operation_id, group_id, occurred_on, room_ids, method \\ nil) do
    cancellation(operation_id, "cancel_rooms", group_id, occurred_on, method)
    |> Map.put("room_ids", room_ids)
  end

  defp cancellation(operation_id, type, group_id, occurred_on, method) do
    operation = %{
      "operation_id" => operation_id,
      "type" => type,
      "occurred_on" => occurred_on,
      "group_id" => group_id
    }

    if method, do: Map.put(operation, "refund_method", method), else: operation
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

  defp assert_credit(conn, guest_id, on, available, liability) do
    assert get_data(conn, "/api/v1/guests/#{guest_id}/credit?on=#{on}")["available_cents"] ==
             available

    assert get_data(conn, "/api/v1/ledger?on=#{on}")["credit_liability_cents"] == liability
  end

  defp assert_cash_conservation(ledger, submitted) do
    assert submitted ==
             Map.get(ledger, "cash_held_cents", 0) +
               Map.get(ledger, "cash_refunded_cents", 0) +
               Map.get(ledger, "cash_retained_cents", 0) +
               Map.get(ledger, "cash_converted_to_credit_cents", 0) +
               Map.get(ledger, "cash_reduced_cents", 0)
  end
end
