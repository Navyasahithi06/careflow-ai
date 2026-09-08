from sqlalchemy.orm import Session
from app.models.doctor import Doctor, DoctorStatus

SEED_DOCTORS = [
    {
        "full_name": "Dr. Priya Sharma",
        "specialization": "Cardiologist",
        "qualification": "MD, DM Cardiology",
        "experience_years": 12,
        "consultation_fee": 800.00,
        "available_days": "Mon,Tue,Wed,Thu,Fri",
        "start_time": "09:00",
        "end_time": "17:00",
    },
    {
        "full_name": "Dr. Rajesh Patel",
        "specialization": "General Physician",
        "qualification": "MBBS, MD Internal Medicine",
        "experience_years": 8,
        "consultation_fee": 500.00,
        "available_days": "Mon,Tue,Wed,Thu,Fri,Sat",
        "start_time": "08:00",
        "end_time": "20:00",
    },
    {
        "full_name": "Dr. Anita Desai",
        "specialization": "Dermatologist",
        "qualification": "MD Dermatology",
        "experience_years": 10,
        "consultation_fee": 700.00,
        "available_days": "Mon,Wed,Fri",
        "start_time": "10:00",
        "end_time": "18:00",
    },
    {
        "full_name": "Dr. Suresh Kumar",
        "specialization": "Orthopedic Surgeon",
        "qualification": "MS Orthopedics, FRCS",
        "experience_years": 15,
        "consultation_fee": 1000.00,
        "available_days": "Tue,Thu,Sat",
        "start_time": "09:00",
        "end_time": "15:00",
    },
    {
        "full_name": "Dr. Meera Joshi",
        "specialization": "Pediatrician",
        "qualification": "MD Pediatrics",
        "experience_years": 7,
        "consultation_fee": 600.00,
        "available_days": "Mon,Tue,Wed,Thu,Fri",
        "start_time": "09:00",
        "end_time": "16:00",
    },
    {
        "full_name": "Dr. Arjun Singh",
        "specialization": "Neurologist",
        "qualification": "MD, DM Neurology",
        "experience_years": 14,
        "consultation_fee": 1200.00,
        "available_days": "Mon,Wed,Fri",
        "start_time": "10:00",
        "end_time": "17:00",
    },
]


def seed_doctors(db: Session):
    existing_count = db.query(Doctor).count()
    if existing_count > 0:
        print(f"Already {existing_count} doctors in database, skipping seed.")
        return
    for data in SEED_DOCTORS:
        doctor = Doctor(
            full_name=data["full_name"],
            specialization=data["specialization"],
            qualification=data["qualification"],
            experience_years=data["experience_years"],
            consultation_fee=data["consultation_fee"],
            available_days=data["available_days"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            status=DoctorStatus.ACTIVE,
        )
        db.add(doctor)
    db.commit()
    print(f"Seeded {len(SEED_DOCTORS)} doctors.")
