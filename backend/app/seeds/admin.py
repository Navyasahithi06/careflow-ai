from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.services.auth import get_password_hash
from app.config import get_settings

settings = get_settings()


def seed_admin(db: Session):
    existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not existing:
        admin = User(
            email=settings.ADMIN_EMAIL,
            full_name="System Admin",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role=Role.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Admin seeded: {settings.ADMIN_EMAIL}")
    else:
        print("Admin already exists, skipping seed.")
