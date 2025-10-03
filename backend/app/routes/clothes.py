"""
衣物路由
职责：处理衣物上传、获取衣橱列表
与前端交互接口：
- POST /api/v1/clothes/upload (multipart/form-data)
- GET /api/v1/clothes/wardrobe
与 ML 模块交互：调用图像识别服务
"""
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

    attributes = analyze_clothing_image(file_path)

    db_item = WardrobeItem(
        user_id=user_id,
        name=file.filename,
        category=attributes["category"],
        color=attributes["color"],
        season=",".join(attributes["season"]),
        material=attributes.get("material", ""),
        image_path=file_path
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "衣物上传成功", "item_id": db_item.id}

@router.get("/wardrobe")
def get_wardrobe(user_id: int, db: Session = Depends(get_db)):
    items = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    return items