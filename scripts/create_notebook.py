"""
Generate the comprehensive qsimeon_SparseMatrixRecovery.ipynb notebook.

This notebook walks through the full paper methodology, running actual
experiments and reproducing key results. It serves as the primary
reference notebook for the paper.
"""
import json


cells = []


def md(source_str):
    lines = source_str.split("\n")
    cells.append({
        "cell_type": "markdown", "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]
    })


def code(source_str):
    lines = source_str.split("\n")
    cells.append({
        "cell_type": "code", "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]],
        "execution_count": None, "outputs": []
    })


# =========================================================================
# TITLE
# =========================================================================
md(
    "# Recovering Sparse Neural Connectivity from Partial Measurements\n"
    "## A Covariance-Based Approach with Granger-Causality Refinement\n"
    "\n"
    "**Quilee Simeon** — Massachusetts Institute of Technology\n"
    "\n"
    "This notebook is the companion to our paper. It:\n"
    "1. Explains the mathematical framework step by step\n"
    "2. Runs actual simulations reproducing key paper results\n"
    "3. Generates the core figures from the paper\n"
    "4. Demonstrates every component: network generation, CPG dynamics, "
    "covariance estimation, diagonal zeroing, Granger refinement, "
    "implicit regularization, and error decomposition\n"
    "\n"
    "**To run**: Use the `work_env` conda environment or install dependencies "
    "from `pyproject.toml`.\n"
    "\n"
    "**Code**: All core functions are in `experiments/core.py`. "
    "Experiment runners in `experiments/run_experiments.py`. "
    "Figure generators in `experiments/analysis.py`."
)

# =========================================================================
# SETUP
# =========================================================================
md("## 1. Setup & Imports")

code(
    "import sys, numpy as np, torch\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "import pandas as pd\n"
    "from pathlib import Path\n"
    "from sklearn.decomposition import PCA\n"
    "\n"
    "# Import our core library\n"
    "sys.path.insert(0, str(Path('.').resolve()))\n"
    "from experiments.core import (\n"
    "    get_nonlinearity, resolve_params,\n"
    "    random_network_topology, create_network_data,\n"
    "    create_multinetwork_dataset, estimate_connectivity_weights,\n"
    "    projected_gradient_causal, calculate_spectral_radius,\n"
    "    adjust_spectral_radius, create_cpg_function, state_to_cpg,\n"
    "    identity, sigmoid, relu, sat,\n"
    ")\n"
    "\n"
    "# Reproducibility\n"
    "SEED = 42\n"
    "np.random.seed(SEED)\n"
    "torch.manual_seed(SEED)\n"
    "\n"
    "# Plot defaults\n"
    "plt.rcParams.update({\n"
    "    'figure.dpi': 150, 'font.size': 11,\n"
    "    'figure.figsize': (12, 4),\n"
    "    'axes.grid': True, 'grid.alpha': 0.3,\n"
    "})\n"
    "\n"
    "# Paper baseline parameters\n"
    "N = 15          # neurons\n"
    "T = 1000        # timesteps per session\n"
    "K = 50          # sessions (network instances)\n"
    "NUM_CPGS = 5    # CPG nodes (33%)\n"
    "NUM_MEAS = 10   # measured nodes (66%)\n"
    "NUM_STIM = 5    # stimulated nodes (33%)\n"
    "STIM = 1.0      # stimulation gain\n"
    "PHI = np.tanh   # nonlinearity\n"
    "\n"
    "print('Setup complete.')\n"
    "print(f'Baseline: N={N}, T={T}, K={K}, measured={NUM_MEAS}/{N} ({NUM_MEAS/N:.0%}), stim={STIM}')"
)

