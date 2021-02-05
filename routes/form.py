from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
import uuid
import config
import schemas
import models
from typing import List
from database import SessionLocal
from routes import oauth
from routes.sio_router import sio
from fastapi.encoders import jsonable_encoder


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_form_details(db: Session, form_id: str):
    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        raise HTTPException(404, "Form Not Exist")

    boss = db.query(models.FormBoss).filter(models.FormBoss.form_id == form_id).limit(5)
    data = form.as_dict()
    temp = config.BOSS_SETTING.get(form.month)
    if not temp:
        bossSet = config.BOSS_SETTING.get(0).copy()
    else:
        bossSet = temp.copy()
    for i in boss:
        bossSet[i.boss - 1] = {"boss": i.boss, "name": i.name, "image": i.image, "hp": [i.hp1, i.hp2, i.hp3, i.hp4]}
    data["boss"] = bossSet
    return data


# Router


@router.get(
    "/forms/{form_id}", response_model=schemas.Form, tags=["Forms"], responses={404: {"description": "Form Not Exist"}}
)
async def get_form(form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"), db: Session = Depends(get_db)):
    """
    Get form details
    """
    return get_form_details(db, form_id)


@router.get(
    "/forms/{form_id}/status",
    tags=["Forms"],
    responses={404: {"description": "Form Not Exist"}},
)
async def get_form_status(form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"), db: Session = Depends(get_db)):
    """
    Get form details
    """
    data = (
        db.query(models.Record.week, func.count(models.Record.user_id))
        .filter(models.Record.form_id == form_id)
        .group_by(models.Record.week)
    )

    print(data)

    return data


# SELECT COUNT(`user_id`), week FROM `Records` WHERE `form_id` = 'd2ed4de53cb341a5b06b93af5859906c' GROUP BY `week`

# @router.post(
#     "/forms/create",
#     response_model=schemas.Form,
#     tags=["Forms"],
#     responses=oauth.oauthFailResponses,
# )
# async def create_form(
#     data: schemas.CreateForm = ..., user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)
# ):
#     """
#     Create a new form
#     """
#     new_form = models.Form(
#         month=data.month, owner_id=user_id, title=data.title, description=data.description, id=uuid.uuid4().hex
#     )
#     db.add(new_form)
#     db.commit()
#     return new_form.as_dict()


@router.post(
    "/forms/{form_id}/modify",
    tags=["Forms"],
    response_model=schemas.Sucess,
    responses={**oauth.oauthFailResponses, 403: {"description": "Not Owner"}, 404: {"description": "Form Not Exist"}},
)
async def modify_form(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    data: schemas.FormModify = ...,
    user_id: int = Depends(oauth.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Modify form
    """
    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        raise HTTPException(404, "Form Not Exist")
    # if form.owner_id != user_id:
    #     raise HTTPException(403, "Not Owner")

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


@router.get("/forms/{form_id}/week/{week}", response_model=List[schemas.WeekRecord], tags=["Forms", "Records"])
async def get_form_record_by_week(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    week: int = Path(..., ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Get specific form"s records with specific week
    """
    records = (
        db.query(models.Record)
        .filter(models.Record.form_id == form_id)
        .filter(models.Record.week == week)
        .filter(models.Record.status != 99)
        .all()
    )
    return [i.as_dict() for i in records]


@router.get("/forms/{form_id}/week/{week}/boss/{boss}", response_model=List[schemas.Record], tags=["Forms", "Records"])
async def get_form_record(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    week: int = Path(..., ge=1, le=200),
    boss: int = Path(..., ge=1, le=5),
    db: Session = Depends(get_db),
):
    """
    Get specific form"s records
    """
    records = (
        db.query(models.Record)
        .filter(models.Record.form_id == form_id)
        .filter(models.Record.week == week)
        .filter(models.Record.boss == boss)
        .filter(models.Record.status != 99)
        .all()
    )
    return [i.as_dict() for i in records]


@router.get(
    "/forms/{form_id}/all",
    response_model=List[schemas.AllRecord],
    tags=["Forms", "Records"],
    responses=oauth.oauthFailResponses,
)
async def get_all_form_record(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    user_id: int = Depends(oauth.get_current_user_id),
    date: date = Query(None),
    created_at: date = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get all records from specific form id
    """
    records = db.query(models.Record).filter(models.Record.form_id == form_id).filter(models.Record.status != 99)
    if date:
        records = records.filter(models.Record.last_modified > date).filter(
            models.Record.last_modified < date + timedelta(hours=24)
        )
    if created_at:
        records = records.filter(models.Record.created_at > created_at).filter(
            models.Record.created_at < created_at + timedelta(hours=24)
        )

    return [i.as_dict() for i in records]


@router.post(
    "/forms/{form_id}/week/{week}/boss/{boss}",
    response_model=schemas.Record,
    tags=["Forms", "Records"],
    responses={
        **oauth.oauthFailResponses,
        403: {"description": "Form Locked"},
        404: {"description": "Form Not Exist / Record Not Exist"},
    },
)
async def post_form_record(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    week: int = Path(..., ge=1, le=200),
    boss: int = Path(..., ge=1, le=5),
    record: schemas.PostRecord = ...,
    user_id: int = Depends(oauth.get_current_user_id),
    db: Session = Depends(get_db),
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
        record_data.team = jsonable_encoder(record.team)
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
            team=jsonable_encoder(record.team),
        )
        db.add(record_data)
        db.commit()
    data = jsonable_encoder(schemas.AllRecord(**record_data.as_dict()))
    await sio.emit("FormTracker", {"type": "RecNEW", "data": data}, room=form_id)
    return data
