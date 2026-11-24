import streamlit as st
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium

from core import db
from core.config import CENTER_LAT, CENTER_LON, DEPOT, zone_for
from core.models import Bin
from core.planner import make_plan
from core.routing import road_leg

st.set_page_config(page_title="Smart Waste Routing", layout="wide")
db.init_db()
COLORS = ["#185FA5", "#8E44AD"]

def bin_color(b, f):
    if b.stale:
        return "#888888"
    if f.fill_now >= 80:
        return "#E24B4A"
    if f.fill_now >= 50:
        return "#EF9F27"
    return "#1D9E75"

plan = make_plan()
bins = plan["bins"]
st.title("Smart Waste Collection: live planner")

if "added" in st.session_state:
    info = st.session_state.pop("added")
    delta = plan["smart_km"] - info["prev_km"]
    st.success(f"{info['id']} added at {info['fill']}%. Route changed by {delta:+.1f} km.")

use_roads = st.sidebar.checkbox("Draw road-following routes (needs internet)", value=False)

# ---------- map ----------
m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=14, tiles="OpenStreetMap")
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri", name="Satellite").add_to(m)
folium.Marker(DEPOT, tooltip="Depot", icon=folium.Icon(color="black", icon="home")).add_to(m)

for b in bins:
    f, d = plan["forecasts"][b.id], plan["decisions"][b.id]
    action = "COLLECT" if d.collect else "SKIP"
    folium.CircleMarker(
        [b.lat, b.lon], radius=10, color="#000" if d.collect else "#666",
        weight=3 if d.collect else 1, fill=True, fill_color=bin_color(b, f), fill_opacity=0.9,
        tooltip=f"{b.id}: {f.fill_now}%",
        popup=folium.Popup(f"<b>{b.id}</b><br>Fill {f.fill_now}%<br>Rate {f.rate}%/h ({f.mode})"
                           f"<br>{action}: {d.reason}", max_width=260)).add_to(m)

for i, r in enumerate(plan["routes"]):
    if not r["stops"]:
        continue
    pts = [DEPOT] + [(s.lat, s.lon) for s in r["stops"]] + [DEPOT]
    if use_roads:
        line = []
        for a, c in zip(pts, pts[1:]):
            line += list(road_leg(a[0], a[1], c[0], c[1]))
    else:
        line = pts
    AntPath(line, color=COLORS[i % 2], weight=5, delay=1200).add_to(m)
    for n, s in enumerate(r["stops"], 1):
        folium.Marker([s.lat, s.lon], icon=folium.DivIcon(
            html=f'<div style="background:{COLORS[i % 2]};color:#fff;border-radius:50%;'
                 f'width:22px;height:22px;text-align:center;line-height:22px;font-weight:700;'
                 f'font-size:12px;margin-left:10px;margin-top:-26px">{n}</div>')).add_to(m)
folium.LayerControl().add_to(m)

left, right = st.columns([3, 2])
with left:
    out = st_folium(m, height=560, use_container_width=True, returned_objects=["last_clicked"])

with right:
    n_collect = sum(d.collect for d in plan["decisions"].values())
    c1, c2 = st.columns(2)
    c1.metric("Bins to collect", f"{n_collect} of {len(bins)}")
    saved = plan["fixed_km"] - plan["smart_km"]
    c2.metric("Smart route km", plan["smart_km"],
              delta=f"-{saved:.1f} vs visit-all {plan['fixed_km']}" if saved > 0 else None,
              delta_color="inverse")
    for r in plan["routes"]:
        ids = " → ".join(s.id for s in r["stops"]) or "no stops"
        warn = "  (WARNING: over capacity)" if r["over_capacity"] else ""
        st.write(f"**{r['truck']}** ({r['km']} km): {ids}{warn}")

# ---------- controls ----------
click = out.get("last_clicked") if out else None
with st.sidebar:
    st.header("Add a bin")
    fill = st.slider("Fill level %", 0, 100, 95)
    if click:
        st.write(f"Selected: {click['lat']:.5f}, {click['lng']:.5f}")
        if st.button("Add bin here", type="primary"):
            lat, lon = click["lat"], click["lng"]
            new_id = db.next_bin_id()
            db.add_bin(Bin(id=new_id, lat=lat, lon=lon, zone=zone_for(lon)))
            db.add_reading(new_id, fill, source="manual")
            st.session_state["added"] = {"id": new_id, "fill": fill, "prev_km": plan["smart_km"]}
            st.rerun()
    else:
        st.info("Click a spot on the map first.")

    st.header("Update a bin")
    if bins:
        sel = st.selectbox("Bin", [b.id for b in bins])
        new_fill = st.slider("New fill %", 0, 100, 50, key="upd")
        if st.button("Save reading"):
            db.add_reading(sel, new_fill, source="citizen", kind="correction")
            st.rerun()
        if st.button("Mark as collected"):
            db.record_pickup(sel)
            st.rerun()
        if st.button("Kill sensor (mark stale)"):
            db.set_stale(sel, True)
            st.rerun()

st.subheader("Why each bin was picked or skipped")
rows = [{"Bin": b.id, "Fill %": plan["forecasts"][b.id].fill_now,
         "Rate %/h": plan["forecasts"][b.id].rate,
         "Worst h": plan["forecasts"][b.id].worst_hours,
         "Mode": plan["forecasts"][b.id].mode,
         "Action": "COLLECT" if plan["decisions"][b.id].collect else "skip",
         "Reason": plan["decisions"][b.id].reason} for b in bins]
rows.sort(key=lambda r: r["Worst h"])
st.dataframe(rows, use_container_width=True)