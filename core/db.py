import sqlite3
import time
import csv
from core.models import Bin, Reading
from core.config import zone_for

DB_PATH = "data/waste.db"

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS bins(
        id TEXT PRIMARY KEY, lat REAL, lon REAL, zone TEXT, stale INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS readings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, bin_id TEXT, ts REAL, fill REAL,
        source TEXT, kind TEXT DEFAULT 'reading');
    """)
    c.commit()
    c.close()

def add_bin(b: Bin):
    c = connect()
    c.execute("INSERT OR REPLACE INTO bins VALUES (?,?,?,?,?)",
              (b.id, b.lat, b.lon, b.zone, int(b.stale)))
    c.commit()
    c.close()

def set_stale(bin_id, value=True):
    c = connect()
    c.execute("UPDATE bins SET stale=? WHERE id=?", (int(value), bin_id))
    c.commit()
    c.close()

def add_reading(bin_id, fill, source="manual", kind="reading", ts=None):
    r = Reading(bin_id=bin_id, ts=ts or time.time(), fill=fill, source=source, kind=kind)
    c = connect()
    c.execute("INSERT INTO readings(bin_id, ts, fill, source, kind) VALUES (?,?,?,?,?)",
              (r.bin_id, r.ts, r.fill, r.source, r.kind))
    c.commit()
    c.close()

def record_pickup(bin_id):
    add_reading(bin_id, 0, source="driver", kind="pickup")
    set_stale(bin_id, False)

def get_bins():
    c = connect()
    rows = c.execute("SELECT * FROM bins").fetchall()
    c.close()
    return [Bin(id=r["id"], lat=r["lat"], lon=r["lon"], zone=r["zone"],
                stale=bool(r["stale"])) for r in rows]

def get_readings(bin_id, limit=24):
    c = connect()
    rows = c.execute("SELECT * FROM readings WHERE bin_id=? ORDER BY ts DESC LIMIT ?",
                     (bin_id, limit)).fetchall()
    c.close()
    return [Reading(bin_id=r["bin_id"], ts=r["ts"], fill=r["fill"],
                    source=r["source"], kind=r["kind"]) for r in reversed(rows)]

def next_bin_id():
    ids = [int(b.id[1:]) for b in get_bins() if b.id[1:].isdigit()]
    return f"B{max(ids, default=0) + 1}"

def import_bins_csv(path):
    """CSV columns: id, lat, lon, and optionally fill"""
    n = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            lon = float(row["lon"])
            add_bin(Bin(id=row["id"], lat=float(row["lat"]), lon=lon, zone=zone_for(lon)))
            if row.get("fill"):
                add_reading(row["id"], float(row["fill"]), source="csv")
            n += 1
    return n