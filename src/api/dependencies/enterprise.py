from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src.api.models.public.user import EnterpriseProfile
from src.api.dependencies.auth import require_user_type, UserType

async def get_enterprise_profile(
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE))
):
    # Check if user is a Response object (RedirectResponse or JSONResponse)
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return user
        
    try:
        enterprise_profile = db.query(EnterpriseProfile).filter(
            EnterpriseProfile.user_id == user["sub"]
        ).first()
        
        if not enterprise_profile:
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Enterprise profile not found"}
                )
            return RedirectResponse(
                url="/login?error=profile_not_found",
                status_code=302
            )
        
        return enterprise_profile
        
    except Exception as e:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(
                status_code=500,
                content={"detail": str(e)}
            )
        return RedirectResponse(
            url="/login?error=profile_error",
            status_code=302
        )