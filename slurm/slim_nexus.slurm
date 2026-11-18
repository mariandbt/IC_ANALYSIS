#!/bin/bash
# Job 0: slim copies of the Kr nexus inputs (drop the ie- rows of /MC/particles), one file per task.
#   sbatch --array=1 slurm/slim_nexus.slurm 20250626_Next100_50Kev_ELoff_Kr
# Output: $ICA_OUT/nexus_slim/<subfolder>/<sample>_<i>.next.h5 ; copy to /data from the login node afterwards.
#SBATCH --job-name=slim
#SBATCH --partition=general
#SBATCH --qos=serial
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --mail-user=mariandelbarrio@gmail.com
#SBATCH --mail-type=FAIL

set -eo pipefail
export PYTHONUNBUFFERED=1
cd "$SLURM_SUBMIT_DIR"
source env.sh
source samples.sh
SAMPLE=${1:?sample}
read SUB FIRST LAST <<< "${SAMPLES[$SAMPLE]}"
i=$SLURM_ARRAY_TASK_ID
IN=$NEXUS_DIR/$SUB/${SAMPLE}_$i.next.h5
OUT_DIR=$ICA_OUT/nexus_slim/$SUB; mkdir -p "$OUT_DIR"
OUT=$OUT_DIR/${SAMPLE}_$i.next.h5
[ -f "$OUT" ] && { echo "task $i: $OUT exists, skipping"; exit 0; }
echo "task $i: $IN -> $OUT  (node $(hostname))"
python tools/slim_nexus.py "$IN" "$OUT"