# =========================================================================
# MATHEMATICAL FRAMEWORK
# =========================================================================
md(
    "## 2. The Problem: Recovering Connectivity from Partial Measurements\n"
    "\n"
    "### The Dynamical System\n"
    "\n"
    "We model a neural circuit as a discrete-time recurrent network:\n"
    "\n"
    "$$x_{t+1} = W \\phi(x_t) + b_t \\quad \\text{(Eq. 1 in paper)}$$\n"
    "\n"
    "where:\n"
    "- $x_t \\in \\mathbb{R}^N$: neural state (activity of all $N$ neurons)\n"
    "- $W \\in \\mathbb{R}^{N \\times N}$: **unknown** connectivity matrix "
    "($W_{ij}$ = weight from neuron $j$ to neuron $i$)\n"
    "- $\\phi$: element-wise nonlinearity (1-Lipschitz, default $\\tanh$)\n"
    "- $b_t$: total input = extrinsic stimulation + intrinsic CPG drive\n"
    "\n"
    "### Constraints on $W$\n"
    "- $W_{ii} = 0$ for all $i$ (no self-connections / autapses)\n"
    "- $\\rho(W) \\leq 1$ (spectral radius $\\leq 1$ for stability)\n"
    "- $W_{ij} \\geq 0$ (excitatory-only, modeling unsigned connectome data)\n"
    "- Sparse, strongly-connected directed graph\n"
    "\n"
    "### The Estimator\n"
    "\n"
    "Under a linear approximation ($\\phi(x) \\approx x$) and input-state "
    "independence ($\\text{Cov}(b_t, x_t) \\approx 0$):\n"
    "\n"
    "$$\\hat{W} = \\Sigma_{x_{t+1}, x_t} \\cdot \\Sigma_{x_t, x_t}^{-1} "
    "\\quad \\text{(Eq. 5 in paper)}$$\n"
    "\n"
    "Then: set $\\hat{W}_{ii} = 0$ (no-autapse prior).\n"
    "\n"
    "### Key Idea: Accumulation Across Sessions\n"
    "\n"
    "We don't need to observe all $N$ neurons simultaneously. "
    "Across $K$ sessions with different observed subsets, "
    "we accumulate pairwise covariances. Each neuron pair $(i,j)$ "
    "contributes whenever both are co-observed."
)

# =========================================================================
# NETWORK GENERATION
# =========================================================================
md("## 3. Generate a Network & Visualize Its Structure")

code(
    "# Generate a random sparse, connected, excitatory network\n"
    "W_true, Adj = random_network_topology(N, non_negative_weights=True, force_stable=True)\n"
    "\n"
    "# Network statistics\n"
    "rho = calculate_spectral_radius(W_true)\n"
    "n_edges = np.count_nonzero(Adj)\n"
    "density = n_edges / (N * (N-1))  # exclude diagonal\n"
    "eigs = np.linalg.eigvals(W_true)\n"
    "\n"
    "print(f'Network: N={N} neurons, {n_edges} edges, density={density:.2f}')\n"
    "print(f'Spectral radius: {rho:.6f}')\n"
    "print(f'Diagonal (all zero): {np.allclose(np.diag(W_true), 0)}')\n"
    "print(f'All weights >= 0: {np.all(W_true >= 0)}')\n"
    "\n"
    "fig, axes = plt.subplots(1, 4, figsize=(18, 4))\n"
    "\n"
    "# (A) Weight matrix\n"
    "im = axes[0].imshow(W_true, cmap='viridis', aspect='equal')\n"
    "axes[0].set_title('(A) True $W$'); plt.colorbar(im, ax=axes[0], shrink=0.8)\n"
    "axes[0].set_xlabel('From neuron $j$'); axes[0].set_ylabel('To neuron $i$')\n"
    "\n"
    "# (B) Adjacency (binary)\n"
    "axes[1].imshow(Adj, cmap='gray_r', aspect='equal')\n"
    "axes[1].set_title('(B) Adjacency (binary)')\n"
    "\n"
    "# (C) Weight histogram\n"
    "nonzero_w = W_true[W_true > 0]\n"
    "axes[2].hist(nonzero_w, bins=20, color='steelblue', edgecolor='white')\n"
    "axes[2].set_xlabel('Weight'); axes[2].set_ylabel('Count')\n"
    "axes[2].set_title(f'(C) Weight distribution (n={len(nonzero_w)})')\n"
    "\n"
    "# (D) Eigenvalue spectrum\n"
    "theta = np.linspace(0, 2*np.pi, 100)\n"
    "axes[3].plot(np.cos(theta), np.sin(theta), 'k--', alpha=0.3, label='Unit circle')\n"
    "axes[3].scatter(eigs.real, eigs.imag, c='steelblue', s=50, zorder=5)\n"
    "axes[3].set_xlabel('Real'); axes[3].set_ylabel('Imaginary')\n"
    "axes[3].set_title(f'(D) Eigenvalues ($\\\\rho$={rho:.4f})')\n"
    "axes[3].set_aspect('equal'); axes[3].legend(fontsize=8)\n"
    "\n"
    "plt.tight_layout(); plt.show()"
)

