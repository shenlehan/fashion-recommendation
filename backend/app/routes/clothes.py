from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.models.wardrobe import Wardrobe
from app.services.image_service import process_image
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/clothes/upload")
async def upload_clothes(file: UploadFile = File(...), db: Session = next(get_db())):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File type not supported. Please upload an image.")
    
    # Process the uploaded image
    clothing_item = process_image(file)
    
    # Save clothing item to the database
    db.add(clothing_item)
    db.commit()
    db.refresh(clothing_item)
    
    return {"message": "Clothing item uploaded successfully", "item_id": clothing_item.id}

@router.get("/clothes/")
async def get_clothes(db: Session = next(get_db())):
    clothes = db.query(Wardrobe).all()
    return clothes

@router.delete("/clothes/{item_id}")
async def delete_clothes(item_id: int, db: Session = next(get_db())):
    clothing_item = db.query(Wardrobe).filter(Wardrobe.id == item_id).first()
    if clothing_item is None:
        raise HTTPException(status_code=404, detail="Clothing item not found.")
    
    db.delete(clothing_item)
    db.commit()
    
    return {"message": "Clothing item deleted successfully"}