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
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import seaborn as sns
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

    if chance_val is not None:
        ax_right.axhline(chance_val, color=C_CHANCE, ls="--", lw=1.5, label="Chance baseline")

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
        # Draw stim arrows on sensor nodes (2, 5)
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
    """Composite: W heatmaps (top) + violin plots for distance/precision/recall (bottom)."""
    r = results[0]
    df = r["distances"]

    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1], hspace=0.35, wspace=0.35)

    # --- Top row: generate example heatmaps via simulation ---
    try:
        from experiments.core import (random_network_topology, create_multinetwork_dataset,
                                      estimate_connectivity_weights, projected_gradient_causal,
                                      get_nonlinearity)
        np.random.seed(42)
        phi = get_nonlinearity("tanh")
        dataset = create_multinetwork_dataset(
            num_networks=20, max_timesteps=500, num_nodes=12, num_cpgs=2,
            num_measured=8, num_sensors=2, fixed_sensors=True, stim_gain=0.0,
            nonlinearity=phi, non_negative_weights=True, force_stable=True)
        est = estimate_connectivity_weights(12, dataset)
        _, W_granger = projected_gradient_causal(est["cov_x"], est["cov_dtx"])
        true_W = est["true_W"]
        approx_W = est["approx_W"]

        for col, (mat, title) in enumerate([
            (true_W, "True $W$"),
            (W_granger, "Granger-refined $\\hat{W}$"),
            (np.abs(true_W - W_granger), "$|W - \\hat{W}_{\\mathrm{Granger}}|$"),
        ]):
            ax = fig.add_subplot(gs[0, col])
            vmax = max(np.abs(true_W).max(), 0.01)
            cmap = "RdBu_r" if col < 2 else "Reds"
            vm = vmax if col < 2 else vmax * 0.5
            im = ax.imshow(mat, cmap=cmap, vmin=-vm if col < 2 else 0, vmax=vm,
                           aspect="equal", interpolation="nearest")
            ax.set_title(title, fontsize=10)
            ax.set_xlabel("Neuron $j$")
            if col == 0:
                ax.set_ylabel("Neuron $i$")
            plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
            _add_panel_label(ax, chr(65 + col))
    except Exception as e:
        print(f"  Warning: could not generate heatmaps: {e}")
        for col in range(3):
            ax = fig.add_subplot(gs[0, col])
            ax.text(0.5, 0.5, f"Heatmap {col+1}\n(simulation failed)", ha="center",
                    va="center", transform=ax.transAxes, fontsize=10, color="gray")
            ax.axis("off")

    # --- Bottom row: violin plots ---
    plot_data = [
        ("estimate_distance", "optimized_distance", "Recovery Error\n(Frobenius / N)",
         "Distance from True $W$"),
        ("estimate_precision", "optimized_precision", "Precision", "Edge Detection Precision"),
        ("estimate_recall", "optimized_recall", "Recall", "Edge Detection Recall"),
    ]

    for col, (before_col, after_col, ylabel, title) in enumerate(plot_data):
        ax = fig.add_subplot(gs[1, col])
        _add_panel_label(ax, chr(68 + col))

        before = df[before_col].values
        after = df[after_col].values

        parts_b = ax.violinplot([before], positions=[0], showmedians=True, widths=0.6)
        parts_a = ax.violinplot([after], positions=[1], showmedians=True, widths=0.6)

        for pc in parts_b["bodies"]:
            pc.set_facecolor(C_EST)
            pc.set_alpha(0.4)
        for pc in parts_a["bodies"]:
            pc.set_facecolor(C_GRN)
            pc.set_alpha(0.4)
        for key in ["cmins", "cmaxes", "cmedians", "cbars"]:
            if key in parts_b:
                parts_b[key].set_color(C_EST)
            if key in parts_a:
                parts_a[key].set_color(C_GRN)

        # Jittered data points
        jitter_b = np.random.RandomState(0).normal(0, 0.05, len(before))
        jitter_a = np.random.RandomState(1).normal(0, 0.05, len(after))
        ax.scatter(jitter_b, before, color=C_EST, alpha=0.6, s=20, zorder=3)
        ax.scatter(1 + jitter_a, after, color=C_GRN, alpha=0.6, s=20, zorder=3)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Before\n(Covariance)", "After\n(Granger)"], fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)

    plt.suptitle("Effect of Granger-Causality Refinement", fontsize=13, fontweight="bold", y=1.0)
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

    # Group data
    by_N = {}
    for r in results:
        N = r["config"]["num_nodes"]
        T = r["config"]["max_timesteps"]
        med = r["distances"]["estimate_distance"].median()
        ci = r["confidence_intervals"]["estimate_distance"]
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
        ax_left.plot(T, med, "o-", color=COLORS[i], label=f"$N={N}$")
        ax_left.fill_between(T, lo, hi, alpha=0.15, color=COLORS[i])

    ax_left.set_xlabel("Recording Duration ($T$)")
    ax_left.set_ylabel("Recovery Error (Frobenius / $N$)")
    ax_left.set_title("Error vs. recording duration", fontsize=11, fontweight="bold")
    ax_left.legend(framealpha=0.9)

    # Right: error vs N
    by_T = {}
    for r in results:
        N = r["config"]["num_nodes"]
        T = r["config"]["max_timesteps"]
        med = r["distances"]["estimate_distance"].median()
        ci = r["confidence_intervals"]["estimate_distance"]
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
        ax_right.plot(N_arr, med, "s-", color=COLORS[i], label=f"$T={T}$")
        ax_right.fill_between(N_arr, lo, hi, alpha=0.15, color=COLORS[i])

    ax_right.set_xlabel("Network Size ($N$)")
    ax_right.set_ylabel("Recovery Error (Frobenius / $N$)")
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
# Utility figures (kept for optional use)
# ============================================================================