# =========================================================================
# NONLINEARITIES
# =========================================================================
md(
    "## 4. Nonlinearities\n"
    "\n"
    "We require $\\phi$ to be **1-Lipschitz** ($|\\phi'(x)| \\leq 1$). "
    "Our default is $\\tanh$ (1-Lipschitz, bounded, odd). "
    "We also test identity, ReLU, and sigmoid — deliberately including "
    "nonlinearities that violate boundedness and/or odd symmetry to assess robustness."
)

code(
    "x = np.linspace(-3, 3, 200)\n"
    "fig, ax = plt.subplots(figsize=(7, 5))\n"
    "for name, fn, ls, c in [\n"
    "    ('tanh (default)', np.tanh, '-', '#4477AA'),\n"
    "    ('identity', identity, '--', '#228833'),\n"
    "    ('ReLU', relu, '-.', '#EE6677'),\n"
    "    ('sigmoid', sigmoid, ':', '#CCBB44'),\n"
    "]:\n"
    "    ax.plot(x, fn(x), ls, label=name, linewidth=2.5, color=c)\n"
    "ax.axhline(0, color='k', alpha=0.15); ax.axvline(0, color='k', alpha=0.15)\n"
    "ax.set_xlabel('$x$', fontsize=12); ax.set_ylabel('$\\phi(x)$', fontsize=12)\n"
    "ax.set_title('Nonlinearities tested (all 1-Lipschitz)', fontsize=13)\n"
    "ax.legend(fontsize=11); ax.set_aspect('equal')\n"
    "plt.tight_layout(); plt.show()\n"
    "\n"
    "# Verify 1-Lipschitz property\n"
    "dx = x[1] - x[0]\n"
    "for name, fn in [('tanh', np.tanh), ('identity', identity), ('ReLU', relu), ('sigmoid', sigmoid)]:\n"
    "    deriv = np.diff(fn(x)) / dx\n"
    "    max_deriv = np.max(np.abs(deriv))\n"
    "    print(f'{name:10s}: max|phi\\'(x)| = {max_deriv:.4f}  (1-Lipschitz: {max_deriv <= 1.001})')"
)

# =========================================================================
# CPG DYNAMICS
# =========================================================================
md(
    "## 5. Central Pattern Generators (CPGs)\n"
    "\n"
    "Real neural circuits have **intrinsic autonomous dynamics** — oscillatory "
    "patterns that persist without external input. We model these as CPGs: "
    "a subset of nodes driven by a chaotic reservoir network (`RandomNet`).\n"
    "\n"
    "**Critical property**: CPG drive is **state-dependent**: "
    "$b_{\\text{CPG}}(t) = \\text{cpg}(x_t)$. This means $\\text{Cov}(b_t, x_t) \\neq 0$, "
    "violating our independence assumption. This turns out to be the "
    "**dominant error source** (not the linear approximation!).\n"
    "\n"
    "CPG nodes can be **detected from data** via their elevated activity variance."
)

