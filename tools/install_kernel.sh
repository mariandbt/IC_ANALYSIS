#!/bin/bash
# Registers the Jupyter kernel "IC_ANALYSIS": the IC conda env with ICTDIR, ICDIR, PYTHONPATH and the
# data paths of env.sh already set, so notebooks work in VS Code without sourcing anything.
# Run once (login node is fine):  bash tools/install_kernel.sh
set -e
cd "$(dirname "$0")/.."
source env.sh >/dev/null
python -m ipykernel install --user --name ic_analysis --display-name "IC_ANALYSIS (IC-3.8)" >/dev/null
K=$(jupyter kernelspec list | awk '/ic_analysis/{print $2}')/kernel.json
python - "$K" <<PY
import json, os, sys
k = json.load(open(sys.argv[1]))
k["env"] = {v: os.environ[v] for v in ["ICA_ROOT", "ICTDIR", "ICDIR", "PYTHONPATH", "NEXUS_DIR", "OLD_IC_DIR",
                                       "ICA_OUT", "S2_TABLE_FIBERS", "PATH"]}
json.dump(k, open(sys.argv[1], "w"), indent=1)
print("kernel written:", sys.argv[1])
PY
