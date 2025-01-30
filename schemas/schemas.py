from pydantic import BaseModel
from typing import Optional,List
from database.db_enum import OrderStatusEnum


class CustomersSchema(BaseModel):
    username:str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str


class OrderStatusUpdate(BaseModel):
    order_id: int
    status: OrderStatusEnum


# Authentication

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    email: Optional[str] = None


# Categories Schema

class CategoriesSchema(BaseModel):
    name:str
    description:str

# Product Schema

class ProductSchema(BaseModel):
    name: str
    description: str
    cover: str
    price: float
    category_id: int


# Cart Schema
class CartSchema(BaseModel):
    user_id: int

# Cart_Items Schema
class CartItemsSchema(BaseModel):
    cart_id:int
    product_id:int
    quantity: int

class UpdateCartItem(BaseModel):
    cart_item_id: int
    cart_id: int
    product_id: int
    quantity: int
    total: float


# order schema
class OrderDetailsSchema(BaseModel):
    total:int

# order item schema
class OrderItemSchema(BaseModel):
    product_id:int
    quantity:int

class Item(BaseModel):
    product_id: int
    quantity: int

class CreateOrderItemSchema(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    zip:str
    phone: str
    payment_method: str
    items: List[Item]

class CancelOrderRequest(BaseModel):
    order_id: int

# payment schema

class PaymentDetails(BaseModel):
    order_id : int
    amount : int
    status : str
    payment:str


# update cart item
class UpdateCartItem(BaseModel):
    cart_item_id: int
    cart_id: int
    product_id: int
    quantity: int
    total: float


# liked product

class ProductBase(BaseModel):
    id: int
    name: str
    description: str
    price: float
    cover: str

    class Config:
        from_attributes = True

class LikedProductsResponse(BaseModel):
    products: List[ProductBase]


class ReviewSchema(BaseModel):
    user_id:int
    product_id:int
    rating: int
    headline: str
    command : str