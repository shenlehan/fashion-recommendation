"""
推荐路由
职责：获取穿搭推荐、缺失品类分析
与前端交互接口：
- GET /api/v1/recommend/outfits
- GET /api/v1/recommend/missing
与推荐模块交互：调用推荐算法
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.weather_api import get_weather_by_city
from app.services.recommendation_service import generate_outfit_recommendations
from app.models.user import User
from app.models.wardrobe import WardrobeItem

router = APIRouter()

@router.get("/outfits")
def get_outfit_recommendations(user_id: int, db: Session = Depends(get_db)):
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    wardrobe_list = [
        {
            "id": item.id,
            "category": item.category,
            "color": item.color,
            "season": item.season.split(","),
            "material": item.material
        }
        for item in wardrobe
    ]

    weather = get_weather_by_city(user.city)

    result = generate_outfit_recommendations(
        user_profile={
            "id": user.id,
            "body_type": user.body_type,
            "city": user.city
        },
        wardrobe_items=wardrobe_list,
        weather=weather
    )
    return result