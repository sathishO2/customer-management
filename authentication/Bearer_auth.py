from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .hashing import verify_password
from database import database, models

security = HTTPBasic()

token_auth_scheme = HTTPBearer()


def authenticate_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(database.get_db),
):
    email = credentials.username
    password = credentials.password
    user = db.query(models.Customers).filter(models.Customers.email == email).first()

    if user:
        if verify_password(password, user.password):
            return user
        else:
            message = "Invalid password"
    else:
        message = "Invalid email"
        
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

def auth_v2(request: Request):
    print(request.headers)
    print(request.headers.get("authToken"))
