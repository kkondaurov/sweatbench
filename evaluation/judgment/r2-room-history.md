# R2: room-accounting history upgrade

**Concept.** Room allocations are reconstructed from retained funding type and durable commit order.

**Entitlement.** Request 3 retains complete submitted content and durable commit order. Request 4
requires legacy funding first, then durable cash and credit in durable-record commit order regardless
of `occurred_on`, while preserving aggregate balances.

**Scenario.** Seed milestone 3 with three-room funding whose event dates disagree with commit order.
Upgrade to milestone 4, inspect the room split, then settle and reduce distinct allocations. Payment
statements, group totals, and the ledger must agree.

**Canary.** Reconstruct allocations by `occurred_on` instead of durable commit order.
