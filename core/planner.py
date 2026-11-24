from math import ceil
from core import db
from core.config import DEPOT, TRUCKS
from core.routing import nearest_neighbour, two_opt, route_km
from agents.forecaster import forecast_bin
from agents.selector import decide

def build_routes(stops):
    stops = sorted(stops, key=lambda b: b.lon)       # split west to east
    size = ceil(len(stops) / len(TRUCKS)) if stops else 0
    routes = []
    for i, t in enumerate(TRUCKS):
        part = stops[i * size:(i + 1) * size] if size else []
        order = two_opt(DEPOT, nearest_neighbour(DEPOT, part)) if part else []
        routes.append({"truck": t["id"], "stops": order,
                       "km": round(route_km(DEPOT, order), 1) if order else 0.0,
                       "over_capacity": len(order) > t["capacity"]})
    return routes

def make_plan():
    bins = db.get_bins()
    forecasts, decisions = {}, {}
    for b in bins:
        forecasts[b.id] = forecast_bin(b)
        decisions[b.id] = decide(b, forecasts[b.id])
    chosen = [b for b in bins if decisions[b.id].collect]
    routes = build_routes(chosen)
    visit_all = build_routes(bins)
    return {"bins": bins, "forecasts": forecasts, "decisions": decisions,
            "routes": routes,
            "smart_km": round(sum(r["km"] for r in routes), 1),
            "fixed_km": round(sum(r["km"] for r in visit_all), 1)}