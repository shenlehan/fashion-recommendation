import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

# 设置 HuggingFace 镜像加速
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image


class FashionQwenModel:
  def __init__(self, model_name: str = None):
    # AUTODL离线加载配置
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    
    # 支持环境变量指定模型路径
    if model_name is None:
      model_name = os.getenv('QWEN_MODEL_PATH', None)
    
    # 检查本地模型路径
    local_model_path = "/root/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots"
    fallback_path = "/root/qwen_model"
    
    if model_name is None:
      # 优先级：/root/qwen_model > snapshot缓存 > 模型名
      from pathlib import Path
      
      if Path(fallback_path).exists() and (Path(fallback_path) / "config.json").exists():
        model_name = fallback_path
        print(f"📂 使用本地完整模型: {model_name}")
      elif Path(local_model_path).exists():
        snapshot_dirs = [d for d in Path(local_model_path).iterdir() if d.is_dir()]
        if snapshot_dirs:
          latest_snapshot = max(snapshot_dirs, key=lambda p: p.stat().st_mtime)
          model_name = str(latest_snapshot)
          print(f"📂 使用缓存snapshot: {model_name}")
        else:
          model_name = "Qwen/Qwen3-VL-8B-Instruct"
          print(f"⚠️  未找到本地模型，使用模型名: {model_name}")
      else:
        model_name = "Qwen/Qwen3-VL-8B-Instruct"
        print(f"⚠️  本地缓存不存在，使用模型名: {model_name}")
    
    self.device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔧 初始化 Qwen3-VL，设备: {self.device}")

    try:
      self.model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        device_map={"":self.device},
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        local_files_only=True,
        code_revision=None,  # 禁用代码版本检查
      )
      
      self.processor = AutoProcessor.from_pretrained(
        model_name,
        trust_remote_code=True,
        local_files_only=True,
      )
      
      if self.device == "cpu":
        self.model = self.model.to(self.device)
      
      print("✅ 模型加载成功！")
      
    except Exception as e:
      print(f"\n❌ 模型加载失败: {e}")
      print(f"\n💡 解决方案：")
      print(f"   1. 下载完整模型:")
      print(f"      cd /root/autodl-tmp/fashion-recommendation/ml")
      print(f"      bash download_qwen_complete.sh")
      print(f"")
      print(f"   2. 或者手动下载:")
      print(f"      export HF_ENDPOINT=https://hf-mirror.com")
      print(f"      huggingface-cli download Qwen/Qwen3-VL-8B-Instruct --local-dir /root/qwen_model")
      print(f"")
      print(f"   3. 设置环境变量(可选):")
      print(f"      export QWEN_MODEL_PATH=/root/qwen_model")
      raise



  def analyze_clothing_image(self, image_path: str) -> Dict[str, Any]:
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "image",
            "image": image_path,
          },
          {
            "type": "text",
            "text": """Analyze this clothing item and return JSON with both Chinese and English descriptions.

RULES:
1. name: Output in CHINESE (中文) - 颜色+材质+类型 (e.g., "黑色棉质T恤")
2. name_en: Output in ENGLISH - color+material+type (e.g., "Black Cotton T-shirt")
3. color: Output in CHINESE (中文) - 主色调中文名 (e.g., "黑色", "白色")
4. color_en: Output in ENGLISH - main color (e.g., "black", "white")
5. material: Output in CHINESE (中文) - 面料中文名 (e.g., "棉", "牛仔布")
6. material_en: Output in ENGLISH - fabric type (e.g., "cotton", "denim")
7. category: Choose ONE based on garment type and layering:
   - underwear: bra, underwear, ...
   - inner_top: T-shirt, tank top, undershirt, ... (thin, fitted, worn next to skin)
   - mid_top: shirt, sweater, hoodie, cardigan, ... (structured tops, can be worn alone)
   - outer_top: jacket, coat, down jacket, windbreaker, ... (outerwear, worn over other layers)
   - bottom: pants, shorts, skirt, ...
   - full_body: dress, jumpsuit, ...
   - shoes: all footwear
   - socks: all socks
   - accessories: bag, hat, scarf, gloves, jewelry, ...
8. season: Select ALL applicable from [spring, summer, fall, winter]

JSON:
{
  "name": "黑色棉质T恤",
  "name_en": "Black Cotton T-shirt",
  "category": "inner_top",
  "color": "黑色",
  "color_en": "black",
  "season": ["spring", "summer", "fall"],
  "material": "棉",
  "material_en": "cotton"
}"""
          }
        ],
      }
    ]

    text = self.processor.apply_chat_template(
      messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = self.processor(
      text=[text],
      images=image_inputs,
      videos=video_inputs,
      padding=True,
      return_tensors="pt",
    )
    inputs = inputs.to(self.device)

    with torch.no_grad():
      generated_ids = self.model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.3,
        top_p=0.9,
      )

    generated_ids_trimmed = [
      out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = self.processor.batch_decode(
      generated_ids_trimmed,
      skip_special_tokens=True,
      clean_up_tokenization_spaces=False
    )[0]

    try:
      output_text = output_text.strip()
      if output_text.startswith("```json"):
        output_text = output_text[7:]
      if output_text.startswith("```"):
        output_text = output_text[3:]
      if output_text.endswith("```"):
        output_text = output_text[:-3]

      result = json.loads(output_text.strip())

      # 将季节列表转换为斜杠分隔的字符串
      if isinstance(result.get("season"), list):
        result["season"] = "/".join(result["season"])

      return result
    except json.JSONDecodeError:
      print(f"Failed to parse JSON: {output_text}")
      return {
        "name": "未知衣物",
        "name_en": "Unknown Item",
        "category": "unknown",
        "color": "未知颜色",
        "color_en": "unknown",
        "season": "spring/summer/fall/winter",
        "material": "未知材质",
        "material_en": "unknown"
      }

  def generate_outfit_recommendation(
      self,
      wardrobe_items: List[Dict[str, Any]],
      weather: Dict[str, Any],
      user_profile: Dict[str, Any],
      preferences: Optional[Dict[str, Any]] = None
  ) -> Dict[str, Any]:
    # 使用英文字段构建纯英文Prompt
    wardrobe_text = "\n".join([
      f"- Item {i + 1}: {item.get('name_en', item.get('name', 'Unknown'))} "
      f"(category: {item.get('category', 'unknown')}, "
      f"color: {item.get('color_en', item.get('color', 'unknown'))}, "
      f"seasons: {item.get('season', 'all')}, "
      f"material: {item.get('material_en', item.get('material', 'unknown'))})"
      for i, item in enumerate(wardrobe_items)
    ])

    weather_text = f"Temperature: {weather.get('temperature', 'N/A')}°C, " \
                   f"Condition: {weather.get('condition', 'N/A')}"

    # 生成用户信息文本
    user_parts = []
    
    # 性别和年龄
    if user_profile.get('gender'):
      gender_map = {'male': 'Male', 'female': 'Female', 'other': 'Other'}
      user_parts.append(f"Gender: {gender_map.get(user_profile['gender'], user_profile['gender'])}")
    if user_profile.get('age'):
      user_parts.append(f"Age: {user_profile['age']}")
    
    # 身高体重和BMI
    if user_profile.get('height') and user_profile.get('weight'):
      height = user_profile['height']
      weight = user_profile['weight']
      # 计算BMI
      bmi = weight / ((height / 100) ** 2)
      user_parts.append(f"Height: {height}cm, Weight: {weight}kg, BMI: {bmi:.1f}")
    
    # 城市
    if user_profile.get('city'):
      user_parts.append(f"Location: {user_profile['city']}")
    
    user_text = ", ".join(user_parts) if user_parts else "No user profile available"

    pref_text = ""
    if preferences:
      pref_parts = []
      if preferences.get('occasion'):
        pref_parts.append(f"Occasion: {preferences['occasion']}")
      if preferences.get('style'):
        pref_parts.append(f"Style: {preferences['style']}")
      if preferences.get('color_preference'):
        pref_parts.append(f"Color tone: {preferences['color_preference']}")
      if pref_parts:
        pref_text = f"\n\nUser Preferences:\n" + "\n".join(pref_parts)

    prompt = f"""Create outfit recommendations based on:

USER: {user_text}
WEATHER: {weather_text}
WARDROBE:
{wardrobe_text}{pref_text}

RULES:
1. Generate 2-3 complete outfits (shoes to outerwear)
2. Use item numbers from wardrobe list
3. Match weather and style preferences
4. Provide styling tips in description
5. IMPORTANT: Output ALL descriptions in CHINESE (中文), including outfit description and missing item reasons

JSON:
{{
  "outfits": [
    {{
      "items": [1, 3, 5],
      "description": "用中文描述完整搭配和穿搭建议"
    }}
  ],
  "missing_items": [
    {{
      "category": "具体单品名称（中文）",
      "reason": "用中文说明为什么需要这个单品"
    }}
  ]
}}"""

    messages = [
      {
        "role": "user",
        "content": [{"type": "text", "text": prompt}]
      }
    ]

    text = self.processor.apply_chat_template(
      messages, tokenize=False, add_generation_prompt=True
    )
    inputs = self.processor(
      text=[text],
      padding=True,
      return_tensors="pt",
    )
    inputs = inputs.to(self.device)

    with torch.no_grad():
      generated_ids = self.model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=1.0,
        top_p=0.9,
        do_sample=True,
        pad_token_id=self.processor.tokenizer.pad_token_id,
      )

    generated_ids_trimmed = [
      out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = self.processor.batch_decode(
      generated_ids_trimmed,
      skip_special_tokens=True,
      clean_up_tokenization_spaces=False
    )[0]

    try:
      output_text = output_text.strip()
      if output_text.startswith("```json"):
        output_text = output_text[7:]
      if output_text.startswith("```"):
        output_text = output_text[3:]
      if output_text.endswith("```"):
        output_text = output_text[:-3]

      result = json.loads(output_text.strip())

      outfits_with_items = []
      for outfit in result.get("outfits", []):
        item_indices = outfit.get("items", [])
        outfit_items = []
        for idx in item_indices:
          if isinstance(idx, int) and 1 <= idx <= len(wardrobe_items):
            outfit_items.append(wardrobe_items[idx - 1])

        outfits_with_items.append({
          "items": outfit_items,
          "description": outfit.get("description", "")
        })

      return {
        "outfits": outfits_with_items,
        "missing_items": result.get("missing_items", [])
      }

    except json.JSONDecodeError:
      print(f"Failed to parse recommendation JSON: {output_text}")
      return {
        "outfits": [],
        "missing_items": []
      }


# Thread-safe singleton pattern
_model_instance: Optional[FashionQwenModel] = None
_model_lock = threading.Lock()
_model_loading = False


def get_model() -> FashionQwenModel:
  """Get or create the model instance (thread-safe singleton)"""
  global _model_instance, _model_loading
  
  # Fast path: model already loaded
  if _model_instance is not None:
    return _model_instance
  
  # Slow path: need to load model
  with _model_lock:
    # Double-check: maybe another thread loaded it while we were waiting
    if _model_instance is not None:
      return _model_instance
    
    # Prevent multiple concurrent loads
    if _model_loading:
      print("Model is already being loaded by another thread, waiting...")
      # Wait for the other thread to finish loading
      while _model_loading:
        import time
        time.sleep(1)
      return _model_instance
    
    # We are the thread that will load the model
    _model_loading = True
    try:
      print("Loading Qwen model (this may take 1-2 minutes)...")
      _model_instance = FashionQwenModel()
      print("Model ready for inference!")
      return _model_instance
    finally:
      _model_loading = False


def predict(image_path: str) -> Dict[str, Any]:
  model = get_model()
  return model.analyze_clothing_image(image_path)


def get_recommendations(
    user: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    weather: Dict[str, Any],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  model = get_model()
  return model.generate_outfit_recommendation(wardrobe, weather, user, preferences)