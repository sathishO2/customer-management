from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Dict, List

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database.database import get_db
from database.models import Categories, Products, Like, Reviews, Customers
from schemas.schemas import ProductSchema

from .auth import get_current_user
from helpers.helpers import get_or_create_cart


router = APIRouter(
    tags=["Products"],
    prefix="/products_page"
)

templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")




@router.get("/products", response_class=HTMLResponse)
async def get_products(request: Request, category: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        products = db.query(Products).filter(Products.category_id == category, Products.is_active == True).all()
        cart = get_or_create_cart(db, user.get('id'))

        category_obj = db.query(Categories).filter(Categories.id == category).first()
        if not category_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        category_name = category_obj.name

        return templates.TemplateResponse("products.html", {
            "request": request,
            "products": products,
            "cart": cart,
            "category": category_name,
            "page_title": "Products"
        })
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while fetching products")


@router.get("/all_products", response_class=HTMLResponse)
async def get_all_products(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        categories = db.query(Categories).all()
        category_ids = [cat.id for cat in categories]
        products = db.query(Products).filter(Products.category_id.in_(category_ids), Products.is_active == True).options(
            joinedload(Products.category)
        ).all()

        context: Dict[str, List[Products]] = {cat.name: [] for cat in categories}
        for product in products:
            context[product.category.name].append(product)

        cart = get_or_create_cart(db, user.get('id'))

        return templates.TemplateResponse("all_products.html", {
            "request": request,
            "context": context,
            "cart": cart
        })
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while fetching all products")


@router.get("/product_info", response_class=HTMLResponse)
async def get_product_info(request: Request, product_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        product = db.query(Products).filter(Products.id == product_id, Products.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        cart = get_or_create_cart(db, user.get('id'))

        reviews = db.query(Reviews).filter(Reviews.product_id == product_id).all()
        customer_info = db.query(Customers).filter(Customers.id == user.get('id')).first()

        reviews_data = [
            {
                'user_id': review.user_id,
                'product_id': review.product_id,
                'rating': review.rating,
                'headline': review.headline,
                'command': review.command,
                'created_at': review.created_at.strftime('%Y-%m-%d'),
                'user_name': customer_info.username
            }
            for review in reviews
        ]

        return templates.TemplateResponse("product_info.html", {
            "request": request,
            "product": product,
            "cart": cart,
            "title": product.name,
            "reviews": reviews_data
        })
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while fetching product info")


@router.post("/create")
def create_product(request: ProductSchema, db: Session = Depends(get_db)):
    try:
        existing_product = db.query(Products).filter(Products.name == request.name, Products.category_id == request.category_id).first()
        if existing_product:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product already exists")

        new_product = Products(
            name=request.name,
            description=request.description,
            cover=request.cover,
            price=request.price,
            created_at=datetime.now(),
            category_id=request.category_id,
            is_active=True
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {"message": "Product created successfully", "product_id": new_product.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while creating product")


@router.get("/read")
def read_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Products).filter(Products.id == product_id, Products.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        return product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while reading product")


@router.put("/update")
def update_product(product_id: int, request: ProductSchema, db: Session = Depends(get_db)):
    try:
        product = db.query(Products).filter(Products.id == product_id, Products.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product.name = request.name
        product.description = request.description
        product.cover = request.cover
        product.price = request.price
        product.updated_at = datetime.now()
        product.category_id = request.category_id

        db.commit()

        return {"message": "Product updated successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while updating product")


@router.delete("/delete")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Products).filter(Products.id == product_id, Products.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product.is_active = False
        product.updated_at = datetime.now()

        db.commit()

        return {"message": "Product deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while deleting product")


@router.post("/like_product/{product_id}")
async def like_product(request:Request, product_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        existing_like = db.query(Like).filter(Like.user_id == user.get('id'), Like.product_id == product_id).first()
        if existing_like:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already liked")

        new_like = Like(user_id=user.get('id'), product_id=product_id)
        db.add(new_like)
        db.commit()

        return {"message": "Product liked successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while liking product")


@router.delete("/like_product/{product_id}")
async def unlike_product(request:Request, product_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        like = db.query(Like).filter(Like.user_id == user.get('id'), Like.product_id == product_id).first()
        if not like:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found for this product")

        db.delete(like)
        db.commit()

        return {"message": "Product unliked successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while unliking product")
    
@router.get("/view_liked_products", response_class=HTMLResponse)
async def view_liked_products(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        liked_products = db.query(Products).join(Like, Like.product_id == Products.id).filter(
            Like.user_id == user.get('id'),
            Products.is_active == True
        ).all()

        cart = get_or_create_cart(db, user.get('id'))

        return templates.TemplateResponse("liked_products.html", {
            "request": request,
            "cart": cart,
            "products": liked_products,
            "category": "Liked Products",
            "page_title": "Liked Products"
        })
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while fetching liked products")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")
