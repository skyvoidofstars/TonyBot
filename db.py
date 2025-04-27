from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Relationship

engine = create_engine('sqlite:///data.db')
Base = declarative_base()
NewSession = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'USERS'
    
    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    user_global_name = Column(String, nullable=False)
    user_display_name = Column(String, nullable=False)
    user_character_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)

class Chest(Base):
    __tablename__ = 'CHEST_LOG'
    
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id = Column(Integer, nullable=False)
    item = Column(String, ForeignKey('ITEMS.item') ,nullable=False)
    quantity = Column(Integer, nullable=False)
    observations = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    message_id = Column(Integer, nullable=True)
    channel_id = Column(Integer, nullable=True)
    guild_id = Column(Integer, nullable=True)
    
    getUser = Relationship('User', backref='CHEST_LOG', lazy='subquery')
    getItem = Relationship('Item', backref='CHEST_LOG', lazy='subquery')

class Item(Base):
    __tablename__ = 'ITEMS'

    id = Column(Integer, primary_key=True, nullable=False)
    item = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    getUser = Relationship('User', backref='ITEMS', lazy='subquery')

Base.metadata.create_all(engine)
