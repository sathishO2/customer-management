from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    TIMESTAMP,
    Double,Enum,Text
)

from sqlalchemy.orm import relationship
from .db_enum import StatusEnum,PaymentMethodEnum,OrderStatusEnum

from database.database import Base

class BaseModel(Base):
    __abstract__ = True
    is_active = Column(Boolean,default=True)
    created_at = Column(TIMESTAMP,nullable=True)
    updated_at = Column(TIMESTAMP)

class Customers(BaseModel):
    __tablename__ = "customers"

    id = Column(Integer,primary_key=True)
    username = Column(String,nullable=False)
    avatar = Column(String)
    email = Column(String,unique=True,nullable=False)
    password = Column(String,nullable=True)
    
    cart = relationship("Cart",back_populates="customers")
    reviews = relationship("Reviews",back_populates="customer")
    order_details = relationship("Order_Details", back_populates="customer")
    address = relationship("Addresses", back_populates="customers")
    likes = relationship("Like",back_populates="customers")

class Categories(BaseModel):
    __tablename__ = "categories"

    id = Column(Integer,primary_key=True)
    name = Column(String,nullable=False,unique=True)
    description = Column(String,nullable=False)
    cover = Column(String)
    
    products = relationship("Products", back_populates="category")

class Products(BaseModel):
    __tablename__ = "products"

    id = Column(Integer,primary_key=True)
    name = Column(String,nullable=False)
    description = Column(String,nullable=False)
    cover = Column(String)
    price = Column(Double,nullable=False)

    category_id = Column(Integer, ForeignKey('categories.id'))

    category = relationship("Categories", back_populates="products")
    cart_items = relationship("Cart_Items",back_populates="products")
    reviews = relationship("Reviews",back_populates="products")
    order_item = relationship("Order_Item",back_populates="products")
    likes = relationship("Like",back_populates="products")


class Order_Details(BaseModel):
    __tablename__ = "order_details"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('customers.id'))
    total = Column(Double, default=0)
    order_status = Column(Enum(OrderStatusEnum),nullable=True)
    delivered_at = Column(TIMESTAMP,nullable=True)
    
    order_item = relationship("Order_Item", back_populates="order_details")
    customer = relationship("Customers", back_populates="order_details")
    payment_details = relationship("Payment_Details", back_populates="order_details")
    address = relationship("Addresses", back_populates="order_details")

class Order_Item(BaseModel):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order_details.id'))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=0)
    
    order_details = relationship("Order_Details", back_populates="order_item")
    products = relationship("Products", back_populates="order_item")

class Payment_Details(BaseModel):
    __tablename__ = "payment_details"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order_details.id"))
    amount = Column(Double, nullable=False)
    payment_status = Column(Enum(StatusEnum), nullable=False)
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)

    order_details = relationship("Order_Details", back_populates="payment_details")


class Cart(BaseModel):
    __tablename__ = "cart"

    id = Column(Integer,primary_key=True)
    user_id = Column(Integer, ForeignKey('customers.id'),unique=True)
    total_item = Column(Integer,default=0)
    total_price = Column(Double,default=0)

    customers = relationship("Customers", back_populates="cart")
    cart_items = relationship("Cart_Items", back_populates="cart")

class Cart_Items(BaseModel):
    __tablename__ = "cart_items"

    id = Column(Integer,primary_key=True)
    cart_id = Column(Integer,ForeignKey("cart.id"))
    product_id = Column(Integer,ForeignKey("products.id"))
    quantity = Column(Integer,default=0)

    cart = relationship("Cart",back_populates="cart_items")
    products = relationship("Products",back_populates="cart_items")


class Reviews(BaseModel):

    __tablename__ = "reviews"

    id = Column(Integer,primary_key=True)
    user_id = Column(Integer,ForeignKey("customers.id"))
    product_id = Column(Integer,ForeignKey("products.id"))
    rating = Column(Integer)
    headline = Column(String)
    command = Column(Text)

    customer = relationship("Customers",back_populates="reviews")
    products = relationship("Products",back_populates="reviews")


class Addresses(BaseModel):

    __tablename__ = "addresses"

    id = Column(Integer,primary_key=True)
    name = Column(String,nullable=True)
    user_id = Column(Integer,ForeignKey("customers.id"))
    order_id = Column(Integer,ForeignKey("order_details.id"))
    address_line = Column(Text,nullable=False)
    country = Column(String,nullable=False)
    city = Column(String,nullable=False)
    state = Column(String,nullable=False)
    zip_code = Column(String,nullable=False)
    phone_number = Column(String,nullable=False)

    customers = relationship("Customers", back_populates="address")
    order_details = relationship("Order_Details", back_populates="address")




class Like(BaseModel):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('customers.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    customers = relationship("Customers", back_populates="likes")
    products = relationship("Products",back_populates="likes")



# Table wishlist {
#   id integer [primary key]
#   user_id integer
#   product_id integer
#   created_at timestamp
#   deleted_at timestamp
# }
# Ref: wishlist.user_id <> users.id
# Ref: wishlist.product_id <> products.id

