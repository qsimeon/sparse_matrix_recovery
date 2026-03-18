"""
Experiment Runner for Sparse Matrix Recovery

Runs systematic experiments (E1-E5) for the workshop paper.
Each experiment tests a specific hypothesis about connectivity recovery.

Usage:
    conda activate work_env
    python experiments/run_experiments.py --experiment E1 --seed 42
    python experiments/run_experiments.py --experiment all --seed 42
    python experiments/run_experiments.py --experiment E3 --wandb
"""

import os
import sys
import json
import argparse
import numpy as np
import torch
import pandas as pd
from pathlib import Path
from scipy.stats import bootstrap

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from experiments.core import (
    get_nonlinearity,
    resolve_params,
    create_multinetwork_dataset,
    estimate_connectivity_weights,
    projected_gradient_causal,
    calculate_spectral_radius,
    adjust_spectral_radius,
)

try:
    import wandb
    HAS_WANDB = True
except ImportError:
    HAS_WANDB = False


# ============================================================================
# Single Repetition
# ============================================================================

def one_repetition(
    repetition_idx, random_seed, num_networks, max_timesteps, num_nodes,
    num_cpgs, num_measured, num_sensors, fixed_sensors, stim_gain,
    nonlinearity_func, non_negative_weights, force_stable, obs_noise_std=0.0,
):
    """Run one repetition of an experiment (one random network topology)."""
    torch.manual_seed(random_seed + repetition_idx)
    np.random.seed(random_seed + repetition_idx)

    dataset = create_multinetwork_dataset(
        num_networks, max_timesteps, num_nodes, num_cpgs,
        num_measured, num_sensors, fixed_sensors, stim_gain,
        nonlinearity_func, non_negative_weights, force_stable,
        obs_noise_std=obs_noise_std,
    )

    estim = estimate_connectivity_weights(num_nodes, dataset)
    approx_W = estim["approx_W"]
    true_W = estim["true_W"]
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

    # Additional baselines: correlation matrix and oracle estimator
    oracle_W = estim["oracle_W"]

    # Correlation baseline: raw cross-correlation (no oracle scaling)
    # This is what you'd compute without knowing W — just normalize cov_dtx
    diag_x = np.sqrt(np.diag(cov_x))
    diag_x[diag_x < 1e-10] = 1e-10
    corr_W = cov_dtx / np.outer(diag_x, diag_x)
    # Do NOT scale to match true W's spectral radius — that would be cheating
    # Instead, scale to unit spectral radius (a reasonable default)
    sr_corr = calculate_spectral_radius(corr_W)
    if sr_corr > 0:
        corr_W = corr_W / sr_corr

    # Distances (normalized by network size)
    distances = {
        "chance_distance": np.linalg.norm(true_W - sample_W, "fro") / num_nodes,
        "adjacency_distance": np.linalg.norm(true_W - adj_sample_W, "fro") / num_nodes,
        "spectral_distance": np.linalg.norm(true_W - spec_adj_sample_W, "fro") / num_nodes,
        "correlation_distance": np.linalg.norm(true_W - corr_W, "fro") / num_nodes,
        "oracle_distance": np.linalg.norm(true_W - oracle_W, "fro") / num_nodes,
        "estimate_distance": np.linalg.norm(true_W - approx_W, "fro") / num_nodes,
        "optimized_distance": np.linalg.norm(true_W - optim_W, "fro") / num_nodes,
    }

    # Edge detection metrics for Granger refinement comparison
    true_edges = (np.abs(true_W) > 0).astype(float)
    est_edges = (np.abs(approx_W) > np.percentile(np.abs(approx_W), 50)).astype(float)
    opt_edges = (np.abs(optim_W) > 0).astype(float)

    np.fill_diagonal(true_edges, 0)
    np.fill_diagonal(est_edges, 0)
    np.fill_diagonal(opt_edges, 0)

    def precision_recall(pred, truth):
        tp = np.sum((pred == 1) & (truth == 1))
        fp = np.sum((pred == 1) & (truth == 0))
        fn = np.sum((pred == 0) & (truth == 1))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        return precision, recall

    est_p, est_r = precision_recall(est_edges, true_edges)
    opt_p, opt_r = precision_recall(opt_edges, true_edges)

    distances["estimate_precision"] = est_p
    distances["estimate_recall"] = est_r
    distances["optimized_precision"] = opt_p
    distances["optimized_recall"] = opt_r

    # Store matrices for later analysis
    matrices = {
        "true_W": true_W,
        "approx_W": approx_W,
        "optim_W": optim_W,
        "cov_x": cov_x,
        "cov_dtx": cov_dtx,
    }

    return distances, matrices


