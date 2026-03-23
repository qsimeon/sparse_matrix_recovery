# RALPH Paper Loop — Sparse Matrix Recovery

## Mission
Produce a NeurIPS-ready paper, a 1-2 slide poster, and a 3-minute lightning talk script. Every claim grounded in data. Every equation verified. Every figure clear and publication-quality.

## Success Criteria
- [ ] PDF compiles cleanly with no warnings (pdflatex or tectonic)
- [ ] Every numerical claim verified against experiments/results/*.json
- [ ] Every equation verified by GPT-5.4 (run tools/openai_math.py)
- [ ] Every citation verified by Gemini (run tools/gemini_research.py)
- [ ] SPARC correctly defined as "Sparse Predictive Activity through Recombinase Competition" (if referenced)
- [ ] Experimental paradigm clearly articulated: what we vary, control, measure in each E1-E7
- [ ] All 10 figure captions describe what's shown in detail (axes, colors, key observations)
- [ ] Paper reads as a coherent story, not a list of experiments
- [ ] 1-2 slide poster created (paper/poster.tex or paper/poster.html)
- [ ] 3-minute lightning talk script created (paper/lightning_talk.md)
- [ ] No broken \ref, no "??" in PDF
- [ ] No unsupported claims — every assertion has a citation or data reference

## Scope
ONLY touch: paper/, tools/ (for verification calls)
Do NOT touch: experiments/, notebooks/ (the other ralph loop handles that)

## Tools Available
- Math verification: `python tools/openai_math.py --model gpt-5.4 --task "..."`
- Lit research: `python tools/gemini_research.py --query "..."`
- Citation check: `python scripts/verify_citations.py`
- PDF compilation: `cd paper && pdflatex -interaction=nonstopmode main.tex` (or `tectonic main.tex`)
- Read PDF: Use the Read tool on paper/main.pdf or paper/sparse_matrix_recovery.pdf

## Iteration Plan
1. Compile PDF, read every page, note ALL issues in paper/REVIEW_NOTES.md
2. Fix the most critical issue found
3. Verify all equations match code (use GPT-5.4 for non-trivial ones)
4. Verify all citations are real papers (use Gemini search grounding)
5. Verify all numbers match data files
6. Improve figure captions for clarity
7. Write poster (1-2 slides, key results + method diagram)
8. Write lightning talk script (3 min, structured as: problem → insight → method → results → impact)
9. Final compilation and visual check

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
