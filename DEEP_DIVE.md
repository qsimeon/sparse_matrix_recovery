# Deep Dive: Sparse Neural Connectivity Recovery

> A complete technical walkthrough of the project — what it does, how it works,
> why every design choice was made, and what the surprising findings are.
> Last updated: 2026-04-11 (comprehensive rewrite — all numbers verified against Apr 7 data).

---

## What Is This?

You have a brain circuit with N neurons wired together by synapses. You want to figure out the full
wiring diagram (an N×N matrix W), but your microscope can only see ~66% of neurons at a time.
Each recording session gives you a different partial view. This project shows how to stitch those
partial views together using covariance statistics, recover W, and then clean it up with biological
constraints — all without deep learning, just linear algebra and some clever bookkeeping.

**The core insight**: Whenever two neurons are simultaneously observed in a session, their
covariance contributes one "puzzle piece" toward the full N×N covariance matrix. After enough
sessions, the whole puzzle is assembled — and the connectivity matrix follows immediately from
one matrix equation.

---

## System Architecture

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    YOUR EXPERIMENT (K=50 sessions)              │
  │                                                                 │
  │  Session 1           Session 2           ...    Session K       │
  │  see {0,2,4,6,...}   see {1,3,5,7,...}          see {random}   │
  │  stim {2,5,8}        stim {3,7,9}                              │
  │       │                    │                                    │
  │       ▼                    ▼                                    │
  │  ┌──────────┐        ┌──────────┐                               │
  │  │ Partial  │        │ Partial  │   ...   (K partial matrices)  │
  │  │ Σ̂_1     │        │ Σ̂_2     │                               │
  │  │ co-obs   │        │ co-obs   │                               │
  │  │ pairs    │        │ pairs    │                               │
  │  └────┬─────┘        └────┬─────┘                               │
  └───────┼──────────────────┼─────────────────────────────────────┘
          └──────────┬────────┘
                     ▼
          ┌─────────────────────┐
          │  ACCUMULATE         │   Average Σ̂(i,j) over sessions
          │  element-wise       │   where both i and j were observed
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │  ESTIMATE           │   Ŵ = Σ̂_{x_{t+1},x_t} · Σ̂_{x_t,x_t}^{-1}
          │  (pseudoinverse)    │   (one matrix multiply)
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │  ZERO DIAGONAL      │   Ŵ_ii = 0  (no autapses)
          │  no-autapse prior   │   Removes autocorrelation artifact
          │  [biggest win]      │   (diagonal 3–4× too large)
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │  GRANGER REFINE     │   Projected gradient descent:
          │  non-causal zeros   │   W_ij = 0 where Σ_{x,x}(i,j) > Σ_{x+1,x}(i,j)
          └──────────┬──────────┘   (unique Granger contribution)
                     ▼
               Final Ŵ
        r = 0.90 (median), 0.94 (representative topology)
        31% error reduction over spectral prior baseline
