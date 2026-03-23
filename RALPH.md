# RALPH — Sparse Matrix Recovery Paper

## Thesis
Recovering sparse neural connectivity from partial measurements via covariance accumulation + Granger refinement. The paper needs to tell a compelling story about experimental design for neural circuit inference.

## Success Criteria
- [ ] Every figure has been visually inspected and looks publication-quality (log scales where needed, consistent colors, readable at print size)
- [ ] Every numerical claim in main.tex matches the corresponding JSON data file
- [ ] Section 2.1 fully motivates every design choice (why excitatory, why tanh, why CPGs, why edge-of-stability)
- [ ] Section 4.1 experimental design table is complete and explains the 5 experimental knobs
- [ ] Discussion addresses sensor fraction findings and their practical implications
- [ ] All 3 notebooks in notebooks/ execute without errors and demonstrate key results
- [ ] Paper reads as a coherent narrative, not a list of experiments
- [ ] No broken \ref, no "??" in compiled PDF

## Current Blockers
1. Paper narrative flow — experiments feel listed, not told as a story
2. Discussion section doesn't integrate E7 sensor findings
3. Notebooks may not include E7 demo
4. Figure quality inconsistent (some have log scale, some don't when they should)

## Iteration Plan (prioritized)
1. Read entire paper top-to-bottom, note every issue in paper/REVIEW_NOTES.md
2. Fix the weakest section identified in step 1
3. Visually inspect EVERY figure (read the PDFs), fix any with quality issues
4. Verify all numbers: run verify_citations.py + cross-check table/text vs JSON
5. Re-read paper again, fix narrative flow
6. Update notebooks with E7 content, re-execute all 3
7. Final consistency audit

## Resources
- Python env: conda activate work_env
- API keys: ~/.secrets (OPENAI via OpenRouter, GEMINI, ANTHROPIC)
- Math verification: python tools/openai_math.py --model gpt-5.4
- Lit review: python tools/gemini_research.py
- Citations: python scripts/verify_citations.py
- All figures: python scripts/generate_all_figures.py
- Experiments: python experiments/run_experiments.py --experiment E1-E7

## Stop Conditions
- max_iterations: 20
- no_improvement_limit: 3 consecutive iterations with no substantive changes
- success: all criteria checked off in REVIEW_NOTES.md
