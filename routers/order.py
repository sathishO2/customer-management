from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
from fastapi.templating import Jinja2Templates

from database.database import get_db
from database.models import Products, Order_Details, Order_Item, Payment_Details, Addresses
from schemas.schemas import CreateOrderItemSchema, OrderStatusUpdate, CancelOrderRequest
from database.db_enum import StatusEnum, PaymentMethodEnum, OrderStatusEnum
from .auth import get_current_user
from helpers.helpers import get_product_info,get_address_info

router = APIRouter(
    tags=["Orders"],
    prefix="/order_page"
)

templates = Jinja2Templates(directory="templates")

@router.post("/create_order_item")
async def create_order_item(request: Request, order_data: CreateOrderItemSchema, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        order_details = Order_Details(
            user_id=user.get('id'),
            created_at=datetime.now(),
            delivered_at=datetime.now() + timedelta(days=3),
            order_status=OrderStatusEnum.processing
        )
        db.add(order_details)
        db.commit()

        address = Addresses(
            name=order_data.name,
            user_id=user.get('id'),
            order_id=order_details.id,
            address_line=order_data.address,
            country=order_data.country,
            city=order_data.city,
            state=order_data.state,
            zip_code=order_data.zip,
            phone_number=order_data.phone
        )
        db.add(address)
        db.commit()

        product_ids = [item.product_id for item in order_data.items]
        products = db.query(Products).filter(Products.id.in_(product_ids)).all()
        product_prices = {product.id: product.price for product in products}
        total_price = 0

        order_items = []
        for item in order_data.items:
            total_price += product_prices[item.product_id] * item.quantity
            new_item = Order_Item(
                order_id=order_details.id,
                product_id=item.product_id,
                quantity=item.quantity,
                created_at=datetime.now()
            )
            order_items.append(new_item)
        
        db.bulk_save_objects(order_items)
        order_details.total = total_price
        db.commit()

        payment = Payment_Details(
            order_id=order_details.id,
            amount=total_price,
            payment_status=StatusEnum.completed.value,
            payment_method=PaymentMethodEnum[order_data.payment_method],
            created_at=datetime.now()
        )
        db.add(payment)
        db.commit()

        return JSONResponse({"redirect_url": f"/order_page/read_order_item?order_id={order_details.id}"})
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()  # rollback to ensure the transaction is reverted
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the order."
        )

@router.get("/read_order_item", response_class=HTMLResponse)
async def read_order_item(request: Request, order_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        order_items = db.query(Order_Item).filter(Order_Item.order_id == order_id,Order_Item.is_active == True).all()
        order_details = db.query(Order_Details).filter(Order_Details.id == order_id).first()
        if not order_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order does not exist")

        address_data = db.query(Addresses).filter(Addresses.user_id == user.get('id')).order_by(Addresses.id.desc()).first()
        payments = db.query(Payment_Details).filter(Payment_Details.order_id == order_id).first()

        product_ids = [item.product_id for item in order_items]
        products = db.query(Products).filter(Products.id.in_(product_ids)).all()
        product_dict = {product.id: product for product in products}

        context = {
            "order_id": order_id,
            "order_date": order_items[0].created_at.strftime('%Y-%m-%d'),
            "address": {
                'address': address_data.address_line,
                'country': address_data.country,
                'city': address_data.city,
                'state': address_data.state,
                'zip_code': address_data.zip_code,
                'phone_number': address_data.phone_number
            },
            "customer_name": address_data.name,
            "products": [
                {
                    'id': item.product_id,
                    'cover': product_dict[item.product_id].cover,
                    'name': product_dict[item.product_id].name,
                    'price': product_dict[item.product_id].price,
                    'detail': product_dict[item.product_id].description,
                    'quantity': item.quantity
                }
                for item in order_items
            ],
            "quantity_total": sum(item.quantity for item in order_items),
            "item_total": sum(item.quantity * product_dict[item.product_id].price for item in order_items),
            "payment_method": payments.payment_method,
            "payment_status": payments.payment_status,
            "arriving_on": order_details.delivered_at.strftime("%A"),
            "delivered_at": order_details.delivered_at.strftime('%Y-%m-%d'),
            "order_status": order_details.order_status
        }

        return templates.TemplateResponse("orders.html", {"request": request, "context": context})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the order details."
        )

@router.post("/cancel_order")
def cancel_order(request: CancelOrderRequest, db: Session = Depends(get_db)):
    try:
        order = db.query(Order_Details).filter(Order_Details.id == request.order_id,Order_Details.is_active==True).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.order_status == OrderStatusEnum.cancelled:
            raise HTTPException(status_code=400, detail="Order already cancelled")
        order.is_active = False
        order.order_status = OrderStatusEnum.cancelled
        db.commit()
        return {"message": "Order cancelled successfully", "order_id": order.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while cancelling the order."
        )

@router.put("/update_status", response_model=OrderStatusUpdate)
async def update_order_status(order_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    try:
        order = db.query(Order_Details).filter(Order_Details.id == order_update.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.order_status = order_update.status
        db.commit()
        return OrderStatusUpdate(order_id=order.id, status=order.order_status)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the order status."
        )

@router.get("/read_orders", response_class=HTMLResponse)
async def get_orders(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        order_details = (
            db.query(Order_Details)
            .filter(Order_Details.user_id == user.get('id'))
            .order_by(desc(Order_Details.id))
            .options(
                joinedload(Order_Details.order_item).joinedload(Order_Item.products),
                joinedload(Order_Details.payment_details),
                joinedload(Order_Details.address),
                joinedload(Order_Details.customer)
            )
            .all()
        )

        all_orders = [
            {
                'order_date': order.created_at.strftime('%Y-%m-%d'),
                "customer_name": order.customer.username,
                "total_price": order.total,
                "order_id": order.id,
                'status': order.order_status.name,
                'delivery_at': order.delivered_at.strftime('%Y-%m-%d') if order.delivered_at else "N/A",
                'items_info': [
                    {
                        'id': item.product_id,
                        'cover': item.products.cover,
                        'name': item.products.name,
                        'price': item.products.price,
                        'detail': item.products.description,
                        'quantity': item.quantity
                    }
                    for item in order.order_item
                ]
            }
            for order in order_details
        ]

        return templates.TemplateResponse("order_history.html", {"request": request, "orders": all_orders})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the orders."
        )


@router.get("/buy_again")
async def process_to_buy(request: Request, order_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        order_items = db.query(Order_Item).filter(Order_Item.order_id == order_id).all()
        if not order_items:
            raise HTTPException(status_code=404, detail="Order items not found")

        product_ids = [item.product_id for item in order_items]
        context = [
            {
                'product_info': get_product_info(item.product_id, db),
                'product_total': item.quantity * get_product_info(item.product_id, db)['price'],
                'quantity': item.quantity,
                'item_id': item.id,
                "product_id": item.product_id
            }
            for item in order_items
        ]
        user_info = get_address_info(user.get('id'), db)
        return templates.TemplateResponse("checkout.html", {"request": request, "context": context, "product_ids": product_ids, "user_info": user_info})

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {str(e)}")
