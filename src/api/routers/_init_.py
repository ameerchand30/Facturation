from fastapi.templating import Jinja2Templates
# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Make `templates` available for import in other modules
__all__ = ["templates"]

from api.dependencies.auth import get_current_user, require_user_type
from api.models.public.user import UserType