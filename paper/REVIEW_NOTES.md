# Paper Review Notes — Iteration 29 (RALPH iter 2)
> Reviewer: Claude Opus 4.6
> Date: 2026-03-23

## Changes This Iteration

### Fixed incorrect E6 oracle crossover numbers in Discussion
The "Oracle crossover analysis" paragraph cited wrong ratios:
- **Before**: "at σ=0.5 the oracle is 3.7× worse, while at σ=5 it is 1.5× worse"
- **After**: "at zero stimulation the oracle is 4.0× worse, at σ=0.5 it is 2.6× worse, and the gap narrows to 1.4–1.6× for σ ≥ 1"
- **Verification**: All numbers re-derived from `E6_oracle_crossover.json` median `estimate_distance` vs `oracle_distance`
- Full data: σ=0→4.0×, σ=0.10→~1.0× (tied), σ=0.25→1.9×, σ=0.5→2.6×, σ=1→1.6×, σ=2→1.4×, σ=5→1.6×

### Verified from this iteration
- [x] E7 numbers match JSON data: 0.244 (1 sensor), 0.128 (2 sensors), plateaus ~0.10 (4+ sensors)
- [x] All \ref and \label links cross-checked — no broken refs
- [x] E6 numbers now match JSON data (fixed above)

### Still Valid from Previous Reviews
- Table 1: all 6 rows match fresh JSON data
- E4 ablation numbers: match
- 19/19 citations verified
- All 9 figures from fresh data (2026-03-22)
- GPT-5.4 math verification: all 5 claims correct
- Section 2.1 fully motivates design choices
- E7 Discussion paragraph integrates sensor coverage findings

## Remaining Items to Check
- [ ] E6 has no subsection in Experiments (only in Discussion) — Table 1 lists it but readers can't find it in Section 4
- [ ] Notebooks: do they include E7 sensor fraction demo?
- [ ] Narrative flow: re-read paper top-to-bottom for coherence
- [ ] Verify figures at print size / visual quality audit
- [ ] Conclusion is only one paragraph — may need strengthening
