from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .settings import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def make_token(user):
    return jwt.encode({"sub": str(user.id), "username": user.username, "role": user.role, "exp": datetime.now(timezone.utc)+timedelta(hours=12)}, settings.secret_key, algorithm="HS256")

def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not creds: raise HTTPException(status_code=401, detail="Sign in is required.")
    try: payload=jwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(status_code=401, detail="Your session is invalid or expired.")
    user=db.get(User,int(payload["sub"]))
    if not user: raise HTTPException(status_code=401, detail="User no longer exists.")
    return user

def require_admin(user=Depends(current_user)):
    if user.role != "admin": raise HTTPException(status_code=403, detail="Admin access is required for this action.")
    return user
