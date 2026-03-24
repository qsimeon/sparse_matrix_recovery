# Project Roadmap — Sparse Matrix Recovery
> Generated: 2026-03-23 (resituate deep review)
> Context: Paper structurally complete but numerical claims stale after final experiment re-run.

## Immediate (blocks arXiv submission)
- [ ] Fix ALL stale numbers in paper/main.tex to match current experiments/results/*.json (M)
  - Table 2 (E1 baseline): ~18 cells wrong
  - E4 in-text claims (line 334): 0.095 → 0.097, 0.533 → 0.538
  - E4 figure caption (line 340): 0.098 → 0.100, 0.095 → 0.097
  - E6 oracle ratios (line 399): "4.0× at σ=0" should be 1.9× (or refer to σ=0.1 = 4.2×)
  - E7 error values (lines 417-418): "0.244" and "0.128" don't match any metric
  - E2 sparsity claims (lines 367-368): "0.270" → 0.321, "0.477" → 0.598
  - E5 tanh claim (line 381): "0.095" → 0.101
  - Abstract "82%" and "r=0.91" — verify against fresh Fig 8 run
- [ ] Decide consistent reporting convention for E7: estimate or Granger? (S)
- [ ] Verify abstract headline numbers still hold after fixes (S)

## Polish (before submission)
- [ ] Update README: change `pip install` to `uv sync` (S)
- [ ] Compile PDF in Overleaf and read it yourself as a human (S)
- [ ] Update progress.json: 7 experiments, 10 figures, iteration 28 (S)
- [ ] Update research_prd.json: add F9/F10 figures, fix E6 oracle ratio (S)

## Nice-to-Have (defer for v2)
- [ ] Add GLM/VAR baseline comparison (L) — strengthens empirical evaluation
- [ ] Test at N=50-100 to expand scaling story (L)
- [ ] Systematic noise robustness experiments (M)
- [ ] E8: CPG fraction sweep (M)

## Kill / Defer
- tools/*.py (openai_math, gemini_research) — development tools, not paper artifacts. Consider gitignoring.
- experiments/results/lit_review*.json, math_verification*.json — RALPH artifacts, not data
- progress.json, research_prd.json — useful for development tracking only
