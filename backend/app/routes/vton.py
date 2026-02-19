from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import List
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 指向你刚才启动的 ML 服务地址
ML_SERVICE_URL = "http://127.0.0.1:8001/process_tryon"
ML_BATCH_URL = "http://127.0.0.1:8001/batch_tryon"

@router.post("/try-on")
async def try_on_proxy(
    person_img: UploadFile = File(...),
    cloth_img: UploadFile = File(...),
    category: str = Form("upper_body")
):
    """
    接收前端请求 -> 转发给 ML 服务 -> 返回图片给前端
    """
    logger.info(f"收到虚拟试衣请求: category={category}, person={person_img.filename}, cloth={cloth_img.filename}")
    
    # 设置超时时间为 120秒，因为生成图片可能需要几秒钟
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # 1. 读取文件内容
            person_bytes = await person_img.read()
            cloth_bytes = await cloth_img.read()
            
            # 2. 构造转发请求
            files = {
                'person_img': (person_img.filename, person_bytes, person_img.content_type),
                'cloth_img': (cloth_img.filename, cloth_bytes, cloth_img.content_type),
            }
            data = {'category': category}
            
            # 3. 发送给 8001 端口
            response = await client.post(ML_SERVICE_URL, files=files, data=data)
            
            if response.status_code != 200:
                logger.error(f"ML 服务报错: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="AI 生成失败，请稍后重试")
            
            # 4. 直接把生成的图片透传回给前端
            return Response(content=response.content, media_type="image/png")
            
        except httpx.RequestError as exc:
            logger.error(f"无法连接到 ML 服务: {exc}")
            raise HTTPException(status_code=500, detail="无法连接到 AI 推理服务，请检查服务是否启动")

@router.post("/batch-try-on")
async def batch_try_on_proxy(
    person_img: UploadFile = File(...),
    cloth_imgs: List[UploadFile] = File(...),
    categories: str = Form(...)
):
    """
    批量试穿：接收多件衣服 -> 转发给 ML 服务 -> 返回最终效果图
    """
    logger.info(f"收到批量试衣请求: categories={categories}, 衣服数量={len(cloth_imgs)}")
    
    # 批量试穿需要更长的超时时间（5分钟）
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # 1. 读取人像
            person_bytes = await person_img.read()
            
            # 2. 构造多文件请求
            files = [('person_img', (person_img.filename, person_bytes, person_img.content_type))]
            
            for cloth in cloth_imgs:
                cloth_bytes = await cloth.read()
                files.append(('cloth_imgs', (cloth.filename, cloth_bytes, cloth.content_type)))
            
            data = {'categories': categories}
            
            # 3. 发送给 ML 批量服务
            response = await client.post(ML_BATCH_URL, files=files, data=data)
            
            if response.status_code != 200:
                logger.error(f"ML 批量服务报错: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="批量试穿失败，请稍后重试")
            
            # 4. 返回最终效果图
            return Response(content=response.content, media_type="image/png")
            
        except httpx.RequestError as exc:
            logger.error(f"无法连接到 ML 批量服务: {exc}")
            raise HTTPException(status_code=500, detail="无法连接到 AI 推理服务，请检查服务是否启动")