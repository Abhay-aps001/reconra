# Benchmark and evaluation

Reconra keeps production reconciliation separate from evaluation truth. The production engine consumes input artifacts; it does not import generator code, held-out truth, or scenario labels.

## Saved result

[saved-benchmark.json](saved-benchmark.json) is a **SAVED BENCHMARK RESULT** copied from the checked-in held-out deterministic benchmark output. It is fallback evidence only, not a fresh execution and not an ordinary reconciliation run.

The underlying held-out output reports 184 records, 177 deterministic resolutions, 17 escalations, and an exact paise tie-out of 137303972 total bank-credit paise, 132983672 explained paise, and 4320300 residual paise.

Its scoring_available value is false. The held-out material contains scenario labels and entity IDs, but no explicit expected candidate mapping. It cannot truthfully support accuracy, precision, recall, F1, auto-resolution rate, false-match rate, or AI-success metrics. Those fields are absent from the saved artifact.

## Reproduce a benchmark

Generate the deterministic fixtures, then run the held-out benchmark:

    python scripts/generate_demo_data.py --dataset all --output data/generated
    python scripts/run_benchmark.py --dataset heldout --mode deterministic

The generator emits a separate ground_truth.json for evaluation-only use, but the normal runner reads only orders.json, payments.json, reconciliation_rows.json, and bank_transactions.json. It writes benchmark.json with reconciliation artifacts in its output directory. To create the stable saved fallback from that unscored deterministic output:

    python scripts/saved_benchmark.py

The publishing script rejects scored or malformed sources, removes local output paths and volatile timing fields, and preserves only stable operational counts and paise values. Optional agent-assisted execution depends on configured provider credentials; an unavailable provider degrades to a documented non-live status rather than producing a fabricated success claim.

Do not tune thresholds, policies, generators, or implementation against held-out evaluation results.
