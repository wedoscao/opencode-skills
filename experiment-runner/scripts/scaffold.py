"""Generate a runnable, reproducible experiment repo skeleton.

Usage:
    python scaffold.py --name se-vn --out ./se-vn

Writes: configs/runs.toml, src/{__init__,methods,run,metrics}.py,
results/, cache/, data/, .gitignore, README.md. `src/metrics.py` is copied
from this skill so the runner and the metrics stay in lockstep.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

RUN_PY = '''"""Deterministic experiment runner: seed -> generate(cached) -> score -> metrics -> cost -> result JSON.

Fill in `methods.py`; you should not need to edit this file for a new method.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

import numpy as np

from methods import METHODS  # {name: (generate_fn, score_fn)}
from metrics import auroc, accuracy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def set_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def cache_key(method: str, model: str, dataset: str, seed: int, config: dict) -> str:
    blob = json.dumps({"method": method, "model": model, "dataset": dataset,
                       "seed": seed, "config": config}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_or_generate(method: str, model: str, dataset: str, seed: int, config: dict):
    key = cache_key(method, model, dataset, seed, config)
    cache_dir = ROOT / "cache"
    cache_dir.mkdir(exist_ok=True)
    path = cache_dir / f"{key}.json"
    if path.exists():
        with open(path) as fh:
            return json.load(fh)
    generate, _ = METHODS[method]
    t0 = time.time()
    samples = generate(model=model, dataset=dataset, seed=seed, **config)
    wall = time.time() - t0
    payload = {"samples": samples, "wall_clock_s": wall,
               "forward_passes": config.get("n_samples", len(samples))}
    with open(path, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    return payload


def run_one(method: str, model: str, dataset: str, seed: int, config: dict) -> dict:
    set_seed(seed)
    generate, score = METHODS[method]
    payload = load_or_generate(method, model, dataset, seed, config)
    samples = payload["samples"]
    scores, y_true = score(samples)
    scores = np.asarray(scores, dtype=float)
    y_true = np.asarray(y_true, dtype=np.int64)
    return {
        "run_id": f"{method}__{model}__{dataset}__seed{seed}",
        "method": method, "model": model, "dataset": dataset, "seed": seed,
        "metrics": {"auroc": round(auroc(y_true, scores), 4),
                    "accuracy": round(accuracy(y_true, (scores >= 0.5).astype(int)), 4)},
        "cost": {"forward_passes": payload.get("forward_passes"),
                 "tokens": payload.get("tokens"),
                 "wall_clock_s": round(payload.get("wall_clock_s", 0.0), 2)},
        "cache_key": cache_key(method, model, dataset, seed, config),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/runs.toml")
    ap.add_argument("--method", nargs="*", default=None, help="filter methods")
    args = ap.parse_args()
    # A minimal TOML-less config: use JSON if the user prefers. Kept simple so
    # the scaffold has zero dependencies. Replace with tomllib (py3.11+) if desired.
    import json
    cfg_path = ROOT / args.config
    if cfg_path.suffix == ".toml":
        try:
            import tomllib
            with open(cfg_path, "rb") as fh:
                cfg = tomllib.load(fh)
        except ModuleNotFoundError:
            raise SystemExit("tomllib requires Python 3.11+; or use a JSON config")
    else:
        cfg = json.loads(cfg_path.read_text())

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    methods = args.method or list(cfg["methods"])
    for method in methods:
        if method not in METHODS:
            print(f"WARN: method '{method}' not in methods.py, skipping")
            continue
        for model in cfg["models"]:
            for dataset in cfg["datasets"]:
                for seed in cfg["seeds"]:
                    result = run_one(method, model, dataset, seed, cfg.get("run_config", {}))
                    out = results_dir / f"{result['run_id']}.json"
                    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
                    print("wrote", out)


if __name__ == "__main__":
    main()
'''

METHODS_PY = '''"""Implement one entry per method. Each entry is (generate, score).

generate(model, dataset, seed, **cfg) -> list of per-sample raw outputs.
    This is the expensive, cached step. Return anything JSON-serializable.

score(samples) -> (scores: np.ndarray[float], y_true: np.ndarray[int]).
    Cheap, deterministic; turns raw outputs into a scalar score per sample plus
    the ground-truth label. Runs every time, so keep it side-effect free.

Replace the placeholder below with real methods. Keep the same backbone,
budget, and question set across every method you compare.
"""
from __future__ import annotations

import numpy as np


def _dummy_generate(model: str, dataset: str, seed: int, **cfg):
    rng = np.random.default_rng(seed)
    n = cfg.get("n_samples", 400)
    return [{"id": i, "raw": float(rng.random())} for i in range(n)]


def _dummy_score(samples):
    rng = np.random.default_rng(0)
    scores = np.array([s["raw"] for s in samples])
    y_true = rng.integers(0, 2, len(samples))
    return scores, y_true


METHODS = {
    "b4-naive-entropy": (_dummy_generate, _dummy_score),
    "b3-ptrue": (_dummy_generate, _dummy_score),
    "b5-verbalized": (_dummy_generate, _dummy_score),
    "b2-sample-consistency": (_dummy_generate, _dummy_score),
    "b1-semantic-entropy": (_dummy_generate, _dummy_score),
}
'''

CONFIG_TOML = '''# Deterministic run manifest. Edit models/datasets/seeds; keep names in sync
# with EXPERIMENTS.md so report.py lines up with the plan.
models = ["qwen2.5-7b-instruct", "llama-3.1-8b-instruct"]
datasets = ["probe-en", "probe-vi", "vihallu", "uiquitviquad2"]
seeds = [0, 1, 2]
methods = ["b4-naive-entropy", "b3-ptrue", "b5-verbalized",
           "b2-sample-consistency", "b1-semantic-entropy"]

[run_config]
n_samples = 400
'''

GITIGNORE = """cache/
data/
results/
.venv/
__pycache__/
*.egg-info/
"""

REQUIREMENTS = """# Runtime dependency for src/metrics.py and src/run.py.
numpy>=1.24
"""

README = """# {name}

Reproducible experiment repo. Runner: `python src/run.py --config configs/runs.toml`.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

- Implement methods in `src/methods.py` (each is a `(generate, score)` pair).
- `generate` is cached under `cache/`; `score` recomputes freely.
- Metrics (`src/metrics.py`): AUROC, bootstrap CI, DeLong paired test, accuracy, ECE.
- Aggregate results: `python ../<skill>/scripts/report.py --results results --out RESULTS.md`.

Never edit a result by hand; re-run the runner so the provenance is real.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.out)
    (root / "configs").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(exist_ok=True)
    (root / "cache").mkdir(exist_ok=True)
    (root / "data").mkdir(exist_ok=True)

    (root / "configs" / "runs.toml").write_text(CONFIG_TOML)
    (root / "src" / "__init__.py").write_text("")
    (root / "src" / "run.py").write_text(RUN_PY)
    (root / "src" / "methods.py").write_text(METHODS_PY)
    shutil.copy(SKILL_DIR / "scripts" / "metrics.py", root / "src" / "metrics.py")
    (root / ".gitignore").write_text(GITIGNORE)
    (root / "requirements.txt").write_text(REQUIREMENTS)
    (root / "README.md").write_text(README.format(name=args.name))

    print(f"Scaffolded {args.out}/ — next: fill src/methods.py, then run src/run.py")


if __name__ == "__main__":
    main()
