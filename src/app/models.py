from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class Event(SQLModel, table=True):
    event_id: str = Field(primary_key=True)
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: datetime
    zone_id: Optional[str] = None
    dwell_ms: Optional[int] = None
    is_staff: bool = False
    confidence: float = 0.0
    metadata_: Optional[dict] = Field(sa_column=Column('metadata', JSON, nullable=True), alias='metadata')

    model_config = {
        'populate_by_name': True,
        'json_schema_extra': {
            'examples': [
                {
                    'event_id': 'uuid-v4',
                    'metadata': {'queue_depth': 4}
                }
            ]
        }
    }

class VisitorSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: str
    visitor_id: str
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime] = None
    billing_seen: bool = False
    billing_first_seen: Optional[datetime] = None
    is_converted: bool = False

class POSRecord(SQLModel, table=True):
    transaction_id: str = Field(primary_key=True)
    store_id: str
    timestamp: datetime
    basket_value_inr: float

class StoreMetric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: str
    metric_name: str
    metric_value: float
    window_start: datetime
    window_end: datetime
