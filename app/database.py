from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Use proper connection handling
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "postgres.USER" in DATABASE_URL:
    # Use SQLite as a logical fallback if no env provided or default template is used
    print("WARNING: Valid DATABASE_URL not found in .env, using local sqlite.db")
    DATABASE_URL = "sqlite:///./local.db"

# connect_args={"check_same_thread": False} is needed for SQLite.
# For Postgres (Supabase), we often need to enforce SSL mode.
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    # Force SSL for Postgres connections to avoid "server closed connection" errors
    connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL, 
    # echo=True, 
    connect_args=connect_args,
    pool_pre_ping=False # Automatically reconnect if connection drops
)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
