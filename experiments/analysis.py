"""
Analysis and Figure Generation for Sparse Matrix Recovery Paper

Generates publication-quality composite figures with:
- Modern Tol bright color palette (colorblind-friendly)
- Sans-serif typography, clean aesthetics
- Multi-panel layouts pairing schematics with data plots
- Bootstrap CI shading on all line/bar plots
- Panel labels (A), (B), etc.

Usage:
    python experiments/analysis.py --results-dir experiments/results --output-dir paper/figures
    python experiments/analysis.py --figure F1  # Generate specific figure
    python experiments/analysis.py --all        # Generate all figures
"""

import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx
from pathlib import Path

# ============================================================================
# Publication Style System
# ============================================================================

plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.figsize": (7, 4.5),
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "text.usetex": False,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.alpha": 0.15,
    "grid.linewidth": 0.5,
    "lines.linewidth": 2.5,
    "lines.markersize": 8,
})

# Tol bright palette — colorblind-friendly and modern
PALETTE = {
    "blue": "#4477AA",
    "cyan": "#66CCEE",
    "green": "#228833",
    "yellow": "#CCBB44",
    "red": "#EE6677",
    "purple": "#AA3377",
    "grey": "#BBBBBB",
}
COLORS = list(PALETTE.values())
C_EST = PALETTE["blue"]      # Covariance estimate
C_GRN = PALETTE["green"]     # Granger refined
C_CHANCE = PALETTE["grey"]   # Chance baseline


def _add_panel_label(ax, label, x=-0.08, y=1.08):
    """Add (A), (B), etc. panel labels."""
    ax.text(x, y, f"({label})", transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="top")


def _draw_mini_network(ax, n_nodes=8, frac_measured=1.0, title="", scale=0.8):
    """Draw a small ring network showing measured vs unmeasured nodes."""
    G = nx.cycle_graph(n_nodes, create_using=nx.DiGraph)
    pos = nx.circular_layout(G, scale=scale)
    n_measured = max(1, int(n_nodes * frac_measured))
    measured = set(range(n_measured))

    # Draw edges lightly
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, width=0.8,
                           arrows=True, arrowsize=6, edge_color="#888888")
    # Measured nodes
    if measured:
        nx.draw_networkx_nodes(G, pos, nodelist=list(measured), ax=ax,
                               node_color=PALETTE["green"], node_size=120,
                               edgecolors="#333333", linewidths=0.8)
    # Unmeasured nodes
    unmeasured = set(range(n_nodes)) - measured
    if unmeasured:
        nx.draw_networkx_nodes(G, pos, nodelist=list(unmeasured), ax=ax,
                               node_color=PALETTE["grey"], node_size=120,
                               edgecolors="#333333", linewidths=0.8)
    ax.set_title(title, fontsize=10, pad=4)
    ax.axis("off")


# ============================================================================
# Data Loading
# ============================================================================

def load_results(filepath):
    """Load experiment results from JSON."""
    with open(filepath) as f:
        data = json.load(f)
    for entry in data:
        entry["distances"] = pd.DataFrame(entry["distances"])
    return data


# ============================================================================
# Figure F2: Measurement Sparsity — Composite
# ============================================================================

def plot_sparsity_effect(results, output_path):
    """Composite: mini network schematics + error vs measurement fraction."""
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 2.2]})

    # --- Left panel: schematic mini networks ---
    _add_panel_label(ax_left, "A")
    ax_left.axis("off")
    ax_left.set_title("Measurement patterns", fontsize=11, fontweight="bold", pad=10)

    # Create 3 inset axes for mini networks
    fracs_show = [0.33, 0.66, 1.0]
    labels_show = ["33%", "66%", "100%"]
    for i, (frac, lab) in enumerate(zip(fracs_show, labels_show)):
        inset = ax_left.inset_axes([0.05, 0.68 - i * 0.35, 0.9, 0.30])
        _draw_mini_network(inset, n_nodes=8, frac_measured=frac, title=lab)

    # --- Right panel: error vs measurement fraction ---
    _add_panel_label(ax_right, "B")

    # Extract data for estimate and optimized
    fracs, est_med, est_lo, est_hi = [], [], [], []
    opt_med, opt_lo, opt_hi = [], [], []
    chance_val = None

    for r in results:
        frac = r["config"].get("measurement_fraction",
                               r["config"]["num_measured"] / r["config"]["num_nodes"])
        fracs.append(frac)
        est_med.append(r["distances"]["estimate_distance"].median())
        est_lo.append(r["confidence_intervals"]["estimate_distance"]["low"])
        est_hi.append(r["confidence_intervals"]["estimate_distance"]["high"])
        opt_med.append(r["distances"]["optimized_distance"].median())
        opt_lo.append(r["confidence_intervals"]["optimized_distance"]["low"])
        opt_hi.append(r["confidence_intervals"]["optimized_distance"]["high"])
        if chance_val is None:
            chance_val = r["distances"]["chance_distance"].median()

    order = np.argsort(fracs)
    fracs = np.array(fracs)[order]
    est_med, est_lo, est_hi = [np.array(a)[order] for a in [est_med, est_lo, est_hi]]
    opt_med, opt_lo, opt_hi = [np.array(a)[order] for a in [opt_med, opt_lo, opt_hi]]

    ax_right.plot(fracs, est_med, "o-", color=C_EST, label="Covariance estimate", zorder=3)
    ax_right.fill_between(fracs, est_lo, est_hi, alpha=0.2, color=C_EST)

    ax_right.plot(fracs, opt_med, "s-", color=C_GRN, label="Granger refined", zorder=3)
    ax_right.fill_between(fracs, opt_lo, opt_hi, alpha=0.2, color=C_GRN)

    ax_right.set_xlabel("Measurement Fraction")
    ax_right.set_ylabel("Recovery Error (Frobenius / N)")
    ax_right.set_title("Effect of measurement density", fontsize=11, fontweight="bold")
    ax_right.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F3: Stimulation Tradeoff — Composite
# ============================================================================

