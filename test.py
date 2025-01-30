from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database.database import get_db
from database.models import Reviews,Products,Customers
from schemas.schemas import ReviewSchema
from authentication.hashing import verify_password,get_hash_password
from authentication.Bearer_auth import authenticate_user

router = APIRouter(
    tags=["Reviews"],
    prefix="/reviews_page"
)

templates = Jinja2Templates(directory="templates")

def get_product_info(product_id: int, db: Session):
    product = db.query(Products).filter(Products.id == product_id).first()
    product_info = {
        'id':product.id,
        'cover': product.cover,
        'name': product.name,
        'description' : product.description,
        'price': product.price
    }
    return product_info

@router.get("/review",response_class=HTMLResponse)
def write_review(request:Request,product_id,db: Session = Depends(get_db), current_user=Depends(authenticate_user)):
    product_info = get_product_info(product_id,db)
    return templates.TemplateResponse("review.html",{"request":request,'product':product_info})


@router.post("/write_review")
def write_review(review_data: ReviewSchema, db: Session = Depends(get_db), current_user=Depends(authenticate_user)):
    # Check if review already exists
    print(review_data)
    existing_review = db.query(Reviews).filter(
        Reviews.product_id == review_data.product_id
    ).first()

    if existing_review:
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail="Review already added for this product")

    # Create a new review
    new_review = Reviews(
        user_id=current_user.id,
        product_id=review_data.product_id,
        rating=review_data.rating,
        headline=review_data.headline,
        command=review_data.command,
        created_at = datetime.now()
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {"message": "Review added successfully"}

@router.get("read_review")
def read_review(product_id:int,db: Session = Depends(get_db), current_user=Depends(authenticate_user)):
    reviews = db.query(Reviews).filter(Reviews.product_id==product_id).all()
    if not reviews:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reviews")
    
    context = []
    for review in reviews:
        user = db.query(Customers).filter(Customers.id==review.user_id).first()

        review_data = {
            'user_id': review.user_id,
            'product_id':review.product_id,
            'rating': review.rating,
            'headline': review.headline,
            'command' : review.command,
            'created_at': review.created_at,
            'user_name' : user.username
        }
        context.append(review_data)

    return




# @router.post("/like_product/{product_id}")
# async def like_product(request:Request, product_id: int, db: Session = Depends(get_db)):
#     try:
#         user = await get_current_user(request)
#         existing_like = db.query(Like).filter(Like.user_id == user.get('id'), Like.product_id == product_id).first()
#         if existing_like:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already liked")

#         new_like = Like(user_id=user.get('id'), product_id=product_id)
#         db.add(new_like)
#         db.commit()

#         return {"message": "Product liked successfully"}
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while liking product")


# @router.delete("/like_unlike/{product_id}")
# async def unlike_product(request:Request, product_id: int, db: Session = Depends(get_db)):
#     try:
#         user = await get_current_user(request)
#         like = db.query(Like).filter(Like.user_id == user.get('id'), Like.product_id == product_id).first()
#         if not like:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found for this product")

#         db.delete(like)
#         db.commit()

#         return {"message": "Product unliked successfully"}
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error while unliking product")