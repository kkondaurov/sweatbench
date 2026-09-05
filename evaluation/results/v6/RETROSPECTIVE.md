# Sweat Bench v6 Retrospective

Snapshot: 30 August 2026; updated 5 September 2026

This analysis covers the earlier 67-run Models population. Six additional Astra runs are now
published in the [dashboard](index.html) and [dataset](accepted-runs.json), bringing Models to
73 runs and the full dataset to 98. See the [current Astra results](ASTRA_TRAJECTORIES.md#current-results)
for the twelve-run effort comparison and interrupted-attempt accounting. Historical statistics
and source-level claims below retain their original population.

Public release: `v6.0.0`

Source benchmark-content commit: `5fda9a09255529b027cadf836c0c16c867a039e5`

## Scope

This report studies the accepted Sweat Bench v6 evidence available in the repository:

- 67 completed trajectories in the main model comparison;
- 20 accepted OpenAI-model trajectories under OpenCode; and
- 5 accepted GPT-5.6 Luna trajectories under Codex CLI with an explicit delegation instruction.

That gives 92 complete trajectories across 22 model, harness, effort, and prompt configurations.
The main leaderboard contains 17 configurations. Most have five samples; Claude Opus 5 has two,
both GLM-5.3 Flash configurations have four, Meta Muse Spark 1.3 has one, and GPT-6 Astra has two
at each of low, medium, and high reasoning effort.

Invalidated, abandoned, interrupted, and infrastructure-debug attempts are intentionally outside
the analysis. They are exclusions, not model outcomes. This is not an infrastructure postmortem.

The quantitative companion is `accepted-runs.json`. Each published run is reconstructed from its
saved state, checked across all seven milestones and the final private evaluation, and joined with
full-session cost, runtime, LOC, source structure, candidate tests, and candidate-launched
subagents. Machine-local paths are removed and each trajectory receives a stable group/sample
identifier. `analyze.py` independently validates the released population and recomputes every
group headline from those run records.

## Executive verdict

Sweat Bench v6 worked. It separates current agent systems, exposes meaningful reliability and
economic differences, and catches failures that large candidate test suites routinely miss. It is
also reaching the end of its useful life as a frontier discriminator.

The right description is not simply "saturated." It is **lopsided**:

1. Eighteen of the 49 scored families never fail in any of the 67 main trajectories.
2. A small hard core accounts for much of the remaining separation.
3. Three period-close families fail in 48 or 49 of 67 runs, although all six Astra observations pass them.
4. Several nominally separate points are statistically the same underlying behavior.
5. The final request is much harder than earlier requests and has no later milestone in which a
   model can repair it.

The benchmark therefore still distinguishes systems, but a growing fraction of its headline
score no longer contributes information, while an unusually large fraction of the remaining
information comes from one temporal-accounting cluster.

The strongest substantive lessons are:

- GPT-5.6 Sol high is the best demonstrated all-around system in v6: 38.8/39 Core, 9.6/10
  Maintenance, and four complete sweeps in five runs.
- GPT-5.6 Sol medium remains the best-replicated high-quality economic compromise: 38.2/39, 8.8/10, and a
  $13.90 median API-equivalent cost.
- GPT-6 Astra low, medium, and high average 39/9, 38/7, and 38.5/8.5 over two runs each, at
  median costs of $12.36, $14.95, and $18.45. Low and high sweep on their second samples; medium
  repeats its migration-decoding and cold-replay defects. All six solve revival/composition.
  Low improves the observed cost-quality frontier, but two samples cannot establish reliability
  or an effort ranking. Astra uses a newer Codex CLI than the earlier GPT cohort, so this compares
  tested systems, not isolated model weights.
- Claude Opus 5 high is provisionally in the same quality region as Sol high, but only two runs
  exist and its $47.65 median cost is much higher. Its uncertainty is too large for a reliability
  ranking.
- Meta Muse Spark 1.3 high completes one valid trajectory at 29/39 Core and 3/10 Maintenance. It
  recovers from an unfinished finance-report release, but remains below every other configuration
  mean while taking 9.45 model-hours and $53.61 of recorded inference. One run is diagnostic, not a
  reliability estimate.
- The tested GPT-5.5 xhigh configuration is dominated by GPT-5.6 Sol medium in both quality and
  efficiency. GPT-5.5 averages 37.0/39 and 7.6/10 at $27.57; Sol medium averages 38.2 and 8.8 at
  roughly half the median cost. Because tier, effort, and cohort differ, this is not an isolated
  estimate of the generational effect.
- Grok 4.6 is strong and unusually consistent, but four of its five runs converge on the same
  38/39, 8/10 plateau and the same period-close blind spot.
- GLM 5.3 demonstrates capability without reliability: it is the only non-frontier model arm with
  a sweep, but spans 33-39 Core and 6-10 Maintenance.
- Increasing GLM-5.3 Flash from high to max does not help: the sample gets slower and more
  expensive while mean Core falls from 34.75 to 34.0.
- Two compound system changes move Luna's operating point dramatically. Standard Luna averages
  32.6/39 and 6.2/10 at $1.50. OpenCode Luna averages 36.6 and 7.6 at $2.55. Codex Luna with an
  explicit delegation prompt averages 37.0 and 8.0 at $4.23. These interventions change prompt,
  context allocation, child-session count, and inference budget together; they do not isolate a
  single audit mechanism.
- Child-session count is not monotonically beneficial. OpenCode makes Sol and Terra launch many
  more child sessions without a corresponding general quality gain, and Sol high's observed
  decline is dominated by one run's operational boot defect rather than a broad semantic
  regression. The benefit depends on the model and on whether the delegated work attacks a real
  weakness.
- More code, more tests, and more wall-clock time are not reliable proxies for quality. Opus writes
  roughly six thousand test lines; Qwen writes nearly eight thousand. Both still miss compact
  hidden invariants that a much smaller test suite can cover when it asks the right question.
- OpenCode is not cheaper on an API-equivalent full-session basis after descendant sessions are
  included. Its actual marginal subscription charge was zero in the OAuth experiment, but the
  recorded inference would cost 5% more for both Sol variants, 15% more for Terra, and about 70%
   more for Luna at list prices.

The successor should freeze v6 as a calibration and regression suite, not keep extending Group
Stay indefinitely. A new benchmark should retain at least one long cumulative hidden-future track
and real persistence upgrades, distribute additional difficulty across independent domains and
engineering axes, measure position and repair opportunity explicitly, reduce score dependence,
and report model-plus-harness systems as first-class experimental conditions.

## Confidence levels

- **High confidence:** published population, score and failure counts, group summaries, LOC,
  runtime, descendant-session cost reconstruction, cache volume, and the existence of repeated
  failure signatures. These are regenerated from 92 complete trajectories and reconcile across
  run, family, and scenario grains.
- **High confidence:** the dominant period-close revival failure mechanism. A
  first-failing-assertion census of the original 47 failures shows that 46 preserve the closed
  report but fail to append the required compensating history; Muse adds a distinct transaction
  deadlock on the same scenario.
- **Moderate confidence:** the interpretation of hotel-credit and migration failures. It is
  supported by failing private scenarios, co-failure patterns, and targeted inspection of passing
  and failing implementations and candidate tests, but is not a complete mechanism census of all
  relevant trajectories.
- **Moderate confidence:** economic-frontier and model-selection conclusions. They accurately
  describe the tested samples and pricing snapshot but can move with more samples or new prices.
- **Low to moderate confidence:** exact sweep probabilities, Claude Opus reliability, and causal
  harness effects. The samples are small, Opus has only two runs, and harness cohorts are
  independent rather than paired.

## What v6 actually measures

### Product shape

The candidate starts from a small Phoenix JSON API and receives seven cumulative product requests:

1. Group setup, deposit pricing, revisions, payments, cancellations, and partner batches.
2. Policy versioning, hotel credit issuance, expiry, consumption, and restoration.
3. Durable exactly-once operations and restart behavior.
4. Room-level accounting, payment reductions, chargebacks, statements, and provenance.
5. Cross-group deposit transfers and corrections.
6. Daily finance reporting, effective dating, reporting inception, and deterministic projection.
7. Period close, immutable historical reports, and late adjustments.

This is not seven independent coding tasks. Each request changes the interpretation of state
created by earlier requests. Later releases require migrations, historical reconstruction,
idempotency, and compatibility with earlier API behavior.

### Agent protocol

Each milestone starts a fresh model session. The model receives the repository as left by the
previous milestone, along with the accumulated product, API, and runbook documents and any tests
the candidate wrote. The ordinary prompt asks it to inspect the repository, implement the current
request completely, preserve all earlier behavior, run the full test suite, repair failures, then
review the full implementation and diff. It explicitly tells the model to fix anything it would
not ship and rerun the relevant tests before ending the turn. The private evaluator runs only after
that review-and-repair opportunity has ended. The protocol requests one explicit final
review-and-repair pass; it does not place the model in a repeated review loop or return evaluator
findings for another attempt.

This protocol measures a particular kind of engineering agent:

- it must onboard into an evolving codebase repeatedly;
- it must use code, documentation, migrations, and tests as durable handoff memory;
- it gets no private-evaluator feedback; and
- later repairs are endogenous consequences of later implementation work, not direct benchmark
  hints.

It does **not** measure one uninterrupted, very-long-context conversation. The fresh-session
boundary is part of the task.

### Evaluation boundary

The private evaluator talks to the product through its public JSON API and through explicit
persistent-database upgrade checks. It does not import candidate tables to derive expected values.
The private suite is run only after the candidate turn exits. Candidate logs are audited against
private evaluator paths and benchmark internals.

The benchmark separately reports:

- **Core /39**: whether the requested product behavior works;
- **Maintenance /10**: whether historical upgrades and cross-feature interactions remain correct;
- **ship-time scenarios**: behavior immediately after each milestone;
- **final-state scenarios**: the last private-test results combined with the recorded outcomes
  of historical system checks, which are executed at their designated upgrade milestones;
- **sweeps**: 39/39 Core and 10/10 Maintenance in the final state; and
- **cost, runtime, LOC, and subagents** as descriptive operating characteristics.

The separation between Core and Maintenance is useful. A model can implement most visible
features while mishandling old production data, or it can preserve history while missing a new
feature. Collapsing them into one score would hide that distinction.

### What makes the benchmark hard

The hard part is not Phoenix syntax or endpoint count. The recurring challenge is maintaining
several notions of time and identity simultaneously:

- operation date versus commit order;
- source operation identity versus current holder;
- current state versus immutable historical projection;
- effective date versus first-open posting date;
- retry identity versus request payload;
- original funding provenance versus later conversion; and
- business correction versus reversal of already published history.

This is why models can generate large applications and extensive tests yet still fail one compact
hidden scenario. The difficult question is usually not "did you build a report endpoint?" It is
"does a later event append the correct compensating history without retroactively changing a
closed report?"

## Main results

Cost is the median full accepted run under the basis shown by the dashboard: recorded OpenRouter
spend for paid external-model rows, and API-equivalent estimates for OpenAI, Opus, and Flash.
Runtime is mean candidate-session wall time; it excludes evaluator and inactive inter-milestone
time.

| Configuration | n | Core mean (range) | Maint. mean (range) | Sweeps | Median cost | Mean hours |
|---|---:|---:|---:|---:|---:|---:|
| GPT-6 Astra low / Codex | 2 | 39.0 (39-39) | 9.0 (8-10) | 1 | ~$12.36 | 0.72 |
| GPT-6 Astra medium / Codex | 2 | 38.0 (38-38) | 7.0 (7-7) | 0 | ~$14.95 | 0.93 |
| GPT-6 Astra high / Codex | 2 | 38.5 (38-39) | 8.5 (7-10) | 1 | ~$18.45 | 1.30 |
| GPT-5.6 Sol high / Codex | 5 | 38.8 (38-39) | 9.6 (8-10) | 4 | ~$22.37 | 1.50 |
| GPT-5.6 Sol medium / Codex | 5 | 38.2 (37-39) | 8.8 (6-10) | 2 | ~$13.90 | 1.28 |
| GPT-5.6 Terra xhigh / Codex | 5 | 36.6 (36-37) | 7.0 (6-8) | 0 | ~$9.96 | 1.52 |
| GPT-5.6 Luna xhigh / Codex | 5 | 32.6 (27-37) | 6.2 (2-8) | 0 | ~$1.50 | 1.99 |
| GPT-5.5 xhigh / Codex | 5 | 37.0 (36-38) | 7.6 (7-9) | 0 | ~$27.57 | 1.67 |
| Claude Opus 5 high / Claude Code | 2 | 38.5 (38-39) | 9.5 (9-10) | 1 | ~$47.65 | 2.06 |
| Meta Muse Spark 1.3 high / OpenCode | 1 | 29.0 | 3.0 | 0 | $53.61 | 9.45 |
| Grok 4.6 xhigh / OpenCode | 5 | 37.6 (36-38) | 7.8 (7-8) | 0 | $14.71 | 2.05 |
| Qwen3.8 Max xhigh / OpenCode | 5 | 35.8 (31-38) | 7.6 (6-10) | 0 | $25.34 | 4.22 |
| DeepSeek V4 Pro max / OpenCode | 5 | 35.0 (34-37) | 6.4 (6-7) | 0 | $8.87 | 4.38 |
| Kimi K3 max / OpenCode | 5 | 36.2 (35-38) | 6.8 (6-8) | 0 | $29.23 | 4.67 |
| GLM 5.3 high / OpenCode | 5 | 35.4 (33-39) | 7.6 (6-10) | 1 | $20.96 | 5.39 |
| GLM-5.3 Flash high / OpenCode | 4 | 34.75 (33-36) | 6.5 (5-8) | 0 | ~$2.08 | 4.16 |
| GLM-5.3 Flash max / OpenCode | 4 | 34.0 (31-36) | 6.75 (6-8) | 0 | ~$2.96 | 6.06 |

### Reliability is not settled by five runs

Five samples are enough to reveal large differences and recurring failure signatures, but not to
estimate sweep probabilities precisely. Wilson 95% intervals make this visible:

- Sol high, 4/5 sweeps: 37.6%-96.4%;
- Sol medium, 2/5: 11.8%-76.9%;
- any 0/5 arm: 0%-43.4%;
- GLM 5.3, 1/5: 3.6%-62.4%; and
- Opus 5, 1/2: 9.5%-90.5%.

The point estimates are still useful. Sol high is clearly more reliable in this sample than a
system that repeatedly produces the same 38/8 result. But claims such as "the true sweep rate is
80%" would be false precision.

Muse has one completed run; each Astra effort has two. These identify concrete mechanisms and
operating costs, but cannot establish stable means, variance estimates, or sweep probabilities.

### Model-specific reading

#### GPT-6 Astra low, medium, and high

Astra's six observations are fast and compact: 42-79 model-minutes, 1,979-2,242 production
lines, and $11.64-$19.42 in standard API-equivalent inference. Low averages 39/9, medium 38/7,
and high 38.5/8.5. Low and high each sweep on their second sample; medium repeats 38/7. All six
clear the late-credit-revival cluster and all five cross-domain Maintenance checks.

The repeated M4 failure is a legacy room decoder that expects maps where the preceding Ecto
writer stored JSON strings. Both medium samples and high 01 hand-insert an imagined format
in their migration fixtures, and both real upgrades crash. High 02 initially writes the same
decoder, but preserves typed insertion in an inherited test. That test exposes the crash; the
agent adds an inner decode before handoff, and both real upgrades pass. Low uses typed loading
in both runs; low 02 additionally freezes migration-local schemas instead of relying on evolving
application code.

The cold-replay failure also changes across samples. All first-round runs restore saved JSON
keys with `String.to_existing_atom` while new finance fields are defined in a separate module.
A first-request retry after restart bypasses that module and can fail. Medium 02 repeats this
arrangement; its subprocess coverage never grows beyond the M3 result kinds. Low 02 instead
returns JSON-shaped results directly from M3 onward, removing the atom dependency. High 02
still converts keys, but defines the finance result literals in the same module as replay, making
them available on a cold start. It passes the current contract without making the decoder
independent of future module layout.

The score improvement is therefore neither newly solving revival nor simply adding more tests.
High 02 succeeds with 108 declared tests versus high 01's 111; medium 02 has 82 versus 73 and
does not improve. Preserving one useful inherited fixture explains the observed migration repair.
The six runs remain independent samples with no feedback from earlier runs.

An earlier Sol-high/OpenCode trajectory exhibits the same cold-replay defect; Sol-medium/Codex's
R4/R5 failures instead arise from structural date comparison. Shared labels are insufficient to
identify a shared mechanism. Nor do Astra's four non-sweeps establish broad headroom: their
fourteen missing family-points repeat two compact boundary defects, while all six solve the
previously dominant accounting problem. The [Astra trajectory analysis](ASTRA_TRAJECTORIES.md)
covers the source, tests, runtime evidence, costs, and implications for the successor.

#### GPT-5.6 Sol high

Sol high produces four exact sweeps. Its only non-sweep is 38/39 Core and 8/10 Maintenance, missing
the period-close revival cluster. Its variance is low: Core standard deviation 0.4, Maintenance
standard deviation 0.8. It also reaches these results faster than most other systems.

This is the clearest evidence that v6 is close to the top system's ceiling while still retaining a
meaningful adversarial corner. Sol high does not merely accumulate points; it usually finds the
hard temporal model as well.

#### GPT-5.6 Sol medium

Sol medium loses 0.6 Core and 0.8 Maintenance relative to Sol high, saves roughly $8.47 on median
cost, and has two sweeps. It has greater Maintenance variance, from 6 to 10. For practical model
selection, it is the strongest high-quality price/performance point in the ordinary leaderboard.

#### GPT-5.6 Terra xhigh

Terra is stable rather than brilliant: all five Core scores are 36 or 37 and Maintenance is 6-8.
It repeatedly misses hotel-credit and period-close semantics. Its consistency makes the mean
credible, but also suggests a structural plateau rather than unlucky sampling.

#### GPT-5.6 Luna xhigh

Vanilla Luna is the most variable OpenAI arm: Core ranges from 27 to 37 and Maintenance from 2 to
8. One run ships only 53/94 scenarios and reaches 72/94 by the end. The model can produce a useful
implementation very cheaply, but the baseline Codex protocol does not reliably elicit enough
parallel review or requirements reconciliation for this benchmark.

That changes under OpenCode and under an explicit delegation instruction, discussed below. The
model identity alone is therefore an incomplete explanation of its baseline result.

#### GPT-5.5 xhigh

GPT-5.5 is coherent and fairly stable at 36-38 Core and 7-9 Maintenance, but it is economically
dominated by GPT-5.6 Sol medium in this sample. The tested Sol-medium configuration gains 1.2 Core
and 1.2 Maintenance points while cutting the median API-equivalent cost almost in half.

This is a useful configuration-level result rather than a clean generational estimate: model tier,
reasoning effort, and cohort differ. The observed gain is concentrated in migration history and
cross-release accounting, exactly where v6 is intended to discriminate engineering judgment.

#### Claude Opus 5 high

The two accepted Opus runs score 38/9 and 39/10. Run 1 misses a hotel-credit date boundary and one
cross-feature judgment case; run 2 sweeps. This places Opus in the top quality region, but `n=2`
does not support a reliability ranking against five-run arms.

Opus builds the most modular implementation and has the highest median test-file and test-
declaration counts. Its median final snapshot has about 4,430 production LOC, 6,424 test LOC, 53
production files, 28 test files, and 327 test declarations. Qwen has more test LOC, at 7,839. The
first Opus run still misses an off-by-one date.
The lesson is not that the tests are useless; it is that test volume is not test coverage of the
right semantic boundary.

#### Meta Muse Spark 1.3 high

The single Muse run finishes at 29/39 Core, 3/10 Maintenance, and 74/94 scenarios. It costs $53.61
of recorded OpenRouter inference and takes 9.45 model-hours. That is below every other
configuration mean in the main view; only the weakest individual Luna run is lower, at 27/39 and
2/10. The result is valid, but `n=1` makes it a trajectory study rather than a model ranking.

Its progression is revealing. Muse passes milestone 1 completely, reaches 22/24 scenarios at
milestone 2, and passes all three new durability families at milestone 3. The first broad break is
milestone 4: room accounting ends at 42/52 scenarios and only 2/9 new families. Milestone 6 then
ships at 52/75 with none of its nine new Core or Maintenance families passing. It adds no candidate
tests in that release and hits the turn-length limit, leaving finance reporting substantially
scaffolded rather than complete. Milestone 7 repairs much of that work and the final evaluation
recovers 11 scenarios, but the historical upgrades and several cross-feature compositions remain
broken.

The residual defects are not random endpoint omissions:

- hotel-credit expiry is calculated as `cancellation date + 366 days`, which is one day late when
  the interval crosses a leap day; the lot-order query itself is deterministic, but the wrong
  expiry changes which lot should be consumed;
- partial cancellation, payment reduction, chargeback, and payment-statement failures share
  reconciliation errors between stored payment provenance and the aggregate ledger read paths;
- current-state finance reports become functional during milestone 7, but databases created by
  earlier milestones still fail the finance-reporting and close-history upgrades; and
- the late credit-revival path performs a reporting read from inside an active operation
  transaction and times out waiting for another database connection. This is an implementation
  deadlock, not evaluator instability.

The implementation concentrates 5,390 of 6,506 production lines in `batches.ex`, launches no
subagents, and ends with 42 candidate tests. Test declarations remain at 39 through milestone 6
and rise to only 42 at milestone 7. The 9.45 hours therefore buy substantial repeated reading and
editing of one growing module, not broader decomposition or an independent requirements audit.

The closest headline result is Luna run 2 at 27/39, 2/10, and 72/94 scenarios. They share 12
failed families, including hotel credit, historical upgrades, and period-close revival. Their
profiles differ: Luna also misses several basic finance-report and restart/migration families,
while Muse uniquely retains a cluster of milestone-4 settlement and statement defects. The
closest family-failure pattern is Flash max run 2 at 31/39 and 6/10. Flash fails more at report
determinism and close immutability; Muse fails more at historical operability and payment
reconciliation. Muse is thus not merely a slower copy of a similarly scoring system. It is strong
at additive protocol and replay machinery, but weak at reconciling old state through later read
models and cross-feature transactions.

#### Grok 4.6 xhigh

Grok scores 36/7 once and 38/8 four times. The repeated 38/8 outcomes share the period-close
revival failures. This is one of the cleanest model fingerprints in the dataset: strong general
implementation, high repeatability, and one stable conceptual blind spot.

Grok is also economically competitive with Sol medium, though it trails on average quality and
has no sweep. Its median cost is $14.71.

#### Qwen3.8 Max xhigh

Qwen spans 31-38 Core and 6-10 Maintenance. One run reaches 38/39 and 10/10, missing only the
hotel-credit family, while another is a broad 31/6 outlier. It writes the largest median candidate
test suite, about 7,839 LOC and 286 declarations, but takes 4.22 hours and costs $25.34.

The high peak matters: the model can solve almost all of v6. The low floor matters more for an
autonomous engineering workflow. Capability is not yet dependable execution.

#### DeepSeek V4 Pro max

DeepSeek is relatively stable at 34-37 Core and 6-7 Maintenance. Its recurring deficits span
hotel credit, migration history, reporting, and period close. At $8.87 it is inexpensive relative
to other large OpenCode arms, but it takes 4.38 hours and remains materially below Terra or Grok
on quality.

#### Kimi K3 max

Kimi ends at 35-38 Core and 6-8 Maintenance. Its distinctive feature is late completion: it gains
an average of roughly nine scenarios between ship-time and final state, far more than other arms.
That is not evidence of private-feedback repair. Later requests cause the model to revisit or
finish earlier behavior.

Kimi is slow and expensive here: 4.67 hours and $29.23 median cost. Its long accumulated contexts
produce large cached-read charges despite discounted cache pricing.

#### GLM 5.3 high

GLM 5.3 has the widest mixture of success and instability among the large OpenCode models. It
produces one 39/10 sweep, but the five runs span 33-39 Core and 6-10 Maintenance. One trajectory
introduces a large stage-6 regression and repairs much of it at stage 7, yielding 11 recorded
regression episodes where 64 of 67 main trajectories have none.

The sweep proves that the capability is present. The distribution says that model selection based
only on the best run would be badly misleading.

#### GLM-5.3 Flash

Flash is an unusually cheap option, but neither higher reasoning nor longer runtime buys a better
Core result in this sample. High averages 34.75/39 and 6.5/10 at $2.08 over 4.16 hours. Max averages
34.0 and 6.75 at $2.96 over 6.06 hours. The max arm consumes substantially more prompt and output
tokens while moving sideways.

This is direct evidence against assuming that the highest available effort setting is the default
economic choice.

## The estimate-basis quality-cost frontier

Using mean Core, mean Maintenance, and median API-equivalent inference cost as three independent
objectives, the descriptive Pareto frontier among arms with reconstructed estimates is:

| System | Mean Core | Mean Maintenance | Median cost |
|---|---:|---:|---:|
| Luna xhigh / Codex | 32.6 | 6.2 | ~$1.50 |
| GLM-5.3 Flash high / OpenCode | 34.75 | 6.5 | ~$2.08 |
| Luna xhigh / OpenCode | 36.6 | 7.6 | ~$2.55 |
| Luna xhigh / delegated Codex | 37.0 | 8.0 | ~$4.23 |
| Terra xhigh / OpenCode | 37.6 | 7.6 | ~$11.50 |
| Astra low / Codex (n=2) | 39.0 | 9.0 | ~$12.36 |
| Sol high / Codex | 38.8 | 9.6 | ~$22.37 |

Paid external-model rows are excluded from this dominance calculation because their recorded
OpenRouter spend is not the same cost basis. They remain in the main results and cost audit, but a
joint frontier would require normalized provider-rate reconstruction. This table still uses small
independent samples, point estimates, and medians; it does not price reliability directly. Within
the estimate-basis arms, it suggests provisional operating points rather than winners:

- low-cost exploratory work: baseline Luna or Flash;
- low-cost work where a stronger review process is acceptable: delegated Luna;
- a promising high-quality operating point: Astra low, with one sweep and one historical-replay miss;
- maximum demonstrated v6 reliability: Sol high.

Sol medium leaves this point-estimate frontier because Astra low has higher mean scores and a
lower median cost. Sol medium remains the better-replicated routine-work comparator; two Astra
samples are not enough to establish reliable dominance.

Opus is absent because its observed quality is slightly below Sol high while its cost is more than
twice as high. That is an economic statement about the current two-run sample, not a general claim
about Claude Code or Opus.

## Harness and delegation effects

The controlled harness view uses the same benchmark commit, milestone order, evaluator, handoff
protocol, model, and reasoning effort. It changes the coding harness. The delegated Luna arm keeps
Codex CLI but adds a compound prompt-and-compute intervention: it requires an audit, changes review
salience and child-session behavior, and permits a larger inference budget.

| Model and effort | System | Mean Core | Mean Maint. | Sweeps | Median cost | Mean candidate subagents |
|---|---|---:|---:|---:|---:|---:|
| Sol high | Codex CLI | 38.8 | 9.6 | 4/5 | ~$22.37 | 4.4 |
| Sol high | OpenCode | 38.2 | 8.8 | 3/5 | ~$23.47 | 13.0 |
| Sol medium | Codex CLI | 38.2 | 8.8 | 2/5 | ~$13.90 | 4.4 |
| Sol medium | OpenCode | 37.2 | 8.0 | 0/5 | ~$14.60 | 9.8 |
| Terra xhigh | Codex CLI | 36.6 | 7.0 | 0/5 | ~$9.96 | 0.6 |
| Terra xhigh | OpenCode | 37.6 | 7.6 | 0/5 | ~$11.50 | 6.2 |
| Luna xhigh | Codex CLI | 32.6 | 6.2 | 0/5 | ~$1.50 | 0.0 |
| Luna xhigh | OpenCode | 36.6 | 7.6 | 0/5 | ~$2.55 | 7.6 |
| Luna xhigh | delegated Codex | 37.0 | 8.0 | 0/5 | ~$4.23 | 17.8 |

### What the harness comparison says

OpenCode causes substantially more delegation for Sol high and medium, with slightly lower
official scores. For Terra, OpenCode gains 1.0 Core and 0.6 Maintenance. For Luna, it gains 4.0
Core and 1.4 Maintenance. The harness is therefore not a universal multiplier. It changes how each
model allocates work, context, review, and output.

Small-sample exact permutation tests are exploratory but useful here:

- Sol high OpenCode versus Codex: Core -0.6 (`p=1.00`), Maintenance -0.8 (`p=0.72`), candidate
  subagents +8.6 (`p=0.0079`).
- Sol medium: Core -1.0 (`p=0.32`), Maintenance -0.8 (`p=0.62`), subagents +5.4 (`p=0.079`).
- Terra: Core +1.0 (`p=0.079`), Maintenance +0.6 (`p=0.67`), subagents +5.6 (`p=0.0079`).
- Luna OpenCode: Core +4.0 (`p=0.063`), Maintenance +1.4 (`p=0.42`), final scenarios +6.4
  (`p=0.056`), subagents +7.6 (`p=0.0079`).
- Luna delegated Codex: Core +4.4 (`p=0.032`), Maintenance +1.8 (`p=0.28`), final scenarios +6.6
  (`p=0.032`), subagents +17.8 (`p=0.0079`).

These are independent five-run samples, not paired trajectories, so the p-values should not be
read as definitive causal estimates. The Luna association is large enough to motivate a controlled
follow-up, but the present samples do not identify which part of the intervention caused it.

The Sol-high aggregate needs one further decomposition. One OpenCode run loses four Core and four
Maintenance points because a synchronous accounting initializer locks SQLite during boot and
starves the connection pool. Its private behavioral scenarios otherwise pass. The official run
and official 38.2/8.8 mean remain valid end-to-end results, but those eight failed checks are one
operational defect rather than eight semantic misses. Removing only that timeout-class defect
produces a diagnostic semantic-only mean of 39.0/9.5. At five runs, the evidence therefore detects
no Sol-high semantic harness difference; it does show lower operational reliability in the tested
OpenCode cohort.

Family fingerprints also show that OpenCode relocates some OpenAI-model failures. Revival improves
slightly, while ship-time migration and history scars appear more often. All 29 such scar-family
failures in the 20 OpenAI-on-OpenCode trajectories were introduced at uninterrupted milestones, so
resume behavior does not explain that pattern. Across the external OpenCode models, interrupted
milestones and scars are associated instead: introducing-milestone checks fail at 25% after an
interruption versus 12% without one, with a model-stratified pooled odds ratio of 2.39. That is an
observational association, not evidence that interruption causes the failures.

### What the Luna intervention says

The added instruction is:

> Use subagents proactively for focused, non-overlapping work. At each milestone, delegate at
> least one independent audit of the relevant requirements, existing implementation, or
> cross-milestone interactions before you finish. Use a second subagent only when the milestone
> genuinely benefits from another independent investigation or review. Incorporate their
> findings, do not duplicate their work, and remain responsible for the final implementation and
> verification.

The delegated Luna cohort averages 37.0/8.0, compared with baseline Luna's 32.6/6.2. It also
averages 17.8 candidate subagents rather than zero and $4.15 rather than $1.42 in mean cost. This is
an association under the controlled prompt variant; five independent runs do not identify a
precise causal effect size.

The intervention is chiefly an audit pipeline. Of 89 candidate-launched children, 87 receive an
explicit read-only audit assignment. Two children, both in the strongest delegated run, own
bounded implementation slices with disjoint write scopes. No child is assigned test writing. The
parent often continues working while an audit runs, so the pipeline is parallel in time without
being broad concurrent implementation.

One stage-7 trajectory contains a complete audit-to-fix chain: the child identifies the interaction
between closed history and restored liability, and the parent implements the compensating entry
and adds tests before finishing. That is direct mechanism evidence for one run, not a cohort-wide
causal estimate. Across the cohort, the intervention also buys more inference and changes review
salience, so its aggregate gain cannot be attributed to child count alone.

OpenCode Luna uses 7.6 subagents on average and scores 36.6/7.6. Delegated Codex Luna uses 17.8 and
scores 37.0/8.0, at an additional $1.61 mean cost. This is descriptive, not a delegation dose-
response: the cohorts also differ in harness, prompt, context assembly, and agent behavior. A
within-harness prompt experiment would be required to estimate diminishing returns.

The two improved Luna systems do not fail in the same way. Relative to baseline Luna:

- both reduce failures in effective-dated reporting, report correctness, report determinism, and
  the late-adjustment revival cluster;
- delegated Codex eliminates the observed stage-4 migration, room-history, stage-5 migration, and
  payment-history failures in its five runs;
- OpenCode cuts hotel-credit failures from 4/5 to 2/5, while delegated Codex remains at 4/5; and
- OpenCode has no transfer-shortfall-composition failures, while delegated Codex has 2/5.

Trajectory-level inspection narrows those differences substantially. Every hotel-credit miss in
the two cohorts is the same one-day `expires_on` representation choice: the implementation stores
the first invalid day rather than the last valid day. The ordering and restoration logic named by
the family is otherwise correct in these runs. Several delegated audits explicitly endorsed that
alternate convention, while three OpenCode parents and one delegated Codex parent chose the
evaluator's convention.

The two delegated transfer-shortfall misses are also downstream of the basic absorption rule. One
preserves lot provenance and absorbs the restoration correctly but reconstructs the report's
opening liability as zero instead of 700. The other crashes in report projection on a string-key
versus atom-key mismatch. Both pass dedicated earlier shortfall checks. OpenCode's five parents all
complete the composed reporting path, but two do so without any stage-6 child task.

The defensible interpretation is therefore narrower than the family counts suggest: OpenCode's
parent trajectories produce more robust stage-6 projections in this sample, while the hotel split
is a convention/cohort effect. Codex also spawns more child sessions than it receives useful final
audit reports; several children return interim status, inspect a changing worktree, or time out.
See [Luna harness trajectory deep dive](LUNA_HARNESS_TRAJECTORIES.md) for the ten-run evidence.

The operational hypothesis worth testing is not "launch as many agents as possible." It is:

1. weaker models can benefit greatly from one genuinely independent audit surface;
2. the main agent must incorporate the result rather than duplicate it;
3. concurrent edits to the same files are a poor default; and
4. additional audits should have a clearly distinct question; count alone is not evidence of
   useful coverage.

### System, not model, is the experimental unit

The same Luna weights occupy three very different points. The model name alone cannot predict
the result. The effective system includes:

- harness tool vocabulary and tool-call ergonomics;
- prompt and repository instructions;
- context assembly and caching;
- subagent availability and the model's propensity to use it;
- retry and continuation behavior; and
- the cost of all descendant sessions.

External OpenCode models almost never launched child sessions in these accepted runs; one Kimi
run launched one. That is an observed system behavior, not proof that those models cannot delegate.
The mechanism was available, but invocation was endogenous and was not explicitly required in the
baseline prompt. Future reports should not silently attribute the resulting score solely to the
model weights.

## Cost audit

### OpenAI harness costs

The dashboard's corrected harness comparison includes every accepted root session and every
descendant model session. It also includes all harness-owned Codex auto-review sessions at Luna
rates while excluding those workers from the candidate `Subagents` count. Accepted baseline Luna
runs contain 1-3 such review children and delegated runs contain 2-8, so review compute is part of
the compound intervention rather than a fixed one-session constant.

The corrected full-session result reverses the initial visual impression that OpenCode was
cheaper:

| Model | Codex median | OpenCode median | OpenCode delta | Cache hit Codex / OpenCode |
|---|---:|---:|---:|---:|
| Sol high | ~$22.37 | ~$23.47 | +5% | 95.0% / 92.7% |
| Sol medium | ~$13.90 | ~$14.60 | +5% | 94.6% / 91.0% |
| Terra xhigh | ~$9.96 | ~$11.50 | +15% | 95.9% / 94.2% |
| Luna xhigh | ~$1.50 | ~$2.55 | +70% | 96.0% / 96.4% |

OpenCode generally has more child sessions and more output. Cache hit alone does not explain cost.
For example, Luna's cache fraction is marginally higher under OpenCode, but prompt replay volume
and output are much larger. Sol high averages about 6.8 descendant sessions in Codex and 13.0 in
OpenCode; Luna averages 1.4 versus 7.6.

The OpenCode OAuth experiment had an actual marginal subscription charge of $0. The displayed
numbers answer a different and useful question: what would the recorded inference have cost at the
same OpenAI API list prices? Subscription economics and inference efficiency must remain separate.

### OpenCode external-model costs

The external-model audit finds no missing descendant cost for Muse, Grok, Qwen, DeepSeek, or GLM
5.3. Muse launches no child sessions. One Kimi child session changes one run materially. The
completed-sample totals are:

| Configuration | n | Median cost | Sample total | Mean prompt tokens/run | Aggregate cache hit |
|---|---:|---:|---:|---:|---:|
| Meta Muse Spark 1.3 high | 1 | $53.61 | $53.61 | 127.9M | 83.8% |
| Grok 4.6 xhigh | 5 | $14.71 | $73.55 | 18.9M | 90.6% |
| Qwen3.8 Max xhigh | 5 | $25.34 | $127.76 | 53.4M | 91.6% |
| DeepSeek V4 Pro max | 5 | $8.87 | $46.62 | 89.4M | 96.4% |
| Kimi K3 max | 5 | $29.23 | $153.51 | 45.8M | 92.7% |
| GLM 5.3 high | 5 | $20.96 | $115.03 | 67.8M | 97.7% |
| GLM-5.3 Flash high | 4 | ~$2.08 | ~$9.01 | 61.4M | 97.3% |
| GLM-5.3 Flash max | 4 | ~$2.96 | ~$13.83 | 95.3M | 97.6% |

This explains the initially suspicious Kimi and GLM totals. Cached input is discounted, but the
discount applies to tens of millions of replayed tokens. A 90%-98% cache hit on a very large
denominator can still dominate cost. Kimi's cache reads account for roughly $12-$14 per run and
GLM 5.3's for roughly $13-$22.

Muse is an even more extreme one-run example: 127.9 million prompt tokens, a lower 83.8% aggregate
cache hit, 341,619 output tokens, and $53.61 of recorded spend. Those figures describe this
trajectory's long, repeatedly replayed working context; they are not a stable estimate for the
model from one sample.

That cost is neither private-evaluator traffic nor an accounting error. It arises from how the
OpenCode conversation repeatedly presents a growing working context to those models. It is best
described as a model-plus-harness context-management cost. It may not be intrinsic to the model,
but it is part of what this tested system needed to produce the result.

### Cost is a result, not a scalar score

The benchmark should not combine quality and dollars into one magic number. Different users have
different loss functions for an incomplete implementation. The correct presentation is a frontier
with at least:

- mean and range of Core;
- mean and range of Maintenance;
- sweep frequency with uncertainty;
- median and sample-total cost;
- runtime; and
- intervention details such as harness and delegation.

This preserves the information needed to choose a system for a cheap exploratory task, a routine
feature, or a high-consequence migration.

## Failure anatomy

### The hard families

The following are final-score failures among the 67 main trajectories:

| Family | Stage | Track | Failed runs | Failure rate |
|---|---:|---|---:|---:|
| Late-adjustment posting | 7 | Core | 49 | 73.1% |
| C5 double revival | 7 | Maintenance | 49 | 73.1% |
| C1 revival | 7 | Maintenance | 48 | 71.6% |
| Hotel-credit lifecycle | 2 | Core | 31 | 46.3% |
| M4 payment-reduction upgrade | 4 | Core | 28 | 41.8% |
| R2 room-history upgrade | 4 | Maintenance | 26 | 38.8% |
| R4 projection-history upgrade | 6 | Maintenance | 18 | 26.9% |
| Finance report determinism | 6 | Core | 14 | 20.9% |
| C3 transfer-shortfall absorption | 6 | Maintenance | 10 | 14.9% |
| R5 close-history upgrade | 7 | Maintenance | 10 | 14.9% |
| Finance-close immutability | 7 | Core | 8 | 11.9% |

The distribution is highly concentrated. The three revival-related families account for 146
failed family-points. Eighteen families account for none.

### The central failure: immutable history plus restored liability

The hardest scenario is a bitemporal accounting case:

1. A credit lot expires and that expiry appears in a now-closed daily report.
2. A later committed operation has an old effective date and applies credit from that lot.
3. The closed report must remain unchanged.
4. The first open posting day must receive a negative `expired_cents` movement, restoring the
   company's liability.
5. If that revived credit is consumed later, the original revival history must remain visible; it
   must not be netted away or rewritten.

Failure on the Core late-adjustment family by main configuration:

| Configuration | Failed / n |
|---|---:|
| Astra low | 0/2 |
| Astra medium | 0/2 |
| Astra high | 0/2 |
| Sol high | 1/5 |
| Sol medium | 2/5 |
| Terra | 5/5 |
| Luna baseline | 5/5 |
| GPT-5.5 | 4/5 |
| Opus 5 | 0/2 |
| Meta Muse Spark 1.3 | 1/1 |
| Grok 4.6 | 5/5 |
| Qwen3.8 Max | 4/5 |
| DeepSeek V4 Pro | 5/5 |
| Kimi K3 | 5/5 |
| GLM 5.3 | 4/5 |
| Flash high | 4/4 |
| Flash max | 4/4 |

A first-failing-assertion census of the original 47 main-view revival failures finds:

- 32 runs emit no restoration;
- 11 restore the liability silently on the backdated effective day rather than the first open day;
- 2 over-restore it;
- 1 restores it under the wrong movement classification; and
- 1 mutates the closed report.

The closed report is therefore preserved in 46 of those 47 failing runs and 59 of the original 60
main trajectories. The dominant defect is not rewriting published history; it is failing to
append the correct compensating entry while changing current lot state. Muse adds a 48th failure
through a different mechanism: its late-application transaction calls the reporting read path and
times out waiting for another database connection. The neighboring finance-close-immutability
family still fails in 8 of 67 runs, so the corpus does not establish that historical immutability
is generally solved.

Passing implementations explicitly model the correction. In simplified form:

```text
if the consumed lot's expiry was already published in a closed period:
    posting_date = first_open_posting_date
    append movement(posting_date, expired_cents = -consumed_amount)
```

Opus run 2 writes a candidate test that names this invariant directly: credit redeemed after a
report expired its lot must come back into the liability. Sol high's passing implementation makes
the same distinction in its finance layer. Failing Grok runs build substantial close and
late-adjustment machinery but omit this compensating classification.

This is a good benchmark problem. It is compact, realistic, hard to bluff, and distinguishes
snapshot-oriented implementations from append-only historical models.

It is also overrepresented in the score. `late-adjustment-posting` and C5 have identical pass/fail
vectors across all 67 runs. C1 co-fails with them in 48 of the 49 failures. One conceptual defect
therefore costs one Core point and usually two Maintenance points.

### Hotel-credit lifecycle

The second-largest cluster is older and more varied. Correct behavior requires:

- availability through the date 365 days after cancellation, followed by expiry on the next day;
- earliest-expiry-first consumption;
- source-operation-ID ordering for equal expiries; and
- restoration to the original lot and origin after reversal.

Thirty-one runs fail the family. The two ordering scenarios fail 31 and 29 runs respectively, but
individual trajectories also miss date arithmetic or provenance restoration. Opus run 1 is an
instructive near miss: its architecture and test volume are strong, but the private check exposes
an off-by-one expiry date.

Muse adds a different concrete instance of the same boundary error. Its implementation stores
credit expiry as cancellation plus 366 elapsed days. That happens to satisfy its non-leap
candidate example, but crosses the wrong calendar date when a leap day intervenes. The ordering
query correctly sorts by expiry and source operation ID; the wrong dates corrupt the ordering
input before that tie-breaker can help.

This family earns its place because it combines calendar semantics with deterministic identity and
reversal provenance. Unlike the revival cluster, its failures are not all the same mechanism.

### Historical migration and payment provenance

The stage-4 system checks move a real milestone-3 database into the milestone-4 implementation.
The upgraded system must reconstruct funding types and commit order, preserve a historical senior
block, retain per-payment provenance through settlement and reduction, survive restart, and remain
idempotent.

The Core migration family fails 28 runs; the corresponding Maintenance room-history family fails
26. They co-fail in 26 of 28 Core failures, a Jaccard similarity of 92.9%.

This is another genuine hard axis: can the model evolve the schema and interpretation of old data,
not just create correct new rows? It should remain in the successor, but its Core and Maintenance
views should either be declared as one composite capability cluster or redesigned to contribute
more independent evidence.

### Score dependence and effective dimension

The 49 family points are not 49 independent trials:

- 18 families have identical all-pass vectors;
- late-adjustment posting and C5 have identical 49-failure vectors;
- C1 overlaps those failures in 48 runs;
- M2 migration and R1 policy history have identical two-failure vectors; and
- M4 migration and R2 room history overlap in 26 runs.

Dependence is not inherently bad. A production defect often affects several user-visible and
maintenance properties. The problem is interpretive: adding the points implies more independent
evidence than the benchmark contains.

The score also gives root defects accidental exchange rates. The missing revival compensation
usually costs three family points, while the Sol-high/OpenCode boot-lock defect costs eight. Both
are legitimate contract failures, so the official score should retain them. They are not three and
eight independent engineering mistakes. Family totals measure affected behavioral surface; they
do not count root causes.

The observed outcome geometry makes the concentration concrete. The 49 family columns contain
only 30 distinct pass/fail vectors across the 67 runs, and their centered matrix has rank 27. The
participation ratio of the family-failure covariance is about 7.1, meaning that the observed
variance is concentrated in a small number of co-moving directions. At scenario grain, only 42 of
94 scenarios fail even once; 52 are saturated in this sample. These are descriptive properties of
the current outcome matrix, not an estimate that software engineering has seven latent abilities.

The same scenario can also belong to more than one scored family. Summing failing family members
produces 403 scenario incidences, while deduplicating by trajectory and scenario produces 355
unique failed scenario/run cells. That reuse is diagnostically reasonable, but it is another reason
not to interpret every family point as independent evidence.

Future reporting should retain the detailed families but also expose a smaller set of latent
capability clusters, for example:

- core operational mechanics;
- deterministic credit identity and reversal;
- durable exact replay;
- historical payment provenance and migration;
- effective-dated reporting;
- immutable close and late adjustment; and
- cross-feature composition.

Model rankings should be checked for robustness both at the family level and at the capability-
cluster level.

A minimal sensitivity check already shows why. The table below treats Core plus Maintenance as 49
family points, then either collapses the three revival families into one strict cluster point or
removes that cluster entirely. These are diagnostics, not proposed official scores.

| Configuration | Original /49 | Revival collapsed /47 | Revival removed /46 |
|---|---:|---:|---:|
| Sol high | 48.4 | 46.8 | 46.0 |
| Opus 5 | 48.0 | 46.0 | 45.0 |
| Sol medium | 47.0 | 45.8 | 45.2 |
| Grok 4.6 | 45.4 | 45.4 | 45.4 |

Removing the cluster moves Grok ahead of both Opus and Sol medium; collapsing it preserves their
order but narrows the gaps. Core and Maintenance are themselves strongly associated across the 67
main runs (Spearman `rho = 0.808`). The headline ordering is therefore a weighting choice over
dependent evidence, not a ranking assembled from 49 independent trials.

## Position, recovery, and trajectory dynamics

### Difficulty by stage

Two denominators are useful. A family-cell rate counts passed family/run cells out of `67 x the
number of families in the stage`. A whole-stage rate counts trajectories that pass every family
in that stage.

| Stage | Track | Families | Ship family cells | Final family cells | Final whole-stage runs |
|---|---|---:|---:|---:|---:|
| 1 | Core | 6 | 98.0% | 99.5% | 65/67 (97.0%) |
| 2 | Core | 5 | 88.4% | 90.1% | 35/67 (52.2%) |
| 2 | Maintenance | 1 | 97.0% | 97.0% | 65/67 (97.0%) |
| 3 | Core | 3 | 96.5% | 98.5% | 64/67 (95.5%) |
| 4 | Core | 8 | 89.6% | 91.2% | 34/67 (50.7%) |
| 4 | Maintenance | 1 | 61.2% | 61.2% | 41/67 (61.2%) |
| 5 | Core | 7 | 96.4% | 97.2% | 57/67 (85.1%) |
| 5 | Maintenance | 1 | 91.0% | 91.0% | 61/67 (91.0%) |
| 6 | Core | 6 | 90.0% | 93.0% | 51/67 (76.1%) |
| 6 | Maintenance | 3 | 84.1% | 86.1% | 44/67 (65.7%) |
| 7 | Core | 4 | 78.0% | 78.0% | 18/67 (26.9%) |
| 7 | Maintenance | 4 | 60.1% | 60.1% | 14/67 (20.9%) |

Stage 7 is plainly hardest, but content and position are confounded. Earlier requests have later
milestones in which incidental refactoring or new tests can repair them. Stage 7 has no such
opportunity, so its ship and final rates are necessarily identical. Earlier stages improve only
modestly from ship to final and 57/67 trajectories never recover any scenarios, so placement alone
does not explain the Stage-7 deficit.

The successor should treat position as an unestimated hypothesis. Put the same hard block in
different positions across order-balanced forms. A final symptom-driven integration audit may be
useful, but it measures diagnosis and repair under an extra prompt; it is not a neutral equalizer
for the original feature task.

### Recovery is uncommon and heterogeneous

Fifty-seven of 67 main trajectories show no scenario recovery. The remaining ten gain between 1 and
21 scenarios. Kimi accounts for much of the large recovery. Muse gains 11 because milestone 7
finishes much of the finance-report work left incomplete at milestone 6. One GLM run has a
catastrophic temporary regression and later repair.

This means the current `average recovery` metric combines at least three phenomena:

- unfinished behavior completed later;
- an earlier defect repaired while implementing a later request; and
- a regression introduced and then reversed.

Those are not equivalent. The successor should report them separately:

- delayed completion of an earlier requirement;
- newly introduced regression count and duration; and
- explicit later repair.

### Prefix depth is too coarse

Prefix depth counts the uninterrupted sequence of checkpoints from milestone 1 with all
introduced Core families passing. It is Core-only and stops at the first failed checkpoint;
later repair does not extend it. Astra low 01 therefore has prefix depth 7 despite two Maintenance
failures; low 02 and high 02 have depth 7 and full sweeps.
Among the 67 main runs, depths are:

- 0: 3 runs;
- 1: 30;
- 2: 1;
- 3: 13;
- 4: 1;
- 6: 8; and
- 7: 11.

One small stage-2 miss sends an otherwise excellent run to depth 1. That makes the measure useful
for strict release-gate reasoning but weak as a general quality summary. Keep it only if labeled
as a strict prefix gate, not as a substitute for final coverage.

### Regression episodes are sparse

Sixty-four runs have zero recorded Core-family regression episodes, two have one, and one GLM run has 11.
The metric is therefore dominated by one trajectory. This may accurately describe v6, but it is
not yet a stable model discriminator.

These counters do not capture Maintenance regressions, and historical system-check outcomes are
carried forward rather than rerun against every later implementation. A final score therefore
combines current private-test behavior with upgrade-time evidence. All six Astra M7 evaluations
pass 83/83 private tests. Low 02 and high 02 also pass both current system checks; the other four
pass one of two. Their published /94 totals include nine earlier system-check outcomes as well.
That distinction must be preserved when
claiming a later repair or persistent defect.

A successor designed to test maintenance should deliberately create more opportunities for
regression: shared contracts, duplicated derived state, external events, concurrent updates, and
schema transitions whose correct treatment cannot be achieved by additive endpoint work alone.

## Code and test behavior

### Size and structure

Median final snapshots show very different implementation styles:

| Configuration | Production LOC | Test LOC | Test declarations | Largest production file share |
|---|---:|---:|---:|---:|
| Astra low | 2,018 | 2,371 | 54.5 | 40% |
| Astra medium | 2,148 | 3,409.5 | 77.5 | 29% |
| Astra high | 2,166 | 5,046 | 109.5 | 29% |
| Sol high | 3,660 | 2,767 | 50 | 47% |
| Sol medium | 3,389 | 2,476 | 50 | 58% |
| Terra | 4,392 | 2,576 | 35 | 57% |
| Luna baseline | 4,299 | 2,354 | 37 | 75% |
| GPT-5.5 | 4,438 | 3,569 | 42 | 66% |
| Opus 5 | 4,430 | 6,424 | 327 | 16% |
| Meta Muse Spark 1.3 | 6,506 | 2,824 | 42 | 83% |
| Grok 4.6 | 4,111 | 5,883 | 158 | 58% |
| Qwen3.8 Max | 4,241 | 7,839 | 286 | 35% |
| DeepSeek V4 Pro | 4,401 | 6,523 | 197 | 33% |
| Kimi K3 | 4,224 | 5,524 | 222 | 44% |
| GLM 5.3 | 4,571 | 7,188 | 220 | 30% |
| Flash high | 4,129 | 4,888 | 161 | 39% |
| Flash max | 4,850 | 6,624 | 212 | 34% |

The LOC columns use the dashboard's file rule. Structural ratios are independently recomputed from
non-hidden source files; 35 trajectories differ by four production lines because the dashboard
also counts a migration `.formatter.exs`. The difference does not affect any conclusion.

Opus and several OpenCode models decompose the code more aggressively and write many more tests.
Baseline and delegated Luna remain heavily concentrated in one production file. Delegated Luna
still improves substantially, so modularity is not the mechanism of its gain.

### Simple code metrics do not explain quality

Across the 67 main trajectories, Spearman correlations with final Core are:

- displayed inference cost under each row's stated basis: `+0.31`;
- runtime: `-0.60`;
- production LOC: `-0.56`;
- test LOC: `-0.22`;
- candidate subagents: `+0.38`;
- largest production-file share: `-0.06`;
- production-file count: `-0.20`;
- test-file count: `-0.11`; and
- test declarations: `-0.12`.

These are confounded cross-model correlations, not causal estimates. The negative runtime and LOC
relationships mostly reflect which models are slow and verbose. The important conclusion is
narrower: none of these simple metrics is a useful standalone quality proxy.

### Test judgment matters more than test volume

Candidate tests serve two roles:

1. they catch implementation defects during the current milestone; and
2. because sessions are fresh, they externalize product understanding for later agents.

The second role is easy to overlook. A well-named test encodes a durable invariant for the next
session. A large test suite can still be poor handoff memory if it mirrors endpoint happy paths and
never states the historical rule.

Grok writes many stage-7 close tests but omits the liability-revival invariant and repeatedly lands
at 38/8. Opus run 2 names and tests that invariant and sweeps. Opus run 1 has hundreds of tests but
misses a one-day expiry boundary. These inspected examples show that outcomes are sensitive to test
selection and semantic modeling, not just test volume; they do not by themselves estimate how often
candidate-test choice caused failure across the full sample.

The next version should measure candidate-test quality directly with held-out mutations or a
behavioral diversity panel. Test LOC should remain descriptive only.

## Validity assessment

### What v6 does unusually well

#### It tests cumulative product evolution

Many coding benchmarks ask for a patch against a fully specified terminal state. V6 asks for a
sequence of locally reasonable releases whose later requirements expose the consequences of
earlier architecture. That is much closer to real software maintenance.

#### It hides future requirements without hiding current requirements

The candidate is not asked to guess the future. Each current request is explicit. The benchmark
tests whether the implementation preserves enough identity, provenance, and history to support a
plausible later product evolution. This is a fairer and more useful challenge than arbitrary secret
requirements.

#### It exercises persistent upgrades

The system checks carry real databases across milestone boundaries and restart the product. They
catch a class of failure that endpoint-only test suites miss: code that works for new state but
misinterprets production state created by an earlier schema and business rule.

#### It evaluates through public behavior

Private expectations are derived independently and tested through the API and explicit upgrade
fixtures. The evaluator does not reward a particular internal architecture. Monoliths and modular
designs can both pass if they implement the behavior.

#### It separates current functionality from maintenance

Core and Maintenance expose different engineering qualities. The stage-4 results show why this
matters: implementations can pass much of current room accounting while failing historical room
provenance.

#### It validates evaluator sensitivity

The canary suite introduces narrow semantic sabotage and observes targeted failures. The evidence
shows that the relevant migration, history, and late-adjustment checks turn red when their intended
invariant is broken. This supports construct validity for the hard families.

#### It preserves run-level evidence

Repeated accepted runs, ship and final states, family-level outcomes, cost, runtime, source
snapshots, and agent logs permit analysis beyond a leaderboard. Without those artifacts, the Luna
delegation effect, context-replay cost, score dependence, and recurring conceptual failures would
remain invisible.

### What v6 can support

V6 can support claims about:

- the tested agent system's ability to evolve this Phoenix product through these seven releases;
- relative quality, reliability signals, and cost in the tested harness and effort configuration;
- sensitivity to historical migrations, temporal accounting, deterministic provenance, and
  cross-feature composition;
- consistency and recurring failure signatures across repeated runs; and
- how prompt/harness interventions change the tested system.

### What v6 cannot support

V6 cannot by itself support broad claims about:

- general software-engineering ability across languages and application types;
- front-end, mobile, data science, systems, or infrastructure engineering;
- security, performance, concurrency, or production operations;
- long-context conversational continuity, because sessions are fresh per milestone;
- human collaboration quality or code-review communication;
- true production cost under every subscription and provider contract; or
- precise sweep probabilities from two to five samples.

The dashboard should continue to say "model plus harness" wherever a causal reading of the model
name alone would be tempting.

## Limitations and measurement distortions

### One domain, one stack, one product topology

All 67 main runs solve the same Phoenix JSON API in the same accounting domain. A model can be
excellent at repository-scale TypeScript or systems Rust and still underperform here; another can
have a strong learned prior for ledger-like CRUD APIs and look more general than it is.

The scaffold also fixes many low-level choices. V6 mostly tests business-state modeling and
evolution, not framework selection, deployment architecture, or user-interface judgment.

### Fixed request order

Difficulty is entangled with position. Stage 7 has accumulated codebase complexity and no later
repair window. Stage 2 has five later opportunities for incidental repair. The stage pass table
cannot tell how much of stage 7's difficulty is content and how much is placement.

### Saturated and dependent families

Eighteen of 49 families contribute no discrimination in the main sample. Several hard families
are duplicate or near-duplicate outcome vectors. The nominal 49-dimensional score has a much
smaller effective dimension.

This makes one-point differences less uniform than the table suggests. Missing a saturated batch
validation family would be an unusual broad failure. Missing one of three co-moving revival points
may reflect one defect counted several ways.

### Small and unequal samples

Most arms have five runs, Flash has four, and Opus has two. Five is a useful screening sample but a
weak reliability sample. Unequal sample counts also make sample totals unsuitable for direct
comparison.

### Independent rather than paired harness samples

The Codex and OpenCode arms share benchmark conditions but are independent model draws. There is
no common random seed or paired latent trajectory. Exact permutation results are useful summaries,
not laboratory-grade estimates of harness causality.

### Counterfactual cost

OpenAI OAuth runs incurred no marginal API bill, and several displayed costs apply current list
prices to recorded token usage. They are consistent counterfactual estimates, not invoices.
Provider pricing, long-context rules, and subscription terms can change.

### Candidate tests are both behavior and treatment

Because tests persist between fresh sessions, a model that writes a test changes the information
available to later instances of itself. This is intended and realistic, but it means "test-writing
ability" and "handoff-memory quality" cannot be separated in the current protocol.

### The benchmark rewards completion, not maintainability as judged by humans

The private evaluator detects behavioral maintenance, not readability, API ergonomics, change
isolation, or whether a human team would want to own the code. LOC and structure help describe the
artifact but are not reviewed scores.

## Lessons for a successor benchmark

### 1. Freeze v6

Do not keep adding requests to Group Stay and call the result v7. Preserve v6 as:

- a regression suite for agent-system changes;
- a calibration anchor for new model generations;
- a cost and harness comparison corpus; and
- a source of known hard semantic patterns.

Changing the existing family definitions would destroy longitudinal comparability. Corrections to
reporting and audit logic are appropriate; changing the product challenge is not.

### 2. Preserve delayed semantic revelation

The successor's central design principle should remain:

> An early implementation can satisfy the current request, but a later ordinary product request
> reveals whether it preserved the identities and invariants needed for evolution.

This is more valuable than simply making each isolated task larger. Difficulty should come from
the interaction between reasonable releases, not from an enormous initial specification.

### 3. Combine a longitudinal track with independent products

The next generation should not be another seven layers of financial accounting. It should contain
at least one long cumulative track plus smaller independent products, each with its own hidden-
future pressure. The long track preserves repeated onboarding, accumulated migration pressure,
path dependence, and durable handoff memory. A useful portfolio could include:

- a financial or inventory ledger for provenance and effective dating;
- a multi-tenant workflow service for authorization and isolation;
- an event-driven integration service for retries, webhooks, and reconciliation;
- a collaborative document or scheduling service for concurrency and conflict resolution; and
- a data or reporting service for migrations, performance, and deterministic backfills.

This reduces domain overfitting and makes the aggregate score more genuinely multidimensional
without throwing away v6's strongest longitudinal construct.

### 4. Add engineering axes v6 barely touches

The most valuable new axes are:

#### Concurrency and serializability

Introduce two valid operations that race against the same logical resource. Test atomicity,
isolation, duplicate delivery, optimistic conflict, and deterministic resolution. Sequential
idempotency is not enough.

#### External effects and reconciliation

Add a mock payment, email, storage, or webhook provider with timeouts, accepted-but-unknown
responses, delayed callbacks, and duplicate notifications. Later requests should require an
outbox, reconciliation, and auditable recovery.

#### Authorization and tenant isolation

Evolve roles and ownership after data exists. Include cross-tenant references, delegated access,
revocation, and historical audit requirements. This tests security invariants without relying on
vague penetration testing.

#### Performance and data scale

Provide a realistic fixture large enough to expose N+1 queries, unbounded scans, or quadratic
recomputation. Score explicit latency or query budgets alongside correctness, with deterministic
hardware-independent proxies where possible.

#### Operational robustness

Exercise cold boot against a large legacy fixture, lock discipline under concurrent requests,
connection-pool starvation, migration runtime budgets, and recovery after a partial start. Score
these as an operational capability rather than allowing one infrastructure defect to alias into
several semantic transition families.

#### Observability and diagnosis

Give the agent symptoms, logs, and metrics rather than a complete defect location. Require a fix
plus an operator-visible diagnostic or invariant. This measures investigation, not just greenfield
implementation.

#### Multi-service contract evolution

Change a schema or protocol consumed by another service. Require backward compatibility, staged
rollout, and eventual removal. A single repository can simulate this with independently deployed
components if multi-repository orchestration is too expensive.

#### Rollback and partial deployment

Test mixed-version operation and migration rollback. Many model-generated migrations are correct
only in a world where every process changes atomically.

#### Human-facing judgment

Include a small number of choices with legitimate tradeoffs, but score explicit observable
consequences and decision records rather than reviewer taste. Ambiguous semantics should remain
documented and excluded, as v6 already does.

### 5. Measure position and repair opportunity

V6 does not identify how much of Stage 7's difficulty comes from content versus terminal position.
Estimate that effect rather than assuming it. Options include:

- create two benchmark forms with hard blocks in different positions;
- rotate hard blocks across independent tracks while preserving within-track order; and
- predeclare whether each form has a later ordinary maintenance release.

A terminal symptom-driven audit can be a useful separate benchmark condition. It should provide
realistic signals such as a reconciliation discrepancy, a slow endpoint, or a migration warning
and require diagnosis of the underlying invariant. Because it adds information and inference, it
measures diagnosis and repair rather than neutrally equalizing the original feature tasks.

### 6. Design for independent evidence

Before freezing the suite, run red-canary interventions and pilot models to estimate the outcome
matrix. Use that matrix to find:

- families that never fail;
- families that always co-fail;
- scenarios that accidentally test the same defect twice;
- checks whose outcome is dominated by request position; and
- checks with unstable or ambiguous expected behavior.

It is acceptable for one defect to have several diagnostic checks. It should not silently count as
three independent headline points. Group correlated checks into a capability cluster or assign one
headline point with multiple diagnostics.

Record the first failing assertion or evaluator-authored mechanism label for every failed scenario,
along with a coarse semantic, operational, or rejection-cascade class. Root-cause interpretation
should be queryable from accepted results rather than reconstructed from logs after the fact.

### 7. Keep Core and Maintenance, add capability clusters

Core and Maintenance should remain separate. Add a second aggregation layer:

- detailed scenarios for diagnosis;
- family outcomes for product requirements;
- capability clusters for independent engineering dimensions; and
- no single grand score unless the weighting is explicit and justified.

This lets a reader see that two systems with 37 Core may differ: one misses a broad new feature,
another misses one historical accounting concept repeated across several families.

### 8. Treat prompt and harness as controlled factors

Future leaderboards should record a system identifier containing:

- model and exact version;
- reasoning effort;
- harness and version;
- base prompt and repository instruction hash;
- subagent policy;
- session and continuation policy;
- interruption and resume counts by milestone; and
- pricing snapshot.

A model-only view can still exist, but only for a declared canonical harness. Harness and prompt
experiments should have their own controlled view, as the current dashboard now does.

### 9. Standardize delegation experiments

The Luna result justifies a small budget-matched prompt experiment rather than ad hoc prompt
folklore:

- no delegation instruction;
- one required independent audit;
- audit plus optional second distinct investigation; and
- unconstrained proactive delegation.

Hold the total inference budget fixed where possible. Measure quality, cost, child-session count,
overlap, child assignment type, and whether findings changed the final diff. Classify children from
their complete assignments and actual write scopes, separating audits, implementation slices, test
work, and other jobs. Repeat this on at least one strong and one weak model. The likely optimum is
model-dependent.

Subagent count should remain descriptive. Rewarding count directly would invite waste.

### 10. Measure test quality, not test mass

Add a held-out mutation panel after each accepted final artifact. Mutations should each violate one
public invariant in a plausible way. Report:

- candidate-test mutation detection rate;
- distinct requirement families exercised by candidate tests;
- whether tests fail for the intended reason;
- whether tests reject a correct implementation because they entrench the candidate's mistaken
  semantics; and
- whether a later session uses the tests to prevent regression.

This would distinguish Opus-style broad test generation from tests that encode the particular
future-sensitive invariant.

### 11. Improve trajectory metrics

Replace or supplement current recovery and regression summaries with:

- requirement first-pass completion;
- delayed completion by later milestone;
- regressions introduced per release;
- regression survival in releases;
- repair without evaluator feedback;
- churn in previously correct capability clusters; and
- time and cost to return to a passing state.

Keep strict prefix depth only as a release-gate metric.

### 12. Use an adaptive sample plan

A practical protocol is:

1. Run three accepted samples for screening.
2. Expand ordinary arms to five.
3. Expand near-frontier ties, high-variance arms, and reliability claims to ten.
4. Stop economically dominated arms early only under a predeclared rule.

Report ranges and individual runs, not only averages. For sweeps, show Wilson intervals. For
harness comparisons, prefer matched versions and simultaneous cohorts where practical, but do not
pretend independent runs are paired.

### 13. Keep cost accounting symmetric and auditable

For every harness:

- include root, child, review, and continuation sessions required for the accepted result;
- normalize cached versus uncached token schemas;
- exclude evaluator computation;
- distinguish recorded provider spend from API-equivalent estimates;
- publish pricing snapshots and formulas; and
- show median cost separately from sample total.

Also report context replay volume and cache hit. Cache percentage without the denominator is
misleading, as Kimi, DeepSeek, and GLM demonstrate.

## A concrete successor shape

One feasible v7 design is a hybrid: one five-to-seven-release longitudinal track plus three shorter
orthogonal tracks. The long track preserves v6's repeated onboarding, accumulated migration
pressure, path dependence, and durable handoff memory; the short tracks broaden the capability
surface without turning every run into a day-long monolith.

| Track | Shape | Main pressure |
|---|---|---|
| Longitudinal ledger | 5-7 releases | reservations, corrections, migration, close, and late events |
| Workflow | 3 releases | approvals, roles, tenant isolation, revocation, and audit |
| Integration | 3 releases | outbound requests, callbacks, unknown outcomes, reconciliation, and replay |
| Collaboration | 3 releases | shared objects, offline edits, conflicts, ordering, and compatibility |

Each track would have:

- a small public API;
- one persistent upgrade;
- one concurrency or failure-injection surface where appropriate;
- one hidden-future identity or provenance requirement;
- one later repair opportunity;
- 6-10 diagnostic scenarios grouped into 3-5 independent families; and
- one or two Maintenance checks derived from real old-state fixtures.

This structure would retain genuine cumulative evolution while reducing the chance that one learned
domain prior dominates the entire score. It would also permit periodic replacement of short tracks
without discarding the longitudinal construct.

Freeze an ex ante capability map before collecting official results. Use order-balanced pilot forms
to estimate position effects, and use held-out model cohorts to check whether outcome-derived
clusters generalize before adopting them as scoring units. The exact track balance is a design
hypothesis to pilot, not a settled consequence of the v6 sample.

## Reporting recommendations

The default dashboard should answer three questions separately.

### 1. How capable and reliable is the system?

Show mean and range for Core and Maintenance, sweeps with intervals, and expandable individual
runs. Add capability-cluster results when available.

### 2. What does that result cost?

Show median cost, sample total, runtime, prompt replay, output, and estimate/recorded status. Do not
merge median and total or convert them into one efficiency score.

### 3. What operating system produced it?

Show harness, effort, prompt variant, child-session count, and whether costs include descendants.
Keep controlled harness comparisons separate from the main model leaderboard.

LOC, test LOC, and subagents belong inside run details and controlled comparisons. They are useful
diagnostics, not top-level definitions of quality.

## Bottom line

V6's central achievement is that it turns plausible software evolution into a reproducible test of
historical reasoning. It reveals a difference between systems that merely keep current state
correct and systems that preserve identity and append the right correction after history has been
published. That is real engineering signal.

Its central weakness is concentration. Too much of the remaining frontier signal now comes from
one accounting concept at the final position, while 18 families are inert and several points are
dependent. Astra clears that accounting concept in all six observations. Two samples sweep;
the other four lose repeated points to migration decoding and cold replay. These are real
reliability defects, not evidence that the instrument has regained broad frontier headroom.
Generational comparison needs the
mechanism analysis as well as the totals.

The suite should therefore be frozen, not discarded. Use it to track regression, cost, harness,
and generational change. Build the next benchmark around the same delayed-revelation principle,
but distribute that principle across independent domains, concurrency, external effects,
authorization, performance, migration, and diagnosis. The benchmark should evolve from "can an
agent survive seven releases of this ledger?" to "which kinds of software evolution can this
configured agent system survive, at what reliability and cost?"

## Reproducibility

Primary public evidence:

- `benchmark.json`: stage and family definitions;
- `candidate/requests/`: cumulative product requests;
- `run_candidate.py`: canonical prompts and fresh-session protocol;
- `evaluation/private_tests/`: behavioral evaluator;
- `evaluation/system_checks.py`: persistent upgrade checks;
- `evaluation/judgment/KNOWN_AMBIGUITIES.md`: intentionally excluded semantics;
- `evaluation/results/v6/index.html`: accepted-run manifest and dashboard;
- `evaluation/results/v6/accepted-runs.json`: all accepted trajectory records and derived tables;
  and
- `evaluation/results/v6/analyze.py`: portable population and aggregate verifier.

Regenerate the analytical artifact from the repository root:

```sh
python3 evaluation/results/v6/analyze.py
```

The verifier fails if the released population, score domains, identifiers, view counts, or group
headline metrics drift from the accepted-run records.
