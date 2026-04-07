# Project Roadmap — Sparse Matrix Recovery
> Generated: 2026-03-23 (resituate deep review)
> Updated: 2026-03-29 — All experiments re-run with corrected fractions (N//3), all numbers verified, paper compiled clean.

## Immediate (blocks arXiv submission)
- [x] Fix fraction computation bug: int(0.33*N) → N//3 with exact fractions
- [x] Re-run E1, E3, E4 on cluster with corrected fractions (480 SLURM tasks)
- [x] Fix ALL stale numbers in paper/main.tex — Table 2, E1/E3/E4/E6 text, all captions
- [x] Regenerate all 10 figures from corrected data
- [x] Recompile main.tex and poster.tex — both clean
- [x] Verify abstract headline numbers (85%, r=0.96) against data
- [x] Update STATUS.md, DEEP_DIVE.md, README.md, research_prd.json — no "pending re-run" remains
- [x] Final-pass audit: dead code, broken imports, stale labels, .gitignore gaps
- [ ] Compile PDF in Overleaf and read it yourself as a human (S)
- [ ] Update progress.json iteration counter (S)

## Polish (before submission)
- [ ] Visual inspection of compiled PDFs (poster column balance, figure quality)
- [ ] Practice lightning talk with timer

## Nice-to-Have (defer for v2)
- [ ] Add GLM/VAR baseline comparison (L) — strengthens empirical evaluation
- [ ] Systematic noise robustness experiments (M)
- [ ] E8: CPG fraction sweep (M)
- [ ] Run WandB mega sweep on engaging cluster (243 configs × 10 topologies)

## Kill / Defer
- tools/*.py (openai_math, gemini_research) — development tools, not paper artifacts
- experiments/results/lit_review*.json, math_verification*.json — RALPH artifacts
- progress.json, research_prd.json — development tracking only
