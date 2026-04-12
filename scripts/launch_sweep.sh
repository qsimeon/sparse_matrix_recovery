#!/bin/bash
#==============================================================================
# launch_sweep.sh — Run the MEGA SWEEP on the engaging cluster
#
# THE MEGA EXPERIMENT:
#   Full 3^5 = 243 parameter grid, each with 50 reps = 12,150 total tasks.
#   This finds the OPTIMAL experimental design for connectivity recovery.
#
# PARAMETER GRID:
#   N            ∈ {8, 15, 30}        (network size)
#   T            ∈ {100, 500, 1000}   (recording duration)
#   meas_frac    ∈ {0.33, 0.66, 1.0}  (measurement fraction)
#   stim_gain    ∈ {0.0, 0.5, 1.0}    (stimulation intensity)
#   stim_frac    ∈ {0.33, 0.66, 1.0}  (stimulation coverage)
#
# TOTAL: 3×3×3×3×3 = 243 configs, each running 50 reps internally = 243 SLURM tasks
# RUNTIME: ~25 min/task (50 reps × ~30 sec) = ~100 CPU-hours total
#          With 100 parallel tasks: ~3 batches × 25 min = ~75 min wall time
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_sweep.sh
#
# RESULTS:
#   experiments/results/sweep/ contains individual JSON files
#   Run: uv run python experiments/aggregate_results.py --sweep to combine
#==============================================================================

#SBATCH --job-name=sparse_sweep
#SBATCH --partition=mit_normal
#SBATCH --array=0-242                  # 243 tasks: one per grid config
                                      # Each task runs ALL 50 reps internally
                                      # (stays well under 500-job cluster limit)

#SBATCH --cpus-per-task=4             # 4 cores per task for joblib parallelism

#SBATCH --mem=4G                      # 4 GB RAM per task
#SBATCH --time=01:00:00               # 1 hour max (50 reps × ~30s = ~25 min,
                                      # with margin for N=30 which is slower)

#SBATCH --output=logs/sweep_%A_%a.out
#SBATCH --error=logs/sweep_%A_%a.err

# ── Environment ──────────────────────────────────────────────────────────────
cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/sweep

source ~/.secrets 2>/dev/null                 # Load WANDB_API_KEY etc.
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

# ── Decode Task ID into 5D Grid Coordinates ─────────────────────────────────
#
# SLURM_ARRAY_TASK_ID goes from 0 to 242 (one per grid config).
# Each task runs ALL 50 reps for its config internally.
#
# This keeps us under the 500-job cluster limit (243 tasks << 500)
# while still getting 50 reps per config.
#
# To decode the 5D grid index: use integer division and modulo,
# peeling off dimensions from right to left.
# Think: TASK_ID = N_idx * 81 + T_idx * 27 + meas_idx * 9 + stim_gain_idx * 3 + stim_frac_idx

TASK_ID=${SLURM_ARRAY_TASK_ID}

# Grid values
N_VALUES=(8 15 30)
T_VALUES=(100 500 1000)
MEAS_VALUES=(0.33 0.66 1.0)
STIM_GAIN_VALUES=(0.0 0.5 1.0)
STIM_FRAC_VALUES=(0.33 0.66 1.0)
NUM_REPS=50

# Decode 5D: TASK_ID is 0-242, no rep dimension
REMAINDER=${TASK_ID}

STIM_FRAC_IDX=$((REMAINDER % 3))
REMAINDER=$((REMAINDER / 3))

STIM_GAIN_IDX=$((REMAINDER % 3))
REMAINDER=$((REMAINDER / 3))

MEAS_IDX=$((REMAINDER % 3))
REMAINDER=$((REMAINDER / 3))

T_IDX=$((REMAINDER % 3))
N_IDX=$((REMAINDER / 3))

# Look up actual values
N=${N_VALUES[$N_IDX]}
T=${T_VALUES[$T_IDX]}
MEAS_FRAC=${MEAS_VALUES[$MEAS_IDX]}
STIM_GAIN=${STIM_GAIN_VALUES[$STIM_GAIN_IDX]}
STIM_FRAC=${STIM_FRAC_VALUES[$STIM_FRAC_IDX]}

# Compute derived params
NUM_MEASURED=$(python3 -c "print(max(2, int(${MEAS_FRAC} * ${N})))")
NUM_STIMULATED=$(python3 -c "print(max(0, int(${STIM_FRAC} * ${N})))")
NUM_CPGS=$(python3 -c "print(max(1, int(0.33 * ${N})))")

echo "=============================================="
echo "MEGA SWEEP — Config ${TASK_ID} / 242 (${NUM_REPS} reps each)"
echo "  N=${N}, T=${T}"
echo "  meas_frac=${MEAS_FRAC} (${NUM_MEASURED} neurons)"
echo "  stim_gain=${STIM_GAIN}"
echo "  stim_frac=${STIM_FRAC} (${NUM_STIMULATED} neurons)"
echo "  Node: $(hostname), CPUs: ${SLURM_CPUS_PER_TASK}"
echo "=============================================="

# ── Run all 50 reps for this config ──────────────────────────────────────────
for REP in $(seq 0 $((NUM_REPS - 1))); do
    echo "  Rep ${REP}/${NUM_REPS}..."
    uv run python experiments/run_single_rep.py \
        --num-nodes "${N}" \
        --max-timesteps "${T}" \
        --num-measured "${NUM_MEASURED}" \
        --num-stimulated "${NUM_STIMULATED}" \
        --stim-gain "${STIM_GAIN}" \
        --nonlinearity tanh \
        --rep "${REP}" \
        --seed 42 \
        --task-id "${TASK_ID}" \
        --output-dir experiments/results/sweep
done

echo "Done! All ${NUM_REPS} reps for config ${TASK_ID}. $(date)"
