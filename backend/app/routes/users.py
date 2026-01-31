from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
  existing_user = db.query(User).filter(User.username == user.username).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="用户名已存在")

  existing_email = db.query(User).filter(User.email == user.email).first()
  if existing_email:
    raise HTTPException(status_code=400, detail="邮箱已存在")

  db_user = User(
    username=user.username,
    email=user.email,
    hashed_password=user.password,
    body_type=user.body_type,
    city=user.city
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
