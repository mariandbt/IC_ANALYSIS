"""0nubb energy from hypathia PMaps (06_qbb).

For every event and every S2 slice (~1 us):
  drift time  dt = t_slice - t0,   t0 = time of the largest S1 slice (the decay is at 100 us in detsim)
  (x, y)      charge barycentre of the SiPMs in that slice (slices without SiPM charge take the peak barycentre)
  lifetime    E * exp(dt / tau)
  (x, y)      two versions: E * LCE(0, 0) / LCE(x, y) from the S2 light table detsim used (e_table), or
              E / K(x, y) with K the Kr response map from the Kr kDSTs at the same gain (e_kr, as NEXT does);
              each at the slice barycentre, or per SiPM "hit" (e_table_hits, e_kr_hits: the slice energy shared
              among its SiPMs by charge, each share corrected at that SiPM; better for tracks that are wide in x, y)
The event energy is the sum over slices and S2 peaks. Truth from /MC/hits (copied by IC into every output).
Per-file results are cached in work/qbb/ so the notebook only reads the PMaps once.
"""
import os, sys, io, contextlib
import numpy as np, pandas as pd
from scipy.interpolate import RegularGridInterpolator
from . import paths

V_DRIFT = 1.0                    # mm/us (detsim drift_velocity)
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "qbb")


# ---------------------------------------------------------------- light collection maps
def lce_map(det, step=5.0, rmax=490.0):
    """LCE(x, y) summed over sensors, evaluated with IC's own table classes (as detsim does) on a grid,
    normalised to the centre. Returns a function f(x, y) -> LCE / LCE(0, 0) (nan outside rmax). Cached."""
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, f"lce_{det}_{step:g}mm.npz")
    if os.path.exists(fn):
        d = np.load(fn); xs, m = d["xs"], d["m"]
    else:
        from invisible_cities.detsim.light_tables_c import LT_FIBERS, LT_PMT
        lt = LT_FIBERS(fname=paths.S2_TABLE_FIBERS) if det == "fibers" else LT_PMT(fname=paths.S2_TABLE_PMTS)
        xs = np.arange(-rmax, rmax + step / 2, step)
        m = np.full((len(xs), len(xs)), np.nan)
        # The Cython table swallows its own out-of-bounds errors (it only reports them); catch the report
        # and leave those points as nan instead of using whatever value came back.
        errors, hook = [], sys.unraisablehook
        sys.unraisablehook = lambda u: errors.append(1)
        try:
            for i, x in enumerate(xs):
                for j, y in enumerate(xs):
                    if np.hypot(x, y) > rmax: continue
                    n = len(errors)
                    v = sum(np.sum(lt.get_values(x, y, s)) for s in range(lt.num_sensors))
                    if len(errors) == n: m[i, j] = v
        finally:
            sys.unraisablehook = hook
        np.savez(fn, xs=xs, m=m, n_bad=len(errors))
    centre = m[len(xs) // 2, len(xs) // 2]
    f = RegularGridInterpolator((xs, xs), m / centre, bounds_error=False, fill_value=np.nan)
    return lambda x, y: f(np.column_stack([np.ravel(x), np.ravel(y)]))


def kr_map(det, gain, tau_us, sample="20250626_Next100_50Kev_ELoff_Kr", step=20.0, rmax=490.0, min_events=50):
    """(x, y) map from the Kr kDSTs (dorothea) of the same detector and gain, as NEXT does with data:
    median of S2e * exp(dt / tau) in (x, y) bins, normalised to the centre (R < 30 mm).
    Returns f(x, y) -> relative response (nan in bins with fewer than min_events). Cached."""
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, f"krmap_{det}_g{gain}_tau{tau_us:.0f}_{step:g}mm.npz")
    if os.path.exists(fn):
        d = np.load(fn); xs, m = d["xs"], d["m"]
    else:
        dst = pd.concat([pd.read_hdf(f, "/DST/Events", columns=["X", "Y", "Z", "R", "S2e", "nS2"])
                         for f in paths.files("dorothea", det, gain, sample)], ignore_index=True)
        dst = dst[dst.nS2 == 1]
        e = dst.S2e.values * np.exp(dst.Z.values / V_DRIFT / tau_us)
        centre = np.median(e[dst.R.values < 30])
        edges = np.arange(-rmax - step / 2, rmax + step, step); xs = 0.5 * (edges[1:] + edges[:-1])
        ix, iy = np.digitize(dst.X.values, edges) - 1, np.digitize(dst.Y.values, edges) - 1
        ok = (ix >= 0) & (ix < len(xs)) & (iy >= 0) & (iy < len(xs))
        g = pd.DataFrame(dict(i=ix[ok], j=iy[ok], e=e[ok])).groupby(["i", "j"]).e.agg(["median", "size"])
        g = g[g["size"] >= min_events]
        m = np.full((len(xs), len(xs)), np.nan)
        m[g.index.get_level_values(0), g.index.get_level_values(1)] = g["median"].values / centre
        np.savez(fn, xs=xs, m=m, n_events=len(dst), centre=centre)
    f = RegularGridInterpolator((xs, xs), m, bounds_error=False, fill_value=np.nan)
    return lambda x, y: f(np.column_stack([np.ravel(x), np.ravel(y)]))


