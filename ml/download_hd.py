import os
# 强制开启镜像加速
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

print("🚀 开始通过镜像下载放大模型...")
try:
    # 下载 sd-x2-latent-upscaler (约 1.6GB)
    snapshot_download(
        repo_id="stabilityai/sd-x2-latent-upscaler",
        ignore_patterns=["*.bin"],  # 只下载 safetensors
        resume_download=True        # 支持断点续传
    )
    print("✅ 下载成功！")
except Exception as e:
    print(f"❌ 下载失败: {e}")
    exit(1) # 失败时返回错误码，让外部循环知道