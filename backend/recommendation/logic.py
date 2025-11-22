from typing import Dict, List, Any, Optional
from ml.inference import get_recommendations as ml_get_recommendations


def get_recommendations(
    user: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  return ml_get_recommendations(user, wardrobe, weather, preferences)
