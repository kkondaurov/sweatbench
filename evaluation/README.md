# Evaluation

The private suite calls the candidate's Phoenix endpoint through `Phoenix.ConnTest` and inspects
only public JSON behavior. It does not import candidate contexts or query candidate tables.

Each evaluation creates and migrates a fresh SQLite database. Ordinary private tests then use
`GroupStayWeb.ConnCase`, so Ecto's SQL sandbox rolls back scenario data after each test. The
candidate's source, schemas, and accumulated migrations are not reset.

`private_tests/` contains the deterministic rule examples. They intentionally use explicit
expected responses rather than a second implementation of the product logic.

Eleven system-level checks need milestone artifacts rather than SQL sandboxing. Six exercise the
Core regression floor:

- milestone 2 carries a database created by milestone 1 through the new migrations;
- milestone 3 repeats a stored operation after stopping and starting the application;
- milestone 4 carries milestone-3 operation records into room allocation and payment reduction,
  then restarts and retries both operations;
- milestone 5 upgrades existing allocations into cross-group transfer behavior;
- milestone 6 starts reporting over milestone-5 financial state and verifies restart-stable daily
  movements;
- milestone 7 closes milestone-6 reports and verifies late adjustments across restart.

Five additional Judgment checks carry deliberately selected historical data across the milestone
that first consumes it: policy history into milestone 2, room funding into milestone 4, payment
history into milestone 5, pre-reporting movements into milestone 6, and pre-close reporting history
into milestone 7. Four ordinary private scenarios cover cross-domain composition at milestones 6
and 7; the fifth composition family reuses the existing late-credit revival scenario on the
Judgment scale.

Those checks are described in `system_scenarios/` and implemented by `system_checks.py`. Judgment
family entitlement chains, scenarios, exclusions, and red-canary faults are fixed in `judgment/`
and hashed by `benchmark.json`.

`score_formatter.exs` records one machine-readable result for every private ExUnit scenario. The
evaluator combines those results with every applicable system check in a milestone JSON report.
The runner reports Core and Judgment family outcomes separately; it never adds them into one scalar.
