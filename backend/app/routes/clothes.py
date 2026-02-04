from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import analyze_clothing_image
from app.models.wardrobe import WardrobeItem

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
    from fastapi import HTTPException
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
