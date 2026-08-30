defmodule GroupStay.Private.ChargebackTest do
  use GroupStayWeb.ConnCase, async: false

  test "a chargeback composes with reductions and reopens held deposit", %{conn: conn} do
    payment = payment("held-pay", "held-group", 3_000, 1)

    [opened, paid, reduced, charged_back] =
      submit(conn, [
        open_group("held-open", "held-group", "held-guest", [10_000, 10_000]),
        payment,
        reduce("held-reduce", "held-pay", 1_000, 2),
        chargeback("held-chargeback", "held-pay", 3)
      ])

    assert opened["revision"] == 1
    assert paid["revision"] == 2
    assert reduced["revision"] == 3
    assert charged_back["charged_back_cents"] == 2_000
    assert charged_back["outstanding_deposit_cents"] == 4_000
    assert charged_back["revision"] == 4

    [again, wrong_type, missing] =
      submit(conn, [
        chargeback("held-chargeback-again", "held-pay", 4),
        chargeback("held-chargeback-open", "held-open", 4),
        chargeback("held-chargeback-missing", "not-recorded", 4)
      ])

    assert again["code"] == "payment_not_chargeable"
    assert wrong_type["code"] == "payment_not_chargeable"
    assert missing["code"] == "operation_not_found"
    assert get_data(conn, "/api/v1/groups/held-group")["revision"] == 4

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-04")
    assert Map.get(ledger, "cash_held_cents", 0) == 0
    assert ledger["cash_reduced_cents"] == 1_000
    assert ledger["cash_charged_back_cents"] == 2_000
  end

  test "refunded and converted portions are reclassified without replaying settlement", %{
    conn: conn
  } do
    [_, _, refunded, converted, charged_back] =
      submit(conn, [
        open_group("split-open", "split-group", "split-guest", [5_000, 5_000]),
        payment("split-pay", "split-group", 2_000, 1),
        cancel_rooms("split-refund", "split-group", ["room-1"], "cash", 2),
        cancel_rooms("split-convert", "split-group", ["room-2"], "hotel_credit", 3),
        chargeback("split-chargeback", "split-pay", 4)
      ])

    assert refunded["refunded_cents"] == 1_000
    assert converted["credit_issued_cents"] == 1_100
    assert charged_back["charged_back_cents"] == 2_000
    assert charged_back["outstanding_deposit_cents"] == 0
    assert charged_back["revision"] == 5

    ledger = get_data(conn, "/api/v1/ledger?on=2027-03-04")
    assert Map.get(ledger, "cash_refunded_cents", 0) == 0
    assert Map.get(ledger, "cash_converted_to_credit_cents", 0) == 0
    assert ledger["cash_charged_back_cents"] == 2_000
    assert ledger["credit_liability_cents"] == 0
    assert ledger["credit_shortfall_cents"] == 0

    assert get_data(conn, "/api/v1/guests/split-guest/credit?on=2027-03-04")["available_cents"] ==
             0
  end

  test "cumulative-difference attribution exposes only the spent entitlement as shortfall", %{
    conn: conn
  } do
    setup = setup_shortfall(conn, "cascade", "flexible")

    assert setup.chargeback["charged_back_cents"] == 405
    assert setup.chargeback["revision"] == 5

    source = get_data(conn, "/api/v1/groups/cascade-source")
    target = get_data(conn, "/api/v1/groups/cascade-target")
    assert source["revision"] == 5
    assert target["revision"] == 2
    assert target["credit_paid_cents"] == 600

    ledger = get_data(conn, "/api/v1/ledger?on=2027-02-04")
    assert ledger["cash_converted_to_credit_cents"] == 405
    assert ledger["cash_charged_back_cents"] == 405
    assert ledger["credit_liability_cents"] == 600
    assert ledger["credit_shortfall_cents"] == 154

    assert get_data(conn, "/api/v1/guests/cascade-guest/credit?on=2027-02-04")["available_cents"] ==
             0
  end

  test "restoration absorbs shortfall before an expired lot can return", %{conn: conn} do
    setup_split_shortfall(conn, "restore")

    [cancelled] =
      submit(conn, [
        cancel_group("restore-target-a-cancel", "restore-target-a", "2028-03-01", "cash", 2)
      ])

    assert cancelled["revision"] == 3

    assert get_data(conn, "/api/v1/guests/restore-guest/credit?on=2028-03-01")["available_cents"] ==
             0

    untouched = get_data(conn, "/api/v1/groups/restore-target-b")
    assert untouched["revision"] == 2
    assert untouched["credit_paid_cents"] == 300

    ledger = get_data(conn, "/api/v1/ledger?on=2028-03-01")
    assert ledger["credit_liability_cents"] == 300
    assert ledger["credit_shortfall_cents"] == 0
  end

  test "non-refundable consumption removes the active-credit shortfall cap", %{conn: conn} do
    setup_shortfall(conn, "consume", "advance_purchase")

    [cancelled] =
      submit(conn, [
        cancel_group("consume-target-cancel", "consume-target", "2027-02-10", "cash", 2)
      ])

    assert cancelled["revision"] == 3

    ledger = get_data(conn, "/api/v1/ledger?on=2027-02-10")
    assert ledger["credit_liability_cents"] == 0
    assert ledger["credit_shortfall_cents"] == 0
  end

  test "one partially reduced payment can be clawed from several lots without rewriting history",
       %{
         conn: conn
       } do
    original_payment = payment("multi-pay", "multi-source", 3_000, 1)
    chargeback = chargeback("multi-chargeback", "multi-pay", 5)

    [_, original_result, _, _, reduced, charged_back] =
      submit(conn, [
        open_group("multi-open", "multi-source", "multi-guest", [5_000, 5_000, 5_000]),
        original_payment,
        cancel_rooms("multi-credit-a", "multi-source", ["room-1"], "hotel_credit", 2),
        cancel_rooms("multi-credit-b", "multi-source", ["room-2"], "hotel_credit", 3),
        reduce("multi-reduce", "multi-pay", 400, 4),
        chargeback
      ])

    assert reduced["revision"] == 5
    assert charged_back["charged_back_cents"] == 2_600
    assert charged_back["outstanding_deposit_cents"] == 1_000
    assert charged_back["revision"] == 6
    assert submit_one(conn, original_payment) == original_result
    assert submit_one(conn, chargeback) == charged_back
    assert get_data(conn, "/api/v1/operations/multi-pay") == original_result

    ledger = get_data(conn, "/api/v1/ledger?on=2027-03-04")
    assert Map.get(ledger, "cash_held_cents", 0) == 0
    assert Map.get(ledger, "cash_converted_to_credit_cents", 0) == 0
    assert ledger["cash_reduced_cents"] == 400
    assert ledger["cash_charged_back_cents"] == 2_600
    assert ledger["credit_liability_cents"] == 0
    assert ledger["credit_shortfall_cents"] == 0
  end

  defp setup_shortfall(conn, prefix, target_rate_plan) do
    source_group = "#{prefix}-source"
    target_group = "#{prefix}-target"
    guest = "#{prefix}-guest"

    [_, first_payment, _, _, _, _, chargeback_result] =
      submit(conn, [
        open_group("#{prefix}-source-open", source_group, guest, [4_050],
          booked_on: "2027-01-01",
          arrival_on: "2027-06-01"
        ),
        payment("#{prefix}-pay-first", source_group, 405, 1),
        payment("#{prefix}-pay-second", source_group, 405, 2),
        cancel_group("#{prefix}-source-cancel", source_group, "2027-02-01", "hotel_credit", 3),
        open_group("#{prefix}-target-open", target_group, guest, [10_000],
          booked_on: "2027-02-02",
          arrival_on: "2028-06-01",
          rate_plan: target_rate_plan
        ),
        apply_credit("#{prefix}-apply", target_group, 600, 1),
        chargeback("#{prefix}-chargeback", "#{prefix}-pay-second", 4)
      ])

    %{payment: first_payment, chargeback: chargeback_result}
  end

  defp setup_split_shortfall(conn, prefix) do
    source_group = "#{prefix}-source"
    guest = "#{prefix}-guest"

    submit(conn, [
      open_group("#{prefix}-source-open", source_group, guest, [4_050],
        booked_on: "2027-01-01",
        arrival_on: "2027-06-01"
      ),
      payment("#{prefix}-pay-first", source_group, 405, 1),
      payment("#{prefix}-pay-second", source_group, 405, 2),
      cancel_group("#{prefix}-source-cancel", source_group, "2027-02-01", "hotel_credit", 3),
      open_group("#{prefix}-target-a-open", "#{prefix}-target-a", guest, [10_000],
        booked_on: "2027-02-02",
        arrival_on: "2028-06-01"
      ),
      open_group("#{prefix}-target-b-open", "#{prefix}-target-b", guest, [10_000],
        booked_on: "2027-02-02",
        arrival_on: "2028-06-01"
      ),
      apply_credit("#{prefix}-apply-a", "#{prefix}-target-a", 300, 1),
      apply_credit("#{prefix}-apply-b", "#{prefix}-target-b", 300, 1),
      chargeback("#{prefix}-chargeback", "#{prefix}-pay-second", 4)
    ])
  end

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
          %{"room_id" => "room-#{index}", "nightly_rate_cents" => rate}
        end)
    }
  end

  defp payment(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-01-02",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
    }
  end

  defp apply_credit(operation_id, group_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "apply_hotel_credit",
      "occurred_on" => "2027-02-03",
      "group_id" => group_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
    }
  end

  defp cancel_group(operation_id, group_id, occurred_on, refund_method, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => refund_method,
      "expected_revision" => expected_revision
    }
  end

  defp cancel_rooms(operation_id, group_id, room_ids, refund_method, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_rooms",
      "occurred_on" => "2027-03-01",
      "group_id" => group_id,
      "room_ids" => room_ids,
      "refund_method" => refund_method,
      "expected_revision" => expected_revision
    }
  end

  defp reduce(operation_id, payment_operation_id, amount_cents, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "reduce_cash_payment",
      "occurred_on" => "2027-05-03",
      "payment_operation_id" => payment_operation_id,
      "amount_cents" => amount_cents,
      "expected_revision" => expected_revision
    }
  end

  defp chargeback(operation_id, payment_operation_id, expected_revision) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => "2027-05-04",
      "payment_operation_id" => payment_operation_id,
      "expected_revision" => expected_revision
    }
  end

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
