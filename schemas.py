from pydantic import BaseModel, HttpUrl
from typing import List, Set, Optional
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    id: str
    avatar: str = "https://i.imgur.com/e4KrYHe.png"
    name: str = "Unknown"
    uid: int = None

    class Config:
        orm_mode = True

class UserProfile(User):
    created_at: datetime
    privacy: int = 2
    guild_id: int = None

    class Config:
        orm_mode = True


class Guild(BaseModel):
    id: int
    name: str
    owner_id: int

class GuildMember(Guild):
    member: List[User] = set()


class Record(BaseModel):
    id: int
    boss_id: UUID
    user_id: str
    status: int
    damage: str
    comment: str
    last_modified: datetime