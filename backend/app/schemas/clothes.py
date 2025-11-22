from pydantic import BaseModel
from typing import List


class WardrobeItemResponse(BaseModel):
  id: int
  name: str
  category: str
  color: str
  season: str
  material: str
  image_path: str

  class Config:
    from_attributes = True
