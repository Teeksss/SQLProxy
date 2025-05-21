from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Örnek kullanıcı doğrulama
    return {"username": "admin"}

def get_current_user_admin(token: str = Depends(oauth2_scheme)):
    # Admin yetkisi olan kullanıcı döndürülür
    return {"username": "admin", "role": "admin"}

def get_db():
    # Geçici db bağlamı (mock)
    db = {}
    try:
        yield db
    finally:
        pass