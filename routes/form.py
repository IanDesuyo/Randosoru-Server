from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
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


@router.get("/forms/{form_id}", response_model=schemas.Form, tags=["Forms"])
def get_form(form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"), db: Session = Depends(get_db)):
    """
    Get form details
    """
    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        raise HTTPException(404, "Form not found")

    boss = db.query(models.FormBoss).filter(models.FormBoss.form_id == form_id).limit(5)
    data = form.as_dict()
    bossSet = config.BOSS_SETTING.get(form.month)
    if not bossSet:
        bossSet = config.BOSS_SETTING.get(0)
    for i in boss:
        bossSet[i.boss - 1] = {"boss": i.boss, "name": i.name, "image": i.image}
    data["boss"] = bossSet
    return data


@router.post("/forms/create", response_model=schemas.Form, tags=["Forms"], deprecated=True)
def create_form(
    data: schemas.CreateForm = None, user_id: int = Depends(oauth.get_current_user_id), db: Session = Depends(get_db)
):
    """
    **deprecated**\n
    Create a new form
    """
    raise HTTPException(400, "Deprecated")
    if not data:
        raise HTTPException(400, "Missing Form data")
    new_form = models.Form(
        month=data.month, owner_id=user_id, title=data.title, description=data.description, id=uuid.uuid4().hex
    )
    db.add(new_form)
    db.commit()
    return new_form.as_dict()


@router.post("/forms/{form_id}/modify", response_model=schemas.Form, tags=["Forms"])
def modify_form(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    data: schemas.FormModify = None,
    user_id: int = Depends(oauth.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Modify form
    """
    if not data:
        raise HTTPException(400, "Missing data")
    if len(data.boss) > 5:
        raise HTTPException(422, "Too many boss settings")
    form = db.query(models.Form).filter(models.Form.id == form_id).filter(models.Form.owner_id == user_id).first()
    if not form:
        raise HTTPException(404, "Form not found")
    print(data)
    print(form.__dict__)
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
                db.flush()
            else:
                boss = models.FormBoss(form_id=form_id, boss=i.boss, name=i.name, image=i.image)
                db.add(boss)
    db.commit()
    data = form.as_dict()

    boss = db.query(models.FormBoss).filter(models.FormBoss.form_id == form_id).limit(5)
    bossSet = config.BOSS_SETTING.get(form.month)
    if not bossSet:
        bossSet = config.BOSS_SETTING.get(0)
    for i in boss:
        bossSet[i.boss - 1] = {"boss": i.boss, "name": i.name, "image": i.image}
    data["boss"] = bossSet
    return data


@router.get("/forms/{form_id}/week/{week}", response_model=List[schemas.WeekRecord], tags=["Forms", "Records"])
def get_form_record_by_week(
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
def get_form_record(
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


@router.get("/forms/{form_id}/all", response_model=List[schemas.AllRecord], tags=["Forms", "Records"])
def get_form_record(
    form_id: str = Path(..., regex="^[0-9a-fA-F]{32}$"),
    user_id: int = Depends(oauth.get_current_user_id),
    date: date = Query(None),
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

    return [i.as_dict() for i in records]


@router.post("/forms/{form_id}/week/{week}/boss/{boss}", response_model=schemas.Record, tags=["Forms", "Records"])
def post_form_record(
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
    if not record:
        raise HTTPException(400, "Missing Record data")
    formData = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not formData:
        raise HTTPException(404, "Form not found")
    if formData.status != 0:
        raise HTTPException(403, "Form locked")

    if record.id:
        record_data = (
            db.query(models.Record)
            .filter(models.Record.form_id == form_id)
            .filter(models.Record.week == week)
            .filter(models.Record.user_id == user_id)
            .filter(models.Record.id == record.id)
            .filter(models.Record.status != 99)
            .first()
        )
        if not record_data:
            raise HTTPException(404, "Record not found")
        record_data.status = record.status.value
        record_data.damage = record.damage
        record_data.comment = record.comment
        record_data.last_modified = datetime.utcnow()
        db.commit()
        return record_data.as_dict()
    else:
        record_data = models.Record(
            form_id=form_id,
            month=record.month,
            week=week,
            boss=boss,
            status=record.status.value,
            damage=record.damage,
            comment=record.comment,
            user_id=user_id,
            last_modified=datetime.utcnow(),
        )
        db.add(record_data)
        db.commit()
    return record_data.as_dict()
