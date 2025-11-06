from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging
from pydantic import BaseModel

from app.models.news import News, NewsCreate, NewsUpdate, NewsInDB
from app.models.user import User, UserRole
from app.core.database import Database
from app.routers.auth import get_current_active_user
from app.routers.users import get_current_admin
from app.services.model_service import model_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["news"])

class ClassificationRequest(BaseModel):
    text: str

# New endpoint for text classification
@router.post("/news/classify", response_model=Dict[str, Any])
async def classify_text(
    request: ClassificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Classify a given text using the BERT model"""
    try:
        result = await model_service.predict(request.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Model service is not available")
    except Exception as e:
        logger.error(f"Classification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Classification failed")

# Admin endpoints for news management
@router.post("/news", response_model=News)
async def create_news(
    news: NewsCreate,
    current_user: User = Depends(get_current_admin)
):
    try:
        # Classify the news content using our model service
        try:
            classification = await model_service.predict(news.content)
            category = classification["category"]
            confidence_score = classification["confidence"]
        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            category = "Uncategorized"
            confidence_score = 0.0
        
        news_dict = news.model_dump()
        news_dict.update({
            "created_by": str(current_user.id),
            "created_at": datetime.utcnow(),
            "category": category,
            "confidence_score": confidence_score,
            "is_active": True,  # Ensure news is active by default
            "views_count": 0,
            "likes_count": 0,
            "is_featured": False
        })
        
        result = await Database.db["news"].insert_one(news_dict)
        created_news = await Database.db["news"].find_one({"_id": result.inserted_id})
        
        # Convert _id to id for Pydantic model
        created_news["id"] = str(created_news.pop("_id"))
        
        return News(**created_news)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create news article")

@router.put("/news/{news_id}", response_model=News)
async def update_news(
    news_id: str,
    news_update: NewsUpdate,
    current_user: User = Depends(get_current_admin)
):
    try:
        # Verify news exists
        existing_news = await Database.db["news"].find_one({"_id": ObjectId(news_id)})
        if not existing_news:
            raise HTTPException(status_code=404, detail="News article not found")
        
        update_data = news_update.model_dump(exclude_unset=True)
        
        # If content is updated, reclassify
        if "content" in update_data:
            classification = await model_service.predict(update_data["content"])
            update_data.update({
                "category": classification["category"],
                "confidence_score": classification["confidence"]
            })
        
        update_data["updated_at"] = datetime.utcnow()
        
        await Database.db["news"].update_one(
            {"_id": ObjectId(news_id)},
            {"$set": update_data}
        )
        
        updated_news = await Database.db["news"].find_one({"_id": ObjectId(news_id)})
        return News(**updated_news)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Model service is not available")
    except Exception as e:
        logger.error(f"Error updating news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update news article")

@router.delete("/news/{news_id}")
async def delete_news(
    news_id: str,
    current_user: User = Depends(get_current_admin)
):
    result = await Database.db["news"].delete_one({"_id": ObjectId(news_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News article not found")
    return {"message": "News article deleted successfully"}

# Public endpoints for news access
@router.get("/news", response_model=Dict[str, Any])
async def list_news(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    # Build query
    query = {"is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await Database.db["news"].count_documents(query)
    skip = (page - 1) * limit
    
    # Get news articles
    cursor = Database.db["news"].find(query)
    
    # Sort by created_at desc and apply pagination
    news_items = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
    
    # Convert ObjectId to string and _id to id for each news item
    for item in news_items:
        item["id"] = str(item.pop("_id"))
    
    # Update view count
    if news_items:
        news_ids = [ObjectId(news["id"]) for news in news_items]
        await Database.db["news"].update_many(
            {"_id": {"$in": news_ids}},
            {"$inc": {"views_count": 1}}
        )
    
    return {
        "items": news_items,
        "total": total
    }

@router.get("/news/{news_id}", response_model=News)
async def get_news(
    news_id: str,
    current_user: User = Depends(get_current_active_user)
):
    news = await Database.db["news"].find_one({"_id": ObjectId(news_id)})
    if not news:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Update view count
    await Database.db["news"].update_one(
        {"_id": ObjectId(news_id)},
        {"$inc": {"views_count": 1}}
    )
    
    # Convert _id to id for Pydantic model
    news["id"] = str(news.pop("_id"))
    return News(**news)

@router.post("/news/{news_id}/like")
async def like_news(
    news_id: str,
    current_user: User = Depends(get_current_active_user)
):
    result = await Database.db["news"].update_one(
        {"_id": ObjectId(news_id)},
        {"$inc": {"likes_count": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="News article not found")
    return {"message": "News article liked successfully"}

@router.get("/news/recommended", response_model=List[News])
async def get_recommended_news(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user)
):
    # Get news based on user's preferred categories
    if current_user.preferred_categories:
        query = {
            "is_active": True,
            "category": {"$in": current_user.preferred_categories}
        }
    else:
        # If no preferences, return latest news
        query = {"is_active": True}
    
    news_items = await Database.db["news"].find(query)\
        .sort("created_at", -1)\
        .limit(limit)\
        .to_list(length=None)
    
    return news_items 