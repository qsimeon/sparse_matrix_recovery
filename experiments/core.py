"""
Core functions for sparse matrix recovery experiments.

Extracted from qsimeon_SparseMatrixRecovery.ipynb.
Contains: activation functions, network generation, dynamics simulation,
weight estimation, and optimization.

WHAT IS "AN EXPERIMENT" IN THIS PROJECT?
=========================================
An experiment is a specific fixed combination of parameters that defines
the problem setting. These parameters are the axes of variation we study:

  - N (num_nodes): size of the network (number of neurons)
  - T (max_timesteps): recording duration per session
  - measurement fraction: fraction of neurons observed per session
  - stim_gain: strength of extrinsic stimulation noise
  - stim_fraction: fraction of neurons receiving stimulation (num_stimulated / N)
  - nonlinearity (phi): transfer function applied to neuron states
  - K (num_sessions): number of recording sessions

One REPETITION of an experiment (num_networks, e.g. 20) means:
  - Draw a fresh random connectivity matrix W (a new random circuit topology)
  - Run K=50 recording sessions, each observing a different random subset
  - Estimate W from those sessions and measure recovery error

The 20 repetitions give error bars over random topologies.
The 50 sessions per topology are necessary for covariance accumulation.

Experiments E1-E7 each vary ONE OR TWO of these parameters while fixing
the rest at the baseline (N=15, T=1000, meas=66%, sigma=1.0, phi=tanh,
33% stimulation, K=50).

The mega sweep (experiments/sweep_config.yaml) varies all axes jointly to
find the optimal experimental design.
"""

import numpy as np
import torch
import networkx as nx
from scipy import sparse
from sklearn.preprocessing import StandardScaler
import joblib


# ============================================================================
# Activation Functions (numpy)
# ============================================================================

def identity(x):
    """Identity activation function."""
    return x


def sigmoid(x):
    """Logistic sigmoid: output in (0,1) with phi(0)=0.5. Related to tanh via sigmoid(x) = (1+tanh(x/2))/2."""
    return 1 / (1 + np.exp(-x))


def relu(x):
    """Rectified Linear Unit (ReLU) activation function."""
    return np.maximum(0, x)


def sat(x, alpha=1):
    """Saturation function used in nonlinear control."""
    if isinstance(x, np.ndarray):
        return np.where(np.abs(x) <= alpha, x, np.sign(x) * alpha)
    else:
        return x if np.abs(x) <= alpha else np.sign(x) * alpha


# Map from string names to functions
NONLINEARITIES = {
    "identity": identity,
    "sigmoid": sigmoid,
    "relu": relu,
    "sat": sat,
    "tanh": np.tanh,
    "sign": np.sign,
}


def get_nonlinearity(name: str):
    """Get a nonlinearity function by name."""
    if name in NONLINEARITIES:
        return NONLINEARITIES[name]
    raise ValueError(f"Unknown nonlinearity: {name}. Options: {list(NONLINEARITIES.keys())}")


# ============================================================================
# PyTorch Activation Layers
# ============================================================================

class AbsoluteActivation(torch.nn.Module):
    def forward(self, x):
        return torch.abs(x)


# ============================================================================
# Central Pattern Generator (CPG)
# ============================================================================

def generate_chaotic_reservoir(N=100, p=0.1, g=1.3, T=2500, dt=0.1):
    """
    Generate chaotic reservoir dynamics for CPG drive signal.

    Returns:
        chaotic_signal: array of shape (T, N), each row is the state r(t)
    """
    scale = 1.0 / np.sqrt(p * N)
    M_sp = sparse.random(N, N, density=p, data_rvs=np.random.randn)
    M = M_sp.toarray() * g * scale

    x = 0.1 * np.random.randn(N)
    chaotic_signal = []
    for step in range(int(T)):
        r = np.tanh(x)
        dx = -x + M.dot(r)
        x += dt * dx
        chaotic_signal.append(x.copy())
    chaotic_signal = np.array(chaotic_signal)
    scaler = StandardScaler()
    chaotic_signal = scaler.fit_transform(chaotic_signal)
    return chaotic_signal


