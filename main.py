from routes import oauth, user, bot, form, sio_router
from fastapi import FastAPI
import socketio
import models
from database import engine

# CORS
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

origins = ["http://localhost", "http://localhost:3000", "https://test.randosoru.me"]
#

app = FastAPI(
    root_path="/api",
    title="Randosoru",
    description="API documents for guild.randosoru.me",
    version="0.5.6",
    docs_url=None,
    redoc_url="/doc",
)

sio_app = socketio.ASGIApp(sio_router.sio)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#

app.include_router(oauth.router)
app.include_router(user.router)
app.include_router(form.router)
app.include_router(bot.router)

app.add_route("/socket.io/", route=sio_app, methods=["GET", "POST"])
app.add_websocket_route("/socket.io/", sio_app)


@app.get("/")
def index():
    return {"version": app.version}