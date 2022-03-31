from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    status,
    WebSocketDisconnect,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import random
import asyncio
import uvicorn
from mongoengine import connect, DoesNotExist
from main.Models import ClientORM, UsersORM, NewUser
from typing import List, NoReturn, Dict
from fastapi.responses import JSONResponse
from passlib.hash import pbkdf2_sha256
from main.ConnectionManager import ConnectionManager
import pytest


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Web socket Connection Manager, lock and necessary tracking variables
manager = ConnectionManager()
client_sock_lock = asyncio.Lock()
clients = {}
sock_client_dict = {}


# Mongo connection
db = connect(db="StreamHelper", host="localhost", port=27017, uuidRepresentation='standard')
# If running for the first time, this dummy object will create the DB
debug_hash_password = pbkdf2_sha256.hash("dummydoc")
UsersORM(email="dummydoc", password=debug_hash_password).save()
__global_ids = []


def generate_id() -> str:
    global __global_ids
    while True:
        max_length = 10
        digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_+"
        generated_id = "".join(random.choice(digits) for _ in range(max_length))
        if generated_id in __global_ids:
            pass
        else:
            __global_ids.append(generated_id)
            return generated_id


def on_client_connection(new_client_id: str) -> JSONResponse:
    try:
        ClientORM.objects.get(client_id=new_client_id)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    except DoesNotExist:
        ClientORM(client_id=new_client_id, client_sounds=[]).save()
        return JSONResponse(status_code=status.HTTP_200_OK)


def on_client_close(close_id: str) -> JSONResponse:
    try:
        ClientORM.objects.get(client_id=close_id).delete()
    except DoesNotExist:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status.HTTP_200_OK)


def get_client_sound_files(client_id: str, sound_files: List) -> JSONResponse:
    """
    Upon client application websocket connection, generate which sound files are present in their sound_file directory
    :param client_id:
    :param sound_files:
    """
    try:
        ClientORM.objects.get(client_id=client_id)
    except DoesNotExist:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    _client = ClientORM.objects.get(client_id=client_id)
    _client.update(client_sounds=sound_files)
    return JSONResponse(status_code=status.HTTP_200_OK)


@app.get("/get_clients")
async def get_clients() -> Dict:
    client_list = []
    for active_client in ClientORM.objects:
        client_list.append(active_client.client_id)
    return {"Clients": client_list}


@app.get("/favicon.ico")
async def favicon() -> NoReturn:
    raise HTTPException(status_code=403, detail="No favicon")


@app.get("/soundboard/{client_id}", response_class=HTMLResponse)
async def html_client(request: Request, client_id: str) -> templates.TemplateResponse:
    _client = ClientORM.objects.get(client_id=client_id)
    sound_files = []
    for item in _client.client_sounds:
        sound_files.append(item)
    return templates.TemplateResponse(
        "index.html", {"request": request, "id": client_id, "sound_files": sound_files}
    )


@app.post("/sign_up")
async def sign_up(new_user: NewUser) -> JSONResponse:
    if UsersORM.objects(email=new_user.email):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    hash_password = pbkdf2_sha256.hash(new_user.password)
    UsersORM(email=new_user.email, password=hash_password).save()
    return JSONResponse(status_code=status.HTTP_201_CREATED)


@app.post("/login")
async def sign_up(user_to_login: NewUser) -> JSONResponse:
    existing_user = UsersORM.objects(email=user_to_login.email).first()
    if existing_user:
        non_hashed_password = pbkdf2_sha256.verify(user_to_login.password, existing_user.password)
        if non_hashed_password:
            return JSONResponse(status_code=status.HTTP_200_OK)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)


@app.post("/remove_user")
async def remove_user(requested_to_delete: NewUser) -> JSONResponse:
    found_user = UsersORM.objects(email=requested_to_delete.email)
    if found_user:
        found_user.delete()
        return JSONResponse(status_code=status.HTTP_200_OK)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)


@app.websocket("/")
async def client_sock(sock: WebSocket):
    await manager.connect(sock)
    client_id = generate_id()
    sock_client_dict[sock] = client_id
    async with client_sock_lock:
        clients[client_id] = sock
    await sock.send_json({"REQUEST": "accepted"})
    try:
        while True:
            try:
                data = await sock.receive_json()

                # WEB BROWSER SOUNDBOARD COMMUNICATION
                client_request = data.keys()
                if "client_id" in client_request:
                    browser_id = data["client_id"]
                    if "sound" in client_request:
                        sound = data["sound"]
                        if browser_id in clients:
                            electron_sock = clients[browser_id]
                            if sound == "STOP":
                                await electron_sock.send_json({"STOP": "STOP"})
                            else:
                                await electron_sock.send_json({"SOUND": sound})

                # ELECTRON CLIENT COMMUNICATION
                if "CONNECT" in client_request:
                    on_client_connection(client_id)
                    await sock.send_json({"CLIENT_ID": client_id})
                if "CLOSE" in client_request:
                    on_client_close(client_id)
                    await sock.send_json({"STATUS": 200, "ACTION": "web socket closed"})
                    await manager.disconnect_user(sock)
                if "SOUND_FILES" in client_request:
                    sound_files = data["SOUND_FILES"]
                    get_client_sound_files(client_id, sound_files)
                    await sock.send_json({"STATUS": 200, "ACTION": "sound files received"})

            except WebSocketDisconnect:
                ClientORM.objects(client_id=sock_client_dict[sock]).delete()
                await manager.disconnect_user(sock)
                break
    finally:
        async with client_sock_lock:
            clients.pop(client_id)


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
