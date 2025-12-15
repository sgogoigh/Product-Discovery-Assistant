from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

# Input schema for creating a product
class FeatureCreate(BaseModel):
    section: str
    title: Optional[str]
    description: str

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    price: int
    description: str
    image_url: str
    category: str
    source_url: str
    features: List[FeatureCreate]

# Output schema for product response
class FeatureOut(BaseModel):
    section: str
    title: Optional[str]
    description: str

class ProductOut(BaseModel):
    product_id: int
    title: str
    price: int
    category: str
    image_url: str
    source_url: str
    features: List[FeatureOut]
    class Config:
        from_attributes = True

class FeatureUpdate(BaseModel):
    section: Optional[str]
    title: Optional[str]
    description: Optional[str]

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    features: Optional[List[FeatureUpdate]] = None
    class Config:
        from_attributes = True