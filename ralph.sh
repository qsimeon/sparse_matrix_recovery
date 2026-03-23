#!/bin/bash
# RALPH Loop — Research Agent Loop for Progressive Hypotheses
# Calls Claude Code repeatedly to iterate on the paper until done.
#
# Usage: ./ralph.sh [max_iterations] [time_budget_hours]
# Example: ./ralph.sh 20 8    # 20 iterations, 8 hour budget
#          ./ralph.sh 10 4    # 10 iterations, 4 hours

set -euo pipefail

# Use Max subscription (OAuth) instead of API key credits
unset ANTHROPIC_API_KEY 2>/dev/null || true

MAX_ITER=${1:-20}
TIME_BUDGET_HOURS=${2:-8}
TIME_BUDGET_SECS=$((TIME_BUDGET_HOURS * 3600))
START_TIME=$(date +%s)
LOG_FILE="ralph_log.jsonl"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

echo "============================================="
echo "  RALPH Loop — Sparse Matrix Recovery Paper"
echo "  Max iterations: $MAX_ITER"
echo "  Time budget: ${TIME_BUDGET_HOURS}h"
echo "  Log: $LOG_FILE"
echo "  Started: $(date)"
echo "============================================="

for i in $(seq 1 "$MAX_ITER"); do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    REMAINING=$(( TIME_BUDGET_SECS - ELAPSED ))

    if [ "$REMAINING" -le 0 ]; then
        echo "[RALPH] Time budget exhausted after $i iterations"
        break
    fi

    ELAPSED_MIN=$(( ELAPSED / 60 ))
    REMAINING_MIN=$(( REMAINING / 60 ))

    echo ""
    echo "===== RALPH Iteration $i / $MAX_ITER  (${ELAPSED_MIN}m elapsed, ${REMAINING_MIN}m remaining) ====="

    PROMPT="You are running as part of a RALPH (Research Agent Loop for Progressive Hypotheses) autonomous loop.

ITERATION: $i of $MAX_ITER
ELAPSED: ${ELAPSED_MIN} minutes
REMAINING: ${REMAINING_MIN} minutes

Read RALPH.md for your mission and success criteria.
Read paper/REVIEW_NOTES.md for known issues.
Read tasks/todo.md for the prioritized task list.

YOUR JOB THIS ITERATION:
1. Identify the SINGLE weakest aspect of the paper/repo right now
2. Make ONE focused improvement (not five things at once)
3. VERIFY your change is correct (re-read what you wrote, check numbers, look at figures)
4. Update paper/REVIEW_NOTES.md with what you did and what's still needed
5. Commit with a descriptive message

RULES:
- Make ONE change per iteration. Small, testable, verifiable.
- Actually READ your output. If a figure looks bad, fix it. If a number is wrong, fix it.
- Use python tools/openai_math.py --model gpt-5.4 for math verification
- Use python scripts/verify_citations.py for citation checks
- Look at PDF figures with the Read tool to verify visual quality
- If you find nothing to improve after honest review, output RALPH_STOP: paper is ready

After making your change, output a JSON summary line:
{\"iteration\": $i, \"action\": \"what you did\", \"files_changed\": [\"list\"], \"next_priority\": \"what to do next\"}

If you believe the paper is ready for submission, output:
RALPH_STOP: [reason]"

    # Run Claude Code with the prompt
    OUTPUT=$(claude --print --dangerously-skip-permissions --max-turns 30 -p "$PROMPT" 2>&1) || true

    # Log the iteration
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"iteration\": $i, \"timestamp\": \"$TIMESTAMP\", \"elapsed_min\": $ELAPSED_MIN}" >> "$LOG_FILE"

    # Check for stop signal
    if echo "$OUTPUT" | grep -q "RALPH_STOP:"; then
        STOP_REASON=$(echo "$OUTPUT" | grep "RALPH_STOP:" | head -1)
        echo "[RALPH] $STOP_REASON"
        echo "{\"iteration\": $i, \"stopped\": true, \"reason\": \"$STOP_REASON\"}" >> "$LOG_FILE"
        break
    fi

    echo "[RALPH] Iteration $i complete"
done

echo ""
echo "============================================="
echo "  RALPH Loop finished"
echo "  Total iterations: $i"
echo "  Total time: $(( ($(date +%s) - START_TIME) / 60 )) minutes"
echo "  Log: $LOG_FILE"
echo "  Commits: $(git log --oneline -5)"
echo "============================================="
