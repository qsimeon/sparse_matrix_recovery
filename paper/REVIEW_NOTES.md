# Paper Review Notes — Iteration 38 (RALPH iter 11)
> Reviewer: Claude Opus 4.6
> Date: 2026-03-23

## Changes This Iteration

### Strengthened Abstract: added concrete numbers and CPG dominance finding

**Problem**: The abstract was the weakest part of an otherwise polished paper. It lacked concrete performance numbers (r=0.91, 82% improvement over chance) and omitted the CPG dominance finding — one of the paper's three key results highlighted in the Conclusion. Reviewers read the abstract first, and missing headline numbers weakens the first impression. The Conclusion enumerates three key findings (control-estimation tradeoff, implicit regularization, CPG dominance), but the abstract only mentioned the first two.

**Fix**: Rewrote the abstract (6 sentences, ~160 words) to include:
1. Concrete performance: "$r = 0.91$ correlation with true connectivity and $82\%$ improvement over chance using only $67\%$ neuron coverage per session"
2. Named the James-Stein connection explicitly: "a concrete instance of James--Stein shrinkage"
3. Added CPG dominance finding: "correlation from central pattern generators, not model mismatch, is the dominant error bottleneck ($3.4\times$ larger)"
4. Tightened method description by combining method + accumulation into one sentence

**Verification**: All four numbers verified against paper data:
- r = 0.91: fig8 panel I Pearson correlation (line 529)
- 82%: (0.533 − 0.095) / 0.533 = 82.2% (line 330, E4 data)
- 67%: 8/12 baseline measurement fraction (line 264)
- 3.4×: E2/E1 = 0.276/0.081 = 3.41 (line 513, fig8 panel H)

**Files changed**: `paper/main.tex` (lines 34-41, abstract)

### Previous iteration: Strengthened Related Work: added matrix completion paragraph

**Problem**: The paper's title says "Sparse Matrix Recovery" but the Related Work section (4 paragraphs) did not cite the foundational matrix completion literature. This is the most directly relevant mathematical framework — recovering a matrix from partial observations — and its omission would be immediately noticed by a reviewer. The compressed sensing paragraph cites Candès et al. 2006 for sparse *vector* recovery, but that's a different problem. Matrix completion (Candès & Recht 2009) is closer to our setting.

**Fix**: Added a 5th paragraph to Related Work, positioned between "Compressed sensing" and "Systems identification":
- Introduces matrix completion (Candès & Recht 2009) as recovering a matrix from partial entries under low-rank assumptions
- States the $O(rN \log^2 N)$ sample complexity for context
- Explicitly differentiates our setting: sparse (not low-rank) matrix, observations are temporal covariance statistics (not direct entries)
- Draws connection: coupon-collector session coverage mirrors matrix completion sampling requirements

**Files changed**: `paper/main.tex` (lines 447-451), `paper/references.bib` (added `candes2009exact`)

**Verification**:
- Citation key `candes2009exact` matches bib entry with correct metadata (FoCM, vol 9, pp 717-772, 2009)
- Paragraph correctly distinguishes our problem (sparse matrix, covariance observations) from standard matrix completion (low-rank matrix, direct entries)
- Reference count: now 20 citations (was 19)

### Previous iteration: Fixed E5 factual error: sigmoid ranking and fig7 caption number

**Problem**: The E5 text (line 377) claimed "Sigmoid performs worst (error 0.14)" — but this is factually wrong. The data shows sigmoid (Granger error = 0.143) is actually *second-best*, performing better than identity (0.190) and ReLU (0.190). Claiming 0.14 is "worst" immediately after stating identity/ReLU are 0.19 is an obvious numerical contradiction that any reviewer would catch. Additionally, the fig7 caption reported tanh error as 0.094 but the actual median is 0.09464, which rounds to 0.095.

**Fixes applied**:

1. **E5 text** (line 377): Changed "Sigmoid performs worst (error $0.14$) due to its non-zero mean." → "Sigmoid achieves intermediate error ($0.14$): its boundedness helps conditioning relative to identity and ReLU, but its non-zero mean ($\phi(0) = 0.5$) biases the covariance estimate."
   - Corrects the factual ranking error: sigmoid is 2nd best (0.14), not worst
   - Explains *why* sigmoid is intermediate: bounded (helps vs identity/ReLU) but biased (hurts vs tanh)

2. **Fig7 caption** (line 383): Changed **0.094 → 0.095** for tanh recovery error
   - Actual median of 17 topologies: 0.09464 → rounds to 0.095
   - Now matches text (line 375) which already said 0.095

**Verification**: All E5 numbers verified against `E5_nonlinearity.json`:
- tanh: median estimate=0.100, median Granger=0.095 (0.09464)
- relu: median estimate=0.190, median Granger=0.190
- identity: median estimate=0.194, median Granger=0.190
- sigmoid: median estimate=0.152, median Granger=0.143
- Correct ranking: tanh (0.095) < sigmoid (0.143) < identity ≈ ReLU (0.190)

