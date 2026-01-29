import sys
from pathlib import Path
import os

# --- 1. 路径设置 ---
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import Base, engine
from app.models.user import User
from app.models.wardrobe import WardrobeItem

# --- 2. 数据库初始化 ---
print("Creating Database..")
Base.metadata.create_all(bind=engine)
print("Completed!")

app = FastAPI(
  title="Fashion Recommendation API",
  description="智能穿搭推荐系统后端服务",
  version="0.1.0",
)

# --- 3. CORS 设置 ---
app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.BACKEND_CORS_ORIGINS,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# --- 4. 路由导入 (Modified) ---
# ⚠️ 修改点 1: 这里增加了 vton
from app.routes import users, clothes, recommendation, vton

# --- 5. 路由注册 (Modified) ---
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(clothes.router, prefix="/api/v1/clothes", tags=["clothes"])
app.include_router(recommendation.router, prefix="/api/v1/recommend", tags=["recommendation"])

# ⚠️ 修改点 2: 注册试衣路由
# 注意：这里我们用了 /api/vton 前缀，对应前端的调用地址
app.include_router(vton.router, prefix="/api/v1/vton", tags=["Virtual Try-On"])
# --- 6. 静态文件挂载 ---
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/")
async def root():
  return {"message": "Fashion Recommendation Backend is running!"}


@app.get("/health")
async def health():
  return {"status": "healthy"}