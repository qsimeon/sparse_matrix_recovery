#!/usr/bin/env python
"""
Generate Figure 10: Oracle vs. Approximation comparison (E6).

Shows that the "incorrect" linear approximation outperforms the oracle
estimator at all stimulation levels — a key finding of the paper.

Usage:
    uv run python scripts/generate_fig10_oracle.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_DIR = Path("experiments/results")
FIGURES_DIR = Path("paper/figures")

def main():
    # Load E6 data
    with open(RESULTS_DIR / "E6_oracle_crossover.json") as f:
        data = json.load(f)

    # Style matching other paper figures
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.15,
        "figure.dpi": 300, "lines.linewidth": 2,
    })
    PAL = {"blue": "#4477AA", "cyan": "#66CCEE", "green": "#228833",
           "yellow": "#CCBB44", "red": "#EE6677", "purple": "#AA3377"}

    stim_gains = []
    oracle_medians = []
    approx_medians = []
    granger_medians = []
    oracle_all = []
    approx_all = []
    granger_all = []

    for entry in data:
        sigma = entry["config"]["stim_gain"]
        stim_gains.append(sigma)

        oracle_vals = list(entry["distances"]["oracle_distance"].values())
        approx_vals = list(entry["distances"]["estimate_distance"].values())
        granger_vals = list(entry["distances"]["optimized_distance"].values())

        oracle_medians.append(np.median(oracle_vals))
        approx_medians.append(np.median(approx_vals))
        granger_medians.append(np.median(granger_vals))

        oracle_all.append(oracle_vals)
        approx_all.append(approx_vals)
        granger_all.append(granger_vals)

    stim_gains = np.array(stim_gains)
    oracle_medians = np.array(oracle_medians)
    approx_medians = np.array(approx_medians)
    granger_medians = np.array(granger_medians)

    # Bootstrap 95% CI
    def bootstrap_ci(vals_list, n_boot=1000, seed=42):
        rng = np.random.RandomState(seed)
        lows, highs = [], []
        for vals in vals_list:
            arr = np.array(vals)
            boots = [np.median(rng.choice(arr, size=len(arr), replace=True))
                     for _ in range(n_boot)]
            lows.append(np.percentile(boots, 2.5))
            highs.append(np.percentile(boots, 97.5))
        return np.array(lows), np.array(highs)

    oracle_lo, oracle_hi = bootstrap_ci(oracle_all)
    approx_lo, approx_hi = bootstrap_ci(approx_all)
    granger_lo, granger_hi = bootstrap_ci(granger_all)

    # Compute ratio for annotation
    ratios = oracle_medians / approx_medians

    # --- Create figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [2, 1]})

    # Left panel: recovery error vs stimulation gain
    # Use slightly shifted x for readability
    x_plot = np.arange(len(stim_gains))
    x_labels = [str(s) for s in stim_gains]

    # Oracle
    ax1.plot(x_plot, oracle_medians, 'o-', color=PAL["red"], label="Oracle ($\\Sigma_{\\phi(x),x}^{-1}$)",
             markersize=8, zorder=3)
    ax1.fill_between(x_plot, oracle_lo, oracle_hi, color=PAL["red"], alpha=0.15)

    # Approximation (raw)
    ax1.plot(x_plot, approx_medians, 's-', color=PAL["blue"], label="Approximation ($\\Sigma_{x,x}^{-1}$)",
             markersize=8, zorder=3)
    ax1.fill_between(x_plot, approx_lo, approx_hi, color=PAL["blue"], alpha=0.15)

    # Granger-refined
    ax1.plot(x_plot, granger_medians, 'D-', color=PAL["green"], label="Granger-refined",
             markersize=7, zorder=3)
    ax1.fill_between(x_plot, granger_lo, granger_hi, color=PAL["green"], alpha=0.15)

    ax1.set_yscale("log")
    ax1.set_xticks(x_plot)
    ax1.set_xticklabels(x_labels)
    ax1.set_xlabel("Stimulation gain $\\sigma$")
    ax1.set_ylabel("Median recovery error ($\\|W - \\hat{W}\\|_F / N$)")
    ax1.set_title("(A) Oracle vs. Approximation across stimulation levels", fontweight="bold")
    ax1.legend(fontsize=9, loc="upper right")

    # Add individual topology dots
    for i, sigma in enumerate(stim_gains):
        ax1.scatter([x_plot[i]] * len(oracle_all[i]), oracle_all[i],
                   color=PAL["red"], s=10, alpha=0.2, zorder=2)
        ax1.scatter([x_plot[i]] * len(approx_all[i]), approx_all[i],
                   color=PAL["blue"], s=10, alpha=0.2, zorder=2)

    # Right panel: ratio (oracle / approximation)
    ax2.bar(x_plot, ratios, color=PAL["purple"], alpha=0.8, edgecolor="#333333", linewidth=0.5)
    for i, r in enumerate(ratios):
        ax2.text(i, r + 0.1, f"{r:.1f}$\\times$", ha="center", fontsize=9, fontweight="bold")
    ax2.axhline(1.0, color="gray", ls="--", lw=1, label="Parity (oracle = approx)")
    ax2.set_xticks(x_plot)
    ax2.set_xticklabels(x_labels)
    ax2.set_xlabel("Stimulation gain $\\sigma$")
    ax2.set_ylabel("Error ratio (oracle / approximation)")
    ax2.set_title("(B) Oracle penalty factor", fontweight="bold")
    ax2.legend(fontsize=8)

    plt.suptitle("Oracle vs. Approximation: Implicit Regularization (E6)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    output_path = FIGURES_DIR / "fig10_oracle_comparison.pdf"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

    # Print summary for verification
    print("\nMedian values per σ:")
    print(f"{'σ':>6} {'Oracle':>10} {'Approx':>10} {'Granger':>10} {'Ratio':>8}")
    for i, s in enumerate(stim_gains):
        print(f"{s:6.2f} {oracle_medians[i]:10.3f} {approx_medians[i]:10.3f} "
              f"{granger_medians[i]:10.3f} {ratios[i]:7.1f}×")


if __name__ == "__main__":
    main()
