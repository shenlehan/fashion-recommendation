from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
  username: str
  email: str
  password: str
  body_type: str = None
  city: str = None


class UserLogin(BaseModel):
  username: str
  password: str


class UserUpdate(BaseModel):
  body_type: str = None
  city: str = None


class UserResponse(BaseModel):
  id: int
  username: str
  email: str
  body_type: Optional[str] = None
  city: Optional[str] = None
  created_at: Optional[datetime] = None

  class Config:
    from_attributes = True
