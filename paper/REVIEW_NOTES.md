# Paper Review Notes — Iteration 28 (RALPH iter 1)
> Reviewer: Claude Opus 4.6 + GPT-5.4 (math verification)
> Date: 2026-03-22

## Changes This Iteration

### Added sensor coverage Discussion paragraph
The Discussion section was missing any integration of the E7 sensor fraction findings — a whole experiment with no Discussion paragraph. Added a new `\paragraph{Sensor coverage: a practical experimental knob.}` after "Connection to neuroscience experiments" that:
1. Synthesizes E3 (intensity) and E7 (coverage) as complementary stimulation axes
2. Explains the rank vs. magnitude distinction
3. Gives a concrete practical recommendation: 3–4 sensors in a 12-neuron circuit suffices
4. Defines the practical operating regime: moderate gain + modest sensor subset

### Still Valid from Previous Reviews
- Table 1: all 6 rows match fresh JSON data
- E4 ablation numbers: match
- 19/19 citations verified
- All 8+ figures from fresh data (2026-03-22)
- GPT-5.4 math verification: all 5 claims correct
- Section 2.1 fully motivates design choices

## Remaining Items to Check
- [ ] Verify the new paragraph's numbers match E7 data (8% single sensor, halving at 17%, plateau at 33%)
- [ ] Check all \ref links still resolve (no broken refs)
- [ ] Notebooks: do they include E7 sensor fraction demo?
- [ ] Narrative flow: re-read paper top-to-bottom for coherence
- [ ] Verify figures at print size / visual quality audit
