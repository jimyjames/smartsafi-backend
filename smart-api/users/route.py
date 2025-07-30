from . import router as users_router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas,models
from schemas import UserCreate,UserLogin


def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@users_router.post("/register", response_model=schemas.Token)
def register(token="hey there"):
# (user: UserCreate, db: Session = Depends(get_db)):
    # db_user = db.query(models.User).filter(models.User.email == user.email).first()
    # if db_user:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # hashed_pw = models.get_password_hash(user.password)
    # new_user = models.User(email=user.email, hashed_password=hashed_pw)
    
    # db.add(new_user)
    # db.commit()
    # db.refresh(new_user)
    
    # token = models.create_access_token(data={"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer"}