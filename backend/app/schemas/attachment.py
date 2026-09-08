from pydantic import BaseModel
from typing import Optional


class AttachmentLink(BaseModel):
    attachment_id: int


class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    mime_type: str
    size_bytes: int
    uploaded_by: int
    created_at: str

    class Config:
        from_attributes = True


class EnrichedAttachmentResponse(BaseModel):
    id: int
    file_name: str
    mime_type: str
    size_bytes: int
    created_at: str
