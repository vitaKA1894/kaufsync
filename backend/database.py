import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use DATA_DIR if set, otherwise default to current directory
DATA_DIR = os.getenv("DATA_DIR", ".")
# SQLite Datenbank-Datei
db_path = os.path.join(DATA_DIR, "kaufsync.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Engine erstellen (check_same_thread ist nur für SQLite nötig)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hilfsfunktion, um die Datenbank-Session in FastAPI-Endpunkten abzurufen
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()