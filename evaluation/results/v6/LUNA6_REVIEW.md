# GPT-6 Luna: three v6 trajectories

## Results

All three GPT-6 Luna xhigh runs completed the seven frozen Sweat Bench v6
milestones. Earlier product features were generally reliable; daily financial
reporting remained the main source of lost points.

| Public run | Core /39 | Maintenance /10 | Scenarios /94 | Agent time | API-equivalent cost |
|---|---:|---:|---:|---:|---:|
| 1 | 35 | 7 | 86 | 2h 09m | $0.59 |
| 2 | 38 | 8 | 92 | 1h 50m | $0.49 |
| 3 | 34 | 7 | 85 | 2h 04m | $0.58 |

All regular API scenarios through milestone 5 passed in all three runs. Runs 1
and 2 also passed every historical upgrade and restart check. Run 3 failed the
two milestone-4 room upgrades. Historical upgrade results remain in the final
score; passing a later version's fresh-database tests does not replace them.

| Milestone | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| 1 | 12/12 | 12/12 | 12/12 |
| 2 | 24/24 | 24/24 | 24/24 |
| 3 | 30/30 | 30/30 | 30/30 |
| 4 | 52/52 | 52/52 | 50/52 |
| 5 | 63/63 | 63/63 | 63/63 |
| 6 | 71/75 | 75/75 | 71/75 |
| 7 | 77/85 | 83/85 | 78/85 |

These milestone counts include cumulative API tests and that milestone's
historical checks. The final 94-scenario result also retains earlier historical
checks, so it is not the milestone-7 denominator.

## Why the Runs Differed

Runs 1 and 3 built cumulative reports rather than daily reports. Their readers
selected every posting up to the requested date and reused the opening position
from the start of reporting. Transactions from earlier days therefore appeared
again as current-day movements. This explains several failures together:

- Opening credit was zero where earlier issuance should have carried forward
  1,100 cents, or 700 cents in the transfer-and-shortfall case.
- A refund reversal returned zero instead of negative 1,000 cents because the
  original refund and its reversal were added together.
- A later report showed 700 cents of late receipts instead of the 300 cents
  posted that day: an earlier 400 cents was counted again.
- An ordinary receipt from before the close appeared in a later day's ordinary
  movements, where the expected value was zero.

The code preserves posting dates. The error is in how the report uses them.
See [run 1's report builder][r1-report] and [run 3's report builder][r3-report].
Run 3's [own period-close test][r3-test] explicitly expects an earlier receipt
and earlier late adjustments to appear again. Its test suite agrees with its
implementation but not with the daily-report contract.

Run 2 instead [walks dated credit events][r2-report], carries prior effects into
the opening balance, and accumulates movements only on the requested day. Its
[candidate-written test][r2-test] checks issuance, application, consumption and
expiry on different dates. This is a concrete difference in both implementation
and test coverage, consistent with its passing daily-report scenarios.

Run 2's remaining gap is credit used before expiry but recorded after the expiry
report has been closed. Closing the report must preserve its old numbers; the
next open report must then undo the expiry of the used amount. Its [application
event handler][r2-apply] subtracts available credit and increases applied credit
without reversing that reported expiry. One test consequently sees zero closing
liability instead of 300 cents; the other reaches the correct ordinary
consumption amount but lacks a negative 600-cent expiry adjustment. These two
tests account for one Core and two Maintenance points.

Run 1 also omits the negative expiry adjustment in the simpler case. Run 3
contains an [explicit reversal when posting after expiry][r3-revival] and passes
that case. Runs 1 and 3 stop the longer case at incorrect ordinary daily
movements, before its later correction assertions. Their failures do not identify
the same remaining defect as run 2's failure at a later assertion.

Run 3's room-upgrade failure is separate: its [migration][r3-migration] calls
`Map.new(converted_rows)` on SQL rows represented as two-element lists. Elixir
expects key-value tuples there. Both historical scenarios crash at that call,
before reaching their post-upgrade accounting assertions. They contribute two
lost family points but expose one shared migration bug.

## Comparison with GPT-5.6 Luna

