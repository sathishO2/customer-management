from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

from database.database import get_db
from database.models import Categories, Products
from schemas.schemas import CategoriesSchema

router = APIRouter(
    tags=["Categories"],
    prefix="/categories_page"
)

templates = Jinja2Templates(directory="templates")

@router.get("/categorys", response_class=HTMLResponse)
async def read_item(request: Request, db: Session = Depends(get_db)):
    try:
        # categories_data = db.query(Categories).all()
        # products = db.query(Products).filter(Products.category_id==)

        categories_data = db.query(Categories).join(Products, Categories.id == Products.category_id).all()
        
        categories = [
            jsonable_encoder(categories)
            for categories in categories_data
        ]
        # print("=======================================",categories)
        return templates.TemplateResponse("category.html", {"request": request, "categories": categories})
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching categories"
        ) from e

@router.post("/create")
def create_category(request: CategoriesSchema, db: Session = Depends(get_db)):
    try:
        existing_category = db.query(Categories).filter(Categories.name == request.name).first()

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists"
            )

        new_category = Categories(
            name=request.name,
            description=request.description,
            created_at=datetime.now()
        )

        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        return {"message": "Category created successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the category"
        ) from e

@router.get("/read")
def read_category(category_name: str, db: Session = Depends(get_db)):
    try:
        category = db.query(Categories).filter(Categories.name == category_name).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category does not exist"
            )

        products_list = db.query(Products).filter(Products.category_id == category.id).all()

        return products_list

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while reading the category"
        ) from e

@router.put("/update")
def update_category(category_name: str, request: CategoriesSchema, db: Session = Depends(get_db)):
    try:
        category = db.query(Categories).filter(Categories.name == category_name).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category does not exist"
            )

        category.name = request.name
        category.description = request.description
        category.updated_at = datetime.now()

        db.commit()
        db.refresh(category)

        return {"message": "Category updated successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the category"
        ) from e

@router.delete("/delete")
def delete_category(category_name: str, db: Session = Depends(get_db)):
    try:
        category = db.query(Categories).filter(Categories.name == category_name).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category does not exist"
            )

        category.is_active = False

        db.commit()
        db.refresh(category)

        return {"message": "Category deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the category"
        ) from e
