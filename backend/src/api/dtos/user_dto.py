import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional

# DTO for creating a new local user (request body)
class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "user"

# DTO for updating an existing user (request body)
class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None

# DTO for user response (returned by API)
class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: str
    provider: str
    is_verified: bool

    class Config:
        orm_mode = True