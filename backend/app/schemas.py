from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeatureCreate(BaseModel):
    section: str
    title: Optional[str] = None
    description: str


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    price: Optional[float] = Field(default=None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=100)
    source_url: Optional[str] = None
    features: List[FeatureCreate] = []


class FeatureOut(BaseModel):
    section: str
    title: Optional[str] = None
    description: str = ""


class ProductOut(BaseModel):
    """Matches the DB: price, category and URLs are nullable there, so they are here."""

    model_config = ConfigDict(from_attributes=True)

    product_id: int
    title: str
    price: Optional[float] = None
    category: str = ""
    description: Optional[str] = None
    image_url: str = ""
    source_url: str = ""
    features: List[FeatureOut] = []


class FeatureUpdate(BaseModel):
    section: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    price: Optional[float] = Field(default=None, ge=0)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    features: Optional[List[FeatureCreate]] = None
