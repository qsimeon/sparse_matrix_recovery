# Lightning Talk: Recovering Sparse Neural Connectivity from Partial Measurements
**3 minutes | Quilee Simeon, MIT**

---

## [Slide 1 — The Problem] (0:00–0:45)

Imagine you're studying a small brain circuit — 15 neurons. You want to know how they're wired: the full connectivity matrix **W**. But your microscope can only see about 10 of those 15 neurons at a time. Each day, you image a different subset.

How do you stitch these partial snapshots into a complete wiring diagram?

This is a real constraint in small-circuit neuroscience — *C. elegans*, larval zebrafish, organoids. And there's a deeper tension: you can *stimulate* neurons to help identify connections, but stimulation disrupts the intrinsic dynamics you care about.

---

## [Slide 2 — The Method] (0:45–1:20)

Our insight: **covariance accumulation**. Whenever two neurons are co-observed in a session, their covariance tells you something about the connection between them. Across 50 sessions with overlapping subsets, you piece together the full covariance matrix.

The estimator is one equation:

> **W-hat = Sigma(x_{t+1}, x_t) times Sigma(x_t, x_t) inverse**

Zero the diagonal — that's a modeling prior, not an optimization trick — then refine with biological constraints via projected gradient descent. Simple, closed-form, no deep learning.

---

## [Slide 3 — Three Surprising Findings] (1:20–2:20)

**First: it works.** On synthetic networks up to 30 neurons, we achieve **r = 0.96** correlation with true weights and **84% improvement** over chance using only 66% neuron coverage per session.

**Second — the "wrong" model wins.** We deliberately use a linear approximation, ignoring the known tanh nonlinearity. The oracle estimator that knows the true nonlinearity is *worse* — up to **4.5 times worse**. Why? The tanh compresses the covariance matrix heterogeneously, making the oracle's matrix inversion amplify noise. The linear version is biased but better-conditioned — a concrete James-Stein phenomenon. You don't need to characterize the neuronal transfer function.

**Third: we found the real bottleneck.** Error decomposition shows that correlation from intrinsic central pattern generators is **3.1 times larger** than model mismatch. The path to better recovery runs through modeling autonomous dynamics, not through better nonlinear approximations.

---

## [Slide 4 — What This Means] (2:20–2:50)

For experimentalists designing recording protocols:

- **Stimulation**: Moderate intensity on about a third of neurons. Zero stimulation fails; too much overwhelms the signal.
- **Coverage**: 50%+ neurons per session hits diminishing returns.
- **Model**: Use the linear estimator. It's simpler *and* better.

This defines a practical operating regime for connectome recovery from calcium imaging with partial observability.

---

## [Closing] (2:50–3:00)

Covariance accumulation turns partial observation from a limitation into a feature — each session is a new view of the same circuit.

Thank you. Paper and code at github.com/qsimeon/sparse\_matrix\_recovery.
