from pydantic import BaseModel


class UserCreate(BaseModel):
  username: str
  email: str
  password: str
  body_type: str = None
  city: str = None


class UserLogin(BaseModel):
  username: str
  password: str


class UserResponse(BaseModel):
  id: int
  username: str
  email: str
  body_type: str = None
  city: str = None

  class Config:
    from_attributes = True
