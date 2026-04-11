import models
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status, Request, Depends
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


def find_user(db ,email: str = None, id: int =None):
    if email:
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    user = db.query(models.User).filter(models.User.id == id).first()
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
async def get_user_from_token(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if token:
        user_decoded = decode_token(token)
        if not user_decoded:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid credentials"
            )
        user = db.query(models.User).filter(models.User.id == user_decoded["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized"
    )