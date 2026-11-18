#!/bin/bash
# Run on YOUR LAPTOP after `sbatch slurm/vscode.slurm` on the cluster:
#   bash vscode_tunnel.sh <jobid> [local-port]
# Reads node and port from /scratch/marian/vscode-<jobid>.out and keeps an SSH tunnel open
# (leave this terminal open). Then in VS Code: Remote Explorer -> hyperion-tunnel.
# Needs once in ~/.ssh/config:
#   Host hyperion-tunnel
#     HostName localhost
#     Port 2222
#     User marian
JOB=${1:?jobid}; LPORT=${2:-2222}; LOGIN=marian@hyperion.sw.ehu.es
OUT=$(ssh $LOGIN "cat /scratch/marian/vscode-$JOB.out 2>/dev/null")
NODE=$(echo "$OUT" | awk '/Hostname:/{print $2}'); PORT=$(echo "$OUT" | awk '/^Port:/{print $2}')
[ -z "$NODE" ] && { echo "job $JOB not running yet (or no output). Check: ssh $LOGIN squeue -u marian"; exit 1; }
echo "tunnel localhost:$LPORT -> $NODE:$PORT  (Ctrl+C to close)"
ssh -L $LPORT:$NODE:$PORT $LOGIN -N
