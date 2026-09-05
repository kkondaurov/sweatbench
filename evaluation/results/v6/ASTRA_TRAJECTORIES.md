# GPT-6 Astra on Sweat Bench v6

5 September 2026. Three completed trajectories, one each at low, medium, and high reasoning
effort, using Codex CLI 0.153.4 and the unchanged seven-milestone v6 benchmark.

## Results

| Effort | Core /39 | Maintenance /10 | Scenarios /94 | API-equivalent cost | Model time | Production LOC | Test LOC | Test declarations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Low | 39 | 8 | 92 | $11.64 | 41.7 min | 1,979 | 2,311 | 55 |
| Medium | 38 | 7 | 90 | $16.43 | 57.4 min | 2,242 | 3,447 | 73 |
| High | 38 | 7 | 90 | $19.42 | 77.2 min | 2,230 | 4,903 | 111 |

The run IDs are `v6-astra-low-01`, `v6-astra-medium-01`, and `v6-astra-high-01` in
[the dataset](accepted-runs.json). All seven milestones completed, all integrity checks passed,
and no candidate subagents or descendant model sessions were recorded. Each run used ordinary
handoff prompts and endogenous tests, without a delegation intervention. Each container had two
CPUs and 4 GiB of memory; the three runs ran concurrently. Model time includes tools and candidate
tests, but excludes evaluator and inter-milestone time. Total elapsed times were 43.0, 58.5, and
78.6 minutes respectively.

**The residual errors are narrow but real.** All three implementations pass v6's difficult
late-credit-revival and cross-domain composition cases. They share one cold-replay defect.
Medium and high also share a migration decoding defect. The ten lost family-points across these
three trajectories represent repeated instances of two mechanisms, not ten distinct mistakes.

This is not evidence that low effort is generally better. Each effort has one sample, and the
newer Codex version differs from the earlier GPT cohort. It is evidence about these three
completed systems, including their cost and the concrete defects they left behind.

## What Failed

| Failure mechanism | Low | Medium | High | Scored families affected |
|---|---|---|---|---|
| Raw migration misreads the preceding application's nested JSON storage | Pass | Fail | Fail | M4 migration and R2 room-history upgrade |
| Cold replay assumes finance result-key atoms are already loaded | Fail | Fail | Fail | R4 projection-history and R5 close-history upgrades |

### A migration tested against the wrong historical representation

At milestone 4, medium and high read the old `groups.rooms` column through raw SQL. They decode
the outer JSON and treat each element as a room map. The actual milestone-3 writer stored an array
whose elements are themselves JSON strings. Accessing `room["nightly_rate_cents"]` therefore raises
`FunctionClauseError`, before either upgrade check reaches its funding-history assertions.

The migration needs a decoder compatible with the actual preceding writer, not merely the
application-level room structure. Both candidates already order funding events by durable ID.
These failed runs do not establish that they misunderstood commit order: that logic was never
reached by the failing checks.

Both models wrote populated migration tests. Their fixtures inserted plain JSON arrays of room
maps directly into SQL, bypassing the preceding application's typed serialization. The fixture
and implementation agreed with each other while disagreeing with the persisted product.

High's trajectory makes the problem particularly visible. Its stated intention was a migration
with "no dependency on evolving application schemas." When a historical test encountered
missing-column errors, it replaced schema-backed insertion with raw SQL plus plain JSON. That
repair removed the schema incompatibility but also removed the realistic serialization path.
Later review improved credit-lot provenance, while leaving the decoder unchanged. Medium also
repaired migration handling without revisiting the stored room representation.

Low avoided the crash by reading groups through Ecto's typed loading path. Its manually seeded
fixture was not more realistic than the others; its implementation happened to preserve the
correct boundary. This is not a recommendation to make historical migrations depend on mutable
current schemas. A version-specific decoder verified against data from the old executable would
also satisfy the contract.

Medium and high reread the migration during later milestones, but its bytes remained unchanged
through milestone 7. The models received no private-evaluation feedback. Their passing candidate
tests therefore continued to provide misleading reassurance about this compatibility boundary.

### Replay that works only after the finance module has loaded

All three implementations introduced the same pattern while implementing durable operations at
milestone 3: store result fields as JSON, then convert string keys back to atoms on replay with
`String.to_existing_atom/1`. The assumption is that server-defined fields must already exist as
atoms in the current VM.

Milestone 6 introduces `:starts_on` in a separate finance module; milestone 7 introduces
`:period_end_on`. First application executes that module, loading its atoms. Exact replay bypasses
the business handler. On a freshly started server, replay can therefore encounter a persisted
field whose atom has not been loaded and raise instead of returning the durable result.

The two historical scenarios expose precisely that request order:

- **R4:** historical migration, inception balances, credit expiry, and shortfall assertions pass.
  The server restarts, and its first request retries the saved reporting-start operation. It
  returns HTTP 500 before the post-restart report comparisons.
