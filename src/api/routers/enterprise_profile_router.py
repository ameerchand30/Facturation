from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from src.core.shared import templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request

from src.database import get_db
from src.api.models.public.user import EnterpriseProfile
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
# Schemas
from src.api.schemas.enterprise_profile import EnterpriseProfileUpdate

from src.api.utils.auth_utils import check_authorization

enterprise_profile_router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise"],
    responses={404: {"description": "Not found"}},
)

@enterprise_profile_router.get("/profile", response_class=HTMLResponse, name="enterprise_profile")
async def enterprise_profile(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    print("Fetching enterprise profile",request.session.get("user_id"))
    profile = db.query(EnterpriseProfile).filter_by(user_id=user["sub"]).first()
    return templates.TemplateResponse(
        "pages/enterprise_profile.html",
        {"request": request, "profile": profile, "current_page": "enterprise_profile", "user": user}    
    )

@enterprise_profile_router.post("/profile/update", response_model=dict, name="update_enterprise_profile")
async def update_enterprise_profile(
    profile_data: EnterpriseProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE))
):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    profile = db.query(EnterpriseProfile).filter_by(user_id=user["sub"]).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Enterprise profile not found")
    
    # Update profile with schema data
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    try:
        db.commit()
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@enterprise_profile_router.post("/profile/upload-logo", response_model=dict, name="upload_enterprise_logo")
async def upload_logo(
    request: Request,
    db: Session = Depends(get_db),
    logo: UploadFile = File(...),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE))
):

    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    profile = db.query(EnterpriseProfile).filter_by(user_id=user["sub"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Enterprise profile not found")
    
    try:
        # Handle logo upload
        file_location = f"static/img/enterprise_profile_images/{logo.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await logo.read())
        
        profile.logo = logo.filename
        db.commit()
        
        return {
            "success": True,
            "message": "Logo uploaded successfully",
            "logo_path": file_location
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))