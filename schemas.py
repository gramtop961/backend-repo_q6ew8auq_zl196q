"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# AiDUC specific schemas

class ForumPost(BaseModel):
    """
    EchoForum posts
    Collection name: "forumpost" (lowercase of class name)
    """
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Main message content")
    author: str = Field(..., description="Display name or user id")
    tags: Optional[List[str]] = Field(default_factory=list, description="Topic tags")

    # Accessibility metadata
    large_text: bool = Field(False, description="Render with larger typography")
    has_audio: bool = Field(False, description="Audio/voice note available")
    subtitles: bool = Field(False, description="Has captions/subtitles")

    # Optional links to attachments
    audio_url: Optional[str] = Field(None, description="URL to voice note if provided")
    attachment_url: Optional[str] = Field(None, description="Optional attachment URL")

# Add more schemas as needed for future features
