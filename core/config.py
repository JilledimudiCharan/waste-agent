CENTER_LAT, CENTER_LON = 16.73, 82.21   # your area's centre (change later)
NEXT_VISIT_HOURS = 24        # if we skip a bin, the next chance to collect is in 24 h
DEFAULT_RATE = 2.0           # % per hour, used for a brand new bin
COLD_START_UNCERTAINTY = 0.6 # wide safety margin when we know little
MIN_UNCERTAINTY = 0.15       # never less than 15% margin
HISTORY_WINDOW = 24          # how many recent readings to learn from

def zone_for(lon):
    if lon < CENTER_LON - 0.004:
        return "A"
    if lon < CENTER_LON + 0.004:
        return "B"
    return "C"