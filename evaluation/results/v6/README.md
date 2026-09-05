# Sweat Bench v6 results

This directory contains the public results for the frozen v6 benchmark.

- `index.html` is a self-contained interactive dashboard.
- `RETROSPECTIVE.md` is the full methodological and behavioral analysis.
- `ASTRA_TRAJECTORIES.md` examines the three Astra efforts, their costs, migration and cold-replay
  failures, comparison with earlier GPT systems, and implications for the next benchmark.
- `LUNA_HARNESS_TRAJECTORIES.md` traces the two family-level differences between OpenCode Luna and
  delegated Codex Luna through candidate code, tests, and parent/child review behavior.
- `accepted-runs.json` contains all 92 completed trajectories and the derived tables used by the
  report.
- `analyze.py` independently validates the population and recomputes group headline metrics from
  the run records.
- `SHA256SUMS` fixes the released dataset, dashboard, and analysis bytes.

Run the verifier from the repository root:

```bash
python3 evaluation/results/v6/analyze.py
```

The dataset has two views. `models` contains 67 model-comparison trajectories. `harness` contains
25 controlled harness or delegation trajectories and is not pooled into the model leaderboard.
The Meta Muse Spark 1.3 row contains one completed run; its interrupted follow-on sample is not a
result and is not included. Astra low, medium, and high each have two completed runs. Their rows
include per-milestone token usage, standard-rate cost calculations, execution versions, and report
hashes. They ran through Codex CLI 0.153.4 with no subagents or delegation intervention.

Costs with `cost_basis: recorded` are provider charges captured for the complete accepted run.
Costs with `cost_basis: estimated` apply the documented production token rates to recorded parent
and descendant usage. The dashboard and retrospective describe rate snapshots and cache treatment.

Raw model sessions and generated applications are not part of this release. Each public run has a
stable `<group>-<sample>` identifier; machine-local source paths were deliberately removed.
