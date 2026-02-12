from typing import Dict, List, Any, Optional
from ml.inference import get_recommendations as ml_get_recommendations
from ml.inference import adjust_recommendations_with_conversation as ml_adjust_recommendations


def get_recommendations(
    user: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  return ml_get_recommendations(user, wardrobe, weather, preferences)


def adjust_recommendations_with_conversation(
    session_id: str,
    adjustment_request: str,
    user: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]],
    current_outfit: List[int]
) -> Dict[str, Any]:
  return ml_adjust_recommendations(
    session_id=session_id,
    adjustment_request=adjustment_request,
    user=user,
    wardrobe=wardrobe,
    weather=weather,
    preferences=preferences,
    conversation_history=conversation_history,
    current_outfit=current_outfit
  )
