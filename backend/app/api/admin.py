from fastapi import APIRouter, Depends
from app.models.user import User, Role
from app.services.auth import require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(require_role(Role.ADMIN))):
    return {"message": f"Welcome to Admin Dashboard, {current_user.full_name}", "role": "admin"}
