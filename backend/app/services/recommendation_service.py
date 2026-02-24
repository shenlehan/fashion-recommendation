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
        {"items": [1, 2], "reason": "适合当前天气"},
      ],
      "missing_items": ["thick jacket"]
    }
  except Exception as e:
    print(f"Error in recommendation service: {e}")
    import traceback
    traceback.print_exc()
    return {
      "outfits": [
        {"items": wardrobe_items[:2] if len(wardrobe_items) >= 2 else wardrobe_items,
         "description": "系统降级推荐（模型错误）"},
      ],
      "missing_items": [{"category": "accessories", "reason": "丰富你的衣橱"}]
    }


def adjust_outfit_with_conversation(
    session_id: str,
    adjustment_request: str,
    user_profile: Dict[str, Any],
    wardrobe_items: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]],
    current_outfit: List[int],
    db
) -> Dict[str, Any]:
  """基于对话历史调整穿搭方案"""
  try:
    from recommendation.logic import adjust_recommendations_with_conversation
    result = adjust_recommendations_with_conversation(
      session_id=session_id,
      adjustment_request=adjustment_request,
      user=user_profile,
      wardrobe=wardrobe_items,
      weather=weather,
      preferences=preferences,
      conversation_history=conversation_history,
      current_outfit=current_outfit
    )
    return result
  except ImportError:
    # 降级方案：返回重新生成的推荐
    return generate_outfit_recommendations(
      user_profile, wardrobe_items, weather, preferences
    )
  except Exception as e:
    print(f"Error in adjustment service: {e}")
    import traceback
    traceback.print_exc()
    return {
      "outfits": [
        {"items": wardrobe_items[:2] if len(wardrobe_items) >= 2 else wardrobe_items,
         "description": "系统降级推荐（调整失败）"},
      ],
      "missing_items": []
    }
