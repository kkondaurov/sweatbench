# Asking for Readable Elixir

8 September 2026. Eighteen trajectories on the frozen Sweat Bench v6 task:
three each for Astra at low, medium, high and X-High, and Sol at medium and high.
This instruction experiment is separate from the baseline Models cohort;
requirements and deterministic scoring are unchanged.

**Astra's medium, high and X-High runs all earned full marks. Two of its three
low runs repeated an earlier migration bug. Sol earned full marks once at
each effort, with other runs missing different requirements.** The most consistent
change was in code organization: every Astra implementation had smaller largest
modules than its controls, including the two with failed migrations. Sol High
also distributed its work more widely. These structural differences did not
amount to a general improvement in correctness.

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
future requirements or private evaluation feedback. Inspection of all 126 session
records confirmed that the instruction was present. No candidate was repaired
after evaluation, and none of the eighteen attempts was replaced or excluded.

The comparison uses three historical controls per Astra effort and five per Sol
effort. It is not a randomized, concurrent experiment. Astra's CLI, runner and
container image match its controls, but shared host capacity differs. Sol's CLI
and operating environment also changed. Those differences matter when interpreting
scores, cost and runtime; the environment details appear below.

## Results

Twelve runs swept: ten Astra and two Sol. All 126 milestones passed their
integrity audits. Core has 39 possible points and Maintenance has 10; a sweep
earns every point in both tracks. Scores below are means across runs.

| Configuration | Earlier Core | Instruction Core | Earlier Maintenance | Instruction Maintenance | Earlier sweeps | Instruction sweeps |
|---|---:|---:|---:|---:|---:|---:|
| Astra Low | 38.7 | 38.3 | 9.0 | 9.3 | 1 of 3 | 1 of 3 |
| Astra Medium | 38.3 | 39.0 | 7.3 | 10.0 | 0 of 3 | 3 of 3 |
| Astra High | 38.7 | 39.0 | 8.3 | 10.0 | 1 of 3 | 3 of 3 |
| Astra X-High | 39.0 | 39.0 | 10.0 | 10.0 | 3 of 3 | 3 of 3 |
| Sol Medium | 38.2 | 38.0 | 8.8 | 8.3 | 2 of 5 | 1 of 3 |
| Sol High | 38.8 | 38.0 | 9.6 | 10.0 | 4 of 5 | 1 of 3 |

### Individual Runs

| Configuration | Run | Core | Maintenance | API-equivalent cost | Agent runtime | Production lines | Test lines |
|---|---:|---:|---:|---:|---:|---:|---:|
| Astra Low | 1 | 39 | 10 | $15.38 | 56m | 2,415 | 2,863 |
| Astra Low | 2 | 38 | 9 | $14.26 | 50m | 2,177 | 2,564 |
| Astra Low | 3 | 38 | 9 | $13.58 | 53m | 2,408 | 2,785 |
| Astra Medium | 1 | 39 | 10 | $16.78 | 1h 04m | 2,632 | 3,474 |
| Astra Medium | 2 | 39 | 10 | $16.64 | 1h 05m | 2,643 | 3,415 |
| Astra Medium | 3 | 39 | 10 | $15.19 | 59m | 2,662 | 3,034 |
| Astra High | 1 | 39 | 10 | $21.90 | 1h 27m | 2,861 | 4,675 |
| Astra High | 2 | 39 | 10 | $24.39 | 1h 34m | 2,615 | 5,197 |
| Astra High | 3 | 39 | 10 | $22.33 | 1h 32m | 2,685 | 4,866 |
| Astra X-High | 1 | 39 | 10 | $32.84 | 2h 07m | 2,969 | 6,323 |
| Astra X-High | 2 | 39 | 10 | $32.15 | 2h 04m | 2,808 | 6,118 |
| Astra X-High | 3 | 39 | 10 | $33.01 | 2h 09m | 3,144 | 6,666 |
| Sol Medium | 1 | 38 | 8 | $12.22 | 1h 43m | 3,682 | 1,957 |
| Sol Medium | 2 | 37 | 7 | $11.26 | 1h 36m | 3,708 | 2,350 |
| Sol Medium | 3 | 39 | 10 | $10.62 | 1h 38m | 3,549 | 1,949 |
| Sol High | 1 | 39 | 10 | $15.88 | 2h 16m | 4,761 | 2,784 |
| Sol High | 2 | 37 | 10 | $16.46 | 2h 24m | 4,410 | 2,804 |
| Sol High | 3 | 38 | 10 | $18.35 | 2h 21m | 4,679 | 2,578 |

