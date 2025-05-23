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
    # You can configure other settings like cookie name, header name, etc.
    # For example:
    # cookie_name: str = "my_csrf_token"
    # header_name: str = "X-MY-CSRF-TOKEN"

    class Config:
        case_sensitive = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()
# --- End Configuration ---