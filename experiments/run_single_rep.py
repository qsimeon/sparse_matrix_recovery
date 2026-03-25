#!/usr/bin/env python
"""
Run a SINGLE repetition of a SINGLE experiment configuration.

This is the atomic unit of work for parallelized execution:
- SLURM job arrays: each array task calls this with different --rep
- WandB sweep: wandb agent calls this with sweep-sampled params
- GNU parallel: pipe a list of commands into parallel
- Debugging: run one rep to inspect a single topology

Design principle: ONE script call = ONE random network topology =
ONE JSON output file. No loops, no aggregation — just atomic work.

Usage examples:
    # Run rep 7 of E2 (Granger ablation)
    python run_single_rep.py --experiment E2 --rep 7 --seed 42

    # Run a custom config (e.g., from WandB sweep)
    python run_single_rep.py --num-nodes 15 --max-timesteps 1000 \\
        --stim-gain 0.5 --measurement-frac 0.66 --rep 3 --seed 42

    # Results go to experiments/results/reps/<experiment>_cfg000_rep007.json
"""

import sys
import json
import argparse
import numpy as np
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from experiments.core import (
    get_nonlinearity,
    create_multinetwork_dataset,
    estimate_connectivity_weights,
    projected_gradient_causal,
    calculate_spectral_radius,
    adjust_spectral_radius,
)


# ============================================================================
# The core computation: one repetition
# ============================================================================

