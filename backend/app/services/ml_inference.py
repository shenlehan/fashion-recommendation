from typing import Any, Dict
import joblib
import numpy as np


class MLInference:
  def __init__(self, model_path: str):
    self.model = joblib.load(model_path)

  def predict(self, features: np.ndarray) -> Any:
    return self.model.predict(features)

  def prepare_features(self, user_data: Dict[str, Any]) -> np.ndarray:
    features = np.array([
      user_data.get('body_type', 0),
      user_data.get('weather_condition', 0),
      user_data.get('wardrobe_items_count', 0),
    ])
    return features
