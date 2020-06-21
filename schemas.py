from pydantic import BaseModel, Field, PositiveInt
from typing import List, Set, Optional, Union
from datetime import datetime
from enum import Enum


class OauthReturn(BaseModel):
    id: str
    token: str


class User(BaseModel):
    id: str
    avatar: str = "https://i.imgur.com/e4KrYHe.png"
    name: str
    uid: PositiveInt = None

    class Config:
        orm_mode = True


class Guild(BaseModel):
    id: str
    name: str
    announcement: str = None

    class Config:
        orm_mode = True


class UserProfile(User):
    created_at: PositiveInt
    privacy: int
    guild: Guild = None

    class Config:
        orm_mode = True


class RecordStatus(int, Enum):
    # sign up
    formal = 1
    reimburse = 2
    kyaru = 3
    # waiting
    inBattle = 11
    waiting = 12
    waitingMention = 13
    # report
    complete = 21
    dead = 22
    needHelp = 23
    # delete
    deleted = 99


class Record(BaseModel):
    id: PositiveInt
    # form_id: str
    # month: int
    # week: int
    # boss: int
    status: int
    damage: PositiveInt = None
    comment: str = None
    last_modified: PositiveInt
    user: User

    class Config:
        orm_mode = True


class PostRecord(BaseModel):
    month: str = Field(None, regex="^(20\d{2})(1[0-2]|0[1-9])$")
    id: PositiveInt = None
    status: RecordStatus
    damage: PositiveInt = None
    comment: str = None


class PostSucess(BaseModel):
    target_id: str = None
    detail: str = "Sucess"


class FormStatus(int, Enum):
    readWrite = 0
    read = 1
    hide = 2


class CreateForm(BaseModel):
    month: str = Field(None, regex="^(20\d{2})(1[0-2]|0[1-9])$")
    title: str
    description: str = None


class EditForm(BaseModel):
    id: str = Field(None, regex="^[0-9a-fA-F]{32}$")
    month: str = Field(None, regex="^(20\d{2})(1[0-2]|0[1-9])$")
    title: str = None
    description: str = None
    status: FormStatus = None


class Form(CreateForm):
    id: str = Field(None, regex="^[0-9a-fA-F]{32}$")
    status: FormStatus
