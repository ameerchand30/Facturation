from fastapi import FastAPI, Request,APIRouter, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# from routers.invoice_router import invoice_router
from src.api.routers.auth_router import auth_router
from src.api.routers.client_router import client_router
from src.api.routers.product_router import product_router
from src.api.routers.enterprise_router import enterprise_router
from src.api.routers.invoice_router import invoice_router
from src.api.routers.report_generate import report_router
from src.api.routers.dashboard_routes import dashboard_router
from src.api.routers.enterprise_profile_router import enterprise_profile_router
from src.api.routers.client_invoices_router import client_invoices_router


from src.database import db_manager,engine
from src.db_config import Base
# Import shared templates
from src.core.shared import templates, STATIC_DIR

app = FastAPI()


# Serve static files with absolute path
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

print("FastAPI application is running...")


# Create the database tables   
# Base.metadata.create_all(bind=engine)

# Set up CORS middleware (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")


# Include routers
# app.include_router(auth)
app.include_router(auth_router)
app.include_router(client_router)
app.include_router(product_router)
app.include_router(enterprise_router)
app.include_router(invoice_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(enterprise_profile_router)
app.include_router(client_invoices_router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("pages/User/LandingPage/landing-page.html", {"request": request})

@app.get("/{full_path:path}")  
async def catch_all(request: Request, full_path: str):
    return templates.TemplateResponse("pages/User/LandingPage/landing-page.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")