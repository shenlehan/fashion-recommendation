"""
推荐服务
职责：整合用户信息、衣橱、天气，调用推荐算法
与推荐模块交互：调用 recommendation.logic.get_recommendations()
返回格式：{
    "outfits": [
        {"items": [1, 2], "reason": "适合晴天"},
    ],
    "missing_items": ["winter coat"]
}
"""
from typing import Dict, List, Any, Optional

def generate_outfit_recommendations(
    user_profile: Dict[str, Any],
    wardrobe_items: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    预留接口：生成穿搭推荐
    """
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
        # 开发阶段 mock 返回
        return {
            "outfits": [
                {"items": [1, 2], "reason": "Mock 推荐：适合当前天气"},
            ],
            "missing_items": ["thick jacket"]
        }
    except Exception as e:
        print(f"Error in recommendation service: {e}")
        # Return mock data if model fails
        return {
            "outfits": [
                {"items": wardrobe_items[:2] if len(wardrobe_items) >= 2 else wardrobe_items,
                 "description": "Fallback recommendation due to model error"},
            ],
            "missing_items": [{"category": "accessories", "reason": "Enhance your wardrobe"}]
        }