import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, Time
from sqlalchemy.orm import relationship
from app.database import Base


class DoctorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=False)
    qualification = Column(String(255), nullable=True)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Numeric(10, 2), nullable=False)
    available_days = Column(String(255), nullable=False, default="Mon,Tue,Wed,Thu,Fri")
    start_time = Column(String(5), nullable=False, default="09:00")
    end_time = Column(String(5), nullable=False, default="17:00")
    status = Column(Enum(DoctorStatus), default=DoctorStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="doctor")
