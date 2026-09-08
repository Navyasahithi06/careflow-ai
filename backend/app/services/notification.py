import asyncio
import json
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification, NotificationType
from app.services.settings import notification_enabled


class NotificationHub:
    """In-process fan-out of new notifications to active SSE subscribers.

    Runs inside the single uvicorn worker process. Publish is thread-safe:
    SSE handlers run on the event loop, business endpoints run on the
    threadpool, and publish dispatches via run_coroutine_threadsafe.
    """

    def __init__(self):
        self._subscribers = defaultdict(set)
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    def subscribe(self, user_id: int) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=2000)
        self._subscribers[user_id].add(q)
        return q

    def unsubscribe(self, user_id: int, q: asyncio.Queue):
        subs = self._subscribers.get(user_id)
        if not subs:
            return
        subs.discard(q)
        if not subs:
            self._subscribers.pop(user_id, None)

    def publish(self, user_id: int, data: dict):
        subs = self._subscribers.get(user_id)
        if not subs:
            return
        payload = json.dumps(data, ensure_ascii=False)
        for q in list(subs):
            try:
                if self._loop is not None and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(q.put(payload), self._loop)
                else:
                    q.put_nowait(payload)
            except Exception:
                continue


hub = NotificationHub()


def serialize_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "recipient_id": n.recipient_id,
        "title": n.title,
        "message": n.message,
        "notification_type": (
            n.notification_type.value
            if isinstance(n.notification_type, NotificationType)
            else str(n.notification_type)
        ),
        "reference_id": n.reference_id,
        "is_read": bool(n.is_read),
        "read_at": str(n.read_at) if n.read_at else None,
        "created_at": str(n.created_at),
    }


def create_notification(
    *,
    recipient_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    reference_id: Optional[int] = None,
    preference_key: Optional[str] = None,
) -> Optional[Notification]:
    """Best-effort notification creation in an isolated session.

    Runs in its own transaction so that any failure is rolled back without
    touching the caller's session. Never raises. Used by every notification
    trigger so notification problems can never break the surrounding business
    operation (booking, payment, token, consultation).

    When ``preference_key`` is provided and the corresponding admin setting is
    disabled, no notification is created or published (admin-controlled gate).
    """
    if preference_key and not notification_enabled(preference_key):
        return None

    try:
        db = SessionLocal()
        try:
            n = Notification(
                recipient_id=recipient_id,
                title=title,
                message=message,
                notification_type=notification_type,
                reference_id=reference_id,
            )
            db.add(n)
            db.commit()
            db.refresh(n)
        except Exception:
            db.rollback()
            return None
        finally:
            db.close()
    except Exception:
        return None

    hub.publish(n.recipient_id, serialize_notification(n))
    return n


def _admin_ids(db: Session) -> list[int]:
    from app.models.user import User, Role
    return [u.id for u in db.query(User).filter(User.role == Role.ADMIN).all()]


def notify_payment_success(
    *,
    patient_id: int,
    amount: float,
    currency: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reference_id: Optional[int] = None,
):
    return create_notification(
        recipient_id=patient_id,
        title="Payment Successful",
        message=(
            f"Your payment of {currency} {amount:,.2f} for Dr. {doctor_name} "
            f"on {appointment_date} at {appointment_time} was successful."
        ),
        notification_type=NotificationType.PAYMENT_SUCCESS,
        reference_id=reference_id,
        preference_key="appointment_confirmed",
    )


def notify_appointment_confirmed(
    *,
    patient_id: int,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reference_id: Optional[int] = None,
):
    return create_notification(
        recipient_id=patient_id,
        title="Appointment Confirmed",
        message=(
            f"Your appointment with Dr. {doctor_name} on {appointment_date} "
            f"at {appointment_time} is confirmed."
        ),
        notification_type=NotificationType.APPOINTMENT_CONFIRMED,
        reference_id=reference_id,
        preference_key="appointment_confirmed",
    )


def notify_token_called(
    *,
    patient_id: int,
    doctor_name: str,
    token_number: int,
    reference_id: Optional[int] = None,
):
    return create_notification(
        recipient_id=patient_id,
        title="Token Called",
        message=(
            f"Your token #{token_number} is now called. "
            f"Please proceed to Dr. {doctor_name}."
        ),
        notification_type=NotificationType.TOKEN_CALLED,
        reference_id=reference_id,
        preference_key="token_called",
    )


def notify_consultation_completed(
    *,
    patient_id: int,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reference_id: Optional[int] = None,
):
    return create_notification(
        recipient_id=patient_id,
        title="Consultation Completed",
        message=(
            f"Your consultation with Dr. {doctor_name} on {appointment_date} "
            f"at {appointment_time} has been completed."
        ),
        notification_type=NotificationType.CONSULTATION_COMPLETED,
        reference_id=reference_id,
        preference_key="consultation_completed",
    )


def notify_admin_new_patient(
    *,
    admin_ids: list[int],
    patient_name: str,
    patient_email: str,
    reference_id: Optional[int] = None,
):
    for aid in admin_ids:
        create_notification(
            recipient_id=aid,
            title="New Patient Registered",
            message=f"{patient_name} ({patient_email}) just registered.",
            notification_type=NotificationType.NEW_PATIENT_REGISTERED,
            reference_id=reference_id,
            preference_key="new_patient_registered",
        )


def notify_admin_payment_received(
    *,
    admin_ids: list[int],
    amount: float,
    currency: str,
    patient_name: str,
    doctor_name: str,
    reference_id: Optional[int] = None,
):
    for aid in admin_ids:
        create_notification(
            recipient_id=aid,
            title="Payment Received",
            message=(
                f"Payment of {currency} {amount:,.2f} received from {patient_name} "
                f"for Dr. {doctor_name}."
            ),
            notification_type=NotificationType.PAYMENT_SUCCESS,
            reference_id=reference_id,
            preference_key="payment_received",
        )