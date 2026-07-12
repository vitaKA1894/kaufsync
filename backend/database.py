from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite Datenbank-Datei im selben Ordner
SQLALCHEMY_DATABASE_URL = "sqlite:///./kaufsync.db"

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