Sweeps have 94 passed scenarios. Sol Medium run 2 has 90; every other non-sweep
has 92. Delivery-time and final scenario totals are identical for each run.
Historical upgrade results remain attached to their designated milestones,
even when later versions pass related checks. These are not 94 fresh tests of
the final code. Across all eighteen runs, 14 failed scenarios account for 15
lost family points; neither total is a count of independent bugs.

Median production code grew at every setting: 17-21% for Astra, 9% for Sol
Medium and 28% for Sol High. Median cost grew 9-17% for Astra and fell 19-26%
for Sol. Astra X-High took less agent time on average than its controls; the
other settings took more. Sol's lower cost therefore did not mean faster
completion, and its environment change prevents a prompt-only interpretation.

The [dashboard comparison](https://kkondaurov.github.io/sweatbench/#intervention)
shows means, medians, observed ranges and individual runs. Baseline records
remain in [accepted-runs.json](accepted-runs.json); the separate experiment is
in [intervention-runs.json](intervention-runs.json).

## What Changed in the Code

The intervention Astra implementations give more responsibilities distinct names
and owners. For example, Low run 1 separates booking policy, payment history
and the reconstruction of room funding. Medium run 1 separates the capture of
financial changes from report queries. High run 1 divides finance into Position,
Journal and Report modules. X-High run 1 separates request addressing and
validation order from the domain operation itself. These divisions remain
recognizable as later milestones add transfers and close.

The documentation explains operational decisions, not just function names.
Low's [Operations module][low-operations] describes the transaction shared by a
request, its business effects and its saved response. X-High's
[Operation parser][xhigh-operation] explains why a stale revision must not be
masked by a later validation error. High's [Finance module][high-finance]
introduces inception, expiry and report publication before presenting the code.

Every intervention Astra run has a smaller largest production file than every
control. The table shows each intervention run separately and the range across
same-effort controls. Production includes migrations; a file count includes
small schemas as well as substantial behavior.

| Configuration | Production files, runs 1 / 2 / 3 | Largest file, runs 1 / 2 / 3 | Earlier largest-file range |
|---|---|---|---|
| Astra Low | 33 / 28 / 27 | 360 / 352 / 380 | 714-843 |
| Astra Medium | 33 / 33 / 31 | 338 / 434 / 375 | 552-721 |
| Astra High | 48 / 43 / 47 | 288 / 294 / 269 | 506-798 |
| Astra X-High | 47 / 49 / 50 | 403 / 291 / 356 | 559-759 |
| Sol Medium | 38 / 43 / 45 | 1,802 / 975 / 1,355 | 1,378-2,154 |
| Sol High | 48 / 46 / 48 | 875 / 1,044 / 986 | 1,480-2,255 |

These counts locate a structural change, not a quality score. The stronger
reason to call particular modules more readable is that operations such as
correcting a payment or recording a financial movement have explicit
responsibilities and domain names, with comments explaining the rules they
preserve. Low runs 2 and 3 demonstrate the limit: small, named modules can
still disagree about the format stored in a database.

There are tradeoffs. Low run 1's migration delegates to current application schemas
and helpers, which future changes could make unsuitable for an old migration.
High run 1 keeps a 1,456-line persistence test combining several kinds of checks.
X-High run 1 has more focused test files, but its reporting hooks are spread across
domain writers, and its daily report loads historical entries into memory.
Those are concrete maintenance considerations, not observed scored failures or
measurements of how these applications would scale in production.

Sol's response is less uniform at medium. Run 1 retains a 1,802-line `Deposits`
context, almost half its production code. Run 2 reduces its largest module to
975 lines, yet has the lowest score. Run 3 sweeps with a 1,355-line largest
module and fewer test lines than either of the others. All three high runs
have smaller largest modules than their controls, but only run 1 sweeps.
The degree of decomposition alone does not explain these outcomes.

## Astra: Storage Across Versions

Milestone 4 introduces accounting for individual rooms. The migration must
read bookings created by the previous application and assign their funding
without losing payment history. Four baseline Astra runs stop before that
accounting can begin: low 3, medium 1 and 2, and high 1.

Their Ecto `{:array, :map}` field is stored by the SQLite adapter as a JSON array
of JSON-encoded strings. Decoding the outer array does not turn those strings
into room objects. A new reader that assumes otherwise fails at its first field
access. Embedded rooms are different: their JSON contains objects after one
decode. Separate room rows avoid this JSON question entirely.

The table follows every intervention run. Run numbers identify independent
attempts, not paired refactorings of the corresponding historical controls.

| Configuration | Run | Earlier room storage | Accepted migration reader | Outcome |
|---|---:|---|---|---|
| Astra Low | 1 | Array/map | Typed application schema | Pass |
| Astra Low | 2 | Array/map | Raw SQL, outer decode only | Both room-upgrade checks fail |
| Astra Low | 3 | Array/map | Schemaless Ecto query, outer decode only | Both room-upgrade checks fail |
| Astra Medium | 1 | Embedded rooms | Raw SQL, matching object JSON | Pass |
| Astra Medium | 2 | Embedded rooms | Raw SQL, matching object JSON | Pass |
| Astra Medium | 3 | Array/map | Frozen migration-local typed schemas | Pass |
| Astra High | 1 | Embedded rooms | Raw SQL, matching object JSON | Pass |
| Astra High | 2 | Separate room rows | Rows in room-position order | Pass |
| Astra High | 3 | Embedded rooms | Raw SQL, matching object JSON | Pass |
| Astra X-High | 1 | Separate room rows | Rows in room-position order | Pass |
| Astra X-High | 2 | Separate room rows | Rows in room-position order | Pass |
| Astra X-High | 3 | Embedded rooms | Raw SQL, matching object JSON | Pass |

### Two Low Runs Repeat the Old Mismatch

[Low run 2's migration][low2-migration] decodes the outer array once.
[Low run 3][low3-migration] does the same through a query without a schema.
Using Ecto does not provide typed loading when no typed schema participates.

Their candidate-written migration tests insert already-decoded room objects
as JSON rather than use the previous application's writer. See
[run 2's fixture][low2-fixture] and [run 3's fixture][low3-fixture].
Those fixtures test a different stored format. The private evaluator creates
the old database through the actual previous HTTP application, and both
migrations fail before the new room balances can be checked.

A diagnostic used disposable copies of each run's milestone-3 and milestone-4
applications. The original copies reproduced both complete historical-check
failures. Adding only an inner decoding step made both checks pass for each
run, including the accounting and restart assertions that followed migration.
This supports one representation defect as the explanation for each run's
two lost family points. It is not a new accepted score or a qualification of
every possible historical database.

Low run 3 later encountered the same shape problem in its milestone-5 transfer
migration. Its own test created data through application operations, rolled
that migration down and up, and failed at access to an encoded room string.
The agent [fixed the milestone-5 decoder][low3-m5-decoder], but left the
milestone-4 migration unchanged. The older migration remains byte-identical
through the final snapshot. A successful later upgrade does not erase a
different historical upgrade that was never repaired.

### Why the Other Ten Pass

The common property is agreement between the writer and reader, not a
particular database style. Low run 1 uses [typed Ecto loading][low-backfill].
Medium run 3 defines [old schemas inside the migration][medium3-schemas],
keeping the typed reader without depending on future application schema changes.
The embedded-room implementations can use a single raw JSON decode correctly;
the row-based implementations do not decode room JSON.

Medium run 3 still makes a nested-decoding mistake in a new raw reader at
milestone 5. Three candidate tests fail, and it adds the
[inner decoding step][medium3-m5-decoder] before delivery. Its milestone-4
typed migration was already correct. This distinguishes it from low run 3:
the two runs can make and repair the same later mistake while having different
earlier migration outcomes.

Successful baselines already provide the alternatives. Baseline low 2 uses
migration-local typed schemas; baseline X-High 2 uses embedded rooms.
Baseline high 2's inherited typed fixture actually triggers the nested-room
exception, and the agent repairs its reader. The instruction may encourage
deliberate design, but none of these successful mechanisms requires it.

## Astra: Saved Responses After Restart

A partner can repeat a payment or reporting request. GroupStay must return the
saved answer without applying the business operation twice, even after a server
restart. Six baselines fail this requirement for saved finance responses:
low 1, medium 1-3, and high 1 and 3.

They restore JSON keys with existing-atom conversion. Some finance keys exist
only after the finance module has loaded. A test that creates or reads a report
first can therefore make the request work accidentally. Restarting the database
pool inside the same Elixir VM also preserves those already-loaded keys.

All twelve intervention runs avoid this dependency:

| Restoration strategy | Runs |
|---|---|
| Keep and return JSON-shaped results | Low 1 and 3; medium 2 and 3; xhigh 1-3 |
| Keep a bounded response-key map inside the decoder | Low 2; medium 1; high 1-3 |

For example, [X-High's saved-result path][xhigh-operations] returns the stored
JSON value. [High run 2's record module][high2-record] owns the allowed key
vocabulary. Neither relies on whether a finance operation has already run.
A bounded map still needs new fields added; JSON-shaped results avoid that
registry, at the cost of choosing JSON types as the response contract.

### Omissions and Tests

High run 1's milestone-6 test retries a reporting-inception request and raises
a `KeyError` for missing `starts_on`. The agent adds it to the
[response-key and date definitions][high-decoder], retains the
[exact-response assertion][high-retry-test], and passes the full suite.
A missing definition now fails in an ordinary test instead of depending on
server startup order. Medium run 1 also replaces a load-dependent decoder
with an explicit map during milestone 3, without a recorded failure prompting
that edit.

Candidate restart coverage is not uniform:

| Runs | Observed test coverage |
|---|---|
| All low runs; medium 1 | Finance tests restart the database pool inside the same VM. |
| Medium 2 | Separate processes cover durable operations, reporting inception and close. |
| Medium 3 | Separate clients test a contended payment; this is not a finance-start cold test. |
| High 1 and 3 | Separate processes cover earlier reservation operations; finance persistence uses pool restarts. |
| High 2 | A fresh process restores saved results before report reads, then compares report bytes and retries requests. |
| X-High 1 and 3 | Separate application lifetimes cover reporting and period close. |
| X-High 2 | Process tests cover earlier operations; a manual HTTP restart rehearsal covers finance and close, but reads the ledger and reports before retrying. |

Some process scripts mention finance directly and could load its module while
compiling the script. Their request order alone does not prove the finance
module remains unloaded. The official evaluator independently checks a fresh
server. A further audit used HTTP-only first requests after separate server
starts on all 24 final Astra snapshots: it reproduced the six baseline
failures, while every intervention returned the exact stored inception and
close responses. This is a final-source diagnostic, separate from the original
historical milestone scores.

High run 2 and X-High run 3 detect another genuine restart problem in their
own tests: closed reports contain the same values, but JSON fields appear in
a different order across processes. Both add deterministic field ordering
before delivery. [X-High run 3's test][xhigh3-close-test] compares encoded output;
[its renderer][xhigh3-renderer] sorts the keys. These tests check more than
decoded-map equality. The failures, repairs and retained checks are visible
in the archived code and the private command logs.

The intervention does not uniformly introduce stronger tests. Some baseline
X-High tests already exposed and repaired the cold-start atom bug. Several
intervention runs pass with narrower tests because their representation avoids
the dependency. Better representation and better coverage are distinct routes
to the observed success.

## Sol: Six Implementations, Different Gaps

All six Sol runs use separate room rows and JSON-shaped saved responses.
They avoid Astra's two recurring representation mistakes, as some Sol controls
already did. That does not ensure that the funding order, financial effects
and record revisions are all correct.

| Run | Scored outcome | Relevant mechanism or missed interaction |
|---|---|---|
| Medium 1 | 38 Core, 8 Maintenance | Omits the expiry reversal for late-recorded credit use. |
| Medium 2 | 37 Core, 7 Maintenance | Gives all old cash priority over credit; independently omits the expiry reversal. |
| Medium 3 | Full marks | Preserves a unified funding timeline and explicitly reverses published expiry. |
| High 1 | Full marks | Preserves funding history and reconciles restored liability into the open report. |
| High 2 | 37 Core, 10 Maintenance | Includes the origin in an update set, but Ecto skips its unchanged-row update and revision increment. |
| High 3 | 38 Core, 10 Maintenance | Correctly handles the revision edge case; returns the first unavailable date rather than the last usable date. |

### Room Funding: Cash Is Not Always Senior

The upgrade requirement distinguishes an unattributed legacy funding block from
later operations with durable receipts. Legacy cash comes first, then legacy
credit, followed by cash and credit operations together in recorded commit
order. The economic dates of those later payments do not reorder their history.

Medium run 2's [migration][sol-m2-cash] allocates all cash first, including
later durable cash, then [places credit][sol-m2-credit] into remaining room
capacity. The application can conserve total money while assigning it to the
wrong rooms. Both historical checks complete migration and then return wrong
room balances; these are not startup failures.

Consider three rooms each requiring 2,000 cents. Recorded funding arrives as
3,000 cash, 1,000 credit and 2,000 more cash:

| Room | Required cash / credit | Medium 2 cash / credit |
|---|---|---|
| 1 | 2,000 / 0 | 2,000 / 0 |
| 2 | 1,000 / 1,000 | 2,000 / 0 |
| 3 | 2,000 / 0 | 1,000 / 1,000 |

The agent does rehearse an old-schema upgrade. Its command prints the resulting
room allocations but does not assert the required order. The displayed output
already contradicts the requirement, yet the subsequent summary calls the
rehearsal successful. This is a failure to check the meaning of the output,
not simply an absence of migration testing.

Medium run 3 [combines all four funding inputs][sol-m3-migration] into one
ordered stream before dividing it among rooms. It then preserves lot identity
while splitting credit between rooms. Both official upgrade tests pass.
Executing the original allocation SQL from runs 2 and 3 on identical isolated
fixtures reproduces the wrong and right room allocations respectively.
That SQL control tests the allocation algorithm, not the full Ecto migration.

### Credit Used Before Expiry, Recorded After Close

A cancellation can create hotel credit. When unused credit expires, a finance
report records the reduction in what the hotel owes. Closing the reporting
period freezes that report. A later request can describe a transaction that
happened while the credit was still usable.

GroupStay must honor that transaction date without rewriting closed history.
If the credit's expiry has already been published, its application restores
liability in the first open period. The report needs a negative expiry entry,
not another issuance of credit or a changed opening balance. If that credit is
then consumed, both restoration and consumption must remain visible even when
their amounts cancel.

Medium runs 1 and 2 omit this entry. [Run 1's helper][sol-medium-expiry]
only changes scheduled expiries that have not yet passed. [Run 2's helper][sol-m2-expiry]
likewise does nothing once the reporting date is later than expiry.
Both accept the credit application and preserve the closed report, but the
first open report shows zero closing liability instead of 300 cents. A second
scenario consumes 600 cents and finds the corresponding negative-expiry entry
missing. The two scenarios cost three family points per run; Medium 2's two
room-upgrade losses have a separate cause.

Their own period-close suites cover late cash, new credit issuance and unchanged
closed output, but never apply existing credit after a closed expiry. The
final suites contain 47 and 52 passing tests. On disposable copies, adding the
missing reversal makes all ten private milestone-7 HTTP cases pass for each
implementation, including later assertions in the formerly failing cases.
Earlier milestones and all historical paths were not requalified by those
small diagnostic changes.

### Successful Review and Explicit Compensation

Medium run 3 and all three high runs pass both scored restoration cases.
Medium run 3 uses an [explicit negative-expiry movement][sol-m3-reversal];
High run 2 explicitly reactivates expired credit. High runs 1 and 3 reconcile
the actual liability change with the categorized credit movements, recording
the missing amount as signed expiry.

Medium run 3 recognizes the case in review after 44 tests pass. It adds the
reversal and a [targeted test][sol-m3-close-test], then passes 45 tests.
High run 1 follows a similar sequence after 59 passing tests: it adds
[reconciliation][sol-high-reconciliation] and a
[closed-expiry test][sol-high-close-test] together, then passes 60.
These are review-led discoveries, not observed test failures preceding the fixes.

The retained tests really exercise the mechanisms. Removing Medium 3's
negative-expiry call from a copy makes its own new test and the same two private
cases fail: selected tests fall from 14 of 14 to 11 of 14. Removing High 1's
reconciliation makes its retained test report zero liability instead of 600.
These ablations establish test sensitivity; they do not reconstruct every
detail of the earlier workspace.

Successful baselines already contain both explicit compensation and targeted
coverage. Baseline Medium 3 [records a negative-expiry movement][baseline-sol-medium-reversal].
Baseline High 1's [unschedule_expiry helper][baseline-sol-high-reversal]
changes a future schedule or adds a reversal once it is closed, with a
[retained test][baseline-sol-high-test]. Baseline Medium 1 and High 4 instead
lose the same financial effect while calculating expiry. The intervention
Medium failures drop it earlier, before recording it. The business omission
recurs even though its location in the code differs.

All ten Sol controls pass the room-upgrade and transfer-revision checks that
intervention Medium 2 and High 2 fail. Those are not recurring accepted failures
within this baseline cohort. Baseline Medium 4 does repeat the expiry-field
convention found in intervention High 3, while still handling late-credit
restoration correctly.

Baseline Medium 2 is different again: it already has a negative-expiry branch
and a candidate test for late credit. Structural comparisons of Elixir Date
values nevertheless produce wrong opening balances and reject valid report
dates. A separate duplicate-open error branch also crashes. Matching failed
family names with the intervention Medium runs would conceal these different
causes. The other six baseline sweeps supply several successful approaches,
including explicit reversals and residual-liability reconciliation.

### An Origin Revision That Ecto Does Not Write

A transferred payment can fund rooms in another booking. If that payment is
reduced, the request requires the addressed original booking's revision to
advance even when only the destination's funds change.

High run 2 [includes the origin in its update set][sol-h2-updates].
Its room-accounting helper recomputes the original booking's totals and calls
`Repo.update` with an [optimistic-lock changeset][sol-h2-changeset].
When the entire reduction comes from transferred funding held elsewhere, those
totals have not changed. In the retained Ecto version, the revision increment is
deferred until update preparation, but an unchanged changeset is skipped before
that preparation runs. Including the booking in the set does not force a write.

The ordinary test pays 2,000 cents, transfers 1,500 and reduces 1,000 entirely
from the destination. The origin remains at revision 3 instead of becoming 4.
The historical transfer-upgrade check reaches the same error after migration
and earlier statement assertions have succeeded. These two Core-family losses
share one observed cause.

The candidate's own reduction test affects both bookings, so the origin's
financial fields change and its update proceeds. High run 3 writes a test in
which only the destination loses funds, sees the missing increment, and
[forces the revision field into the changeset][sol-h3-changeset] before the
optimistic lock. Its [retained test][sol-h3-transfer-test] checks the origin
and destination revisions separately. This is an actual failed-test, repair,
passing-test sequence.

Applying that small correction to a copy of High 2 makes all eleven private
transfer tests pass, including the later assertions in the original failing
case. The historical upgrade was not rerun with the correction; its shared
first failure is traced in source, not newly certified as repaired.

### A Date Field, Not an Extra Day of Credit

High run 3 documents `expires_on` as the first day credit cannot be used.
It stores cancellation plus 366 days, checks availability with a strict
comparison against that date, and returns the stored value. This keeps the
usable period through day 365 but disagrees with the evaluator's last-usable-day
response convention.

Both failing responses identify the expected surviving lot and 3,800-cent
amount. One returns 1 May instead of 30 April; the other returns 1 April instead
of 31 March. They are exact response-map failures, not observed wrong lot
selection merely because the scenario names mention expiry order and tie-breaks.
See the [documented convention][sol-h3-credit-lot] and
[response serialization][sol-h3-credit-output].

On an audit copy, subtracting one day only when serializing that response moves
the unchanged private credit file from three of five to five of five passing
cases. Stored dates, eligibility, ordering, allocations and finance are untouched.
This isolates the observed representation mismatch; it is not a full contract
repair, since the agent's own tests expect the first-unavailable field.

The [Findings note](https://kkondaurov.github.io/sweatbench/#findings-expiry)
discusses the ambiguity in the early credit request. The delivered
[milestone-6 request][sol-h3-expiry-request] explicitly says unused credit
remains available through its `expires_on` date and expires the following day.
The session record shows the agent reading that text, but its final serializer
still exposes the original first-unavailable convention. The final failure is
therefore a failure to reconcile the field after clarification, not an unresolved
ambiguity throughout the task. It retains its one lost Core point and passes
every Maintenance check.

### Mistakes Fixed Before Delivery

The trajectories also contain successful corrections that disappear from final
score summaries. Medium run 1 fixes structural Date comparison after a test
failure and adds migration flush boundaries after a populated fixture queries a
column before it exists. Both sample-1 Sol runs repair rejected operations that
incorrectly roll back their saved response: a SQL savepoint lets business changes
roll back while the outer transaction records the rejection for future retries.

High run 3 fixes the unchanged-row revision problem and later corrects
calendar comparisons exposed by finance tests. These cases show real language
and framework learning within runs. The instruction did not prevent those
mistakes, and their eventual correction depended on a test or review reaching
the relevant situation.

Structural changes are equally concrete. High run 1 extracts
[transfer handling][sol-high-transfer] and [report queries][sol-high-report]
as those features arrive. Medium run 2 separates room accounting, hotel credit
and finance from its main coordinator, but retains the two wrong rules described
above. Medium run 3 introduces an operation journal and a funding-transfer
module while retaining a larger central context. The sweep does not make that
last design automatically clearer than its lower-scoring counterparts.

## Beyond the Scored Examples

A report can show the right balance while omitting the events that explain it.
An additional HTTP probe starts reporting, takes 100 cents, converts a
cancellation to 110 cents of credit, closes through expiry, then charges back
the payment using a transaction date before expiry. The open report should
record a 110-cent credit revocation and a negative 110-cent expiry reversal.
The two entries cancel in the balance.

This reading follows the requirements for complete signed transaction
classifications and unchanged closed reports. The exact credit sequence is
not one of the frozen scored examples, so these findings are diagnostic only.

The same probe was executed against all twelve intervention and twelve baseline
Astra final snapshots:

| Cohort | Both credit entries retained | Both omitted |
|---|---|---|
| Astra intervention | Low 1; X-High 1, 2 and 3 | Low 2 and 3; all medium and high runs |
| Astra baseline | High 2; X-High 3 | The other ten runs |

All 24 keep the tested closed report unchanged and end with zero liability.
Low 1 and the three intervention X-High runs preserve the original economic date
while moving the reporting entry to the first open period. X-High 2's
[journal][xhigh2-journal] names those dates separately. All three intervention
X-High suites contain assertions for both categories, including
[run 2's paired entries and post-expiry control][xhigh2-pair-test].

High run 1 instead shifts the date through close before classifying credit
revocation. At that later date, the credit is already expired; the code sees
no liability change and records neither entry. The same HTTP probe confirms
that omission in the accepted source. This is a narrower limitation within a
scored sweep, not a reason to silently change its result.

Sol High run 1 was also checked with this sequence. It preserves the report and
balance but omits both entries. Its residual-liability calculation cannot recover
two missing categories whose net effect is zero. The probe was not applied
across all six Sol runs, so this observation is limited to High 1.

## Diagnostic Scope

The review combines original evaluator reports, accepted source snapshots,
candidate-written tests, and the session record of visible edits and commands.
Indexing every milestone is not a claim that every source line received the
same level of manual inspection. Detailed source tracing follows the failures,
their successful comparators, migration fixtures, response readers and report
corrections.

| Additional audit | Scope and result | What it does not establish |
|---|---|---|
| Astra Low 2 and 3 inner decoding | Both full historical M3-to-M4 checks fail on original copies and pass after decoding-only edits. | A new whole-trajectory score or all possible upgrades. |
| Astra cold HTTP retries | All 24 terminal implementations checked; six baseline failures reproduced, twelve intervention passes. | Replacement of historical milestone evaluations. |
| Astra signed credit pair | Same unscored sequence on all 24 terminal implementations. | Coverage of every financial history. |
| Sol Medium 2 and 3 allocation SQL | Original SQL executed on identical isolated funding histories; wrong and right allocations reproduced. | A full Ecto/HTTP migration rerun. |
| Sol Medium 1 and 2 expiry correction | Each copied implementation passes all ten M7 HTTP cases after a narrow reversal edit. | Earlier milestone and full-history requalification. |
| Sol Medium 3 reversal removal | Its retained test and two private cases fail without the reversal. | An original red test before its review-led fix. |
| Sol High 1 reconciliation removal | The retained candidate test fails without the reconciliation. | Every transaction category is correct when reconciliation passes. |
| Sol High 2 forced revision | Private transfer file improves from 10 of 11 to 11 of 11. | A newly passing historical upgrade, which was not rerun. |
| Sol High 3 display-only date change | Private credit file improves from 3 of 5 to 5 of 5. | A reconciled public and candidate-test contract. |

Audit changes were made only in disposable copies. Original requests, accepted
snapshots and scores remain unchanged. No audit finding was supplied to a
candidate and no extra model run was used to improve the published sample.

## Interpretation

The result differs by model and effort. Astra Medium and High each sweep all
three intervention runs, compared with zero and one of three controls. That is
a promising correctness result. Astra Low sweeps once in each condition and
repeats an old migration defect twice with the instruction. X-High sweeps all
three in both conditions, leaving no score headroom in that comparison.

Sol's sweep counts show no corresponding improvement: one of three at each
effort, compared with two of five Medium and four of five High controls. High
passes every Maintenance check but retains narrower Core failures. Medium
varies from 37 Core and 7 Maintenance to full marks. The medium run with
the smallest largest module is not its best-scoring run.

The successful choices are concrete: a migration reads the representation
its previous version actually wrote; a saved response can be read independently
of finance-module loading; a report records a correction without changing
closed history. Some are established from the beginning, some emerge during
review, and some are repairs prompted by failed candidate tests. Successful
baseline runs already contain alternatives that meet the same obligations.

The code is more deliberately divided in Astra and Sol High, but readability
and correctness remain separate observations. A named helper can express too
narrow a rule, and an isolated migration can still assume the wrong data
format. More documentation or more files does not ensure these interactions
have been understood and tested.

Three samples per setting and historical controls do not isolate the instruction's
effect, especially with Sol's environment change. The results neither establish
a general reliability improvement nor show that the instruction has no effect.
They support using the instruction to express a preference for maintainable
code, without treating it as a dependable remedy for recurring benchmark bugs.
Readability assessments and audit-only probes remain separate from fixed scoring.

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

Costs reconcile the final cumulative usage of all 126 sessions against the CLI's
completion records. There were seven main sessions and no descendants per run.
The same model-specific rates used for the baseline apply. Per million tokens,
Astra uses $10 for uncached input, $1 for cached input and $50 for output; Sol
uses $4, $0.40 and $20 respectively.
Reasoning is included in output, not billed twice. No cache-write tokens or
requests above the long-context threshold were recorded; the largest recorded
input request contained 143,575 tokens. Total API-equivalent cost across all
18 runs was $343.25. These are
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

[low-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-7/lib/group_stay/operations.ex#L1
[low-backfill]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-4/lib/group_stay/room_accounting/backfill.ex#L14
[medium-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-3/lib/group_stay/reservations/group.ex#L30
[high-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-1/lib/group_stay/reservations/group.ex#L21
[xhigh-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-1/priv/repo/migrations/20260907000000_create_reservations.exs#L23
[xhigh-operation]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/reservations/operation.ex#L1
[high-finance]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-7/lib/group_stay/finance.ex#L1
[medium-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-7/lib/group_stay/operations.ex#L16
[high-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/lib/group_stay/operations/record.ex#L18
[high-retry-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/test/group_stay_web/controllers/daily_finance_report_test.exs#L28
[xhigh-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/operations.ex#L27
[xhigh-restart]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L83
[xhigh-revocation]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L135
[baseline-room-writer]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-3/lib/group_stay/group.ex#L17
[baseline-room-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-4/priv/repo/migrations/20260905000003_add_room_accounting.exs#L61
[sol-medium-context]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L1
[sol-medium-transaction]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L1452
[sol-medium-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-4/priv/repo/migrations/20260907030000_add_room_accounting_and_payment_reductions.exs#L65
[sol-medium-settlement]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits/cash_settlement.ex#L1
[sol-medium-allocation]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/deposits.ex#L688
[sol-medium-expiry]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/lib/group_stay/finance_reporting.ex#L178
[sol-medium-close-tests]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L99
[sol-high-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/partner_operations.ex#L48
[sol-high-transfer]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/reservations/deposit_transfer.ex#L1
[sol-high-report]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/finance_reporting/report.ex#L1
[sol-high-reconciliation]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/lib/group_stay/finance_reporting.ex#L348
[sol-high-close-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L155
[baseline-sol-medium-reversal]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-medium-03/milestone-7/lib/group_stay/reservations.ex#L1575
[baseline-sol-high-reversal]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-high-01/milestone-7/lib/group_stay/finance.ex#L158
[baseline-sol-high-test]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/sol-high-01/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L137
[low2-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-02/milestone-4/priv/repo/migrations/20260907000003_add_room_accounting.exs#L124
[low3-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-03/milestone-4/priv/repo/migrations/20260907000003_add_room_accounting.exs#L31
[low2-fixture]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-02/milestone-4/test/group_stay/room_accounting_migration_test.exs#L131
[low3-fixture]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-03/milestone-4/test/group_stay/room_accounting_migration_test.exs#L47
[low3-m5-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-low-03/milestone-5/priv/repo/migrations/20260907000004_add_deposit_transfers.exs#L265
[medium3-schemas]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-medium-03/milestone-4/priv/repo/migrations/20260907210000_add_room_accounting.exs#L5
[medium3-m5-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-medium-03/milestone-5/priv/repo/migrations/20260907220000_add_deposit_transfers.exs#L72
[high2-record]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-high-02/milestone-7/lib/group_stay/reservations/operation_record.ex#L19
[xhigh3-close-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-03/milestone-7/test/group_stay/finance_period_close_persistence_test.exs#L220
[xhigh3-renderer]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-03/milestone-7/lib/group_stay_web/controllers/daily_finance_report_json.ex#L1
[sol-m2-cash]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-02/milestone-4/priv/repo/migrations/20260907030000_add_room_accounting_and_payment_reductions.exs#L152
[sol-m2-credit]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-02/milestone-4/priv/repo/migrations/20260907030000_add_room_accounting_and_payment_reductions.exs#L227
[sol-m3-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-03/milestone-4/priv/repo/migrations/20260907214000_add_room_and_payment_accounting.exs#L141
[sol-m2-expiry]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-02/milestone-7/lib/group_stay/finance_reporting.ex#L334
[sol-m3-reversal]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-03/milestone-7/lib/group_stay/finance.ex#L102
[sol-m3-close-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-medium-03/milestone-7/test/group_stay_web/controllers/finance_period_close_test.exs#L194
[sol-h2-updates]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-02/milestone-7/lib/group_stay/partner_operations.ex#L923
[sol-h2-changeset]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-02/milestone-7/lib/group_stay/reservations/group.ex#L97
[sol-h3-changeset]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-03/milestone-7/lib/group_stay/reservations/group.ex#L68
[sol-h3-transfer-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-03/milestone-7/test/group_stay_web/controllers/deposit_transfers_test.exs#L155
[sol-h3-credit-lot]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-03/milestone-7/lib/group_stay/reservations/credit_lot.ex#L1
[sol-h3-credit-output]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-03/milestone-7/lib/group_stay_web/controllers/guest_credit_controller.ex#L18
[xhigh2-journal]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-02/milestone-7/lib/group_stay/finance/journal.ex#L15
[xhigh2-pair-test]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-astra-xhigh-02/milestone-7/test/group_stay_web/controllers/finance_period_close_credit_test.exs#L86
[sol-h3-expiry-request]: https://github.com/kkondaurov/sweatbench-runs/blob/c3d1120c3ef49744efef6693aa5ee1ec6158bfc9/v6/interventions/readable-elixir/v6-readable-sol-high-03/milestone-6/docs/requests/06-daily-finance-report.md#L92
