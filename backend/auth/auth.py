from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
from database.db import users_collection

SECRET_KEY = "mvp_secret_key"
ALGORITHM = "HS256"

router = APIRouter(prefix="/api/iam")

# ===== Schemas =====
class UserRegisterForm(BaseModel):
    email: str
    password: str

class UserLoginForm(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str

# ===== Helpers =====
def create_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ===== Register =====
# @router.post("/register", response_model=AuthResponse)
# async def register(form: UserRegisterForm):
#     existing_user = await users_collection.find_one({"email": form.email})
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User already exists")
    
#     user_doc = {
#         "email": form.email,
#         "password": form.password,
#         "role": "user",
#         "created_at": datetime.utcnow()
#     }
#     result = await users_collection.insert_one(user_doc)

#     access_token = create_token({"sub": form.email, "role": "user"})
#     refresh_token = create_token({"sub": form.email, "role": "user"}, expires_minutes=1440)
#     return {"access_token": access_token, "refresh_token": refresh_token}

# ===== Login =====
@router.post("/login", response_model=AuthResponse)
async def login(form: UserLoginForm):
    user = await users_collection.find_one({"email": form.email})
    if not user or user["password"] != form.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_token({"sub": user["email"], "role": user["role"]})
    refresh_token = create_token({"sub": user["email"], "role": user["role"]}, expires_minutes=1440)
    return {"access_token": access_token, "refresh_token": refresh_token}