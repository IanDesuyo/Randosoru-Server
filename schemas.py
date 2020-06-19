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
    uid: int = None

    class Config:
        orm_mode = True


class Guild(BaseModel):
    id: str
    name: str
    announcement: str = None

    class Config:
        orm_mode = True


class UserProfile(User):
    created_at: datetime
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
    id: int
    # guild_id: str
    # month: int
    # week: int
    # boss: int
    status: RecordStatus
    damage: int = None
    comment: str = None
    last_modified: datetime
    user: User

    class Config:
        orm_mode = True

class PostRecord(BaseModel):
    id: PositiveInt = None
    status: RecordStatus
    damage: PositiveInt = None
    comment: str = None

class PostSucess(BaseModel):
    target_id: str = None
    detail: str = "Sucess"