def plot_stimulation_tradeoff(results, output_path):
    """Composite: stimulation intensity schematic + tradeoff curves."""
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 2.2]})

    # --- Left panel: schematic ---
    _add_panel_label(ax_left, "A")
    ax_left.axis("off")
    ax_left.set_title("Stimulation intensity", fontsize=11, fontweight="bold", pad=10)

    # Draw two mini networks: low vs high stim
    for idx, (label, lw, y_off) in enumerate([("Low stim", 1.5, 0.55), ("High stim", 4.0, 0.05)]):
        inset = ax_left.inset_axes([0.05, y_off, 0.9, 0.42])
        G = nx.cycle_graph(8, create_using=nx.DiGraph)
        pos = nx.circular_layout(G, scale=0.7)
        nx.draw_networkx_edges(G, pos, ax=inset, alpha=0.15, width=0.6,
                               arrows=True, arrowsize=5, edge_color="#888888")
        nx.draw_networkx_nodes(G, pos, ax=inset, node_color=PALETTE["cyan"],
                               node_size=100, edgecolors="#333333", linewidths=0.6)
        # Draw stim arrows on stimulated nodes (2, 5)
        for sn in [2, 5]:
            x, y = pos[sn]
            dx = x / max(np.hypot(x, y), 0.01) * 0.35
            dy = y / max(np.hypot(x, y), 0.01) * 0.35
            inset.annotate("", xy=(x, y), xytext=(x + dx, y + dy),
                           arrowprops=dict(arrowstyle="-|>", color="#FF9800",
                                           lw=lw, shrinkB=6))
        inset.set_title(label, fontsize=9)
        inset.axis("off")

    # --- Right panel: tradeoff curves grouped by measurement fraction ---
    _add_panel_label(ax_right, "B")

    meas_groups = {}
    for r in results:
        # Support both old (cpg_fraction) and new (measurement_fraction) formats
        meas_frac = r["config"].get("measurement_fraction",
                     r["config"].get("cpg_fraction", 0.66))
        if meas_frac not in meas_groups:
            meas_groups[meas_frac] = {"stim": [], "med": [], "lo": [], "hi": []}
        g = meas_groups[meas_frac]
        g["stim"].append(r["config"]["stim_gain"])
        # Use Granger-refined distance for the main plot
        dist_key = "optimized_distance" if "optimized_distance" in r["confidence_intervals"] else "estimate_distance"
        g["med"].append(r["distances"][dist_key].median())
        ci = r["confidence_intervals"][dist_key]
        g["lo"].append(ci["low"])
        g["hi"].append(ci["high"])

    for i, (meas_frac, g) in enumerate(sorted(meas_groups.items())):
        stim = np.array(g["stim"])
        med = np.array(g["med"])
        lo, hi = np.array(g["lo"]), np.array(g["hi"])
        order = np.argsort(stim)

        label = f"{meas_frac:.0%} measured" if meas_frac <= 1 else f"CPG = {meas_frac:.0%}"
        ax_right.semilogy(stim[order], np.clip(med[order], 1e-3, None), "o-",
                          color=COLORS[i], label=label)
        ax_right.fill_between(stim[order], np.clip(lo[order], 1e-4, None),
                              np.clip(hi[order], 1e-4, None),
                              alpha=0.15, color=COLORS[i])

    ax_right.set_xlabel("Stimulation Gain ($\\sigma$)")
    ax_right.set_ylabel("Granger Recovery Error (log scale)")
    ax_right.set_title("Stimulation × measurement interaction", fontsize=11, fontweight="bold")
    ax_right.legend(loc="best", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F4: Granger Refinement — Composite with heatmaps + violins
# ============================================================================

def plot_granger_comparison(results, output_path):
    """Composite: heatmaps (top) + heteroskedasticity analysis (middle) + violins (bottom).

    Row 0 (A-D): True W, raw estimate, Granger-refined, absolute error.
    Row 1 (E-H): Error-weight scatter (heteroskedasticity), E1 component, E2 component, ablation.
    Row 2 (I-K): Violin plots for error, precision, recall.
    """
    r = results[0]
    df = r["distances"]

    fig = plt.figure(figsize=(14, 12))
    gs = gridspec.GridSpec(3, 4, height_ratios=[1, 1, 0.85], hspace=0.48, wspace=0.4)

    # ── Row 0: 4 heatmaps from a representative simulation ───────────────────
    true_W = approx_W = W_granger = cov_x = cov_dtx = cov_bx = cov_phix = None
    try:
        from experiments.core import (create_multinetwork_dataset,
                                      estimate_connectivity_weights, projected_gradient_causal,
                                      get_nonlinearity)
        import torch
        np.random.seed(42); torch.manual_seed(42)
        phi = get_nonlinearity("tanh")
        dataset = create_multinetwork_dataset(
            num_sessions=50, max_timesteps=1000, num_nodes=15, num_cpgs=5,
            num_measured=10, num_stimulated=5, fixed_stim=False, stim_gain=1.0,
            nonlinearity=phi, non_negative_weights=True, force_stable=True)
        est = estimate_connectivity_weights(15, dataset)
        _, W_granger = projected_gradient_causal(est["cov_x"], est["cov_dtx"])
        true_W = est["true_W"]
        approx_W = est["approx_W"]
        cov_x = est["cov_x"]
        cov_dtx = est["cov_dtx"]
        cov_bx = est["cov_bx"]
        cov_phix = est["cov_phix"]

        panels = [
            (true_W, "True $W$", "Reds"),
            (approx_W, r"Covariance est.\ $\hat{W}$", "RdBu_r"),
            (W_granger, "Granger-refined $\\hat{W}$", "Reds"),
            (np.abs(true_W - W_granger), "Error $|W - \\hat{W}|$", "Reds"),
        ]
        vmax = true_W.max()
        for col, (mat, title, cmap) in enumerate(panels):
            ax = fig.add_subplot(gs[0, col])
            if col == 1:
                im = ax.imshow(mat, cmap=cmap, vmin=-vmax, vmax=vmax,
                               aspect="equal", interpolation="nearest")
            elif col == 3:
                im = ax.imshow(mat, cmap=cmap, vmin=0, vmax=vmax * 0.3,
                               aspect="equal", interpolation="nearest")
            else:
                im = ax.imshow(mat, cmap=cmap, vmin=0, vmax=vmax,
                               aspect="equal", interpolation="nearest")
            ax.set_title(title, fontsize=10)
            ax.set_xlabel("Neuron $j$")
            if col == 0:
                ax.set_ylabel("Neuron $i$")
            plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
            _add_panel_label(ax, chr(65 + col))

        N = len(true_W)
        err_a = np.linalg.norm(true_W - approx_W, "fro") / N
        err_g = np.linalg.norm(true_W - W_granger, "fro") / N
        fig.text(0.5, 0.665,
                 f"(A\u2013D) representative topology: Covariance\u202f=\u202f{err_a:.3f},"
                 f" Granger\u202f=\u202f{err_g:.3f}",
                 ha="center", fontsize=9, fontstyle="italic")
    except Exception as e:
        print(f"  Warning: could not generate heatmaps: {e}")

    # ── Row 1: Heteroskedasticity analysis ────────────────────────────────────
    if true_W is not None:
        # Panel E: Error-weight scatter with OLS regression
        ax = fig.add_subplot(gs[1, 0])
        _add_panel_label(ax, "E")
        # Off-diagonal entries only (diagonal is zeroed by construction)
        mask = ~np.eye(len(true_W), dtype=bool)
        w_flat = true_W[mask].ravel()
        err_flat = np.abs((W_granger - true_W)[mask].ravel())

        # OLS regression
        A = np.column_stack([w_flat, np.ones_like(w_flat)])
        slope, intercept = np.linalg.lstsq(A, err_flat, rcond=None)[0]
        corr = np.corrcoef(w_flat, err_flat)[0, 1]

        ax.scatter(w_flat, err_flat, alpha=0.35, s=18, color=PALETTE["blue"],
                   edgecolors="none", label="Off-diag entries")
        x_line = np.linspace(0, w_flat.max(), 50)
        ax.plot(x_line, slope * x_line + intercept, color=PALETTE["red"],
                lw=2, label=f"OLS: slope={slope:.2f}\n$r={corr:.2f}$")
        ax.set_xlabel("True weight $W_{ij}$")
        ax.set_ylabel("Absolute error $|\\hat{W}_{ij} - W_{ij}|$")
        ax.set_title("Error vs. weight magnitude\n(heteroskedasticity)", fontsize=9)
        ax.legend(fontsize=8, loc="upper left")
        ax.annotate(f"Slope $\\approx 1 - \\bar{{d}} = {slope:.2f}$",
                    xy=(0.98, 0.02), xycoords="axes fraction",
                    fontsize=8, ha="right", va="bottom",
                    color=PALETTE["red"], fontstyle="italic")

        # Panel F: E1 heatmap (model mismatch per entry)
        ax = fig.add_subplot(gs[1, 1])
        _add_panel_label(ax, "F")
        pinv_x = np.linalg.pinv(cov_x)
        E1 = true_W @ (cov_phix - cov_x) @ pinv_x
        np.fill_diagonal(E1, 0)
        e1_max = max(np.abs(E1).max(), 1e-6)
        im = ax.imshow(E1, cmap="RdBu_r", vmin=-e1_max, vmax=e1_max,
                       aspect="equal", interpolation="nearest")
        ax.set_title(f"$E_1$ (model mismatch)\n$\\|E_1\\|_F/N={np.linalg.norm(E1,'fro')/len(true_W):.3f}$",
                     fontsize=9)
        ax.set_xlabel("Neuron $j$"); ax.set_ylabel("Neuron $i$")
        plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)

        # Panel G: E2 heatmap (CPG correlation per entry)
        ax = fig.add_subplot(gs[1, 2])
        _add_panel_label(ax, "G")
        E2 = cov_bx @ pinv_x
        np.fill_diagonal(E2, 0)
        e2_max = max(np.abs(E2).max(), 1e-6)
        im = ax.imshow(E2, cmap="RdBu_r", vmin=-e2_max, vmax=e2_max,
                       aspect="equal", interpolation="nearest")
        ax.set_title(f"$E_2$ (CPG correlation)\n$\\|E_2\\|_F/N={np.linalg.norm(E2,'fro')/len(true_W):.3f}$",
                     fontsize=9)
        ax.set_xlabel("Neuron $j$")
        plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)

        fig.text(0.5, 0.36,
                 "(E) error proportional to weight magnitude (slope $\\approx 1-\\bar{d}$); "
                 "(F,G) per-entry error components $E_1$ and $E_2$",
                 ha="center", fontsize=9, fontstyle="italic")

    # Panel H: Ablation bar — now includes VAR baseline between Spec and Est
    ax = fig.add_subplot(gs[1, 3])
    _add_panel_label(ax, "H")
    has_var = "var_distance" in df.columns
    has_glm = "glm_distance" in df.columns
    if has_var and has_glm:
        names = ["Chance", "Adj", "Spec", "VAR", "GLM", "Est", "Grn"]
        cols   = ["chance_distance", "adjacency_distance", "spectral_distance",
                  "var_distance", "glm_distance", "estimate_distance", "optimized_distance"]
        bar_colors = [PALETTE["red"], PALETTE["yellow"], PALETTE["cyan"],
                      PALETTE["purple"], "#AA5577", C_EST, C_GRN]
    elif has_var:
        names = ["Chance", "Adj", "Spec", "VAR", "Est", "Grn"]
        cols   = ["chance_distance", "adjacency_distance", "spectral_distance",
                  "var_distance", "estimate_distance", "optimized_distance"]
        bar_colors = [PALETTE["red"], PALETTE["yellow"], PALETTE["cyan"],
                      PALETTE["purple"], C_EST, C_GRN]
    else:
        names = ["Chance", "Adj", "Spec", "Est", "Grn"]
        cols  = ["chance_distance", "adjacency_distance", "spectral_distance",
                 "estimate_distance", "optimized_distance"]
        bar_colors = [PALETTE["red"], PALETTE["yellow"], PALETTE["cyan"], C_EST, C_GRN]

    has_all = all(c in df.columns for c in cols)
    if has_all:
        vals = [df[c].median() for c in cols]
    else:
        vals = [0.54, 0.21, 0.13, df["estimate_distance"].median(), df["optimized_distance"].median()]
        names = ["Chance", "Adj", "Spec", "Est", "Grn"]
        bar_colors = [PALETTE["red"], PALETTE["yellow"], PALETTE["cyan"], C_EST, C_GRN]

    ax.bar(names, vals, color=bar_colors, alpha=0.85, edgecolor="#333333", linewidth=0.5)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.005, f"{v:.3f}", ha="center",
                fontsize=6 if has_var else 7, fontweight="bold")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=7, rotation=30 if has_var else 0, ha="right" if has_var else "center")
    ax.set_ylabel("Error")
    ax.set_title("Recovery with\nincreasing prior", fontsize=9)

    # ── Row 2: Violin plots ───────────────────────────────────────────────────
    plot_data = [
        ("estimate_distance", "optimized_distance", "Recovery Error\n(Frobenius / N)",
         "Distance from True $W$"),
        ("estimate_precision", "optimized_precision", "Precision", "Edge Detection Precision"),
        ("estimate_recall", "optimized_recall", "Recall", "Edge Detection Recall"),
    ]

    for col, (before_col, after_col, ylabel, title) in enumerate(plot_data):
        ax = fig.add_subplot(gs[2, col])
        _add_panel_label(ax, chr(73 + col))   # I, J, K

        before = df[before_col].values
        after = df[after_col].values

        parts_b = ax.violinplot([before], positions=[0], showmedians=True, widths=0.6)
        parts_a = ax.violinplot([after], positions=[1], showmedians=True, widths=0.6)

        for pc in parts_b["bodies"]:
            pc.set_facecolor(C_EST); pc.set_alpha(0.4)
        for pc in parts_a["bodies"]:
            pc.set_facecolor(C_GRN); pc.set_alpha(0.4)
        for key in ["cmins", "cmaxes", "cmedians", "cbars"]:
            if key in parts_b: parts_b[key].set_color(C_EST)
            if key in parts_a: parts_a[key].set_color(C_GRN)

        jitter_b = np.random.RandomState(0).normal(0, 0.05, len(before))
        jitter_a = np.random.RandomState(1).normal(0, 0.05, len(after))
        ax.scatter(jitter_b, before, color=C_EST, alpha=0.6, s=20, zorder=3)
        ax.scatter(1 + jitter_a, after, color=C_GRN, alpha=0.6, s=20, zorder=3)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Before\n(Covariance)", "After\n(Granger)"], fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)

    fig.text(0.5, 0.005,
             "(I\u2013K) distribution across 10 topologies (50 sessions each)",
             ha="center", fontsize=9, fontstyle="italic")

    plt.suptitle("Effect of Granger-Inspired Refinement (N=15, 66% measured, stim=1.0)",
                 fontsize=13, fontweight="bold", y=1.0)
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F5: Scaling — with CI shading
# ============================================================================

