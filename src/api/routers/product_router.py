from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from typing import List

from src.database import get_db
from src.api.models.product import ProductModel
from src.api.schemas.product import Product, ProductCreate, ProductUpdate
from src.api.dependencies.auth import get_current_user, require_user_type
from src.api.models.public.user import UserType
# to add product with enterprise profile
from src.api.dependencies.enterprise import get_enterprise_profile
from src.api.models.public.user import EnterpriseProfile

templates = Jinja2Templates(directory="templates")

product_router = APIRouter(
    prefix="/products",
    tags=["Product"]
) 
# to read all products
@product_router.get("/")
async def read_products(request: Request,db: Session = Depends(get_db), name="read_products", user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    products = db.query(ProductModel).filter(ProductModel.enterprise_profile_id == enterprise_profile.id).all()
    return templates.TemplateResponse("pages/product.html", {"request": request, "products": products, "current_page": "view_products", "user": user})
# to add new product Form
@product_router.get("/addProduct", name="add_product_form")
async def addProduct(request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    return templates.TemplateResponse("pages/addProduct.html", {"request": request, "current_page": "add_product", "user": user})
# to edit a existing product form
@product_router.get("/edit/{product_id}", name="edit_product")
async def edit_product(product_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE))):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("pages/addProduct.html", {"request": request, "product": product, "current_page": "edit_product", "user": user})

# to receive new post request to store a new product
@product_router.post("/", response_model=dict, name="create_product")
async def create_product(product: ProductCreate, db: Session = Depends(get_db), user: dict = Depends(require_user_type(UserType.ENTERPRISE)), enterprise_profile: EnterpriseProfile = Depends(get_enterprise_profile)):
    try:
        product_dict = product.model_dump()
        product_dict["enterprise_profile_id"] = enterprise_profile.id
        db_product = ProductModel(**product_dict)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return {"success": True, "message": "Product created successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}

# to update a product
@product_router.post("/update/{product_id}", response_model=dict, name="update_product")
async def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    try:
        # Unpack the product data into a dictionary
        product_data = product.model_dump()
        db.query(ProductModel).filter(ProductModel.id == product_id).update(product_data)
        db.commit()
        return {"success": True, "message": "Product updated successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}
# to delete a product 
@product_router.delete("/delete/{product_id}", response_model=dict, name="delete_product") 
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        db.query(ProductModel).filter(ProductModel.id == product_id).delete()
        db.commit()
        return {"success": True, "message": "Product Deleted successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": str(e)}




