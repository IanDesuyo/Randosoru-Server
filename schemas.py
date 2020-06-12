from pydantic import BaseModel
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
    id: str
    name: str
    announcement: str = None

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
    guild_id: str
    month: int
    week: int
    boss: int
    status: int
    damage: int = None
    comment: str = None
    last_modified: datetime
    user: User

    class Config:
        orm_mode = True

class PostRecord(BaseModel):
    boss: int
    status: int
    damage: int = None
    comment: str = None