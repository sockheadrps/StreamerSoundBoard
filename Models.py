from mongoengine import Document, StringField, ListField
from pydantic import BaseModel


class Client(Document):
    client_id = StringField()
    client_pin = StringField()
    client_sounds = ListField()


class Users(Document):
    email = StringField()
    password = StringField()


class NewUser(BaseModel):
    email: str
    password: str
