from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.core.shared import templates
from typing import List

from src.database import get_db
from src.api.models.product import ProductModel
from src.api.schemas.product import Product, ProductCreate, ProductUpdate
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
# to add product with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile



product_router = APIRouter(
    prefix="/products",
    tags=["Product"]
) 
# to read all products
@product_router.get("/", name="read_products")
async def read_products(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile),
    page: int = 1,
    per_page: int = 10,
    search: str = None
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )

    try:
         # Ensure valid pagination parameters
        page = max(1, page)  # Ensure page is at least 1
        per_page = min(max(10, per_page), 100)  # Limit between 10 and 100
    # Base query
        query = db.query(ProductModel).filter(
            ProductModel.enterprise_profile_id == enterprise_profile.id
        )
        
        # Apply search if provided
        if search:
            search = f"%{search}%"
            query = query.filter(
                or_(
                    ProductModel.name.ilike(search),
                    ProductModel.ref_number.ilike(search),
                    ProductModel.description.ilike(search)
                )
            )
        
        # Get total count for pagination
        total_items = query.count()
        total_pages = max(1, (total_items + per_page - 1) // per_page)

        # Adjust page if it exceeds total pages
        page = min(page, total_pages)
         # Apply pagination with exact offset
        offset = (page - 1) * per_page
        # Apply pagination
        products = query.order_by(ProductModel.id.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()

        return templates.TemplateResponse(
            "pages/product.html",
            {
                "request": request,
                "products": products,
                "current_page": "view_products",
                "page_number": page,
                "total_pages": total_pages,
                "per_page": per_page,
                "total_items": total_items,
                "search": search,
                "user": user,
                "enterprise_id": enterprise_profile.id
            }
        )
    except Exception as e:
        print(f"Error fetching products: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Error loading products = " + str(e),
                "current_page": "error",
                "user": user
            },
            status_code=500
        )
# to add new product Form
@product_router.get("/addProduct", name="add_product_form")
async def addProduct(
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
        return templates.TemplateResponse(
            "pages/addProduct.html", 
            {
                "request": request, 
                "current_page": "add_product", 
                "user": user,
                "enterprise_id": enterprise_profile.id,
                "csrf_token": request.state.csrf_token if hasattr(request.state, 'csrf_token') else None
            }
        )
    except Exception as e:
        print(f"Error rendering add product form: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Error loading the product form",
                "current_page": "error"
            },
            status_code=500
        )
# to edit a existing product form
@product_router.get("/edit/{product_id}", name="edit_product")
async def edit_product(product_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)),enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
   
       # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return RedirectResponse(
            url="/login?error=unauthorized",
            status_code=302
        )
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("pages/addProduct.html", {"request": request, "product": product, "current_page": "edit_product", "user": user})

# to receive new post request to store a new product
@product_router.post("/", response_model=dict, name="create_product")
async def create_product(
    product: ProductCreate, 
    db: Session = Depends(get_db), 
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)), 
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Unauthorized"}
        )
    
    try:
        # Create product with enterprise profile
        product_dict = product.model_dump()
        product_dict["enterprise_profile_id"] = enterprise_profile.id
        
        # Validate product data
        if product_dict.get("price", 0) < 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Price cannot be negative"}
            )
            
        if product_dict.get("quantity", 0) < 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Quantity cannot be negative"}
            )
        
        # Create new product
        db_product = ProductModel(**product_dict)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True, 
                "message": "Product created successfully",
                "product_id": db_product.id
            }
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

# to update a product
@product_router.post("/update/{product_id}", response_model=dict, name="update_product")
async def update_product(
    product_id: int, 
    product: ProductUpdate, 
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)),
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Unauthorized"}
        )
    
    try:
        # Check if product exists and belongs to enterprise
        existing_product = db.query(ProductModel).filter(
            ProductModel.id == product_id,
            ProductModel.enterprise_profile_id == enterprise_profile.id
        ).first()
        
        if not existing_product:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Product not found or unauthorized"}
            )
            
        # Update product data
        product_data = product.model_dump(exclude_unset=True)
        
        # Ensure enterprise_profile_id doesn't change
        product_data["enterprise_profile_id"] = enterprise_profile.id
        
        # Update the product
        db.query(ProductModel).filter(
            ProductModel.id == product_id,
            ProductModel.enterprise_profile_id == enterprise_profile.id
        ).update(product_data)
        
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True, 
                "message": "Product updated successfully",
                "product_id": product_id
            }
        )
    except Exception as e:
        db.rollback()
        print(f"Error updating product: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
# to delete a product 
@product_router.delete("/delete/{product_id}", response_model=dict, name="delete_product") 
async def delete_product(
    product_id: int, 
    db: Session = Depends(get_db),
    user: dict = Depends(require_user_type(UserType.ENTERPRISE)), 
    enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)
):
    # Check if user is unauthorized
    if isinstance(user, (RedirectResponse, JSONResponse)):
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Unauthorized"}
        )
    
    try:
        # Check if product exists and belongs to enterprise
        product = db.query(ProductModel).filter(
            ProductModel.id == product_id,
            ProductModel.enterprise_profile_id == enterprise_profile.id
        ).first()
        
        if not product:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Product not found"}
            )
            
        db.delete(product)
        db.commit()
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Product Deleted successfully"}
        )
    except Exception as e:
        print(f"Error deleting product: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )




