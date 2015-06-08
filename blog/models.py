"""
    models.py
    ~~~~~~~~~
    models
"""
import bcrypt
# import datetime
import tornado.gen
from avatar import avatar
# from functools import partial
from libs.document import Custom_Document
from mongoengine import connect, CASCADE
from mongoengine.fields import (StringField, DateTimeField, EmbeddedDocument,
                                IntField, EmailField, EmbeddedDocumentField,
                                ReferenceField, ListField)

# connect
connect('blogtest')


class Skill(EmbeddedDocument):
    name = StringField(required=True, max_length=20)
    value = IntField(required=True, default=0)

    def __repr__(self):
        return '<Skill %r>' % (self.name)


class User(Custom_Document):
    nickname = StringField(required=True, unique=True, max_length=20)
    email = EmailField(required=True, unique=True, max_length=50)
    password_hash = StringField(max_length=200, required=True)
    about_me = StringField(max_length=200)
    skills = ListField(EmbeddedDocumentField(Skill))
    last_seen = DateTimeField(required=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable')

    @password.setter
    @tornado.gen.coroutine
    def password(self, password):
        self.password_hash = yield self._executor.submit(
            bcrypt.hashpw, password, bcrypt.gensalt())

    @tornado.gen.coroutine
    def verify_password(self, password):
        password_hash = yield self._executor.submit(
            bcrypt.hashpw, password, self.password_hash)
        return password_hash == self.password_hash

    def avatar(self, size):
        return avatar(self.email, size)

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Comment(EmbeddedDocument):
    content = StringField(required=True)
    author_name = StringField(required=True, max_length=20)
    author_email = EmailField(required=True, max_length=50)
    author_url = StringField(max_length=100)
    create_time = DateTimeField(required=True)

    def avatar(self, size):
        return avatar(self.author_email, size)

    def __repr__(self):
        return '<Comment %r>' % (self.create_time)


class Category(Custom_Document):
    name = StringField(required=True)

    def __repr__(self):
        return '<Category %r>' % (self.name)


class Post(Custom_Document):
    title = StringField(required=True, unique=True, max_length=120)
    content = StringField(required=True)
    markdown = StringField()
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    category = ReferenceField(Category, reverse_delete_rule=CASCADE)
    comments = ListField(EmbeddedDocumentField(Comment))
    tags = ListField(StringField(max_length=50))
    create_time = DateTimeField(required=True)
    modified_time = DateTimeField()

    def __repr__(self):
        return '<Post %r>' % (self.title)
