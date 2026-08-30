defmodule GroupStay.Private.HotelCreditTest do
  use GroupStayWeb.ConnCase, async: false

  test "credit consumes earliest expiry first and restored credit keeps its origin", %{conn: conn} do
    setup_operations =
      credit_source("a", "2027-04-01", "2027-06-01") ++
        credit_source("b", "2027-05-01", "2027-07-01") ++
        [
          open_group("open-target", "target", "2028-03-01", "2028-05-01", 30_000),
          %{
            "operation_id" => "apply-target",
            "type" => "apply_hotel_credit",
            "occurred_on" => "2028-03-31",
            "group_id" => "target",
            "amount_cents" => 5_000
          }
        ]

    submit(conn, setup_operations)

    credit_after_apply = get_data(conn, "/api/v1/guests/guest-1/credit?on=2028-03-31")

    assert credit_after_apply["available_cents"] == 3_800

    assert [
             %{
               "source_operation_id" => "cancel-b",
               "remaining_cents" => 3_800,
               "expires_on" => "2028-04-30"
             }
           ] = credit_after_apply["lots"]

    [cancelled] =
      submit(conn, [
        %{
          "operation_id" => "cancel-target",
          "type" => "cancel_group",
          "occurred_on" => "2028-03-31",
          "group_id" => "target"
        }
      ])

    assert cancelled["refunded_cents"] == 0
    assert cancelled["credit_issued_cents"] == 0

    restored = get_data(conn, "/api/v1/guests/guest-1/credit?on=2028-03-31")
    assert restored["available_cents"] == 8_800

    assert [
             %{
               "source_operation_id" => "cancel-a",
               "remaining_cents" => 4_400,
               "expires_on" => "2028-03-31"
             },
             %{
               "source_operation_id" => "cancel-b",
               "remaining_cents" => 4_400,
               "expires_on" => "2028-04-30"
             }
           ] = restored["lots"]

    ledger = get_data(conn, "/api/v1/ledger?on=2028-03-31")
    assert ledger["credit_liability_cents"] == 8_800
    assert ledger["cash_converted_to_credit_cents"] == 8_000
  end

  test "an expired lot cannot fund a group and no longer contributes to liability", %{conn: conn} do
    submit(conn, credit_source("expired", "2027-04-01", "2027-06-01"))
    submit(conn, [open_group("open-later", "later", "2028-03-01", "2028-05-01", 30_000)])

    [result] =
      submit(conn, [
        %{
          "operation_id" => "apply-expired",
          "type" => "apply_hotel_credit",
          "occurred_on" => "2028-04-01",
          "group_id" => "later",
          "amount_cents" => 1
        }
      ])

    assert result["status"] == "rejected"
    assert result["code"] == "insufficient_credit"
    assert get_data(conn, "/api/v1/guests/guest-1/credit?on=2028-04-01")["available_cents"] == 0
    assert get_data(conn, "/api/v1/ledger?on=2028-04-01")["credit_liability_cents"] == 0
  end

  test "the credit bonus rounds an exact half-cent upward", %{conn: conn} do
    operations = [
      open_group("open-half-cent", "half-cent", "2027-03-01", "2027-06-01", 10_013),
      %{
        "operation_id" => "pay-half-cent",
        "type" => "record_cash_payment",
        "occurred_on" => "2027-03-02",
        "group_id" => "half-cent",
        "amount_cents" => 4_005
      },
      %{
        "operation_id" => "cancel-half-cent",
        "type" => "cancel_group",
        "occurred_on" => "2027-04-01",
        "group_id" => "half-cent",
        "refund_method" => "hotel_credit"
      }
    ]

    [_opened, _paid, cancelled] = submit(conn, operations)
    assert cancelled["credit_issued_cents"] == 4_406
    assert get_data(conn, "/api/v1/ledger?on=2027-04-01")["credit_liability_cents"] == 4_406
  end

  test "equal-expiry lots are consumed by source operation identifier", %{conn: conn} do
    operations =
      credit_source("z", "2027-04-01", "2027-06-01") ++
        credit_source("a", "2027-04-01", "2027-07-01") ++
        [
          open_group("open-tied-target", "tied-target", "2027-03-01", "2027-08-01", 20_000),
          %{
            "operation_id" => "apply-tied-target",
            "type" => "apply_hotel_credit",
            "occurred_on" => "2027-04-02",
            "group_id" => "tied-target",
            "amount_cents" => 5_000
          }
        ]

    submit(conn, operations)
    credit = get_data(conn, "/api/v1/guests/guest-1/credit?on=2027-04-02")

    assert credit["available_cents"] == 3_800

    assert [
             %{
               "source_operation_id" => "cancel-z",
               "remaining_cents" => 3_800,
               "expires_on" => "2028-03-31"
             }
           ] = credit["lots"]
  end

  test "hotel credit cannot be selected for a non-refundable cancellation", %{conn: conn} do
    submit(conn, [
      open_group("open-late-credit", "late-credit", "2027-03-01", "2027-05-01", 10_000),
      %{
        "operation_id" => "pay-late-credit",
        "type" => "record_cash_payment",
        "occurred_on" => "2027-03-02",
        "group_id" => "late-credit",
        "amount_cents" => 4_000
      }
    ])

    [rejected] =
      submit(conn, [
        %{
          "operation_id" => "cancel-late-credit",
          "type" => "cancel_group",
          "occurred_on" => "2027-04-15",
          "group_id" => "late-credit",
          "refund_method" => "hotel_credit"
        }
      ])

    assert rejected["code"] == "refund_method_not_available"
    assert get_data(conn, "/api/v1/groups/late-credit")["status"] == "active"
    assert get_data(conn, "/api/v1/ledger?on=2027-04-15")["cash_held_cents"] == 4_000
  end

  defp credit_source(suffix, cancellation_on, arrival_on) do
    group_id = "source-#{suffix}"

    [
      open_group("open-#{suffix}", group_id, "2027-03-01", arrival_on, 10_000),
      %{
        "operation_id" => "pay-#{suffix}",
        "type" => "record_cash_payment",
        "occurred_on" => "2027-03-02",
        "group_id" => group_id,
        "amount_cents" => 4_000
      },
      %{
        "operation_id" => "cancel-#{suffix}",
        "type" => "cancel_group",
        "occurred_on" => cancellation_on,
        "group_id" => group_id,
        "refund_method" => "hotel_credit"
      }
    ]
  end

  defp open_group(operation_id, group_id, booked_on, arrival_on, nightly_rate_cents) do
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
      "rooms" => [%{"room_id" => "room-1", "nightly_rate_cents" => nightly_rate_cents}]
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
