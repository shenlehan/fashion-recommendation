"""
后端主入口文件
职责：初始化 FastAPI 应用、挂载路由、配置 CORS、提供健康检查接口
与前端交互：提供 API 端点
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.models.user import User
from app.models.wardrobe import WardrobeItem

# 创建数据库表
print("正在创建数据库表...")
Base.metadata.create_all(bind=engine)
print("数据库表创建完成！")

app = FastAPI(
    title="Fashion Recommendation API",
    description="智能穿搭推荐系统后端服务",
    version="0.1.0",
)

# 配置 CORS（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延迟导入路由，避免循环导入和数据库初始化问题
from app.routes import users, clothes, recommendation

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(clothes.router, prefix="/api/v1/clothes", tags=["clothes"])
app.include_router(recommendation.router, prefix="/api/v1/recommend", tags=["recommendation"])

@app.get("/")
async def root():
    return {"message": "Fashion Recommendation Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
