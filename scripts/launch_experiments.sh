#!/bin/bash
#==============================================================================
# launch_experiments.sh — Unified SLURM launcher for ALL experiments (E1-E8)
#
# Design: one task = one (experiment, config_idx, rep_idx) triple.
# Flattened so every task does exactly one thing — no loops inside.
#
# Layout:
#   E1: 9 configs × 10 reps = 90 tasks   (IDs 0-89)
#   E2: 1 config  × 10 reps = 10 tasks   (IDs 90-99)
#   E3: 18 configs × 10 reps = 180 tasks (IDs 100-279)
#   E4: 5 configs × 10 reps = 50 tasks   (IDs 280-329)
#   E5: 4 configs × 10 reps = 40 tasks   (IDs 330-369)
#   E6: 7 configs × 10 reps = 70 tasks   (IDs 370-439)
#   E7: 3 configs × 10 reps = 30 tasks   (IDs 440-469)
#   E8: 5 configs × 10 reps = 50 tasks   (IDs 470-519)
#   Total: 520 tasks.
#
# Memory: 8GB per task (safe for E1 N=300; slight overallocation for others).
# Time:   1 hour per task (E1 N=300 T=1000 ≈ 20min; others finish in seconds).
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_experiments.sh
#
# MONITOR:
#   squeue -u $USER
#   tail -f logs/experiments_<JOBID>_*.out
#
# AFTER all tasks finish, aggregate and transfer:
#   uv run python experiments/aggregate_results.py \
#       --reps-dir experiments/results/reps --output-dir experiments/results
#==============================================================================

#SBATCH --job-name=sparse_all
#SBATCH --partition=mit_normal
#SBATCH --array=0-519
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/experiments_%A_%a.out
#SBATCH --error=logs/experiments_%A_%a.err

cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/reps

source ~/.secrets 2>/dev/null
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

TASK_ID=${SLURM_ARRAY_TASK_ID}
NUM_REPS=10

# Map flat TASK_ID to (experiment, config_idx, rep_idx).
# Each experiment claims a contiguous range: E{k}_START .. E{k}_START + NUM_CONFIGS*NUM_REPS - 1.
# Within its range: rep = TASK % NUM_REPS; config_idx = (TASK / NUM_REPS).
mapfile -t BOUNDARIES < <(uv run python - <<'PY'
from experiments.run_single_rep import get_experiment_configs
start = 0
for exp in ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]:
    n_cfg = len(get_experiment_configs(exp))
    end = start + n_cfg * 10 - 1
    print(f"{exp} {start} {end} {n_cfg}")
    start = end + 1
PY
)

EXPERIMENT=""
CONFIG_IDX=""
REP_IDX=""
for line in "${BOUNDARIES[@]}"; do
    read -r exp start end n_cfg <<< "$line"
    if [ "$TASK_ID" -ge "$start" ] && [ "$TASK_ID" -le "$end" ]; then
        EXPERIMENT="$exp"
        LOCAL_ID=$((TASK_ID - start))
        CONFIG_IDX=$((LOCAL_ID / NUM_REPS))
        REP_IDX=$((LOCAL_ID % NUM_REPS))
        break
    fi
done

if [ -z "$EXPERIMENT" ]; then
    echo "ERROR: TASK_ID=$TASK_ID out of range"
    exit 1
fi

echo "=============================================="
echo "SLURM Task ID: ${TASK_ID}"
echo "Experiment:    ${EXPERIMENT}"
echo "Config:        ${CONFIG_IDX}"
echo "Rep:           ${REP_IDX} / ${NUM_REPS}"
echo "Node:          $(hostname)"
echo "Time:          $(date)"
echo "=============================================="

uv run python experiments/run_single_rep.py \
    --experiment "${EXPERIMENT}" \
    --config-idx "${CONFIG_IDX}" \
    --rep "${REP_IDX}" \
    --seed 42 \
    --num-sessions 50 \
    --output-dir experiments/results/reps

echo "Done! $(date)"
