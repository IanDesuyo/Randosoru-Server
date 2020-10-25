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
from routes.sio_router import sio
from fastapi.encoders import jsonable_encoder

router = APIRouter()

models.Base.metadata.create_all(bind=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def check_x_token(x_token: str = Header(...)):
    if not x_token in config.API_TOKEN:
        raise HTTPException(401, "Forbidden")
    return True


responses = {401: {"description": "Forbidden"}}

# Router


@router.post(
    "/bot/forms/{form_id}/week/{week}/boss/{boss}",
    response_model=schemas.Record,
    tags=["Bot"],
    responses={
        **responses,
        403: {"description": "Form Locked"},
        404: {"description": "Form Not Exist / Record Not Exist"},
    },
)
async def post_form_record(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    week: int = Path(..., ge=1, le=200),
    boss: int = Path(..., ge=1, le=5),
    record: schemas.PostRecord = ...,
    user_id: str = Depends(oauth.bot_get_user_id),
    db: Session = Depends(get_db),
    x_token: bool = Depends(check_x_token),
):
    """
    Add or update a record\n
    It will try to update exist record if request include an id.
    """
    formData = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not formData:
        raise HTTPException(404, "Form Not Exist")
    if formData.status != 0:
        raise HTTPException(403, "Form Locked")

    if record.id:
        record_data = (
            db.query(models.Record)
            .filter(models.Record.form_id == form_id)
            .filter(models.Record.user_id == user_id)
            .filter(models.Record.id == record.id)
            .filter(models.Record.status != 99)
            .first()
        )
        if not record_data:
            raise HTTPException(404, "Record Not Exist")

        record_data.status = record.status.value
        record_data.damage = record.damage
        record_data.comment = record.comment
        record_data.last_modified = datetime.utcnow()
        db.commit()
        data = jsonable_encoder(schemas.AllRecord(**record_data.as_dict()))
        await sio.emit("FormTracker", {"type": "RecUP", "data": data}, room=form_id)
        return data
    else:
        record_data = models.Record(
            form_id=form_id,
            month=record.month if record.month else formData.month,
            week=week,
            boss=boss,
            status=record.status.value,
            damage=record.damage,
            comment=record.comment,
            user_id=user_id,
        )
        db.add(record_data)
        db.commit()
    data = jsonable_encoder(schemas.AllRecord(**record_data.as_dict()))
    await sio.emit("FormTracker", {"type": "RecNEW", "data": data}, room=form_id)
    return data


@router.post(
    "/bot/forms/create",
    response_model=schemas.Form,
    tags=["Bot"],
    responses=responses,
)
async def create_form(
    data: schemas.CreateForm = ...,
    user_id: str = Depends(oauth.bot_get_user_id),
    db: Session = Depends(get_db),
    x_token: bool = Depends(check_x_token),
):
    """
    Create a new form
    """
    new_form = models.Form(
        month=data.month, owner_id=user_id, title=data.title, description=data.description, id=uuid.uuid4().hex
    )
    db.add(new_form)
    db.commit()
    return new_form.as_dict()


@router.post(
    "/bot/forms/{form_id}/modify",
    response_model=schemas.Form,
    tags=["Bot"],
    responses={**responses, 404: {"description": "Form Not Exist"}},
)
async def modify_form(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    data: schemas.FormModify = ...,
    db: Session = Depends(get_db),
    x_token: bool = Depends(check_x_token),
):
    """
    Modify form
    """
    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        raise HTTPException(404, "Form Not Exist")

    if data.title:
        form.title = data.title
    if data.description:
        form.description = data.description
    if data.boss:
        for i in data.boss:
            boss = (
                db.query(models.FormBoss)
                .filter(models.FormBoss.form_id == form_id)
                .filter(models.FormBoss.boss == i.boss)
                .first()
            )
            if boss:
                boss.name = i.name
                boss.image = i.image
                boss.hp1 = i.hp[0]
                boss.hp2 = i.hp[1]
                boss.hp3 = i.hp[2]
                boss.hp4 = i.hp[3]
                db.flush()
            else:
                boss = models.FormBoss(
                    form_id=form_id,
                    boss=i.boss,
                    name=i.name,
                    image=i.image,
                    hp1=i.hp[0],
                    hp2=i.hp[1],
                    hp3=i.hp[2],
                    hp4=i.hp[3],
                )
                db.add(boss)
    db.commit()
    await sio.emit("FormTracker", {"type": "modify", "message": "Form has been modified"}, room=form_id)
    return {"detail": "Sucess"}


@router.get(
    "/bot/isRegister",
    response_model=schemas.UserProfile,
    tags=["Bot"],
    responses={**responses, 404: {"description": "User Not Exist"}},
)
async def check_is_register(
    platform: int = Query(..., ge=1, le=2),
    user_id: str = Query(..., min_length=18, max_length=40),
    db: Session = Depends(get_db),
    x_token: bool = Depends(check_x_token),
):
    """
    Check if the user is registered or not
    """
    checkExist = (
        db.query(models.OauthDetail)
        .filter(models.OauthDetail.platform == platform)
        .filter(models.OauthDetail.id == user_id)
        .first()
    )
    if not checkExist:
        raise HTTPException(404, "User Not Exist")
    return checkExist.user.as_dict()


@router.post(
    "/bot/register",
    response_model=schemas.UserProfile,
    tags=["Bot"],
    responses={400: {"description": "User Exist"}},
)
async def register_new_user(
    user_data: schemas.BotRegister = ...,
    db: Session = Depends(get_db),
    x_token: bool = Depends(check_x_token),
):
    """
    Register a new user
    """
    checkExist = (
        db.query(models.OauthDetail)
        .filter(models.OauthDetail.platform == user_data.platform)
        .filter(models.OauthDetail.id == user_data.user_id)
        .first()
    )
    if checkExist:
        raise HTTPException(400, "User Exist")

    if user_data.platform == 2:
        newUser = models.User(avatar=f"{user_data.avatar}.png" if user_data.avatar else None, name=user_data.name)
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(platform=2, id=user_data.user_id, user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()
        return newUser.as_dict()
