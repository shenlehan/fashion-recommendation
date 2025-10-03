from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "蓝色T恤"
    category = Column(String, nullable=False)  # e.g., "top", "bottom", "outerwear"
    color = Column(String, nullable=False)     # e.g., "blue"
    season = Column(String, nullable=False)    # e.g., "spring,summer"
    material = Column(String, nullable=True)   # e.g., "cotton"
    image_path = Column(String, nullable=False)  # 本地/云端图片路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())