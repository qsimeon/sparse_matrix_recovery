#!/usr/bin/env python
"""
Aggregate individual rep JSON files into combined experiment results.

After running experiments via SLURM job arrays (which produce one JSON per rep),
this script combines them into the format expected by analysis.py.

Usage:
    # Aggregate E1-E7 experiment reps
    python experiments/aggregate_results.py --input-dir experiments/results/reps --output-dir experiments/results

    # Aggregate mega sweep reps
    python experiments/aggregate_results.py --input-dir experiments/results/sweep --output-dir experiments/results --sweep

HOW IT WORKS:
    1. Scan input-dir for JSON files matching the pattern
    2. Group by (experiment, config) — files like E1_cfg000_rep000.json
    3. For each group, combine all reps into a single DataFrame
    4. Compute bootstrap CIs
    5. Save in the format analysis.py expects
"""

import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from scipy.stats import bootstrap


def aggregate_experiment_reps(input_dir, output_dir):
    """Aggregate per-rep JSONs from E1-E7 into combined experiment files."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group files by experiment and config index
    groups = defaultdict(list)
    for f in sorted(input_dir.glob("E*_cfg*_rep*.json")):
        parts = f.stem.split("_")  # E1_cfg000_rep007
        exp = parts[0]             # E1
        cfg = parts[1]             # cfg000
        groups[(exp, cfg)].append(f)

    # Map experiment names to output filenames
    exp_to_file = {
        "E1": "E1_baseline.json",
        "E2": "E2_granger.json",
        "E3": "E3_stimulation.json",
        "E4": "E4_sparsity.json",
        "E5": "E5_nonlinearity.json",
        "E6": "E6_oracle_crossover.json",
        "E7": "E7_stim_fraction.json",
    }

    # Group by experiment (across all configs)
    exp_results = defaultdict(list)
    for (exp, cfg), files in sorted(groups.items()):
        print(f"  {exp}/{cfg}: {len(files)} reps")

        # Load all reps
        all_distances = []
        config = None
        for f in files:
            with open(f) as fh:
                data = json.load(fh)
            all_distances.append(data["distances"])
            if config is None:
                config = data["config"]

        # Create DataFrame and compute CIs
        df = pd.DataFrame(all_distances)
        dist_cols = [c for c in df.columns if c.endswith("_distance")]
        data_arr = df[dist_cols].to_numpy()
        res = bootstrap((data_arr,), np.median, axis=0, confidence_level=0.95, n_resamples=1000)
        ci_l, ci_u = res.confidence_interval
        CIs = {dist_cols[i]: {"low": float(ci_l[i]), "high": float(ci_u[i])}
               for i in range(len(dist_cols))}

        exp_results[exp].append({
            "config": config,
            "distances": df.to_dict(),
            "confidence_intervals": CIs,
        })

    # Save
    for exp, results in exp_results.items():
        outfile = output_dir / exp_to_file.get(exp, f"{exp}.json")
        with open(outfile, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  Saved: {outfile} ({len(results)} configs)")


def aggregate_sweep_reps(input_dir, output_dir):
    """Aggregate mega sweep results into a single summary file."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Load all files
    all_results = []
    for f in sorted(input_dir.glob("*.json")):
        with open(f) as fh:
            all_results.append(json.load(fh))

    print(f"Loaded {len(all_results)} sweep results")

    # Group by config (ignoring rep)
    groups = defaultdict(list)
    for r in all_results:
        key = json.dumps(r["config"], sort_keys=True)
        groups[key].append(r["distances"])

    # Summarize each config
    summary = []
    for config_key, distances_list in groups.items():
        config = json.loads(config_key)
        df = pd.DataFrame(distances_list)
        medians = df.median().to_dict()
        stds = df.std().to_dict()
        summary.append({
            "config": config,
            "n_reps": len(distances_list),
            "medians": medians,
            "stds": stds,
        })

    outfile = output_dir / "sweep_summary.json"
    with open(outfile, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {outfile} ({len(summary)} configs)")


def main():
    parser = argparse.ArgumentParser(description="Aggregate per-rep results")
    parser.add_argument("--input-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="experiments/results")
    parser.add_argument("--sweep", action="store_true", help="Aggregate sweep (not experiments)")
    args = parser.parse_args()

    if args.sweep:
        aggregate_sweep_reps(args.input_dir, args.output_dir)
    else:
        aggregate_experiment_reps(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
