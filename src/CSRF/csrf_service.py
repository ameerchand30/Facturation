# services/csrf_service.py
from fastapi import Request, HTTPException, status, Response, Depends
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse

# Make sure to import your CsrfSettings so it's loaded by CsrfProtect
from src.CSRF.csrf_config import CsrfSettings

class CsrfService:
    # def __init__(self, csrf_protect: CsrfProtect = Depends()):
    #     self.csrf_protect = csrf_protect

    async def validate_csrf(self, request: Request, csrf_protect: CsrfProtect = Depends()): # <--- Pass CsrfProtect here
        """
        Validates the CSRF token from the request.
        This method is designed to be directly used as a FastAPI dependency.
        """
        try:
            await csrf_protect.validate_csrf_in_cookies(request) # <--- Use the injected csrf_protect
            return True
        except CsrfProtectError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=exc.message
            )

    def generate_csrf_token_for_form(self, response: Response):
        """
        Generates a CSRF token and sets it as a cookie on the response.
        Returns the token value to be embedded in HTML forms.
        """
        csrf_token = self.csrf_protect.generate_csrf()
        self.csrf_protect.set_csrf_cookie(csrf_token, response)
        return csrf_token

    def get_csrf_token_from_cookie(self, request: Request):
        """
        Retrieves the CSRF token from the cookie. Useful for SPAs where
        JavaScript needs to read the token to send in headers.
        """
        token = self.csrf_protect.get_csrf_from_cookies(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSRF cookie not found."
            )
        return token
    def generate_csrf_token_for_response(self, response: Response, csrf_protect: CsrfProtect = Depends()): # <--- Pass CsrfProtect here
        """
        Generates a CSRF token, sets it as a cookie on the response,
        and returns the token value to be embedded in HTML.
        """
        csrf_token = csrf_protect.generate_csrf() # <--- Use the injected csrf_protect
        csrf_protect.set_csrf_cookie(csrf_token, response) # <--- Use the injected csrf_protect
        return csrf_token