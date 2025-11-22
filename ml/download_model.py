import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

print("Starting Qwen3-VL-8B-Instruct download...")
print("This will download approximately 15GB of model files.")
print("Please wait, this may take several minutes depending on your internet connection.\n")

model_name = "Qwen/Qwen3-VL-8B-Instruct"

print(f"Downloading processor for {model_name}...")
processor = AutoProcessor.from_pretrained(model_name)
print("Processor downloaded successfully!")

print(f"\nDownloading model {model_name}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

model = AutoModelForImageTextToText.from_pretrained(
    model_name,
    torch_dtype=dtype,
    device_map="auto" if device == "cuda" else None
)
print("Model downloaded successfully!")

print(f"\nModel will be used on: {device}")
print(f"Data type: {dtype}")
print("\nDownload complete! The model is ready to use.")