def one_repetition(rep_idx, seed, num_networks, max_timesteps, num_nodes,
                   num_cpgs, num_measured, num_stimulated, stim_gain,
                   nonlinearity_name, obs_noise_std=0.0):
    """
    Run one repetition: generate a random topology, simulate K sessions,
    estimate connectivity, evaluate against ground truth.

    The seed + rep_idx combination ensures each rep is deterministic
    and reproducible regardless of execution order.
    """
    torch.manual_seed(seed + rep_idx)
    np.random.seed(seed + rep_idx)

    phi = get_nonlinearity(nonlinearity_name)

    # Simulate K=num_networks sessions with shared topology
    dataset = create_multinetwork_dataset(
        num_networks, max_timesteps, num_nodes, num_cpgs,
        num_measured, num_stimulated, False, stim_gain,
        phi, True, True, obs_noise_std,
    )

    # Estimate connectivity
    estim = estimate_connectivity_weights(num_nodes, dataset)
    true_W = estim["true_W"]
    approx_W = estim["approx_W"]
    Adj = estim["Adj"]

    # Granger refinement
    _, optim_W = projected_gradient_causal(
        estim["cov_x"], estim["cov_dtx"], non_negative_weights=True,
    )

    # Baselines
    eps = np.finfo(float).eps
    sample_W = eps + np.random.rand(*true_W.shape)
    adj_sample_W = Adj * sample_W
    spec_adj_sample_W = adjust_spectral_radius(
        adj_sample_W, target_radius=calculate_spectral_radius(true_W)
    )

    # Distances (normalized by N)
    distances = {
        "chance_distance": float(np.linalg.norm(true_W - sample_W, "fro") / num_nodes),
        "adjacency_distance": float(np.linalg.norm(true_W - adj_sample_W, "fro") / num_nodes),
        "spectral_distance": float(np.linalg.norm(true_W - spec_adj_sample_W, "fro") / num_nodes),
        "oracle_distance": float(np.linalg.norm(true_W - estim["oracle_W"], "fro") / num_nodes),
        "estimate_distance": float(np.linalg.norm(true_W - approx_W, "fro") / num_nodes),
        "optimized_distance": float(np.linalg.norm(true_W - optim_W, "fro") / num_nodes),
    }

    # Edge detection metrics
    true_edges = (np.abs(true_W) > 0).astype(float)
    opt_edges = (np.abs(optim_W) > 0).astype(float)
    np.fill_diagonal(true_edges, 0)
    np.fill_diagonal(opt_edges, 0)
    tp = float(np.sum((opt_edges == 1) & (true_edges == 1)))
    fp = float(np.sum((opt_edges == 1) & (true_edges == 0)))
    fn = float(np.sum((opt_edges == 0) & (true_edges == 1)))
    distances["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    distances["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return distances


# ============================================================================
# Experiment configurations (matching run_experiments.py)
# ============================================================================

def get_experiment_configs(experiment):
    """
    Return a list of config dicts for a given experiment.
    Each config is one 'condition' (e.g., one N×T combination in E1).
    The caller picks which config via --config-idx.
    """
    N = 15  # default baseline

    if experiment == "E1":
        return [
            {"num_nodes": n, "max_timesteps": t,
             "num_cpgs": max(1, int(0.33*n)), "num_measured": max(2, int(0.66*n)),
             "num_stimulated": max(1, int(0.33*n)), "stim_gain": 1.0, "nonlinearity": "tanh"}
            for n in [8, 15, 30] for t in [100, 500, 1000]
        ]
    elif experiment == "E2":  # Granger ablation (single config)
        return [{"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
                 "num_measured": 10, "num_stimulated": 5, "stim_gain": 1.0, "nonlinearity": "tanh"}]
    elif experiment == "E3":  # Stim × measurement
        return [
            {"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
             "num_measured": max(2, int(mf*N)), "num_stimulated": 5,
             "stim_gain": sg, "nonlinearity": "tanh"}
            for mf in [0.33, 0.66, 1.0] for sg in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
        ]
    elif experiment == "E4":  # Measurement sparsity
        return [
            {"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
             "num_measured": max(2, int(mf*N)), "num_stimulated": 5,
             "stim_gain": 1.0, "nonlinearity": "tanh"}
            for mf in [0.33, 0.5, 0.66, 0.8, 1.0]
        ]
    elif experiment == "E5":  # Nonlinearity
        return [
            {"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
             "num_measured": 10, "num_stimulated": 5, "stim_gain": 1.0, "nonlinearity": nl}
            for nl in ["tanh", "relu", "identity", "sigmoid"]
        ]
    elif experiment == "E6":  # Oracle crossover
        return [
            {"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
             "num_measured": 10, "num_stimulated": 5, "stim_gain": sg, "nonlinearity": "tanh"}
            for sg in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        ]
    elif experiment == "E7":  # Stim fraction
        return [
            {"num_nodes": N, "max_timesteps": 1000, "num_cpgs": 5,
             "num_measured": 10, "num_stimulated": ns, "stim_gain": 1.0, "nonlinearity": "tanh"}
            for ns in [0, 5, 7, 10, 15]
        ]
    else:
        raise ValueError(f"Unknown experiment: {experiment}")


def main():
    parser = argparse.ArgumentParser(
        description="Run a single experiment repetition (atomic unit for parallel execution)")
    # Experiment mode
    parser.add_argument("--experiment", type=str, help="Experiment name (E1-E7)")
    parser.add_argument("--config-idx", type=int, default=0,
                        help="Which config within the experiment's sweep (0-indexed)")
    # Always required
    parser.add_argument("--rep", type=int, required=True, help="Repetition index (0-49)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--num-networks", type=int, default=50, help="Sessions per topology")
    parser.add_argument("--output-dir", type=str, default="experiments/results/reps")
    # Override params (for WandB sweep or custom configs)
    parser.add_argument("--num-nodes", type=int)
    parser.add_argument("--max-timesteps", type=int)
    parser.add_argument("--num-measured", type=int)
    parser.add_argument("--num-stimulated", type=int)
    parser.add_argument("--stim-gain", type=float)
    parser.add_argument("--nonlinearity", type=str)
    parser.add_argument("--measurement-frac", type=float,
                        help="Shorthand: sets num_measured = int(frac * num_nodes)")
    # WandB
    parser.add_argument("--wandb", action="store_true", help="Log to WandB")
    args = parser.parse_args()

    # Build config
    if args.experiment:
        configs = get_experiment_configs(args.experiment)
        if args.config_idx >= len(configs):
            print(f"Config index {args.config_idx} out of range (0-{len(configs)-1})")
            sys.exit(1)
        config = configs[args.config_idx]
    else:
        config = {"num_nodes": 15, "max_timesteps": 1000, "num_cpgs": 5,
                  "num_measured": 10, "num_stimulated": 5, "stim_gain": 1.0, "nonlinearity": "tanh"}

    # Apply explicit overrides
    for key, arg_name in [("num_nodes", "num_nodes"), ("max_timesteps", "max_timesteps"),
                          ("num_measured", "num_measured"), ("num_stimulated", "num_stimulated"),
                          ("stim_gain", "stim_gain"), ("nonlinearity", "nonlinearity")]:
        val = getattr(args, arg_name, None)
        if val is not None:
            config[key] = val
    if args.measurement_frac is not None:
        config["num_measured"] = max(2, int(args.measurement_frac * config["num_nodes"]))

    # Run
    label = args.experiment or "custom"
    print(f"[{label} cfg={args.config_idx} rep={args.rep}] {config}")
    distances = one_repetition(
        args.rep, args.seed, args.num_networks,
        config["max_timesteps"], config["num_nodes"], config.get("num_cpgs", 5),
        config["num_measured"], config["num_stimulated"],
        config["stim_gain"], config["nonlinearity"],
    )

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{label}_cfg{args.config_idx:03d}_rep{args.rep:03d}.json"
    result = {"config": config, "rep": args.rep, "seed": args.seed, "distances": distances}
    with open(output_dir / filename, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  -> {output_dir / filename}")

    # Optional WandB logging
    if args.wandb:
        try:
            import wandb
            wandb.init(project="sparse_matrix_recovery", entity="qsimeon",
                       config={**config, "rep": args.rep, "experiment": label},
                       name=f"{label}_c{args.config_idx:03d}_r{args.rep:03d}")
            wandb.log(distances)
            wandb.finish()
        except Exception as e:
            print(f"  WandB error: {e}")


if __name__ == "__main__":
    main()
