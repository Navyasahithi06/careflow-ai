import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.services.auth import decode_token, get_current_user
from app.services.notification import hub, serialize_notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def current_user_from_sse(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT from a query param (SSE can't set headers) or the
    Authorization header as a fallback."""
    auth = request.headers.get("Authorization", "")
    if not token and auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def _to_response(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=n.id,
        recipient_id=n.recipient_id,
        title=n.title,
        message=n.message,
        notification_type=(n.notification_type.value if hasattr(n.notification_type, "value") else str(n.notification_type)),
        reference_id=n.reference_id,
        is_read=bool(n.is_read),
        read_at=str(n.read_at) if n.read_at else None,
        created_at=str(n.created_at),
    )


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
    ).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()
    return [_to_response(n) for n in query]


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read.is_(False),
    ).count()
    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n or n.recipient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not n.is_read:
        n.is_read = True
        n.read_at = datetime.utcnow()
        db.commit()
        db.refresh(n)
    return _to_response(n)


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read.is_(False),
    ).update({"is_read": True, "read_at": datetime.utcnow()}, synchronize_session=False)
    db.commit()
    return {"updated": result}


@router.get("/stream")
async def notification_stream(
    request: Request,
    current_user: User = Depends(current_user_from_sse),
):
    async def event_generator():
        q = hub.subscribe(current_user.id)
        hub.set_loop(asyncio.get_running_loop())
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"event: notification\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                try:
                    if await request.is_disconnected():
                        break
                except Exception:
                    pass
        finally:
            hub.unsubscribe(current_user.id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")