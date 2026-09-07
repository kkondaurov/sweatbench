# Asking for Readable Elixir

7 September 2026. Six trajectories on the frozen Sweat Bench v6 task:
Astra at low, medium, high and X-High, and Sol at medium and high.
This is an instruction experiment,
not a new scoring version and not an addition to the baseline Models cohort.

## The Experiment

In v6, a coding agent builds GroupStay, a hotel-deposit application, through seven
successive requests. Each new version must preserve earlier behavior and data.
The earlier Astra runs produced compact implementations, while both Astra and
Sol often concentrated much of the application in a few large modules. Several
Astra runs failed when a new version opened an old database or when the server
restarted. Sol more often struggled with financial events reported after an
accounting period had closed.

The experiment asks whether an instruction about maintainability changes how
the agents organize the application and handle these obligations. It requests
clearer code without naming the earlier failures. The
following instruction was appended to the normal request at every milestone:

> Produce idiomatic, well-structured Elixir/Phoenix code that a human maintainer would find clear and a pleasure to read. Organize the application into cohesive modules with clear responsibilities, choose descriptive names, and document important domain concepts and design decisions. Favor straightforward implementations and useful abstractions over either terse code or unnecessary layers. Maintain this standard as the application evolves.

Each milestone started a fresh model session with the candidate's own repository
and tests. The agent received no baseline implementations, failure analysis,
future requirements or private evaluation feedback. Inspection of all 42 session
records confirmed that the instruction was present. No candidate was repaired
after evaluation, and none of the six attempts was replaced or excluded.

The six configurations and instruction were recorded before the pilot started.
Every completed run in this pilot is included, with one sample per model and effort.

## Results

All four Astra runs and Sol High earned all 39 Core and 10 Maintenance points.
Sol Medium earned 38 Core and 8 Maintenance points, with two failing scenarios
at milestone 7. Those two scenarios belong to three scoring families. The five
sweeps have 94 passed scenarios in both delivery-time and final totals; Sol
Medium has 92 in both. All 42 milestones passed their integrity audits. These
totals include historical system checks at their designated milestones, not 94
new tests of the final code.

| Configuration | Earlier sweeps | Core | Maintenance | API-equivalent cost | Agent runtime | Production lines | Test lines |
|---|---:|---:|---:|---:|---:|---:|---:|
| Astra Low | 1 of 3 | 39 | 10 | $15.38 | 56m | 2,415 | 2,863 |
| Astra Medium | 0 of 3 | 39 | 10 | $16.78 | 1h 04m | 2,632 | 3,474 |
| Astra High | 1 of 3 | 39 | 10 | $21.90 | 1h 27m | 2,861 | 4,675 |
| Astra X-High | 3 of 3 | 39 | 10 | $32.84 | 2h 07m | 2,969 | 6,323 |
| Sol Medium | 2 of 5 | 38 | 8 | $12.22 | 1h 43m | 3,682 | 1,957 |
| Sol High | 4 of 5 | 39 | 10 | $15.88 | 2h 16m | 4,761 | 2,784 |

Core has 39 possible points and Maintenance has 10. Each instruction row is one
run, not an average. A sweep earns all points in both tracks.

Each intervention Astra run cost more and produced more production code than any of its three
same-effort controls. Relative to the earlier medians, production code grew by
17%, 21%, 29% and 19%; cost grew by 25%, 10%, 15% and 14%. Test code did not grow
uniformly: the new high run had fewer test lines than any earlier high run.
X-High completed faster than its earlier average, but within its earlier runtime
range. The other three Astra efforts took longer than their earlier ranges.

Sol does not follow the same cost pattern. Its medium and high runs cost 12% and
29% less than their respective historical medians, while production code is 9%
and 30% larger. Medium has fewer test lines than any of its five controls; high
is close to its earlier median. Both take longer than their earlier runtime
ranges. Sol's CLI version and execution environment changed alongside the
instruction, so these differences cannot be assigned to the prompt alone.