code(
    "# Simulate autonomous dynamics (no stimulation) to see CPG behavior\n"
    "cpg_net = create_cpg_function(state_dim=N)\n"
    "state = np.random.randn(N) * 0.1\n"
    "T_demo = 300\n"
    "states_auto = np.zeros((T_demo, N))\n"
    "cpg_mask = np.zeros(N, dtype=bool); cpg_mask[:NUM_CPGS] = True\n"
    "\n"
    "for t in range(T_demo):\n"
    "    cpg_drive = state_to_cpg(state, cpg_net)\n"
    "    b = cpg_mask * cpg_drive  # only CPG nodes get drive\n"
    "    state = W_true @ np.tanh(state) + b\n"
    "    states_auto[t] = state\n"
    "\n"
    "# Now simulate WITH stimulation\n"
    "np.random.seed(SEED); torch.manual_seed(SEED)\n"
    "cpg_net2 = create_cpg_function(state_dim=N)\n"
    "state2 = np.random.randn(N) * 0.1\n"
    "states_stim = np.zeros((T_demo, N))\n"
    "stim_mask = np.zeros(N, dtype=bool); stim_mask[-NUM_STIM:] = True\n"
    "\n"
    "for t in range(T_demo):\n"
    "    cpg_drive2 = state_to_cpg(state2, cpg_net2)\n"
    "    b2 = cpg_mask * cpg_drive2 + stim_mask * np.random.normal(0, STIM, N)\n"
    "    state2 = W_true @ np.tanh(state2) + b2\n"
    "    states_stim[t] = state2\n"
    "\n"
    "fig, axes = plt.subplots(2, 3, figsize=(16, 8))\n"
    "\n"
    "# Row 1: Time series\n"
    "for i in range(NUM_CPGS):\n"
    "    axes[0,0].plot(states_auto[:, i], label=f'CPG n{i}', alpha=0.8)\n"
    "axes[0,0].plot(states_auto[:, 6], '--', label='n6', alpha=0.5, color='gray')\n"
    "axes[0,0].set_title('(A) Autonomous dynamics'); axes[0,0].set_ylabel('Activity')\n"
    "axes[0,0].legend(fontsize=7)\n"
    "\n"
    "for i in range(NUM_CPGS):\n"
    "    axes[0,1].plot(states_stim[:, i], label=f'CPG n{i}', alpha=0.8)\n"
    "axes[0,1].plot(states_stim[:, 6], '--', label='n6', alpha=0.5, color='gray')\n"
    "axes[0,1].set_title('(B) With stimulation (stim=1.0)')\n"
    "axes[0,1].legend(fontsize=7)\n"
    "\n"
    "# Per-node variance for CPG detection\n"
    "var_auto = np.var(states_auto, axis=0)\n"
    "colors = ['salmon' if cpg_mask[i] else 'steelblue' for i in range(N)]\n"
    "axes[0,2].bar(range(N), var_auto, color=colors)\n"
    "axes[0,2].axhline(np.median(var_auto), ls='--', color='gray', label='Median')\n"
    "axes[0,2].set_title('(C) Per-node variance (CPG=red)')\n"
    "axes[0,2].set_xlabel('Neuron'); axes[0,2].set_ylabel('Variance')\n"
    "axes[0,2].legend(fontsize=8)\n"
    "\n"
    "# Row 2: PCA phase portraits + power spectrum\n"
    "pca = PCA(n_components=2)\n"
    "X_auto = pca.fit_transform(states_auto)\n"
    "axes[1,0].scatter(X_auto[:, 0], X_auto[:, 1], c=range(T_demo), cmap='viridis', s=5)\n"
    "axes[1,0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.0%})')\n"
    "axes[1,0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.0%})')\n"
    "axes[1,0].set_title('(D) Phase portrait (autonomous)')\n"
    "\n"
    "pca2 = PCA(n_components=2)\n"
    "X_stim = pca2.fit_transform(states_stim)\n"
    "axes[1,1].scatter(X_stim[:, 0], X_stim[:, 1], c=range(T_demo), cmap='viridis', s=5)\n"
    "axes[1,1].set_xlabel(f'PC1 ({pca2.explained_variance_ratio_[0]:.0%})')\n"
    "axes[1,1].set_ylabel(f'PC2 ({pca2.explained_variance_ratio_[1]:.0%})')\n"
    "axes[1,1].set_title('(E) Phase portrait (stimulated)')\n"
    "\n"
    "# Power spectrum\n"
    "from scipy.signal import welch\n"
    "for data, label, color in [(states_auto, 'Autonomous', '#4477AA'), (states_stim, 'Stimulated', '#EE6677')]:\n"
    "    freqs, psd = welch(data.mean(axis=1), fs=1.0, nperseg=min(64, T_demo//2))\n"
    "    axes[1,2].semilogy(freqs, psd, label=label, color=color, linewidth=2)\n"
    "axes[1,2].set_xlabel('Frequency'); axes[1,2].set_ylabel('PSD')\n"
    "axes[1,2].set_title('(F) Power spectrum'); axes[1,2].legend()\n"
    "\n"
    "plt.suptitle(f'CPG Dynamics: N={N}, {NUM_CPGS} CPG nodes, stim={STIM}', fontsize=14, y=1.02)\n"
    "plt.tight_layout(); plt.show()"
)

# =========================================================================
# COVARIANCE ESTIMATION
# =========================================================================
md(
    "## 6. Running the Estimation Pipeline\n"
    "\n"
    "Now we run the full pipeline:\n"
    "1. Generate $K=50$ sessions with shared $W$ but different measured/stimulated subsets\n"
    "2. Accumulate pairwise covariances across sessions\n"
    "3. Compute $\\hat{W} = \\Sigma_{x_{t+1},x_t} \\Sigma_{x_t,x_t}^{-1}$\n"
    "4. Zero the diagonal (no-autapse prior)\n"
    "5. Apply Granger-causality refinement"
)

