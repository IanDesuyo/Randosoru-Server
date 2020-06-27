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


def platform2user(platform: int = Query(..., ge=1, le=2), user_id: str = Query(..., min_length=18, max_length=40), db: Session = Depends(get_db)):
    OauthDetail = db.query(models.OauthDetail).filter(
        models.OauthDetail.platform == platform).filter(
        models.OauthDetail.id == user_id).first()
    if not OauthDetail:
        raise HTTPException(404, "User not found")
    if OauthDetail.user.status != 0:
        raise HTTPException(403, "You have been banned")
    return OauthDetail


def recordUserID2platformID(Record, pfID):
    tempR = Record.as_dict()
    tempU = tempR["user"].as_dict()
    tempU["id"] = pfID
    tempR.update({"user": tempU})
    return tempR


def formOwnerID2platformID(Form, pfID):
    tempF = Form.as_dict()
    tempF["owner_id"] = pfID
    return tempF


def check_x_token(x_token: str = Header(...)):
    if not x_token in config.API_TOKEN:
        raise HTTPException(403, "Forbidden")
    return True
# Router


@router.post("/bot/forms/{form_id}/week/{week}/boss/{boss}", response_model=schemas.Record, tags=["Bot"])
def post_form_record(form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
                     week: int = Path(..., ge=1, lt=100),
                     boss: int = Path(..., ge=1, le=5),
                     x_token: bool = Depends(check_x_token),
                     record: schemas.PostRecord = None,
                     OauthDetail: dict = Depends(platform2user),
                     db: Session = Depends(get_db)):
    """
    Add or update a record\n
    It will try to update exist record if request include an id. 
    """
    if not record:
        raise HTTPException(400, "Missing Record data")
    formData = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not formData:
        raise HTTPException(404, "Form not found")
    if formData.status != 0:
        raise HTTPException(403, "Form locked")

    if record.id:
        record_data = db.query(models.Record).filter(
            models.Record.form_id == form_id).filter(
            models.Record.week == week).filter(
            models.Record.user_id == OauthDetail.user.id).filter(
            models.Record.id == record.id).filter(
            models.Record.status != 99).first()
        if not record_data:
            raise HTTPException(404, "Record not found")
        record_data.status = record.status.value
        record_data.damage = record.damage
        record_data.comment = record.comment
        record_data.last_modified = datetime.utcnow()
        db.commit()
        return recordUserID2platformID(record_data, OauthDetail.id)
    else:
        record_data = models.Record(form_id=form_id, month=record.month, week=week, boss=boss,
                                    status=record.status.value, damage=record.damage, comment=record.comment, user_id=OauthDetail.user_id)
        db.add(record_data)
        db.commit()
        record_data.user.id = OauthDetail.id
    return recordUserID2platformID(record_data, OauthDetail.id)


@router.post("/bot/forms/create", response_model=schemas.Form, tags=["Bot"])
def create_form(data: schemas.CreateForm = None,
                x_token: bool = Depends(check_x_token),
                OauthDetail: dict = Depends(platform2user),
                db: Session = Depends(get_db)):
    """
    Create a new form
    """
    if not data:
        raise HTTPException(400, "Missing Form data")
    new_form = models.Form(month=data.month, owner_id=OauthDetail.user_id,
                           title=data.title, description=data.description, id=uuid.uuid4().hex)
    db.add(new_form)
    db.commit()
    return formOwnerID2platformID(new_form, OauthDetail.user_id)


@router.post("/bot/forms/modify", response_model=schemas.Form, tags=["Bot"])
def modify_form(data: schemas.EditForm = None,
                x_token: bool = Depends(check_x_token),
                OauthDetail: dict = Depends(platform2user),
                db: Session = Depends(get_db)):
    """
    Modify form
    """
    if not data:
        raise HTTPException(400, "Missing Form data")
    form = db.query(models.Form).filter(
        models.Form.id == data.id).filter(
        models.Form.owner_id == OauthDetail.user_id).first()
    if not form:
        raise HTTPException(404, "Form not found")
    if data.month:
        form.month = data.month
    if data.title:
        form.title = data.title
    if data.description:
        form.description = data.description
    if data.status:
        form.status = data.status
    db.commit()
    return formOwnerID2platformID(form, OauthDetail.user_id)


@router.post("/bot/register", response_model=schemas.UserProfile, tags=["Bot"])
def registration_new_user(x_token: bool = Depends(check_x_token),
                          platform: int = Query(..., ge=1, le=2),
                          user_id: str = Query(..., min_length=18, max_length=40),
                          avatar: str = Query(None, max_length=140),
                          name: str = Query(..., max_length=40),
                          db: Session = Depends(get_db)):
    checkExist = db.query(models.OauthDetail).filter(
        models.OauthDetail.platform == platform).filter(models.OauthDetail.id == user_id).first()
    if checkExist:
        raise HTTPException(400, "User exist")

    if platform == 2:
        newUser = models.User(
            avatar=f"{avatar}.png", name=name)
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(
            platform=2, id=user_id, user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()
        temp = newUser.as_dict()
        temp["id"] = oauth.get_hashed_id(temp["id"])
        return temp
