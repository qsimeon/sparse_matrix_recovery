"""
Experiment Runner for Sparse Matrix Recovery

Runs systematic experiments (E1-E7) for the paper.
Each experiment tests a specific hypothesis about connectivity recovery.

Usage:
    conda activate work_env
    python experiments/run_experiments.py --experiment E1 --seed 42
    python experiments/run_experiments.py --experiment all --seed 42
    python experiments/run_experiments.py --experiment E3 --wandb
"""

import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import bootstrap

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from experiments.core import resolve_params

try:
    import wandb
    HAS_WANDB = True
except ImportError:
    HAS_WANDB = False

# Import the canonical one_repetition from run_single_rep
from experiments.run_single_rep import one_repetition


# ============================================================================
# Run Experiment
# ============================================================================

def run_experiment(
    random_seed=42, num_networks=10, num_sessions=50,
    max_timesteps=1000, num_nodes=15, num_cpgs=None, num_measured=None,
    num_stimulated=None, fixed_stim=False, stim_gain=1.0,
    nonlinearity="tanh", non_negative_weights=True, force_stable=True,
    save_matrices=False, obs_noise_std=0.0,
):
    """Run a full experiment with multiple repetitions."""
    assert num_networks > 1

    num_cpgs, num_measured, num_stimulated = resolve_params(
        num_nodes, num_cpgs, num_measured, num_stimulated
    )

    config = dict(
        random_seed=random_seed, num_networks=num_networks,
        num_sessions=num_sessions, max_timesteps=max_timesteps,
        num_nodes=num_nodes, num_cpgs=num_cpgs, num_measured=num_measured,
        num_stimulated=num_stimulated, fixed_stim=fixed_stim,
        stim_gain=stim_gain, nonlinearity=nonlinearity,
        non_negative_weights=non_negative_weights, force_stable=force_stable,
    )

    all_distances = []
    all_matrices = []

    for rep in range(num_networks):
        print(f"  Repetition {rep+1}/{num_networks}...", end=" ", flush=True)
        result = one_repetition(
            rep, random_seed, num_sessions, max_timesteps, num_nodes,
            num_cpgs, num_measured, num_stimulated, stim_gain,
            nonlinearity, non_negative_weights=non_negative_weights,
            force_stable=force_stable, fixed_stim=fixed_stim,
            obs_noise_std=obs_noise_std, return_matrices=save_matrices,
        )
        if save_matrices:
            distances, matrices = result
            all_matrices.append(matrices)
        else:
            distances = result
        all_distances.append(distances)
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

    # Statistical tests: pairwise comparisons between key methods
    from scipy.stats import mannwhitneyu
    stat_tests = {}
    pairs = [
        ("estimate_distance", "chance_distance", "estimate_vs_chance"),
        ("optimized_distance", "estimate_distance", "granger_vs_estimate"),
        ("estimate_distance", "oracle_distance", "estimate_vs_oracle"),
    ]
    for col_a, col_b, label in pairs:
        if col_a in distance_df.columns and col_b in distance_df.columns:
            a = distance_df[col_a].values
            b = distance_df[col_b].values
            try:
                stat, p = mannwhitneyu(a, b, alternative="less")
                stat_tests[label] = {"U": float(stat), "p": float(p), "n": len(a)}
            except Exception:
                pass

    return {
        "config": config,
        "distances": distance_df,
        "confidence_intervals": CIs,
        "statistical_tests": stat_tests,
        "matrices": all_matrices if save_matrices else None,
    }


# ============================================================================
# Experiment Definitions (E1-E7)
# ============================================================================

def run_E1_baseline(seed=42, output_dir=None):
    """E1: Baseline recovery across network sizes and recording durations.

    Uses 66% measurement, 33% CPG, 33% stimulated, stim=1.0 (favorable conditions).
    """
    print("=" * 60)
    print("E1: Baseline Recovery")
    print("=" * 60)

    results = []
    # N values divisible by 3 so 33%/66% fractions give exact integers
    for num_nodes in [15, 30, 159, 300, 1074]:
        num_cpgs = max(1, int(0.33 * num_nodes))
        num_measured = max(2, int(0.66 * num_nodes))
        num_stimulated = max(1, int(0.33 * num_nodes))
        for T in [100, 250, 500, 750, 1000]:
            print(f"\n  N={num_nodes}, T={T}, measured={num_measured}")
            r = run_experiment(
                random_seed=seed, num_networks=10, num_sessions=50,
                max_timesteps=T, num_nodes=num_nodes,
                num_cpgs=num_cpgs, num_measured=num_measured,
                num_stimulated=num_stimulated,
                stim_gain=1.0, nonlinearity="tanh",
                save_matrices=(num_nodes <= 30),
            )
            r["config"]["experiment"] = "E1"
            results.append(r)

    if output_dir:
        save_results(results, output_dir / "E1_baseline.json")
    return results


