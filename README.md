# Recovering Sparse Neural Connectivity from Partial Measurements

A covariance-based method for estimating the weight matrix of a recurrent neural network from sparse, partial measurements across multiple recording sessions, with Granger-causality refinement and heteroskedastic error analysis.

**Paper**: `paper/main.tex` (NeurIPS preprint format, 21 pages)
**Code**: https://github.com/qsimeon/sparse_matrix_recovery

## Quick Start

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Run all 8 experiments
uv run python experiments/run_experiments.py --experiment all --seed 42

# Generate all 10 paper figures
uv run python scripts/generate_all_figures.py

# Run the primary walkthrough notebook
uv run jupyter notebook notebooks/qsimeon_SparseMatrixRecovery.ipynb
```

## Method

Given a network of N neurons with unknown connectivity W, we observe different subsets of neurons across K recording sessions. The key insight: **pairwise covariance statistics can be accumulated across sessions** where different neurons are co-observed.

```
x_{t+1} = W φ(x_t) + b_t                       # Recurrent dynamics (Eq. 1)
Ŵ = Σ_{x_{t+1},x_t} Σ_{x_t,x_t}^{-1}          # Covariance estimator (Eq. 6)
```

Then: zero diagonal (no autapses) → non-negativity → Granger-causality refinement → recovered W.

**Key findings:**
- The linear approximation beats the oracle with known nonlinearity (James–Stein effect) at all tested regimes
- CPG–state correlation (E₂) dominates model mismatch (E₁) by ~2× — the main bottleneck
- Error is heteroskedastic: |Ŵᵢⱼ − Wᵢⱼ| ∝ Wᵢⱼ (slope ≈ 1 − d̄)
- 31% improvement over an independent draw from the same generative prior

## Experiments

| Exp | Question | Key Finding |
|-----|----------|-------------|
| E1 | How does recovery scale with N and T? | N=300, T=1000 → 0.014 error (97.5% over chance) |
| E2 | What does each pipeline step add? | 31% over spectral prior; Granger: precision 0.30→0.40, recall 0.97 |
| E3 | What stimulation protocol is optimal? | σ≈0.5 at full measurement; interaction effect |
| E4 | How much measurement coverage is needed? | Plateaus above ~50% |
| E5 | How robust to nonlinearity mismatch? | tanh best (bounds state variance, improves conditioning) |
| E6 | Does the oracle with known φ win? | Never — approximation wins 1.45–2.72× at all σ |
| E7 | How many neurons to stimulate? | ≥33% suffices (rank condition); 0% fails |
| E8 | Robust to observation noise? | σ_ε=0.1: +1.5% error; σ_ε=0.5: +32% error |

## Project Structure

```
experiments/
  core.py              # Network generation, CPG dynamics, estimation, Granger refinement
  run_experiments.py   # CLI runner for E1-E8
  run_single_rep.py    # Atomic SLURM-compatible single-repetition runner
  analysis.py          # Publication figure generation (all 10 figures)
  aggregate_results.py # Combine per-rep JSONs from cluster runs
  results/             # Experiment data (E1-E8 JSON files)
  sweep_config.yaml    # WandB sweep configuration
paper/
  main.tex             # LaTeX paper (21 pages, NeurIPS preprint format)
  references.bib       # 23 references
  figures/             # 10 paper figures (PDF)
  poster.tex           # 36"×24" conference poster
  presentation.tex     # SDSCon 2026 lightning talk (8 slides)
  math_walkthrough.md  # Mathematical companion document
notebooks/
  qsimeon_SparseMatrixRecovery.ipynb  # Primary paper walkthrough (23 cells)
  complete_analysis.ipynb             # Teaching notebook with ablation and oracle analysis
  explore_dynamics.ipynb              # CPG dynamics + abs vs ReLU comparison
scripts/
  generate_all_figures.py  # Regenerate all 10 figures from experiment JSONs
  verify_citations.py      # Check citation integrity (23/23)
  launch_experiments.sh    # SLURM launcher for E2-E7 (engaging cluster)
  launch_E1_scaling.sh     # SLURM launcher for E1 (90 tasks: 3N×3T×10 reps)
  launch_wandb_sweep.sh    # WandB sweep agent launcher
  launch_sweep.sh          # Mega sweep (3^5 grid, 243 SLURM tasks)
```

## Citation

**Preprint**: https://arxiv.org/abs/2603.18497

```bibtex
@misc{simeon2026recoveringsparseneuralconnectivity,
  title={Recovering Sparse Neural Connectivity from Partial Measurements:
         A Covariance-Based Approach with Granger-Causality Refinement},
  author={Quilee Simeon},
  year={2026},
  eprint={2603.18497},
  archivePrefix={arXiv},
  primaryClass={q-bio.QM},
  url={https://arxiv.org/abs/2603.18497},
}
```

## Author

Quilee Simeon — Massachusetts Institute of Technology — qsimeon@mit.edu
