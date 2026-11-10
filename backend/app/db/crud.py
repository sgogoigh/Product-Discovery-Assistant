from typing import List, Optional

from sqlalchemy.orm import Session

from app.db import models
from app.schemas import ProductCreate, ProductUpdate


def create_product(db: Session, product_data: ProductCreate) -> models.Product:
    product = models.Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_products(db: Session, limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[models.Product]:
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    return q.order_by(models.Product.id).offset(offset).limit(limit).all()


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.get(models.Product, product_id)


def update_product(db: Session, product_id: int, product_data: ProductCreate) -> Optional[models.Product]:
    product = get_product(db, product_id)
    if not product:
        return None
    for key, value in product_data.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def patch_product(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[models.Product]:
    product = get_product(db, product_id)
    if not product:
        return None
    for key, value in product_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = get_product(db, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True
