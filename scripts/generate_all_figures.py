#!/usr/bin/env python
"""
Generate ALL paper figures from experiment data.

Run this single script to regenerate every figure in the paper:
    uv run python scripts/generate_all_figures.py

Figures are saved to paper/figures/fig1_*.pdf through fig10_*.pdf.
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
    plot_scaling,
    plot_granger_comparison,
    plot_stimulation_tradeoff,
    plot_sparsity_effect,
    plot_nonlinearity_robustness,
    plot_stim_fraction,
    plot_oracle_crossover,
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


def generate_fig9_dynamics(output_path):
    """Figure 8: Network dynamics (phase portraits), power spectrum, and recovery.

    Phase portraits use PCA-projected trajectories colored by time (plasma cmap).
    Shows full network, then CPG-only and non-CPG-only breakdown, each paired
    autonomous vs stimulated.
    """
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.15,
        "figure.dpi": 300, "lines.linewidth": 2,
    })
    PAL = {"blue": "#4477AA", "cyan": "#66CCEE", "green": "#228833",
           "yellow": "#CCBB44", "red": "#EE6677", "purple": "#AA3377"}
    # Node-type colors
    C_CPG = "#E76F51"    # warm orange-red for CPG nodes
    C_NONCPG = "#2A9D8F" # teal for non-CPG nodes
    CMAP_TIME = "plasma"  # sequential: dark purple → yellow, no white

    np.random.seed(42); torch.manual_seed(42)
    phi = get_nonlinearity("tanh"); N = 15
    W, _ = random_network_topology(N, non_negative_weights=True, force_stable=True)

    # Autonomous dynamics (no stim, all measured)
    data_auto = create_network_data(0, 1000, N, 5, N, 0, True, 0.0, phi, W)
    # Stimulated dynamics (same topology, same CPG if cpg_config provided)
    np.random.seed(42); torch.manual_seed(42)
    data_stim = create_network_data(0, 1000, N, 5, N, 5, False, 1.0, phi, W)

    X_auto = data_auto["activity_data"]
    X_stim = data_stim["activity_data"]
    cpg_mask = data_auto["cpg_nodes_mask"]
    cpg_idx = np.where(cpg_mask)[0]
    non_cpg_idx = np.where(~cpg_mask)[0]
    T_plot = len(X_auto)
    t_colors = np.arange(T_plot)

    # Fit PCA on autonomous (full network) — reuse for all projections
    pca_full = PCA(n_components=2).fit(X_auto)
    # Separate PCAs for CPG-only and non-CPG-only subspaces
    pca_cpg = PCA(n_components=2).fit(X_auto[:, cpg_idx])
    pca_noncpg = PCA(n_components=2).fit(X_auto[:, non_cpg_idx])

    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 3, hspace=0.45, wspace=0.4)

    def _phase_plot(ax, X_proj, title, add_cbar=False):
        sc = ax.scatter(X_proj[:, 0], X_proj[:, 1], c=t_colors, cmap=CMAP_TIME,
                        s=4, alpha=0.7, edgecolors="none")
        ax.set_title(title, fontweight="bold")
        if add_cbar:
            cb = plt.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
            cb.set_label("Time step", fontsize=9)

    # Row 1: Full network phase portraits
    ax = fig.add_subplot(gs[0, 0])
    Xp_auto = pca_full.transform(X_auto)
    _phase_plot(ax, Xp_auto, "(A) Full network — autonomous")
    ev = pca_full.explained_variance_ratio_
    ax.set_xlabel(f"PC1 ({ev[0]:.0%})"); ax.set_ylabel(f"PC2 ({ev[1]:.0%})")

    ax = fig.add_subplot(gs[0, 1])
    Xp_stim = pca_full.transform(X_stim)
    _phase_plot(ax, Xp_stim, "(B) Full network — stimulated", add_cbar=True)
    ax.set_xlabel(f"PC1 ({ev[0]:.0%})"); ax.set_ylabel(f"PC2 ({ev[1]:.0%})")

    # Row 1 col 3: Power spectrum
    ax = fig.add_subplot(gs[0, 2])
    for label, X_data, color in [("Autonomous", X_auto, PAL["blue"]),
                                  ("Stimulated", X_stim, PAL["red"])]:
        psds = [welch(X_data[:, i], nperseg=min(128, len(X_data) // 2))[1] for i in range(N)]
        f = welch(X_data[:, 0], nperseg=min(128, len(X_data) // 2))[0]
        ax.semilogy(f, np.mean(psds, axis=0), label=label, color=color)
    ax.set_xlabel("Frequency"); ax.set_ylabel("PSD")
    ax.set_title("(C) Power spectrum", fontweight="bold"); ax.legend(fontsize=9)

    # Row 2: CPG-node and non-CPG-node phase portraits
    ax = fig.add_subplot(gs[1, 0])
    Xc_auto = pca_cpg.transform(X_auto[:, cpg_idx])
    _phase_plot(ax, Xc_auto, f"(D) CPG nodes only — autonomous")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")

    ax = fig.add_subplot(gs[1, 1])
    Xc_stim = pca_cpg.transform(X_stim[:, cpg_idx])
    _phase_plot(ax, Xc_stim, f"(E) CPG nodes only — stimulated", add_cbar=True)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")

    # Row 2 col 3: Per-node variance (CPG detection)
    ax = fig.add_subplot(gs[1, 2])
    vars_auto = np.var(X_auto, axis=0)
    bar_colors = [C_CPG if cpg_mask[i] else C_NONCPG for i in range(N)]
    ax.bar(range(N), vars_auto, color=bar_colors, alpha=0.85, edgecolor="#333333", linewidth=0.5)
    ax.axhline(np.median(vars_auto), color="gray", ls="--", lw=1.5, label="Median")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C_CPG, label="CPG"),
                       Patch(facecolor=C_NONCPG, label="Non-CPG")],
              fontsize=8, loc="upper right")
    ax.set_xlabel("Neuron index"); ax.set_ylabel("Activity variance")
    ax.set_title("(F) Per-node variance", fontweight="bold")

    # Row 3: Non-CPG phase + Error decomposition + True vs estimated
    ax = fig.add_subplot(gs[2, 0])
    Xn_auto = pca_noncpg.transform(X_auto[:, non_cpg_idx])
    _phase_plot(ax, Xn_auto, "(G) Non-CPG nodes — autonomous")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")

    # Error decomposition
    np.random.seed(42); torch.manual_seed(42)
    ds = create_multinetwork_dataset(50, 1000, N, 5, 10, 5, False, 1.0, phi, True, True)
    est = estimate_connectivity_weights(N, ds)
    cov_x_inv = np.linalg.pinv(est["cov_x"])
    E1 = est["true_W"] @ (est["cov_phix"] @ cov_x_inv - np.eye(N))
    E2 = est["cov_bx"] @ cov_x_inv
    ax = fig.add_subplot(gs[2, 1])
    vals = [np.linalg.norm(E1, "fro") / N, np.linalg.norm(E2, "fro") / N,
            np.linalg.norm(est["approx_W"] - est["true_W"], "fro") / N]
    ax.bar(["$E_1$\n(model)", "$E_2$\n(CPG)", "Total"],
           vals, color=[PAL["blue"], PAL["red"], PAL["purple"]], alpha=0.85)
    for j, v in enumerate(vals):
        ax.text(j, v + 0.005, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("$\\|\\cdot\\|_F / N$")
    ax.set_title("(H) Error decomposition", fontweight="bold")

    # True vs estimated weights
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
    """Generate all paper figures from experiment results.

    Loads results from experiments/results/ and generates figures in paper/figures/.
    Requires experiment results to be run first.
    """
    print("=" * 60)
    print("  Generating ALL paper figures")
    print("=" * 60)

    # Fig 1: Problem schematic (no data needed)
    print("\nFig 1: Problem schematic")
    generate_problem_schematic(FIGURES_DIR / "fig1_problem_schematic.pdf")

    # Fig 2: Scaling (E1 data)
    print("\nFig 2: Scaling (E1)")
    data = load_results(RESULTS_DIR / "E1_baseline.json")
    plot_scaling(data, FIGURES_DIR / "fig2_scaling.pdf")

    # Fig 3: Granger refinement + heteroskedasticity + ablation (E2)
    print("\nFig 3: Granger refinement (E2)")
    data = load_results(RESULTS_DIR / "E2_granger.json")
    plot_granger_comparison(data, FIGURES_DIR / "fig3_granger_refinement.pdf")

    # Fig 4: Stimulation-dynamics tradeoff (E3)
    print("\nFig 4: Stimulation tradeoff (E3)")
    data = load_results(RESULTS_DIR / "E3_stimulation.json")
    plot_stimulation_tradeoff(data, FIGURES_DIR / "fig4_stimulation.pdf")

    # Fig 5: Measurement density (E4)
    print("\nFig 5: Measurement sparsity (E4)")
    data = load_results(RESULTS_DIR / "E4_sparsity.json")
    plot_sparsity_effect(data, FIGURES_DIR / "fig5_sparsity.pdf")

    # Fig 6: Nonlinearity robustness (E5)
    print("\nFig 6: Nonlinearity robustness (E5)")
    data = load_results(RESULTS_DIR / "E5_nonlinearity.json")
    plot_nonlinearity_robustness(data, FIGURES_DIR / "fig6_nonlinearity.pdf")

    # Fig 7: Oracle vs. approximation (E6)
    print("\nFig 7: Oracle vs Approximation (E6)")
    data = load_results(RESULTS_DIR / "E6_oracle_crossover.json")
    plot_oracle_crossover(data, FIGURES_DIR / "fig7_oracle_comparison.pdf")

    # Fig 8: Stimulation coverage (E7)
    print("\nFig 8: Stimulation fraction (E7)")
    data = load_results(RESULTS_DIR / "E7_stim_fraction.json")
    plot_stim_fraction(data, FIGURES_DIR / "fig8_stim_fraction.pdf")

    # Fig 9: Network dynamics, CPG detection, error decomposition (simulation)
    print("\nFig 9: Network dynamics")
    generate_fig9_dynamics(FIGURES_DIR / "fig9_dynamics.pdf")

    # Note: CPG architecture is a TikZ diagram inline in main.tex (Appendix A.8)
    # — no external figure file needed.

    print("\n" + "=" * 60)
    print("  All 10 figures generated!")
    print("=" * 60)
    print(f"\n  Output: {FIGURES_DIR}/")
    for f in sorted(FIGURES_DIR.glob("fig*.pdf")):
        print(f"    {f.name}")


if __name__ == "__main__":
    main()