class RandomNet(torch.nn.Module):
    """
    A randomly initialized neural network that implements a spatiotemporal
    function used as a central pattern generator (CPG).

    The output is periodic in time due to circular shifting of input dimensions,
    modulated by a chaotic reservoir drive signal.
    """

    def __init__(self, input_size, n_layers=3, layer_width=8, gain=1.0, use_chaos=True):
        super().__init__()
        self.input_size = input_size
        self.n_layers = n_layers
        self.layer_width = layer_width
        self.shifts = 0
        self.pi = torch.acos(torch.zeros(1)) * 2
        self.gain = gain
        self.use_chaos = use_chaos
        self.chaos_buffer = generate_chaotic_reservoir(N=max(input_size, 100))

        layers = []
        for i in range(n_layers):
            if i == 0:
                layer = torch.nn.Linear(input_size, layer_width, bias=False)
                torch.nn.init.normal_(layer.weight, mean=0.0, std=(1.0 / input_size) ** 0.5)
            else:
                layer = torch.nn.Linear(layer_width, layer_width, bias=False)
                torch.nn.init.normal_(layer.weight, mean=0.0, std=(1.0 / layer_width) ** 0.5)
            layers.extend([layer, torch.nn.RMSNorm(layer_width), AbsoluteActivation()])

        layer = torch.nn.Linear(layer_width, input_size, bias=False)
        torch.nn.init.normal_(layer.weight, mean=0.0, std=(1.0 / layer_width) ** 0.5)
        layers.extend([layer, torch.nn.Tanh()])
        self.model = torch.nn.Sequential(*layers)

    @torch.no_grad()
    def forward(self, x):
        assert x.shape[-1] == self.input_size, "Input of wrong size"
        x = torch.roll(x, self.shifts, dims=-1)

        if not self.use_chaos:
            t = (self.shifts / (2 * self.pi) + torch.arange(self.input_size)) / self.input_size
            drive = torch.sin(2 * self.pi * t).to(x.dtype).unsqueeze(0)
        else:
            t = self.shifts % len(self.chaos_buffer)
            drive = torch.tensor(self.chaos_buffer[t, :self.input_size]).to(x.dtype).unsqueeze(0)

        self.shifts += 1
        x = torch.nn.functional.rms_norm(x, (x.shape[-1],))
        y = self.model(x)
        output = (y + drive) * self.gain
        return output


def create_cpg_function(state_dim, **kwargs):
    """Creates a CPG function parameterized as a random deep neural network."""
    cpg_net = RandomNet(input_size=state_dim, **kwargs).double()
    cpg_net.eval()
    return cpg_net


def state_to_cpg(state, cpg_net):
    """Converts a state vector to a CPG drive vector using the provided neural network."""
    if isinstance(state, np.ndarray):
        _state_ = torch.from_numpy(state)
    else:
        _state_ = state
    if _state_.ndim == 1:
        _input_ = _state_.unsqueeze(0)
    else:
        _input_ = _state_
    with torch.no_grad():
        _output_ = cpg_net(_input_).detach()
    cpg = _output_.squeeze(0).numpy()
    return cpg


# ============================================================================
# Spectral Analysis
# ============================================================================

def calculate_spectral_radius(matrix):
    """Calculate the spectral radius of a square matrix."""
    assert matrix.shape[0] == matrix.shape[1], "Input matrix must be square."
    eigenvalues = np.linalg.eigvals(matrix)
    return max(abs(eigenvalues))


def adjust_spectral_radius(matrix, target_radius=1.0):
    """Adjust matrix so that its spectral radius is no more than target_radius."""
    eps = np.finfo(float).eps
    current_radius = calculate_spectral_radius(matrix)
    if current_radius <= target_radius - eps:
        gain = 1.0
    else:
        gain = (target_radius - eps) / current_radius
    return matrix * gain


# ============================================================================
# Network Topology Generation
# ============================================================================

