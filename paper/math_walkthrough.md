# Mathematical Walkthrough: Sparse Connectivity Recovery

> A complete guide to the core ideas, equations, and intuitions behind the paper.
> Intended as a companion for presentations and for rebuilding your mental model
> from the ground up. Every step explains the *why*, not just the *what*.

---

## 0. The Big Picture in One Paragraph

You're studying a neural circuit of N neurons. You want to recover the connectivity
matrix W (who connects to whom and how strongly). But your microscope can only see
~66% of the neurons at a time, and each recording session images a different random
subset. The key insight: whenever two neurons are simultaneously visible, their
covariance tells you something about the connection between them. Over many sessions,
you accumulate enough pairwise statistics to estimate the full W. The estimator is
one equation, uses a deliberate "wrong" linear approximation that turns out to be
*better* than the oracle, and the dominant error comes not from this approximation
but from intrinsic oscillatory dynamics (CPGs) that correlate with the state.

---

## 1. The Dynamical Model

### The dynamics equation

The neural circuit evolves in discrete time:

```
x_{t+1} = W φ(x_t) + b_t                                    [Eq. 1]
```

- **x_t ∈ R^N**: state of all N neurons at time t (e.g., calcium fluorescence)
- **W ∈ R^{N×N}**: connectivity matrix — W_ij is the strength of the connection from neuron j to neuron i. This is what we want to recover.
- **φ**: element-wise nonlinearity (our default is tanh)
- **b_t ∈ R^N**: total external input = extrinsic stimulation + intrinsic CPG drive

### Why φ = tanh?

Neurons saturate — they can't fire infinitely fast. tanh maps R → (-1, 1), bounding
the state and preventing blow-up. Crucially:
- tanh is 1-Lipschitz: |tanh'(x)| ≤ 1 for all x
- This means W's spectral radius controls stability
- tanh is centered at 0 (unlike sigmoid), so zero-mean states are possible

### Why ρ(W) ≤ 1?

The spectral radius ρ(W) controls whether dynamics explode. With ρ(W) ≤ 1 and
1-Lipschitz φ, the autonomous dynamics (b_t = 0) are contractive — the network
"dies" without input. This is realistic: real circuits need ongoing drive to
maintain activity. It also motivates the CPG.

### Structural priors on W

We impose three priors, applied to ALL estimates (not method-specific):

1. **No autapses**: W_ii = 0. In C. elegans and many circuits, neurons don't
   synapse onto themselves. The raw diagonal entries are dominated by
   autocorrelation (how x_i(t+1) correlates with x_i(t) through the neuron's
   own persistence), not self-connectivity.

2. **Non-negative weights**: W_ij ≥ 0. EM connectomics measures synapse count
   and size but not sign. Inhibitory effects arise from negative *activations*
   propagated through non-negative weights: W φ(x) can have negative entries
   even when W ≥ 0 and φ(x) has negative entries (tanh outputs are in (-1,1)).
   This is an explicit modeling choice — results apply to non-negative networks.

3. **Strong connectivity**: The directed graph of W must be strongly connected
   (every neuron reachable from every other). Otherwise, isolated components
   receive no stimulation signal and are unidentifiable.

### What is the CPG?

A Central Pattern Generator — an internal oscillatory drive that keeps the network
alive, like a cardiac pacemaker. In our model, it's a chaotic reservoir network
(Sussillo-style, gain g=1.3 at the edge of chaos) fed through a frozen random deep
network with circular input permutation, producing rich, nonstationary, state-dependent
spatiotemporal signals.

**Critically**: The CPG drive depends on the current state: b_CPG = f(x_t), so
Cov(b_CPG, x_t) ≠ 0. This is the dominant source of estimation error (see Step 5).

The CPG is a property of the circuit topology — the same CPG drives all recording
sessions for a given network, with each session starting from a fresh time counter.

---

## 2. The Observation Model

Each session k observes only a subset of neurons:

```
Session k observes M_k ⊂ {1, ..., N},  |M_k| = m
Session k stimulates S_k ⊂ {1, ..., N},  |S_k| = s
```

Measurement masks are random (different subset each session). The key statistical
quantity: **pairwise co-observation**. Neurons i and j are co-observed in session k
if both i, j ∈ M_k. Only then can we estimate their covariance from that session.

### With observation noise

If measurements are noisy: y_t = x_t + ε_t, where ε_t ~ N(0, σ_ε² I), then:

```
Cov(y_t, y_t) = Cov(x_t, x_t) + σ_ε² I     (noise inflates diagonal)
Cov(y_{t+1}, y_t) = Cov(x_{t+1}, x_t)       (cross-time noise independent)
```

