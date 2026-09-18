from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

PASSWORD = os.getenv("DB_PASSWORD")

if not PASSWORD:
    raise ValueError("DB_PASSWORD is not set in the environment")

DATABASE_URL = f"postgresql://postgres:{quote_plus(PASSWORD)}@localhost:5432/fintrack"
TEST_DATABASE_URL = f"postgresql://postgres:{quote_plus(PASSWORD)}@localhost:5432/fintrack_test"


engine = create_engine(DATABASE_URL)
test_engine = create_engine(TEST_DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()