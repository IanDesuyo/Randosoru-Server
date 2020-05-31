from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session

from schemas import User, UserProfile
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


# get user's records
def db_get_user_records(db: Session, user_id: str):
    user_records = db.query(models.Record).filter(
        models.Record.user_id == user_id).all()
    if not user_records:
        raise HTTPException(404, 'Record not found')
    return user_records

@router.get("/users/{user_id}/records")
def get_user_records(user_id: str = Path(None, min_length=10, max_length=35, regex="^[0-3]-.*$"), db: Session = Depends(get_db)):
    return db_get_user_records(db, user_id)

# Get Profile


def db_get_user_profile(db: Session, user_id: str, me: bool = False):
    user_profile = db.query(models.User).filter(
        models.User.id == user_id).first()
    if not user_profile:
        raise HTTPException(404, 'User not found')
    if user_profile.privacy != 0 and not me:
        raise HTTPException(403, 'User privacy blocked')
    return user_profile


@router.get("/profile/users/me", response_model=UserProfile)
def get_user_profile_me(user_id: str = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    return db_get_user_profile(db, user_id, True)


@router.get("/profile/users/{user_id}", response_model=UserProfile)
def get_user_profile(user_id: str = Path(None, min_length=10, max_length=35, regex="^[0-3]-.*$"), db: Session = Depends(get_db)):
    return db_get_user_profile(db, user_id)

# Just id, avatar and name

@router.get("/users/me", response_model=User)
def get_user_profile_me(user_id: str = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)):
    return db_get_user_profile(db, user_id, True)

@router.get("/users/{user_id}", response_model=User)
def get_user_profile_me(user_id: str = Path(None, min_length=10, max_length=35, regex="^[0-3]-.*$"), db: Session = Depends(get_db)):
    return db_get_user_profile(db, user_id)
