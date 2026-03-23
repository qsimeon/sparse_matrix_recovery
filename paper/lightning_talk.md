# Lightning Talk: Recovering Sparse Neural Connectivity from Partial Measurements
**3 minutes | Quilee Simeon, MIT**

---

## [Slide 1 — Problem] (0:00–0:40)

You want to map how neurons are wired — the connectivity matrix **W** — but you can never record every neuron at once. Different sessions give you different subsets. How do you stitch partial snapshots into a complete picture?

This is a real constraint in small-circuit neuroscience — *C. elegans*, larval zebrafish, organoids — where neuron counts are tractable but simultaneous full-circuit recording is not.

**Key tension:** You can stimulate neurons to help identify connections, but stimulation disrupts the intrinsic dynamics you care about. We call this the **control-estimation tradeoff**.

---

## [Slide 2 — Method] (0:40–1:20)

Our approach: **covariance accumulation across sessions**.

Whenever two neurons are co-observed in a session, their covariance contributes to estimating the corresponding entry of **W**. Across *K* = 50 sessions with overlapping subsets, we reconstruct the full covariance matrix, then estimate connectivity as:

> **Ŵ = Σ(x_{t+1}, x_t) · Σ(x_t, x_t)⁻¹**

A Granger-causality refinement step then enforces biological constraints — no self-connections, sparsity, non-negativity — via projected gradient descent.

Simple, closed-form, no deep learning required.

---

## [Slide 3 — Key Results] (1:20–2:20)

Three findings that matter for experimentalists:

**1. It works.** On synthetic networks (N = 8–30 neurons), we achieve **r = 0.91** correlation with true weights and **82% improvement over chance** using only 66% neuron coverage per session.

**2. The "wrong" model wins.** The linear approximation — which ignores the known tanh nonlinearity — **outperforms the oracle estimator** that uses the true nonlinearity at *every* stimulation level tested. Why? The linear covariance is better-conditioned. Using the exact nonlinearity amplifies noise during matrix inversion. This is a concrete James–Stein phenomenon: a biased estimator with lower variance beats an unbiased one. Practical implication: you don't need to characterize the neuronal transfer function.

**3. CPG correlation is the bottleneck.** Error decomposition shows that correlation from intrinsic central pattern generators is **3.4× larger** than model mismatch error. The path to better recovery runs through modeling autonomous dynamics — not through better nonlinear approximations.

---

## [Slide 4 — Practical Takeaway] (2:20–2:50)

For experimentalists designing recording protocols:

- **Stimulation:** Moderate intensity (σ ≈ 0.5–1.0) on ~33% of neurons. Zero stimulation fails; too much overwhelms the signal.
- **Measurement:** 50%+ neuron coverage per session hits diminishing returns. You don't need to see everything.
- **Model:** Use the linear estimator. It's simpler *and* better.

This defines a practical operating regime for connectome recovery from calcium imaging with partial observability.

---

## [Closing] (2:50–3:00)

Covariance accumulation turns the partial-observation problem from a limitation into a feature — each session is a new view of the same circuit. The code and all experiments are publicly available.

Thank you.
