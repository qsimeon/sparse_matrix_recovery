#!/bin/bash
#==============================================================================
# launch_experiments.sh — Run all E1-E7 experiments on the engaging cluster
#
# HOW IT WORKS:
#   1. This script is submitted to SLURM via: sbatch launch_experiments.sh
#   2. SLURM creates 350 copies (7 experiments × 50 reps)
#   3. Each copy gets a unique SLURM_ARRAY_TASK_ID (0-349)
#   4. We decode that ID into: which experiment + which repetition
#   5. Each copy runs ONE call to run_single_rep.py
#   6. Results are saved as individual JSON files
#   7. After all jobs finish, run aggregate_results.py to combine them
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_experiments.sh
#
# MONITOR:
#   squeue -u $USER                    # see your jobs
#   squeue -u $USER -t RUNNING | wc -l # count running
#   sacct -j <JOBID> --format=JobID,State,Elapsed  # job details
#   tail -f logs/experiments_<JOBID>_42.out         # watch one job
#
# CANCEL:
#   scancel <JOBID>        # cancel all array tasks
#   scancel <JOBID>_42     # cancel just task 42
#==============================================================================

# ── SLURM Configuration ─────────────────────────────────────────────────────
# These lines starting with #SBATCH are NOT comments — SLURM reads them!

#SBATCH --job-name=sparse_exp     # Name shown in squeue
#SBATCH --partition=mit_normal    # Which cluster partition (queue) to use
                                  # mit_normal: 12h limit, ~50 nodes, CPU-only
                                  # Our jobs are CPU-only (no GPU needed)

#SBATCH --array=0-349             # 350 tasks: 7 experiments × 50 reps
                                  # Each gets SLURM_ARRAY_TASK_ID ∈ {0..349}

#SBATCH --cpus-per-task=4         # Each task gets 4 CPU cores
                                  # joblib inside run_single_rep uses these
                                  # 4 is enough for 50 sessions in parallel

#SBATCH --mem=4G                  # 4 GB RAM per task (generous for N≤30)

#SBATCH --time=00:30:00           # 30 minutes max per task
                                  # One rep of one experiment takes ~5-30 sec
                                  # 30 min is very generous (safety margin)

#SBATCH --output=logs/experiments_%A_%a.out
                                  # %A = master job ID, %a = array task ID
                                  # So you get logs/experiments_12345_42.out
                                  # for task 42 of job 12345

#SBATCH --error=logs/experiments_%A_%a.err
                                  # Separate file for stderr (errors)

# ── Environment Setup ────────────────────────────────────────────────────────
# This runs on the compute node, not your login node.
# The compute node is a fresh environment — you need to set up everything.

cd ~/sparse_matrix_recovery       # Navigate to project directory
mkdir -p logs                     # Create logs directory if missing
mkdir -p experiments/results/reps # Create output directory

# Load Python environment
# uv run handles the virtual environment automatically
source ~/.secrets 2>/dev/null                 # Load WANDB_API_KEY etc.
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK  # Tell NumPy/BLAS to use our allocated cores
export JOBLIB_START_METHOD=fork               # Faster than spawn for joblib

# ── Decode the Array Task ID ────────────────────────────────────────────────
# SLURM_ARRAY_TASK_ID goes from 0 to 349.
# We need to convert this into (experiment, repetition).
#
# Layout:
#   Tasks   0-49:   E1 (9 configs × ... wait, E1 has 9 configs!)
#
# Actually, the mapping is more nuanced because experiments have different
# numbers of configs. Let's use a flat mapping:

TASK_ID=${SLURM_ARRAY_TASK_ID}

# Experiment config counts: E1=9, E2=1, E3=18, E4=5, E5=4, E6=7, E7=5 = 49 configs total
# With 50 reps each: 49 × 50 = 2450 total tasks
# But that's too many for a first run. Let's do 50 reps of each experiment
# where each "task" is one rep of one experiment (ignoring config sweep for now).

# Simple version: 7 experiments × 50 reps = 350 tasks
EXPERIMENTS=(E1 E2 E3 E4 E5 E6 E7)
NUM_REPS=50

EXP_IDX=$((TASK_ID / NUM_REPS))     # Integer division: 0-6
REP_IDX=$((TASK_ID % NUM_REPS))     # Remainder: 0-49

EXPERIMENT=${EXPERIMENTS[$EXP_IDX]}

echo "=============================================="
echo "SLURM Task ID: ${TASK_ID}"
echo "Experiment:    ${EXPERIMENT} (index ${EXP_IDX})"
echo "Repetition:    ${REP_IDX}"
echo "CPUs:          ${SLURM_CPUS_PER_TASK}"
echo "Node:          $(hostname)"
echo "Time:          $(date)"
echo "=============================================="

# ── Run the Experiment ───────────────────────────────────────────────────────
# For experiments with multiple configs (E1 has 9, E3 has 18, etc.),
# we run ALL configs for this rep in one task.
# This is a tradeoff: fewer SLURM tasks vs. longer per-task runtime.

# Get the number of configs for this experiment
NUM_CONFIGS=$(uv run python -c "
from experiments.run_single_rep import get_experiment_configs
configs = get_experiment_configs('${EXPERIMENT}')
print(len(configs))
")

echo "Running ${NUM_CONFIGS} configs for ${EXPERIMENT}, rep ${REP_IDX}"

for CONFIG_IDX in $(seq 0 $((NUM_CONFIGS - 1))); do
    echo "  Config ${CONFIG_IDX}/${NUM_CONFIGS}..."
    uv run python experiments/run_single_rep.py \
        --experiment "${EXPERIMENT}" \
        --config-idx "${CONFIG_IDX}" \
        --rep "${REP_IDX}" \
        --seed 42 \
        --output-dir experiments/results/reps
done

echo "Done! $(date)"
