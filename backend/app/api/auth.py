from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from app.schemas.auth import UserRegister, UserLogin, AdminLogin, TokenResponse, UserResponse
from app.services.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_role
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        phone=payload.phone,
        role=Role.PATIENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        from app.services.notification import _admin_ids, notify_admin_new_patient
        notify_admin_new_patient(
            admin_ids=_admin_ids(db),
            patient_name=user.full_name,
            patient_email=user.email,
            reference_id=user.id,
        )
    except Exception:
        pass
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.role == Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admins must use admin login")
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        role=user.role.value,
        user_id=user.id,
        full_name=user.full_name,
    )


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: AdminLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not an admin account")
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        role=user.role.value,
        user_id=user.id,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
