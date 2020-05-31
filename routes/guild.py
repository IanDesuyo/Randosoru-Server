from fastapi import APIRouter, Response, HTTPException, Depends, Path
from sqlalchemy.orm import Session

from schemas import Guild
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


def db_get_guild(db: Session, user_id: str):
    user_profile = db.query(models.User).filter(
        models.User.id == user_id).first()
    if not user_profile:
        raise HTTPException(404, 'User not found')
    return user_profile

@router.get("/guilds/{guild_id}", response_model=Guild)
def get_guild(guild_id: int, db: Session = Depends(get_db)):
    return