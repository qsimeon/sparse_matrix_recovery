# Deep Dive: Sparse Neural Connectivity Recovery

> A complete technical walkthrough of the project — what it does, how it works,
> why every design choice was made, and what the surprising findings are.
> Generated 2026-03-24.

---

## What Is This?

You have a brain circuit with N neurons wired together by synapses. You want to figure out the full wiring diagram (an N x N matrix W), but your microscope can only see ~66% of neurons at a time. Each recording session gives you a different partial view. This project shows how to stitch those partial views together using covariance statistics, recover W, and then clean it up with biological constraints — all without deep learning, just linear algebra and some clever bookkeeping.

---

## System Architecture

```
                          YOUR EXPERIMENT
                    (K=50 recording sessions)
                              |
          Session 1           |          Session 2          ...
     see {0,2,4,6,8,10}      |     see {1,3,5,7,9,11}
     stim neurons {8,10}      |     stim neurons {3,7}
              |                |              |
              v                |              v
    +-------------------+     |    +-------------------+
    |  Partial Sigma_1  |     |    |  Partial Sigma_2  |
    |  (only co-obs     |     |    |  (only co-obs     |
    |   pairs filled)   |     |    |   pairs filled)   |
    +---------+---------+     |    +---------+---------+
              |                |              |
              +--------+-------+--------------+
                       v
          +-------------------------+
          |  ACCUMULATE             |  Average each (i,j) entry
          |  element-wise across    |  over sessions where both
          |  all K sessions         |  i and j were observed
          +------------+------------+
                       v
          +-------------------------+
          |  ESTIMATE               |  W_hat = Sigma_{x+1,x} * Sigma_{x,x}^{-1}
          |  (one matrix multiply   |
          |   + pseudoinverse)      |
          +------------+------------+
                       v
          +-------------------------+
          |  ZERO DIAGONAL          |  W_hat_ii = 0  (no autapses)
          |  (biggest single        |  Removes autocorrelation
          |   improvement)          |  artifact (3-4x too large)
          +------------+------------+
                       v
          +-------------------------+
          |  GRANGER REFINEMENT     |  Projected gradient descent:
          |  Enforce: W_ij >= 0     |  - non-negative weights
          |           W_ij = 0      |  - zero non-causal edges
          |  where not causal       |  - preserve all true edges
          +------------+------------+
                       v
                  Final W_hat
           (r = 0.90 with true W)
```

---

## Key Files

| File | Lines | What it does |
|------|-------|-------------|
| `experiments/core.py` | 597 | **The brain.** All algorithms: network generation, CPG dynamics, covariance estimation, Granger refinement |
| `experiments/run_experiments.py` | 531 | **The lab.** Defines and runs E1-E7, each testing a specific hypothesis |
| `experiments/analysis.py` | 973 | **The artist.** Generates 9 of the 10 publication figures |
| `scripts/generate_all_figures.py` | 234 | **The orchestrator.** Calls analysis.py + generates fig8 (dynamics 9-panel) |
| `paper/main.tex` | 630 | **The paper.** NeurIPS preprint, 10 main pages + 3 appendix |
| `paper/references.bib` | 216 | 20 verified citations |
| `paper/math_walkthrough.md` | 215 | Educational companion — the full mathematical derivation story |
| `paper/poster.tex` | 231 | A1 conference poster |
| `paper/lightning_talk.md` | 59 | 3-minute talk script |
| `experiments/results/*.json` | 7 files | Raw data from all experiments |

---

## Tracing Through the System

Let's follow a single experiment from start to finish. Imagine you type:

```bash
uv run python experiments/run_experiments.py --experiment E4 --seed 42
```

### Step 1: Generate a random brain circuit

`core.py:202` — `random_network_topology(num_nodes=12, non_negative_weights=True, force_stable=True)`

This creates a random directed graph, like a tiny connectome:

```
Grow density until strongly connected -> draw Unif(0,1) weights -> scale so rho(W) <= 1
```

**Why strongly connected?** Real connectomes (C. elegans) have a giant strongly connected component — every neuron can influence every other through some path. We match that.

**Why non-negative weights?** Electron microscopy measures synapse *size* (contact area, vesicle count) — always positive. The *sign* of a connection (excitatory vs inhibitory) isn't directly observed. So we model W >= 0 and let the sign of the *activity* carry the inhibitory effect: a positive weight on a negative (hyperpolarized) state drives the target neuron down.

**Why rho(W) <= 1?** Spectral radius controls stability. With rho(W) <= 1 and tanh (1-Lipschitz), the map x -> W*phi(x) is non-expansive — states can't blow up. We set rho(W) = 1 - eps (edge of stability) for maximally rich dynamics.

