import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, BigInteger, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class AttachmentEntityType(str, enum.Enum):
    MEDICAL_RECORD = "medical_record"
    CONSULTATION = "consultation"


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    mime_type = Column(String(120), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = relationship("User", foreign_keys=[uploaded_by])
    entity_links = relationship("RecordAttachment", back_populates="attachment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_attachments_uploaded_by", "uploaded_by"),
        Index("ix_attachments_created", "created_at"),
    )


class RecordAttachment(Base):
    __tablename__ = "record_attachments"

    id = Column(Integer, primary_key=True, index=True)
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=False)
    entity_type = Column(Enum(AttachmentEntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attachment = relationship("Attachment", back_populates="entity_links")

    __table_args__ = (
        UniqueConstraint("attachment_id", name="uq_record_attachments_attachment"),
        Index("ix_record_attachments_entity", "entity_type", "entity_id"),
    )
