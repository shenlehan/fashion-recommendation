from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.wardrobe import Wardrobe

DATABASE_URL = "sqlite:///./fashion_recommendation.db"  # Update with your database URL

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    # Create a new session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed initial data if necessary
    # Example: Add a default user
    default_user = User(username="default_user", password="password")
    session.add(default_user)
    
    # Example: Add a default wardrobe item
    default_item = Wardrobe(item_name="T-shirt", item_type="top", user_id=1)
    session.add(default_item)

    session.commit()
    session.close()

if __name__ == "__main__":
    init_db()