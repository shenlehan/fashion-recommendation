from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import analyze_clothing_image
from app.services.embedding_service import get_embedding_service
from app.models.wardrobe import WardrobeItem
import json

router = APIRouter()


@router.post("/upload")
def upload_clothing(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
  import os
  import uuid
  from pathlib import Path
  
  upload_dir = "uploads"
  os.makedirs(upload_dir, exist_ok=True)
  
  # 生成唯一文件名，保留原始扩展名，确保不冲突
  file_ext = Path(file.filename).suffix
  max_attempts = 10
  for attempt in range(max_attempts):
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    if not os.path.exists(file_path):
      break
    pass  # 文件名冲突，重新生成
  else:
    raise HTTPException(status_code=500, detail="无法生成唯一文件名")
  
  with open(file_path, "wb") as f:
    f.write(file.file.read())

  # Analyze image with Qwen model
  attributes = analyze_clothing_image(file_path)

  season = attributes["season"]
  if isinstance(season, list):
    season = "/".join(season)

  # Use AI-generated name if available, otherwise use filename
  item_name = attributes.get("name", file.filename)

  db_item = WardrobeItem(
    user_id=user_id,
    name=item_name,
    category=attributes["category"],
    color=attributes["color"],
    season=season,
    material=attributes.get("material", ""),
    name_en=attributes.get("name_en", ""),
    color_en=attributes.get("color_en", ""),
    material_en=attributes.get("material_en", ""),
    image_path=file_path
  )
  db.add(db_item)
  db.commit()
  db.refresh(db_item)
  
  # 生成并存储向量到ChromaDB（多模态：文本+图像）
  try:
    embedding_service = get_embedding_service()
    embedding_service.add_item(db_item.id, {
      "user_id": user_id,
      "name": item_name,
      "name_en": attributes.get("name_en", ""),
      "color_en": attributes.get("color_en", ""),
      "material_en": attributes.get("material_en", ""),
      "season": season,
      "category": attributes["category"]
    }, image_path=file_path)  # 传入图像路径
  except Exception as e:
    pass  # 向量生成失败不影响上传
  
  return {"message": "上传成功！", "item_id": db_item.id}


@router.post("/upload-batch-stream")
async def upload_clothing_batch_stream(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
  import uuid
  from app.services.upload_manager import get_upload_manager
  
  # 生成任务ID
  task_id = str(uuid.uuid4())
  upload_manager = get_upload_manager()
  
  # 创建任务记录
  upload_manager.create_task(task_id, user_id, len(files))
  
  async def generate_progress():
    import os
    import asyncio
    import sys
    import uuid
    from pathlib import Path
    from starlette.requests import Request
    from concurrent.futures import ThreadPoolExecutor
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    total = len(files)
    uploaded_ids = []  # 记录已上传的ID，用于回滚
    
    # 创建线程池用于AI分析，避免阻塞事件循环
    executor = ThreadPoolExecutor(max_workers=2)
    
    try:
      message = json.dumps({'type': 'start', 'total': total, 'task_id': task_id})
      yield f"data: {message}\n\n"
      await asyncio.sleep(0)
      
      success_count = 0
      failed_count = 0
      success_items = []
      failed_items = []
      
      for idx, file in enumerate(files, 1):
        file_path = None
        db_item = None
        try:
          # 生成唯一文件名，保留原始扩展名，确保不冲突
          file_ext = Path(file.filename).suffix
          max_attempts = 10
          for attempt in range(max_attempts):
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            if not os.path.exists(file_path):
              break
          else:
            raise Exception("无法生成唯一文件名")
          
          # 保存文件
          content = await file.read()
          with open(file_path, "wb") as f:
            f.write(content)
          
          # AI分析 - 使用线程池异步执行，避免阻塞其他请求
          loop = asyncio.get_event_loop()
          attributes = await loop.run_in_executor(executor, analyze_clothing_image, file_path)
          
          season = attributes["season"]
          if isinstance(season, list):
            season = "/".join(season)
          
          item_name = attributes.get("name", file.filename)
          
          # 保存到数据库
          db_item = WardrobeItem(
            user_id=user_id,
            name=item_name,
            category=attributes["category"],
            color=attributes["color"],
            season=season,
            material=attributes.get("material", ""),
            name_en=attributes.get("name_en", ""),
            color_en=attributes.get("color_en", ""),
            material_en=attributes.get("material_en", ""),
            image_path=file_path
          )
          db.add(db_item)
          db.commit()
          db.refresh(db_item)
          
          uploaded_ids.append(db_item.id)  # 记录已上传ID
          
          # 生成向量（异步，失败不影响上传）
          try:
            embedding_service = get_embedding_service()
            embedding_service.add_item(db_item.id, {
              "user_id": user_id,
              "name": item_name,
              "name_en": attributes.get("name_en", ""),
              "color_en": attributes.get("color_en", ""),
              "material_en": attributes.get("material_en", ""),
              "season": season,
              "category": attributes["category"]
            }, image_path=file_path)  # 传入图像路径
          except Exception as emb_err:
            pass  # 向量生成失败不影响上传
          
          success_count += 1
          success_item = {
            "filename": file.filename,
            "name": item_name,
            "item_id": db_item.id
          }
          success_items.append(success_item)
          
          # 更新任务进度
          upload_manager.update_progress(task_id, idx, success_item=success_item)
          
          message = json.dumps({'type': 'progress', 'current': idx, 'total': total, 'status': 'success', 'filename': file.filename, 'name': item_name, 'item_id': db_item.id})
          yield f"data: {message}\n\n"
          await asyncio.sleep(0)
          
        except Exception as e:
          failed_count += 1
          failed_item = {
            "filename": file.filename,
            "error": str(e)
          }
          failed_items.append(failed_item)
          
          # 更新任务进度（失败）
          upload_manager.update_progress(task_id, idx, failed_item=failed_item)
          
          # 删除失败文件
          if file_path and os.path.exists(file_path):
            try:
              os.remove(file_path)
            except:
              pass
          
          message = json.dumps({'type': 'progress', 'current': idx, 'total': total, 'status': 'failed', 'filename': file.filename, 'error': str(e)})
          yield f"data: {message}\n\n"
          await asyncio.sleep(0)
      
      # 发送完成消息
      message = json.dumps({'type': 'complete', 'success': success_items, 'failed': failed_items, 'total': total, 'task_id': task_id})
      yield f"data: {message}\n\n"
      await asyncio.sleep(0)
      
      # 标记任务完成
      upload_manager.complete_task(task_id)
      
    except (ConnectionError, asyncio.CancelledError, GeneratorExit) as e:
      # 客户端断开，标记任务取消
      upload_manager.cancel_task(task_id)
      # 客户端断开，立即回滚已上传的衣物
      for item_id in uploaded_ids:
        try:
          item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
          if item:
            if item.image_path and os.path.exists(item.image_path):
              os.remove(item.image_path)
            db.delete(item)
            db.commit()
        except Exception as del_err:
          pass  # 回滚删除失败
      raise
  
  return StreamingResponse(
    generate_progress(), 
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no"
    }
  )


@router.post("/upload-batch")
def upload_clothing_batch(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
  import os
  import uuid
  from pathlib import Path
  
  upload_dir = "uploads"
  os.makedirs(upload_dir, exist_ok=True)
  
  results = {
    "success": [],
    "failed": [],
    "total": len(files)
  }
  
  for idx, file in enumerate(files, 1):
    file_path = None
    try:
      # 生成唯一文件名，保留原始扩展名，确保不冲突
      file_ext = Path(file.filename).suffix
      max_attempts = 10
      for attempt in range(max_attempts):
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        if not os.path.exists(file_path):
          break
      else:
        raise Exception("无法生成唯一文件名")
      
      # 保存文件
      with open(file_path, "wb") as f:
        f.write(file.file.read())
      
      # AI分析
      attributes = analyze_clothing_image(file_path)
      
      season = attributes["season"]
      if isinstance(season, list):
        season = "/".join(season)
      
      item_name = attributes.get("name", file.filename)
      
      # 保存到数据库
      db_item = WardrobeItem(
        user_id=user_id,
        name=item_name,
        category=attributes["category"],
        color=attributes["color"],
        season=season,
        material=attributes.get("material", ""),
        name_en=attributes.get("name_en", ""),
        color_en=attributes.get("color_en", ""),
        material_en=attributes.get("material_en", ""),
        image_path=file_path
      )
      db.add(db_item)
      db.commit()
      db.refresh(db_item)
      
      # 生成向量
      try:
        embedding_service = get_embedding_service()
        embedding_service.add_item(db_item.id, {
          "user_id": user_id,
          "name": item_name,
          "name_en": attributes.get("name_en", ""),
          "color_en": attributes.get("color_en", ""),
          "material_en": attributes.get("material_en", ""),
          "season": season,
          "category": attributes["category"]
        }, image_path=file_path)  # 传入图像路径
      except Exception as emb_err:
        pass  # 向量生成失败
      
      results["success"].append({
        "filename": file.filename,
        "name": item_name,
        "item_id": db_item.id
      })
      
    except Exception as e:
      # 删除已保存的文件
      if os.path.exists(file_path):
        try:
          os.remove(file_path)
        except:
          pass
      
      results["failed"].append({
        "filename": file.filename,
        "error": str(e)
      })
  
  return results


@router.get("/wardrobe/{user_id}")
def get_wardrobe(user_id: int, db: Session = Depends(get_db)):
  items = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  return items


@router.get("/upload-status/{user_id}")
def get_upload_status(user_id: int):
  """获取用户当前的上传任务状态"""
  from app.services.upload_manager import get_upload_manager
  
  upload_manager = get_upload_manager()
  task = upload_manager.get_user_active_task(user_id)
  
  if task:
    return {
      "has_active_task": True,
      "task": task.to_dict()
    }
  else:
    return {
      "has_active_task": False,
      "task": None
    }


@router.delete("/{item_id}")
def delete_clothing_item(item_id: int, db: Session = Depends(get_db)):
  item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
  if not item:
    raise HTTPException(status_code=404, detail="未找到该衣物")
  
  import os
  # 检查是否有其他记录引用同一个图片文件
  if item.image_path:
    other_items_count = db.query(WardrobeItem).filter(
      WardrobeItem.image_path == item.image_path,
      WardrobeItem.id != item_id
    ).count()
    
    if other_items_count > 0:
      pass  # 还有其他衣物引用同一图片，跳过物理文件删除
    elif os.path.exists(item.image_path):
      try:
        os.remove(item.image_path)
      except Exception as e:
        pass  # 删除图片文件失败

  db.delete(item)
  db.commit()
  
  # 删除ChromaDB中的向量
  try:
    embedding_service = get_embedding_service()
    embedding_service.delete_item(item_id)
  except Exception as e:
    pass  # 向量删除失败不影响主流程
  
  return {"message": "删除成功"}


@router.post("/delete-batch")
def delete_clothing_batch(item_ids: List[int] = Body(...), db: Session = Depends(get_db)):
  import os
  results = {
    "success": [],
    "failed": [],
    "total": len(item_ids)
  }
  
  for idx, item_id in enumerate(item_ids, 1):
    try:
      item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
      if not item:
        raise Exception(f"未找到 item_id={item_id} 的衣物")
      
      # 检查是否有其他记录引用同一个图片文件
      if item.image_path:
        other_items_count = db.query(WardrobeItem).filter(
          WardrobeItem.image_path == item.image_path,
          WardrobeItem.id != item_id
        ).count()
        
        if other_items_count > 0:
          pass  # 还有其他衣物引用同一图片，跳过物理文件删除
        elif os.path.exists(item.image_path):
          try:
            os.remove(item.image_path)
          except Exception as e:
            pass  # 删除图片失败
      
      # 删除数据库记录
      db.delete(item)
      db.commit()
      
      # 删除向量
      try:
        embedding_service = get_embedding_service()
        embedding_service.delete_item(item_id)
      except Exception as emb_err:
        pass  # 向量删除失败
      
      results["success"].append({
        "item_id": item_id,
        "name": item.name
      })
      
    except Exception as e:
      results["failed"].append({
        "item_id": item_id,
        "error": str(e)
      })
  
  return results
