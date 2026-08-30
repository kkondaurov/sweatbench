# C4: reporting replay purity

**Concept.** Starting reporting cannot turn an old durable retry into a movement.

**Entitlement.** Request 3 requires an exact replay without reading or changing current state.
Request 6 derives movements from operations after inception and says durable retries never report a
movement twice.

**Scenario.** Commit a payment before reporting, start reporting from that position, then retry the
payment. Its result is byte-identical and every report and current view remains unchanged.

**Canary.** Emit a received movement when the pre-reporting payment is retried.