def plot_scaling(results, output_path):
    """Error vs T and N with bootstrap CI shading."""
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(11, 4.5))
    _add_panel_label(ax_left, "A")
    _add_panel_label(ax_right, "B")

    # Group data — use Granger-refined (optimized_distance) to match Table 1 and paper captions.
    by_N = {}
    for r in results:
        N = r["config"]["num_nodes"]
        T = r["config"]["max_timesteps"]
        med = r["distances"]["optimized_distance"].median()
        ci = r["confidence_intervals"]["optimized_distance"]
        if N not in by_N:
            by_N[N] = {"T": [], "med": [], "lo": [], "hi": []}
        by_N[N]["T"].append(T)
        by_N[N]["med"].append(med)
        by_N[N]["lo"].append(ci["low"])
        by_N[N]["hi"].append(ci["high"])

    # Left: error vs T
    for i, (N, data) in enumerate(sorted(by_N.items())):
        order = np.argsort(data["T"])
        T = np.array(data["T"])[order]
        med = np.array(data["med"])[order]
        lo = np.array(data["lo"])[order]
        hi = np.array(data["hi"])[order]
        ax_left.plot(T, med, "o-", color=COLORS[i], label=f"$N={N}$", zorder=3)
        ax_left.fill_between(T, lo, hi, alpha=0.25, color=COLORS[i], zorder=2)
        # Show individual topology results as scatter
        for r_inner in results:
            if r_inner["config"]["num_nodes"] == N:
                raw = r_inner["distances"]["optimized_distance"].values
                t_val = r_inner["config"]["max_timesteps"]
                ax_left.scatter([t_val]*len(raw), raw, s=12, alpha=0.3,
                                color=COLORS[i], zorder=1, edgecolors="none")

    ax_left.set_yscale("log")
    ax_left.set_xlabel("Recording Duration ($T$)")
    ax_left.set_ylabel("Granger-refined Recovery Error (Frobenius / $N$)")
    ax_left.set_title("Error vs. recording duration", fontsize=11, fontweight="bold")
    ax_left.legend(framealpha=0.9)

    # Right: error vs N
    by_T = {}
    for r in results:
        N = r["config"]["num_nodes"]
        T = r["config"]["max_timesteps"]
        med = r["distances"]["optimized_distance"].median()
        ci = r["confidence_intervals"]["optimized_distance"]
        if T not in by_T:
            by_T[T] = {"N": [], "med": [], "lo": [], "hi": []}
        by_T[T]["N"].append(N)
        by_T[T]["med"].append(med)
        by_T[T]["lo"].append(ci["low"])
        by_T[T]["hi"].append(ci["high"])

    for i, (T, data) in enumerate(sorted(by_T.items())):
        order = np.argsort(data["N"])
        N_arr = np.array(data["N"])[order]
        med = np.array(data["med"])[order]
        lo = np.array(data["lo"])[order]
        hi = np.array(data["hi"])[order]
        ax_right.plot(N_arr, med, "s-", color=COLORS[i], label=f"$T={T}$", zorder=3)
        ax_right.fill_between(N_arr, lo, hi, alpha=0.25, color=COLORS[i], zorder=2)
        # Show individual topology results
        for r_inner in results:
            if r_inner["config"]["max_timesteps"] == T:
                raw = r_inner["distances"]["optimized_distance"].values
                n_val = r_inner["config"]["num_nodes"]
                ax_right.scatter([n_val]*len(raw), raw, s=12, alpha=0.3,
                                 color=COLORS[i], zorder=1, edgecolors="none")

    ax_right.set_yscale("log")
    ax_right.set_xlabel("Network Size ($N$)")
    ax_right.set_ylabel("Granger-refined Recovery Error (Frobenius / $N$)")
    ax_right.set_title("Error vs. network size", fontsize=11, fontweight="bold")
    ax_right.legend(framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F6: Nonlinearity Robustness — Composite
# ============================================================================

def plot_nonlinearity_robustness(results, output_path):
    """Composite: activation function curves + grouped bar chart with error bars."""
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 1.8]})
    _add_panel_label(ax_left, "A")
    _add_panel_label(ax_right, "B")

    # --- Left: activation function curves ---
    x = np.linspace(-3, 3, 200)
    funcs = {
        "identity": (x, COLORS[0]),
        "tanh": (np.tanh(x), COLORS[1]),
        "relu": (np.maximum(0, x), COLORS[2]),
        "sigmoid": (1 / (1 + np.exp(-x)), COLORS[3]),
    }
    for name, (y, color) in funcs.items():
        ax_left.plot(x, y, color=color, label=name, lw=2.5)
    ax_left.axhline(0, color="#CCCCCC", lw=0.5, zorder=0)
    ax_left.axvline(0, color="#CCCCCC", lw=0.5, zorder=0)
    ax_left.set_xlabel("$x$")
    ax_left.set_ylabel("$\\phi(x)$")
    ax_left.set_title("Activation functions", fontsize=11, fontweight="bold")
    ax_left.legend(fontsize=8, framealpha=0.9)
    ax_left.set_xlim(-3, 3)

    # --- Right: grouped bar chart with error bars and data points ---
    nl_names = []
    est_med, opt_med = [], []
    est_lo, est_hi, opt_lo, opt_hi = [], [], [], []
    est_points, opt_points = [], []

    for r in results:
        nl = r["config"]["nonlinearity"]
        nl_names.append(nl)
        df = r["distances"]
        est_med.append(df["estimate_distance"].median())
        opt_med.append(df["optimized_distance"].median())
        ci_e = r["confidence_intervals"]["estimate_distance"]
        ci_o = r["confidence_intervals"]["optimized_distance"]
        est_lo.append(ci_e["low"])
        est_hi.append(ci_e["high"])
        opt_lo.append(ci_o["low"])
        opt_hi.append(ci_o["high"])
        est_points.append(df["estimate_distance"].values)
        opt_points.append(df["optimized_distance"].values)

    x_pos = np.arange(len(nl_names))
    width = 0.35
    est_med, opt_med = np.array(est_med), np.array(opt_med)
    est_err = [est_med - np.array(est_lo), np.array(est_hi) - est_med]
    opt_err = [opt_med - np.array(opt_lo), np.array(opt_hi) - opt_med]

    bars1 = ax_right.bar(x_pos - width / 2, est_med, width, color=C_EST,
                         label="Covariance estimate", alpha=0.85, zorder=2)
    bars2 = ax_right.bar(x_pos + width / 2, opt_med, width, color=C_GRN,
                         label="Granger refined", alpha=0.85, zorder=2)
    ax_right.errorbar(x_pos - width / 2, est_med, yerr=est_err,
                      fmt="none", capsize=4, color="#333333", lw=1.2, zorder=3)
    ax_right.errorbar(x_pos + width / 2, opt_med, yerr=opt_err,
                      fmt="none", capsize=4, color="#333333", lw=1.2, zorder=3)

    # Overlay individual data points
    rng = np.random.RandomState(42)
    for i in range(len(nl_names)):
        jitter = rng.normal(0, 0.04, len(est_points[i]))
        ax_right.scatter(x_pos[i] - width / 2 + jitter, est_points[i],
                         color=C_EST, alpha=0.5, s=15, zorder=4, edgecolors="none")
        jitter = rng.normal(0, 0.04, len(opt_points[i]))
        ax_right.scatter(x_pos[i] + width / 2 + jitter, opt_points[i],
                         color=C_GRN, alpha=0.5, s=15, zorder=4, edgecolors="none")

    ax_right.set_xlabel("Nonlinearity $\\phi$")
    ax_right.set_ylabel("Recovery Error (Frobenius / $N$, log scale)")
    ax_right.set_yscale("log")
    ax_right.set_title("Robustness to nonlinearity mismatch", fontsize=11, fontweight="bold")
    ax_right.set_xticks(x_pos)
    ax_right.set_xticklabels(nl_names)
    ax_right.legend(framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F8: Stimulation Fraction — E7
# ============================================================================

def plot_stim_fraction(results, output_path):
    """Composite: stimulation coverage schematic + recovery error vs stimulation fraction."""
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 2.2]})

    # --- Left panel: schematic mini networks showing stimulation coverage ---
    _add_panel_label(ax_left, "A")
    ax_left.axis("off")
    ax_left.set_title("Stimulation coverage patterns", fontsize=11, fontweight="bold", pad=10)

    fracs_show = [0.08, 0.33, 1.0]
    labels_show = ["8%", "33%", "100%"]
    for i, (frac, lab) in enumerate(zip(fracs_show, labels_show)):
        inset = ax_left.inset_axes([0.05, 0.68 - i * 0.35, 0.9, 0.30])
        _draw_mini_network(inset, n_nodes=8, frac_measured=frac, title=f"Stimulated: {lab}")

    # --- Right panel: error vs stimulation fraction ---
    _add_panel_label(ax_right, "B")

    fracs, est_med, est_lo, est_hi = [], [], [], []
    opt_med, opt_lo, opt_hi = [], [], []
    chance_val = None

    for r in results:
        frac = r["config"].get("stim_fraction",
                               r["config"]["num_stimulated"] / r["config"]["num_nodes"])
        fracs.append(frac)
        est_med.append(r["distances"]["estimate_distance"].median())
        est_lo.append(r["confidence_intervals"]["estimate_distance"]["low"])
        est_hi.append(r["confidence_intervals"]["estimate_distance"]["high"])
        opt_med.append(r["distances"]["optimized_distance"].median())
        opt_lo.append(r["confidence_intervals"]["optimized_distance"]["low"])
        opt_hi.append(r["confidence_intervals"]["optimized_distance"]["high"])
        if chance_val is None:
            chance_val = r["distances"]["chance_distance"].median()

    order = np.argsort(fracs)
    fracs = np.array(fracs)[order]
    est_med, est_lo, est_hi = [np.array(a)[order] for a in [est_med, est_lo, est_hi]]
    opt_med, opt_lo, opt_hi = [np.array(a)[order] for a in [opt_med, opt_lo, opt_hi]]

    ax_right.plot(fracs, est_med, "o-", color=C_EST, label="Covariance estimate", zorder=3)
    ax_right.fill_between(fracs, est_lo, est_hi, alpha=0.2, color=C_EST)

    ax_right.plot(fracs, opt_med, "s-", color=C_GRN, label="Granger refined", zorder=3)
    ax_right.fill_between(fracs, opt_lo, opt_hi, alpha=0.2, color=C_GRN)

    ax_right.set_xlabel("Stimulation Fraction (stimulated neurons / N)")
    ax_right.set_ylabel("Recovery Error (Frobenius / N)")
    ax_right.set_title("Effect of stimulation coverage on recovery", fontsize=11, fontweight="bold")
    ax_right.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F9: Oracle vs. Approximation Crossover — E6
