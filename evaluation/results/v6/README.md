# Sweat Bench v6 results

This directory is the frozen public record for the v6 pre-disclosure cohort.

- `index.html` is a self-contained interactive dashboard.
- `RETROSPECTIVE.md` is the full methodological and behavioral analysis.
- `accepted-runs.json` contains all 85 accepted trajectories and the derived tables used by the
  report.
- `analyze.py` independently validates the population and recomputes group headline metrics from
  the run records.
- `SHA256SUMS` fixes the released dataset, dashboard, and retrospective bytes.

Run the verifier from the repository root:

```bash
python3 evaluation/results/v6/analyze.py
```

The dataset has two views. `models` contains 60 model-comparison trajectories. `harness` contains
25 controlled harness or delegation trajectories and is not pooled into the model leaderboard.

Costs with `cost_basis: recorded` are provider charges captured for the complete accepted run.
Costs with `cost_basis: estimated` apply the documented production token rates to recorded parent
and descendant usage. The dashboard and retrospective describe rate snapshots and cache treatment.

Raw model sessions and generated applications are not part of this release. Each public run has a
stable `<group>-<sample>` identifier; machine-local source paths were deliberately removed.
