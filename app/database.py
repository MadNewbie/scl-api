from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

db_name = os.getenv("DB_NAME")
db_username = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

DB_URL = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DB_URL, echo=True)

autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

SessionLocalAutoCommit = sessionmaker(autoflush=False, bind=autocommit_engine, autocommit=False)

Base = declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def autocommit_db():
    db=SessionLocalAutoCommit()
    try:
        yield db
    finally:
        db.close()
