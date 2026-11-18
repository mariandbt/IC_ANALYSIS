# Source this file before running anything:  source env.sh
# Sets up IC from external/IC (pinned submodule), the conda environment, and the data paths.

export ICA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export IC_ENV=IC-3.8-2024-06-08

source "$HOME/miniconda/etc/profile.d/conda.sh"
conda activate "$IC_ENV"

export ICTDIR="$ICA_ROOT/external/IC"
export ICDIR="$ICTDIR/invisible_cities"
export PATH="$ICTDIR/bin:$PATH"
export PYTHONPATH="$ICA_ROOT:$ICTDIR:$ICA_ROOT/external/python_cluster/s2simulation/modules${PYTHONPATH:+:$PYTHONPATH}"

# Data. Inputs are read only; everything new goes under ICA_OUT.
export NEXUS_DIR=/data/marian/s2simulation          # nexus inputs: Kr/, bb/, ie/, s1/
export OLD_IC_DIR=/data/marian/IC                    # 2025 outputs (detsim/, hypathia/, dorothea/, LT/)
export ICA_OUT=/data/marian/IC_ANALYSIS              # new outputs: <sample>/<detector>/<city>/
export S2_TABLE_FIBERS=/data/marian/IC/LT/20250408_s2_table.h5

echo "IC_ANALYSIS: IC from $ICTDIR ($(git -C "$ICTDIR" rev-parse --short HEAD)), env $IC_ENV"
