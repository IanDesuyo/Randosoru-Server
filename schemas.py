from pydantic import BaseModel, HttpUrl
from typing import List, Set, Optional, Union
from datetime import datetime
from uuid import UUID


class User(BaseModel):
    id: str
    avatar: str = "https://i.imgur.com/e4KrYHe.png"
    name: str = "Unknown"
    uid: int = None

    class Config:
        orm_mode = True


class Guild(BaseModel):
    id: int
    name: str
    announcement: str

    class Config:
        orm_mode = True


class UserProfile(User):
    created_at: datetime
    privacy: int = 2
    guild: Guild = None

    class Config:
        orm_mode = True


class Record(BaseModel):
    id: int
    guild_id: int
    guild_week: int
    boss: int
    user_id: str
    status: int
    damage: str
    comment: str
    last_modified: datetime

    class Config:
        orm_mode = True