### Previous iteration: Added experiment ordering roadmap to Section 4.1

**Problem**: Table 1 lists experiments E1–E7 in numerical order, but the subsections present them in narrative order: E1, E4, E3, E2, E5, E6, E7. A reader expects E2 after E1 but instead encounters E4, which is disorienting. No text explained this deliberate reordering.

**Fix**: Added one sentence after Table 1 (before §4.2) explaining the narrative order:
> "The subsections below present experiments in narrative order rather than numerical order: we first establish baseline scaling (E1) and ablate method components (E4), then examine the key experimental design tradeoffs—stimulation intensity (E3) and measurement density (E2)—and finally test robustness to nonlinearity (E5), the oracle comparison (E6), and sensor coverage (E7)."

**Verification**: Confirmed the sentence matches the actual subsection ordering (E1→E4→E3→E2→E5→E6→E7) by grepping for `\subsection{.*E[0-9]}` in main.tex.

### Previous iteration: Added missing E6 (Oracle vs. Approximation) figure

**Problem**: E6 was the only experiment without a figure. All other experiments (E1-E5, E7) had dedicated figures, but E6 — one of the paper's three key findings (implicit regularization / James-Stein phenomenon) — was text-only. A reviewer would expect visual evidence for such a central claim.

**Fix**: Created `fig10_oracle_comparison.pdf` with two panels:
- **(A)** Recovery error vs. stimulation gain (log scale) for oracle, approximation, and Granger-refined estimators with bootstrap CIs and individual topology dots
- **(B)** Oracle penalty factor (ratio) showing the oracle is 1.0-4.0× worse across all σ

Added `\includegraphics` and full caption to §4.6 (E6 subsection) with `\label{fig:oracle}` and `\ref{fig:oracle}` in the text.

Also softened "outperforms at every" → "outperforms or matches at every" since at σ=0.1 the median ratio is 1.0× (oracle 1.000 vs. approx 1.006 — within noise).

**Verification**:
- Figure numbers match paper text: 4.0× at σ=0, 2.6× at σ=0.5, 1.4-1.6× for σ≥1 ✓
- Figure style matches other paper figures (same color palette, spines, grid, bootstrap CIs) ✓
- Cross-references: `\ref{fig:oracle}` in text, `\label{fig:oracle}` in figure ✓
- Script: `scripts/generate_fig10_oracle.py` for reproducibility ✓

### Previous iteration: Fixed E2 (Measurement Sparsity) numerical discrepancies in text and caption

**Problem**: The E2 section text and fig6 caption reported incorrect numbers for the 33% measurement condition. The text claimed raw estimate = 0.592 and Granger = 0.307 (48% improvement), but the actual data (E2_sparsity.json medians) gives 0.477 and 0.270 (43% improvement). These stale numbers likely came from a previous experimental run and were not updated when figures were regenerated on 2026-03-22. A reviewer cross-checking the figure against the text would immediately spot this — the blue dot at 33% is clearly around 0.48 in the figure, not 0.59.

**Fixes applied**:

1. **Section 4.5 text** (lines 359-360):
   - Raw estimate at 33%: **0.592 → 0.477** (actual median of 17 topologies)
   - Granger at 33%: **0.307 → 0.270** (actual median)
   - Improvement: **48% → 43%** (recalculated)
   - Granger at 100%: **0.094 → 0.095** (actual median = 0.0948)

2. **Fig6 caption** (line 366): Same corrections applied
   - **0.094 → 0.095**, **0.307 → 0.270**, **48% → 43%**, **0.592 → 0.477**

**Verification**: All corrected numbers verified against `E2_sparsity.json`:
- 33% measurement: median estimate_distance = 0.4768, median optimized_distance = 0.2700
- 100% measurement: median optimized_distance = 0.0948
- Improvement: (0.477 - 0.270) / 0.477 = 43.4%
- Figure fig6 visual inspection: blue dot at 33% ≈ 0.48, green square ≈ 0.27 — matches corrected values

### Previous iteration: Fixed numerical discrepancies between text/captions and figures/data (E4, fig8)

**Problem**: Several numbers in the paper text and fig8 caption did not match the actual figure data or the experiment JSON files. A reviewer cross-checking the figure labels against the caption would spot these inconsistencies.

**Fixes applied**:

1. **Granger improvement percentage** (lines 322, 460): Changed "~6%" → "~5%"
   - E4 data: per-topology mean improvement = 5.2%, median = 4.8%
   - The old "~6%" was generous rounding; "~5%" is accurate for both mean and median
   - Figure subtitle shows "2%" (single representative topology), median across 30 topologies is 3.2%, mean per-topology is 5.2%

