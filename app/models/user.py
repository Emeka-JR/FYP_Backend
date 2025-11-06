from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from bson import ObjectId

class UserRole(str, Enum):
    ADMIN = "admin"
    STUDENT = "student"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.STUDENT
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    matric_number: Optional[str] = None  # For students
    department: Optional[str] = None
    staff_id: Optional[str] = None  # For admin/staff

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferred_categories: List[str] = []  # For personalization
    matric_number: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None
    staff_id: Optional[str] = None

    class Config:
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True

class User(UserBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferred_categories: List[str] = []
    matric_number: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None
    staff_id: Optional[str] = None

    class Config:
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True 