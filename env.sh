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
export ICA_STORE=/data/marian/IC_ANALYSIS             # long-term copies made by tools/store.sh (read-only on compute nodes)
# EL gain (photons per electron) used by detsim; outputs go to <sample>/<det>_g<EL_GAIN>/<city>/
# 1050 = the gain nexus used for the S2 table runs: XenonELLightYield (Monteiro 2007 form, Freitas 2010 slope 170 for
# p >= 8 bar) at 10 bar and 13 kV/cm (1.3 kV/cm/bar, NEXT-White's operating point at 10.2 bar, NEXT2nu) over 1 cm.
# Other values: 365 (IC default, 2025 runs), 782 (NEXT-100 at 4 bar now). See README "EL gain and diffusion".
export EL_GAIN=${EL_GAIN:-1050}
export S2_TABLE_FIBERS=/data/marian/IC/LT/20250408_s2_table.h5

echo "IC_ANALYSIS: IC from $ICTDIR ($(git -C "$ICTDIR" rev-parse --short HEAD)), env $IC_ENV"
