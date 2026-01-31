from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.weather_api import get_weather_by_city
from app.services.recommendation_service import generate_outfit_recommendations
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

  wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  wardrobe_list = [
    {
      "id": item.id,
      "name": item.name,
      "category": item.category,
      "color": item.color,
      "season": item.season,
      "material": item.material,
      "image_path": item.image_path
    }
    for item in wardrobe
  ]

  weather = {"temperature": 7, "condition": "Sunny"}

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
      "body_type": user.body_type,
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
