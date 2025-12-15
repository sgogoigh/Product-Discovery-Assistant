from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import SessionLocal
from app.db import crud
from app.schemas import ProductCreate, ProductOut, ProductUpdate
from app.utils.exceptions import NotFoundException

router = APIRouter()

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProductOut)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product with validation"""
    created = crud.create_product(db, product)
    data = {
        "product_id": created.id,   # map ORM id → product_id
        "title": created.title,
        "price": created.price,
        "description": created.description,
        "category": created.category,
        "image_url": created.image_url,
        "source_url": created.source_url,
        "features": created.features,
    }
    return ProductOut.model_validate(data)

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product by product_id"""
    product = crud.get_product(db, product_id)
    if not product:
        raise NotFoundException(detail=f"Product {product_id} not found")
    crud.delete_product(db, product_id)
    return None

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """Update an existing product by product_id"""
    existing = crud.get_product(db, product_id)
    if not existing:
        raise NotFoundException(detail=f"Product {product_id} not found")

    updated = crud.update_product(db, product_id, product)

    # Map ORM → API schema
    data = {
        "product_id": updated.id,   # map DB id → API product_id
        "title": updated.title,
        "price": updated.price,
        "description": updated.description,
        "category": updated.category,
        "image_url": updated.image_url,
        "source_url": updated.source_url,
        "features": updated.features,
    }
    return ProductOut.model_validate(data)

@router.patch("/{product_id}", response_model=ProductOut)
def patch_product_endpoint(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """Partially update a product by product_id"""
    existing = crud.get_product(db, product_id)
    if not existing:
        raise NotFoundException(detail=f"Product {product_id} not found")

    updated = crud.patch_product(db, product_id, product)

    # Normalize features if dict
    features = updated.features
    if isinstance(features, dict):
        features = normalize_features(features)

    data = {
        "product_id": updated.id,
        "title": updated.title,
        "price": updated.price,
        "description": updated.description,
        "category": updated.category,
        "image_url": updated.image_url,
        "source_url": updated.source_url,
        "features": features,
    }
    return ProductOut.model_validate(data)

def normalize_features(raw: dict) -> list:
    features = []
    if isinstance(raw, dict):
        for section, items in raw.items():
            for item in items:
                features.append({
                    "section": section,
                    "title": item.get("title"),
                    "description": item.get("description"),
                })
    return features

@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = crud.get_products(db)
    output: List[ProductOut] = []
    for p in products:
        # Build dict manually from ORM attributes
        data = {
            "product_id": p.id,
            "title": p.title,
            "price": p.price,
            "category": p.category,
            "image_url": p.image_url,
            "source_url": p.source_url,
            "features": normalize_features(p.features),
        }
        model = ProductOut.model_validate(data)
        output.append(model)
    return output

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise NotFoundException(detail=f"Product {product_id} not found")

    data = {
        "product_id": product.id,
        "title": product.title,
        "price": product.price,
        "category": product.category,
        "image_url": product.image_url,
        "source_url": product.source_url,
        "features": normalize_features(product.features),
    }
    return ProductOut.model_validate(data)