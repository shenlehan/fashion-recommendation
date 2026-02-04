from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
  existing_user = db.query(User).filter(User.username == user.username).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="用户名已存在")

  existing_email = db.query(User).filter(User.email == user.email).first()
  if existing_email:
    raise HTTPException(status_code=400, detail="邮箱已存在")

  # 注册时不需要填写个人资料，使用默认值
  db_user = User(
    username=user.username,
    email=user.email,
    hashed_password=user.password,
    gender=user.gender if user.gender else None,
    age=user.age if user.age is not None else None,
    height=0,  # 默认值，后续在个人资料页填写
    weight=0,  # 默认值，后续在个人资料页填写
    city=user.city if user.city else None
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user


@router.post("/login", response_model=UserResponse)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
  user = db.query(User).filter(User.username == credentials.username).first()
  if not user:
    raise HTTPException(status_code=404, detail="用户不存在")

  # Note: Password is stored as plaintext (security issue)
  if user.hashed_password != credentials.password:
    raise HTTPException(status_code=401, detail="密码错误")

  return user


@router.get("/profile", response_model=UserResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="用户不存在")
  return user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
  user_id: int,
  gender: Optional[str] = Form(None),
  age: Optional[str] = Form(None),
  height: Optional[str] = Form(None),
  weight: Optional[str] = Form(None),
  city: Optional[str] = Form(None),
  new_password: Optional[str] = Form(None),
  profile_photo: Optional[UploadFile] = File(None),
  db: Session = Depends(get_db)
):
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="用户不存在")
  
  # 更新普通字段
  if gender is not None and gender != '':
    user.gender = gender
  if age is not None and age != '':
    user.age = int(age)
  if height is not None and height != '':
    user.height = int(height)
  if weight is not None and weight != '':
    user.weight = int(weight)
  if city is not None and city != '':
    user.city = city
  
  # 更新密码
  if new_password is not None and new_password.strip():
    if len(new_password) < 6:
      raise HTTPException(status_code=400, detail="密码长度至少为6位")
    user.hashed_password = new_password
  
  # 处理照片上传
  if profile_photo:
    # 创建上传目录
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成独特文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(profile_photo.filename)[1]
    new_filename = f"profile_{user_id}_{timestamp}{file_ext}"
    file_path = os.path.join(upload_dir, new_filename)
    
    # 记录旧照片路径
    old_photo_path = None
    if user.profile_photo:
      old_photo_path = os.path.join(upload_dir, user.profile_photo)
    
    # 先保存新照片
    try:
      with open(file_path, "wb") as buffer:
        shutil.copyfileobj(profile_photo.file, buffer)
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"照片保存失败: {str(e)}")
    
    # 新照片保存成功后，删除旧照片
    if old_photo_path and os.path.exists(old_photo_path):
      try:
        os.remove(old_photo_path)
      except Exception as e:
        # 旧照片删除失败不影响主流程，只记录警告
        print(f"警告：删除旧照片失败 {old_photo_path}: {e}")
    
    user.profile_photo = new_filename
  
  db.commit()
  db.refresh(user)
  return user
