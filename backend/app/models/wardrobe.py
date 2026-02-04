from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class WardrobeItem(Base):
  __tablename__ = "wardrobe_items"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  
  # 中文字段（前端显示）
  name = Column(String, nullable=False)  # e.g., "黑色针织毛衣"
  color = Column(String, nullable=False)  # e.g., "黑色"
  material = Column(String, nullable=True)  # e.g., "针织"
  
  # 英文字段（Prompt使用）
  name_en = Column(String, nullable=True)  # e.g., "Black Knit Sweater"
  color_en = Column(String, nullable=True)  # e.g., "black"
  material_en = Column(String, nullable=True)  # e.g., "knit"
  
  # 其他字段
  category = Column(String, nullable=False)  # e.g., "top", "bottom", "outerwear"
  season = Column(String, nullable=False)  # e.g., "spring,summer"
  image_path = Column(String, nullable=False)  # 本地/云端图片路径
  created_at = Column(DateTime(timezone=True), server_default=func.now())
