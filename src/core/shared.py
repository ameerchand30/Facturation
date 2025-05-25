from fastapi.templating import Jinja2Templates
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("BASE_DIR:", BASE_DIR)
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")
print("TEMPLATES_DIR:", TEMPLATES_DIR)
print("STATIC_DIR:", STATIC_DIR)    


templates = Jinja2Templates(directory=TEMPLATES_DIR)