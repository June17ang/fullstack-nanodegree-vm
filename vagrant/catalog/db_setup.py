import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    profile_image = Column(String(250), nullable=True)
    status = Column(String(1), default='A')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    update_at = Column(DateTime, default=datetime.datetime.utcnow)
    deleted_at = Column(DateTime, default=datetime.datetime.utcnow)


class ItemCategory(Base):
    __tablename__ = 'item_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    status = Column(String(1), default='A')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    update_at = Column(DateTime, default=datetime.datetime.utcnow)
    deleted_at = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status
        }


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    item_category_id = Column(Integer, ForeignKey('item_categories.id'))
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(String(1), default='A')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    update_at = Column(DateTime, default=datetime.datetime.utcnow)
    deleted_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship(User)
    item_categories = relationship(ItemCategory)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status
        }


engine = create_engine('sqlite:///item_catalog.db')


Base.metadata.create_all(engine)