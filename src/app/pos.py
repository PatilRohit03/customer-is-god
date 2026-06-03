from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .database import get_session
from .models import POSRecord
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

class POSPayload(BaseModel):
    transaction_id: str
    store_id: str
    timestamp: datetime
    basket_value_inr: float

class BulkPOSRequest(BaseModel):
    transactions: List[POSPayload]

@router.post('/ingest')
async def ingest_pos(payload: BulkPOSRequest):
    inserted = 0
    errors = []
    with get_session() as session:
        for idx, record in enumerate(payload.transactions):
            try:
                existing = session.get(POSRecord, record.transaction_id)
                if existing:
                    continue
                pos_record = POSRecord(**record.model_dump())
                session.add(pos_record)
                inserted += 1
            except SQLAlchemyError as exc:
                errors.append({'index': idx, 'transaction_id': record.transaction_id, 'error': str(exc)})
        session.commit()
    return {'inserted': inserted, 'errors': errors, 'received': len(payload.transactions)}
