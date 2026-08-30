defmodule GroupStay.Private.PeriodCloseTest do
  use GroupStayWeb.ConnCase, async: false

  @cash_fields ~w(received_cents transferred_in_cents transferred_out_cents refunded_cents retained_cents converted_to_credit_cents reduced_cents charged_back_cents)
  @credit_fields ~w(issued_cents expired_cents consumed_cents revoked_cents absorbed_cents)

  test "a closed report remains identical after a late cash movement", %{conn: conn} do
    submit(conn, [
      start_reporting("immutable-start", "2027-06-01"),
      open_group("immutable-open", "immutable-group", "immutable-guest", "ams-canal"),
      payment("immutable-first-pay", "immutable-group", 500, "2027-06-15"),
      close_period("immutable-close", "2027-06-30")
    ])

    published = report(conn, "2027-06-30")
    assert published["status"] == "closed"

    submit(conn, [payment("immutable-late-pay", "immutable-group", 400, "2027-06-20")])
    assert report(conn, "2027-06-30") == published
  end

  test "closing freezes credit expiry and classification figures through the cutoff", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("credit-close-start", "2027-06-01"),
      open_group("credit-close-open", "credit-close-group", "credit-close-guest", "ams-canal"),
      payment("credit-close-pay", "credit-close-group", 1_000, "2027-06-01"),
      cancel_group("credit-close-issue", "credit-close-group", "2027-06-01", "hotel_credit"),
      close_period("credit-close", "2028-06-01")
    ])

    published_issue = report(conn, "2027-06-01")
    published_expiry = report(conn, "2028-06-01")
    assert published_expiry["credit"]["movements"]["expired_cents"] == 1_100

    submit(conn, [
      open_group(
        "credit-close-late-open",
        "credit-close-late",
        "credit-close-guest",
        "rome-centro"
      ),
      payment("credit-close-late-pay", "credit-close-late", 500, "2027-06-01")
    ])

    assert report(conn, "2027-06-01") == published_issue
    assert report(conn, "2028-06-01") == published_expiry
  end

  test "an old-dated payment posts as a visible late adjustment on the first open day", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("late-pay-start", "2027-06-01"),
      open_group("late-pay-open", "late-pay-group", "late-pay-guest", "ams-canal"),
      close_period("late-pay-close", "2027-06-30"),
      payment("late-pay", "late-pay-group", 700, "2027-06-10")
    ])

    next_day = report(conn, "2027-07-01")
    assert cash(next_day, "ams-canal")["movements"] == zero_cash()
    assert late_cash(next_day, "ams-canal")["movements"]["received_cents"] == 700
    assert cash(next_day, "ams-canal")["opening_held_cents"] == 0
    assert cash(next_day, "ams-canal")["closing_held_cents"] == 700
  end

  test "a zero-net late reclassification retains both signed cash classifications", %{conn: conn} do
    submit(conn, [
      start_reporting("zero-start", "2027-06-01"),
      open_group("zero-open", "zero-group", "zero-guest", "ams-canal"),
      payment("zero-pay", "zero-group", 1_000, "2027-06-01"),
      cancel_group("zero-refund", "zero-group", "2027-06-02", "cash"),
      close_period("zero-close", "2027-06-30"),
      chargeback("zero-chargeback", "zero-pay", "2027-06-03")
    ])

    adjustment = late_cash(report(conn, "2027-07-01"), "ams-canal")["movements"]
    assert adjustment["refunded_cents"] == -1_000
    assert adjustment["charged_back_cents"] == 1_000
  end

  test "an adjustment keeps its first-open posting date across later closes", %{conn: conn} do
    submit(conn, [
      start_reporting("pin-start", "2027-06-01"),
      open_group("pin-open", "pin-group", "pin-guest", "ams-canal"),
      close_period("pin-close-one", "2027-06-30"),
      payment("pin-payment-one", "pin-group", 400, "2027-06-15"),
      close_period("pin-close-two", "2027-07-31"),
      payment("pin-payment-two", "pin-group", 300, "2027-06-15")
    ])

    july_first = report(conn, "2027-07-01")
    assert july_first["status"] == "closed"
    assert late_cash(july_first, "ams-canal")["movements"]["received_cents"] == 400

    august_first = report(conn, "2027-08-01")
    assert august_first["status"] == "open"
    assert late_cash(august_first, "ams-canal")["movements"]["received_cents"] == 300
  end

  test "close validation, durable replay, and conflict preserve the published cutoff", %{
    conn: conn
  } do
    [before_start] = submit(conn, [close_period("invalid-before-start", "2027-06-30")])
    assert before_start["code"] == "invalid_period"

    submit(conn, [start_reporting("contract-start", "2027-06-01")])
    close = close_period("contract-close", "2027-06-30")
    [applied] = submit(conn, [close])

    assert applied == %{
             "operation_id" => "contract-close",
             "status" => "applied",
             "period_end_on" => "2027-06-30"
           }

    assert submit(conn, [close]) == [applied]

    [same, earlier, conflict] =
      submit(conn, [
        close_period("contract-same", "2027-06-30"),
        close_period("contract-earlier", "2027-06-29"),
        Map.put(close, "period_end_on", "2027-07-31")
      ])

    assert same["code"] == "invalid_period"
    assert earlier["code"] == "invalid_period"
    assert conflict["code"] == "operation_id_conflict"
    assert report(conn, "2027-06-30")["status"] == "closed"
    assert report(conn, "2027-07-01")["status"] == "open"
  end

  test "same-batch close ordering separates an ordinary movement from a late one", %{conn: conn} do
    submit(conn, [
      start_reporting("order-start", "2027-06-01"),
      open_group("order-first-open", "order-first", "order-guest", "ams-canal"),
      open_group("order-second-open", "order-second", "order-guest", "ams-canal"),
      payment("order-before-close", "order-first", 500, "2027-06-15"),
      close_period("order-close", "2027-06-30"),
      payment("order-after-close", "order-second", 300, "2027-06-15")
    ])

    june = report(conn, "2027-06-15")
    assert cash(june, "ams-canal")["movements"]["received_cents"] == 500
    assert june["late_adjustments"]["cash"] == []

    july = report(conn, "2027-07-01")
    assert cash(july, "ams-canal")["movements"]["received_cents"] == 0
    assert late_cash(july, "ams-canal")["movements"]["received_cents"] == 300
  end

  test "a late application restores liability without rewriting a closed credit expiry", %{
    conn: conn
  } do
    submit(conn, [
      start_reporting("revival-start", "2027-06-01"),
      open_group("revival-source-open", "revival-source", "revival-guest", "ams-canal"),
      open_group(
        "revival-destination-open",
        "revival-destination",
        "revival-guest",
        "rome-centro"
      ),
      payment("revival-pay", "revival-source", 1_000, "2027-06-01"),
      cancel_group("revival-issue", "revival-source", "2027-06-02", "hotel_credit"),
      close_period("revival-close", "2028-06-30")
    ])

    published = report(conn, "2028-06-30")
    assert published["status"] == "closed"
    assert published["credit"]["closing_liability_cents"] == 0

    [application] =
      submit(conn, [
        %{
          "operation_id" => "revival-apply",
          "type" => "apply_hotel_credit",
          "occurred_on" => "2027-06-03",
          "group_id" => "revival-destination",
          "amount_cents" => 300
        }
      ])

    assert application["status"] == "applied"
    assert report(conn, "2028-06-30") == published

    first_open = report(conn, "2028-07-01")
    assert first_open["credit"]["opening_liability_cents"] == 0
    assert first_open["credit"]["closing_liability_cents"] == 300

    assert first_open["late_adjustments"]["credit"] ==
             Map.put(zero_credit(), "expired_cents", -300)

    ledger =
      conn
      |> recycle()
      |> get("/api/v1/ledger?on=2028-07-01")
      |> json_response(200)
      |> Map.fetch!("data")

    assert ledger["credit_liability_cents"] == 300
  end

  defp cash(report, property_id) do
    Enum.find(report["cash"], &(&1["property_id"] == property_id))
  end

  defp late_cash(report, property_id) do
    Enum.find(report["late_adjustments"]["cash"], &(&1["property_id"] == property_id))
  end

  defp zero_cash, do: Map.new(@cash_fields, &{&1, 0})
  defp zero_credit, do: Map.new(@credit_fields, &{&1, 0})

  defp report(conn, date) do
    conn
    |> recycle()
    |> get("/api/v1/finance/daily-report?date=#{date}")
    |> json_response(200)
    |> Map.fetch!("data")
  end

  defp start_reporting(operation_id, starts_on) do
    %{
      "operation_id" => operation_id,
      "type" => "start_finance_reporting",
      "occurred_on" => starts_on,
      "starts_on" => starts_on
    }
  end

  defp close_period(operation_id, period_end_on) do
    %{
      "operation_id" => operation_id,
      "type" => "close_finance_period",
      "occurred_on" => period_end_on,
      "period_end_on" => period_end_on
    }
  end

  defp open_group(operation_id, group_id, guest_id, property_id) do
    %{
      "operation_id" => operation_id,
      "type" => "open_group",
      "occurred_on" => "2027-05-01",
      "group_id" => group_id,
      "guest_id" => guest_id,
      "property_id" => property_id,
      "arrival_on" => "2027-10-01",
      "departure_on" => "2027-10-02",
      "rate_plan" => "flexible",
      "rooms" => [%{"room_id" => "#{group_id}-room", "nightly_rate_cents" => 10_000}]
    }
  end

  defp payment(operation_id, group_id, amount, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "record_cash_payment",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "amount_cents" => amount
    }
  end

  defp cancel_group(operation_id, group_id, occurred_on, refund_method) do
    %{
      "operation_id" => operation_id,
      "type" => "cancel_group",
      "occurred_on" => occurred_on,
      "group_id" => group_id,
      "refund_method" => refund_method
    }
  end

  defp chargeback(operation_id, payment_operation_id, occurred_on) do
    %{
      "operation_id" => operation_id,
      "type" => "charge_back_payment",
      "occurred_on" => occurred_on,
      "payment_operation_id" => payment_operation_id
    }
  end

  defp submit(conn, operations) do
    conn
    |> recycle()
    |> post("/api/v1/partner-batches", %{"operations" => operations})
    |> json_response(200)
    |> Map.fetch!("results")
  end
end
