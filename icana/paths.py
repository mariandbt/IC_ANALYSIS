"""Where everything is. Inputs are read only; new outputs go under ICA_OUT."""
import os, glob

NEXUS_DIR   = os.environ.get("NEXUS_DIR",  "/data/marian/s2simulation")
OLD_IC_DIR  = os.environ.get("OLD_IC_DIR", "/data/marian/IC")
ICA_OUT     = os.environ.get("ICA_OUT",    "/data/marian/IC_ANALYSIS")
ICDIR       = os.environ.get("ICDIR",      "")
OLD_ICCOURSE = "/scratch/marian/ic-course/data"          # matched 1Kev Dorothea outputs (2025)

S2_TABLE_FIBERS = "/data/marian/IC/LT/20250408_s2_table.h5"
S2_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S2_LT.h5")
S1_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S1_LT.h5")

def new_files(sample, det, city):
    """Outputs of this repository: $ICA_OUT/<sample>/<det>/<city>/<sample>_<i>.<city>.h5, sorted by index."""
    fs = glob.glob(os.path.join(ICA_OUT, sample, det, city, f"{sample}_*.{city}.h5"))
    return sorted(fs, key=file_index)

def file_index(path):
    base = os.path.basename(path).split(".")[0]
    try:    return int(base.rsplit("_", 1)[1])
    except: return -1

# 2025 outputs, for comparison (produced with the same configs, IC fibers branch)
OLD = {
    ("20250626_Next100_50Kev_ELoff_Kr", "fibers", "dorothea"): [f"{OLD_IC_DIR}/dorothea/20250626_Next100_50Kev_ELoff_Kr_0-40.dorothea.h5"],
    ("20250624_Next100_1Kev_ELoff_Kr",  "fibers", "dorothea"): [f"{OLD_ICCOURSE}/20250624_Next100_1Kev_ELoff_Kr_ALL.dorothea.h5"],
    ("20250624_Next100_1Kev_ELoff_Kr",  "pmts",   "dorothea"): [f"{OLD_ICCOURSE}/20250624_Next100_1Kev_ELoff_Kr_ALL_PMTs.dorothea.h5"],
}
def old_files(sample, det, city):
    if (sample, det, city) in OLD: return OLD[(sample, det, city)]
    if city in ("detsim", "hypathia"):
        sub = "PMTs/" if (det == "pmts" and city == "detsim") else ""
        suf = "_PMTs" if det == "pmts" else ""
        fs = glob.glob(f"{OLD_IC_DIR}/{city}/{sub}{sample}_*{suf}.{city}.h5")
        fs = [f for f in fs if "TEST" not in f]
        if det == "fibers": fs = [f for f in fs if "_PMTs" not in f]
        return sorted(fs, key=lambda p: file_index(p.replace("_PMTs", "")))
    return []

def nexus_files(sample):
    fs = glob.glob(f"{NEXUS_DIR}/*/{sample}_*.next.h5")
    return sorted(fs, key=file_index)
