#!/bin/bash
# Execute a notebook on a compute node and save the executed copy (with outputs) in work/executed/.
#   sbatch slurm/run_notebook.slurm notebooks/00_pipeline_and_inventory.ipynb
# Quick checks (<10 min, high priority):  sbatch --qos=test --time=00:10:00 slurm/run_notebook.slurm <notebook>
#SBATCH --mail-user=mariandelbarrio@gmail.com
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --job-name=notebook
#SBATCH --partition=general
#SBATCH --qos=regular
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -eo pipefail
cd "$SLURM_SUBMIT_DIR"
source env.sh
NB=${1:?notebook}
mkdir -p work/executed
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 \
    --ExecutePreprocessor.kernel_name=ic_analysis "$NB" --output-dir work/executed
echo "executed copy: work/executed/$(basename "$NB")"
