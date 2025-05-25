from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from src.core.shared import templates

from src.database import get_db
from src.api.routers.crud import crud_enterprise  # Correct import statement
from src.api.schemas.enterprise import Enterprise as schemaEnterprise, EnterpriseCreate, EnterpriseUpdate
from src.api.models.client import Clients
from src.api.schemas.client import Client
from src.api.models.enterprise import Enterprise
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
# to add Enterprise with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile
from src.api.utils.auth_utils import check_authorization



enterprise_router = APIRouter(
    prefix="/enterprises",
    tags=["Enterprises"],
    responses={404: {"description": "Not found"}},
)

# show the enterprise page
@enterprise_router.get("/", response_class=HTMLResponse, name="read_enterprises")
def read_enterprises(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    page: int = 1,
    per_page: int = 10,
    search: str = None,
    sort: str = "id",
    order: str = "desc"
):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check

    try:
        # Ensure valid pagination parameters
        page = max(1, page)
        per_page = min(max(10, per_page), 100)

        # Base query with join
        query = db.query(Enterprise, Clients).join(Clients).filter(
            Enterprise.enterprise_profile_id == enterprise_profile.id,
            Clients.enterprise_profile_id == enterprise_profile.id
        )

        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Enterprise.name.ilike(search_term),
                    Enterprise.siretNo.ilike(search_term),
                    Clients.name.ilike(search_term),
                    Clients.email.ilike(search_term)
                )
            )

        # Get total count for pagination
        total_items = query.count()
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        
        # Adjust page if it exceeds total pages
        page = min(page, total_pages)

        # Apply sorting
        if sort == "name":
            sort_column = Enterprise.name
        elif sort == "siretNo":
            sort_column = Enterprise.siretNo
        elif sort == "client_name":
            sort_column = Clients.name
        elif sort == "client_email":
            sort_column = Clients.email
        else:
            sort_column = Enterprise.id

        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        enterprises = query.offset(offset).limit(per_page).all()

        return templates.TemplateResponse(
            "pages/enterprise.html",
            {
                "request": request,
                "enterprises": enterprises,
                "current_page": "view_enterprise",
                "page_number": page,
                "total_pages": total_pages,
                "per_page": per_page,
                "total_items": total_items,
                "search": search,
                "sort": sort,
                "order": order,
                "user": user
            }
        )

    except Exception as e:
        print(f"Error fetching enterprises: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Error loading enterprises",
                "current_page": "error",
                "user": user
            },
            status_code=500
        )

# show the enterprise Form page with the customer data
@enterprise_router.get("/add", response_class=HTMLResponse, name="add_enterprise_form")
async def add_enterprise_form(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    # Get all customers
    customers = db.query(Clients).all()
    customer_data = {customer.name: {"customer_id": customer.id,"email": customer.email,"notes": customer.notes} for customer in customers}
    return templates.TemplateResponse("pages/addEnterprise.html", {"request": request,"customer_data": customer_data, "customers": customers, "current_page": "add_enterprise", "user": user})

# create enterprise to the database
@enterprise_router.post("/", response_model=dict, name="create_enterprise")
def create_enterprise( enterprise : EnterpriseCreate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check

    # print(enterprise.__dict__)
    try:
        enterprise_dict = enterprise.model_dump()
        enterprise_dict["enterprise_profile_id"] = enterprise_profile.id
        db_enterprise = Enterprise(**enterprise_dict)
        crud_enterprise.create_enterprise(db=db, enterprise=db_enterprise)
        return {"success": True, "message": "Enterprise created successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}

# link the edit enterprise page
@enterprise_router.get("/edit/{enterprise_id}", response_class=HTMLResponse, name="edit_enterprise_form")
def edit_enterprise_form(enterprise_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    enterprise = crud_enterprise.get_enterprise(db, enterprise_id=enterprise_id)
    if enterprise is None:
        raise HTTPException(status_code=404, detail="Enterprise not found")
    customers = db.query(Clients).all()
    customer_data = {customer.name: {"customer_id": customer.id,"email": customer.email,"notes": customer.notes} for customer in customers}
    return templates.TemplateResponse("pages/addEnterprise.html", {"request": request, "enterprise": enterprise, "customer_data": customer_data, "customers": customers, "current_page": "edit_enterprise", "user": user})

# update enterprise to the database
@enterprise_router.post("/update/{enterprise_id}", response_model=dict, name="update_enterprise")
def update_enterprise(enterprise_id: int, enterprise : EnterpriseUpdate ,db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    try:
        enterprise_dict = enterprise.model_dump()
        db_enterprise = Enterprise(**enterprise_dict)
        crud_enterprise.update_enterprise(db,enterprise_id,enterprise_dict)
        return {"success": True, "message": "Enterprise has been updated"}
        
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}
# to delete the enterprise 
@enterprise_router.delete("/delete/{enterprise_id}", response_model = dict, name="delete_enterprise")
def delete_enterprise(enterprise_id: int, request: Request ,db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    # Check authorization
    auth_check = check_authorization(user, redirect=True)
    if auth_check:
        return auth_check
    try:
        crud_enterprise.delete_enterprise(db,enterprise_id)
        return {"success": True, "message": "Product Deleted successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}




