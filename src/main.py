from fastapi import FastAPI, Request,APIRouter, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os



app = FastAPI()


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

print("FastAPI application is running...")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("pages/User/LandingPage/landing-page.html", {"request": request})

@app.get("/{full_path:path}")  
async def catch_all(request: Request, full_path: str):
    return templates.TemplateResponse("pages/User/LandingPage/landing-page.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")