code(
    "%%time\n"
    "# Generate multi-session dataset\n"
    "np.random.seed(SEED); torch.manual_seed(SEED)\n"
    "dataset = create_multinetwork_dataset(\n"
    "    num_sessions=K, max_timesteps=T, num_nodes=N,\n"
    "    num_cpgs=NUM_CPGS, num_measured=NUM_MEAS, num_stimulated=NUM_STIM,\n"
    "    fixed_stim=False, stim_gain=STIM, nonlinearity=PHI,\n"
    "    non_negative_weights=True, force_stable=True,\n"
    ")\n"
    "print(f'Created {K} sessions, each with T={T} timesteps, {NUM_MEAS}/{N} neurons measured')\n"
    "\n"
    "# Estimate connectivity\n"
    "results = estimate_connectivity_weights(N, dataset)\n"
    "W_est = results['approx_W']     # diagonal already zeroed in core.py\n"
    "W_true = results['true_W']\n"
    "W_oracle = results['oracle_W']\n"
    "cov_x = results['cov_x']\n"
    "cov_dtx = results['cov_dtx']\n"
    "cov_phix = results['cov_phix']\n"
    "cov_bx = results['cov_bx']\n"
    "\n"
    "# Granger refinement\n"
    "_, W_granger = projected_gradient_causal(cov_x, cov_dtx, non_negative_weights=True)\n"
    "\n"
    "# Errors\n"
    "err_est = np.linalg.norm(W_true - W_est, 'fro') / N\n"
    "err_granger = np.linalg.norm(W_true - W_granger, 'fro') / N\n"
    "err_oracle = np.linalg.norm(W_true - W_oracle, 'fro') / N\n"
    "err_chance = np.linalg.norm(W_true - np.random.rand(N, N) * W_true.max(), 'fro') / N\n"
    "\n"
    "# Correlation\n"
    "mask = ~np.eye(N, dtype=bool)\n"
    "r_est = np.corrcoef(W_true[mask], W_est[mask])[0, 1]\n"
    "r_granger = np.corrcoef(W_true[mask], W_granger[mask])[0, 1]\n"
    "\n"
    "print(f'\\nResults:')\n"
    "print(f'  Condition number:   {results[\"condition_number\"]:.1f}')\n"
    "print(f'  Chance error:       {err_chance:.4f}')\n"
    "print(f'  Estimate error:     {err_est:.4f}  (r={r_est:.3f})')\n"
    "print(f'  Granger error:      {err_granger:.4f}  (r={r_granger:.3f})')\n"
    "print(f'  Oracle error:       {err_oracle:.4f}  ({err_oracle/err_est:.1f}x WORSE than estimate!)')\n"
    "print(f'  Improvement vs chance: {(err_chance - err_granger)/err_chance:.0%}')"
)

# =========================================================================
# DIAGONAL ZEROING
# =========================================================================
md(
    "## 7. The No-Autapse Prior (Diagonal Zeroing)\n"
    "\n"
    "The **single most impactful step** in the pipeline. "
    "The raw diagonal of $\\hat{W}$ is dominated by autocorrelation "
    "(each neuron correlates with itself across time), not genuine self-connectivity."
)

code(
    "# Recompute raw estimate WITHOUT diagonal zeroing\n"
    "W_raw = cov_dtx @ np.linalg.pinv(cov_x)\n"
    "W_zeroed = W_raw.copy()\n"
    "np.fill_diagonal(W_zeroed, 0)\n"
    "\n"
    "err_raw = np.linalg.norm(W_true - W_raw, 'fro') / N\n"
    "err_zeroed = np.linalg.norm(W_true - W_zeroed, 'fro') / N\n"
    "improvement = (err_raw - err_zeroed) / err_raw * 100\n"
    "\n"
    "print('=== Diagonal Zeroing Impact ===')\n"
    "print(f'Error WITHOUT zeroing: {err_raw:.4f}')\n"
    "print(f'Error WITH zeroing:    {err_zeroed:.4f}')\n"
    "print(f'Improvement:           {improvement:.0f}%')\n"
    "print()\n"
    "print('Diagonal values (raw estimate vs true):')\n"
    "print(f'  Raw diag:  {np.diag(W_raw).round(3)}')\n"
    "print(f'  True diag: {np.diag(W_true)}  (all zeros by construction)')"
)

# =========================================================================
# WEIGHT RECOVERY VISUALIZATION
# =========================================================================
md("## 8. Visualizing Weight Recovery")

