from typing import Dict, List, Any, Optional


def generate_outfit_recommendations(
    user_profile: Dict[str, Any],
    wardrobe_items: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  try:
    from recommendation.logic import get_recommendations
    result = get_recommendations(
      user=user_profile,
      wardrobe=wardrobe_items,
      weather=weather,
      preferences=preferences
    )
    return result
  except ImportError:
    return {
      "outfits": [
        {"items": [1, 2], "reason": "Mock 推荐：适合当前天气"},
      ],
      "missing_items": ["thick jacket"]
    }
  except Exception as e:
    print(f"❌ Error in recommendation service: {e}")
    import traceback
    traceback.print_exc()
    return {
      "outfits": [
        {"items": wardrobe_items[:2] if len(wardrobe_items) >= 2 else wardrobe_items,
         "description": "系统降级推荐（模型错误）"},
      ],
      "missing_items": [{"category": "accessories", "reason": "丰富你的衣橱"}]
    }
