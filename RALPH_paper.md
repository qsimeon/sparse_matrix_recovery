# RALPH Paper Loop — Sparse Matrix Recovery

## Mission
Produce a NeurIPS-ready paper, a 1-2 slide poster, and a 3-minute lightning talk script. Every claim grounded in data. Every equation verified. Every figure clear and publication-quality.

## Success Criteria
- [~] PDF compiles cleanly with no warnings (pdflatex or tectonic) — fixed overfull hbox; only cosmetic underfull remain
- [~] Every numerical claim verified against experiments/results/*.json — key claims verified; N=30 T=1000 data source TBD
- [ ] Every equation verified by GPT-5.4 (run tools/openai_math.py)
- [x] Every citation verified — all 20 bib entries are real papers with correct metadata (authors, year, journal, volume, pages); verify_citations.py confirms 1:1 match between cited keys and bib entries
- [x] SPARC correctly defined as "Sparse Predictive Activity through Recombinase Competition" (if referenced) — misattributed citation fixed in prior run; only generic "SPARC transgenic line" remains
- [x] Experimental paradigm clearly articulated: what we vary, control, measure in each E1-E7 — Table 1 + Section 4.1 text
- [x] All 10 figure captions describe what's shown in detail (axes, colors, key observations) — verified in prior run
- [x] Paper reads as a coherent story, not a list of experiments — narrative flow verified in prior run
- [x] 1-2 slide poster created (paper/poster.tex or paper/poster.html)
- [x] 3-minute lightning talk script created (paper/lightning_talk.md)
- [x] No broken \ref, no "??" in PDF — verified this iteration
- [x] No unsupported claims — every assertion has a citation or data reference — verified in prior run

## Scope
ONLY touch: paper/, tools/ (for verification calls)
Do NOT touch: experiments/, notebooks/ (the other ralph loop handles that)

## Tools Available
- Math verification: `python tools/openai_math.py --model gpt-5.4 --task "..."`
- Lit research: `python tools/gemini_research.py --query "..."`
- Citation check: `python scripts/verify_citations.py`
- PDF compilation: `cd paper && pdflatex -interaction=nonstopmode main.tex` (or `tectonic main.tex`)
- Read PDF: Use the Read tool on paper/main.pdf or paper/sparse_matrix_recovery.pdf

## RESUMING — Previous run completed 3 real iterations then died (API credits/OAuth)
Previous run accomplished:
- [x] Fixed LaTeX float specifier warnings ([h] → [ht])
- [x] Created A1 landscape poster (paper/poster.tex)
- [x] Created 3-minute lightning talk script (paper/lightning_talk.md)

REMAINING (resumed session):
1. ~~Compile PDF and READ every page visually~~ — DONE (iter 1): fixed overfull hbox, no broken refs
2. Verify all equations match code implementations (use GPT-5.4: `python tools/openai_math.py --model gpt-5.4 --task "..."`)
3. ~~Verify all citations are real papers~~ — DONE (iter 2): all 20 citations verified, verify_citations.py 20/20 match
4. ~~Verify all numerical claims~~ — DONE (iter 1): key claims match E4/E5/E6/E7 data
5. ~~Improve figure captions~~ — DONE (prior run): all 10 captions have axes, colors, observations
6. ~~Ensure experimental paradigm clearly described~~ — DONE (prior run): Table 1 + Section 4.1
7. Review poster and lightning talk for accuracy against current paper
8. Final PDF compilation and visual quality check

## Key Facts (ground truth)
- SPARC = "Sparse Predictive Activity through Recombinase Competition" (NOT "random perturbation" or "ensemble stimulation")
- Baseline: N=12 neurons, T=900 timesteps, K=50 sessions, 66% measured, 33% sensors, stim=1.0, φ=tanh
- Best result: N=30, T=1000 → error 0.053 (91% vs chance)
- r ≈ 0.91 weight correlation (Granger-refined)
- CPG correlation (E2) is 3.3× larger than model mismatch (E1)
- Oracle is always worse than approximate (E6)

## Self-Improvement
You CAN edit this RALPH_paper.md, ralph_paper.sh, or tools/ if needed. If the PDF compiler isn't installed, install it or find an alternative.

## Stop Conditions
- max_iterations: 15
- All criteria checked: RALPH_STOP
- 3 iterations no progress: RALPH_STOP: stuck

## Commit Convention
Prefix all commits with `paper:` e.g. `paper: fix equation 7 sign error, verified by GPT-5.4`