def run_E4_sparsity(seed=42, output_dir=None):
    """E4: Effect of measurement sparsity at N=15."""
    print("=" * 60)
    print("E4: Measurement Sparsity Effect")
    print("=" * 60)

    results = []
    num_nodes = 15
    for meas_frac in [0.33, 0.5, 0.66, 0.8, 1.0]:
        num_measured = max(2, int(meas_frac * num_nodes))
        print(f"\n  meas_frac={meas_frac} (num_measured={num_measured})")
        r = run_experiment(
            random_seed=seed, num_networks=10, num_sessions=50,
            max_timesteps=1000, num_nodes=num_nodes,
            num_cpgs=5, num_measured=num_measured, num_stimulated=5,
            stim_gain=1.0, nonlinearity="tanh",
        )
        r["config"]["experiment"] = "E4"
        r["config"]["measurement_fraction"] = meas_frac
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E4_sparsity.json")
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
    num_nodes = 15
    for meas_frac in [0.33, 0.66, 1.0]:
        num_measured = max(2, int(meas_frac * num_nodes))
        for stim_gain in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]:
            print(f"\n  meas={meas_frac:.0%}, stim_gain={stim_gain}")
            r = run_experiment(
                random_seed=seed, num_networks=10, num_sessions=50,
                max_timesteps=1000, num_nodes=num_nodes,
                num_cpgs=5, num_measured=num_measured, num_stimulated=5,
                stim_gain=stim_gain, nonlinearity="tanh",
            )
            r["config"]["experiment"] = "E3"
            r["config"]["measurement_fraction"] = meas_frac
            results.append(r)

    if output_dir:
        save_results(results, output_dir / "E3_stimulation.json")
    return results


def run_E2_granger(seed=42, output_dir=None):
    """E2: Ablation study — each step adds knowledge.

    Compares: Chance > Adjacency > Spectral > Estimate > Granger-refined.
    Uses N=15, 66% measurement, stim=1.0 (favorable conditions).
    """
    print("=" * 60)
    print("E2: Granger Refinement / Ablation Study")
    print("=" * 60)

    results = []
    num_nodes = 15
    r = run_experiment(
        random_seed=seed, num_networks=10, num_sessions=50,
        max_timesteps=1000, num_nodes=num_nodes,
        num_cpgs=5, num_measured=10, num_stimulated=5,
        stim_gain=1.0, nonlinearity="tanh", save_matrices=True,
    )
    r["config"]["experiment"] = "E2"
    results.append(r)

    if output_dir:
        save_results(results, output_dir / "E2_granger.json")
    return results


def run_E5_nonlinearity(seed=42, output_dir=None):
    """E5: Robustness to nonlinearity mismatch at N=15."""
    print("=" * 60)
    print("E5: Nonlinearity Robustness")
    print("=" * 60)

    results = []
    num_nodes = 15
    for nl in ["tanh", "relu", "identity", "sigmoid"]:
        print(f"\n  nonlinearity={nl}")
        r = run_experiment(
            random_seed=seed, num_networks=10, num_sessions=50,
            max_timesteps=1000, num_nodes=num_nodes,
            num_cpgs=5, num_measured=10, num_stimulated=5,
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
    num_nodes = 15
    for stim_gain in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
        print(f"\n  stim_gain={stim_gain}")
        r = run_experiment(
            random_seed=seed, num_networks=10, num_sessions=50,
            max_timesteps=1000, num_nodes=num_nodes,
            num_cpgs=5, num_measured=10, num_stimulated=5,
            stim_gain=stim_gain, nonlinearity="tanh",
        )
        r["config"]["experiment"] = "E6"
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E6_oracle_crossover.json")
    return results


def run_E7_stim_fraction(seed=42, output_dir=None):
    """E7: How many neurons to stimulate (stimulation coverage).

    Varies the fraction of neurons receiving extrinsic stimulation,
    independently of stimulation gain. This answers: 'Does it matter
    how many neurons you poke, or just how hard?'

    Stimulation fraction controls the rank of the stimulation covariance:
    with 1 stimulated neuron, only 1 direction in state space is directly excited;
    with N stimulated, all directions receive independent noise.
    """
    print("=" * 60)
    print("E7: Stimulation Fraction Sweep")
    print("=" * 60)

    results = []
    num_nodes = 30
    # Sweep: 0%, 33%, 50%, 66%, 100% of N=30
    for num_stimulated in [0, 10, 15, 20, 30]:
        stim_frac = num_stimulated / num_nodes
        print(f"\n  num_stimulated={num_stimulated} ({stim_frac:.0%} of N={num_nodes})")
        r = run_experiment(
            random_seed=seed, num_networks=10, num_sessions=50,
            max_timesteps=1000, num_nodes=num_nodes,
            num_cpgs=10, num_measured=20, num_stimulated=num_stimulated,
            stim_gain=1.0, nonlinearity="tanh",
        )
        r["config"]["experiment"] = "E7"
        r["config"]["stim_fraction"] = stim_frac
        results.append(r)

    if output_dir:
        save_results(results, output_dir / "E7_stim_fraction.json")
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
    "E2": run_E2_granger,
    "E3": run_E3_stimulation,
    "E4": run_E4_sparsity,
    "E5": run_E5_nonlinearity,
    "E6": run_E6_oracle_crossover,
    "E7": run_E7_stim_fraction,
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
