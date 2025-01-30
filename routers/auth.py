from starlette.responses import JSONResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from typing import Optional
from database import models
from database.database import get_db
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

SECRET_KEY = "2c2b9ce8f69a8108ce6e2d3b3ecfc715641df3645a188f83341bf6c48368c404"
ALGORITHM = "HS256"

templates = Jinja2Templates(directory="templates")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["auth"])

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(models.Customers).filter(models.Customers.email == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            raise HTTPException(status_code=401, detail="Token missing")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Token invalid")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=403, detail="Token verification failed")

@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        token_expires = timedelta(minutes=60)
        token = create_access_token(user.email, user.id, expires_delta=token_expires)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_form(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = JSONResponse(content={"user_name": form.username})
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)
        if not validate_user_cookie:
            raise HTTPException(status_code=401, detail="Incorrect Username or Password")
        return response
    except HTTPException as e:
        msg = str(e.detail)
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.get("/logout")
async def logout(request: Request):
    try:
        msg = "Logout Successful"
        response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        response.delete_cookie(key="access_token")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        validation = db.query(models.Customers).filter(models.Customers.email == email).first()
        if validation is not None:
            raise HTTPException(status_code=208, detail="Email already registered")

        user_model = models.Customers()
        user_model.username = name
        user_model.email = email
        hash_password = get_password_hash(password)
        user_model.password = hash_password
        user_model.is_active = True

        db.add(user_model)
        db.commit()

        msg = "User successfully created"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    except HTTPException as e:
        msg = str(e.detail)
        # return templates.TemplateResponse("register.html", {"request": request, "msg": msg})
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")
