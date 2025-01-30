from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database.database import get_db
from database.models import Products, Cart, Cart_Items, Addresses
from schemas.schemas import UpdateCartItem
from .auth import get_current_user
from helpers.helpers import get_address_info,get_product_price,get_or_create_cart

router = APIRouter(
    tags=["Cart"],
    prefix="/cart_page"
)

templates = Jinja2Templates(directory="templates")

@router.get("/cart", response_class=HTMLResponse)
async def get_cart(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        cart = db.query(Cart).filter(Cart.user_id == user.get('id')).first()
        if not cart:
            get_or_create_cart(db,user.get('id'))
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart does not exist")
        
        cart_items = db.query(Cart_Items).filter(Cart_Items.cart_id == cart.id, Cart_Items.is_active==True).all()
        
        # if not cart_items:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active items in the cart")

        product_ids = [item.product_id for item in cart_items]
        products = db.query(Products).filter(Products.id.in_(product_ids)).all()

        # if not products:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Products not found")

        product_dict = {product.id: product for product in products}

        context = []
        items_ids = []

        for item in cart_items:
            product_info = product_dict.get(item.product_id)
            if product_info:
                item_context = {
                    'product_info': {
                        'id': product_info.id,
                        'cover': product_info.cover,
                        'name': product_info.name,
                        'price': product_info.price
                    },
                    'product_total': item.quantity * product_info.price,
                    'quantity': item.quantity,
                    'item_id': item.id,
                    'cart_id': item.cart_id
                }
                items_ids.append(item.id)
                context.append(item_context)

        return templates.TemplateResponse("cart.html", {"request": request, "context": context, "items": items_ids})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.post("/add_cart_item")
async def add_cart_item(request: Request, product_id: int = Form(...), db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
        if not cart:
            cart = Cart(user_id=user.get("id"), created_at=datetime.now())
            db.add(cart)
            db.commit()
            db.refresh(cart)

        cart_item = db.query(Cart_Items).filter(Cart_Items.cart_id == cart.id, Cart_Items.product_id == product_id, Cart_Items.is_active==True).first()
        if cart_item:
            cart_item.quantity += 1
            cart_item.updated_at = datetime.now()
            db.commit()
            db.refresh(cart_item)
        else:
            cart_item = Cart_Items(cart_id=cart.id, product_id=product_id, quantity=1, created_at=datetime.now())
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)

        product_price = get_product_price(db, product_id)
        cart.total_item = (cart.total_item or 0) + 1
        cart.total_price = (cart.total_price or 0.0) + product_price
        cart.updated_at = datetime.now()

        db.commit()
        db.refresh(cart)

        return {"message": "Item added to cart successfully"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/remove_cart_item")
def remove_cart_item(item_id: int = Form(...), db: Session = Depends(get_db)):
    try:
        cart_item = db.query(Cart_Items).filter(Cart_Items.id == item_id).first()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item does not exist")
        db.delete(cart_item)
        db.commit()
        return RedirectResponse(url="/cart_page/cart", status_code=status.HTTP_303_SEE_OTHER)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/update_cart_item")
def update_cart_item(data: UpdateCartItem, db: Session = Depends(get_db)):
    try:
        cart_item = db.query(Cart_Items).filter(Cart_Items.id == data.cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item does not exist")

        cart = db.query(Cart).filter(Cart.id == cart_item.cart_id).first()
        old_product_price = get_product_price(db, cart_item.product_id)
        cart.total_item -= cart_item.quantity
        cart.total_price -= cart_item.quantity * old_product_price

        cart_item.cart_id = data.cart_id
        cart_item.product_id = data.product_id
        cart_item.quantity = data.quantity
        cart_item.updated_at = datetime.now()
        db.commit()
        db.refresh(cart_item)

        new_product_price = get_product_price(db, data.product_id)
        cart.total_item += cart_item.quantity
        cart.total_price += cart_item.quantity * new_product_price
        cart.updated_at = datetime.now()

        db.commit()
        db.refresh(cart)

        return {"message": "Cart item updated successfully"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/process_to_buy")
async def process_to_buy(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
        if not cart or cart.total_item == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty or does not exist")
        
        cart_items = db.query(Cart_Items).filter(Cart_Items.cart_id == cart.id,Cart_Items.is_active==True)
        product_ids = [item.product_id for item in cart_items]

        products = db.query(Products).filter(Products.id.in_(product_ids)).all()
        product_dict = {product.id: product for product in products}

        context = []
        for item in cart_items.filter(Cart_Items.is_active==True).all():
            product_info = product_dict.get(item.product_id)
            item_context = {
                'product_info': {
                        'id': product_info.id,
                        'cover': product_info.cover,
                        'name': product_info.name,
                        'price': product_info.price
                    },
                'product_total': item.quantity * product_info.price,
                'quantity': item.quantity,
                'item_id': item.id,
                'cart_id': item.cart_id,
                'product_id': item.product_id
            }
            context.append(item_context)
        
        user_info = user.get('username')

        cart_items.update({"is_active": False})
        db.commit()
        
        return templates.TemplateResponse("checkout.html", {"request": request, "context": context, "product_ids": product_ids, "user_info": user_info})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/buy_now")
async def buy_now(request: Request, product_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product_info = {
            'id': product.id,
            'cover': product.cover,
            'name': product.name,
            'price': product.price
        } 

        context = [{
            'product_info': product_info,
            'quantity': 1,
            'product_total': product_info['price'],
            'product_id': product_id
        }]
        
        user_info = get_address_info(user.get("id"), db)
        
        return templates.TemplateResponse("checkout.html", {"request": request, "context": context, "product_ids": [product_id], "user_info": user_info})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