### Step 2: Simulate 50 recording sessions

`core.py:244` — `create_network_data(...)` called 50 times via `create_multinetwork_dataset`

Each session:
1. **Pick which neurons to observe** (random 8 of 12 = 66%)
2. **Pick which neurons to stimulate** (random 4 of 12 = 33%)
3. **Pick which neurons have CPG** (4 of 12 = 33%)
4. **Run the dynamics** for T=900 timesteps (+ 300 warmup, discarded):

```python
# core.py:326 — THE dynamics equation
state = connection_weights @ nonlinearity(state) + total_input
```

where `total_input = extrinsic_drive + intrinsic_drive`:

```
                        +--------------------------------------+
                        |         total_input (b_t)             |
                        |                                       |
  extrinsic_drive ------+  sensor_mask * N(0, sigma^2)          |
  (you control this)    |  i.i.d. Gaussian per sensor node      |
                        |  Cov(b_stim, x) = 0  <-- KEY!        |
                        |                                       |
  intrinsic_drive ------+  cpg_mask * cpg_net(state)            |
  (the circuit's own    |  chaotic reservoir -> random MLP      |
   heartbeat)           |  Cov(b_CPG, x) != 0  <-- PROBLEM!    |
                        +--------------------------------------+
```

**The CPG is a chaotic reservoir** (`core.py:75`): a random sparse matrix M with gain g=1.3 (above edge of chaos), integrated via Euler steps: dx/dt = -x + M*tanh(x). This produces rich, unpredictable temporal signals — like the heartbeat that keeps the circuit alive when there's no external input.

**Why does the circuit need a heartbeat?** With rho(W) <= 1 and tanh, the autonomous system (no input) contracts to zero — the network dies. CPGs are biologically real: think cardiac pacemaker cells, respiratory rhythm generators, locomotion circuits.

### Step 3: Accumulate covariances across sessions

`core.py:410` — `estimate_connectivity_weights(num_nodes=12, multinet_dataset)`

This is the core algorithm. For each session k:

```python
# core.py:446-458
mask = measured_nodes_mask.reshape(-1, 1)     # which neurons we see
S = mask @ mask.T                              # co-measurement matrix
total_mask += S                                # count co-observations

cov_x   += (X[:-1].T @ X[:-1] / n) * S       # Sigma_{x,x}  (same-time)
cov_dtx += (X[1:].T  @ X[:-1] / n) * S       # Sigma_{x+1,x} (lagged)
```

Think of it like a jigsaw puzzle. Each session gives you some pieces (the covariance entries for co-observed pairs). After 50 sessions, you have the whole puzzle:

```python
# core.py:461-465 — Average over sessions
total_mask = np.clip(total_mask, a_min=1, a_max=None)  # avoid /0
cov_x   = cov_x   / total_mask
cov_dtx = cov_dtx / total_mask
```

### Step 4: The Estimator

```python
# core.py:467 — THE estimator (one line!)
approx_W = cov_dtx @ np.linalg.pinv(cov_x)
```

**The derivation in 30 seconds**: Starting from x_{t+1} = W*phi(x_t) + b_t, multiply both sides by x_t^T, take expectations, approximate phi(x) ~ x and Cov(b,x) ~ 0:

```
Sigma_{x+1,x} ~ W * Sigma_{x,x}    ->    W ~ Sigma_{x+1,x} * Sigma_{x,x}^{-1}
```

That's it. The rest of the paper is about understanding *when and why this works*, and *what the error looks like*.

### Step 5: Zero the diagonal

```python
# core.py:472
np.fill_diagonal(approx_W, 0)
```

**Why this matters so much**: The diagonal of W_hat measures autocorrelation — how much neuron i predicts *itself* one timestep later. This is dominated by the neuron's own momentum (persistence), which is huge (3-4x larger than off-diagonal entries) and has nothing to do with self-connectivity (we know W_ii = 0). Removing it is the single biggest improvement in the pipeline.

**Analogy**: Imagine trying to figure out who influences whom in a conversation. Each person's speech at time t+1 is most correlated with their *own* speech at time t (they tend to keep talking about the same topic). You need to remove that self-correlation before you can see the cross-influences.

### Step 6: Granger refinement

`core.py:529` — `projected_gradient_causal(cov_x, cov_dtx)`

This cleans up the estimate by enforcing biological constraints:

```
For 200 iterations:
  1. Gradient step: A -= lr * (A - A_init)     <-- pull toward data
  2. For 3 sub-iterations:
     a. W = A @ Sigma^{-1}                     <-- convert to weight space
     b. Clamp: W_ii=0, W_ij>=0, zero non-causal  <-- enforce biology
     c. A = backsolve(W, Sigma^{-1})            <-- convert back
```

