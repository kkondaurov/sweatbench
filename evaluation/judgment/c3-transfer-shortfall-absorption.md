# C3: shortfall absorption through transfer

**Concept.** Restored transferred credit pays its lot's clawback before becoming available.

**Entitlement.** Request 4 requires restoration to extinguish unrecovered clawback before availability
or expiry. Request 5 preserves the original credit lot through transfer. Request 6 exposes shortfall
absorption as a credit movement.

**Scenario.** Create a shortfall against applied credit, transfer part across properties, and cancel
the destination while refundable. The restoration is absorbed, never becomes available, and the
ledger, source group, and report agree on the residual liability and shortfall.

**Canary.** Skip absorption when the returning allocation was transferred.
