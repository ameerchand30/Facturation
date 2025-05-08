from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from typing import Optional
from jwt import PyJWTError, ExpiredSignatureError, decode


from src.api.models.public.user import UserType
from src.configDict import Setting


settings = Setting()
security = HTTPBearer()

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    # Clean the token to remove any unwanted characters
    token = clean_token(token)

    if not token:
        # Try to get token from header
        auth_header = request.headers.get("access_token")
        if auth_header:
            token = auth_header
        else:
            """ raise HTTPException(
                status_code=401,
                detail="Not authenticated - No token found in cookies or headers"
            ) """
            print("Not authenticated - No token found in cookies or headers")
            return RedirectResponse(url="/", status_code=302)
    try:
        # Decode the JWT token
        # Remove 'Bearer ' prefix if present
        token_value = clean_token(token)
        payload = decode(
            token_value, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        return payload
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Token has expired{str(e)}"
        )
        print("Token has expired", str(e))
        # Redirect to login page if token has expired
        return RedirectResponse(url="/", status_code=302)
    except PyJWTError as e:
        raise HTTPException(
            status_code=401, 
            detail=f"PyJWTError: Could not validate credentials: {str(e)}"
        )
    except Exception as e:
        """ raise HTTPException(
            status_code=401, 
            detail=f"Could not validate credentials: {str(e)}"
        ) """
        print("Could not validate credentials", str(e))
        # Redirect to login page if token is invalid
        return RedirectResponse(url="/", status_code=302)

def require_user_type(allowed_type: UserType):
    async def user_type_dependency(user: dict = Depends(get_current_user)):
        if user["user_type"] != allowed_type:
            raise HTTPException(
                status_code=403,
                detail=f"Access restricted to {allowed_type} users only"
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