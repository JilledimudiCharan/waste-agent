from core import db
from agents.forecaster import forecast_bin
from agents.selector import decide

bins = db.get_bins()
collect = 0
for b in bins:
    f = forecast_bin(b)
    d = decide(b, f)
    collect += d.collect
    print(f"{b.id:4} now={f.fill_now:5.1f}%  rate={f.rate:4.2f}/h ({f.mode:10}) "
          f"worst={f.worst_hours:6.1f}h  {'COLLECT' if d.collect else 'skip   '}  {d.reason}")

print(f"\nCollect {collect} of {len(bins)} bins")