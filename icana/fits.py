"""Fits used in the 2025 notebooks (python_cluster/notebooks/20250614_s2simulation_ICdorothea.ipynb)."""
import numpy as np
from scipy.optimize import curve_fit

FWHM_OVER_SIGMA = 2 * np.sqrt(2 * np.log(2))

def gauss(x, a, mu, sigma):
    return a * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def fit_peak(values, bins, weighted=False):
    """Histogram `values` and fit one Gaussian. Returns dict with mu, sigma, their errors and FWHM/mu in %.
    weighted=False reproduces the 2025 notebook (unweighted least squares on the bin contents);
    weighted=True uses Poisson errors sqrt(N) per bin."""
    y, edges = np.histogram(values, bins)
    x = 0.5 * (edges[1:] + edges[:-1])
    p0 = [y.max(), np.mean(values), np.std(values)]
    sig = np.sqrt(np.maximum(y, 1)) if weighted else None
    p, cov = curve_fit(gauss, x, y, p0=p0, sigma=sig, maxfev=100000)
    e = np.sqrt(np.diag(cov))
    res = FWHM_OVER_SIGMA * abs(p[2]) / p[1] * 100
    res_err = res * np.hypot(e[2] / p[2], e[1] / p[1])
    return dict(x=x, y=y, p=p, mu=p[1], mu_err=e[1], sigma=abs(p[2]), sigma_err=e[2],
                n=len(values), fwhm_pct=res, fwhm_pct_err=res_err)

def binned_means(x, y, n):
    """Sort by x, split into n equal-count groups, return group means (as in the 2025 notebook)."""
    idx = np.argsort(x); m = len(x) // n
    xs, ys = x[idx][: m * n].reshape(n, m), y[idx][: m * n].reshape(n, m)
    return xs.mean(1), ys.mean(1), ys.std(1) / np.sqrt(m)

def fit_lifetime(drift_time_us, energy, n=10, weighted=False):
    """Straight-line fit of ln(<E>) vs drift time on n equal-count groups. Returns tau in us and its error.
    weighted=False reproduces the 2025 notebook (np.polyfit without weights)."""
    x, y, ey = binned_means(np.asarray(drift_time_us), np.asarray(energy), n)
    (slope, icpt), cov = np.polyfit(x, np.log(y), 1, w=(y / ey) if weighted else None, cov=True)
    tau = -1 / slope
    return dict(x=x, y=y, ey=ey, tau_us=tau, tau_err_us=np.sqrt(cov[0, 0]) / slope**2, e0=np.exp(icpt))
