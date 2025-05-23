from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from typing import Optional
from sqlalchemy.orm import Session
from src.configDict import Setting, oauth
from src.api.models.public.user import UserType, User
from src.database import get_db
from src.core.shared import templates
from src.api.dependencies.auth import get_current_user

from datetime import datetime, timedelta 
import jwt


auth_router = APIRouter()
settings = Setting()

@auth_router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("pages/User/login/login.html", {"request": request})
@auth_router.get("/register")
async def register(request: Request):
    return templates.TemplateResponse("pages/User/login/register.html", {"request": request})
@auth_router.get("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[dict] = Depends(get_current_user)
):
    try:
        # Clear session data
        request.session.clear()

        # Create response
        response = RedirectResponse(
            url="/login",
            status_code=302
        )

        # Clear all authentication cookies
        response.delete_cookie(
            key="access_token",
            path="/",
            domain=None,
            secure=True,
            httponly=True,
            samesite="lax"
        )
        
        # Clear refresh token if you have one
        response.delete_cookie(
            key="refresh_token",
            path="/",
            domain=None,
            secure=True,
            httponly=True,
            samesite="lax"
        )

        # Clear any other session cookies
        response.delete_cookie(
            key="session",
            path="/",
            domain=None,
            secure=True,
            httponly=True,
            samesite="lax"
        )

        # Log the logout event if you want to track it
        if current_user:
            print(f"User logged out: {current_user.get('email', 'Unknown')}")

        return response

    except Exception as e:
        print(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during logout"
        )

@auth_router.get("/login/{provider}/{user_type}")
            #get /login/google/enterprise
async def login(request: Request, provider: str, user_type: UserType):
    # Store user_type in session for callback
    request.session['user_type'] = user_type
    
    # Get OAuth client
    client = getattr(oauth, provider, None)
    if not client:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    # Redirect to provider's login
    redirect_uri = request.url_for('auth_callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@auth_router.get("/auth/callback/{provider}")
async def auth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    try:
        # Get OAuth client
        client = getattr(oauth, provider, None)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        # Get token and user info
        token = await client.authorize_access_token(request)
        
        # Different providers return user info in different ways
        if provider == "google":
            userinfo = token.get('userinfo')
            if not userinfo:
                # Fetch user info if not in token
                userinfo = await client.userinfo()
        else:
            # Handle other providers here
            raise HTTPException(status_code=400, detail="Provider not supported")
        
        # Get user_type from session
        user_type = request.session.get('user_type')
        if not user_type:
            raise HTTPException(status_code=400, detail="User type not specified")
        
        # Find or create user
        db_user = db.query(User).filter_by(
            email=userinfo['email'],
            auth_provider=provider
        ).first()
        
        if not db_user:
            db_user = User(
                email=userinfo['email'],
                name=userinfo.get('name'),
                picture=userinfo.get('picture'),
                auth_provider=provider,
                provider_user_id=userinfo['sub'],
                user_type=user_type
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
         # Get user_type from session and convert back to enum
        user_type_str = request.session.get('user_type')
        if not user_type_str:
            raise HTTPException(status_code=400, detail="User type not specified")
        
        user_type = UserType(user_type_str)  # Convert string back to enum
        # Create JWT token
        token_data = {
            "sub": str(db_user.id),
            "name": db_user.name,
            "picture": db_user.picture,
            "email": db_user.email,
            "user_type": user_type_str,  # Use the string value from session
            "exp": datetime.utcnow() + timedelta(hours=4),  # Add expiration
            "google_access_token": token.get('access_token')  # Add Google access token if needed
        }
        token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)
        
# Redirect to the appropriate dashboard route
        redirect_url = (
            "/client/dashboard" if user_type == UserType.CLIENT 
            else "/enterprise/dashboard"
        )
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite='lax'
        )
        return response
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return templates.TemplateResponse(
            "pages/User/login/login.html",
            {"request": request, "error": "Authentication failed"}
        )