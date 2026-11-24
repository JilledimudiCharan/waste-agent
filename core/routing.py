import json
import urllib.request
from functools import lru_cache
from math import radians, sin, cos, asin, sqrt

ROAD_FACTOR = 1.3   # roads are longer than straight lines

def haversine_km(a, b):
    """Straight-line distance in km between (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(radians, [a[0], a[1], b[0], b[1]])
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))

def road_km(a, b):
    return haversine_km(a, b) * ROAD_FACTOR

def route_km(depot, order):
    pts = [depot] + [(s.lat, s.lon) for s in order] + [depot]
    return sum(road_km(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

def nearest_neighbour(depot, stops):
    order, current, left = [], depot, list(stops)
    while left:
        nxt = min(left, key=lambda s: road_km(current, (s.lat, s.lon)))
        order.append(nxt)
        left.remove(nxt)
        current = (nxt.lat, nxt.lon)
    return order

def two_opt(depot, order):
    best = list(order)
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                new = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if route_km(depot, new) < route_km(depot, best) - 1e-9:
                    best, improved = new, True
    return best

@lru_cache(maxsize=None)
def road_leg(lat1, lon1, lat2, lon2):
    """Road-following line between two points (free OSRM demo server, light use only)."""
    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson")
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.load(r)
        return tuple((c[1], c[0]) for c in data["routes"][0]["geometry"]["coordinates"])
    except Exception:
        return ((lat1, lon1), (lat2, lon2))   # fall back to a straight line