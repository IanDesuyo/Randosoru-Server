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


class UserProfile(User):
    created_at: PositiveInt
    privacy: int
    guild_name: str = None

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
    completeFormal = 21
    completeReimburse = 22
    dead = 23
    needHelp = 24
    # delete
    deleted = 99


class RecordTeam(BaseModel):
    id: PositiveInt
    star: int = Field(None, ge=1, le=6)
    rank: str = None


class Record(BaseModel):
    id: PositiveInt
    status: int
    damage: PositiveInt = None
    comment: str = None
    team: List[RecordTeam] = None
    last_modified: PositiveInt
    user: User

    class Config:
        orm_mode = True


class AllRecord(Record):
    week: int
    boss: int


class PostRecord(BaseModel):
    month: str = Field(None, regex="^(20\d{2})(1[0-2]|0[1-9])$")
    id: PositiveInt = None
    status: RecordStatus
    damage: int = Field(None, ge=1, le=20000000)
    comment: str = Field(None, max_length=40)


class PostSucess(BaseModel):
    target_id: str = None
    detail: str = "Sucess"


class FormStatus(int, Enum):
    readWrite = 0
    read = 1
    hide = 2


class CreateForm(BaseModel):
    month: str = Field(..., regex="^(20\d{2})(1[0-2]|0[1-9])$")
    title: str = Field(..., max_length=20)
    description: str = Field(None, max_length=40)


class EditForm(BaseModel):
    id: str = Field(None, regex="^[0-9a-fA-F]{32}$")
    month: str = Field(None, regex="^(20\d{2})(1[0-2]|0[1-9])$")
    title: str = Field(None, max_length=20)
    description: str = Field(None, max_length=40)
    status: FormStatus = None


class Form(CreateForm):
    id: str = Field(None, regex="^[0-9a-fA-F]{32}$")
    status: FormStatus


class CheckRegister(BaseModel):
    platform: int = Field(..., ge=1, le=2)
    user_id: str = Field(..., min_length=18, max_length=40)


class BotRegister(CheckRegister):
    avatar: str = Field(None, max_length=140)
    name: str = Field(..., max_length=40)
