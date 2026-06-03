from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class EventSchema(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: datetime
    zone_id: Optional[str] = None
    dwell_ms: Optional[int] = None
    is_staff: bool
    confidence: float
    metadata: dict | None = None
