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

def one_repetition(rep_idx, seed, num_sessions, max_timesteps, num_nodes,
                   num_cpgs, num_measured, num_stimulated, stim_gain,
                   nonlinearity_name, non_negative_weights=True,
                   force_stable=True, fixed_stim=False, obs_noise_std=0.0,
                   return_matrices=False):
    """
    Run one repetition: generate a random topology, simulate K sessions,
    estimate connectivity, evaluate against ground truth.

    This is THE canonical implementation. Both run_experiments.py and
    run_single_rep.py call this function.

    Args:
        return_matrices: If True, also return (distances, matrices) tuple
                        where matrices contains true_W, approx_W, optim_W, etc.
                        If False, return distances dict only.
    """
    torch.manual_seed(seed + rep_idx)
    np.random.seed(seed + rep_idx)

    phi = get_nonlinearity(nonlinearity_name)

    # Simulate K=num_sessions sessions with shared topology
    dataset = create_multinetwork_dataset(
        num_sessions, max_timesteps, num_nodes, num_cpgs,
        num_measured, num_stimulated, fixed_stim, stim_gain,
        phi, non_negative_weights, force_stable, obs_noise_std,
    )

    # Estimate connectivity
    estim = estimate_connectivity_weights(num_nodes, dataset)
    true_W = estim["true_W"]
    approx_W = estim["approx_W"]
    Adj = estim["Adj"]
    cov_x = estim["cov_x"]
    cov_dtx = estim["cov_dtx"]

    # Granger refinement
    _, optim_W = projected_gradient_causal(
        cov_x, cov_dtx, non_negative_weights=non_negative_weights,
    )

    # Baselines
    eps = np.finfo(float).eps
    if non_negative_weights:
        sample_W = eps + np.random.rand(*true_W.shape)
    else:
        sample_W = 2 * (eps + np.random.rand(*true_W.shape) - 0.5)
    adj_sample_W = Adj * sample_W
    spec_adj_sample_W = adjust_spectral_radius(
        adj_sample_W, target_radius=calculate_spectral_radius(true_W)
    )
    oracle_W = estim["oracle_W"]

    # Correlation baseline
    diag_x = np.sqrt(np.diag(cov_x))
    diag_x[diag_x < 1e-10] = 1e-10
    corr_W = cov_dtx / np.outer(diag_x, diag_x)
    sr_corr = calculate_spectral_radius(corr_W)
    if sr_corr > 0:
        corr_W = corr_W / sr_corr

    # Distances (normalized by N, cast to float for JSON serialization)
    distances = {
        "chance_distance": float(np.linalg.norm(true_W - sample_W, "fro") / num_nodes),
        "adjacency_distance": float(np.linalg.norm(true_W - adj_sample_W, "fro") / num_nodes),
        "spectral_distance": float(np.linalg.norm(true_W - spec_adj_sample_W, "fro") / num_nodes),
        "correlation_distance": float(np.linalg.norm(true_W - corr_W, "fro") / num_nodes),
        "oracle_distance": float(np.linalg.norm(true_W - oracle_W, "fro") / num_nodes),
        "estimate_distance": float(np.linalg.norm(true_W - approx_W, "fro") / num_nodes),
        "optimized_distance": float(np.linalg.norm(true_W - optim_W, "fro") / num_nodes),
    }

    # Edge detection metrics for both estimate and Granger-refined
    true_edges = (np.abs(true_W) > 0).astype(float)
    est_edges = (np.abs(approx_W) > np.percentile(np.abs(approx_W), 50)).astype(float)
    opt_edges = (np.abs(optim_W) > 0).astype(float)
    np.fill_diagonal(true_edges, 0)
    np.fill_diagonal(est_edges, 0)
    np.fill_diagonal(opt_edges, 0)

    def _precision_recall(pred, truth):
        tp = float(np.sum((pred == 1) & (truth == 1)))
        fp = float(np.sum((pred == 1) & (truth == 0)))
        fn = float(np.sum((pred == 0) & (truth == 1)))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        return prec, rec

    est_p, est_r = _precision_recall(est_edges, true_edges)
    opt_p, opt_r = _precision_recall(opt_edges, true_edges)
    distances["estimate_precision"] = est_p
    distances["estimate_recall"] = est_r
    distances["optimized_precision"] = opt_p
    distances["optimized_recall"] = opt_r

    if return_matrices:
        matrices = {
            "true_W": true_W, "approx_W": approx_W, "optim_W": optim_W,
            "cov_x": cov_x, "cov_dtx": cov_dtx,
        }
        return distances, matrices

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
    parser.add_argument("--num-sessions", type=int, default=50, help="Recording sessions per topology (K in paper)")
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
    # Labeling
    parser.add_argument("--task-id", type=int, help="SLURM task ID (used in output filename for sweeps)")
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
    result_data = one_repetition(
        args.rep, args.seed, args.num_sessions,
        config["max_timesteps"], config["num_nodes"], config.get("num_cpgs", 5),
        config["num_measured"], config["num_stimulated"],
        config["stim_gain"], config["nonlinearity"],
        return_matrices=args.wandb,  # return matrices for WandB figure logging
    )
    if args.wandb:
        distances, _ = result_data
    else:
        distances = result_data

    # Save — use task_id in filename for sweeps to avoid collisions
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg_id = args.task_id if args.task_id is not None else args.config_idx
    filename = f"{label}_cfg{cfg_id:03d}_rep{args.rep:03d}.json"
    result = {"config": config, "rep": args.rep, "seed": args.seed, "distances": distances}
    with open(output_dir / filename, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  -> {output_dir / filename}")

    # Optional WandB logging with rich figures
    if args.wandb:
        try:
            import wandb
            import matplotlib.pyplot as plt

            wandb.init(project="sparse_matrix_recovery", entity="qsimeon",
                       config={**config, "rep": args.rep, "experiment": label},
                       name=f"{label}_c{cfg_id:03d}_r{args.rep:03d}")

            # Log scalar metrics
            wandb.log(distances)

            # Log weight matrix comparison figure if we have matrices
            if isinstance(result_data, tuple):
                _, matrices = result_data
                fig, axes = plt.subplots(1, 3, figsize=(12, 4))
                vmax = matrices["true_W"].max()
                axes[0].imshow(matrices["true_W"], cmap="Reds", vmin=0, vmax=vmax)
                axes[0].set_title("True W")
                axes[1].imshow(matrices["approx_W"], cmap="RdBu_r", vmin=-vmax, vmax=vmax)
                axes[1].set_title("Estimate")
                axes[2].imshow(matrices["optim_W"], cmap="Reds", vmin=0, vmax=vmax)
                axes[2].set_title("Granger-refined")
                plt.tight_layout()
                wandb.log({"weight_matrices": wandb.Image(fig)})
                plt.close()

            wandb.finish()
        except Exception as e:
            print(f"  WandB error: {e}")


if __name__ == "__main__":
    main()
