from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session,declarative_base

# DATABASE_URL = "sqlite:///./test.db"
DATABASE_URL = "postgresql://jimi:jimi@localhost:5432/smartsafi_db"

# engine = create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}  # Needed for SQLite
# )
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
