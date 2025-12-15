from sqlalchemy.orm import Session
from app.db import models
from app.schemas import ProductCreate, ProductUpdate, ProductOut

# Create product
def create_product(db: Session, product_data: ProductCreate):
    product = models.Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# Get all products
def get_products(db: Session):
    return db.query(models.Product).all()

# Get product by ID
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def update_product(db: Session, product_id: int, product_data: ProductCreate):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
    product.title = product_data.title
    product.price = product_data.price
    product.description = product_data.description
    product.category = product_data.category
    product.image_url = product_data.image_url
    product.source_url = product_data.source_url

    # Convert features (list of Pydantic models) → list of dicts
    if product_data.features:
        product.features = [f.model_dump() for f in product_data.features]
    else:
        product.features = []

    db.commit()
    db.refresh(product)
    return product

def patch_product(db: Session, product_id: int, product_data: ProductUpdate):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
    if product_data.title is not None:
        product.title = product_data.title
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.category is not None:
        product.category = product_data.category
    if product_data.image_url is not None:
        product.image_url = product_data.image_url
    if product_data.source_url is not None:
        product.source_url = product_data.source_url
    if product_data.features is not None:
        product.features = [f.model_dump() for f in product_data.features]

    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return True
    return False