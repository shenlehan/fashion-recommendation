from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.weather_api import get_weather_by_city
from app.services.recommendation_service import generate_outfit_recommendations, adjust_outfit_with_conversation
from app.services.embedding_service import get_embedding_service
from app.services.conversation_manager import ConversationManager
from app.models.user import User
from app.models.wardrobe import WardrobeItem

router = APIRouter()


@router.get("/outfits")
def get_outfit_recommendations(
    user_id: int,
    occasion: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    color_preference: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="用户不存在")

  # 检查必填字段
  if not user.gender or not user.age:
    raise HTTPException(status_code=400, detail="请先完善个人资料")
  
  # 检查身高体重必填项
  if not user.height or not user.weight:
    raise HTTPException(status_code=400, detail="请先完善个人资料")

  # 获取天气信息（根据用户城市）
  city = user.city or "北京"  # 默认北京
  weather = get_weather_by_city(city)

  # ===== RAG向量检索优化（分类平衡策略）=====
  # 1. 构建查询文本（天气 + 场合 + 风格）- 简化为核心特征
  
  temp_max = weather.get('temp_max', 25)
  temp_min = weather.get('temp_min', 15)
  avg_temp = (temp_max + temp_min) // 2
  
  query_parts = []
  
  # 核心特征1：温度描述（只保留最关键的）
  if avg_temp >= 28:
    query_parts.extend(['hot', 'lightweight', 'thin'])  # 高温特征
  elif avg_temp >= 20:
    query_parts.extend(['warm', 'comfortable', 'breathable'])  # 温暖特征
  elif avg_temp >= 10:
    query_parts.extend(['cool', 'layered', 'moderate'])  # 凉爽特征
  else:
    query_parts.extend(['cold', 'insulated', 'thick', 'warm'])  # 保暖特征
  
  # 核心特征2：天气状况（处理趋势并映射为英文）
  condition = weather.get('condition', 'clear')
  
  # 中文天气状况映射回英文（用于向量检索）
  cn_to_en_map = {
    '晴': 'sunny',
    '多云': 'cloudy',
    '阴': 'overcast',
    '小雨': 'light rain',
    '中雨': 'rain',
    '大雨': 'heavy rain',
    '暴雨': 'rainstorm',
    '雷阵雨': 'thunderstorm',
    '小雪': 'light snow',
    '中雪': 'snow',
    '大雪': 'heavy snow',
    '暴雪': 'snowstorm',
    '雾': 'foggy',
    '霾': 'hazy',
    '沙尘': 'dusty'
  }
  
  if '转' in condition:  # 如"多云转晴"
    parts = condition.split('转')
    final_weather_cn = parts[-1]  # 最终状态（中文）
    final_weather_en = cn_to_en_map.get(final_weather_cn, condition.lower())
    query_parts.append(final_weather_en)
  else:
    # 如果是英文，转为小写；如果是中文，映射为英文
    if any('\u4e00' <= c <= '\u9fff' for c in condition):
      # 包含中文字符
      weather_en = cn_to_en_map.get(condition, condition.lower())
      query_parts.append(weather_en)
    else:
      # 纯英文
      query_parts.append(condition.lower())
  
  # 核心特征3：特殊天气需求（只添加最重要的）
  rain_prob = weather.get('rain_prob', 0)
  if rain_prob > 50:
    query_parts.append('waterproof')  # 高降水概率
  
  humidity = weather.get('humidity', 60)
  if humidity > 75:
    query_parts.append('breathable')  # 高湿度
  
  # 用户偏好（只保留通用属性，避免类别交叉污染）
  if occasion:
    query_parts.append(occasion)
    # 只添加与场合相关的通用形容词，不添加具体类别
    occasion_lower = occasion.lower()
    if occasion_lower in ['business', 'formal', 'office']:
      query_parts.extend(['formal', 'professional', 'elegant'])
    elif occasion_lower in ['work', 'commute']:
      query_parts.extend(['practical', 'professional', 'comfortable'])
    elif occasion_lower in ['casual', 'daily', 'everyday']:
      query_parts.extend(['comfortable', 'relaxed', 'simple'])
    elif occasion_lower in ['home', 'indoor', 'leisure']:
      query_parts.extend(['cozy', 'comfortable', 'relaxed', 'soft'])
    elif occasion_lower in ['sport', 'gym', 'fitness', 'exercise']:
      query_parts.extend(['athletic', 'functional', 'flexible'])
    elif occasion_lower in ['party', 'celebration', 'nightclub']:
      query_parts.extend(['stylish', 'fashionable', 'eye-catching'])
    elif occasion_lower in ['date', 'romantic', 'dinner']:
      query_parts.extend(['elegant', 'charming', 'refined'])
    elif occasion_lower in ['travel', 'vacation', 'trip']:
      query_parts.extend(['versatile', 'practical', 'easy-care'])
    elif occasion_lower in ['outdoor', 'hiking', 'camping']:
      query_parts.extend(['durable', 'functional', 'protective'])
  
  if style:
    query_parts.append(style)
  
  # 色调偏好（保留抽象概念，避免过度限制）
  if color_preference:
    color_lower = color_preference.lower()
    if color_lower in ['neutral', 'neutrals']:
      query_parts.append('neutral-tone')
    elif color_lower in ['warm', 'warm-tone', 'warm-tones']:
      query_parts.append('warm-tone')
    elif color_lower in ['cool', 'cool-tone', 'cool-tones']:
      query_parts.append('cool-tone')
  
  query_text = " ".join(query_parts)
  
  # 2. 使用分类平衡检索策略
  try:
    embedding_service = get_embedding_service()
    
    # 按类别检索，确保每类都有代表
    # 新分类体系：上身3层 + 下身 + 全身 + 鞋子 + 配饰（排除内衣和袜子）
    categories = [
      'inner_top',    # 内层上衣（打底衫、背心、T恤）
      'mid_top',      # 中层上衣（衬衫、毛衣、卫衣）
      'outer_top',    # 外层上衣（夹克、外套、大衣）
      'bottom',       # 裤子、短裤、裙子
      'full_body',    # 连衣裙、连体裤
      'shoes',        # 鞋子
      'accessories'   # 包、帽子、围巾、首饰等
    ]
    selected_items = []
    items_per_category = 3  # 每类最多3件
    
    for category in categories:
      category_items = embedding_service.search_similar_items(
        query_text=query_text,
        user_id=user_id,
        top_k=items_per_category,
        category_filter=category
      )
      if category_items:
        selected_items.extend(category_items)
    
    # 去重（不限制总数）
    relevant_item_ids = list(dict.fromkeys(selected_items))
    
    if not relevant_item_ids:
      # 降级方案：向量检索失败时使用全量查询
      wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    else:
      # 从数据库批量查询检索到的衣物
      wardrobe = db.query(WardrobeItem).filter(
        WardrobeItem.id.in_(relevant_item_ids)
      ).all()
      # 按向量检索的相关性排序
      id_to_item = {item.id: item for item in wardrobe}
      wardrobe = [id_to_item[item_id] for item_id in relevant_item_ids if item_id in id_to_item]
  
  except Exception as e:
    # 向量检索异常降级处理
    wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  
  # ===== 构建衣物列表 =====
  wardrobe_list = [
    {
      "id": item.id,
      "name": item.name,
      "name_en": item.name_en,
      "category": item.category,
      "color": item.color,
      "color_en": item.color_en,
      "season": item.season,
      "material": item.material,
      "material_en": item.material_en,
      "image_path": item.image_path
    }
    for item in wardrobe
  ]

  preferences = {}
  if occasion:
    preferences["occasion"] = occasion
  if style:
    preferences["style"] = style
  if color_preference:
    preferences["color_preference"] = color_preference

  # 创建新的对话会话
  session_id = ConversationManager.create_session(db, user_id, preferences)
  
  result = generate_outfit_recommendations(
    user_profile={
      "id": user.id,
      "gender": user.gender,
      "age": user.age,
      "height": user.height,
      "weight": user.weight,
      "city": user.city
    },
    wardrobe_items=wardrobe_list,
    weather=weather,
    preferences=preferences if preferences else None
  )
  
  # ⚠️ 修改：不自动保存推荐到会话历史，等用户选择后再保存
  # 用户需要调用 /select-outfit 接口来选择某组推荐

  return {
    "session_id": session_id,
    "weather": weather,
    "outfits": result.get("outfits", []),
    "missing_items": result.get("missing_items", [])
  }


