from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
  username: str
  email: str
  password: str
  gender: Optional[str] = None
  age: Optional[int] = None
  height: Optional[int] = None
  weight: Optional[int] = None
  city: Optional[str] = None


class UserLogin(BaseModel):
  username: str
  password: str


class UserUpdate(BaseModel):
  gender: Optional[str] = None
  age: Optional[int] = None
  height: Optional[int] = None
  weight: Optional[int] = None
  city: Optional[str] = None
  profile_photo: Optional[str] = None
  new_password: Optional[str] = None


class UserResponse(BaseModel):
  id: int
  username: str
  email: str
  gender: Optional[str] = None
  age: Optional[int] = None
  height: int
  weight: int
  city: Optional[str] = None
  profile_photo: Optional[str] = None
  created_at: Optional[datetime] = None

  class Config:
    from_attributes = True
