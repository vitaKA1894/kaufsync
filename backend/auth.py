from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError
import bcrypt # NEU: Direktes bcrypt statt passlib
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_only_for_local_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- NEU: DIREKTE BCRYPT PASSWORT FUNKTIONEN ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt erwartet Bytes, also codieren wir die Strings
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

def get_password_hash(password: str) -> str:
    # Generiert einen Salt und hasht das Passwort direkt
    return bcrypt.hashpw(
        password.encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")

# --- JWT FUNKTIONEN (Bleiben gleich) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- ABHÄNGIGKEIT: AKTUELLEN USER HOLEN ---
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    
    if not token:
        try:
            token = request.headers.get("Authorization").split("Bearer ")[1]
        except:
            raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Authentifizierungsdaten",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except PyJWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user