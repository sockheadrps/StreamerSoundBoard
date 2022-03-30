from main.Models import Client, Users, NewUser
from mongoengine.base.datastructures import BaseList


def test_client():
	client = Client(client_id='a_client', client_sounds=['one', 'two'])
	assert client.client_id == 'a_client'
	assert client.client_sounds == ['one', 'two']
	assert type(client.client_id) == str
	assert type(client.client_sounds) == BaseList


def test_user():
	user = Users(email='an_email', password='a_password')
	assert user.email == 'an_email'
	assert user.password == 'a_password'
	assert type(user.email) == str
	assert type(user.password) == str


def test_new_user():
	new_user = NewUser(email="another_email", password="another_password")
	assert new_user.email == 'another_email'
	assert new_user.password == 'another_password'
	assert type(new_user.email) == str
	assert type(new_user.password) == str
