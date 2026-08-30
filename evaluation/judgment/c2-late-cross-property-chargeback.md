# C2: cross-property late chargeback

**Concept.** A late correction follows transferred cash to its settlement property.

**Entitlement.** Request 5 preserves payment provenance through transfer. Request 6 says a correction
follows cash to the property where it is held or settled. Request 7 requires old-dated post-close
effects to appear in signed late-adjustment classifications.

**Scenario.** Transfer a payment across properties, refund it there, close the refund day, then charge
it back with an old date. The closed day is stable and the first-open late reversal belongs only to the
destination property.

**Canary.** Attribute the correction to the payment's original property.
