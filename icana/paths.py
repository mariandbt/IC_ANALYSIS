"""Where everything is. Inputs are read only; new outputs go under ICA_OUT (/scratch), long-term copies under ICA_STORE (/data)."""
import os, glob

NEXUS_DIR   = os.environ.get("NEXUS_DIR",  "/data/marian/s2simulation")
ICA_OUT     = os.environ.get("ICA_OUT",    "/scratch/marian/IC_ANALYSIS_OUT")
ICA_STORE   = os.environ.get("ICA_STORE",  "/data/marian/IC_ANALYSIS")   # long-term copies (tools/store.sh)
ICDIR       = os.environ.get("ICDIR",      "")

S2_TABLE_FIBERS = "/data/marian/IC/LT/20250408_s2_table.h5"
S2_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S2_LT.h5")
S1_TABLE_PMTS   = os.path.join(ICDIR, "database/test_data/NEXT100_S1_LT.h5")

EL_GAIN = int(os.environ.get("EL_GAIN", 1050))   # same default as env.sh (the Jupyter kernel does not pass EL_GAIN)

# Layout, the same on /data (ICA_STORE) and /scratch (ICA_OUT):
#     IC_ANALYSIS/<city>/<det>/g<gain>/<sample>_<file>[_<chunk>].<city>.h5
#     city = detsim, hypathia, dorothea;  det = fibers, pmts;  gain = 1050 (new runs), 365 (2025 runs)
CITIES, DETECTORS = ("detsim", "hypathia", "dorothea"), ("fibers", "pmts")

def files(city, det, gain, sample, file=None):
    """All files of one run, sorted by file and chunk. /data first; /scratch adds files not copied to /data yet.
    file=None: every file; file=1: all chunks of file 1."""
    found = {}
    for root in (ICA_STORE, ICA_OUT):
        for f in glob.glob(os.path.join(root, city, det, f"g{gain}", f"{sample}_*.{city}.h5")):
            found.setdefault(os.path.basename(f), f)
    fs = sorted(found.values(), key=lambda p: (file_index(p), chunk_index(p) or 0))
    if file is not None: fs = [f for f in fs if file_index(f) == int(file)]
    if not fs:
        raise FileNotFoundError(f"no {city} files for {det}, gain {gain}, {sample}" + (f", file {file}" if file is not None else "")
                                + ". Run paths.show() to see what exists.")
    return fs

def file(city, det, gain, sample, i, chunk=0):
    """One file: <sample>_<i>.<city>.h5, or chunk <chunk> of it for runs split in chunks (50Kev at gain 1050)."""
    fs = files(city, det, gain, sample, i)
    if len(fs) == 1: return fs[0]
    fs = [f for f in fs if chunk_index(f) == int(chunk)]
    if not fs: raise FileNotFoundError(f"file {i} of {sample} has no chunk {chunk}")
    return fs[0]

def show(sample=None):
    """Table of what exists: number of files per sample, city, detector and gain (on /data + /scratch)."""
    rows = {}
    for root in (ICA_STORE, ICA_OUT):
        for f in glob.glob(os.path.join(root, "*", "*", "g*", "*.h5")):
            city, det, g = f.split("/")[-4:-1]
            if city not in CITIES: continue
            s = os.path.basename(f).split(f".{city}.")[0]
            n = _numbers(f); s = "_".join(s.split("_")[:len(s.split("_")) - len(n)]) if n else s.rsplit("_", 1)[0]
            if sample and s != sample: continue
            rows.setdefault((s, city, det, int(g[1:])), set()).add(os.path.basename(f))
    import pandas as pd
    t = pd.Series({k: len(v) for k, v in rows.items()}, dtype=int)
    if t.empty: print("nothing found"); return t
    t.index.names = ["sample", "city", "det", "gain"]
    return t.unstack(["det", "gain"]).fillna(0).astype(int)

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

def nexus_files(sample):
    fs = glob.glob(f"{NEXUS_DIR}/*/{sample}_*.next.h5")
    return sorted(fs, key=file_index)
