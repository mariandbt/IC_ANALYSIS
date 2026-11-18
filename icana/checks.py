"""File integrity and the configurations stored inside nexus and IC files."""
import ast, re
import numpy  as np
import pandas as pd
import tables as tb

def is_readable(path):
    """Open the file and read the first and last row of every table. Returns (ok, message)."""
    try:
        with tb.open_file(path) as h:
            for leaf in h.walk_nodes("/", "Leaf"):
                n = getattr(leaf, "nrows", 0)
                if n: leaf.read(0, 1); leaf.read(n - 1, n)
        return True, ""
    except Exception as e:
        return False, str(e).splitlines()[0][:80]

def ic_config(path, city):
    """Config of `city` stored by IC in /config/<city> of an output file, as a dict of strings."""
    with tb.open_file(path) as h:
        rows = getattr(h.root.config, city).read()
    return {r[0].decode(): r[1].decode() for r in rows}

def physics(cfg):
    """physics_params of a stored detsim config, as a dict of floats (IC internal units)."""
    return ast.literal_eval(cfg["physics_params"])

def nexus_config(path, keys=("pressure", "RegisterGenerator", "RegisterGeometry", "region",
                              "elfield", "EL_field", "sensor_type", "num_events", "nphotons", "Xe136DecayMode")):
    """Selected lines of /MC/configuration of a nexus file."""
    c = pd.read_hdf(path, "/MC/configuration")
    out = {}
    for _, r in c.iterrows():
        p, v = str(r.iloc[0]), str(r.iloc[1])
        for k in keys:
            if p.endswith(k) or p.endswith("/" + k): out[k] = v.split("#")[0].strip()
    return out

def summary_ic(paths, city="detsim"):
    """One row per file: readability and the detsim settings that must be equal across a sample."""
    rows = []
    for p in paths:
        ok, msg = is_readable(p)
        row = dict(file=p.split("/")[-1], readable=ok, error=msg)
        if ok:
            try:
                d  = ic_config(p, "detsim"); ph = physics(d)
                row.update(detector_db=d["detector_db"], s1_table=d["s1_lighttable"].split("/")[-1],
                           s2_table=d["s2_lighttable"], el_gain=ph["el_gain"],
                           lifetime_ms=ph["lifetime"] / 1e6, nexus_input=ast.literal_eval(d["files_in"])[0].split("/")[-1])
            except Exception as e:
                row["error"] = f"no detsim config: {e}"
        rows.append(row)
    return pd.DataFrame(rows)
