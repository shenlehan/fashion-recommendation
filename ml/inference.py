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
7. category: Classify tops by SLEEVES FIRST, then by structure:
   
   DECISION TREE:
   Step 1 - Check sleeves:
   - NO sleeves (tank/camisole/vest) → inner_top
   - HAS sleeves → Continue to Step 2
   
   Step 2 - Check structure:
   - Thin/casual (T-shirt, thin top) → inner_top
   - Structured/standalone (shirt, sweater, polo, hoodie) → mid_top
   - Outerwear (jacket, coat, blazer) → outer_top
   
   EXAMPLES:
   - inner_top: T-shirt, tank top, camisole, sleeveless shirt
   - mid_top: Dress shirt, sweater, polo, hoodie, cardigan
   - outer_top: Jacket, coat, blazer, windbreaker
   
   OTHER CATEGORIES:
   - underwear: Undergarments (bra, underwear)
   - bottom: Pants, shorts, skirts
   - full_body: One-piece garments (dress, jumpsuit, romper)
   - shoes: All footwear
   - socks: All socks and hosiery
   - accessories: Bags, hats, scarves, gloves, jewelry

8. season: Select ALL applicable from [spring, summer, fall, winter]
   - Thin/short items: [spring, summer, fall]
   - Thick/warm items: [fall, winter]
   - Mid-weight: [spring, fall, winter] or [spring, summer, fall]

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
    # 按类别分组衣物（减少LLM搜索成本）
    categorized = {}
    for item in wardrobe_items:
      category = item.get('category', 'unknown')
      if category not in categorized:
        categorized[category] = []
      categorized[category].append(item)
    
    # 构建分类展示的衣物列表
    wardrobe_sections = []
    item_counter = 0
    
    # 定义类别顺序和标签
    category_order = [
      ('inner_top', 'INNER LAYER'),
      ('mid_top', 'MID LAYER'),
      ('outer_top', 'OUTER LAYER'),
      ('bottom', 'BOTTOM'),
      ('full_body', 'FULL BODY'),
      ('shoes', 'SHOES'),
      ('socks', 'SOCKS'),
      ('accessories', 'ACCESSORIES'),
      ('underwear', 'UNDERWEAR')
    ]
    
    for category_key, category_label in category_order:
      items = categorized.get(category_key, [])
      if items:
        items_text = []
        for item in items:
          item_counter += 1
          items_text.append(
            f"{item_counter}. {item.get('name_en', 'Unknown')} "
            f"({item.get('color_en', 'unknown')}, {item.get('material_en', 'unknown')})"
          )
        wardrobe_sections.append(f"{category_label}:\n" + "\n".join(items_text))
    
    wardrobe_text = "\n\n".join(wardrobe_sections)

    # 构建天气信息文本（使用正确的字段名）
    temp_max = weather.get('temp_max', 'N/A')
    temp_min = weather.get('temp_min', 'N/A')
    condition = weather.get('condition', 'N/A')
    humidity = weather.get('humidity', 'N/A')
    wind_speed = weather.get('wind_speed', 'N/A')
    rain_prob = weather.get('rain_prob', 0)
    
    weather_parts = [f"Temperature: {temp_min}~{temp_max}°C"]
    weather_parts.append(f"Condition: {condition}")
    
    if humidity != 'N/A':
      weather_parts.append(f"Humidity: {humidity}%")
    if wind_speed != 'N/A':
      weather_parts.append(f"Wind: {wind_speed}m/s")
    if rain_prob > 0:
      weather_parts.append(f"Rain probability: {rain_prob}%")
    
    weather_text = ", ".join(weather_parts)

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
1. Generate 2-3 complete outfits
2. Use item numbers from wardrobe list ONLY
3. SELECTION RULES:
   - TOPS: Must include at least one (can select multiple from different layers)
   - BOTTOM: Exactly one if available
   - SHOES: Exactly one if available
   - ACCESSORIES: Optional
   - FULL BODY: Replaces top and bottom
4. For missing_items: Suggest SPECIFIC items with colors and styles, NOT generic categories

