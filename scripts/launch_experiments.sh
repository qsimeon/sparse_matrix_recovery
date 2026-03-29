#!/bin/bash
#==============================================================================
# launch_experiments.sh — Run E2-E7 experiments on the engaging cluster
#
# E2-E7 all use N=15 or N=30 (fast), so they share resource requirements.
# E1 scaling (N up to 1074) has its own script: launch_E1_scaling.sh
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_experiments.sh
#
# MONITOR:
#   squeue -u $USER
#   tail -f logs/experiments_<JOBID>_*.out
#==============================================================================

#SBATCH --job-name=sparse_E2-7
#SBATCH --partition=mit_normal
#SBATCH --array=0-59             # 6 experiments × 10 reps = 60 tasks
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G                 # Sufficient for N≤30
#SBATCH --time=00:30:00          # 30 min (generous for N≤30)
#SBATCH --output=logs/experiments_%A_%a.out
#SBATCH --error=logs/experiments_%A_%a.err

cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/reps

source ~/.secrets 2>/dev/null
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

TASK_ID=${SLURM_ARRAY_TASK_ID}

# 6 experiments (E2-E7) × 10 reps = 60 tasks
EXPERIMENTS=(E2 E3 E4 E5 E6 E7)
NUM_REPS=10

EXP_IDX=$((TASK_ID / NUM_REPS))
REP_IDX=$((TASK_ID % NUM_REPS))

EXPERIMENT=${EXPERIMENTS[$EXP_IDX]}

echo "=============================================="
echo "SLURM Task ID: ${TASK_ID}"
echo "Experiment:    ${EXPERIMENT}"
echo "Repetition:    ${REP_IDX} / ${NUM_REPS}"
echo "Node:          $(hostname)"
echo "Time:          $(date)"
echo "=============================================="

# Get number of configs for this experiment
NUM_CONFIGS=$(uv run python -c "
from experiments.run_single_rep import get_experiment_configs
print(len(get_experiment_configs('${EXPERIMENT}')))
")

echo "Running ${NUM_CONFIGS} configs for ${EXPERIMENT}, rep ${REP_IDX}"

for CONFIG_IDX in $(seq 0 $((NUM_CONFIGS - 1))); do
    echo "  Config ${CONFIG_IDX}/${NUM_CONFIGS}..."
    uv run python experiments/run_single_rep.py \
        --experiment "${EXPERIMENT}" \
        --config-idx "${CONFIG_IDX}" \
        --rep "${REP_IDX}" \
        --seed 42 \
        --num-sessions 50 \
        --output-dir experiments/results/reps
done

echo "Done! $(date)"
