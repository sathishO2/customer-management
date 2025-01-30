from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain_pwd,hashed_pwd):
    return pwd_context.verify(plain_pwd,hashed_pwd)

