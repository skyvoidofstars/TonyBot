from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Relationship

engine: Engine = create_engine('sqlite:///data.db')
Base = declarative_base()

_new_session: sessionmaker = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'USERS'
    
    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    user_display_name = Column(String, nullable=False)
    user_character_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)

class Chest(Base):
    __tablename__ = 'CHEST_LOG'
    
    chest_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id = Column(Integer, nullable=False)
    item_id = Column(Integer, ForeignKey('ITEMS.item_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    observations = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    message_id = Column(Integer, nullable=True)
    channel_id = Column(Integer, nullable=True)
    
    user = Relationship('User', foreign_keys=[user_id], backref='CHEST_LOG', lazy='subquery')
    item = Relationship('Item', foreign_keys=[item_id], backref='CHEST_LOG', lazy='subquery')

class Item(Base):
    __tablename__ = 'ITEMS'

    item_id = Column(Integer, primary_key=True, nullable=False)
    item_name = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    user = Relationship('User', foreign_keys=[created_by], backref='ITEMS', lazy='subquery')

class Seizure(Base):
    __tablename__ = 'SEIZURE'

    seizure_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    guild_id = Column(Integer, nullable=False)
    officer_name = Column(String(60), nullable=False)
    officer_badge = Column(String(10), nullable=False)
    image_url = Column(String(2048), nullable=True)
    observations = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False, default='PENDENTE') # PENDENTE, CRIADO, REEMBOLSADO, RESGATADO, CANCELADO    
    created_at = Column(DateTime, nullable=False)
    message_id = Column(Integer, nullable=True)
    refund_id = Column(Integer, ForeignKey('SEIZURE_REFUNDS.refund_id'), nullable=True)
    redeemed_at = Column(DateTime, nullable=True)

    user = Relationship('User', foreign_keys=[user_id], backref='SEIZURE', lazy='subquery')
    refund = Relationship('SeizureRefund', foreign_keys=[refund_id], backref='SEIZURE', lazy='subquery')

class SeizureRefund(Base):
    __tablename__ = 'SEIZURE_REFUNDS'
    
    refund_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    total_value = Column(Integer, nullable=False)
    redeemed_value = Column(Integer, nullable=True)
    message_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default='PENDENTE') # EM ANDAMENTO, FINALIZADO
    created_by = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    finished_by = Column(Integer, ForeignKey('USERS.user_id'), nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    user = Relationship('User', foreign_keys=[created_by], backref='SEIZURE_REFUNDS', lazy='subquery')    

class PersistentMessage(Base):
    __tablename__ = 'PERSISTENT_MESSAGES'

    view_key = Column(String, primary_key=True, nullable=False)
    message_id = Column(Integer, nullable=True)
    channel_id = Column(Integer, nullable=True)
    
class Log(Base):
    __tablename__ = 'LOGS'
    
    id = Column(Integer, primary_key=True, nullable=False)
    guild = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('USERS.user_id'), nullable=False)
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    user = Relationship('User', foreign_keys=[user_id], backref='LOGS', lazy='subquery')

Base.metadata.create_all(engine)
