import json
import random

random.seed(42)  # makes the "random" numbers the same every run

CENTER_LAT, CENTER_LON = 16.73, 82.21  # change to your own area later

bins = []
for i in range(1, 31):
    lat = CENTER_LAT + random.uniform(-0.01, 0.01)
    lon = CENTER_LON + random.uniform(-0.012, 0.012)
    if lon < CENTER_LON - 0.004:
        zone = "A"
    elif lon < CENTER_LON + 0.004:
        zone = "B"
    else:
        zone = "C"
    bins.append({
        "id": f"B{i}",
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "zone": zone,
        "fill": round(random.uniform(15, 95), 1),   # % full right now
        "rate": round(random.uniform(0.5, 5.0), 1), # % added per hour
    })

trucks = [
    {"id": "T1", "capacity_bins": 10, "shift_hours": 6},
    {"id": "T2", "capacity_bins": 10, "shift_hours": 6},
]
depot = {"lat": CENTER_LAT, "lon": CENTER_LON}

with open("data/city.json", "w") as f:
    json.dump({"depot": depot, "bins": bins, "trucks": trucks}, f, indent=2)

print(f"Saved {len(bins)} bins and {len(trucks)} trucks")