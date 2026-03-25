# Mathematical Walkthrough: Sparse Connectivity Recovery

> A guide to the core ideas, equations, and intuitions behind the paper.
> Intended as a companion for presentations and for rebuilding your own mental model.

---

## The Big Picture

You're a neuroscientist studying a small brain circuit (say, 15 neurons in *C. elegans*). You want to know the connectivity matrix W: how strongly does neuron j influence neuron i?

**The catch**: Your microscope can only see ~10 of the 15 neurons at a time. Each session, you image a different subset. Some days you see neurons {0,2,4,6,8,10,12,14}, other days {1,3,5,7,9,11,13}.

**The insight**: Whenever neurons i and j are simultaneously visible, you can compute their covariance. Over many sessions, you eventually observe every *pair* at least once, accumulating a complete N x N covariance matrix piece by piece.

---

## Step 1: The Forward Model

The dynamics of the neural circuit are:

```
x_{t+1} = W phi(x_t) + b_t
```

- **x_t** is the state of all N neurons at time t
- **W** is the N x N connectivity matrix (what we want to find)
- **phi** is a nonlinearity (tanh) applied element-wise
- **b_t** is external input (stimulation + CPG drive)

**Why phi = tanh?** Neurons saturate -- they can't fire infinitely fast. tanh maps (-inf, inf) -> (-1, 1), bounding the state. This prevents blow-up AND provides the implicit regularization that makes the oracle estimator lose (more on this in Step 3).

**Why rho(W) <= 1?** The spectral radius controls whether dynamics explode. With rho(W) <= 1 and 1-Lipschitz phi, the autonomous dynamics (b_t = 0) contract to zero -- the network "dies" without input. This motivates the CPG.

**What is the CPG?** A Central Pattern Generator -- an internal oscillatory drive that keeps the network alive, like a cardiac pacemaker. In our model, it's a chaotic reservoir network that produces rich temporal signals. Critically, the CPG output depends on the current state: cpg(x_t), so Cov(b_CPG, x_t) != 0.

---

## Step 2: The Estimator Derivation

Starting from x_{t+1} = W phi(x_t) + b_t, multiply both sides by x_t^T and take expectations:

```
E[x_{t+1} x_t^T] = W E[phi(x_t) x_t^T] + E[b_t x_t^T]
```

In covariance notation:

```
Sigma_{x+1,x} = W Sigma_{phi(x),x} + Sigma_{b,x}
```

Now make two approximations:

1. **Linear approximation**: phi(x) ~ x, so Sigma_{phi(x),x} ~ Sigma_{x,x}
2. **Independence**: The extrinsic stimulation is i.i.d. and independent of state, so Cov(b_stim, x) = 0

This gives:

```
Sigma_{x+1,x} ~ W Sigma_{x,x} + Sigma_{CPG,x}
```

