import os
# 1. 强制镜像加速
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
import io
import uvicorn
import torch
import numpy as np
from PIL import Image, ImageFilter, ImageOps
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import List
import json
from contextlib import asynccontextmanager
from diffusers import StableDiffusionLatentUpscalePipeline

# --- 路径配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
catvton_path = os.path.join(current_dir, "CatVTON")
sys.path.append(catvton_path)

try:
    from model.pipeline import CatVTONPipeline
    from model.cloth_masker import AutoMasker  # 引入最强 Mask 工具
    print("成功导入 CatVTONPipeline 和 AutoMasker")
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

# --- 全局变量 ---
pipeline = None
automasker = None
upscaler = None 
device = "cuda" if torch.cuda.is_available() else "cpu"

# --- 类别 → mask_type 映射 ---
CATEGORY_TO_MASK_TYPE = {
    'inner_top': 'upper',
    'mid_top': 'upper', 
    'outer_top': 'outer',
    'bottom': 'lower',
    'full_body': 'overall',
}

# --- 试穿顺序优先级（数字越小越先穿）---
CATEGORY_PRIORITY = {
    'inner_top': 10,
    'mid_top': 20,
    'outer_top': 30,
    'bottom': 40,
    'full_body': 50,
}

# --- 核心辅助函数：防变形缩放 ---
def resize_and_padding(image, target_size):
    width, height = target_size
    w, h = image.size
    scale = min(width / w, height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    image = image.resize((new_w, new_h), Image.LANCZOS)
    new_image = Image.new("RGB", (width, height), (127, 127, 127))
    paste_x = (width - new_w) // 2
    paste_y = (height - new_h) // 2
    new_image.paste(image, (paste_x, paste_y))
    return new_image, (paste_x, paste_y, new_w, new_h)

# --- 生命周期 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, automasker, upscaler
    print("正在初始化 CatVTON 服务器...")
    try:
        # 1. 加载 Inpainting 模型
        print("Loading CatVTON Pipeline...")
        pipeline = CatVTONPipeline(
            base_ckpt="booksforcharlie/stable-diffusion-inpainting",
            attn_ckpt="zhengchong/CatVTON",
            attn_ckpt_version="mix",
            weight_dtype=torch.float16,
            device=device,
            skip_safety_check=True
        )
        
        # 2. 加载 AutoMasker (DensePose + SCHP) - 这是质量的关键！
        print("Loading AutoMasker (High Quality)...")
        # 假设权重在 CatVTON 目录下，或者自动下载
        automasker = AutoMasker(
            densepose_ckpt=os.path.join(current_dir, "CatVTON", "model", "DensePose"),
            schp_ckpt=os.path.join(current_dir, "CatVTON", "model", "SCHP"),
            device=device
        )

        # 3. (可选) 加载放大模型
        # Paste Back技术通常比Upscaler更有效且省显存，这里先保留但设为可选
        # print("Loading Upscaler...")
        # upscaler = StableDiffusionLatentUpscalePipeline.from_pretrained(...)
        
        print("服务启动成功！端口: 8001")
    except Exception as e:
        print(f"模型加载崩溃: {e}")
        import traceback
        traceback.print_exc()
    yield
    # 清理
    del pipeline, automasker
    torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

@app.post("/process_tryon")
async def process_tryon(
    person_img: UploadFile = File(...),
    cloth_img: UploadFile = File(...),
    category: str = Form("upper_body") # 暂时只做上半身，通用性最强
):
    global pipeline, automasker
    
    # 调试目录
    debug_dir = os.path.join(current_dir, "output", "debug_server")
    os.makedirs(debug_dir, exist_ok=True)

    try:
        print(f"Processing Request: category={category}")
        
        # 1. 读取图片
        person_raw = Image.open(io.BytesIO(await person_img.read())).convert("RGB")
        cloth_raw = Image.open(io.BytesIO(await cloth_img.read())).convert("RGB")

        # 2. 智能缩放 (768x1024)
        target_size = (768, 1024)
        person_resized, paste_info = resize_and_padding(person_raw, target_size)
        cloth_resized, _ = resize_and_padding(cloth_raw, target_size)
        
        # 保存一下输入图，方便调试
        person_resized.save(os.path.join(debug_dir, "input_person.png"))

        # 3. 自动生成高质量 Mask
        print("Generating Mask...")
        mask_result = automasker(person_resized, mask_type='upper')
        mask = mask_result['mask'] # 这是一个 PIL Image
        
        # [关键步骤] 保存 Mask 检查质量
        mask.save(os.path.join(debug_dir, "generated_mask.png"))

        # 4. Mask 边缘羽化
        mask_blurred = mask.filter(ImageFilter.GaussianBlur(radius=5))

        # 5. 模型推理
        print("模型推理中...")
        generator = torch.Generator(device=device).manual_seed(42)
        result_image = pipeline(
            image=person_resized,
            condition_image=cloth_resized,
            mask=mask_blurred,
            num_inference_steps=50, # 保持 50 步
            guidance_scale=2.5,
            generator=generator
        )[0]
        
        # 保存直出结果
        result_image.save(os.path.join(debug_dir, "raw_output.png"))

        # 6. [核心技术] Paste Back (回贴)
        # 将生成的衣服融合回原图 (person_resized)，只保留衣服区域
        # 这样脸部和背景就绝对不会变糊
        print("Pasting Back...")
        
        # 重新调整 mask 大小用于合成 (mask 也是 768x1024，不用动)
        mask_for_composite = mask.convert("L")
        # 稍微腐蚀一点 Mask，防止白边
        mask_for_composite = mask_for_composite.filter(ImageFilter.GaussianBlur(radius=1))
        
        # 组合：Mask 白色区域用新图，黑色区域用原图
        final_image = Image.composite(result_image, person_resized, mask_for_composite)
        
        # (可选) 如果需要还原回用户原始上传图片的尺寸，可以在这里做反向 Crop
        # 但通常 Web 端展示 768x1024 就够了

        # 7. 返回结果
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='PNG')
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/batch_tryon")
async def batch_tryon(
    person_img: UploadFile = File(...),
    cloth_imgs: List[UploadFile] = File(...),
    categories: str = Form(...)
):
    """批量试穿：按顺序依次试穿多件衣服"""
    global pipeline, automasker
    
    debug_dir = os.path.join(current_dir, "output", "debug_batch")
    os.makedirs(debug_dir, exist_ok=True)
    
    try:
        # 1. 解析类别列表
        category_list = json.loads(categories)
        print(f"📦 收到批量试穿请求: {len(cloth_imgs)} 件衣服, 类别: {category_list}")
        
        # 2. 读取所有衣服图片
        cloth_images = []
        for cloth_file in cloth_imgs:
            cloth_raw = Image.open(io.BytesIO(await cloth_file.read())).convert("RGB")
            cloth_images.append(cloth_raw)
        
        # 3. 按优先级排序（内层→外层→下装）
        items = list(zip(category_list, cloth_images))
        items.sort(key=lambda x: CATEGORY_PRIORITY.get(x[0], 99))
        
        # 4. 读取人像
        person_raw = Image.open(io.BytesIO(await person_img.read())).convert("RGB")
        target_size = (768, 1024)
        current_person, _ = resize_and_padding(person_raw, target_size)
        
        # 保存原始人像用于调试
        current_person.save(os.path.join(debug_dir, "input_person.png"))
        
        # 5. 顺序推理
        for i, (category, cloth_raw) in enumerate(items):
            print(f"试穿第 {i+1}/{len(items)} 件: {category}")
            
            mask_type = CATEGORY_TO_MASK_TYPE.get(category, 'upper')
            cloth_resized, _ = resize_and_padding(cloth_raw, target_size)
            
            # 保存衣服图片用于调试
            cloth_resized.save(os.path.join(debug_dir, f"cloth_{i+1}_{category}.png"))
            
            # 生成 mask
            print(f"生成 mask (type={mask_type})...")
            mask_result = automasker(current_person, mask_type=mask_type)
            mask = mask_result['mask']
            mask.save(os.path.join(debug_dir, f"mask_{i+1}_{category}.png"))
            mask_blurred = mask.filter(ImageFilter.GaussianBlur(radius=5))
            
            # 推理
            print(f"模型推理中...")
            generator = torch.Generator(device=device).manual_seed(42)
            result_image = pipeline(
                image=current_person,
                condition_image=cloth_resized,
                mask=mask_blurred,
                num_inference_steps=50,
                guidance_scale=2.5,
                generator=generator
            )[0]
            
            # Paste Back
            mask_for_composite = mask.convert("L").filter(ImageFilter.GaussianBlur(radius=1))
            current_person = Image.composite(result_image, current_person, mask_for_composite)
            
            # 保存中间结果
            current_person.save(os.path.join(debug_dir, f"step_{i+1}_{category}.png"))
            print(f"第 {i+1} 件完成")
        
        # 6. 返回最终结果
        print(f"批量试穿完成！共 {len(items)} 件")
        img_byte_arr = io.BytesIO()
        current_person.save(img_byte_arr, format='PNG')
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量试穿失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)