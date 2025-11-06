from app.core.security import get_password_hash
import json
from datetime import datetime

# Create a user with a properly hashed password
password = "password123"
hashed_password = get_password_hash(password)

user = {
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "student",
    "is_active": True,
    "hashed_password": hashed_password,
    "created_at": datetime.utcnow().isoformat(),
    "preferred_categories": []
}

print("Copy this JSON to MongoDB Compass:")
print(json.dumps(user, indent=2)) 