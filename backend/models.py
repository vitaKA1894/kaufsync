from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import secrets
import string
from database import Base
from sqlalchemy import Boolean

def generate_uuid():
    return str(uuid.uuid4())

# Generiert einen 6-stelligen Code aus Großbuchstaben und Zahlen
def generate_share_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

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
    is_admin = Column(Boolean, default=False)
    status = Column(String, default="pending") # 'pending', 'active', 'locked'
    settings_push_async_events = Column(Boolean, default=False)
    settings_push_new_items = Column(Boolean, default=False)
    settings_push_admin_pending_users = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    token = Column(String, index=True)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    title = Column(String)
    body = Column(String)
    action_url = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    endpoint = Column(String)
    p256dh = Column(String)
    auth = Column(String)
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
    creator = relationship("User", foreign_keys=[created_by])

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    list_id = Column(String, ForeignKey("lists.id"))
    user_id = Column(String, ForeignKey("users.id"))
    action_type = Column(String) # 'added', 'completed', 'deleted', 'reactivated'
    item_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Beziehungen
    list = relationship("List")
    user = relationship("User", foreign_keys=[user_id])

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
    tags = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    shopping_list = relationship("List", back_populates="items")

class ListInvitation(Base):
    __tablename__ = "list_invitations"
    id = Column(String, primary_key=True, default=generate_uuid)
    list_id = Column(String, ForeignKey("lists.id"))
    inviter_id = Column(String, ForeignKey("users.id"))
    invitee_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="pending") # "pending", "accepted", "declined"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Beziehungen
    list = relationship("List")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])