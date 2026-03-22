# Project Roadmap — Sparse Matrix Recovery
> Generated: 2026-03-22 (resituate recovery)
> Context: Paper is 90% done. Missing: E7 figure, experimental design framing, sensor discussion.

## Immediate (blocks paper submission)
- [ ] Generate F9 figure for E7 sensor fraction results (S)
- [ ] Add F9 \includegraphics to paper Section 4.7 (S)
- [ ] Add experimental design summary table to Section 4.1 listing all 7 experiments with their swept/fixed variables (M)
- [ ] Update progress.json to iteration 28 and add E7 to history (S)
- [ ] Update research_prd.json with E7/H7 (S)

## Core Improvements (strengthen paper for review)
- [ ] Add sensor fraction discussion paragraph to Discussion section (M)
- [ ] Expand Section 4.1 "Experimental Setup" with proper framing of the 5 experimental knobs (measurement, sensor count, stim gain, CPG density, recording duration) (M)
- [ ] Add node role explanation: each node is characterized by {CPG?, sensor?, measured?} — these are NOT mutually exclusive (S)
- [ ] Consider E8: CPG fraction sweep (L) — deferred unless quick win

## Polish
- [ ] Regenerate primary notebook with E7 sensor fraction demo cell (M)
- [ ] Final consistency check: all numbers, figures, citations (M)
- [ ] Compile PDF in Overleaf and verify all 9+ figures render (S)
- [ ] Commit and push final version (S)

## Kill / Defer
- paper/figures/diagrams/ — 5 supplementary diagrams that aren't referenced in paper. Keep for now but don't add to paper.
- E8 (CPG fraction sweep) — interesting but not essential for first submission
- tools/gemini_research.py — useful for lit review but not needed for paper completion
