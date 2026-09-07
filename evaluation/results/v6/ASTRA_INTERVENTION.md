# Asking Astra for Readable Elixir

7 September 2026. Four new Astra trajectories on the frozen Sweat Bench v6 task,
one each at low, medium, high and X-High. This is an instruction experiment,
not a new scoring version and not an addition to the baseline Models cohort.

## The Experiment

In v6, a coding agent builds GroupStay, a hotel-deposit application, through seven
successive requests. Each new version must preserve earlier behavior and data.
The original Astra runs produced compact implementations. Several nevertheless
failed when a new version opened an old database or when the server restarted.

The intervention asked for clearer code, without naming those failures. The
following instruction was appended to the normal request at every milestone:

> Produce idiomatic, well-structured Elixir/Phoenix code that a human maintainer would find clear and a pleasure to read. Organize the application into cohesive modules with clear responsibilities, choose descriptive names, and document important domain concepts and design decisions. Favor straightforward implementations and useful abstractions over either terse code or unnecessary layers. Maintain this standard as the application evolves.

Each milestone started a fresh model session with the candidate's own repository
and tests. The agent received no baseline implementations, failure analysis,
future requirements or private evaluation feedback. Inspection of all 28 session
records confirmed that the instruction was present. No candidate was repaired
after evaluation, and none of the four Astra attempts was replaced or excluded.

The four configurations and instruction were recorded before the pilot started.
The wider pilot also included Sol; this publication covers only Astra. Every
completed Astra run in this pilot is included, with one sample per effort.

## Results

All four new runs earned all 39 Core and 10 Maintenance points. All 28 accepted
milestones passed their ordinary private API checks and integrity audits. Each
run has 94 passed scenarios in both its delivery-time and final totals. Those
totals include historical system checks at their designated milestones, not 94
new tests of the final code.

| Effort | Earlier sweeps | New sweep | API-equivalent cost | Agent runtime | Production lines | Test lines |
|---|---:|---:|---:|---:|---:|---:|
| Low | 1 of 3 | 1 of 1 | $15.38 | 56m | 2,415 | 2,863 |
| Medium | 0 of 3 | 1 of 1 | $16.78 | 1h 04m | 2,632 | 3,474 |
| High | 1 of 3 | 1 of 1 | $21.90 | 1h 27m | 2,861 | 4,675 |
| X-High | 3 of 3 | 1 of 1 | $32.84 | 2h 07m | 2,969 | 6,323 |

Each new run cost more and produced more production code than any of its three
same-effort controls. Relative to the earlier medians, production code grew by
17%, 21%, 29% and 19%; cost grew by 25%, 10%, 15% and 14%. Test code did not grow
uniformly: the new high run had fewer test lines than any earlier high run.
X-High completed faster than its earlier average, but within its earlier runtime
range. The other three efforts took longer than their earlier ranges.

The [dashboard comparison](https://kkondaurov.github.io/sweatbench/#intervention)
shows the earlier scores and observed ranges next to each new run. Baseline data
remain in [accepted-runs.json](accepted-runs.json); the new records are in
[intervention-runs.json](intervention-runs.json).

## What Changed in the Code

The new implementations give more responsibilities distinct names and owners.
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

Across the new runs, the largest production file is 288-403 lines; across the
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

## Reading Old Room Data

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

## Returning the Same Answer After Restart

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

## What Their Tests Cover

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

## Interpretation

The passing outcomes are supported by specific storage and response-handling
choices, not just by a lucky ordering of the scored requests. The code also
shows the sort of organization requested by the instruction. High supplies an
especially useful edit-and-test sequence: the explicit decoder exposed an omitted
field in a setting where a load-dependent decoder could hide it.

What remains unknown is whether the instruction makes those choices more likely.
The successful mechanisms already existed among the controls, and baseline
X-High had swept all three runs. One new trajectory at each effort is not enough
to separate an instruction effect from variation between implementations. Nor
does a perfect v6 score establish that every plausible accounting case works.

The pilot supports a promising, concrete result: four more explicitly organized
implementations, all passing the existing benchmark, at higher API-equivalent
cost. A larger comparison with new runs both with and without the instruction
would be needed to measure a reliability effect. No subjective readability
judgment has been added to the benchmark score.

## Environment and Measurement

The benchmark remains commit `5fda9a09255529b027cadf836c0c16c867a039e5`.
Astra's Codex CLI version (0.153.4), runner bytes and Docker image match the
earlier Astra campaign. The runner's recorded source commit is
`a74f0f2fa079f164b346ecc0cebe2f1e6f1e4ba2`; its byte hash is recorded separately
because the archived CLI-version qualification was updated. Each candidate
container retained a two-CPU, 4-GiB limit. The shared VM grew from six CPUs and
14 GiB to eight CPUs and 18 GiB. The runs were historical comparisons, not
concurrent randomized controls, and host capacity can affect timing.

Costs reconcile the final cumulative usage of each session against the CLI's
completion records. There were seven main sessions and no descendants per run.
The same Astra rates used for the baseline apply: $10 per million uncached input
tokens, $1 per million cached input tokens and $50 per million output tokens.
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

[low-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-7/lib/group_stay/operations.ex#L1
[low-backfill]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-low-01/milestone-4/lib/group_stay/room_accounting/backfill.ex#L14
[medium-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-3/lib/group_stay/reservations/group.ex#L30
[high-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-1/lib/group_stay/reservations/group.ex#L21
[xhigh-rooms]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-1/priv/repo/migrations/20260907000000_create_reservations.exs#L23
[xhigh-operation]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/reservations/operation.ex#L1
[high-finance]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-7/lib/group_stay/finance.ex#L1
[medium-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-medium-01/milestone-7/lib/group_stay/operations.ex#L16
[high-decoder]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/lib/group_stay/operations/record.ex#L18
[high-retry-test]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-high-01/milestone-6/test/group_stay_web/controllers/daily_finance_report_test.exs#L28
[xhigh-operations]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/lib/group_stay/operations.ex#L27
[xhigh-restart]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L83
[xhigh-revocation]: https://github.com/kkondaurov/sweatbench-runs/blob/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir/v6-readable-astra-xhigh-01/milestone-7/test/group_stay/operations_restart_test.exs#L135
[baseline-room-writer]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-3/lib/group_stay/group.ex#L17
[baseline-room-migration]: https://github.com/kkondaurov/sweatbench-runs/blob/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6/v6-astra-medium-01/milestone-4/priv/repo/migrations/20260905000003_add_room_accounting.exs#L61
