from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.weather_api import get_weather_by_city
from app.services.recommendation_service import generate_outfit_recommendations
from app.services.embedding_service import get_embedding_service
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
        print(f"🔍 [{category}] 检索到 {len(category_items)} 件: {category_items}")
        selected_items.extend(category_items)
    
    # 去重（不限制总数）
    relevant_item_ids = list(dict.fromkeys(selected_items))
    print(f"✅ 向量检索总计: {len(relevant_item_ids)} 件衣物 (ID: {relevant_item_ids})")
    
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

  return {
    "weather": weather,
    "outfits": result.get("outfits", []),
    "missing_items": result.get("missing_items", [])
  }
