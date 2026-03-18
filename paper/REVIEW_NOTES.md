# Paper Review Notes — Line-by-Line Audit
> Reviewer: Claude (acting as critical scientist/mathematician)
> Date: 2026-03-18

## Overall Assessment
The paper is 13 pages (10 main + 3 appendix). For a workshop paper (typically 4-6 pages), this is WAY too long. The content is solid but needs significant trimming. The figures are good but some have issues. The math is mostly correct (GPT-5.4 verified) but the presentation could be cleaner.

---

## PAGE 1: Title, Abstract, Introduction

### Title
- OK but long. Consider shorter: "Connectivity Recovery from Partial Neural Measurements via Covariance Accumulation"

### Abstract
- GOOD: concise, hits all key points
- ISSUE: "small brain circuits" — good framing
- ISSUE: "control-estimation tradeoff" mentioned but not defined in abstract — reader doesn't know what this means yet

### Introduction (p1-2)
- GOOD: Well-cited now (10 citations in intro)
- ISSUE p1 line "We formalize this as a sparse matrix recovery problem [Candès et al., 2011]" — Candès 2011 is about *robust PCA*, not sparse matrix recovery per se. A more appropriate citation would be about matrix completion (Candès & Recht 2009) or just remove the citation since the formalization is our own.
- ISSUE: "governed by discrete-time recurrent dynamics [Strogatz, 2015]" — Strogatz is a textbook on *continuous-time* nonlinear dynamics. The discrete-time recurrence x_{t+1} = Wφ(x_t) + b_t is more standard in RNN literature. Better cite a recurrent neural network reference (e.g., Sompolinsky et al. 1988 or Sussillo & Abbott 2009 which is already cited).
- ISSUE: Contribution bullet 4 says "optimal stimulation depends on fraction of observed neurons" but doesn't mention that this is a *corrected* finding (original analysis said zero stim was optimal). This is fine for the paper — don't mention the correction.

## PAGE 2: Problem Formulation, Methods

### Section 2.1 (Dynamical System Model)
- GOOD: Clean, standard notation
- MINOR: "ρ(W) ≤ 1" — should clarify this is the spectral radius *constraint we impose*, not a property of all neural circuits

### Section 2.2 (Observation Model)
- ISSUE: Eq (2) has ε_t (measurement noise) but this noise is NEVER used in our simulations. We simulate noise-free observations of measured neurons. Should either: (a) drop ε_t and note we assume noiseless observation, or (b) add observation noise to the simulation.

### Section 3.1 (Covariance-Based Estimator)
- GOOD: Derivation is clean
- ISSUE: Eq (3) says Σ_{b_t, x_t} ≈ 0 but we just showed this is BADLY violated (E2 is 3.5x larger than E1). The paper later discusses this (p10) but the initial presentation is misleading. Should add a forward reference: "this approximation is revisited in Section 6"
- MATH CHECK: Eq (6) sign — FIXED in latest version. Now reads Σ_{φ(x),x} - Σ_{x,x} which GPT-5.4 confirmed correct.