def random_network_topology(num_nodes, non_negative_weights, force_stable, strongly_connected=True):
    """
    Creates a random connected directed network with specified properties.

    Returns:
        connection_weights: (num_nodes, num_nodes) weight matrix where W[i,j] is weight from j to i
        adjacency_matrix: binary adjacency matrix
    """
    density = 0.0
    step = 0.001
    connected = False
    while not connected:
        density = density + step
        density = min(density, 1.0)
        step = 1.1 * step
        step = min(step, 1 - density)
        adjacency_matrix = np.random.choice(
            [0, 1], size=(num_nodes, num_nodes), p=[1 - density, density]
        )
        adjacency_matrix[np.diag_indices(num_nodes)] = 0
        G = nx.from_numpy_array(A=adjacency_matrix.T, create_using=nx.DiGraph)
        if not strongly_connected:
            connected = nx.is_weakly_connected(G)
        else:
            connected = nx.is_strongly_connected(G)

    eps = np.finfo(float).eps
    if non_negative_weights:
        connection_weights = adjacency_matrix * (eps + np.random.rand(num_nodes, num_nodes))
    else:
        connection_weights = adjacency_matrix * (2 * (eps + np.random.rand(num_nodes, num_nodes) - 0.5))

    if force_stable:
        connection_weights = adjust_spectral_radius(connection_weights, target_radius=1.0)

    return connection_weights, adjacency_matrix


# ============================================================================
# Network Simulation
# ============================================================================

def create_network_data(
    session_idx, max_timesteps, num_nodes, num_cpgs, num_measured,
    num_stimulated, fixed_stim, stim_gain, nonlinearity, connection_weights,
    obs_noise_std=0.0, worker_seed=None,
):
    """
    Simulate dynamics on a network and return recorded data.

    Args:
        session_idx: index of this network instance
        max_timesteps: number of timesteps to record (after warmup)
        num_nodes: total nodes in network
        num_cpgs: number of CPG nodes
        num_measured: number of measured/observed nodes
        num_stimulated: number of nodes receiving extrinsic stimulation
        fixed_stim: if True, same stimulated nodes for all instances
        stim_gain: std of Gaussian stimulation noise
        nonlinearity: activation function
        connection_weights: (num_nodes, num_nodes) weight matrix
        worker_seed: per-worker random seed for reproducibility with joblib

    Returns:
        dict with all simulation data
    """
    # Seed each worker deterministically so results don't depend on
    # joblib scheduling order.
    if worker_seed is not None:
        np.random.seed(worker_seed)
        torch.manual_seed(worker_seed)

    assert connection_weights.shape == (num_nodes, num_nodes)

    warmup_timesteps = max_timesteps // 3
    simulation_steps = max_timesteps + warmup_timesteps

    session = f"session{session_idx}"
    network_data = {}
    activity_data = np.zeros((simulation_steps, num_nodes))
    extrinsic_input_matrix = np.zeros_like(activity_data)
    intrinsic_input_matrix = np.zeros_like(activity_data)
    total_input_matrix = np.zeros_like(activity_data)

    cpg_nodes_mask = np.zeros(num_nodes, dtype=bool)
    cpg_nodes_mask[:num_cpgs] = True

    measured_inds = sorted(
        np.random.choice(np.arange(num_nodes), size=num_measured, replace=False)
    )
    measured_nodes_mask = np.zeros(num_nodes, dtype=bool)
    measured_nodes_mask[measured_inds] = True

    spectral_radius = calculate_spectral_radius(connection_weights)
    adjacency_matrix = (np.abs(connection_weights) > 0).astype(int)
    density = np.count_nonzero(adjacency_matrix) / adjacency_matrix.size
    sparsity = 1 - density
    networkx_graph = nx.from_numpy_array(
        A=connection_weights.T, create_using=nx.DiGraph, edge_attr="weight"
    )

    if fixed_stim:
        stim_inds = np.arange(num_nodes)[-num_stimulated:].tolist()
    else:
        stim_inds = sorted(
            np.random.choice(np.arange(num_nodes), size=num_stimulated, replace=False)
        )
    stim_nodes_mask = np.zeros(num_nodes, dtype=bool)
    stim_nodes_mask[stim_inds] = True

    for t in range(simulation_steps):
        stimulation = np.random.normal(loc=0.0, scale=stim_gain, size=num_nodes)

        if t == 0:
            cpg_net = create_cpg_function(state_dim=num_nodes)
            extrinsic_drive = np.zeros(num_nodes)
            intrinsic_drive = np.zeros(num_nodes)
            total_input = extrinsic_drive + intrinsic_drive
            state = np.random.uniform(low=-5.0, high=5.0, size=num_nodes)
        else:
            central_pattern = state_to_cpg(state, cpg_net)
            extrinsic_drive = stim_nodes_mask * stimulation
            intrinsic_drive = cpg_nodes_mask * central_pattern
            total_input = extrinsic_drive + intrinsic_drive
            state = connection_weights @ nonlinearity(state) + total_input

        observed = state[measured_inds]
        if obs_noise_std > 0:
            observed = observed + np.random.normal(0, obs_noise_std, observed.shape)
        activity_data[t][measured_inds] = observed
        extrinsic_input_matrix[t] = extrinsic_drive
        intrinsic_input_matrix[t] = intrinsic_drive
        total_input_matrix[t] = total_input

    # Discard warmup
    activity_data = activity_data[warmup_timesteps:]
    extrinsic_input_matrix = extrinsic_input_matrix[warmup_timesteps:]
    intrinsic_input_matrix = intrinsic_input_matrix[warmup_timesteps:]
    total_input_matrix = total_input_matrix[warmup_timesteps:]

    network_data["session"] = session
    network_data["activity_data"] = activity_data
    network_data["max_timesteps"] = max_timesteps
    network_data["num_nodes"] = num_nodes
    network_data["measured_nodes_mask"] = measured_nodes_mask
    network_data["stim_nodes_mask"] = stim_nodes_mask
    network_data["cpg_nodes_mask"] = cpg_nodes_mask
    network_data["connection_weights"] = connection_weights
    network_data["spectral_radius"] = spectral_radius
    network_data["adjacency_matrix"] = adjacency_matrix
    network_data["density"] = density
    network_data["sparsity"] = sparsity
    network_data["networkx_graph"] = networkx_graph
    network_data["extrinsic_input_matrix"] = extrinsic_input_matrix
    network_data["intrinsic_input_matrix"] = intrinsic_input_matrix
    network_data["total_input_matrix"] = total_input_matrix
    network_data["nonlinearity"] = nonlinearity
    network_data["stim_gain"] = stim_gain

    return network_data


