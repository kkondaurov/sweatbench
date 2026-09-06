# Disclosure policy

Sweat Bench v6 was published with its evaluator on 30 August 2026.

## Reference cohort

The repository's 85 accepted trajectories were produced before public evaluator disclosure:

- 60 trajectories in the model-comparison view;
- 20 additional OpenAI-model trajectories in the Codex CLI versus OpenCode comparison; and
- 5 additional GPT-5.6 Luna trajectories under an explicit delegation instruction.

The reference cohort contains every completed, valid trajectory admitted by the frozen experiment
manifests. Valid low-scoring runs remain included. Incomplete work, integrity-invalid work, and
infrastructure-debug attempts are not model results and are not part of the cohort.

Claude Opus 5 has two accepted pre-disclosure samples. That small sample is reported as such rather
than extrapolated or supplemented after disclosure.

## Post-disclosure use

Publishing the private tests retires v6 as a hidden benchmark. Anyone can still run it to inspect a
harness, reproduce the machinery, or develop a new benchmark version. Such results must say
"post-disclosure" prominently and must not be silently pooled with the reference cohort.

For a future hidden evaluation, fork the design into a new version with new requests, private tests,
system scenarios, family assignments, and integrity hashes. Keep that evaluator private until the
new reference cohort is frozen.

## Data boundary

The release includes scored trajectory records, aggregate analyses, cost provenance, code-size
metrics, failure families, and the full frozen evaluator. The separate
[v6 source archive](https://github.com/kkondaurov/sweatbench-runs/tree/be3005fa4092a75107d627e51bf9e9ee1f8474de/v6) contains the submitted
applications and candidate-written tests at all seven milestones of each of the 98 accepted runs
in the current dashboard. It includes both the original reference cohort and the later published
Astra and Muse Spark runs; their original evaluation status is unchanged.

Raw provider sessions, credentials, transient infrastructure logs, downloaded dependencies,
build output and runtime databases are not included.
