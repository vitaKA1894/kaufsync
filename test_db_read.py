from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append('backend')
from models import Base, User, List, Item
import auth

SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/kaufsync.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Add a test item to test_list
user = db.query(User).filter(User.email == "test@test.com").first()
test_list = db.query(List).filter(List.created_by == user.id).first()

items = db.query(Item).filter(Item.list_id == test_list.id).all()
for item in items:
    print(f"Item: {item.name}, Tags: {item.tags}")

with engine.connect() as conn:
    res = conn.execute(text("PRAGMA table_info(items)"))
    print([r for r in res])
