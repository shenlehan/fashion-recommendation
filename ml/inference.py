import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image


class FashionQwenModel:
  def __init__(self, model_name: str = "Qwen/Qwen3-VL-8B-Instruct"):
    self.device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Initializing Qwen3-VL on device: {self.device}")

    self.model = AutoModelForImageTextToText.from_pretrained(
      model_name,
      torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
      device_map="auto" if self.device == "cuda" else None
    )
    self.processor = AutoProcessor.from_pretrained(model_name)

    if self.device == "cpu":
      self.model = self.model.to(self.device)

    print("Model loaded successfully!")

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
            "text": """Analyze this clothing item and provide the following information in JSON format:
{
  "category": "top/bottom/dress/outerwear/shoes/accessories",
  "color": "primary color name",
  "season": ["spring", "summer", "fall", "winter"] (list all suitable seasons),
  "material": "fabric type (e.g., cotton, denim, wool, polyester, silk)"
}

Only respond with the JSON object, nothing else."""
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

      if isinstance(result.get("season"), list):
        result["season"] = ",".join(result["season"])

      return result
    except json.JSONDecodeError:
      print(f"Failed to parse JSON: {output_text}")
      return {
        "category": "unknown",
        "color": "unknown",
        "season": "spring,summer,fall,winter",
        "material": "unknown"
      }

  def generate_outfit_recommendation(
      self,
      wardrobe_items: List[Dict[str, Any]],
      weather: Dict[str, Any],
      user_profile: Dict[str, Any],
      preferences: Optional[Dict[str, Any]] = None
  ) -> Dict[str, Any]:
    wardrobe_text = "\n".join([
      f"- Item {i + 1}: {item.get('name', 'Unknown')} "
      f"({item.get('category', 'unknown')}, {item.get('color', 'unknown')}, "
      f"seasons: {item.get('season', 'all')}, material: {item.get('material', 'unknown')})"
      for i, item in enumerate(wardrobe_items)
    ])

    weather_text = f"Temperature: {weather.get('temperature', 'N/A')}°C, " \
                   f"Condition: {weather.get('condition', 'N/A')}"

    user_text = f"Body type: {user_profile.get('body_type', 'average')}, " \
                f"City: {user_profile.get('city', 'Unknown')}"

    pref_text = ""
    if preferences:
      pref_parts = []
      if preferences.get('occasion'):
        pref_parts.append(f"Occasion: {preferences['occasion']}")
      if preferences.get('style'):
        pref_parts.append(f"Style: {preferences['style']}")
      if preferences.get('color_preference'):
        pref_parts.append(f"Preferred colors: {preferences['color_preference']}")
      if pref_parts:
        pref_text = f"\n\nUser Preferences:\n" + "\n".join(pref_parts)

    prompt = f"""You are a professional fashion stylist. Based on the following information, create outfit recommendations:

User Profile:
{user_text}

Current Weather:
{weather_text}

Available Wardrobe Items:
{wardrobe_text}{pref_text}

Please provide:
1. 2-3 complete outfit combinations using the available items (reference items by their numbers)
2. Analysis of missing items that would enhance the wardrobe
3. Brief explanation for each outfit

Respond in this JSON format:
{{
  "outfits": [
    {{
      "items": [list of item numbers from the wardrobe],
      "description": "brief description of the outfit and why it works"
    }}
  ],
  "missing_items": [
    {{
      "category": "item type",
      "reason": "why this item would be useful"
    }}
  ]
}}

Only respond with the JSON object."""

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
        temperature=0.7,
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


_model_instance: Optional[FashionQwenModel] = None


def get_model() -> FashionQwenModel:
  global _model_instance
  if _model_instance is None:
    _model_instance = FashionQwenModel()
  return _model_instance


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
