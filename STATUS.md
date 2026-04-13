# Project Status — Sparse Matrix Recovery

> Last reviewed: 2026-04-13 (notebook execution + README/STATUS audit)
> Reviewed by: Claude Sonnet 4.6

---

## Project Overview

A covariance-based method for recovering sparse neural connectivity matrices from partial
multi-session recordings. The method accumulates pairwise covariances across K=50 sessions,
inverts via pseudoinverse, applies structural priors (no autapses, non-negativity), and
refines with a Granger-causality projected gradient descent. Key finding: the linear
approximation (treating tanh as identity) outperforms the oracle with known nonlinearity
at all tested regimes — a concrete James–Stein shrinkage instance.

**Repo**: https://github.com/qsimeon/sparse_matrix_recovery (PUBLIC as of 2026-04-12)

---

## Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core algorithms (`core.py`) | ✅ | Reviewed line-by-line; all design choices documented |
| Experiments E1–E8 | ✅ | Re-run 2026-04-12 seed=42; deterministic; all 8 paper claims verified |
| Figures (9 PDFs) | ✅ | All regenerated; sequential fig1–fig9; fig3 is 3-row with heteroskedasticity row |
| Paper (`main.tex`, 21 pp) | ✅ | All known issues fixed; GitHub link added; new appendix A.8 |
| Poster | ✅ | Numbers current; GitHub URL added; compiled |
| Presentation (8 slides) | ✅ | Numbers current; GitHub URL added; compiled |
| Citations | ✅ | 23/23 verified; all used, all have bib entries |
| Notebooks | ✅ | All 3 executed end-to-end (2026-04-13); all cells pass |
| DEEP_DIVE.md | ✅ | Comprehensive rewrite 2026-04-11 |
| README.md | ✅ | Audited 2026-04-13; figure count corrected to 9, all references current |
| STATUS.md / tracking | ✅ | This file |

---

## Verified Key Numbers (locked — do not change without re-running)

| Metric | Value | Source |
|--------|-------|--------|
| Weight correlation r | 0.90 median / 0.94 representative topology | E2_granger.json |
| Improvement over spectral prior | 31% (0.083 vs 0.120) | E2_granger.json |
| Best recovery | N=300, T=1000 → 0.014 (97.5% over chance) | E1_baseline.json |
| Precision raw→Granger | 0.30 → 0.40 | E2_granger.json |
| Recall | 0.97 (maintained) | E2_granger.json |
| Oracle ratio | 1.45–2.72× worse | E6_oracle_crossover.json |
| E₂/E₁ ratio | ~2× median, ~2.8× representative | E2_granger.json |
| Error-weight correlation | r≈0.91, slope≈1-d̄ (heteroskedasticity) | Fig 3 panel E |
| E7: 0% stim → error | 0.83 (catastrophic) | E7_stim_fraction.json |
| E7: 33% stim → error | 0.05 (recovers) | E7_stim_fraction.json |
| E8: σ_ε=0.5 → degradation | +32% error | E8_noise.json |

---

## What's Complete (this session 2026-04-11/12)

**Paper edits:**
- §3.2: Fixed Granger bullet logic (was listing "no self-connections" as Granger contribution)
- §2: EM autapse claim → structural hypothesis with citations
- Em dashes: 15 → 2
- LLM filler removed ("Crucially,", "a striking pattern emerges:", etc.)
- N range in Limitations: was stale "15 to 1074" → corrected to N∈{15,159,300}
- Perron-Frobenius citation added (Horn & Johnson 1985)
- Zebrafish count: 10⁴ → 10⁵ in intro
- 66%/67% inconsistency resolved
- E7 §4.8 rewritten: rank-vs-magnitude motivation for stimulation fraction
- New Appendix A.8: Heteroskedastic Error Structure (E₁[i,j]∝W_{ij}, r≈0.91, James–Stein connection)
- Figure 3 redesigned as 3-row: heatmaps (A–D) + error analysis (E–H) + violins (I–K)
- GitHub link in title footnote and code availability paragraph
- URL escape bug fixed (was rendering as %5C in PDF)
- CPG TikZ diagram: attempted then removed per user request

**Experiments & code:**
- E7 simplified from 5 to 3 conditions {0%, 33%, 66%}
- All E1–E8 re-run seed=42 (deterministic, results confirmed)
- launch_E1_scaling.sh: 250-task → 90-task (3N×3T)
- create_notebook.py deleted (was overwriting working notebook with broken one)
- launch_sweep.sh: fixed broken aggregate_sweep.py reference

**Repo hygiene:**
- Repo made public
- Deleted: tools/, paper/figures/diagrams/, old sweep JSONs, fig2_pipeline.pdf, fig_error_analysis.pdf
- scripts/aggregate_results.py duplicate deleted

**Notebooks:**
- explore_dynamics.ipynb: abs vs ReLU comparison cell added
- qsimeon_SparseMatrixRecovery.ipynb: warmup in CPG sim, stale r=0.96/recall=1.0 fixed
- complete_analysis.ipynb: unused imports removed, stale fig save removed, N=20 notes

---

## What's Left

### Before arXiv Submission (human needed)
- [ ] **Final human read-through** of compiled 21-page PDF — catch any remaining prose issues
- [x] **Run notebooks end-to-end** — all 3 executed cleanly 2026-04-13
- [ ] **Visual inspection** of all 9 figures at print resolution

### Completed by Agent (2026-04-13)
- [x] README.md audit — figure count corrected (10→9), all stale "10 figures" references fixed
- [x] STATUS.md updated — fig names corrected to sequential fig1–fig9, notebooks marked done

### Deferred (post-submission)
- GLM/VAR baseline comparison
- Systematic noise robustness beyond σ_ε=0.5
- CPG fraction sweep
- Mixed-sign weight experiments
- WandB mega sweep

---

## Figures Directory (CLEAN — only used files)

Renamed to sequential fig1–fig9 in commit f676e12 (2026-04-12).

| File | Used in | Notes |
|------|---------|-------|
| fig1_problem_schematic.pdf | paper, poster, presentation | Problem setup schematic |
| fig2_scaling.pdf | paper, poster, presentation | E1 scaling (N, T) |
| fig3_granger_refinement.pdf | paper | E2 3-row: heatmaps + error + violins |
| fig4_stimulation.pdf | paper, poster, presentation | E3 stimulation sweep |
| fig5_sparsity.pdf | paper | E4 measurement coverage |
| fig6_nonlinearity.pdf | paper | E5 nonlinearity mismatch |
| fig7_oracle_comparison.pdf | paper, poster, presentation | E6 oracle crossover |
| fig8_stim_fraction.pdf | paper | E7 stimulation fraction (3-condition) |
| fig9_dynamics.pdf | paper | E8 + CPG dynamics |

**No orphaned files.** Every PDF in figures/ is referenced by at least one document.

---

## Recommendations for Next Session

1. **Run notebooks end-to-end** — execute all 3 notebooks with `jupyter nbconvert --execute` and
   verify no errors. The warmup and import fixes haven't been execution-tested post-change.

2. **README.md audit** — quick scan for stale references (still says "7 experiments"? wrong figures count?).
   Take 10 minutes to align it with current state before arXiv.

3. **Human read-through of paper** — the paper is in near-final state. The single most valuable
   remaining action is a careful human read for scientific clarity, flow, and any edge cases
   in the experimental descriptions that only the author can judge.
