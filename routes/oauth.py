from fastapi import APIRouter, Response, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
import aiohttp
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from hashids import Hashids
import config
from schemas import User
import models
from database import SessionLocal, engine

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

models.Base.metadata.create_all(bind=engine)

hashids = Hashids(salt=config.ID_SECRET, min_length=6)


@router.get("/login/discord", tags=["Login"])
def discord_login():
    return RedirectResponse(f"https://discordapp.com/api/oauth2/authorize?client_id={config.CLIENT_ID}&redirect_uri={config.REDIRECT_URL}&response_type=code&scope=identify&prompt=none")


@router.get("/oauth/discord", tags=["Oauth"])
async def discord_oauth(code: str, response: Response):
    data = {
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.REDIRECT_URL,
        "scope": "identify email connections"
    }
    async with aiohttp.ClientSession() as session:
        r1 = await session.post(config.API_ENDPOINT + "/oauth2/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = await r1.json()
        if resp.get("access_token") != None:
            r2 = await session.get("https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + resp["access_token"]})
            resp = await r2.json()
        else:
            raise HTTPException(400, "Discord Oauth handle failed")

    # check if user exist
    db = SessionLocal()
    OauthDetail = db.query(models.OauthDetail).filter(
        models.OauthDetail.platform == 1).filter(models.OauthDetail.id == resp["id"]).first()

    # not exist, create one
    if not OauthDetail:
        newUser = models.User(avatar=f"https://cdn.discordapp.com/avatars/{resp['id']}/{resp['avatar']}.png", name=resp["username"])
        db.add(newUser)
        db.flush()
        OauthDetail = models.OauthDetail(
            platform=1, id=resp["id"], user_id=newUser.id)
        db.add(OauthDetail)
        db.commit()

    # create jwt token, expire after 7 days
    expire = datetime.utcnow() + timedelta(days=7)
    user = jwt.encode({"id": hashids.encode(OauthDetail.user_id), "exp": expire},
                      config.JWT_SECRET, algorithm='HS256').decode('utf-8')
    response.set_cookie('token', user, expires=30)
    return user


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms='HS256')
    except ExpiredSignatureError:
        raise HTTPException(401, "Credentials expired", {
                            "WWW-Authenticate": "Bearer"})
    except PyJWTError:
        raise HTTPException(401, "Could not validate credentials", {
                            "WWW-Authenticate": "Bearer"})
    return hashids.decode(payload["id"])[0]


def get_user_id(hashed_id: str):
    user_id = hashids.decode(hashed_id)
    if not user_id:
        raise HTTPException(404, 'User not found')
    return user_id[0]


def get_hashed_id(user_id: int):
    return hashids.encode(user_id)