# ============================================================================
# Run Experiment
# ============================================================================

def run_experiment(
    random_seed=42, num_repetitions=17, num_networks=50,
    max_timesteps=900, num_nodes=12, num_cpgs=None, num_measured=None,
    num_sensors=None, fixed_sensors=False, stim_gain=1.0,
    nonlinearity="tanh", non_negative_weights=True, force_stable=True,
    save_matrices=False, obs_noise_std=0.0,
):
    """Run a full experiment with multiple repetitions."""
    assert num_repetitions > 1

    num_cpgs, num_measured, num_sensors = resolve_params(
        num_nodes, num_cpgs, num_measured, num_sensors
    )
    nonlinearity_func = get_nonlinearity(nonlinearity)

    config = dict(
        random_seed=random_seed, num_repetitions=num_repetitions,
        num_networks=num_networks, max_timesteps=max_timesteps,
        num_nodes=num_nodes, num_cpgs=num_cpgs, num_measured=num_measured,
        num_sensors=num_sensors, fixed_sensors=fixed_sensors,
        stim_gain=stim_gain, nonlinearity=nonlinearity,
        non_negative_weights=non_negative_weights, force_stable=force_stable,
    )

    all_distances = []
    all_matrices = []

    for rep in range(num_repetitions):
        print(f"  Repetition {rep+1}/{num_repetitions}...", end=" ", flush=True)
        distances, matrices = one_repetition(
            rep, random_seed, num_networks, max_timesteps, num_nodes,
            num_cpgs, num_measured, num_sensors, fixed_sensors, stim_gain,
            nonlinearity_func, non_negative_weights, force_stable,
            obs_noise_std=obs_noise_std,
        )
        all_distances.append(distances)
        if save_matrices:
            all_matrices.append(matrices)
        print(f"est_dist={distances['estimate_distance']:.4f}")

    distance_df = pd.DataFrame(all_distances)
    distance_df.index.name = "repetition"

    # Bootstrap CI
    dist_cols = [c for c in distance_df.columns if c.endswith("_distance")]
    data = distance_df[dist_cols].to_numpy()
    res = bootstrap((data,), np.median, axis=0, confidence_level=0.95, n_resamples=1000)
    ci_l, ci_u = res.confidence_interval
    CIs = {
        dist_cols[i]: {"low": ci_l[i], "high": ci_u[i]}
        for i in range(len(dist_cols))
    }

    return {
        "config": config,
        "distances": distance_df,
        "confidence_intervals": CIs,
        "matrices": all_matrices if save_matrices else None,
    }


# ============================================================================
# Experiment Definitions (E1-E5)
# ============================================================================

def run_E1_baseline(seed=42, output_dir=None):
    """E1: Baseline recovery across network sizes and recording durations.

    Uses 66% measurement, 33% CPG, 33% sensors, stim=1.0 (favorable conditions).
    """
    print("=" * 60)
    print("E1: Baseline Recovery")
    print("=" * 60)

    results = []
    for num_nodes in [8, 12, 30]:
        num_cpgs = max(1, int(0.33 * num_nodes))
        num_measured = max(2, int(0.66 * num_nodes))
        num_sensors = max(1, int(0.33 * num_nodes))
        for T in [100, 500, 1000]:
            print(f"\n  N={num_nodes}, T={T}, measured={num_measured}")
            r = run_experiment(
                random_seed=seed, num_repetitions=17, num_networks=50,
                max_timesteps=T, num_nodes=num_nodes,
                num_cpgs=num_cpgs, num_measured=num_measured,
                num_sensors=num_sensors,
                stim_gain=1.0, nonlinearity="tanh",
                save_matrices=(num_nodes <= 12),
            )
            r["config"]["experiment"] = "E1"
            results.append(r)

    if output_dir:
        save_results(results, output_dir / "E1_baseline.json")
    return results