- **R5:** closing and historical-report preservation pass, as does the 200-cent reduction posted
  on the first open day. After restart, the first operation in the batch retries the saved close.
  That replay fails before the remaining batch operations can be evaluated.

The ordinary finance-upgrade checks read a report before replaying. That loads the finance module
and masks the dependency. They pass on the same implementations.

Candidate verification masked it in three different ways:

- **Low** restarted only the repository process, keeping the VM and its atom table alive.
- **Medium** launched a fresh VM, but its test script directly referenced
  `FinanceReporting.daily`. Compiling that script loaded the finance module before the nominally
  earlier replay executed.
- **High** tested fresh-process report reads, while replay checks ran in the already warm VM.

Medium and high did catch and repair JSON key-order differences across process restarts. Their
tests were substantive, and higher effort produced more coverage. The missing question was
whether the *first request of a truly cold deployment* could replay an operation without warming
its business module first.

The HTTP failures and their positions are recorded in the sealed evaluations. Their original
server exception stacks were not retained by the evaluator. The specific atom-loading diagnosis
was reconstructed from source and isolated checks against archived BEAM files for all six M6/M7
snapshots: loading the replay modules leaves the relevant key absent; loading the finance module
makes it available. This is not a patched-candidate full-suite result. A repair should remove the
implicit module-load dependency, for example by keeping JSON-shaped result fields or using an
explicit bounded key mapping. Unbounded conversion of external strings into atoms is not the fix.

## What They Solved

The passing accounting behavior matters as much as the missing points. All three clear the
hotel-credit family, signed late adjustments, liability revival after closed expiry, double
revival, cross-property chargeback, transfer-shortfall absorption, and reporting replay purity.

Low's finance implementation derives the signed expiry adjustment from the liability change at
the **posting date**:

```text
expiry adjustment = issued - consumed - revoked - absorbed
                    - (liability after - liability before)
```

It appends that movement on the first open day and schedules future expiry only beyond the
posting date. Medium and high likewise build durable reporting journals and explicitly test
backdated credit application after a closed expiry. They do not merely freeze the old report;
they account for the restored liability in the open period.

The distinction is important because v6's dominant earlier failure was precisely that missing
compensation. Its three related families often charged one conceptual mistake three points.
Astra clears all three in all three observations. The reported Maintenance deficits instead arise
at persistence and process boundaries.

## Comparison With Earlier GPT Systems

| Configuration | n | Core mean | Maintenance mean | Median cost | Mean model time |
|---|---:|---:|---:|---:|---:|
| Astra low | 1 | 39.0 | 8.0 | $11.64 | 41.7 min |
| Astra medium | 1 | 38.0 | 7.0 | $16.43 | 57.4 min |
| Astra high | 1 | 38.0 | 7.0 | $19.42 | 77.2 min |
| Sol high, Codex | 5 | 38.8 | 9.6 | $22.37 | 89.8 min |
| Sol medium, Codex | 5 | 38.2 | 8.8 | $13.90 | 76.8 min |
| Terra xhigh, Codex | 5 | 36.6 | 7.0 | $9.96 | 91.3 min |
| Luna xhigh, Codex | 5 | 32.6 | 6.2 | $1.50 | 119.7 min |
| GPT-5.5 xhigh, Codex | 5 | 37.0 | 7.6 | $27.57 | 100.1 min |

Similar totals hide different weaknesses:

- The older **Sol-high/Codex** failure omitted effective revival compensation; four other runs
  swept. All five passed the historical families missed here. Astra is not an unambiguous
  reliability improvement over that cohort.
- **Sol-high/OpenCode run 3** has the same `String.to_existing_atom` restoration pattern and fails
  at the same cold reporting-start and close retries. This is a genuinely recurring mechanism,
  not merely a shared family label.
- **Sol-medium/Codex run 2** fails R4/R5 for a different reason: structural comparison of `Date`
  structs rejects valid reporting dates as earlier than inception.
- The inspected **Luna run 1 and Terra run 5** M4 migrations lose interleaving by reconstructing
  cash before credit. Astra medium/high instead crash decoding rooms before funding assertions.
- **GPT-5.5 run 2** also crashes in M4 migration, but reverses the return components of
  `Enum.map_reduce`, then iterates the wrong structure. The common category is legacy-data
  operability, not identical reasoning about provenance.

Baseline Luna fails the revival family in 5/5 runs, Terra in 5/5, GPT-5.5 in 4/5, and Sol medium
in 2/5. Astra's three passes are a meaningful contrast, but one observation per effort and a newer
harness cannot establish the size or generality of a model-generation improvement.

## Cost And Work Pattern

