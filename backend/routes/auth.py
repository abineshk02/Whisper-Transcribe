from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from models import User
from database import get_db
from schemas import SignupRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])
MAX_PASSWORD_LENGTH = 128

# Signup
@router.post("/signup")
def signup(auth: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == auth.username) | (User.email == auth.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=auth.username,
        email=auth.email,
        hashed_password=bcrypt.hash(auth.password[:MAX_PASSWORD_LENGTH])
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Signup successful", "user_id": user.id}

# Login
@router.post("/login")
def login(auth: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == auth.username).first()
    if not user or not bcrypt.verify(auth.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"message": "Login successful", "user_id": user.id, "username": user.username}
