# Project Status — Sparse Matrix Recovery
> Last reviewed: 2026-04-26 (multi-round refinement loop, ready for arXiv)
> Reviewed by: Claude Opus 4.7

## Project Overview
A covariance-based method for recovering sparse neural connectivity matrices from partial multi-session recordings. The method accumulates pairwise covariances across K=50 sessions, inverts via pseudoinverse, applies structural priors (no autapses, non-negativity), and refines via a Granger-inspired projected gradient. Headline finding: the linear approximation beats the natural plug-in oracle estimator (James–Stein effect).

**Repo**: https://github.com/qsimeon/sparse_matrix_recovery (public)
**Paper**: `paper/main.tex` — 26 pages, NeurIPS preprint format. **Ready for arXiv submission.**

## Progress Summary
| Area | Status | Notes |
|------|--------|-------|
| Core algorithms (`experiments/core.py`) | ✅ | 813 lines, line-by-line reviewed |
| Paper `main.tex` (26 pp) | ✅ | All 5 review rounds applied; weak-accept verdict from 2nd-pass reviewer |
| Figures (9 PDFs) | ✅ | Regenerated 2026-04-26 from fresh 520-task SLURM rerun |
| Experiments E1-E8 | ✅ | Full VAR/GLM coverage; numerical claims verified to match data |
| Experiment code | ✅ | E8 `obs_noise_std` bug fixed; consolidated launcher |
| Bibliography | ✅ | 26 entries; new: Soudry 2015, Linderman 2014, Janzing 2010 |
| Notebooks (3) | 🔧 | Aligned with paper baseline; not re-executed since 2026-04-15 |
| Poster | ✅ | Recompiled 2026-04-26 with "natural plug-in oracle" qualifier |
| Presentation (8 slides) | ✅ | Recompiled 2026-04-26 |
| README, STATUS | ✅ | Reflect 26 pages, 9 figures, unified launcher |
| arXiv submission | ⏳ | URL placeholder cleanly removed; needs user to upload |

## Multi-Round Refinement Log (2026-04-26)

**Round 1** — 4 parallel agents:
- Math audit (H1 oracle naive vs smart, H2 Granger off-path sign-cancellation)
- Citation hunt (Soudry et al. 2015, Linderman & Adams 2014, Janzing & Schölkopf 2010)
- Section flow + global coherence (5 surgical edits)
- Code/repo cleanup audit (3 SAFE-TO-DELETE, 1 SAFE-TO-FIX, 4 NEEDS-USER-DECISION)

**Round 2** (math + citations applied):
- §A.4 oracle clarification: "natural plug-in" vs "split" oracle distinction
- §A.4 Caveat (2) tightened: bidirectional failure modes (false zero AND false retention) under off-path sign-cancellation
- 3 new citations inserted in Related Work with comparison framing

**Round 3** (5 flow edits applied):
- Abstract: James-Stein finding promoted to position 2 (was buried)
- §2: autapse paragraph compressed 6→3 sentences
- Conclusion: findings reordered to lead with James-Stein
- Contributions: reframed as consequences of pooling-then-inverting design choice
- §4 experiment list: E1-E7 → E1-E8 with inline finding hooks

**Round 4** (code cleanup):
- Deleted 137 lines of dead code: `generate_cpg_architecture_figure()` (analysis.py:1091) and superseded `main()` block (analysis.py:1041-1091)
- Removed orphaned `argparse` import
- Fixed docstring: "E1-E7" → "E1-E8" (core.py:29)
- Fixed print statements: "10 figures" → "9 figures" (generate_all_figures.py)
- All modules import cleanly; figure pipeline verified end-to-end

**Round 5** (2nd-pass critical reviewer): Weak accept verdict.
- 1 HIGH: arXiv URL `2603.18497` was a placeholder → removed entirely (and self-citation in references.bib)
- 3 MEDIUM: linear-identifiability disclaimer added to §A.3; abstract qualifier `at the N=15 baseline`; "natural plug-in oracle" qualifier added to main-text §6
- 1 nit: Algorithm 1 max() clarified as element-wise

**Round 6** (final compile): pdflatex×3 + bibtex; 26 pages, 758KB; zero undefined refs/citations/warnings (other than benign font notices).

**Round 7** (poster + presentation sync): Both recompiled with the "natural plug-in oracle" qualifier. Numerical content unchanged.

## What's Left

### Human Action Needed
- **Final read-through** of compiled `paper/main.pdf` at print resolution.
- **arXiv submission**: upload `main.tex`, `references.bib`, `paper/figures/*.pdf`, `neurips_2024.sty`. Once posted, optionally re-add the preprint URL to a final published version.
- **Notebook re-execution**: optional. Notebooks haven't been re-run since 2026-04-15; they may have stale outputs that don't quite match the new figures.

### Cleanup Candidates (left untouched, your call)
- `progress.json` (last modified Apr 11), `research_prd.json` (last modified Mar 29) — RALPH-loop iteration tracking. Not referenced by any code. Could move to `history/` or delete.
- `experiments/results/archive_2026_04_11/` and `archive_pre_rerun_2026_04_24/` — old result snapshots. Safe to delete now that fresh rerun is verified.
- 9 untracked `paper/figures/*.png` files — gitignored going forward; existing copies on disk not needed.

## Cluster State
- Engaging cluster: synced 2026-04-24, last SLURM jobs 12467081/12467143/12468840 all COMPLETED. Reps directory contains 520 per-rep JSONs.
- Local: aggregated `experiments/results/E{1..8}_*.json` are the source of truth for paper figures and numbers.

## Recommendations for Next Session
1. **Read the compiled PDF** end-to-end before submitting.
2. **arXiv submit** when ready; expected ID format: `2604.XXXXX` (April 2026).
3. **Commit** the multi-round refinement work as 1-2 logical commits (paper polish + repo cleanup).