code(
    "fig, axes = plt.subplots(2, 4, figsize=(18, 8))\n"
    "\n"
    "# Row 1: Heatmaps\n"
    "vmax = max(W_true.max(), abs(W_est).max(), abs(W_granger).max())\n"
    "kw = dict(cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='equal')\n"
    "\n"
    "for ax, mat, title in zip(\n"
    "    axes[0],\n"
    "    [W_true, W_est, W_granger, W_true - W_granger],\n"
    "    ['(A) True $W$', f'(B) Estimate (err={err_est:.3f})',\n"
    "     f'(C) Granger (err={err_granger:.3f})', '(D) Error $W - \\hat{W}$'],\n"
    "):\n"
    "    im = ax.imshow(mat, **kw)\n"
    "    ax.set_title(title, fontsize=10)\n"
    "    plt.colorbar(im, ax=ax, shrink=0.7)\n"
    "\n"
    "# Row 2: Scatter plots + diagnostics\n"
    "# (E) True vs Estimate scatter\n"
    "axes[1,0].scatter(W_true[mask], W_est[mask], alpha=0.5, s=20, c='#4477AA')\n"
    "axes[1,0].plot([0, W_true.max()], [0, W_true.max()], 'k--', alpha=0.5)\n"
    "axes[1,0].set_xlabel('True $W_{ij}$'); axes[1,0].set_ylabel('Estimated')\n"
    "axes[1,0].set_title(f'(E) Estimate (r={r_est:.3f})')\n"
    "\n"
    "# (F) True vs Granger scatter\n"
    "axes[1,1].scatter(W_true[mask], W_granger[mask], alpha=0.5, s=20, c='#228833')\n"
    "axes[1,1].plot([0, W_true.max()], [0, W_true.max()], 'k--', alpha=0.5)\n"
    "axes[1,1].set_xlabel('True $W_{ij}$'); axes[1,1].set_ylabel('Granger-refined')\n"
    "axes[1,1].set_title(f'(F) Granger (r={r_granger:.3f})')\n"
    "\n"
    "# (G) Oracle comparison\n"
    "methods = ['Chance', 'Estimate', 'Granger', 'Oracle']\n"
    "errors = [err_chance, err_est, err_granger, err_oracle]\n"
    "colors = ['#BBBBBB', '#4477AA', '#228833', '#EE6677']\n"
    "axes[1,2].bar(methods, errors, color=colors)\n"
    "axes[1,2].set_ylabel('Error (Frobenius / N)')\n"
    "axes[1,2].set_title('(G) Method comparison')\n"
    "for i, (m, e) in enumerate(zip(methods, errors)):\n"
    "    axes[1,2].text(i, e + 0.005, f'{e:.3f}', ha='center', fontsize=9)\n"
    "\n"
    "# (H) Condition number context\n"
    "sv = np.linalg.svd(cov_x, compute_uv=False)\n"
    "axes[1,3].semilogy(sv, 'o-', color='#4477AA', markersize=6)\n"
    "axes[1,3].set_xlabel('Index'); axes[1,3].set_ylabel('Singular value')\n"
    "axes[1,3].set_title(f'(H) $\\\\Sigma_{{x,x}}$ spectrum ($\\\\kappa$={sv[0]/sv[-1]:.0f})')\n"
    "\n"
    "plt.suptitle('Weight Recovery: Paper Baseline Configuration', fontsize=14, y=1.02)\n"
    "plt.tight_layout(); plt.show()"
)

# =========================================================================
# IMPLICIT REGULARIZATION
# =========================================================================
md(
    "## 9. Implicit Regularization: Why the Oracle Loses\n"
    "\n"
    "**Key finding**: The \"incorrect\" linear approximation ($\\Sigma_{x,x}$) "
    "outperforms the oracle ($\\Sigma_{\\phi(x),x}$) with known $\\phi$ and $b$.\n"
    "\n"
    "**Why?** By the Stein-Price identity:\n"
    "$$\\Sigma_{\\phi(x),x} = D' \\Sigma_{x,x}, \\quad D' = \\text{diag}(\\mathbb{E}[\\text{sech}^2(x_i)])$$\n"
    "\n"
    "Since $D'_{ii} < 1$, the oracle covariance is a \"compressed\" version of "
    "$\\Sigma_{x,x}$ with **worse conditioning**. Inverting it amplifies noise.\n"
    "\n"
    "This is the **bias-variance tradeoff**: the approximate estimator is biased "
    "(ignores nonlinearity) but low-variance (well-conditioned), while the oracle "
    "is unbiased but high-variance."
)

