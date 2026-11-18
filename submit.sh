#!/bin/bash
# Run one IC city over one sample, as a slurm array (one task per input file).
#
#   ./submit.sh <city> <fibers|pmts> <sample> [first-last] [--submit] [--force]
#
#   city     detsim | hypathia | dorothea
#   sample   a key of samples.sh
#   range    file indices to run (default: the whole sample)
#   --submit actually call sbatch. Without it, nothing is submitted: it prints the plan and
#            the config of the first task (dry run).
#   --force  overwrite outputs that already exist (default: tasks with an existing output are skipped)
#
# Inputs and outputs (pipeline: nexus -> detsim -> hypathia -> dorothea):
#   detsim    in  $NEXUS_DIR/<sub>/<sample>_<i>.next.h5
#   hypathia  in  $ICA_OUT/<sample>/<det>/detsim/<sample>_<i>.detsim.h5
#   dorothea  in  $ICA_OUT/<sample>/<det>/hypathia/<sample>_<i>.hypathia.h5
#   every city writes $ICA_OUT/<sample>/<det>/<city>/<sample>_<i>.<city>.h5
set -euo pipefail
cd "$(dirname "$0")"
source env.sh >/dev/null
source samples.sh

CITY=${1:?city}; DET=${2:?fibers|pmts}; SAMPLE=${3:?sample}; shift 3
RANGE=""; SUBMIT=0; FORCE=0
for a in "$@"; do case $a in --submit) SUBMIT=1;; --force) FORCE=1;; *-*) RANGE=$a;; *) echo "unknown option $a"; exit 1;; esac; done

[[ -v SAMPLES[$SAMPLE] ]] || { echo "unknown sample $SAMPLE (see samples.sh)"; exit 1; }
read SUB FIRST LAST <<< "${SAMPLES[$SAMPLE]}"
[ -n "$RANGE" ] && { FIRST=${RANGE%-*}; LAST=${RANGE#*-}; }

case $DET in
  fibers) DB=next100fibers; S2=$S2_TABLE_FIBERS ;;
  pmts)   DB=next100;       S2='$ICDIR/database/test_data/NEXT100_S2_LT.h5' ;;
  *) echo "detector must be fibers or pmts"; exit 1;;
esac
case $CITY in
  detsim)   IN_PATTERN="$NEXUS_DIR/$SUB/${SAMPLE}_@I@.next.h5" ;;
  hypathia) IN_PATTERN="$ICA_OUT/$SAMPLE/$DET/detsim/${SAMPLE}_@I@.detsim.h5" ;;
  dorothea) IN_PATTERN="$ICA_OUT/$SAMPLE/$DET/hypathia/${SAMPLE}_@I@.hypathia.h5" ;;
  *) echo "city must be detsim, hypathia or dorothea"; exit 1;;
esac
OUT_DIR="$ICA_OUT/$SAMPLE/$DET/$CITY"
OUT_PATTERN="$OUT_DIR/${SAMPLE}_@I@.$CITY.h5"

# Which tasks to run: input must exist; output must not (unless --force)
TODO=(); MISSING=(); DONE=()
for ((i=FIRST; i<=LAST; i++)); do
  in=${IN_PATTERN//@I@/$i}; out=${OUT_PATTERN//@I@/$i}
  if [ ! -f "$in" ]; then MISSING+=($i); elif [ -f "$out" ] && [ $FORCE = 0 ]; then DONE+=($i); else TODO+=($i); fi
done
echo "city=$CITY detector=$DET ($DB) sample=$SAMPLE files $FIRST-$LAST"
echo "  input : $IN_PATTERN"
echo "  output: $OUT_PATTERN"
echo "  to run: ${#TODO[@]}   already done: ${#DONE[@]} ${DONE[*]:-}   missing input: ${#MISSING[@]} ${MISSING[*]:-}"
[ ${#TODO[@]} = 0 ] && { echo "nothing to run"; exit 0; }

# Config of the first task, for inspection
i=${TODO[0]}
sed -e "s|@IN@|${IN_PATTERN//@I@/$i}|" -e "s|@OUT@|${OUT_PATTERN//@I@/$i}|" \
    -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" config/$CITY.conf.template > /tmp/ica_preview_$$.conf
echo "---- config for task $i ----"; grep -v '^\s*#' /tmp/ica_preview_$$.conf | grep -v '^\s*$' | head -12; echo "   ..."
rm -f /tmp/ica_preview_$$.conf

if [ $SUBMIT = 0 ]; then echo "dry run: add --submit to send ${#TODO[@]} jobs"; exit 0; fi
mkdir -p "$OUT_DIR" logs work/configs
ARRAY=$(IFS=,; echo "${TODO[*]}")
sbatch --array="$ARRAY" --job-name="${CITY}_${DET}" \
       --output="logs/%x_%A_%a.out" --error="logs/%x_%A_%a.err" \
       --export=ALL,CITY=$CITY,DB=$DB,S2=$S2,IN_PATTERN=$IN_PATTERN,OUT_PATTERN=$OUT_PATTERN,TAG=${SAMPLE}_${DET} \
       slurm/run_city.slurm
