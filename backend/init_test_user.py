from database import SessionLocal
import models
from auth import get_password_hash

db = SessionLocal()
try:
    user = models.User(email="test@test.com", password_hash=get_password_hash("test1234"), status="active")
    db.add(user)
    db.commit()
    print("Test user created with ID:", user.id)
except Exception as e:
    print(e)
finally:
    db.close()
