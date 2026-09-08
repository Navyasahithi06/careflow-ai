from pydantic import BaseModel
from typing import Optional


class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    title: str
    message: str
    notification_type: str
    reference_id: Optional[int] = None
    is_read: bool
    read_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True