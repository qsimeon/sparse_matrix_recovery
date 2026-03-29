#!/bin/bash
#==============================================================================
# launch_E1_scaling.sh — Run E1 baseline scaling experiment
#
# E1 sweeps N ∈ {15, 30, 159, 300, 1074} × T ∈ {100, 250, 500, 750, 1000}
# = 25 configs × 10 reps = 250 tasks
#
# Each task runs ONE config for ONE rep (per-config-per-rep), because
# large N values (300, 1074) are expensive and need different resources.
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_E1_scaling.sh
#
# MONITOR:
#   squeue -u $USER -n sparse_E1
#   sacct -j <JOBID> --format=JobID,State,Elapsed,MaxRSS
#==============================================================================

#SBATCH --job-name=sparse_E1
#SBATCH --partition=mit_normal
#SBATCH --array=0-249            # 25 configs × 10 reps = 250 tasks
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G                # N=1074 needs ~8-12GB; 16GB for safety
#SBATCH --time=02:00:00          # N=1074 can take ~30min per config
#SBATCH --output=logs/E1_%A_%a.out
#SBATCH --error=logs/E1_%A_%a.err

cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/reps

source ~/.secrets 2>/dev/null
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

TASK_ID=${SLURM_ARRAY_TASK_ID}

# E1 has 25 configs (5 N × 5 T), 10 reps each
NUM_CONFIGS=25
NUM_REPS=10

CONFIG_IDX=$((TASK_ID / NUM_REPS))
REP_IDX=$((TASK_ID % NUM_REPS))

echo "=============================================="
echo "E1 Scaling Experiment"
echo "SLURM Task ID: ${TASK_ID}"
echo "Config:        ${CONFIG_IDX} / ${NUM_CONFIGS}"
echo "Repetition:    ${REP_IDX} / ${NUM_REPS}"
echo "Node:          $(hostname)"
echo "Time:          $(date)"
echo "=============================================="

uv run python experiments/run_single_rep.py \
    --experiment E1 \
    --config-idx "${CONFIG_IDX}" \
    --rep "${REP_IDX}" \
    --seed 42 \
    --num-sessions 50 \
    --output-dir experiments/results/reps

echo "Done! $(date)"
