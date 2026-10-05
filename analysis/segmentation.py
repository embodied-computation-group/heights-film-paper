"""Piecewise-linear segmentation of a group-mean rating time series.

This is the method that set the registered segment edges (vmp_film_rating, qc/segment_film.py at tag
prereg-draft-v1), ported here so the edges can be re-estimated in the confirmatory sample (a descriptive analysis
in the preregistration).

The idea: cut the series into a fixed number of pieces and fit a separate straight line to each piece. Among all
possible cuts (each piece at least `min_length` seconds long), pick the one where the lines fit best, i.e. where
the summed squared distance between the series and the lines is smallest. Dynamic programming finds this best cut
exactly, without trying every combination one by one.
"""
import numpy as np

MIN_LENGTH = 30  # shortest allowed segment in seconds, as in the registered method


def line_costs(series, min_length=MIN_LENGTH):
    """Table of how badly one straight line fits each stretch of the series.

    costs[i, j] = sum of squared residuals of a least-squares line through series[i:j] (j not included).
    Stretches shorter than `min_length` get an infinite cost, so they are never chosen.

    The sums needed for every stretch come from running totals (cumulative sums), which makes this fast enough to
    repeat in a bootstrap.
    """
    y = np.asarray(series, float)
    n = len(y)
    x = np.arange(n, dtype=float)

    def running_total(values):
        return np.concatenate([[0.0], np.cumsum(values)])

    start, end = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    length = (end - start).astype(float)

    def stretch_sum(values):
        totals = running_total(values)
        return totals[end] - totals[start]

    sum_x, sum_xx = stretch_sum(x), stretch_sum(x * x)
    sum_y, sum_yy, sum_xy = stretch_sum(y), stretch_sum(y * y), stretch_sum(x * y)

    with np.errstate(divide="ignore", invalid="ignore"):
        spread_x = sum_xx - sum_x ** 2 / length
        spread_y = sum_yy - sum_y ** 2 / length
        co_spread = sum_xy - sum_x * sum_y / length
        costs = np.where(spread_x > 0, spread_y - co_spread ** 2 / spread_x, spread_y)

    costs[length < min_length] = np.inf
    return costs


def find_breakpoints(series, n_breakpoints=3, min_length=MIN_LENGTH):
    """The best `n_breakpoints` cut points (in seconds), giving n_breakpoints + 1 straight-line segments."""
    costs = line_costs(series, min_length)
    n = len(series)

    # best[j] = lowest total cost of covering series[0:j] with the number of segments used so far.
    best = costs[0].copy()
    where_cut = []
    for _ in range(n_breakpoints):
        total = best[:, None] + costs   # cut at i, then one more segment from i to j
        cut = np.argmin(total, axis=0)
        best = total[cut, np.arange(n + 1)]
        where_cut.append(cut)

    # Walk back from the end of the series to read off the cut points.
    breakpoints, position = [], n
    for cut in reversed(where_cut):
        position = int(cut[position])
        breakpoints.append(position)
    return sorted(breakpoints)


def bootstrap_breakpoints(ratings, n_breakpoints=3, n_boot=1000, seed=0):
    """Breakpoints of the group mean, with participant-bootstrap 95% intervals.

    `ratings` has one row per participant and one column per second. Each bootstrap round resamples participants
    with replacement, averages them and finds the breakpoints again.
    """
    ratings = np.asarray(ratings, float)
    n_people = len(ratings)
    estimate = find_breakpoints(ratings.mean(axis=0), n_breakpoints)

    rng = np.random.default_rng(seed)
    rounds = []
    for _ in range(n_boot):
        pick = rng.integers(0, n_people, n_people)
        rounds.append(find_breakpoints(ratings[pick].mean(axis=0), n_breakpoints))
    low, high = np.percentile(rounds, [2.5, 97.5], axis=0)

    return {"breakpoints": estimate, "ci_low": [float(v) for v in low], "ci_high": [float(v) for v in high]}
