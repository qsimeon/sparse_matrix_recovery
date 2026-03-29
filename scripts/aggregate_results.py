#!/usr/bin/env python
"""
Aggregate per-rep JSON files from cluster runs into experiment-level JSON files.

After running launch_experiments.sh and launch_E1_scaling.sh on the cluster,
this script combines the individual rep files into the format expected by
analysis.py and generate_all_figures.py.

Usage:
    uv run python scripts/aggregate_results.py
    uv run python scripts/aggregate_results.py --reps-dir experiments/results/reps
"""

import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from scipy.stats import bootstrap


def aggregate_experiment(rep_files, experiment_name):
    """Combine per-rep JSON files into one experiment result list.

    Groups files by config, computes medians and bootstrap CIs,
    and returns the same format as run_experiments.py:save_results().
    """
    # Group by config
    configs = defaultdict(list)
    for f in rep_files:
        with open(f) as fh:
            data = json.load(fh)
        # Create a hashable config key (exclude rep-specific fields)
        cfg = data["config"]
        key = json.dumps(cfg, sort_keys=True)
        configs[key].append(data["distances"])

    results = []
    for cfg_json, distances_list in sorted(configs.items()):
        cfg = json.loads(cfg_json)
        df = pd.DataFrame(distances_list)
        df.index.name = "repetition"

        # Bootstrap CI on distance columns
        dist_cols = [c for c in df.columns if c.endswith("_distance")]
        data_arr = df[dist_cols].to_numpy()
        try:
            res = bootstrap(
                (data_arr,), np.median, axis=0,
                confidence_level=0.95, n_resamples=1000,
            )
            ci_l, ci_u = res.confidence_interval
            CIs = {
                dist_cols[i]: {"low": float(ci_l[i]), "high": float(ci_u[i])}
                for i in range(len(dist_cols))
            }
        except Exception:
            CIs = {}

        cfg["experiment"] = experiment_name

        # Add derived fields that run_experiments.py adds
        if "measurement_fraction" not in cfg and "num_measured" in cfg and "num_nodes" in cfg:
            cfg["measurement_fraction"] = cfg["num_measured"] / cfg["num_nodes"]
        if "stim_fraction" not in cfg and "num_stimulated" in cfg and "num_nodes" in cfg:
            cfg["stim_fraction"] = cfg["num_stimulated"] / cfg["num_nodes"]

        results.append({
            "config": cfg,
            "distances": df.to_dict(),
            "confidence_intervals": CIs,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Aggregate per-rep results")
    parser.add_argument(
        "--reps-dir", type=str, default="experiments/results/reps",
        help="Directory containing per-rep JSON files",
    )
    parser.add_argument(
        "--output-dir", type=str, default="experiments/results",
        help="Output directory for aggregated JSON files",
    )
    args = parser.parse_args()

    reps_dir = Path(args.reps_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not reps_dir.exists():
        print(f"No reps directory found at {reps_dir}")
        return

    # Group files by experiment
    exp_files = defaultdict(list)
    for f in sorted(reps_dir.glob("*.json")):
        # Filename format: E1_cfg000_rep007.json
        exp_name = f.stem.split("_")[0]
        exp_files[exp_name].append(f)

    exp_to_output = {
        "E1": "E1_baseline.json",
        "E2": "E2_granger.json",
        "E3": "E3_stimulation.json",
        "E4": "E4_sparsity.json",
        "E5": "E5_nonlinearity.json",
        "E6": "E6_oracle_crossover.json",
        "E7": "E7_stim_fraction.json",
    }

    for exp_name in sorted(exp_files.keys()):
        files = exp_files[exp_name]
        print(f"\n{exp_name}: {len(files)} rep files")

        results = aggregate_experiment(files, exp_name)
        print(f"  → {len(results)} configs aggregated")

        output_name = exp_to_output.get(exp_name, f"{exp_name}.json")
        output_path = output_dir / output_name
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  → Saved: {output_path}")

    print("\nDone! Aggregated results ready for figure generation.")


if __name__ == "__main__":
    main()
