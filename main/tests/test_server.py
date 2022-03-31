from fastapi.testclient import TestClient
from main.server import (app, generate_id, on_client_connection, on_client_close,
                         get_client_sound_files)
from httpx import AsyncClient
import pytest


client = TestClient(app, backend_options={"use_uvloop": True})


def test_get_clients() -> None:
    response = client.get("/get_clients")
    assert response.status_code == 200


def test_generate_id() -> None:
    assert generate_id() != generate_id()


def test_legitimate_client_connection() -> None:
    response = on_client_connection('a_client')
    assert response.status_code == 200


def test_illegitimate_client_connection() -> None:
    response = on_client_connection('a_client')
    assert response.status_code == 400


def test_legitimate_client_close() -> None:
    response = on_client_close('a_client')
    assert response.status_code == 200


def test_illegitimate_client_close() -> None:
    response = on_client_close('a_client')
    assert response.status_code == 400


def test_get_client_sound_files() -> None:
    on_client_connection('a_client')
    response = get_client_sound_files("a_client", ['a', 'b', 'c'])
    assert response.status_code == 200
    on_client_close('a_client')


def test_illegitimate_client_sound_files() -> None:
    response = get_client_sound_files('an_illegitimate_client', [])
    assert response.status_code == 400


@pytest.mark.anyio
async def test_html_client() -> None:
    on_client_connection('a_client')
    get_client_sound_files("a_client", ['a', 'b', 'c'])
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/soundboard/a_client")
    assert response.status_code == 200
    on_client_close('a_client')


def test_can_create_user() -> None:
    test_user = {
        "email": "a_client",
        "password": "a password"
    }
    response = client.post("/sign_up", json=test_user)
    assert response.status_code == 201


def test_duplicate_user() -> None:
    test_user = {
        "email": "a_client",
        "password": "a password"
    }
    response = client.post("/sign_up", json=test_user)
    assert response.status_code == 400


def test_login_correct_credentials() -> None:
    existing_user = {
        "email": "a_client",
        "password": "a password"
    }
    response = client.post("/login", json=existing_user)
    assert response.status_code == 200


def test_login_incorrect_credentials() -> None:
    in_correct_credentials = {
        "email": "a_wrong_client",
        "password": "a password"
    }
    response = client.post("/login", json=in_correct_credentials)
    assert response.status_code == 400


def test_remove_existing_user() -> None:
    existing_user = {
        "email": "a_client",
        "password": "a password"
    }
    good_response = client.post("/remove_user", json=existing_user)
    assert good_response.status_code == 200


def test_remove_non_existing_user() -> None:
    incorrect_credentials = {
        "email": "a_wrong_client",
        "password": "a password"
    }
    bad_response = client.post("/remove_user", json=incorrect_credentials)
    assert bad_response.status_code == 400


def test_websocket() -> None:
    ws_client = TestClient(app)
    with ws_client.websocket_connect('/') as websocket:
        data = websocket.receive_json()
        assert data == {"REQUEST": "accepted"}
        websocket.send_json({'CONNECT': {"client_id": True}}, mode="text")
        data = websocket.receive_json(mode="text")
        assert isinstance(data['CLIENT_ID'], str)
        websocket.send_json({'CLOSE': True}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data['STATUS'] == 200
        websocket.send_json({"SOUND_FILES": ['some', 'sound', 'files']}, mode="text")
        data = websocket.receive_json(mode="text")
        assert data["STATUS"] == 200
