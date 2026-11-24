import sqlite3
import time
import csv
from core.models import Bin, Reading
from core.config import zone_for

DB_PATH = "data/waste.db"

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row          # lets us read columns by name
    return c

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS bins(
        id TEXT PRIMARY KEY, lat REAL, lon REAL, zone TEXT, stale INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS readings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, bin_id TEXT, ts REAL, fill REAL, source TEXT);
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT, bin_id TEXT, ts REAL, level TEXT);
    """)
    c.commit()
    c.close()

def add_bin(b: Bin):
    c = connect()
    c.execute("INSERT OR REPLACE INTO bins VALUES (?,?,?,?,?)",
              (b.id, b.lat, b.lon, b.zone, int(b.stale)))
    c.commit()
    c.close()

def add_reading(bin_id, fill, source="manual", ts=None):
    r = Reading(bin_id=bin_id, ts=ts or time.time(), fill=fill, source=source)  # Pydantic checks 0-100
    c = connect()
    c.execute("INSERT INTO readings(bin_id, ts, fill, source) VALUES (?,?,?,?)",
              (r.bin_id, r.ts, r.fill, r.source))
    c.commit()
    c.close()

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
    return [Reading(bin_id=r["bin_id"], ts=r["ts"], fill=r["fill"], source=r["source"])
            for r in reversed(rows)]      # oldest first

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