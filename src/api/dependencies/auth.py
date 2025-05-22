from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from jwt import PyJWTError, ExpiredSignatureError, decode


from src.api.models.public.user import UserType
from src.configDict import Setting


settings = Setting()
security = HTTPBearer()

async def get_current_user(request: Request) -> dict:
    # Check if request accepts JSON
    is_api_request = "application/json" in request.headers.get("accept", "")
    
    token = request.cookies.get("access_token")
    token = clean_token(token)

    if not token:
        auth_header = request.headers.get("access_token")
        if auth_header:
            token = auth_header
        else:
            if is_api_request:
                # Return JSON response for API requests
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Not authenticated - No token found"}
                )
            else:
                # Redirect for browser requests
                return RedirectResponse(
                    url="/login?error=unauthorized",
                    status_code=302
                )

    try:
        token_value = clean_token(token)
        payload = decode(
            token_value, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        return payload

    except ExpiredSignatureError:
        if is_api_request:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired"}
            )
        return RedirectResponse(
            url="/login?error=token_expired",
            status_code=302
        )

    except (PyJWTError, Exception) as e:
        if is_api_request:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Authentication failed: {str(e)}"}
            )
        return RedirectResponse(
            url="/login?error=authentication_failed",
            status_code=302
        )

def require_user_type(allowed_type: UserType):
    async def user_type_dependency(request: Request, user: dict = Depends(get_current_user)):
        # Check if response is RedirectResponse or JSONResponse
        if isinstance(user, (RedirectResponse, JSONResponse)):
            return user
            
        # Check user type
        if user.get("user_type") != allowed_type:
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"Access restricted to {allowed_type} users only"}
                )
            return RedirectResponse(
                url="/login?error=unauthorized_role",
                status_code=302
            )
        return user
    return user_type_dependency

def clean_token(token: str) -> str:
    if not token:
        return ""
    # Remove 'Bearer ' prefix if present
    if token.startswith('Bearer '):
        token = token[7:]
    # remove 'b' prefix if present
    if token.startswith('b'):
        token = token[1:]
    # Remove any quotes
    token = token.strip("'\"")

    # Remove any extra whitespace
    token = token.strip()

    return token