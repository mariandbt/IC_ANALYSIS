"""S2 light tables: the fiber table (s2simulation format) and the IC PMT table."""
import numpy as np, pandas as pd, tables as tb

def read_fiber_s2_table(path):
    """Returns (config DataFrame, light table DataFrame, sensor positions). Light table: one row per (x, y) bin,
    one column per fiber sensor (SiPMf_<id>), value = detection probability per EL photon (PDE included)."""
    cfg = pd.read_hdf(path, "/s2LT/Config")
    lt  = pd.read_hdf(path, "/s2LT/LightTable")
    sns = pd.read_hdf(path, "/s2LT/sns_positions")
    return cfg, lt, sns

def fiber_lce_map(lt):
    """Total collection efficiency per (x, y) bin: sum over the 108 sensor columns."""
    cols = [c for c in lt.columns if c.startswith("SiPMf")]
    out = lt[["bin_initial_x", "bin_final_x", "bin_initial_y", "bin_final_y"]].copy()
    out["x"] = 0.5 * (out.bin_initial_x + out.bin_final_x)
    out["y"] = 0.5 * (out.bin_initial_y + out.bin_final_y)
    out["lce"] = lt[cols].sum(axis=1)
    return out, cols

def list_nodes(path):
    with tb.open_file(path) as h:
        return [n._v_pathname for n in h.walk_nodes("/", "Leaf")]
