import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ):
    await sio.emit("message", "Hello", sid)


@sio.event
async def track(sid, data: dict):
    form_id = data.get("form_id")
    if form_id:
        sio.enter_room(sid, form_id)
        await sio.emit("FormTracker", {"type": "Join", "message": f"{sid} joined"}, room=form_id)
