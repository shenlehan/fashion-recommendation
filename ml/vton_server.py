import os
# 1. 强制镜像加速 (防止重启后环境变量丢失)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from PIL import Image, ImageFilter
import sys
import io
import uvicorn
import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from contextlib import asynccontextmanager
from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation
from diffusers import StableDiffusionLatentUpscalePipeline  # <--- 高清核心组件

# --- 路径配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
catvton_path = os.path.join(current_dir, "CatVTON")
sys.path.append(catvton_path)

try:
    from model.pipeline import CatVTONPipeline
    print("✅ 成功导入 CatVTONPipeline")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# --- 全局变量 ---
pipeline = None
upscaler = None     # <--- 放大模型
seg_processor = None
seg_model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

# --- 辅助函数：自动 Mask ---
def get_accurate_mask(image, category):
    global seg_processor, seg_model, device
    inputs = seg_processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = seg_model(**inputs)
        logits = outputs.logits
    
    upsampled_logits = torch.nn.functional.interpolate(
        logits, size=image.size[::-1], mode="bilinear", align_corners=False,
    )
    pred_seg = upsampled_logits.argmax(dim=1)[0]
    mask_tensor = torch.zeros_like(pred_seg, dtype=torch.float32)
    
    # 标签映射
    if category == "upper_body":
        target_labels = [4, 14, 15] 
    elif category == "lower_body":
        target_labels = [5, 6, 12, 13]
    elif category == "dresses":
        target_labels = [4, 5, 7, 12, 13, 14, 15]
    else:
        target_labels = [4, 14, 15]

    for label in target_labels:
        mask_tensor[pred_seg == label] = 1.0
        
    mask_np = mask_tensor.cpu().numpy() * 255
    return Image.fromarray(mask_np.astype(np.uint8)).convert("L")

# --- 生命周期 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, upscaler, seg_processor, seg_model
    print("🚀 正在初始化高清系统...")
    try:
        # 1. 加载 Inpainting 模型
        print("Loading CatVTON...")
        pipeline = CatVTONPipeline(
            base_ckpt="runwayml/stable-diffusion-inpainting",
            attn_ckpt="zhengchong/CatVTON",
            attn_ckpt_version="mix",
            weight_dtype=torch.float16,
            device=device,
            skip_safety_check=True
        )
        
        # 2. 加载放大模型 (关键一步！)
        print("Loading Upscaler (HD Mode)...")
        # 如果模型已经下载好，这里会瞬间加载完成
        upscaler = StableDiffusionLatentUpscalePipeline.from_pretrained(
            "stabilityai/sd-x2-latent-upscaler",
            torch_dtype=torch.float16
        )
        # 显存优化：平时放内存，用时才上显卡，防止显存爆炸
        upscaler.enable_model_cpu_offload()

        # 3. 加载 SegFormer
        print("Loading SegFormer...")
        seg_processor = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
        seg_model = AutoModelForSemanticSegmentation.from_pretrained("mattmdjaga/segformer_b2_clothes").to(device)
        
        print("✨ 高清版服务就绪！支持 1536x2048 分辨率！端口: 8001")
    except Exception as e:
        print(f"💥 模型加载崩溃: {e}")
        raise e
    yield
    del pipeline, upscaler, seg_model
    torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

@app.post("/process_tryon")
async def process_tryon(
    person_img: UploadFile = File(...),
    cloth_img: UploadFile = File(...),
    category: str = Form("upper_body")
):
    global pipeline, upscaler
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        print(f"Processing Try-On: category={category}")
        
        # 1. 读取
        image = Image.open(io.BytesIO(await person_img.read())).convert("RGB")
        cloth = Image.open(io.BytesIO(await cloth_img.read())).convert("RGB")

        # 2. Resize (官方 Demo 标准分辨率)
        target_size = (768, 1024)
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        cloth = cloth.resize(target_size, Image.Resampling.LANCZOS)

        # 3. Mask & 关键模糊处理
        mask = get_accurate_mask(image, category)
        # 核心优化：高斯模糊，消除贴纸感
        mask = mask.filter(ImageFilter.GaussianBlur(radius=5)) 

        # 4. 推理 (第一阶段：生成底图)
        output = pipeline(
            image=image,
            condition_image=cloth,
            mask=mask, 
            num_inference_steps=50, # 提升至 50 步以获得最佳质感
            guidance_scale=2.5
        )

        if isinstance(output, list):
            base_img = output[0]
        elif hasattr(output, 'images'):
            base_img = output.images[0]
        else:
            base_img = output

        # 5. 高清放大 (第二阶段：细节增强)
        # 注意：如果显存紧张，可以把这步去掉，768x1024 的质量已经很高了
        print("🔍 正在进行 2x 高清放大...")
        upscaled_result = upscaler(
            prompt="",
            image=base_img,
            num_inference_steps=20,
            guidance_scale=0,
            generator=torch.manual_seed(42)
        ).images[0]

        # 6. 返回高清图
        img_byte_arr = io.BytesIO()
        upscaled_result.save(img_byte_arr, format='PNG')
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)