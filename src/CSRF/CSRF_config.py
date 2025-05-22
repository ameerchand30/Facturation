from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
from src.configDict import Setting

settings = Setting()

class CsrfSettings(BaseModel):
    """CSRF Settings Configuration"""
    secret_key: str = settings.CSRF_SECRET_KEY
    token_location: str = "header"
    cookie_name: str = "csrf_token"
    cookie_samesite: str = "lax"
    cookie_secure: bool = True
    cookie_httponly: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return [
        ("secret_key", settings.CSRF_SECRET_KEY),
        ("token_location", "header"),
        ("cookie_name", "csrf_token"),
        ("cookie_samesite", "lax"),
        ("cookie_secure", True),
        ("cookie_httponly", True)
    ]