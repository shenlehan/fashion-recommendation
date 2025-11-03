# ML Model Setup Guide - Qwen2-VL Integration

This guide will help you set up the Qwen2-VL-7B multimodal LLM for fashion image analysis and recommendations.

## 📋 Prerequisites

- **Python 3.8+**
- **16GB+ RAM** (32GB recommended for CPU usage)
- **GPU with 16GB+ VRAM** (optional but highly recommended)
- **50GB free disk space** (for model download)

## 🚀 Installation Steps

### Step 1: Install ML Dependencies

```bash
cd backend/ml
pip install -r requirements.txt
```

This will install:
- PyTorch (with CUDA support if available)
- Transformers
- Qwen-VL utilities
- Other required packages

### Step 2: Verify Installation

Run the test script to verify everything is working:

```bash
cd backend
python -m ml.test_model
```

**Expected output**:
- ✓ PyTorch and dependencies loaded
- ✓ Model downloaded and loaded (first run takes ~5-10 minutes)
- ✓ Image analysis test passed
- ✓ Recommendation test passed

### Step 3: Update Backend Requirements

Add ML dependencies to main backend requirements:

```bash
cd backend
cat ml/requirements.txt >> requirements.txt
pip install -r requirements.txt
```

## 🎯 How It Works

### 1. Image Upload Flow

```
User uploads clothing image
         ↓
Backend receives image → Saves to uploads/
         ↓
backend/app/routes/clothes.py calls analyze_clothing_image()
         ↓
backend/app/services/image_service.py calls ml.inference.predict()
         ↓
ml/inference.py: FashionQwenModel.analyze_clothing_image()
         ↓
Qwen2-VL analyzes image → Returns: {category, color, season, material}
         ↓
Backend saves item to database with extracted attributes
```

### 2. Recommendation Flow

```
User requests recommendations
         ↓
backend/app/routes/recommendation.py receives request
         ↓
Fetches: user profile, wardrobe items, weather, preferences
         ↓
backend/app/services/recommendation_service.py calls recommendation.logic
         ↓
recommendation/logic.py calls ml.inference.get_recommendations()
         ↓
Qwen2-VL generates outfit combinations and missing items analysis
         ↓
Returns structured recommendations to frontend
```

## 🔧 Configuration

### Using CPU Only

If you don't have a GPU or want to test on CPU:

```bash
# Set environment variable
export CUDA_VISIBLE_DEVICES=""

# Then start backend
uvicorn app.main:app --reload
```

### Using Custom Model

To use a different model (e.g., smaller 2B version):

Edit `backend/ml/inference.py`:
```python
class FashionQwenModel:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):  # Changed from 7B to 2B
        ...
```

## 📊 Performance Benchmarks

### GPU (NVIDIA RTX 3090 / 4090)
- **First load**: ~30s
- **Image analysis**: 2-5s per image
- **Recommendations**: 5-10s per request

### CPU (Modern x86_64)
- **First load**: ~60s
- **Image analysis**: 15-30s per image
- **Recommendations**: 30-60s per request

## 🧪 Testing

### Test Image Analysis

```python
from ml.inference import predict

result = predict("path/to/clothing/image.jpg")
print(result)
# {
#     "category": "top",
#     "color": "blue",
#     "season": "spring,summer",
#     "material": "cotton"
# }
```

### Test Recommendations

```python
from ml.inference import get_recommendations

result = get_recommendations(
    user={"body_type": "athletic", "city": "NYC"},
    wardrobe=[
        {"id": 1, "name": "T-shirt", "category": "top", ...},
        {"id": 2, "name": "Jeans", "category": "bottom", ...}
    ],
    weather={"temperature": 22, "condition": "Sunny"},
    preferences={"occasion": "casual", "style": "minimalist"}
)
print(result)
```

### Run Full Backend with ML

```bash
cd backend
uvicorn app.main:app --reload
```

Then test via the frontend:
1. Upload a clothing item → Should extract attributes automatically
2. Click "Get Recommendations" → Should generate AI-powered suggestions

## ❗ Troubleshooting

### Problem: OOM (Out of Memory) Error

**Solution**:
```bash
# Use CPU
export CUDA_VISIBLE_DEVICES=""

# Or use smaller model
# Edit ml/inference.py and change to Qwen2-VL-2B-Instruct
```

### Problem: Model Download Fails

**Solution**:
```bash
# Check connection
ping huggingface.co

# Manual download
huggingface-cli login  # if needed
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct
```

### Problem: Import Error

**Solution**:
```bash
# Reinstall dependencies
cd backend/ml
pip install --upgrade -r requirements.txt
```

### Problem: Slow Performance

**Causes**:
- Running on CPU (expected)
- First run (model loading + caching)
- Swapping memory (need more RAM)

**Solutions**:
- Use GPU if available
- Increase system RAM
- Use smaller 2B model
- Reduce concurrent requests

## 🔄 Fallback Behavior

If the ML model fails to load or errors occur:
- Image service returns **mock data** (category, color, etc.)
- Recommendation service returns **basic suggestions**
- Backend continues to function normally

This ensures the app works even without GPU or during model loading.

## 📚 Advanced Usage

### Custom Prompts

You can modify the prompts in `ml/inference.py`:
- `analyze_clothing_image()` - Image analysis prompt
- `generate_outfit_recommendation()` - Recommendation prompt

### Model Caching

The model uses lazy loading with global instance caching:
```python
# First call: loads model (~30s)
predict("image1.jpg")

# Subsequent calls: uses cached model (~3s)
predict("image2.jpg")
predict("image3.jpg")
```

### Batch Processing

For multiple images, the model stays loaded:
```python
for image in image_list:
    result = predict(image)  # Fast after first call
```

## 🎓 Model Information

- **Name**: Qwen2-VL-7B-Instruct
- **Developer**: Alibaba Cloud
- **Type**: Multimodal (Vision + Language)
- **Parameters**: 7 Billion
- **License**: Apache 2.0
- **HuggingFace**: https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct

## 🚦 Next Steps

1. ✅ Install dependencies: `pip install -r backend/ml/requirements.txt`
2. ✅ Run test script: `python -m ml.test_model`
3. ✅ Start backend: `uvicorn app.main:app --reload`
4. ✅ Test via frontend: Upload images and get recommendations!

If you encounter any issues, check the troubleshooting section or open an issue on GitHub.
