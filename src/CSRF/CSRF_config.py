from pydantic_settings import BaseSettings
from src.configDict import Setting
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

settings = Setting()

# --- Configuration for CSRFProtect ---
class CsrfSettings(BaseSettings):
    secret_key: str = settings.CSRF_SECRET_KEY
    csrf_token_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    token_location: str = "header"  # Changed from set to str
    cookie_secure: bool = True
    cookie_samesite: str = "lax"

    class Config:
        case_sensitive = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()
# --- End Configuration ---