def create_multinetwork_dataset(
    num_sessions, max_timesteps, num_nodes, num_cpgs, num_measured,
    num_stimulated, fixed_stim, stim_gain, nonlinearity,
    non_negative_weights, force_stable, obs_noise_std=0.0,
):
    """
    Creates a dataset of multiple network instances with shared connectivity.
    Each instance has different initial conditions and measured/stimulated nodes.

    Args:
        obs_noise_std: Standard deviation of i.i.d. Gaussian observation noise
            added to measured neuron activity (default 0.0 = noiseless).
    """
    assert max_timesteps >= 100
    assert num_nodes >= 2
    assert num_stimulated <= num_nodes
    assert num_cpgs <= num_nodes
    assert num_measured <= num_nodes
    assert num_measured >= 2
    assert callable(nonlinearity)

    connection_weights, _ = random_network_topology(
        num_nodes, non_negative_weights, force_stable
    )

    # Pre-generate per-worker seeds from parent RNG so results are
    # deterministic regardless of joblib scheduling order.
    worker_seeds = np.random.randint(0, 2**31, size=num_sessions).tolist()

    results = joblib.Parallel(n_jobs=-2, verbose=0)(
        joblib.delayed(create_network_data)(
            session_idx, max_timesteps, num_nodes, num_cpgs,
            num_measured, num_stimulated, fixed_stim, stim_gain,
            nonlinearity, connection_weights, obs_noise_std,
            worker_seed=worker_seeds[session_idx],
        )
        for session_idx in range(num_sessions)
    )
    dataset = {res["session"]: res for res in results}
    return dataset


# ============================================================================
# Weight Estimation
# ============================================================================

