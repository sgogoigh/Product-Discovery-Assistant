from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
from dotenv import load_dotenv
load_dotenv()

# SQLAlchemy base class for models
Base = declarative_base()

# Create DB engine
engine = create_engine(os.getenv("DATABASE_URL"))

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize DB (create tables)
def init_db():
    Base.metadata.create_all(bind=engine)