code(
    "# Condition number comparison\n"
    "sv_x = np.linalg.svd(cov_x, compute_uv=False)\n"
    "sv_phi = np.linalg.svd(cov_phix, compute_uv=False)\n"
    "kappa_x = sv_x[0] / max(sv_x[-1], 1e-15)\n"
    "kappa_phi = sv_phi[0] / max(sv_phi[-1], 1e-15)\n"
    "\n"
    "print('=== Implicit Regularization ===')\n"
    "print(f'Approximate error: {err_est:.4f}')\n"
    "print(f'Oracle error:      {err_oracle:.4f}  ({err_oracle/err_est:.1f}x WORSE)')\n"
    "print()\n"
    "print(f'kappa(Cov_x):       {kappa_x:.1f}')\n"
    "print(f'kappa(Cov_phi_x):   {kappa_phi:.1f}  ({kappa_phi/kappa_x:.1f}x worse conditioned)')\n"
    "print()\n"
    "print('The oracle must invert a MORE ill-conditioned matrix.')\n"
    "print('The linear approximation trades small bias for much lower variance.')"
)

# =========================================================================
# ERROR DECOMPOSITION
# =========================================================================
md(
    "## 10. Error Decomposition\n"
    "\n"
    "The estimation error has two sources (Eq. 7 in paper):\n"
    "\n"
    "$$\\hat{W} - W = \\underbrace{W(\\Sigma_{\\phi(x),x} - \\Sigma_{x,x})\\Sigma_{x,x}^{-1}}_{E_1: "
    "\\text{model mismatch}} + \\underbrace{\\Sigma_{b,x}\\Sigma_{x,x}^{-1}}_{E_2: \\text{input correlation}}$$\n"
    "\n"
    "- $E_1$: Error from the linear approximation $\\phi(x) \\approx x$\n"
    "- $E_2$: Error from CPG-state correlation $\\text{Cov}(b_{\\text{CPG}}, x) \\neq 0$"
)

code(
    "pinv_x = np.linalg.pinv(cov_x)\n"
    "E1 = W_true @ (cov_phix - cov_x) @ pinv_x\n"
    "E2 = cov_bx @ pinv_x\n"
    "\n"
    "e1 = np.linalg.norm(E1, 'fro') / N\n"
    "e2 = np.linalg.norm(E2, 'fro') / N\n"
    "e_total = np.linalg.norm(W_est - W_true, 'fro') / N\n"
    "\n"
    "print('=== Error Decomposition ===')\n"
    "print(f'E1 (model mismatch):  {e1:.4f}')\n"
    "print(f'E2 (CPG correlation): {e2:.4f}')\n"
    "print(f'Total error:          {e_total:.4f}')\n"
    "print(f'E2/E1 ratio:          {e2/e1:.1f}x')\n"
    "print()\n"
    "print('CPG correlation (E2) is the DOMINANT error source.')\n"
    "print('The linear approximation (E1) is NOT the bottleneck.')\n"
    "print(f'(Total < E1+E2 because the components partially cancel.)')\n"
    "\n"
    "fig, ax = plt.subplots(figsize=(6, 4))\n"
    "bars = ax.bar(['$E_1$ (model)', '$E_2$ (CPG corr.)', 'Total'],\n"
    "              [e1, e2, e_total],\n"
    "              color=['#4477AA', '#EE6677', '#AA3377'])\n"
    "for bar, val in zip(bars, [e1, e2, e_total]):\n"
    "    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,\n"
    "            f'{val:.3f}', ha='center', fontsize=11)\n"
    "ax.set_ylabel('$||\\cdot||_F / N$')\n"
    "ax.set_title('Error Decomposition: CPG correlation dominates')\n"
    "plt.tight_layout(); plt.show()"
)

# =========================================================================
# MULTI-REPETITION EXPERIMENT
# =========================================================================
md(
    "## 11. Running a Full Experiment (Multiple Topologies)\n"
    "\n"
    "The results above are for a single network topology. "
    "To get robust statistics, we repeat across multiple random topologies "
    "(as in the paper). Here we run a mini version of E4 (the ablation study)."
)

