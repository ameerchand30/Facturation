from fastapi.responses import JSONResponse, RedirectResponse
from typing import Union, Optional

def check_authorization(
    user: dict, 
    redirect: bool = False,
    redirect_url: str = "/login"
) -> Optional[Union[JSONResponse, RedirectResponse]]:
    """
    Check if user is authorized and return appropriate response if not
    
    Args:
        user: The user object from require_user_type dependency
        redirect: Whether to redirect or return JSON response
        redirect_url: URL to redirect to if unauthorized
    
    Returns:
        None if authorized, JSONResponse or RedirectResponse if unauthorized
    """
    if isinstance(user, (RedirectResponse, JSONResponse)):
        if redirect:
            return RedirectResponse(
                url=f"{redirect_url}?error=unauthorized",
                status_code=302
            )
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Unauthorized"}
        )
    return None