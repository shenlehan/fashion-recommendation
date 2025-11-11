"""
Test script for LoRA fine-tuned model
Tests the fine-tuned model on sample fashion tasks
"""
import torch
from pathlib import Path
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from peft import PeftModel


def load_finetuned_model(adapter_path: str):
    """Load base model with LoRA adapters"""
    print("🔧 Loading fine-tuned model...")

    base_model_name = "Qwen/Qwen2-VL-7B-Instruct"

    # Load base model
    print("  Loading base model...")
    base_model = Qwen2VLForConditionalGeneration.from_pretrained(
        base_model_name,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # Load LoRA adapters
    print(f"  Loading LoRA adapters from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()

    # Load processor
    processor = AutoProcessor.from_pretrained(
        base_model_name,
        trust_remote_code=True
    )

    print("✓ Model loaded successfully\n")
    return model, processor


def test_clothing_analysis(model, processor):
    """Test clothing analysis task"""
    print("=" * 60)
    print("Test 1: Clothing Analysis")
    print("=" * 60)

    prompt = """<|im_start|>system
You are a professional fashion stylist and wardrobe consultant. Provide detailed, personalized fashion advice based on user preferences, body types, and weather conditions.<|im_end|>
<|im_start|>user
Analyze this clothing item and provide detailed information about its category, color, season suitability, and material. The item is a navy blue cotton shirt with buttons.<|im_end|>
<|im_start|>assistant
"""

    inputs = processor(text=prompt, return_tensors="pt").to(model.device)

    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

    response = processor.decode(outputs[0], skip_special_tokens=False)

    # Extract assistant response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]
        response = response.split("<|im_end|>")[0].strip()

    print(f"\n📝 Model Response:\n{response}\n")


def test_outfit_recommendation(model, processor):
    """Test outfit recommendation task"""
    print("=" * 60)
    print("Test 2: Outfit Recommendation")
    print("=" * 60)

    prompt = """<|im_start|>system
You are a professional fashion stylist and wardrobe consultant. Provide detailed, personalized fashion advice based on user preferences, body types, and weather conditions.<|im_end|>
<|im_start|>user
Based on the following information, suggest a complete outfit:

User Profile:
- Body Type: athletic
- City: New York

Wardrobe:
- White T-shirt (cotton, casual)
- Blue Jeans (denim, casual)
- Black Leather Jacket (leather, fall/winter)
- Sneakers (athletic, all seasons)

Weather: 15°C, partly cloudy

Preferences:
- Occasion: casual outing
- Style: streetwear
- Color Preference: neutral<|im_end|>
<|im_start|>assistant
"""

    inputs = processor(text=prompt, return_tensors="pt").to(model.device)

    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

    response = processor.decode(outputs[0], skip_special_tokens=False)

    # Extract assistant response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]
        response = response.split("<|im_end|>")[0].strip()

    print(f"\n📝 Model Response:\n{response}\n")


def test_style_advice(model, processor):
    """Test style advice task"""
    print("=" * 60)
    print("Test 3: Style Advice")
    print("=" * 60)

    prompt = """<|im_start|>system
You are a professional fashion stylist and wardrobe consultant. Provide detailed, personalized fashion advice based on user preferences, body types, and weather conditions.<|im_end|>
<|im_start|>user
Provide style advice for an athletic body type in business casual settings.<|im_end|>
<|im_start|>assistant
"""

    inputs = processor(text=prompt, return_tensors="pt").to(model.device)

    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=384,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

    response = processor.decode(outputs[0], skip_special_tokens=False)

    # Extract assistant response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]
        response = response.split("<|im_end|>")[0].strip()

    print(f"\n📝 Model Response:\n{response}\n")


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("🧪 Testing LoRA Fine-tuned Fashion Model")
    print("=" * 60 + "\n")

    # Find the latest adapter
    adapter_base = Path(__file__).parent.parent / "lora_adapters"

    # Check for final model first
    final_adapter = adapter_base / "final"
    if final_adapter.exists():
        adapter_path = final_adapter
    else:
        # Find latest checkpoint
        checkpoints = sorted(adapter_base.glob("checkpoint-*"))
        if not checkpoints:
            print(f"❌ No LoRA adapters found in {adapter_base}")
            print("💡 Please train the model first: python finetune/train_lora.py")
            return

        adapter_path = checkpoints[-1]

    print(f"📁 Using adapter: {adapter_path}\n")

    # Load model
    model, processor = load_finetuned_model(str(adapter_path))

    # Run tests
    test_clothing_analysis(model, processor)
    test_outfit_recommendation(model, processor)
    test_style_advice(model, processor)

    print("=" * 60)
    print("✅ Testing completed!")
    print("=" * 60)
    print("\n💡 If the results look good, update inference.py to use these adapters.")


if __name__ == "__main__":
    main()