```

---

## Key Files

| File | Lines | What it does |
|------|-------|-------------|
| `experiments/core.py` | 622 | **The brain.** All algorithms: network generation, CPG dynamics, covariance estimation, Granger refinement |
| `experiments/run_experiments.py` | 480 | **The lab.** Defines and runs E1–E8; each tests a specific hypothesis |
| `experiments/run_single_rep.py` | ~200 | **One repetition.** Runs a full topology→sessions→estimate→measure pipeline |
| `experiments/analysis.py` | ~1060 | **The artist.** Generates all 11 publication figures |
| `experiments/aggregate_results.py` | ~100 | Results aggregation utility |
| `scripts/generate_all_figures.py` | ~250 | **The orchestrator.** Calls analysis.py functions in order |
| `paper/main.tex` | ~760 | **The paper.** 21 pages: 10 main + 3 appendix, NeurIPS preprint format |
| `paper/references.bib` | ~250 | 23 verified citations |
| `paper/math_walkthrough.md` | ~500 | Educational companion — full mathematical derivation |
| `paper/poster.tex` | ~215 | A1 conference poster |
| `paper/presentation.tex` | ~335 | SDSCon 2026 lightning talk slides |
| `experiments/results/*.json` | 8 files | Raw data from all experiments (E1–E8) |

---

## Step-by-Step: Tracing One Experiment

Imagine you type:
```bash
uv run python experiments/run_experiments.py --experiment E2 --seed 42
```

### Step 1: Generate a random brain circuit
`core.py:260` → `random_network_topology(num_nodes=15, non_negative_weights=True, force_stable=True)`

```
Grow density until strongly connected
→ draw Uniform(0,1) weights on edges
→ scale so ρ(W) ≤ 1  (spectral radius control)
```

**Why strongly connected?** Sink nodes with no stimulation path leave Σ_{x,x} rank-deficient. Every node must be reachable from some stimulated node.

**Why non-negative weights?** EM connectomics measures synapse *size* (always positive); sign is carried by the *activity* direction. We use W ≥ 0 and let hyperpolarized states propagate inhibitory effects.

**Why ρ(W) ≤ 1?** With tanh (1-Lipschitz) and ρ(W) ≤ 1, the map x → Wφ(x) is non-expansive. The network falls silent without input — which motivates the CPG.

### Step 2: Create the CPG (once per topology)
`core.py:455` → `create_cpg_function(state_dim=N)` then `serialize_cpg(cpg_net)`

The CPG (Central Pattern Generator) models intrinsic oscillatory drive in biological circuits. It is a **frozen random deep network** that maps the current state x_t to an intrinsic drive signal b_CPG(t). Key properties:

```
  x_t (network state)
       │
       ▼
 ┌─────────────────────────────────┐
 │  CPG Function (frozen, per topology)
 │                                 │
 │  1. Circular shift of x_t by t  │  ← time-dependence (parameter-free)
 │  2. Random deep network         │  ← 3 layers, abs activations, Xavier
 │     (frozen weights)            │
 │  3. + Chaotic reservoir drive   │  ← Sussillo-style, g=1.3 (chaotic)
 │  4. Final tanh → output ∈[-1,1] │
 └────────────────┬────────────────┘
                  │
                  ▼
            b_CPG(t)    ← STATE-DEPENDENT! Cov(b_CPG, x_t) ≠ 0
```

**Why chaotic?** Real CPGs (e.g., lobster STG, respiratory rhythm generators) produce rich, non-periodic signals. Simple sinusoids would not capture this. The Sussillo-Abbott gain g=1.3 places the reservoir firmly in the chaotic regime.

**Why abs activations in hidden layers?** Empirically, abs produces richer frequency content (spectral entropy 1.75) than ReLU (1.16) — ReLU kills the negative half of activations, creating overly smooth, repetitive signals. Tanh (entropy 2.67) is broadest but saturates more in deeper networks.

**The critical state-dependence**: b_CPG(t) = f_CPG(x_t), so Cov(b_CPG, x_t) ≠ 0. This violates the independence assumption Cov(b_t, x_t) ≈ 0 in the estimator derivation, producing the dominant **E₂ error** (CPG correlation ~2× larger than E₁ model mismatch at median).

**Topology invariance**: The CPG is created **once per topology** and serialized. Each session worker deserializes a fresh copy (shifts=0 = independent time counter) but with the same weights. This was a critical bug fix — previously CPGs were created per session, giving each session a different oscillator.

### Step 3: Simulate K=50 recording sessions
`core.py:302` → `create_network_data(...)` called 50 times via `create_multinetwork_dataset`

Each session:
1. **Draw random measurement mask**: 10 of 15 neurons (66%) observed
2. **Draw random stimulation mask**: 5 of 15 neurons (33%) receive i.i.d. Gaussian noise
3. **CPG mask**: Always nodes 0–4 (fixed per topology, random circuit means no bias)
4. **Run dynamics** for T=1000 timesteps (+ T/3=333 warmup, discarded):

```python
# core.py:390 — THE dynamics equation
state = connection_weights @ nonlinearity(state) + total_input
# where total_input = stim_mask * N(0, σ²) + cpg_mask * f_CPG(state)
```

Workers run in parallel via `joblib.Parallel(n_jobs=-2)`. Per-worker seeds are pre-generated from the parent RNG to guarantee determinism regardless of scheduling order.

### Step 4: Accumulate covariances across sessions
`core.py:480` → `estimate_connectivity_weights(num_nodes=15, multinet_dataset)`

For each session k, let S = mask @ mask.T (co-measurement indicator):
```python
total_mask += S                         # count co-observations per pair
cov_x   += (X[:-1].T @ X[:-1] / n) * S   # Σ_{y_t, y_t}
cov_dtx += (X[1:].T  @ X[:-1] / n) * S   # Σ_{y_{t+1}, y_t}
```
Then average: `cov_x /= total_mask` (clipped to 1 to avoid division by zero; unobserved pairs get covariance 0 — a practical choice).

### Step 5: The Estimator
```python
# core.py:547 — THE estimator (one line)
approx_W = cov_dtx @ np.linalg.pinv(cov_x)
```
**Derivation**: x_{t+1} = Wφ(x_t) + b_t. Approximate φ(x) ≈ x and Cov(b,x) ≈ 0:
```
Σ_{x+1,x} ≈ W · Σ_{x,x}   →   W ≈ Σ_{x+1,x} · Σ_{x,x}^{-1}
```
`pinv` handles rank-deficient cases (large N, small T) via truncated SVD.

### Step 6: Structural priors (applied to ALL estimates)
```python
# core.py:551-553
np.fill_diagonal(approx_W, 0)          # no autapses — single biggest improvement
approx_W = np.maximum(approx_W, 0.0)   # non-negativity — modeling prior
```
These are enforced on both the approximate AND oracle estimators. They are not Granger-specific.

### Step 7: Granger refinement
`core.py:612` → `projected_gradient_causal(cov_x, cov_dtx)`

Unique contribution: zero W[i,j] where `cov_x[i,j] > cov_dtx[i,j]` (lagged cov ≤ contemporaneous cov → no causal influence from j to i). Applied via projected gradient descent, 200 steps, lr=1e-3.

**Net effect**: ~4% additional error reduction; precision 0.30 → 0.40; recall maintained at 0.97.

---

## The Eight Experiments (E1–E8)

| Exp | Question | Parameters | Key Result |
|-----|----------|-----------|------------|
| E1 | How does recovery scale? | N ∈ {15,159,300}, T ∈ {100,350,1000} | Best: N=300, T=1000 → 0.014 (97.5% over chance) |
| E2 | What does each step add? | Ablation: Chance→Adj→Spec→Est→Granger | 31% over spectral prior (0.083 vs 0.120) |
| E3 | Stimulation tradeoff? | σ ∈ [0,2] × meas ∈ {33,66,100%} | σ≈0.5 optimal at full measurement |
| E4 | How much observation? | Measurement 33–100%, N=15 | Plateaus above ~50% |
| E5 | Robust to nonlinearity? | tanh, relu, identity, sigmoid | tanh best (bounds variance, improves κ) |
| E6 | Does oracle win? | σ ∈ {0,0.1,0.25,0.5,1,2,5}, N=15 | Never — approx wins 1.45–2.72× at all σ |
| E7 | How many stimulated? | 0–100% of N=30 | ≥33% suffices; 0% catastrophically fails (0.83 vs 0.05) |
| E8 | Robust to noise? | σ_ε ∈ {0,0.05,0.1,0.2,0.5}, N=15 | σ_ε=0.1 → +1.5%; σ_ε=0.5 → +32% error |

**E8 is not in Table 1** — it is a robustness sanity check, not a primary hypothesis test.

### Baseline configuration (used for all experiments unless swept):
- N=15 neurons, T=1000 timesteps per session
- K=50 sessions per topology, 10 topologies per configuration
- 10 measured (66%), 5 stimulated (33%), 5 CPG nodes (33%)
- σ=1.0 stimulation gain, φ=tanh nonlinearity, seed=42

---

## The Error Decomposition (Why the "Wrong" Model Wins)

The estimation error decomposes exactly as:
```
Ŵ - W = W(D - I)            +  Σ_{b,x} · Σ_{x,x}^{-1}
          E₁: model mismatch       E₂: CPG correlation
          ||E₁||_F/N ≈ 0.080      ||E₂||_F/N ≈ 0.225
          (1×)                     (~2.8×  ← DOMINANT)
```

**E₁ (model mismatch)**: Price of approximating φ(x) ≈ x. Stein-Price identity gives D = diag(𝔼[sech²(x_i)]), so E₁ = W(D-I). For small state variance, 1-d_i ≈ σ_i².

**E₂ (CPG correlation)**: Price of ignoring Cov(b_CPG, x). State-dependent CPG drive creates this non-zero term. Dominates E₁ by ~2× at median, ~3× at representative topology.

**Why the oracle loses** (James-Stein phenomenon): The oracle must invert Σ_{φ(x),x} = D·Σ_{x,x} rather than Σ_{x,x}. The D matrix compresses rows heterogeneously, potentially worsening condition number: κ(D·Σ) ≤ κ(Σ) · d_max/d_min. The linear approximation avoids this compression — it is biased but better-conditioned. Classic bias-variance tradeoff.

**Oracle penalty across stimulation levels** (E6 data): ranges from 2.72× (σ=0) to 1.45× (σ=2). No crossover point exists.

---

## Five Key Insights

### 1. The "wrong" model wins (James-Stein)
Oracle (knows true tanh) is 1.45–2.72× *worse* than the naive linear approximation. Don't bother characterizing the neuronal transfer function.

### 2. CPG correlation is the real bottleneck
E₂ is ~2.8× larger than E₁ (representative topology: ~3×). Future improvements should focus on modeling intrinsic dynamics, not refining the nonlinear approximation.

### 3. The control-estimation tradeoff is quantifiable
Zero stimulation fails (Σ_{x,x} ill-conditioned, E7: error 0.83 vs 0.05). Sweet spot: σ ≈ 0.5–1.0, ~33% of neurons stimulated.

### 4. Diagonal zeroing is the unsung hero
One line (`np.fill_diagonal(approx_W, 0)`) matters more than 200 iterations of Granger refinement. The diagonal is dominated by autocorrelation (3–4× off-diagonal magnitude).

### 5. Partial observation has diminishing returns
33%→50% coverage: large improvement. 50%→100%: barely matters. You don't need full-circuit access — just enough sessions to cover all pairs.

---

## Mathematical Core (30-second version)

The whole method follows from one identity. Start from the dynamics:
```
x_{t+1} = W φ(x_t) + b_t
```
Multiply both sides by x_t^T, take expectations, approximate φ(x) ≈ x and Cov(b, x) ≈ 0:
```
Σ_{x+1, x} ≈ W · Σ_{x, x}    →    W ≈ Σ_{x+1, x} · Σ_{x, x}^{-1}
```
The rest of the paper — the Stein-Price identity, the oracle analysis, the Granger refinement — explains *when this works*, *why the approximation beats the oracle*, and *how to clean up the edges*.

For the full derivation with every step shown, see `paper/math_walkthrough.md`.

---

## How to Run

```bash
# Install dependencies
uv sync

# Run a single experiment (~2 min for one, ~20 min for all)
uv run python experiments/run_experiments.py --experiment E2 --seed 42
uv run python experiments/run_experiments.py --experiment all --seed 42

# Generate all 11 figures
uv run python scripts/generate_all_figures.py

# Compile paper (requires TeX Live)
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

# Compile poster / presentation
cd paper && pdflatex poster.tex
cd paper && pdflatex presentation.tex
```

---

## Verified Key Numbers (2026-04-07 data, cross-checked 2026-04-11)

| Metric | Value | Source |
|--------|-------|--------|
| Weight correlation r | 0.90 (median), 0.94 (representative topology) | E2_granger.json |
| Error vs spectral prior | 31% improvement (0.083 vs 0.120) | E2_granger.json |
| Best recovery | N=300, T=1000 → 0.014 (97.5% over chance) | E1_baseline.json |
| Precision (raw→Granger) | 0.30 → 0.40 | E2_granger.json |
| Recall (raw→Granger) | 0.97 → 0.97 | E2_granger.json |
| Oracle ratio range | 1.45×–2.72× worse | E6_oracle_crossover.json |
| E₂/E₁ error ratio | ~2× median, ~3× representative topology | E2_granger.json |
| E7 (0% stim) | 0.83 error (catastrophic) | E7_stim_fraction.json |
| E7 (33% stim) | 0.051 error (recovers) | E7_stim_fraction.json |
| E8 (σ_ε=0.1) | +1.5% error increase | E8_noise.json |
| E8 (σ_ε=0.5) | +32% error increase | E8_noise.json |

---

## Experiment Design: The Three Levels

```
LEVEL 1: TOPOLOGIES (num_networks = 10)
├── "10 different circuits" — each a fresh random W matrix
├── Purpose: statistical power over diverse circuit structures
└── Output: 10 independent error measurements → median ± 95% bootstrap CI

LEVEL 2: SESSIONS (K = num_sessions = 50)
├── "50 scans of the SAME circuit"
├── Purpose: covariance accumulation — piece together partial views
├── Each shares W, but sees different measured/stimulated subsets
└── This is the CORE of the method

LEVEL 3: TIMESTEPS (T = max_timesteps = 1000)
├── "1000 data points per scan"
├── Purpose: reliable empirical covariance estimates per session
└── Output: one session covariance matrix Σ̂_k
```

**DOF ratio** = (K × T) / N² tells you the estimation quality:
- N=15: DOF=222 → κ≈30 (good)
- N=159: DOF=1.98 → κ≈500 (degraded at T=100)
- N=300: DOF=0.56 (at T=100) → catastrophic rank deficiency