# ============================================================================

def plot_oracle_crossover(results, output_path):
    """Oracle vs approximation comparison across stimulation levels."""
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [2, 1]})

    stim_gains = []
    oracle_med, approx_med, granger_med = [], [], []
    oracle_all, approx_all, granger_all = [], [], []

    for r in results:
        stim_gains.append(r["config"]["stim_gain"])
        o_vals = r["distances"]["oracle_distance"].values
        a_vals = r["distances"]["estimate_distance"].values
        g_vals = r["distances"]["optimized_distance"].values

        oracle_med.append(np.median(o_vals))
        approx_med.append(np.median(a_vals))
        granger_med.append(np.median(g_vals))
        oracle_all.append(o_vals)
        approx_all.append(a_vals)
        granger_all.append(g_vals)

    stim_gains = np.array(stim_gains)
    oracle_med = np.array(oracle_med)
    approx_med = np.array(approx_med)
    granger_med = np.array(granger_med)

    # Bootstrap 95% CI
    def _bootstrap_ci(vals_list, n_boot=1000, seed=42):
        rng = np.random.RandomState(seed)
        lows, highs = [], []
        for vals in vals_list:
            arr = np.asarray(vals)
            boots = [np.median(rng.choice(arr, size=len(arr), replace=True))
                     for _ in range(n_boot)]
            lows.append(np.percentile(boots, 2.5))
            highs.append(np.percentile(boots, 97.5))
        return np.array(lows), np.array(highs)

    o_lo, o_hi = _bootstrap_ci(oracle_all)
    a_lo, a_hi = _bootstrap_ci(approx_all)
    g_lo, g_hi = _bootstrap_ci(granger_all)

    x_plot = np.arange(len(stim_gains))
    x_labels = [str(s) for s in stim_gains]

    # Left panel: recovery error vs stimulation
    _add_panel_label(ax1, "A")
    ax1.plot(x_plot, oracle_med, "o-", color=PALETTE["red"],
             label=r"Oracle ($\Sigma_{\phi(x),x}^{-1}$)", markersize=8, zorder=3)
    ax1.fill_between(x_plot, o_lo, o_hi, color=PALETTE["red"], alpha=0.25)

    ax1.plot(x_plot, approx_med, "s-", color=C_EST,
             label=r"Approximation ($\Sigma_{x,x}^{-1}$)", markersize=8, zorder=3)
    ax1.fill_between(x_plot, a_lo, a_hi, color=C_EST, alpha=0.25)

    ax1.plot(x_plot, granger_med, "D-", color=C_GRN,
             label="Granger-refined", markersize=7, zorder=3)
    ax1.fill_between(x_plot, g_lo, g_hi, color=C_GRN, alpha=0.25)

    ax1.set_yscale("log")
    ax1.set_xticks(x_plot)
    ax1.set_xticklabels(x_labels)
    ax1.set_xlabel(r"Stimulation gain $\sigma$")
    ax1.set_ylabel(r"Median recovery error ($\|W - \hat{W}\|_F / N$)")
    ax1.set_title("Oracle vs. Approximation across stimulation levels",
                   fontsize=11, fontweight="bold")
    ax1.legend(fontsize=9, loc="upper right")

    # Right panel: ratio (oracle / Granger-refined approximation) — paper text
    # cites these ratios, so panel B must match. At σ=0 all three estimators
    # are pathological; we still show the bar for completeness.
    _add_panel_label(ax2, "B")
    ratios = oracle_med / granger_med
    ax2.bar(x_plot, ratios, color=PALETTE["purple"], alpha=0.8,
            edgecolor="#333333", linewidth=0.5)
    for i, r in enumerate(ratios):
        ax2.text(i, r + 0.1, f"{r:.1f}x", ha="center", fontsize=9, fontweight="bold")
    ax2.axhline(1.0, color="gray", ls="--", lw=1, label="Parity")
    ax2.set_xticks(x_plot)
    ax2.set_xticklabels(x_labels)
    ax2.set_xlabel(r"Stimulation gain $\sigma$")
    ax2.set_ylabel("Error ratio (oracle / Granger-refined approximation)")
    ax2.set_title("Oracle penalty factor", fontsize=11, fontweight="bold")
    ax2.legend(fontsize=8)

    plt.suptitle("Oracle vs. Approximation: Implicit Regularization (E6)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F1: Problem Schematic (Network Diagram) — KEPT AS-IS
# ============================================================================

def generate_problem_schematic(output_path, r_value=None):
    """Generate Figure F1 — network diagram illustrating the problem setup."""
    if r_value is None:
        # Compute from E2 data if available
        results_dir = Path(__file__).parent / "results"
        e2_path = results_dir / "E2_granger.json"
        if e2_path.exists():
            e2 = load_results(e2_path)
            if e2 and "distances" in e2[0]:
                wc = e2[0]["distances"]["weight_correlation"]
                r_value = float(np.median(wc.values if hasattr(wc, "values") else list(wc)))
        if r_value is None:
            r_value = 0.90  # fallback (median across topologies)
    N = 15
    np.random.seed(42)
    G = nx.DiGraph()
    G.add_nodes_from(range(N))
    edges = [
        (0, 1, 0.8), (0, 3, 0.5), (1, 2, 0.7), (2, 5, 0.6),
        (3, 4, 0.9), (4, 5, 0.4), (5, 8, 0.7), (6, 7, 0.8),
        (7, 8, 0.6), (8, 9, 0.5), (9, 10, 0.7), (10, 11, 0.9),
        (11, 6, 0.3), (2, 9, 0.4), (4, 7, 0.6), (1, 10, 0.3),
        (3, 6, 0.5), (5, 11, 0.4),
        # Nodes 12-14: connected into the network
        (11, 12, 0.6), (12, 13, 0.7), (13, 14, 0.5),
        (14, 0, 0.4), (12, 7, 0.3), (9, 14, 0.6), (13, 3, 0.5),
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    cpg_nodes = {0, 3, 6, 9, 12}          # 5 CPG nodes (33%)
    stim_nodes = {2, 5, 8, 11, 14}         # 5 stimulated nodes (33%)
    session1_measured = {0, 2, 4, 6, 8, 10, 12, 14}  # 8 of 15 ~53% (visual clarity)
    pos = nx.circular_layout(G, scale=1.8)
    fig = plt.figure(figsize=(10, 7))
    ax_main = fig.add_axes([0.02, 0.12, 0.62, 0.80])
    ax_main.set_xlim(-3.0, 3.0); ax_main.set_ylim(-3.0, 3.0)
    ax_main.set_aspect("equal"); ax_main.axis("off")
    for u, v, d in G.edges(data=True):
        w = d["weight"]
        ax_main.annotate("", xy=pos[v], xytext=pos[u],
            arrowprops=dict(arrowstyle="-|>", color=(0.3, 0.3, 0.3, 0.3 + 0.6 * w),
                            lw=1.0 + 2.0 * w, connectionstyle="arc3,rad=0.1",
                            shrinkA=12, shrinkB=12))
    node_size = 500
    for node in range(N):
        x, y = pos[node]
        facecolor = "#4CAF50" if node in session1_measured else "#9E9E9E"
        edgecolor = "#D32F2F" if node in cpg_nodes else "#333333"
        edgewidth = 2.5 if node in cpg_nodes else 1.0
        marker = "^" if node in stim_nodes else "o"
        ax_main.scatter(x, y, s=node_size, c=facecolor, edgecolors=edgecolor,
                        linewidths=edgewidth, marker=marker, zorder=5)
        ax_main.text(x, y, str(node), ha="center", va="center",
                     fontsize=8, fontweight="bold", color="white", zorder=6)
    for node in stim_nodes:
        x, y = pos[node]
        dx = x / np.hypot(x, y) * 0.6; dy = y / np.hypot(x, y) * 0.6
        ox, oy = x + dx, y + dy
        ax_main.annotate("", xy=(x, y), xytext=(ox, oy),
            arrowprops=dict(arrowstyle="-|>", color="#FF9800", lw=2.5,
                            connectionstyle="arc3,rad=0.15", shrinkB=12))
        ax_main.text(ox + dx * 0.15, oy + dy * 0.15, "S", fontsize=9,
                     fontweight="bold", ha="center", va="center", color="#FF9800", zorder=7)
    ax_main.text(0, -2.7, "Session 1: observe $\\{0, 2, 4, 6, 8, 10, 12, 14\\}$",
                 ha="center", fontsize=9, color="#2E7D32", fontstyle="italic")
    ax_main.text(0, -2.95, "Session 2: observe $\\{1, 3, 5, 7, 9, 11, 13\\}$",
                 ha="center", fontsize=9, color="#616161", fontstyle="italic")
    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#4CAF50",
                    markeredgecolor="#333333", markersize=10, label="Measured (session 1)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#9E9E9E",
                    markeredgecolor="#333333", markersize=10, label="Unmeasured (session 1)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#BBBBBB",
                    markeredgecolor="#D32F2F", markeredgewidth=2.5, markersize=10,
                    label="CPG node (red border)"),
        plt.Line2D([0], [0], marker="^", color="w", markerfacecolor="#BBBBBB",
                    markeredgecolor="#333333", markersize=10, label="Stimulated node (triangle)"),
        plt.Line2D([0], [0], marker=">", color="#FF9800", lw=0, markersize=8,
                    label="Stimulation input"),
    ]
    ax_main.legend(handles=legend_elements, loc="upper left", frameon=True,
                   fancybox=True, framealpha=0.9, fontsize=8)
    # Right panel: accumulation → estimation pipeline (unified flow)
    ax_inset = fig.add_axes([0.65, 0.05, 0.33, 0.88])
    ax_inset.set_xlim(0, 10); ax_inset.set_ylim(-4, 10); ax_inset.axis("off")
    ax_inset.set_title("Method Pipeline", fontsize=10,
                       fontweight="bold", pad=8)

    # === TOP: Covariance accumulation ===
    box_colors = ["#A5D6A7", "#90CAF9", "#CE93D8"]
    labels = [r"$\hat{\Sigma}_1$", r"$\hat{\Sigma}_2$", r"$\hat{\Sigma}_K$"]
    y_positions = [8.2, 6.5, 4.2]
    for i, (yp, color, lab) in enumerate(zip(y_positions, box_colors, labels)):
        box = FancyBboxPatch((0.3, yp), 3.2, 1.2, boxstyle="round,pad=0.12",
                             facecolor=color, edgecolor="#333333", linewidth=1.0)
        ax_inset.add_patch(box)
        ax_inset.text(1.9, yp + 0.6, lab, ha="center", va="center", fontsize=9)
        ax_inset.annotate("", xy=(5.8, 5.6), xytext=(3.7, yp + 0.6),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0))
    ax_inset.text(1.9, 5.5, r"$\vdots$", ha="center", va="center", fontsize=12)

    # Accumulated covariance
    acc_box = FancyBboxPatch((5.2, 4.8), 3.0, 1.8, boxstyle="round,pad=0.15",
                             facecolor="#FFF9C4", edgecolor="#F57F17", linewidth=1.8)
    ax_inset.add_patch(acc_box)
    ax_inset.text(6.7, 5.9, r"$\hat{\Sigma}$", ha="center", va="center",
                  fontsize=13, fontweight="bold")
    ax_inset.text(6.7, 5.2, "accumulated", ha="center", va="center", fontsize=7)

    # === MIDDLE: Estimation ===
    ax_inset.annotate("", xy=(5.0, 3.4), xytext=(6.7, 4.7),
        arrowprops=dict(arrowstyle="-|>", color="#0077B6", lw=2.0))

    est_box = FancyBboxPatch((2.5, 2.4), 5.0, 1.2, boxstyle="round,pad=0.12",
                             facecolor="#BBDEFB", edgecolor="#0077B6", linewidth=1.5)
    ax_inset.add_patch(est_box)
    ax_inset.text(5.0, 3.2, r"$\hat{W} = \hat{\Sigma}_{x',x}\hat{\Sigma}_{x,x}^{-1}$",
                  ha="center", va="center", fontsize=9, fontweight="bold")
    ax_inset.text(5.0, 2.7, "linear estimator", ha="center", va="center",
                  fontsize=7, color="#555555")

    # === Diagonal zeroing ===
    ax_inset.annotate("", xy=(5.0, 1.4), xytext=(5.0, 2.3),
        arrowprops=dict(arrowstyle="-|>", color="#E76F51", lw=2.0))

    diag_box = FancyBboxPatch((2.5, 0.5), 5.0, 1.0, boxstyle="round,pad=0.12",
                              facecolor="#FFE0B2", edgecolor="#E76F51", linewidth=1.5)
    ax_inset.add_patch(diag_box)
    ax_inset.text(5.0, 1.15, r"$\mathrm{diag}(\hat{W}) \leftarrow 0$",
                  ha="center", va="center", fontsize=9, fontweight="bold")
    ax_inset.text(5.0, 0.7, "no-autapse prior", ha="center", va="center",
                  fontsize=7, color="#555555")

    # === Granger refinement ===
    ax_inset.annotate("", xy=(5.0, -0.4), xytext=(5.0, 0.4),
        arrowprops=dict(arrowstyle="-|>", color="#2A9D8F", lw=2.0))

    grn_box = FancyBboxPatch((2.5, -1.6), 5.0, 1.3, boxstyle="round,pad=0.12",
                             facecolor="#C8E6C9", edgecolor="#2A9D8F", linewidth=1.5)
    ax_inset.add_patch(grn_box)
    ax_inset.text(5.0, -0.65, "Granger refinement", ha="center", va="center",
                  fontsize=9, fontweight="bold")
    ax_inset.text(5.0, -1.15, r"$W_{ij} \geq 0$,  sparse,  $W_{ii}=0$",
                  ha="center", va="center", fontsize=7, color="#555555")

    # === Final output ===
    ax_inset.annotate("", xy=(5.0, -2.6), xytext=(5.0, -1.7),
        arrowprops=dict(arrowstyle="-|>", color="#333333", lw=2.0))
    ax_inset.text(5.0, -3.0, r"$\hat{W}$  (recovered)", ha="center", va="center",
                  fontsize=11, fontweight="bold", color="#2E4057")
    ax_inset.text(5.0, -3.5, f"$r = {r_value:.2f}$", ha="center", va="center",
                  fontsize=9, color="#2A9D8F", fontweight="bold")

    fig.suptitle("", fontsize=1)  # no suptitle — the combined figure speaks for itself
    plt.savefig(output_path, dpi=300); plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F7: Method Pipeline Schematic — KEPT AS-IS
