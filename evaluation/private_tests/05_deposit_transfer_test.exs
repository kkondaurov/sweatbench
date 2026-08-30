defmodule GroupStay.Private.DepositTransferTest do
  use GroupStayWeb.ConnCase, async: false

  test "transfers draw held funding in reverse allocation order and fill destination rooms in order",
       %{conn: conn} do
    submit(conn, [
      open_group("mix-credit-open", "mix-credit", "mix-guest", [10_000]),
      payment("mix-credit-pay", "mix-credit", 2_000, nil),
      cancel_group("mix-credit-cancel", "mix-credit", "2027-02-01", "hotel_credit", nil),
      open_group("mix-source-open", "mix-source", "mix-guest", [5_000, 5_000, 5_000, 5_000]),
      open_group("mix-destination-open", "mix-destination", "mix-guest", [5_000, 5_000, 5_000]),
      payment("mix-pay-first", "mix-source", 1_500, nil),
      apply_credit("mix-apply", "mix-source", 1_000, nil),
      payment("mix-pay-second", "mix-source", 500, nil)
    ])

    [moved] =
      submit(conn, [
        transfer("mix-transfer", "mix-source", "mix-destination", 1_800, nil, nil)
      ])

    assert moved["source_outstanding_deposit_cents"] == 2_800
    assert moved["destination_outstanding_deposit_cents"] == 1_200
    source = rooms_by_id(get_data(conn, "/api/v1/groups/mix-source"))
    assert source["mix-source-room-1"]["cash_paid_cents"] == 1_000
    assert source["mix-source-room-2"]["cash_paid_cents"] == 200
    assert source["mix-source-room-2"]["credit_paid_cents"] == 0
    assert source["mix-source-room-3"]["cash_paid_cents"] == 0
    assert source["mix-source-room-3"]["credit_paid_cents"] == 0

    destination = rooms_by_id(get_data(conn, "/api/v1/groups/mix-destination"))
    assert destination["mix-destination-room-1"]["cash_paid_cents"] == 500
    assert destination["mix-destination-room-1"]["credit_paid_cents"] == 500
    assert destination["mix-destination-room-2"]["cash_paid_cents"] == 300
    assert destination["mix-destination-room-2"]["credit_paid_cents"] == 500

    assert get_data(conn, "/api/v1/payments/mix-pay-first")["held_by_group"] == [
             %{"group_id" => "mix-destination", "amount_cents" => 300},
             %{"group_id" => "mix-source", "amount_cents" => 1_200}
           ]

    assert get_data(conn, "/api/v1/payments/mix-pay-second")["held_by_group"] == [
             %{"group_id" => "mix-destination", "amount_cents" => 500}
           ]
  end

  test "transfer validation distinguishes identity, amount, funding, capacity, and group errors",
       %{conn: conn} do
    submit(conn, [
      open_group("errors-source-open", "errors-source", "errors-guest", [5_000]),
      open_group("errors-destination-open", "errors-destination", "errors-guest", [2_500]),
      open_group("errors-large-open", "errors-large", "errors-guest", [10_000]),
      open_group("errors-other-open", "errors-other", "other-guest", [5_000]),
      open_group("errors-inactive-open", "errors-inactive", "errors-guest", [5_000]),
      payment("errors-source-pay", "errors-source", 1_000, nil),
      cancel_group("errors-inactive-cancel", "errors-inactive", "2027-04-01", "cash", nil)
    ])

    cases = [
      {transfer("same", "errors-source", "errors-source", 1, nil, nil), "invalid_transfer"},
      {transfer("guest", "errors-source", "errors-other", 1, nil, nil), "invalid_transfer"},
      {transfer("inactive", "errors-source", "errors-inactive", 1, nil, nil), "group_not_active"},
      {transfer("zero", "errors-source", "errors-large", 0, nil, nil), "invalid_amount"},
      {transfer("negative", "errors-source", "errors-large", -1, nil, nil), "invalid_amount"},
      {transfer("funding", "errors-source", "errors-large", 1_001, nil, nil),
       "transfer_exceeds_held_funding"},
      {transfer("capacity", "errors-source", "errors-destination", 501, nil, nil),
       "transfer_exceeds_outstanding"},
      {transfer("missing-source", "missing", "errors-large", 1, nil, nil), "group_not_found"},
      {transfer("missing-destination", "errors-source", "missing", 1, nil, nil),
       "group_not_found"}
    ]

    Enum.each(cases, fn {operation, code} ->
      [result] = submit(conn, [operation])
      assert result["status"] == "rejected"
      assert result["code"] == code

      if operation["operation_id"] == "inactive" do
        assert result["group_id"] == "errors-inactive"
      end
    end)

    assert get_data(conn, "/api/v1/groups/errors-source")["cash_paid_cents"] == 1_000
  end

  test "a transfer guards both groups and advances both revisions exactly once", %{conn: conn} do
    submit(conn, [
      open_group("occ-source-open", "occ-source", "occ-guest", [10_000]),
      open_group("occ-destination-open", "occ-destination", "occ-guest", [10_000]),
      payment("occ-pay", "occ-source", 1_000, 1)
    ])

    [stale_source] =
      submit(conn, [transfer("occ-stale-source", "occ-source", "occ-destination", 100, 1, 1)])

    assert stale_source["code"] == "stale_revision"
    assert stale_source["group_id"] == "occ-source"
    assert stale_source["actual_revision"] == 2

    [stale_destination] =
      submit(conn, [transfer("occ-stale-destination", "occ-source", "occ-destination", 100, 2, 2)])

    assert stale_destination["code"] == "stale_revision"
    assert stale_destination["group_id"] == "occ-destination"
    assert stale_destination["actual_revision"] == 1

    operation = transfer("occ-transfer", "occ-source", "occ-destination", 500, 2, 1)
    [applied] = submit(conn, [operation])
    assert applied["source_revision"] == 3
    assert applied["destination_revision"] == 2
    assert submit_one(conn, operation) == applied

    [second] =
      submit(conn, [transfer("occ-transfer-two", "occ-source", "occ-destination", 500, 3, 2)])

    assert second["source_revision"] == 4
    assert second["destination_revision"] == 3
  end

  test "corrections bump every group whose funding they change while guarding the origin", %{
    conn: conn
  } do
    submit(conn, [
      open_group("bump-source-open", "bump-source", "bump-guest", [10_000, 10_000]),
      open_group("bump-destination-open", "bump-destination", "bump-guest", [10_000, 10_000]),
      payment("bump-pay", "bump-source", 2_000, 1),
      transfer("bump-transfer", "bump-source", "bump-destination", 1_500, 2, 1)
    ])

    [reduced] = submit(conn, [reduction("bump-reduce", "bump-pay", 1_000, 3)])
    assert reduced["revision"] == 4
    assert get_data(conn, "/api/v1/groups/bump-destination")["revision"] == 3

    [charged] = submit(conn, [chargeback("bump-charge", "bump-pay", 4)])
    assert charged["revision"] == 5
    assert get_data(conn, "/api/v1/groups/bump-destination")["revision"] == 4

    [stale] = submit(conn, [chargeback("bump-stale", "bump-pay", 4)])
    assert stale["code"] == "stale_revision"
    assert stale["group_id"] == "bump-source"
    assert stale["actual_revision"] == 5
  end

  test "a reduction follows one payment across groups in reverse allocation order", %{conn: conn} do
    submit(conn, [
      open_group("reduce-source-open", "reduce-source", "reduce-guest", [5_000, 5_000, 5_000]),
      open_group("reduce-destination-open", "reduce-destination", "reduce-guest", [5_000, 5_000]),
      payment("reduce-pay", "reduce-source", 2_000, nil),
      transfer("reduce-transfer", "reduce-source", "reduce-destination", 1_500, nil, nil)
    ])

    [first] = submit(conn, [reduction("reduce-first", "reduce-pay", 1_000, nil)])
    assert first["outstanding_deposit_cents"] == 2_500

    assert get_data(conn, "/api/v1/payments/reduce-pay")["held_by_group"] == [
             %{"group_id" => "reduce-destination", "amount_cents" => 500},
             %{"group_id" => "reduce-source", "amount_cents" => 500}
           ]

    [second] = submit(conn, [reduction("reduce-second", "reduce-pay", 700, nil)])
    assert second["outstanding_deposit_cents"] == 2_700

    assert get_data(conn, "/api/v1/payments/reduce-pay")["held_by_group"] == [
             %{"group_id" => "reduce-source", "amount_cents" => 300}
           ]

    assert get_data(conn, "/api/v1/groups/reduce-destination")["cash_paid_cents"] == 0
  end

  test "a chargeback reclassifies one payment across groups without touching other funding", %{
    conn: conn
  } do
    submit(conn, [
      open_group("charge-source-open", "charge-source", "charge-guest", [
        5_000,
        5_000,
        5_000,
        5_000
      ]),
      open_group("charge-destination-open", "charge-destination", "charge-guest", [
        5_000,
        5_000,
        5_000
      ]),
      payment("charge-unrelated", "charge-destination", 1_000, nil),
      payment("charge-target", "charge-source", 2_000, nil),
      transfer("charge-transfer", "charge-source", "charge-destination", 1_500, nil, nil)
    ])

    [charged] = submit(conn, [chargeback("charge-back", "charge-target", nil)])
    assert charged["charged_back_cents"] == 2_000

    source = get_data(conn, "/api/v1/groups/charge-source")
    destination = get_data(conn, "/api/v1/groups/charge-destination")
    assert source["cash_paid_cents"] == 0
    assert destination["cash_paid_cents"] == 1_000

    assert get_data(conn, "/api/v1/payments/charge-unrelated")["held_cents"] == 1_000
    assert get_data(conn, "/api/v1/payments/charge-target")["charged_back_cents"] == 2_000

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-04")
    assert ledger["cash_held_cents"] == 1_000
    assert ledger["cash_charged_back_cents"] == 2_000
  end

  test "destination policy settles transferred cash and computes its credit bonus", %{conn: conn} do
    submit(conn, [
      open_group("settle-source-open", "settle-source", "settle-guest", [5_000, 5_000]),
      open_group("settle-flex-open", "settle-flex", "settle-guest", [5_000]),
      open_group("settle-advance-open", "settle-advance", "settle-guest", [5_000],
        rate_plan: "advance_purchase"
      ),
      payment("settle-pay", "settle-source", 2_000, nil),
      transfer("settle-flex-transfer", "settle-source", "settle-flex", 1_000, nil, nil),
      transfer("settle-advance-transfer", "settle-source", "settle-advance", 1_000, nil, nil),
      cancel_group("settle-flex-cancel", "settle-flex", "2027-04-01", "hotel_credit", nil),
      cancel_group("settle-advance-cancel", "settle-advance", "2027-04-01", "cash", nil)
    ])

    statement = get_data(conn, "/api/v1/payments/settle-pay")
    assert statement["held_cents"] == 0
    assert statement["converted_to_credit_cents"] == 1_000
    assert statement["retained_cents"] == 1_000

    credit = get_data(conn, "/api/v1/guests/settle-guest/credit?on=2027-04-01")
    assert credit["available_cents"] == 1_100

    ledger = get_data(conn, "/api/v1/ledger?on=2027-04-01")
    assert ledger["cash_converted_to_credit_cents"] == 1_000
    assert ledger["cash_retained_cents"] == 1_000
  end

  test "transferred credit restores to its original lot and respects expiry", %{conn: conn} do
    setup_credit_transfer(conn, "restore-live", "2027-03-01")

    live = get_data(conn, "/api/v1/guests/restore-live-guest/credit?on=2027-03-01")
    assert live["available_cents"] == 1_100
    assert Enum.map(live["lots"], & &1["source_operation_id"]) == ["restore-live-credit-cancel"]

    setup_credit_transfer(conn, "restore-expired", "2028-02-02")

    expired = get_data(conn, "/api/v1/guests/restore-expired-guest/credit?on=2028-02-02")
    assert expired["available_cents"] == 0
    assert expired["lots"] == []
  end

  test "a payment statement reports held cash by group after transfer and settlement", %{
    conn: conn
  } do
    submit(conn, [
      open_group("view-source-open", "view-source", "view-guest", [5_000, 5_000]),
      open_group("view-destination-open", "view-destination", "view-guest", [5_000, 5_000]),
      payment("view-pay", "view-source", 2_000, nil),
      transfer("view-transfer", "view-source", "view-destination", 1_500, nil, nil),
      cancel_rooms(
        "view-refund",
        "view-destination",
        ["view-destination-room-1"],
        "2027-04-01",
        "cash",
        nil
      )
    ])

    statement = get_data(conn, "/api/v1/payments/view-pay")
    assert statement["recorded_cents"] == 2_000
    assert statement["held_cents"] == 1_000
    assert statement["refunded_cents"] == 1_000

    assert statement["held_by_group"] == [
             %{"group_id" => "view-destination", "amount_cents" => 500},
             %{"group_id" => "view-source", "amount_cents" => 500}
           ]
  end

  test "batched and sequential transfer histories have identical outcomes and final reads", %{
    conn: conn
  } do
    batched_operations = transfer_history("batched")
    batched_results = submit(conn, batched_operations)
    batched_source = get_data(conn, "/api/v1/groups/batched-source")
    batched_destination = get_data(conn, "/api/v1/groups/batched-destination")
    batched_statement = get_data(conn, "/api/v1/payments/batched-pay")
    first_ledger = get_data(conn, "/api/v1/ledger?on=2027-05-04")

    sequential_results = Enum.map(transfer_history("sequential"), &submit_one(conn, &1))
    sequential_source = get_data(conn, "/api/v1/groups/sequential-source")
    sequential_destination = get_data(conn, "/api/v1/groups/sequential-destination")
    sequential_statement = get_data(conn, "/api/v1/payments/sequential-pay")
    second_ledger = get_data(conn, "/api/v1/ledger?on=2027-05-04")

    assert normalize(batched_results, "batched") == normalize(sequential_results, "sequential")
    assert normalize(batched_source, "batched") == normalize(sequential_source, "sequential")

    assert normalize(batched_destination, "batched") ==
             normalize(sequential_destination, "sequential")

    assert normalize(batched_statement, "batched") ==
             normalize(sequential_statement, "sequential")

    for {field, value} <- first_ledger, is_integer(value) do
      assert second_ledger[field] == value * 2
    end
  end

  test "a transfer leaves ledger totals and an unrelated group unchanged", %{conn: conn} do
    submit(conn, [
      open_group("isolation-source-open", "isolation-source", "isolation-guest", [10_000]),
      open_group("isolation-destination-open", "isolation-destination", "isolation-guest", [
        10_000
      ]),
      open_group("isolation-third-open", "isolation-third", "isolation-guest", [10_000]),
      payment("isolation-source-pay", "isolation-source", 1_000, nil),
      payment("isolation-third-pay", "isolation-third", 500, nil)
    ])

    ledger_before = get_data(conn, "/api/v1/ledger?on=2027-05-03")
    third_before = get_data(conn, "/api/v1/groups/isolation-third")

    submit(conn, [
      transfer("isolation-transfer", "isolation-source", "isolation-destination", 750, nil, nil)
    ])

    assert get_data(conn, "/api/v1/ledger?on=2027-05-03") == ledger_before
    assert get_data(conn, "/api/v1/groups/isolation-third") == third_before
  end

  defp setup_credit_transfer(conn, prefix, cancellation_on) do
    guest = "#{prefix}-guest"

    submit(conn, [
      open_group("#{prefix}-credit-open", "#{prefix}-credit", guest, [5_000]),
      payment("#{prefix}-credit-pay", "#{prefix}-credit", 1_000, nil),
      cancel_group(
        "#{prefix}-credit-cancel",
        "#{prefix}-credit",
        "2027-02-01",
        "hotel_credit",
        nil
      ),
      open_group("#{prefix}-source-open", "#{prefix}-source", guest, [5_000],
        arrival_on: "2029-06-01"
      ),
      open_group("#{prefix}-destination-open", "#{prefix}-destination", guest, [5_000],
        arrival_on: "2029-06-01"
      ),
      apply_credit("#{prefix}-apply", "#{prefix}-source", 1_000, nil),
      transfer(
        "#{prefix}-transfer",
        "#{prefix}-source",
        "#{prefix}-destination",
        1_000,
        nil,
        nil
      ),
      cancel_group(
        "#{prefix}-destination-cancel",
        "#{prefix}-destination",
        cancellation_on,
        "cash",
        nil
      )
    ])
  end

  defp transfer_history(prefix) do
    [
      open_group("#{prefix}-source-open", "#{prefix}-source", "#{prefix}-guest", [5_000, 5_000]),
      open_group("#{prefix}-destination-open", "#{prefix}-destination", "#{prefix}-guest", [
        5_000,
        5_000
      ]),
      payment("#{prefix}-pay", "#{prefix}-source", 2_000, nil),
      transfer(
        "#{prefix}-transfer",
        "#{prefix}-source",
        "#{prefix}-destination",
        1_500,
        nil,
        nil
      ),
      reduction("#{prefix}-reduce", "#{prefix}-pay", 500, nil)
    ]
  end

  defp normalize(value, prefix) do
    value
    |> Jason.encode!()
    |> String.replace(prefix, "history")
    |> Jason.decode!()
  end

  defp rooms_by_id(group), do: Map.new(group["rooms"], &{&1["room_id"], &1})

  defp open_group(operation_id, group_id, guest_id, room_rates, options \\ []) do
    booked_on = Keyword.get(options, :booked_on, "2027-01-01")
    arrival_on = Keyword.get(options, :arrival_on, "2027-10-01")
    rate_plan = Keyword.get(options, :rate_plan, "flexible")

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
        room_rates
        |> Enum.with_index(1)
        |> Enum.map(fn {rate, index} ->
          %{"room_id" => "#{group_id}-room-#{index}", "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, amount, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-01-02",
      "group_id" => group_id,
      "amount_cents" => amount
    }
    |> maybe_put("expected_revision", revision)
  end

  defp apply_credit(operation_id, group_id, amount, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => "2027-02-02",
      "group_id" => group_id,
      "amount_cents" => amount
    }
    |> maybe_put("expected_revision", revision)
  end

  defp transfer(operation_id, source, destination, amount, source_revision, destination_revision) do
    operation = %{
      "operation_id" => operation_id,
      "type" => "transfer_deposit",
      "occurred_on" => "2027-05-03",
      "source_group_id" => source,
      "destination_group_id" => destination,
      "amount_cents" => amount
    }

    operation
    |> maybe_put("expected_revision", source_revision)
    |> maybe_put("destination_expected_revision", destination_revision)
  end

  defp reduction(operation_id, payment_operation_id, amount, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "reduce_cash_payment",
      "occurred_on" => "2027-05-04",
      "payment_operation_id" => payment_operation_id,
      "amount_cents" => amount
    }
    |> maybe_put("expected_revision", revision)
  end

  defp chargeback(operation_id, payment_operation_id, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => "2027-05-04",
      "payment_operation_id" => payment_operation_id
    }
    |> maybe_put("expected_revision", revision)
  end

  defp cancel_group(operation_id, group_id, occurred_on, method, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => method
    }
    |> maybe_put("expected_revision", revision)
  end

  defp cancel_rooms(operation_id, group_id, room_ids, occurred_on, method, revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_rooms",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "room_ids" => room_ids,
      "refund_method" => method
    }
    |> maybe_put("expected_revision", revision)
  end

  defp maybe_put(map, _key, nil), do: map
  defp maybe_put(map, key, value), do: Map.put(map, key, value)

  defp submit_one(conn, operation), do: submit(conn, [operation]) |> List.first()

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
