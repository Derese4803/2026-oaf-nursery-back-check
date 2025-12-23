import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Determine the path for the database file
# This ensures the file is created in the same folder as your app code
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'survey.db')

# 2. Create the Database Engine
# check_same_thread=False is required for SQLite to work with Streamlit's multi-threading
engine = create_engine(
    f'sqlite:///{DB_PATH}', 
    connect_args={"check_same_thread": False}
)

# 3. Create the Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base class for models to inherit from
Base = declarative_base()
