from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base


class ConversationSession(Base):
  __tablename__ = "conversation_sessions"

  id = Column(Integer, primary_key=True, index=True)
  session_id = Column(String(64), unique=True, index=True, nullable=False)
  user_id = Column(Integer, nullable=False, index=True)
  
  # 时间戳
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
  
  # 对话历史：[{"role": "user/assistant", "content": "...", "outfit_ids": [...]}]
  conversation_history = Column(JSON, default=list)
  
  # 当前穿搭方案（衣物ID列表）
  current_outfit = Column(JSON, default=list)
  
  # 用户偏好快照（避免每次查询）
  preferences = Column(JSON, default=dict)
