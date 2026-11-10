import os
import secrets
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.db.models import Product
from app.schemas import ProductCreate, ProductOut, ProductUpdate
from app.utils.exceptions import NotFoundException

router = APIRouter()


def require_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    """Write endpoints need X-Admin-Key == $ADMIN_API_KEY. Unset key = writes disabled."""
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=403, detail="Product writes are disabled on this deployment")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key")


def normalize_features(raw: Any) -> List[dict]:
    """Accept both stored shapes.

    Scraped rows:  {"Product Features": [{"title", "description"}], ...}
    API rows:      [{"section", "title", "description"}, ...]
    """
    out: List[dict] = []
    if isinstance(raw, dict):
        for section, items in raw.items():
            for item in items or []:
                if isinstance(item, dict):
                    out.append({"section": section, "title": item.get("title"),
                                "description": item.get("description") or ""})
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                out.append({"section": item.get("section") or "Features", "title": item.get("title"),
                            "description": item.get("description") or ""})
    return out


def to_out(p: Product) -> ProductOut:
    return ProductOut(
        product_id=p.id,
        title=p.title,
        price=p.price,
        category=p.category or "",
        description=p.description,
        image_url=p.image_url or "",
        source_url=p.source_url or "",
        features=normalize_features(p.features),
    )


def _get_or_404(db: Session, product_id: int) -> Product:
    product = crud.get_product(db, product_id)
    if not product:
        raise NotFoundException(detail=f"Product {product_id} not found")
    return product


# Both slash forms: the app sets redirect_slashes=False.
@router.get("", response_model=List[ProductOut], include_in_schema=False)
@router.get("/", response_model=List[ProductOut])
def list_products(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    return [to_out(p) for p in crud.get_products(db, limit=limit, offset=offset, category=category)]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return to_out(_get_or_404(db, product_id))


@router.post("/", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    return to_out(crud.create_product(db, product))


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    _get_or_404(db, product_id)
    return to_out(crud.update_product(db, product_id, product))


@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def patch_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    _get_or_404(db, product_id)
    return to_out(crud.patch_product(db, product_id, product))


@router.delete("/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, product_id)
    crud.delete_product(db, product_id)
