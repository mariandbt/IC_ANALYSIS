"""Plots for each step, in the style of the 2025 notebooks (python_cluster/notebooks/2025*_s2simulation_IC*.ipynb).

    from icana import plots; plots.set_style()
Every function returns the figure; plots.save(fig, name) writes work/figures/<name>.pdf and .png (for the thesis).
"""
import os
import numpy as np
import tables as tb
import matplotlib.pyplot as plt

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "figures")
EP_WIDTH_US   = 0.1    # energy-plane (fibers or PMTs) sampling: 100 ns
SIPM_WIDTH_US = 1.0    # tracking-plane SiPMs: 1 us


def set_style(font_size=20):
    """Same matplotlib settings as the 2025 notebooks."""
    plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm", "font.size": font_size,
                         "lines.linewidth": 2.5, "lines.markersize": 8, "lines.markeredgewidth": 1.0,
                         "axes.prop_cycle": plt.cycler(color=["blue", "deepskyblue", "lightcoral",
                                                              "darkseagreen", "plum"])})


def save(fig, name):
    """Save to work/figures/<name>.pdf and .png. Returns the pdf path."""
    os.makedirs(FIG_DIR, exist_ok=True)
    p = os.path.join(FIG_DIR, name)
    fig.savefig(p + ".pdf", bbox_inches="tight"); fig.savefig(p + ".png", dpi=150, bbox_inches="tight")
    return p + ".pdf"


def ep_node(h):
    """'fibrd' for fibers, 'pmtrd' for PMTs."""
    return "fibrd" if "fibrd" in h.root else "pmtrd"


def detector_label(path):
    with tb.open_file(path) as h:
        return "Fibers" if ep_node(h) == "fibrd" else "PMTs"


def event_id(path, i):
    """nexus event number of row i of the waveform arrays."""
    with tb.open_file(path) as h:
        return int(h.root.Run.events[i]["evt_number"])


# ---------------------------------------------------------------- input hits (detsim copies /MC/hits)
def hits_projections(path, i):
    """Energy deposits of event row i in z-x, z-y and x-y, one colour per particle (2025 plot)."""
    import pandas as pd
    ev = event_id(path, i)
    with tb.open_file(path) as h:
        hits = pd.DataFrame(h.root.MC.hits.read_where(f"event_id == {ev}"))
    c = {k: np.average(hits[k], weights=hits.energy) for k in "xyz"}     # energy-weighted centre
    um = lambda k, h: (h[k] - c[k]) * 1e3                                # hits relative to it, in um
    fig, axs = plt.subplots(1, 3, figsize=(30, 8))
    for _, h in hits.groupby("particle_id"):
        axs[0].plot(um("z", h), um("x", h), marker=".", ms=20); axs[1].plot(um("z", h), um("y", h), marker=".", ms=20)
        axs[2].plot(um("x", h), um("y", h), marker=".", ms=20)
    for ax, (a, b) in zip(axs, [("z", "x"), ("z", "y"), ("x", "y")]):
        ax.set_xlabel(rf"${a} - {a}_0$ ($\mu$m)"); ax.set_ylabel(rf"${b} - {b}_0$ ($\mu$m)"); ax.grid()
    axs[1].set_title(f"Event {ev}: {hits.energy.sum() * 1e3:.1f} keV at "
                     f"$(x_0, y_0, z_0)$ = ({c['x']:.0f}, {c['y']:.0f}, {c['z']:.0f}) mm")
    return fig


# ---------------------------------------------------------------- detsim waveforms
def _wf(arr, i, how):
    w = arr[i].astype(float)                       # (sensors, samples)
    if how == "sum":     return w.sum(axis=0)
    if how == "average": return w.sum(axis=0) / w.shape[0]
    if how == "highest": return w[np.argmax(w.max(axis=1))]
    raise ValueError("how must be sum, average or highest")


def waveforms(path, i, how="sum", xlim=None):
    """Energy plane (top) and SiPMs (bottom) of event row i: sum, average or highest channel (2025 plot)."""
    with tb.open_file(path) as h:
        node = ep_node(h)
        wf_ep, wf_si = _wf(h.root[node], i, how), _wf(h.root.sipmrd, i, how)
        ev = int(h.root.Run.events[i]["evt_number"])
    det = "Fibers" if node == "fibrd" else "PMTs"
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(13, 8))
    ax1.plot(np.arange(wf_ep.size) * EP_WIDTH_US, wf_ep, "-k"); ax1.text(0.02, 0.8, det, transform=ax1.transAxes)
    ax2.plot(np.arange(wf_si.size) * SIPM_WIDTH_US, wf_si, "-k"); ax2.text(0.02, 0.8, "SiPMs", transform=ax2.transAxes)
    ax1.set_ylabel("Amplitude (pes)"); ax2.set_ylabel("Amplitude (pes)"); ax2.set_xlabel(r"Time ($\mu$s)")
    ax1.grid(); ax2.grid(); ax1.set_title(f"Event {ev} {how} waveform")
    if xlim: ax1.set_xlim(*xlim)
    return fig


