from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Relationship

engine: Engine = create_engine('sqlite:///data.db')
Base = declarative_base()

_new_session: sessionmaker = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'USERS'
    
    user_id: Column = Column(Integer, primary_key=True, nullable=False)
    username: Column = Column(String, nullable=False)
    user_display_name: Column = Column(String, nullable=False)
    user_character_name: Column = Column(String, nullable=True)
    created_at: Column = Column(DateTime, nullable=False)

class Chest(Base):
    __tablename__ = 'CHEST_LOG'
    
    chest_id: Column = Column(Integer, primary_key=True, nullable=False)
    user_id: Column = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id: Column = Column(Integer, nullable=False)
    item_id: Column = Column(Integer, ForeignKey('ITEMS.item_id'), nullable=False)
    quantity: Column = Column(Integer, nullable=False)
    observations: Column = Column(String, nullable=True)
    created_at: Column = Column(DateTime, nullable=False)
    message_id: Column = Column(Integer, nullable=True)
    channel_id: Column = Column(Integer, nullable=True)
    
    user: Relationship = Relationship('User', backref='CHEST_LOG', lazy='subquery')
    item: Relationship = Relationship('Item', backref='CHEST_LOG', lazy='subquery')

class Item(Base):
    __tablename__ = 'ITEMS'

    item_id: Column = Column(Integer, primary_key=True, nullable=False)
    item_name: Column = Column(String, nullable=False)
    group_name: Column = Column(String, nullable=False)
    description: Column = Column(String, nullable=True)
    created_by: Column = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    created_at: Column = Column(DateTime, nullable=False)
    
    user: Relationship = Relationship('User', backref='ITEMS', lazy='subquery')

class Seizure(Base):
    __tablename__ = 'SEIZURE'

    seizure_id: Column = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id: Column = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id: Column = Column(Integer, nullable=False)
    officer_name: Column = Column(String(60), nullable=False)
    officer_badge: Column = Column(String(10), nullable=False)
    image_url: Column = Column(String(2048), nullable=True)
    created_at: Column = Column(DateTime, nullable=False)
    observations: Column = Column(String(1000), nullable=True)
    status: Column = Column(String(50), nullable=False, default='PENDENTE') # PENDENTE, CRIADO, REEMBOLSADO, CANCELADO    
    refunded_at: Column = Column(DateTime, nullable=True)
    refunded_by: Column = Column(Integer, ForeignKey('USERS.user_id'), nullable=True)

    user: Relationship = Relationship('User', foreign_keys=[user_id], backref='SEIZURE', lazy='subquery')

class Log(Base):
    __tablename__ = 'LOGS'
    
    id: Column = Column(Integer, primary_key=True, nullable=False)
    guild: Column = Column(String, nullable=False)
    user_id: Column = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    description: Column = Column(String, nullable=False)
    timestamp: Column = Column(DateTime, nullable=False)
    
    user: Relationship = Relationship('User', backref='LOGS', lazy='subquery')

Base.metadata.create_all(engine)
