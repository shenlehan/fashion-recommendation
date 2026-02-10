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
  print(f"\n=== 开始获取天气信息 ===")
  print(f"🌆 用户城市: {city}")
  weather = get_weather_by_city(city)
  print(f"🌡️  天气数据: 温度={weather.get('temperature')}°C, 状况={weather.get('condition')}")
  print(f"=== 天气获取完成 ===\n")

  # ===== RAG向量检索优化（分类平衡策略）=====
  # 1. 构建查询文本（天气 + 场合 + 风格）
  query_parts = [f"{weather.get('temperature', 20)}C", weather.get('condition', 'clear')]
  if occasion:
    query_parts.append(occasion)
  if style:
    query_parts.append(style)
  query_text = " ".join(query_parts)
  
  # 2. 使用分类平衡检索策略
  try:
    embedding_service = get_embedding_service()
    
    # 按类别检索，确保每类都有代表
    # 新分类体系：内衣 + 上身3层 + 下身 + 全身 + 鞋子 + 袜子 + 配饰
    categories = [
      'underwear',    # 内衣内裤
      'inner_top',    # 内层上衣（打底衫、背心、T恤）
      'mid_top',      # 中层上衣（衬衫、毛衣、卫衣）
      'outer_top',    # 外层上衣（夹克、外套、大衣）
      'bottom',       # 裤子、短裤、裙子
      'full_body',    # 连衣裙、连体裤
      'shoes',        # 鞋子
      'socks',        # 袜子
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
        print(f"  • {category}: {category_items}")
      selected_items.extend(category_items)
    
    # 去重（不限制总数）
    relevant_item_ids = list(dict.fromkeys(selected_items))
    
    if not relevant_item_ids:
      # 降级方案：向量检索失败时使用全量查询
      print(f"⚠️  向量检索无结果，降级为全量查询")
      wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    else:
      # 从数据库批量查询检索到的衣物
      wardrobe = db.query(WardrobeItem).filter(
        WardrobeItem.id.in_(relevant_item_ids)
      ).all()
      # 按向量检索的相关性排序
      id_to_item = {item.id: item for item in wardrobe}
      wardrobe = [id_to_item[item_id] for item_id in relevant_item_ids if item_id in id_to_item]
      
      print(f"✅ 分类平衡检索成功：从 {len(relevant_item_ids)} 件衣物中推荐（包含多类别）")
  
  except Exception as e:
    # 向量检索异常降级处理
    print(f"⚠️  向量检索异常，降级为全量查询: {e}")
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
