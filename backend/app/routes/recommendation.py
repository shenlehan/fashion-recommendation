from fastapi import APIRouter, Depends
from typing import List
from app.models.wardrobe import Wardrobe
from app.services.recommend_logic import generate_recommendations
from app.services.weather_api import get_weather
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/recommendations/", response_model=List[str])
async def recommend_outfits(user_id: int, db: Session = Depends(get_db)):
    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == user_id).all()
    weather_data = get_weather()  # Fetch current weather data
    recommendations = generate_recommendations(wardrobe_items, weather_data)
    return recommendations

@router.get("/recommendations/{user_id}", response_model=List[str])
async def get_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == user_id).all()
    weather_data = get_weather()  # Fetch current weather data
    recommendations = generate_recommendations(wardrobe_items, weather_data)
    return recommendations
