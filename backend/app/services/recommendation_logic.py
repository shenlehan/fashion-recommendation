"""
Recommendation Logic
Wraps ML model inference for outfit recommendations
"""
from typing import Dict, List, Any, Optional
from ml.inference import get_recommendations as ml_get_recommendations


def get_recommendations(
    user: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate outfit recommendations using Qwen2-VL
    
    Args:
        user: User profile information
        wardrobe: List of wardrobe items
        weather: Weather data
        preferences: Optional user preferences
        
    Returns:
        Dict with outfit recommendations and missing items analysis
    """
    return ml_get_recommendations(user, wardrobe, weather, preferences)
