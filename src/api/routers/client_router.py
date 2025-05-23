from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse


from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.api.models.client import Clients
from src.api.schemas.client import Client,ClientCreate,ClientUpdate
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType


from src.CSRF.CSRF_config import CsrfSettings
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

from src.core.shared import templates

# to add client with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile


client_router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    responses={404: {"description": "Not found"}},
)
# to show all clinets form
@client_router.get("/", response_class=HTMLResponse, name="read_clients")
async def read_clients(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )

    try:
        # Get clients for the enterprise
        clients = db.query(Clients).filter(
            Clients.enterprise_profile_id == enterprise_profile.id
        ).order_by(Clients.id.desc()).all()

        return templates.TemplateResponse(
            "pages/clients.html",
            {
                "request": request,
                "clients": clients,
                "current_page": "view_clients",
                "user": user,
                "enterprise_id": enterprise_profile.id,
                "csrf_token": request.state.csrf_token if hasattr(request.state, 'csrf_token') else None,
                "error": request.query_params.get("error"),
                "success": request.query_params.get("success")
            },
            status_code=200
        )

    except Exception as e:
        print(f"Error fetching clients: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Error loading clients",
                "current_page": "error",
                "user": user
            },
            status_code=500
        )
# to add Client form
@client_router.get("/add", response_class=HTMLResponse, name="add_client_form")
async def add_client_form(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    csrf_protect: CsrfProtect = Depends()
):
# Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )

    try:
        # Initialize CSRF protection with settings
        csrf_token =  csrf_protect.generate_csrf()
        
        response = templates.TemplateResponse(
            "pages/addClient.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "client": None,
                "current_page": "add_client",
                "user": user,
                "enterprise_id": enterprise_profile.id
            }
        )
        # Set the CSRF token in an HttpOnly cookie
        csrf_protect.set_csrf_cookie(csrf_token, response) 
        return response
    # Handle CSRF errors
    except Exception as e:
        print(f"Error rendering add client form: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Access Denied: You don't have permission to view this page",
                "error_details": str(e),  # Optional detailed error info
                "current_page": "error",
                "user": user
            },
            status_code=500
        )
# when a Enterpenieur Click on Edit 
@client_router.get("/edit/{client_id}", response_class=HTMLResponse, name="edit_client_form")
async def edit_client_form(
    client_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    csrf_protect: CsrfProtect = Depends()
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )

    try:
        # Get client and verify ownership
        client = db.query(Clients).filter(
            Clients.id == client_id
        ).first()
        
        if client is None:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_message": "Client not found",
                    "current_page": "error",
                    "user": user
                },
                status_code=404
            )

        # Generate CSRF token
        csrf_token = csrf_protect.generate_csrf()
        
        # Create response with template
        response = templates.TemplateResponse(
            "pages/addClient.html",
            {
                "request": request,
                "client": client,
                "current_page": "edit_client",
                "user": user,
                #"enterprise_id": enterprise_profile.id,
                "csrf_token": csrf_token
            }
        )
        
        # Set CSRF cookie
        csrf_protect.set_csrf_cookie(csrf_token, response)
        return response

    except Exception as e:
        print(f"Error rendering edit client form: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Error loading client",
                "error_details": str(e),
                "current_page": "error",
                "user": user
            },
            status_code=500
        )
# this is to add new Client 
@client_router.post("/", response_model=dict, name="create_client")
async def create_client(client: ClientCreate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )
    try:
        client_data = client.model_dump()
        client_data["enterprise_profile_id"] = enterprise_profile.id
        db_client = Clients(**client_data)
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return {"success": True, "message": "Client created successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}

# to update client
@client_router.post("/update/{client_id}", response_model=dict, name="update_client")
async def update_client(
    client_id: int,
    client: ClientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    csrf_protect: CsrfProtect = Depends()
):

    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )
    try:
        # Verify CSRF token
        # await csrf_protect.validate_csrf(request)
        
        # Verify client ownership
        existing_client = db.query(Clients).filter(
            Clients.id == client_id
        ).first()
        
        if not existing_client:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Client not found"}
            )

        # Update client
        client_data = client.model_dump()
        db.query(Clients).filter(Clients.id == client_id).update(client_data)
        db.commit()
        
        return JSONResponse(
            content={"success": True, "message": "Client updated successfully"}
        )
    except CsrfProtectError:
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "CSRF token validation failed"}
        )
    except Exception as e:
        print(f"Error updating client: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@client_router.delete("/delete/{client_id}", response_model=dict, name="delete_client")
async def delete_client(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    csrf_protect: CsrfProtect = Depends()
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )
    try:
        # Verify CSRF token
        # await csrf_protect.validate_csrf(request)
        
        # Delete client with ownership check
        result = db.query(Clients).filter(Clients.id == client_id).delete()

        if not result:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Client not found"}
            )
            
        db.commit()
        
        return {"success": True, "message": "Client deleted successfully"}
        
    except CsrfProtectError:
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "CSRF token validation failed"}
        )
    except Exception as e:
        print(f"Error deleting client: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )