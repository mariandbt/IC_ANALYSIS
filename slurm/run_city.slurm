#!/bin/bash
# One IC city on one input file per array task.
#   sbatch --array=1-40 slurm/run_city.slurm <detsim|hypathia|dorothea> <fibers|pmts> <sample>
# (./submit.sh prints this command with the right list of file indices.)
# Run from the IC_ANALYSIS folder. qos=serial: 1-CPU jobs, up to 1000 running, 2 days max.
# Job name: submit.sh sets <city>_<detector> (e.g. detsim_fibers); ic_city if you sbatch it directly.
#SBATCH --job-name=ic_city
#SBATCH --partition=general
#SBATCH --qos=serial
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=12G
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --mail-user=mariandelbarrio@gmail.com
#SBATCH --mail-type=BEGIN,END,FAIL

set -eo pipefail
export PYTHONUNBUFFERED=1          # progress lines appear in the log while the job runs
cd "$SLURM_SUBMIT_DIR"
source env.sh
source pipeline.sh
ica_setup "$1" "$2" "$3"

# Chunks: with ICA_NCHUNK=n and ICA_CHUNK_EVENTS=e (sbatch --export), each nexus file is split into n chunks
# of e events. Array task t -> file i = (t-1)/n + 1, chunk c = (t-1)%n, events [c*e, (c+1)*e).
# Outputs are named <sample>_<i>_<c>.<city>.h5; hypathia and dorothea then run on each chunk file whole.
t=$SLURM_ARRAY_TASK_ID; NCH=${ICA_NCHUNK:-1}; CHE=${ICA_CHUNK_EVENTS:-0}
if [ "$NCH" -gt 1 ]; then
  i=$(( (t - 1) / NCH + 1 )); c=$(( (t - 1) % NCH )); U=${i}_$c
else
  i=$t; c=""; U=$i
fi
ER=all
if [ "$CITY" = detsim ]; then
  IN=${IN_PATTERN//@I@/$i}
  [ "$NCH" -gt 1 ] && ER="$(( c * CHE )), $(( (c + 1) * CHE ))"
else
  IN=${IN_PATTERN//@I@/$U}
fi
OUT=${OUT_PATTERN//@I@/$U}
[ -f "$OUT" ] && [ -z "${ICA_FORCE:-}" ] && { echo "task $i: $OUT exists, skipping"; exit 0; }
mkdir -p "$OUT_DIR" work/configs
CONF=work/configs/${SAMPLE}_${DET}_g${EL_GAIN}_${CITY}_${U}.conf      # kept for provenance (IC also stores it in the output)
sed -e "s|@IN@|$IN|" -e "s|@OUT@|$OUT.part|" -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" -e "s|@EL_GAIN@|$EL_GAIN|" -e "s|@EVENT_RANGE@|$ER|" \
    config/$CITY.conf.template > "$CONF"
echo "task $t (file $i, chunk ${c:-none}, events $ER): $CITY $DET  $IN -> $OUT  (IC $(git -C "$ICTDIR" rev-parse --short HEAD), node $(hostname))"

city $CITY "$CONF"

python -c "import tables, sys; tables.open_file(sys.argv[1]).close()" "$OUT.part"   # readable?
mv "$OUT.part" "$OUT"
ls -la "$OUT"
