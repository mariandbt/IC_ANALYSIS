#!/bin/bash
# VS Code on a compute node (DIPC docs: https://scc.dipc.org/docs/interactive/vscode/).
#   sbatch slurm/vscode.slurm
# Then, on your laptop:  bash tools/vscode_tunnel.sh <jobid>   and connect VS Code to "hyperion-tunnel".
# Never run VS Code on the login nodes.
#SBATCH --job-name=vscode
#SBATCH --qos=regular
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --mail-user=mariandelbarrio@gmail.com
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --output=/scratch/%u/vscode-%j.out
#SBATCH --error=/scratch/%u/vscode-%j.err
module load DIPC-Utils/0.0.2
ssh-server-start.sh
