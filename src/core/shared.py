from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("BASE_DIR:", BASE_DIR)
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)