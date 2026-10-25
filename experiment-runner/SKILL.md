---
name: experiment-runner
description: Build and run reproducible ML/NLP experiments — seeded runs, generation caching, metric computation (AUROC, bootstrap CI, DeLong paired test), cost accounting, and auto-generated result tables. Use whenever the user wants to run or track experiments, reproduce a baseline, "chạy thí nghiệm", "tái lập", "bootstrap", "p-value", "seed", compare methods on a dataset, or turn an EXPERIMENTS.md plan into runnable code.
---

# Experiment Runner

Turn an experiment plan (an `EXPERIMENTS.md`, a matrix of method × dataset) into reproducible runs whose numbers a reviewer can trust.

The failure mode this skill exists to prevent is the *unreproducible run*: a seed leaked across methods, generations recomputed on every re-run (cost + drift), two methods compared at different sample budgets or backbones, an AUROC reported without a confidence interval, and a "difference" claimed without a paired test. Every rule below exists because one of those happened.

## Principles (non-negotiable)

1. **Same backbone, same budget, same questions.** Never compare methods that differ in model, sample count, or input set. A comparison that is off by any of these is not a comparison.
2. **Deterministic by construction.** Fix every source of randomness (torch, numpy, Python hash, sampler) per seed. Record the seed with the result.
3. **Cache generations, not metrics.** The expensive step is model forward passes. Cache raw outputs keyed by (method, model, dataset, seed, prompt hash); recompute metrics freely from the cache.
4. **Report uncertainty.** Every headline number is a mean over seeds ± std, plus a bootstrap CI. A difference between two methods gets a paired test (DeLong for AUROC), never "looks higher".
5. **Report raw quality first.** If a model is nearly always wrong, say its accuracy first; a high AUROC on top of garbage is still garbage.
6. **Cost is a result.** Log forward passes, tokens, and wall-clock per cell, and report the table. If the research question is about the cost/quality trade-off, this table is a first-class figure, not an appendix.

## Workflow

### 1. Read the plan first

If an `EXPERIMENTS.md` (or similar) exists, read it before writing code. Extract the matrix (methods × datasets), the metric, the seed budget, and any "same backbone" constraints. Reconcile the code to the plan, not the plan to the code.

### 2. Scaffold the repo

```bash
python scripts/scaffold.py --name se-vn --out ./se-vn
```

This writes a runnable skeleton: `configs/runs.toml`, `src/run.py`, `src/methods.py`, `src/metrics.py` (copied from this skill), `requirements.txt` (`numpy`), `results/`, `cache/`, a `.gitignore` for `cache/` and `data/`, and a `README.md`. The scaffold is the floor: fill `methods.py` with the actual methods.

`src/metrics.py` and `src/run.py` import `numpy`, so create a venv and install the dependency before the first run:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

### 3. Implement methods behind one interface

Every method exposes the same two calls so the runner is method-agnostic:

```python
def generate(model, dataset) -> list[dict]      # raw outputs (one per sample)
def score(samples) -> np.ndarray                # a scalar "confidence/hallucination" score per sample
```

Generation is the cached, expensive step; `score` is the cheap step that turns raw outputs into a score. The runner calls `generate` once per (method, model, dataset, seed), caches it, then calls `score` as often as needed.

### 4. Run through the runner, not by hand

```bash
python src/run.py --config configs/runs.toml
```

The runner (the template in `src/run.py`) does, in order: set all seeds → generate (or load from cache) → score → compute metrics → record cost → write `results/<run_id>.json`. Re-running with a changed metric never re-generates.

### 5. Compute metrics honestly

Use `scripts/metrics.py` (pure numpy, no sklearn):

| Metric | Function | When |
|---|---|---|
| AUROC (Mann-Whitney) | `auroc(y_true, score)` | headline discrimination metric |
| Bootstrap CI | `bootstrap_auc_ci(y_true, score, seed=...)` | every headline AUROC |
| DeLong paired test | `delong_test(y_true, s_a, s_b)` | claim "A beats B" |
| Accuracy | `accuracy(y_true, y_pred)` | report raw quality first |
| ECE | `ece(y_true, proba)` | if confidence calibration matters |

Report AUROC as `mean ± std` over seeds and state the CI. Never report an AUROC from a single seed as a fact. For the paired test, compare the two score vectors on the *same* samples; DeLong accounts for the correlation.

### 6. Regenerate the result table

```bash
python scripts/report.py --results results --out RESULTS.md --metric auroc
```

This aggregates the per-run JSONs into the markdown matrix from the plan, with `mean ± std` per cell and a separate cost table (forward passes, tokens, wall-clock). Keep the columns and row order identical to the plan's matrix.

## Result file schema

Every run writes `results/<run_id>.json`:

```json
{
  "run_id": "b1__qwen2.5-7b__probe-vi__seed0",
  "method": "b1-semantic-entropy",
  "model": "qwen2.5-7b-instruct",
  "dataset": "probe-vi",
  "seed": 0,
  "metrics": {"auroc": 0.812, "accuracy": 0.55, "ece": 0.09},
  "cost": {"forward_passes": 4000, "tokens": 1180000, "wall_clock_s": 1832},
  "cache_key": "sha256:...",
  "config_hash": "sha256:..."
}
```

`run_id` is `<method>__<model>__<dataset>__seed<N>`. `cache_key` and `config_hash` make re-runs provably identical or provably changed.

## Failure modes and what they look like

| Symptom | Real cause | Fix |
|---|---|---|
| Numbers change every re-run | Seed not fixed, or Python hash randomization / non-deterministic sampler | Fix every seed; set `PYTHONHASHSEED`; use `use_deterministic_algorithms` where available |
| AUROC higher for method A but A uses a different model | Comparing across backbones | Force same backbone + same questions |
| "A beats B" but they overlap heavily | Single seed, no paired test | Report CI + DeLong p-value |
| GPU cost ballooned after a metric tweak | Regenerating instead of caching | Cache raw outputs; recompute only metrics |
| High AUROC, nobody asks about accuracy | Model nearly always wrong | Report raw accuracy/quality first |
| Table cell missing or in wrong column | run_id/aggregation mismatch | Keep method/dataset names identical to the plan |

## Definition of done

The experiment is finished when a reviewer can answer, from the repo alone:

- Which method, model, dataset, seed produced this number, and how to re-run it?
- Is the headline number `mean ± std` with a CI, or a single-run point estimate?
- Were the compared methods on the same backbone, sample budget, and input set?
- Was the "A beats B" claim backed by a paired test?
- What did each cell cost (passes, tokens, wall-clock)?

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/scaffold.py` | Generate a runnable experiment repo skeleton (incl. `requirements.txt`) |
| `scripts/metrics.py` | AUROC, bootstrap CI, DeLong test, accuracy, ECE (requires `numpy`) |
| `scripts/report.py` | Aggregate per-run JSONs into a markdown matrix + cost table |

All scripts take `--help`; none hardcode paths or identities.
