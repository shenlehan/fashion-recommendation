from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Wardrobe(Base):
    __tablename__ = 'wardrobes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    clothing_item = Column(String, index=True)
    category = Column(String, index=True)
    image_url = Column(String)

    user = relationship("User", back_populates="wardrobes")

    def __repr__(self):
        return f"<Wardrobe(id={self.id}, user_id={self.user_id}, clothing_item='{self.clothing_item}', category='{self.category}')>"