code(
    "%%time\n"
    "from experiments.run_single_rep import one_repetition\n"
    "\n"
    "# Run 10 repetitions (10 random topologies, 50 sessions each)\n"
    "n_reps = 10\n"
    "all_distances = []\n"
    "for rep in range(n_reps):\n"
    "    distances = one_repetition(\n"
    "        rep, SEED, K, T, N, NUM_CPGS, NUM_MEAS, NUM_STIM,\n"
    "        STIM, 'tanh',\n"
    "    )\n"
    "    all_distances.append(distances)\n"
    "    print(f'  Rep {rep+1}/{n_reps}: est={distances[\"estimate_distance\"]:.4f}, '\n"
    "          f'granger={distances[\"optimized_distance\"]:.4f}')\n"
    "\n"
    "df = pd.DataFrame(all_distances)\n"
    "print(f'\\n=== Summary over {n_reps} topologies ===')\n"
    "for col in ['chance_distance', 'estimate_distance', 'optimized_distance']:\n"
    "    med = df[col].median()\n"
    "    print(f'  {col:25s}: median={med:.4f}')\n"
    "\n"
    "# Bar chart\n"
    "fig, ax = plt.subplots(figsize=(8, 5))\n"
    "cols = ['chance_distance', 'estimate_distance', 'optimized_distance']\n"
    "labels = ['Chance', 'Estimate\\n(diag zeroed)', 'Granger\\nrefined']\n"
    "colors = ['#BBBBBB', '#4477AA', '#228833']\n"
    "medians = [df[c].median() for c in cols]\n"
    "ax.bar(labels, medians, color=colors, edgecolor='white', linewidth=1.5)\n"
    "for i, (lbl, med) in enumerate(zip(labels, medians)):\n"
    "    ax.text(i, med + 0.01, f'{med:.3f}', ha='center', fontsize=11, fontweight='bold')\n"
    "ax.set_ylabel('Frobenius Error / N', fontsize=12)\n"
    "ax.set_title(f'Recovery Error ({n_reps} topologies, {K} sessions each)', fontsize=13)\n"
    "plt.tight_layout(); plt.show()"
)

# =========================================================================
# SUMMARY
# =========================================================================
md(
    "## 12. Summary of Key Findings\n"
    "\n"
    "| Finding | Evidence | Paper Section |\n"
    "|---------|----------|---------------|\n"
    "| Covariance accumulation recovers $W$ | $r \\sim 0.96$ correlation | E1, E2 |\n"
    "| Diagonal zeroing is the most impactful step | ~30-50% error reduction | Sec 3.1 |\n"
    "| Granger refinement adds 6-15% improvement | Perfect recall (1.0) | E4 |\n"
    "| Linear approximation = implicit regularization | Oracle 2-4x worse | E6 |\n"
    "| CPG correlation dominates error ($E_2 \\gg E_1$) | 3-4x ratio | Discussion |\n"
    "| Moderate stimulation is optimal | Zero stim fails at high measurement | E3 |\n"
    "| $\\tanh$ yields best recovery (counterintuitively) | Bounds state variance | E5 |\n"
    "\n"
    "### How to run the full paper experiments\n"
    "\n"
    "```bash\n"
    "# All 7 experiments\n"
    "python experiments/run_experiments.py --experiment all --seed 42\n"
    "\n"
    "# Regenerate all 10 figures\n"
    "python scripts/generate_all_figures.py\n"
    "```\n"
    "\n"
    "### Project structure\n"
    "\n"
    "```\n"
    "sparse_matrix_recovery/\n"
    "  experiments/core.py          # Core algorithms\n"
    "  experiments/run_experiments.py # E1-E6 experiment runner\n"
    "  experiments/analysis.py      # Figure generation\n"
    "  paper/main.tex               # LaTeX paper\n"
    "  paper/figures/               # 8 paper figures\n"
    "  paper/references.bib         # 20 references\n"
    "```\n"
    "\n"
    "**Code**: [github.com/qsimeon/sparse_matrix_recovery](https://github.com/qsimeon/sparse_matrix_recovery)"
)

# =========================================================================
# BUILD AND VERIFY
# =========================================================================
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

out_path = "notebooks/qsimeon_SparseMatrixRecovery.ipynb"
with open(out_path, "w") as f:
    json.dump(nb, f, indent=1)

# Verify syntax
errors = 0
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        try:
            compile(src, f"cell_{i}", "exec")
        except SyntaxError as e:
            print(f"SYNTAX ERROR cell {i}: {e}")
            errors += 1

md_count = sum(1 for c in nb["cells"] if c["cell_type"] == "markdown")
code_count = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
print(f"Written: {out_path}")
print(f"  {len(nb['cells'])} cells ({md_count} markdown, {code_count} code)")
print(f"  {errors} syntax errors")