@router.post("/select-outfit")
def select_outfit(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
  """用户选择某组推荐作为会话基础"""
  session_id = payload.get("session_id")
  outfit_index = payload.get("outfit_index")  # 推荐组索引（0-based）
  outfit_data = payload.get("outfit_data")  # 推荐组数据（items + description）
  user_id = payload.get("user_id")
  
  if not session_id or outfit_index is None or not outfit_data:
    raise HTTPException(status_code=400, detail="缺少必要参数")
  
  # 验证会话存在
  session = ConversationManager.get_session(db, session_id)
  if not session:
    raise HTTPException(status_code=404, detail="会话不存在")
  
  # 验证用户权限
  if session.user_id != user_id:
    raise HTTPException(status_code=403, detail="无权操作此会话")
  
  # 提取衣物ID
  outfit_ids = [item["id"] for item in outfit_data.get("items", [])]
  description = outfit_data.get("description", "已选择推荐方案")
  
  # 保存到会话历史
  ConversationManager.add_message(
    db, session_id, "assistant",
    description,
    outfit_ids
  )
  
  # 更新当前穿搭
  ConversationManager.update_current_outfit(db, session_id, outfit_ids)
  
  # 获取更新后的会话历史和衣物映射
  updated_session = ConversationManager.get_session(db, session_id)
  all_item_ids = set()
  for msg in updated_session.conversation_history or []:
    if "outfit_ids" in msg:
      all_item_ids.update(msg["outfit_ids"])
  
  # 查询衣物详情
  items_map = {}
  if all_item_ids:
    items = db.query(WardrobeItem).filter(WardrobeItem.id.in_(all_item_ids)).all()
    for item in items:
      items_map[item.id] = {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "color": item.color,
        "image_path": item.image_path
      }
  
  return {
    "success": True,
    "message": "已选择推荐方案作为会话基础",
    "conversation_history": updated_session.conversation_history,
    "items_map": items_map
  }


@router.post("/adjust")
def adjust_outfit(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
  """根据用户反馈调整穿搭方案（多轮对话）"""
  session_id = payload.get("session_id")
  adjustment_request = payload.get("adjustment_request")
  user_id = payload.get("user_id")
  
  if not session_id or not adjustment_request:
    raise HTTPException(status_code=400, detail="缺少session_id或adjustment_request")
  
  # 验证会话存在
  session = ConversationManager.get_session(db, session_id)
  if not session:
    raise HTTPException(status_code=404, detail="会话不存在")
  
  # 验证用户权限
  if session.user_id != user_id:
    raise HTTPException(status_code=403, detail="无权操作此会话")
  
  # 检查会话是否过期（3天）
  from datetime import datetime, timedelta
  if datetime.now() - session.updated_at > timedelta(days=3):
    # 删除过期会话
    ConversationManager.delete_session(db, session_id)
    raise HTTPException(status_code=410, detail="会话已过期（3天未活跃），请重新生成推荐")
  
  # 记录用户调整请求
  ConversationManager.add_message(db, session_id, "user", adjustment_request)
  
  # 获取用户和衣物数据
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="用户不存在")
  
  # 获取天气信息
  city = user.city or "北京"
  weather = get_weather_by_city(city)
  
  # 向量检索相关衣物
  try:
    embedding_service = get_embedding_service()
    
    # 构建检索查询（结合调整请求和天气）
    query_parts = [adjustment_request]
    
    temp_max = weather.get('temp_max', 25)
    temp_min = weather.get('temp_min', 15)
    avg_temp = (temp_max + temp_min) // 2
    
    if avg_temp >= 28:
      query_parts.extend(['hot', 'lightweight'])
    elif avg_temp >= 20:
      query_parts.append('warm')
    elif avg_temp >= 10:
      query_parts.append('cool')
    else:
      query_parts.extend(['cold', 'warm'])
    
    query_text = " ".join(query_parts)
    
    categories = [
      'inner_top', 'mid_top', 'outer_top', 'bottom',
      'full_body', 'shoes', 'accessories'
    ]
    selected_items = []
    
    for category in categories:
      category_items = embedding_service.search_similar_items(
        query_text=query_text,
        user_id=user_id,
        top_k=3,
        category_filter=category
      )
      if category_items:
        selected_items.extend(category_items)
    
    relevant_item_ids = list(dict.fromkeys(selected_items))
    
    if not relevant_item_ids:
      wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    else:
      wardrobe = db.query(WardrobeItem).filter(
        WardrobeItem.id.in_(relevant_item_ids)
      ).all()
      id_to_item = {item.id: item for item in wardrobe}
      wardrobe = [id_to_item[item_id] for item_id in relevant_item_ids if item_id in id_to_item]
  
  except Exception as e:
    wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  
  # 构建衣物列表
  wardrobe_list = [
    {
      "id": item.id,
      "name": item.name,
      "name_en": item.name_en,
      "category": item.category,
      "color": item.color,
      "color_en": item.color_en,
      "season": item.season,
      "material": item.material,
      "material_en": item.material_en,
      "image_path": item.image_path
    }
    for item in wardrobe
  ]
  
  # 调用AI调整服务
  result = adjust_outfit_with_conversation(
    session_id=session_id,
    adjustment_request=adjustment_request,
    user_profile={
      "id": user.id,
      "gender": user.gender,
      "age": user.age,
      "height": user.height,
      "weight": user.weight,
      "city": user.city
    },
    wardrobe_items=wardrobe_list,
    weather=weather,
    preferences=session.preferences,
    conversation_history=session.conversation_history,
    current_outfit=session.current_outfit,
    db=db
  )
  
  # 保存调整结果
  if result.get("outfits") and len(result["outfits"]) > 0:
    first_outfit = result["outfits"][0]
    outfit_ids = [item["id"] for item in first_outfit.get("items", [])]
    
    ConversationManager.add_message(
      db, session_id, "assistant",
      first_outfit.get("description", "调整了推荐方案"),
      outfit_ids
    )
    ConversationManager.update_current_outfit(db, session_id, outfit_ids)
  
  # 获取更新后的会话历史和衣物映射
  updated_session = ConversationManager.get_session(db, session_id)
  
  all_item_ids = set()
  for msg in updated_session.conversation_history or []:
    if "outfit_ids" in msg:
      all_item_ids.update(msg["outfit_ids"])
  
  # 批量查询衣物信息
  items_map = {}
  if all_item_ids:
    items = db.query(WardrobeItem).filter(WardrobeItem.id.in_(all_item_ids)).all()
    items_map = {
      item.id: {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "color": item.color,
        "image_path": item.image_path
      }
      for item in items
    }
  
  return {
    "session_id": session_id,
    "outfits": result.get("outfits", []),
    "conversation_history": updated_session.conversation_history,
    "items_map": items_map
  }


@router.get("/sessions")
def get_user_sessions(
    user_id: int = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
  """获取用户的会话列表（自动过滤过期会话）"""
  from datetime import datetime, timedelta
  
  sessions = ConversationManager.get_user_sessions(db, user_id, limit, offset)
  
  # 过滤3天前的会话不显示（处理updated_at为None的情况）
  cutoff_date = datetime.now() - timedelta(days=3)
  active_sessions = [s for s in sessions if s.updated_at and s.updated_at >= cutoff_date]
  
  return {
    "sessions": [
      {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "preferences": session.preferences,
        "message_count": len(session.conversation_history or []),
        "preview": (session.conversation_history[0].get("content", "") 
                   if session.conversation_history and len(session.conversation_history) > 0 
                   else "新会话")
      }
      for session in active_sessions
    ],
    "has_more": len(sessions) == limit  # 如果返回数量等于limit，说明可能还有更多
  }


@router.get("/sessions/{session_id}")
def get_session_detail(
    session_id: str,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
  """获取会话详情和完整历史"""
  session = ConversationManager.get_session(db, session_id)
  if not session:
    raise HTTPException(status_code=404, detail="会话不存在")
  
  if session.user_id != user_id:
    raise HTTPException(status_code=403, detail="无权访问此会话")
  
  # 获取对话中涉及的所有衣物ID
  all_item_ids = set()
  for msg in session.conversation_history or []:
    if "outfit_ids" in msg:
      all_item_ids.update(msg["outfit_ids"])
  
  # 批量查询衣物信息
  items_map = {}
  if all_item_ids:
    items = db.query(WardrobeItem).filter(WardrobeItem.id.in_(all_item_ids)).all()
    items_map = {
      item.id: {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "color": item.color,
        "image_path": item.image_path
      }
      for item in items
    }
  
  return {
    "session_id": session.session_id,
    "created_at": session.created_at.isoformat(),
    "updated_at": session.updated_at.isoformat(),
    "preferences": session.preferences,
    "conversation_history": session.conversation_history,
    "current_outfit": session.current_outfit,
    "items_map": items_map
  }


@router.delete("/sessions/{session_id}/messages/{message_index}")
def delete_conversation_message(
    session_id: str,
    message_index: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
  """删除对话中的特定消息"""
  # 验证会话存在且属于该用户
  session = ConversationManager.get_session(db, session_id)
  if not session:
    raise HTTPException(status_code=404, detail="会话不存在")
  
  if session.user_id != user_id:
    raise HTTPException(status_code=403, detail="无权操作此会话")
  
  try:
    ConversationManager.delete_message(db, session_id, message_index)
    return {
      "success": True,
      "message": "消息已删除",
      "remaining_count": len(session.conversation_history or []) - 1
    }
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
  """删除整个会话"""
  # 验证会话存在且属于该用户
  session = ConversationManager.get_session(db, session_id)
  if not session:
    raise HTTPException(status_code=404, detail="会话不存在")
  
  if session.user_id != user_id:
    raise HTTPException(status_code=403, detail="无权删除此会话")
  
  # 删除会话
  ConversationManager.delete_session(db, session_id)
  
  return {
    "success": True,
    "message": "会话已删除"
  }


@router.delete("/sessions")
def delete_all_sessions(
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
  """清空用户的所有会话"""
  count = ConversationManager.delete_all_user_sessions(db, user_id)
  
  return {
    "success": True,
    "message": f"已清空 {count} 个会话",
    "deleted_count": count
  }
