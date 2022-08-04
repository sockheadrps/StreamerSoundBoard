from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    status,
    WebSocketDisconnect,
    Depends,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio
import uvicorn
from mongoengine import connect, DoesNotExist
from main.Models import ClientORM, UsersORM, UserModel
from auth import AuthHandler
from typing import List, Dict
from fastapi.responses import JSONResponse
from passlib.hash import pbkdf2_sha256
from main.ConnectionManager import ConnectionManager
import uuid
import pytest


app = FastAPI()
auth_handler = AuthHandler()
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


def generate_id() -> str:
    return str(uuid.uuid4())


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
    Upon client application websocket connection, generate which sound files are present in local sound_file directory
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
async def favicon() -> None:
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
async def sign_up(new_user: UserModel) -> JSONResponse:
    if UsersORM.objects(email=new_user.email):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    hashed_password = auth_handler.get_password_hash(password=new_user.password)
    UsersORM(email=new_user.email, password=hashed_password).save()
    return JSONResponse(status_code=status.HTTP_201_CREATED)


@app.post("/login")
async def login(user_to_login: UserModel) -> JSONResponse:
    existing_user = UsersORM.objects(email=user_to_login.email).first()
    if existing_user and auth_handler.verify_password(user_to_login.password, existing_user.password):
        token = auth_handler.encode_token(user_to_login.email)
        json_compatible_response = {"status_code": status.HTTP_200_OK, 'token': token}
        return JSONResponse(content=json_compatible_response)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)


@app.post("/remove_user")
async def remove_user(requested_to_delete: UserModel) -> JSONResponse:
    found_user = UsersORM.objects(email=requested_to_delete.email)
    if found_user:
        found_user.delete()
        return JSONResponse(status_code=status.HTTP_200_OK)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)


@app.websocket("/")
async def client_sock(sock: WebSocket, username=Depends(auth_handler.auth_wrapper)):
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
                    # If data{'sound'] browser is either requesting to play a sound, or stop currently playing sounds
                    if "sound" in client_request:
                        sound = data["sound"]
                        # Matching the browser ID to the client ID, to send the correct application client the request
                        if browser_id in clients:
                            browser_socket = clients[browser_id]
                            if sound == "STOP":
                                await browser_socket.send_json({"STOP": "stop"})
                            else:
                                # Play the requested sound
                                await browser_socket.send_json({"SOUND": sound})

                # CLIENT APPLICATION COMMUNICATION
                if "CONNECT" in client_request:
                    on_client_connection(client_id)
                    await sock.send_json({"CLIENT_ID": client_id})
                if "CLOSE" in client_request:
                    on_client_close(client_id)
                    await sock.send_json({"STATUS": 200, "ACTION": "web socket closed"})
                    await manager.disconnect_user(sock)
                # Application sending the server what sound files are present in local sound_files directory
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
