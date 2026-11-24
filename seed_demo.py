import random
import time
from core import db
from core.models import Bin
from core.config import CENTER_LAT, CENTER_LON, zone_for

random.seed(42)
db.init_db()
now = time.time()

for i in range(1, 31):
    lon = round(CENTER_LON + random.uniform(-0.012, 0.012), 5)
    lat = round(CENTER_LAT + random.uniform(-0.01, 0.01), 5)
    db.add_bin(Bin(id=f"B{i}", lat=lat, lon=lon, zone=zone_for(lon)))

    rate = random.uniform(0.5, 4.0)                       # this bin's hidden true rate
    fill_now = random.uniform(max(15, rate * 12 + 2), 95)
    for h in range(12, -1, -1):                           # 12 hourly readings up to now
        noise = 0 if h == 0 else random.uniform(-1, 1)
        fill = min(100, max(0, fill_now - rate * h + noise))
        db.add_reading(f"B{i}", round(fill, 1), source="simulated", ts=now - h * 3600)

# one brand new bin with a single reading, to show the cold start
db.add_bin(Bin(id="B31", lat=16.735, lon=82.215, zone=zone_for(82.215)))
db.add_reading("B31", 90, source="manual")

print("Seeded 31 bins with history")