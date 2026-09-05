# GPT-6 Astra on Sweat Bench v6

5 September 2026. Six completed trajectories, two each at low, medium, and high reasoning
effort, using Codex CLI 0.153.4 and the unchanged seven-milestone v6 benchmark.

## Results

| Effort / sample | Core /39 | Maintenance /10 | Scenarios /94 | API-equivalent cost | Model time | Production LOC | Test LOC | Test declarations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Low 01 | 39 | 8 | 92 | $11.64 | 41.7 min | 1,979 | 2,311 | 55 |
| Low 02 | 39 | 10 | 94 | $13.08 | 45.2 min | 2,057 | 2,431 | 54 |
| Medium 01 | 38 | 7 | 90 | $16.43 | 57.4 min | 2,242 | 3,447 | 73 |
| Medium 02 | 38 | 7 | 90 | $13.48 | 54.1 min | 2,054 | 3,372 | 82 |
| High 01 | 38 | 7 | 90 | $19.42 | 77.2 min | 2,230 | 4,903 | 111 |
| High 02 | 39 | 10 | 94 | $17.47 | 79.1 min | 2,102 | 5,189 | 108 |

Run IDs are `v6-astra-{low,medium,high}-{01,02}` in [the dataset](accepted-runs.json).
All seven milestones completed, every integrity check passed, and no candidate subagents or
descendant sessions were recorded. Every milestone completed in one runner attempt, using
ordinary handoff prompts and endogenous tests without a delegation intervention.

The second round used fresh workspaces and sessions, not prior implementations, tests, or
evaluation feedback. Benchmark content, runner, image, and prompts were unchanged. Each
container had two CPUs and 4 GiB of memory; each three-run round ran concurrently. Model time
includes tools and candidate tests, excluding evaluation and inter-milestone work. Total elapsed
times were 43.0/46.8 minutes for low, 58.5/55.5 for medium, and 78.6/80.5 for high.

**Low and high sweep in round two; medium repeats its original defects.** All six pass the
difficult late-credit-revival and cross-domain composition cases. Fourteen lost family-points
across the six runs represent repeated instances of two mechanisms, not fourteen distinct
mistakes. High's successful migration is a directly logged case of an inherited test exposing
a defect and prompting a repair before handoff.

Two samples per effort do not establish an effort ranking. Earlier GPT cohorts also used an
older Codex CLI: comparisons describe tested systems, not an isolated change of model weights.

## Failure Map

| Mechanism | Low 01 / 02 | Medium 01 / 02 | High 01 / 02 | Affected families |
|---|---|---|---|---|
| Misreads legacy room serialization | Pass / Pass | Fail / Fail | Fail / Pass | M4 migration; R2 room history |
| Cold replay requires unloaded result-key atoms | Fail / Pass | Fail / Fail | Fail / Pass | R4 projection history; R5 close history |

The official /94 combines current private tests with historical system checks recorded at their
designated milestones. It is not 94 fresh checks of terminal code. All six have identical
ship-time and final scenario totals; no failed sample recovers a scored family later.

## Migration: Preserving A Useful Test

### The repeated decoding error

Both medium samples and high 01 read the old `groups.rooms` column through raw SQL in M4.
They decode the outer JSON and treat its elements as maps. The M3 writer uses Ecto's
`{:array, :map}` type: the retained SQLite adapter encodes individual maps and then the enclosing
array. One decode therefore returns strings. The captured upgrade exception shows `Access.get/3`
receiving a string such as `{"nightly_rate_cents":10000,"room_id":"source-room"}`.

Both checks stop before funding-history assertions. These migrations already sort durable
records by ID; the failures do not establish a misunderstanding of cash/credit interleaving.
Their candidate fixtures insert plain arrays of room maps into SQL, bypassing typed serialization.
Fixture and implementation agree with each other while disagreeing with the persisted product.
The faulty migration files remain byte-identical from M4 through M7.

### High 02 initially makes the same mistake, then repairs it

The decisive sequence is in high 02's M4 log:

1. `item_11` writes an outer-only decoder. An inherited persistence test first fails earlier
   because a pre-upgrade ledger assertion uses a table that does not yet exist.
2. `item_13` adjusts those assertions but retains typed `%Group{rooms: [...]}` insertion into
   the older database. The suite passes 59/60 tests. The remaining failure exposes the
   JSON-string argument to `Access.get/3`.
3. `item_16` adds an inner decode for string elements.
4. Only afterward, `item_17` adds dedicated M4 migration tests. The final suite passes 68
   tests, and both sealed upgrades pass on databases written through the actual M3 HTTP server.

The triggering fixture was inherited from M3, not invented in the new M4 test file. Subsequent
tests cover senior funding, commit order despite reversed event dates, credit provenance, settled
entitlements, and reruns. The private checks also exercise cancellation, payment reduction,
restart, and replay. The pass is historical operability, not just migration startup.

High 01 took a different fixture-repair path. After missing-column errors, it replaced
schema-backed insertion with raw SQL and plain JSON, removing serialization-sensitive coverage.
There is no evidence that it knowingly ignored the JSON-string crash: its modified test no
longer exposed one. The contrast is preserving useful inherited coverage, not cross-round learning.

### Low and medium provide useful controls

Both low samples use typed loading and pass the real upgrades. During final review, low 02 also
moves the backfill into migration-local schemas and allocation functions, avoiding dependence on
future changes to live application modules. Its manually seeded fixture is still no more realistic
than the failing fixtures; the implementation preserves the decoding boundary.

Medium 02 repeats the outer-only decoder and plain-object SQL fixture. Its tests address ordering
and restart but instantiate the wrong stored representation. It ends with 82 test declarations,
versus medium 01's 73, without improving that boundary.

High 02 also retains individual credit-consumption rows from M3; high 01 coalesces usage by
group/lot and must reconstruct more history later. That simplifies high 02's ordered backfill,
but does not explain high 01's earlier decoding crash. Early schema choices influence later
repair opportunities without determining the outcome by themselves.

## Cold Replay: Two Routes To A Pass

### Why the first round fails

All three first-round implementations store operation results as JSON, then restore keys with
`String.to_existing_atom/1`. M6 introduces `:starts_on` in a separate finance module; M7 adds
`:period_end_on`. First application loads that module, but exact replay bypasses it. On a cold
VM, a persisted field can name an atom that has not been loaded.

The historical checks expose precisely that order:

- **R4:** migration, inception balances, credit expiry, and shortfall assertions pass. After
  restart, the first request retries reporting start and returns HTTP 500.
- **R5:** close and historical preservation pass, including a 200-cent reduction posted on the
  first open day. After restart, the first batch operation retries close and fails.

Ordinary upgrade checks read a report before replay, masking the dependency. Candidate tests
also warmed the required state: low 01 restarted only the repository; medium 01's fresh-VM script
referenced finance during compilation; high 01's fresh-process tests read reports instead of
cold-replaying. Medium/high caught JSON key-order differences but missed the module-load issue.

The HTTP failure positions are retained in sealed reports; the original server exception stacks
were not retained. The atom diagnosis was reconstructed from source and isolated archived BEAM
checks for all six first-round M6/M7 snapshots: the key is absent after loading replay and present
after loading finance. These are not patched-candidate full-suite results. Unbounded conversion
of external strings into atoms is not an appropriate repair.

### What round two changes

**Low 02 removes the dependency.** From M3 it normalizes results through JSON and returns the
stored result directly on replay. There is no string-to-atom conversion at this boundary.
Later finance fields cannot introduce the earlier atom-loading failure.

**High 02 satisfies the dependency through organization.** It still uses
`String.to_existing_atom`, but reporting-start and period-close handlers construct their result
maps inside the same `Reservations` module that performs replay. Loading it makes both atoms
available before the first retry. This is a valid cold-start pass, not an evaluator warm-up.
It is less general than low's JSON-shaped approach: extracting those handlers later could
reintroduce the assumption unless serialization changes too.

**Medium 02 retains the failing arrangement.** Conversion remains in `Reservations`, while
finance result fields are defined elsewhere. Its repeated R4/R5 failures occur at the same cold
replay boundary, not at a different accounting assertion hidden behind the same total.

The two sweeps should not be credited as identical durability improvements. Low avoids the risky
conversion; high's organization makes it work for the current contract.

Isolated archived-BEAM probes of all six second-round M6/M7 snapshots confirm that loading
Reservations alone creates the relevant atoms for high, not for medium or low. No application,
database, or HTTP handler was started. Together with the sealed first-request results and source
control flow, this supports the mechanism; it is not a newly reproduced HTTP exception stack.

Candidate tests remain narrower than these outcomes. Low 02 restarts Repo within the same VM.
Medium 02's fresh-process test covers only M3 result kinds; its finance tests restart Repo, so
it never extends cold-process coverage to the new fields. High 02's finance subprocess test
references FinanceReporting and reads reports before close replay. Those tests alone cannot
exclude warm-up; its sealed cold-first-request passes and module-loading evidence do.

## What All Six Solve

All six clear hotel credit, signed late adjustments, liability revival after closed expiry,
double revival, cross-property chargeback, transfer-shortfall absorption, and reporting replay
purity. No Astra sample misses any of the five cross-domain Maintenance families.

Low 01's signed expiry adjustment is the difference between issued-minus-consumed-minus-revoked-
minus-absorbed movements and the change in liability at the **posting date**. It appends the
movement at that posting date, using the first open day for close-shifted operations, and schedules
future expiry only beyond it. The passing
implementations do not merely freeze old reports; they restore revived liability in the open period.

That is v6's dominant earlier semantic failure. Three related families often charge one conceptual
mistake three points. Astra clears all three in all six observations; its missing points instead
concentrate at serialization and process boundaries.

Passing these cases does not prove identical finance semantics everywhere. High 02 additionally
tests a backdated clawback of unused credit whose expiry is already closed, expecting equal and
opposite late revoked/expired movements at zero net liability. Low 02 and medium 02 instead
evaluate revocation eligibility at the post-close posting date; source inspection implies no
such pair for that shape. This is an unscored, source-derived difference, not an endpoint-
reproduced failure or a change to official results. It suggests a focused question for future
tests about preserving gross classifications when the net balance does not change.

## Comparison With Earlier GPT Systems

| Configuration | n | Core mean | Maintenance mean | Sweeps | Median cost | Mean model time |
|---|---:|---:|---:|---:|---:|---:|
| Astra low | 2 | 39.0 | 9.0 | 1/2 | $12.36 | 43.4 min |
| Astra medium | 2 | 38.0 | 7.0 | 0/2 | $14.95 | 55.7 min |
| Astra high | 2 | 38.5 | 8.5 | 1/2 | $18.45 | 78.1 min |
| Sol high, Codex | 5 | 38.8 | 9.6 | 4/5 | $22.37 | 89.8 min |
| Sol medium, Codex | 5 | 38.2 | 8.8 | 2/5 | $13.90 | 76.8 min |
| Terra xhigh, Codex | 5 | 36.6 | 7.0 | 0/5 | $9.96 | 91.3 min |
| Luna xhigh, Codex | 5 | 32.6 | 6.2 | 0/5 | $1.50 | 119.7 min |
| GPT-5.5 xhigh, Codex | 5 | 37.0 | 7.6 | 0/5 | $27.57 | 100.1 min |

Similar totals hide different weaknesses:

- **Sol-high/Codex:** one non-sweep omits revival compensation; four sweep. All five pass the
  historical families missed by Astra. Astra is not an unambiguous reliability improvement.
- **Sol-high/OpenCode run 3:** the same atom-restoration pattern fails at the same cold reporting-
  start and close retries. This is a recurring mechanism, not merely a shared family label.
- **Sol-medium/Codex run 2:** R4/R5 fail because structural comparison of `Date` structs rejects
  valid dates as earlier than inception. Same families, different cause.
- **Luna run 1 and Terra run 5:** M4 reconstructs cash before credit and loses interleaving.
  Failing Astra migrations crash before reaching that accounting question.
- **GPT-5.5 run 2:** M4 reverses `Enum.map_reduce`'s return components, then iterates the wrong
  structure. Legacy-data operability is a category, not one shared reasoning failure.

Baseline Luna fails revival in 5/5 runs, Terra in 5/5, GPT-5.5 in 4/5, and Sol medium in 2/5.
Astra's six passes are meaningful, but two samples per effort and a newer harness cannot establish
the size or generality of a model-generation improvement.

## Cost And Work Pattern

| Effort / sample | Uncached input | Cached input | Output, including reasoning | Reasoning subset | Input cost | Cache cost | Output cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Low 01 | 384,068 | 4,657,792 | 62,904 | 5,357 | $3.84 | $4.66 | $3.15 |
| Low 02 | 418,305 | 5,485,696 | 68,230 | 6,597 | $4.18 | $5.49 | $3.41 |
| Medium 01 | 495,533 | 7,001,472 | 89,373 | 11,160 | $4.96 | $7.00 | $4.47 |
| Medium 02 | 408,167 | 5,170,176 | 84,511 | 9,827 | $4.08 | $5.17 | $4.23 |
| High 01 | 541,173 | 7,684,864 | 126,489 | 24,563 | $5.41 | $7.68 | $6.32 |
| High 02 | 515,862 | 6,209,792 | 122,073 | 21,603 | $5.16 | $6.21 | $6.10 |

