# Fashion Recommendation ML Module

This module uses **Qwen3-VL-8B-Instruct** - the most powerful multimodal Large Language Model in the Qwen series for:
1. **Clothing Image Analysis**: Extract category, color, season, and material from clothing images
2. **Outfit Recommendations**: Generate personalized outfit suggestions based on wardrobe, weather, and preferences

## Model Information

- **Model**: [Qwen/Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)
- **Parameters**: 8 Billion
- **Capabilities**: Enhanced vision + language understanding with improved spatial perception
- **Hardware Requirements**:
  - **GPU**: Recommended (16GB+ VRAM for optimal performance)
  - **CPU**: Supported but slower (32GB+ RAM recommended)

## Installation

### 1. Install Dependencies

```bash
cd ml
pip install -r requirements.txt
```

### 2. Download Model (Automatic)

The model will be automatically downloaded from HuggingFace on first use. This may take some time depending on your internet connection (~15GB download).

### 3. Manual Model Download (Optional)

If you prefer to download manually:

```bash
# Using huggingface-cli
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct
```

## Usage

### Clothing Image Analysis

```python
from ml.inference import predict

# Analyze a clothing image
result = predict("path/to/clothing/image.jpg")

# Result format:
# {
#     "category": "top",
#     "color": "blue",
#     "season": "spring,summer",
#     "material": "cotton"
# }
```

### Outfit Recommendations

```python
from ml.inference import get_recommendations

# Generate recommendations
result = get_recommendations(
    user={
        "body_type": "athletic",
        "city": "New York"
    },
    wardrobe=[
        {"id": 1, "name": "Blue T-shirt", "category": "top", "color": "blue", "season": "spring,summer", "material": "cotton"},
        {"id": 2, "name": "Jeans", "category": "bottom", "color": "blue", "season": "all", "material": "denim"}
    ],
    weather={
        "temperature": 22,
        "condition": "Sunny"
    },
    preferences={
        "occasion": "casual",
        "style": "minimalist",
        "color_preference": "blue,white"
    }
)

# Result format:
# {
#     "outfits": [
#         {
#             "items": [wardrobe_item1, wardrobe_item2],
#             "description": "Perfect casual look for sunny weather..."
#         }
#     ],
#     "missing_items": [
#         {
#             "category": "shoes",
#             "reason": "Would complete the casual outfit"
#         }
#     ]
# }
```

## Model Performance

### GPU Performance
- **First Load**: ~30 seconds (model loading)
- **Image Analysis**: ~2-5 seconds per image
- **Recommendation Generation**: ~5-10 seconds

### CPU Performance
- **First Load**: ~60 seconds (model loading)
- **Image Analysis**: ~15-30 seconds per image
- **Recommendation Generation**: ~30-60 seconds

## Integration with Backend

The ML module is automatically integrated with the backend services:

1. **Image Service** (`app/services/image_service.py`):
   - Calls `ml.inference.predict()` for clothing analysis
   - Automatically used when uploading clothing items

2. **Recommendation Service** (`app/services/recommendation_service.py`):
   - Calls `recommendation.logic.get_recommendations()`
   - Which internally uses `ml.inference.get_recommendations()`

## Model Behavior

### Image Analysis
The model is prompted to identify:
- **Category**: top, bottom, dress, outerwear, shoes, accessories
- **Color**: Primary color name
- **Season**: Suitable seasons (spring, summer, fall, winter)
- **Material**: Fabric type (cotton, denim, wool, etc.)

### Recommendations
The model considers:
- Available wardrobe items
- Current weather conditions
- User's body type and location
- User preferences (occasion, style, color)
- Fashion compatibility and styling rules

## Troubleshooting

### Out of Memory (OOM) Error

If you get CUDA OOM errors:

```python
# Option 1: Use CPU instead
export CUDA_VISIBLE_DEVICES=""

# Option 2: Reduce batch size / Use model offloading
# The model is already configured for auto device mapping
```

### Slow Performance

- Ensure you're using GPU if available
- First inference is always slow due to model loading
- Subsequent inferences use the cached model instance

### Model Not Found

If download fails:
```bash
# Check HuggingFace connection
huggingface-cli whoami

# Manually download
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct
```

## Alternative Models

If Qwen3-VL-8B is too large, you can modify `inference.py` to use:
- **Qwen3-VL-2B-Instruct**: Smaller, faster, less accurate
- **Qwen3-VL-4B-Instruct**: Balanced option
- **Qwen2.5-VL-7B-Instruct**: Previous generation

Change the model name in `FashionQwenModel.__init__()`:
```python
def __init__(self, model_name: str = "Qwen/Qwen3-VL-4B-Instruct"):
```

## API Access (Alternative to Local Model)

Instead of running the model locally, you can use Qwen API for faster inference:

### Get API Key:
1. **Alibaba Cloud DashScope** (Official): https://www.alibabacloud.com/help/en/model-studio/get-api-key
2. **Qwen.ai Platform**: https://qwen.ai/apiplatform
3. **OpenRouter** (Free Tier): https://openrouter.ai

Set environment variable:
```bash
export QWEN_API_KEY="your-api-key-here"
```

## License

This module uses the Qwen3-VL model which is licensed under Apache 2.0.
