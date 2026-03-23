# RALPH Code Loop — Sparse Matrix Recovery

## Mission
Ensure all code, experiments, notebooks, and data are complete, correct, and reproducible. Every experiment result in the paper must be reproducible from the code.

## Success Criteria
- [x] All 7 experiments (E1-E7) re-run with seed=42, results match paper claims
- [x] All 10 figures regenerated from fresh data via scripts/generate_all_figures.py
- [x] All 3 notebooks in notebooks/ execute end-to-end without errors
- [x] experiments/core.py has no bugs (spectral radius, diagonal zeroing, CPG, etc.)
- [x] experiments/run_experiments.py E1-E7 configs match paper's Table 2
- [x] experiments/analysis.py generates all 10 figures correctly
- [x] No stale data in experiments/results/ — everything from current code
- [x] scripts/verify_citations.py passes (20/20 citations)

## Scope
ONLY touch: experiments/, notebooks/, scripts/, tools/
Do NOT touch: paper/ (the other ralph loop handles that)

## Tools Available
- Math verification: `python tools/openai_math.py --model gpt-5.4 --task "..."`
- Lit research: `python tools/gemini_research.py --query "..."`
- Citation check: `python scripts/verify_citations.py`
- Figure generation: `python scripts/generate_all_figures.py`
- Experiments: `python experiments/run_experiments.py --experiment E1 --seed 42`

## RESUMING — Previous run completed 3 real iterations then died (API credits/OAuth)
Previous run accomplished:
- [x] Added Fig 9 + Fig 10 to generate_all_figures.py pipeline
- [x] Fixed sys.path in main notebook for notebooks/ directory execution
- [x] Figures regenerated, notebooks execute, analysis.py works

REMAINING (start here):
1. Re-run ALL experiments: `python experiments/run_experiments.py --experiment all --seed 42`
2. Compare fresh results to experiments/results/*.json — flag any discrepancies with paper
3. Review core.py line by line — check math matches paper equations (use GPT-5.4)
4. Review run_experiments.py — verify E1-E7 configs match paper Table 2
5. Verify no stale data — everything from current code
6. Run scripts/verify_citations.py
7. Clean up any stale files

## Self-Improvement
You CAN edit this RALPH_code.md, ralph_code.sh, or any tool in tools/ if you find issues. If a tool is broken or could be better, fix it.

## Stop Conditions
- max_iterations: 15
- All criteria checked: RALPH_STOP
- 3 iterations no progress: RALPH_STOP: stuck

## Commit Convention
Prefix all commits with `code:` e.g. `code: re-run E1-E7 with seed=42, verify results`
