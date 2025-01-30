from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from database.models import Products, Cart, Addresses
from datetime import datetime

# CART
def get_product_price(db: Session, product_id: int) -> float:
    product = db.query(Products).filter(Products.id == product_id).first()
    if product:
        return product.price
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

def get_address_info(user_id: int, db: Session):
    try:
        info = db.query(Addresses).filter(Addresses.user_id == user_id).order_by(Addresses.id.desc()).first()
        if not info:
            raise HTTPException(status_code=404, detail="Address not found")

        address_info = {
            'id': info.id,
            'name': info.name,
            'user_id': info.user_id,
            'address_line': info.address_line,
            'country': info.country,
            'city': info.city,
            'state': info.state,
            'zip_code': info.zip_code,
            'phone_number': info.phone_number
        }
        return address_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving address information: {str(e)}")

# CATEGORYES

# ORDERS
    
def get_product_info(product_id: int, db: Session):
    try:
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return {
            'id': product.id,
            'cover': product.cover,
            'name': product.name,
            'description': product.description,
            'price': product.price
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# PRODUCTS

def get_or_create_cart(db: Session, user_id: int) -> Cart:
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id, created_at=datetime.now())
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while accessing cart")