This means noise acts as **implicit ridge regularization** — the estimator becomes:

```
Ŵ_noisy = Σ_{x+1,x} (Σ_{x,x} + σ_ε² I)^{-1}
```

which is algebraically identical to ridge regression with λ = σ_ε². Small noise
*helps* by stabilizing the inversion.

---

## 3. The Estimator Derivation

### Step 1: Covariance identity

Starting from x_{t+1} = W φ(x_t) + b_t, multiply both sides by x_t^T and take
expectations:

```
E[x_{t+1} x_t^T] = W E[φ(x_t) x_t^T] + E[b_t x_t^T]
```

In covariance notation:

```
Σ_{x+1,x} = W Σ_{φ(x),x} + Σ_{b,x}                         [Eq. 2]
```

This is exact — no approximations yet.

### Step 2: Two approximations

**Linear approximation**: φ(x) ≈ x, so Σ_{φ(x),x} ≈ Σ_{x,x}

Why is this reasonable? If neuron states are small (|x_i| << 1), then tanh(x) ≈ x.
Even when this isn't true, the approximation introduces a *structured* bias that
turns out to be beneficial (see Step 4).

**Independence approximation**: The extrinsic stimulation b_stim is i.i.d. and
independent of state, so Cov(b_stim, x) = 0. But the CPG drive depends on state,
so Cov(b_CPG, x) ≠ 0. We ignore this term — it becomes the E2 error.

### Step 3: The estimator

Combining both approximations:

```
Σ_{x+1,x} ≈ W Σ_{x,x}
```

Solving for W:

```
Ŵ = Σ_{x+1,x} Σ_{x,x}^{-1}                                  [Eq. 6]
```

That's the entire estimator. One line of code: `approx_W = cov_dtx @ pinv(cov_x)`.

### Step 4: Accumulation across sessions

For each pair (i,j), we compute covariances only from sessions where BOTH neurons
are observed. The accumulated covariance averages element-wise:

```
Σ̂_ij = (1/n_ij) Σ_{k: i,j ∈ M_k} Σ̂_ij^(k)
```

where n_ij counts how many sessions co-observed the pair.

If a pair is never co-observed (n_ij = 0), its covariance defaults to 0
(independence assumption) — a practical choice for handling partial coverage.

### Post-processing

After computing Ŵ:
1. Zero the diagonal (no autapses)
2. Clamp negative entries to 0 (non-negativity prior)
3. Optionally: Granger-causality refinement (see Step 7)

---

## 4. Why the "Wrong" Approximation Beats the "Right" One

This is the paper's most surprising result.

### The oracle estimator

The **oracle** knows the true φ = tanh and can compute:

```
Ŵ_oracle = (Σ_{x+1,x} - Σ_{b,x}) Σ_{φ(x),x}^{-1}
```

With infinite data, this recovers W exactly. But with finite data, it's *worse*.

### The Stein-Price identity explains why

For Gaussian x with φ = tanh, a result due to Price (1958) gives:

```
E[tanh(x_i) · x_j] = Σ_ij · E[sech²(x_i)]
```

Define D = diag(E[sech²(x_i)]) with 0 < d_i < 1. Then:

```
Σ_{φ(x),x} = D Σ_{x,x}
```

The oracle must invert D Σ_{x,x} instead of just Σ_{x,x}. The D matrix *compresses*
each row by a factor d_i < 1.

### The condition number argument

```
κ(D Σ) ≤ κ(Σ) × d_max / d_min
```

When some neurons have high variance (d_i → 0, tanh saturates) and others low
variance (d_i → 1, tanh is linear), d_max/d_min is large. The oracle's inversion
amplifies noise much more than the approximation's.

### The bias-variance tradeoff

This is a concrete instance of **James-Stein shrinkage**: a biased estimator with
lower variance can achieve better total mean squared error than an unbiased one with
high variance. The linear approximation:

- Introduces bias: it doesn't account for the tanh compression
- Reduces variance: it uses the better-conditioned Σ_{x,x} instead of D Σ_{x,x}
- Net effect: lower total error at every tested stimulation level (1.3-5× better)

**Practical implication**: You do NOT need to characterize the neuronal nonlinearity.
The simpler model is literally better.

---

## 5. The Error Decomposition

The full estimation error (from Eq. 2 with the linear approximation) is:

```
Ŵ - W = W(D - I)              +  Σ_{b,x} Σ_{x,x}^{-1}
         ─────────                 ─────────────────────
         E1: model mismatch       E2: CPG correlation          [Eq. 8]
```

