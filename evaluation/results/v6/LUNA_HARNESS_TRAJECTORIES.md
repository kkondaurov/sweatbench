# Luna harness trajectory deep dive

Snapshot: 30 August 2026

This note follows up on one narrow comparison in the v6 retrospective: five GPT-5.6 Luna xhigh
runs under OpenCode and five under Codex CLI with an explicit delegation instruction. The two
cohorts have similar aggregate scores but different counts in two families:

- hotel-credit lifecycle: OpenCode misses in 2/5 runs; delegated Codex misses in 4/5; and
- C3 transfer-shortfall composition: OpenCode misses in 0/5; delegated Codex misses in 2/5.

Those family labels are useful for scoring, but they are too coarse to explain the mechanism. This
review traced the exact assertions, candidate code, candidate tests, parent-agent updates, child
assignments, returned findings, and whether the parent incorporated them.

## Bottom line

The evidence does not support the simple interpretation that OpenCode's subagents reasoned better
about hotel credit and transfer shortfalls.

1. The hotel-credit difference collapses to one date-field convention. Every target miss stores
   `expires_on` as the first invalid day, cancellation date plus 366 days. Every pass stores it as
   the last valid day, plus 365. The ordering and restoration logic implicated by the family name
   is otherwise correct in these ten runs.
2. The two delegated Codex C3 misses are downstream reporting defects, not failures of the basic
   shortfall-absorption rule. One computes the day's opening credit liability as zero instead of
   700. The other crashes in report projection by reading atom keys from a persisted string-keyed
   map.
3. OpenCode does have one practical orchestration advantage in these trajectories: its child-task
   calls return a bounded result synchronously to the parent. Several Codex child sessions returned
   only interim status, inspected a concurrently changing worktree, or did not return before the
   parent finished. Therefore 17.8 spawned Codex children and 7.6 OpenCode children are not 17.8
   versus 7.6 completed, distinct, incorporated audits.
4. That orchestration difference is not a complete causal explanation. Two OpenCode runs use no
   stage-6 child at all and still pass C3. The strongest visible difference is in the parent work:
   OpenCode's stage-6 parents repeatedly model per-lot lifecycle events, opening snapshots, event
   ordering, and absorbed restoration directly, and add slightly broader report tests.

## Ten-run map

`+365` means the candidate exposes the last valid date in `expires_on`. `+366` means it exposes the
first invalid date. Stage-6 tests are new candidate test declarations added while implementing the
daily finance report.

| Cohort | Sample | Candidate subagents | `expires_on` | Hotel family | C3 composition | New stage-6 tests |
|---|---:|---:|---:|---|---|---:|
| OpenCode | 1 | 4 | +365 | pass | pass | 7 |
| OpenCode | 2 | 7 | +365 | pass | pass | 9 |
| OpenCode | 3 | 10 | +366 | miss | pass | 7 |
| OpenCode | 4 | 7 | +366 | miss | pass | 5 |
| OpenCode | 5 | 10 | +365 | pass | pass | 7 |
| Delegated Codex | 1 | 18 | +366 | miss | pass | 6 |
| Delegated Codex | 2 | 16 | +366 | miss | pass | 6 |
| Delegated Codex | 3 | 21 | +366 | miss | miss: opening projection | 4 |
| Delegated Codex | 4 | 16 | +366 | miss | pass | 5 |
| Delegated Codex | 5 | 18 | +365 | pass | miss: map-key crash | 4 |

The table rules out a delegation-dose explanation for either family. OpenCode sample 4 misses the
hotel family without a stage-2 child, but sample 3 misses it with two. OpenCode sample 2 passes it
without a stage-2 child. The date convention, not child count, predicts all ten hotel outcomes.

## Hotel credit: one convention, two failing assertions

The request says that hotel credit is available through the date 365 days after cancellation and
expires the following day. Two internal representations are plausible:

- `expires_on` is the last valid day: store `cancellation + 365`, and consider the lot unavailable
  after that date; or
- `expires_on` is the first invalid day: store `cancellation + 366`, and consider the lot
  unavailable on that date.

The evaluator and public API contract use the first representation. The six target-family misses
use the second. Their private failures are exact one-day differences in the returned field, such as
expected `2028-04-30` versus returned `2028-05-01`.

This matters because the two failing scenarios have names about consumption order and origin
restoration. In these ten trajectories, however, the candidate code orders lots by expiry and
source operation ID correctly. The assertion first fails because the remaining lot carries the
alternate `expires_on` value. The same convention causes both family members to miss.

