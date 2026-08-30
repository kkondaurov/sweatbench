# R3: payment-state history upgrade

**Concept.** Partially settled and corrected payment provenance survives the transfer release.

**Entitlement.** Request 4 defines immutable per-payment dispositions and reverse-fill correction.
Request 5 moves held provenance across groups and requires later reductions and chargebacks to follow
it while preserving the original result.

**Scenario.** Seed milestone 4 with multiple payments across properties, including a partial refund
and reduction. Upgrade to milestone 5, transfer the remaining provenance, then correct both payments.
Statements, revisions, rooms, and ledger classifications must reconcile across restart.

**Canary.** Collapse historical held cash to group totals and lose the originating payment identity.
