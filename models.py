from sqlalchemy import ForeignKey, Boolean, Column, ForeignKey, Integer, String, DateTime, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
import uuid

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, unique=True, index=True)          # Discord / Line / Twitter(?)'s user ID, like {platform(1 = Discord, 2 = Line, 3 = Twitter)}-{user ID}
    avatar = Column(String, nullable=True)                                  # Avatar from platform's api, can be update
    name = Column(String)                                                   # Username, can be update
    uid = Column(Integer, nullable=True, index=True)                        # In-game UID
    created_at = Column(DateTime, server_default=func.now())                # Account Created time
    privacy = Column(Integer, server_default=text('0'))                    # Account privacy mode, 0 = everyone, 1 = guild, 2 = self
    
    guild_id = Column(Integer, ForeignKey("guilds.id"))

    def __repr__(self):
        return "<User (%s)>" % self.platform, self.id

class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Guild ID
    name = Column(String)                                                   # Guild name
    announcement = Column(String, nullable=True)                            # Guild's announcement

    owner_id = Column(Integer)#, ForeignKey("users.id"))

#     def __repr__(self):
#         return "<Guild (%s - %s)>" % self.id, self.name

class Form(Base):
    __tablename__ = "forms"

    guild_id = Column(Integer, ForeignKey("guilds.id"), primary_key=True)
    month = Column(Integer)
    week = Column(Integer)
    boss1_id = Column(UUIDType(binary=True), ForeignKey("records.boss_id"), unique=True)
    boss2_id = Column(UUIDType(binary=True), ForeignKey("records.boss_id"), unique=True)
    boss3_id = Column(UUIDType(binary=True), ForeignKey("records.boss_id"), unique=True)
    boss4_id = Column(UUIDType(binary=True), ForeignKey("records.boss_id"), unique=True)
    boss5_id = Column(UUIDType(binary=True), ForeignKey("records.boss_id"), unique=True)
    
class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    boss_id = Column(UUIDType(binary=False), index=True)
    user_id = Column(String, index=True)
    status = Column(Integer, server_default=text('10'))
    damage = Column(Integer)
    comment = Column(String, nullable=True)
    last_modified = Column(DateTime, server_default=func.now(), server_onupdate=func.now())

    def __repr__(self):
        return "<Record (%s - %s)>" % self.id, self.user_id