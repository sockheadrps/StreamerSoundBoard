from fastapi.testclient import TestClient
from main.server import app, generate_id, on_client_connection, on_client_close, on_client_sound_files
from mongoengine import connect, disconnect, get_connection, DoesNotExist
from main.Models import Client
import pytest

client = TestClient(app)
connect('mongoenginetest', host='mongomock://localhost', alias='testdb')
conn = get_connection('testdb')

def test_get_clients():
    response = client.get("/get_clients")
    assert response.status_code == 200


def test_generate_id():
    assert generate_id() != generate_id()


def test_on_client_connection():
    assert on_client_connection('a_client') is None


def test_on_client_close():
    # for client in Client.Objects- if you have doubts
    assert on_client_close('a_client') is None
    assert on_client_close('another_client') == DoesNotExist


def test_on_client_sound_files():
    on_client_connection(id="a_client_id")
    assert on_client_sound_files("a_client_id", ['a', 'b', 'c']) is None
    assert on_client_sound_files('asdxcvs', []) == DoesNotExist


