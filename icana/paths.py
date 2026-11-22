"""Where everything is. Inputs are read only; new outputs go under ICA_OUT."""
import os, glob

NEXUS_DIR   = os.environ.get("NEXUS_DIR",  "/data/marian/s2simulation")
OLD_IC_DIR  = os.environ.get("OLD_IC_DIR", "/data/marian/IC")
ICA_OUT     = os.environ.get("ICA_OUT",    "/scratch/marian/IC_ANALYSIS_OUT")
ICA_STORE   = os.environ.get("ICA_STORE",  "/data/marian/IC_ANALYSIS")   # long-term copies (tools/store.sh)
ICDIR       = os.environ.get("ICDIR",      "")
OLD_ICCOURSE = "/scratch/marian/ic-course/data"          # matched 1Kev Dorothea outputs (2025)

S2_TABLE_FIBERS = "/data/marian/IC/LT/20250408_s2_table.h5"
S2_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S2_LT.h5")
S1_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S1_LT.h5")

EL_GAIN = int(os.environ.get("EL_GAIN", 1050))   # same default as env.sh (the Jupyter kernel does not pass EL_GAIN)

def new_files(sample, det, city, el_gain=None):
    """Outputs of this repository: <root>/<sample>/<det>_g<gain>/<city>/<sample>_<i>.<city>.h5, sorted by index.
    Looks in $ICA_OUT (/scratch) first and, if nothing is there, in $ICA_STORE (/data, after tools/store.sh)."""
    g = EL_GAIN if el_gain is None else el_gain
    for root in (ICA_OUT, ICA_STORE):
        fs = glob.glob(os.path.join(root, sample, f"{det}_g{g}", city, f"{sample}_*.{city}.h5"))
        if fs: break
    return sorted(fs, key=lambda p: (file_index(p), chunk_index(p) or 0))

def _numbers(path):
    """Trailing numbers of the name: <sample>_<i> -> [i]; chunk files <sample>_<i>_<c> -> [i, c]."""
    toks = os.path.basename(path).split(".")[0].split("_")
    out = []
    while toks and toks[-1].isdigit(): out.insert(0, int(toks.pop()))
    return out[-2:] if len(out) >= 2 and not toks[-1].endswith("ev") else out[-1:]

def file_index(path):
    """File number i of <sample>_<i>[_<c>].<city>.h5 (-1 if none)."""
    n = _numbers(path); return n[0] if n else -1

def chunk_index(path):
    """Chunk number c of <sample>_<i>_<c>.<city>.h5, None for whole-file outputs."""
    n = _numbers(path); return n[1] if len(n) == 2 else None

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