The [dashboard comparison](https://kkondaurov.github.io/sweatbench/#intervention)
shows the earlier scores and observed ranges next to each new run. Baseline data
remain in [accepted-runs.json](accepted-runs.json); the new records are in
[intervention-runs.json](intervention-runs.json).

## What Changed in the Code

The intervention Astra implementations give more responsibilities distinct names and owners.
Low separates booking policy, payment history and the reconstruction of room
funding. Medium separates the capture of financial changes from report queries.
High divides finance into Position, Journal and Report modules. X-High separates
request addressing and validation order from the domain operation itself.
These divisions remain recognizable as later milestones add transfers and close.

The documentation explains operational decisions, not just function names.
Low's [Operations module][low-operations] describes the transaction shared by a
request, its business effects and its saved response. X-High's
[Operation parser][xhigh-operation] explains why a stale revision must not be
masked by a later validation error. High's [Finance module][high-finance]
introduces inception, expiry and report publication before presenting the code.

Across the intervention Astra runs, the largest production file is 288-403 lines; across the
twelve controls it is 506-843. The new totals include 33, 33, 48 and 47 production
files, including migrations, compared with 22-25, 23-26, 26-29 and 32-40 in the
corresponding controls. These counts locate a structural change. The stronger
reason to call it more readable is that operations such as correcting a payment
or recording a financial movement now have explicit responsibilities and domain
names, supported by comments about the rules they preserve.

There are tradeoffs. Low's migration delegates to current application schemas
and helpers, which future changes could make unsuitable for an old migration.
High keeps a 1,456-line persistence test combining several kinds of checks.
X-High has more focused test files, but its reporting hooks are spread across
domain writers, and its daily report loads historical entries into memory.
Those are concrete maintenance considerations, not observed scored failures or
measurements of how these applications would scale in production.

Sol's response is less uniform. High has 48 production files and a largest file
of 875 lines, compared with 33-42 files and largest files of 1,480-2,255 lines in
the five earlier high runs. Medium has 38 files, but its `Deposits` context is
1,802 lines: almost half of its 3,682 production lines. Its earlier medium runs
had largest files of 1,378-2,154 lines. More files and more code did not produce
the same redistribution of responsibilities in every configuration.

## Astra: Reading Old Room Data

Milestone 4 introduces accounting for individual rooms. A migration must read
existing bookings and divide their funding among rooms without losing payment
history. Four baseline runs failed before reaching that accounting: low 3,
medium 1 and 2, and high 1.

Their older applications stored rooms with Ecto's `{:array, :map}` type. With the
retained SQLite adapter, the database contained an array of JSON-encoded strings.
The migration decoded the outer array once, then tried to read each string as a
room object. Some candidate tests wrote plain room objects directly into SQL;
that made the fixture agree with the migration but not with the old writer.
See [baseline medium 1's writer][baseline-room-writer] and
[migration][baseline-room-migration].

The four new runs take three routes around the mismatch:

| Effort | What the accepted implementation does |
|---|---|
| Low | Keeps array/map storage, but uses Ecto to load the records in [Backfill][low-backfill]. The typed reader handles the representation written by the schema. |
| Medium | Uses [embedded room records][medium-rooms]. The historical JSON contains room objects, which match the migration's single decode. |
| High | Also uses [embedded rooms][high-rooms], beginning in milestone 1. Its raw-SQL migration is correct for that stored representation. |
| X-High | Uses a [separate rooms table][xhigh-rooms] from milestone 1. Its migration reads room rows in stored order; there is no room JSON decoder. |

No recorded nested-room decoding failure prompted these new choices. They were
already in place before the relevant upgrade. The new migration tests still
construct old-schema data rather than execute the old application. Low's fixture
uses typed Ecto insertion; the others construct data matching their own storage.
The private evaluator supplies the stronger historical check: it writes data
through the actual earlier application, then upgrades and exercises the result.
All four pass both scored room-upgrade scenarios.

These are explanations of why the submitted implementations pass, not patches
that teach them to import another candidate's database. Each run is responsible
for its own earlier versions. Successful controls had already found alternatives:
baseline low 2 used typed loading with migration-local schemas, and baseline
X-High 2 used embedded rooms. Baseline high 2 kept array/map storage, but its
typed fixture exposed the decoding mistake and prompted a repair.

## Astra: Returning the Same Answer After Restart

A partner may retry a payment or reporting request. The application must return
the saved original answer without performing the business operation twice,
including after a server restart. Six baseline runs failed at that boundary:
low 1, medium 1-3, and high 1 and 3.

Those implementations restored JSON response keys with `String.to_existing_atom`.
The needed finance-key atoms sometimes existed only after the finance module
loaded. A normal test that first created a report could therefore pass, while
retrying a saved reporting request immediately after startup could crash.
Elixir's [String documentation](https://elixir.hexdocs.pm/String.html#to_existing_atom/1)
describes the module-loading dependency; [Jason's decoding options](https://jason.hexdocs.pm/Jason.html#decode/2)
distinguish string keys from existing-atom conversion.

**Low and X-High keep responses JSON-shaped.** They normalize the first response
to JSON, store it, and return the stored value directly on a repeated request.
There is no need to rebuild its keys as atoms. Adding a finance field therefore
does not make replay depend on loading a finance module. The relevant code is in
[low Operations][low-operations] and [X-High Operations][xhigh-operations].

**Medium and high own the response-key vocabulary in the decoder.** Their fixed
maps contain the permitted atom literals, including later finance fields. The
decoder can load its own required keys without calling finance first. Medium's
milestone-3 transcript initially contains the old existing-atom conversion, then
replaces it with this explicit map before handoff. No recorded failure triggered
that edit. Its [accepted decoder][medium-decoder] retains the approach through
milestone 7.

**High catches a real omission through an ordinary test.** At milestone 6, the
new reporting test retries an inception request. The CLI transcript records
13 of 14 focused tests passing; the remaining test raises
`KeyError: key "starts_on" not found` in `Record.original_result/1`. The agent
adds `starts_on` to the [decoder's key and date lists][high-decoder], keeps the
[exact-response retry assertion][high-retry-test], and later passes the full
110-test suite. This is not a caught cold-start atom exception. It is an example
of an explicit response contract making a missing field fail even in a running,
already-loaded application. At milestone 7 it adds `period_end_on` as well.

The explicit maps still require upkeep: a future field must be added or decoding
will reject it. Returning JSON directly avoids that particular registry. Both
approaches have passing baseline precedents: low 2 already returned JSON directly,
and X-High 3 already used an explicit map, with a fallback for unknown fields.

## Astra: What the Tests Cover

Low and medium's finance-durability tests restart Repo, the database connection
pool, inside the same Elixir VM. High has a genuine subprocess test for its
earlier operation types, but its finance and close tests also restart the pool.
Those tests exercise persisted data but do not reproduce a fresh VM's atom table.

X-High extends its [subprocess test][xhigh-restart] through report inception,
period close, later corrections and another close. It really starts independent
Elixir applications against the same database. Its helper also references finance
code, however, so request order alone does not establish that the module is still
unloaded. None of these candidate-test observations replaces the private checks:
the evaluator independently restarts a server and retries the saved reporting
requests before reading a report. All four implementations pass.

This is not uniformly stronger testing than before. Some baseline X-High tests
actually exposed and repaired the cold-start bug. The new low and medium runs
pass with narrower restart tests because their response representation avoids
the dependency. Better representation and better tests are distinct advantages.

### A Further X-High Check

The new X-High tests also cover a distinction raised by the earlier source
review. When a backdated chargeback removes unused credit whose expiry is already
in a closed report, the next open period must record both the credit revocation
and an offsetting expiry reversal. Omitting both leaves the same net balance but
loses the explanation of what happened.

The [X-High restart scenario][xhigh-revocation] asserts both entries and unchanged
closed reports. High's tests cover related reversals, but not this exact pair.
Its source applies the closed-period date adjustment before classifying credit
revocation, which suggests it could omit both entries in this case. That is a
source-review prediction, not a newly executed failure: this audit did not run
the additional scenario against high. It does not change either published score.

## Sol: How the Application Evolved

Both Sol runs start with rooms in a separate database table and later return
saved operation responses as JSON maps. They avoid the two recurring Astra
defects without needing either the nested-room decoder or a response-key atom
registry. Both pass all eleven historical upgrade and restart checks, including
the checks that retry saved reporting requests immediately after startup.
Their differences concern how the business logic grows and how the final
version handles a transaction that arrives after its accounting period closes.

The seven trajectories show substantial testing and self-correction in both
runs. They also show why passing candidate tests alone did not predict the
final result. The counts below are the agent's own tests, not evaluator cases.

| Milestone | Sol Medium | Sol High |
|---|---|---|
| 1: bookings and deposits | Starts with ordered room rows and a 427-line Deposits context. Review corrects validation order; a small-value test checks per-room rounding. Ends with 14 tests. | Starts with ordered room rows and a 380-line largest module. SQLite rejects an unsupported constraint operation, which the agent removes. Ends with 18 tests. |
| 2: cancellation and credit | A refund test exposes structural Date comparison. The agent switches to chronological comparison and checks an upgrade with populated old-schema data. Ends with 20 tests. | Introduces policy history, credit lots and allocations. Checks an old-schema cash booking after upgrade. Ends with 28 tests. |
| 3: durable requests | Failed tests expose a nested-transaction rollback that prevents saving rejected requests. A savepoint repair lets the rejection record commit while undoing partial business changes. Ends with 26 tests. | Encounters the same transaction problem and repairs it with an explicit savepoint. Tests failure while saving a response and manually checks persistence across processes. Ends with 37 tests. |
| 4: room accounting | Expands Deposits to 1,275 lines. A populated migration fails because raw queries run before queued schema changes; explicit flushes fix the execution order. Ends with 30 tests. | Builds a dedicated backfill for old funding history. A manual old-schema example checks that older cash is allocated before later recorded payments. Ends with 44 tests. |
| 5: transfers | Adds payment-settlement provenance, but keeps transfer behavior in Deposits, now 1,623 lines. Ends with 36 tests. | Extracts DepositTransfer from RoomAccounting during review. Ends with 51 tests. |
| 6: daily reports | Introduces FinanceReporting. Tests expose a return-value mismatch; subsequent review corrects another Date comparison. Ends with 43 tests. | Separates capturing financial changes from querying reports. Review corrects a Date comparison and adds date coverage. Ends with 55 tests. |
| 7: period close | Adds stored closed reports and explicit posting dates. All 47 tests pass, but none applies existing credit after a closed expiry. Two private scenarios fail. | Review after 59 passing tests identifies the closed-expiry case. The agent adds a reconciliation and targeted test together. All 60 tests and all scored families pass. |

### Transaction and Migration Repairs

Durable requests must save the result of a rejected operation as well as a
successful one. Both runs initially let a rejection roll back the transaction
that was supposed to save its answer. Their repairs separate two obligations:
undo partial business effects, but commit the rejection record so a retry gets
the same answer. The accepted [Medium transaction helper][sol-medium-transaction]
and [High operation coordinator][sol-high-operations] use explicit SQL
savepoints within the enclosing transaction. These were repairs prompted by
failing tests, not merely documentation changes.

Medium's milestone-4 migration exposed a different Elixir/Ecto integration
issue. The migration queued schema changes, then immediately queried a column
that had not yet been created. An empty-database check passed; a populated
old-schema fixture failed with `no such column: deposit_due_cents`. The agent
added [flush boundaries][sol-medium-migration] before those reads and before
reconstruction used queued backfill writes. The repeated check then produced
the expected ordering of legacy cash, later cash and credit. The private
upgrade checks also passed.

These trajectories do not show agents that simply avoided all language or
framework mistakes. They show several mistakes discovered and corrected during
the run. Medium fixed a Date comparison after a cancellation test failed and
another during reporting review; High also corrected them during review.
The readability instruction did not make
those details automatic.

### Different Degrees of Decomposition

High's [DepositTransfer][sol-high-transfer] and [Report][sol-high-report] were
extracted during milestones 5 and 6, respectively. They give transfer provenance
and report calculation identifiable homes rather than adding both to an
ever-growing command handler. Module documentation explains such rules as
keeping the original payment identity when funding moves between groups.
Its final largest file is still an 875-line operation coordinator, but that is
substantially smaller than the 1,480-2,255-line largest files in its controls.

Medium's [Deposits context][sol-medium-context] grows from 427 to 1,802 lines.
It contains reads, request dispatch, validation, payments, transfers, credit
allocation, settlement, reporting calls and transaction machinery. Its named
helpers and documentation are useful, and the separate reporting context owns
real behavior. The [CashSettlement schema][sol-medium-settlement] also preserves
an important distinction between where a payment originated and where it was
settled. But most business responsibilities remain together. The 38-file total
includes many small schemas; it does not mean the behavior has been divided
into 38 cohesive parts.

The designs have maintenance tradeoffs. Medium's large migration is
self-contained, so it does not depend on future versions of application
schemas, but it duplicates some funding-reconstruction logic. High's migration
calls an application backfill helper that later changes could affect. High's
reporting also scans historical state and reconstructs closed reports from
retained inputs. Neither the benchmark nor this review measures production
scale, and future changes to that calculation would need to preserve the old
reports' meaning.

## Sol: Credit After a Closed Expiry

GroupStay issues hotel credit when some bookings are cancelled. Credit remains
usable for a limited period; when unused credit expires, the finance report
reduces the hotel's outstanding credit liability. Closing a period freezes its
reports. A later request can still describe a transaction that happened before
the credit expired. The application must use that transaction date to decide
eligibility, while putting the reporting effect in the first open period.

This creates a specific obligation: if a closed report has already recorded
the expiry, applying the credit must reverse the relevant amount of that expiry
in the open period. The old report stays unchanged. The reversal restores
liability; it is not a second issuance of credit. If a later cancellation
consumes that credit, the report must retain both the restoration and the
consumption even though their net effect is zero.

### Medium Drops the Required Entry

Medium correctly accepts the old-dated application, assigns the credit and
keeps the closed report unchanged. Its [allocation code][sol-medium-allocation]
then asks the reporting helper to reduce the scheduled expiry. The helper's
[documented responsibility][sol-medium-expiry] is changing a *future* expiry.
If the posting date is later than the expiry, it simply returns `:ok` and
writes nothing. That branch was adequate for changing a still-open schedule,
but not for reversing an expiry that had already been published.

The two failed cases reveal the same missing entry:

| Case | What already worked | First failed assertion | Lost families |
|---|---|---|---|
| Apply 300 cents using a pre-expiry transaction date after closing the expiry period | The request succeeds and the closed report remains unchanged. | The first open report shows zero closing liability instead of 300 cents. | Core late-adjustment posting and Maintenance credit restoration |
| Apply 600 cents the same way, then consume it through a non-refundable cancellation | Ordinary consumption is correctly recorded as 600 cents. | The late-adjustment section has zero expired credit instead of negative 600 cents. | Maintenance restoration followed by consumption |

The first case contributes to two families, and the second contributes to one.
Their three lost points therefore do not describe three independent bugs.

To test that explanation, the audit reproduced both failures against an
unchanged disposable copy, using the original private HTTP tests without
changing their assertions. It then changed only the no-op branch in
`adjust_scheduled_expiry`:

```diff
     else
-      :ok
+      if delta < 0 and late_adjustment?(posting) do
+        record_credit(posting, "expired", delta)
+      else
+        :ok
+      end
     end
```

All ten milestone-7 HTTP cases then passed, including all later assertions in
the two formerly failing cases. This supports the missing-entry explanation
for the observed failures. It is not a full requalification of the modified
application: earlier upgrades, restarts and the complete test suite were not
rerun against that edit. The accepted source and its 38 Core, 8 Maintenance
score are unchanged.

Medium's [period-close tests][sol-medium-close-tests] explain why its own suite
missed the case. They cover late payments, newly issued credit, unchanged
closed reports and signed cash adjustments. They never apply an existing
credit lot after its expiry has been closed. Earlier tests exercise credit
application and expiry together, but without period close.

### High Recognizes the Connection During Review

High's milestone-7 suite first passes 59 tests. During subsequent review, the
agent explicitly identifies the case of a backdated allocation arriving after
a published expiry. It adds [liability reconciliation][sol-high-reconciliation]
and a [targeted period-close test][sol-high-close-test] in the same patch, then
passes all 60 tests. There is no recorded failing test before that repair; the
sequence is review-led recognition followed by implementation and coverage.

The reconciliation compares the change in actual credit liability with the
change explained by the named business entries. It records the difference as
signed expiry. In the retained test, allocating 600 cents to a booking after
the expiry was published restores 600 cents of liability. An expiry entry of
negative 600 accounts for that change in the first open report. This candidate
test reads the closed report before the application, but does not read it again
afterward. The private evaluator supplies the unchanged-history check, which
High also passes.

An audit on another disposable copy checked whether the test really exercises
this code. The original candidate suite passed all 60 tests. Replacing the
reconciliation call with the unreconciled movements made the targeted test
fail with closing liability of zero instead of 600. This establishes the
test's sensitivity to that mechanism; it is not a reconstruction of the entire
earlier workspace before the agent's patch.

### Earlier Sol Runs Already Show Both Outcomes

Baseline Medium run 1 and High run 4 fail the same two assertions as intervention
Medium. Their implementations record intermediate adjustments but lose the
required effect while calculating expiry: adjustments posted after expiry are
filtered out, and no reversal is shown in the first open period. The intervention
instead drops the adjustment before recording it. The financial omission is
the same; the faulty code is in a different place.

Successful controls provide concrete alternatives. Baseline Medium run 3
[records an explicit negative expiry movement][baseline-sol-medium-reversal]
when the credit application is posted after expiry, and its own test checks
the closed report and restored liability. Baseline High run 1 names the
operation [unschedule_expiry][baseline-sol-high-reversal]: change the scheduled
expiry while it is open, or append a reversal once it is closed. Its
[retained test][baseline-sol-high-test] checks that distinction. Both runs swept
without the intervention. These are precedents, not evidence that the pilot
agents saw or copied earlier solutions.

### An Unscored Check of Offsetting Entries

A matching closing balance does not ensure that a report explains the money
correctly. The audit also exercised Sol High with a backdated chargeback of
cash that had created credit whose expiry was already closed. The chargeback's
transaction date was the credit's last valid day, before that expiry. A 100-cent
payment had created 110 cents of credit. Removing that credit requires both
a 110-cent revocation and a negative 110-cent expiry reversal in the open
period. They cancel in the balance, but represent different events.

The HTTP probe confirmed that the operations succeeded, the closed report
stayed unchanged, and the first open report had the correct zero opening and
closing liability. Its cash entries were also correct. Both credit entries,
however, were zero. The [chargeback classification][sol-high-reconciliation]
uses liability at the posting date, when the unused credit is already expired.
It sees no before/after reduction and records no revocation. Reconciliation
also sees no net change, so it cannot supply the missing offsetting entries.

This was an additional audit test, not one of the frozen scored scenarios.
It used the original High implementation with the reconciliation restored;
the published sweep remains unchanged. The result complements the Astra
X-High test above: preserving each required transaction category is a separate
obligation from making the balance agree. The probe covers this particular
chargeback sequence, not every possible late-credit operation.

## Interpretation

The pilot produced five sweeps and one run with a narrowly explained reporting
failure. All four Astra implementations and Sol High have more explicitly
separated responsibilities than their controls. Sol Medium has locally clear
names and useful documentation, but retains a large mixed-responsibility
context. The same instruction did not produce the same structural response.

The observed successes have specific mechanisms. Storage and readers agree;
saved responses do not depend on finance-module loading; Sol High accounts for
a credit application after a closed expiry. Astra High's response test catches
a missing field, while Sol High's final review identifies a missing financial
effect. Sol Medium shows how a clear helper can still implement too narrow a
responsibility. Its small audit correction explains three lost points without
requiring a wholesale architectural rewrite.

What remains unknown is whether the instruction makes the successful choices
more likely. Those mechanisms already appear in controls. Baseline Astra
X-High swept three of three runs, and Sol High four of five. There is one pilot
sample per configuration, and Sol's CLI and execution environment also changed.
Costs rose for Astra and fell for Sol relative to historical medians. None of
these comparisons isolates an instruction effect.

The strongest conclusion is therefore about the submitted implementations:
several are more deliberately organized, their successes can be explained in
code, and readable code still leaves room for missed interactions. Measuring
a reliability effect would require fresh runs both with and without the
instruction under the same conditions. Readability assessments and audit-only
probes remain separate from deterministic benchmark scoring.

## Environment and Measurement

The benchmark remains commit `5fda9a09255529b027cadf836c0c16c867a039e5`.
Astra's Codex CLI version (0.153.4), runner bytes and Docker image match the
earlier Astra campaign. The runner's recorded source commit is
`a74f0f2fa079f164b346ecc0cebe2f1e6f1e4ba2`; its byte hash is recorded separately
because the archived CLI-version qualification was updated. Each candidate
container retained a two-CPU, 4-GiB limit. The shared VM grew from six CPUs and
14 GiB to eight CPUs and 18 GiB. The runs were historical comparisons, not
concurrent randomized controls, and host capacity can affect timing.

Sol's intervention uses the same CLI 0.153.4 image and container limits. Its
historical controls ran natively on macOS, using CLI 0.149.0-alpha.4.3 for runs
1-3 and 0.150.0-alpha.8 for runs 4-5 at each effort. CLI version, operating system,
isolation and resource limits therefore differ alongside the instruction. The
comparison describes the resulting implementations; it cannot isolate a prompt
effect for Sol.

Costs reconcile the final cumulative usage of each session against the CLI's
completion records. There were seven main sessions and no descendants per run.
The same model-specific rates used for the baseline apply. Per million tokens,
Astra uses $10 for uncached input, $1 for cached input and $50 for output; Sol
uses $4, $0.40 and $20 respectively.
Reasoning is included in output, not billed twice. No cache-write tokens or
requests above the long-context threshold were recorded. These are
API-equivalent costs for subscription runs, not additional charges.

Runtime sums agent work across the seven milestones, including tests, and
excludes private evaluation and time between milestones. Production lines
include `lib/**/*.ex` and database migrations; test lines include Elixir source
under `test/`. Counts include comments and blank lines, matching the baseline.
They describe size, not an independent quality score.

The source archive contains the unmodified accepted code and candidate-written
documents and tests. Raw session logs remain private. This review distinguishes
code that can be inspected in the archive from observations about the sequence
of edits and test runs in those logs. The latter are supporting analysis, not
additional scored checks.

[low-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-7/lib/group_stay/operations.ex#L1
[low-backfill]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-4/lib/group_stay/room_accounting/backfill.ex#L14
[medium-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-3/lib/group_stay/reservations/group.ex#L30
[high-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-1/lib/group_stay/reservations/group.ex#L21
[xhigh-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-1/priv/repo/migrations/20260907000000_create_reservations.exs#L23
[xhigh-operation]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/reservations/operation.ex#L1
[high-finance]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-7/lib/group_stay/finance.ex#L1
[medium-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-7/lib/group_stay/operations.ex#L16
[high-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/lib/group_stay/operations/record.ex#L18
[high-retry-test]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/test/group_stay_web/controllers/daily_finance_report_test.exs#L28
[xhigh-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/operations.ex#L27
[xhigh-restart]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L83
[xhigh-revocation]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L135
[baseline-room-writer]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-3/lib/group_stay/group.ex#L17
[baseline-room-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-4/priv/repo/migrations/20260905000003_add_room_accounting.exs#L61
[sol-medium-context]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L1
[sol-medium-transaction]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L1452
[sol-medium-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-4/priv/repo/migrations/20260907030000_add_room_accounting_and_payment_reductions.exs#L65
[sol-medium-settlement]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits/cash_settlement.ex#L1
[sol-medium-allocation]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L688
[sol-medium-expiry]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/finance_reporting.ex#L178
[sol-medium-close-tests]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L99
[sol-high-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/partner_operations.ex#L48
[sol-high-transfer]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/reservations/deposit_transfer.ex#L1
[sol-high-report]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/finance_reporting/report.ex#L1
[sol-high-reconciliation]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/finance_reporting.ex#L348
[sol-high-close-test]: https://github.com/kkondaurov/sweatbench-runs/blob/16dbf0451f11a928ee01dcdaf8727d5d8ee3db3b/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L155
[baseline-sol-medium-reversal]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-medium-03/milestone-7/lib/group_stay/reservations.ex#L1575
[baseline-sol-high-reversal]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-high-01/milestone-7/lib/group_stay/finance.ex#L158
[baseline-sol-high-test]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-high-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L137
