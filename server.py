from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    Response,
    status,
    WebSocketDisconnect,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import random
import asyncio
import uvicorn
from mongoengine import connect
from Models import Client, Users, NewUser
from typing import List, NoReturn, Dict, Optional
from fastapi.responses import JSONResponse
from passlib.hash import pbkdf2_sha256
import logging
from ConnectionManager import ConnectionManager


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Web socket Connection Manager, lock and necessary tracking variables
manager = ConnectionManager()
client_sock_lock = asyncio.Lock()
clients = {}
sock_client_dict = {}


# Mongo connection
db = connect(db="StreamHelper", host="localhost", port=27017)
# If running for the first time, this dummy object will create the DB
debug_hash_password = pbkdf2_sha256.hash("dummydoc")
Users(email="dummydoc", password=debug_hash_password).save()


# Debug variable for development
debugger = False


def generate_id(
    digits="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_+",
    max_length=10,
) -> str:
    return "".join(random.choice(digits) for _ in range(max_length))


def on_client_connection(client_id: str):
    new_client = Client()
    new_client.client_id = client_id
    new_client.client_sounds = []
    new_client.save()


def on_client_close(client_id: str):
    _client = Client.objects.get(client_id=client_id)
    _client.delete()


def on_client_sound_files(client_id: str, sound_files: List) -> NoReturn:
    """
    Upon client application websocket connection, generate which sound files are present in their sound_file directory
    :param client_id:
    :param sound_files:
    """
    _client = Client.objects.get(client_id=client_id)
    _client.update(client_sounds=sound_files)


if debugger:
    logging.warning("DEBUG MODE")

    @app.get("/get_clients")
    async def get_clients() -> Dict:
        client_list = []
        for active_client in Client.objects:
            client_list.append(active_client.client_id)
        return {"Clients": client_list}


@app.get("/favicon.ico")
async def favicon() -> NoReturn:
    raise HTTPException(status_code=403, detail="No favicon")


@app.get("/soundboard/{client_id}", response_class=HTMLResponse)
async def client(request: Request, client_id: str) -> templates.TemplateResponse:
    _client = Client.objects.get(client_id=client_id)
    sound_files = []
    for item in _client.client_sounds:
        sound_files.append(item)
    return templates.TemplateResponse(
        "index.html", {"request": request, "id": client_id, "sound_files": sound_files}
    )


@app.post("/sign_up")
async def sign_up(new_user: NewUser, response: Response) -> JSONResponse:
    for user in Users.objects:
        if new_user.email == user.email:
            response.status_code = status.HTTP_409_CONFLICT
            return JSONResponse(content={"status": response.status_code})
    hash_password = pbkdf2_sha256.hash(new_user.password)
    Users(email=new_user.email, password=hash_password).save()
    response.status_code = status.HTTP_201_CREATED
    return JSONResponse(content={"status": response.status_code})


@app.post("/login")
async def sign_up(new_user: NewUser, response: Response) -> JSONResponse:
    for user in Users.objects:
        if user.email == new_user.email:
            non_hashed_password = pbkdf2_sha256.verify(new_user.password, user.password)
            if non_hashed_password:
                response.status_code = status.HTTP_200_OK
                break
            else:
                response.status_code = status.HTTP_409_CONFLICT
                break
        else:
            response.status_code = status.HTTP_409_CONFLICT
    return JSONResponse(content={"status": response.status_code})


@app.websocket("/")
async def client_sock(sock: WebSocket) -> Optional[any]:
    await manager.connect(sock)
    client_id = generate_id()
    sock_client_dict[sock] = client_id
    async with client_sock_lock:
        clients[client_id] = sock
    try:
        while True:
            try:
                data = await sock.receive_json()
                if debugger:
                    logging.warning(data)

                # WEB BROWSER SOUNDBOARD COMMUNICATION
                if "client_id" in data.keys():
                    browser_id = data["client_id"]
                    if "sound" in data.keys():
                        sound = data["sound"]
                        if browser_id in clients:
                            electron_sock = clients[browser_id]
                            if sound == "STOP":
                                await electron_sock.send_json({"STOP": "STOP"})
                            else:
                                await electron_sock.send_json({"SOUND": sound})

                # ELECTRON CLIENT COMMUNICATION
                client_request = data.keys()
                if "CONNECT" in client_request:
                    on_client_connection(client_id)
                    await sock.send_json({"client_id": client_id})
                if "CLOSE" in client_request:
                    on_client_close(client_id)
                    await manager.disconnect_user(sock)
                if "SOUNDFILES" in client_request:
                    sound_files = data["SOUNDFILES"]
                    on_client_sound_files(client_id, sound_files)
                    await sock.send_json({"SOUNDFILES": "200"})

            except WebSocketDisconnect:
                pop_id = sock_client_dict[sock]
                Client.objects(client_id=pop_id).delete()
                await manager.disconnect_user(sock)
                break
    finally:
        async with client_sock_lock:
            clients.pop(client_id)


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