Costs use the [standard Astra API rates](https://developers.openai.com/api/docs/models/gpt-6-astra)
checked on 5 September: $10 uncached input, $1 cached input, and $50 output per million tokens.
Cached reads are a subset of input; reasoning is a subset of output. Neither is counted twice.
Cache-write counts were zero, and the largest request was 113,468 input tokens, below the 272K
long-context threshold. Seven final session counters per run reconcile exactly with CLI usage
summaries. These subscription runs are not additional per-run invoices. Startup probes are excluded.

The second round costs $44.03, versus $47.49 for the first; all six total $91.52.

- **Low:** cost rises 12.3%. M4 accounts for $1.36 of the $1.44 increase and ships a self-contained
  migration. This is a work-pattern association, not an isolated price for that change.
- **Medium:** cost falls 17.9%. Cached input falls by 1.83 million tokens, explaining $1.83 of
  the $2.95 saving. M7 alone is $1.72 cheaper. The score and defect mechanisms are unchanged.
- **High:** cost falls 10.0%, chiefly through 1.48 million fewer cached-input tokens. M1 and M4
  are $0.93 and $1.12 cheaper. It emits slightly less output and uses fewer completed command
  executions, 131 versus 148, but takes 2.4% longer in model-session time. Runtime is not a
  token-cost proxy, and a better result need not require a larger bill.

Astra is not cheaper per token than Sol; lower inference volume offsets the higher price here.
High's $18.45 median is below Sol high's $22.37 median but inside its $13.23-$25.58 range.
Low's $12.36 median and 39/9 mean make it promising. At these point estimates it dominates Sol
medium on both scores and cost; two samples cannot establish reliable superiority. Sol high
retains the better replicated Maintenance result, 9.6 versus low's 9.0.

Higher effort changes work in both rounds: low emits 63K-68K output tokens and ends with 54-55 test
declarations; high emits 122K-126K and ends with 108-111. Production stays at 1,979-2,242 lines.
High 02 succeeds with fewer declared tests than high 01; medium 02 fails with more than medium 01.
The decisive M4 difference is the fidelity of one inherited fixture, not the surrounding test count.

## Implications For V6 And V7

**V6 still catches real errors, but these results do not restore broad frontier headroom.**
Two Astra samples sweep, all six solve the formerly dominant accounting problem, and the other
four miss two compact boundary defects. Calling v6 simply saturated would erase useful reliability
evidence; treating those residual misses as broad next-generation headroom would overstate it.

The concrete lessons are:

1. Generate legacy data through the actual preceding application and continue using it after
   upgrade. Fixtures can share an implementation's mistaken assumptions about stored formats.
2. Exercise genuinely cold processes and vary the first legal request. Reading a report first
   can accidentally turn cold durability into a warm-module check.
3. Make business evolution invalidate earlier assumptions across components. An M3 decoder became
   unsafe when M6 introduced fields in another module, without needing another product.
4. Preserve meaningful repair opportunities. High 02 shows an inherited test exposing a later
   regression; high 01 shows how repairing a test can discard what it protected. Measure the
   resulting behavior without prescribing a candidate test suite.
5. Distinguish affected families from root causes, and ship-time failures from terminal-code
   retests. A startup crash can block several historical assertions without proving all the
   downstream business semantics wrong.

The family matrix still contains 30 distinct vectors and has centered rank 27. The new samples
repeat existing patterns rather than adding an independent source of difficulty. V7 needs
separation across distinct behaviors, including semantic business evolution and legacy operability,
not more atom-loading traps, duplicate points, or milestones added merely to increase length.

## Evidence Map

The public dataset preserves scores, usage, execution metadata, and hashes. Source and logs
remain with sealed runs. Source paths below refer to the indicated milestone snapshot.

| Evidence | Run artifact |
|---|---|
| Failing room decoders | Both mediums and high 01, M4 `priv/repo/migrations/20260905000003_add_room_accounting.exs` |
| Wrong fixtures | Medium 01 M4 `test/group_stay/room_accounting_upgrade_test.exs`; medium 02 M4 `test/group_stay/persistence_test.exs` |
| High 01 fixture rewrite | `logs/agent-4.jsonl`, completed `item_13` |
| High 02 crash and repair | `logs/agent-4.jsonl`, completed `item_13`, `item_16`; M3/M4 `test/group_stay/durable_operations_persistence_test.exs` |
| Typed decoding | Low 01 M4 `lib/group_stay/accounting.ex`; low 02 M4 migration-local `GroupRow` |
| Failing replay conversion | First-round low/medium and medium 02 M7 `lib/group_stay/reservations.ex`; high 01 M7 `lib/group_stay/operations.ex` |
| JSON-shaped replay | Low 02 M3/M7 `lib/group_stay/reservations.ex`, `apply_operation/1` |
| Co-located result literals | High 02 M6/M7 `lib/group_stay/reservations.ex`, `restore_result/1`, `apply_operation/1` |
| Cold request order | Frozen `evaluation/system_checks.py`, R4 `projection-start`, R5 `close-history-close` |
| Signed revival calculation | Low 01 M7 `lib/group_stay/finance.ex`, `capture/4`, `schedule/3` |
| Verification work | Both rounds' medium/high `logs/agent-7.jsonl` and M7 durability tests |
