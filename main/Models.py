from mongoengine import Document, StringField, ListField
from pydantic import BaseModel


class ClientORM(Document):
    client_id = StringField()
    client_sounds = ListField()


class UsersORM(Document):
    email = StringField()
    password = StringField()


class NewUser(BaseModel):
    email: str
    password: str
