import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
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
	email = Column(String(250), nullable=False)
	account = Column(String(250), nullable=False)
	picture = Column(String(250))
	password = Column(String(250))


class Post(Base):
	__tablename__ = 'post'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	title = Column(String(250), nullable=False)
	post_content = Column(String(250), nullable=False)
	date_added = Column(DateTime, nullable=False)

	@property
	def serialize(self):
		return {
			'id': self.id,
			'user_id': self.user_id,
			'title': self.title,
			'post_content': self.post_content,
			'date_added': self.date_added
		}

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

engine = create_engine('sqlite:///mindwelder.db')

Base.metadata.create_all(engine)
