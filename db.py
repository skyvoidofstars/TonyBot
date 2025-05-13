from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Relationship

engine = create_engine('sqlite:///data.db')
Base = declarative_base()
NewSession = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'USERS'
    
    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    user_display_name = Column(String, nullable=False)
    user_character_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)

class Chest(Base):
    __tablename__ = 'CHEST_LOG'
    
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id = Column(Integer, nullable=False)
    item_id = Column(Integer, ForeignKey('ITEMS.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    observations = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    message_id = Column(Integer, nullable=True)
    channel_id = Column(Integer, nullable=True)
    
    user = Relationship('User', backref='CHEST_LOG', lazy='subquery')
    item = Relationship('Item', backref='CHEST_LOG', lazy='subquery')

class Item(Base):
    __tablename__ = 'ITEMS'

    id = Column(Integer, primary_key=True, nullable=False)
    item = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    user = Relationship('User', backref='ITEMS', lazy='subquery')

class Log(Base):
    __tablename__ = 'LOGS'
    
    id = Column(Integer, primary_key=True, nullable=False)
    guild = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    user = Relationship('User', backref='LOGS', lazy='subquery')

Base.metadata.create_all(engine)