### Section 3.1 (Error Analysis / Price's Theorem)
- ISSUE: Eq (7) says D' = diag(E[sech²(x_i)]) and then claims E1 = W(D'-I). Let me check: if Σ_{φ(x),x} = D'Σ_{x,x}, then E1 = W[D'Σ - Σ]Σ^{-1} = W[D'-I]. YES this is correct.
- ISSUE: "substantially tighter than generic Lipschitz bounds" — we should quantify HOW much tighter. E.g., "For σ_i = 0.8 (typical in our simulations), d_i ≈ 0.5 vs the Lipschitz bound which gives 1.0"
- ISSUE: "||Σ_{x,x}^{-1}||_2 amplifies both error sources" — this sentence appears after the Price's theorem paragraph but refers to *both* E1 and E2. It should be its own sentence, not attached to the Price paragraph.

### Section 3.2 (Granger Refinement)
- ISSUE: The Granger non-causality criterion "W_{ij} = 0 where Σ_{x_t,x_t}(i,j) > Σ_{x_{t+1},x_t}(i,j)" — this is our NOVEL criterion, not standard Granger causality. We should be clearer about what is novel vs standard. Standard Granger causality uses autoregressive models; ours uses a simple covariance comparison.

## PAGE 3: Algorithm, Figure 1

### Algorithm 1
- GOOD: Clear pseudocode
- MINOR: Line 9 uses Σ^† (pseudoinverse) — should note this is because Σ may be rank-deficient from partial measurement

### Figure 1 (Problem Schematic)
- GOOD: Clear network diagram with color coding
- ISSUE: The right panel (covariance accumulation) is somewhat generic — could be more informative if it showed actual partial matrices with NaN/missing values filling in

## PAGE 4: Experiments Setup, E1, Algorithm box

### Section 4.1 (Experimental Setup)
- ISSUE: "modeling small brain circuits" but then describes random directed graphs — a reviewer might ask "how is a random graph a model of a brain circuit?" Should mention that random graphs with spectral radius constraint and sparse connectivity capture key structural features of small circuits.
- ISSUE: Figure numbering is wrong! The pipeline is labeled Figure 2, scaling is Figure 3, granger is Figure 4, stim is Figure 5, sparsity is Figure 6, nonlinearity is Figure 7, dynamics is Figure 8. But in the text: "Figure~\ref{fig:scaling}" etc. The REFERENCES are correct (they use labels) but the CAPTIONS in the text sometimes refer to wrong figure numbers because the pipeline figure was inserted before the experiments section.

### Table 1 (E1 results)
- GOOD: Clean, clear improvement numbers
- ISSUE: The "Improvement" column shows Granger improvement over Estimate, but a more informative metric would be improvement over Chance (which ranges 72-90%). Should either add this or clarify.

## PAGE 5-6: E4, E3, E2, E5

### Figure 3 (Scaling)
- ISSUE: The CI bands are VERY wide for N=8 and N=12, making the lines hard to distinguish. The figure would be clearer with just the median lines and error bars at data points rather than continuous shading.

### Figure 4 (Granger Refinement)
- GOOD: The 8-panel layout works well
- GOOD: Heatmaps now show actual good recovery (A vs C look similar!)
- ISSUE: Panel (H) ablation bar chart is very small — hard to read the labels and numbers

### Figure 5 (Stimulation Tradeoff)
- GOOD: The interaction effect is clearly visible
- ISSUE: Left panel schematic is not very informative — just two generic networks. Would be better to show actual stimulation arrows of different thickness.
- ISSUE: The 100% measured line at σ=0 goes off the top of the chart (error >10⁶) but this isn't noted anywhere.

### Figure 6 (Measurement Sparsity)
- GOOD: Clear improvement with measurement
- ISSUE: The schematic (left panel) shows ring networks, not the actual random topologies used in experiments

### Figure 7 (Nonlinearity)
- GOOD: Log scale makes the comparison much clearer than before!
- ISSUE: The dots for identity and sigmoid are scattered over 3 orders of magnitude — this suggests massive variance across topologies. Should discuss why some topologies give error >100.

## PAGE 7: Related Work

### Related Work Section
- GOOD: Well-organized into 4 paragraphs with proper citations
- ISSUE: No citation for "the RESCUME method" — oh wait, this was already removed. Good.
- ISSUE: The related work doesn't mention matrix completion methods (e.g., Candès & Recht 2009) which are directly relevant to our partial observation + covariance accumulation approach.
- ISSUE: No mention of VAR (vector autoregression) models, which are the most standard approach to multivariate time series connectivity inference.

## PAGES 8-10: Discussion

### Discussion Paragraphs
- GOOD: "Error decomposition: CPG correlation dominates" — this is an honest, important finding
- GOOD: "Implicit regularization" explanation is clear
- ISSUE: The oracle crossover analysis says N=12, T=900 but earlier version said N=30, T=1000. Need to verify these match the actual E6 data.
- ISSUE: "Limitations" paragraph is only 2 sentences long. Should be expanded to discuss: (a) synthetic data only, (b) Gaussian assumption for Price's theorem, (c) no comparison with GLM/VAR baselines, (d) small network sizes only, (e) non-negative weights constraint may not hold for all circuits.

### Figure 8 (Dynamics Analysis)
- GOOD: Beautiful 9-panel figure, very informative
- ISSUE: Panel (D) phase portrait — the trajectory looks noisy, not structured. For "interesting dynamics like real biological networks" we'd want to see a clearer limit cycle or attractor structure.
- ISSUE: Panel (G) variance bars — the bars are very small and hard to read. CPG nodes should be more visually distinct.
- ISSUE: Panel (I) scatter — looks excellent! r=0.90 is a strong result. This should be highlighted more prominently in the paper.

## PAGE 11-12: References, Conclusion

### Conclusion
- GOOD: Concise, hits main points
- ISSUE: Only 4 sentences. Could be slightly expanded to mention the CPG detection finding and the r=0.90 correlation.

### References
- 21 references, all appear to be correctly formatted
- All verified as real papers in the previous audit

## PAGE 13: Appendix

### Appendix A.1 (Price's Theorem)
- GOOD: Clean derivation
- ISSUE: States "mismatch approaches W·(-I) = -W" — this should be clarified as "the mismatch term E1 approaches -W, meaning the estimator degrades to Ŵ → 0"

### Appendix A.2 (Identifiability)
- GOOD: Clear theorem/proof structure
- MINOR: Could add a remark about what happens when some pairs are observed many times (the estimate improves with √n_ij)

### Appendix A.3 (Oracle Analysis)
- GOOD: Crossover condition is mathematically precise
- ISSUE: Uses ε (noise) term that doesn't appear in our model. Should clarify this refers to finite-sample estimation error.

---

## PRIORITY FIXES (ordered by importance)

1. **PAPER IS TOO LONG** (13 pages). For a workshop: cut to 6 pages + appendix. Move E2, E5 to appendix. Keep E1, E3, E4 in main text.
2. **Fix Figure 5 caption** — says N=12, T=900 but E3 data is N=12 (confirmed from code). Verify the numbers in the caption match what's plotted.
3. **Observation noise ε_t** — either add it to simulations or remove from Eq (2)
4. **Candès 2011 citation** — replace with matrix completion reference or remove
5. **Strogatz citation** — replace with RNN reference
6. **Add forward reference** at Eq (3) about the independence assumption being revisited
7. **Expand Limitations** paragraph
8. **Highlight r=0.90** result more prominently
9. **Fix left-panel schematics** in F5 and F6 to be more informative
10. **Add VAR baseline discussion** to Related Work
