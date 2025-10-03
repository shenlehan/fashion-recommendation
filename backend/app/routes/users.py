from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.database import get_db
from app.services.image_service import upload_user_image
from app.services.ml_inference import get_user_recommendations

router = APIRouter()

@router.post("/register")
def register_user(user: User, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": user.id}

@router.post("/upload-image")
def upload_image(user_id: int, image: bytes, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    image_url = upload_user_image(image)
    user.image_url = image_url
    db.commit()
    return {"message": "Image uploaded successfully", "image_url": image_url}

@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    recommendations = get_user_recommendations(user)
    return recommendations