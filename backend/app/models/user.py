from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  username = Column(String, unique=True, index=True, nullable=False)
  email = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)
  gender = Column(String, nullable=True)  # 性别：male/female/other
  age = Column(Integer, nullable=True)  # 年龄
  height = Column(Integer, nullable=False)  # 身高(cm) 必填
  weight = Column(Integer, nullable=False)  # 体重(kg) 必填
  city = Column(String, nullable=True)  # e.g., "Beijing"
  profile_photo = Column(String, nullable=True)  # 个人正面照路径
  created_at = Column(DateTime(timezone=True), server_default=func.now())