**The Granger criterion** (`core.py:548`): Set W_ij = 0 wherever Sigma_{x,x}(i,j) > Sigma_{x+1,x}(i,j). Intuition: if the *contemporaneous* covariance between neurons i and j exceeds their *lagged* covariance, then j's past doesn't help predict i's future — so there's no causal connection.

Result: ~3% additional error reduction, **perfect recall** (all true edges preserved, zero missed).

---

## The Seven Experiments

| Exp | Question | What it varies | Key Finding |
|-----|----------|---------------|-------------|
| E1 | How does recovery scale? | N in {8,12,30}, T in {100,500,1000} | N=30, T=1000 -> 0.053 error (91% vs chance) |
| E2 | How much observation? | Measurement 33-100% | Plateaus above ~50% |
| E3 | Stimulation tradeoff? | sigma x measurement density | Zero stim fails; sigma~0.5 optimal |
| E4 | What does each step add? | Ablation: chance->estimate->Granger | 82% improvement, perfect recall |
| E5 | Robust to nonlinearity? | tanh, relu, identity, sigmoid | tanh best (bounds variance) |
| E6 | Does oracle win? | Oracle vs approx across sigma | No — approx always wins (1.4-4.4x) |
| E7 | How many sensors? | 1,2,4,8,12 stimulated neurons | 1 fails; >=33% suffices |

---

## The Error Decomposition (Why the "Wrong" Model Wins)

The full estimation error is:

```
W_hat - W = W(D - I)              +  Sigma_{b,x} * Sigma_{x,x}^{-1}
             E1: model mismatch       E2: CPG correlation
             (0.083)                   (0.271)
             1x                        3.3x  <-- DOMINANT
```

**E1 (model mismatch)**: The price of approximating phi(x) ~ x. The Stein-Price identity gives an exact formula: E1 = W(D-I) where D = diag(E[sech^2(x_i)]). For small state variance, 1-d_i ~ sigma_i^2.

**E2 (CPG correlation)**: The price of ignoring Cov(b_CPG, x). The stimulation is truly independent, but the CPG depends on state. This is 3.3x larger than E1.

**Why the oracle loses**: It must invert D*Sigma_{x,x} instead of Sigma_{x,x}. The D matrix compresses rows heterogeneously (high-variance neurons get compressed more), worsening the condition number:

```
kappa(D*Sigma) <= kappa(Sigma) * d_max/d_min
```

The linear estimator avoids this — it's biased but better-conditioned. Classic bias-variance tradeoff, a concrete James-Stein phenomenon.

---

## Five Key Insights

### 1. The "wrong" model wins
The oracle (which knows the true tanh) is 1.4-4.4x worse than the naive linear approximation. Don't bother characterizing the neuronal transfer function — the simpler model is provably better.

### 2. CPG correlation is the real bottleneck
E2 is 3.3x larger than E1. Future improvements should focus on modeling intrinsic dynamics, not refining the nonlinear model.

### 3. The control-estimation tradeoff is quantifiable
Zero stimulation fails (Sigma_{x,x} ill-conditioned). Too much overwhelms the signal. Sweet spot: sigma ~ 0.5-1.0, ~33% of neurons.

### 4. Diagonal zeroing is the unsung hero
One line of code (`np.fill_diagonal(approx_W, 0)`) matters more than 200 iterations of Granger refinement.

### 5. Partial observation has diminishing returns
Going 33% -> 50% coverage = huge improvement. Going 50% -> 100% = barely helps. You don't need full-circuit access.

---

## Summary

```
THE WHOLE PROJECT IN ONE DIAGRAM:

    Partial observations          Accumulate            Estimate
    +--------+ +--------+       covariances            connectivity
    |Sess 1  | |Sess 2  | ...   piece by piece    ->  W_hat = Sigma_1 * Sigma_0^{-1}
    |see 8   | |see 8   |       across 50              (one equation)
    |of 12   | |of 12   |       sessions
    +--------+ +--------+
                                                          |
                                                          v
    Three surprise findings:                    Zero diagonal
    1. Linear > Oracle (James-Stein)            (biggest win)
    2. CPG correlation >> model mismatch               |
    3. Sweet spot: sigma~0.5, 33% sensors              v
                                                 Granger refine
                                                 (non-neg, sparse)
                                                       |
                                                       v
                                                 Final W_hat
                                              r=0.90, 82% > chance
```

---

## How to Run

```bash
# Install
uv sync

# Run all experiments (~30 min)
uv run python experiments/run_experiments.py --experiment all --seed 42

# Generate all 10 figures
uv run python scripts/generate_all_figures.py

# Compile paper
cd paper && tectonic main.tex

# Compile poster
cd paper && tectonic poster.tex
```
