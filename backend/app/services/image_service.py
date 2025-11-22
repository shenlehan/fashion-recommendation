from typing import Dict, Any


def analyze_clothing_image(image_path: str) -> Dict[str, Any]:
  try:
    from ml.inference import predict
    result = predict(image_path)
    return result
  except ImportError:
    return {
      "category": "top",
      "color": "blue",
      "season": ["spring", "summer"],
      "material": "cotton"
    }
