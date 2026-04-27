# Project Roadmap — Sparse Matrix Recovery
> Updated: 2026-04-26 (resituate post-commit — staleness audit + strategic review)

## 2026-04-26 (post-commit) resituate findings — actionable

### Immediate Fixes (broken or wrong)
- [x] README.md: 24 pp -> 26 pp (3 places, just fixed)
- [x] README.md: removed `2603.18497` arXiv URL + bibtex (just fixed; wasn't valid)
- [x] README.md: E2/E1 ratio "~2x" -> "~2.8x / ~3x" matching paper (just fixed)
- [ ] DEEP_DIVE.md: stale ("Last updated: 2026-04-11", numbers verified against Apr 7 data) — needs a sync to the 2026-04-24 fresh rerun results, or a one-line "Numbers verified to current state on YYYY-MM-DD" stamp
- [ ] paper/REVIEW_NOTES.md: archival document, header dated 2026-03-23 with content through 2026-04-14 — decide whether to retain in repo or move to a `history/` subfolder
- [ ] origin/ralph/sparse_matrix_recovery: stale remote branch (4 commits diverged, never merged) — `git push origin --delete ralph/sparse_matrix_recovery` after confirming nothing to salvage
- [ ] pyproject.toml: `[tool.hatch.build.targets.wheel] packages = ["experiments", "tools"]` references nonexistent `tools/` directory (wheel builds OK, but lying manifest) — drop `"tools"` from list

### Pre-arXiv Submission Checklist
- [ ] Final human read-through of compiled main.pdf (26 pp)
- [ ] arXiv submit: upload main.tex, references.bib, paper/figures/*.pdf, neurips_2024.sty
- [ ] Once posted with real arXiv ID, optionally re-add citation block to README + bibtex back-reference in paper

### Cleanup (cosmetic, deferred)
- [ ] Squash todo.md to a "## Recent" section + archive prior session logs to `tasks/history/2026-04.md`
- [ ] `.DS_Store` files on disk in 5 dirs — gitignored, harmless, but `find . -name '.DS_Store' -not -path './.venv/*' -delete` is a one-liner for cleanliness

## 2026-04-26 session (5-round refinement loop, 5 specialist agents)
- [x] Round 1: Spawned 4 parallel agents (math audit, citation hunt, section flow, code cleanup)
- [x] Round 2: Applied H1 (oracle naive vs split clarification, App A.4) and H2 (Granger off-path sign-cancellation, Caveat 2) edits
- [x] Round 2: Added 3 missing citations: Soudry 2015 (shotgun multi-session), Linderman 2014 (latent network Hawkes), Janzing 2010 (causal inference partial obs)
- [x] Round 3: 5 surgical flow edits (abstract reorder leads with James-Stein, §2 autapse compressed, conclusion reorder, contributions reframed, E1-E8 inline hooks)
- [x] Round 4: Removed 137 lines of dead code (`generate_cpg_architecture_figure`, stale `main()`, orphan `argparse`); fixed docstrings; verified imports + figure pipeline
- [x] Round 5: 2nd-pass reviewer (fresh-eyes) returned WEAK ACCEPT
- [x] Round 5: Fixed HIGH (placeholder arXiv URL `2603.18497` removed + self-citation excised from references.bib)
- [x] Round 5: Fixed 3 MEDIUM (§A.3 linear-identifiability disclaimer, abstract `at the N=15 baseline` qualifier, §6 "natural plug-in oracle" qualifier)
- [x] Round 5: Fixed editorial nit (Algorithm 1 element-wise max annotation)
- [x] Round 6: Final compile pdflatex×3+bibtex — 26 pages, 758KB, zero undefined refs
- [x] Round 7: Poster + presentation recompiled with "natural plug-in oracle" qualifier
- [x] STATUS.md rewritten to reflect new state; tasks/todo.md updated



## 2026-04-24 session (cluster rerun + caption audit)
- [x] Consolidated `launch_E1_scaling.sh` + `launch_experiments.sh` into single flat-index launcher (520 tasks; delete old E1 script)
- [x] Fixed E8 `obs_noise_std` bug in `run_single_rep.py` (was silently dropped from SLURM config)
- [x] Added E8 entry to `aggregate_results.py` exp_to_file mapping
- [x] rsync'd repo to engaging (cluster is NOT a git repo — uses scp/rsync)
- [x] Submitted 3 SLURM waves due to 500-task QOS cap (E1 / E2-E7 / E8) — all COMPLETED
- [x] rsync'd 520 rep JSONs back to local
- [x] Aggregated into 8 fresh experiment JSONs with full VAR/GLM coverage (was only in E2 before)
- [x] Regenerated all 9 figures from fresh data
- [x] Numerical audit: every paper claim matches fresh data within rounding (chance 0.555/0.576, VAR 58% worse, GLM 36% worse, Est 31% over Spec, r=0.90, N=300/T=1000 best = 0.014, E6 σ=0.1 ratio 2.2×, E8 degradation +2.4% at σ=0.1 / +31.5% at σ=0.5)
- [x] Paper recompiles clean at 24 pages, zero undefined refs
- [x] Caption audit: Fig 9 rewritten (described phantom layout); Fig 7/8 "Dots" claims removed (code only plots median + CI); Fig 2/5/6 "Left/Right" → "(A)/(B)"; Fig 5/8 schematics corrected to match actual experiment fractions
- [x] Repo cleanup: `texput.log` deleted; `.ipynb_checkpoints/` empty dir removed; `.gitignore` extended for `paper/figures/*.png` + `texput.log`
- [x] Docs updated: README.md (21→24 pp, 10→9 figs, launcher consolidation); STATUS.md full rewrite

## 2026-04-15 session (deep-dive review, Chunks 1–5)
- [x] Chunk 1: §1–§3 cross-referenced against core.py (estimator, priors, CPG, oracle)
- [x] Chunk 2: §3 internals + baselines verified (VAR, GLM, projected gradient); Fig 9 caption "raw-estimator" fix applied
- [x] Chunk 3: All 8 experiments (E1–E8) runner→JSON→plot verified; Fig 2 scaling fix + Fig 7 oracle ratio fix applied
- [x] Chunk 4: §5–§7 numerical claims verified; E2/E1 ratio ~2×→~3× fixed in 4 locations
- [x] Chunk 5: Appendices A.1–A.10 spot-checked; "Granger-inspired" reframing applied throughout; new Appendix A.4 derivation added
- [x] Granger deep-dive appended to DEEP_DIVE.md
- [x] Figures regenerated (all 9); paper compiles clean at 24 pages
- [x] Committed (e2ed821) and pushed to origin/main

## 2026-04-14 session (v7 Phase E)
- [x] E1: Added `fawzi2022discovering` (AlphaTensor) citation to A9 scalability note
- [x] E2: Added synaptic plasticity caveat as new Limitations item (6)
- [x] E5 (round 1): Reconciled VAR/GLM stale numbers in §4.3, §5, §6, Appendix A.10 (26%→36%, 37%→58%)
- [x] E6: Full vision-based page-by-page review via pdftoppm; findings logged in REVIEW_NOTES.md
- [x] Fixed blank pages 9 & 23: float placement `[p!]`→`[!tbp]` (fig 3), `[ht]`→`[!tbp]` (fig 9) + compact A.10 Summary. Paper: 24→22 pages.
- [x] E3 (partial): Archived 2026-04-11 JSONs; reran E2 on 2026-04-13; started local reruns of E1+E3-E8 on 2026-04-14
- [x] E10: Verified poster.tex + presentation.tex compile clean; no body-number edits needed (they don't reference VAR/GLM)
- [x] E4: Figures regenerated in deep-dive session (2026-04-15)
- [x] E5 (round 2): Final numerical reconciliation done in deep-dive Chunks 1–5
- [x] Phase D: Final compile (24 pages), committed + pushed to origin/main
- [ ] SSH cluster reruns (deferred, user requested "later"): need to `git clone`/`git pull` on engaging first; ControlMaster tunnel via `!ssh -M -N engaging` in parent shell

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
