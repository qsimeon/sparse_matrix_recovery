# Paper Review Notes — Iteration 27
> Reviewer: Claude Opus 4.6 + GPT-5.4 (math verification)
> Date: 2026-03-22

## Changes This Iteration

### Section 2.1 Expanded (Surgical Additions)
1. **Weight motivation**: Added EM measurement modality argument — unsigned synapse size from electron microscopy justifies non-negative W. Explained the "dual formulation" where inhibition comes from signed activity rather than signed weights.
2. **CPG as heartbeat**: Added paragraph after stability explaining that ρ(W)≤1 + 1-Lipschitz φ means autonomous system contracts to origin (network "falls silent"). CPGs keep it alive like pacemaker cells. Input decomposition b = b_stim + b_CPG made explicit with independence properties.
3. **Connectivity motivation**: Added Cook et al. citation for sparse connected topology matching real connectomes.

### GPT-5.4 Deep Math Verification (5 questions)
All verified via openai/gpt-5.4 on OpenRouter:
- **(a) CORRECT**: ρ(W)<1 ⟹ Banach contraction, geometric convergence at rate ρ(W)
- **(b) CORRECT**: At ρ(W)=1, tanh still ensures decay since |tanh(x)|<|x| for x≠0, but convergence is subgeometric
- **(c) CORRECT**: PF gives real simple dominant eigenvalue with positive eigenvector; zero diagonal may cause imprimitivity but PF still holds for irreducible W
- **(d) NUANCED**: Not a formal duality theorem, but a "representation equivalence" via sign-splitting. Paper's informal "dual formulation" wording is appropriate.
- **(e) CORRECT**: Stein-Price identity verified. E[sech²(X)] = integral expression, approaches 1 for σ→0 and 0 for σ→∞.

### Still Valid from Previous Reviews
- Table 1: all 6 rows match fresh JSON data
- E4 ablation numbers: match
- 19/19 citations verified
- All 8 figures from fresh data (2026-03-22)

## No Outstanding Issues
All priority fixes from iteration 26 have been applied. Paper is internally consistent.
