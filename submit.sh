#!/bin/bash
# Check what an IC step would do, and print (or run) the sbatch command.
#
#   ./submit.sh <detsim|hypathia|dorothea> <fibers|pmts> <sample> [first-last] [--submit] [--force] [--after <jobid>]
#
# --after <jobid>: chain on a previous step that is still running. Task i starts when task i of <jobid> has
#   finished successfully (slurm aftercorr). Inputs are then not required to exist yet (the nexus file must).
#
# Without --submit nothing is sent: it lists which files are done, missing or to run, shows the
# config of the first task and prints the sbatch command. With --submit it runs that command.
# Each array task = one input file (slurm/run_city.slurm). Outputs: $ICA_OUT/<sample>/<det>/<city>/.
set -euo pipefail
cd "$(dirname "$0")"
source env.sh >/dev/null
source pipeline.sh

ica_setup "${1:?city}" "${2:?fibers|pmts}" "${3:?sample}"; shift 3
RANGE=""; SUBMIT=0; FORCE=0; AFTER=""
while [ $# -gt 0 ]; do case $1 in --submit) SUBMIT=1;; --force) FORCE=1;; --after) AFTER=$2; shift;;
  *-*) RANGE=$1;; *) echo "unknown option $1"; exit 1;; esac; shift; done
[ -n "$RANGE" ] && { FIRST=${RANGE%-*}; LAST=${RANGE#*-}; }

TODO=(); MISSING=(); DONE=()
for ((i=FIRST; i<=LAST; i++)); do
  in=${IN_PATTERN//@I@/$i}; out=${OUT_PATTERN//@I@/$i}
  [ -n "$AFTER" ] && in="$NEXUS_DIR/$SUB/${SAMPLE}_${i}.next.h5"   # chained: the upstream output does not exist yet
  if [ ! -f "$in" ]; then MISSING+=($i); elif [ -f "$out" ] && [ $FORCE = 0 ]; then DONE+=($i); else TODO+=($i); fi
done
echo "city=$CITY detector=$DET ($DB) sample=$SAMPLE files $FIRST-$LAST  el_gain=$EL_GAIN"
echo "  input : $IN_PATTERN"
echo "  output: $OUT_PATTERN"
echo "  to run: ${#TODO[@]}   already done: ${#DONE[@]} ${DONE[*]:-}   missing input: ${#MISSING[@]} ${MISSING[*]:-}"
[ ${#TODO[@]} = 0 ] && { echo "nothing to run"; exit 0; }

i=${TODO[0]}
echo "---- config of task $i (first lines) ----"
sed -e "s|@IN@|${IN_PATTERN//@I@/$i}|" -e "s|@OUT@|${OUT_PATTERN//@I@/$i}|" -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" -e "s|@EL_GAIN@|$EL_GAIN|" \
    config/$CITY.conf.template | grep -v '^\s*#' | grep -v '^\s*$' | head -8; echo "   ..."

# compress 1,2,3,5 -> 1-3,5
ARRAY=$(printf "%s\n" "${TODO[@]}" | awk 'NR==1{s=p=$1;next} $1==p+1{p=$1;next} {printf "%s%s,", s, (s==p?"":"-"p); s=p=$1} END{printf "%s%s\n", s, (s==p?"":"-"p)}')
EXTRA=" --export=ALL,EL_GAIN=$EL_GAIN"; [ $FORCE = 1 ] && EXTRA="$EXTRA,ICA_FORCE=1"
[ -n "$AFTER" ] && EXTRA="$EXTRA --dependency=aftercorr:$AFTER"
CMD="sbatch --parsable --array=$ARRAY$EXTRA slurm/run_city.slurm $CITY $DET $SAMPLE"
echo "---- command ----"; echo "$CMD"
if [ $SUBMIT = 1 ]; then mkdir -p "$OUT_DIR"; $CMD; else echo "(dry run: add --submit, or paste the command)"; fi
