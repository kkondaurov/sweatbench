# C5: revival followed by consumption

**Concept.** One lot can move from published expiry to revived liability and then to ordinary
non-refundable consumption without rewriting history or netting classifications away.

**Entitlement.** Request 2 pauses expiry while applied and consumes credit on non-refundable
settlement. Request 6 requires explicit expiry and consumption movements. Request 7 keeps the closed
expiry stable, posts the revival as a late adjustment, and leaves a first-open-day settlement as an
ordinary movement.

**Scenario.** Close a day containing an operation-free expiry, apply part of that credit using an old
event date, then consume the revived amount non-refundably on the first open day. Closed data stays
stable; late `expired_cents` is negative, ordinary `consumed_cents` is positive, and report, ledger,
credit, group, and stored operation views reconcile.

**Canary.** Net the revival and consumption to zero or post consumption back into the closed day.
