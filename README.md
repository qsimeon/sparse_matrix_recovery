# Recovering Sparse Neural Connectivity from Partial Measurements

A covariance-based method for estimating the weight matrix of a recurrent neural network from sparse, partial measurements across multiple recording sessions, with Granger-causality refinement.

**Paper**: `paper/main.tex` ([Overleaf-compatible](https://www.overleaf.com/), NeurIPS preprint format)

## Quick Start

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Run all 7 experiments
uv run python experiments/run_experiments.py --experiment all --seed 42

# Generate all 10 paper figures
uv run python scripts/generate_all_figures.py

# Run the primary walkthrough notebook
uv run jupyter notebook notebooks/qsimeon_SparseMatrixRecovery.ipynb
```

## Method

Given a network of N neurons with unknown connectivity W, we observe different subsets of neurons across K recording sessions. The key insight: **pairwise covariance statistics can be accumulated across sessions** where different neurons are co-observed.

```
x_{t+1} = W φ(x_t) + b_t        # Recurrent dynamics (Eq. 1)
Ŵ = Σ_{x_{t+1},x_t} Σ_{x_t,x_t}^{-1}   # Covariance estimator (Eq. 6)
```

Then: zero diagonal (no autapses) → Granger-causality refinement → recovered W.

## Experiments

| Exp | Question | Key Finding |
|-----|----------|-------------|
| E1 | How does recovery scale with N and T? | N=30, T=1000 → 0.053 error (91% vs chance) |
| E2 | What does each pipeline step add? | Diagonal zeroing most impactful; Granger gives perfect recall |
| E3 | What stimulation protocol is optimal? | Depends on measurement density |
| E4 | How much measurement coverage is needed? | Plateaus above ~50% |
| E5 | How robust to nonlinearity mismatch? | tanh best (bounds state variance) |
| E6 | Does the oracle with known φ win? | No — approximate always wins (implicit regularization) |
| E7 | How many neurons to stimulate? | ≥33% suffices; 0% fails |

## Project Structure

```
experiments/
  core.py              # Network generation, dynamics, estimation, Granger refinement
  run_experiments.py   # CLI runner for E1-E7
  analysis.py          # Publication figure generation
  results/             # Experiment data (JSON)
paper/
  main.tex             # LaTeX paper (~630 lines, NeurIPS preprint format)
  references.bib       # 20 references
  figures/             # 10 paper figures (PDF)
  poster.tex           # A1 conference poster
  lightning_talk.md    # 3-minute talk script
notebooks/
  qsimeon_SparseMatrixRecovery.ipynb   # Primary walkthrough (23 cells)
  complete_analysis.ipynb               # Teaching notebook with ablation
  explore_dynamics.ipynb                # CPG dynamics exploration
scripts/
  generate_all_figures.py   # Regenerate all 10 figures
  verify_citations.py       # Check citation integrity
tools/
  openai_math.py        # GPT-5.4 math verification (via OpenRouter)
  gemini_research.py    # Gemini literature review
```

## Citation

```bibtex
@article{simeon2026sparse,
  title={Recovering Sparse Neural Connectivity from Partial Measurements:
         A Covariance-Based Approach with Granger-Causality Refinement},
  author={Simeon, Quilee},
  year={2026},
  note={Preprint}
}
```

## Author

Quilee Simeon — Massachusetts Institute of Technology — qsimeon@mit.edu
