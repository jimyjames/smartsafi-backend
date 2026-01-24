from fastapi import  Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, Token,UserResponse
from emails import send_verification_email
from . import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_verification_token,
    verify_token,
    router ,
    get_current_user
)

auth_router = router


@auth_router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = User(
        email=user.email, 
        hashed_password=hashed_pw, 
        role=user.role
        )
    if user.role == "admin":
        new_user.is_admin = True
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    email_token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, email_token)

    access_token = create_access_token({"sub": new_user.id, "role": new_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@auth_router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    return {"message": "Email successfully verified"}


@auth_router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # if not db_user.is_verified:
    #     raise HTTPException(status_code=403, detail="Email not verified")

    token = create_access_token({"client_id": db_user.id, "role": db_user.role, "email": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
