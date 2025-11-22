import torch
from modelscope import AutoModelForCausalLM, AutoProcessor

print("Starting Qwen3-VL-8B-Instruct download...")
print("This will download approximately 15GB of model files.")
print("Using ModelScope for faster and stable download in China.")
print("Please wait, this may take several minutes depending on your network.\n")

model_id = "Qwen/Qwen3-VL-8B-Instruct"

print(f"Downloading processor for {model_id}...")
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
print("Processor downloaded successfully!\n")

print(f"Downloading model {model_id}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" and torch.cuda.is_bf16_supported() else torch.float16

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=dtype,
    device_map="auto",
    trust_remote_code=True,
)
print("Model downloaded successfully!\n")

print(f"Model loaded on: {device.upper()}")
print(f"Data type: {dtype}")
print("\nDownload & loading complete! The model is ready to use.")