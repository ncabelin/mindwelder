import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	# password and picture are optional. depending on
	# if account = self
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	username = Column(String(250), nullable=False)
	description = Column(String(100))
	email = Column(String(250), nullable=False)
	account = Column(String(250), nullable=False)
	picture = Column(String(250))
	password = Column(String(250))
	confirmed = Column(Boolean(), default=False, nullable=False)
	registered_on = Column(DateTime, nullable=False)
	posts = relationship('Post', cascade="delete")
	tests = relationship('Test', cascade="delete")

class Post(Base):
	__tablename__ = 'post'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	title = Column(String(250), nullable=False)
	description = Column(String(250))
	picture = Column(String(250))
	post_content = Column(Text(), nullable=False)
	date_added = Column(DateTime, nullable=False)
	comments = relationship('Comment', cascade="delete")
	keywords = relationship('Keyword', cascade="delete")
	likes = relationship('Like', cascade="delete")
	tests = relationship('Test', cascade="delete")

	@property
	def serialize(self):
		return {
			'id': self.id,
			'user_id': self.user_id,
			'title': self.title,
			'description': self.description,
			'picture': self.picture,
			'post_content': self.post_content,
			'date_added': self.date_added
		}

class Keyword(Base):
	__tablename__ = 'keyword'
	id = Column(Integer, primary_key=True)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)
	word = Column(String(100), nullable=False)


class Like(Base):
	__tablename__ = 'like'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)

	@property
	def serialize(self):
		return {
			'like_id': self.id,
			'user_id': self.user_id,
			'post_id': self.post_id
		}


class Comment(Base):
	__tablename__ = 'comment'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)
	content = Column(String(250), nullable=False)
	date_added = Column(DateTime, nullable=False)

	@property
	def serialize(self):
		return {
			'comment_id': self.id,
			'user_id': self.user_id,
			'post_id': self.post_id,
			'content': self.content,
			'date_added': self.date_added
		}

class Test(Base):
	__tablename__ = 'test'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)
	answer = Column(String(500), nullable=False)

	@property
	def serialize(self):
		return {
			'id': self.id,
			'user_id': self.user_id,
			'post_id': self.post_id,
			'answer': self.answer
		}

engine = create_engine('postgresql://meeska:Marcopupu2014@localhost:5432/mindwelder')

Base.metadata.create_all(engine)