def generate_heatmaps(true_W, approx_W, optim_W, total_mask, output_path, title_suffix=""):
    """Generate heatmap comparison of true vs estimated weights."""
    small = true_W.shape[0] < 15
    annot = small
    ticklabels = "auto" if small else False
    fig, axes = plt.subplots(2, 2, figsize=(8, 7))
    vmax = max(np.abs(true_W).max(), np.abs(approx_W).max(), np.abs(optim_W).max())
    vmin = -vmax
    kw = dict(cmap="RdBu_r", annot=annot, square=True, cbar_kws={"shrink": 0.6},
              fmt=".2f" if annot else "", xticklabels=ticklabels, yticklabels=ticklabels,
              vmin=vmin, vmax=vmax)
    sns.heatmap(true_W, ax=axes[0, 0], **kw); axes[0, 0].set_title("True W")
    sns.heatmap(approx_W, ax=axes[0, 1], **kw); axes[0, 1].set_title("Covariance Estimate")
    sns.heatmap(optim_W, ax=axes[1, 0], **kw); axes[1, 0].set_title("Granger Refined")
    kw_mask = dict(cmap="viridis", annot=annot, square=True, cbar_kws={"shrink": 0.6},
                   xticklabels=ticklabels, yticklabels=ticklabels)
    if annot: kw_mask["fmt"] = "g"
    hm = sns.heatmap(total_mask, ax=axes[1, 1], **kw_mask)
    cbar = hm.collections[0].colorbar; cbar.locator = ticker.MaxNLocator(integer=True); cbar.update_ticks()
    axes[1, 1].set_title("Co-measurement Counts")
    plt.suptitle(f"Weight Recovery Comparison{title_suffix}", y=1.02)
    plt.tight_layout(); plt.savefig(output_path); plt.close()
    print(f"  Saved: {output_path}")


def plot_summary_bar(results, output_path):
    """Generate summary bar graph with confidence intervals."""
    r = results[0]; df = r["distances"]
    dist_cols = [c for c in df.columns if c.endswith("_distance")]
    medians = df[dist_cols].median(); ci = r["confidence_intervals"]
    labels = [c.replace("_distance", "").capitalize() for c in dist_cols]
    values = medians.values
    errors_low = [values[i] - ci[dist_cols[i]]["low"] for i in range(len(dist_cols))]
    errors_high = [ci[dist_cols[i]]["high"] - values[i] for i in range(len(dist_cols))]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color=[COLORS[i] for i in range(len(labels))])
    ax.errorbar(labels, values, yerr=[errors_low, errors_high], fmt="none", capsize=5, color="black")
    ax.set_ylabel("Frobenius Distance / N"); ax.set_title("Recovery Distance Comparison (95% CI)")
    plt.tight_layout(); plt.savefig(output_path); plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# Figure F1: Problem Schematic (Network Diagram) — KEPT AS-IS
# ============================================================================

