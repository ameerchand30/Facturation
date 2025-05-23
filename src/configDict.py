import os
from pydantic_settings import BaseSettings
from authlib.integrations.starlette_client import OAuth

from src.core.shared import BASE_DIR

class Setting(BaseSettings):
    host_name: str
    host_port: str
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str

    POSTGRES_USER : str = "postgres"
    POSTGRES_PASSWORD : str = "admin"
    POSTGRES_DB : str = "facturaization"
    
    algorithm: str
    access_token_expire_minutes: int
    # security
    secret_key: str
    jwt_secret_key: str
    session_secret: str
    CSRF_SECRET_KEY: str = "your-secure-secret-key" 
    # OAuth2 settings
    google_client_id: str
    google_client_secret: str
    github_client_id: str
    github_client_secret: str
    linkedin_client_id: str
    linkedin_client_secret: str
    facebook_client_id: str
    facebook_client_secret: str
    OPENAI_API_KEY: str
    OPENAI_API_MODEL: str
    class Config:
        # Get the root directory dynamically
    
        print("Root Directory:", BASE_DIR)
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = 'utf-8'

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            # Docker environment variables take precedence over .env file
            return env_settings, init_settings, file_secret_settings

  
settings = Setting()
oauth = OAuth()
# Configure OAuth providers
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly'
    }
)

# Add other providers similarly