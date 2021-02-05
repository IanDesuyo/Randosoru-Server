from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List

from starlette import responses
import schemas
import models
from database import SessionLocal
from routes import oauth

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_get_user_profile(db: Session, user_id: int, me: bool = False):
    user_profile = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_profile:
        raise HTTPException(404, "User Not Exist")
    if user_profile.privacy != 0 and not me:
        raise HTTPException(403, "Private Account")
    return user_profile.as_dict()


def db_get_user_records(
    db: Session,
    user_id: int,
    form_id: str = None,
    date: datetime = None,
    created_at: datetime = None,
    limit: int = None,
    offest: int = None,
):
    records = db.query(models.Record).filter(models.Record.user_id == user_id)
    if form_id:
        records = records.filter(models.Record.form_id == form_id)
    if date:
        records = records.filter(models.Record.last_modified > date).filter(
            models.Record.last_modified < date + timedelta(hours=24)
        )
    if created_at:
        records = records.filter(models.Record.created_at > created_at).filter(
            models.Record.created_at < created_at + timedelta(hours=24)
        )
    if limit:
        records = records.limit(limit)
    if offest:
        records = records.offset(offest)
    return [i.as_dict() for i in records]


responses = {403: {"description": "Private User"}, 404: {"description": "User Not Exist"}}

# Router


@router.get("/profile/users/me", response_model=schemas.UserProfile, tags=["Users"], responses=oauth.oauthFailResponses)
def get_my_profile(user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    """
    Get current user's profile
    """
    return db_get_user_profile(db, user_id, True)


@router.get("/profile/users/{user_id}", response_model=schemas.UserProfile, tags=["Users"], responses=responses)
def get_user_profile(user_id: str = Path(..., min_length=6, max_length=16), db: Session = Depends(get_db)):
    """
    Get specific user profile by user_id
    """
    return db_get_user_profile(db, oauth.get_user_id(user_id))


@router.get("/users/me", response_model=schemas.User, tags=["Users"], responses=oauth.oauthFailResponses)
def get_my_profile_slim(user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    """
    Get current user's profile (only id, avatar ,name and uid)
    """
    return db_get_user_profile(db, user_id, True)


@router.get("/users/{user_id}", response_model=schemas.User, tags=["Users"], responses=responses)
def get_user_profile_slim(user_id: str = Path(..., min_length=6, max_length=16), db: Session = Depends(get_db)):
    """
    Get specific user profile by user_id (only id, avatar ,name and uid)
    """
    return db_get_user_profile(db, oauth.get_user_id(user_id))


@router.get(
    "/users/me/records",
    response_model=List[schemas.Record],
    tags=["Users", "Records"],
    responses=oauth.oauthFailResponses,
)
def get_my_records(
    user_id: int = Depends(oauth.get_current_user_id),
    form_id: str = Query(None, regex="^[0-9a-fA-F]{32}$"),
    date: date = Query(None),
    created_at: date = Query(None),
    limit: int = Query(None, ge=1),
    offset: int = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get current user's records
    """
    return db_get_user_records(db, user_id, form_id, date, created_at, limit, offset)


@router.get(
    "/users/{user_id}/records", response_model=List[schemas.Record], tags=["Users", "Records"], responses=responses
)
def get_user_records(
    user_id: str = Path(..., min_length=6, max_length=16),
    form_id: str = Query(None, regex="^[0-9a-fA-F]{32}$"),
    date: date = Query(None),
    created_at: date = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get specific user's records
    """
    return db_get_user_records(db, oauth.get_user_id(user_id), form_id, date, created_at, limit, offset)
