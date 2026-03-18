# Paper Review Notes — Line-by-Line Audit
> Reviewer: Claude (acting as critical scientist/mathematician)
> Date: 2026-03-18 (iteration 20)

## Overall Assessment
13-page paper (10 main + 3 appendix) with 8 figures and 19 citations. For a workshop paper (target ~6 pages), this needs trimming. The science is solid: key results (82% improvement, r=0.90, stimulation-measurement interaction, implicit regularization) are verified and reproducible across seeds. All numbers match actual data files. All equations verified by GPT-5.4.

## Issues Fixed This Iteration
- [x] Figure filenames renamed to match paper order (fig1-fig8)
- [x] All LaTeX references updated to new filenames
- [x] analysis.py output paths updated
- [x] explore_dynamics.ipynb: 5 cells with stale params fixed (non_neg=False→True, stim=0.1→1.0, nets=15/20→50)
- [x] complete_analysis.ipynb: num_networks=30→50 in 2 cells
- [x] Noise robustness numbers corrected: 7% at σ=0.1, 37% at σ=0.5 (10-seed average)
- [x] Notebook executed end-to-end with all outputs verified

## Remaining Issues (non-blocking)
1. **Paper length**: 13 pages — needs trimming to ~6 for workshop. Move E2+E5 to appendix.
2. **Figure schematics**: F5 left panel (stimulation) and F6 left panel (sparsity) use generic ring networks, not actual random topologies from experiments. Cosmetic.
3. **No GLM/VAR experimental comparison**: Discussed in limitations but not tested. Would strengthen the paper.

## All Checks Passing
- 19 citations = 19 bib entries (perfect match)
- Zero N=60 references in any code
- Zero stale parameters in any notebook
- All figure filenames match paper order
- Noise robustness numbers match 10-seed average
- Key results reproduce with independent seed (seed=99)
