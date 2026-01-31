from typing import Dict, Any
import traceback


def analyze_clothing_image(image_path: str) -> Dict[str, Any]:
  try:
    print(f"\n{'='*60}")
    print(f"开始分析衣朏图片: {image_path}")
    print(f"{'='*60}")
    
    from ml.inference import predict
    result = predict(image_path)
    
    if isinstance(result.get("season"), list):
      result["season"] = ",".join(result["season"])
    
    print(f"\n✅ 分析成功: {result}")
    print(f"{'='*60}\n")
    return result
    
  except Exception as e:
    error_type = type(e).__name__
    print(f"\n{'='*60}")
    print(f"❌ ML 推理失败")
    print(f"{'='*60}")
    print(f"错误类型: {error_type}")
    print(f"错误信息: {str(e)}")
    print(f"\n详细堆栈:")
    print(traceback.format_exc())
    print(f"{'='*60}\n")
    
    print("⚠️  返回默认值，所有衣朏将显示相同标签")
    return {
      "category": "top",
      "color": "blue",
      "season": "spring,summer",
      "material": "cotton"
    }
