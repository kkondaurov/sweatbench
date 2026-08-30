# Review guide

This is the human-readable view of the benchmark before any model is run.

## Business requirements

Read these as if they came from a product team:

1. `candidate/PRODUCT.md`
2. `candidate/API.md`
3. `candidate/requests/01-operational-core.md`
4. Continue through requests 02-07 in order.

Request 01 is the launch scope. Every later request changes the same running service. Earlier
behavior remains required unless a later request explicitly replaces it.

## What a model receives

At milestone 1, the model receives the generated application, the product, API, and runtime
documents, and request 01. At milestone 2 a fresh agent session inherits the milestone-1 repository
and receives request 02. The same handoff pattern continues through milestone 7. Tests written by
earlier engineers remain in the repository, but the incoming request has no ready-made executable
acceptance test. The current engineer decides what new automated coverage the change needs.

The task instruction is deliberately ordinary: implement the current request, run the available
tests, inspect the result, and keep working until the change is ready to ship. It does not tell the
model that it is being scored and it does not expose future requests. Milestone 4 adds a public
payment-reconciliation read before milestone 5 requires that contract to survive cross-group
deposit transfers. Milestones 6 and 7 then require those current-state decisions to support daily
finance reporting and immutable period close.

## What is judged

The private tests exercise the HTTP API and persisted state. They look for:

- correct outcomes at dates and policy boundaries;
- rejected operations leaving no partial mutation;
- optimistic revisions across same-batch writes, stale requests, and durable retries;
- earlier behavior surviving later changes;
- cash, deposit, and hotel-credit conservation;
- correct evolution of records created under an older release;
- durable idempotency under retries and process restarts;
- payment provenance across room settlement, reduction, chargeback clawbacks, upgrades, and retries;
- payment and credit provenance across same-guest deposit transfers;
- revision truthfulness when one operation changes more than one group;
- credit shortfall, restoration, expiry, and non-refundable consumption interacting without recycling
  revoked credit;
- effective-dated daily finance reports reconciling current state across cash and credit; and
- immutable period close with signed late adjustments that preserve published figures.

Each private scenario is an explicit request/response test. There is no second, opaque reference
implementation. The expected values are written directly into short ExUnit cases so they can be
audited against the product documents.

Version 6 reports two independent family scales. **Core /39** is the cumulative regression floor
for the product's explicit business requirements. **Judgment /10** consists of five historical-data
upgrade obligations and five cross-domain compositions whose answers are uniquely forced by those
same requirements but are not supplied as candidate-visible examples. Judgment definitions and
their hashes are fixed in `benchmark.json` before any candidate run.

Reports preserve the result of each scenario and each cross-process check. The milestone pass/fail
status is only a summary of that vector. Every scenario and system check is assigned to exactly one
family per scale in `benchmark.json`; the same scenario may support one Core and one Judgment family
when those scales describe different aspects of the failure. Headline comparisons report the two
scales separately; raw scenarios remain diagnostic. Comparisons also report prefix depth, Core
regression episodes, ship-time outcomes, and final-state outcomes rather than counting early work
repeatedly. Later milestones still run after an earlier failure and are identified as conditional
when that happens.

## State between tests and milestones

- Each evaluation starts with a newly created and migrated private-test database. Within that run,
  ordinary scenarios use SQL sandbox transactions to reset **data**, not source code or migration
  history.
- A milestone uses every migration accumulated up to that point.
- The candidate's implementation is carried forward; later milestones are maintenance work, not
  fresh attempts.
- Upgrade scenarios seed a database using the preceding milestone, migrate that database with the
  new milestone, and then verify the new behavior.
