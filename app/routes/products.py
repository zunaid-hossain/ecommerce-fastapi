import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product, ProductCategory
from app.schemas.product import ProductCreate, Product as ProductSchema

router = APIRouter()

FAKESTORE_API_URL = "https://fakestoreapi.com/products"


def _get_or_create_category(db: Session, name: str) -> ProductCategory:
    category = db.query(ProductCategory).filter(ProductCategory.name == name).first()
    if category:
        return category

    category = ProductCategory(name=name, description=f"Imported from Fake Store: {name}")
    db.add(category)
    db.flush()
    return category


def _sync_fakestore_products(db: Session, limit: int | None = None) -> list[Product]:
    try:
        response = requests.get(FAKESTORE_API_URL, timeout=8)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not load products from Fake Store API: {exc}",
        )

    products_payload = response.json()
    if limit:
        products_payload = products_payload[:limit]

    synced_products = []
    for item in products_payload:
        external_id = item.get("id")
        sku = f"fake-store-{external_id}"
        product = db.query(Product).filter(Product.sku == sku).first()
        rating = item.get("rating") or {}
        category_name = item.get("category") or "general"
        category = _get_or_create_category(db, category_name)

        product_data = {
            "name": item.get("title") or "Untitled product",
            "description": item.get("description") or "",
            "price": float(item.get("price") or 0),
            "stock": int(rating.get("count") or 25),
            "sku": sku,
            "image_url": item.get("image"),
            "rating": float(rating.get("rate") or 0),
            "views": int(rating.get("count") or 0),
        }

        if product:
            for field, value in product_data.items():
                setattr(product, field, value)
        else:
            product = Product(**product_data)
            db.add(product)

        if category not in product.categories:
            product.categories.append(category)
        synced_products.append(product)

    db.commit()
    for product in synced_products:
        db.refresh(product)
    return synced_products


@router.get("/", response_model=list[ProductSchema])
def list_products(
    skip: int = 0,
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    source: str = Query("auto", pattern="^(auto|local)$"),
    db: Session = Depends(get_db),
):
    if source == "auto" and db.query(Product).count() == 0:
        _sync_fakestore_products(db, limit=limit)

    query = db.query(Product)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(term)) | (Product.description.ilike(term))
        )
    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product SKU already exists",
        )
    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.post("/sync-fakestore", response_model=list[ProductSchema])
def sync_fakestore_products(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _sync_fakestore_products(db, limit=limit)


@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.views += 1
    db.commit()
    db.refresh(product)
    return product
