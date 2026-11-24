from core.models import Bin, Forecast, Decision
from core.config import NEXT_VISIT_HOURS

def decide(b: Bin, f: Forecast) -> Decision:
    note = " (new bin, little history, wide margin)" if f.mode == "cold-start" else ""
    if b.stale:
        return Decision(bin_id=b.id, collect=True, worst_hours=f.worst_hours,
                        reason="Sensor silent, priority raised")
    if f.worst_hours < NEXT_VISIT_HOURS:
        return Decision(bin_id=b.id, collect=True, worst_hours=f.worst_hours,
                        reason=f"Could overflow in {f.worst_hours} h, before next visit{note}")
    return Decision(bin_id=b.id, collect=False, worst_hours=f.worst_hours,
                    reason=f"Safe for at least {f.worst_hours} h{note}")