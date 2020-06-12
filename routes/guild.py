from fastapi import APIRouter, Response, HTTPException, Depends, Path, Header
from sqlalchemy.orm import Session

import config
import schemas
import models
from typing import List
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


# Get guild records

@router.get("/guilds/{guild_id}/{month}/{week}", response_model=List[schemas.Record], tags=["Guilds", "Records"])
def get_guild(guild_id: str = Path(None, min_length=18, max_length=32),
              month: int = Path(None),
              week: int = Path(None, ge=1, le=12),
              db: Session = Depends(get_db)):
    records = db.query(models.Record).filter(
        models.Record.guild_id == guild_id).filter(
        models.Record.month == month).filter(
        models.Record.week == week).all()
    if not records:
        raise HTTPException(404, 'Record not found')
    return {i.as_dict() for i in records}


@router.post("/guilds/{guild_id}/{month}/{week}",  tags=["Guilds", "Records"])
def get_guild(guild_id: str = Path(None, min_length=18, max_length=32),
              month: int = Path(None),
              week: int = Path(None, ge=1, le=12),
              record: schemas.PostRecord = None,
              user_id: int = Depends(oauth.get_current_user_id),
              db: Session = Depends(get_db)):
    if not record:
        raise HTTPException(400, 'Missing Record data')
    record_data = models.Record(guild_id=guild_id, month=month, week=week, boss=record.boss,
                                status=record.status, damage=record.damage, comment=record.comment, user_id=user_id)
    db.add(record_data)
    db.commit()
    return record_data


# Get guild profile


@router.get("/guilds/{guild_id}", response_model=schemas.Guild, tags=["Guilds"])
def get_guild(guild_id: str = Path(None, min_length=18, max_length=32), db: Session = Depends(get_db)):
    guild_data = db.query(models.Guild).filter(
        models.Guild.id == guild_id).first()
    if not guild_data:
        raise HTTPException(404, 'Guild not found')
    return guild_data

# Modify guild


@router.post("/guilds/modify", tags=["Guilds", "Bot Func"])
def modify_guild(guild: schemas.Guild, x_token: str = Header(None), db: Session = Depends(get_db)):
    if not x_token in config.API_TOKEN:
        raise HTTPException(401, "Could not validate token")

    guild_data = db.query(models.Guild).filter(
        models.Guild.id == guild.id).first()
    if not guild_data:
        guild_data = models.Guild(id=guild.id, name=guild.name)
        db.add(guild_data)
    else:
        if guild_data.name != guild.name:
            guild_data.name = guild.name
        if guild_data.announcement != guild.announcement:
            guild_data.announcement = guild.announcement
    db.commit()
    return {"id": guild_data.id, "name": guild_data.name, "announcement": guild.announcement}
