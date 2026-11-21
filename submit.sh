#!/bin/bash
# Check what an IC step would do, and print (or run) the sbatch command.
#
#   ./submit.sh <detsim|hypathia|dorothea> <fibers|pmts> <sample> [first-last] [--chunks NxE] [--mem M] [--time T]
#               [--submit] [--force] [--after <jobid>]
#
# --chunks NxE: split each nexus file into N chunks of E events (e.g. 5x10000 for 50 000-event files).
#   Array task t -> file i = (t-1)/N + 1, chunk c = (t-1)%N; outputs <sample>_<i>_<c>.<city>.h5.
#   Use the same --chunks for hypathia and dorothea so they find the chunk files (and task ids match for --after).
# --mem / --time: override the defaults of slurm/run_city.slurm (12G, 1 day), e.g. --mem 4G --time 12:00:00.
# --after <jobid>: chain on a previous step that is still running. Task t starts when task t of <jobid> has
#   finished successfully (slurm aftercorr). Inputs are then not required to exist yet (the nexus file must).
#
# Without --submit nothing is sent: it lists which files are done, missing or to run, shows the
# config of the first task and prints the sbatch command. With --submit it runs that command.
# Outputs: $ICA_OUT/<sample>/<det>_g<EL_GAIN>/<city>/.
set -euo pipefail
cd "$(dirname "$0")"
source env.sh >/dev/null
source pipeline.sh

ica_setup "${1:?city}" "${2:?fibers|pmts}" "${3:?sample}"; shift 3
RANGE=""; SUBMIT=0; FORCE=0; AFTER=""; NCH=1; CHE=0; MEM=""; TIME=""
while [ $# -gt 0 ]; do case $1 in --submit) SUBMIT=1;; --force) FORCE=1;; --after) AFTER=$2; shift;;
  --chunks) NCH=${2%x*}; CHE=${2#*x}; shift;; --mem) MEM=$2; shift;; --time) TIME=$2; shift;;
  *-*) RANGE=$1;; *) echo "unknown option $1"; exit 1;; esac; shift; done
[ -n "$RANGE" ] && { FIRST=${RANGE%-*}; LAST=${RANGE#*-}; }

TODO=(); MISSING=(); DONE=(); TASKS=()        # TODO/DONE/MISSING hold unit names (i or i_c); TASKS the array ids
for ((i=FIRST; i<=LAST; i++)); do
  for ((c=0; c<NCH; c++)); do
    if [ "$NCH" -gt 1 ]; then U=${i}_$c; else U=$i; fi
    t=$(( (i - 1) * NCH + c + 1 ))
    if [ "$CITY" = detsim ]; then in=${IN_PATTERN//@I@/$i}; else in=${IN_PATTERN//@I@/$U}; fi
    out=${OUT_PATTERN//@I@/$U}
    [ -n "$AFTER" ] && in="$NEXUS_DIR/$SUB/${SAMPLE}_${i}.next.h5"   # chained: the upstream output does not exist yet
    if [ ! -f "$in" ]; then MISSING+=($U); elif [ -f "$out" ] && [ $FORCE = 0 ]; then DONE+=($U); else TODO+=($U); TASKS+=($t); fi
  done
done
echo "city=$CITY detector=$DET ($DB) sample=$SAMPLE files $FIRST-$LAST  chunks=${NCH}x${CHE}  el_gain=$EL_GAIN"
echo "  input : $IN_PATTERN"
echo "  output: $OUT_PATTERN"
echo "  to run: ${#TODO[@]}   already done: ${#DONE[@]} ${DONE[*]:-}   missing input: ${#MISSING[@]} ${MISSING[*]:-}"
[ ${#TODO[@]} = 0 ] && { echo "nothing to run"; exit 0; }

U=${TODO[0]}; i=${U%_*}
if [ "$NCH" -gt 1 ]; then c=${U#*_}; ER="$(( c * CHE )), $(( (c + 1) * CHE ))"; else ER=all; fi
if [ "$CITY" = detsim ]; then in=${IN_PATTERN//@I@/$i}; else in=${IN_PATTERN//@I@/$U}; fi
echo "---- config of unit $U (first lines) ----"
sed -e "s|@IN@|$in|" -e "s|@OUT@|${OUT_PATTERN//@I@/$U}|" -e "s|@DETECTOR_DB@|$DB|" -e "s|@S2_TABLE@|$S2|" -e "s|@EL_GAIN@|$EL_GAIN|" \
    -e "s|@EVENT_RANGE@|$ER|" config/$CITY.conf.template | grep -v '^\s*#' | grep -v '^\s*$' | head -8; echo "   ..."

# compress 1,2,3,5 -> 1-3,5
ARRAY=$(printf "%s\n" "${TASKS[@]}" | awk 'NR==1{s=p=$1;next} $1==p+1{p=$1;next} {printf "%s%s,", s, (s==p?"":"-"p); s=p=$1} END{printf "%s%s\n", s, (s==p?"":"-"p)}')
EXTRA=" --export=ALL,EL_GAIN=$EL_GAIN"; [ $FORCE = 1 ] && EXTRA="$EXTRA,ICA_FORCE=1"
[ "$NCH" -gt 1 ] && EXTRA="$EXTRA,ICA_NCHUNK=$NCH,ICA_CHUNK_EVENTS=$CHE"
[ -n "$MEM" ]  && EXTRA="$EXTRA --mem=$MEM"
[ -n "$TIME" ] && EXTRA="$EXTRA --time=$TIME"
[ -n "$AFTER" ] && EXTRA="$EXTRA --dependency=aftercorr:$AFTER"
CMD="sbatch --parsable --job-name=${CITY}_${DET} --array=$ARRAY$EXTRA slurm/run_city.slurm $CITY $DET $SAMPLE"
echo "---- command ----"; echo "$CMD"
if [ $SUBMIT = 1 ]; then mkdir -p "$OUT_DIR"; $CMD; else echo "(dry run: add --submit, or paste the command)"; fi
