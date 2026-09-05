# Sweat Bench v6 results

This directory contains the public results for the frozen v6 benchmark.

- `index.html` is a self-contained interactive dashboard.
- `RETROSPECTIVE.md` is the full methodological and behavioral analysis.
- `ASTRA_TRAJECTORIES.md` records all four Astra efforts and examines the first two rounds' migration and cold-replay
  failures, comparison with earlier GPT systems, and implications for the next benchmark.
- `LUNA_HARNESS_TRAJECTORIES.md` traces the two family-level differences between OpenCode Luna and
  delegated Codex Luna through candidate code, tests, and parent/child review behavior.
- `accepted-runs.json` contains all 98 completed trajectories and the derived tables used by the
  report.
- `analyze.py` independently validates the population and recomputes group headline metrics from
  the run records.
- `SHA256SUMS` fixes the released dataset, dashboard, and analysis bytes.

Run the verifier from the repository root:

```bash
python3 evaluation/results/v6/analyze.py
```

The dataset has two views. `models` contains 73 model-comparison trajectories. `harness` contains
25 controlled harness or delegation trajectories and is not pooled into the model leaderboard.
The Meta Muse Spark 1.3 row contains one completed run; its interrupted follow-on sample is not a
result and is not included. Astra low, medium, high, and X-High each have three completed runs. Their rows
include per-milestone token usage, standard-rate cost calculations, execution versions, and report
hashes. They ran through Codex CLI 0.153.4 with no subagents or delegation intervention.

X-High runs 2 and 3 resumed from accepted snapshots after provider-capacity errors. Their costs
and runtimes include the interrupted attempts, but exclude the time the runs were stopped.
The earlier retrospective remains a dated analysis of the 67-run Models population; the dashboard,
dataset and Astra results section contain the expanded 73-run population.

Costs with `cost_basis: recorded` are provider charges captured for the complete accepted run.
The legacy data field `cost_basis: estimated` identifies API-equivalent costs, which apply the documented production token rates to recorded parent
and descendant usage. The dashboard and retrospective describe rate snapshots and cache treatment.

Raw model sessions and generated applications are not part of this release. Each public run has a
stable `<group>-<sample>` identifier; machine-local source paths were deliberately removed.