Ignoring the CPG term (which we can't easily compute):

> **W_hat = Sigma_{x+1,x} Sigma_{x,x}^{-1}**

That's the entire estimator. One line of code: `approx_W = cov_dtx @ np.linalg.pinv(cov_x)`.

### Accumulation across sessions

For each pair (i,j), we only compute covariances from sessions where BOTH neurons i and j are observed. The accumulated covariance averages these element-wise:

```
Sigma_hat_ij = (sum over sessions k where i,j both measured) Sigma_ij^(k) / count_ij
```

**When is W recoverable?** If and only if every pair (i,j) is co-observed in at least one session. For random measurement with probability p per neuron, a coupon-collector argument gives: K >= log(N^2 / delta) / p^2 sessions suffice with probability >= 1 - delta.

---

## Step 3: Why the "Wrong" Approximation Beats the "Right" One

The **oracle estimator** uses the true phi:

```
W_oracle = (Sigma_{x+1,x} - Sigma_{b,x}) Sigma_{phi(x),x}^{-1}
```

With infinite data, this recovers W exactly. But with finite data, it's *worse*. This is the paper's most surprising result.

### The Stein-Price identity explains why

For Gaussian x with phi = tanh:

```
E[tanh(x_i) x_j] = Sigma_ij * E[sech^2(x_i)]
```

Define D = diag(E[sech^2(x_i)]) with 0 < d_i < 1. Then:

```
Sigma_{phi(x),x} = D Sigma_{x,x}
```

The oracle must invert D Sigma_{x,x} instead of just Sigma_{x,x}. The D matrix *compresses* each row by a factor d_i < 1. If some neurons have high variance (d_i ~ 0, tanh saturates) and others low variance (d_i ~ 1, tanh is nearly linear), this compression is *heterogeneous*:

```
kappa(D Sigma) <= kappa(Sigma) * d_max / d_min
```

When d_max/d_min is large, the oracle's inversion amplifies noise much more than the approximation's.

### The bias-variance tradeoff

This is a concrete instance of **James-Stein shrinkage**: a biased estimator with lower variance can achieve better total risk than an unbiased one with high variance. The linear approximation introduces bias (it doesn't know about tanh), but it uses a better-conditioned matrix, reducing variance. The total error is lower.

**Data confirms**: At every tested stimulation level, the oracle is 1.4-4.4x worse. The gap is largest at sigma=0.1 (4.4x) because that's when state variances are most heterogeneous.

---

## Step 4: The Error Decomposition

The full estimation error (Eq. 8 in the paper) is:

```
W_hat - W = W(D - I)              +  Sigma_{b,x} Sigma_{x,x}^{-1}
             E1: model mismatch       E2: CPG correlation
```

**E1 (model mismatch)**: The price of using Sigma_{x,x} instead of Sigma_{phi(x),x}. Via Stein-Price: E1 = W(D-I), where D-I has diagonal entries -(1-d_i). For small variance, 1-d_i ~ sigma_i^2, so the error scales quadratically.

**E2 (CPG correlation)**: The price of assuming Cov(b,x) = 0. The extrinsic stimulation IS independent. But the CPG depends on state, so Cov(cpg_t, x_t) != 0.

**Key finding**: E1 = 0.073, E2 = 0.229. **E2 is 3.1x larger**. The CPG correlation is the dominant bottleneck -- not the linear approximation. Future improvements should focus on modeling CPG effects.

---

## Step 5: Diagonal Zeroing (the Biggest Single Step)

Before any refinement, we set W_hat_ii = 0 for all i. This seems minor but is the single most impactful processing step.

**Why the diagonal is problematic**: The raw (Sigma_{x+1,x} Sigma_{x,x}^{-1})_ii measures the autocorrelation of neuron i -- how x_i(t+1) correlates with x_i(t). This is dominated by the neuron's own persistence (momentum), not self-connectivity. The diagonal is 3-4x larger than off-diagonal entries.

**Why we can zero it**: We KNOW W_ii = 0 (no autapses in C. elegans and many circuits). This is a structural prior, not something learned from data. Removing the autocorrelation-dominated diagonal is a huge win.

---

## Step 6: Granger-Causality Refinement

After diagonal zeroing, W_hat may still have:
- Negative entries (violating non-negative weights)
- Spurious small connections (noise artifacts)

The Granger refinement solves:

```
min_A ||A - Sigma_{x+1,x}||^2   subject to   W = A Sigma_{x,x}^{-1} in C
```

where C enforces:
1. **No self-connections**: W_ii = 0
2. **Non-negativity**: W_ij >= 0
3. **Granger criterion**: W_ij = 0 where Sigma_{x,x}(i,j) > Sigma_{x+1,x}(i,j)

The Granger criterion says: if the contemporaneous covariance exceeds the lagged covariance for pair (i,j), then j's past doesn't help predict i -- so W_ij should be zero.

The algorithm alternates between:
1. Gradient step toward the unconstrained optimum (data-fidelity)
2. Projection onto the constraint set (biology)

Result: ~3% additional improvement, **perfect recall** (all true edges preserved, median = 1.0).

---

## Step 7: The Control-Estimation Tradeoff

Perhaps the most practical finding for experimentalists.

**Zero stimulation fails** at high measurement density because the CPG alone doesn't excite all network modes -- Sigma_{x,x} becomes ill-conditioned (some eigenvalues near zero).

**Too much stimulation fails** because noise overwhelms the signal in the covariance.

**The sweet spot**: sigma ~ 0.5--1.0, applied to ~33% of neurons. This provides enough independent noise directions to excite all network modes while not drowning out the connectivity signal.

**Stimulation coverage matters independently**: Stimulation gain controls the *magnitude* of input covariance. Stimulation fraction controls its *rank* (number of independent noise directions). One stimulated node is insufficient; beyond 33% coverage, performance plateaus.

---

## Summary: The Mathematical Story

```
x_{t+1} = W phi(x_t) + b_t                     [dynamics]
    |
    v
Sigma_{x+1,x} = W Sigma_{x,x} + small terms    [covariance identity]
    |
    v
W_hat = Sigma_{x+1,x} Sigma_{x,x}^{-1}         [estimator]
    |
    v
zero diagonal (no autapses)                      [structural prior]
    |
    v
Granger refinement (non-neg, sparse)             [biological constraints]
    |
    v
Error = W(D-I)  +  Sigma_{b,x} Sigma_{x,x}^{-1}
        ^small      ^3.1x larger                  [CPG dominates]
```

**Three key takeaways**:
1. The "wrong" linear approximation is actually *better* than the oracle (implicit regularization via James-Stein shrinkage)
2. CPG correlation, not model mismatch, is the dominant error source (3.1x larger)
3. Moderate stimulation (~sigma=0.5-1.0) of a modest subset (~33%) of neurons defines the practical operating regime
