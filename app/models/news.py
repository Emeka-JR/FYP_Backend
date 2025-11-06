from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(str(v)):
            raise ValueError("Invalid ObjectId")
        return str(v)

class NewsBase(BaseModel):
    title: str
    content: str
    category: Optional[str] = None  # Will be auto-classified by BERT model
    source: Optional[str] = None
    tags: List[str] = []
    image_url: Optional[str] = None

class NewsCreate(NewsBase):
    pass

class NewsInDB(NewsBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None  # Admin user ID
    views_count: int = 0
    likes_count: int = 0
    is_featured: bool = False
    is_active: bool = True
    confidence_score: Optional[float] = None  # Classification confidence from BERT

    class Config:
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

class News(NewsBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    views_count: int = 0
    likes_count: int = 0
    is_featured: bool = False
    is_active: bool = True
    confidence_score: Optional[float] = None

    class Config:
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True 