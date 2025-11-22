from typing import Dict, Any


def analyze_clothing_image(image_path: str) -> Dict[str, Any]:
  try:
    from ml.inference import predict
    result = predict(image_path)
    if isinstance(result.get("season"), list):
      result["season"] = ",".join(result["season"])
    return result
  except Exception as e:
    print(f"ML inference failed: {e}")
    return {
      "category": "top",
      "color": "blue",
      "season": "spring,summer",
      "material": "cotton"
    }
