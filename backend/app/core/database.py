from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "sqlite:///./fashion_recommendation.db"  # Change this to your database URL

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a base class for declarative models
Base = declarative_base()

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()