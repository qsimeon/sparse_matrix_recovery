# Project Roadmap — Sparse Matrix Recovery
> Updated: 2026-04-14 (v7 plan — Phase E critical review + reruns)

## 2026-04-14 session (v7 Phase E)
- [x] E1: Added `fawzi2022discovering` (AlphaTensor) citation to A9 scalability note
- [x] E2: Added synaptic plasticity caveat as new Limitations item (6)
- [x] E5 (round 1): Reconciled VAR/GLM stale numbers in §4.3, §5, §6, Appendix A.10 (26%→36%, 37%→58%)
- [x] E6: Full vision-based page-by-page review via pdftoppm; findings logged in REVIEW_NOTES.md
- [x] Fixed blank pages 9 & 23: float placement `[p!]`→`[!tbp]` (fig 3), `[ht]`→`[!tbp]` (fig 9) + compact A.10 Summary. Paper: 24→22 pages.
- [x] E3 (partial): Archived 2026-04-11 JSONs; reran E2 on 2026-04-13; started local reruns of E1+E3-E8 on 2026-04-14
- [x] E10: Verified poster.tex + presentation.tex compile clean; no body-number edits needed (they don't reference VAR/GLM)
- [ ] E3 (continuing): Local reruns for E5, E6, E7, E8 still running in background
- [ ] E4: Regenerate 9 PDF figures once all fresh JSONs land (`uv run python scripts/generate_all_figures.py`)
- [ ] E5 (round 2): Final numerical reconciliation — check if fresh numbers shift `r=0.90`, `0.083`, `0.014`, E1/E2 error decomp, VAR/GLM percentages
- [ ] SSH cluster reruns (deferred, user requested "later"): need to `git clone`/`git pull` on engaging first; ControlMaster tunnel via `!ssh -M -N engaging` in parent shell
- [ ] Phase D: Final compile (24±2 pages), 3 clean commits (Phase A / Phase B / Phase E), push after user sign-off

## Completed (2026-04-11 session)
- [x] Paper §3.2: Remove erroneous "No self-connections" bullet (not Granger-specific); fold into preamble
- [x] Paper §2: EM autapse claim reframed as structural hypothesis + cited (white1986, cook2019)
- [x] Paper: Em dashes reduced from 15 to 2 (only true appositives remain)
- [x] Paper: Remove LLM filler expressions ("Crucially,", "a striking pattern emerges:", "Surprisingly,")
- [x] Paper: N range in Limitations updated (was "15 to 1074", now N∈{15,159,300} with bio motivation)
- [x] Paper: Perron-Frobenius citation added (Horn & Johnson 1985)
- [x] Paper: marinazzo2008kernel removed from bib; horn1985matrix added
- [x] Paper: 66%/67% inconsistency fixed (10/15 = 66%, consistent throughout)
- [x] Paper: Intro circuit list sentence restructured for clarity; zebrafish count fixed (10^4→10^5)
- [x] Paper: Figure 1 r value fixed (was 0.96, now reads from data = 0.90)
- [x] Paper: Figure 3 header clarified ("representative topology" vs "all 10 topologies")
- [x] Paper: Figure 9 caption corrected (r=0.90→0.94 for single-topology scatter)
- [x] Paper: CPG architecture figure (fig11) added to Appendix A.8 with caption
- [x] Repo: 500KB stale files removed (tools/, diagrams/, old sweep JSONs, duplicate scripts)
- [x] DEEP_DIVE.md: Comprehensive rewrite with verified numbers, CPG section, DOF table
- [x] Core.py: Full line-by-line walkthrough; abs vs ReLU empirically validated in notebook
- [x] Experiments: All 8 claims cross-referenced vs code and JSON data — 8/8 verified
- [x] Experiments: Re-run all E1-E8 with seed=42 (2026-04-11), confirmed deterministic
- [x] Figures: Regenerated all 11 from fresh data
- [x] launch_E1_scaling.sh: Updated from old 250-task (5N×5T) to current 90-task (3N×3T) config
- [x] Poster: Em dashes fixed, recompiled (poster.pdf 204KB)
- [x] Presentation: Verified numbers, recompiled (presentation.pdf 337KB)
- [x] Citations: 23/23 verified (all used, all cited)
- [x] explore_dynamics.ipynb: Abs vs ReLU CPG comparison cell added

## Completed (2026-04-07 session)
- [x] Fix precision/recall calculation bug (>0 threshold, was density-matched)
- [x] Full number audit: cross-check all 8 experiment JSONs against paper text
- [x] Fix 16+ stale numbers in main.tex, poster.tex, presentation.tex
- [x] Regenerate all 10 figures, recompile all PDFs
- [x] Remove dead code (sat, sign nonlinearities)
- [x] Fix notebook imports (sat reference removed)
- [x] Verify results reproduce bit-for-bit from code (seed determinism)

## Before arXiv Submission
- [ ] Final human read-through of compiled 21-page PDF (Overleaf or local)
- [ ] Visual inspection of all 11 figures at print resolution
- [ ] Run all 3 notebooks end-to-end, verify cell outputs match paper figures
- [ ] Consider adding GLM/VAR baseline comparison (strengthens empirical eval — reviewer will ask)
- [ ] Check presentation.tex slides for visual quality (SDSCon)

## Deferred (post-submission)
- [ ] GLM/VAR baseline comparison (L — reviewer will likely request)
- [ ] Systematic noise robustness beyond σ_ε=0.5 (M)
- [ ] CPG fraction sweep experiment (M)
- [ ] Mixed-sign weight experiments (L — extends non-negative assumption)
- [ ] WandB mega sweep on cluster if any parameter questions arise (L)
