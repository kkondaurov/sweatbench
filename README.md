# Sweat Bench

Sweat Bench is a sequential software-engineering benchmark for coding agents. A candidate inherits
one Phoenix application through seven product releases. Every release adds a real business change,
while all earlier behavior, persisted data, migrations, retry semantics, and accounting invariants
remain in force.

Version 6 is frozen and public. Its evaluator is disclosed, so the included results are the final
pre-disclosure reference cohort. New v6 runs can be useful for engineering experiments, but must be
labeled post-disclosure and must not be pooled silently with the reference results.

- [Interactive results dashboard](https://kkondaurov.github.io/sweatbench/)
- [Dashboard source](evaluation/results/v6/index.html)
- [Full retrospective](evaluation/results/v6/RETROSPECTIVE.md)
- [Accepted-run dataset](evaluation/results/v6/accepted-runs.json)
- [Human review guide](REVIEW_GUIDE.md)
- [Disclosure policy](DISCLOSURE.md)

## What it measures

The benchmark starts with an empty Group Stay service and reveals seven requests in order:

1. operational deposit accounting;
2. cancellation economics and hotel credit;
3. durable idempotent operations;
4. room accounting, payments, reductions, and chargebacks;
5. cross-group deposit transfers;
6. effective-dated daily finance reports; and
7. immutable period close with late adjustments.

Candidates see the product documents, the current request, and the code left by the previous
milestone. They do not see future requests or the evaluator. The reference protocol uses a fresh
agent session at each handoff and asks the candidate to author its own tests.

Results keep two scales separate:

- **Core /39**: explicit product requirements and cumulative regression behavior.
- **Maintenance /10**: five historical-data upgrades and five cross-domain interactions.

A **sweep** is 39/39 Core and 10/10 Maintenance in the final state. Raw scenario results, ship-time
scores, recovery, regression episodes, runtime, cost, code size, and subagent use remain available
for diagnosis; they are not collapsed into one synthetic score.

## Reference results

The model-comparison view contains 60 accepted trajectories. Every listed trajectory completed all
seven milestones and passed the benchmark's integrity checks. Low-scoring valid runs are included;
incomplete, invalid, and infrastructure-debug attempts are not model results and are excluded.

| Model and harness | n | Avg Core | Avg Maintenance | Sweeps | Median cost |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 Sol high, Codex CLI | 5 | 38.8 | 9.6 | 4/5 | ~= $22.37 |
| GPT-5.6 Sol medium, Codex CLI | 5 | 38.2 | 8.8 | 2/5 | ~= $13.90 |
| GPT-5.6 Terra xhigh, Codex CLI | 5 | 36.6 | 7.0 | 0/5 | ~= $9.96 |
| GPT-5.6 Luna xhigh, Codex CLI | 5 | 32.6 | 6.2 | 0/5 | ~= $1.50 |
| GPT-5.5 xhigh, Codex CLI | 5 | 37.0 | 7.6 | 0/5 | ~= $27.57 |
| Claude Opus 5 high, Claude Code | 2 | 38.5 | 9.5 | 1/2 | ~= $47.65 |
| Grok 4.6 xhigh, OpenCode | 5 | 37.6 | 7.8 | 0/5 | $14.71 |
| Qwen3.8 Max xhigh, OpenCode | 5 | 35.8 | 7.6 | 0/5 | $25.34 |
| DeepSeek V4 Pro 0813 max, OpenCode | 5 | 35.0 | 6.4 | 0/5 | $8.87 |
| Kimi K3 max, OpenCode | 5 | 36.2 | 6.8 | 0/5 | $29.23 |
| GLM 5.3 high, OpenCode | 5 | 35.4 | 7.6 | 1/5 | $20.96 |
| GLM-5.3 Flash high, OpenCode | 4 | 34.8 | 6.5 | 0/4 | ~= $2.08 |
| GLM-5.3 Flash max, OpenCode | 4 | 34.0 | 6.8 | 0/4 | ~= $2.96 |

`~=` marks an API-equivalent estimate from recorded token usage. Unmarked OpenCode costs are
recorded provider charges. The dashboard documents model-specific rates, cached input treatment,
descendant sessions, and harness-owned review work.

An additional 25 accepted trajectories form a controlled harness view: the same four GPT-5.6
model/effort configurations under OpenCode, plus a Codex Luna condition explicitly instructed to
delegate independent audits. These are kept outside the model leaderboard because harness and
prompting policy are the variables under test.

## Quick start

Requirements:

- Python 3.11 or newer;
- Erlang and Elixir versions from `.tool-versions`;
- SQLite build tools and `mix`; and
- Codex CLI, Claude Code, or OpenCode for an actual candidate run.

Validate the benchmark and its runner:

```bash
python3 bench.py validate
python3 -m unittest discover -s tests
python3 evaluation/results/v6/analyze.py
```

Materialize milestone 1 without invoking a model:

```bash
python3 bench.py materialize 1 /tmp/sweat-bench-example --candidate-tests endogenous
```

Run one isolated seven-milestone trajectory with a locally installed harness:

```bash
python3 run_candidate.py \
  --label example-01 \
  --harness codex \
  --model gpt-5.6-sol \
  --effort high \
  --protocol handoff \
  --candidate-tests endogenous \
  --benchmark-ref v6.0.0
```

The runner records the benchmark commit, harness version, prompt policy, milestone snapshots,
private reports, integrity audits, and final scores under `.runs/<label>/`. Credentials remain
outside the candidate workspace. OpenCode can also be placed inside the included Docker image; see
`run_candidate.py --help` for container and OAuth seeding options.

## Repository map

- `candidate/`: starter service, product documents, seven requests, and optional example tests.
- `evaluation/`: disclosed v6 private tests, system scenarios, Judgment definitions, and scorer.
- `benchmark.json`: frozen stage, family, scenario, and integrity manifest.
- `bench.py`: materialization, advancement, snapshot, evaluation, and validation commands.
- `run_candidate.py`: isolated sequential runner for Codex, Claude Code, and OpenCode.
- `evaluation/results/v6/`: frozen dashboard, retrospective, accepted data, and verifier.

Candidate-generated applications and raw model sessions are intentionally not committed. They add
substantial bulk and may contain provider/session metadata; the public dataset preserves the scored
trajectory, cost, structure, and failure evidence needed for the published analysis.

## Reuse

The code, benchmark materials, evaluator, and reports are available under the MIT License. Keep v6
frozen. Any change to requests, prompts, candidate-visible tests, private tests, family assignment,
or scoring creates a new benchmark version and should not be compared as if it were v6.

When citing the project, use `CITATION.cff` and name the exact release tag.