def fib_vs_pmt(path_fib, path_pmt, i, xlim=None):
    """Sum waveforms of the same event with fibers (red) and PMTs (black dashed) (2025 plot)."""
    with tb.open_file(path_fib) as hf, tb.open_file(path_pmt) as hp:
        ev_f, ev_p = int(hf.root.Run.events[i]["evt_number"]), int(hp.root.Run.events[i]["evt_number"])
        assert ev_f == ev_p, f"row {i} is event {ev_f} in fibers but {ev_p} in PMTs"
        wf, wp = _wf(hf.root.fibrd, i, "sum"), _wf(hp.root.pmtrd, i, "sum")
        sf, sp = _wf(hf.root.sipmrd, i, "sum"), _wf(hp.root.sipmrd, i, "sum")
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(13, 8))
    ax1.plot(np.arange(wf.size) * EP_WIDTH_US, wf, "-r", label="Fibers")
    ax1.plot(np.arange(wp.size) * EP_WIDTH_US, wp, "--k", label="PMTs")
    ax2.plot(np.arange(sf.size) * SIPM_WIDTH_US, sf, "-r", label="SiPMs (fibers run)")
    ax2.plot(np.arange(sp.size) * SIPM_WIDTH_US, sp, "--k", label="SiPMs (PMTs run)")
    for ax in (ax1, ax2): ax.set_ylabel("Amplitude (pes)"); ax.grid(); ax.legend()
    ax2.set_xlabel(r"Time ($\mu$s)"); ax1.set_title(f"Event {ev_f} sum waveform")
    if xlim: ax1.set_xlim(*xlim)
    return fig


# ---------------------------------------------------------------- hypathia: PMAPs (peaks found in the waveforms)
def pmap(path, event=None):
    """S1 (magenta) and S2 (black) peaks of one event, summed over the energy-plane sensors (2025 plot),
    with zooms on S1 and S2. event=None: first event that has both an S1 and an S2. Returns (fig, event)."""
    import pandas as pd
    s1, s2 = pd.read_hdf(path, "/PMAPS/S1"), pd.read_hdf(path, "/PMAPS/S2")
    if event is None:
        event = sorted(set(s1.event) & set(s2.event))[0]
    s1, s2 = s1[s1.event == event], s2[s2.event == event]
    fig, axs = plt.subplots(1, 3, figsize=(30, 8), gridspec_kw=dict(width_ratios=[2, 1, 1]))
    for ax, which in zip(axs, ["all", "S1", "S2"]):
        if which in ("all", "S1"):
            for _, p in s1.groupby("peak"): ax.plot(p.time / 1e3, p.ene, "m", label="S1" if which == "S1" else None)
        if which in ("all", "S2"):
            for _, p in s2.groupby("peak"): ax.plot(p.time / 1e3, p.ene, "k", label="S2" if which == "S2" else None)
        ax.set_xlabel(r"Time ($\mu$s)"); ax.grid()
    axs[0].set_ylabel("Amplitude (pes)")
    axs[0].set_title(f"{detector_label_pmap(path)}, event #{event}: "
                     f"S1 = {s1.ene.sum():.1f} pes, S2 = {s2.ene.sum():.0f} pes")
    axs[1].set_title("S1"); axs[2].set_title("S2")
    return fig, event


def detector_label_pmap(path):
    """Fibers or PMTs, from the detector_db stored in the hypathia config."""
    with tb.open_file(path) as h:
        db = dict(h.root.config.hypathia[:])[b"detector_db"]
    return "Fibers" if b"fibers" in db else "PMTs"


# ---------------------------------------------------------------- dorothea: kDST (one row per S1-S2 pair)
_DST_PANELS = [("S1e", np.linspace(0, 60, 51), "S1 energy (pes)"),
               ("S1w", np.arange(0, 800, 25), "S1 width (ns)"),
               ("S2e", np.linspace(0, 1.2e4, 51), "S2 energy (pes)"),
               ("S2w", np.linspace(0, 40, 51), r"S2 width ($\mu$s)"),
               ("S2q", np.linspace(0, 250, 51), "S2 charge (pes)"),
               ("Nsipm", np.arange(0, 17), "# SiPMs"),
               ("Z", np.linspace(0, 1500, 51), "Z (mm)")]


def dst_overview(dst, label):
    """Distributions of the kDST variables and the x-y map (2025 plots)."""
    fig, axs = plt.subplots(2, 4, figsize=(32, 14)); axs = axs.ravel()
    for ax, (col, bins, xl) in zip(axs, _DST_PANELS):
        ax.hist(dst[col], bins, histtype="step", color="r", lw=3); ax.set_xlabel(xl); ax.grid()
    h = axs[7].hist2d(dst.X, dst.Y, np.linspace(-500, 500, 26), cmin=1); fig.colorbar(h[3], ax=axs[7])
    axs[7].set_xlabel("x (mm)"); axs[7].set_ylabel("y (mm)"); axs[7].set_aspect("equal")
    fig.suptitle(f"{label}: {len(dst)} S1-S2 pairs"); fig.tight_layout()
    return fig


