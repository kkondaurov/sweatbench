# Sweat Bench v6 results

This directory contains the public results for the frozen v6 benchmark.

- `index.html` is a self-contained interactive dashboard.
- The Intervention tab compares four new Astra readable-Elixir instruction runs with the
  twelve earlier Astra runs. It remains separate from the original 98-run dataset.
  `intervention-runs.json` contains the audited measurements; `build_intervention.py`
  validates accounting and generates `intervention-data.js`. `ASTRA_INTERVENTION.md`
  explains the instruction, source changes, test evidence and limits of the comparison.
- The Findings tab groups the 73 model-view trajectories into 13 model families. Its curated
  explanations are in `findings.js`; `findings-data.js` is a portable extract of run scores and
  failed check memberships, generated from `accepted-runs.json` by `build_findings.py`.
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
python3 evaluation/results/v6/build_findings.py --check
python3 evaluation/results/v6/build_intervention.py --check
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

The Findings review is dated 6 September 2026. It checks all model-view run outcomes, with a deeper
84-milestone audit of Astra and targeted source and test inspection for the other families.
Mechanisms, counterexamples and blocked assertions are distinguished from the score labels.
The extra Astra counterfactual and paired HTTP probes are analyst checks, not new accepted runs
or a rescore. The generated code and tests are in the public source archive; raw session logs remain
private, so the archive is not the full evidence for every explanation. The controlled Harnesses cohort is excluded
from the family findings. These small samples do not establish intrinsic model failure rates.

The [note on expiry dates](index.html#findings-expiry) distinguishes the field convention left open
in milestone 2 from its explicit definition in milestone 6. Scores retain the original evaluations.

Costs with `cost_basis: recorded` are provider charges captured for the complete accepted run.
The legacy data field `cost_basis: estimated` identifies API-equivalent costs, which apply the documented production token rates to recorded parent
and descendant usage. The dashboard and retrospective describe rate snapshots and cache treatment.

The [source archive](https://github.com/kkondaurov/sweatbench-runs/tree/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6) contains all 98 accepted runs,
with a `v6/<run.id>/README.md` and `milestone-1/` through `milestone-7/` for each run. Source links
in Models, Harnesses and Findings open that run's directory. Raw model session logs remain private;
machine-local source paths are not published.

Dashboard run IDs are copied from `accepted-runs.json`, matched by `group` and public `sample`,
not reconstructed from legacy `label` values. The 20 Codex runs shared by Models and Harnesses
reuse the same run objects and source links. Findings uses the accepted IDs in `findings-data.js`.
`sourceArchiveBaseUrl` in `results.js` controls the baseline dashboard archive links. It is pinned to
archive commit `be3005fa4092a75107d627e51bf9e9ee1f8474de`, as are the source links in the reports.

The four intervention trajectories have their own [source collection](https://github.com/kkondaurov/sweatbench-runs/tree/90627782faa8382cd9af5007450550cd75a6d9fe/v6/interventions/readable-elixir),
with 28 snapshots. Its pin is recorded in `intervention-runs.json`; the original archive
and data are unchanged. All 28 source checkpoint, report and accepted log hashes were
verified before publication, and usage reconciled against the recorded main sessions.
