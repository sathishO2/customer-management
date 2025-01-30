from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database.database import get_db
from database.models import Reviews, Products, Customers
from schemas.schemas import ReviewSchema
from .auth import get_current_user
from helpers.helpers import get_product_info

router = APIRouter(
    tags=["Reviews"],
    prefix="/reviews_page"
)

templates = Jinja2Templates(directory="templates")


@router.get("/review", response_class=HTMLResponse)
async def write_review(request: Request, product_id: int, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        product_info = get_product_info(product_id, db)
        return templates.TemplateResponse("review.html", {"request": request, 'product': product_info})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/write_review")
async def write_review(request: Request, review_data: ReviewSchema, db: Session = Depends(get_db)):
    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

        existing_review = db.query(Reviews).filter(
            Reviews.product_id == review_data.product_id,
            Reviews.user_id == user.get('id')
        ).first()

        if existing_review:
            raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail="Review already added for this product")
        
        new_review = Reviews(
            user_id=user.get('id'),
            product_id=review_data.product_id,
            rating=review_data.rating,
            headline=review_data.headline,
            command=review_data.command,
            created_at=datetime.now()
        )

        db.add(new_review)
        db.commit()
        db.refresh(new_review)

        return {"message": "Review added successfully"}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/read_review")
def read_review(product_id: int, db: Session = Depends(get_db)):
    try:
        reviews = db.query(Reviews).filter(Reviews.product_id == product_id).all()
        if not reviews:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reviews found")

        user_ids = [review.user_id for review in reviews]
        users = db.query(Customers).filter(Customers.id.in_(user_ids)).all()
        user_dict = {user.id: user.username for user in users}

        context = [
            {
                'user_id': review.user_id,
                'product_id': review.product_id,
                'rating': review.rating,
                'headline': review.headline,
                'command': review.command,
                'created_at': review.created_at.strftime('%Y-%m-%d'),
                'user_name': user_dict.get(review.user_id)
            }
            for review in reviews
        ]

        return {"reviews": context}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
