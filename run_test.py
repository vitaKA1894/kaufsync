import subprocess
import time
from backend.database import SessionLocal, engine
from backend.models import User, List
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_db():
    db = SessionLocal()
    # Create test user
    email = "test@test.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        hashed_pw = pwd_context.hash("test1234")
        user = User(email=email, password_hash=hashed_pw, display_name="Test User")
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.password_hash = pwd_context.hash("test1234")
        db.commit()

    # Create test list
    test_list = db.query(List).filter(List.created_by == user.id).first()
    if not test_list:
        test_list = List(name="Test List", created_by=user.id, icon_name="Allgemein")
        db.add(test_list)
        db.commit()

    db.close()

if __name__ == '__main__':
    setup_db()
