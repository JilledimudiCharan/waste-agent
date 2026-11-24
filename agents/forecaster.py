import numpy as np
from core.models import Bin, Forecast
from core import db
from core.config import (DEFAULT_RATE, COLD_START_UNCERTAINTY,
                         MIN_UNCERTAINTY, HISTORY_WINDOW)

def forecast_bin(b: Bin) -> Forecast:
    rs = db.get_readings(b.id, HISTORY_WINDOW)
    if not rs:
        raise ValueError(f"No readings for {b.id}")

    # use only readings after the last pickup (a big drop in fill)
    start = 0
    for i in range(1, len(rs)):
        if rs[i].fill < rs[i - 1].fill - 15:
            start = i
    rs = rs[start:]

    fill_now = rs[-1].fill

    if len(rs) < 4:                      # not enough history: cold start
        rate, spread, mode = DEFAULT_RATE, COLD_START_UNCERTAINTY, "cold-start"
    else:                                # learn the rate from the readings
        t = np.array([(r.ts - rs[0].ts) / 3600 for r in rs])   # hours
        y = np.array([r.fill for r in rs])
        slope, intercept = np.polyfit(t, y, 1)                 # best-fit line
        resid = y - (slope * t + intercept)
        sigma = resid.std(ddof=2)                              # how noisy the data is
        se = sigma / np.sqrt(((t - t.mean()) ** 2).sum())      # how unsure the slope is
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