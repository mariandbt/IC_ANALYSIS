#!/bin/bash
# One IC city on one input file per array task.
#   sbatch --array=1-40 slurm/run_city.slurm <detsim|hypathia|dorothea> <fibers|pmts> <sample>
# (./submit.sh prints this command with the right list of file indices.)
# Run from the IC_ANALYSIS folder. qos=serial: 1-CPU jobs, up to 1000 running, 2 days max.
#SBATCH --job-name=ica
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
#SBATCH --mail-type=FAIL,ARRAY_TASKS

set -eo pipefail
cd "$SLURM_SUBMIT_DIR"
source env.sh
source pipeline.sh
ica_setup "$1" "$2" "$3"

i=$SLURM_ARRAY_TASK_ID
IN=${IN_PATTERN//@I@/$i}
OUT=${OUT_PATTERN//@I@/$i}
[ -f "$OUT" ] && [ -z "${ICA_FORCE:-}" ] && { echo "task $i: $OUT exists, skipping"; exit 0; }
mkdir -p "$OUT_DIR" work/configs
CONF=work/configs/${SAMPLE}_${DET}_${CITY}_${i}.conf      # kept for provenance (IC also stores it in the output)
sed -e "s|@IN@|$IN|" -e "s|@OUT@|$OUT.part|" -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" -e "s|@EL_GAIN@|$EL_GAIN|" \
    config/$CITY.conf.template > "$CONF"
echo "task $i: $CITY $DET  $IN -> $OUT  (IC $(git -C "$ICTDIR" rev-parse --short HEAD), node $(hostname))"

city $CITY "$CONF"

python -c "import tables, sys; tables.open_file(sys.argv[1]).close()" "$OUT.part"   # readable?
mv "$OUT.part" "$OUT"
ls -la "$OUT"
