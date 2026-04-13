# RALPH.md — Sparse Matrix Recovery

## Project Goal
Produce a publication-ready arXiv preprint + reproducible codebase for a covariance-based method that recovers sparse neural connectivity matrices from partial multi-session recordings, with Granger-causality refinement.

---

## Deliverable
- **Primary**: `paper/main.tex` → compiled PDF (NeurIPS preprint format, 21 pages) on arXiv at `arXiv:2603.18497`
- **Secondary**: Reproducible experiment code (`experiments/core.py`, `run_experiments.py`), 9 publication figures, 3 notebooks, poster + lightning talk slides
- **Repo**: https://github.com/qsimeon/sparse_matrix_recovery (public)

---

## Audience
Systems/computational neuroscience researchers; ML community interested in structured estimation. Reviewers will expect rigorous empirical validation, correct citations, and reproducible code.

---

## Success Criteria
- [x] Every figure (9 total, fig1–fig9) visually inspected and publication-quality
- [x] Every numerical claim in paper matches corresponding JSON in `experiments/results/`
- [x] Paper compiles cleanly (no "??", no overfull hboxes that escape margin)
- [x] All citations valid (23 refs, all used)
- [x] No broken `\ref`, no undefined labels
- [x] Experiments E1–E8 re-run seed=42, results deterministic and locked
- [x] Paper uploaded to arXiv (arXiv:2603.18497)
- [ ] All 3 notebooks execute end-to-end without errors (post-import-fix unverified)
- [ ] README.md aligned with current state (figures renamed, 8 experiments, arXiv link)
- [ ] STATUS.md updated to reflect figure rename (was 10 figs → now 9 sequential figs)

---

## Design Philosophy
- **Simplicity over complexity**: the linear approximation wins over oracle because of implicit James–Stein regularization — lean into this as the central conceptual insight
- **Data integrity first**: never change verified numerical results; all claims locked to JSON files in `experiments/results/`
- **No speculative additions**: only add baselines or experiments reviewers will concretely ask for (Ridge-GLM and VAR baselines already added)
- **Code hygiene**: scripts should be clean enough that a reader can reproduce every figure from scratch with `uv run python experiments/run_experiments.py --experiment all --seed 42`

---

## Constraints
- **Do NOT change verified numerical results** — all E1–E8 numbers locked (seed=42, run 2026-04-11/12)
- **Do NOT re-run experiments** without strong reason — they are deterministic and verified
- **Do NOT add new experiments** beyond what's already in E1–E8 without user approval
- **Do NOT modify paper prose** arbitrarily — every word has been reviewed 30+ iterations
- Figures are **sequential fig1–fig9** (renamed in commit f676e12); STATUS.md is stale on this
- Python environment: `conda activate work_env` + `uv run`; notebooks use same env

---

## Current State: ~96%

### What's done (locked)
- Paper: 21 pages, all sections complete, compiled clean, on arXiv
- Experiments: E1–E8 all verified, JSON results locked, seed=42 deterministic
- Figures: 9 PDFs (fig1–fig9), all referenced, no orphans
- Baselines: Ridge-GLM and VAR baselines added to E2 comparison
- Citations: 23 refs, all used and correct
- Poster + presentation: compiled, numbers current
- Repo hygiene: clean, public, arXiv citation in README

### What's incomplete (agent can fix)
- [ ] **Notebooks not executed end-to-end** — import fixes applied but untested
  - `qsimeon_SparseMatrixRecovery.ipynb` (primary, 23 cells)
  - `complete_analysis.ipynb` (ablation/oracle teaching notebook)
  - `explore_dynamics.ipynb` (CPG dynamics + abs vs ReLU)
- [ ] **STATUS.md stale** — lists old fig names (fig3_scaling→fig2_scaling, etc., 10 figs→9)
- [ ] **README.md may have stale references** — quick audit needed (figure count, experiment table)

### What requires human
- Final author read-through of compiled PDF
- arXiv revision submission (if any changes needed post-review)
- SDSCon presentation delivery

---

## Human Actions Needed
1. **Read compiled `paper/main.pdf`** — 21-page final read for scientific clarity and flow
2. **Submit arXiv revision** if any post-review fixes are made
3. **Run notebooks interactively** if output cells need visual verification (agent can run headlessly)

---

## Codex Delegation Guide

**Delegate to `/codex:rescue` when:**
- Implementing new analysis or experiment code
- Debugging failing Python scripts or notebook execution errors
- Making structural changes to `experiments/core.py` or `analysis.py`
- Fixing LaTeX compilation errors that require understanding complex TeX macros
- Running the notebooks programmatically and fixing any import/runtime errors

**Handle directly (this agent) when:**
- README.md / STATUS.md audits and prose edits
- LaTeX prose edits (paper text, captions, abstract)
- `RALPH.md` / `REVIEW_NOTES.md` updates
- Git commits and pushes
- Checking figure references, citation integrity, cross-ref audits

**DO NOT delegate:**
- Changing locked numerical results
- Adding new experiments without user approval
- Architectural decisions about the core algorithm

---

## Key File Map

| File | Role |
|------|------|
| `experiments/core.py` | All algorithm logic (network gen, CPG sim, estimation, Granger) |
| `experiments/run_experiments.py` | CLI to run E1–E8 |
| `experiments/analysis.py` | Figure generation (all 9 figs) |
| `experiments/results/` | Locked JSON outputs (E1–E8) |
| `paper/main.tex` | The paper (21 pp, NeurIPS preprint) |
| `paper/references.bib` | 23 citations |
| `paper/figures/` | fig1–fig9 PDFs |
| `notebooks/qsimeon_SparseMatrixRecovery.ipynb` | Primary walkthrough notebook |
| `scripts/generate_all_figures.py` | Regenerate figures from JSON |
| `STATUS.md` | Project state (partially stale — see above) |
| `DEEP_DIVE.md` | Full technical reference (comprehensive, accurate) |