| Cohort | Runs | Mean Core | Mean Maintenance | Full-score runs | Median cost | Mean agent time |
|---|---:|---:|---:|---:|---:|---:|
| GPT-6 Luna xhigh | 3 | 35.7 | 7.3 | 0 | $0.58 | 2h 01m |
| GPT-5.6 Luna xhigh | 5 | 32.6 | 6.2 | 0 | $1.50 | 2h 00m |

The five GPT-5.6 baselines had more varied early failures: cash-first room
allocation that lost payment order, structural rather than chronological date
comparison, and a cold-start request reader that treated valid fields as missing.
Three also used the first unavailable day in the expiry-date response field.
Those failures do not recur in the three GPT-6 results. Two GPT-6 runs pass both
room upgrades; the third fails for the distinct SQL-row conversion mistake above.

The daily-reporting weakness persists across generations. All five GPT-5.6 runs
failed the late-credit correction tests. GPT-6 run 3 passes the simpler case, but
none of its three runs passes the longer case. The strongest GPT-6 run is close
to complete; the other two still confuse earlier activity with today's activity.

The cohorts are small and were not run under identical tooling. GPT-6 used
Codex CLI 0.155.1 and candidate containers with two CPUs and 4096 MiB of memory;
the GPT-5.6 baseline used CLI 0.149.0-alpha.4.3 and native execution. Both used
the frozen v6 requirements, handoff protocol and candidate-written tests. GPT-6
had delegation disabled and no readability intervention. The comparison describes
these observed cohorts, not an isolated estimate of a model-version effect.

## Evaluation and Accounting Checks

All 21 accepted checkpoint hashes, evaluation-report hashes and candidate-test
inventories matched their recorded artifacts. Original final evaluations were
rerun on disposable copies of all three final snapshots, using the preceding
snapshot for upgrades. Every one of the 85 final-stage outcomes reproduced,
including both upgrade checks. Transient database-lock messages in the original
logs did not change those outcomes.

The numeric failures were checked against the daily-report and period-close
requests and the candidate implementations. No evaluator or candidate changes
were needed. Passing close-history checks establish preservation of the reports
those scenarios create; they do not establish that every possible report is
numerically correct. Likewise, the failed transfer-shortfall case in runs 1 and 3
reaches a wrong reporting opening balance after the preceding business operations
succeed. It is not evidence that the earlier absorption operation failed.

Cost uses the [official GPT-6 Luna API pricing][pricing], checked 23 September
2026: $0.10 per million uncached input tokens, $0.01 per million cached input
tokens, and $0.50 per million output tokens. Each milestone's cumulative session
usage was reconciled with its CLI completion event and counted once. Reasoning
is part of output, not an additional charge. No child sessions or cache writes
were recorded, and the largest request had 175,697 input tokens, below the
272,000-token long-context threshold. These are API-equivalent comparison costs,
not subscription invoices. Private evaluation and startup probes are excluded.

| Run | Total input | Cached input | Output, including reasoning | Exact API-equivalent cost |
|---|---:|---:|---:|---:|
| 1 | 30,458,203 | 29,315,584 | 365,825 | $0.59033024 |
| 2 | 24,675,087 | 23,735,552 | 325,890 | $0.49425402 |
| 3 | 30,328,656 | 29,275,136 | 354,930 | $0.57556836 |

Per-milestone usage and provenance are in [accepted-runs.json](accepted-runs.json).
The source archive contains all seven accepted snapshots per run. Raw sessions
and private evaluation logs are not published.

[pricing]: https://developers.openai.com/api/docs/pricing
[r1-report]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-01/milestone-7/lib/group_stay/reservations.ex#L234
[r2-report]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-02/milestone-7/lib/group_stay/groups.ex#L293
[r2-apply]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-02/milestone-7/lib/group_stay/groups.ex#L407
[r2-test]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-02/milestone-7/test/group_stay_web/controllers/daily_finance_report_test.exs#L220
[r3-report]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-03/milestone-7/lib/group_stay/groups.ex#L409
[r3-test]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-03/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L111
[r3-revival]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-03/milestone-7/lib/group_stay/groups.ex#L2080
[r3-migration]: https://github.com/kkondaurov/sweatbench-runs/tree/003583cf9a6f895786a43921a5ed9ff52ee85e2c/v6/luna6-xhigh-03/milestone-4/priv/repo/migrations/20260925000000_add_room_payment_accounting.exs#L403
