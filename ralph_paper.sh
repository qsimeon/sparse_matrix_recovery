#!/bin/bash
# RALPH Paper Loop — paper quality, poster, lightning talk
set -euo pipefail
unset ANTHROPIC_API_KEY 2>/dev/null || true

MAX_ITER=${1:-15}
TIME_BUDGET_HOURS=${2:-6}
TIME_BUDGET_SECS=$((TIME_BUDGET_HOURS * 3600))
START_TIME=$(date +%s)
LOG_FILE="ralph_paper_log.jsonl"
cd "$(dirname "$0")"

echo "============================================="
echo "  RALPH Paper Loop — Sparse Matrix Recovery"
echo "  Max: $MAX_ITER iters, ${TIME_BUDGET_HOURS}h"
echo "  Started: $(date)"
echo "============================================="

for i in $(seq 1 "$MAX_ITER"); do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    REMAINING=$(( TIME_BUDGET_SECS - ELAPSED ))
    [ "$REMAINING" -le 0 ] && echo "[RALPH-PAPER] Time up" && break
    ELAPSED_MIN=$(( ELAPSED / 60 ))
    REMAINING_MIN=$(( REMAINING / 60 ))

    echo ""
    echo "===== PAPER Iteration $i / $MAX_ITER  (${ELAPSED_MIN}m elapsed, ${REMAINING_MIN}m remaining) ====="

    OUTPUT=$(claude --print --dangerously-skip-permissions --max-turns 30 -p "You are RALPH Paper Loop iteration $i of $MAX_ITER for sparse_matrix_recovery.
Time: ${ELAPSED_MIN}m elapsed, ${REMAINING_MIN}m remaining.

Read RALPH_paper.md for your mission and success criteria.

YOUR JOB: Make ONE improvement to the paper, OR create the poster/talk if the paper is solid.

Key tools:
- Compile PDF: cd paper && pdflatex -interaction=nonstopmode main.tex (or tectonic main.tex)
- Read the PDF: use the Read tool on paper/sparse_matrix_recovery.pdf
- Verify math with GPT-5.4: python tools/openai_math.py --model gpt-5.4 --task '...'
- Verify citations with Gemini: python tools/gemini_research.py --query '...'
- Check data: python -c 'import json; ...' on experiments/results/*.json
- Citation integrity: python scripts/verify_citations.py

IMPORTANT FACTS:
- SPARC = 'Sparse Predictive Activity through Recombinase Competition' (if referenced)
- Route to best model: GPT-5.4 for math, Gemini for research/citations, Claude for writing

Rules:
- ONE change per iteration
- ONLY touch: paper/, tools/, RALPH_paper.md
- Do NOT touch experiments/ or notebooks/ (other loop handles that)
- Prefix commits: paper: [description]
- After paper is solid, create poster (paper/poster.tex) and lightning talk (paper/lightning_talk.md)
- If ALL criteria met: RALPH_STOP: all criteria met
- You CAN edit RALPH_paper.md or tools if needed (self-improvement)
" 2>&1) || true

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"iteration\": $i, \"timestamp\": \"$TIMESTAMP\", \"loop\": \"paper\"}" >> "$LOG_FILE"

    if echo "$OUTPUT" | grep -q "RALPH_STOP:"; then
        echo "[RALPH-PAPER] $(echo "$OUTPUT" | grep 'RALPH_STOP:' | head -1)"
        break
    fi
    echo "[RALPH-PAPER] Iteration $i complete"
done

echo "============================================="
echo "  RALPH Paper Loop finished ($i iterations)"
echo "============================================="
