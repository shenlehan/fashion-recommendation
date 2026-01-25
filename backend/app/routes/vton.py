from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 指向你刚才启动的 ML 服务地址
ML_SERVICE_URL = "http://127.0.0.1:8001/process_tryon"

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
                raise HTTPException(status_code=response.status_code, detail="AI 生成失败，请稍后再试")
            
            # 4. 直接把生成的图片透传回给前端
            return Response(content=response.content, media_type="image/png")
            
        except httpx.RequestError as exc:
            logger.error(f"无法连接到 ML 服务: {exc}")
            raise HTTPException(status_code=500, detail="无法连接到 AI 推理服务，请检查服务是否启动")