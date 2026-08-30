# Milestone 4: allocation, reduction, and chargeback

This scenario requires the completed milestone-3 and milestone-4 workspaces.

1. Start milestone 3 against an empty SQLite database.
2. Issue hotel credit from a refundable source group. Open a flexible target group with three rooms,
   then submit a cash payment, a hotel-credit application, and a second cash payment. Their event
   dates do not match their submission and durable-record commit order. All operations receive
   durable records under milestone 3.
   Also open a two-room source group, fund it with one cash payment, and open a second target group
   for the same guest. These operations receive milestone-3 revisions and durable records.
3. Stop milestone 3 without deleting the database.
4. Run milestone 4 migrations and start milestone 4. Cash and credit must retain their funding
   types and be allocated to rooms in durable-record commit order, not event-date order.
5. Verify that the credit application cannot be targeted by `reduce_cash_payment`.
6. Cancel one room while refundable, refunding its cash and restoring its credit.
7. Reduce the second cash payment. The settled refund stays unchanged and the outstanding deposit
   reopens.
8. Settle one room from the additional source as a cash refund and the other as hotel credit. Spend
   part of that lot on the second target, then charge back the original source payment. Verify the
   refund and conversion are reclassified, the spent target is untouched, the shortfall is visible,
   and milestone-3 revisions survived migration.
9. Stop and restart milestone 4.
10. Retry the reduction, chargeback, and both original payments. Each returns its original stored
    result, and the affected groups and ledger remain byte-for-byte unchanged.

This combines historical allocation, retained funding classification, per-payment provenance,
settlement, reduction, chargeback clawback, revision migration, durable idempotency, and process
restart without inspecting candidate tables.
