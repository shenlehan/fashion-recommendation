from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.conversation import ConversationSession


class ConversationManager:
  @staticmethod
  def create_session(db: Session, user_id: int, preferences: Optional[Dict] = None) -> str:
    """创建新的对话会话"""
    session_id = str(uuid.uuid4())
    
    new_session = ConversationSession(
      session_id=session_id,
      user_id=user_id,
      conversation_history=[],
      current_outfit=[],
      preferences=preferences or {}
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return session_id
  
  @staticmethod
  def get_session(db: Session, session_id: str) -> Optional[ConversationSession]:
    """获取会话"""
    return db.query(ConversationSession).filter(
      ConversationSession.session_id == session_id
    ).first()
  
  @staticmethod
  def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    outfit_ids: Optional[List[int]] = None
  ):
    """向会话添加消息"""
    session = ConversationManager.get_session(db, session_id)
    if not session:
      raise ValueError(f"Session {session_id} not found")
    
    message = {
      "role": role,
      "content": content,
      "timestamp": datetime.now().isoformat()
    }
    
    if outfit_ids is not None:
      message["outfit_ids"] = outfit_ids
    
    history = session.conversation_history or []
    history.append(message)
    
    # 限制对话历史最多20转，超出删除最早的
    if len(history) > 20:
      history = history[-20:]
    
    # SQLAlchemy的JSON字段需要重新赋值才能触发更新
    session.conversation_history = history[:]
    flag_modified(session, 'conversation_history')
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
  
  @staticmethod
  def update_current_outfit(db: Session, session_id: str, outfit_ids: List[int]):
    """更新当前穿搭方案"""
    session = ConversationManager.get_session(db, session_id)
    if not session:
      raise ValueError(f"Session {session_id} not found")
    
    # SQLAlchemy的JSON字段需要重新赋值才能触发更新
    session.current_outfit = outfit_ids[:]
    flag_modified(session, 'current_outfit')
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
  
  @staticmethod
  def get_conversation_history(db: Session, session_id: str) -> List[Dict]:
    """获取对话历史"""
    session = ConversationManager.get_session(db, session_id)
    if not session:
      return []
    
    return session.conversation_history or []
  
  @staticmethod
  def delete_message(db: Session, session_id: str, message_index: int) -> bool:
    """删除指定索引的消息"""
    session = ConversationManager.get_session(db, session_id)
    if not session:
      raise ValueError(f"Session {session_id} not found")
    
    history = session.conversation_history or []
    
    # 检查索引是否有效
    if message_index < 0 or message_index >= len(history):
      raise ValueError(f"Invalid message index: {message_index}")
    
    # 删除消息
    history.pop(message_index)
    
    # 重新赋值触发SQLAlchemy更新
    session.conversation_history = history[:]
    flag_modified(session, 'conversation_history')
    session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(session)
    
    return True
  
  @staticmethod
  def delete_session(db: Session, session_id: str):
    """删除会话"""
    session = ConversationManager.get_session(db, session_id)
    if session:
      db.delete(session)
      db.commit()
  
  @staticmethod
  def delete_all_user_sessions(db: Session, user_id: int) -> int:
    """删除用户的所有会话"""
    sessions = db.query(ConversationSession).filter(
      ConversationSession.user_id == user_id
    ).all()
    
    count = len(sessions)
    for session in sessions:
      db.delete(session)
    
    if count > 0:
      db.commit()
    
    return count
  
  @staticmethod
  def get_user_sessions(db: Session, user_id: int, limit: int = 10, offset: int = 0) -> List[ConversationSession]:
    """获取用户的所有会话（支持分页）"""
    return db.query(ConversationSession).filter(
      ConversationSession.user_id == user_id
    ).order_by(ConversationSession.updated_at.desc()).offset(offset).limit(limit).all()
  
  @staticmethod
  def cleanup_old_sessions(db: Session, days: int = 7) -> int:
    """清理超过指定天数的会话"""
    cutoff_date = datetime.now() - timedelta(days=days)
    old_sessions = db.query(ConversationSession).filter(
      ConversationSession.updated_at < cutoff_date
    ).all()
    
    count = len(old_sessions)
    for session in old_sessions:
      db.delete(session)
    
    if count > 0:
      db.commit()
    
    return count
