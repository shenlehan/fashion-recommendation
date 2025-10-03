from typing import List, Dict
import random

class ClothingItem:
    def __init__(self, item_type: str, image_url: str, size: str):
        self.item_type = item_type
        self.image_url = image_url
        self.size = size

class User:
    def __init__(self, body_type: str, wardrobe: List[ClothingItem]):
        self.body_type = body_type
        self.wardrobe = wardrobe

def get_weather_condition() -> str:
    # Placeholder for actual weather API call
    return random.choice(["sunny", "rainy", "cold"])

def recommend_outfits(user: User) -> List[Dict[str, str]]:
    weather = get_weather_condition()
    recommendations = []

    for item in user.wardrobe:
        if weather == "sunny" and item.item_type in ["t-shirt", "shorts"]:
            recommendations.append({"item": item.item_type, "image": item.image_url})
        elif weather == "rainy" and item.item_type in ["raincoat", "umbrella"]:
            recommendations.append({"item": item.item_type, "image": item.image_url})
        elif weather == "cold" and item.item_type in ["jacket", "sweater"]:
            recommendations.append({"item": item.item_type, "image": item.image_url})

    return recommendations

def analyze_missing_items(user: User) -> List[str]:
    required_items = {
        "sunny": ["t-shirt", "shorts", "sunglasses"],
        "rainy": ["raincoat", "umbrella", "waterproof shoes"],
        "cold": ["jacket", "sweater", "thermal wear"]
    }

    weather = get_weather_condition()
    missing_items = [item for item in required_items[weather] if item not in [clothing.item_type for clothing in user.wardrobe]]

    return missing_items

def generate_recommendations(user: User) -> Dict[str, List[Dict[str, str]]]:
    outfits = recommend_outfits(user)
    missing_items = analyze_missing_items(user)

    return {
        "outfits": outfits,
        "missing_items": missing_items
    }
