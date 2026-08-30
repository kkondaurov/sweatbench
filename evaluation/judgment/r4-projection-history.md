# R4: projection-history upgrade

**Concept.** Reporting starts from the committed financial position, not a reconstructed event-date
history.

**Entitlement.** Request 6 says the state immediately before `start_finance_reporting` is the opening
position, including operations already committed whose `occurred_on` is on or after `starts_on`.
Earlier transfer, correction, shortfall, restoration, and expiry rules retain their meanings.

**Scenario.** Seed milestone 5 with held and transferred cash, every permanent cash disposition,
shortfalled credit, a fully pre-inception expired lot, a later-expiring lot, and future-dated committed
funding. Upgrade to milestone 6. Opening views must equal current state with zero movements; only the
later expiry appears as a dated movement. No lot expires exactly on the inception boundary.

**Canary.** Rebuild opening balances by filtering historical operations on `occurred_on`.
