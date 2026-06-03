from datetime import datetime
from sqlmodel import select
from .database import get_session
from .models import VisitorSession


def create_or_get_session(store_id: str, visitor_id: str, entry_timestamp: datetime) -> VisitorSession:
    with get_session() as session:
        existing = session.exec(
            select(VisitorSession)
            .where(VisitorSession.store_id == store_id)
            .where(VisitorSession.visitor_id == visitor_id)
            .where(VisitorSession.exit_timestamp.is_(None))
        ).first()
        if existing:
            return existing
        new_session = VisitorSession(
            store_id=store_id,
            visitor_id=visitor_id,
            entry_timestamp=entry_timestamp,
        )
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        return new_session


def close_session(store_id: str, visitor_id: str, exit_timestamp: datetime) -> None:
    with get_session() as session:
        existing = session.exec(
            select(VisitorSession)
            .where(VisitorSession.store_id == store_id)
            .where(VisitorSession.visitor_id == visitor_id)
            .where(VisitorSession.exit_timestamp.is_(None))
            .order_by(VisitorSession.entry_timestamp.desc())
        ).first()
        if existing:
            existing.exit_timestamp = exit_timestamp
            session.add(existing)
            session.commit()


def mark_billing_seen(store_id: str, visitor_id: str, event_timestamp: datetime) -> None:
    with get_session() as session:
        existing = session.exec(
            select(VisitorSession)
            .where(VisitorSession.store_id == store_id)
            .where(VisitorSession.visitor_id == visitor_id)
            .where(VisitorSession.exit_timestamp.is_(None))
            .order_by(VisitorSession.entry_timestamp.desc())
        ).first()
        if existing:
            existing.billing_seen = True
            existing.billing_first_seen = existing.billing_first_seen or event_timestamp
            session.add(existing)
            session.commit()
