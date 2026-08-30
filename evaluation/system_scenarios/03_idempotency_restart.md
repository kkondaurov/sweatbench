# Milestone 3: process-restart idempotency

This scenario uses one completed milestone-3 workspace and one SQLite database.

1. Start the application, open a group, and submit a cash payment with operation identifier
   `restart-payment`.
2. Record the complete payment result and read the group and ledger.
3. Stop the application process and start it again against the same database.
4. Submit the identical payment operation.
5. The response must equal the original result, and the group and ledger must still contain only
   one payment's effect.
6. `GET /api/v1/operations/restart-payment` must return the original result.