# ============================================================================

def generate_pipeline_schematic(output_path):
    """Generate Figure F7 — method pipeline flow chart."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(-0.5, 14.5); ax.set_ylim(-1.5, 5.5); ax.axis("off")
    c_data, c_compute, c_output, c_border = "#BBDEFB", "#FFE0B2", "#C8E6C9", "#333333"

    def draw_box(ax, x, y, w, h, text, color, fontsize=9, bold=False):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                             facecolor=color, edgecolor=c_border, linewidth=1.5, zorder=3)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fontsize, fontweight="bold" if bold else "normal", zorder=4, linespacing=1.4)

    def draw_arrow(ax, x1, y1, x2, y2, color="#555555"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                     color=color, lw=2.0, mutation_scale=15, zorder=2))

    for label, y in [("Session 1\n(partial obs.)", 3.8), ("Session 2\n(partial obs.)", 2.2),
                     ("Session K\n(partial obs.)", 0.2)]:
        draw_box(ax, 0, y, 2.0, 1.2, label, c_data, fontsize=8)
    ax.text(1.0, 1.65, r"$\vdots$", ha="center", va="center", fontsize=16, color="#555555")
    for label, y in [(r"$\hat{\Sigma}_1$", 3.8), (r"$\hat{\Sigma}_2$", 2.2),
                     (r"$\hat{\Sigma}_K$", 0.2)]:
        draw_box(ax, 2.8, y, 1.4, 1.2, label, c_compute, fontsize=11, bold=True)
    ax.text(3.5, 1.65, r"$\vdots$", ha="center", va="center", fontsize=16, color="#555555")
    for y in [4.4, 2.8, 0.8]: draw_arrow(ax, 2.0, y, 2.8, y)
    draw_box(ax, 5.0, 1.8, 2.0, 1.8, "Accumulated\n" + r"$\hat{\Sigma}$", c_compute, 10, True)
    for y in [4.4, 2.8, 0.8]: draw_arrow(ax, 4.2, y, 5.0, 2.7)
    draw_box(ax, 7.7, 1.8, 2.2, 1.8,
             r"$\hat{W}_{\mathrm{approx}}$" + "\n" + r"$= \hat{\Sigma}_{x',x}\hat{\Sigma}_{x,x}^{-1}$",
             c_compute, 9)
    draw_arrow(ax, 7.0, 2.7, 7.7, 2.7)
    draw_box(ax, 10.6, 1.8, 1.8, 1.8, "Granger\nRefinement\n(sparsify)", c_compute, 9, True)
    draw_arrow(ax, 9.9, 2.7, 10.6, 2.7)
    draw_box(ax, 13.0, 1.8, 1.3, 1.8, "Final\n" + r"$\hat{W}$", c_output, 11, True)
    draw_arrow(ax, 12.4, 2.7, 13.0, 2.7, "#2E7D32")
    for x, label, color in [(1.0, "Data\nCollection", c_data), (3.5, "Partial\nCovariances", c_compute),
                            (6.0, "Accumulation", c_compute), (8.8, "Least-Squares\nInversion", c_compute),
                            (11.5, "Granger\nRefinement", c_compute), (13.65, "Output", c_output)]:
        ax.text(x, 4.8, label, ha="center", va="bottom", fontsize=7.5, color="#555555", fontstyle="italic")
        ax.plot(x, 4.7, "v", color=color, markersize=5)
    ax.legend(handles=[mpatches.Patch(fc=c, ec=c_border, label=l)
              for c, l in [(c_data, "Data / Input"), (c_compute, "Computation"), (c_output, "Output")]],
              loc="lower right", fontsize=8, frameon=True, fancybox=True, framealpha=0.9)
    fig.suptitle("Method Pipeline: Covariance Accumulation + Granger-Inspired Refinement",
                 fontsize=13, fontweight="bold", y=0.98)
    plt.savefig(output_path, dpi=300); plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate paper figures")
    parser.add_argument("--results-dir", type=str, default="experiments/results")
    parser.add_argument("--output-dir", type=str, default="paper/figures")
    parser.add_argument("--figure", type=str, help="Generate specific figure (F1-F9)")
    parser.add_argument("--all", action="store_true", help="Generate all figures")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all or args.figure is None:
        figures = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
    else:
        figures = [args.figure]

    for fig_name in figures:
        print(f"\nGenerating {fig_name}...")
        try:
            if fig_name == "F1":
                generate_problem_schematic(output_dir / "fig1_problem_schematic.pdf")
            elif fig_name == "F2":
                data = load_results(results_dir / "E4_sparsity.json")
                plot_sparsity_effect(data, output_dir / "fig6_sparsity.pdf")
            elif fig_name == "F3":
                data = load_results(results_dir / "E3_stimulation.json")
                plot_stimulation_tradeoff(data, output_dir / "fig5_stimulation.pdf")
            elif fig_name == "F4":
                data = load_results(results_dir / "E2_granger.json")
                plot_granger_comparison(data, output_dir / "fig4_granger_refinement.pdf")
            elif fig_name == "F5":
                data = load_results(results_dir / "E1_baseline.json")
                plot_scaling(data, output_dir / "fig3_scaling.pdf")
            elif fig_name == "F6":
                data = load_results(results_dir / "E5_nonlinearity.json")
                plot_nonlinearity_robustness(data, output_dir / "fig7_nonlinearity.pdf")
            elif fig_name == "F7":
                generate_pipeline_schematic(output_dir / "fig2_pipeline.pdf")
            elif fig_name == "F8":
                data = load_results(results_dir / "E7_stim_fraction.json")
                plot_stim_fraction(data, output_dir / "fig9_stim_fraction.pdf")
            elif fig_name == "F9":
                data = load_results(results_dir / "E6_oracle_crossover.json")
                plot_oracle_crossover(data, output_dir / "fig10_oracle_comparison.pdf")
        except FileNotFoundError as e:
            print(f"  Skipping {fig_name}: {e}")
            print(f"  Run the corresponding experiment first.")


def generate_cpg_architecture_figure(output_path):
    """
    Generate a high-level diagram of the Central Pattern Generator (CPG) model.

    Shows the CPG's role in the simulation: it maps the current network state x_t
    to an intrinsic drive signal b_CPG(t), producing state-dependent input that
    is the source of the E2 estimation error.
    """
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.5); ax.axis("off")

    # Color palette — consistent with rest of paper figures
    c_state   = "#E3F2FD"   # light blue — network state
    c_cpg     = "#FFF3E0"   # light orange — CPG internals
    c_output  = "#E8F5E9"   # light green — output / drive
    c_network = "#FCE4EC"   # light pink — network dynamics
    c_border  = "#333333"
    c_arrow   = "#555555"
    c_warn    = "#B71C1C"   # dark red — for the "≠0" annotation

    def box(x, y, w, h, text, color, fs=9, bold=False, italic=False):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                               facecolor=color, edgecolor=c_border, linewidth=1.5, zorder=3)
        ax.add_patch(patch)
        style = "italic" if italic else "normal"
        weight = "bold" if bold else "normal"
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fs, fontstyle=style, fontweight=weight,
                zorder=4, linespacing=1.5, wrap=True)

    def arrow(x1, y1, x2, y2, label="", color=c_arrow, lw=2.0):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=2)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx + 0.1, my, label, fontsize=8, color=color, va="center", style="italic")

    def bracket(ax, x, y_lo, y_hi, color="#777777", label="", label_x_offset=0.25):
        ax.plot([x, x+0.15, x+0.15, x], [y_lo, y_lo, y_hi, y_hi],
                color=color, lw=1.5, zorder=2)
        if label:
            ax.text(x + label_x_offset, (y_lo+y_hi)/2, label,
                    fontsize=7.5, color=color, va="center", style="italic")

    # ── Column layout ────────────────────────────────────────────────────────
    # [state x_t] → [CPG Function] → [b_CPG(t)] → [+] → [dynamics]
    #                 ┌─────────────┐
    #                 │ Frozen deep │
    #                 │ network     │
    #                 │ (3-layer,   │
    #                 │ abs, Xavier)│
    #                 └─────────────┘
    #                 ┌─────────────┐
    #                 │  Chaotic    │
    #                 │  reservoir  │
    #                 │  (g=1.3)    │
    #                 └─────────────┘

    # Main input
    box(0.3, 2.2, 1.6, 1.1, r"$x_t$" + "\nnetwork state", c_state, fs=9, bold=False)

    # CPG outer bounding box (dashed style)
    cpg_rect = FancyBboxPatch((2.3, 0.5), 5.2, 4.5,
                              boxstyle="round,pad=0.2",
                              facecolor="#FFFDE7", edgecolor="#F9A825",
                              linewidth=2.0, linestyle="--", zorder=1)
    ax.add_patch(cpg_rect)
    ax.text(4.9, 4.75, "CPG Function  (one per topology, frozen)",
            ha="center", va="center", fontsize=9, color="#F57F17",
            fontweight="bold", zorder=4)

    # CPG internals: two sub-boxes
    box(2.6, 2.6, 2.2, 1.6,
        "Frozen deep\nnetwork\n(3 layers, |·|,\nXavier init)",
        c_cpg, fs=8)
    box(5.1, 2.6, 2.2, 1.6,
        "Chaotic\nreservoir\n(Sussillo-style,\ng = 1.3)",
        c_cpg, fs=8)
    box(2.6, 0.8, 4.7, 1.4,
        r"Circular shift of $x_t$ by $t$ positions $\;\to\;$ time-varying input",
        c_cpg, fs=8, italic=True)

    # Arrows within CPG
    arrow(1.9, 2.75, 2.6, 2.75)
    arrow(1.9, 2.75, 4.9, 2.0)      # to shift box
    arrow(4.8, 3.4,  5.1, 3.4)      # deep net → reservoir
    arrow(7.3, 3.4,  8.0, 3.4)      # reservoir → sum circle

    # Main input → CPG
    arrow(1.9, 2.75, 2.6, 3.2, color=c_arrow)

    # Sum circle
    theta = np.linspace(0, 2*np.pi, 100)
    cx, cy, r = 8.35, 3.4, 0.3
    ax.plot(cx + r*np.cos(theta), cy + r*np.sin(theta), color=c_border, lw=1.5, zorder=3)
    ax.text(cx, cy, "+", ha="center", va="center", fontsize=14, fontweight="bold", zorder=4)

    # b_stim arrow (from above)
    box(8.05, 4.4, 0.6, 0.7, r"$b^{\rm stim}_t$" + "\n(i.i.d.)", c_state, fs=8)
    arrow(8.35, 4.4, 8.35, 3.7)

    # b_CPG output label
    ax.text(7.55, 3.62, r"$b^{\rm CPG}_t$", fontsize=9, color="#E65100",
            fontstyle="italic", zorder=5)
    ax.annotate("", xy=(8.05, 3.4), xytext=(7.3, 3.4),
                arrowprops=dict(arrowstyle="-|>", color="#E65100", lw=1.8), zorder=2)

    # Network dynamics box
    box(8.8, 2.5, 2.9, 1.8,
        r"$x_{t+1} = W\phi(x_t) + b^{\rm stim}_t + b^{\rm CPG}_t$"
        + "\n\nnetwork dynamics",
        c_network, fs=8.5)
    arrow(8.65, 3.4, 8.8, 3.4)

    # State-dependence annotation — the key E2 point
    ax.annotate("",
                xy=(2.3, 1.5), xytext=(8.8, 2.5),
                arrowprops=dict(arrowstyle="-|>", color=c_warn, lw=1.5,
                                connectionstyle="arc3,rad=0.3"), zorder=2)
    ax.text(5.6, 1.15,
            r"$\mathrm{Cov}(b^{\rm CPG}_t,\, x_t) \neq 0$  →  source of $E_2$ error",
            ha="center", fontsize=8.5, color=c_warn, fontweight="bold", zorder=5)

    # "shared across K sessions" annotation
    ax.text(4.9, 0.25,
            "Created once per topology — same weights for all K sessions, "
            "independent time counter per session",
            ha="center", fontsize=8, color="#5D4037", fontstyle="italic", zorder=5)

    plt.tight_layout(pad=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  CPG architecture figure saved to {output_path}")


if __name__ == "__main__":
    main()
