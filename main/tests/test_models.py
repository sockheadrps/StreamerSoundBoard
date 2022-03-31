from main.Models import ClientORM, UsersORM, NewUser
from mongoengine.base.datastructures import BaseList


def test_client():
	client = ClientORM(client_id='a_client', client_sounds=['one', 'two'])
	assert client.client_id == 'a_client'
	assert client.client_sounds == ['one', 'two']
	assert isinstance(client.client_id, str)
	assert isinstance(client.client_sounds, BaseList)


def test_user():
	user = UsersORM(email='an_email', password='a_password')
	assert user.email == 'an_email'
	assert user.password == 'a_password'
	assert isinstance(user.email, str)
	assert isinstance(user.password, str)


def test_new_user():
	new_user = NewUser(email="another_email", password="another_password")
	assert new_user.email == 'another_email'
	assert new_user.password == 'another_password'
	assert isinstance(new_user.email, str)
	assert isinstance(new_user.password, str)