def generate_problem_schematic(output_path):
    """Generate Figure F1 — network diagram illustrating the problem setup."""
    N = 12
    np.random.seed(42)
    G = nx.DiGraph()
    G.add_nodes_from(range(N))
    edges = [
        (0, 1, 0.8), (0, 3, 0.5), (1, 2, 0.7), (2, 5, 0.6),
        (3, 4, 0.9), (4, 5, 0.4), (5, 8, 0.7), (6, 7, 0.8),
        (7, 8, 0.6), (8, 9, 0.5), (9, 10, 0.7), (10, 11, 0.9),
        (11, 6, 0.3), (2, 9, 0.4), (4, 7, 0.6), (1, 10, 0.3),
        (3, 6, 0.5), (5, 11, 0.4),
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    cpg_nodes = {0, 3, 6, 9}
    sensor_nodes = {2, 5, 8, 11}
    session1_measured = {0, 2, 4, 6, 8, 10}
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
        marker = "^" if node in sensor_nodes else "o"
        ax_main.scatter(x, y, s=node_size, c=facecolor, edgecolors=edgecolor,
                        linewidths=edgewidth, marker=marker, zorder=5)
        ax_main.text(x, y, str(node), ha="center", va="center",
                     fontsize=8, fontweight="bold", color="white", zorder=6)
    for node in sensor_nodes:
        x, y = pos[node]
        dx = x / np.hypot(x, y) * 0.6; dy = y / np.hypot(x, y) * 0.6
        ox, oy = x + dx, y + dy
        ax_main.annotate("", xy=(x, y), xytext=(ox, oy),
            arrowprops=dict(arrowstyle="-|>", color="#FF9800", lw=2.5,
                            connectionstyle="arc3,rad=0.15", shrinkB=12))
        ax_main.text(ox + dx * 0.15, oy + dy * 0.15, "S", fontsize=9,
                     fontweight="bold", ha="center", va="center", color="#FF9800", zorder=7)
    ax_main.text(0, -2.7, "Session 1: observe $\\{0, 2, 4, 6, 8, 10\\}$",
                 ha="center", fontsize=9, color="#2E7D32", fontstyle="italic")
    ax_main.text(0, -2.95, "Session 2: observe $\\{1, 3, 5, 7, 9, 11\\}$",
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
                    markeredgecolor="#333333", markersize=10, label="Sensor node (triangle)"),
        plt.Line2D([0], [0], marker=">", color="#FF9800", lw=0, markersize=8,
                    label="Stimulation input"),
    ]
    ax_main.legend(handles=legend_elements, loc="upper left", frameon=True,
                   fancybox=True, framealpha=0.9, fontsize=8)
    ax_inset = fig.add_axes([0.65, 0.18, 0.33, 0.68])
    ax_inset.set_xlim(0, 10); ax_inset.set_ylim(0, 10); ax_inset.axis("off")
    ax_inset.set_title("Covariance Accumulation\nAcross Sessions", fontsize=9,
                       fontweight="bold", pad=8)
    box_colors = ["#A5D6A7", "#90CAF9", "#CE93D8"]
    labels = [r"$\hat{\Sigma}_1$  (Session 1)", r"$\hat{\Sigma}_2$  (Session 2)",
              r"$\hat{\Sigma}_K$  (Session K)"]
    y_positions = [7.0, 4.5, 1.5]
    for i, (yp, color, lab) in enumerate(zip(y_positions, box_colors, labels)):
        box = FancyBboxPatch((1.0, yp), 4.5, 1.6, boxstyle="round,pad=0.15",
                             facecolor=color, edgecolor="#333333", linewidth=1.2)
        ax_inset.add_patch(box)
        ax_inset.text(3.25, yp + 0.8, lab, ha="center", va="center", fontsize=8)
        ax_inset.annotate("", xy=(7.5, 5.2), xytext=(5.7, yp + 0.8),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.2))
    ax_inset.text(3.25, 3.4, r"$\vdots$", ha="center", va="center", fontsize=14)
    acc_box = FancyBboxPatch((6.5, 4.0), 3.0, 2.4, boxstyle="round,pad=0.2",
                             facecolor="#FFF9C4", edgecolor="#F57F17", linewidth=2.0)
    ax_inset.add_patch(acc_box)
    ax_inset.text(8.0, 5.5, r"$\hat{\Sigma}$", ha="center", va="center",
                  fontsize=14, fontweight="bold")
    ax_inset.text(8.0, 4.7, "(accumulated)", ha="center", va="center", fontsize=7)
    fig.suptitle("Problem Setup: Partial Measurement Across Sessions",
                 fontsize=13, fontweight="bold", y=0.97)
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
    fig.suptitle("Method Pipeline: Covariance Accumulation + Granger Refinement",
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
    parser.add_argument("--figure", type=str, help="Generate specific figure (F1-F7)")
    parser.add_argument("--all", action="store_true", help="Generate all figures")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all or args.figure is None:
        figures = ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]
    else:
        figures = [args.figure]

    for fig_name in figures:
        print(f"\nGenerating {fig_name}...")
        try:
            if fig_name == "F1":
                generate_problem_schematic(output_dir / "fig1_problem_schematic.pdf")
            elif fig_name == "F2":
                data = load_results(results_dir / "E2_sparsity.json")
                plot_sparsity_effect(data, output_dir / "fig2_sparsity.pdf")
            elif fig_name == "F3":
                data = load_results(results_dir / "E3_stimulation.json")
                plot_stimulation_tradeoff(data, output_dir / "fig3_stimulation_tradeoff.pdf")
            elif fig_name == "F4":
                data = load_results(results_dir / "E4_granger.json")
                plot_granger_comparison(data, output_dir / "fig4_granger_refinement.pdf")
            elif fig_name == "F5":
                data = load_results(results_dir / "E1_baseline.json")
                plot_scaling(data, output_dir / "fig5_scaling.pdf")
            elif fig_name == "F6":
                data = load_results(results_dir / "E5_nonlinearity.json")
                plot_nonlinearity_robustness(data, output_dir / "fig6_nonlinearity.pdf")
            elif fig_name == "F7":
                generate_pipeline_schematic(output_dir / "fig7_pipeline_schematic.pdf")
        except FileNotFoundError as e:
            print(f"  Skipping {fig_name}: {e}")
            print(f"  Run the corresponding experiment first.")


if __name__ == "__main__":
    main()
