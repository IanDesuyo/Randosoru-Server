from sqlalchemy import ForeignKey, Boolean, Column, ForeignKey, Integer, String, DateTime, text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from datetime import timezone, datetime
from database import Base
from routes import oauth
import uuid


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, unique=True,
                autoincrement=True, index=True)
    avatar = Column(String(120), nullable=True)
    name = Column(String(40))
    uid = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    privacy = Column(Integer, server_default=text('0'))
    status = Column(Integer, server_default=text('0'))
    guild_name = Column(String(40), nullable=True)

    def __repr__(self):
        return "<User (%s)>" % self.platform, self.id

    def as_dict(self):
        self.created_at = int(self.created_at.timestamp())+28800
        return self.__dict__


class OauthDetail(Base):
    __tablename__ = "OauthDetails"

    platform = Column(Integer)
    id = Column(String(40), primary_key=True, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    user = relationship("User")

    def __repr__(self):
        return "<OauthDetail (%s-%s)>" % self.platform, self.id

class Form(Base):
    __tablename__ = "Forms"

    id = Column(String(32), primary_key=True, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("Users.id"))
    month = Column(Integer)
    title = Column(String(20), server_default="unknow")
    description = Column(String(40), nullable=True)
    status = Column(Integer, server_default=text('0'))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return "<Form (%s - %s)>" % self.id, self.owner_id

    def as_dict(self):
        self.created_at = int(self.created_at.timestamp())+28800
        # self.owner_id = oauth.get_hashed_id(self.owner_id)
        return self.__dict__


class Record(Base):
    __tablename__ = "Records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    form_id = Column(String(32), ForeignKey("Forms.id"), index=True)
    month = Column(Integer)
    week = Column(Integer)
    boss = Column(Integer)
    user_id = Column(Integer, ForeignKey("Users.id"), index=True)
    user = relationship("User")
    status = Column(Integer, server_default=text('10'))
    damage = Column(Integer)
    comment = Column(String(40), nullable=True)
    team = Column(JSON, nullable=True)
    last_modified = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now())

    def __repr__(self):
        return "<Record (%s - %s)>" % self.id, self.user_id

    def as_dict(self):
        self.last_modified = int(self.last_modified.timestamp())+28800
        self.user = self.user
        self.user.id = oauth.get_hashed_id(self.user_id)
        return self.__dict__