JSON:
{{
  "outfits": [
    {{
      "items": [1, 3, 5, 8],
      "description": "<outfit description in Chinese>"
    }}
  ],
  "missing_items": [
    {{
      "category": "<item category in Chinese>",
      "reason": "<reason in Chinese>"
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

  def adjust_outfit_with_conversation(
      self,
      adjustment_request: str,
      wardrobe_items: List[Dict[str, Any]],
      weather: Dict[str, Any],
      user_profile: Dict[str, Any],
      preferences: Optional[Dict[str, Any]],
      conversation_history: List[Dict[str, Any]],
      current_outfit: List[int]
  ) -> Dict[str, Any]:
    """根据对话历史调整穿搭方案"""
    # 按类别分组衣物
    categorized = {}
    for item in wardrobe_items:
      category = item.get('category', 'unknown')
      if category not in categorized:
        categorized[category] = []
      categorized[category].append(item)
    
    # 构建分类展示的衣物列表
    wardrobe_sections = []
    item_counter = 0
    
    category_order = [
      ('inner_top', 'INNER LAYER'),
      ('mid_top', 'MID LAYER'),
      ('outer_top', 'OUTER LAYER'),
      ('bottom', 'BOTTOM'),
      ('full_body', 'FULL BODY'),
      ('shoes', 'SHOES'),
      ('socks', 'SOCKS'),
      ('accessories', 'ACCESSORIES'),
      ('underwear', 'UNDERWEAR')
    ]
    
    for category_key, category_label in category_order:
      items = categorized.get(category_key, [])
      if items:
        items_text = []
        for item in items:
          item_counter += 1
          items_text.append(
            f"{item_counter}. {item.get('name_en', 'Unknown')} "
            f"({item.get('color_en', 'unknown')}, {item.get('material_en', 'unknown')})"
          )
        wardrobe_sections.append(f"{category_label}:\n" + "\n".join(items_text))
    
    wardrobe_text = "\n\n".join(wardrobe_sections)

    # 构建天气信息
    temp_max = weather.get('temp_max', 'N/A')
    temp_min = weather.get('temp_min', 'N/A')
    condition = weather.get('condition', 'N/A')
    humidity = weather.get('humidity', 'N/A')
    wind_speed = weather.get('wind_speed', 'N/A')
    rain_prob = weather.get('rain_prob', 0)
    
    weather_parts = [f"Temperature: {temp_min}~{temp_max}°C"]
    weather_parts.append(f"Condition: {condition}")
    
    if humidity != 'N/A':
      weather_parts.append(f"Humidity: {humidity}%")
    if wind_speed != 'N/A':
      weather_parts.append(f"Wind: {wind_speed}m/s")
    if rain_prob > 0:
      weather_parts.append(f"Rain probability: {rain_prob}%")
    
    weather_text = ", ".join(weather_parts)

    # 生成用户信息
    user_parts = []
    if user_profile.get('gender'):
      gender_map = {'male': 'Male', 'female': 'Female', 'other': 'Other'}
      user_parts.append(f"Gender: {gender_map.get(user_profile['gender'], user_profile['gender'])}")
    if user_profile.get('age'):
      user_parts.append(f"Age: {user_profile['age']}")
    if user_profile.get('height') and user_profile.get('weight'):
      height = user_profile['height']
      weight = user_profile['weight']
      bmi = weight / ((height / 100) ** 2)
      user_parts.append(f"Height: {height}cm, Weight: {weight}kg, BMI: {bmi:.1f}")
    if user_profile.get('city'):
      user_parts.append(f"Location: {user_profile['city']}")
    
    user_text = ", ".join(user_parts) if user_parts else "No user profile available"

    # 构建用户偏好信息
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
        pref_text = "\nUSER PREFERENCES: " + ", ".join(pref_parts)

    # 构建当前穿搭信息
    current_outfit_items = []
    for item_id in current_outfit:
      for item in wardrobe_items:
        if item.get('id') == item_id:
          current_outfit_items.append(item)
          break
    
    if current_outfit_items:
      current_outfit_text = "CURRENT OUTFIT:\n" + "\n".join([
        f"- {item.get('name_en', 'Unknown')} ({item.get('color_en', 'unknown')}, {item.get('material_en', 'unknown')})"
        for item in current_outfit_items
      ])
    else:
      current_outfit_text = "CURRENT OUTFIT: None"

    # 构建对话历史文本
    conversation_text = ""
    if conversation_history:
      history_lines = []
      for msg in conversation_history[-5:]:  # 只保留最近5轮
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'user':
          history_lines.append(f"User: {content}")
        elif role == 'assistant':
          history_lines.append(f"Assistant: {content}")
      
      if history_lines:
        conversation_text = "\n\nCONVERSATION HISTORY:\n" + "\n".join(history_lines)

    prompt = f"""Adjust the outfit recommendation based on user feedback:

USER: {user_text}{pref_text}
WEATHER: {weather_text}
{current_outfit_text}
WARDROBE:
{wardrobe_text}{conversation_text}

USER REQUEST (translate to English if needed): {adjustment_request}

CRITICAL RULES:
1. PRESERVATION PRIORITY:
   - If user only mentions changing ONE category, KEEP ALL OTHER categories unchanged
   - If user says change the jacket, keep bottom, shoes, and accessories from current outfit
   - If user says change dress to pants, replace ONLY the dress/full_body, keep shoes and accessories
   - NEVER remove shoes unless explicitly requested

2. MANDATORY CATEGORIES (must include in final outfit):
   - BOTTOM or FULL_BODY: Exactly one (required)
   - SHOES: Exactly one (ALWAYS required unless user says remove shoes)
   - TOPS: At least one if not using full_body

3. EXAMPLE:
   Current: [T-shirt(1), Dress(10), Sneakers(15)]
   Request: Change dress to pants
   Result: [T-shirt(1), Jeans(12), Sneakers(15)] - Shoes preserved

4. Return 1-2 adjusted outfits
5. Description MUST be in Chinese

JSON:
{{
  "outfits": [
    {{
      "items": [1, 3, 5, 8],
      "description": "<Chinese description explaining what changed and why>"
    }}
  ],
  "missing_items": []
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
        temperature=0.8,
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
        
        # ✅ 关键修复：验证并修复缺失的必需品类
        outfit_items = self._ensure_required_categories(
          outfit_items, current_outfit, wardrobe_items
        )

        outfits_with_items.append({
          "items": outfit_items,
          "description": outfit.get("description", "")
        })

      return {
        "outfits": outfits_with_items,
        "missing_items": result.get("missing_items", [])
      }

    except json.JSONDecodeError:
      print(f"Failed to parse adjustment JSON: {output_text}")
      return {
        "outfits": [],
        "missing_items": []
      }

  def _ensure_required_categories(
      self,
      outfit_items: List[Dict[str, Any]],
      current_outfit_ids: List[int],
      wardrobe_items: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """确保调整后的方案包含必需品类（特别是鞋子）"""
    # 统计当前方案的类别
    categories_present = set(item.get('category') for item in outfit_items)
    
    # 检查是否缺少鞋子
    has_shoes = 'shoes' in categories_present
    has_bottom = 'bottom' in categories_present or 'full_body' in categories_present
    
    # 如果缺少关键品类，从原方案中补回
    if not has_shoes or not has_bottom:
      # 构建原方案的衣物字典
      current_items_map = {}
      for item_id in current_outfit_ids:
        for item in wardrobe_items:
          if item.get('id') == item_id:
            current_items_map[item.get('category')] = item
            break
      
      # 补回缺失的鞋子
      if not has_shoes and 'shoes' in current_items_map:
        outfit_items.append(current_items_map['shoes'])
      
      # 补回缺失的下装（如果原方案有）
      if not has_bottom:
        if 'bottom' in current_items_map:
          outfit_items.append(current_items_map['bottom'])
        elif 'full_body' in current_items_map:
          outfit_items.append(current_items_map['full_body'])
    
    return outfit_items


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
  """基于对话历史调整穿搭方案"""
  model = get_model()
  return model.adjust_outfit_with_conversation(
    adjustment_request=adjustment_request,
    wardrobe_items=wardrobe,
    weather=weather,
    user_profile=user,
    preferences=preferences,
    conversation_history=conversation_history,
    current_outfit=current_outfit
  )