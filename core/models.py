from pydantic import BaseModel, Field

class Bin(BaseModel):
    id: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    zone: str = "A"
    stale: bool = False          # True if the sensor went silent

class Reading(BaseModel):
    bin_id: str
    ts: float                    # time in seconds
    fill: float = Field(ge=0, le=100)
    source: str = "manual"       # sensor, driver, citizen, csv, simulated

class Forecast(BaseModel):
    bin_id: str
    fill_now: float
    rate: float                  # % per hour (best estimate)
    worst_hours: float           # fastest it could overflow
    best_hours: float            # slowest it could overflow
    n_readings: int
    mode: str                    # "learned" or "cold-start"

class Decision(BaseModel):
    bin_id: str
    collect: bool
    worst_hours: float
    reason: str