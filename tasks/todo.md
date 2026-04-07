# Project Roadmap — Sparse Matrix Recovery
> Generated: 2026-04-07 (deep critical review v2)

## Completed (this session)
- [x] Fix precision/recall calculation bug (> 0 threshold, was density-matched)
- [x] Full number audit: cross-check all 8 experiment JSONs against paper text
- [x] Fix 16+ stale numbers in main.tex, poster.tex, presentation.tex
- [x] Regenerate all 10 figures, recompile all PDFs
- [x] Remove dead code (sat, sign nonlinearities)
- [x] Fix notebook imports (sat reference removed)
- [x] Verify results reproduce bit-for-bit from code (seed determinism)
- [x] Verify citation integrity (22 cited, 23 in bib, 1 unused: marinazzo2008kernel)
- [x] Fix stale doc references (DEEP_DIVE.md, README.md: r=0.96→0.90, perfect recall→actual)

## In Progress — Deep Review
- [ ] Core algorithm review: core.py line-by-line walkthrough with user
- [ ] Experiment design review: E1-E8 parameter choices explained
- [ ] Mathematical deep dive: trace paper equations through code
- [ ] Run all 3 notebooks end-to-end, verify outputs
- [ ] Scripts/tools review (generate_all_figures.py, create_notebook.py, tools/)
- [ ] Paper critical review: line-by-line as reviewer
- [ ] Update progress.json (stale at iteration 29, needs 30+)

## Before arXiv Submission
- [ ] Compile PDF in Overleaf and human-read the whole paper
- [ ] Visual inspection of all compiled figures (quality, readability)
- [ ] Consider adding marinazzo2008kernel citation to Related Work
- [ ] Consider adding GLM/VAR baseline comparison (strengthens empirical eval)
- [ ] Update progress.json iteration counter

## Deferred (v2 / post-submission)
- [ ] GLM/VAR baseline comparison (L)
- [ ] Systematic noise robustness sweep beyond σ_ε=0.5 (M)
- [ ] CPG fraction sweep experiment (M)
- [ ] WandB mega sweep on cluster (243 configs × 10 topologies) (L)
- [ ] Mixed-sign weight experiments (extends beyond non-negative assumption) (L)
