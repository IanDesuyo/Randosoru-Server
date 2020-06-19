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

# Router


@router.get("/guilds/{guild_id}/records/{month}/{week}/{boss}", response_model=List[schemas.Record], tags=["Guilds", "Records"])
def get_guild_record(guild_id: str = Path(None, min_length=18, max_length=32),
                     month: str = Path(None, regex="^(20\d{2})(1[0-2]|0[1-9])$"),
                     week: int = Path(None, ge=1, lt=100),
                     boss: int = Path(None, ge=1, le=5),
                     db: Session = Depends(get_db)):
    """
    Get specific guild's records
    """
    records = db.query(models.Record).filter(
        models.Record.guild_id == guild_id).filter(
        models.Record.month == month).filter(
        models.Record.week == week).filter(
        models.Record.boss == boss).all()
    if not records:
        raise HTTPException(404, 'Record not found')
    return {i.as_dict() for i in records}


@router.post("/guilds/{guild_id}/records/{month}/{week}/{boss}", response_model=schemas.Record, tags=["Guilds", "Records"])
def post_guild_record(guild_id: str = Path(None, min_length=18, max_length=32),
                      month: str = Path(None, regex="^(20\d{2})(1[0-2]|0[1-9])$"),
                      week: int = Path(None, ge=1, lt=100),
                      boss: int = Path(None, ge=1, le=5),
                      record: schemas.PostRecord = None,
                      user_id: int = Depends(oauth.get_current_user_id),
                      db: Session = Depends(get_db)):
    """
    Add or update a record\n
    It will try to update exist record if request include an id. 
    """
    if not record:
        raise HTTPException(400, 'Missing Record data')

    if record.id:
        record_data = db.query(models.Record).filter(
            models.Record.guild_id == guild_id).filter(
            models.Record.month == month).filter(
            models.Record.week == week).filter(
            models.Record.user_id == user_id).filter(
            models.Record.id == record.id).filter(
            models.Record.status != 99).first()
        if not record_data:
            raise HTTPException(404, 'Record not found')
        if record.status != record_data.status:
            record_data.status = record.status
        if record.damage:
            record_data.damage = record.damage
        if record.comment:
            record_data.comment = record.comment
        db.commit()
        return record_data.as_dict()
    else:
        record_data = models.Record(guild_id=guild_id, month=month, week=week, boss=boss,
                                    status=record.status, damage=record.damage, comment=record.comment, user_id=user_id)
        db.add(record_data)
        db.commit()
    return record_data.as_dict()


@router.post("/guilds/modify", response_model=schemas.PostSucess, tags=["Guilds", "Bot Func"])
def modify_guild(guild: schemas.Guild, x_token: str = Header(None), db: Session = Depends(get_db)):
    """
    Modify guild details\n
    **Need X-Token, for BOT use only**
    """
    if not x_token in config.API_TOKEN:
        raise HTTPException(401, "Could not validate token")

    guild_data = db.query(models.Guild).filter(
        models.Guild.id == guild.id).first()
    if not guild_data:
        guild_data = models.Guild(
            id=guild.id, name=guild.name, announcement=guild.announcement)
        db.add(guild_data)
    else:
        if guild_data.name != guild.name:
            guild_data.name = guild.name
        if guild_data.announcement != guild.announcement:
            guild_data.announcement = guild.announcement
    db.commit()
    return {"target_id": guild_data.id}


@router.get("/guilds/{guild_id}", response_model=schemas.Guild, tags=["Guilds"])
def get_guild_detail(guild_id: str = Path(None, min_length=18, max_length=32), db: Session = Depends(get_db)):
    """
    Get specific guild details by guild_id
    """
    guild_data = db.query(models.Guild).filter(
        models.Guild.id == guild_id).first()
    if not guild_data:
        raise HTTPException(404, 'Guild not found')
    return guild_data
