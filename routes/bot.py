from fastapi import APIRouter, HTTPException, Depends, Path, Header, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
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

# Router


@router.post("/bot/{form_id}/week/{week}/boss/{boss}", response_model=schemas.Record, tags=["Bot"])
def post_form_record(form_id: str = Path(None, regex="^[0-9a-fA-F]{32}$"),
                     week: int = Path(None, ge=1, lt=100),
                     boss: int = Path(None, ge=1, le=5),
                     record: schemas.PostRecord = None,
                     platform: int = Query(None, ge=1, le=2),
                     user_id: str = Query(None, min_length=18, max_length=40),
                     x_token: str = Header(None),
                     db: Session = Depends(get_db)):
    """
    Add or update a record\n
    It will try to update exist record if request include an id. 
    """
    if not x_token in config.API_TOKEN:
        raise HTTPException(403, "Forbidden")
    if not user_id or not platform:
        raise HTTPException(400, "Missing User data")
    if not record:
        raise HTTPException(400, "Missing Record data")

    # get user
    OauthDetail = db.query(models.OauthDetail).filter(
        models.OauthDetail.platform == platform).filter(
        models.OauthDetail.id == user_id).first()
    if not OauthDetail:
        raise HTTPException(404, "User not found")
    if OauthDetail.user.status != 0:
        raise HTTPException(403, "You have been banned")

    if record.id:
        record_data = db.query(models.Record).filter(
            models.Record.form_id == form_id).filter(
            models.Record.week == week).filter(
            models.Record.user_id == OauthDetail.user.id).filter(
            models.Record.id == record.id).filter(
            models.Record.status != 99).first()
        if not record_data:
            raise HTTPException(404, "Record not found")
        record_data.status = record.status
        record_data.damage = record.damage
        record_data.comment = record.comment
        record_data.last_modified = datetime.utcnow()
        db.commit()
        return record_data.as_dict()
    else:
        record_data = models.Record(form_id=form_id, month=record.month, week=week, boss=boss,
                                    status=record.status, damage=record.damage, comment=record.comment, user_id=OauthDetail.user.id)
        db.add(record_data)
        db.commit()
    return record_data.as_dict()
