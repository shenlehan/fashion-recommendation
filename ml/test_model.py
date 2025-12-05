"""
Test script for Qwen2-VL Fashion Model
Run this to verify your ML setup is working correctly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 60)
print("Fashion Recommendation ML Model Test")
print("=" * 60)

print("\n1. Checking dependencies...")
try:
  import torch

  print(f"PyTorch {torch.__version__} OK!")
  print(f"CUDA available: {torch.cuda.is_available()} OK!")
  if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)} OK!")
except ImportError as e:
  print(f"Error: {e} ERROR!")
  sys.exit(1)

try:
  import transformers

  print(f"   ✓ Transformers {transformers.__version__}")
except ImportError as e:
  print(f"   ✗ Error: {e}")
  sys.exit(1)

print("\n2. Loading Qwen2-VL model...")
print("   (This may take a while on first run)")
try:
  from ml.inference import get_model

  model = get_model()
  print("   ✓ Model loaded successfully!")
except Exception as e:
  print(f"   ✗ Error loading model: {e}")
  sys.exit(1)

print("\n3. Testing clothing image analysis...")
# Create a test case with mock data
try:
  # You can replace this with an actual image path
  test_image = "test_clothing.jpg"

  if os.path.exists(test_image):
    result = model.analyze_clothing_image(test_image)
    print(f"   ✓ Analysis successful!")
    print(f"      Category: {result['category']}")
    print(f"      Color: {result['color']}")
    print(f"      Season: {result['season']}")
    print(f"      Material: {result['material']}")
  else:
    print(f"   ⚠ Skipped (no test image found at {test_image})")
    print(f"      To test, place a clothing image at: {test_image}")
except Exception as e:
  print(f"   ✗ Error: {e}")

print("\n4. Testing outfit recommendations...")
try:
  test_wardrobe = [
    {"id": 1, "name": "Blue T-shirt", "category": "top", "color": "blue", "season": "spring,summer",
     "material": "cotton"},
    {"id": 2, "name": "Jeans", "category": "bottom", "color": "blue", "season": "all", "material": "denim"}
  ]

  test_weather = {"temperature": 22, "condition": "Sunny"}
  test_user = {"body_type": "average", "city": "Test City"}

  result = model.generate_outfit_recommendation(
    test_wardrobe,
    test_weather,
    test_user,
    {"occasion": "casual"}
  )

  print(f"   ✓ Recommendation successful!")
  print(f"      Generated {len(result['outfits'])} outfit(s)")
  print(f"      Suggested {len(result['missing_items'])} missing item(s)")

  if result['outfits']:
    print(f"\n   First outfit:")
    print(f"      Items: {len(result['outfits'][0]['items'])}")
    print(f"      Description: {result['outfits'][0]['description'][:100]}...")
except Exception as e:
  print(f"   ✗ Error: {e}")
  import traceback

  traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
print("\nIf all tests passed, your ML module is ready to use!")
print("The backend will automatically use this model when:")
print("  - Uploading clothing images")
print("  - Generating outfit recommendations")