The trajectory evidence also cuts against a review-quality explanation:

- several delegated Codex audits explicitly recommend the +366 interpretation, describing
  `expires_on` as the day after the last usable date;
- those parents incorporate the recommendation and write tests consistent with it;
- OpenCode samples 3 and 4 independently make the same choice and miss; and
- OpenCode samples 1, 2, and 5 choose +365 and pass, with no consistent relationship to child-task
  use.

The correct reading is therefore not "OpenCode solves hotel-credit ordering more reliably." It is
"this OpenCode cohort selected the evaluator's date-field representation three times, while the
delegated Codex cohort selected it once." The benchmark should make the field semantics explicit
in a successor version so this point measures business behavior rather than representation choice.

## C3: the family name hides the failure site

The C3 scenario composes five earlier capabilities:

1. issue a credit lot from converted cash;
2. apply part of the lot;
3. create a clawback shortfall against the original entitlement;
4. transfer credit to another group and later restore it; and
5. report the resulting absorbed amount and opening/closing liability.

Both delegated trajectories that miss C3 pass the dedicated shortfall tests at earlier milestones,
including restoration absorption and clawback accounting. Their final defects are different.

### Delegated sample 3

The implementation preserves the original credit-lot identifier through the transfer. On
restoration it absorbs the available amount into the lot's unrecovered clawback before exposing any
guest balance. The evaluator confirms the resulting business state: no available credit and the
expected residual liability and shortfall.

The miss occurs later in the daily report. The report shows an opening credit liability of zero
where the composed history requires 700. This trajectory also has other finance-projection misses,
which localizes C3 to its opening-state reconstruction rather than its transfer or absorption code.

The review process saw the relevant concepts but did not close the loop. An early audit listed the
opening-liability equation and shortfall absorption as required coverage. A design audit asked for
same-day restoration, expiry, chargeback, and absorption tests. The final audit nevertheless
reported no ship-blocking gap after a 36-test visible suite. No candidate test combines transferred
credit, original-lot shortfall, restoration, and the next report opening.

### Delegated sample 5

This implementation also carries the original lot identity through transfer. The C3 path fails
inside report projection when code accesses `event.delta_cents` on a map restored from persistence
with the string key `"delta_cents"`. The evaluator cannot complete the composed scenario because of
that integration/type boundary.

The parent catches and repairs a different expiry-projection defect during its own review. Its
last delegated reviewer does not return before the time limit, and the parent finishes using the
earlier findings and the passing visible suite. Again, the candidate tests cover transferred cash,
credit shortfall absorption, and finance reporting separately, but not the exact composition.

## What OpenCode does differently at stage 6

All five OpenCode implementations pass C3, including two with no stage-6 child task. Their parent
trajectories share several direct behaviors:

- they reject reconstruction from mutable current totals and choose a persisted event/posting
  ledger plus an inception snapshot;
- they reason explicitly about per-lot lifecycle state, operation order versus posting date,
  transferred provenance, and absorption before availability;
- they add 5-9 report tests at stage 6, averaging 7, versus 4-6 and an average of 5 for delegated
  Codex; and
- when they do call a child task, the result is returned in the same tool exchange and the parent
  either repairs the finding or asks the child to recheck the repair.

The OpenCode reviews are not uniformly superior. They miss other real defects, and samples 1 and 4
need no stage-6 child to pass C3. The stronger claim supported by the trajectories is narrower:
OpenCode's parent sessions spend more of their own visible trajectory constructing and testing the
report projection, while delegated Codex sometimes treats the child audit as the review pass even
when the child result is partial, stale, or falsely reassuring.

## Implications

- Count completed, result-bearing, incorporated audits separately from spawned child sessions.
- Report composite-scenario failure sites, not only family labels. A C3 miss can be a provenance
  defect, an absorption defect, an opening-projection defect, or a serialization crash.
- Do not infer delegation dose-response from child count. The independent question and the
  parent's repair are the intervention; the process count is only a cost indicator.
- Make boundary-field conventions explicit. Here, subagents sometimes increased confidence in a
  coherent but evaluator-incompatible interpretation.
- Add cross-feature candidate-test prompts or scoring diagnostics for the exact interfaces between
  already-correct components. Both delegated C3 misses live at those interfaces.

The trajectory evidence therefore changes the interpretation but not the score. OpenCode is 5/5
on this composed scenario and delegated Codex is 3/5. What it does not show is that OpenCode has a
general advantage in hotel-credit business rules or that more delegation would have fixed the two
Codex cases.
