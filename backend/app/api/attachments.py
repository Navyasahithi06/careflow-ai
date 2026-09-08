import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, Role
from app.models.attachment import Attachment, RecordAttachment, AttachmentEntityType
from app.models.medical_record import MedicalRecord
from app.models.consultation_note import ConsultationNote
from app.schemas.attachment import AttachmentLink, AttachmentResponse, EnrichedAttachmentResponse
from app.services.auth import get_current_user, require_role

settings = get_settings()

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

# Allowed MIME types -> canonical file extension. Reports/prescriptions are typically
# PDFs or images; a small set of common office/text formats is also permitted.
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/octet-stream": "",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _upload_root() -> str:
    if os.path.isabs(settings.UPLOAD_DIR):
        root = settings.UPLOAD_DIR
    else:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root = os.path.join(backend_dir, settings.UPLOAD_DIR)
    os.makedirs(root, exist_ok=True)
    return root


def _sanitize_original_name(filename: str) -> str:
    if not filename:
        return "file"
    base = os.path.basename(filename.replace("\\", "/"))
    base = "".join(c for c in base if c.isprintable() and c not in '<>:"/\\|?*')
    base = base.strip().strip(".")
    return base[:150] or "file"


def _resolve_entity_access(db: Session, entity_type: str, entity_id: int, current_user: User):
    try:
        et = AttachmentEntityType(entity_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    if et == AttachmentEntityType.MEDICAL_RECORD:
        entity = db.query(MedicalRecord).filter(MedicalRecord.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Medical record not found")
        owner_id = entity.patient_id
    else:
        entity = db.query(ConsultationNote).filter(ConsultationNote.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Consultation not found")
        owner_id = entity.patient_id

    if current_user.role != Role.ADMIN and owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return et


def _attachment_to_response(a: Attachment) -> EnrichedAttachmentResponse:
    return EnrichedAttachmentResponse(
        id=a.id,
        file_name=a.file_name,
        mime_type=a.mime_type,
        size_bytes=a.size_bytes,
        created_at=str(a.created_at),
    )


@router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    mime = (file.content_type or "application/octet-stream").lower()
    if mime not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime}. Allowed: pdf, jpg/png/webp, txt, csv, doc/docx",
        )

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds the {MAX_FILE_SIZE // (1024 * 1024)} MB limit")

    original_name = _sanitize_original_name(file.filename)
    ext = ALLOWED_TYPES[mime]
    stored_name = uuid.uuid4().hex + (ext or os.path.splitext(original_name)[1].lower()[:10])

    root = _upload_root()
    target_path = os.path.join(root, stored_name)

    size_bytes = 0
    try:
        with open(target_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_FILE_SIZE:
                    out.close()
                    os.remove(target_path)
                    raise HTTPException(status_code=400, detail="File exceeds the 5 MB limit")
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(status_code=500, detail="Failed to store file")

    if size_bytes == 0:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(status_code=400, detail="Empty file")

    attachment = Attachment(
        file_name=original_name,
        stored_name=stored_name,
        mime_type=mime,
        size_bytes=size_bytes,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return AttachmentResponse(
        id=attachment.id,
        file_name=attachment.file_name,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,
        uploaded_by=attachment.uploaded_by,
        created_at=str(attachment.created_at),
    )


@router.post("/entity/{entity_type}/{entity_id}", response_model=list[EnrichedAttachmentResponse])
def attach_attachment(
    entity_type: str,
    entity_id: int,
    payload: AttachmentLink,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    et = _resolve_entity_access(db, entity_type, entity_id, current_user)

    attachment = db.query(Attachment).filter(Attachment.id == payload.attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    existing = db.query(RecordAttachment).filter(RecordAttachment.attachment_id == payload.attachment_id).first()
    if existing:
        if existing.entity_type == et and existing.entity_id == entity_id:
            raise HTTPException(status_code=409, detail="Attachment already linked to this entity")
        raise HTTPException(status_code=409, detail="Attachment is already linked to another entity")

    db.add(RecordAttachment(
        attachment_id=attachment.id,
        entity_type=et,
        entity_id=entity_id,
    ))
    db.commit()

    return _list_attachments_for_entity(db, entity_type, entity_id, current_user)


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[EnrichedAttachmentResponse])
def list_entity_attachments(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _resolve_entity_access(db, entity_type, entity_id, current_user)
    return _list_attachments_for_entity(db, entity_type, entity_id, current_user)


def _list_attachments_for_entity(db, entity_type: str, entity_id: int, current_user: User) -> list[EnrichedAttachmentResponse]:
    try:
        et = AttachmentEntityType(entity_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity type")
    links = db.query(RecordAttachment).filter(
        RecordAttachment.entity_type == et,
        RecordAttachment.entity_id == entity_id,
    ).order_by(RecordAttachment.created_at.asc()).all()
    result = []
    for link in links:
        att = db.query(Attachment).filter(Attachment.id == link.attachment_id).first()
        if att:
            result.append(_attachment_to_response(att))
    return result


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    link = db.query(RecordAttachment).filter(RecordAttachment.attachment_id == attachment_id).first()
    if link:
        _resolve_entity_access(db, link.entity_type.value if isinstance(link.entity_type, AttachmentEntityType) else str(link.entity_type), link.entity_id, current_user)
    elif current_user.role != Role.ADMIN and attachment.uploaded_by != current_user.id:
        # Attachment not yet linked to an entity: only the uploader (or an admin) may download.
        raise HTTPException(status_code=403, detail="Not authorized")

    root = _upload_root()
    path = os.path.join(root, attachment.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path,
        media_type=attachment.mime_type,
        filename=attachment.file_name,
    )


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    link = db.query(RecordAttachment).filter(RecordAttachment.attachment_id == attachment_id).first()
    if link:
        _resolve_entity_access(
            db,
            link.entity_type.value if isinstance(link.entity_type, AttachmentEntityType) else str(link.entity_type),
            link.entity_id,
            current_user,
        )
    elif current_user.role != Role.ADMIN and attachment.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    root = _upload_root()
    path = os.path.join(root, attachment.stored_name)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    db.delete(attachment)
    db.commit()
    return {"message": "Attachment deleted"}