def run_E2_sparsity(seed=42, output_dir=None):
    """E2: Effect of measurement sparsity at N=12."""
    print("=" * 60)
    print("E2: Measurement Sparsity Effect")
    print("=" * 60)

    results = []
    num_nodes = 12
    for meas_frac in [0.33, 0.5, 0.66, 0.8, 1.0]:
        num_measured = max(2, int(meas_frac * num_nodes))
        print(f"\n  meas_frac={meas_frac} (num_measured={num_measured})")
        r = run_experiment(
            random_seed=seed, num_repetitions=17, num_networks=50,
            max_timesteps=900, num_nodes=num_nodes,
            num_cpgs=4, num_measured=num_measured, num_sensors=4,
            stim_gain=1.0, nonlinearity="tanh",
        )
        r["config"]["experiment"] = "E2"
        r["config"]["measurement_fraction"] = meas_frac
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E2_sparsity.json")
    return results


def run_E3_stimulation(seed=42, output_dir=None):
    """E3: Stimulation × measurement interaction (2D sweep).

    Tests the control-estimation tradeoff: how does optimal stimulation
    depend on measurement density?
    """
    print("=" * 60)
    print("E3: Stimulation × Measurement Interaction")
    print("=" * 60)

    results = []
    num_nodes = 12
    for meas_frac in [0.33, 0.66, 1.0]:
        num_measured = max(2, int(meas_frac * num_nodes))
        for stim_gain in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]:
            print(f"\n  meas={meas_frac:.0%}, stim_gain={stim_gain}")
            r = run_experiment(
                random_seed=seed, num_repetitions=17, num_networks=50,
                max_timesteps=900, num_nodes=num_nodes,
                num_cpgs=4, num_measured=num_measured, num_sensors=4,
                stim_gain=stim_gain, nonlinearity="tanh",
            )
            r["config"]["experiment"] = "E3"
            r["config"]["measurement_fraction"] = meas_frac
            results.append(r)

    if output_dir:
        save_results(results, output_dir / "E3_stimulation.json")
    return results


def run_E4_granger(seed=42, output_dir=None):
    """E4: Ablation study — each step adds knowledge.

    Compares: Chance > Adjacency > Spectral > Estimate > Granger-refined.
    Uses N=12, 66% measurement, stim=1.0 (favorable conditions).
    """
    print("=" * 60)
    print("E4: Granger Refinement / Ablation Study")
    print("=" * 60)

    results = []
    num_nodes = 12
    r = run_experiment(
        random_seed=seed, num_repetitions=30, num_networks=50,
        max_timesteps=900, num_nodes=num_nodes,
        num_cpgs=4, num_measured=8, num_sensors=4,
        stim_gain=1.0, nonlinearity="tanh", save_matrices=True,
    )
    r["config"]["experiment"] = "E4"
    results.append(r)

    if output_dir:
        save_results(results, output_dir / "E4_granger.json")
    return results


def run_E5_nonlinearity(seed=42, output_dir=None):
    """E5: Robustness to nonlinearity mismatch at N=12."""
    print("=" * 60)
    print("E5: Nonlinearity Robustness")
    print("=" * 60)

    results = []
    num_nodes = 12
    for nl in ["tanh", "relu", "identity", "sigmoid"]:
        print(f"\n  nonlinearity={nl}")
        r = run_experiment(
            random_seed=seed, num_repetitions=17, num_networks=50,
            max_timesteps=900, num_nodes=num_nodes,
            num_cpgs=4, num_measured=8, num_sensors=4,
            stim_gain=1.0, nonlinearity=nl,
        )
        r["config"]["experiment"] = "E5"
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E5_nonlinearity.json")
    return results


