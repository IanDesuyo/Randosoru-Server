from fastapi import APIRouter, Response, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
import aiohttp
import jwt
from jwt import PyJWTError, ExpiredSignatureError
import config
from schemas import User
import models
from database import SessionLocal, engine

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

models.Base.metadata.create_all(bind=engine)


@router.get("/login/discord", tags=["Login"])
async def discord_login():
    return RedirectResponse("https://discordapp.com/api/oauth2/authorize?client_id=594885334232334366&redirect_uri=http://127.0.0.1:8000/oauth/discord&response_type=code&scope=identify&prompt=none")


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
    
    #check if user exist
    db = SessionLocal()
    user_profile = db.query(models.User).filter(
        models.User.id == "1-"+resp["id"]).first()

    # not exist, create one
    if not user_profile:
        user_profile = models.User(
            id="1-"+resp["id"], name=resp["username"], avatar=resp["avatar"])
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
    # update user's avatar & name
    elif user_profile.avatar != resp["avatar"] or user_profile.name != resp["name"]:
        user_profile.avatar = resp["avatar"]
        user_profile.name = resp["name"]
        db.commit()
        db.refresh(user_profile)
    # create jwt token, expire after 7 days
    expire = datetime.utcnow() + timedelta(days=7)
    user = jwt.encode({"id": "1-" + resp["id"], "exp": expire},
                      config.JWT_SECRET, algorithm='HS256').decode('utf-8')
    response.set_cookie('token', user, expires=30)
    return user


async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms='HS256')
    except ExpiredSignatureError:
        raise HTTPException(401, "Credentials expired", {
                            "WWW-Authenticate": "Bearer"})
    except PyJWTError:
        raise HTTPException(401, "Could not validate credentials", {
                            "WWW-Authenticate": "Bearer"})
    return payload["id"]
