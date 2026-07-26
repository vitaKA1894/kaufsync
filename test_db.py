from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

import sys
sys.path.append('backend')
from models import Base, User, List, Item
import auth

SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/kaufsync.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Ensure test user exists
user = db.query(User).filter(User.email == "test@test.com").first()
if not user:
    user = User(email="test@test.com", password_hash=auth.get_password_hash("test1234"), display_name="Test User")
    db.add(user)
    db.commit()
    db.refresh(user)

# Ensure a list exists for the user
test_list = db.query(List).filter(List.created_by == user.id).first()
if not test_list:
    test_list = List(name="Test List", created_by=user.id)
    db.add(test_list)
    db.commit()

print("Test database setup complete.")
