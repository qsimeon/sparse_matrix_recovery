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
# TOTAL: 3×3×3×3×3 = 243 configs × 50 reps = 12,150 tasks
# RUNTIME: ~30 sec/task × 12,150 = ~100 CPU-hours
#          With 96 parallel tasks (2 nodes × 48 cores): ~2 hours wall time
#
# USAGE:
#   cd ~/sparse_matrix_recovery
#   sbatch scripts/launch_sweep.sh
#
# RESULTS:
#   experiments/results/sweep/ contains 12,150 JSON files
#   Run: python experiments/aggregate_sweep.py to combine into one file
#==============================================================================

#SBATCH --job-name=sparse_sweep
#SBATCH --partition=mit_normal
#SBATCH --array=0-12149%200          # 12,150 tasks, max 200 running at once
                                      # The %200 is a THROTTLE — it prevents
                                      # you from hogging the entire cluster.
                                      # 200 concurrent tasks is polite.

#SBATCH --cpus-per-task=2             # 2 cores per task (less than experiments
                                      # because we have 12K tasks and want to
                                      # be a good cluster citizen)

#SBATCH --mem=2G                      # 2 GB RAM per task
#SBATCH --time=00:15:00               # 15 min max (one config+rep is fast)

#SBATCH --output=logs/sweep_%A_%a.out
#SBATCH --error=logs/sweep_%A_%a.err

# ── Environment ──────────────────────────────────────────────────────────────
cd ~/sparse_matrix_recovery
mkdir -p logs experiments/results/sweep

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

# ── Decode Task ID into 5D Grid Coordinates ─────────────────────────────────
#
# SLURM_ARRAY_TASK_ID goes from 0 to 12149.
# We need to convert this to (N, T, meas_frac, stim_gain, stim_frac, rep).
#
# Think of it like a 6D array with dimensions:
#   [3 × 3 × 3 × 3 × 3 × 50] = 12,150
#
# To decode: use integer division and modulo, peeling off dimensions
# from right to left (like converting a linear index to multi-dim subscripts).

TASK_ID=${SLURM_ARRAY_TASK_ID}

# Grid values
N_VALUES=(8 15 30)
T_VALUES=(100 500 1000)
MEAS_VALUES=(0.33 0.66 1.0)
STIM_GAIN_VALUES=(0.0 0.5 1.0)
STIM_FRAC_VALUES=(0.33 0.66 1.0)
NUM_REPS=50

# Decode: peel off rep first (innermost), then stim_frac, stim_gain, meas, T, N
REP=$((TASK_ID % NUM_REPS))
REMAINDER=$((TASK_ID / NUM_REPS))
# Now REMAINDER is 0-242 (one of the 243 grid points)

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
echo "MEGA SWEEP — Task ${TASK_ID} / 12149"
echo "  N=${N}, T=${T}"
echo "  meas_frac=${MEAS_FRAC} (${NUM_MEASURED} neurons)"
echo "  stim_gain=${STIM_GAIN}"
echo "  stim_frac=${STIM_FRAC} (${NUM_STIMULATED} neurons)"
echo "  rep=${REP}, seed=42"
echo "  Node: $(hostname), CPUs: ${SLURM_CPUS_PER_TASK}"
echo "=============================================="

# ── Run ──────────────────────────────────────────────────────────────────────
uv run python experiments/run_single_rep.py \
    --num-nodes "${N}" \
    --max-timesteps "${T}" \
    --num-measured "${NUM_MEASURED}" \
    --num-stimulated "${NUM_STIMULATED}" \
    --stim-gain "${STIM_GAIN}" \
    --nonlinearity tanh \
    --rep "${REP}" \
    --seed 42 \
    --output-dir experiments/results/sweep \
    --wandb

echo "Done! $(date)"
