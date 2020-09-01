from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import aiohttp
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from hashids import Hashids
import config
import schemas
import models
from database import SessionLocal, engine

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

models.Base.metadata.create_all(bind=engine)

hashids = Hashids(salt=config.ID_SECRET, min_length=6)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms="HS256")
    except ExpiredSignatureError:
        raise HTTPException(401, "Credentials expired", {"WWW-Authenticate": "Bearer"})
    except PyJWTError:
        raise HTTPException(401, "Could not validate credentials", {"WWW-Authenticate": "Bearer"})
    return hashids.decode(payload["id"])[0]


def get_user_id(hashed_id: str):
    user_id = hashids.decode(hashed_id)
    if not user_id:
        raise HTTPException(404, "User not found")
    return user_id[0]


def get_hashed_id(user_id: int):
    return hashids.encode(user_id)


# Router


@router.post("/oauth/discord", response_model=schemas.OauthReturn, tags=["Oauth"])
async def discord_oauth(code: str, db: Session = Depends(get_db)):
    """
    For Discord Oauth
    """
    data = {
        "client_id": config.Discord.CLIENT_ID,
        "client_secret": config.Discord.CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.Discord.REDIRECT_URL,
        "scope": "identify email connections",
    }
    async with aiohttp.ClientSession() as session:
        r1 = await session.post(
            config.Discord.API_ENDPOINT + "/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = await r1.json()
        if resp.get("access_token") != None:
            r2 = await session.get(
                "https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + resp["access_token"]}
            )
            resp = await r2.json()
        else:
            raise HTTPException(400, "Discord Oauth handle failed")

    # check if user exist
    OauthDetail = (
        db.query(models.OauthDetail)
        .filter(models.OauthDetail.platform == 1)
        .filter(models.OauthDetail.id == resp["id"])
        .first()
    )

    # not exist, create one
    if not OauthDetail:
        newUser = models.User(
            avatar=f"https://cdn.discordapp.com/avatars/{resp['id']}/{resp['avatar']}.png", name=resp["username"]
        )
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(platform=1, id=resp["id"], user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()
    else:
        # check if user have been banned
        if OauthDetail.user.status != 0:
            raise HTTPException(403, "You have been banned")
        # update account
        OauthDetail.user.avatar = f"https://cdn.discordapp.com/avatars/{resp['id']}/{resp['avatar']}.png"
        OauthDetail.user.name = resp["username"]
        db.commit()

    # create jwt token, expire after 7 days
    expire = datetime.utcnow() + timedelta(days=7)
    user_id = hashids.encode(OauthDetail.user_id)
    token = jwt.encode({"id": user_id, "exp": expire}, config.JWT_SECRET, algorithm="HS256").decode("utf-8")
    return {"id": user_id, "token": token}


@router.post("/oauth/line", response_model=schemas.OauthReturn, tags=["Oauth"])
async def line_oauth(code: str, db: Session = Depends(get_db)):
    """
    For Line Oauth
    """
    data = {
        "client_id": config.Line.CLIENT_ID,
        "client_secret": config.Line.CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.Line.REDIRECT_URL,
    }
    async with aiohttp.ClientSession() as session:
        r1 = await session.post(
            config.Line.API_ENDPOINT + "/oauth/accessToken",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = await r1.json()
        if resp.get("access_token") != None:
            r2 = await session.get(
                "https://api.line.me/v2/profile", headers={"Authorization": "Bearer " + resp["access_token"]}
            )
            resp = await r2.json()
        else:
            raise HTTPException(400, "Line Oauth handle failed")

    # check if user exist
    OauthDetail = (
        db.query(models.OauthDetail)
        .filter(models.OauthDetail.platform == 2)
        .filter(models.OauthDetail.id == resp["userId"])
        .first()
    )

    # not exist, create one
    if not OauthDetail:
        newUser = models.User(avatar=f"{resp['pictureUrl']}.png", name=resp["displayName"])
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(platform=2, id=resp["userId"], user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()
    else:
        # check if user have been banned
        if OauthDetail.user.status != 0:
            raise HTTPException(403, "You have been banned")
        # update account
        OauthDetail.user.avatar = f"{resp['pictureUrl']}.png"
        OauthDetail.user.name = resp["displayName"]
        db.commit()

    # create jwt token, expire after 7 days
    expire = datetime.utcnow() + timedelta(days=7)
    user_id = hashids.encode(OauthDetail.user_id)
    token = jwt.encode({"id": user_id, "exp": expire}, config.JWT_SECRET, algorithm="HS256").decode("utf-8")
    return {"id": user_id, "token": token}


@router.post("/oauth/line_liff", response_model=schemas.OauthReturn, tags=["Oauth"])
async def line_liff_oauth(access_token: str, db: Session = Depends(get_db)):
    """
    Line Liff Login
    """
    async with aiohttp.ClientSession() as session:
        r1 = await session.get("https://api.line.me/v2/profile", headers={"Authorization": "Bearer " + access_token})
        resp = await r1.json()
        if resp.get("userId") == None:
            raise HTTPException(400, "Line Oauth handle failed")

    # check if user exist
    OauthDetail = (
        db.query(models.OauthDetail)
        .filter(models.OauthDetail.platform == 2)
        .filter(models.OauthDetail.id == resp["userId"])
        .first()
    )

    # not exist, create one
    if not OauthDetail:
        newUser = models.User(avatar=f"{resp['pictureUrl']}.png", name=resp["displayName"])
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(platform=2, id=resp["userId"], user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()
    else:
        # check if user have been banned
        if OauthDetail.user.status != 0:
            raise HTTPException(403, "You have been banned")
        # update account
        OauthDetail.user.avatar = f"{resp['pictureUrl']}.png"
        OauthDetail.user.name = resp["displayName"]
        db.commit()

    # create jwt token, expire after 7 days
    expire = datetime.utcnow() + timedelta(days=7)
    user_id = hashids.encode(OauthDetail.user_id)
    token = jwt.encode({"id": user_id, "exp": expire}, config.JWT_SECRET, algorithm="HS256").decode("utf-8")
    return {"id": user_id, "token": token}
