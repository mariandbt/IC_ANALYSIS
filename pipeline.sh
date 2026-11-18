# Shared by submit.sh and slurm/run_city.slurm: where each step reads and writes.
# Usage: source pipeline.sh; ica_setup <city> <fibers|pmts> <sample>
source "$ICA_ROOT/samples.sh"
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
    hypathia) IN_PATTERN="$ICA_OUT/$SAMPLE/$DET/detsim/${SAMPLE}_@I@.detsim.h5" ;;
    dorothea) IN_PATTERN="$ICA_OUT/$SAMPLE/$DET/hypathia/${SAMPLE}_@I@.hypathia.h5" ;;
    *) echo "city must be detsim, hypathia or dorothea"; return 1;;
  esac
  OUT_DIR="$ICA_OUT/$SAMPLE/$DET/$CITY"
  OUT_PATTERN="$OUT_DIR/${SAMPLE}_@I@.$CITY.h5"
}
