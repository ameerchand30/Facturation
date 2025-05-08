from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.api.models.client import Clients
from src.api.schemas.client import Client,ClientCreate,ClientUpdate
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType

from fastapi.templating import Jinja2Templates


# to add client with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile

templates = Jinja2Templates(directory="templates")

client_router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    responses={404: {"description": "Not found"}},
)
# to show all clinets form
@client_router.get("/", response_class=HTMLResponse , name="read_clients")
async def read_clients(request: Request, db: Session = Depends(get_db),user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    clients = db.query(Clients).filter(Clients.enterprise_profile_id == enterprise_profile.id).all()
    return templates.TemplateResponse("pages/clients.html", {"request": request, "clients": clients, "current_page": "view_clients","user": user})
# to add Client form
@client_router.get("/add", response_class=HTMLResponse, name="add_client_form")
async def add_client_form(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    return templates.TemplateResponse("pages/addClient.html", {"request": request, "client": None, "current_page": "add_client","user": user})
# when a Enterpenieur Click on Edit 
@client_router.get("/edit/{client_id}", response_class=HTMLResponse, name="edit_client_form")
async def edit_client_form(client_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    client = db.query(Clients).filter(Clients.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return templates.TemplateResponse("pages/addClient.html", {"request": request, "client": client, "current_page": "edit_client","user": user})
# this is to add new Client 
@client_router.post("/", response_model=dict, name="create_client")
async def create_client(client: ClientCreate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
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
    clinet: ClientUpdate,
    db: Session = Depends(get_db),
    
):
    try:
        client_data = clinet.model_dump()
        db.query(Clients).filter(Clients.id == client_id).update(client_data)
        db.commit()
        return {"success": True, "message": "Client updated successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}
@client_router.delete("/delete/{client_id}",response_model=dict, name="delete_client")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    try:
        db.query(Clients).filter(Clients.id == client_id).delete()
        db.commit()
        return {"success": True, "message": "Client Deleted successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}