### E1: Model mismatch (0.073)

The price of using Σ_{x,x} instead of Σ_{φ(x),x}. Via Stein-Price:
E1 = W(D-I), where D-I has diagonal entries -(1-d_i).

Key property: **E1 is proportional to W**. Large weights have larger absolute error.
This is heteroscedastic bias — the error is correlated with the covariate. If you
look at the error heatmap alongside the true W heatmap, they have the same structure.
This suggests weighted least squares could improve estimation by downweighting
entries where W is large.

For small variance: 1 - d_i ≈ σ_i², so E1 scales quadratically with state variance.

### E2: CPG correlation (0.229 — 3.1× larger!)

The price of assuming Cov(b, x) = 0. The extrinsic stimulation IS independent.
But the CPG depends on state, so Cov(b_CPG, x) ≠ 0.

**This is the dominant bottleneck.** E2 is 3.1× larger than E1. The path to better
recovery runs through modeling autonomous dynamics, not through better nonlinear
approximations.

### Why E2 dominates

The CPG is a chaotic, state-dependent signal that creates structured correlation
between the input and the state. This correlation biases the covariance estimate
systematically. The approximation error (E1) is relatively small because:
- For moderate-variance states, tanh ≈ x is a good approximation
- The D matrix is close to I when states aren't saturated

---

## 6. Diagonal Zeroing — The Biggest Single Step

Before any refinement, we set Ŵ_ii = 0 for all i.

**Why the diagonal is problematic**: The raw (Σ_{x+1,x} Σ_{x,x}^{-1})_ii measures
the autocorrelation of neuron i — how x_i(t+1) correlates with x_i(t). This is
dominated by the neuron's own persistence (temporal smoothness), not self-connectivity.
The diagonal is 3-4× larger than off-diagonal entries.

**Why we can zero it**: We KNOW W_ii = 0 (no autapses). This is a structural prior
from biology, not something learned from data.

---

## 7. Granger-Causality Refinement

After diagonal zeroing, Ŵ may still have spurious small connections from noise and
CPG correlations.

### The Granger criterion

For each pair (i,j), compare:
- **Contemporaneous covariance**: Cov(x_i(t), x_j(t)) — how correlated are i and j right now?
- **Lagged covariance**: Cov(x_i(t+1), x_j(t)) — does j's current state predict i's future?

If the contemporaneous covariance EXCEEDS the lagged covariance, then j's "influence"
on i is decaying over time — suggesting no direct causal connection j → i. So we
force W_ij = 0.

This is inspired by Granger's (1969) core idea: X Granger-causes Y if past X helps
predict future Y beyond past Y alone. Our covariance version applies this to the
accumulated statistics.

### The optimization

Enforce zeros via projected gradient descent:

```
min_A ||A - Â_init||²   subject to   W = A Σ_{x,x}^{-1} satisfying:
  (i)   W_ii = 0                      [no autapses]
  (ii)  W_ij ≥ 0                      [non-negativity]
  (iii) W_ij = 0 where Σ_x(i,j) > Σ_{x+1,x}(i,j)   [Granger zeros]
```

Algorithm: alternate between gradient step (pull toward data) and projection
(enforce constraints via clamping + ridge backsolve).

### What Granger achieves

- **Perfect recall** (median 1.0): every true edge is preserved
- **Modest precision improvement**: some spurious edges are removed
- The remaining false positives are from CPG-induced correlations that
  create genuine lagged covariance (they look causal even though they aren't)

---

## 8. The Control-Estimation Tradeoff

Perhaps the most practical finding for experimentalists.

### Zero stimulation fails

Without extrinsic input, the only drive is the CPG. The CPG excites a
low-dimensional subspace of state space → Σ_{x,x} becomes ill-conditioned
(some eigenvalues near zero) → the inversion amplifies noise catastrophically.

### Too much stimulation fails

Excessive noise overwhelms the connectivity signal in the covariance. The
signal-to-noise ratio in Σ_{x+1,x} degrades.

### The sweet spot

σ_stim ≈ 0.5–1.0, applied to ~33% of neurons. This provides:
- Enough independent noise directions to excite all network modes
- Low enough noise to preserve the connectivity signal

**Stimulation coverage matters independently**: The gain controls the
*magnitude* of input covariance. The fraction of stimulated neurons controls
its *rank*. One stimulated neuron provides one noise direction; beyond ~33%
coverage, performance plateaus.

---

## 9. Sampling Sufficiency: When is K Enough?

### Pair coverage (coupon collector)

With N neurons and m = ⌈2N/3⌉ measured per session, the probability that a
specific pair (i,j) is co-observed in a single session is:

```
P(pair) = m(m-1) / (N(N-1))  ≈  4/9  ≈  0.44
```

The probability a pair is NEVER observed in K sessions:

```
P(missed) = (1 - P(pair))^K
```

For K=50: P(missed) ≈ 10^{-13}. Expected unobserved pairs ≈ 0 even at N=1074.

**Formal bound** (union bound): K ≥ log(N²/δ) / P(pair) sessions suffice for
all-pairs coverage with probability ≥ 1 - δ. For δ = 0.001 and N = 300:
K_min ≈ 30 sessions.

**Bottom line**: K=50 provides overwhelming pair coverage at all tested N.

### Estimation quality (the real bottleneck)

Coverage says every pair is *seen*. But how well is each covariance entry *estimated*?

Each pair is observed in ~K × P(pair) ≈ 22 sessions, each with T timesteps,
giving ~22,000 effective samples per covariance entry. This is plenty for each
individual entry.

But the estimator inverts the full N×N covariance matrix. The degrees-of-freedom
ratio matters:

```
DOF ratio = (K × T) / N²
```

| N | DOF ratio | Quality |
|---|-----------|---------|
| 15 | 222 | Excellent — massively overdetermined |
| 159 | 1.98 | Borderline — just barely sufficient |
| 300 | 0.56 | Underdetermined — pinv is unreliable |

When DOF < 1, the sample covariance matrix is rank-deficient relative to the true
dimensionality. The pseudoinverse amplifies estimation noise in the null space.
This explains the non-monotonic behavior and high variance at large N in E1.

**The non-negativity prior helps**: It constrains ~N² parameters to be ≥ 0,
effectively halving the parameter space. But this implicit regularization is
insufficient when DOF << 1.

---

## 10. Noise as Implicit Regularization (E8)

When observation noise σ_ε > 0 is present:

```
Ŵ = Σ_{x+1,x} (Σ_{x,x} + σ_ε² I)^{-1}
```

This is algebraically identical to ridge regression with λ = σ_ε².

- For well-conditioned Σ (small N): noise hurts (adds bias, no benefit)
- For ill-conditioned Σ (large N): noise helps (regularizes, prevents blow-up)
- There should be an optimal noise level that balances bias and variance

This is counterintuitive: measurement imprecision can *improve* connectivity
recovery by stabilizing the matrix inversion.

---

## 11. Edge Detection and Sparsity

### The threshold problem

The raw estimate Ŵ has no exact zeros — every entry is some nonzero value.
To identify which connections exist, we must threshold.

**Sparsity-calibrated threshold**: If the true network has edge density d
(fraction of nonzero entries), threshold at the (1-d) percentile of |Ŵ|.
This predicts d × N² entries as edges, matching the true sparsity level.

**Effect**: With the correct threshold, precision and recall are both ~0.83
(balanced). With the naive 50th percentile, precision drops to ~0.34 while
recall inflates to ~0.90 — because you're over-predicting edges.

### Granger threshold

The Granger-refined estimate has explicit zeros from the non-causality criterion.
Any nonzero entry is called an edge. This gives perfect recall (1.0) but modest
precision — some spurious correlations survive the Granger test because CPG
dynamics create genuine lagged covariance.

---

## Summary: The Mathematical Story in One Diagram

```
x_{t+1} = W φ(x_t) + b_t                     [dynamics]
    |
    v
Σ_{x+1,x} = W Σ_{x,x} + small terms          [covariance identity]
    |
    v  (linear approx φ(x)≈x, ignore CPG)
Ŵ = Σ_{x+1,x} Σ_{x,x}^{-1}                   [estimator]
    |
    v
zero diagonal (no autapses)                     [structural prior]
    |
    v
Granger refinement (non-neg, sparse)            [biological constraints]
    |
    v
Error = W(D-I)  +  Σ_{b,x} Σ_{x,x}^{-1}
        ^small      ^3.1× larger                [CPG dominates]
```

### Five key takeaways

1. **The estimator is one equation** — simple, closed-form, no deep learning
2. **The "wrong" linear approximation beats the oracle** — James-Stein shrinkage in action
3. **CPG correlation, not model mismatch, is the bottleneck** — 3.1× larger error
4. **Moderate stimulation of ~33% of neurons defines the practical operating regime**
5. **K=50 sessions provides overwhelming pair coverage, but estimation quality degrades at large N due to the DOF ratio** — the curse of dimensionality, not coverage, limits scaling
