# Source this file before running anything:  source env.sh
# Sets up IC from external/IC (pinned submodule), the conda environment, and the data paths.

export ICA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export IC_ENV=IC-3.8-2024-06-08

_ica_u=$-; set +u                                  # conda scripts fail under set -u
source "$HOME/miniconda/etc/profile.d/conda.sh"
conda activate "$IC_ENV"
[[ $_ica_u == *u* ]] && set -u; unset _ica_u

export ICTDIR="$ICA_ROOT/external/IC"
export ICDIR="$ICTDIR/invisible_cities"
export PATH="$ICTDIR/bin:$PATH"
export PYTHONPATH="$ICA_ROOT:$ICTDIR:$ICA_ROOT/external/python_cluster/s2simulation/modules${PYTHONPATH:+:$PYTHONPATH}"

# Data. Inputs are read only; everything new goes under ICA_OUT.
export NEXUS_DIR=/data/marian/s2simulation          # nexus inputs: Kr/, bb/, ie/, s1/
export OLD_IC_DIR=/data/marian/IC                    # 2025 outputs (detsim/, hypathia/, dorothea/, LT/)
export ICA_OUT=/scratch/marian/IC_ANALYSIS_OUT       # new outputs: <sample>/<detector>/<city>/ (jobs cannot write /data)
# EL gain (photons per electron) used by detsim; outputs go to <sample>/<det>_g<EL_GAIN>/<city>/
# 782 = NEXT-100 now: Monteiro 2007 (in NEXT2009 eq. 2.13), eta = 140 (E/p - 0.83) p dx with E/p = 2.27 kV/cm/bar,
# p = 4 bar, dx = 0.97 cm (MartinezLema2025, Table 1 and Sec. 2). 2025 runs used 365 (IC default).
export EL_GAIN=${EL_GAIN:-782}
export S2_TABLE_FIBERS=/data/marian/IC/LT/20250408_s2_table.h5

echo "IC_ANALYSIS: IC from $ICTDIR ($(git -C "$ICTDIR" rev-parse --short HEAD)), env $IC_ENV"
