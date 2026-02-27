from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
class UserRole(str, Enum):
    STUDENT = "student"
    ACADEMY_ADMIN = "academy_admin"
    SUPER_ADMIN = "super_admin"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def serialize_id(user_doc: dict) -> dict:
    """Safely convert MongoDB _id Filter to id string for JSON response."""
    if user_doc and "_id" in user_doc:
        user_doc["id"] = str(user_doc.pop("_id"))
    return user_doc


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone_number: str = Field(..., min_length=10, max_length=10)
    role: UserRole = UserRole.STUDENT
    academy_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=10)
    role: Optional[UserRole] = None
    academy_id: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    academy_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