2. **Fig8 caption error decomposition numbers** (line 511): Updated to match figure bar labels
   - E1 (model mismatch): 0.082 → **0.081** (matches figure bar)
   - E2 (CPG correlation): 0.272 → **0.276** (matches figure bar)
   - Total error: 0.100 → **0.097** (matches figure bar)

3. **Error ratio** (lines 496, 511, 544): Changed "3.3×" → "3.4×"
   - Old caption numbers: 0.272/0.082 = 3.32× ≈ 3.3× (internally consistent with wrong caption values)
   - Corrected: 0.276/0.081 = 3.41× ≈ 3.4× (matches actual figure)

**Verification**: All corrected numbers verified against:
- `E4_granger.json`: median estimate_distance=0.0981, median optimized_distance=0.0950
- Fig8 bar chart labels: E1=0.081, E2=0.276, Total=0.097

### Previous iteration: Strengthened Conclusion section (was single paragraph)
The Conclusion was just one paragraph summarizing the method with a throwaway future-work sentence. Expanded to three structured paragraphs:
1. **Method summary** with quantitative results (r=0.91, 82% over chance)
2. **Three key findings**: control-estimation tradeoff + optimal operating regime, implicit regularization (James-Stein), CPG dominance as error bottleneck
3. **Concrete future directions**: real C. elegans data, structured stimulation protocols, joint W+CPG estimation

### Previous iteration: Added missing E6 subsection to Experiments (Section 4)
Table 1 listed E6 (Oracle vs. Approximation) but there was no corresponding subsection in the Experiments section — readers would see E6 in the table and not find it. Added §4.7 "Oracle vs. Approximation (E6)" between E5 and E7 with:
- Experimental setup (σ sweep, 17 topologies)
- Key finding: approximation outperforms oracle at all σ, no crossover
- Cross-references to Discussion and Appendix A.3

### Previous iteration: Fixed incorrect E6 oracle crossover numbers in Discussion
- **Before**: "at σ=0.5 the oracle is 3.7× worse, while at σ=5 it is 1.5× worse"
- **After**: "at zero stimulation the oracle is 4.0× worse, at σ=0.5 it is 2.6× worse, and the gap narrows to 1.4–1.6× for σ ≥ 1"

### Verified (cumulative)
- [x] E7 numbers match JSON data: 0.244 (1 sensor), 0.128 (2 sensors), plateaus ~0.10 (4+ sensors)
- [x] All \ref and \label links cross-checked — no broken refs
- [x] E6 numbers now match JSON data
- [x] Table 1: all 7 rows match fresh JSON data
- [x] E4 ablation bar chart numbers: match JSON (0.533, 0.209, 0.134, 0.098, 0.095)
- [x] Fig8 caption numbers now match figure bars (0.081, 0.276, 0.097)
- [x] Granger improvement: ~5% matches data (mean 5.2%, median 4.8%)
- [x] 20/20 citations verified (added candes2009exact for matrix completion, iter 10)
- [x] All 10 figures from fresh data (2026-03-22/23): fig1-fig9 + fig10 (E6 oracle)
- [x] GPT-5.4 math verification: all 5 claims correct
- [x] Section 2.1 fully motivates design choices
- [x] E7 Discussion paragraph integrates sensor coverage findings
- [x] Figures visually inspected: fig1, fig3, fig4, fig5, fig8, fig9 — all publication quality
- [x] Figures visually inspected: fig2, fig6, fig7 — all publication quality (iter 6). All 9/9 complete.
- [x] Fig10 (E6 oracle) visually inspected — publication quality, numbers match text (iter 7)
- [x] E2 numbers match JSON data: 0.477 (raw at 33%), 0.270 (Granger at 33%), 0.095 (Granger at 100%), 43% improvement
- [x] E5 numbers now match JSON data: tanh=0.095, sigmoid=0.143, identity=0.190, ReLU=0.190; ranking corrected in text
- [x] E5 sigmoid ranking: correctly described as "intermediate" (2nd best), not "worst"

## Remaining Items to Check
- [ ] Notebooks: do they include E7 sensor fraction demo?
- [x] Related Work: was thin (4 paragraphs), missing matrix completion — **FIXED** iter 10: added matrix completion paragraph with Candès & Recht 2009
- [x] Narrative flow: structure is sound (iter 6); added experiment ordering roadmap to §4.1 (iter 8) explaining why subsections follow E1→E4→E3→E2→E5→E6→E7 order
- [x] Verify figures at print size / visual quality audit — **DONE**: all 9/9 figures inspected, all look good
- [x] Conclusion is only one paragraph — **FIXED** iter 4: expanded to 3 paragraphs
- [x] E6 has no subsection in Experiments — **FIXED** iter 3: added §4.7
- [x] Numerical discrepancies (E4, fig8) — **FIXED** iter 5
- [x] Numerical discrepancies (E2, fig6) — **FIXED** iter 6
- [x] Numerical discrepancies (E5, fig7) — **FIXED** iter 9: sigmoid ranking + tanh 0.094→0.095
