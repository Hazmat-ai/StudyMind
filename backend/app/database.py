import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./studymind.db") # fallback for local dev if postgres not setup fully yet

# If using PostgreSQL with psycopg2, the URL needs to be correctly formatted. 
# SQLAlchemy 2.0 recommends using psycopg2 or asyncpg.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
