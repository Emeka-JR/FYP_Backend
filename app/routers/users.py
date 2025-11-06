from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from app.core.security import get_password_hash
from app.core.database import Database
from app.models.user import User, UserCreate, UserRole
from app.routers.auth import get_current_active_user

router = APIRouter(tags=["users"])

@router.post("/users", response_model=User)
async def create_user(user: UserCreate):
    # Check if email already exists
    if await Database.db["users"].find_one({"email": user.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Additional validation for student/admin specific fields
    if user.role == UserRole.STUDENT:
        if not user.matric_number:
            raise HTTPException(
                status_code=400,
                detail="Matric number is required for students"
            )
    elif user.role == UserRole.ADMIN:
        if not user.staff_id:
            raise HTTPException(
                status_code=400,
                detail="Staff ID is required for admin users"
            )

    # Create user document
    user_dict = user.model_dump()
    hashed_password = get_password_hash(user_dict.pop("password"))
    user_dict["hashed_password"] = hashed_password
    
    result = await Database.db["users"].insert_one(user_dict)
    created_user = await Database.db["users"].find_one({"_id": result.inserted_id})
    return User(**created_user)

@router.get("/users/me/preferences")
async def get_user_preferences(current_user: User = Depends(get_current_active_user)):
    return {"preferred_categories": current_user.preferred_categories}

@router.put("/users/me/preferences")
async def update_user_preferences(
    categories: List[str],
    current_user: User = Depends(get_current_active_user)
):
    # Update user preferences
    await Database.db["users"].update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"preferred_categories": categories}}
    )
    return {"message": "Preferences updated successfully"}

@router.get("/users/me/department")
async def get_user_department(current_user: User = Depends(get_current_active_user)):
    return {"department": current_user.department}

# Admin only endpoints
async def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access this endpoint"
        )
    return current_user

@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_admin)):
    users = await Database.db["users"].find().to_list(length=None)
    return [User(**user) for user in users] 