def kr_centre(det, gain, tau_us, step=20.0):
    """Median lifetime-corrected Kr S2e at R < 30 mm (pes): the 41.5 keV reference for the energy scale."""
    kr_map(det, gain, tau_us, step=step)
    return float(np.load(os.path.join(CACHE, f"krmap_{det}_g{gain}_tau{tau_us:.0f}_{step:g}mm.npz"))["centre"])


# ---------------------------------------------------------------- one file -> one row per event
def _truth(path):
    """True energy in the active volume and the hit extent per nexus event."""
    h = pd.read_hdf(path, "/MC/hits")
    a = h[h.label == "ACTIVE"]
    r = np.hypot(a.x, a.y)
    t = pd.DataFrame(dict(e_true=a.groupby("event_id").energy.sum() * 1e3,       # MeV -> keV
                          r_true_max=r.groupby(a.event_id).max(),
                          z_true_min=a.groupby("event_id").z.min(), z_true_max=a.groupby("event_id").z.max()))
    t["e_outside"] = h[h.label != "ACTIVE"].groupby("event_id").energy.sum().reindex(t.index, fill_value=0) * 1e3
    return t


def file_events(path, det, gain, tau_us, q_min=5.0, use_cache=True):
    """One row per event of one hypathia file: S2 energy in pes, raw (e_raw), lifetime-corrected (e_lt), and with the
    (x, y) correction from the light table (e_table) or from the Kr map (e_kr); reconstructed extent (slices with
    SiPM charge >= q_min pes); MC truth."""
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, f"{det}_g{gain}_{os.path.basename(path).replace('.h5', '')}_tau{tau_us:.0f}.h5")
    if use_cache and os.path.exists(fn): return pd.read_hdf(fn, "events")

    from invisible_cities.io.pmaps_io import load_pmaps
    from invisible_cities.database.load_db import DataSiPM
    db = "next100fibers" if det == "fibers" else "next100"
    sx, sy = DataSiPM(db, 0).X.values, DataSiPM(db, 0).Y.values
    lce, krm = lce_map(det), kr_map(det, gain, tau_us)
    rows = []
    with contextlib.redirect_stdout(io.StringIO()):        # the IC fibers branch prints "HERE!" per event
        pmaps = load_pmaps(path)
    for evt, pm in pmaps.items():
        row = dict(event=evt, n_s1=len(pm.s1s), n_s2=len(pm.s2s))
        if pm.s1s:
            s1 = max(pm.s1s, key=lambda p: p.total_energy)
            t0 = s1.time_at_max_energy; row["s1e"] = sum(p.total_energy for p in pm.s1s)
        else:
            t0 = 100e3; row["s1e"] = 0.0                      # no S1 found: use the known decay time
        e_raw = e_lt = e_tab = e_kr = e_tab_h = e_kr_h = 0.0; x_all, y_all, z_all, nan_tab, nan_kr = [], [], [], 0, 0
        for s2 in pm.s2s:
            e = s2.pmts.sum_over_sensors                     # energy plane (fibers or PMTs), per slice
            q = s2.sipms.all_waveforms                       # (n_sipm, n_slice)
            ids = np.asarray(s2.sipms.ids, dtype=int)        # empty (float) when no SiPM passed the threshold
            if q.ndim != 2 or q.shape[0] != ids.size: q = np.zeros((ids.size, len(s2.times)))
            qs = q.sum(axis=0)
            with np.errstate(invalid="ignore", divide="ignore"):
                x = (sx[ids][:, None] * q).sum(axis=0) / qs
                y = (sy[ids][:, None] * q).sum(axis=0) / qs
            qt = q.sum()
            xb = (sx[ids] * q.sum(axis=1)).sum() / qt if qt > 0 else 0.0
            yb = (sy[ids] * q.sum(axis=1)).sum() / qt if qt > 0 else 0.0
            x = np.where(qs > 0, x, xb); y = np.where(qs > 0, y, yb)
            dt = (s2.times - t0) / 1e3                       # us
            el = e * np.exp(dt / tau_us)
            c_tab, c_kr = lce(x, y), krm(x, y)
            nan_tab += int(np.isnan(c_tab).sum()); nan_kr += int(np.isnan(c_kr).sum())
            c_kr = np.where(np.isnan(c_kr), c_tab, c_kr)     # empty Kr bins (edge): use the table there
            c_tab = np.where(np.isnan(c_tab), 1.0, c_tab); c_kr = np.where(np.isnan(c_kr), 1.0, c_kr)
            e_raw += e.sum(); e_lt += el.sum(); e_tab += (el / c_tab).sum(); e_kr += (el / c_kr).sum()
            # hits: each slice shared among its SiPMs in proportion to their charge, each share corrected at
            # that SiPM's (x, y). Slices without SiPM charge keep the barycentre correction.
            if ids.size:
                h_tab, h_kr = lce(sx[ids], sy[ids]), krm(sx[ids], sy[ids])
                h_kr = np.where(np.isnan(h_kr), h_tab, h_kr)
                h_tab = np.where(np.isnan(h_tab), 1.0, h_tab); h_kr = np.where(np.isnan(h_kr), 1.0, h_kr)
                with np.errstate(invalid="ignore", divide="ignore"):
                    w = q / qs
                f_tab = np.where(qs > 0, (w / h_tab[:, None]).sum(axis=0), 1 / c_tab)
                f_kr  = np.where(qs > 0, (w / h_kr[:, None]).sum(axis=0), 1 / c_kr)
            else:
                f_tab, f_kr = 1 / c_tab, 1 / c_kr
            e_tab_h += (el * f_tab).sum(); e_kr_h += (el * f_kr).sum()
            good = qs >= q_min
            x_all.append(x[good]); y_all.append(y[good]); z_all.append(dt[good] * V_DRIFT)
        x_all, y_all, z_all = (np.concatenate(v) if v else np.array([]) for v in (x_all, y_all, z_all))
        r = np.hypot(x_all, y_all)
        row.update(e_raw=e_raw, e_lt=e_lt, e_table=e_tab, e_kr=e_kr, e_table_hits=e_tab_h, e_kr_hits=e_kr_h,
                   n_nan_table=nan_tab, n_nan_kr=nan_kr,
                   r_max=r.max() if r.size else np.nan, z_min=z_all.min() if z_all.size else np.nan,
                   z_max=z_all.max() if z_all.size else np.nan)
        rows.append(row)
    ev = pd.DataFrame(rows)
    # Run/events.evt_number = 7 x nexus event_id (detsim sub-events, see CLAUDE.md); truth is per nexus event_id
    ev["event_id"] = ev.event // 7
    ev = ev.join(_truth(path), on="event_id")
    ev["file"] = paths.file_index(path)
    ev.to_hdf(fn, "events", mode="w")
    return ev


def all_events(det, gain, sample, tau_us, files=None):
    """file_events for every hypathia file of the run (or only the file numbers in `files`)."""
    fs = paths.files("hypathia", det, gain, sample)
    if files is not None: fs = [f for f in fs if paths.file_index(f) in files]
    return pd.concat([file_events(f, det, gain, tau_us) for f in fs], ignore_index=True)
