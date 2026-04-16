from pydantic import BaseModel
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserDisplay(UserBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional

class TokenData(BaseModel):
    email: Optional[str] = None
