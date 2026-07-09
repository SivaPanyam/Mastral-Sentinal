from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
import sys

DATABASE_URL = settings.get_database_url()

if not DATABASE_URL.startswith("postgresql"):
    print("FATAL ERROR: A PostgreSQL DATABASE_URL is required.")
    sys.exit(1)

# Enforce postgresql connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
