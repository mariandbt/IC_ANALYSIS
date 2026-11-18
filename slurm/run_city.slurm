#!/bin/bash
# One task of an IC city over one input file. Launched by submit.sh (do not sbatch it directly).
#SBATCH --partition=general
#SBATCH --qos=regular
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --mail-user=mariandelbarrio@gmail.com
#SBATCH --mail-type=FAIL,ARRAY_TASKS

set -eo pipefail
cd "$SLURM_SUBMIT_DIR"
source env.sh

i=$SLURM_ARRAY_TASK_ID
IN=${IN_PATTERN//@I@/$i}
OUT=${OUT_PATTERN//@I@/$i}
CONF=work/configs/${TAG}_${CITY}_${i}.conf      # kept for provenance (IC also stores it inside the output)

sed -e "s|@IN@|$IN|" -e "s|@OUT@|$OUT.part|" -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" \
    config/$CITY.conf.template > "$CONF"
echo "task $i: $CITY  $IN -> $OUT  (IC $(git -C "$ICTDIR" rev-parse --short HEAD), node $(hostname))"

city $CITY "$CONF"

# Only a finished, readable file gets the final name
python -c "import tables, sys; tables.open_file(sys.argv[1]).close()" "$OUT.part"
mv "$OUT.part" "$OUT"
ls -la "$OUT"
