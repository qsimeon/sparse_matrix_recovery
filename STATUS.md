# Project Status — Sparse Matrix Recovery

> Last reviewed: 2026-04-07 (deep critical review v2, number audit, precision/recall fix)
> Reviewer: Claude Opus 4.6

## Component Status

| Area | Status | Notes |
|------|--------|-------|
| Core algorithms | ✅ | core.py reviewed line-by-line, dead code removed, API verified |
| Experiments E1-E8 | ✅ | All re-run 2026-04-07, results bit-for-bit reproducible |
| Figures | ✅ | All 10 regenerated, fig4 precision/recall violins now distinct |
| Paper (main.tex) | ✅ | 16+ stale numbers fixed, Table 1 rewritten for 3×3 grid |
| Poster | ✅ | Numbers updated, recompiled |
| Presentation | ✅ | Numbers updated, recompiled |
| Notebooks | ✅ | Imports fixed (sat removed), all 3 import cleanly |
| Citations | ✅ | 22 cited, all verified; 1 unused bib entry (marinazzo2008kernel) |
| Edge detection | ✅ | Bug fixed: was density-matched (precision≡recall), now >0 threshold |

## Key Numbers (2026-04-07, post-audit)

- r = 0.90 (median across 10 topologies), 0.94 (representative topology in fig8)
- Improvement over chance: 85.0% (baseline: N=15, T=1000, 66% measured)
- Best: N=300, T=1000 → error 0.014 (97.5% improvement)
- Precision: 0.30 → 0.40 (raw → Granger-refined)
- Recall: 0.97 (maintained through Granger refinement)
- Oracle 1.45–2.72× worse than approximation (E6)
- CPG correlation (E2) dominates model mismatch (E1) by ~2× (median), ~3× (rep topology)
- Noise: σ_ε=0.1 → +1.5% error, σ_ε=0.5 → +32% error

## What's Left

- [ ] Deep review: math walkthrough, experiment design rationale, paper line-by-line
- [ ] Run notebooks end-to-end (imports verified, execution pending)
- [ ] Update progress.json (stale at iteration 29)
- [ ] Update DEEP_DIVE.md numbers (in progress)
- [ ] Final human read-through before arXiv
