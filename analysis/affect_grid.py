"""Where on the valence x arousal grid people spent their time (EXPLORATORY, descriptive).

Ported from vmp_film_rating qc/plot_affect_grid.py (the per-segment maps tried on the exploratory data).

Occupancy = share of viewing time in each 2 x 2-unit cell of the 0-100 grid (50 x 50 cells), lightly smoothed
(Gaussian, sigma 4 rating units, reflected at the edges of the scale). Each participant counts equally: their own
map adds up to one before the maps are summed, so people with more samples do not dominate (1 Hz samples follow
each other closely and are not independent observations).
"""
import numpy as np
from scipy.ndimage import gaussian_filter

BINS = 50              # 2 rating units per cell
SMOOTHING_UNITS = 4.0  # sigma of the Gaussian smoothing, in rating units


def occupancy(valence, arousal, smooth=True):
    """Percentage of (participant-weighted) time in each cell; grid[valence_bin, arousal_bin], adds up to 100.

    `valence` and `arousal` are lists (or arrays) with one series per participant.
    """
    total = np.zeros((BINS, BINS))
    for v, a in zip(valence, arousal):
        v, a = np.asarray(v, float), np.asarray(a, float)
        valid = np.isfinite(v) & np.isfinite(a)
        if not valid.any():
            continue
        counts, _, _ = np.histogram2d(v[valid], a[valid], bins=BINS, range=[[0, 100], [0, 100]])
        total += counts / counts.sum()
    if smooth:
        total = gaussian_filter(total, sigma=SMOOTHING_UNITS / (100 / BINS), mode="reflect")
    return 100 * total / total.sum()
