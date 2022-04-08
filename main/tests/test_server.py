from fastapi.testclient import TestClient
from main.server import (app, generate_id, on_client_connection, on_client_close,
                         get_client_sound_files)
from httpx import AsyncClient
import pytest


client = TestClient(app, backend_options={"use_uvloop": True})


@pytest.fixture()
def create_test_user():
    test_user = {
        "email": "a_client",
        "password": "a password"
    }
    return test_user


@pytest.fixture()
def create_incorrect_user():
    incorrect_user = {
        "email": "a_wrong_client",
        "password": "a password"
    }
    return incorrect_user


def test_get_clients():
    response = client.get("/get_clients")
    assert response.status_code == 200


def test_generate_id():
    assert generate_id() != generate_id()


def test_legitimate_client_connection():
    response = on_client_connection('a_client')
    assert response.status_code == 200


def test_illegitimate_client_connection():
    response = on_client_connection('a_client')
    assert response.status_code == 400


def test_legitimate_client_close():
    response = on_client_close('a_client')
    assert response.status_code == 200


def test_illegitimate_client_close():
    response = on_client_close('a_client')
    assert response.status_code == 400


def test_get_client_sound_files():
    on_client_connection('a_client')
    response = get_client_sound_files("a_client", ['a', 'b', 'c'])
    assert response.status_code == 200
    on_client_close('a_client')


def test_illegitimate_client_sound_files():
    response = get_client_sound_files('an_illegitimate_client', [])
    assert response.status_code == 400


@pytest.mark.anyio
async def test_html_client():
    on_client_connection('a_client')
    get_client_sound_files("a_client", ['a', 'b', 'c'])
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/soundboard/a_client")
    assert response.status_code == 200
    on_client_close('a_client')


def test_can_create_user(create_test_user):
    response = client.post("/sign_up", json=create_test_user)
    assert response.status_code == 201


def test_duplicate_user(create_test_user):
    response = client.post("/sign_up", json=create_test_user)
    assert response.status_code == 400


def test_login_correct_credentials(create_test_user):
    response = client.post("/login", json=create_test_user)
    assert response.status_code == 200


def test_login_incorrect_credentials(create_incorrect_user):
    response = client.post("/login", json=create_incorrect_user)
    assert response.status_code == 400


def test_remove_existing_user(create_test_user):
    good_response = client.post("/remove_user", json=create_test_user)
    assert good_response.status_code == 200


def test_remove_non_existing_user(create_incorrect_user):
    bad_response = client.post("/remove_user", json=create_incorrect_user)
    assert bad_response.status_code == 400


def test_websocket():
    ws_client = TestClient(app)
    with ws_client.websocket_connect('/') as websocket:
        # Initial WS connection
        data = websocket.receive_json()
        assert data == {"REQUEST": "accepted"}
        # Initial connection logic (generating client ID)
        websocket.send_json({'CONNECT': {"client_id": True}}, mode="text")
        data = websocket.receive_json(mode="text")
        assert isinstance(data['CLIENT_ID'], str)
        client_id = data['CLIENT_ID']
        # Close event
        websocket.send_json({'CLOSE': True}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data['STATUS'] == 200
        # Sound file data exchange (When client application sends the names of the sound files)
        websocket.send_json({"SOUND_FILES": ['some', 'sound', 'files']}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data["STATUS"] == 200
        # Test when browser client requests application client to play a sound
        websocket.send_json({"client_id": client_id, 'sound': "test_sound.mp3"}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data['SOUND'] == "test_sound.mp3"
        # Test when browser client requests application client stop all sounds
        websocket.send_json({"client_id": client_id, 'sound': "stop"}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data['SOUND'] == "stop"