def run_E6_oracle_crossover(seed=42, output_dir=None):
    """E6: Oracle vs Approximation — sweep state variance to find crossover.

    Tests the implicit regularization hypothesis: the approximate estimator
    (using Σ_{x,x}) should outperform the oracle (using Σ_{φ(x),x}) when
    state variance is high (saturating tanh regime).
    We control effective state variance via stimulation gain.
    """
    print("=" * 60)
    print("E6: Oracle vs Approximation Crossover")
    print("=" * 60)

    results = []
    num_nodes = 12
    for stim_gain in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
        print(f"\n  stim_gain={stim_gain}")
        r = run_experiment(
            random_seed=seed, num_repetitions=17, num_networks=50,
            max_timesteps=900, num_nodes=num_nodes,
            num_cpgs=4, num_measured=8, num_sensors=4,
            stim_gain=stim_gain, nonlinearity="tanh",
        )
        r["config"]["experiment"] = "E6"
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E6_oracle_crossover.json")
    return results


# ============================================================================
# I/O Helpers
# ============================================================================

def save_results(results, filepath):
    """Save experiment results to JSON (converting DataFrames to dicts)."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    serializable = []
    for r in results:
        entry = {
            "config": r["config"],
            "distances": r["distances"].to_dict(),
            "confidence_intervals": r["confidence_intervals"],
        }
        serializable.append(entry)

    with open(filepath, "w") as f:
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nResults saved to {filepath}")


def log_to_wandb(results, project="sparse_matrix_recovery"):
    """Log experiment results to WandB."""
    if not HAS_WANDB:
        print("WandB not available, skipping logging")
        return

    for r in results:
        config = r["config"]
        run_name = (
            f"{config['experiment']}_N{config['num_nodes']}"
            f"_T{config['max_timesteps']}_stim{config['stim_gain']}"
        )
        with wandb.init(
            entity="qsimeon", project=project,
            config=config, name=run_name, save_code=False,
        ):
            wandb.log({
                "distances_table": wandb.Table(dataframe=r["distances"]),
            })
            medians = r["distances"].median()
            wandb.log({f"median_{k}": v for k, v in medians.items()})
            for ci_name, ci_vals in r["confidence_intervals"].items():
                wandb.log({
                    f"{ci_name}_ci_low": ci_vals["low"],
                    f"{ci_name}_ci_high": ci_vals["high"],
                })


# ============================================================================
# Main
# ============================================================================

EXPERIMENTS = {
    "E1": run_E1_baseline,
    "E2": run_E2_sparsity,
    "E3": run_E3_stimulation,
    "E4": run_E4_granger,
    "E5": run_E5_nonlinearity,
    "E6": run_E6_oracle_crossover,
}


def main():
    parser = argparse.ArgumentParser(
        description="Run sparse matrix recovery experiments"
    )
    parser.add_argument(
        "--experiment", type=str, default="all",
        choices=list(EXPERIMENTS.keys()) + ["all"],
        help="Which experiment to run (default: all)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output-dir", type=str, default="experiments/results",
        help="Output directory for results",
    )
    parser.add_argument("--wandb", action="store_true", help="Log results to WandB")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.experiment == "all":
        experiments = list(EXPERIMENTS.keys())
    else:
        experiments = [args.experiment]

    all_results = {}
    for exp_name in experiments:
        print(f"\n{'#' * 60}")
        print(f"Running {exp_name}")
        print(f"{'#' * 60}\n")
        results = EXPERIMENTS[exp_name](seed=args.seed, output_dir=output_dir)
        all_results[exp_name] = results

        if args.wandb:
            log_to_wandb(results)

    print("\n" + "=" * 60)
    print("All experiments complete!")
    print("=" * 60)

    return all_results


if __name__ == "__main__":
    main()