def estimate_connectivity_weights(num_nodes, multinet_dataset, non_negative_weights=True):
    """
    Estimate connectivity weights from multi-network dataset using
    covariance-based estimator: W_hat = Cov(y_{t+1}, y_t) @ pinv(Cov(y_t, y_t))

    Structural priors applied to ALL estimates (not method-specific):
      (i)  No autapses: W_ii = 0
      (ii) Non-negativity: W_ij >= 0 (when non_negative_weights=True)

    NOTE: This operates on the OBSERVED data y_t (which may include measurement noise).
    When obs_noise_std > 0, y_t = x_t + ε_t, so:
      Cov(y,y) = Cov(x,x) + σ²I  (noise inflates diagonal)
      Cov(y_{t+1}, y_t) = Cov(x_{t+1}, x_t)  (cross-time noise is independent)
    The estimator becomes: W_hat = W * Σ_xx * (Σ_xx + σ²I)^{-1}
    This is equivalent to ridge regression with regularization parameter σ².

    Returns:
        dict with approx_W, true_W, oracle_W, covariance matrices, etc.
    """
    assert multinet_dataset['session0']['connection_weights'].shape == (num_nodes, num_nodes)

    total_mask = np.zeros((num_nodes, num_nodes))
    cov_x = np.zeros((num_nodes, num_nodes))
    cov_dtx = np.zeros((num_nodes, num_nodes))
    cov_phix = np.zeros((num_nodes, num_nodes))
    cov_bx = np.zeros((num_nodes, num_nodes))

    true_W = None
    Adj = None
    phi = None

    num_sessions = len(multinet_dataset)
    for session_idx in range(num_sessions):
        session = f"session{session_idx}"
        network_data = multinet_dataset[session]

        true_W = network_data["connection_weights"]
        Adj = network_data["adjacency_matrix"]
        phi = network_data["nonlinearity"]

        mask = network_data["measured_nodes_mask"].reshape(-1, 1)
        data = network_data["activity_data"]
        inputs = network_data["total_input_matrix"]

        X = data
        n = data.shape[0] - 1
        S = mask @ mask.T
        total_mask += S

        cov_x += ((X[:-1].T @ X[:-1]) / n) * S
        cov_dtx += ((X[1:].T @ X[:-1]) / n) * S
        cov_phix += ((phi(X[:-1]).T @ X[:-1]) / n) * S
        cov_bx += ((inputs[:-1].T @ X[:-1]) / n) * S

    num_never_obs = (np.diag(total_mask) < 1).sum()
    total_mask = np.clip(total_mask, a_min=1, a_max=None)
    cov_x = np.divide(cov_x, total_mask)
    cov_dtx = np.divide(cov_dtx, total_mask)
    cov_phix = np.divide(cov_phix, total_mask)
    cov_bx = np.divide(cov_bx, total_mask)

    approx_W = cov_dtx @ np.linalg.pinv(cov_x)
    # Structural priors applied uniformly to ALL estimates (not method-specific):
    #   (i)  No autapses: W_ii = 0 — diagonal dominated by autocorrelation
    #   (ii) Non-negativity: W_ij >= 0 — modeling prior for excitatory networks
    np.fill_diagonal(approx_W, 0)
    if non_negative_weights:
        approx_W = np.maximum(approx_W, 0.0)

    oracle_W = (cov_dtx - cov_bx) @ np.linalg.pinv(cov_phix)
    np.fill_diagonal(oracle_W, 0)
    if non_negative_weights:
        oracle_W = np.maximum(oracle_W, 0.0)

    # Diagnostics: condition number and error bound components
    # The estimation error decomposes as:
    #   E = W * [Cov(x,x) - Cov(phi(x),x)] * pinv(Cov(x,x))   [model mismatch]
    #     + Cov(b,x) * pinv(Cov(x,x))                            [input correlation]
    # Error bound: ||E||_F <= ||W||_F * ||Cov_x - Cov_phix||_F * kappa + ||Cov_bx||_F * kappa
    # where kappa = ||pinv(Cov_x)||_2 (inverse of smallest singular value)
    svs = np.linalg.svd(cov_x, compute_uv=False)
    cond_number = svs[0] / max(svs[-1], 1e-15)
    kappa = 1.0 / max(svs[-1], 1e-15)
    model_mismatch = np.linalg.norm(cov_x - cov_phix, "fro")
    input_correlation = np.linalg.norm(cov_bx, "fro")
    error_bound = np.linalg.norm(true_W, "fro") * model_mismatch * kappa + input_correlation * kappa

    return dict(
        approx_W=approx_W, true_W=true_W, oracle_W=oracle_W,
        cov_x=cov_x, cov_dtx=cov_dtx, cov_phix=cov_phix, cov_bx=cov_bx,
        Adj=Adj, phi=phi,
        total_mask=total_mask, num_never_obs=num_never_obs,
        # Diagnostics
        condition_number=cond_number,
        model_mismatch_norm=model_mismatch,
        input_correlation_norm=input_correlation,
        error_bound=error_bound,
    )


