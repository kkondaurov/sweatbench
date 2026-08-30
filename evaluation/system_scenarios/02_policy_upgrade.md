# Milestone 2: existing-data upgrade

This scenario requires the completed milestone-1 and milestone-2 workspaces.

1. Start milestone 1 against an empty SQLite database.
2. Open and fund two flexible groups through the API:
   - one booked `2026-12-31`, arriving `2027-03-01`;
   - one booked `2027-01-01`, arriving `2027-03-01`.
3. Stop milestone 1 without deleting the database.
4. Run milestone 2 migrations against that database and start milestone 2.
5. Read both groups. The first must report `flex-14`; the second must report `flex-30`.
6. Cancel both on `2027-02-01`. The first is refundable under its 14-day policy. The second is
   28 days before arrival and retains its cash under its 30-day policy.

The point is not a particular table or column. The externally created milestone-1 records must
survive the schema evolution and acquire the policy implied by their booking dates.
