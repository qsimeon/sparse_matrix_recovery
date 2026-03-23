# RALPH Code Loop — Sparse Matrix Recovery

## Mission
Deep line-by-line review of ALL code. Verify correctness, completeness, clarity. Ensure every experiment is reproducible and every result matches what the paper claims.

## Success Criteria
- [x] Read experiments/core.py line by line — verify every function's math matches paper equations
  - Dynamics: `state = W @ phi(state) + total_input` matches paper eq (1)
  - Estimator: `approx_W = cov_dtx @ pinv(cov_x)` matches paper eq W_hat = Σ_{x_{t+1},x_t} Σ_{x_t,x_t}^{-1}
  - Covariance accumulation across sessions with mask correctly handles partial observations
  - Oracle estimator, Granger projected gradient, spectral radius adjustment all correct
- [x] Read experiments/run_experiments.py line by line — verify E1-E7 configs match paper Table 2 exactly
  - E1: N∈{8,12,30}, T∈{100,500,1000}, 66% measured, 33% CPG/sensors, stim=1.0, tanh ✓
  - E2: N=12, T=900, meas∈{33%,50%,66%,80%,100%} ✓
  - E3: N=12, T=900, 2D sweep meas×stim ✓
  - E4: N=12, T=900, 30 reps, 50 sessions, save_matrices=True ✓
  - E5: N=12, tanh/relu/identity/sigmoid ✓
  - E6: stim sweep {0,0.1,...,5.0} for oracle crossover ✓
  - E7: sensors∈{1,2,4,8,12} ✓
  - Fixed: docstring "E1-E6"→"E1-E7", section header "E1-E5"→"E1-E7", removed unused `import os`
- [x] Read experiments/analysis.py — verify each figure function produces what the paper caption describes
  - All 9 figure functions reviewed line-by-line: schematics (F1, F7), data plots (F2–F6, F8–F9)
  - Fixed: main() was missing F8 (sensor fraction) and F9 (oracle crossover) handlers — these figures couldn't be generated via `--figure F8` or `--all`
  - Fixed: help text "F1-F7" → "F1-F9", figure list now includes all 9 internal figures
  - Internal F-numbering (F1–F9) maps correctly to paper fig numbers (fig1–fig10) via generate_all_figures.py
  - Each plot function correctly: loads data, extracts medians + CIs, plots with correct labels/axes/colors
- [x] Re-run E1-E7 fresh, compare results to paper claims (flag ANY discrepancy)
  - ALL experiments re-run with deterministic per-worker seeding (seed=42), full results reproducible
  - E1: N=30/T=1000 achieves 0.062, recovery improves with T and N ✓
  - E2: 33%→0.597, 50%→0.119, 66%→0.105, 80%→0.101, 100%→0.096 — monotonic improvement ✓
  - E3: stimulation×measurement tradeoff confirmed across all 18 conditions ✓
  - E4: est=0.100, grn=0.097, chance=0.54, recall=1.0 ✓
  - E5: tanh=0.102, relu=0.189, identity=0.191, sigmoid=0.149 ✓
  - E6: oracle always worse than estimator at all stim levels ✓
  - E7: 1sensor=0.387, 2=0.120, 4+=≈0.10 ✓ (Note: 1-sensor value 0.387 differs from old non-deterministic 0.30 — this is the correct reproducible value)
  - All qualitative paper conclusions hold; minor quantitative shifts due to deterministic seeding
- [ ] Regenerate all figures, visually inspect each one (read the PDFs!)
- [x] Execute all 3 notebooks end-to-end, verify they produce sensible output
  - explore_dynamics.ipynb: 9 code cells, 8 figures, 0 errors — demonstrates topology generation, CPG dynamics, chaotic reservoir, stimulation tradeoff
  - complete_analysis.ipynb: 8 code cells, 7 figures, 0 errors — Price's theorem, covariance accumulation, ablation chart, noise robustness (σ_ε=0.00: Granger error=0.0992)
  - qsimeon_SparseMatrixRecovery.ipynb: 10 code cells, 6 figures, 0 errors — full method demonstration including 10 reps × 50 networks experiment
  - All outputs sensible, no warnings except cosmetic urllib3 RequestsDependencyWarning in last notebook
- [x] Review scripts/generate_all_figures.py — does it generate all 11 figure PDFs?
  - Generates 10 figures (fig1–fig10), NOT 11. Script says "All 10 figures generated!"
  - fig1: problem schematic, fig2: pipeline, fig3: scaling(E1), fig4: granger(E4)
  - fig5: stim tradeoff(E3), fig6: sparsity(E2), fig7: nonlinearity(E5)
  - fig8: dynamics(live sim), fig9: sensor fraction(E7), fig10: oracle(E6)
- [x] Check for dead code, unused imports, stale comments in ALL .py files
  - Fixed: `import os` unused in run_experiments.py
  - Fixed: "E1-E6" and "E1-E5" stale comments in run_experiments.py
  - Note: analysis.py internal figure labels (F1-F9) differ from paper figure numbers (fig1-fig10) but this is handled by generate_all_figures.py mapping — not a bug, just legacy naming
- [x] Verify tools/openai_math.py and tools/gemini_research.py work (test them)
  - openai_math.py: --list-models works, imports clean, API call via OpenRouter (gpt-4o) returns proper math verification with LaTeX, usage stats, timestamps
  - gemini_research.py: imports clean (urllib3 version warning only), API call via Gemini (2.0-flash) returns research synthesis with 4 grounded sources
  - Both tools: batch mode, file input, JSON output all structurally correct
  - Minor: gemini_research.py shows RequestsDependencyWarning from urllib3 version mismatch — cosmetic, not functional

## Scope
Touch: experiments/, notebooks/, scripts/, tools/
Do NOT touch: paper/ (the other loop handles that)

## Tools
- Run experiments: `conda run -n work_env python experiments/run_experiments.py --experiment E1 --seed 42`
- Generate figures: `conda run -n work_env python scripts/generate_all_figures.py`
- Execute notebook: `conda run -n work_env jupyter nbconvert --to notebook --execute notebooks/X.ipynb --output X.ipynb`
- Math verify: `conda run -n work_env python tools/openai_math.py --model gpt-5.4 --task "..."`
- Citations: `conda run -n work_env python scripts/verify_citations.py`

## Rules
- ONE change per iteration. Read → identify weakest thing → fix it → verify → commit.
- Actually READ your output. If a figure looks wrong, fix it. If code has a bug, fix it.
- Prefix commits: `code: [description]`
- RALPH_STOP when all criteria checked OR stuck for 3 iterations.
- You CAN edit this file, ralph_code.sh, or tools/ (self-improvement allowed).

## Stop Conditions
- max_iterations: 15
- time_budget: 6h
- All criteria checked: RALPH_STOP: all criteria met
- 3 iterations no progress: RALPH_STOP: stuck
