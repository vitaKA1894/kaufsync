from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import random
import string
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Generiert einen 6-stelligen Code aus Großbuchstaben und Zahlen
def generate_share_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Zwischentabelle: Speichert, welcher User in welcher Liste Mitglied ist
list_members = Table(
    'list_members',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('list_id', String, ForeignKey('lists.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class List(Base):
    __tablename__ = "lists"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    icon_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))
    share_code = Column(String, unique=True, index=True, default=generate_share_code) # NEU
    
    # Beziehungen
    items = relationship("Item", back_populates="shopping_list", cascade="all, delete-orphan")
    members = relationship("User", secondary=list_members, backref="shared_lists") # NEU

class Item(Base):
    __tablename__ = "items"
    id = Column(String, primary_key=True, default=generate_uuid)
    list_id = Column(String, ForeignKey("lists.id"))
    name = Column(String)
    category = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    unit = Column(String, default="Stk")
    note = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    shopping_list = relationship("List", back_populates="items")