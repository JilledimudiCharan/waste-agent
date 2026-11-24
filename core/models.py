from pydantic import BaseModel, Field

class Bin(BaseModel):
    id: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    zone: str = "A"
    stale: bool = False

class Reading(BaseModel):
    bin_id: str
    ts: float
    fill: float = Field(ge=0, le=100)
    source: str = "manual"      # sensor, driver, citizen, csv, simulated
    kind: str = "reading"       # reading, pickup, correction

class Forecast(BaseModel):
    bin_id: str
    fill_now: float
    rate: float
    worst_hours: float
    best_hours: float
    n_readings: int
    mode: str                   # learned, cold-start, no-data

class Decision(BaseModel):
    bin_id: str
    collect: bool
    worst_hours: float
    reason: str