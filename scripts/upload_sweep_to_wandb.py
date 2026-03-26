#!/usr/bin/env python
"""
Upload sweep results to WandB — one run per config (not per rep).

Aggregates reps into summary statistics before uploading,
creating 243 WandB runs (one per grid config) with median/std metrics.

Usage:
    source ~/.secrets  # load WANDB_API_KEY
    uv run python scripts/upload_sweep_to_wandb.py --input-dir experiments/results/sweep
"""

import json
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

import wandb


def main():
    parser = argparse.ArgumentParser(description="Upload sweep results to WandB")
    parser.add_argument("--input-dir", type=str, default="experiments/results/sweep")
    parser.add_argument("--project", type=str, default="sparse_matrix_recovery")
    parser.add_argument("--entity", type=str, default="qsimeon")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    files = sorted(input_dir.glob("*.json"))
    print(f"Found {len(files)} result files")

    # Group by config
    groups = defaultdict(list)
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        key = json.dumps(data["config"], sort_keys=True)
        groups[key].append(data["distances"])

    print(f"Grouped into {len(groups)} configs")

    for i, (config_key, distances_list) in enumerate(sorted(groups.items())):
        config = json.loads(config_key)

        # Compute summary stats
        keys = distances_list[0].keys()
        medians = {k: float(np.median([d[k] for d in distances_list])) for k in keys}
        stds = {f"{k}_std": float(np.std([d[k] for d in distances_list])) for k in keys}

        N = config.get("num_nodes", 15)
        sg = config.get("stim_gain", 1.0)
        mf = config.get("num_measured", 10) / N
        sf = config.get("num_stimulated", 5) / N
        T = config.get("max_timesteps", 1000)

        run = wandb.init(
            project=args.project,
            entity=args.entity,
            config={**config, "n_reps": len(distances_list),
                    "meas_frac": mf, "stim_frac": sf},
            name=f"N{N}_T{T}_m{mf:.0%}_sg{sg}_sf{sf:.0%}",
        )
        wandb.log({**medians, **stds, "n_reps": len(distances_list)})
        wandb.finish()

        if (i + 1) % 50 == 0:
            print(f"  Uploaded {i+1}/{len(groups)}")

    print(f"Done! {len(groups)} runs uploaded to {args.project}")
    print(f"View at: https://wandb.ai/{args.entity}/{args.project}")


if __name__ == "__main__":
    main()
