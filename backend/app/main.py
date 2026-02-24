import sys
from pathlib import Path
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# --- 1. 路径设置 ---
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.models.conversation import ConversationSession
from app.services.conversation_manager import ConversationManager

# --- 2. 数据库初始化 ---
init_db()

# --- 3. 定时任务：清理过期会话 ---
def cleanup_sessions_job():
  db = SessionLocal()
  try:
    count = ConversationManager.cleanup_old_sessions(db, days=3)
    if count > 0:
      print(f"清理了 {count} 个过期会话（3天前）")
  except Exception as e:
    print(f"会话清理失败: {e}")
  finally:
    db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(
  cleanup_sessions_job,
  CronTrigger(hour=3, minute=0),
  id='cleanup_sessions',
  name='清理过期会话',
  replace_existing=True
)
scheduler.start()

# 启动时执行会话清理
cleanup_sessions_job()

app = FastAPI(
  title="时尚推荐 API",
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

from app.routes import users, clothes, recommendation, vton

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(clothes.router, prefix="/api/v1/clothes", tags=["clothes"])
app.include_router(recommendation.router, prefix="/api/v1/recommend", tags=["recommendation"])
app.include_router(vton.router, prefix="/api/v1/vton", tags=["Virtual Try-On"])
# --- 6. 静态文件挂载 ---
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/")
async def root():
  return {"message": "时尚推荐系统后端正在运行！"}


@app.get("/health")
async def health():
  return {"status": "healthy"}


# --- 关闭时停止定时任务 ---
@app.on_event("shutdown")
def shutdown_event():
  scheduler.shutdown()