def dst_compare(dst_fib, dst_pmt, title=""):
    """Same panels, fibers (red) vs PMTs (black), with the ratio of the means for S1e and S2e (2025 plots)."""
    fig, axs = plt.subplots(2, 4, figsize=(32, 14)); axs = axs.ravel()
    for ax, (col, bins, xl) in zip(axs, _DST_PANELS):
        ax.hist(dst_pmt[col], bins, histtype="step", color="k", lw=3, label="PMTs")
        ax.hist(dst_fib[col], bins, histtype="step", color="r", lw=3, label="Fibers")
        if col in ("S1e", "S2e"):
            ax.set_title(rf"$\mu_{{FIB}} / \mu_{{PMT}}$ = {dst_fib[col].mean() / dst_pmt[col].mean():.2f}")
        ax.set_xlabel(xl); ax.grid(); ax.legend()
    axs[7].plot(dst_pmt.S2e, dst_pmt.S1e, ".k", ms=3, label="PMTs"); axs[7].plot(dst_fib.S2e, dst_fib.S1e, ".r", ms=3, label="Fibers")
    axs[7].set_xlabel("S2 energy (pes)"); axs[7].set_ylabel("S1 energy (pes)"); axs[7].grid(); axs[7].legend()
    fig.suptitle(title); fig.tight_layout()
    return fig


def peak_fit(fit, label, title="Kr events", xlabel="S2 energy (pes)"):
    """Histogram and Gaussian fit from fits.fit_peak, with FWHM/mu (2025 plot)."""
    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)
    ax.step(fit["x"], fit["y"], where="mid", color="k", lw=4, label=label)
    xf = np.linspace(fit["x"].min(), fit["x"].max(), 300)
    from .fits import gauss
    ax.plot(xf, gauss(xf, *fit["p"]), "-r", label="Gaussian fit")
    fwhm = 2 * np.sqrt(2 * np.log(2)) * fit["sigma"]
    ax.text(0.03, 0.75, rf"$\frac{{FWHM}}{{\mu}}$ = $\frac{{{fwhm:.0f}}}{{{fit['mu']:.0f}}}$ = {fit['fwhm_pct']:.2f} %",
            transform=ax.transAxes)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel("Counts"); ax.legend(loc="upper right", fontsize=16); ax.grid()
    return fig


def lifetime(drift_time_us, s2e, lt, label):
    """S2e vs drift time (left) and the means in equal-count groups with the exponential fit (right) (2025 plot)."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(20, 7), constrained_layout=True)
    a1.plot(drift_time_us, s2e, "or", ms=2, label=label)
    a1.set_xlabel(r"$T_{drift}$ ($\mu$s)"); a1.set_ylabel(r"$S2_e$ (pes)"); a1.set_yscale("log"); a1.grid(); a1.legend(fontsize=16)
    a2.errorbar(lt["x"], lt["y"], lt["ey"], fmt="ok", capsize=3, label="mean per group")
    t = np.linspace(lt["x"].min(), lt["x"].max(), 100)
    a2.plot(t, lt["e0"] * np.exp(-t / lt["tau_us"]), "--r",
            label=rf"$\tau$ = {lt['tau_us'] / 1e3:.2f} $\pm$ {lt['tau_err_us'] / 1e3:.2f} ms")
    a2.set_xlabel(r"$T_{drift}$ ($\mu$s)"); a2.set_ylabel(r"mean $S2_e$ (pes)"); a2.grid(); a2.legend(fontsize=16)
    fig.suptitle("Kr events: electron lifetime")
    return fig


def peak_in_z_slices(dst, rcut, bins, n=9, label="Fibers"):
    """Raw S2e peak and Gaussian fit in n equal z slices (2025 plot: 3x3). Shows the lifetime effect slice by slice."""
    from .fits import fit_peak, gauss
    d = dst[dst.R < rcut]; z = np.linspace(d.Z.min(), d.Z.max(), n + 1)
    k = int(np.ceil(np.sqrt(n))); fig, axs = plt.subplots(k, k, figsize=(10 * k, 8 * k), constrained_layout=True)
    for i, ax in enumerate(axs.ravel()):
        if i >= n: ax.axis("off"); continue
        v = d.S2e[(d.Z >= z[i]) & (d.Z < z[i + 1])].values
        f = fit_peak(v, bins)
        ax.step(f["x"], f["y"], where="mid", color="k", lw=3)
        ax.plot(f["x"], gauss(f["x"], *f["p"]), "-r")
        ax.set_title(f"{z[i]:.0f} ≤ z < {z[i + 1]:.0f} mm: {f['fwhm_pct']:.2f} %", fontsize=18)
        ax.set_xlabel("S2 energy (pes)"); ax.grid()
    fig.suptitle(f"{label}, R < {rcut} mm, raw S2e in z slices")
    return fig
