# Contributing

Sweat Bench treats benchmark definition and benchmark results as separate artifacts. Please open an
issue before changing the task or evaluator so the version boundary is explicit.

## Benchmark changes

Version 6 is frozen. A change to any of the following requires a new benchmark version:

- candidate-visible product, API, runtime, request, prompt, or example-test material;
- private scenarios, system checks, Judgment definitions, family assignment, or score logic;
- milestone order, handoff policy, candidate-test policy, or isolation contract.

New versions should update `benchmark.json`, add targeted tests, document the semantic difference,
and retain enough migration history to explain why old and new results are not pooled.

## Code changes

Keep runner and analysis changes narrow and portable. Run:

```bash
python3 bench.py validate
python3 -m unittest discover -s tests
python3 evaluation/results/v6/analyze.py
```

Do not commit credentials, raw session databases, `.runs`, `.results`, generated applications,
dependency builds, or provider logs.

## Result submissions

Results must be complete seven-milestone trajectories. Include the benchmark commit, exact harness
and model versions, reasoning effort, protocol, candidate-test policy, prompt suffix, final private
reports, integrity status, and the source of every cost figure. Report every valid trajectory in a
declared cohort, including low scores. Do not treat incomplete, invalid, or infrastructure-debug
attempts as model outcomes.

Because the v6 evaluator is public, all new v6 results must be labeled post-disclosure. They may be
reported for engineering comparison but must not be merged into the pre-disclosure reference cohort.
