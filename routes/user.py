from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session

from typing import List
import schemas
import models
from database import SessionLocal, engine
from routes import oauth

router = APIRouter()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Router


def db_get_user_profile(db: Session, user_id: int, me: bool = False, response_model=schemas.UserProfile, tags=["Users"]):
    user_profile = db.query(models.User).filter(
        models.User.id == user_id).first()
    if not user_profile:
        raise HTTPException(404, 'User not found')
    if user_profile.privacy != 0 and not me:
        raise HTTPException(403, 'User privacy blocked')
    return user_profile.as_dict()


@router.get("/profile/users/me", response_model=schemas.UserProfile, tags=["Users"])
def get_my_profile(user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    """
    Get current user's profile
    """
    return db_get_user_profile(db, user_id, True)


@router.get("/profile/users/{user_id}", response_model=schemas.UserProfile, tags=["Users"])
def get_user_profile(user_id: str = Path(..., min_length=6, max_length=16), db: Session = Depends(get_db)):
    """
    Get specific user profile by user_id
    """
    return db_get_user_profile(db, oauth.get_user_id(user_id))


@router.get("/users/me", response_model=schemas.User, tags=["Users"])
def get_my_profile_slim(user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    """
    Get current user's profile (only id, avatar ,name and uid)
    """
    return db_get_user_profile(db, user_id, True)


@router.get("/users/{user_id}", response_model=schemas.User, tags=["Users"])
def get_user_profile_slim(user_id: str = Path(..., min_length=6, max_length=16), db: Session = Depends(get_db)):
    """
    Get specific user profile by user_id (only id, avatar ,name and uid)
    """
    return db_get_user_profile(db, oauth.get_user_id(user_id))


@router.get("/users/me/records", response_model=List[schemas.Record], tags=["Users", "Records"])
def get_my_records(user_id: int = Depends(oauth.get_current_user_id), page: int = Query(1, ge=0, le=100), db: Session = Depends(get_db)):
    """
    Get current user's records
    """
    records = db.query(models.Record).filter(
        models.Record.user_id == user_id).all().limit(10).offset((page-1)*10)
    return {i.as_dict() for i in records}
