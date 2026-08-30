defmodule GroupStay.Private.LedgerContractTest do
  use GroupStayWeb.ConnCase, async: false

  @cash_fields [
    "cash_held_cents",
    "cash_refunded_cents",
    "cash_retained_cents",
    "cash_converted_to_credit_cents",
    "cash_reduced_cents",
    "cash_charged_back_cents"
  ]

  test "a fresh ledger exposes every cumulative field at zero", %{conn: conn} do
    ledger = get_data(conn, "/api/v1/ledger?on=2027-01-01")

    for field <- @cash_fields ++ ["credit_liability_cents", "credit_shortfall_cents"] do
      assert Map.fetch!(ledger, field) == 0
    end

    assert recorded_cash(ledger) == 0
  end

  test "the ledger conserves recorded cash across every disposition", %{conn: conn} do
    Enum.each(
      ["held", "refunded", "retained", "converted", "reduced", "charged"],
      fn group_id ->
        submit(conn, [
          open_group("open-#{group_id}", group_id),
          payment("pay-#{group_id}", group_id)
        ])
      end
    )

    submit(conn, [
      cancel("cancel-refunded", "refunded", "2027-04-01", "cash"),
      cancel("cancel-retained", "retained", "2027-05-15", "cash"),
      cancel("cancel-converted", "converted", "2027-04-01", "hotel_credit"),
      %{
        "operation_id" => "reduce-payment",
        "type" => "reduce_cash_payment",
        "occurred_on" => "2027-04-02",
        "payment_operation_id" => "pay-reduced",
        "amount_cents" => 1_000
      },
      %{
        "operation_id" => "charge-payment",
        "type" => "charge_back_payment",
        "occurred_on" => "2027-04-02",
        "payment_operation_id" => "pay-charged"
      }
    ])

    ledger = get_data(conn, "/api/v1/ledger?on=2027-05-15")

    assert Map.take(ledger, @cash_fields) == %{
             "cash_held_cents" => 1_000,
             "cash_refunded_cents" => 1_000,
             "cash_retained_cents" => 1_000,
             "cash_converted_to_credit_cents" => 1_000,
             "cash_reduced_cents" => 1_000,
             "cash_charged_back_cents" => 1_000
           }

    assert ledger["credit_liability_cents"] == 1_100
    assert ledger["credit_shortfall_cents"] == 0
    assert recorded_cash(ledger) == 6_000
  end

  defp recorded_cash(ledger) do
    Enum.sum(Enum.map(@cash_fields, &Map.fetch!(ledger, &1)))
  end

  defp open_group(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-02-01",
      "group_id" => group_id,
      "guest_id" => "ledger-guest",
      "property_id" => "ams-canal",
      "arrival_on" => "2027-06-01",
      "departure_on" => "2027-06-02",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "#{group_id}-room", "nightly_rate_cents" => 5_000}]
    }
  end

  defp payment(operation_id, group_id) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => "2027-02-02",
      "group_id" => group_id,
      "amount_cents" => 1_000
    }
  end

  defp cancel(operation_id, group_id, occurred_on, method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => method
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
