# Project Status — Sparse Matrix Recovery

> Last reviewed: 2026-04-11 (deep critical review v3 — comprehensive session)
> Reviewer: Claude Sonnet 4.6

## Component Status

| Area | Status | Notes |
|------|--------|-------|
| Core algorithms | ✅ | core.py reviewed line-by-line, abs vs ReLU empirically validated, CPG serialize/deserialize confirmed correct |
| Experiments E1-E8 | ✅ | All re-run 2026-04-11, seed=42, results bit-for-bit reproducible vs Apr 7 |
| Figures | ✅ | All 11 figures regenerated (added fig11_cpg_architecture.pdf in Appendix A.8) |
| Paper (main.tex) | ✅ | 21 pages; §3.2 bullet logic fixed, em dashes→2, EM autapse reframed, LLM phrases removed, 66% consistent, Perron-Frobenius cited |
| Poster | ✅ | Numbers current, em dashes fixed, recompiled |
| Presentation | ✅ | Numbers current, recompiled |
| Notebooks | ✅ | abs vs ReLU comparison cell added to explore_dynamics.ipynb; all 3 notebooks import cleanly |
| Citations | ✅ | 23 cited, 23 in bib; marinazzo2008kernel removed, horn1985matrix added |
| Edge detection | ✅ | >0 threshold confirmed correct in code and paper |
| DEEP_DIVE.md | ✅ | Comprehensive rewrite 2026-04-11: updated numbers, CPG section, experiment table, verified numbers |
| Repo | ✅ | 500KB stale files removed (tools/, diagrams/, old sweep JSONs, duplicate scripts) |
| launch_E1_scaling.sh | ✅ | Updated to current E1 config (9 configs, array 0-89, not old 250-task version) |

## Key Numbers (2026-04-11, verified against fresh re-run)

- r = 0.90 (median across 10 topologies), 0.94 (representative topology in fig9)
- Improvement over spectral prior: **31%** (0.083 vs 0.120)
- Best: N=300, T=1000 → error 0.014 (97.5% over dense random baseline)
- Precision: 0.30 → 0.40 (raw → Granger-refined); Recall: 0.97 (maintained)
- Oracle 1.45–2.72× worse than approximation (E6)
- E₂ (CPG correlation) dominates E₁ (model mismatch) by ~1.8× (median), ~2.8× (rep topology)
- Noise: σ_ε=0.1 → +1.5% error, σ_ε=0.5 → +32% error

## What's Left (Before arXiv)

- [ ] Final human read-through of compiled 21-page PDF
- [ ] Visual inspection of all 11 figures at paper scale
- [ ] Consider adding GLM/VAR baseline comparison (strengthens empirical eval)
- [ ] Run notebooks end-to-end to verify all cell outputs match paper figures
- [ ] Update progress.json iteration counter (done in this session: 29→30)
