#!/bin/bash
#==============================================================================
# launch_wandb_sweep.sh — Run a WandB sweep agent on the engaging cluster
#
# USAGE:
#   1. Create the sweep (from your Mac or login node):
#      cd ~/sparse_matrix_recovery
#      source ~/.secrets
#      wandb sweep experiments/sweep_config.yaml
#      # This prints: "Created sweep with ID: XXXXXXXX"
#
#   2. Launch agents on the cluster:
#      SWEEP_ID=<paste_id> sbatch scripts/launch_wandb_sweep.sh
#
#   3. View results at: https://wandb.ai/qsimeon/sparse_matrix_recovery/sweeps
#
# Each SLURM task runs one wandb agent that picks up configs from the sweep.
# WandB coordinates which config each agent runs — no manual decoding needed.
#==============================================================================

#SBATCH --job-name=wandb_sweep
#SBATCH --partition=mit_normal
#SBATCH --array=0-9                   # 10 parallel agents
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=04:00:00               # 4 hours (agents run multiple configs)
#SBATCH --output=logs/wandb_sweep_%A_%a.out
#SBATCH --error=logs/wandb_sweep_%A_%a.err

cd ~/sparse_matrix_recovery
mkdir -p logs
source ~/.secrets
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export JOBLIB_START_METHOD=fork

echo "WandB sweep agent ${SLURM_ARRAY_TASK_ID} starting on $(hostname)"
echo "Sweep ID: ${SWEEP_ID}"

# Each agent picks up configs from the sweep controller
# and runs them until the sweep is complete
uv run wandb agent "qsimeon/sparse_matrix_recovery/${SWEEP_ID}"

echo "Agent ${SLURM_ARRAY_TASK_ID} done. $(date)"
