from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from app.schemas.user import ProfileUpdate
from app.schemas.auth import UserResponse
from app.services.auth import require_role

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/dashboard")
def user_dashboard(current_user: User = Depends(require_role(Role.PATIENT))):
    return {"message": f"Welcome to your Dashboard, {current_user.full_name}", "role": "patient"}


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(require_role(Role.PATIENT))):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(payload: ProfileUpdate, current_user: User = Depends(require_role(Role.PATIENT)), db: Session = Depends(get_db)):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    db.commit()
    db.refresh(current_user)
    return current_user