| Effort | Uncached input | Cached input | Output, including reasoning | Reasoning subset | Input cost | Cache cost | Output cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Low | 384,068 | 4,657,792 | 62,904 | 5,357 | $3.84 | $4.66 | $3.15 |
| Medium | 495,533 | 7,001,472 | 89,373 | 11,160 | $4.96 | $7.00 | $4.47 |
| High | 541,173 | 7,684,864 | 126,489 | 24,563 | $5.41 | $7.68 | $6.32 |

Costs use the [standard Astra API rates](https://developers.openai.com/api/docs/models/gpt-6-astra)
checked on 5 September: $10 uncached input, $1 cached input, and $50 output per million tokens.
Cached reads are a subset of total input; reasoning is a subset of output. Neither is counted
twice. Cache-write counts were zero, and the largest individual prompt was 113,468 tokens, below
the 272K long-context threshold. The seven final session counters for each run reconcile exactly
with the corresponding CLI usage summaries. These are subscription runs, so the estimates are
not additional invoices. Failed startup probes are not part of the scored trajectory costs.

Astra is not cheaper per token than Sol. Its lower inference volume offsets that higher price in
these observations; elapsed time itself is not a billing input. High's $19.42 is below Sol high's $22.37 median,
but inside Sol high's observed $13.23-$25.58 range; it is not a demonstrated cost breakthrough.
Low's $11.64 is a more interesting cost-quality point, albeit with weaker historical reliability
than the Sol-high sample. Aggregate cost for the three completed runs is $47.49.

Higher effort changes the work substantially: recorded reasoning grows from 5.4K to 24.6K tokens,
output roughly doubles, and test declarations grow from 55 to 111. Medium and high also split
production code more: the largest file accounts for 25% and 23%, versus low's 43%. Yet they retain
the same cold-replay assumption, and both add the same migration decoder error. More extensive
review cannot compensate for tests that instantiate the same mistaken boundary assumptions.

## What This Means For V6 And V7

**V6 still catches real errors, but these results do not restore broad frontier headroom.** The
new observations leave its observed family-outcome matrix at 30 distinct vectors and rank 27.
Astra passes the formerly dominant semantic cliff while losing points to two compact operational
defects. Calling it simply saturated would erase useful evidence; calling the lack of sweeps proof
of a sufficiently difficult next-generation benchmark would overstate it.

The useful design lessons are specific:

1. Keep real product history. Generate legacy data through the actual preceding application,
   then continue using it after the upgrade. Hand-built fixtures can share the candidate's error.
2. Exercise genuinely cold processes and vary the first legal request. A report read before a
   retry can accidentally turn a durability check into a warm-cache check.
3. Make later business changes invalidate earlier assumptions across components. Here a result
   decoder that was introduced at M3 became unsafe when M6 added new result kinds in a separate
   module. This is cumulative evolution pressure without an extra product or many endpoints.
4. Separate root-cause attribution from affected score families. Two historical scenarios may be
   valuable coverage but still represent one plausible repair. A startup crash does not prove
   that all downstream historical semantics are wrong.
5. Measure genuine later repair. V6 carries one-time historical system-check outcomes into its
   final score; it does not rerun every old database upgrade against the last implementation.
   Preserve ship-time evidence and distinguish it from terminal-code re-evaluation.

These observations support deeper interactions and assumption changes in the existing v7 product
arc. They do not justify designing a successor around obscure atom-loading traps, adding more
copies of the same failure, or assuming that increasing milestone count creates useful headroom.
The next calibration needs separation across distinct, interpretable behaviors, including
semantic business evolution as well as legacy operability. Astra's non-sweeps alone are not that
calibration evidence.

## Evidence Map

The public dataset preserves per-milestone scores, token counts, hashes, and execution metadata.
Detailed source and runtime evidence is retained with each sealed run, not exposed as raw model
sessions. The key locations within those run artifacts are:

| Evidence | Run artifact |
|---|---|
| M4 raw room decoder | Medium/high `snapshots/milestone-4/priv/repo/migrations/20260905000003_add_room_accounting.exs` |
| Mis-shaped upgrade fixture | Medium `snapshots/milestone-4/test/group_stay/room_accounting_upgrade_test.exs` |
| High's fixture rewrite and final migration review | High `logs/agent-4.jsonl` |
| Typed loading in low's backfill | Low `snapshots/milestone-4/lib/group_stay/accounting.ex` |
| Cold replay conversion | Low/medium `snapshots/milestone-7/lib/group_stay/reservations.ex`; high `lib/group_stay/operations.ex` |
| Cold historical retry boundaries | Frozen `evaluation/system_checks.py`, R4 `projection-start` and R5 `close-history-close` requests |
| Signed revival implementation | Low `snapshots/milestone-7/lib/group_stay/finance.ex`, `capture/4` and `schedule/3` |
| Fresh-process tests and serialization repairs | Medium/high `logs/agent-7.jsonl` and milestone-7 durability tests |
