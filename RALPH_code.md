# RALPH Code Loop — Sparse Matrix Recovery

## Mission
Ensure all code, experiments, notebooks, and data are complete, correct, and reproducible. Every experiment result in the paper must be reproducible from the code.

## Success Criteria
- [ ] All 7 experiments (E1-E7) re-run with seed=42, results match paper claims
- [ ] All 10 figures regenerated from fresh data via scripts/generate_all_figures.py
- [ ] All 3 notebooks in notebooks/ execute end-to-end without errors
- [ ] experiments/core.py has no bugs (spectral radius, diagonal zeroing, CPG, etc.)
- [ ] experiments/run_experiments.py E1-E7 configs match paper's Table 2
- [ ] experiments/analysis.py generates all 10 figures correctly
- [ ] No stale data in experiments/results/ — everything from current code
- [ ] scripts/verify_citations.py passes (19-20 citations)

## Scope
ONLY touch: experiments/, notebooks/, scripts/, tools/
Do NOT touch: paper/ (the other ralph loop handles that)

## Tools Available
- Math verification: `python tools/openai_math.py --model gpt-5.4 --task "..."`
- Lit research: `python tools/gemini_research.py --query "..."`
- Citation check: `python scripts/verify_citations.py`
- Figure generation: `python scripts/generate_all_figures.py`
- Experiments: `python experiments/run_experiments.py --experiment E1 --seed 42`

## Iteration Plan
1. Run `python experiments/run_experiments.py --experiment all --seed 42` — re-run everything
2. Compare fresh results to experiments/results/*.json — flag any discrepancies
3. Run `python scripts/generate_all_figures.py` — regenerate all figures
4. Execute each notebook: `jupyter nbconvert --execute notebooks/*.ipynb`
5. Review core.py line by line — check math matches paper equations
6. Review run_experiments.py — verify E1-E7 configs match paper Table 2
7. Clean up any stale files, fix any issues found

## Self-Improvement
You CAN edit this RALPH_code.md, ralph_code.sh, or any tool in tools/ if you find issues. If a tool is broken or could be better, fix it.

## Stop Conditions
- max_iterations: 15
- All criteria checked: RALPH_STOP
- 3 iterations no progress: RALPH_STOP: stuck

## Commit Convention
Prefix all commits with `code:` e.g. `code: re-run E1-E7 with seed=42, verify results`
