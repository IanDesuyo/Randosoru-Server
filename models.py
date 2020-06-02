from sqlalchemy import ForeignKey, Boolean, Column, ForeignKey, Integer, String, DateTime, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
import uuid

from database import Base


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    avatar = Column(String, nullable=True)
    name = Column(String)
    uid = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    privacy = Column(Integer, server_default=text('0'))

    guild_id = Column(Integer, ForeignKey("Guilds.id"), nullable=True, index=True)

    def __repr__(self):
        return "<User (%s)>" % self.platform, self.id


class OauthDetail(Base):
    __tablename__ = "OauthDetails"

    platform = Column(Integer)
    id = Column(String, primary_key=True, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"))

    def __repr__(self):
        return "<OauthDetail (%s-%s)>" % self.platform, self.id


class Guild(Base):
    __tablename__ = "Guilds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    announcement = Column(String, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("Users.id"))

    def __repr__(self):
        return "<Guild (%s - %s)>" % self.id, self.name


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey("Guilds.id"), index=True)
    guild_week = Column(Integer)
    boss = Column(Integer)
    user_id = Column(Integer, ForeignKey("Users.id"), index=True)
    status = Column(Integer, server_default=text('10'))
    damage = Column(Integer)
    comment = Column(String, nullable=True)
    last_modified = Column(DateTime, server_default=func.now(), server_onupdate=func.now())

    def __repr__(self):
        return "<Record (%s - %s)>" % self.id, self.user_id
