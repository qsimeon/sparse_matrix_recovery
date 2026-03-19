#!/usr/bin/env python
"""
Generate ALL paper figures from experiment data.

Run this single script to regenerate every figure in the paper:
    uv run python scripts/generate_all_figures.py

Figures are saved to paper/figures/fig1_*.pdf through fig8_*.pdf.
Requires experiment results in experiments/results/ (run experiments first).
"""

import sys
import numpy as np
import torch
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from sklearn.decomposition import PCA
from scipy.signal import welch
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.analysis import (
    load_results,
    generate_problem_schematic,
    generate_pipeline_schematic,
    plot_scaling,
    plot_granger_comparison,
    plot_stimulation_tradeoff,
    plot_sparsity_effect,
    plot_nonlinearity_robustness,
)
from experiments.core import (
    random_network_topology,
    create_network_data,
    create_multinetwork_dataset,
    estimate_connectivity_weights,
    projected_gradient_causal,
    get_nonlinearity,
)

RESULTS_DIR = Path("experiments/results")
FIGURES_DIR = Path("paper/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_fig8_dynamics(output_path):
    """Figure 8: Dynamics, CPG detection, and error analysis (9-panel)."""
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.15,
        "figure.dpi": 300, "lines.linewidth": 2,
    })
    PAL = {"blue": "#4477AA", "cyan": "#66CCEE", "green": "#228833",
           "yellow": "#CCBB44", "red": "#EE6677", "purple": "#AA3377"}

    np.random.seed(42); torch.manual_seed(42)
    phi = get_nonlinearity("tanh"); N = 12
    W, _ = random_network_topology(N, non_negative_weights=True, force_stable=True)

    # Autonomous dynamics (no stim, all measured)
    data_auto = create_network_data(0, 1000, N, 4, N, 0, True, 0.0, phi, W)
    # Stimulated dynamics
    np.random.seed(42); torch.manual_seed(42)
    data_stim = create_network_data(0, 1000, N, 4, N, 4, False, 1.0, phi, W)

    X_auto = data_auto["activity_data"]
    X_stim = data_stim["activity_data"]
    cpg_nodes = np.where(data_auto["cpg_nodes_mask"])[0]
    non_cpg = np.where(~data_auto["cpg_nodes_mask"])[0]

    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 3, hspace=0.45, wspace=0.4)

    # (A) Autonomous time series
    ax = fig.add_subplot(gs[0, 0])
    for i in cpg_nodes[:2]:
        ax.plot(X_auto[:200, i], label=f"CPG n{i}", alpha=0.8)
    for i in non_cpg[:2]:
        ax.plot(X_auto[:200, i], label=f"n{i}", alpha=0.5, ls="--")
    ax.set_xlabel("Time"); ax.set_ylabel("Activity")
    ax.set_title("(A) Autonomous dynamics", fontweight="bold"); ax.legend(fontsize=7)

    # (B) Stimulated time series
    ax = fig.add_subplot(gs[0, 1])
    for i in cpg_nodes[:2]:
        ax.plot(X_stim[:200, i], label=f"CPG n{i}", alpha=0.8)
    for i in non_cpg[:2]:
        ax.plot(X_stim[:200, i], label=f"n{i}", alpha=0.5, ls="--")
    ax.set_xlabel("Time"); ax.set_ylabel("Activity")
    ax.set_title("(B) With stimulation", fontweight="bold"); ax.legend(fontsize=7)

    # (C) CPG drive signals
    ax = fig.add_subplot(gs[0, 2])
    cpg_drive = data_auto["intrinsic_input_matrix"]
    for i in cpg_nodes[:3]:
        ax.plot(cpg_drive[:200, i], label=f"CPG n{i}", alpha=0.8)
    ax.set_xlabel("Time"); ax.set_ylabel("CPG drive")
    ax.set_title("(C) Intrinsic CPG signals", fontweight="bold"); ax.legend(fontsize=8)

    # (D) Phase portrait — autonomous
    ax = fig.add_subplot(gs[1, 0])
    pca = PCA(n_components=2)
    Xp = pca.fit_transform(X_auto)
    ax.scatter(Xp[:, 0], Xp[:, 1], c=range(len(Xp)), cmap="viridis", s=3, alpha=0.6)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%})")
    ax.set_title("(D) Phase portrait (autonomous)", fontweight="bold")

    # (E) Phase portrait — stimulated
    ax = fig.add_subplot(gs[1, 1])
    Xps = pca.transform(X_stim)
    ax.scatter(Xps[:, 0], Xps[:, 1], c=range(len(Xps)), cmap="magma", s=3, alpha=0.6)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("(E) Phase portrait (stimulated)", fontweight="bold")

    # (F) Power spectrum comparison
    ax = fig.add_subplot(gs[1, 2])
    for label, X_data, color in [("Autonomous", X_auto, PAL["blue"]),
                                   ("Stimulated", X_stim, PAL["red"])]:
        psds = [welch(X_data[:, i], nperseg=min(128, len(X_data) // 2))[1] for i in range(N)]
        f = welch(X_data[:, 0], nperseg=min(128, len(X_data) // 2))[0]
        ax.semilogy(f, np.mean(psds, axis=0), label=label, color=color)
    ax.set_xlabel("Frequency"); ax.set_ylabel("PSD")
    ax.set_title("(F) Power spectrum", fontweight="bold"); ax.legend(fontsize=9)

    # (G) Per-node variance — CPG detection
    ax = fig.add_subplot(gs[2, 0])
    vars_auto = np.var(X_auto, axis=0)
    colors = [PAL["red"] if data_auto["cpg_nodes_mask"][i] else PAL["blue"] for i in range(N)]
    ax.bar(range(N), vars_auto, color=colors, alpha=0.8, edgecolor="#333333", linewidth=0.5)
    ax.axhline(np.median(vars_auto), color="gray", ls="--", label="Median threshold")
    ax.set_xlabel("Neuron"); ax.set_ylabel("Activity variance")
    ax.set_title("(G) Per-node variance (CPG=red)", fontweight="bold"); ax.legend(fontsize=8)

    # (H) Error decomposition
    np.random.seed(42); torch.manual_seed(42)
    ds = create_multinetwork_dataset(50, 900, N, 4, 8, 4, False, 1.0, phi, True, True)
    est = estimate_connectivity_weights(N, ds)
    cov_x_inv = np.linalg.pinv(est["cov_x"])
    E1 = est["true_W"] @ (est["cov_phix"] @ cov_x_inv - np.eye(N))
    E2 = est["cov_bx"] @ cov_x_inv
    ax = fig.add_subplot(gs[2, 1])
    vals = [np.linalg.norm(E1, "fro") / N, np.linalg.norm(E2, "fro") / N,
            np.linalg.norm(est["approx_W"] - est["true_W"], "fro") / N]
    ax.bar(["$E_1$ (model)", "$E_2$ (CPG corr.)", "Total"],
           vals, color=[PAL["blue"], PAL["red"], PAL["purple"]], alpha=0.85)
    for j, v in enumerate(vals):
        ax.text(j, v + 0.005, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("||.||_F / N"); ax.set_title("(H) Error decomposition", fontweight="bold")

    # (I) True vs estimated weights
    ax = fig.add_subplot(gs[2, 2])
    _, grn = projected_gradient_causal(est["cov_x"], est["cov_dtx"])
    tf, ef = est["true_W"].flatten(), grn.flatten()
    ax.scatter(tf, ef, s=5, alpha=0.4, color=PAL["green"])
    ax.plot([0, tf.max()], [0, tf.max()], "k--", lw=1)
    r = np.corrcoef(tf, ef)[0, 1]
    ax.set_xlabel("True $W_{ij}$"); ax.set_ylabel("Estimated $\\hat{W}_{ij}$")
    ax.set_title(f"(I) True vs estimated (r={r:.3f})", fontweight="bold")

    plt.suptitle("Network Dynamics, CPG Detection, and Recovery Analysis",
                 fontsize=14, fontweight="bold", y=1.01)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path} (r={r:.3f})")


def main():
    print("=" * 60)
    print("  Generating ALL paper figures")
    print("=" * 60)

    # Fig 1: Problem schematic (no data needed)
    print("\nFig 1: Problem schematic")
    generate_problem_schematic(FIGURES_DIR / "fig1_problem_schematic.pdf")

    # Fig 2: Pipeline schematic (no data needed)
    print("\nFig 2: Pipeline schematic")
    generate_pipeline_schematic(FIGURES_DIR / "fig2_pipeline.pdf")

    # Fig 3: Scaling (E1 data)
    print("\nFig 3: Scaling (E1)")
    data = load_results(RESULTS_DIR / "E1_baseline.json")
    plot_scaling(data, FIGURES_DIR / "fig3_scaling.pdf")

    # Fig 4: Granger refinement (E4 data)
    print("\nFig 4: Granger refinement (E4)")
    data = load_results(RESULTS_DIR / "E4_granger.json")
    plot_granger_comparison(data, FIGURES_DIR / "fig4_granger_refinement.pdf")

    # Fig 5: Stimulation tradeoff (E3 data)
    print("\nFig 5: Stimulation tradeoff (E3)")
    data = load_results(RESULTS_DIR / "E3_stimulation.json")
    plot_stimulation_tradeoff(data, FIGURES_DIR / "fig5_stimulation.pdf")

    # Fig 6: Measurement sparsity (E2 data)
    print("\nFig 6: Measurement sparsity (E2)")
    data = load_results(RESULTS_DIR / "E2_sparsity.json")
    plot_sparsity_effect(data, FIGURES_DIR / "fig6_sparsity.pdf")

    # Fig 7: Nonlinearity robustness (E5 data)
    print("\nFig 7: Nonlinearity robustness (E5)")
    data = load_results(RESULTS_DIR / "E5_nonlinearity.json")
    plot_nonlinearity_robustness(data, FIGURES_DIR / "fig7_nonlinearity.pdf")

    # Fig 8: Dynamics analysis (runs its own simulation)
    print("\nFig 8: Dynamics analysis")
    generate_fig8_dynamics(FIGURES_DIR / "fig8_dynamics.pdf")

    print("\n" + "=" * 60)
    print("  All 8 figures generated!")
    print("=" * 60)
    print(f"\n  Output: {FIGURES_DIR}/")
    for f in sorted(FIGURES_DIR.glob("fig*.pdf")):
        print(f"    {f.name}")


if __name__ == "__main__":
    main()
