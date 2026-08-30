# R5: close-era history upgrade

**Concept.** A new close feature freezes reports according to their durable pre-close posting history.

**Entitlement.** Request 6 fixes inception-floor posting and commit-defined opening state. Request 7
freezes reports through the cutoff byte-for-byte and moves only operations committed after a close to
the first open day.

**Scenario.** Seed milestone 6 with reports where commit order and event dates disagree. Capture the
reports, upgrade to milestone 7, close them, and require identical data. Then commit an old-dated
correction and verify one pinned first-open late adjustment across restart and retry.

**Canary.** Recompute pre-close posting dates using the newly introduced cutoff.
