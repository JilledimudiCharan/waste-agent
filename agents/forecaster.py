import numpy as np
from core.models import Bin, Forecast
from core import db
from core.config import (DEFAULT_RATE, COLD_START_UNCERTAINTY,
                         MIN_UNCERTAINTY, HISTORY_WINDOW)

def forecast_bin(b: Bin) -> Forecast:
    rs = db.get_readings(b.id, HISTORY_WINDOW)
    if not rs:
        return Forecast(bin_id=b.id, fill_now=50.0, rate=DEFAULT_RATE, worst_hours=0.0,
                        best_hours=0.0, n_readings=0, mode="no-data")

    # history restarts after a pickup or a correction
    start = 0
    for i, r in enumerate(rs):
        if r.kind in ("pickup", "correction"):
            start = i
    rs = rs[start:]
    fill_now = rs[-1].fill
    span = rs[-1].ts - rs[0].ts

    if len(rs) < 4 or span < 1800:          # not enough history yet
        rate, spread, mode = DEFAULT_RATE, COLD_START_UNCERTAINTY, "cold-start"
    else:
        t = np.array([(r.ts - rs[0].ts) / 3600 for r in rs])
        y = np.array([r.fill for r in rs])
        slope, intercept = np.polyfit(t, y, 1)
        resid = y - (slope * t + intercept)
        sigma = resid.std(ddof=2)
        se = sigma / np.sqrt(((t - t.mean()) ** 2).sum())
        rate = max(float(slope), 0.1)
        spread = max(2 * se / rate, MIN_UNCERTAINTY)
        mode = "learned"

    remaining = 100 - fill_now
    worst_rate = rate * (1 + spread)
    best_rate = rate * max(1 - spread, 0.2)
    return Forecast(bin_id=b.id, fill_now=round(fill_now, 1), rate=round(rate, 2),
                    worst_hours=round(remaining / worst_rate, 1),
                    best_hours=round(remaining / best_rate, 1),
                    n_readings=len(rs), mode=mode)