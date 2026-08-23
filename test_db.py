import sys
sys.path.append('backend')
from database import engine, Base
from models import User, List
from database import SessionLocal
from auth import get_password_hash

Base.metadata.create_all(bind=engine)

db = SessionLocal()
pwd_hash = get_password_hash('test1234')

user = db.query(User).filter_by(email='test@test.com').first()
if user:
    user.password_hash = pwd_hash
    db.commit()
else:
    user = User(
        id='test-user-id',
        email='test@test.com',
        password_hash=pwd_hash,
        display_name='Test User',
        status='active'
    )
    db.add(user)
    db.commit()
    db.refresh(user)

new_list = db.query(List).filter_by(name='My Test List').first()
if not new_list:
    new_list = List(
        id='test-list-id',
        name='My Test List',
        icon_name='🛒',
        created_by=user.id,
        share_code='TEST12'
    )
    new_list.members.append(user)
    db.add(new_list)
    db.commit()

db.close()
print('Database setup successfully')
