from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import analyze_clothing_image
from app.models.wardrobe import WardrobeItem
import json

router = APIRouter()


@router.post("/upload")
def upload_clothing(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
  print(f"\n{'='*60}")
  print(f"收到上传请求")
  print(f"user_id: {user_id}")
  print(f"filename: {file.filename}")
  print(f"content_type: {file.content_type}")
  print(f"{'='*60}\n")
  
  import os
  upload_dir = "uploads"
  os.makedirs(upload_dir, exist_ok=True)
  file_path = os.path.join(upload_dir, file.filename)
  
  print(f"保存文件到: {file_path}")
  with open(file_path, "wb") as f:
    f.write(file.file.read())
  print(f"✅ 文件保存成功")

  # Analyze image with Qwen model
  attributes = analyze_clothing_image(file_path)

  season = attributes["season"]
  if isinstance(season, list):
    season = ",".join(season)

  # Use AI-generated name if available, otherwise use filename
  item_name = attributes.get("name", file.filename)

  db_item = WardrobeItem(
    user_id=user_id,
    name=item_name,
    category=attributes["category"],
    color=attributes["color"],
    season=season,
    material=attributes.get("material", ""),
    image_path=file_path
  )
  db.add(db_item)
  db.commit()
  db.refresh(db_item)
  
  print(f"✅ 数据库保存成功, item_id: {db_item.id}")
  return {"message": "上传成功！", "item_id": db_item.id}


@router.post("/upload-batch-stream")
async def upload_clothing_batch_stream(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
  async def generate_progress():
    import os
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    total = len(files)
    yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
    
    success_count = 0
    failed_count = 0
    success_items = []
    failed_items = []
    
    for idx, file in enumerate(files, 1):
      file_path = None
      try:
        # 保存文件
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
          f.write(content)
        
        # AI分析
        yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': total, 'status': 'analyzing', 'filename': file.filename})}\n\n"
        
        attributes = analyze_clothing_image(file_path)
        
        season = attributes["season"]
        if isinstance(season, list):
          season = ",".join(season)
        
        item_name = attributes.get("name", file.filename)
        
        # 保存到数据库
        db_item = WardrobeItem(
          user_id=user_id,
          name=item_name,
          category=attributes["category"],
          color=attributes["color"],
          season=season,
          material=attributes.get("material", ""),
          image_path=file_path
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        success_count += 1
        success_items.append({
          "filename": file.filename,
          "name": item_name,
          "item_id": db_item.id
        })
        
        yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': total, 'status': 'success', 'filename': file.filename, 'name': item_name})}\n\n"
        
      except Exception as e:
        failed_count += 1
        failed_items.append({
          "filename": file.filename,
          "error": str(e)
        })
        
        # 删除失败文件
        if os.path.exists(file_path):
          try:
            os.remove(file_path)
          except:
            pass
        
        yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': total, 'status': 'failed', 'filename': file.filename, 'error': str(e)})}\n\n"
    
    # 发送完成消息
    yield f"data: {json.dumps({'type': 'complete', 'success': success_items, 'failed': failed_items, 'total': total})}\n\n"
  
  return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.post("/upload-batch")
def upload_clothing_batch(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
  print(f"\n{'='*60}")
  print(f"收到批量上传请求")
  print(f"user_id: {user_id}")
  print(f"文件数量: {len(files)}")
  print(f"{'='*60}\n")
  
  import os
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
      print(f"\n[{idx}/{len(files)}] 处理文件: {file.filename}")
      
      # 保存文件
      file_path = os.path.join(upload_dir, file.filename)
      with open(file_path, "wb") as f:
        f.write(file.file.read())
      print(f"✅ 文件保存成功: {file_path}")
      
      # AI分析
      print(f"🤖 开始AI分析...")
      attributes = analyze_clothing_image(file_path)
      
      season = attributes["season"]
      if isinstance(season, list):
        season = ",".join(season)
      
      item_name = attributes.get("name", file.filename)
      
      # 保存到数据库
      db_item = WardrobeItem(
        user_id=user_id,
        name=item_name,
        category=attributes["category"],
        color=attributes["color"],
        season=season,
        material=attributes.get("material", ""),
        image_path=file_path
      )
      db.add(db_item)
      db.commit()
      db.refresh(db_item)
      
      print(f"✅ [{idx}/{len(files)}] 成功: {item_name} (ID: {db_item.id})")
      results["success"].append({
        "filename": file.filename,
        "name": item_name,
        "item_id": db_item.id
      })
      
    except Exception as e:
      print(f"❌ [{idx}/{len(files)}] 失败: {file.filename}")
      print(f"错误详情: {str(e)}")
      
      # 删除已保存的文件
      if os.path.exists(file_path):
        try:
          os.remove(file_path)
          print(f"🗑️  已清理失败文件: {file_path}")
        except:
          pass
      
      results["failed"].append({
        "filename": file.filename,
        "error": str(e)
      })
  
  print(f"\n{'='*60}")
  print(f"批量上传完成")
  print(f"成功: {len(results['success'])}/{results['total']}")
  print(f"失败: {len(results['failed'])}/{results['total']}")
  print(f"{'='*60}\n")
  
  return results


@router.get("/wardrobe/{user_id}")
def get_wardrobe(user_id: int, db: Session = Depends(get_db)):
  items = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  return items


@router.delete("/{item_id}")
def delete_clothing_item(item_id: int, db: Session = Depends(get_db)):
  print(f"\n{'='*60}")
  print(f"收到删除请求, item_id: {item_id}")
  
  item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
  if not item:
    print(f"❌ 未找到 item_id={item_id} 的衣物")
    print(f"{'='*60}\n")
    raise HTTPException(status_code=404, detail="未找到该衣物")

  print(f"找到衣物: {item.name}, 图片路径: {item.image_path}")
  
  import os
  if item.image_path and os.path.exists(item.image_path):
    try:
      os.remove(item.image_path)
      print(f"✅ 已删除图片文件: {item.image_path}")
    except Exception as e:
      print(f"⚠️  删除图片文件失败: {e}")
  else:
    print(f"⚠️  图片文件不存在: {item.image_path}")

  db.delete(item)
  db.commit()
  print(f"✅ 数据库记录删除成功")
  print(f"{'='*60}\n")
  return {"message": "删除成功"}
