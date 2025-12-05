from modelscope import pipeline
import torch

print("Loading Qwen3-VL-8B-Instruct...")

pipe = pipeline(
    task="image-text-to-text",
    model="Qwen/Qwen3-VL-8B-Instruct",
    model_revision="master",
    device="cuda" if torch.cuda.is_available() else "cpu",
    trust_remote_code=True
)

print("Successfully load model on", pipe.model.device)