# Milestone 5 upgrade and restart scenario

1. Run the milestone-4 application against a fresh database.
2. Create two same-guest groups, fund both, and read the source payment statement.
3. Stop milestone 4 and migrate the same database with milestone 5.
4. Confirm the existing statement retains every milestone-4 value and its milestone-4 shape
   before any transfer occurs.
5. Transfer part of the source payment, confirm the held-by-group view appears, reduce it across the
   destination, and charge back the remainder across both groups.
6. Verify revisions, group funding, payment reconciliation, and ledger conservation.
7. Restart milestone 5, retry the transfer, reduction, chargeback, and original payment, and
   require their exact stored results with no state change.
