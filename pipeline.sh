# Shared by submit.sh and slurm/run_city.slurm: where each step reads and writes.
# Usage: source pipeline.sh; ica_setup <city> <fibers|pmts> <sample>
source "$ICA_ROOT/samples.sh"
# Layout (same on /scratch = $ICA_OUT and /data = $ICA_STORE): <city>/<det>/g<EL_GAIN>/<sample>_<i>[_<c>].<city>.h5
# Input of the previous step: /data if that sample is stored there (tools/store.sh), otherwise /scratch.
ica_root () { compgen -G "$ICA_STORE/$1/$DET/g$EL_GAIN/${SAMPLE}_*.$1.h5" >/dev/null && echo "$ICA_STORE" || echo "$ICA_OUT"; }
ica_setup () {
  CITY=$1; DET=$2; SAMPLE=$3
  [[ -v SAMPLES[$SAMPLE] ]] || { echo "unknown sample $SAMPLE (see samples.sh)"; return 1; }
  read SUB FIRST LAST <<< "${SAMPLES[$SAMPLE]}"
  case $DET in
    fibers) DB=next100fibers; S2=$S2_TABLE_FIBERS ;;
    pmts)   DB=next100;       S2='$ICDIR/database/test_data/NEXT100_S2_LT.h5' ;;
    *) echo "detector must be fibers or pmts"; return 1;;
  esac
  case $CITY in
    detsim)   IN_PATTERN="$NEXUS_DIR/$SUB/${SAMPLE}_@I@.next.h5" ;;
    hypathia) IN_PATTERN="$(ica_root detsim)/detsim/$DET/g$EL_GAIN/${SAMPLE}_@I@.detsim.h5" ;;
    dorothea) IN_PATTERN="$(ica_root hypathia)/hypathia/$DET/g$EL_GAIN/${SAMPLE}_@I@.hypathia.h5" ;;
    *) echo "city must be detsim, hypathia or dorothea"; return 1;;
  esac
  OUT_DIR="$ICA_OUT/$CITY/$DET/g$EL_GAIN"
  OUT_PATTERN="$OUT_DIR/${SAMPLE}_@I@.$CITY.h5"
}
