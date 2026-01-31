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
  import os
  upload_dir = "uploads"
  os.makedirs(upload_dir, exist_ok=True)
  file_path = os.path.join(upload_dir, file.filename)
  with open(file_path, "wb") as f:
    f.write(file.file.read())

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
  return {"message": "上传成功！", "item_id": db_item.id}


@router.get("/wardrobe/{user_id}")
def get_wardrobe(user_id: int, db: Session = Depends(get_db)):
  items = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
  return items


@router.delete("/{item_id}")
def delete_clothing_item(item_id: int, db: Session = Depends(get_db)):
  item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
  if not item:
    return {"error": "未找到该衣物"}

  import os
  if item.image_path and os.path.exists(item.image_path):
    os.remove(item.image_path)

  db.delete(item)
  db.commit()
  return {"message": "删除成功"}
