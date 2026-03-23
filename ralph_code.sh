#!/bin/bash
# RALPH Code Loop — experiments, notebooks, code quality
set -euo pipefail
unset ANTHROPIC_API_KEY 2>/dev/null || true

MAX_ITER=${1:-15}
TIME_BUDGET_HOURS=${2:-6}
TIME_BUDGET_SECS=$((TIME_BUDGET_HOURS * 3600))
START_TIME=$(date +%s)
LOG_FILE="ralph_code_log.jsonl"
cd "$(dirname "$0")"

echo "============================================="
echo "  RALPH Code Loop — Sparse Matrix Recovery"
echo "  Max: $MAX_ITER iters, ${TIME_BUDGET_HOURS}h"
echo "  Started: $(date)"
echo "============================================="

for i in $(seq 1 "$MAX_ITER"); do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    REMAINING=$(( TIME_BUDGET_SECS - ELAPSED ))
    [ "$REMAINING" -le 0 ] && echo "[RALPH-CODE] Time up" && break
    ELAPSED_MIN=$(( ELAPSED / 60 ))
    REMAINING_MIN=$(( REMAINING / 60 ))

    echo ""
    echo "===== CODE Iteration $i / $MAX_ITER  (${ELAPSED_MIN}m elapsed, ${REMAINING_MIN}m remaining) ====="

    OUTPUT=$(claude --print --dangerously-skip-permissions --max-turns 30 -p "You are RALPH Code Loop iteration $i of $MAX_ITER for sparse_matrix_recovery.
Time: ${ELAPSED_MIN}m elapsed, ${REMAINING_MIN}m remaining.

Read RALPH_code.md for your mission and success criteria.

YOUR JOB: Make ONE improvement to the code/experiments/notebooks.

Key tools:
- Re-run experiments: python experiments/run_experiments.py --experiment E1 --seed 42
- Regenerate figures: python scripts/generate_all_figures.py
- Verify math with GPT-5.4: python tools/openai_math.py --model gpt-5.4 --task '...'
- Execute notebook: jupyter nbconvert --to notebook --execute notebooks/X.ipynb --output X.ipynb
- Citation check: python scripts/verify_citations.py

Rules:
- ONE change per iteration
- ONLY touch: experiments/, notebooks/, scripts/, tools/, RALPH_code.md
- Do NOT touch paper/ (other loop handles that)
- Prefix commits: code: [description]
- If ALL criteria met: RALPH_STOP: all criteria met
- You CAN edit RALPH_code.md or tools if needed (self-improvement)
" 2>&1) || true

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"iteration\": $i, \"timestamp\": \"$TIMESTAMP\", \"loop\": \"code\"}" >> "$LOG_FILE"

    if echo "$OUTPUT" | grep -q "RALPH_STOP:"; then
        echo "[RALPH-CODE] $(echo "$OUTPUT" | grep 'RALPH_STOP:' | head -1)"
        break
    fi
    echo "[RALPH-CODE] Iteration $i complete"
done

echo "============================================="
echo "  RALPH Code Loop finished ($i iterations)"
echo "============================================="
