from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import sessionmaker
import os

# This creates a local database file named distribution.db
DATABASE_URL = "sqlite:///./distribution.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
