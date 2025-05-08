from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.api.models.public.user import EnterpriseProfile
from src.api.dependencies.auth import require_user_type, UserType

async def get_enterprise_profile(
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE))
):
    enterprise_profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == user["sub"]
    ).first()
    
    if not enterprise_profile:
        raise HTTPException(
            status_code=404,
            detail="Enterprise profile not found"
        )
    
    return enterprise_profile