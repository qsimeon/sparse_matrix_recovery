#!/bin/bash
#==============================================================================
# launch_E1_scaling.sh — Run E1 baseline scaling experiment on SLURM cluster
#
# E1 sweeps N ∈ {15, 159, 300} × T ∈ {100, 350, 1000}
# = 9 configs × 10 reps = 90 tasks
#
# Each task runs ONE config for ONE rep (per-config-per-rep).
# N=300 jobs are memory-intensive: ~8GB each.
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_E1_scaling.sh
#
# MONITOR:
#   squeue -u $USER -n sparse_E1
#   sacct -j <JOBID> --format=JobID,State,Elapsed,MaxRSS
#
# After all tasks finish, aggregate results:
#   uv run python experiments/aggregate_results.py \
#       --experiment E1 --reps-dir experiments/results/reps \
#       --output experiments/results/E1_baseline.json
#==============================================================================

#SBATCH --job-name=sparse_E1
#SBATCH --partition=mit_normal
#SBATCH --array=0-89             # 9 configs × 10 reps = 90 tasks
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G                 # N=300 needs ~4-6GB; 8GB for safety
#SBATCH --time=01:00:00          # N=300, T=1000 takes ~15-20 min per rep
#SBATCH --output=logs/E1_%A_%a.out
#SBATCH --error=logs/E1_%A_%a.err

cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/reps

source ~/.secrets 2>/dev/null
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

TASK_ID=${SLURM_ARRAY_TASK_ID}

# E1 has 9 configs (3 N × 3 T), 10 reps each
NUM_CONFIGS=9
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