# ============================================================================
# Projected Gradient Optimization (Granger-causality refinement)
# ============================================================================

def clamp_W_constraints(W, mask_zero_positions, non_negative_weights=True, zero_diagonal=True):
    """Apply sparsity and non-negativity constraints to weight matrix."""
    if zero_diagonal:
        np.fill_diagonal(W, 0.0)
    for (i, j) in mask_zero_positions:
        W[i, j] = 0.0
    if non_negative_weights:
        W = np.maximum(W, 0.0)
    return W


def least_squares_backsolve(W, B, alpha=1e-6):
    """Solve for A such that A @ B ≈ W using ridge regression."""
    n = B.shape[0]
    BBt = B @ B.T
    for i in range(n):
        BBt[i, i] += alpha
    # Use solve instead of inv for numerical stability at large N
    A_new = np.linalg.solve(BBt, (W @ B.T).T).T
    return A_new


def projected_gradient_causal(
    cov_x, cov_dtx, non_negative_weights=True, zero_diagonal=True,
    steps=200, lr=1e-3, subiters=3,
):
    """
    Minimize ||A - A_init||^2 subject to Granger-causality sparsity constraints.

    The Granger step's unique contribution is enforcing non-causality zeros:
      - W[i,j] = 0 where cov_x[i,j] > cov_dtx[i,j] (Granger non-causality)

    Structural priors (no autapses, non-negativity) are applied upstream to ALL
    estimates via estimate_connectivity_weights(). They are re-enforced here for
    consistency but are not specific to the Granger refinement.
    """
    A_init = cov_dtx.copy()
    n = A_init.shape[0]
    B = np.linalg.pinv(cov_x)

    zero_positions = []
    if zero_diagonal:
        zero_positions.extend((i, i) for i in range(n))
    idx = np.argwhere(cov_x > cov_dtx)
    zero_positions.extend((int(i), int(j)) for (i, j) in idx)

    A = A_init.copy()

    for it in range(steps):
        grad = (A - A_init)
        A -= lr * grad

        for _ in range(subiters):
            W = A @ B
            W = clamp_W_constraints(W, zero_positions,
                                    non_negative_weights=non_negative_weights,
                                    zero_diagonal=zero_diagonal)
            A = least_squares_backsolve(W, B)

    W_optimized = A @ B
    A_optimized = A
    return A_optimized, W_optimized


# ============================================================================
# Parameter Resolution
# ============================================================================

def resolve_params(num_nodes, num_cpgs, num_measured, num_stimulated):
    """Resolve sentinel values (-999, 0, 999) for experiment parameters."""
    if num_cpgs is None or num_cpgs < 0:
        num_cpgs = 1
    elif num_cpgs == 0:
        num_cpgs = max(1, int(np.ceil(1 / 6 * num_nodes)))
    elif num_cpgs > num_nodes:
        num_cpgs = int(np.ceil(1 / 3 * num_nodes))

    if num_measured is None or num_measured < 0:
        num_measured = max(2, int(np.ceil(1 / 3 * num_nodes)))
    elif num_measured == 0:
        num_measured = int(np.ceil(2 / 3 * num_nodes))
    elif num_measured > num_nodes:
        num_measured = num_nodes

    if num_stimulated is None or num_stimulated < 0:
        num_stimulated = 1
    elif num_stimulated > num_nodes:
        num_stimulated = int(np.ceil(1 / 3 * num_nodes))

    return num_cpgs, num_measured, num_stimulated
