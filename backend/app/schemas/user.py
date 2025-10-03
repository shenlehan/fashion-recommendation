"""
用户数据结构定义（Pydantic）
职责：定义请求/响应数据格式
与前端交互：定义 API 输入输出格式
"""
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    body_type: str = None
    city: str = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    body_type: str = None
    city: str = None

    class Config:
        from_attributes = True